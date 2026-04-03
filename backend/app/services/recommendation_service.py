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

def """
api/routes_consultation.py

Consultation endpoints for career advice and guidance.
Uses CV service and recommendation service.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.services.recommendation_service import (
    get_job_recommendations,
    get_skill_gap_analysis
)

router = APIRouter(prefix="/api/consultation", tags=["Consultation"])
client = OpenAI(api_key=OPENAI_API_KEY)


@router.post("/career-advice")
async def get_career_advice(
    current_role: str,
    current_skills: List[str],
    target_role: Optional[str] = None,
    years_experience: int = 0
) -> Dict[str, Any]:
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
        if not current_role or not current_skills:
            raise ValueError("current_role and current_skills are required")
        
        message = f"""
        Berikan saran karir untuk:
        - Posisi Saat Ini: {current_role}
        - Skill Saat Ini: {', '.join(current_skills)}
        - Posisi Target: {target_role or 'Belum ditentukan'}
        - Pengalaman: {years_experience} tahun
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "status": "success",
            "current_role": current_role,
            "target_role": target_role,
            "current_skills": current_skills,
            "years_experience": years_experience,
            "career_advice": result.get("formatted_answer", ""),
            "recommendations": result.get("recommendations", []),
            "success": True
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting career advice: {str(e)}")


@router.post("/skill-gap-analysis")
async def analyze_skill_gap(
    current_skills: List[str],
    target_job_id: Optional[str] = None,
    target_job_title: Optional[str] = None
) -> Dict[str, Any]:
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
        if not current_skills:
            raise ValueError("current_skills is required")
        
        if not target_job_id and not target_job_title:
            raise ValueError("Either target_job_id or target_job_title is required")
        
        target = target_job_title or target_job_id
        
        message = f"""
        Analisis skill gap untuk:
        - Skill Saat Ini: {', '.join(current_skills)}
        - Target: {target}
        
        Sertakan:
        1. Skill yang masih kurang
        2. Skill yang sudah dimiliki
        3. Rekomendasi pembelajaran
        4. Estimasi waktu pembelajaran
        """
        
        result = get_skill_gap_analysis(message, client)
        
        return {
            "status": "success",
            "current_skills": current_skills,
            "target_position": target,
            "skill_gap_analysis": result.get("formatted_answer", ""),
            "gap_skills": result.get("gap_skills", []),
            "matching_skills": result.get("matching_skills", []),
            "recommended_skills": result.get("recommended_skills", []),
            "learning_resources": result.get("learning_resources", []),
            "estimated_learning_time": result.get("estimated_learning_time", "3-6 months"),
            "success": True
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing skill gap: {str(e)}")


@router.post("/salary-negotiation")
async def get_salary_negotiation_advice(
    current_salary: float,
    target_role: str,
    location: str,
    years_experience: int
) -> Dict[str, Any]:
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
        if current_salary <= 0:
            raise ValueError("current_salary must be greater than 0")
        
        if not target_role or not location:
            raise ValueError("target_role and location are required")
        
        if years_experience < 0:
            raise ValueError("years_experience cannot be negative")
        
        message = f"""
        Berikan saran negosiasi gaji untuk:
        - Gaji Saat Ini: Rp {current_salary:,.0f}
        - Posisi Target: {target_role}
        - Lokasi: {location}
        - Pengalaman: {years_experience} tahun
        
        Berikan:
        1. Market rate estimate untuk posisi ini
        2. Salary range yang reasonable
        3. Tips negosiasi
        4. Faktor-faktor yang mempengaruhi
        5. Strategi presentasi
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "status": "success",
            "current_salary": current_salary,
            "target_role": target_role,
            "location": location,
            "years_experience": years_experience,
            "salary_advice": result.get("formatted_answer", ""),
            "negotiation_tips": result.get("recommendations", []),
            "market_insights": result.get("market_insights", ""),
            "success": True
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting salary negotiation advice: {str(e)}")


@router.post("/career-transition")
async def get_career_transition_advice(
    current_role: str,
    target_role: str,
    current_skills: List[str],
    years_experience: int,
    industry_switch: bool = False
) -> Dict[str, Any]:
    """
    Get advice for career transition/switch.
    
    Args:
        current_role: Current job title
        target_role: Desired job title
        current_skills: List of current skills
        years_experience: Years of experience in current role
        industry_switch: Is this an industry switch?
    
    Returns:
        Career transition advice and action plan
    """
    try:
        if not current_role or not target_role:
            raise ValueError("current_role and target_role are required")
        
        switch_type = "industri" if industry_switch else "posisi"
        
        message = f"""
        Berikan saran untuk transisi karir {switch_type}:
        - Dari: {current_role}
        - Ke: {target_role}
        - Skill Saat Ini: {', '.join(current_skills)}
        - Pengalaman: {years_experience} tahun
        
        Sertakan:
        1. Kelayakan transisi
        2. Tantangan yang mungkin dihadapi
        3. Skill yang perlu dikembangkan
        4. Langkah-langkah action plan
        5. Timeline yang reasonable
        6. Tips untuk menarik perhatian recruiter
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "status": "success",
            "transition_type": "industry_switch" if industry_switch else "role_switch",
            "from_role": current_role,
            "to_role": target_role,
            "current_skills": current_skills,
            "transition_advice": result.get("formatted_answer", ""),
            "action_plan": result.get("recommendations", []),
            "required_skills": result.get("required_skills", []),
            "success": True
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting career transition advice: {str(e)}")


@router.post("/work-life-balance-advice")
async def get_work_life_balance_advice(
    current_role: str,
    current_workload: str,  # light, moderate, heavy
    work_hours_per_week: int,
    location: str,
    job_type_preferred: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get advice on finding work-life balance in job search.
    
    Args:
        current_role: Current job title
        current_workload: light, moderate, or heavy
        work_hours_per_week: Average hours worked per week
        location: Current/preferred location
        job_type_preferred: remote, hybrid, on-site
    
    Returns:
        Work-life balance recommendations
    """
    try:
        if not current_role or not location:
            raise ValueError("current_role and location are required")
        
        if work_hours_per_week < 0:
            raise ValueError("work_hours_per_week cannot be negative")
        
        message = f"""
        Berikan saran untuk menemukan work-life balance yang lebih baik:
        - Posisi Saat Ini: {current_role}
        - Beban Kerja: {current_workload}
        - Jam Kerja/Minggu: {work_hours_per_week} jam
        - Lokasi: {location}
        - Preferensi Tipe Kerja: {job_type_preferred or 'Fleksibel'}
        
        Sertakan:
        1. Posisi-posisi yang menawarkan work-life balance lebih baik
        2. Perusahaan-perusahaan yang terkenal dengan budaya sehat
        3. Tips untuk negosiasi flexible working
        4. Red flags untuk dihindari
        5. Pertanyaan yang harus ditanyakan saat interview
        """
        
        result = get_job_recommendations(message, client)
        
        return {
            "status": "success",
            "current_workload": current_workload,
            "work_hours_per_week": work_hours_per_week,
            "job_type_preferred": job_type_preferred,
            "balance_advice": result.get("formatted_answer", ""),
            "recommended_companies": result.get("recommended_companies", []),
            "tips": result.get("recommendations", []),
            "success": True
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting work-life balance advice: {str(e)}")get_skill_gap_analysis(cv_data: dict, openai_client: OpenAI = None) -> dict:
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
