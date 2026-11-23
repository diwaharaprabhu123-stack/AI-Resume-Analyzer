"""AI Resume Analyzer & ATS Score Checker
Input  : resume (PDF) + job description (text)
Model  : Google Gemini (via google-genai)
Output : match score, matched skills, missing keywords, 5 suggestions
"""
import os
import json

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv()  # reads GEMINI_API_KEY from a local .env file (never submit this file)

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ---------- 1. Define the exact shape of the AI's answer ----------
class Analysis(BaseModel):
    match_score: int = Field(description="ATS match score from 0 to 100")
    matched_skills: list[str] = Field(description="Skills/keywords found in BOTH resume and job description")
    missing_skills: list[str] = Field(description="Important skills/keywords in the job description but NOT in the resume")
    suggestions: list[str] = Field(description="Exactly 5 specific suggestions to improve the resume for this job")


# ---------- 2. Helper functions ----------
def get_api_key():
    """Look for the key in environment/.env first, then Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None


def read_pdf(file) -> str:
    """Extract text from every page of the uploaded PDF."""
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def analyze(resume_text: str, job_text: str, api_key: str) -> Analysis:
    """Send resume + job description to Gemini and get structured JSON back."""
    client = genai.Client(api_key=api_key)
    prompt = f"""You are an expert ATS (Applicant Tracking System) and recruiter.
Compare the RESUME with the JOB DESCRIPTION.

Rules:
- match_score: honest 0-100 score based on skills, keywords, tools and experience match.
- matched_skills: skills present in both.
- missing_skills: important job requirements absent from the resume.
- suggestions: exactly 5 specific, actionable improvements.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_text}
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Analysis,
            temperature=0.2,
        ),
    )
    return Analysis(**json.loads(response.text))


# ---------- 3. Screen ----------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="centered")
st.title("📄 AI Resume Analyzer & ATS Score Checker")
st.caption("Upload your resume, paste a job description, and see how well they match.")

api_key = get_api_key()
if not api_key:
    st.error("GEMINI_API_KEY not found. Add it to a .env file or Streamlit secrets (see README).")
    st.stop()

resume_file = st.file_uploader("1. Upload your resume (PDF)", type="pdf")
job_text = st.text_area("2. Paste the job description", height=220)

if st.button("Analyze my resume", type="primary"):
    if not resume_file or not job_text.strip():
        st.warning("Please upload a resume and paste a job description.")
        st.stop()

    resume_text = read_pdf(resume_file)
    if len(resume_text) < 50:
        st.error("Couldn't read text from this PDF (it may be a scanned image). Try a text-based PDF.")
        st.stop()

    with st.spinner("Analyzing with Gemini..."):
        try:
            result = analyze(resume_text, job_text, api_key)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    # ---------- 4. Output ----------
    score = max(0, min(100, result.match_score))
    st.subheader("Match score")
    st.metric("ATS match", f"{score} / 100")
    st.progress(score / 100)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Matching skills")
        for s in result.matched_skills:
            st.write(f"- {s}")
    with col2:
        st.subheader("❌ Missing skills")
        for s in result.missing_skills:
            st.write(f"- {s}")

    st.subheader("💡 5 ways to improve your resume")
    for i, s in enumerate(result.suggestions[:5], 1):
        st.write(f"{i}. {s}")
