import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central app configuration, overridable via environment variables / .env"""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://resume_user:resume_pass@localhost:5432/resume_matcher",
    )
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    upload_dir: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    match_score_weights: dict = {
        "skills": 0.55,
        "experience": 0.20,
        "education": 0.10,
        "semantic": 0.15,
    }

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
