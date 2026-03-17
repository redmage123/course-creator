"""
Message Entity - AI Assistant Domain

BUSINESS PURPOSE:
Represents a single message in a conversation between user and AI assistant.
Tracks message content, role (user/assistant), timestamp, and metadata.

TECHNICAL IMPLEMENTATION:
Domain entity with no infrastructure dependencies. Used by conversation
history tracking and LLM API calls.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """
    Message role enumeration

    BUSINESS PURPOSE:
    Distinguishes between user input and AI responses in conversation flow.
    Required for LLM API formatting (OpenAI/Claude conversation format).
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """
    Message entity representing single conversation turn

    BUSINESS PURPOSE:
    Core entity for tracking conversation history. Each message represents
    one turn in the conversation - either user input or AI response.

    TECHNICAL IMPLEMENTATION:
    - Immutable after creation (frozen dataclass)
    - Automatic timestamp assignment
    - Optional metadata for context tracking
    - Used in LLM API calls and conversation storage

    ATTRIBUTES:
        role: Who sent the message (user/assistant/system)
        content: Message text content
        timestamp: When message was created
        message_id: Unique identifier
        metadata: Optional context (intent, function_call, etc.)
    """

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_llm_format(self) -> Dict[str, str]:
        """
        Convert message to LLM API format

        BUSINESS PURPOSE:
        Formats message for OpenAI/Claude API calls. Required for
        maintaining conversation context in LLM requests.

        TECHNICAL IMPLEMENTATION:
        Returns dict with 'role' and 'content' keys as expected by
        OpenAI Chat Completion API and Claude Messages API.

        RETURNS:
            Dictionary formatted for LLM API: {"role": "user", "content": "..."}
        """
        return {
            "role": self.role.value,
            "content": self.content
        }

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to message

        BUSINESS PURPOSE:
        Enriches message with additional context like detected intent,
        function calls executed, or RAG sources used.

        TECHNICAL IMPLEMENTATION:
        Updates metadata dictionary. Used for tracking which actions
        were taken in response to this message.

        ARGS:
            key: Metadata field name
            value: Metadata value (any JSON-serializable type)
        """
        self.metadata[key] = value
