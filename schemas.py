from typing import List, Optional
from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: int
    filename: str
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]
    education: List[dict]
    experience: List[dict]
    projects: List[dict]
    total_experience_years: float

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    title: str
    raw_text: str
    min_experience_years: Optional[float] = 0.0
    education_requirement: Optional[str] = None


class JobOut(BaseModel):
    id: int
    title: str
    raw_text: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: float
    education_requirement: Optional[str]

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    ats_score: float
    skills_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    suggestions: List[str]

    class Config:
        from_attributes = True


class JobRecommendation(BaseModel):
    job_id: int
    title: str
    ats_score: float
    matched_skills: List[str]
    missing_skills: List[str]
