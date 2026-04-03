"""
database/init_db.py

Database initialization and health check.
Used during app startup to verify all databases are ready.

Usage:
    from backend.app.database.init_db import check_databases

    status = check_databases()
    print(status)
"""

import sqlite3
from pathlib import Path
from typing import Optional

from backend.app.config import SQLITE_DB_PATH, QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION


def check_sqlite() -> dict:
    """
    Check if SQLite database exists and is readable.

    Returns:
        dict with: status ("ok" or "error"), message, row_count
    """
    try:
        if not SQLITE_DB_PATH.exists():
            return {
                "status": "error",
                "message": f"jobs.db not found at {SQLITE_DB_PATH}",
                "row_count": 0,
            }

        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cur = conn.cursor()

        # Check table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if not cur.fetchone():
            conn.close()
            return {
                "status": "error",
                "message": "Table 'jobs' not found in database",
                "row_count": 0,
            }

        # Count rows
        cur.execute("SELECT COUNT(*) FROM jobs")
        count = cur.fetchone()[0]
        conn.close()

        return {
            "status": "ok",
            "message": f"SQLite ready with {count} jobs",
            "row_count": count,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"SQLite error: {str(e)}",
            "row_count": 0,
        }


def check_qdrant() -> dict:
    """
    Check if Qdrant is accessible and collection exists.

    Returns:
        dict with: status ("ok" or "error"), message, point_count
    """
    try:
        if not QDRANT_URL or not QDRANT_API_KEY:
            return {
                "status": "error",
                "message": "Qdrant credentials not configured in .env",
                "point_count": 0,
            }

        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=10,
        )

        # Check collection exists
        collections = [c.name for c in client.get_collections().collections]
        if QDRANT_COLLECTION not in collections:
            return {
                "status": "error",
                "message": f"Collection '{QDRANT_COLLECTION}' not found",
                "point_count": 0,
            }

        # Count points
        info = client.get_collection(QDRANT_COLLECTION)
        count = info.points_count

        return {
            "status": "ok",
            "message": f"Qdrant ready with {count} vectors",
            "point_count": count,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Qdrant error: {str(e)}",
            "point_count": 0,
        }


def check_databases() -> dict:
    """
    Run all database health checks.

    Returns:
        dict with: sqlite, qdrant, all_ok
    """
    sqlite_status = check_sqlite()
    qdrant_status = check_qdrant()

    all_ok = (
        sqlite_status["status"] == "ok"
        and qdrant_status["status"] == "ok"
    )

    return {
        "sqlite": sqlite_status,
        "qdrant": qdrant_status,
        "all_ok": all_ok,
    }


# ── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Checking databases...\n")
    status = check_databases()

    print(f"SQLite: {status['sqlite']['status']}")
    print(f"  → {status['sqlite']['message']}")
    print()
    print(f"Qdrant: {status['qdrant']['status']}")
    print(f"  → {status['qdrant']['message']}")
    print()
    print(f"All OK: {'Yes' if status['all_ok'] else 'No'}")
