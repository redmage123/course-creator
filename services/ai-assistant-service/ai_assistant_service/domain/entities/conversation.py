"""
Conversation Entity - AI Assistant Domain

BUSINESS PURPOSE:
Represents an ongoing conversation between user and AI assistant.
Tracks conversation history, user context, and session state.

TECHNICAL IMPLEMENTATION:
Maintains ordered list of messages for multi-turn conversations.
Provides conversation context to LLM for coherent responses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from ai_assistant_service.domain.entities.message import Message, MessageRole


@dataclass
class UserContext:
    """
    User context for conversation

    BUSINESS PURPOSE:
    Tracks user identity, role, organization, and current page context.
    Used for RBAC checks and contextual AI responses.

    TECHNICAL IMPLEMENTATION:
    Immutable user context passed to all AI assistant operations.
    Used to determine available functions and permissions.

    ATTRIBUTES:
        user_id: Unique user identifier
        username: User's display name
        role: User's role (site_admin, org_admin, instructor, student)
        organization_id: User's organization (for multi-tenant isolation)
        current_page: Current page user is on (for contextual help)
        additional_context: Any other relevant context data
    """
    user_id: int
    username: str
    role: str
    organization_id: Optional[int] = None
    current_page: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """
    Conversation entity representing full chat session

    BUSINESS PURPOSE:
    Maintains conversation state for multi-turn interactions. Enables
    AI to reference previous messages and provide contextual responses.
    Essential for natural conversation flow.

    TECHNICAL IMPLEMENTATION:
    - Stores ordered message history
    - Tracks user context for RBAC
    - Provides LLM-formatted history
    - Manages conversation lifecycle

    ATTRIBUTES:
        conversation_id: Unique conversation identifier
        user_context: User identity and context
        messages: Ordered list of conversation messages
        created_at: Conversation start timestamp
        updated_at: Last message timestamp
        metadata: Additional conversation metadata
    """

    user_context: UserContext
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str) -> Message:
        """
        Add message to conversation

        BUSINESS PURPOSE:
        Records new message in conversation history. Updates conversation
        timestamp and maintains chronological order.

        TECHNICAL IMPLEMENTATION:
        Creates Message entity and appends to messages list.
        Updates updated_at timestamp for conversation tracking.

        ARGS:
            role: Message role (user/assistant)
            content: Message text content

        RETURNS:
            Created Message entity
        """
        message = Message(
            role=role,
            content=content,
            message_id=f"{self.conversation_id}-{len(self.messages)}"
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message

    def get_history_for_llm(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM API

        BUSINESS PURPOSE:
        Provides conversation context to LLM for generating contextual
        responses. Limits history to prevent token limit issues.

        TECHNICAL IMPLEMENTATION:
        Converts messages to LLM API format. Optionally limits to
        most recent N messages to stay within token limits.

        ARGS:
            max_messages: Maximum number of recent messages to include

        RETURNS:
            List of messages in LLM format: [{"role": "user", "content": "..."}]
        """
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]

        return [msg.to_llm_format() for msg in messages]

    def get_last_user_message(self) -> Optional[Message]:
        """
        Get most recent user message

        BUSINESS PURPOSE:
        Retrieves current user input for processing. Used to determine
        intent and generate appropriate response.

        TECHNICAL IMPLEMENTATION:
        Iterates messages in reverse to find most recent user message.

        RETURNS:
            Most recent Message with role=USER, or None if no user messages
        """
        for message in reversed(self.messages):
            if message.role == MessageRole.USER:
                return message
        return None

    def clear_history(self) -> None:
        """
        Clear conversation history

        BUSINESS PURPOSE:
        Allows users to start fresh conversation. Maintains privacy
        by removing previous conversation data.

        TECHNICAL IMPLEMENTATION:
        Empties messages list and resets timestamps.
        Keeps conversation_id and user_context intact.
        """
        self.messages.clear()
        self.updated_at = datetime.utcnow()
