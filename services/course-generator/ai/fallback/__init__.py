"""
AI Fallback Implementations

Fallback implementations for AI services when external APIs are unavailable.
"""

from .fallback_syllabus import FallbackSyllabusGenerator
from .fallback_slide import FallbackSlideGenerator
from .fallback_quiz import FallbackQuizGenerator
from .fallback_chat import FallbackChatGenerator

__all__ = [
    "FallbackSyllabusGenerator",
    "FallbackSlideGenerator",
    "FallbackQuizGenerator",
    "FallbackChatGenerator"
]