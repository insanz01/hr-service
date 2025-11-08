"""
AI Engine Module untuk Evaluasi CV dan Project menggunakan Gemini + Instructor
"""

import os
import warnings
import logging
from typing import Optional, List, Any
import instructor

from pydantic import BaseModel, Field

# Suppress SSL resource warnings
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*SSL.*")

# Setup logging
logger = logging.getLogger(__name__)

# Global variables untuk availability status
instructorAvailable = False
genaiAvailable = False
geminiApiKey = False


# Try to import dependencies with proper error handling
try:
    instructorAvailable = True
    logger.info("Instructor library loaded successfully")
except ImportError:
    logger.warning(
        "Instructor tidak terinstall. AI evaluation akan menggunakan fallback."
    )

try:
    import google.generativeai as genai

    genaiAvailable = True
    logger.info("Google Generative AI library loaded successfully")
except ImportError:
    logger.warning(
        "Google Generative AI tidak terinstall. AI evaluation akan menggunakan fallback."
    )

# Check API key availability
if os.getenv("GEMINI_API_KEY"):
    geminiApiKey = True
    logger.info("GEMINI_API_KEY found in environment")
else:
    logger.warning(
        "GEMINI_API_KEY tidak ditemukan. AI evaluation akan menggunakan fallback."
    )


# CV Evaluation Parameters (each scored 1-5)
class CVEvaluationParams(BaseModel):
    technical_skills_match: int = Field(
        ...,
        ge=1,
        le=5,
        description="Technical Skills Match (backend, databases, APIs, cloud, AI/LLM exposure) - Score 1-5",
    )
    experience_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Experience Level (years, project complexity) - Score 1-5",
    )
    relevant_achievements: int = Field(
        ..., ge=1, le=5, description="Relevant Achievements (impact, scale) - Score 1-5"
    )
    cultural_fit: int = Field(
        ...,
        ge=1,
        le=5,
        description="Cultural Fit (communication, learning attitude) - Score 1-5",
    )


class CVResult(BaseModel):
    evaluation_params: CVEvaluationParams
    cv_match_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall CV match rate (0..1) - calculated from params",
    )
    cv_feedback: str = Field(
        ..., min_length=1, description="Comprehensive feedback on CV evaluation"
    )
    detailed_scores: str = Field(
        ..., min_length=1, description="Detailed breakdown of scores for each parameter"
    )


# Project Deliverable Evaluation Parameters (each scored 1-5)
class ProjectEvaluationParams(BaseModel):
    correctness: int = Field(
        ...,
        ge=1,
        le=5,
        description="Correctness (meets requirements: prompt design, chaining, RAG, handling errors) - Score 1-5",
    )
    code_quality: int = Field(
        ...,
        ge=1,
        le=5,
        description="Code Quality (clean, modular, testable) - Score 1-5",
    )
    resilience: int = Field(
        ...,
        ge=1,
        le=5,
        description="Resilience (handles failures, retries) - Score 1-5",
    )
    documentation: int = Field(
        ...,
        ge=1,
        le=5,
        description="Documentation (clear README, explanation of trade-offs) - Score 1-5",
    )
    creativity_bonus: int = Field(
        ...,
        ge=1,
        le=5,
        description="Creativity/Bonus (optional improvements like authentication, deployment, dashboards) - Score 1-5",
    )


class ProjectResult(BaseModel):
    evaluation_params: ProjectEvaluationParams
    project_score: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Overall project score (1..5) - calculated from params",
    )
    project_feedback: str = Field(
        ..., min_length=1, description="Comprehensive feedback on project evaluation"
    )
    detailed_scores: str = Field(
        ..., min_length=1, description="Detailed breakdown of scores for each parameter"
    )


class OverallResult(BaseModel):
    cv_result: CVEvaluationParams
    project_result: ProjectEvaluationParams
    cv_match_rate: float = Field(..., ge=0.0, le=1.0)
    project_score: float = Field(..., ge=1.0, le=5.0)
    cv_feedback: str = Field(..., min_length=1)
    project_feedback: str = Field(..., min_length=1)
    detailed_cv_scores: str = Field(..., min_length=1)
    detailed_project_scores: str = Field(..., min_length=1)
    overall_summary: str = Field(..., min_length=1)
    final_recommendation: str = Field(..., min_length=1)


def _client() -> Any:
    """
    Create and return Gemini client with proper error handling.
    Returns: instructor client configured for Gemini
    """
    if not instructorAvailable:
        raise RuntimeError("Instructor tidak tersedia")
    if not genaiAvailable:
        raise RuntimeError("Google Generative AI tidak tersedia")
    if not geminiApiKey:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan dalam environment")

    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is empty or not set")

        genai.configure(api_key=api_key)

        # Create Gemini model - use standard model name
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Use instructor.from_gemini with correct parameter order
        return instructor.from_gemini(
            model,
            mode=instructor.Mode.GEMINI_JSON,
        )
    except Exception as e:
        logger.error(f"Error creating Gemini client: {e}")
        raise RuntimeError(f"Failed to create Gemini client: {str(e)}")


def available() -> bool:
    """Check if all LLM dependencies are available."""
    return instructorAvailable and genaiAvailable and geminiApiKey


