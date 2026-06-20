import json
from google import genai
from google.genai import types
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.models.user import User
from app.auth_utils import get_current_user
from app.schemas.job import ResumeAnalysisRequest, ResumeAnalysisResponse

router = APIRouter(prefix="/ai", tags=["AI"])

# New SDK — client based approach
client = genai.Client(api_key=settings.gemini_api_key)
GEMINI_MODEL = "gemini-2.5-flash-lite"


def build_prompt(resume_text: str, job_description: str) -> str:
    return f"""
You are an expert technical recruiter and career coach.

Analyze this resume against the job description and return ONLY a valid JSON object.
No explanation, no markdown, no code blocks. Just raw JSON.

Resume:
{resume_text}

Job Description:
{job_description}

Return this exact JSON structure:
{{
    "match_score": <integer 0-100>,
    "matched_keywords": [<list of skills/keywords found in both resume and JD>],
    "missing_keywords": [<list of important skills in JD missing from resume>],
    "experience_match": "<Strong|Moderate|Weak>",
    "summary": "<2-3 sentence honest assessment of fit>",
    "interview_tips": [
        "<specific tip 1 based on this JD>",
        "<specific tip 2 based on this JD>",
        "<specific tip 3 based on this JD>"
    ]
}}
"""


@router.post("/analyze-resume", response_model=ResumeAnalysisResponse)
def analyze_resume(
    request: ResumeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        prompt = build_prompt(request.resume_text, request.job_description)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,       # lower = more consistent/predictable output
                max_output_tokens=1000
            )
        )

        raw_text = response.text.strip()

        # Strip markdown code blocks if Gemini adds them anyway
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        parsed["match_score"] = max(0, min(100, int(parsed["match_score"])))

        return ResumeAnalysisResponse(**parsed)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid response format. Please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {str(e)}"
        )