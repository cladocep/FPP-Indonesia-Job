"""
services/sql_service.py

SQL service layer — handles all database query logic.
Called by SQL Agent to generate, execute, and format SQL queries.

Usage:
    from backend.app.services.sql_service import generate_and_execute_query
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
- IMPORTANT: For city filtering, ALWAYS use LIKE with wildcards, e.g. location_city_norm LIKE '%jakarta%' NOT location_city_norm = 'jakarta'. Cities are stored as subdistricts like 'jakarta raya', 'jakarta selatan', 'jakarta barat'.
- Column `skills` is a comma-separated text field (e.g. "python, sql, excel")
- Columns `salary_min` and `salary_max` are integers (IDR). Many are NULL.
- For salary queries, always filter WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL
- If no results found with strict filters, relax location or salary filters to return nearby/related results
- Always use LIMIT to prevent huge results (default LIMIT 20)

Generate ONLY a valid SELECT SQL query. No explanation, no markdown, no backticks.
Just the raw SQL query."""


# ── SQL generation ───────────────────────────────────────────────────────────

def generate_sql(user_message: str, openai_client: OpenAI = None) -> str:
    """
    Use LLM to convert natural language to SQL query.

    Args:
        user_message: natural language question
        openai_client: OpenAI client instance

    Returns:
        SQL query string
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    schema = get_table_schema()

    try:
        samples = get_sample_data(limit=2)
        sample_text = str(samples)[:1500]
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
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql


def run_query(sql: str) -> list[dict]:
    """
    Execute a SQL query with safety checks.

    Args:
        sql: SQL query string (must be SELECT)

    Returns:
        list of result dicts

    Raises:
        ValueError: if query is not a SELECT statement
    """
    return execute_query(sql)


def format_results(
    question: str,
    results: list[dict],
    openai_client: OpenAI = None,
) -> str:
    """
    Use LLM to format raw SQL results into human-readable answer.

    Args:
        question: original user question
        results: raw query results
        openai_client: OpenAI client instance

    Returns:
        formatted answer string
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    if not results:
        results_text = "Query returned no results."
    else:
        results_text = str(results[:50])

    prompt = f"""You are a helpful assistant for an Indonesian Job Search platform.

The user asked: "{question}"

The SQL query returned this data:
{results_text}

Format this data into a clear, human-readable answer.
Rules:
1. Respond in the same language the user uses (Indonesian or English).
2. Use numbers and statistics clearly.
3. If the result is empty, say no data was found.
4. Keep it concise but informative.
5. Format large numbers with separators (e.g. 5.000.000 for IDR)."""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    return response.choices[0].message.content


def generate_and_execute_query(
    user_message: str,
    openai_client: OpenAI = None,
) -> dict:
    """
    Full SQL service pipeline: generate SQL + execute + format.

    Returns:
        dict with: sql, raw_results, formatted_answer, row_count, success
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        sql = generate_sql(user_message, openai_client)
        results = run_query(sql)

        # Retry without location filter if no meaningful results found
        # (handles empty list AND single-row results where all values are None)
        def is_empty_result(rows: list) -> bool:
            if not rows:
                return True
            if len(rows) == 1 and all(v is None for v in rows[0].values()):
                return True
            return False

        if is_empty_result(results):
            fallback_message = user_message + " (ignore location filter, search nationally across all cities)"
            sql = generate_sql(fallback_message, openai_client)
            results = run_query(sql)

        answer = format_results(user_message, results, openai_client)

        return {
            "sql": sql,
            "raw_results": results,
            "formatted_answer": answer,
            "row_count": len(results),
            "success": True,
        }

    except ValueError as e:
        return {
            "sql": "",
            "raw_results": [],
            "formatted_answer": f"Query tidak valid: {e}",
            "row_count": 0,
            "success": False,
        }

    except Exception as e:
        return {
            "sql": "",
            "raw_results": [],
            "formatted_answer": f"Terjadi kesalahan: {e}",
            "row_count": 0,
            "success": False,
        }
