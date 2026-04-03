"""
api/routes_consultation.py

Consultation endpoints for career advice and guidance.
Uses CV service and recommendation service.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, List
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.services.cv_service import analyze_cv_with_service
from backend.app.services.recommendation_service import get_job_recommendations, get_skill_gap_analysis

router = APIRouter(prefix="/api/consultation", tags=["Consultation"])
client = OpenAI(api_key=OPENAI_API_KEY)


@router.post("/career-advice")
async def get_career_advice(
    current_role: str,
    current_skills: List[str],
    target_role: Optional[str] = None,
    years_experience: int = 0
):
    """
    Get personalized career advice based on current and target roles.
    
    Args:
        current_role: Current job title
        current_skills: List of current skills
        target_role: Desired job title (optional)
        years_experience: Years of experience
    
    Returns:
        Career advice and recommendations
    """
    try:
        message = f"""
        Berikan saran karir untuk:
        - Posisi Saat Ini: {current_role}
        - Skill Saat Ini: {', '.join(current_skills)}
        - Posisi Target: {target_role or 'Belum ditentukan'}
        - Pengalaman: {years_experience} tahun
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "current_role": current_role,
            "target_role": target_role,
            "current_skills": current_skills,
            "career_advice": result.get("formatted_answer", ""),
            "recommendations": result.get("recommendations", []),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill-gap-analysis")
async def analyze_skill_gap(
    current_skills: List[str],
    target_job_id: Optional[str] = None,
    target_job_title: Optional[str] = None
):
    """
    Analyze skill gap between current and target position.
    
    Args:
        current_skills: List of current skills
        target_job_id: Target job ID from database
        target_job_title: Or target job title
    
    Returns:
        Skill gap analysis with learning recommendations
    """
    try:
        message = f"""
        Analisis skill gap untuk:
        - Skill Saat Ini: {', '.join(current_skills)}
        - Target: {target_job_title or target_job_id}
        """
        
        result = get_skill_gap_analysis(message, client)
        
        return {
            "current_skills": current_skills,
            "target_position": target_job_title or target_job_id,
            "skill_gap_analysis": result.get("formatted_answer", ""),
            "recommended_skills": result.get("recommended_skills", []),
            "learning_resources": result.get("learning_resources", []),
            "estimated_learning_time": result.get("estimated_learning_time", ""),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/salary-negotiation")
async def get_salary_negotiation_advice(
    current_salary: float,
    target_role: str,
    location: str,
    years_experience: int
):
    """
    Get salary negotiation advice based on market data.
    
    Args:
        current_salary: Current salary in IDR
        target_role: Target job title
        location: Location (city/province)
        years_experience: Years of experience
    
    Returns:
        Salary negotiation tips and market data
    """
    try:
        message = f"""
        Berikan saran negosiasi gaji untuk:
        - Gaji Saat Ini: Rp {current_salary:,.0f}
        - Posisi Target: {target_role}
        - Lokasi: {location}
        - Pengalaman: {years_experience} tahun
        Bandingkan dengan market rate dan berikan saran negosiasi.
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "current_salary": current_salary,
            "target_role": target_role,
            "location": location,
            "salary_advice": result.get("formatted_answer", ""),
            "negotiation_tips": result.get("recommendations", []),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))