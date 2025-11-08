"""
Fixed AI Engine using direct Gemini API instead of instructor
"""
import os
import json
import re
from typing import Optional, List
from pydantic import BaseModel, Field

# Global variables untuk availability status
_GENAI_AVAILABLE = False
_GEMINI_API_KEY_AVAILABLE = False

# Try to import dependencies with proper error handling
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    print("⚠️  Google Generative AI tidak terinstall. AI evaluation akan menggunakan fallback.")

# Check API key availability
if os.getenv("GEMINI_API_KEY"):
    _GEMINI_API_KEY_AVAILABLE = True
else:
    print("⚠️  GEMINI_API_KEY tidak ditemukan. AI evaluation akan menggunakan fallback.")


class CVResult(BaseModel):
    cv_match_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Kecocokan CV terhadap role (0..1)"
    )
    cv_feedback: str = Field(
        ..., min_length=1, description="Feedback ringkas namun informatif"
    )


class ProjectResult(BaseModel):
    project_score: float = Field(..., ge=1.0, le=5.0, description="Skor project (1..5)")
    project_feedback: str = Field(
        ..., min_length=1, description="Feedback singkat dan spesifik"
    )


class OverallResult(BaseModel):
    cv_match_rate: float = Field(..., ge=0.0, le=1.0)
    cv_feedback: str = Field(..., min_length=1)
    project_score: float = Field(..., ge=1.0, le=5.0)
    project_feedback: str = Field(..., min_length=1)
    overall_summary: str = Field(..., min_length=1)


def _get_gemini_client():
    """Create and return Gemini client"""
    if not _GENAI_AVAILABLE:
        raise RuntimeError("Google Generative AI tidak tersedia")
    if not _GEMINI_API_KEY_AVAILABLE:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan dalam environment")

    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # Use working model
    model = genai.GenerativeModel("models/gemini-flash-latest")
    return model


def available() -> bool:
    """Check if all LLM dependencies are available."""
    return _GENAI_AVAILABLE and _GEMINI_API_KEY_AVAILABLE


def _extract_json_from_text(text: str) -> dict:
    """Extract JSON from text response"""
    try:
        # Try to find JSON in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # If no JSON found, try parsing the whole text
            return json.loads(text)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {}


def _evaluate_cv_direct(cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None) -> CVResult:
    """Evaluate CV using direct Gemini API"""
    client = _get_gemini_client()
    snippets = "\n\n".join(context_snippets or [])

    prompt = f"""
Anda adalah sistem evaluasi CV untuk posisi: {job_title}.
Gunakan konteks relevan berikut jika ada:
{snippets}

Tugas:
- Nilai kecocokan CV terhadap role (0..1) dan berikan feedback ringkas namun informatif.
- Hindari informasi yang tidak ada di CV.
- Pastikan cv_match_rate berada pada rentang [0,1].

Kembalikan jawaban dalam format JSON persis seperti ini:
{{"cv_match_rate": 0.8, "cv_feedback": "Feedback di sini"}}

CV:
---
{cv_text}
---
"""

    try:
        response = client.generate_content(prompt)
        json_data = _extract_json_from_text(response.text)

        # Validate and return result
        cv_match_rate = float(json_data.get("cv_match_rate", 0.5))
        cv_feedback = json_data.get("cv_feedback", "Evaluasi CV berhasil dilakukan.")

        # Ensure constraints
        cv_match_rate = max(0.0, min(1.0, cv_match_rate))

        return CVResult(cv_match_rate=cv_match_rate, cv_feedback=cv_feedback)
    except Exception as e:
        print(f"⚠️  Direct CV evaluation failed: {e}")
        raise


