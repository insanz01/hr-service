"""
AI Engine Manager - Manages between Instructor and Pydantic-AI implementations
"""

import os
import logging
from typing import Optional, List, Any
from enum import Enum

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment
except Exception:
    pass  # error loading .env file, use system environment

from .ai_engine import (
    CVEvaluationParams, CVResult, ProjectEvaluationParams,
    ProjectResult, OverallResult, available as instructor_available,
    evaluate_cv as instructor_evaluate_cv,
    evaluate_project as instructor_evaluate_project,
    synthesize_overall as instructor_synthesize_overall
)

# Try to import Pydantic-AI with graceful fallback
try:
    from .ai_engine_pydantic_ai import (
        CVEvaluationParams as PydanticAICVEvaluationParams,
        CVResult as PydanticAICVResult,
        ProjectEvaluationParams as PydanticAIProjectEvaluationParams,
        ProjectResult as PydanticAIProjectResult,
        OverallResult as PydanticAIOverallResult,
        available as pydantic_ai_available,
        evaluate_cv_sync as pydantic_ai_evaluate_cv,
        evaluate_project_sync as pydantic_ai_evaluate_project,
        synthesize_overall_sync as pydantic_ai_synthesize_overall
    )
    PYDANTIC_AI_IMPORT_SUCCESS = True
    logger = logging.getLogger(__name__)
    logger.info("Pydantic-AI imports successful")
except ImportError as e:
    PYDANTIC_AI_IMPORT_SUCCESS = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Pydantic-AI imports failed: {e}. Using Instructor-only mode.")

    # Create fallback functions
    def pydantic_ai_available():
        return False

    def pydantic_ai_evaluate_cv(*args, **kwargs):
        raise RuntimeError("Pydantic-AI not available")

    def pydantic_ai_evaluate_project(*args, **kwargs):
        raise RuntimeError("Pydantic-AI not available")

    def pydantic_ai_synthesize_overall(*args, **kwargs):
        raise RuntimeError("Pydantic-AI not available")

logger = logging.getLogger(__name__)


class AIEngineType(Enum):
    INSTRUCTOR = "instructor"
    PYDANTIC_AI = "pydantic_ai"
    AUTO = "auto"


