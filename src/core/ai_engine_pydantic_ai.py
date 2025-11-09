"""
AI Engine Module dengan Pydantic-AI untuk Evaluasi CV dan Project menggunakan Gemini
"""

import os
import warnings
import logging
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment
except Exception:
    pass  # error loading .env file, use system environment

# Pydantic-AI imports
import pydantic_ai
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

# Suppress SSL resource warnings
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*SSL.*")

# Setup logging
logger = logging.getLogger(__name__)

# Global variables untuk availability status
pydanticAiAvailable = False
genaiAvailable = False
geminiApiKey = False


# Try to import dependencies with proper error handling
try:
    from pydantic_ai import Agent, RunContext
    pydanticAiAvailable = True
    logger.info("Pydantic-AI library loaded successfully")
except ImportError:
    logger.warning(
        "Pydantic-AI tidak terinstall. AI evaluation akan menggunakan fallback."
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


def _create_cv_agent() -> Agent:
    """
    Create and return Pydantic-AI agent for CV evaluation.
    Returns: Agent configured for CV evaluation
    """
    if not pydanticAiAvailable:
        raise RuntimeError("Pydantic-AI tidak tersedia")
    if not genaiAvailable:
        raise RuntimeError("Google Generative AI tidak tersedia")
    if not geminiApiKey:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan dalam environment")

    try:
        import google.generativeai as genai
        from pydantic_ai import Agent

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is empty or not set")

        genai.configure(api_key=api_key)

        # Create Pydantic-AI agent with Gemini model
        agent = Agent(
            'gemini-2.0-flash-exp',
            result_type=CVResult,
            system_prompt="""Anda adalah sistem evaluasi CV yang ahli untuk posisi teknologi.

Tugas Anda:
1. Evaluasi CV berdasarkan 4 parameter (skor 1-5):
   - Technical Skills Match: backend, databases, APIs, cloud, AI/LLM exposure
   - Experience Level: years, project complexity
   - Relevant Achievements: impact, scale
   - Cultural Fit: communication, learning attitude

2. Hitung cv_match_rate sebagai rata-rata skor dibagi 5 (0..1)

3. Berikan feedback komprehensif dan breakdown detail

Pastikan semua field terisi dengan valid dan sesuai konteks evaluasi.""",
        )

        return agent
    except Exception as e:
        logger.error(f"Error creating CV agent: {e}")
        raise RuntimeError(f"Failed to create CV agent: {str(e)}")


def _create_project_agent() -> Agent:
    """
    Create and return Pydantic-AI agent for Project evaluation.
    Returns: Agent configured for Project evaluation
    """
    if not pydanticAiAvailable:
        raise RuntimeError("Pydantic-AI tidak tersedia")
    if not genaiAvailable:
        raise RuntimeError("Google Generative AI tidak tersedia")
    if not geminiApiKey:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan dalam environment")

    try:
        import google.generativeai as genai
        from pydantic_ai import Agent

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is empty or not set")

        genai.configure(api_key=api_key)

        # Create Pydantic-AI agent with Gemini model
        agent = Agent(
            'gemini-2.0-flash-exp',
            result_type=ProjectResult,
            system_prompt="""Anda adalah evaluator Project Report yang ahli terhadap Case Study Brief.

Tugas Anda:
1. Evaluasi project berdasarkan 5 parameter (skor 1-5):
   - Correctness: meets requirements (prompt design, chaining, RAG, handling errors)
   - Code Quality: clean, modular, testable
   - Resilience: handles failures, retries
   - Documentation: clear README, explanation of trade-offs
   - Creativity/Bonus: optional improvements (authentication, deployment, dashboards)

2. Hitung project_score sebagai rata-rata skor (1..5)

3. Berikan feedback komprehensif dan breakdown detail

Pastikan semua field terisi dengan valid dan sesuai konteks evaluasi.""",
        )

        return agent
    except Exception as e:
        logger.error(f"Error creating Project agent: {e}")
        raise RuntimeError(f"Failed to create Project agent: {str(e)}")


def _create_overall_agent() -> Agent:
    """
    Create and return Pydantic-AI agent for Overall synthesis.
    Returns: Agent configured for Overall synthesis
    """
    if not pydanticAiAvailable:
        raise RuntimeError("Pydantic-AI tidak tersedia")
    if not genaiAvailable:
        raise RuntimeError("Google Generative AI tidak tersedia")
    if not geminiApiKey:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan dalam environment")

    try:
        import google.generativeai as genai
        from pydantic_ai import Agent

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is empty or not set")

        genai.configure(api_key=api_key)

        # Create Pydantic-AI agent with Gemini model
        agent = Agent(
            'gemini-2.0-flash-exp',
            result_type=OverallResult,
            system_prompt="""Anda adalah evaluator senior yang menggabungkan hasil evaluasi CV dan Project.

Tugas Anda:
1. Sintesis hasil CV dan Project menjadi overall_summary yang komprehensif
2. Identifikasi strengths dan gaps dari kedua evaluasi
3. Berikan final_recommendation yang jelas (hire/reject/consider)
4. Sertakan semua detail evaluasi di output

Gabungkan insight dari CV evaluation dan Project evaluation untuk memberikan rekomendasi hiring yang terbaik.""",
        )

        return agent
    except Exception as e:
        logger.error(f"Error creating Overall agent: {e}")
        raise RuntimeError(f"Failed to create Overall agent: {str(e)}")


def available() -> bool:
    """Check if all LLM dependencies are available."""
    return pydanticAiAvailable and genaiAvailable and geminiApiKey


async def evaluate_cv(
    cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None
) -> CVResult:
    """
    Evaluasi CV menjadi output terstruktur (Pydantic) menggunakan Pydantic-AI.

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
            "AI services not available. Please ensure Pydantic-AI, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not cv_text.strip():
        raise ValueError("CV text cannot be empty")

    if not job_title.strip():
        raise ValueError("Job title cannot be empty")

    try:
        agent = _create_cv_agent()
        snippets = "\n\n".join(context_snippets or [])

        user_prompt = f"""
Evaluasi CV untuk posisi: {job_title}

Konteks relevan (jika ada):
{snippets}

CV Text:
---
{cv_text}
---

Lakukan evaluasi berdasarkan parameter yang telah ditentukan."""

        result = await agent.run(user_prompt)
        return result.data
    except Exception as e:
        logger.error(f"CV evaluation failed: {e}")
        raise RuntimeError(f"CV evaluation failed: {str(e)}")


async def evaluate_project(
    report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None
) -> ProjectResult:
    """
    Evaluasi Project Report terhadap Case Study Brief, hasil terstruktur (Pydantic) menggunakan Pydantic-AI.

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
            "AI services not available. Please ensure Pydantic-AI, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not report_text.strip():
        raise ValueError("Report text cannot be empty")

    if not case_brief_text.strip():
        raise ValueError("Case brief text cannot be empty")

    try:
        agent = _create_project_agent()
        snippets = "\n\n".join(context_snippets or [])

        user_prompt = f"""
Evaluasi Project Report terhadap Case Study Brief.

Konteks relevan (jika ada):
{snippets}

Case Study Brief:
---
{case_brief_text}
---

Project Report:
---
{report_text}
---

Lakukan evaluasi berdasarkan parameter yang telah ditentukan."""

        result = await agent.run(user_prompt)
        return result.data
    except Exception as e:
        logger.error(f"Project evaluation failed: {e}")
        raise RuntimeError(f"Project evaluation failed: {str(e)}")


async def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """
    Sintesis akhir menjadi OverallResult (Pydantic) menggunakan Pydantic-AI.

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
            "AI services not available. Please ensure Pydantic-AI, Google Generative AI, and GEMINI_API_KEY are properly configured."
        )

    if not isinstance(cv, CVResult):
        raise TypeError("cv must be a CVResult instance")

    if not isinstance(pr, ProjectResult):
        raise TypeError("pr must be a ProjectResult instance")

    try:
        agent = _create_overall_agent()

        user_prompt = f"""
Data Evaluasi CV:
- Match Rate: {cv.cv_match_rate}
- Feedback: {cv.cv_feedback}
- Detailed Scores: {cv.detailed_scores}
- Technical Skills: {cv.evaluation_params.technical_skills_match}/5
- Experience Level: {cv.evaluation_params.experience_level}/5
- Relevant Achievements: {cv.evaluation_params.relevant_achievements}/5
- Cultural Fit: {cv.evaluation_params.cultural_fit}/5

Data Evaluasi Project:
- Score: {pr.project_score}
- Feedback: {pr.project_feedback}
- Detailed Scores: {pr.detailed_scores}
- Correctness: {pr.evaluation_params.correctness}/5
- Code Quality: {pr.evaluation_params.code_quality}/5
- Resilience: {pr.evaluation_params.resilience}/5
- Documentation: {pr.evaluation_params.documentation}/5
- Creativity/Bonus: {pr.evaluation_params.creativity_bonus}/5

Lakukan sintesis komprehensif dari kedua evaluasi untuk memberikan rekomendasi hiring terbaik."""

        result = await agent.run(user_prompt)
        return result.data
    except Exception as e:
        logger.error(f"Overall synthesis failed: {e}")
        raise RuntimeError(f"Overall synthesis failed: {str(e)}")


# Synchronous wrapper functions for backward compatibility
def evaluate_cv_sync(cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None) -> CVResult:
    """Synchronous wrapper for evaluate_cv"""
    import asyncio
    return asyncio.run(evaluate_cv(cv_text, job_title, context_snippets))


def evaluate_project_sync(report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None) -> ProjectResult:
    """Synchronous wrapper for evaluate_project"""
    import asyncio
    return asyncio.run(evaluate_project(report_text, case_brief_text, context_snippets))


def synthesize_overall_sync(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Synchronous wrapper for synthesize_overall"""
    import asyncio
    return asyncio.run(synthesize_overall(cv, pr))