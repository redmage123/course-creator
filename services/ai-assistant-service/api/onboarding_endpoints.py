"""
Onboarding and Help REST API Endpoints.

BUSINESS PURPOSE:
Provides REST endpoints for the AI assistant's onboarding and help features.
These endpoints support the welcome popup, guided tour, FAQ system, and
contextual help features.

ENDPOINTS:
- POST /api/ai/welcome - Get personalized welcome message for first-time users
- POST /api/ai/tour/{phase} - Get tour content for a specific phase
- GET /api/ai/faq - Get list of all FAQ topics
- GET /api/ai/faq/{topic} - Get specific FAQ answer
- POST /api/ai/help - Get help response for a query
- POST /api/ai/hints - Get contextual hints for current page

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-12-01
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ai", tags=["AI Assistant - Onboarding & Help"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class UserContextRequest(BaseModel):
    """User context for personalized responses."""
    user_id: str = Field(..., description="User's unique identifier")
    username: str = Field(..., description="User's display name")
    role: str = Field(..., description="User's role (student, instructor, org_admin, etc.)")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    organization_name: Optional[str] = Field(None, description="Organization name")
    current_page: Optional[str] = Field(None, description="Current page/URL")
    is_first_login: bool = Field(False, description="Whether this is user's first login")


class WelcomeResponse(BaseModel):
    """Welcome message response."""
    welcome_message: str = Field(..., description="Personalized welcome message")
    tour_highlights: List[str] = Field(default_factory=list, description="Key features to highlight")
    first_actions: List[str] = Field(default_factory=list, description="Suggested first actions")
    show_tour: bool = Field(False, description="Whether to show the guided tour")
    role: str = Field(..., description="User's role category")


class TourStepResponse(BaseModel):
    """Tour step response."""
    phase: str = Field(..., description="Current tour phase")
    prompts: List[str] = Field(default_factory=list, description="Tour prompts for this phase")
    feature_explanations: Dict[str, str] = Field(default_factory=dict, description="Feature explanations")


class FAQEntry(BaseModel):
    """FAQ entry."""
    topic: str = Field(..., description="FAQ topic key")
    question: str = Field(..., description="FAQ question")
    answer: Optional[str] = Field(None, description="FAQ answer (included in detail view)")


class HelpRequest(BaseModel):
    """Help query request."""
    query: str = Field(..., description="User's help query")
    current_page: Optional[str] = Field(None, description="Current page context")
    user_context: Optional[UserContextRequest] = Field(None, description="User context")


class HelpResponse(BaseModel):
    """Help response."""
    response: Optional[str] = Field(None, description="Direct answer if available")
    faq_matches: List[FAQEntry] = Field(default_factory=list, description="Matching FAQ entries")
    hints: List[str] = Field(default_factory=list, description="Contextual hints")
    help_topics: List[str] = Field(default_factory=list, description="Related help topics")


class ContextualHintsRequest(BaseModel):
    """Contextual hints request."""
    current_page: str = Field(..., description="Current page identifier")


class ContextualHintsResponse(BaseModel):
    """Contextual hints response."""
    hints: List[str] = Field(default_factory=list, description="Helpful hints for current page")
    help_topics: List[str] = Field(default_factory=list, description="Related help topics")
    context: Optional[str] = Field(None, description="Detected context")


# =============================================================================
# DEPENDENCY - Get WebSocket Handler
# =============================================================================

# This will be set by the main app during startup
_websocket_handler = None


def set_websocket_handler(handler):
    """Set the WebSocket handler instance for use by endpoints."""
    global _websocket_handler
    _websocket_handler = handler


def get_handler():
    """Get the WebSocket handler instance."""
    if _websocket_handler is None:
        raise HTTPException(
            status_code=503,
            detail="AI Assistant service not initialized"
        )
    return _websocket_handler


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/welcome", response_model=WelcomeResponse)
async def get_welcome_message(
    request: UserContextRequest,
    handler = Depends(get_handler)
) -> WelcomeResponse:
    """
    Get personalized welcome message for a user.

    BUSINESS PURPOSE:
    Generates a warm, personalized welcome message for users,
    especially first-time users. Includes tour highlights and
    suggested first actions based on the user's role.

    Args:
        request: User context including role, name, and first_login status

    Returns:
        WelcomeResponse with personalized message and guidance
    """
    try:
        # Create user context object
        from ai_assistant_service.domain.entities.conversation import UserContext
        user_context = UserContext(
            user_id=request.user_id,
            username=request.username,
            role=request.role,
            organization_id=request.organization_id,
            current_page=request.current_page
        )
        # Add organization_name as attribute
        user_context.organization_name = request.organization_name

        # Generate welcome message
        result = await handler.generate_welcome_message(
            user_context=user_context,
            is_first_login=request.is_first_login
        )

        logger.info(f"Generated welcome message for user {request.username}")

        return WelcomeResponse(
            welcome_message=result.get("welcome_message", "Welcome!"),
            tour_highlights=result.get("tour_highlights", []),
            first_actions=result.get("first_actions", []),
            show_tour=result.get("show_tour", request.is_first_login),
            role=result.get("role", "guest")
        )

    except Exception as e:
        logger.error(f"Error generating welcome message: {e}")
        # Return a fallback welcome message
        return WelcomeResponse(
            welcome_message=f"Welcome to Course Creator Platform, {request.username}!",
            tour_highlights=[],
            first_actions=["Explore your dashboard"],
            show_tour=request.is_first_login,
            role=request.role
        )


@router.post("/tour/{phase}", response_model=TourStepResponse)
async def get_tour_step(
    phase: str,
    request: UserContextRequest,
    handler = Depends(get_handler)
) -> TourStepResponse:
    """
    Get tour content for a specific phase.

    BUSINESS PURPOSE:
    Provides step-by-step guided tour content for new users.
    Each phase focuses on different aspects of the platform.

    Phases:
    - tour_start: Introduction to the tour
    - tour_dashboard: Dashboard overview
    - tour_features: Key feature highlights
    - tour_complete: Tour completion and next steps

    Args:
        phase: Tour phase identifier
        request: User context

    Returns:
        TourStepResponse with phase-specific content
    """
    try:
        from ai_assistant_service.domain.entities.conversation import UserContext
        user_context = UserContext(
            user_id=request.user_id,
            username=request.username,
            role=request.role,
            organization_id=request.organization_id,
            current_page=request.current_page
        )

        result = await handler.get_tour_step(user_context, phase)

        return TourStepResponse(
            phase=result.get("phase", phase),
            prompts=result.get("prompts", []),
            feature_explanations=result.get("feature_explanations", {})
        )

    except Exception as e:
        logger.error(f"Error getting tour step: {e}")
        return TourStepResponse(
            phase=phase,
            prompts=["Let me show you around the platform!"],
            feature_explanations={}
        )


@router.get("/faq", response_model=List[FAQEntry])
async def get_faq_list(
    handler = Depends(get_handler)
) -> List[FAQEntry]:
    """
    Get list of all FAQ topics.

    BUSINESS PURPOSE:
    Returns a list of all available FAQ topics for display
    in the help section. Users can browse topics and select
    ones they're interested in.

    Returns:
        List of FAQEntry with topic and question
    """
    try:
        result = await handler.get_faq_list()
        return [
            FAQEntry(topic=item["topic"], question=item["question"])
            for item in result
        ]
    except Exception as e:
        logger.error(f"Error getting FAQ list: {e}")
        return []


@router.get("/faq/{topic}", response_model=FAQEntry)
async def get_faq_by_topic(
    topic: str,
    handler = Depends(get_handler)
) -> FAQEntry:
    """
    Get FAQ answer for a specific topic.

    BUSINESS PURPOSE:
    Returns the full FAQ entry including the answer for
    a specific topic. Called when user clicks on a FAQ topic.

    Args:
        topic: FAQ topic key

    Returns:
        FAQEntry with question and answer
    """
    try:
        result = await handler.get_faq_answer_by_topic(topic)
        if result is None:
            raise HTTPException(status_code=404, detail="FAQ topic not found")

        return FAQEntry(
            topic=topic,
            question=result.get("question", ""),
            answer=result.get("answer", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting FAQ topic {topic}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving FAQ")


@router.post("/help", response_model=HelpResponse)
async def get_help_response(
    request: HelpRequest,
    handler = Depends(get_handler)
) -> HelpResponse:
    """
    Get help response for a user query.

    BUSINESS PURPOSE:
    Searches FAQs and provides contextual help for user queries.
    Returns matching FAQ entries, direct answers when available,
    and contextual hints based on the current page.

    Args:
        request: Help query with optional user context

    Returns:
        HelpResponse with answer, FAQ matches, and hints
    """
    try:
        user_context = None
        if request.user_context:
            from ai_assistant_service.domain.entities.conversation import UserContext
            user_context = UserContext(
                user_id=request.user_context.user_id,
                username=request.user_context.username,
                role=request.user_context.role,
                organization_id=request.user_context.organization_id,
                current_page=request.user_context.current_page
            )

        result = await handler.get_help_response(
            user_context=user_context,
            query=request.query,
            current_page=request.current_page
        )

        return HelpResponse(
            response=result.get("response"),
            faq_matches=[
                FAQEntry(
                    topic=faq.get("topic", ""),
                    question=faq.get("question", ""),
                    answer=faq.get("answer")
                )
                for faq in result.get("faq_matches", [])
            ],
            hints=result.get("hints", []),
            help_topics=result.get("help_topics", [])
        )

    except Exception as e:
        logger.error(f"Error getting help response: {e}")
        return HelpResponse(
            response="I'm here to help! Try searching for a specific topic.",
            faq_matches=[],
            hints=[],
            help_topics=[]
        )


@router.post("/hints", response_model=ContextualHintsResponse)
async def get_contextual_hints(
    request: ContextualHintsRequest,
    handler = Depends(get_handler)
) -> ContextualHintsResponse:
    """
    Get contextual hints for the current page.

    BUSINESS PURPOSE:
    Provides helpful tips and hints based on where the user
    is currently in the platform. Used for proactive assistance.

    Args:
        request: Current page identifier

    Returns:
        ContextualHintsResponse with page-specific hints
    """
    try:
        result = await handler.get_contextual_hints(request.current_page)

        return ContextualHintsResponse(
            hints=result.get("hints", []),
            help_topics=result.get("help_topics", []),
            context=result.get("context")
        )

    except Exception as e:
        logger.error(f"Error getting contextual hints: {e}")
        return ContextualHintsResponse(
            hints=[],
            help_topics=[],
            context=None
        )
