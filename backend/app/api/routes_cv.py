"""
api/routes_cv.py

CV analysis and improvement endpoints.
Uses CV service for document analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, List
from openai import OpenAI

import json

from backend.app.config import OPENAI_API_KEY
from backend.app.services.cv_service import parse_cv, parse_cv_with_llm
from backend.app.agents.main_agent import handle_chat

router = APIRouter(prefix="/api/cv", tags=["CV"])
client = OpenAI(api_key=OPENAI_API_KEY)

_SCORING_SYSTEM_PROMPT = """You are an expert CV reviewer. Given structured CV data, score it and provide actionable feedback.

Return ONLY valid JSON with these exact fields:
{
  "overall_score": <integer 0-100>,
  "strengths": ["list of specific strengths found in the CV"],
  "weaknesses": ["list of specific issues or missing elements"],
  "recommendations": ["list of concrete improvement tips"]
}

Scoring rubric (total 100):
- Contact info complete (name, email, phone): 10 pts
- Professional summary present: 10 pts
- Work experience with quantified achievements: 30 pts
- Skills list (relevant and specific): 20 pts
- Education details: 10 pts
- Languages / certifications bonus: 10 pts
- Overall formatting/completeness: 10 pts

Return ONLY pure JSON — no markdown, no explanation."""


def _score_cv(cv_data: dict) -> dict:
    """Call LLM to score CV and return strengths, weaknesses, recommendations."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": f"Score this CV data:\n\n{json.dumps(cv_data, indent=2)}"},
        ],
        temperature=0.2,
        max_tokens=800,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


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

        # parse_cv handles PDF/DOCX/TXT extraction properly
        cv_data = parse_cv(contents, filename, client)
        scoring = _score_cv(cv_data)

        return {
            "filename": filename,
            "overall_score": scoring.get("overall_score", 0),
            "analysis": cv_data.get("summary", ""),
            "strengths": scoring.get("strengths", []),
            "weaknesses": scoring.get("weaknesses", []),
            "recommendations": scoring.get("recommendations", []),
            "keywords_found": cv_data.get("skills", []),
            "success": True
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
        
        prompt = f"Berikan saran peningkatan CV berikut"
        if job_title:
            prompt += f" untuk posisi {job_title}"
        if industry:
            prompt += f" di industri {industry}"
        prompt += f":\n\n{cv_text}"
        reply = handle_chat(prompt, client)

        return {
            "improvement_suggestions": reply,
            "quick_wins": [],
            "priority_improvements": [],
            "estimated_impact": "",
            "success": True
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
        
        prompt = f"Cocokkan CV berikut dengan lowongan yang tersedia"
        if location:
            prompt += f" di {location}"
        if job_level:
            prompt += f" untuk level {job_level}"
        prompt += f":\n\n{cv_text}"
        reply = handle_chat(prompt, client)

        return {
            "matched_jobs": [],
            "top_matches": [],
            "match_analysis": reply,
            "total_matches": 0,
            "success": True
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
        
        result = parse_cv_with_llm(cv_text, client)

        return {
            "extracted_info": result,
            "professional_summary": result.get("summary", ""),
            "key_skills": result.get("skills", []),
            "experience_summary": result.get("experience", ""),
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))