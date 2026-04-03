"""
agents/cv_agent.py

CV Agent (Job Recommendation & Career Consultation)

Flow:
1. Receive parsed CV data (from Orang 1's parser)
2. Use skills to search matching jobs in Qdrant
3. Calculate skill match percentage
4. Generate career consultation with LLM

Handles:
- "Rekomendasikan pekerjaan berdasarkan CV saya"
- "Analisis skill gap saya"
- "Berikan saran karir berdasarkan pengalaman saya"
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY, LLM_MODEL
from backend.app.database.qdrant_client import search_qdrant


# ── prompts ──────────────────────────────────────────────────────────────────

RECOMMENDATION_PROMPT = """You are a career advisor for an Indonesian Job Search platform.

The user has these skills and profile from their CV:
{cv_summary}

Here are the top matching job listings found:
{matching_jobs}

Skill match results:
{match_results}

Your task:
1. Present the Top 3 most suitable jobs with clear reasoning WHY each job fits.
2. For each job, show: Job Title, Company, Location, Skill Match %, and a brief explanation.
3. Highlight which of the user's skills are most valuable.
4. Respond in the same language the user uses (Indonesian or English).
5. Be encouraging but honest about the match quality."""

CONSULTATION_PROMPT = """You are an experienced career consultant for an Indonesian Job Search platform.

The user has these skills and profile from their CV:
{cv_summary}

Based on the current job market data:
{market_context}

Skill match analysis:
{match_results}

