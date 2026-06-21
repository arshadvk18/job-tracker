import json
import base64
import io
from datetime import datetime, timezone

import pdfplumber
from google import genai
from google.genai import types
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.job import Application
from app.auth_utils import get_current_user
from app.schemas.job import ResumeAnalysisRequest, ResumeAnalysisResponse
from app.schemas.user import PDFExtractResponse

router = APIRouter(prefix="/ai", tags=["AI"])

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


# --- PDF text extraction endpoint (new) ---

@router.post("/extract-pdf", response_model=PDFExtractResponse)
def extract_pdf(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts { "pdf_base64": "<base64 string>" }
    Returns extracted text from the PDF.
    """
    pdf_base64 = payload.get("pdf_base64", "")
    if not pdf_base64:
        raise HTTPException(status_code=400, detail="pdf_base64 field is required")

    try:
        # Strip data URI prefix if browser sends it (e.g. "data:application/pdf;base64,...")
        if "," in pdf_base64:
            pdf_base64 = pdf_base64.split(",", 1)[1]

        pdf_bytes = base64.b64decode(pdf_base64)
        pdf_file = io.BytesIO(pdf_bytes)

        extracted_pages = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text.strip())

        extracted_text = "\n\n".join(extracted_pages).strip()

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from this PDF. It may be scanned or image-based. Please paste your resume as text instead."
            )

        return PDFExtractResponse(
            extracted_text=extracted_text,
            char_count=len(extracted_text)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing error: {str(e)}"
        )


# --- Resume analysis endpoint (extended) ---

@router.post("/analyze-resume", response_model=ResumeAnalysisResponse)
def analyze_resume(
    request: ResumeAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        prompt = build_prompt(request.resume_text, request.job_description)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1000
            )
        )

        raw_text = response.text.strip()

        # Strip markdown code blocks if Gemini adds them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        parsed["match_score"] = max(0, min(100, int(parsed["match_score"])))

        # Save to application if application_id was provided
        saved = False
        if request.application_id is not None:
            application = db.query(Application).filter(
                Application.id == request.application_id,
                Application.user_id == current_user.id   # security: only own applications
            ).first()

            if application:
                application.ai_analysis = parsed
                application.analyzed_at = datetime.now(timezone.utc)
                db.commit()
                saved = True
            # if application not found or doesn't belong to user — silently skip, don't error

        result = ResumeAnalysisResponse(**parsed)
        result.saved_to_application = saved
        return result

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