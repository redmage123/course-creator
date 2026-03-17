"""
TDD Tests for ConsensusService

BUSINESS PURPOSE:
Test the consensus service that uses a frontier model (GPT-4/Claude) to evaluate
responses from the ensemble of local models (Mistral + LLama) and select the best response.

TEST STRATEGY:
- Test frontier model consensus evaluation
- Test response selection based on quality criteria
- Test fallback when frontier model unavailable
- Test handling when only one model succeeds
- Test tie-breaking logic
- Test response quality metrics
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from ai_assistant_service.application.services.consensus_service import (
    ConsensusService,
    ConsensusResult
)
from ai_assistant_service.application.services.ensemble_model_service import EnsembleResponse


class TestConsensusServiceInitialization:
    """Test consensus service initialization"""

    def test_consensus_service_initializes_with_frontier_model(self):
        """RED: Should initialize with frontier model configuration"""
        service = ConsensusService(
            frontier_model="gpt-4",
            api_key="test-key"
        )

        assert service.frontier_model == "gpt-4"
        assert service.api_key == "test-key"

    def test_consensus_service_creates_openai_client(self):
        """RED: Should create OpenAI client for GPT-4"""
        service = ConsensusService(
            frontier_model="gpt-4",
            api_key="test-key"
        )

        assert service.client is not None


class TestConsensusEvaluation:
    """Test frontier model consensus evaluation"""

    @pytest.fixture
    def consensus_service(self):
        """Create consensus service instance"""
        return ConsensusService(
            frontier_model="gpt-4-turbo-preview",
            api_key="test-key-12345"
        )

    @pytest.mark.asyncio
    async def test_evaluates_ensemble_responses_with_frontier_model(self, consensus_service):
        """
        RED: Should use frontier model to evaluate both responses

        BUSINESS VALUE:
        GPT-4 provides superior evaluation of response quality, accuracy,
        and relevance compared to simple heuristics
        """
        # Mock ensemble response
        ensemble = EnsembleResponse(
            mistral_response="Python is a high-level programming language known for simplicity.",
            llama_response="Python is an interpreted language used for web dev, ML, and automation.",
            mistral_model="course-creator-assistant",
            llama_model="llama3.1:8b-instruct-q4_K_M",
            generation_time_ms=1234
        )

        # Mock frontier model response
        mock_evaluation = {
            "selected_model": "llama",
            "reasoning": "LLama's response is more comprehensive",
            "quality_scores": {
                "mistral": {"accuracy": 0.85, "relevance": 0.90, "completeness": 0.70},
                "llama": {"accuracy": 0.90, "relevance": 0.95, "completeness": 0.85}
            }
        }

        with patch.object(consensus_service, '_call_frontier_model', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_evaluation

            result = await consensus_service.evaluate_consensus(
                user_query="What is Python?",
                ensemble_response=ensemble
            )

            assert isinstance(result, ConsensusResult)
            assert result.selected_response == ensemble.llama_response
            assert result.selected_model == "llama"
            assert result.reasoning is not None

    @pytest.mark.asyncio
    async def test_returns_selected_response_based_on_evaluation(self, consensus_service):
        """RED: Should return the response selected by frontier model"""
        ensemble = EnsembleResponse(
            mistral_response="Response A",
            llama_response="Response B",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000
        )

        mock_evaluation = {"selected_model": "mistral"}

        with patch.object(consensus_service, '_call_frontier_model', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_evaluation

            result = await consensus_service.evaluate_consensus(
                user_query="Test query",
                ensemble_response=ensemble
            )

            assert result.selected_response == "Response A"
            assert result.selected_model == "mistral"


class TestPartialEnsembleHandling:
    """Test handling when only one model succeeds"""

    @pytest.fixture
    def consensus_service(self):
        """Create consensus service"""
        return ConsensusService(frontier_model="gpt-4", api_key="test-key")

    @pytest.mark.asyncio
    async def test_returns_mistral_response_when_llama_fails(self, consensus_service):
        """
        RED: Should return Mistral response without evaluation if LLama failed

        BUSINESS VALUE:
        System continues to work even if one local model fails
        """
        ensemble = EnsembleResponse(
            mistral_response="Valid response from Mistral",
            llama_response=None,
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000,
            llama_error="Model unavailable"
        )

        result = await consensus_service.evaluate_consensus(
            user_query="Test",
            ensemble_response=ensemble
        )

        assert result.selected_response == "Valid response from Mistral"
        assert result.selected_model == "mistral"
        assert "only available response" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_returns_llama_response_when_mistral_fails(self, consensus_service):
        """RED: Should return LLama response without evaluation if Mistral failed"""
        ensemble = EnsembleResponse(
            mistral_response=None,
            llama_response="Valid response from LLama",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000,
            mistral_error="Model unavailable"
        )

        result = await consensus_service.evaluate_consensus(
            user_query="Test",
            ensemble_response=ensemble
        )

        assert result.selected_response == "Valid response from LLama"
        assert result.selected_model == "llama"

    @pytest.mark.asyncio
    async def test_returns_error_when_both_models_fail(self, consensus_service):
        """RED: Should return error result when both models failed"""
        ensemble = EnsembleResponse(
            mistral_response=None,
            llama_response=None,
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000,
            mistral_error="Failed",
            llama_error="Failed"
        )

        result = await consensus_service.evaluate_consensus(
            user_query="Test",
            ensemble_response=ensemble
        )

        assert result.selected_response is None
        assert "both models failed" in result.reasoning.lower()
        assert result.has_error is True


class TestFrontierModelFallback:
    """Test fallback when frontier model unavailable"""

    @pytest.fixture
    def consensus_service(self):
        """Create consensus service"""
        return ConsensusService(frontier_model="gpt-4", api_key="test-key")

    @pytest.mark.asyncio
    async def test_uses_simple_heuristic_when_frontier_unavailable(self, consensus_service):
        """
        RED: Should fall back to simple selection if frontier model fails

        BUSINESS VALUE:
        System continues to work even if GPT-4 is down
        """
        ensemble = EnsembleResponse(
            mistral_response="Short response",
            llama_response="Much longer and more detailed response with examples",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000
        )

        with patch.object(consensus_service, '_call_frontier_model', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API unavailable")

            result = await consensus_service.evaluate_consensus(
                user_query="Test",
                ensemble_response=ensemble
            )

            # Should still return a response (fallback selection)
            assert result.selected_response is not None
            assert "fallback" in result.reasoning.lower()


class TestConsensusResultDataClass:
    """Test ConsensusResult data class"""

    def test_consensus_result_has_required_fields(self):
        """RED: ConsensusResult should have all required fields"""
        result = ConsensusResult(
            selected_response="The selected answer",
            selected_model="mistral",
            reasoning="Mistral provided more accurate information",
            confidence_score=0.92,
            evaluation_time_ms=456
        )

        assert result.selected_response == "The selected answer"
        assert result.selected_model == "mistral"
        assert result.reasoning == "Mistral provided more accurate information"
        assert result.confidence_score == 0.92
        assert result.evaluation_time_ms == 456
        assert result.has_error is False

    def test_consensus_result_to_dict(self):
        """RED: Should convert to dictionary for JSON serialization"""
        result = ConsensusResult(
            selected_response="Answer",
            selected_model="llama",
            reasoning="Best response",
            confidence_score=0.88,
            evaluation_time_ms=123
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["selected_response"] == "Answer"
        assert result_dict["selected_model"] == "llama"
        assert result_dict["confidence_score"] == 0.88


class TestQualityMetrics:
    """Test response quality evaluation"""

    @pytest.fixture
    def consensus_service(self):
        """Create consensus service"""
        return ConsensusService(frontier_model="gpt-4", api_key="test-key")

    @pytest.mark.asyncio
    async def test_includes_quality_scores_in_result(self, consensus_service):
        """RED: Should include quality scores from frontier model"""
        ensemble = EnsembleResponse(
            mistral_response="A",
            llama_response="B",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000
        )

        mock_evaluation = {
            "selected_model": "mistral",
            "quality_scores": {
                "mistral": {"accuracy": 0.90, "relevance": 0.85},
                "llama": {"accuracy": 0.80, "relevance": 0.75}
            }
        }

        with patch.object(consensus_service, '_call_frontier_model', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_evaluation

            result = await consensus_service.evaluate_consensus(
                user_query="Test",
                ensemble_response=ensemble
            )

            assert result.quality_scores is not None
            assert "mistral" in result.quality_scores
            assert "llama" in result.quality_scores


class TestPromptConstruction:
    """Test evaluation prompt construction"""

    @pytest.fixture
    def consensus_service(self):
        """Create consensus service"""
        return ConsensusService(frontier_model="gpt-4", api_key="test-key")

    def test_build_evaluation_prompt_includes_all_context(self, consensus_service):
        """RED: Should build prompt with query and both responses"""
        ensemble = EnsembleResponse(
            mistral_response="Mistral answer",
            llama_response="LLama answer",
            mistral_model="mistral",
            llama_model="llama",
            generation_time_ms=1000
        )

        prompt = consensus_service._build_evaluation_prompt(
            user_query="What is Python?",
            ensemble_response=ensemble
        )

        assert "What is Python?" in prompt
        assert "Mistral answer" in prompt
        assert "LLama answer" in prompt
        assert "evaluate" in prompt.lower()
