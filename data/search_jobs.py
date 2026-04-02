"""
search_jobs.py

Version 2 search utilities for Indonesian Job Dataset.

Main purposes:
1. Structured search for SQL Agent
2. Job browser filters for Streamlit
3. Compare selected jobs
4. Insights / analytics queries

Designed to match prepare_data.py v2 schema.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Any


# ── paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "jobs.db"


# ── connection helpers ───────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite DB not found at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


def normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    return str(text).strip().lower()


# ── basic lookups for UI filters ─────────────────────────────────────────────

def get_distinct_cities(limit: int = 200) -> list[str]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT location_city
        FROM jobs
        WHERE location_city IS NOT NULL
          AND TRIM(location_city) != ''
        ORDER BY location_city ASC
        LIMIT ?
    """, (limit,))

    rows = [row["location_city"] for row in cur.fetchall()]
    conn.close()
    return rows


def get_distinct_provinces(limit: int = 200) -> list[str]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT location_province
        FROM jobs
        WHERE location_province IS NOT NULL
          AND TRIM(location_province) != ''
        ORDER BY location_province ASC
        LIMIT ?
    """, (limit,))

    rows = [row["location_province"] for row in cur.fetchall()]
    conn.close()
    return rows


def get_distinct_work_types(limit: int = 50) -> list[str]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT work_type_normalized
        FROM jobs
        WHERE work_type_normalized IS NOT NULL
          AND TRIM(work_type_normalized) != ''
        ORDER BY work_type_normalized ASC
        LIMIT ?
    """, (limit,))

    rows = [row["work_type_normalized"] for row in cur.fetchall()]
    conn.close()
    return rows


# ── main browser search ──────────────────────────────────────────────────────

def search_jobs(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    work_type: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    sort_by: str = "newest",
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Main structured job search for Job Browser tab.

    Supported filters:
    - keyword: searches title, company, description, skills
    - city
    - province
    - work_type (normalized)
    - min_salary / max_salary
    - sort_by: newest | highest_salary | lowest_salary | title_az
    """

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            id,
            job_title,
            company_name,
            location,
            location_city,
            location_province,
            work_type,
            work_type_normalized,
            salary_raw,
            salary_min,
            salary_max,
            job_description,
            skills,
            scrape_timestamp,
            document
        FROM jobs
        WHERE 1=1
    """
    params: list[Any] = []

    if keyword:
        keyword_like = f"%{keyword.strip().lower()}%"
        query += """
            AND (
                LOWER(job_title) LIKE ?
                OR LOWER(company_name) LIKE ?
                OR LOWER(job_description) LIKE ?
                OR LOWER(skills) LIKE ?
            )
        """
        params.extend([keyword_like, keyword_like, keyword_like, keyword_like])

    if city:
        query += " AND location_city_norm = ?"
        params.append(normalize_text(city))

    if province:
        query += " AND location_province_norm = ?"
        params.append(normalize_text(province))

    if work_type:
        query += " AND work_type_normalized = ?"
        params.append(normalize_text(work_type))

    if min_salary is not None:
        query += " AND salary_max IS NOT NULL AND salary_max >= ?"
        params.append(min_salary)

    if max_salary is not None:
        query += " AND salary_min IS NOT NULL AND salary_min <= ?"
        params.append(max_salary)

    if sort_by == "highest_salary":
        query += """
            ORDER BY
                salary_max DESC,
                scrape_timestamp DESC
        """
    elif sort_by == "lowest_salary":
        query += """
            ORDER BY
                salary_min ASC,
                scrape_timestamp DESC
        """
    elif sort_by == "title_az":
        query += """
            ORDER BY
                job_title ASC,
                scrape_timestamp DESC
        """
    else:
        query += """
            ORDER BY
                scrape_timestamp DESC,
                salary_max DESC
        """

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


def count_search_jobs(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    work_type: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
) -> int:
    """
    Count results for pagination / UI info.
    """

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT COUNT(*) AS total FROM jobs WHERE 1=1"
    params: list[Any] = []

    if keyword:
        keyword_like = f"%{keyword.strip().lower()}%"
        query += """
            AND (
                LOWER(job_title) LIKE ?
                OR LOWER(company_name) LIKE ?
                OR LOWER(job_description) LIKE ?
                OR LOWER(skills) LIKE ?
            )
        """
        params.extend([keyword_like, keyword_like, keyword_like, keyword_like])

    if city:
        query += " AND location_city_norm = ?"
        params.append(normalize_text(city))

    if province:
        query += " AND location_province_norm = ?"
        params.append(normalize_text(province))

    if work_type:
        query += " AND work_type_normalized = ?"
        params.append(normalize_text(work_type))

    if min_salary is not None:
        query += " AND salary_max IS NOT NULL AND salary_max >= ?"
        params.append(min_salary)

    if max_salary is not None:
        query += " AND salary_min IS NOT NULL AND salary_min <= ?"
        params.append(max_salary)

    cur.execute(query, params)
    total = cur.fetchone()["total"]
    conn.close()

    return total


# ── direct fetch / compare ───────────────────────────────────────────────────

def get_job_by_id(job_id: int) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            job_title,
            company_name,
            location,
            location_city,
            location_province,
            work_type,
            work_type_normalized,
            salary_raw,
            salary_min,
            salary_max,
            job_description,
            skills,
            scrape_timestamp,
            document
        FROM jobs
        WHERE id = ?
    """, (job_id,))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


def get_jobs_by_ids(job_ids: list[int]) -> list[dict]:
    if not job_ids:
        return []

    placeholders = ",".join("?" for _ in job_ids)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            id,
            job_title,
            company_name,
            location,
            location_city,
            location_province,
            work_type,
            work_type_normalized,
            salary_raw,
            salary_min,
            salary_max,
            job_description,
            skills,
            scrape_timestamp,
            document
        FROM jobs
        WHERE id IN ({placeholders})
        ORDER BY id ASC
    """, job_ids)

    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


