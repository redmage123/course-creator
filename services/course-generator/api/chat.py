"""
Chat API Routes

BUSINESS CONTEXT:
Provides AI-powered chat responses for course-related interactions.
Supports context-aware conversations for project creation, course design,
lab development, and general educational assistance.

TECHNICAL IMPLEMENTATION:
- FastAPI routes for chat endpoints
- Integration with ChatGenerator
- RAG context enhancement
- Conversation history management
- Context-aware system prompts

@module chat
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ai.generators.chat_generator import ChatGenerator
from ai.client import AIClient

# Custom exceptions
from exceptions import (
    ContentException,
    ContentValidationException,
    APIException
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize AI client and chat generator
# These will be properly initialized via dependency injection in production
ai_client = None
chat_generator = None


def get_chat_generator() -> ChatGenerator:
    """
    Get or initialize chat generator

    BUSINESS CONTEXT:
    Lazy initialization of chat generator with AI client
    """
    global ai_client, chat_generator

    if chat_generator is None:
        if ai_client is None:
            # Create minimal config for AIClient
            from omegaconf import OmegaConf
            import os

            config = OmegaConf.create({
                'ai': {
                    'anthropic': {
                        'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                        'default_model': 'claude-3-sonnet-20240229',
                        'max_tokens': 4000,
                        'temperature': 0.7,
                        'timeout': 30.0,
                        'max_retries': 3
                    }
                }
            })
            ai_client = AIClient(config)
        chat_generator = ChatGenerator(ai_client)

    return chat_generator


# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """
    Chat request payload

    BUSINESS FIELDS:
    - question: User's question or prompt
    - context: Optional context (project, course, etc.)
    - conversation_history: Previous messages for continuity
    """
    question: str = Field(..., min_length=1, max_length=5000, description="User's question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context data (project name, course info, etc.)")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation messages")


class ChatResponse(BaseModel):
    """
    Chat response payload

    BUSINESS FIELDS:
    - question: Original question
    - answer: AI-generated response
    - context_used: Whether context was provided
    - suggestions: Optional follow-up suggestions
    - metadata: Additional response metadata
    """
    question: str
    answer: str
    context_used: bool
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# ========================================
# CHAT ENDPOINTS
# ========================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    AI-powered chat endpoint for course-related interactions

    BUSINESS USE CASE:
    Provides intelligent responses to user questions about:
    - Project structure and organization
    - Course design and curriculum
    - Learning objectives and outcomes
    - Lab and exercise creation
    - Best practices and recommendations

    TECHNICAL IMPLEMENTATION:
    - Uses ChatGenerator with AI client
    - Supports conversation history for continuity
    - Can leverage context (project, course, etc.)
    - Returns structured response with suggestions

    Args:
        request: ChatRequest with question, context, and history

    Returns:
        ChatResponse with answer and metadata

    Raises:
        400: Invalid request (question too short/long)
        500: AI service error

    Example Request:
        POST /api/v1/chat
        {
            "question": "What learning tracks should I create for a Python course?",
            "context": {
                "course_title": "Python Programming Fundamentals",
                "target_roles": ["Application Developer", "Data Analyst"]
            },
            "conversation_history": []
        }

    Example Response:
        {
            "question": "What learning tracks should I create...",
            "answer": "For Python Programming Fundamentals targeting Application Developers and Data Analysts, I recommend 4 progressive tracks...",
            "context_used": true,
            "suggestions": [
                "Would you like me to detail the content for each track?",
                "Should I suggest specific labs for hands-on practice?"
            ],
            "metadata": {
                "generation_method": "ai",
                "timestamp": "2025-10-05T19:30:00Z"
            }
        }
    """
    try:
        logger.info(f"Chat request: {request.question[:50]}...")

        # Validate request
        if not request.question or len(request.question.strip()) == 0:
            raise ContentValidationException(
                message="Question cannot be empty",
                error_code="EMPTY_QUESTION",
                details={}
            )

        # Get chat generator
        generator = get_chat_generator()

        # Convert conversation history to format expected by ChatGenerator
        history = []
        if request.conversation_history:
            history = [
                {
                    'role': msg.role,
                    'content': msg.content
                }
                for msg in request.conversation_history
            ]

        # Generate response
        response = await generator.generate_response(
            question=request.question,
            context=request.context,
            conversation_history=history
        )

        if not response:
            raise ContentException(
                message="Failed to generate chat response",
                error_code="CHAT_GENERATION_FAILED",
                details={"question": request.question[:100]}
            )

        # Build response
        chat_response = ChatResponse(
            question=response.get('question', request.question),
            answer=response.get('answer', ''),
            context_used=response.get('context_used', False),
            suggestions=[
                "Would you like more details on any specific aspect?",
                "Should I provide implementation examples?",
                "Do you need help with the next steps?"
            ],
            metadata=response.get('metadata', {
                'generation_method': response.get('generation_method', 'ai'),
                'timestamp': response.get('timestamp')
            })
        )

        logger.info("Chat response generated successfully")
        return chat_response

    except ContentValidationException as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)

    except ContentException as e:
        logger.error(f"Content generation error: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )


class ExplainRequest(BaseModel):
    """Request model for concept explanation"""
    concept: str = Field(..., min_length=1, max_length=500, description="Concept to explain")
    level: str = Field(default="beginner", description="Difficulty level")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional course context")


@router.post("/chat/explain", response_model=ChatResponse)
async def explain_concept(request: ExplainRequest) -> ChatResponse:
    """
    Explain a specific concept

    BUSINESS USE CASE:
    Provides clear explanations of educational concepts at appropriate levels

    Args:
        concept: Concept to explain
        level: Difficulty level (beginner, intermediate, advanced)
        context: Optional course context

    Returns:
        ChatResponse with explanation

    Example:
        POST /api/v1/chat/explain?concept=recursion&level=beginner
    """
    try:
        logger.info(f"Explain concept: {request.concept} at {request.level} level")

        generator = get_chat_generator()

        response = await generator.generate_explanation(
            concept=request.concept,
            level=request.level,
            context=request.context
        )

        if not response:
            raise ContentException(
                message="Failed to generate explanation",
                error_code="EXPLANATION_GENERATION_FAILED",
                details={"concept": request.concept}
            )

        return ChatResponse(
            question=f"Explain {request.concept}",
            answer=response.get('explanation', ''),
            context_used=bool(request.context),
            metadata={
                'concept': response.get('concept'),
                'level': response.get('level'),
                'generation_method': response.get('generation_method')
            }
        )

    except ContentException as e:
        logger.error(f"Explanation generation error: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class HintRequest(BaseModel):
    """Request model for exercise hint"""
    exercise_context: Dict[str, Any] = Field(..., description="Exercise information")
    student_progress: Optional[Dict[str, Any]] = Field(None, description="Student's progress")


@router.post("/chat/hint", response_model=ChatResponse)
async def generate_hint(request: HintRequest) -> ChatResponse:
    """
    Generate a hint for an exercise

    BUSINESS USE CASE:
    Helps students progress through exercises without giving away solutions

    Args:
        exercise_context: Exercise details (title, description, requirements)
        student_progress: Student's current code/progress

    Returns:
        ChatResponse with helpful hint

    Example:
        POST /api/v1/chat/hint
        {
            "exercise_context": {
                "title": "Implement Binary Search",
                "description": "Write a function that searches a sorted array"
            },
            "student_progress": {
                "current_code": "def binary_search(arr, target): ...",
                "errors": ["IndexError: list index out of range"]
            }
        }
    """
    try:
        logger.info(f"Generate hint for exercise: {request.exercise_context.get('title', 'Unknown')}")

        generator = get_chat_generator()

        response = await generator.generate_hint(
            exercise_context=request.exercise_context,
            student_progress=request.student_progress
        )

        if not response:
            raise ContentException(
                message="Failed to generate hint",
                error_code="HINT_GENERATION_FAILED",
                details={"exercise": request.exercise_context.get('title')}
            )

        return ChatResponse(
            question=f"Hint for: {request.exercise_context.get('title')}",
            answer=response.get('hint', ''),
            context_used=bool(request.student_progress),
            metadata={
                'exercise_title': response.get('exercise_title'),
                'generation_method': response.get('generation_method')
            }
        )

    except ContentException as e:
        logger.error(f"Hint generation error: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
