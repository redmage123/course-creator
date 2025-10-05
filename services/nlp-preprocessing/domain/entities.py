"""
NLP Preprocessing Domain Entities

BUSINESS CONTEXT:
Core data structures for NLP preprocessing operations including
intent classification, entity extraction, query expansion, and
semantic similarity operations.

TECHNICAL IMPLEMENTATION:
- Pydantic models for validation
- Type hints for clarity
- Immutable data structures where appropriate
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    """
    User query intent types

    BUSINESS VALUE:
    Enables intelligent routing to skip LLM for simple queries,
    reducing cost and latency
    """
    QUESTION = "question"  # General question requiring LLM
    PREREQUISITE_CHECK = "prerequisite_check"  # Can use knowledge graph directly
    COURSE_LOOKUP = "course_lookup"  # Can use metadata search directly
    SKILL_LOOKUP = "skill_lookup"  # Can use metadata search directly
    LEARNING_PATH = "learning_path"  # Can use knowledge graph directly
    CONCEPT_EXPLANATION = "concept_explanation"  # Requires LLM
    FEEDBACK = "feedback"  # User feedback, no response needed
    COMMAND = "command"  # Action request (create, update, delete)
    CLARIFICATION = "clarification"  # Follow-up question
    GREETING = "greeting"  # Simple greeting
    UNKNOWN = "unknown"  # Cannot classify, send to LLM


class EntityType(str, Enum):
    """
    Entity types that can be extracted from user queries

    BUSINESS VALUE:
    Extracted entities enable targeted searches and reduce hallucination
    """
    COURSE = "course"
    TOPIC = "topic"
    SKILL = "skill"
    CONCEPT = "concept"
    PERSON = "person"  # Instructor, student names
    ORGANIZATION = "organization"
    DIFFICULTY = "difficulty"  # beginner, intermediate, advanced
    DURATION = "duration"  # time mentions


class Entity(BaseModel):
    """
    Extracted entity from user query

    TECHNICAL DETAILS:
    - text: The actual text matched
    - entity_type: Classification of entity
    - confidence: Extraction confidence (0.0-1.0)
    - span: Character positions in original text
    - metadata: Additional context
    """
    text: str = Field(..., description="Entity text as it appears in query")
    entity_type: EntityType = Field(..., description="Type of entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    span: tuple[int, int] = Field(..., description="(start, end) character positions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class Intent(BaseModel):
    """
    Classified user intent

    TECHNICAL DETAILS:
    - intent_type: Primary intent classification
    - confidence: Classification confidence
    - keywords: Keywords that triggered classification
    - should_call_llm: Whether LLM is needed
    """
    intent_type: IntentType = Field(..., description="Classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    keywords: List[str] = Field(default_factory=list, description="Matched keywords")
    should_call_llm: bool = Field(..., description="Whether to invoke LLM")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ExpandedQuery(BaseModel):
    """
    Query expansion result

    BUSINESS VALUE:
    Captures vocabulary mismatch and improves RAG recall

    TECHNICAL DETAILS:
    - original: Original user query
    - expansions: Synonym/related term variations
    - combined: All queries combined for search
    """
    original: str = Field(..., description="Original query")
    expansions: List[str] = Field(default_factory=list, description="Expanded query variations")
    combined: str = Field(..., description="Combined query for search")
    expansion_terms: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Original term -> synonyms mapping"
    )


class ConversationMessage(BaseModel):
    """
    Conversation history message

    TECHNICAL DETAILS:
    Used for semantic deduplication
    """
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    embedding: Optional[List[float]] = Field(None, description="Semantic embedding vector")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class SemanticSimilarity(BaseModel):
    """
    Semantic similarity result

    TECHNICAL DETAILS:
    - index1, index2: Message indices being compared
    - similarity: Cosine similarity score (0.0-1.0)
    - is_duplicate: Whether messages are semantically similar enough to dedupe
    """
    index1: int
    index2: int
    similarity: float = Field(..., ge=0.0, le=1.0)
    is_duplicate: bool = Field(..., description="True if similarity > threshold")


class PreprocessingResult(BaseModel):
    """
    Complete NLP preprocessing result

    BUSINESS VALUE:
    Combines all preprocessing steps for AI assistant pipeline

    TECHNICAL DETAILS:
    - intent: Classified intent
    - entities: Extracted entities
    - expanded_query: Query expansions
    - deduplicated_history: Cleaned conversation history
    - should_call_llm: Final routing decision
    - direct_response: Optional response without LLM (for simple lookups)
    """
    intent: Intent
    entities: List[Entity] = Field(default_factory=list)
    expanded_query: Optional[ExpandedQuery] = None
    deduplicated_history: Optional[List[ConversationMessage]] = None
    should_call_llm: bool
    direct_response: Optional[Dict[str, Any]] = Field(
        None,
        description="Direct response for simple queries (bypasses LLM)"
    )
    processing_time_ms: float = Field(..., description="Total preprocessing time")
    metadata: Dict[str, Any] = Field(default_factory=dict)
