"""
SQL Agent

Flow:
1. Receive natural language question
2. LLM generates a SQL query based on table schema
3. Execute query on SQLite
4. LLM formats the raw result into a human-readable answer

Handles questions like:
- "Berapa jumlah lowongan full-time di Jakarta?"
- "Rata-rata gaji untuk posisi data analyst?"
- "Kota mana yang paling banyak lowongan?"
- "Berapa persen lowongan yang mencantumkan gaji?"
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, LLM_MODEL
from backend.app.database.sqlite_db import execute_query, get_table_schema, get_sample_data


# ── prompts ──────────────────────────────────────────────────────────────────

SQL_GENERATOR_PROMPT = """You are a SQL query generator for an Indonesian Job database.

Database schema:
{schema}

Sample data:
{sample_data}

Important notes:
- The database is SQLite. Use SQLite-compatible syntax.
- Table name is `jobs`.
- Column `work_type_normalized` contains values like:
  full_time, part_time, contract, internship, freelance, remote, hybrid, unknown
- Column `location_city_norm` and `location_province_norm` are lowercase normalized versions.
- Column `location` contains the original full location text.
- Column `skills` is a comma-separated text field (example: "python, sql, excel").
- Columns `salary_min` and `salary_max` are integers in IDR. Many rows are NULL.
- For salary-related queries, filter to rows with salary data:
  `(salary_min IS NOT NULL OR salary_max IS NOT NULL)`
- The work_type_normalized column only has: full_time, contract, kasual, part_time.
  There is NO "remote" or "internship" or "freelance" value in this dataset.
- If user asks about remote jobs, also search in job_description using LIKE '%remote%'.

Location handling rules:
- Users may ask for broad locations that do not exactly match `location_city_norm`.
- If user asks for "Jakarta", do NOT generate:
  `location_city_norm = 'jakarta'`
- For "Jakarta", use broader matching:
  `(location_city_norm LIKE 'jakarta%' OR location_province_norm LIKE 'jakarta%' OR LOWER(location) LIKE '%jakarta%')`
- For other broad location mentions, prefer flexible matching with `LIKE` when exact equality may miss subregions.

Query rules:
- Only generate a SELECT query.
- Do not generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or PRAGMA.
- Use LIMIT 20 for row-level result queries unless the query is an aggregate-only query like COUNT, AVG, MIN, MAX.
- For role/title matching, prefer case-insensitive matching with LOWER(job_title) LIKE '%...%'.
- For skill/description matching, use LOWER(job_description) LIKE '%...%' or LOWER(skills) LIKE '%...%'.
- If user asks for average salary, return AVG(salary_min) and AVG(salary_max).
- If user asks for counts, use COUNT(*).
- If user asks for top lists, sort clearly and use LIMIT.

Generate ONLY a valid raw SQLite SELECT query.
No explanation.
No markdown.
No backticks.
"""


RESULT_FORMATTER_PROMPT = """You are a helpful assistant for an Indonesian Job Search platform.

The user asked: "{question}"

The SQL query returned this data:
{results}

Format this data into a clear, human-readable answer.

