from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.job import ApplicationStatus
from typing import Optional, List


# --- Job Schemas ---

class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    salary_range: Optional[str]
    job_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Application Schemas ---

class ApplicationCreate(BaseModel):
    job_id: int
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: ApplicationStatus
    notes: Optional[str]
    applied_at: datetime
    updated_at: Optional[datetime]
    job: JobResponse         # nested — returns full job details inside application

    model_config = {"from_attributes": True}

    # --- AI Schemas ---

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    job_description: str

class ResumeAnalysisResponse(BaseModel):
    match_score: int                    # 0-100
    matched_keywords: List[str]         # skills you have that match
    missing_keywords: List[str]         # skills you're lacking
    experience_match: str               # "Strong" / "Moderate" / "Weak"
    summary: str                        # 2-3 line human readable summary
    interview_tips: List[str]           # 3 tips specific to this JD