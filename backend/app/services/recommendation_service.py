"""
services/recommendation_service.py

Recommendation Service

Orchestrates job recommendations and career consultations using the CV Agent's
matching logic. Acts as the service layer between API routes and the CV Agent.
"""

from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.agents.cv_agent import (
    find_matching_jobs,
    rank_jobs_with_skill_match,
    format_cv_summary,
    handle_cv_query,
)


# ── job recommendations ───────────────────────────────────────────────────────

def get_job_recommendations(cv_data: dict, top_n: int = 5) -> dict:
    """
    Given parsed CV data, find and rank the best matching jobs.

    Args:
        cv_data: Structured CV dict (from cv_service.parse_cv)
        top_n:   Number of top jobs to return

    Returns:
        {
            "cv_summary": str,
            "top_jobs": [
                {
                    "rank": int,
                    "job_title": str,
                    "company_name": str,
                    "location": str,
                    "work_type": str,
                    "salary_raw": str,
                    "skill_match_percentage": float,
                    "matched_skills": list[str],
                    "missing_skills": list[str],
                    "combined_score": float,
                },
                ...
            ],
            "total_found": int,
        }
    """
    cv_summary = format_cv_summary(cv_data)

    # Fetch more candidates than needed so ranking has good material to work with
    search_results = find_matching_jobs(cv_data, top_k=max(top_n * 3, 10))

    # Re-rank by combined semantic + skill-match score
    ranked_jobs = rank_jobs_with_skill_match(cv_data, search_results, top_n=top_n)

    top_jobs = []
    for i, job in enumerate(ranked_jobs, 1):
        match = job["skill_match"]
        top_jobs.append({
            "rank": i,
            "job_title": job["job_title"],
            "company_name": job["company_name"],
            "location": job["location"],
            "work_type": job["work_type"],
            "salary_raw": job["salary_raw"],
            "skill_match_percentage": match["match_percentage"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "combined_score": job["combined_score"],
        })

    return {
        "cv_summary": cv_summary,
        "top_jobs": top_jobs,
        "total_found": len(search_results),
    }


# ── skill gap analysis ────────────────────────────────────────────────────────

def get_skill_gap_analysis(cv_data: dict, openai_client: OpenAI = None) -> dict:
    """
    Analyse which skills the candidate is missing relative to the top matching jobs.

    Returns:
        {
            "user_skills": list[str],
            "top_jobs": list[dict],
            "common_missing_skills": [{"skill": str, "frequency": int}, ...],
            "llm_advice": str,
        }
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    recommendations = get_job_recommendations(cv_data, top_n=5)

    # Count how often each missing skill appears across the top jobs
    missing_counts: dict[str, int] = {}
    for job in recommendations["top_jobs"]:
        for skill in job["missing_skills"]:
            missing_counts[skill] = missing_counts.get(skill, 0) + 1

    common_missing = sorted(
        [{"skill": s, "frequency": c} for s, c in missing_counts.items()],
        key=lambda x: x["frequency"],
        reverse=True,
    )[:10]

    llm_advice = handle_cv_query(
        user_message="Tolong analisis skill gap saya dan berikan saran pengembangan karir.",
        cv_data=cv_data,
        openai_client=openai_client,
    )

    return {
        "user_skills": cv_data.get("skills", []),
        "top_jobs": recommendations["top_jobs"],
        "common_missing_skills": common_missing,
        "llm_advice": llm_advice,
    }


# ── career consultation ───────────────────────────────────────────────────────

def get_career_consultation(
    cv_data: dict,
    user_question: str = "",
    openai_client: OpenAI = None,
) -> str:
    """
    Generate a personalised career consultation response based on CV data.

    Args:
        cv_data:       Structured CV dict
        user_question: The user's specific question (optional)
        openai_client: Reuse an existing OpenAI client (optional)

    Returns:
        LLM-generated consultation text (str)
    """
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

    message = user_question or "Berikan saran karir berdasarkan CV saya."
    return handle_cv_query(
        user_message=message,
        cv_data=cv_data,
        openai_client=openai_client,
    )
