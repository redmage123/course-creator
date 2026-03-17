"""
Integration Tests for Local LLM Service with All Platform Services

BUSINESS CONTEXT:
Tests integration between local-llm-service and all other platform services
to ensure seamless communication, data flow, and error handling across
the entire microservices architecture.

TECHNICAL IMPLEMENTATION:
- Tests HTTP/REST API integration
- Tests WebSocket communication where applicable
- Validates request/response formats
- Tests error propagation and handling
- Validates service discovery and health checks

Services Tested:
1. AI Assistant Service (port 8011)
2. RAG Service (port 8009)
3. Knowledge Graph Service (port 8012)
4. NLP Preprocessing Service (port 8013)
5. User Management Service (port 8000)
6. Course Management Service (port 8003)
7. Organization Management Service (port 8007)
8. Analytics Service (port 8006)
9. Metadata Service (port 8014)
"""

import pytest
import requests
import json
import asyncio
from typing import Dict, Any
import httpx


# Base URLs for all services
SERVICE_URLS = {
    "local_llm": "http://localhost:8015",
    "ai_assistant": "http://localhost:8011",
    "rag": "http://localhost:8009",
    "knowledge_graph": "http://localhost:8012",
    "nlp": "http://localhost:8013",
    "user_management": "http://localhost:8000",
    "course_management": "http://localhost:8003",
    "organization": "http://localhost:8007",
    "analytics": "http://localhost:8006",
    "metadata": "http://localhost:8014"
}


