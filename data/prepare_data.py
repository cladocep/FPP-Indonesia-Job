"""
prepare_data.py

Version 2 data preparation pipeline for Indonesian Job Dataset.

Goals:
1. Load jobs.jsonl
2. Store structured data into SQLite for SQL Agent
3. Build rich RAG documents and upload to Qdrant for RAG Agent
4. Prepare metadata useful for CV matching and career consultation

Recommended architecture:
- SQLite  -> exact filtering, sorting, analytics, comparison
- Qdrant  -> semantic retrieval, recommendation, consultation
"""

import json
import sqlite3
import re
import os
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


# ── paths & env ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "indonesian_jobs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATA_PATH = BASE_DIR / "jobs.jsonl"
DB_PATH = BASE_DIR / "jobs.db"

EMBED_MODEL = "text-embedding-3-small"
VECTOR_DIM = 1536
BATCH_SIZE = 25
QDRANT_TIMEOUT = 120


# ── configurable skills dictionary ───────────────────────────────────────────

SKILL_PATTERNS = {
    "sql": [r"\bsql\b", r"\bmysql\b", r"\bpostgresql\b", r"\bpostgres\b", r"\bsql server\b"],
    "python": [r"\bpython\b"],
    "excel": [r"\bexcel\b", r"\bmicrosoft excel\b"],
    "power bi": [r"\bpower\s?bi\b"],
    "tableau": [r"\btableau\b"],
    "looker": [r"\blooker\b", r"\blooker studio\b", r"\bdata studio\b"],
    "google sheets": [r"\bgoogle sheets\b"],
    "dashboarding": [r"\bdashboard\b", r"\bdashboarding\b", r"\breporting\b"],
    "statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "data analysis": [r"\bdata analysis\b", r"\bdata analyst\b", r"\banalytical\b"],
    "data visualization": [r"\bdata visualization\b", r"\bvisualization\b"],
    "etl": [r"\betl\b", r"\bdata pipeline\b"],
    "spark": [r"\bspark\b", r"\bpyspark\b"],
    "hadoop": [r"\bhadoop\b"],
    "aws": [r"\baws\b", r"\bamazon web services\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "azure": [r"\bazure\b"],
    "communication": [r"\bcommunication\b", r"\bcommunicate\b", r"\binterpersonal\b"],
    "presentation": [r"\bpresentation\b", r"\bpresenting\b"],
    "problem solving": [r"\bproblem solving\b", r"\bproblem-solving\b"],
    "leadership": [r"\bleadership\b", r"\blead\b", r"\bteam lead\b"],
    "project management": [r"\bproject management\b", r"\bproject manager\b"],
    "recruitment": [r"\brecruitment\b", r"\brecruiter\b", r"\btalent acquisition\b"],
    "sales": [r"\bsales\b"],
    "marketing": [r"\bmarketing\b", r"\bdigital marketing\b"],
    "customer service": [r"\bcustomer service\b", r"\bcustomer support\b"],
    "accounting": [r"\baccounting\b", r"\baccountant\b"],
    "finance": [r"\bfinance\b", r"\bfinancial\b"],
    "hr": [r"\bhuman resources\b", r"\bhr\b"],
    "canva": [r"\bcanva\b"],
    "figma": [r"\bfigma\b"],
    "javascript": [r"\bjavascript\b", r"\bjs\b"],
    "java": [r"\bjava\b"],
    "c++": [r"\bc\+\+\b"],
    "php": [r"\bphp\b"],
    "laravel": [r"\blaravel\b"],
    "react": [r"\breact\b", r"\breactjs\b", r"\breact\.js\b"],
    "node.js": [r"\bnode\.?js\b", r"\bnodejs\b"],
    "git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "english": [r"\benglish\b", r"\bfluent in english\b"],
}


# ── validation ───────────────────────────────────────────────────────────────

def validate_env():
    missing = []

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"jobs.jsonl not found at: {DATA_PATH}")


# ── helpers ──────────────────────────────────────────────────────────────────

def safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", safe_text(text)).strip()


def parse_salary(salary_str: str):
    """
    Extract min/max salary as integers (IDR) from raw salary string.
    Example:
    'Rp 5.000.000 - Rp 7.500.000' -> (5000000, 7500000)
    """
    if not salary_str or salary_str == "None":
        return None, None

    numbers = re.findall(r"[\d.]+", salary_str.replace(",", ""))
    values = []

    for n in numbers:
        cleaned = n.replace(".", "")
        if cleaned.isdigit() and len(cleaned) >= 6:
            values.append(int(cleaned))

    if not values:
        return None, None

    if len(values) == 1:
        return values[0], values[0]

    return min(values), max(values)


def normalize_work_type(work_type: str) -> str:
    text = safe_text(work_type).lower()

    if not text:
        return "unknown"

    if "intern" in text or "magang" in text:
        return "internship"
    if "part" in text or "paruh" in text:
        return "part_time"
    if "contract" in text or "kontrak" in text:
        return "contract"
    if "freelance" in text or "freelancer" in text:
        return "freelance"
    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "full" in text:
        return "full_time"

    return re.sub(r"\s+", "_", text)


