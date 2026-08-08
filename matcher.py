"""
Core matching engine:
 - Generates sentence-transformer embeddings for semantic similarity
 - Computes a weighted ATS-style match score (skills, experience, education, semantic)
 - Produces missing-skill gaps and improvement suggestions
"""

from functools import lru_cache
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    # Cached so the (relatively large) model is loaded into memory only once
    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> List[float]:
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def semantic_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a).reshape(1, -1)
    b = np.array(vec_b).reshape(1, -1)
    return float(cosine_similarity(a, b)[0][0])


def score_skills(resume_skills: List[str], required: List[str], preferred: List[str]) -> Dict:
    resume_set = set(s.lower() for s in resume_skills)
    required_set = set(s.lower() for s in required)
    preferred_set = set(s.lower() for s in preferred)

    matched_required = resume_set & required_set
    matched_preferred = resume_set & preferred_set
    missing_required = required_set - resume_set
    missing_preferred = preferred_set - resume_set

    if required_set:
        required_score = len(matched_required) / len(required_set)
    else:
        required_score = 1.0
    if preferred_set:
        preferred_score = len(matched_preferred) / len(preferred_set)
    else:
        preferred_score = 1.0

    # required skills weigh more heavily than preferred/nice-to-have skills
    combined = 0.8 * required_score + 0.2 * preferred_score

    return {
        "score": round(combined * 100, 2),
        "matched": sorted(matched_required | matched_preferred),
        "missing": sorted(missing_required | missing_preferred),
        "missing_required": sorted(missing_required),
    }


def score_experience(resume_years: float, min_years: float) -> float:
    if min_years <= 0:
        return 100.0
    ratio = resume_years / min_years
    return round(min(ratio, 1.2) / 1.2 * 100, 2)


def score_education(resume_education: List[Dict], requirement: str | None) -> float:
    if not requirement:
        return 100.0
    req_lower = requirement.lower()
    for edu in resume_education:
        if req_lower in edu.get("raw", "").lower():
            return 100.0
    # partial credit if candidate has *any* degree listed
    return 50.0 if resume_education else 0.0


def generate_suggestions(missing_skills: List[str], skills_score: float, experience_score: float) -> List[str]:
    suggestions = []
    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(
            f"Add or highlight experience with: {', '.join(top_missing)} to strengthen alignment with this role."
        )
    if skills_score < 60:
        suggestions.append(
            "Your listed skills cover less than 60% of the job's requirements — consider a certification "
            "or project that demonstrates the missing competencies."
        )
    if experience_score < 70:
        suggestions.append(
            "Quantify your work experience with measurable outcomes (e.g. 'reduced latency by 30%') "
            "to better match the seniority this role expects."
        )
    if not suggestions:
        suggestions.append("Strong match — tailor your summary section to mirror this job's exact keywords for ATS parsing.")
    return suggestions


def compute_match(resume, job) -> Dict:
    """resume and job are ORM objects (models.Resume / models.JobDescription)."""
    weights = settings.match_score_weights

    skills_result = score_skills(resume.skills or [], job.required_skills or [], job.preferred_skills or [])
    experience_result = score_experience(resume.total_experience_years or 0.0, job.min_experience_years or 0.0)
    education_result = score_education(resume.education or [], job.education_requirement)
    semantic_result = semantic_similarity(resume.embedding, job.embedding) * 100

    overall = (
        weights["skills"] * skills_result["score"]
        + weights["experience"] * experience_result
        + weights["education"] * education_result
        + weights["semantic"] * semantic_result
    )

    suggestions = generate_suggestions(skills_result["missing"], skills_result["score"], experience_result)

    return {
        "ats_score": round(overall, 2),
        "skills_score": skills_result["score"],
        "experience_score": experience_result,
        "education_score": education_result,
        "semantic_score": round(semantic_result, 2),
        "matched_skills": skills_result["matched"],
        "missing_skills": skills_result["missing"],
        "suggestions": suggestions,
    }
