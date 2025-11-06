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
    rag_lab_assistant
)

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
