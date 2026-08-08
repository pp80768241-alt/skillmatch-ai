import React, { useState } from "react";
import axios from "axios";
import ScoreGauge from "./components/ScoreGauge.jsx";
import SkillTags from "./components/SkillTags.jsx";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [jdTitle, setJdTitle] = useState("");
  const [jdText, setJdText] = useState("");
  const [resume, setResume] = useState(null);
  const [job, setJob] = useState(null);
  const [match, setMatch] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1);

  async function handleAnalyze() {
    if (!file || !jdText.trim()) {
      setError("Attach a resume and paste a job description first.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const resumeRes = await axios.post(`${API_BASE}/api/resumes/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResume(resumeRes.data);

      const jobRes = await axios.post(`${API_BASE}/api/jobs`, {
        title: jdTitle || "Untitled Role",
        raw_text: jdText,
      });
      setJob(jobRes.data);

      const matchRes = await axios.post(
        `${API_BASE}/api/match/${resumeRes.data.id}/${jobRes.data.id}`
      );
      setMatch(matchRes.data);

      const recRes = await axios.get(`${API_BASE}/api/match/recommend/${resumeRes.data.id}`);
      setRecommendations(recRes.data);

      setStep(2);
    } catch (err) {
      console.error(err);
      setError(
        err?.response?.data?.detail ||
          "Something went wrong reaching the API. Is the backend running on :8000?"
      );
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setJdTitle("");
    setJdText("");
    setResume(null);
    setJob(null);
    setMatch(null);
    setRecommendations([]);
    setStep(1);
    setError(null);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◈</span>
          <span>SKILLMATCH</span>
        </div>
        <div className="topbar-sub">AI resume screening console</div>
      </header>

      {step === 1 && (
        <main className="intake">
          <div className="intake-copy">
            <div className="eyebrow">01 — SCAN INPUT</div>
            <h1>Run a resume through the screener.</h1>
            <p>
              Upload a candidate's resume and drop in the job description.
              The engine extracts skills, experience and education, then
              scores the fit the way an ATS would — with the gaps spelled out.
            </p>
          </div>

          <div className="intake-panel">
            <label className="field">
              <span className="field-label">Resume file (PDF, DOCX, TXT)</span>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </label>

            <label className="field">
              <span className="field-label">Job title</span>
              <input
                type="text"
                placeholder="e.g. Backend Engineer, Data Analyst"
                value={jdTitle}
                onChange={(e) => setJdTitle(e.target.value)}
              />
            </label>

            <label className="field">
              <span className="field-label">Job description</span>
              <textarea
                rows={8}
                placeholder="Paste the full job description here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            </label>

            {error && <div className="error-banner">{error}</div>}

            <button className="primary-btn" onClick={handleAnalyze} disabled={loading}>
              {loading ? "Scanning…" : "Run match"}
            </button>
          </div>
        </main>
      )}

      {step === 2 && match && (
        <main className="results">
          <div className="results-head">
            <div className="eyebrow">02 — MATCH REPORT</div>
            <h1>{resume.candidate_name || resume.filename} → {job.title}</h1>
            <button className="ghost-btn" onClick={reset}>New scan</button>
          </div>

          <section className="score-row">
            <ScoreGauge score={match.ats_score} label="OVERALL ATS MATCH" />
            <div className="sub-scores">
              <SubScore label="Skills" value={match.skills_score} />
              <SubScore label="Experience" value={match.experience_score} />
              <SubScore label="Education" value={match.education_score} />
              <SubScore label="Semantic fit" value={match.semantic_score} />
            </div>
          </section>

          <section className="panel-grid">
            <div className="panel">
              <SkillTags title="Matched skills" tags={match.matched_skills} tone="good" />
              <SkillTags title="Missing skills" tags={match.missing_skills} tone="bad" />
            </div>

            <div className="panel">
              <div className="tag-title">Improvement suggestions</div>
              <ul className="suggestion-list">
                {match.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </section>

          {recommendations.length > 0 && (
            <section className="panel">
              <div className="tag-title">Other roles this resume fits</div>
              <table className="rec-table">
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Match</th>
                    <th>Top missing skills</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.map((r) => (
                    <tr key={r.job_id}>
                      <td>{r.title}</td>
                      <td className="mono">{r.ats_score.toFixed(0)}</td>
                      <td className="mono dim">{r.missing_skills.slice(0, 4).join(", ") || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </main>
      )}

      <footer className="footer">
        <span>SKILLMATCH · FastAPI + Sentence-Transformers + PostgreSQL</span>
      </footer>
    </div>
  );
}

function SubScore({ label, value }) {
  return (
    <div className="sub-score">
      <div className="sub-score-bar-track">
        <div
          className="sub-score-bar-fill"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
      <div className="sub-score-meta">
        <span>{label}</span>
        <span className="mono">{value.toFixed(0)}</span>
      </div>
    </div>
  );
}
