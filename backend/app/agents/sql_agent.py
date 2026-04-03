"""
agents/sql_agent.py

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
- Column `work_type_normalized` contains: full_time, part_time, contract, internship, freelance, remote, hybrid, unknown
- Column `location_city_norm` and `location_province_norm` are lowercase normalized versions
- Column `skills` is a comma-separated text field (e.g. "python, sql, excel")
- Columns `salary_min` and `salary_max` are integers (IDR). Many are NULL.
- For salary queries, always filter WHERE salary_min IS NOT NULL or salary_max IS NOT NULL
- Always use LIMIT to prevent huge results (default LIMIT 20)

Generate ONLY a valid SELECT SQL query. No explanation, no markdown, no backticks.
Just the raw SQL query."""

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
5. Format large numbers with separators (e.g. 5.000.000 for IDR)."""


# ── SQL generation ───────────────────────────────────────────────────────────

def generate_sql(user_message: str, openai_client: OpenAI) -> str:
    """Use LLM to convert natural language to SQL."""
    schema = get_table_schema()

    # Get sample data for context
    try:
        samples = get_sample_data(limit=2)
        sample_text = str(samples)[:1500]  # limit context size
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

    # Clean up common LLM formatting issues
    sql = sql.replace("```sql", "").replace("```", "").strip()

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
        # Limit to prevent token overflow
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

    # Step 1: Generate SQL
    print(f"[SQL Agent] Generating SQL for: {user_message[:60]}...")
    sql = generate_sql(user_message, openai_client)
    print(f"[SQL Agent] Generated SQL: {sql}")

    # Step 2: Execute query (with safety check)
    try:
        results = execute_query(sql)
        print(f"[SQL Agent] Query returned {len(results)} rows.")
    except ValueError as e:
        # Non-SELECT query attempted
        return f"Maaf, query yang dihasilkan tidak valid: {e}"
    except Exception as e:
        print(f"[SQL Agent] SQL execution error: {e}")
        return (
            "Maaf, terjadi kesalahan saat menjalankan query database. "
            "Coba tanyakan dengan cara yang berbeda ya!"
        )

    # Step 3: Format results
    answer = format_results(user_message, results, openai_client)
    return answer
