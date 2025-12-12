#!/usr/bin/env python3

"""
RAG-Enhanced Lab Assistant API Endpoints

This module provides RESTful API endpoints for the RAG-enhanced programming assistance
system integrated with lab environments in the Course Creator Platform.

## Educational Context:

### Intelligent Programming Assistance
- **Context-Aware Help**: Analyzes code, errors, and student context for targeted assistance
- **Progressive Learning**: Learns from successful solutions to improve over time
- **Personalized Guidance**: Adapts responses based on student skill level
- **Multi-Language Support**: Python, JavaScript, Java, C++, and more

### RAG Enhancement Features
- **Knowledge Retrieval**: Searches educational resources and documentation
- **Code Pattern Recognition**: Identifies common errors and anti-patterns
- **Solution Suggestions**: Provides step-by-step guidance without giving away answers
- **Learning Reinforcement**: Tracks successful solutions for future reference

### Educational Benefits
- **24/7 Availability**: Students get help anytime, reducing frustration
- **Consistent Quality**: Standardized assistance across all students
- **Scalability**: Supports unlimited concurrent students
- **Analytics**: Tracks common issues for curriculum improvement

## API Endpoints:
- POST /assistant/help - Get programming assistance
- GET /assistant/stats - Get assistance statistics

## Integration:
This router integrates with the RAGLabAssistant service for intelligent
programming assistance, enhancing the educational experience in lab environments.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Optional
import logging

# Import models
from pydantic import BaseModel

# Import RAG assistant
from rag_lab_assistant import (
    AssistanceResponse,
    get_programming_help,
    rag_lab_assistant,
    SkillLevel,
    STUDENT_PROMPTS_AVAILABLE
)
from typing import List

# Initialize router
router = APIRouter(
    prefix="/assistant",
    tags=["rag-assistant"],
    responses={
        500: {"description": "Internal server error"}
    }
)

logger = logging.getLogger(__name__)

# Request/Response Models
class ProgrammingHelpRequest(BaseModel):
    """
    Programming assistance request with code context.

    Educational Context:
    - Student submits code snippet with specific question
    - Optional error message for debugging assistance
    - Student ID for personalized learning
    - Skill level for appropriate response complexity

    Fields:
    - code: Student's code snippet for analysis
    - language: Programming language (python, javascript, java, etc.)
    - question: Specific question or problem description
    - error_message: Optional error message for debugging help
    - student_id: Student identifier for tracking and personalization
    - skill_level: beginner, intermediate, or advanced
    """
    code: str
    language: str
    question: str
    error_message: Optional[str] = None
    student_id: str = "anonymous"
    skill_level: str = "intermediate"

class AssistantStatsResponse(BaseModel):
    """
    RAG assistant performance statistics.

    Metrics:
    - Total assistance requests handled
    - Success rate of assistance
    - RAG enhancement effectiveness
    - Learning operation statistics
    - Service health indicators
    """
    assistant_stats: Dict[str, int]
    rag_service_stats: Dict
    timestamp: str


class EmotionalSupportRequest(BaseModel):
    """
    Request for emotional support response.

    Educational Context:
    - Students may feel frustrated, confused, or discouraged while learning
    - Emotional support helps maintain motivation and engagement
    - Personalized encouragement improves learning outcomes

    Fields:
    - detected_emotion: The emotion detected or reported (frustrated, confused, etc.)
    - student_context: Optional additional context about the student situation
    """
    detected_emotion: str
    student_context: Optional[Dict] = None


class EmotionalSupportResponse(BaseModel):
    """
    Emotional support response with recognition, validation, and support.

    Pedagogical Elements:
    - Recognition: Acknowledging the student's emotional state
    - Validation: Affirming that their feelings are normal
    - Support: Actionable encouragement and next steps
    """
    recognition: str
    validation: str
    support: List[str]


class ErrorExplanationRequest(BaseModel):
    """
    Request for student-friendly error explanation.

    Educational Context:
    - Error messages can be confusing for students
    - Understanding errors helps build debugging skills
    - Teaching moments help students learn to read errors themselves

    Fields:
    - error_message: The error message from the student's code
    """
    error_message: str


class ErrorExplanationResponse(BaseModel):
    """
    Student-friendly error explanation with teaching moment.

    Educational Elements:
    - Explanation: What the error means in simple terms
    - Common causes: Likely reasons for this error
    - Teaching moment: Skill-building insight for the student
    """
    explanation: str
    common_causes: List[str]
    teaching_moment: str


class EncouragementRequest(BaseModel):
    """
    Request for skill-level-appropriate encouragement.

    Fields:
    - skill_level: beginner, intermediate, or advanced
    """
    skill_level: str = "intermediate"


class EncouragementResponse(BaseModel):
    """
    List of encouragement phrases for the skill level.
    """
    encouragement_phrases: List[str]
    skill_level: str


class PromptStatusResponse(BaseModel):
    """
    Status of student AI prompts availability.
    """
    prompts_available: bool
    message: str

# RAG-Enhanced Lab Assistant Endpoints

@router.post("/help", response_model=AssistanceResponse, status_code=status.HTTP_200_OK)
async def get_programming_assistance(request: ProgrammingHelpRequest):
    """
    Get RAG-enhanced programming assistance for lab environments.

    Educational Workflow:
    1. Student encounters problem in lab environment
    2. Submits code snippet with question or error
    3. RAG system analyzes code and retrieves relevant knowledge
    4. Assistant generates personalized guidance
    5. Student receives step-by-step help without direct answers

    Intelligent Assistance Features:
    - **Code Analysis**: Identifies syntax errors, logic issues, and anti-patterns
    - **Context Retrieval**: Searches documentation and educational resources
    - **Personalized Response**: Adapts explanation to student skill level
    - **Progressive Hints**: Provides escalating hints without giving away solutions
    - **Learning Tracking**: Records successful interactions for future reference

    Multi-Language Support:
    - Python: Web development, data science, automation
    - JavaScript: Frontend, Node.js, React/Vue/Angular
    - Java: OOP, Spring Boot, Android development
    - C/C++: Systems programming, performance optimization
    - SQL: Database design and query optimization
    - And more: Go, Rust, TypeScript, PHP, Ruby, etc.

    Skill Level Adaptation:
    - **Beginner**: Simple explanations, basic concepts, step-by-step guidance
    - **Intermediate**: Technical details, best practices, optimization tips
    - **Advanced**: Architecture patterns, performance analysis, advanced techniques

    Example Request:
    ```json
    {
      "code": "def factorial(n):\\n    return n * factorial(n-1)",
      "language": "python",
      "question": "My factorial function causes a stack overflow. How do I fix it?",
      "error_message": "RecursionError: maximum recursion depth exceeded",
      "student_id": "student_123",
      "skill_level": "beginner"
    }
    ```

    Example Response:
    ```json
    {
      "suggestion": "Your factorial function is missing a base case...",
      "explanation": "Recursion needs a stopping condition...",
      "code_examples": ["def factorial(n):\\n    if n <= 1:\\n        return 1..."],
      "related_concepts": ["recursion", "base case", "stack overflow"],
      "confidence_score": 0.95,
      "assistance_type": "debugging"
    }
    ```

    Args:
        request: Programming assistance request with code and context

    Returns:
        AssistanceResponse: Intelligent assistance with suggestions and explanations

    Raises:
        HTTPException 500: If assistance generation fails
    """
    try:
        # Use the convenience function for simple integration
        response = await get_programming_help(
            code=request.code,
            language=request.language,
            question=request.question,
            error_message=request.error_message,
            student_id=request.student_id,
            skill_level=request.skill_level
        )

        logger.info(f"Provided programming assistance for {request.language} to student {request.student_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to provide programming assistance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Programming assistance failed: {str(e)}"
        )

@router.get("/stats", response_model=AssistantStatsResponse, status_code=status.HTTP_200_OK)
async def get_assistant_statistics():
    """
    Get RAG lab assistant performance statistics and metrics.

    Performance Insights:
    - **Request Volume**: Total assistance requests handled
    - **Success Rate**: Percentage of successful assistance interactions
    - **Response Time**: Average time to generate assistance
    - **RAG Effectiveness**: Knowledge retrieval success rate
    - **Learning Operations**: Successful solution tracking
    - **Service Health**: System availability and performance

    Educational Analytics:
    - **Common Issues**: Most frequently encountered problems
    - **Language Distribution**: Programming language usage patterns
    - **Skill Level Trends**: Student progression indicators
    - **Assistance Types**: Debugging vs. learning vs. optimization

    Monitoring Use Cases:
    - Service health monitoring for SLA compliance
    - Capacity planning for scaling decisions
    - Quality assessment for assistance effectiveness
    - Curriculum insights from common student challenges

    Example Response:
    ```json
    {
      "assistant_stats": {
        "total_requests": 15420,
        "successful_requests": 14889,
        "success_rate_percent": 96.6,
        "avg_response_time_ms": 1234
      },
      "rag_service_stats": {
        "total_queries": 15420,
        "cache_hits": 8234,
        "knowledge_retrievals": 7186,
        "learning_operations": 442
      },
      "timestamp": "2025-10-15T17:30:00Z"
    }
    ```

    Returns:
        AssistantStatsResponse: Comprehensive statistics and metrics

    Raises:
        HTTPException 500: If statistics retrieval fails
    """
    try:
        stats = await rag_lab_assistant.get_assistance_stats()
        return AssistantStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get assistant statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Statistics retrieval failed: {str(e)}"
        )


@router.post("/emotional-support", response_model=EmotionalSupportResponse, status_code=status.HTTP_200_OK)
async def get_emotional_support(request: EmotionalSupportRequest):
    """
    Get emotional support response for a student's emotional state.

    Educational Workflow:
    1. Detect student frustration, confusion, or discouragement
    2. Request appropriate emotional support response
    3. Provide recognition, validation, and supportive next steps
    4. Help student regain motivation and continue learning

    Supported Emotions:
    - **Frustrated**: Student is stuck and becoming upset
    - **Confused**: Student doesn't understand the concept
    - **Discouraged**: Student is losing confidence
    - **Anxious**: Student is worried about performance
    - **Excited**: Student is enthusiastic and engaged
    - **Accomplished**: Student has achieved a milestone

    Pedagogical Approach:
    - Recognition: "I can see you're feeling frustrated..."
    - Validation: "That's completely normal when learning..."
    - Support: Actionable suggestions and encouragement

    Example Request:
    ```json
    {
      "detected_emotion": "frustrated",
      "student_context": {"attempts": 5, "topic": "recursion"}
    }
    ```

    Example Response:
    ```json
    {
      "recognition": "It sounds like you're feeling frustrated. That's completely normal!",
      "validation": "This is a challenging topic - many students struggle with it.",
      "support": ["Let's take a step back...", "Would you like to take a short break?"]
    }
    ```

    Args:
        request: Emotional support request with detected emotion

    Returns:
        EmotionalSupportResponse: Recognition, validation, and support

    Raises:
        HTTPException 500: If emotional support generation fails
    """
    try:
        support_data = rag_lab_assistant.get_emotional_support_response(
            detected_emotion=request.detected_emotion,
            student_context=request.student_context
        )

        logger.info(f"Provided emotional support for emotion: {request.detected_emotion}")

        return EmotionalSupportResponse(
            recognition=support_data["recognition"],
            validation=support_data["validation"],
            support=support_data["support"]
        )

    except Exception as e:
        logger.error(f"Failed to provide emotional support: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Emotional support failed: {str(e)}"
        )


@router.post("/explain-error", response_model=ErrorExplanationResponse, status_code=status.HTTP_200_OK)
async def get_error_explanation(request: ErrorExplanationRequest):
    """
    Get student-friendly explanation for a programming error.

    Educational Workflow:
    1. Student encounters an error in their code
    2. System analyzes the error message
    3. Returns explanation, common causes, and teaching moment
    4. Student learns to understand and fix errors independently

    Supported Error Types:
    - **SyntaxError**: Code structure problems
    - **NameError**: Undefined variables/functions
    - **TypeError**: Wrong data type operations
    - **IndexError**: List/array index out of bounds
    - **KeyError**: Dictionary key not found
    - **AttributeError**: Invalid attribute access
    - **ValueError**: Invalid value for operation

    Pedagogical Elements:
    - **Explanation**: What the error means in simple terms
    - **Common Causes**: Most likely reasons for this error
    - **Teaching Moment**: Skill-building insight

    Example Request:
    ```json
    {
      "error_message": "NameError: name 'counter' is not defined"
    }
    ```

    Example Response:
    ```json
    {
      "explanation": "A NameError means you're using a variable that Python doesn't recognize.",
      "common_causes": [
        "Typo in the variable name",
        "Using a variable before defining it",
        "Variable defined inside a function but used outside"
      ],
      "teaching_moment": "Check the exact spelling of your variable..."
    }
    ```

    Args:
        request: Error explanation request with error message

    Returns:
        ErrorExplanationResponse: Explanation, causes, and teaching moment

    Raises:
        HTTPException 500: If error explanation fails
    """
    try:
        error_data = rag_lab_assistant.get_error_explanation_prompt(request.error_message)

        logger.info(f"Provided error explanation for: {request.error_message[:50]}...")

        return ErrorExplanationResponse(
            explanation=error_data.get("explanation", "Unknown error"),
            common_causes=error_data.get("common_causes", []),
            teaching_moment=error_data.get("teaching_moment", "")
        )

    except Exception as e:
        logger.error(f"Failed to provide error explanation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error explanation failed: {str(e)}"
        )


@router.post("/encouragement", response_model=EncouragementResponse, status_code=status.HTTP_200_OK)
async def get_encouragement(request: EncouragementRequest):
    """
    Get skill-level-appropriate encouragement phrases.

    Educational Purpose:
    - Beginners need more basic, supportive encouragement
    - Intermediate students need challenge acknowledgment
    - Advanced students need peer-level recognition

    Example Request:
    ```json
    {
      "skill_level": "beginner"
    }
    ```

    Example Response:
    ```json
    {
      "encouragement_phrases": [
        "That's a great question - asking questions is how we learn!",
        "Don't worry if this feels challenging at first...",
        "You're making excellent progress!"
      ],
      "skill_level": "beginner"
    }
    ```

    Args:
        request: Encouragement request with skill level

    Returns:
        EncouragementResponse: List of appropriate phrases

    Raises:
        HTTPException 500: If encouragement retrieval fails
    """
    try:
        # Convert string to SkillLevel enum
        try:
            skill_level_enum = SkillLevel(request.skill_level.lower())
        except ValueError:
            skill_level_enum = SkillLevel.INTERMEDIATE

        phrases = rag_lab_assistant.get_encouragement(skill_level_enum)

        logger.info(f"Provided encouragement for skill level: {request.skill_level}")

        return EncouragementResponse(
            encouragement_phrases=phrases,
            skill_level=request.skill_level
        )

    except Exception as e:
        logger.error(f"Failed to provide encouragement: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Encouragement retrieval failed: {str(e)}"
        )


@router.get("/prompts-status", response_model=PromptStatusResponse, status_code=status.HTTP_200_OK)
async def get_prompts_status():
    """
    Check if student AI prompts module is available.

    Returns availability status and message about the prompts system.
    Useful for monitoring and debugging prompt integration.

    Example Response:
    ```json
    {
      "prompts_available": true,
      "message": "Student AI prompts are fully integrated and available."
    }
    ```

    Returns:
        PromptStatusResponse: Availability status and message
    """
    if STUDENT_PROMPTS_AVAILABLE:
        return PromptStatusResponse(
            prompts_available=True,
            message="Student AI prompts are fully integrated and available."
        )
    else:
        return PromptStatusResponse(
            prompts_available=False,
            message="Student AI prompts not available. Using fallback prompts."
        )
