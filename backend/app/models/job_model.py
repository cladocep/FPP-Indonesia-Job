"""
models/job_model.py

Pydantic model for Job listing data structure.
Used for validating job information from database and RAG.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobModel(BaseModel):
    """Structured Job listing data model."""
    
    # Basic info
    job_id: Optional[str] = Field(None, description="Unique job ID")
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    
    # Location & work type
    location: str = Field(..., description="Job location")
    location_city: Optional[str] = Field(None, description="City")
    location_province: Optional[str] = Field(None, description="Province")
    work_type: Optional[str] = Field(None, description="Work type (full_time, part_time, contract, etc)")
    is_remote: Optional[bool] = Field(False, description="Whether position is remote")
    
    # Salary info
    salary_min: Optional[int] = Field(None, description="Minimum salary in IDR")
    salary_max: Optional[int] = Field(None, description="Maximum salary in IDR")
    salary_currency: Optional[str] = Field("IDR", description="Currency")
    
    # Job details
    job_description: Optional[str] = Field(None, description="Full job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    skills_required: List[str] = Field(default=[], description="List of required skills")
    
    # Benefits & info
    benefits: List[str] = Field(default=[], description="Job benefits")
    company_description: Optional[str] = Field(None, description="Company information")
    
    # Metadata
    posted_date: Optional[datetime] = Field(None, description="Date job was posted")
    expiry_date: Optional[datetime] = Field(None, description="Job posting expiry date")
    application_url: Optional[str] = Field(None, description="Link to apply")
    
    # RAG-specific
    relevance_score: Optional[float] = Field(None, description="Search relevance score (0-1)")
    document: Optional[str] = Field(None, description="Full raw document text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "tokopedia_001",
                "job_title": "Data Scientist",
                "company_name": "Tokopedia",
                "location": "Jakarta Selatan, Jakarta",
                "location_city": "Jakarta",
                "location_province": "Jakarta",
                "work_type": "full_time",
                "is_remote": False,
                "salary_min": 8000000,
                "salary_max": 15000000,
                "salary_currency": "IDR",
                "job_description": "We are looking for an experienced Data Scientist...",
                "requirements": "5+ years experience in data science, proficient in Python...",
                "skills_required": ["Python", "SQL", "Machine Learning", "Statistics"],
                "benefits": ["Health insurance", "Flexible working hours", "Professional development"],
                "company_description": "Tokopedia is the largest e-commerce platform in Indonesia...",
                "posted_date": "2026-04-01T10:00:00",
                "expiry_date": "2026-05-01T10:00:00",
                "application_url": "https://tokopedia.com/careers/apply/001",
                "relevance_score": 0.87
            }
        }


class JobSearchResult(BaseModel):
    """Search result containing a job and metadata."""
    job: JobModel = Field(..., description="Job information")
    match_percentage: Optional[float] = Field(None, description="Skill match percentage if from CV agent")
    matched_skills: List[str] = Field(default=[], description="Skills that match user CV")
    missing_skills: List[str] = Field(default=[], description="Skills user is missing")


class JobListResponse(BaseModel):
    """Response with list of jobs."""
    total: int = Field(..., description="Total number of jobs")
    jobs: List[JobModel] = Field(..., description="List of jobs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "jobs": [
                    {
                        "job_title": "Data Scientist",
                        "company_name": "Tokopedia",
                        "location": "Jakarta",
                        "work_type": "full_time",
                        "skills_required": ["Python", "SQL"]
                    }
                ]
            }
        }
