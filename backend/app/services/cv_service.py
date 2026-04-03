"""
services/cv_service.py

CV Parsing Service

Flow:
1. Accept raw file bytes (PDF, DOCX, TXT)
2. Extract plain text from the file
3. Use LLM to extract structured fields: name, skills, experience, education, summary
4. Return a structured dict ready for the CV Agent
"""

import io
import json
from pathlib import Path

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, LLM_MODEL


# ── text extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pdfplumber (falls back to PyPDF2)."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except ImportError:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX bytes using python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route file to the correct text extractor based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace").strip()
    else:
        raise ValueError(f"Unsupported file type: '{ext}'. Supported: .pdf, .docx, .doc, .txt")


# ── LLM-based structured extraction ──────────────────────────────────────────

_EXTRACTION_SYSTEM_PROMPT = """You are a CV/resume parser. Extract structured information from the CV text provided.

Return ONLY valid JSON with these exact fields:
{
  "name": "Full name of the candidate",
  "email": "email address or null",
  "phone": "phone number or null",
  "location": "city/country or null",
  "summary": "Professional summary or objective (1-3 sentences)",
  "skills": ["list", "of", "individual", "skill", "strings"],
  "experience": "Short description of work experience (e.g. '3 years as Backend Developer at fintech companies')",
  "education": "Highest education level and institution (e.g. 'S1 Computer Science, Universitas Indonesia')",
  "certifications": ["list of certifications or empty list"],
  "languages": ["list of spoken languages or empty list"]
}

Rules:
- skills must be a flat list of individual skill strings (e.g. ["Python", "SQL", "FastAPI", "Docker"])
- Do NOT group skills — each skill is its own string
- If a field is not found, use null for strings or [] for lists
- Return ONLY pure JSON — no markdown, no explanation"""


def parse_cv_with_llm(raw_text: str, openai_client: OpenAI = None) -> dict:
    """
    Use OpenAI to extract structured CV data from raw text.

    Returns a dict with: name, email, phone, location, summary,
                         skills, experience, education, certifications, languages
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Truncate to avoid token limits — most CVs fit in 6000 chars
    truncated_text = raw_text[:6000] if len(raw_text) > 6000 else raw_text

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this CV:\n\n{truncated_text}"},
        ],
        temperature=0.0,
        max_tokens=1000,
        response_format={"type": "json_object"},
    )

    parsed = json.loads(response.choices[0].message.content)

    # Normalize skills — always a clean list of strings
    if not isinstance(parsed.get("skills"), list):
        parsed["skills"] = []
    parsed["skills"] = [str(s).strip() for s in parsed["skills"] if s]

    return parsed


# ── main entrypoint ───────────────────────────────────────────────────────────

def parse_cv(file_bytes: bytes, filename: str, openai_client: OpenAI = None) -> dict:
    """
    Full CV parsing pipeline:
      1. Extract raw text from the uploaded file
      2. Use LLM to extract structured fields
      3. Return structured CV dict

    Returns dict with keys:
        name, email, phone, location, summary, skills,
        experience, education, certifications, languages, raw_text

    Raises:
        ValueError: if file type is unsupported or no text could be extracted
    """
    raw_text = extract_text(file_bytes, filename)

    if not raw_text:
        raise ValueError("Could not extract any text from the uploaded CV file.")

    cv_data = parse_cv_with_llm(raw_text, openai_client)
    cv_data["raw_text"] = raw_text  # keep for reference / re-parsing

    print(
        f"[CV Service] Parsed: {cv_data.get('name', 'Unknown')} | "
        f"{len(cv_data.get('skills', []))} skills extracted"
    )
    return cv_data
