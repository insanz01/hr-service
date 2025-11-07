import os
from typing import Optional, List

from pydantic import BaseModel, Field

# Global variables untuk availability status
_INSTRUCTOR_AVAILABLE = False
_GENAI_AVAILABLE = False
_GEMINI_API_KEY_AVAILABLE = False

# Try to import dependencies with proper error handling
try:
    import instructor
    _INSTRUCTOR_AVAILABLE = True
except ImportError:
    print("⚠️  Instructor tidak terinstall. AI evaluation akan menggunakan fallback.")

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    print("⚠️  Google Generative AI tidak terinstall. AI evaluation akan menggunakan fallback.")

# Check API key availability
if os.getenv('GEMINI_API_KEY'):
    _GEMINI_API_KEY_AVAILABLE = True
else:
    print("⚠️  GEMINI_API_KEY tidak ditemukan. AI evaluation akan menggunakan fallback.")


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
    """Create and return Gemini client with proper error handling."""
    if not _INSTRUCTOR_AVAILABLE:
        raise RuntimeError('Instructor tidak tersedia')
    if not _GENAI_AVAILABLE:
        raise RuntimeError('Google Generative AI tidak tersedia')
    if not _GEMINI_API_KEY_AVAILABLE:
        raise RuntimeError('GEMINI_API_KEY tidak ditemukan dalam environment')

    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return instructor.from_provider(
        "google/gemini-1.5-flash-latest",
        mode=instructor.Mode.GEMINI_JSON,
    )


def available() -> bool:
    """Check if all LLM dependencies are available."""
    return _INSTRUCTOR_AVAILABLE and _GENAI_AVAILABLE and _GEMINI_API_KEY_AVAILABLE


def _fallback_evaluate_cv(cv_text: str, job_title: str) -> CVResult:
    """Fallback evaluation when AI is not available."""
    # Simple heuristic based evaluation
    text_length = len(cv_text)

    # Keywords untuk backend dan AI skills
    backend_keywords = ['python', 'java', 'node', 'api', 'database', 'sql', 'nosql', 'redis', 'docker']
    ai_keywords = ['ai', 'ml', 'machine learning', 'llm', 'openai', 'gemini', 'transformer', 'neural']

    cv_lower = cv_text.lower()
    backend_score = sum(1 for keyword in backend_keywords if keyword in cv_lower)
    ai_score = sum(1 for keyword in ai_keywords if keyword in cv_lower)

    # Calculate match rate based on keywords and text length
    base_score = min(0.3, text_length / 10000)  # Base score from text length
    backend_bonus = min(0.4, backend_score * 0.1)  # Bonus for backend skills
    ai_bonus = min(0.3, ai_score * 0.15)  # Bonus for AI skills

    cv_match_rate = min(1.0, base_score + backend_bonus + ai_bonus)

    # Generate feedback
    if cv_match_rate >= 0.8:
        feedback = f"CV sangat kuat untuk posisi {job_title} dengan kombinasi backend dan AI skills yang excellent."
    elif cv_match_rate >= 0.6:
        feedback = f"CV baik untuk posisi {job_title} dengan solid foundation. Perlu lebih banyak AI/ML experience."
    elif cv_match_rate >= 0.4:
        feedback = f"CV menunjukkan potensi untuk {job_title}. Perlu加强 backend dan AI skills."
    else:
        feedback = f"CV memerlukan improvement signifikan untuk posisi {job_title}."

    return CVResult(cv_match_rate=cv_match_rate, cv_feedback=feedback)