def split_location(location: str):
    """
    Very simple heuristic split:
    'Jakarta Selatan, Jakarta Raya' -> ('Jakarta Selatan', 'Jakarta Raya')
    'Karawaci, Banten' -> ('Karawaci', 'Banten')
    """
    raw = safe_text(location)
    if not raw:
        return "", ""

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        city = parts[0]
        province = parts[-1]
        return city, province

    return raw, ""


def normalize_location_city(city: str) -> str:
    return normalize_whitespace(city).lower()


def normalize_location_province(province: str) -> str:
    return normalize_whitespace(province).lower()


def extract_skills(text: str) -> list[str]:
    text_lower = safe_text(text).lower()
    found = []

    for canonical_skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(canonical_skill)
                break

    return sorted(set(found))


def skills_to_csv(skills: list[str]) -> str:
    return ", ".join(skills)


def load_jsonl(path: Path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON on line {line_num}: {e}")

    return records


def build_document(record: dict, extracted_skills: list[str]) -> str:
    """
    Rich document for embedding in Qdrant.
    Designed for:
    - semantic job search
    - CV-to-job matching
    - career consultation
    """
    parts = []

    job_title = safe_text(record.get("job_title"))
    company_name = safe_text(record.get("company_name"))
    location = safe_text(record.get("location"))
    work_type = safe_text(record.get("work_type"))
    salary = safe_text(record.get("salary"))
    description = normalize_whitespace(record.get("job_description"))
    skills_text = skills_to_csv(extracted_skills)

    if job_title:
        parts.append(f"Job Title: {job_title}")
    if company_name:
        parts.append(f"Company: {company_name}")
    if location:
        parts.append(f"Location: {location}")
    if work_type:
        parts.append(f"Work Type: {work_type}")
    if salary:
        parts.append(f"Salary: {salary}")
    if skills_text:
        parts.append(f"Skills: {skills_text}")
    if description:
        parts.append(f"Description: {description}")

    return "\n".join(parts)


def get_embeddings(texts: list[str], client: OpenAI) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def safe_qdrant_upsert(
    qdrant: QdrantClient,
    collection_name: str,
    points: list[PointStruct],
    retries: int = 3,
):
    for attempt in range(1, retries + 1):
        try:
            qdrant.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )
            return
        except Exception as e:
            print(f"  Upsert failed (attempt {attempt}/{retries}): {e}")

            if attempt == retries:
                raise

            sleep_seconds = attempt * 2
            print(f"  Retrying in {sleep_seconds} seconds...")
            time.sleep(sleep_seconds)


# ── record enrichment ────────────────────────────────────────────────────────

def enrich_record(record: dict) -> dict:
    """
    Enrich original job record with normalized fields and extracted metadata.
    """
    job_title = safe_text(record.get("job_title"))
    company_name = safe_text(record.get("company_name"))
    location = safe_text(record.get("location"))
    work_type = safe_text(record.get("work_type"))
    salary_raw = safe_text(record.get("salary"))
    job_description = normalize_whitespace(record.get("job_description"))
    scrape_timestamp = safe_text(record.get("_scrape_timestamp"))

    salary_min, salary_max = parse_salary(salary_raw)
    city, province = split_location(location)
    city_norm = normalize_location_city(city)
    province_norm = normalize_location_province(province)
    work_type_norm = normalize_work_type(work_type)
    skills = extract_skills(job_description)
    document = build_document(record, skills)

    return {
        "job_title": job_title,
        "company_name": company_name,
        "location": location,
        "location_city": city,
        "location_province": province,
        "location_city_norm": city_norm,
        "location_province_norm": province_norm,
        "work_type": work_type,
        "work_type_normalized": work_type_norm,
        "salary_raw": salary_raw,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "job_description": job_description,
        "skills_list": skills,
        "skills_csv": skills_to_csv(skills),
        "scrape_timestamp": scrape_timestamp,
        "document": document,
    }


# ── SQLite ───────────────────────────────────────────────────────────────────

