from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, parser, matcher

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=schemas.JobOut)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    parsed = parser.parse_job_description(payload.raw_text)
    embedding = matcher.embed_text(payload.raw_text[:5000])

    job = models.JobDescription(
        title=payload.title,
        raw_text=payload.raw_text,
        required_skills=parsed["required_skills"],
        preferred_skills=parsed["preferred_skills"],
        min_experience_years=payload.min_experience_years or parsed["min_experience_years"],
        education_requirement=payload.education_requirement,
        embedding=embedding,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.JobDescription).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(models.JobDescription).order_by(models.JobDescription.created_at.desc()).limit(100).all()