def _fallback_evaluate_project(report_text: str, case_brief_text: str) -> ProjectResult:
    """Fallback project evaluation when AI is not available."""
    text_length = len(report_text)

    # Keywords untuk good implementation
    implementation_keywords = ['api', 'database', 'testing', 'error handling', 'async', 'queue', 'docker']
    ai_keywords = ['rag', 'vector', 'embedding', 'llm', 'prompt', 'ai', 'machine learning']

    report_lower = report_text.lower()
    impl_score = sum(1 for keyword in implementation_keywords if keyword in report_lower)
    ai_score = sum(1 for keyword in ai_keywords if keyword in report_lower)

    # Calculate project score
    base_score = min(2.0, text_length / 5000)  # Base score from text length
    impl_bonus = min(2.0, impl_score * 0.3)  # Bonus for implementation quality
    ai_bonus = min(1.0, ai_score * 0.2)  # Bonus for AI integration

    project_score = min(5.0, max(1.0, base_score + impl_bonus + ai_bonus))

    # Generate feedback
    if project_score >= 4.5:
        feedback = "Project implementation excellent dengan AI integration yang solid dan error handling yang baik."
    elif project_score >= 3.5:
        feedback = "Project implementation baik dengan struktur yang jelas. Perlu lebih sedikit improvement di AI integration."
    elif project_score >= 2.5:
        feedback = "Project implementation basic yang berfungsi. Perlu improvement signifikan di architecture dan AI features."
    else:
        feedback = "Project implementation memerlukan improvement fundamental di semua aspek."

    return ProjectResult(project_score=project_score, project_feedback=feedback)


def evaluate_cv(cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None) -> CVResult:
    """Evaluasi CV menjadi output terstruktur (Pydantic) menggunakan Instructor."""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback evaluation untuk CV")
        return _fallback_evaluate_cv(cv_text, job_title)

    try:
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
    except Exception as e:
        print(f"⚠️  AI evaluation failed: {e}. Menggunakan fallback evaluation.")
        return _fallback_evaluate_cv(cv_text, job_title)


def evaluate_project(report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None) -> ProjectResult:
    """Evaluasi Project Report terhadap Case Study Brief, hasil terstruktur (Pydantic)."""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback evaluation untuk Project")
        return _fallback_evaluate_project(report_text, case_brief_text)

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
    except Exception as e:
        print(f"⚠️  AI evaluation failed: {e}. Menggunakan fallback evaluation.")
        return _fallback_evaluate_project(report_text, case_brief_text)


def synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Sintesis akhir menjadi OverallResult (Pydantic) menggunakan Instructor."""
    if not available():
        print("⚠️  AI tidak tersedia, menggunakan fallback synthesis")
        return _fallback_synthesize_overall(cv, pr)

    try:
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
    except Exception as e:
        print(f"⚠️  AI synthesis failed: {e}. Menggunakan fallback synthesis.")
        return _fallback_synthesize_overall(cv, pr)


def _fallback_synthesize_overall(cv: CVResult, pr: ProjectResult) -> OverallResult:
    """Fallback synthesis when AI is not available."""
    # Simple template-based synthesis
    cv_score = cv.cv_match_rate
    project_score = pr.project_score

    if cv_score >= 0.8 and project_score >= 4.5:
        summary = f"Kandidat excellent dengan CV match rate {cv_score:.1f} dan project score {project_score:.1f}. Strong combination of backend expertise dan AI implementation skills. Highly recommended."
    elif cv_score >= 0.6 and project_score >= 3.5:
        summary = f"Kandidat solid dengan CV match rate {cv_score:.1f} dan project score {project_score:.1f}. Good foundation dengan room untuk improvement di AI integration. Recommended for consideration."
    elif cv_score >= 0.4 and project_score >= 2.5:
        summary = f"Kandidat developing dengan CV match rate {cv_score:.1f} dan project score {project_score:.1f}. Shows potential but needs more experience di backend systems dan AI technologies."
    else:
        summary = f"Kandidat entry level dengan CV match rate {cv_score:.1f} dan project score {project_score:.1f}. Requires significant development di technical skills dan project implementation."

    return OverallResult(
        cv_match_rate=cv.cv_match_rate,
        cv_feedback=cv.cv_feedback,
        project_score=pr.project_score,
        project_feedback=pr.project_feedback,
        overall_summary=summary
    )