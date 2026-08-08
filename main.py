from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routes import resume, jobs, match

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Screening & Job Matching API",
    description="Upload resumes, post job descriptions, and get ATS-style match scores powered by NLP embeddings.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(match.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "resume-matcher-api"}