def _evaluate_project_direct(report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None) -> ProjectResult:
    """Evaluate Project using direct Gemini API"""
    client = _get_gemini_client()
    snippets = "\n\n".join(context_snippets or [])

    prompt = f"""
Anda adalah evaluator Project Report terhadap Case Study Brief.
Pertimbangkan konteks berikut (jika ada):
{snippets}

Case Study Brief:
---
{case_brief_text}
---

Tugas:
- Skor project (1..5) berdasarkan kesesuaian dengan brief, kualitas chaining/prompting/RAG/error handling.
- Berikan feedback singkat namun spesifik perbaikan.
- Pastikan project_score berada pada rentang [1,5].

Kembalikan jawaban dalam format JSON persis seperti ini:
{{"project_score": 4.0, "project_feedback": "Feedback di sini"}}

Report:
---
{report_text}
---
"""

    try:
        response = client.generate_content(prompt)
        json_data = _extract_json_from_text(response.text)

        # Validate and return result
        project_score = float(json_data.get("project_score", 3.0))
        project_feedback = json_data.get("project_feedback", "Evaluasi project berhasil dilakukan.")

        # Ensure constraints
        project_score = max(1.0, min(5.0, project_score))

        return ProjectResult(project_score=project_score, project_feedback=project_feedback)
    except Exception as e:
        print(f"⚠️  Direct project evaluation failed: {e}")
        raise


def _synthesize_overall_direct(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Synthesize overall result using direct Gemini API"""
    client = _get_gemini_client()

    prompt = f"""
Gabungkan hasil evaluasi CV dan Project menjadi ringkasan 3-5 kalimat.
Fokus: strengths, gaps, recommendations.

CV: rate={cv.cv_match_rate}, feedback={cv.cv_feedback}
Project: score={pr.project_score}, feedback={pr.project_feedback}

Kembalikan jawaban dalam format JSON persis seperti ini:
{{"cv_match_rate": {cv.cv_match_rate}, "cv_feedback": "{cv.cv_feedback}", "project_score": {pr.project_score}, "project_feedback": "{pr.project_feedback}", "overall_summary": "Summary di sini"}}
"""

    try:
        response = client.generate_content(prompt)
        json_data = _extract_json_from_text(response.text)

        # Use original values for CV and project, extract summary
        overall_summary = json_data.get("overall_summary", "Kandidat memiliki kombinasi skills yang baik untuk posisi ini.")

        return OverallResult(
            cv_match_rate=cv.cv_match_rate,
            cv_feedback=cv.cv_feedback,
            project_score=pr.project_score,
            project_feedback=pr.project_feedback,
            overall_summary=overall_summary
        )
    except Exception as e:
        print(f"⚠️  Direct synthesis failed: {e}")
        raise


# Import fallback functions from original module
from .ai_engine import _fallback_evaluate_cv, _fallback_evaluate_project, _fallback_synthesize_overall


def evaluate_cv(
    cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None
) -> CVResult:
    """Evaluasi CV menggunakan direct Gemini API"""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback evaluation untuk CV")
        return _fallback_evaluate_cv(cv_text, job_title)

    try:
        return _evaluate_cv_direct(cv_text, job_title, context_snippets)
    except Exception as e:
        print(f"⚠️  AI evaluation failed: {e}. Menggunakan fallback evaluation.")
        return _fallback_evaluate_cv(cv_text, job_title)


def evaluate_project(
    report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None
) -> ProjectResult:
    """Evaluasi Project menggunakan direct Gemini API"""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback evaluation untuk Project")
        return _fallback_evaluate_project(report_text, case_brief_text)

    try:
        return _evaluate_project_direct(report_text, case_brief_text, context_snippets)
    except Exception as e:
        print(f"⚠️  AI evaluation failed: {e}. Menggunakan fallback evaluation.")
        return _fallback_evaluate_project(report_text, case_brief_text)


def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Sintesis akhir menggunakan direct Gemini API"""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback synthesis")
        return _fallback_synthesize_overall(cv, pr)

    try:
        return _synthesize_overall_direct(cv, pr)
    except Exception as e:
        print(f"⚠️  AI synthesis failed: {e}. Menggunakan fallback synthesis.")
        return _fallback_synthesize_overall(cv, pr)