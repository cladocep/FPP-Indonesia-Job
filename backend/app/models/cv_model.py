from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Education(BaseModel):
    """Education experience in CV"""
    school: str = Field(..., description="School/University name")
    degree: str = Field(..., description="Degree obtained")
    field: str = Field(..., description="Field of study")
    start_year: int
    end_year: int
    gpa: Optional[float] = None

class Experience(BaseModel):
    """Work experience in CV"""
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position")
    duration_months: int = Field(..., description="Duration in months")
    description: str = Field(..., description="Job responsibilities")
    start_date: datetime
    end_date: Optional[datetime] = None

class Skill(BaseModel):
    """Skills in CV"""
    name: str = Field(..., description="Skill name")
    level: str = Field(..., description="Proficiency level: beginner, intermediate, advanced, expert")
    years_of_experience: Optional[int] = None

class CVModel(BaseModel):
    """Complete CV/Resume Model"""
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    summary: Optional[str] = Field(None, description="Professional summary")
    
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+62812345678",
                "summary": "Experienced backend developer",
                "education": [
                    {
                        "school": "Universitas Indonesia",
                        "degree": "Bachelor",
                        "field": "Computer Science",
                        "start_year": 2018,
                        "end_year": 2022,
                        "gpa": 3.8
                    }
                ],
                "experience": [
                    {
                        "company": "Tech Company",
                        "position": "Backend Developer",
                        "duration_months": 12,
                        "description": "Develop REST APIs",
                        "start_date": "2023-01-01T00:00:00",
                        "end_date": None
                    }
                ],
                "skills": [
                    {
                        "name": "Python",
                        "level": "advanced",
                        "years_of_experience": 3
                    }
                ]
            }
        }