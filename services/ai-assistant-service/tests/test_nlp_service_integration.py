"""
TDD RED Phase: NLP Preprocessing Service Integration Tests

BUSINESS PURPOSE:
Tests integration between AI Assistant and NLP Preprocessing Service.
Ensures intent classification, entity extraction, and query expansion work correctly.

TECHNICAL IMPLEMENTATION:
Tests NLP service client, preprocessing pipeline, and cost optimization.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock

from ai_assistant_service.application.services.nlp_service import NLPService
from ai_assistant_service.domain.entities.message import Message, MessageRole


@pytest.mark.asyncio
class TestNLPServiceIntegration:
    """Test NLP Preprocessing Service integration"""

    @pytest.fixture
    def nlp_service(self):
        """Create NLP service instance"""
        return NLPService(base_url="https://localhost:8013")

    @pytest.fixture
    def sample_query(self):
        """Sample user query"""
        return "Create a beginner Python track in the Data Science project"

    @pytest.fixture
    def sample_conversation(self):
        """Sample conversation history"""
        return [
            Message(role=MessageRole.USER, content="What is the platform?"),
            Message(role=MessageRole.ASSISTANT, content="This is Course Creator Platform..."),
            Message(role=MessageRole.USER, content="How do I create a project?"),
        ]

    async def test_service_initialization(self, nlp_service):
        """Test NLP service initializes correctly"""
        assert nlp_service is not None
        assert nlp_service.base_url == "https://localhost:8013"
        assert nlp_service.client is not None

    async def test_health_check(self, nlp_service):
        """Test NLP service health check"""
        is_healthy = await nlp_service.health_check()
        assert isinstance(is_healthy, bool)

    async def test_classify_intent(self, nlp_service, sample_query):
        """Test intent classification"""
        intent_result = await nlp_service.classify_intent(sample_query)

        assert intent_result is not None
        assert "intent_type" in intent_result
        assert "confidence" in intent_result
        assert "should_call_llm" in intent_result
        assert isinstance(intent_result["confidence"], float)
        assert 0.0 <= intent_result["confidence"] <= 1.0

    async def test_extract_entities(self, nlp_service, sample_query):
        """Test entity extraction"""
        entities = await nlp_service.extract_entities(sample_query)

        assert isinstance(entities, list)
        if entities:
            entity = entities[0]
            assert "text" in entity
            assert "entity_type" in entity
            assert "confidence" in entity
            assert "span" in entity

    async def test_expand_query(self, nlp_service, sample_query):
        """Test query expansion"""
        expanded = await nlp_service.expand_query(sample_query)

        assert isinstance(expanded, dict)
        assert "original_query" in expanded
        assert "expanded_keywords" in expanded
        assert "synonyms" in expanded
        assert isinstance(expanded["expanded_keywords"], list)

    async def test_deduplicate_conversation(self, nlp_service, sample_conversation):
        """Test conversation deduplication"""
        deduplicated = await nlp_service.deduplicate_conversation(
            sample_conversation,
            threshold=0.95
        )

        assert isinstance(deduplicated, list)
        assert len(deduplicated) <= len(sample_conversation)
        # Should remove semantically similar messages
        for msg in deduplicated:
            assert isinstance(msg, Message)

    async def test_preprocess_query(self, nlp_service, sample_query, sample_conversation):
        """Test complete preprocessing pipeline"""
        result = await nlp_service.preprocess_query(
            query=sample_query,
            conversation_history=sample_conversation
        )

        assert isinstance(result, dict)
        assert "intent" in result
        assert "entities" in result
        assert "expanded_query" in result
        assert "deduplicated_history" in result
        assert "should_call_llm" in result

    async def test_should_call_llm_decision(self, nlp_service):
        """Test intelligent LLM routing decision"""
        # Simple query - should not call LLM
        simple_query = "hello"
        result1 = await nlp_service.classify_intent(simple_query)
        assert result1["should_call_llm"] == False

        # Complex query - should call LLM
        complex_query = "Create a beginner Python track with 5 courses about machine learning"
        result2 = await nlp_service.classify_intent(complex_query)
        assert result2["should_call_llm"] == True

    async def test_entity_extraction_accuracy(self, nlp_service):
        """Test entity extraction finds correct entities"""
        query = "Create a beginner Python track in the Data Science project"
        entities = await nlp_service.extract_entities(query)

        # Should find: level (beginner), language (Python), project name (Data Science)
        entity_types = [e["entity_type"] for e in entities]
        entity_texts = [e["text"].lower() for e in entities]

        assert "beginner" in entity_texts or "level" in entity_types
        assert "python" in entity_texts or "Python" in entity_texts

    async def test_intent_classification_accuracy(self, nlp_service):
        """Test intent classification accuracy for different intents"""
        test_cases = [
            ("Create a new project", "create_project"),
            ("Make a track for beginners", "create_track"),
            ("Add an instructor", "onboard_instructor"),
            ("Show me analytics", "view_analytics"),
            ("What is the platform?", "help_question"),
        ]

        for query, expected_intent in test_cases:
            result = await nlp_service.classify_intent(query)
            assert result["intent_type"] == expected_intent

    async def test_query_expansion_improves_search(self, nlp_service):
        """Test query expansion adds relevant terms"""
        query = "Python course"
        expanded = await nlp_service.expand_query(query)

        keywords = expanded["expanded_keywords"]
        synonyms = expanded["synonyms"]

        # Should add related terms
        assert len(keywords) > 0
        assert any(term in ["programming", "coding", "development"] for term in keywords + synonyms)

    async def test_deduplication_removes_duplicates(self, nlp_service):
        """Test deduplication removes semantically similar messages"""
        # Create conversation with duplicates
        conversation = [
            Message(role=MessageRole.USER, content="How do I create a project?"),
            Message(role=MessageRole.ASSISTANT, content="To create a project..."),
            Message(role=MessageRole.USER, content="How can I create a new project?"),  # Duplicate
            Message(role=MessageRole.USER, content="What are the steps to make a project?"),  # Duplicate
        ]

        deduplicated = await nlp_service.deduplicate_conversation(
            conversation,
            threshold=0.90  # High threshold for duplicates
        )

        # Should remove duplicates
        assert len(deduplicated) < len(conversation)
        user_messages = [m for m in deduplicated if m.role == MessageRole.USER]
        assert len(user_messages) <= 2  # Should keep at most 2 user messages

    async def test_cost_optimization_metrics(self, nlp_service, sample_query, sample_conversation):
        """Test NLP service provides cost savings metrics"""
        result = await nlp_service.preprocess_query(
            query=sample_query,
            conversation_history=sample_conversation
        )

        # Should include metrics
        assert "metrics" in result
        metrics = result["metrics"]
        assert "original_message_count" in metrics
        assert "deduplicated_message_count" in metrics
        assert "estimated_token_savings" in metrics

    async def test_error_handling_invalid_query(self, nlp_service):
        """Test error handling for invalid input"""
        with pytest.raises(Exception):
            await nlp_service.preprocess_query(query="")

    async def test_error_handling_service_unavailable(self):
        """Test error handling when service is unavailable"""
        nlp_service = NLPService(base_url="https://invalid-url:9999")

        with pytest.raises(httpx.HTTPError):
            await nlp_service.classify_intent("test query")

    async def test_caching_improves_performance(self, nlp_service, sample_query):
        """Test caching reduces repeated API calls"""
        # First call
        result1 = await nlp_service.classify_intent(sample_query)

        # Second call (should use cache)
        result2 = await nlp_service.classify_intent(sample_query)

        # Should return same result
        assert result1 == result2
        # Should use cache (test via metrics or timing)

    async def test_batch_preprocessing(self, nlp_service):
        """Test batch preprocessing multiple queries"""
        queries = [
            "Create a project",
            "Make a track",
            "Add instructor",
        ]

        results = await nlp_service.batch_preprocess(queries)

        assert len(results) == len(queries)
        for result in results:
            assert "intent" in result
            assert "entities" in result

    async def test_preprocessing_preserves_context(self, nlp_service, sample_conversation):
        """Test preprocessing preserves conversation context"""
        query = "Add another one"  # Vague query needing context
        result = await nlp_service.preprocess_query(
            query=query,
            conversation_history=sample_conversation
        )

        # Should use context to understand "another one" refers to previous topic
        assert result["entities"] is not None or result["expanded_query"]["expanded_keywords"]

    async def test_close_client(self, nlp_service):
        """Test client closes gracefully"""
        await nlp_service.close()
        assert nlp_service.client.is_closed
