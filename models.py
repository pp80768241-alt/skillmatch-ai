from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    skills = Column(JSON, default=list)          # ["python", "react", ...]
    education = Column(JSON, default=list)        # [{"degree": ..., "institute": ...}]
    experience = Column(JSON, default=list)        # [{"title": ..., "company": ..., "years": ...}]
    projects = Column(JSON, default=list)

    total_experience_years = Column(Float, default=0.0)
    embedding = Column(ARRAY(Float), nullable=True)   # sentence-transformer vector

    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    min_experience_years = Column(Float, default=0.0)
    education_requirement = Column(String, nullable=True)

    embedding = Column(ARRAY(Float), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))

    ats_score = Column(Float, nullable=False)          # 0-100 overall score
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)

    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="matches")
    job = relationship("JobDescription", back_populates="matches")