Rules:
1. Respond in the same language the user uses (Indonesian or English).
2. Use numbers and statistics clearly.
3. If the result is empty, say no data was found.
4. Keep it concise but informative.
5. Format IDR numbers nicely with Indonesian separators when helpful.
6. If the result contains average salary_min and average salary_max, present them as a salary range estimate.
7. If the result is a COUNT(*) result equal to 0, clearly say no matching jobs were found.
"""


# ── SQL helpers ──────────────────────────────────────────────────────────────

def clean_sql_response(sql: str) -> str:
    """Remove common LLM wrappers/formatting."""
    sql = sql.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def patch_sql_for_known_location_issues(sql: str, user_message: str) -> str:
    """
    Apply defensive fixes for known generation mistakes.
    Current main fix: broad Jakarta matching.
    """
    sql_lower = sql.lower()
    user_lower = user_message.lower()

    jakarta_exact = "location_city_norm = 'jakarta'"
    jakarta_broad = (
        "(location_city_norm LIKE 'jakarta%' "
        "OR location_province_norm LIKE 'jakarta%' "
        "OR LOWER(location) LIKE '%jakarta%')"
    )

    if "jakarta" in user_lower and jakarta_exact in sql_lower:
        # Replace exact match with broader match while preserving rest of query
        sql = sql.replace("location_city_norm = 'jakarta'", jakarta_broad)
        sql = sql.replace("location_city_norm = 'JAKARTA'", jakarta_broad)
        sql = sql.replace('location_city_norm = "jakarta"', jakarta_broad)
        sql = sql.replace('location_city_norm = "JAKARTA"', jakarta_broad)

    return sql


def validate_sql_is_safe(sql: str) -> None:
    """Extra safety validation before execution."""
    cleaned = sql.strip().lower()

    if not cleaned.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    blocked_keywords = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "create ",
        "pragma ",
        "attach ",
        "detach ",
        "replace ",
        "truncate ",
    ]

    for keyword in blocked_keywords:
        if keyword in cleaned:
            raise ValueError(f"Blocked SQL keyword detected: {keyword.strip()}")


# ── SQL generation ───────────────────────────────────────────────────────────

def generate_sql(user_message: str, openai_client: OpenAI) -> str:
    """Use LLM to convert natural language to SQL."""
    schema = get_table_schema()

    try:
        samples = get_sample_data(limit=3)
        sample_text = str(samples)[:2000]
    except Exception:
        sample_text = "No sample data available."

    prompt = SQL_GENERATOR_PROMPT.format(
        schema=schema,
        sample_data=sample_text,
    )

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=500,
    )

    sql = response.choices[0].message.content.strip()
    sql = clean_sql_response(sql)
    sql = patch_sql_for_known_location_issues(sql, user_message)
    validate_sql_is_safe(sql)

    return sql


# ── result formatting ────────────────────────────────────────────────────────

def format_results(
    question: str,
    results: list[dict],
    openai_client: OpenAI,
) -> str:
    """Use LLM to format raw SQL results into readable answer."""
    if not results:
        results_text = "Query returned no results."
    else:
        results_text = str(results[:50])

    prompt = RESULT_FORMATTER_PROMPT.format(
        question=question,
        results=results_text,
    )

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    return response.choices[0].message.content


# ── main handler ─────────────────────────────────────────────────────────────

def handle_sql_query(
    user_message: str,
    openai_client: OpenAI = None,
) -> str:
    """
    Handle a SQL query end-to-end.

    1. Generate SQL from natural language
    2. Execute SQL on SQLite
    3. Format results into readable answer
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"[SQL Agent] Generating SQL for: {user_message[:60]}...")

    try:
        sql = generate_sql(user_message, openai_client)
    except ValueError as e:
        print(f"[SQL Agent] SQL validation error: {e}")
        return f"Maaf, query yang dihasilkan tidak valid: {e}"
    except Exception as e:
        print(f"[SQL Agent] SQL generation error: {e}")
        return (
            "Maaf, terjadi kesalahan saat membuat query database. "
            "Coba tanyakan dengan cara yang berbeda ya!"
        )

    print(f"[SQL Agent] Generated SQL: {sql}")

    try:
        results = execute_query(sql)
        print(f"[SQL Agent] Query returned {len(results)} rows.")
    except ValueError as e:
        return f"Maaf, query yang dihasilkan tidak valid: {e}"
    except Exception as e:
        print(f"[SQL Agent] SQL execution error: {e}")
        return (
            "Maaf, terjadi kesalahan saat menjalankan query database. "
            "Coba tanyakan dengan cara yang berbeda ya!"
        )

    return format_results(user_message, results, openai_client)