"""
TDD Tests for EnsembleModelService

BUSINESS PURPOSE:
Test ensemble model service that calls both Mistral and LLama models
in parallel, providing multiple perspectives for consensus evaluation.

TEST STRATEGY:
- Test parallel model calls (both Mistral and LLama)
- Test response collection from both models
- Test graceful handling when one model fails
- Test timeout handling for slow models
- Test response format consistency
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import asyncio

from ai_assistant_service.application.services.ensemble_model_service import (
    EnsembleModelService,
    EnsembleResponse
)


class TestEnsembleModelServiceInitialization:
    """Test ensemble model service initialization"""

    def test_ensemble_service_initializes_with_local_llm(self):
        """RED: Should initialize with local LLM service"""
        mock_local_llm = MagicMock()
        service = EnsembleModelService(local_llm_service=mock_local_llm)

        assert service.local_llm_service == mock_local_llm

    def test_ensemble_service_configures_models(self):
        """RED: Should configure both Mistral and LLama model names"""
        service = EnsembleModelService(local_llm_service=MagicMock())

        assert service.mistral_model == "course-creator-assistant"
        assert service.llama_model == "llama3.1:8b-instruct-q4_K_M"


class TestParallelModelGeneration:
    """Test parallel model calls"""

    @pytest.fixture
    def ensemble_service(self):
        """Create ensemble service with mocked LLM"""
        mock_llm = MagicMock()
        return EnsembleModelService(local_llm_service=mock_llm)

    @pytest.mark.asyncio
    async def test_generates_ensemble_responses_from_both_models(self, ensemble_service):
        """
        RED: Should call both Mistral and LLama models in parallel

        BUSINESS VALUE:
        Provides multiple AI perspectives for better consensus decision
        """
        # Mock local LLM responses
        async def mock_generate_mistral(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate latency
            return "Mistral response: Python is a high-level programming language"

        async def mock_generate_llama(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate latency
            return "LLama response: Python is an interpreted language for general-purpose programming"

        # Setup mock to return different responses based on model parameter
        def side_effect(*args, **kwargs):
            model = kwargs.get("model", "")
            if "mistral" in model.lower():
                return mock_generate_mistral(*args, **kwargs)
            else:
                return mock_generate_llama(*args, **kwargs)

        ensemble_service.local_llm_service.generate_response = AsyncMock(side_effect=side_effect)

        # Generate ensemble responses
        result = await ensemble_service.generate_ensemble_responses(
            user_message="What is Python?",
            system_prompt="You are a helpful assistant",
            rag_context="Python documentation...",
            kg_context="Related courses: Python 101",
            metadata_context="Course: Python Programming"
        )

        # Verify both responses returned
        assert isinstance(result, EnsembleResponse)
        assert result.mistral_response is not None
        assert result.llama_response is not None
        assert "Python" in result.mistral_response
        assert "Python" in result.llama_response

    @pytest.mark.asyncio
    async def test_calls_models_in_parallel_not_sequential(self, ensemble_service):
        """
        RED: Should call models concurrently for performance

        BUSINESS VALUE:
        Reduces latency by running models in parallel instead of sequentially
        """
        call_times = []

        async def mock_generate(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # 100ms delay
            return "Response"

        ensemble_service.local_llm_service.generate_response = AsyncMock(side_effect=mock_generate)

        start_time = asyncio.get_event_loop().time()
        await ensemble_service.generate_ensemble_responses(
            user_message="Test",
            system_prompt="Test"
        )
        end_time = asyncio.get_event_loop().time()

        # If parallel, total time should be ~100ms (not 200ms)
        # If sequential, would be ~200ms
        elapsed = end_time - start_time
        assert elapsed < 0.15, "Models should run in parallel, not sequentially"

    @pytest.mark.asyncio
    async def test_includes_all_context_in_prompts(self, ensemble_service):
        """RED: Should include RAG, KG, and metadata context in prompts"""
        ensemble_service.local_llm_service.generate_response = AsyncMock(return_value="Response")

        await ensemble_service.generate_ensemble_responses(
            user_message="What is Python?",
            system_prompt="You are helpful",
            rag_context="RAG: Python docs",
            kg_context="KG: Python courses",
            metadata_context="Metadata: Python programming"
        )

        # Verify generate_response was called with context
        calls = ensemble_service.local_llm_service.generate_response.call_args_list
        assert len(calls) == 2  # Called twice (Mistral + LLama)

        # Check that context was included in prompt
        for call in calls:
            prompt = call[1].get("prompt", "")
            assert "RAG: Python docs" in prompt
            assert "KG: Python courses" in prompt
            assert "Metadata: Python programming" in prompt


class TestGracefulDegradation:
    """Test error handling and graceful degradation"""

    @pytest.fixture
    def ensemble_service(self):
        """Create ensemble service"""
        return EnsembleModelService(local_llm_service=MagicMock())

    @pytest.mark.asyncio
    async def test_returns_partial_result_when_one_model_fails(self, ensemble_service):
        """
        RED: Should return partial result if one model fails

        BUSINESS VALUE:
        System continues to work even if one model is down
        """
        # Mock Mistral success, LLama failure
        async def mock_generate(*args, **kwargs):
            model = kwargs.get("model", "")
            if "mistral" in model.lower():
                return "Mistral response"
            else:
                raise Exception("LLama model unavailable")

        ensemble_service.local_llm_service.generate_response = AsyncMock(side_effect=mock_generate)

        result = await ensemble_service.generate_ensemble_responses(
            user_message="Test",
            system_prompt="Test"
        )

        # Should have Mistral response, LLama should be None
        assert result.mistral_response == "Mistral response"
        assert result.llama_response is None
        assert result.mistral_error is None
        assert result.llama_error is not None

    @pytest.mark.asyncio
    async def test_returns_empty_result_when_both_models_fail(self, ensemble_service):
        """RED: Should return empty result when both models fail"""
        ensemble_service.local_llm_service.generate_response = AsyncMock(
            side_effect=Exception("All models down")
        )

        result = await ensemble_service.generate_ensemble_responses(
            user_message="Test",
            system_prompt="Test"
        )

        assert result.mistral_response is None
        assert result.llama_response is None
        assert result.mistral_error is not None
        assert result.llama_error is not None


class TestEnsembleResponse:
    """Test EnsembleResponse data class"""

    def test_ensemble_response_has_required_fields(self):
        """RED: EnsembleResponse should have all required fields"""
        response = EnsembleResponse(
            mistral_response="Mistral answer",
            llama_response="LLama answer",
            mistral_model="course-creator-assistant",
            llama_model="llama3.1:8b-instruct-q4_K_M",
            generation_time_ms=1234,
            mistral_error=None,
            llama_error=None
        )

        assert response.mistral_response == "Mistral answer"
        assert response.llama_response == "LLama answer"
        assert response.mistral_model == "course-creator-assistant"
        assert response.llama_model == "llama3.1:8b-instruct-q4_K_M"
        assert response.generation_time_ms == 1234
        assert response.mistral_error is None
        assert response.llama_error is None

    def test_ensemble_response_to_dict(self):
        """RED: Should convert to dictionary"""
        response = EnsembleResponse(
            mistral_response="A",
            llama_response="B",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=100,
            mistral_error=None,
            llama_error=None
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result["mistral_response"] == "A"
        assert result["llama_response"] == "B"
        assert result["generation_time_ms"] == 100


class TestPromptConstruction:
    """Test prompt building"""

    @pytest.fixture
    def ensemble_service(self):
        """Create ensemble service"""
        return EnsembleModelService(local_llm_service=MagicMock())

    def test_build_prompt_includes_all_components(self, ensemble_service):
        """RED: Should build complete prompt with all context"""
        prompt = ensemble_service._build_prompt(
            user_message="What is Python?",
            system_prompt="You are helpful",
            rag_context="RAG context",
            kg_context="KG context",
            metadata_context="Metadata context"
        )

        assert "You are helpful" in prompt
        assert "What is Python?" in prompt
        assert "RAG context" in prompt
        assert "KG context" in prompt
        assert "Metadata context" in prompt

    def test_build_prompt_handles_empty_context(self, ensemble_service):
        """RED: Should handle empty context gracefully"""
        prompt = ensemble_service._build_prompt(
            user_message="Test",
            system_prompt="Test",
            rag_context="",
            kg_context="",
            metadata_context=""
        )

        assert "Test" in prompt
        # Should not have empty context sections
        assert prompt.count("\n\n") <= 2


class TestPerformanceMetrics:
    """Test performance tracking"""

    @pytest.fixture
    def ensemble_service(self):
        """Create ensemble service"""
        return EnsembleModelService(local_llm_service=MagicMock())

    @pytest.mark.asyncio
    async def test_tracks_generation_time(self, ensemble_service):
        """RED: Should track total generation time in milliseconds"""
        async def mock_generate(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms
            return "Response"

        ensemble_service.local_llm_service.generate_response = AsyncMock(side_effect=mock_generate)

        result = await ensemble_service.generate_ensemble_responses(
            user_message="Test",
            system_prompt="Test"
        )

        # Should be around 50ms (parallel execution)
        assert result.generation_time_ms >= 45
        assert result.generation_time_ms <= 100
