"""
Resume & Job-Description parsing utilities.

Handles:
 - Raw text extraction from PDF / DOCX / TXT
 - Contact info extraction (name / email / phone)
 - Skill extraction against a curated + extensible skills taxonomy
 - Education / experience section extraction
 - Total years-of-experience estimation
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import pdfplumber
import docx

# ---------------------------------------------------------------------------
# Skill taxonomy - extend this list (or load from a DB table) as needed
# ---------------------------------------------------------------------------
SKILL_TAXONOMY = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "kotlin", "swift", "scala", "r", "matlab",
    # Web / frontend
    "react", "angular", "vue", "next.js", "html", "css", "tailwind", "redux",
    # Backend / frameworks
    "fastapi", "flask", "django", "spring boot", "node.js", "express",
    "graphql", "rest api", "microservices",
    # Data / ML / AI
    "machine learning", "deep learning", "nlp", "computer vision",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    "llm", "langchain", "transformers", "opencv", "keras",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "vector database", "pinecone", "faiss", "chromadb",
    # DevOps / Cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "ci/cd", "jenkins", "github actions", "linux",
    # Data engineering
    "spark", "airflow", "kafka", "etl", "hadoop",
    # General / soft
    "git", "agile", "scrum", "jira", "communication", "leadership",
    "problem solving", "team management",
]

EDUCATION_KEYWORDS = [
    "b.tech", "bachelor", "b.sc", "bsc", "m.tech", "master", "msc", "m.sc",
    "phd", "doctorate", "mba", "bca", "mca", "b.e.", "be ", "diploma",
]

DEGREE_PATTERN = re.compile(
    r"(bachelor(?:'s)?|master(?:'s)?|b\.?tech|m\.?tech|phd|mba|bca|mca|"
    r"b\.?e\.?|b\.?sc|m\.?sc|diploma)[^\n,;]{0,80}",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}")
YEAR_RANGE_PATTERN = re.compile(
    r"(20\d{2}|19\d{2})\s*(?:-|to|–)\s*(20\d{2}|19\d{2}|present|current)",
    re.IGNORECASE,
)


def extract_text(file_path: str) -> str:
    """Extract raw text from a PDF, DOCX, or TXT file."""
    if file_path.lower().endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts)

    if file_path.lower().endswith(".docx"):
        document = docx.Document(file_path)
        return "\n".join(p.text for p in document.paragraphs)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    email_match = EMAIL_PATTERN.search(text)
    phone_match = PHONE_PATTERN.search(text)

    # Naive name guess: first non-empty line that isn't an email/phone/url
    name = None
    for line in text.splitlines()[:5]:
        clean = line.strip()
        if clean and "@" not in clean and not PHONE_PATTERN.search(clean) and len(clean.split()) <= 5:
            name = clean
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
    }


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for skill in SKILL_TAXONOMY:
        # word-boundary safe match, allows for skills containing symbols like c++
        pattern = re.escape(skill)
        if re.search(rf"(?<![a-zA-Z0-9]){pattern}(?![a-zA-Z0-9])", text_lower):
            found.add(skill)
    return sorted(found)


def extract_education(text: str) -> List[Dict[str, str]]:
    matches = DEGREE_PATTERN.findall(text)
    education = []
    for m in DEGREE_PATTERN.finditer(text):
        education.append({"raw": m.group(0).strip()})
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for edu in education:
        key = edu["raw"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(edu)
    return unique[:5]


def estimate_total_experience_years(text: str) -> float:
    """Sum up year ranges found in the resume (e.g. 2019-2022) as a rough proxy."""
    total_months = 0
    now_year = datetime.now().year
    for start, end in YEAR_RANGE_PATTERN.findall(text):
        start_year = int(start)
        end_year = now_year if end.lower() in ("present", "current") else int(end)
        if end_year >= start_year:
            total_months += (end_year - start_year) * 12
    return round(total_months / 12, 1)


def extract_experience_entries(text: str) -> List[Dict[str, str]]:
    entries = []
    for match in YEAR_RANGE_PATTERN.finditer(text):
        # grab surrounding line for context (title/company)
        start_idx = max(0, match.start() - 80)
        context = text[start_idx:match.start()].splitlines()[-1].strip()
        entries.append({
            "period": match.group(0),
            "context": context,
        })
    return entries[:10]


def parse_resume(file_path: str) -> Dict:
    text = extract_text(file_path)
    contact = extract_contact_info(text)
    return {
        "raw_text": text,
        "candidate_name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience_entries(text),
        "projects": [],  # left as an extension point (section-header based extraction)
        "total_experience_years": estimate_total_experience_years(text),
    }


def parse_job_description(text: str) -> Dict:
    skills = extract_skills(text)
    # crude split: skills mentioned near "required"/"must have" vs "preferred"/"nice to have"
    lower = text.lower()
    required_section = lower.split("preferred")[0] if "preferred" in lower else lower
    required_skills = [s for s in skills if s in required_section]
    preferred_skills = [s for s in skills if s not in required_skills]

    exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", lower)
    min_experience = float(exp_match.group(1)) if exp_match else 0.0

    return {
        "required_skills": required_skills or skills,
        "preferred_skills": preferred_skills,
        "min_experience_years": min_experience,
    }
