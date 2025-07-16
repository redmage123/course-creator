"""
Course Generator AI Module

This module contains all AI integration components for the course generation system.
It handles communication with AI services, prompt management, and content generation
with proper fallback mechanisms.
"""

from .client import AIClient
from .prompts import PromptTemplates
from .generators import (
    SlideGenerator,
    ExerciseGenerator,
    QuizGenerator,
    SyllabusGenerator,
    ChatGenerator
)
from .fallback import (
    FallbackSlideGenerator,
    FallbackExerciseGenerator,
    FallbackQuizGenerator,
    FallbackSyllabusGenerator
)

__all__ = [
    "AIClient",
    "PromptTemplates",
    "SlideGenerator",
    "ExerciseGenerator", 
    "QuizGenerator",
    "SyllabusGenerator",
    "ChatGenerator",
    "FallbackSlideGenerator",
    "FallbackExerciseGenerator",
    "FallbackQuizGenerator",
    "FallbackSyllabusGenerator"
]