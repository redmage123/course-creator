"""
NLP Preprocessing Service Client

BUSINESS PURPOSE:
Provides intelligent NLP preprocessing to optimize AI assistant costs and performance.
Includes intent classification, entity extraction, query expansion, and conversation
deduplication to reduce LLM API calls and token usage.

TECHNICAL IMPLEMENTATION:
HTTP client for NLP Preprocessing Service (port 8013).
Handles intent classification for routing, entity extraction for context,
query expansion for better retrieval, and semantic deduplication for cost optimization.
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from ai_assistant_service.domain.entities.message import Message, MessageRole


logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Intent classification result"""
    intent_type: str
    confidence: float
    should_call_llm: bool


@dataclass
class Entity:
    """Extracted entity"""
    text: str
    entity_type: str
    confidence: float
    span: tuple


@dataclass
class QueryExpansion:
    """Query expansion result"""
    original_query: str
    expanded_keywords: List[str]
    synonyms: List[str]


@dataclass
class PreprocessingResult:
    """Complete preprocessing pipeline result"""
    intent: IntentResult
    entities: List[Entity]
    expanded_query: QueryExpansion
    deduplicated_history: List[Message]
    should_call_llm: bool
    metrics: Dict[str, Any]


class NLPService:
    """
    NLP Preprocessing Service Client

    Provides intelligent preprocessing for AI assistant queries:
    - Intent classification: Determine if LLM call is needed
    - Entity extraction: Extract structured data from queries
    - Query expansion: Add related terms for better retrieval
    - Conversation deduplication: Remove redundant messages to save tokens
    """

    def __init__(self, base_url: str = "https://localhost:8013"):
        """
        Initialize NLP service client

        Args:
            base_url: Base URL of NLP preprocessing service
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            verify=False,  # SSL verification disabled for local dev
            timeout=30.0
        )
        logger.info(f"NLP Service initialized: {self.base_url}")

    async def health_check(self) -> bool:
        """
        Check if NLP service is healthy

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/nlp/health"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"NLP service health check failed: {e}")
            return False

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent and determine if LLM call is needed

        Simple queries (greetings, basic questions) can be handled without LLM.
        Complex queries (actions, multi-step requests) require LLM processing.

        Args:
            query: User query text

        Returns:
            Dictionary with intent_type, confidence, and should_call_llm

        Raises:
            httpx.HTTPError: If API call fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/nlp/classify-intent",
                json={"query": query}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Intent classification failed: {e}")
            raise

    async def extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """
        Extract entities from user query

        Identifies structured data like:
        - Levels: "beginner", "intermediate", "advanced"
        - Languages: "Python", "JavaScript", "Java"
        - Project names: "Data Science", "Web Development"
        - Numbers: course counts, durations

        Args:
            query: User query text

        Returns:
            List of entities with text, type, confidence, and span
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/nlp/extract-entities",
                json={"query": query}
            )
            response.raise_for_status()
            return response.json().get("entities", [])
        except httpx.HTTPError as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def expand_query(self, query: str) -> Dict[str, Any]:
        """
        Expand query with related keywords and synonyms

        Improves RAG retrieval by adding semantically related terms:
        - "Python course" → ["programming", "coding", "development"]
        - "machine learning" → ["ML", "AI", "neural networks"]

        Args:
            query: User query text

        Returns:
            Dictionary with original_query, expanded_keywords, synonyms
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/nlp/expand-query",
                json={"query": query}
            )
            response.raise_for_status()
            result = response.json()
            return {
                "original_query": query,
                "expanded_keywords": result.get("expanded_keywords", []),
                "synonyms": result.get("synonyms", [])
            }
        except httpx.HTTPError as e:
            logger.error(f"Query expansion failed: {e}")
            return {
                "original_query": query,
                "expanded_keywords": [],
                "synonyms": []
            }

    async def deduplicate_conversation(
        self,
        conversation: List[Message],
        threshold: float = 0.95
    ) -> List[Message]:
        """
        Remove semantically duplicate messages from conversation

        COST OPTIMIZATION: Reduces token usage by removing redundant messages.
        Uses semantic similarity to detect duplicates even if wording differs.

        Example:
            "How do I create a project?" (keep)
            "How can I create a new project?" (remove - duplicate)
            "What are the steps to make a project?" (remove - duplicate)

        Args:
            conversation: List of conversation messages
            threshold: Similarity threshold (0.0-1.0, higher = more strict)

        Returns:
            Deduplicated conversation history
        """
        if len(conversation) <= 1:
            return conversation

        try:
            # Convert messages to serializable format
            messages_data = [
                {
                    "role": msg.role.value,
                    "content": msg.content
                }
                for msg in conversation
            ]

            response = await self.client.post(
                f"{self.base_url}/api/v1/nlp/deduplicate",
                json={
                    "messages": messages_data,
                    "threshold": threshold
                }
            )
            response.raise_for_status()

            # Convert response back to Message objects
            deduplicated_data = response.json().get("deduplicated_messages", [])
            return [
                Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                )
                for msg in deduplicated_data
            ]
        except httpx.HTTPError as e:
            logger.error(f"Conversation deduplication failed: {e}")
            # Return original conversation if deduplication fails
            return conversation

    async def preprocess_query(
        self,
        query: str,
        conversation_history: List[Message]
    ) -> Dict[str, Any]:
        """
        Complete preprocessing pipeline

        Performs all preprocessing steps in one call:
        1. Intent classification
        2. Entity extraction
        3. Query expansion
        4. Conversation deduplication

        Returns comprehensive result with metrics for cost tracking.

        Args:
            query: User query text
            conversation_history: Previous conversation messages

        Returns:
            Dictionary with intent, entities, expanded_query,
            deduplicated_history, should_call_llm, and metrics
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Run all preprocessing steps in parallel for efficiency
        intent_task = self.classify_intent(query)
        entities_task = self.extract_entities(query)
        expansion_task = self.expand_query(query)
        dedup_task = self.deduplicate_conversation(conversation_history)

        intent_result, entities, expanded, deduplicated = await asyncio.gather(
            intent_task,
            entities_task,
            expansion_task,
            dedup_task
        )

        # Calculate metrics
        original_count = len(conversation_history)
        deduplicated_count = len(deduplicated)
        estimated_token_savings = (original_count - deduplicated_count) * 150  # Estimate 150 tokens per message

        return {
            "intent": intent_result,
            "entities": entities,
            "expanded_query": expanded,
            "deduplicated_history": deduplicated,
            "should_call_llm": intent_result.get("should_call_llm", True),
            "metrics": {
                "original_message_count": original_count,
                "deduplicated_message_count": deduplicated_count,
                "estimated_token_savings": estimated_token_savings
            }
        }

    async def batch_preprocess(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Preprocess multiple queries in batch

        More efficient than calling preprocess_query multiple times.
        Useful for batch operations or testing.

        Args:
            queries: List of query strings

        Returns:
            List of preprocessing results (one per query)
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/nlp/batch-preprocess",
                json={"queries": queries}
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Batch preprocessing failed: {e}")
            # Fallback: process individually
            results = []
            for query in queries:
                try:
                    intent = await self.classify_intent(query)
                    entities = await self.extract_entities(query)
                    results.append({
                        "intent": intent,
                        "entities": entities
                    })
                except Exception:
                    results.append({
                        "intent": None,
                        "entities": []
                    })
            return results

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("NLP Service client closed")
