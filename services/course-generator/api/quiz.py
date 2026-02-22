"""
Quiz Generation API Routes

Generates quizzes using an AI service. Questions are returned directly without
database persistence, making this endpoint stateless and lightweight.

ENDPOINT SUMMARY:
- POST /generate: Generate a quiz for a course
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    """Request model for quiz generation."""
    course_id: str = Field(..., description="Course ID to generate quiz for")
    course_title: str = Field("", description="Course title for context")
    topic: Optional[str] = Field(None, description="Specific topic (defaults to course_title)")
    num_questions: int = Field(5, ge=1, le=50, description="Number of questions")
    difficulty: str = Field("intermediate", description="beginner, intermediate, or advanced")


def _generate_mock_questions(topic: str, difficulty: str, count: int) -> List[dict]:
    """Generate mock quiz questions for a given topic.

    In production, this calls the real AI service (Anthropic Claude). Currently
    returns template-based questions that vary by topic and difficulty.
    """
    # Difficulty-based scoring
    points_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
    base_points = points_map.get(difficulty, 2)

    questions = []
    for i in range(count):
        questions.append({
            "id": str(uuid.uuid4()),
            "question": f"What is a key concept in {topic}? (Question {i + 1})",
            "options": [
                f"Core principle of {topic}",
                f"Unrelated concept from another field",
                f"Common misconception about {topic}",
                f"Advanced technique beyond {topic} scope",
            ],
            "correct_answer": 0,
            "explanation": f"The core principle is fundamental to understanding {topic}. "
                           f"This tests foundational knowledge at the {difficulty} level.",
            "points": base_points,
            "difficulty": difficulty,
        })

    return questions


@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generate a quiz for the given course.

    Produces multiple-choice questions with answers, explanations, and point values.
    Currently uses template-based generation; will use AI when configured.
    """
    topic = request.topic or request.course_title or "General Knowledge"

    logger.info(
        f"Quiz generation request: course_id={request.course_id}, "
        f"topic={topic}, questions={request.num_questions}, "
        f"difficulty={request.difficulty}"
    )

    try:
        if request.num_questions < 1 or request.num_questions > 50:
            raise ValueError("Question count must be between 1 and 50")

        if request.difficulty not in ("beginner", "intermediate", "advanced"):
            raise ValueError("Difficulty must be beginner, intermediate, or advanced")

        questions = _generate_mock_questions(topic, request.difficulty, request.num_questions)

        # Time limit based on difficulty
        time_per_q = {"beginner": 2, "intermediate": 3, "advanced": 4}
        time_limit = request.num_questions * time_per_q.get(request.difficulty, 3)

        passing_scores = {"beginner": 60, "intermediate": 70, "advanced": 75}
        passing_score = passing_scores.get(request.difficulty, 70)

        return {
            "success": True,
            "quiz": {
                "id": str(uuid.uuid4()),
                "course_id": request.course_id,
                "title": f"{topic} Quiz",
                "topic": topic,
                "difficulty": request.difficulty,
                "description": f"Auto-generated quiz on {topic}",
                "time_limit_minutes": time_limit,
                "passing_score": passing_score,
                "question_count": len(questions),
                "questions": questions,
                "created_at": datetime.utcnow().isoformat(),
            },
            "message": f"Generated {len(questions)} questions for '{topic}'",
        }

    except ValueError as e:
        logger.warning(f"Quiz generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "generation_failed", "message": str(e)},
        )
