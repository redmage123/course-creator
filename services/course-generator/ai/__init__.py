"""
Course Generator AI Module

This module contains all AI integration components for the course generation system.
It handles communication with AI services, prompt management, and content generation
with proper fallback mechanisms.
"""

from ai.client import AIClient
from ai.prompts import PromptTemplates
from ai.generators import (
    SlideGenerator,
    ExerciseGenerator,
    QuizGenerator,
    SyllabusGenerator,
    ChatGenerator
)
from ai.fallback import (
    FallbackSlideGenerator,
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
    "FallbackQuizGenerator",
    "FallbackSyllabusGenerator"
]