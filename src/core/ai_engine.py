"""
AI Engine Module untuk Evaluasi CV dan Project menggunakan Gemini + Instructor
No dummy processes or fallbacks - only retry mechanisms for reliability.
"""

import os
import warnings
import logging
import time
import random
from typing import Optional, List, Any
import instructor

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment
except Exception:
    pass  # error loading .env file, use system environment

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
    logger.error("Instructor library is required. Please install it: pip install instructor")
    raise RuntimeError("Instructor library is required")

try:
    import google.generativeai as genai

    genaiAvailable = True
    logger.info("Google Generative AI library loaded successfully")
except ImportError:
    logger.error("Google Generative AI library is required. Please install it: pip install google-generativeai")
    raise RuntimeError("Google Generative AI library is required")

# Check API key availability
if os.getenv("GEMINI_API_KEY"):
    geminiApiKey = True
    logger.info("GEMINI_API_KEY found in environment")
else:
    logger.error("GEMINI_API_KEY is required in environment variables")
    raise RuntimeError("GEMINI_API_KEY is required in environment variables")


# CV Evaluation Parameters (each scored 1-5) - Based on requirements
class CVEvaluationParams(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    technical_skills_match: int = Field(
        ...,
        ge=1,
        le=5,
        description="Technical Skills Match (backend, databases, APIs, cloud, AI/LLM exposure) - Score 1-5",
        examples=[4]
    )
    experience_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Experience Level (years, project complexity) - Score 1-5",
        examples=[3]
    )
    relevant_achievements: int = Field(
        ...,
        ge=1,
        le=5,
        description="Relevant Achievements (impact, scale) - Score 1-5",
        examples=[4]
    )
    cultural_fit: int = Field(
        ...,
        ge=1,
        le=5,
        description="Cultural Fit (communication, learning attitude) - Score 1-5",
        examples=[4]
    )

    @field_validator('technical_skills_match', 'experience_level', 'relevant_achievements', 'cultural_fit')
    @classmethod
    def validate_scores(cls, v):
        """Ensure scores are integers"""
        if not isinstance(v, int):
            raise ValueError('Scores must be integers')
        return v

    @property
    def average_score(self) -> float:
        """Calculate average score for quick reference"""
        return sum([
            self.technical_skills_match,
            self.experience_level,
            self.relevant_achievements,
            self.cultural_fit
        ]) / 4.0


