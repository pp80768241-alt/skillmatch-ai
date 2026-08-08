from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, matcher

router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/{resume_id}/{job_id}", response_model=schemas.MatchOut)
def run_match(resume_id: int, job_id: int, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).get(resume_id)
    job = db.query(models.JobDescription).get(job_id)
    if not resume or not job:
        raise HTTPException(404, "Resume or Job not found")

    result = matcher.compute_match(resume, job)

    match = models.MatchResult(
        resume_id=resume.id,
        job_id=job.id,
        **result,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/recommend/{resume_id}", response_model=list[schemas.JobRecommendation])
def recommend_jobs(resume_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    """Rank every stored job description against a resume and return the best fits."""
    resume = db.query(models.Resume).get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")

    jobs = db.query(models.JobDescription).all()
    scored = []
    for job in jobs:
        result = matcher.compute_match(resume, job)
        scored.append(
            schemas.JobRecommendation(
                job_id=job.id,
                title=job.title,
                ats_score=result["ats_score"],
                matched_skills=result["matched_skills"],
                missing_skills=result["missing_skills"],
            )
        )

    scored.sort(key=lambda r: r.ats_score, reverse=True)
    return scored[:top_n]