class AIEngineManager:
    """
    Manager class that handles switching between Instructor and Pydantic-AI implementations
    """

    def __init__(self, preferred_engine: str = "auto"):
        self.preferred_engine = AIEngineType(preferred_engine.lower())
        self.current_engine = None
        self._determine_best_engine()

    def _determine_best_engine(self):
        """Determine the best available AI engine"""
        instructor_available_status = instructor_available()
        pydantic_ai_available_status = pydantic_ai_available() if PYDANTIC_AI_IMPORT_SUCCESS else False

        logger.info(f"Instructor available: {instructor_available_status}")
        logger.info(f"Pydantic-AI available: {pydantic_ai_available_status} (import success: {PYDANTIC_AI_IMPORT_SUCCESS})")

        if self.preferred_engine == AIEngineType.PYDANTIC_AI:
            if pydantic_ai_available_status and PYDANTIC_AI_IMPORT_SUCCESS:
                self.current_engine = AIEngineType.PYDANTIC_AI
                logger.info("Using Pydantic-AI engine (preferred)")
            elif instructor_available_status:
                self.current_engine = AIEngineType.INSTRUCTOR
                logger.warning("Pydantic-AI not available, falling back to Instructor")
            else:
                logger.error("No AI engine available")
                self.current_engine = None

        elif self.preferred_engine == AIEngineType.INSTRUCTOR:
            if instructor_available_status:
                self.current_engine = AIEngineType.INSTRUCTOR
                logger.info("Using Instructor engine (preferred)")
            elif pydantic_ai_available_status and PYDANTIC_AI_IMPORT_SUCCESS:
                self.current_engine = AIEngineType.PYDANTIC_AI
                logger.warning("Instructor not available, falling back to Pydantic-AI")
            else:
                logger.error("No AI engine available")
                self.current_engine = None

        else:  # AUTO
            # Prefer Pydantic-AI if both are available (it's more modern)
            if pydantic_ai_available_status and PYDANTIC_AI_IMPORT_SUCCESS and instructor_available_status:
                self.current_engine = AIEngineType.PYDANTIC_AI
                logger.info("Auto mode: Using Pydantic-AI (both available, preferring modern)")
            elif pydantic_ai_available_status and PYDANTIC_AI_IMPORT_SUCCESS:
                self.current_engine = AIEngineType.PYDANTIC_AI
                logger.info("Auto mode: Using Pydantic-AI (only Pydantic-AI available)")
            elif instructor_available_status:
                self.current_engine = AIEngineType.INSTRUCTOR
                logger.info("Auto mode: Using Instructor (only Instructor available)")
            else:
                logger.error("Auto mode: No AI engine available")
                self.current_engine = None

    def get_current_engine(self) -> str:
        """Get the current engine type"""
        return self.current_engine.value if self.current_engine else "none"

    def is_available(self) -> bool:
        """Check if any AI engine is available"""
        return self.current_engine is not None

    def evaluate_cv(self, cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None):
        """Evaluate CV using the current engine"""
        if not self.is_available():
            raise RuntimeError("No AI engine available")

        try:
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.debug("Evaluating CV with Pydantic-AI")
                return pydantic_ai_evaluate_cv(cv_text, job_title, context_snippets)
            else:  # INSTRUCTOR
                logger.debug("Evaluating CV with Instructor")
                return instructor_evaluate_cv(cv_text, job_title, context_snippets)
        except Exception as e:
            logger.error(f"CV evaluation failed with {self.current_engine.value}: {e}")
            # Try fallback engine if available
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS and instructor_available():
                logger.info("Attempting fallback to Instructor for CV evaluation")
                try:
                    return instructor_evaluate_cv(cv_text, job_title, context_snippets)
                except Exception as fallback_error:
                    logger.error(f"Instructor fallback also failed: {fallback_error}")
            elif self.current_engine == AIEngineType.INSTRUCTOR and pydantic_ai_available() and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.info("Attempting fallback to Pydantic-AI for CV evaluation")
                try:
                    return pydantic_ai_evaluate_cv(cv_text, job_title, context_snippets)
                except Exception as fallback_error:
                    logger.error(f"Pydantic-AI fallback also failed: {fallback_error}")

            raise RuntimeError(f"CV evaluation failed with all available engines: {str(e)}")

    def evaluate_project(self, report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None):
        """Evaluate Project using the current engine"""
        if not self.is_available():
            raise RuntimeError("No AI engine available")

        try:
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.debug("Evaluating project with Pydantic-AI")
                return pydantic_ai_evaluate_project(report_text, case_brief_text, context_snippets)
            else:  # INSTRUCTOR
                logger.debug("Evaluating project with Instructor")
                return instructor_evaluate_project(report_text, case_brief_text, context_snippets)
        except Exception as e:
            logger.error(f"Project evaluation failed with {self.current_engine.value}: {e}")
            # Try fallback engine if available
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS and instructor_available():
                logger.info("Attempting fallback to Instructor for project evaluation")
                try:
                    return instructor_evaluate_project(report_text, case_brief_text, context_snippets)
                except Exception as fallback_error:
                    logger.error(f"Instructor fallback also failed: {fallback_error}")
            elif self.current_engine == AIEngineType.INSTRUCTOR and pydantic_ai_available() and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.info("Attempting fallback to Pydantic-AI for project evaluation")
                try:
                    return pydantic_ai_evaluate_project(report_text, case_brief_text, context_snippets)
                except Exception as fallback_error:
                    logger.error(f"Pydantic-AI fallback also failed: {fallback_error}")

            raise RuntimeError(f"Project evaluation failed with all available engines: {str(e)}")

    def synthesize_overall(self, cv_result, project_result):
        """Synthesize overall result using the current engine"""
        if not self.is_available():
            raise RuntimeError("No AI engine available")

        try:
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.debug("Synthesizing overall result with Pydantic-AI")
                return pydantic_ai_synthesize_overall(cv_result, project_result)
            else:  # INSTRUCTOR
                logger.debug("Synthesizing overall result with Instructor")
                return instructor_synthesize_overall(cv_result, project_result)
        except Exception as e:
            logger.error(f"Overall synthesis failed with {self.current_engine.value}: {e}")
            # Try fallback engine if available
            if self.current_engine == AIEngineType.PYDANTIC_AI and PYDANTIC_AI_IMPORT_SUCCESS and instructor_available():
                logger.info("Attempting fallback to Instructor for overall synthesis")
                try:
                    return instructor_synthesize_overall(cv_result, project_result)
                except Exception as fallback_error:
                    logger.error(f"Instructor fallback also failed: {fallback_error}")
            elif self.current_engine == AIEngineType.INSTRUCTOR and pydantic_ai_available() and PYDANTIC_AI_IMPORT_SUCCESS:
                logger.info("Attempting fallback to Pydantic-AI for overall synthesis")
                try:
                    return pydantic_ai_synthesize_overall(cv_result, project_result)
                except Exception as fallback_error:
                    logger.error(f"Pydantic-AI fallback also failed: {fallback_error}")

            raise RuntimeError(f"Overall synthesis failed with all available engines: {str(e)}")


# Global instance for easy access
_engine_manager = None


def get_engine_manager() -> AIEngineManager:
    """Get the global AI engine manager instance"""
    global _engine_manager
    if _engine_manager is None:
        preferred_engine = os.getenv("AI_ENGINE_PREFERENCE", "auto")
        _engine_manager = AIEngineManager(preferred_engine)
    return _engine_manager


def evaluate_cv(cv_text: str, job_title: str, context_snippets: Optional[List[str]] = None):
    """Wrapper function for CV evaluation"""
    return get_engine_manager().evaluate_cv(cv_text, job_title, context_snippets)


def evaluate_project(report_text: str, case_brief_text: str, context_snippets: Optional[List[str]] = None):
    """Wrapper function for Project evaluation"""
    return get_engine_manager().evaluate_project(report_text, case_brief_text, context_snippets)


def synthesize_overall(cv_result, project_result):
    """Wrapper function for overall synthesis"""
    return get_engine_manager().synthesize_overall(cv_result, project_result)


def available() -> bool:
    """Check if any AI engine is available"""
    return get_engine_manager().is_available()


def get_engine_info() -> dict:
    """Get information about current AI engine"""
    manager = get_engine_manager()
    return {
        "current_engine": manager.get_current_engine(),
        "available": manager.is_available(),
        "preferred_engine": manager.preferred_engine.value,
        "instructor_available": instructor_available(),
        "pydantic_ai_available": pydantic_ai_available() if PYDANTIC_AI_IMPORT_SUCCESS else False,
        "pydantic_ai_import_success": PYDANTIC_AI_IMPORT_SUCCESS
    }