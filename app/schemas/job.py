from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any
from app.models.job import ApplicationStatus


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


class ApplicationAnalysis(BaseModel):
    match_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    experience_match: str
    summary: str
    interview_tips: List[str]


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: ApplicationStatus
    notes: Optional[str]
    applied_at: datetime
    updated_at: Optional[datetime]
    job: JobResponse
    ai_analysis: Optional[Any] = None          # ← new: raw JSONB from DB
    analyzed_at: Optional[datetime] = None     # ← new

    model_config = {"from_attributes": True}


# --- AI Schemas ---

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    job_description: str
    application_id: Optional[int] = None       # ← new: if provided, saves result to DB


class ResumeAnalysisResponse(BaseModel):
    match_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    experience_match: str
    summary: str
    interview_tips: List[str]
    saved_to_application: bool = False         # ← new: tells frontend if it was saved