"""
api/routes_cv.py

CV analysis and improvement endpoints.
Uses CV service for document analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, List
from openai import OpenAI

from backend.app.config import OPENAI_API_KEY
from backend.app.services.cv_service import (
    analyze_cv_with_service,
    get_cv_improvement_suggestions,
    match_cv_to_jobs
)

router = APIRouter(prefix="/api/cv", tags=["CV"])
client = OpenAI(api_key=OPENAI_API_KEY)


@router.post("/analyze")
async def analyze_cv(
    file: UploadFile = File(...),
    job_title: Optional[str] = None
):
    """
    Analyze uploaded CV/Resume.
    
    Args:
        file: PDF or text file of CV
        job_title: Optional target job title for context
    
    Returns:
        CV analysis with scores and insights
    """
    try:
        contents = await file.read()
        filename = file.filename
        
        # Decode file content
        try:
            cv_text = contents.decode('utf-8')
        except:
            cv_text = contents.decode('latin-1')
        
        # Analyze CV
        result = analyze_cv_with_service(cv_text, client, job_title)
        
        return {
            "filename": filename,
            "overall_score": result.get("overall_score", 0),
            "analysis": result.get("formatted_answer", ""),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "keywords_found": result.get("keywords_found", []),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve")
async def get_cv_improvements(
    file: UploadFile = File(...),
    job_title: Optional[str] = None,
    industry: Optional[str] = None
):
    """
    Get specific suggestions to improve CV.
    
    Args:
        file: PDF or text file of CV
        job_title: Target job title for context
        industry: Industry/field
    
    Returns:
        Detailed improvement suggestions
    """
    try:
        contents = await file.read()
        
        try:
            cv_text = contents.decode('utf-8')
        except:
            cv_text = contents.decode('latin-1')
        
        # Get improvement suggestions
        result = get_cv_improvement_suggestions(
            cv_text,
            client,
            job_title,
            industry
        )
        
        return {
            "improvement_suggestions": result.get("formatted_answer", ""),
            "quick_wins": result.get("quick_wins", []),
            "priority_improvements": result.get("priority_improvements", []),
            "estimated_impact": result.get("estimated_impact", ""),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-jobs")
async def match_cv_to_positions(
    file: UploadFile = File(...),
    location: Optional[str] = None,
    job_level: Optional[str] = None
):
    """
    Match CV to available job positions.
    
    Args:
        file: PDF or text file of CV
        location: Preferred location
        job_level: Preferred job level (junior, mid, senior)
    
    Returns:
        Matched job positions with match scores
    """
    try:
        contents = await file.read()
        
        try:
            cv_text = contents.decode('utf-8')
        except:
            cv_text = contents.decode('latin-1')
        
        # Match CV to jobs
        result = match_cv_to_jobs(
            cv_text,
            client,
            location,
            job_level
        )
        
        return {
            "matched_jobs": result.get("matched_jobs", []),
            "top_matches": result.get("top_matches", []),
            "match_analysis": result.get("formatted_answer", ""),
            "total_matches": len(result.get("matched_jobs", [])),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-info")
async def extract_cv_information(file: UploadFile = File(...)):
    """
    Extract structured information from CV.
    
    Args:
        file: PDF or text file of CV
    
    Returns:
        Extracted CV information (name, email, skills, etc)
    """
    try:
        contents = await file.read()
        
        try:
            cv_text = contents.decode('utf-8')
        except:
            cv_text = contents.decode('latin-1')
        
        # Extract info
        result = analyze_cv_with_service(cv_text, client)
        
        return {
            "extracted_info": result.get("extracted_info", {}),
            "professional_summary": result.get("professional_summary", ""),
            "key_skills": result.get("keywords_found", []),
            "experience_summary": result.get("experience_summary", ""),
            "success": result.get("success", False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))