def setup_sqlite(enriched_records: list[dict]):
    print(f"Setting up SQLite at {DB_PATH} ...")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS jobs")
    cur.execute("""
        CREATE TABLE jobs (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title                TEXT,
            company_name             TEXT,
            location                 TEXT,
            location_city            TEXT,
            location_province        TEXT,
            location_city_norm       TEXT,
            location_province_norm   TEXT,
            work_type                TEXT,
            work_type_normalized     TEXT,
            salary_raw               TEXT,
            salary_min               INTEGER,
            salary_max               INTEGER,
            job_description          TEXT,
            skills                   TEXT,
            scrape_timestamp         TEXT,
            document                 TEXT
        )
    """)

    rows = []
    for r in enriched_records:
        rows.append((
            r["job_title"],
            r["company_name"],
            r["location"],
            r["location_city"],
            r["location_province"],
            r["location_city_norm"],
            r["location_province_norm"],
            r["work_type"],
            r["work_type_normalized"],
            r["salary_raw"],
            r["salary_min"],
            r["salary_max"],
            r["job_description"],
            r["skills_csv"],
            r["scrape_timestamp"],
            r["document"],
        ))

    cur.executemany("""
        INSERT INTO jobs (
            job_title,
            company_name,
            location,
            location_city,
            location_province,
            location_city_norm,
            location_province_norm,
            work_type,
            work_type_normalized,
            salary_raw,
            salary_min,
            salary_max,
            job_description,
            skills,
            scrape_timestamp,
            document
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    # Helpful indexes for SQL Agent
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(job_title)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_city_norm ON jobs(location_city_norm)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_province_norm ON jobs(location_province_norm)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_work_type_norm ON jobs(work_type_normalized)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_salary_min ON jobs(salary_min)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_salary_max ON jobs(salary_max)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_timestamp ON jobs(scrape_timestamp)")

    conn.commit()
    conn.close()

    print(f"  Inserted {len(rows)} rows into jobs table.")


# ── Qdrant ───────────────────────────────────────────────────────────────────

def recreate_qdrant_collection(qdrant: QdrantClient):
    print("Setting up Qdrant collection ...")

    existing_collections = [c.name for c in qdrant.get_collections().collections]

    if QDRANT_COLLECTION in existing_collections:
        qdrant.delete_collection(QDRANT_COLLECTION)
        print(f"  Deleted existing collection '{QDRANT_COLLECTION}'.")

    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )

    print(f"  Created collection '{QDRANT_COLLECTION}'.")


def setup_qdrant(enriched_records: list[dict]):
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=QDRANT_TIMEOUT,
    )

    recreate_qdrant_collection(qdrant)

    total_records = len(enriched_records)
    total_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
    uploaded_count = 0

    for batch_idx, start_idx in enumerate(range(0, total_records, BATCH_SIZE), start=1):
        batch = enriched_records[start_idx:start_idx + BATCH_SIZE]
        docs = [r["document"] for r in batch]
        embeddings = get_embeddings(docs, openai_client)

        points = []
        for offset, (record, emb) in enumerate(zip(batch, embeddings)):
            point_id = start_idx + offset

            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "job_title": record["job_title"],
                        "company_name": record["company_name"],
                        "location": record["location"],
                        "location_city": record["location_city"],
                        "location_province": record["location_province"],
                        "location_city_norm": record["location_city_norm"],
                        "location_province_norm": record["location_province_norm"],
                        "work_type": record["work_type"],
                        "work_type_normalized": record["work_type_normalized"],
                        "salary_raw": record["salary_raw"],
                        "salary_min": record["salary_min"],
                        "salary_max": record["salary_max"],
                        "job_description": record["job_description"],
                        "skills": record["skills_list"],
                        "skills_csv": record["skills_csv"],
                        "scrape_timestamp": record["scrape_timestamp"],
                        "document": record["document"],
                    },
                )
            )

        print(f"  Embedding batch {batch_idx}/{total_batches} ({len(batch)} records)...")
        safe_qdrant_upsert(qdrant, QDRANT_COLLECTION, points)

        uploaded_count += len(points)
        print(f"  Uploaded batch {batch_idx}/{total_batches} | total uploaded: {uploaded_count}")

    print(f"  Uploaded {uploaded_count} vectors to Qdrant.")


# ── diagnostics ──────────────────────────────────────────────────────────────

def print_summary(enriched_records: list[dict]):
    total = len(enriched_records)
    with_salary = sum(1 for r in enriched_records if r["salary_min"] is not None or r["salary_max"] is not None)
    with_skills = sum(1 for r in enriched_records if r["skills_list"])
    full_time = sum(1 for r in enriched_records if r["work_type_normalized"] == "full_time")
    internship = sum(1 for r in enriched_records if r["work_type_normalized"] == "internship")

    print("\nSummary")
    print(f"  Total records: {total}")
    print(f"  Records with parsed salary: {with_salary}")
    print(f"  Records with extracted skills: {with_skills}")
    print(f"  Full-time jobs: {full_time}")
    print(f"  Internship jobs: {internship}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    validate_env()

    raw_records = load_jsonl(DATA_PATH)
    print(f"Loaded {len(raw_records)} records from {DATA_PATH}")

    if not raw_records:
        raise ValueError("No valid records found in jobs.jsonl")

    enriched_records = [enrich_record(r) for r in raw_records]

    setup_sqlite(enriched_records)
    setup_qdrant(enriched_records)
    print_summary(enriched_records)

    print("\nData preparation complete!")
    print(f"  SQLite: {DB_PATH}")
    print(f"  Qdrant: {QDRANT_URL} / collection '{QDRANT_COLLECTION}'")


if __name__ == "__main__":
    main()