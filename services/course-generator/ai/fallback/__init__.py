"""
AI Fallback Implementations

Fallback implementations for AI services when external APIs are unavailable.
"""

from ai.fallback.fallback_syllabus import FallbackSyllabusGenerator
from ai.fallback.fallback_slide import FallbackSlideGenerator
from ai.fallback.fallback_quiz import FallbackQuizGenerator
from ai.fallback.fallback_chat import FallbackChatGenerator

__all__ = [
    "FallbackSyllabusGenerator",
    "FallbackSlideGenerator",
    "FallbackQuizGenerator",
    "FallbackChatGenerator"
]