def evaluate_cv(
    cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None
) -> CVResult:
    """
    Evaluasi CV menjadi output terstruktur (Pydantic) menggunakan Instructor.

    Args:
        cv_text: Text content of CV
        job_title: Target job title for evaluation
        context_snippets: Optional list of context snippets for RAG

    Returns:
        CVResult: Structured evaluation result

    Raises:
        RuntimeError: If AI services are not available or evaluation fails
    """
    if not available():
        raise RuntimeError(
            "AI services not available. Please ensure Instructor, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not cv_text.strip():
        raise ValueError("CV text cannot be empty")

    if not job_title.strip():
        raise ValueError("Job title cannot be empty")

    try:
        client = _client()
        snippets = "\n\n".join(context_snippets or [])
        prompt = f"""
Anda adalah sistem evaluasi CV untuk posisi: {job_title}.
Gunakan konteks relevan berikut jika ada:
{snippets}

Tugas:
- Evaluasi CV berdasarkan 4 parameter berikut (skor 1-5):
  1. Technical Skills Match: backend, databases, APIs, cloud, AI/LLM exposure
  2. Experience Level: years, project complexity
  3. Relevant Achievements: impact, scale
  4. Cultural Fit: communication, learning attitude

- Berikan skor untuk setiap parameter (1-5)
- Hitung cv_match_rate sebagai rata-rata skor dibagi 5 (0..1)
- Berikan feedback komprehensif tentang evaluasi CV
- Berikan breakdown detail untuk setiap skor

Kembalikan objek CVResult dengan semua field yang diperlukan.
CV:
---
{cv_text}
---
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=CVResult,
        )
        return resp
    except Exception as e:
        logger.error(f"CV evaluation failed: {e}")
        raise RuntimeError(f"CV evaluation failed: {str(e)}")


def evaluate_project(
    report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None
) -> ProjectResult:
    """
    Evaluasi Project Report terhadap Case Study Brief, hasil terstruktur (Pydantic).

    Args:
        report_text: Text content of project report
        case_brief_text: Text content of case study brief
        context_snippets: Optional list of context snippets for RAG

    Returns:
        ProjectResult: Structured evaluation result

    Raises:
        RuntimeError: If AI services are not available or evaluation fails
    """
    if not available():
        raise RuntimeError(
            "AI services not available. Please ensure Instructor, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not report_text.strip():
        raise ValueError("Report text cannot be empty")

    if not case_brief_text.strip():
        raise ValueError("Case brief text cannot be empty")

    try:
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
- Evaluasi project berdasarkan 5 parameter berikut (skor 1-5):
  1. Correctness: meets requirements (prompt design, chaining, RAG, handling errors)
  2. Code Quality: clean, modular, testable
  3. Resilience: handles failures, retries
  4. Documentation: clear README, explanation of trade-offs
  5. Creativity/Bonus: optional improvements (authentication, deployment, dashboards)

- Berikan skor untuk setiap parameter (1-5)
- Hitung project_score sebagai rata-rata skor (1..5)
- Berikan feedback komprehensif tentang evaluasi project
- Berikan breakdown detail untuk setiap skor

Kembalikan objek ProjectResult dengan semua field yang diperlukan.
Report:
---
{report_text}
---
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=ProjectResult,
        )
        return resp
    except Exception as e:
        logger.error(f"Project evaluation failed: {e}")
        raise RuntimeError(f"Project evaluation failed: {str(e)}")


def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """
    Sintesis akhir menjadi OverallResult (Pydantic) menggunakan Instructor.

    Args:
        cv: CV evaluation result
        pr: Project evaluation result

    Returns:
        OverallResult: Combined evaluation result

    Raises:
        RuntimeError: If AI services are not available or synthesis fails
    """
    if not available():
        raise RuntimeError(
            "AI services not available. Please ensure Instructor, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not isinstance(cv, CVResult):
        raise TypeError("cv must be a CVResult instance")

    if not isinstance(pr, ProjectResult):
        raise TypeError("pr must be a ProjectResult instance")

    try:
        client = _client()
        prompt = f"""
Gabungkan hasil evaluasi CV dan Project menjadi sintesis komprehensif.

Data CV:
- Match Rate: {cv.cv_match_rate}
- Feedback: {cv.cv_feedback}
- Detailed Scores: {cv.detailed_scores}
- Technical Skills: {cv.evaluation_params.technical_skills_match}/5
- Experience Level: {cv.evaluation_params.experience_level}/5
- Relevant Achievements: {cv.evaluation_params.relevant_achievements}/5
- Cultural Fit: {cv.evaluation_params.cultural_fit}/5

Data Project:
- Score: {pr.project_score}
- Feedback: {pr.project_feedback}
- Detailed Scores: {pr.detailed_scores}
- Correctness: {pr.evaluation_params.correctness}/5
- Code Quality: {pr.evaluation_params.code_quality}/5
- Resilience: {pr.evaluation_params.resilience}/5
- Documentation: {pr.evaluation_params.documentation}/5
- Creativity/Bonus: {pr.evaluation_params.creativity_bonus}/5

Tugas:
- Buat overall_summary yang menggabungkan strengths dan gaps dari kedua evaluasi
- Berikan final_recommendation yang jelas (hire/reject/consider)
- Sertakan semua detail evaluasi di output

Kembalikan objek OverallResult dengan semua field yang diperlukan.
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=OverallResult,
        )
        return resp
    except Exception as e:
        logger.error(f"Overall synthesis failed: {e}")
        raise RuntimeError(f"Overall synthesis failed: {str(e)}")
