import os
from typing import Optional, List

from pydantic import BaseModel, Field

try:
    import instructor
    import google.generativeai as genai
except Exception as e:
    raise RuntimeError(f"Instructor/Google GenerativeAI tidak tersedia: {e}")


class CVResult(BaseModel):
    cv_match_rate: float = Field(..., ge=0.0, le=1.0, description="Kecocokan CV terhadap role (0..1)")
    cv_feedback: str = Field(..., min_length=1, description="Feedback ringkas namun informatif")


class ProjectResult(BaseModel):
    project_score: float = Field(..., ge=1.0, le=5.0, description="Skor project (1..5)")
    project_feedback: str = Field(..., min_length=1, description="Feedback singkat dan spesifik")


class OverallResult(BaseModel):
    cv_match_rate: float = Field(..., ge=0.0, le=1.0)
    cv_feedback: str = Field(..., min_length=1)
    project_score: float = Field(..., ge=1.0, le=5.0)
    project_feedback: str = Field(..., min_length=1)
    overall_summary: str = Field(..., min_length=1)


def _client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY tidak ditemukan dalam environment')
    genai.configure(api_key=api_key)
    return instructor.from_provider(
        "google/gemini-1.5-flash-latest",
        mode=instructor.Mode.GEMINI_JSON,
    )


def available() -> bool:
    return bool(os.getenv('GEMINI_API_KEY'))


def evaluate_cv(cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None) -> CVResult:
    """Evaluasi CV menjadi output terstruktur (Pydantic) menggunakan Instructor."""
    client = _client()
    snippets = "\n\n".join(context_snippets or [])
    prompt = f"""
Anda adalah sistem evaluasi CV untuk posisi: {job_title}.
Gunakan konteks relevan berikut jika ada:
{snippets}

Tugas:
- Nilai kecocokan CV terhadap role (0..1) dan berikan feedback ringkas namun informatif.
- Hindari informasi yang tidak ada di CV.
- Pastikan cv_match_rate berada pada rentang [0,1].

Kembalikan objek dengan field: cv_match_rate (float 0..1), cv_feedback (string).
CV:
---
{cv_text}
---
"""
    resp = client.messages.create(
        messages=[{"role": "user", "content": prompt}],
        response_model=CVResult,
        generation_config={"temperature": 0.2, "max_tokens": 1000},
    )
    return resp


def evaluate_project(report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None) -> ProjectResult:
    """Evaluasi Project Report terhadap Case Study Brief, hasil terstruktur (Pydantic)."""
    client = _client()
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

Kembalikan objek dengan field: project_score (float 1..5), project_feedback (string).
Report:
---
{report_text}
---
"""
    resp = client.messages.create(
        messages=[{"role": "user", "content": prompt}],
        response_model=ProjectResult,
        generation_config={"temperature": 0.2, "max_tokens": 1000},
    )
    return resp


def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Sintesis akhir menjadi OverallResult (Pydantic) menggunakan Instructor."""
    client = _client()
    prompt = f"""
Gabungkan hasil evaluasi CV dan Project menjadi ringkasan 3-5 kalimat.
Fokus: strengths, gaps, recommendations.

CV: rate={cv.cv_match_rate}, feedback={cv.cv_feedback}
Project: score={pr.project_score}, feedback={pr.project_feedback}
"""
    resp = client.messages.create(
        messages=[{"role": "user", "content": prompt}],
        response_model=OverallResult,
        generation_config={"temperature": 0.3, "max_tokens": 800},
    )
    return resp