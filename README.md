# Skillmatch — AI Resume Screening & Job Matching System

An end-to-end ATS-style screening tool. Upload a resume, paste a job
description, and get a weighted match score, a skills gap analysis, and
personalized improvement suggestions — backed by NLP entity extraction and
sentence-embedding semantic search.

Resume (PDF/DOCX) ──▶ Parser ──▶ Skills / Education / Experience
│
Job Description ──▶ Parser ──▶ Required / Preferred skills
│
Matching Engine (rules + embeddings)
│
ATS score · Missing skills · Suggestions


## Stack

| Layer      | Tech                                                        |
|------------|--------------------------------------------------------------|
| Backend    | FastAPI, SQLAlchemy, Python                                  |
| NLP/AI     | `sentence-transformers` (MiniLM embeddings), regex/rule-based entity extraction, cosine similarity |
| Database   | PostgreSQL                                                    |
| Frontend   | React (Vite), Axios                                            |
| Infra      | Docker, docker-compose                                        |

## How matching works

The overall **ATS score** is a weighted blend of four sub-scores:

- **Skills (55%)** — overlap between resume skills and the JD's required/preferred skills
- **Experience (20%)** — candidate's estimated years of experience vs. the JD's minimum
- **Education (10%)** — whether the JD's stated degree requirement is present
- **Semantic fit (15%)** — cosine similarity between resume and JD sentence embeddings, catching phrasing/context the keyword match misses

Weights are configurable in `backend/app/config.py`.

## Project structure

resume-matcher/
├── backend/
│ ├── app/
│ │ ├── main.py # FastAPI app + router registration
│ │ ├── config.py # settings (env-driven)
│ │ ├── database.py # SQLAlchemy engine/session
│ │ ├── models.py # Resume / JobDescription / MatchResult tables
│ │ ├── schemas.py # Pydantic response/request models
│ │ ├── parser.py # resume/JD text extraction + entity extraction
│ │ ├── matcher.py # embeddings + scoring engine
│ │ └── routes/ # resume.py, jobs.py, match.py
│ ├── requirements.txt
│ └── Dockerfile
├── frontend/
│ ├── src/
│ │ ├── App.jsx # upload → analyze → results flow
│ │ ├── components/ # ScoreGauge, SkillTags
│ │ └── App.css / index.css
│ ├── package.json
│ └── Dockerfile
├── docker-compose.yml
└── README.md


## Run it locally with Docker (recommended)

```bash
git clone <your-repo-url>
cd resume-matcher
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend/API docs (Swagger): http://localhost:8000/docs
- Postgres: localhost:5432 (user: `resume_user`, pass: `resume_pass`, db: `resume_matcher`)

First boot will take a minute or two while `sentence-transformers` downloads
the `all-MiniLM-L6-v2` embedding model (~90MB).

## Run it without Docker

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # then start Postgres locally and update DATABASE_URL if needed
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

You'll need a local PostgreSQL instance matching `DATABASE_URL`, e.g.:
```bash
docker run -d --name resume-db -p 5432:5432 \
  -e POSTGRES_USER=resume_user -e POSTGRES_PASSWORD=resume_pass \
  -e POSTGRES_DB=resume_matcher postgres:16-alpine
```

## API reference

| Method | Endpoint                              | Description                                  |
|--------|----------------------------------------|-----------------------------------------------|
| POST   | `/api/resumes/upload`                  | Upload + parse a resume (multipart file)      |
| GET    | `/api/resumes/{id}`                    | Fetch a parsed resume                          |
| GET    | `/api/resumes`                         | List uploaded resumes                          |
| POST   | `/api/jobs`                            | Create a job description                       |
| GET    | `/api/jobs/{id}`                       | Fetch a job description                        |
| POST   | `/api/match/{resume_id}/{job_id}`      | Run the scoring engine, returns ATS report      |
| GET    | `/api/match/recommend/{resume_id}`     | Rank all stored jobs against one resume         |

Full interactive docs are auto-generated at `/docs` once the backend is running.

## Extending it

- **Vector search at scale**: swap the in-Python cosine similarity in `matcher.py` for `pgvector` (Postgres extension) once you have thousands of resumes/jobs, so similarity search happens in SQL instead of Python.
- **Better parsing**: the `parser.py` skill taxonomy is a plain list — swap in spaCy NER + a trained skill-extraction model, or call an LLM (OpenAI/Anthropic API) for higher-accuracy structured extraction.
- **Auth**: `passlib`/`python-jose` are already in `requirements.txt` for adding recruiter login if you want to gate uploads.
- **Job recommendations**: currently brute-force scores every stored job for a resume; for large catalogs, pre-filter with an ANN index (FAISS/pgvector) before running the full weighted score.

## License

MIT — use freely for your portfolio.
