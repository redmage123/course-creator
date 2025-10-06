"""
Tests for NLP Preprocessor Orchestrator

BUSINESS CONTEXT:
Verify end-to-end NLP preprocessing pipeline works correctly.
"""

import pytest
import numpy as np
from nlp_preprocessing.application.nlp_preprocessor import NLPPreprocessor
from nlp_preprocessing.domain.entities import ConversationMessage, IntentType


class TestNLPPreprocessor:
    """
    Test NLP preprocessing orchestrator
    """

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance for tests"""
        return NLPPreprocessor()

    def test_preprocesses_simple_query(self, preprocessor):
        """Should preprocess a simple query successfully"""
        query = "What are the prerequisites for 'Machine Learning'?"

        result = preprocessor.preprocess(query)

        # Should classify intent
        assert result.intent.intent_type == IntentType.PREREQUISITE_CHECK
        # Should extract entities (quoted course name)
        assert len(result.entities) > 0
        # Should have expanded query
        assert result.expanded_query is not None
        # Should make routing decision
        assert result.should_call_llm is False  # Can use knowledge graph directly
        assert result.direct_response is not None

    def test_preprocesses_complex_query_requiring_llm(self, preprocessor):
        """Complex queries should route to LLM"""
        query = "Explain how gradient descent works in neural networks"

        result = preprocessor.preprocess(query)

        # Should classify as CONCEPT_EXPLANATION
        assert result.intent.intent_type == IntentType.CONCEPT_EXPLANATION
        # Should require LLM
        assert result.should_call_llm is True
        assert result.direct_response is None

    def test_deduplicates_conversation_history(self, preprocessor):
        """Should deduplicate conversation history with embeddings"""
        query = "Tell me more"

        # Create conversation history with duplicate embeddings
        conversation_history = [
            ConversationMessage(
                role="user",
                content="Hello",
                embedding=[1.0, 0.0, 0.0]
            ),
            ConversationMessage(
                role="assistant",
                content="Hi there!",
                embedding=[0.0, 1.0, 0.0]
            ),
            ConversationMessage(
                role="user",
                content="Hello",  # Duplicate
                embedding=[1.0, 0.0, 0.0]
            ),
        ]

        result = preprocessor.preprocess(
            query,
            conversation_history=conversation_history,
            enable_deduplication=True
        )

        # Should deduplicate
        assert result.deduplicated_history is not None
        assert len(result.deduplicated_history) < len(conversation_history)

    def test_skips_deduplication_when_disabled(self, preprocessor):
        """Should skip deduplication when disabled"""
        query = "Hello"
        conversation_history = [
            ConversationMessage(role="user", content="Hi", embedding=[1.0, 0.0]),
            ConversationMessage(role="user", content="Hi", embedding=[1.0, 0.0]),
        ]

        result = preprocessor.preprocess(
            query,
            conversation_history=conversation_history,
            enable_deduplication=False
        )

        # Should not deduplicate
        assert result.deduplicated_history is None

    def test_handles_query_without_conversation_history(self, preprocessor):
        """Should work without conversation history"""
        query = "Find courses about Python"

        result = preprocessor.preprocess(query)

        # Should work fine
        assert result.intent.intent_type == IntentType.COURSE_LOOKUP
        assert result.deduplicated_history is None

    def test_greeting_returns_direct_response(self, preprocessor):
        """Greetings should get direct response"""
        query = "Hello"

        result = preprocessor.preprocess(query)

        # Should classify as greeting
        assert result.intent.intent_type == IntentType.GREETING
        # Should not call LLM
        assert result.should_call_llm is False
        # Should have direct response
        assert result.direct_response is not None
        assert result.direct_response["type"] == "greeting"

    def test_tracks_processing_time(self, preprocessor):
        """Should track processing time"""
        query = "Find ML courses"

        result = preprocessor.preprocess(query)

        # Should have processing time
        assert result.processing_time_ms > 0
        # Should be fast (<20ms target)
        assert result.processing_time_ms < 20

    def test_extracts_entities_from_complex_query(self, preprocessor):
        """Should extract multiple entities from complex query"""
        query = "Find beginner courses about machine learning in 'Python Basics'"

        result = preprocessor.preprocess(query)

        # Should extract multiple entity types
        entity_types = {e.entity_type.value for e in result.entities}
        assert len(entity_types) >= 2  # At least difficulty and course/topic

    def test_expands_acronyms(self, preprocessor):
        """Should expand acronyms in query"""
        query = "ML courses"

        result = preprocessor.preprocess(query)

        # Should have expansions
        assert result.expanded_query is not None
        assert len(result.expanded_query.expansions) > 0
        # Should include machine learning
        assert any("machine learning" in exp.lower()
                   for exp in result.expanded_query.expansions)

    def test_performance_benchmark(self, preprocessor, benchmark):
        """Benchmark: Should preprocess in <20ms"""
        query = "Find beginner courses about ML and AI"
        conversation_history = [
            ConversationMessage(
                role="user",
                content="Hello",
                embedding=np.random.randn(384).tolist()
            )
            for _ in range(10)
        ]

        result = benchmark(
            preprocessor.preprocess,
            query,
            conversation_history
        )

        # Should complete successfully
        assert result.intent is not None
        assert result.processing_time_ms < 20
