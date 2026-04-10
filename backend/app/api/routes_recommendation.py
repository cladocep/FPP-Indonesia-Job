"""
api/routes_recommendation.py

Job recommendation endpoints.
Uses recommendation service for personalized suggestions.
"""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.agents.main_agent import handle_chat

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])
client = OpenAI(api_key=OPENAI_API_KEY)


class PersonalizedRequest(BaseModel):
    current_skills: List[str]
    desired_roles: Optional[List[str]] = None
    location: Optional[str] = None
    salary_range: Optional[dict] = None
    job_type: Optional[str] = None


_JOB_REC_SYSTEM_PROMPT = """You are a job recommendation engine. Given a candidate's skills, desired roles, and location, generate realistic job listings.

Return ONLY valid JSON with this exact structure:
{
  "recommendations": [
    {
      "job_title": "...",
      "company": "...",
      "location": "...",
      "skill_match_percentage": <number 0-100>,
      "description": "one sentence about the role"
    }
  ]
}

Generate 5 relevant job listings. Make companies and titles realistic for the location provided.
Return ONLY pure JSON — no markdown, no explanation."""


@router.post("/personalized")
async def get_personalized_job_recommendations(body: PersonalizedRequest):
    """
    Get personalized job recommendations based on profile.

    Returns:
        Personalized job recommendations
    """
    try:
        prompt = (
            f"Skills: {', '.join(body.current_skills)}\n"
            f"Desired roles: {', '.join(body.desired_roles) if body.desired_roles else 'Any'}\n"
            f"Location: {body.location or 'Flexible'}\n"
            f"Job type: {body.job_type or 'All types'}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _JOB_REC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        jobs = result.get("recommendations", [])

        return {
            "recommendations": jobs,
            "total_recommendations": len(jobs),
            "filters_applied": {
                "skills": body.current_skills,
                "desired_roles": body.desired_roles,
                "location": body.location,
                "job_type": body.job_type,
            },
            "success": True,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_positions(
    location: Optional[str] = None,
    limit: int = 10
):
    """
    Get trending job positions in market.
    
    Args:
        location: Optional location filter
        limit: Number of recommendations
    
    Returns:
        Trending job positions with market insights
    """
    try:
        message = f"""
        Apa lowongan yang paling trending saat ini?
        Lokasi: {location or 'Seluruh Indonesia'}
        Berikan top {limit} posisi dengan analisis trend.
        """
        
        reply = handle_chat(message, client)

        return {
            "trending_jobs": [],
            "market_insights": reply,
            "location": location,
            "limit": limit,
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/by-skills")
async def recommend_jobs_by_skills(
    skills: List[str],
    location: Optional[str] = None,
    match_threshold: float = 0.7
):
    """
    Get job recommendations based on skills match.
    
    Args:
        skills: List of skills to match
        location: Optional location filter
        match_threshold: Minimum match score (0-1)
    
    Returns:
        Jobs matching the provided skills
    """
    try:
        message = f"""
        Cari lowongan yang cocok dengan skill: {', '.join(skills)}
        Lokasi: {location or 'Semua lokasi'}
        Tingkat kecocokan minimal: {match_threshold * 100:.0f}%
        """
        
        reply = handle_chat(message, client)

        return {
            "matching_jobs": [],
            "analysis": reply,
            "skills_used": skills,
            "location": location,
            "match_threshold": match_threshold,
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/growth-path")
async def get_career_growth_path(
    current_role: str,
    current_level: str,
    years_experience: int,
    desired_outcome: Optional[str] = None
):
    """
    Get recommended career growth path.
    
    Args:
        current_role: Current job title
        current_level: Current level (junior, mid, senior, lead)
        years_experience: Years of experience
        desired_outcome: Optional target outcome
    
    Returns:
        Career growth recommendations and learning path
    """
    try:
        message = f"""
        Berikan rekomendasi career growth path untuk:
        - Posisi Saat Ini: {current_role}
        - Level: {current_level}
        - Pengalaman: {years_experience} tahun
        """
        
        if desired_outcome:
            message += f"\n- Target: {desired_outcome}"
        
        reply = handle_chat(message, client)

        return {
            "growth_path": reply,
            "next_steps": [],
            "skill_recommendations": [],
            "current_position": {
                "role": current_role,
                "level": current_level,
                "years_experience": years_experience
            },
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))