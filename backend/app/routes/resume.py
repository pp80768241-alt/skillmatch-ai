import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app import models, schemas, parser, matcher

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/upload", response_model=schemas.ResumeOut)
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Use PDF, DOCX, or TXT.")

    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(settings.upload_dir, saved_name)
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    parsed = parser.parse_resume(saved_path)
    embedding = matcher.embed_text(parsed["raw_text"][:5000])  # cap length for speed

    resume = models.Resume(
        filename=file.filename,
        raw_text=parsed["raw_text"],
        candidate_name=parsed["candidate_name"],
        email=parsed["email"],
        phone=parsed["phone"],
        skills=parsed["skills"],
        education=parsed["education"],
        experience=parsed["experience"],
        projects=parsed["projects"],
        total_experience_years=parsed["total_experience_years"],
        embedding=embedding,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(models.Resume).get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    return resume


@router.get("", response_model=list[schemas.ResumeOut])
def list_resumes(db: Session = Depends(get_db)):
    return db.query(models.Resume).order_by(models.Resume.created_at.desc()).limit(100).all()