# ── insights / analytics ─────────────────────────────────────────────────────

def get_total_jobs() -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM jobs")
    total = cur.fetchone()["total"]
    conn.close()

    return total


def get_salary_availability_rate() -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_jobs,
            SUM(
                CASE
                    WHEN salary_min IS NOT NULL OR salary_max IS NOT NULL THEN 1
                    ELSE 0
                END
            ) AS jobs_with_salary
        FROM jobs
    """)

    row = cur.fetchone()
    conn.close()

    total_jobs = row["total_jobs"] or 0
    jobs_with_salary = row["jobs_with_salary"] or 0
    rate = (jobs_with_salary / total_jobs * 100) if total_jobs else 0

    return {
        "total_jobs": total_jobs,
        "jobs_with_salary": jobs_with_salary,
        "salary_availability_rate": round(rate, 2),
    }


def get_top_locations(limit: int = 10) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            location_city,
            COUNT(*) AS job_count
        FROM jobs
        WHERE location_city IS NOT NULL
          AND TRIM(location_city) != ''
        GROUP BY location_city
        ORDER BY job_count DESC, location_city ASC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


def get_top_provinces(limit: int = 10) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            location_province,
            COUNT(*) AS job_count
        FROM jobs
        WHERE location_province IS NOT NULL
          AND TRIM(location_province) != ''
        GROUP BY location_province
        ORDER BY job_count DESC, location_province ASC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


def get_top_companies(limit: int = 10) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            company_name,
            COUNT(*) AS job_count
        FROM jobs
        WHERE company_name IS NOT NULL
          AND TRIM(company_name) != ''
        GROUP BY company_name
        ORDER BY job_count DESC, company_name ASC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


def get_work_type_distribution() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            work_type_normalized,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY work_type_normalized
        ORDER BY job_count DESC, work_type_normalized ASC
    """)

    rows = cur.fetchall()
    conn.close()

    return rows_to_dicts(rows)


def get_top_skills(limit: int = 15) -> list[dict]:
    """
    Reads skills from CSV text column and counts them in Python.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT skills
        FROM jobs
        WHERE skills IS NOT NULL
          AND TRIM(skills) != ''
    """)

    rows = cur.fetchall()
    conn.close()

    counts: dict[str, int] = {}

    for row in rows:
        skills_text = row["skills"] or ""
        skills = [s.strip() for s in skills_text.split(",") if s.strip()]
        unique_skills = set(skills)

        for skill in unique_skills:
            counts[skill] = counts.get(skill, 0) + 1

    sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    return [{"skill": skill, "job_count": count} for skill, count in sorted_items[:limit]]


# ── utility helpers for app display ──────────────────────────────────────────

def shorten_text(text: Optional[str], max_length: int = 300) -> str:
    text = (text or "").strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def format_salary_range(job: dict) -> str:
    if job.get("salary_raw"):
        return job["salary_raw"]

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")

    if salary_min is not None and salary_max is not None:
        return f"Rp {salary_min:,} - Rp {salary_max:,}"
    if salary_min is not None:
        return f"Rp {salary_min:,}+"
    if salary_max is not None:
        return f"Up to Rp {salary_max:,}"

    return "Not disclosed"


def format_job_card(job: dict, description_length: int = 220) -> str:
    parts = [
        f"ID: {job.get('id')}",
        f"Title: {job.get('job_title', '-')}",
        f"Company: {job.get('company_name', '-')}",
        f"Location: {job.get('location', '-')}",
        f"Work Type: {job.get('work_type', '-')}",
        f"Salary: {format_salary_range(job)}",
        f"Skills: {job.get('skills', '-') or '-'}",
        f"Scraped At: {job.get('scrape_timestamp', '-')}",
    ]

    description = shorten_text(job.get("job_description", ""), max_length=description_length)
    if description:
        parts.append(f"Description: {description}")

    return "\n".join(parts)


def format_job_cards(jobs: list[dict], description_length: int = 220) -> str:
    if not jobs:
        return "No jobs found."

    chunks = []
    for i, job in enumerate(jobs, start=1):
        chunks.append(f"[{i}]\n{format_job_card(job, description_length=description_length)}")

    return "\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(chunks)


# ── quick manual test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Total jobs ===")
    print(get_total_jobs())

    print("\n=== Distinct work types ===")
    print(get_distinct_work_types())

    print("\n=== Search jobs: data + jakarta ===")
    jobs = search_jobs(
        keyword="data",
        city="jakarta selatan",
        sort_by="newest",
        limit=5,
    )
    print(format_job_cards(jobs))

    print("\n=== Top companies ===")
    print(get_top_companies(limit=10))

    print("\n=== Top skills ===")
    print(get_top_skills(limit=10))

    print("\n=== Salary availability ===")
    print(get_salary_availability_rate())