class CVResult(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    cv_match_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall CV match rate (0..1) - aggregated from parameters",
        examples=[0.82]
    )
    cv_feedback: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Comprehensive feedback on CV evaluation",
        examples=["Strong in backend and cloud, limited AI integration experience..."]
    )

    @field_validator('cv_match_rate')
    @classmethod
    def validate_match_rate(cls, v):
        """Validate match rate is within reasonable bounds"""
        if not isinstance(v, (int, float)):
            raise ValueError('Match rate must be a number')
        if v < 0 or v > 1:
            raise ValueError('Match rate must be between 0 and 1')
        return round(float(v), 2)  # Round to 2 decimal places per requirement format

    @field_validator('cv_feedback')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields are not empty or just whitespace"""
        if not isinstance(v, str):
            raise ValueError('Text fields must be strings')
        if not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()

    @property
    def match_percentage(self) -> int:
        """Convert match rate to percentage for display"""
        return int(self.cv_match_rate * 100)

    @property
    def is_strong_match(self) -> bool:
        """Determine if this is a strong match (>= 0.7)"""
        return self.cv_match_rate >= 0.7


# Project Deliverable Evaluation Parameters (each scored 1-5) - Based on requirements
class ProjectEvaluationParams(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    correctness: int = Field(
        ...,
        ge=1,
        le=5,
        description="Correctness (meets requirements: prompt design, chaining, RAG, handling errors) - Score 1-5",
        examples=[5]
    )
    code_quality: int = Field(
        ...,
        ge=1,
        le=5,
        description="Code Quality (clean, modular, testable) - Score 1-5",
        examples=[4]
    )
    resilience: int = Field(
        ...,
        ge=1,
        le=5,
        description="Resilience (handles failures, retries) - Score 1-5",
        examples=[4]
    )
    documentation: int = Field(
        ...,
        ge=1,
        le=5,
        description="Documentation (clear README, explanation of trade-offs) - Score 1-5",
        examples=[3]
    )
    creativity_bonus: int = Field(
        ...,
        ge=1,
        le=5,
        description="Creativity/Bonus (optional improvements like authentication, deployment, dashboards) - Score 1-5",
        examples=[4]
    )

    @field_validator('correctness', 'code_quality', 'resilience', 'documentation', 'creativity_bonus')
    @classmethod
    def validate_scores(cls, v):
        """Ensure scores are integers"""
        if not isinstance(v, int):
            raise ValueError('Scores must be integers')
        return v

    @property
    def average_score(self) -> float:
        """Calculate average score for quick reference"""
        return sum([
            self.correctness,
            self.code_quality,
            self.resilience,
            self.documentation,
            self.creativity_bonus
        ]) / 5.0


class ProjectResult(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    project_score: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Overall project score (1..5) - aggregated from parameters",
        examples=[4.5]
    )
    project_feedback: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Comprehensive feedback on project evaluation",
        examples=["Meets prompt chaining requirements, lacks error handling robustness..."]
    )

    @field_validator('project_score')
    @classmethod
    def validate_project_score(cls, v):
        """Validate project score is within reasonable bounds"""
        if not isinstance(v, (int, float)):
            raise ValueError('Project score must be a number')
        if v < 1 or v > 5:
            raise ValueError('Project score must be between 1 and 5')
        return round(float(v), 1)  # Round to 1 decimal place per requirement format

    @field_validator('project_feedback')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields are not empty or just whitespace"""
        if not isinstance(v, str):
            raise ValueError('Text fields must be strings')
        if not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()

    @property
    def is_excellent(self) -> bool:
        """Determine if this is an excellent project (>= 4.0)"""
        return self.project_score >= 4.0

    @property
    def letter_grade(self) -> str:
        """Convert numeric score to letter grade"""
        if self.project_score >= 4.5:
            return "A+"
        elif self.project_score >= 4.0:
            return "A"
        elif self.project_score >= 3.5:
            return "B+"
        elif self.project_score >= 3.0:
            return "B"
        elif self.project_score >= 2.5:
            return "C+"
        elif self.project_score >= 2.0:
            return "C"
        else:
            return "D"


