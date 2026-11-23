# AI Resume Analyzer & ATS Score Checker

Upload a resume (PDF) + paste a job description -> Gemini returns a match score,
matching skills, missing skills and 5 improvement suggestions.

## Run
1. Get a free key at https://aistudio.google.com
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and put your key in it
4. `streamlit run app.py`

## How it works
PDF -> pypdf extracts text -> prompt (resume + job) -> Gemini returns JSON that
matches the `Analysis` schema -> Streamlit displays it.

On Streamlit Cloud, put `GEMINI_API_KEY = "..."` in the app's Secrets instead of a .env file.