Your task:
1. Identify the user's SKILL GAPS — what skills are they missing for their target roles?
2. Suggest specific learning paths or resources for each gap.
3. Recommend a realistic career path (short-term: 6 months, long-term: 2 years).
4. Be supportive and actionable — give concrete steps, not vague advice.
5. Respond in the same language the user uses (Indonesian or English)."""


# ── skill matching ───────────────────────────────────────────────────────────

def calculate_skill_match(user_skills: list[str], job_skills: list[str]) -> dict:
    """
    Calculate skill match percentage between user and job.

    Returns dict with:
        - match_percentage: float
        - matched_skills: list of matching skills
        - missing_skills: list of skills user doesn't have
    """
    if not job_skills:
        return {
            "match_percentage": 0.0,
            "matched_skills": [],
            "missing_skills": [],
        }

    user_skills_lower = {s.lower().strip() for s in user_skills}
    job_skills_lower = {s.lower().strip() for s in job_skills}

    matched = user_skills_lower & job_skills_lower
    missing = job_skills_lower - user_skills_lower

    percentage = (len(matched) / len(job_skills_lower)) * 100 if job_skills_lower else 0

    return {
        "match_percentage": round(percentage, 1),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
    }


def format_cv_summary(cv_data: dict) -> str:
    """Format CV data into a readable summary for the LLM."""
    parts = []

    if cv_data.get("name"):
        parts.append(f"Name: {cv_data['name']}")
    if cv_data.get("skills"):
        parts.append(f"Skills: {', '.join(cv_data['skills'])}")
    if cv_data.get("experience"):
        parts.append(f"Experience: {cv_data['experience']}")
    if cv_data.get("education"):
        parts.append(f"Education: {cv_data['education']}")
    if cv_data.get("summary"):
        parts.append(f"Summary: {cv_data['summary']}")

    return "\n".join(parts) if parts else "No CV data provided."


# ── job matching with Qdrant ─────────────────────────────────────────────────

def find_matching_jobs(cv_data: dict, top_k: int = 10) -> list[dict]:
    """
    Search Qdrant for jobs that match the user's CV skills.
    Uses the skills as a semantic search query.
    """
    # Build search query from CV skills and experience
    search_parts = []
    if cv_data.get("skills"):
        search_parts.append(" ".join(cv_data["skills"]))
    if cv_data.get("experience"):
        search_parts.append(str(cv_data["experience"]))

    search_query = " ".join(search_parts) if search_parts else "job opening"

    results = search_qdrant(query=search_query, top_k=top_k)
    return results


def rank_jobs_with_skill_match(
    cv_data: dict,
    search_results: list[dict],
    top_n: int = 3,
) -> list[dict]:
    """
    Rank jobs by combining semantic score + skill match percentage.
    Returns top N jobs with match details.
    """
    user_skills = cv_data.get("skills", [])
    ranked = []

    for result in search_results:
        payload = result["payload"]
        semantic_score = result["score"]

        # Get job skills (stored as list in Qdrant payload)
        job_skills = payload.get("skills", [])
        if isinstance(job_skills, str):
            job_skills = [s.strip() for s in job_skills.split(",") if s.strip()]

        # Calculate skill match
        match = calculate_skill_match(user_skills, job_skills)

        # Combined score: 60% semantic + 40% skill match
        combined_score = (semantic_score * 0.6) + (match["match_percentage"] / 100 * 0.4)

        ranked.append({
            "job_title": payload.get("job_title", "Unknown"),
            "company_name": payload.get("company_name", "Unknown"),
            "location": payload.get("location", "Unknown"),
            "work_type": payload.get("work_type", "Unknown"),
            "salary_raw": payload.get("salary_raw", "Not disclosed"),
            "job_skills": job_skills,
            "semantic_score": round(semantic_score, 3),
            "skill_match": match,
            "combined_score": round(combined_score, 3),
        })

    # Sort by combined score
    ranked.sort(key=lambda x: x["combined_score"], reverse=True)
    return ranked[:top_n]


# ── format match results for LLM ────────────────────────────────────────────

def format_match_results(ranked_jobs: list[dict]) -> str:
    """Format ranked jobs into readable text for LLM prompt."""
    if not ranked_jobs:
        return "No matching jobs found."

    parts = []
    for i, job in enumerate(ranked_jobs, 1):
        match = job["skill_match"]
        parts.append(
            f"Job {i}:\n"
            f"  Title: {job['job_title']}\n"
            f"  Company: {job['company_name']}\n"
            f"  Location: {job['location']}\n"
            f"  Work Type: {job['work_type']}\n"
            f"  Salary: {job['salary_raw']}\n"
            f"  Skill Match: {match['match_percentage']}%\n"
            f"  Matched Skills: {', '.join(match['matched_skills']) or 'None'}\n"
            f"  Missing Skills: {', '.join(match['missing_skills']) or 'None'}"
        )

    return "\n\n".join(parts)


# ── main handler ─────────────────────────────────────────────────────────────

def handle_cv_query(
    user_message: str,
    cv_data: dict = None,
    openai_client: OpenAI = None,
) -> str:
    """
    Handle CV-related queries.

    If cv_data is provided → job recommendation + career consultation
    If only user_message → career advice based on conversation
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # If no CV data, give general career advice
    if not cv_data:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a career advisor. The user is asking about career-related topics "
                        "but hasn't uploaded their CV yet. Encourage them to upload their CV "
                        "for personalized recommendations. Answer their question helpfully. "
                        "Respond in the same language they use."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        return response.choices[0].message.content

    # ── Full CV analysis flow ────────────────────────────────────────────

    print(f"[CV Agent] Processing CV with {len(cv_data.get('skills', []))} skills...")

    cv_summary = format_cv_summary(cv_data)

    # Step 1: Find matching jobs from Qdrant
    search_results = find_matching_jobs(cv_data, top_k=10)

    # Step 2: Rank with skill match
    ranked_jobs = rank_jobs_with_skill_match(cv_data, search_results, top_n=3)

    # Step 3: Format results
    match_results = format_match_results(ranked_jobs)
    matching_jobs_text = "\n".join(
        f"- {r['payload'].get('document', '')[:300]}"
        for r in search_results[:5]
    )

    # Step 4: Determine if user wants recommendation or consultation
    is_consultation = any(
        keyword in user_message.lower()
        for keyword in [
            "konsultasi", "saran", "advice", "skill gap",
            "karir", "career", "rekomendasi belajar", "learning path",
            "consultation",
        ]
    )

    if is_consultation:
        prompt = CONSULTATION_PROMPT.format(
            cv_summary=cv_summary,
            market_context=matching_jobs_text,
            match_results=match_results,
        )
    else:
        prompt = RECOMMENDATION_PROMPT.format(
            cv_summary=cv_summary,
            matching_jobs=matching_jobs_text,
            match_results=match_results,
        )

    # Step 5: Generate response with LLM
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=1500,
    )

    return response.choices[0].message.content