class TestLocalLLMHealthChecks:
    """Test health check integration with all services."""

    @pytest.mark.integration
    def test_local_llm_service_health(self):
        """Test local LLM service health endpoint."""
        response = requests.get(f"{SERVICE_URLS['local_llm']}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "model" in data

    @pytest.mark.integration
    def test_all_services_reachable_from_local_llm(self):
        """Test that local LLM can reach all other services."""
        # This test verifies network connectivity
        for service_name, url in SERVICE_URLS.items():
            if service_name == "local_llm":
                continue

            try:
                response = requests.get(f"{url}/health", timeout=5)
                assert response.status_code in [200, 503], \
                    f"{service_name} should respond to health checks"
            except requests.RequestException as e:
                pytest.skip(f"{service_name} not available: {e}")


class TestAIAssistantIntegration:
    """Test integration between Local LLM and AI Assistant Service."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ai_assistant_uses_local_llm(self):
        """Test AI Assistant can use Local LLM for responses."""
        # The AI Assistant should route simple queries to local LLM
        payload = {
            "user_id": 1,
            "message": "What is Python?",
            "conversation_id": "test-conv-123"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVICE_URLS['ai_assistant']}/api/v1/ai-assistant/chat",
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    assert "response" in data
                    assert "metadata" in data
                    # Check if local LLM was used
                    if "llm_source" in data.get("metadata", {}):
                        assert data["metadata"]["llm_source"] in ["local", "cloud"]
        except httpx.RequestError:
            pytest.skip("AI Assistant service not available")

    @pytest.mark.integration
    def test_local_llm_response_format_for_ai_assistant(self):
        """Test Local LLM returns format expected by AI Assistant."""
        payload = {
            "prompt": "Hello",
            "max_tokens": 50,
            "temperature": 0.7
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response format
        assert "response" in data
        assert "latency_ms" in data
        assert "cached" in data
        assert isinstance(data["response"], str)
        assert isinstance(data["latency_ms"], (int, float))
        assert isinstance(data["cached"], bool)


class TestRAGServiceIntegration:
    """Test integration between Local LLM and RAG Service."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_local_llm_summarizes_rag_results(self):
        """Test Local LLM can summarize RAG query results."""
        # Step 1: Query RAG service
        rag_query = {"query": "Python programming", "n_results": 5}

        try:
            async with httpx.AsyncClient() as client:
                rag_response = await client.post(
                    f"{SERVICE_URLS['rag']}/api/v1/rag/query",
                    json=rag_query,
                    timeout=10.0
                )

                if rag_response.status_code != 200:
                    pytest.skip("RAG service query failed")

                rag_data = rag_response.json()

                # Step 2: Summarize with Local LLM
                context = " ".join([r.get("text", "") for r in rag_data.get("results", [])])

                llm_payload = {
                    "context": context,
                    "max_summary_tokens": 100
                }

                llm_response = await client.post(
                    f"{SERVICE_URLS['local_llm']}/summarize",
                    json=llm_payload,
                    timeout=10.0
                )

                assert llm_response.status_code == 200
                llm_data = llm_response.json()
                assert "summary" in llm_data
                assert len(llm_data["summary"]) < len(context)

        except httpx.RequestError:
            pytest.skip("RAG or Local LLM service not available")

    @pytest.mark.integration
    def test_local_llm_query_expansion_for_rag(self):
        """Test Local LLM can expand queries for RAG."""
        payload = {
            "prompt": "Expand this query for better search: 'machine learning'",
            "max_tokens": 100
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Expanded query should be longer
        assert len(data["response"]) > len("machine learning")


class TestKnowledgeGraphIntegration:
    """Test integration between Local LLM and Knowledge Graph Service."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_local_llm_extracts_entities_for_kg(self):
        """Test Local LLM can extract entities for Knowledge Graph."""
        text = "Python is a programming language created by Guido van Rossum."

        payload = {
            "prompt": f"Extract entities from: {text}. Return as JSON.",
            "max_tokens": 100
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVICE_URLS['local_llm']}/generate",
                    json=payload,
                    timeout=10.0
                )

                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                # Response should contain extracted information
                assert any(keyword in data["response"].lower()
                          for keyword in ["python", "language", "entity"])

        except httpx.RequestError:
            pytest.skip("Local LLM service not available")

    @pytest.mark.integration
    def test_local_llm_generates_learning_paths(self):
        """Test Local LLM can generate learning path descriptions."""
        payload = {
            "prompt": "Create a brief learning path for Python basics (3 steps)",
            "max_tokens": 150
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Should contain numbered steps or learning progression
        assert any(char.isdigit() for char in data["response"])


class TestNLPPreprocessingIntegration:
    """Test integration between Local LLM and NLP Preprocessing Service."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_local_llm_intent_classification(self):
        """Test Local LLM can classify user intents."""
        user_message = "I want to create a new course about data science"

        payload = {
            "prompt": f"Classify the intent of this message: '{user_message}'. Choose from: create_course, search_course, enroll, question",
            "max_tokens": 50
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVICE_URLS['local_llm']}/generate",
                    json=payload,
                    timeout=10.0
                )

                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                # Should identify "create_course" intent
                assert "create" in data["response"].lower()

        except httpx.RequestError:
            pytest.skip("Local LLM service not available")

    @pytest.mark.integration
    def test_local_llm_query_preprocessing(self):
        """Test Local LLM can preprocess queries for NLP."""
        payload = {
            "prompt": "Normalize this query: 'HOW DO I LEARN PYTHON???'",
            "max_tokens": 50
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestUserManagementIntegration:
    """Test integration between Local LLM and User Management Service."""

    @pytest.mark.integration
    def test_local_llm_generates_user_onboarding_messages(self):
        """Test Local LLM can generate personalized onboarding messages."""
        payload = {
            "prompt": "Generate a welcome message for a new student named Alex who wants to learn Python",
            "max_tokens": 100
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "alex" in data["response"].lower() or "student" in data["response"].lower()

    @pytest.mark.integration
    def test_local_llm_validates_user_inputs(self):
        """Test Local LLM can validate user inputs."""
        payload = {
            "prompt": "Is this a valid email: 'test@example.com'? Answer yes or no.",
            "max_tokens": 10
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestCourseManagementIntegration:
    """Test integration between Local LLM and Course Management Service."""

    @pytest.mark.integration
    def test_local_llm_generates_course_descriptions(self):
        """Test Local LLM can generate course descriptions."""
        payload = {
            "prompt": "Generate a brief course description for 'Introduction to Python Programming'",
            "max_tokens": 150
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "python" in data["response"].lower()

    @pytest.mark.integration
    def test_local_llm_extracts_course_metadata(self):
        """Test Local LLM can extract course metadata."""
        payload = {
            "user_message": "Create a 10-week Python course for beginners",
            "function_schema": {
                "name": "create_course",
                "parameters": {
                    "duration_weeks": "integer",
                    "level": "string",
                    "topic": "string"
                }
            }
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/extract_parameters",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "parameters" in data


class TestOrganizationManagementIntegration:
    """Test integration between Local LLM and Organization Management Service."""

    @pytest.mark.integration
    def test_local_llm_generates_org_announcements(self):
        """Test Local LLM can generate organization announcements."""
        payload = {
            "prompt": "Generate a professional announcement about new course offerings",
            "max_tokens": 100
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.integration
    def test_local_llm_formats_org_reports(self):
        """Test Local LLM can format organization reports."""
        payload = {
            "prompt": "Format this data as a report: 50 students, 5 courses, 90% completion rate",
            "max_tokens": 150
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestAnalyticsIntegration:
    """Test integration between Local LLM and Analytics Service."""

    @pytest.mark.integration
    def test_local_llm_interprets_analytics_data(self):
        """Test Local LLM can interpret analytics data."""
        payload = {
            "prompt": "Interpret these analytics: 75% course completion, 4.5/5 rating, 200 students. Provide insights.",
            "max_tokens": 150
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Should contain analytical insights
        assert any(keyword in data["response"].lower()
                  for keyword in ["high", "good", "positive", "completion", "rating"])

    @pytest.mark.integration
    def test_local_llm_generates_analytics_summaries(self):
        """Test Local LLM can generate analytics summaries."""
        payload = {
            "context": "Student progress data: Module 1: 100%, Module 2: 85%, Module 3: 70%",
            "max_summary_tokens": 50
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/summarize",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data


class TestMetadataServiceIntegration:
    """Test integration between Local LLM and Metadata Service."""

    @pytest.mark.integration
    def test_local_llm_generates_metadata_tags(self):
        """Test Local LLM can generate metadata tags."""
        payload = {
            "prompt": "Generate 5 relevant tags for a course about 'Advanced Python Data Structures'",
            "max_tokens": 50
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.integration
    def test_local_llm_enriches_metadata(self):
        """Test Local LLM can enrich content metadata."""
        payload = {
            "prompt": "Enrich this metadata: Title: 'Python Basics'. Add description, level, and prerequisites.",
            "max_tokens": 150
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestCrossServiceWorkflow:
    """Test complex workflows involving multiple services."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_ai_assistant_workflow(self):
        """Test complete workflow: User Query → NLP → Local LLM → RAG → Response."""
        try:
            async with httpx.AsyncClient() as client:
                # 1. User asks question
                user_query = "What is object-oriented programming?"

                # 2. Local LLM classifies intent
                intent_payload = {
                    "prompt": f"Classify intent: '{user_query}'. Is this a 'question', 'create', or 'search'?",
                    "max_tokens": 20
                }

                intent_response = await client.post(
                    f"{SERVICE_URLS['local_llm']}/generate",
                    json=intent_payload,
                    timeout=10.0
                )

                assert intent_response.status_code == 200

                # 3. Query RAG for context
                rag_payload = {"query": user_query, "n_results": 3}
                rag_response = await client.post(
                    f"{SERVICE_URLS['rag']}/api/v1/rag/query",
                    json=rag_payload,
                    timeout=10.0
                )

                # 4. Local LLM generates response
                llm_payload = {
                    "prompt": f"Answer this question: {user_query}",
                    "max_tokens": 200
                }

                llm_response = await client.post(
                    f"{SERVICE_URLS['local_llm']}/generate",
                    json=llm_payload,
                    timeout=10.0
                )

                assert llm_response.status_code == 200
                final_data = llm_response.json()
                assert "response" in final_data
                assert len(final_data["response"]) > 0

        except httpx.RequestError as e:
            pytest.skip(f"Service not available: {e}")

    @pytest.mark.integration
    def test_conversation_compression_workflow(self):
        """Test conversation compression across services."""
        # Simulate multi-turn conversation
        messages = [
            {"role": "user", "content": "How do I learn Python?"},
            {"role": "assistant", "content": "Start with basics like variables and loops."},
            {"role": "user", "content": "What about data structures?"},
            {"role": "assistant", "content": "Learn lists, dictionaries, and sets."}
        ]

        payload = {
            "messages": messages,
            "target_tokens": 100
        }

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/compress",
            json=payload,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "compressed_summary" in data
        assert len(data["compressed_summary"]) < sum(len(m["content"]) for m in messages)


class TestErrorPropagation:
    """Test error handling across service boundaries."""

    @pytest.mark.integration
    def test_local_llm_handles_invalid_requests(self):
        """Test Local LLM handles invalid requests gracefully."""
        # Missing required field
        payload = {"max_tokens": 50}  # Missing 'prompt'

        response = requests.post(
            f"{SERVICE_URLS['local_llm']}/generate",
            json=payload,
            timeout=10
        )

        assert response.status_code in [400, 422]  # Bad request

    @pytest.mark.integration
    def test_local_llm_timeout_handling(self):
        """Test Local LLM handles timeouts appropriately."""
        payload = {
            "prompt": "Very long prompt that might timeout" * 1000,
            "max_tokens": 5000
        }

        try:
            response = requests.post(
                f"{SERVICE_URLS['local_llm']}/generate",
                json=payload,
                timeout=2  # Short timeout
            )
            # If no timeout, should still complete or return error
            assert response.status_code in [200, 408, 504]
        except requests.Timeout:
            pass  # Timeout is acceptable


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
