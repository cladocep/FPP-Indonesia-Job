"""
models/response_model.py

Pydantic models for API responses.
Used for request/response validation and OpenAPI documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ── Chat/Query Response ──────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    intent: str = Field(..., description="Classified intent (rag, sql, cv, hybrid, chat)")
    response: str = Field(..., description="The agent's answer")
    source: str = Field(..., description="Which agent handled the query")

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "rag",
                "response": "Lowongan data scientist terdapat di Tokopedia dengan skill requirements python dan sql...",
                "source": "RAG Agent"
            }
        }


# ── CV Models ────────────────────────────────────────────────────────────────

class CVData(BaseModel):
    """Parsed CV data from CV parser."""
    name: Optional[str] = Field(None, description="Candidate name")
    skills: List[str] = Field(default=[], description="List of skills")
    experience: Optional[str] = Field(None, description="Work experience summary")
    education: Optional[str] = Field(None, description="Education background")
    summary: Optional[str] = Field(None, description="Professional summary")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "skills": ["python", "sql", "excel", "data analysis"],
                "experience": "2 years as data analyst at PT ABC",
                "education": "S1 Informatika dari Universitas XYZ",
                "summary": "Passionate about data and analytics"
            }
        }


class CVUploadRequest(BaseModel):
    """Request for CV upload and recommendation."""
    message: str = Field(..., description="User's request (e.g. 'Rekomendasikan pekerjaan')")
    cv_data: CVData = Field(..., description="Parsed CV data")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Rekomendasikan pekerjaan berdasarkan CV saya",
                "cv_data": {
                    "name": "John Doe",
                    "skills": ["python", "sql"],
                    "experience": "2 years as data analyst",
                    "education": "S1 Informatika",
                    "summary": "Data enthusiast"
                }
            }
        }


class JobRecommendation(BaseModel):
    """Single job recommendation."""
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    skill_match_percentage: float = Field(..., description="Skill match percentage (0-100)")
    matched_skills: List[str] = Field(default=[], description="Skills the candidate has")
    missing_skills: List[str] = Field(default=[], description="Skills the candidate is missing")
    reason: Optional[str] = Field(None, description="Why this job matches")


class CVRecommendationResponse(BaseModel):
    """Response with job recommendations based on CV."""
    intent: str = Field(default="cv", description="Intent type")
    response: str = Field(..., description="LLM-generated recommendation text")
    source: str = Field(default="CV Agent", description="Source agent")
    recommendations: List[JobRecommendation] = Field(default=[], description="Structured recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "cv",
                "response": "Berdasarkan CV kamu, berikut adalah 3 lowongan yang paling cocok...",
                "source": "CV Agent",
                "recommendations": [
                    {
                        "job_title": "Data Scientist",
                        "company_name": "Tokopedia",
                        "location": "Jakarta",
                        "skill_match_percentage": 85.5,
                        "matched_skills": ["python", "sql"],
                        "missing_skills": ["machine learning", "deep learning"],
                        "reason": "Strong technical foundation with data analysis experience"
                    }
                ]
            }
        }


# ── RAG Response Models ──────────────────────────────────────────────────────

class RAGSource(BaseModel):
    """Citation source for RAG response."""
    index: int = Field(..., description="Source index")
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    location: str = Field(..., description="Location")
    relevance_score: float = Field(..., description="Relevance score (0-1)")


class RAGResponse(BaseModel):
    """Response from RAG Agent."""
    intent: str = Field(default="rag", description="Intent type")
    response: str = Field(..., description="LLM-generated answer with citations")
    source: str = Field(default="RAG Agent", description="Source agent")
    sources: List[RAGSource] = Field(default=[], description="List of cited sources")

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "rag",
                "response": "Lowongan data scientist tersedia di Tokopedia dengan skill requirements...",
                "source": "RAG Agent",
                "sources": [
                    {
                        "index": 1,
                        "job_title": "Data Scientist",
                        "company_name": "Tokopedia",
                        "location": "Jakarta",
                        "relevance_score": 0.87
                    }
                ]
            }
        }


# ── SQL Response Models ──────────────────────────────────────────────────────

class SQLResponse(BaseModel):
    """Response from SQL Agent."""
    intent: str = Field(default="sql", description="Intent type")
    response: str = Field(..., description="Formatted SQL query result")
    source: str = Field(default="SQL Agent", description="Source agent")
    raw_results: Optional[List[dict]] = Field(None, description="Raw query results")

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "sql",
                "response": "Terdapat 150 lowongan full-time di Jakarta dengan rata-rata gaji 10 juta rupiah",
                "source": "SQL Agent",
                "raw_results": [
                    {
                        "count": 150,
                        "avg_salary": 10000000,
                        "location": "Jakarta"
                    }
                ]
            }
        }


# ── Error Response ───────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Error response format."""
    detail: str = Field(..., description="Error message")
    error_type: str = Field(default="error", description="Type of error")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Maaf, terjadi kesalahan saat memproses permintaan Anda",
                "error_type": "processing_error"
            }
        }


# ── Health Check Response ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "Multi-Agent Job Search System",
                "version": "1.0.0"
            }
        }