class OverallResult(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    cv_match_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall CV match rate (0..1) - aggregated from CV evaluation",
        examples=[0.82]
    )
    cv_feedback: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Comprehensive feedback on CV evaluation",
        examples=["Strong in backend and cloud, limited AI integration experience..."]
    )
    project_score: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Overall project score (1..5) - aggregated from project evaluation",
        examples=[4.5]
    )
    project_feedback: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Comprehensive feedback on project evaluation",
        examples=["Meets prompt chaining requirements, lacks error handling robustness..."]
    )
    overall_summary: str = Field(
        ...,
        min_length=20,
        max_length=5000,
        description="Overall summary combining CV and project evaluation",
        examples=["Good candidate fit, would benefit from deeper RAG knowledge..."]
    )

    @field_validator('cv_match_rate')
    @classmethod
    def validate_cv_match_rate(cls, v):
        """Validate CV match rate"""
        if not isinstance(v, (int, float)):
            raise ValueError('CV match rate must be a number')
        if v < 0 or v > 1:
            raise ValueError('CV match rate must be between 0 and 1')
        return round(float(v), 2)

    @field_validator('project_score')
    @classmethod
    def validate_project_score(cls, v):
        """Validate project score"""
        if not isinstance(v, (int, float)):
            raise ValueError('Project score must be a number')
        if v < 1 or v > 5:
            raise ValueError('Project score must be between 1 and 5')
        return round(float(v), 1)

    @field_validator('cv_feedback', 'project_feedback', 'overall_summary')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields are not empty or just whitespace"""
        if not isinstance(v, str):
            raise ValueError('Text fields must be strings')
        if not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()

    @property
    def overall_score(self) -> float:
        """Calculate combined overall score (0-100)"""
        cv_weight = 0.4  # 40% weight for CV
        project_weight = 0.6  # 60% weight for project

        cv_normalized = self.cv_match_rate * 100  # Convert to 0-100 scale
        project_normalized = (self.project_score / 5) * 100  # Convert to 0-100 scale

        return (cv_normalized * cv_weight) + (project_normalized * project_weight)

    @property
    def is_strong_candidate(self) -> bool:
        """Determine if this is a strong candidate overall"""
        return (
            self.cv_match_rate >= 0.7 and
            self.project_score >= 4.0
        )

    def to_api_response(self) -> dict:
        """Convert to API response format as specified in requirements"""
        return {
            "cv_match_rate": round(self.cv_match_rate, 2),
            "cv_feedback": self.cv_feedback,
            "project_score": round(self.project_score, 1),
            "project_feedback": self.project_feedback,
            "overall_summary": self.overall_summary
        }


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


def _retry_with_backoff(func, *args, max_retries=5, base_delay=1.0, **kwargs):
    """
    Enhanced retry function with exponential backoff for LLM API calls.
    No dummy processes - only retry mechanisms for reliability.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries (increased to 5)
        base_delay: Base delay in seconds
        *args, **kwargs: Arguments to pass to function

    Returns:
        Function result if successful

    Raises:
        RuntimeError: If all retries fail
    """
    last_exception = None
    retry_count = 0

    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Attempting LLM API call (attempt {attempt + 1}/{max_retries + 1})")
            result = func(*args, **kwargs)

            # Validate response on successful call
            _validate_llm_response(result, kwargs.get('response_model', None))

            if attempt > 0:
                logger.info(f"LLM API call succeeded after {attempt} retries")

            return result

        except Exception as e:
            last_exception = e
            retry_count += 1

            # Analyze error type to determine if retryable
            error_str = str(e).lower()

            # Google Gemini specific error patterns
            is_retryable = (
                "rate limit" in error_str or
                "429" in error_str or
                "timeout" in error_str or
                "deadline exceeded" in error_str or
                "500" in error_str or
                "503" in error_str or
                "502" in error_str or
                "resource exhausted" in error_str or
                "quota exceeded" in error_str or
                "billing" in error_str or
                "permission denied" in error_str or
                "bad gateway" in error_str or
                "service unavailable" in error_str or
                "temporarily unavailable" in error_str or
                "overloaded" in error_str
            )

            # Non-retryable errors (more specific check)
            if ("invalid request" in error_str or
                "bad request" in error_str or
                "authentication" in error_str or
                "authorization" in error_str or
                "forbidden" in error_str):
                is_retryable = False

            if not is_retryable:
                logger.error(f"Non-retryable error ({type(e).__name__}): {e}")
                raise RuntimeError(f"LLM API call failed with non-retryable error: {str(e)}")

            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) reached for LLM API call")
                raise RuntimeError(f"LLM API call failed after {max_retries} retries: {str(e)}")

            # Calculate exponential backoff with jitter to avoid thundering herd
            # For 429 errors, use longer delays
            if "429" in error_str or "resource exhausted" in error_str:
                delay = base_delay * (3 ** attempt) + random.uniform(2.0, 5.0)  # More aggressive backoff for rate limits
                delay = min(delay, 120)  # Cap at 2 minutes for rate limits
            else:
                delay = base_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                delay = min(delay, 60)  # Cap at 60 seconds for other errors

            logger.warning(f"LLM API call failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
            time.sleep(delay)

    raise RuntimeError(f"LLM API call failed after {retry_count} retries. Last error: {last_exception}")


def _validate_llm_response(response, expected_type):
    """
    Validate LLM response format and content.
    Ensures stable responses by validating structure and values.
    """
    if not response:
        raise RuntimeError("Empty LLM response received")

    # Basic type validation - handle None expected_type safely
    if expected_type and not isinstance(response, expected_type):
        expected_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
        actual_name = type(response).__name__ if hasattr(type(response), '__name__') else str(type(response))
        raise RuntimeError(f"Expected {expected_name}, got {actual_name}")

    # Field-specific validation based on model type
    if hasattr(response, 'model_dump'):
        # Pydantic V2 model
        data = response.model_dump()
    elif hasattr(response, 'dict'):
        # Fallback for older Pydantic versions
        data = response.dict()
    else:
        # For non-Pydantic responses
        data = response

    # Validate critical fields based on model type
    if expected_type == CVResult:
        if not isinstance(data.get('cv_match_rate'), (int, float)) or data['cv_match_rate'] < 0 or data['cv_match_rate'] > 1:
            raise RuntimeError("Invalid cv_match_rate in CV evaluation result")
        if not isinstance(data.get('cv_feedback'), str) or len(data['cv_feedback'].strip()) < 10:
            raise RuntimeError("Invalid cv_feedback in CV evaluation result")

    elif expected_type == ProjectResult:
        if not isinstance(data.get('project_score'), (int, float)) or data['project_score'] < 1 or data['project_score'] > 5:
            raise RuntimeError("Invalid project_score in Project evaluation result")
        if not isinstance(data.get('project_feedback'), str) or len(data['project_feedback'].strip()) < 10:
            raise RuntimeError("Invalid project_feedback in Project evaluation result")

    elif expected_type == OverallResult:
        if not isinstance(data.get('overall_summary'), str) or len(data['overall_summary'].strip()) < 20:
            raise RuntimeError("Invalid overall_summary in Overall result")
        if not isinstance(data.get('cv_match_rate'), (int, float)):
            raise RuntimeError("Invalid cv_match_rate in Overall result")
        if not isinstance(data.get('project_score'), (int, float)):
            raise RuntimeError("Invalid project_score in Overall result")

    # Safe logging with None handling
    type_name = expected_type.__name__ if (expected_type and hasattr(expected_type, '__name__')) else 'Unknown'
    logger.debug(f"LLM response validated successfully for {type_name}")
    return True


def available() -> bool:
    """Check if all LLM dependencies are available."""
    return instructorAvailable and genaiAvailable and geminiApiKey


def evaluate_cv(
    cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None
) -> CVResult:
    """
    Evaluasi CV menggunakan LLM dengan RAG context retrieval dan retry logic.
    Pipeline Step 1: CV Evaluation - Parse candidate's CV into structured data

    Args:
        cv_text: Text content of CV
        job_title: Target job title for evaluation
        context_snippets: RAG-retrieved context from Job Description and CV Scoring Rubrics

    Returns:
        CVResult: Structured evaluation result with cv_match_rate and cv_feedback

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

    def _evaluate_cv_internal():
        # Simulate random failure for testing (disabled in production)
        # if _simulate_llm_failure(failure_rate=0.0):  # Set to 0.0 for production
        #     raise RuntimeError("Simulated LLM failure for testing")

        client = _client()
        rag_context = "\n\n".join(context_snippets or [])

        # Lower temperature for stable scoring
        prompt = f"""
Anda adalah evaluator CV ahli untuk posisi "{job_title}".

KONTEKS SISTEM (RAG-retrieved dari Job Description dan CV Scoring Rubrics):
{rag_context}

TUGAS EVALUASI CV:
1. Parse CV kandidat berikut dan evaluasi berdasarkan 4 parameter (skor 1-5):
   - Technical Skills Match: backend, databases, APIs, cloud, AI/LLM exposure
   - Experience Level: years, project complexity
   - Relevant Achievements: impact, scale
   - Cultural Fit: communication, learning attitude

2. Hitung cv_match_rate (0.0-1.0) sebagai rata-rata skor dibagi 5

3. Berikan cv_feedback yang komprehensif

CV KANDIDAT:
---
{cv_text}
---

INSTRUKSI:
- Gunakan konteks sistem untuk mengevaluasi kesesuaian dengan job requirements
- Berikan skor yang konsisten dan objektif (1-5)
- Format response harus sesuai CVResult model
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=CVResult,
        )

        # Validate response
        _validate_llm_response(resp, CVResult)
        return resp

    try:
        # Use retry logic with more retries for rate limits
        return _retry_with_backoff(_evaluate_cv_internal, max_retries=5, base_delay=2.0)
    except Exception as e:
        logger.error(f"CV evaluation failed: {e}")
        raise RuntimeError(f"CV evaluation failed: {str(e)}")


def evaluate_project(
    report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None
) -> ProjectResult:
    """
    Evaluasi Project Report menggunakan LLM dengan RAG context retrieval dan retry logic.
    Pipeline Step 2: Project Report Evaluation - Parse candidate's Project Report into structured data

    Args:
        report_text: Text content of project report
        case_brief_text: Text content of case study brief
        context_snippets: RAG-retrieved context from Case Study Brief and Project Scoring Rubrics

    Returns:
        ProjectResult: Structured evaluation result with project_score and project_feedback

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

    def _evaluate_project_internal():
        client = _client()
        rag_context = "\n\n".join(context_snippets or [])

        prompt = f"""
Anda adalah evaluator Project Report ahli.

KONTEKS SISTEM (RAG-retrieved dari Case Study Brief dan Project Scoring Rubrics):
{rag_context}

CASE STUDY BRIEF (Requirements yang harus dipenuhi):
---
{case_brief_text}
---

TUGAS EVALUASI PROJECT:
1. Parse Project Report kandidat berikut dan evaluasi berdasarkan 5 parameter (skor 1-5):
   - Correctness: meets requirements (prompt design, chaining, RAG, handling errors)
   - Code Quality: clean, modular, testable
   - Resilience: handles failures, retries
   - Documentation: clear README, explanation of trade-offs
   - Creativity/Bonus: optional improvements (authentication, deployment, dashboards)

2. Hitung project_score (1.0-5.0) sebagai rata-rata skor

3. Berikan project_feedback yang komprehensif

PROJECT REPORT KANDIDAT:
---
{report_text}
---

INSTRUKSI:
- Evaluasi seberapa baik project memenuhi requirements di Case Study Brief
- Gunakan konteks sistem untuk scoring guidelines
- Berikan skor yang konsisten dan objektif (1-5)
- Format response harus sesuai ProjectResult model
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=ProjectResult,
        )

        # Validate response
        _validate_llm_response(resp, ProjectResult)
        return resp

    try:
        # Use retry logic with more retries for rate limits
        return _retry_with_backoff(_evaluate_project_internal, max_retries=5, base_delay=2.0)
    except Exception as e:
        logger.error(f"Project evaluation failed: {e}")
        raise RuntimeError(f"Project evaluation failed: {str(e)}")


def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """
    Sintesis akhir menggunakan LLM dengan retry logic - Final Analysis step.
    Pipeline Step 3: Final Analysis - Synthesize outputs from previous steps into concise overall_summary

    Args:
        cv: CV evaluation result from Step 1
        pr: Project evaluation result from Step 2

    Returns:
        OverallResult: Combined evaluation result with overall_summary

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

    def _synthesize_overall_internal():
        client = _client()

        prompt = f"""
Anda adalah evaluator senior yang akan mensintesis hasil evaluasi kandidat.

HASIL EVALUASI CV (Step 1):
- CV Match Rate: {cv.cv_match_rate:.2f}
- CV Feedback: {cv.cv_feedback}

HASIL EVALUASI PROJECT (Step 2):
- Project Score: {pr.project_score:.1f}
- Project Feedback: {pr.project_feedback}

TUGAS FINAL ANALYSIS:
1. Sintesis hasil CV dan Project evaluation menjadi overall_summary yang komprehensif
2. Identifikasi strengths dan gaps dari kedua evaluasi
3. Berikan insight apakah kandidat cocok untuk posisi ini
4. Buat kesimpulan yang jelas dan actionable

INSTRUKSI:
- Fokus pada kesimpulan yang terintegrasi antara CV dan project capabilities
- Berikan overall_summary yang ringkas namun informatif
- Format response harus sesuai OverallResult model
"""
        resp = client.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=OverallResult,
        )

        # Validate response
        _validate_llm_response(resp, OverallResult)
        return resp

    try:
        # Use retry logic with more retries for rate limits
        return _retry_with_backoff(_synthesize_overall_internal, max_retries=5, base_delay=2.0)
    except Exception as e:
        logger.error(f"Overall synthesis failed: {e}")
        raise RuntimeError(f"Overall synthesis failed: {str(e)}")
