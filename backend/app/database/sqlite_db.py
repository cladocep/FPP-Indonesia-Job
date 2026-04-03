"""
database/sqlite_db.py

SQLite database connection and query execution.
Used by SQL Agent for structured data queries.
"""

import sqlite3
from typing import Optional, Any

from backend.app.config import SQLITE_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with Row factory."""
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"SQLite DB not found: {SQLITE_DB_PATH}")

    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = ()) -> list[dict]:
    """
    Execute a SELECT query and return results as list of dicts.

    Safety: only allows SELECT statements.
    """
    cleaned = query.strip().upper()
    if not cleaned.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed for safety.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_table_schema() -> str:
    """
    Return the schema of the jobs table.
    Used by SQL Agent to understand available columns.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(jobs)")
        columns = cur.fetchall()

        schema_lines = []
        for col in columns:
            col_dict = dict(col)
            name = col_dict["name"]
            col_type = col_dict["type"]
            schema_lines.append(f"  {name} ({col_type})")

        return "Table: jobs\nColumns:\n" + "\n".join(schema_lines)
    finally:
        conn.close()


def get_sample_data(limit: int = 3) -> list[dict]:
    """Return a few sample rows for context."""
    return execute_query(f"SELECT * FROM jobs LIMIT {limit}")
