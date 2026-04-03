"""
api/routes_recommendation.py

Job recommendation endpoints.
Uses recommendation service for personalized suggestions.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.services.recommendation_service import (
    get_job_recommendations,
    get_personalized_recommendations,
    get_trending_jobs,
    get_skill_gap_analysis
)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])
client = OpenAI(api_key=OPENAI_API_KEY)


@router.post("/personalized")
async def get_personalized_job_recommendations(
    current_skills: List[str],
    desired_roles: Optional[List[str]] = None,
    location: Optional[str] = None,
    salary_range: Optional[dict] = None,
    job_type: Optional[str] = None
):
    """
    Get personalized job recommendations based on profile.
    
    Args:
        current_skills: List of current skills
        desired_roles: Preferred job titles
        location: Preferred location
        salary_range: {"min": int, "max": int} in IDR
        job_type: Full-time, part-time, remote, etc
    
    Returns:
        Personalized job recommendations
    """
    try:
        message = f"""
        Rekomendasikan lowongan yang sesuai untuk:
        - Skill Saat Ini: {', '.join(current_skills)}
        - Posisi yang Diinginkan: {', '.join(desired_roles) if desired_roles else 'Terbuka'}
        - Lokasi: {location or 'Fleksibel'}
        - Tipe Kerja: {job_type or 'Semua tipe'}
        """
        
        if salary_range:
            message += f"\n- Range Gaji: Rp {salary_range.get('min', 0):,} - Rp {salary_range.get('max', 0):,}"
        
        result = get_personalized_recommendations(message, client)
        
        return {
            "recommendations": result.get("recommendations", []),
            "recommendation_analysis": result.get("formatted_answer", ""),
            "total_recommendations": len(result.get("recommendations", [])),
            "filters_applied": {
                "skills": current_skills,
                "desired_roles": desired_roles,
                "location": location,
                "salary_range": salary_range,
                "job_type": job_type
            },
            "success": result.get("success", False)
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
        
        result = get_trending_jobs(message, client)
        
        return {
            "trending_jobs": result.get("trending_jobs", []),
            "market_insights": result.get("formatted_answer", ""),
            "location": location,
            "limit": limit,
            "success": result.get("success", False)
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
        
        result = get_job_recommendations(message, client)
        
        return {
            "matching_jobs": result.get("recommendations", []),
            "analysis": result.get("formatted_answer", ""),
            "skills_used": skills,
            "location": location,
            "match_threshold": match_threshold,
            "success": result.get("success", False)
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
        
        result = get_job_recommendations(message, client)
        
        return {
            "growth_path": result.get("formatted_answer", ""),
            "next_steps": result.get("recommendations", []),
            "skill_recommendations": result.get("skill_recommendations", []),
            "current_position": {
                "role": current_role,
                "level": current_level,
                "years_experience": years_experience
            },
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))