"""
ConsensusService - Frontier model evaluation of ensemble responses

BUSINESS PURPOSE:
Uses a frontier model (GPT-4 or Claude) to evaluate responses from the ensemble
of local models (Mistral + LLama) and select the best response based on quality,
accuracy, relevance, and completeness.

TECHNICAL IMPLEMENTATION:
Calls OpenAI API or Anthropic API to evaluate both responses. The frontier model
acts as a "judge" that provides superior evaluation compared to simple heuristics.
Includes fallback logic for robustness.

USAGE:
    consensus = ConsensusService(
        frontier_model="gpt-4-turbo-preview",
        api_key="sk-..."
    )

    result = await consensus.evaluate_consensus(
        user_query="What is Python?",
        ensemble_response=ensemble  # EnsembleResponse object
    )

    print(f"Selected: {result.selected_model}")
    print(f"Response: {result.selected_response}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Confidence: {result.confidence_score}")
"""

import logging
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from openai import AsyncOpenAI

from ai_assistant_service.application.services.ensemble_model_service import EnsembleResponse


logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """
    Result from consensus evaluation

    BUSINESS VALUE:
    Contains the selected response plus detailed metadata about the evaluation
    process, enabling transparency and quality assurance.

    ATTRIBUTES:
        selected_response: The response text selected by frontier model
        selected_model: Which model was selected ("mistral" or "llama")
        reasoning: Explanation of why this response was selected
        confidence_score: Confidence in selection (0.0 to 1.0)
        evaluation_time_ms: Time taken for evaluation in milliseconds
        quality_scores: Quality metrics for each model's response
        has_error: True if there was an error during evaluation
    """
    selected_response: Optional[str]
    selected_model: Optional[str]
    reasoning: str
    confidence_score: Optional[float] = None
    evaluation_time_ms: Optional[int] = None
    quality_scores: Optional[Dict[str, Dict[str, float]]] = None
    has_error: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ConsensusService:
    """
    Consensus service for frontier model evaluation

    RESPONSIBILITIES:
    - Initialize OpenAI or Anthropic client
    - Build evaluation prompts with context
    - Call frontier model for consensus evaluation
    - Parse evaluation results
    - Handle errors and fallbacks
    - Return structured consensus results

    ATTRIBUTES:
        frontier_model: Model identifier (e.g., "gpt-4-turbo-preview")
        api_key: API key for frontier model provider
        client: OpenAI or Anthropic client instance
    """

    def __init__(self, frontier_model: str, api_key: str):
        """
        Initialize consensus service

        Args:
            frontier_model: Model identifier (e.g., "gpt-4-turbo-preview", "claude-3-opus")
            api_key: API key for the frontier model provider

        Example:
            service = ConsensusService(
                frontier_model="gpt-4-turbo-preview",
                api_key="sk-..."
            )
        """
        self.frontier_model = frontier_model
        self.api_key = api_key

        # Initialize OpenAI client (supports GPT-4)
        if frontier_model.startswith("gpt"):
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info(f"ConsensusService initialized with OpenAI model: {frontier_model}")
        else:
            # TODO: Add Anthropic client support for Claude models
            raise NotImplementedError(
                f"Frontier model {frontier_model} not yet supported. "
                "Currently only GPT-4 models are supported."
            )

    async def evaluate_consensus(
        self,
        user_query: str,
        ensemble_response: EnsembleResponse
    ) -> ConsensusResult:
        """
        Evaluate ensemble responses and select the best one

        BUSINESS VALUE:
        - Superior evaluation compared to simple heuristics
        - Transparent reasoning for selection
        - Quality assurance for user-facing responses
        - Continuous improvement through evaluation metrics

        DECISION LOGIC:
        1. If both models succeeded → Use frontier model to evaluate
        2. If only one succeeded → Return that response (no evaluation needed)
        3. If both failed → Return error result
        4. If frontier model fails → Use simple fallback heuristic

        Args:
            user_query: User's original query
            ensemble_response: Response from ensemble of models

        Returns:
            ConsensusResult with selected response and metadata

        Example:
            result = await service.evaluate_consensus(
                user_query="Explain decorators in Python",
                ensemble_response=ensemble
            )

            if not result.has_error:
                print(f"Best answer: {result.selected_response}")
                print(f"Selected model: {result.selected_model}")
                print(f"Reasoning: {result.reasoning}")
        """
        start_time = time.time()

        # Handle partial failures (only one model succeeded)
        if ensemble_response.mistral_response is None and ensemble_response.llama_response is None:
            # Both models failed
            logger.error("Both models failed to generate responses")
            return ConsensusResult(
                selected_response=None,
                selected_model=None,
                reasoning="Both models failed to generate responses",
                has_error=True,
                evaluation_time_ms=int((time.time() - start_time) * 1000)
            )

        if ensemble_response.mistral_response is None:
            # Only LLama succeeded
            logger.warning("Mistral failed, using LLama response without evaluation")
            return ConsensusResult(
                selected_response=ensemble_response.llama_response,
                selected_model="llama",
                reasoning="Only available response (Mistral failed)",
                confidence_score=0.5,  # Lower confidence since no comparison
                evaluation_time_ms=int((time.time() - start_time) * 1000)
            )

        if ensemble_response.llama_response is None:
            # Only Mistral succeeded
            logger.warning("LLama failed, using Mistral response without evaluation")
            return ConsensusResult(
                selected_response=ensemble_response.mistral_response,
                selected_model="mistral",
                reasoning="Only available response (LLama failed)",
                confidence_score=0.5,  # Lower confidence since no comparison
                evaluation_time_ms=int((time.time() - start_time) * 1000)
            )

        # Both models succeeded - use frontier model for evaluation
        logger.info(f"Evaluating ensemble responses for query: '{user_query[:50]}...'")

        try:
            evaluation = await self._call_frontier_model(
                user_query=user_query,
                ensemble_response=ensemble_response
            )

            # Extract selected model and response
            selected_model = evaluation.get("selected_model", "mistral")
            selected_response = (
                ensemble_response.mistral_response
                if selected_model == "mistral"
                else ensemble_response.llama_response
            )

            # Extract quality scores and reasoning
            quality_scores = evaluation.get("quality_scores")
            reasoning = evaluation.get("reasoning", "Selected based on frontier model evaluation")
            confidence_score = evaluation.get("confidence_score", 0.8)

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Consensus evaluation complete in {elapsed_ms}ms: "
                f"Selected {selected_model} with confidence {confidence_score}"
            )

            return ConsensusResult(
                selected_response=selected_response,
                selected_model=selected_model,
                reasoning=reasoning,
                confidence_score=confidence_score,
                evaluation_time_ms=elapsed_ms,
                quality_scores=quality_scores,
                has_error=False
            )

        except Exception as e:
            # Frontier model failed - use fallback heuristic
            logger.error(f"Frontier model evaluation failed: {e}")
            return await self._fallback_selection(
                ensemble_response=ensemble_response,
                start_time=start_time
            )

    async def _call_frontier_model(
        self,
        user_query: str,
        ensemble_response: EnsembleResponse
    ) -> Dict[str, Any]:
        """
        Call frontier model to evaluate responses

        TECHNICAL IMPLEMENTATION:
        Constructs a structured prompt asking the frontier model to evaluate
        both responses on multiple dimensions (accuracy, relevance, completeness,
        clarity) and select the best one with reasoning.

        Args:
            user_query: User's original query
            ensemble_response: Responses from both models

        Returns:
            Dictionary with evaluation results:
            {
                "selected_model": "mistral" or "llama",
                "reasoning": "Explanation of selection",
                "confidence_score": 0.0 to 1.0,
                "quality_scores": {
                    "mistral": {"accuracy": 0.9, "relevance": 0.85, ...},
                    "llama": {"accuracy": 0.8, "relevance": 0.9, ...}
                }
            }

        Raises:
            Exception: If frontier model call fails
        """
        prompt = self._build_evaluation_prompt(
            user_query=user_query,
            ensemble_response=ensemble_response
        )

        # Call frontier model (GPT-4)
        response = await self.client.chat.completions.create(
            model=self.frontier_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert evaluator of AI responses. "
                        "Your job is to compare two responses and select the best one "
                        "based on accuracy, relevance, completeness, and clarity."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent evaluation
            max_tokens=1000
        )

        # Parse response
        evaluation_text = response.choices[0].message.content

        # Try to parse as JSON
        try:
            evaluation = json.loads(evaluation_text)
        except json.JSONDecodeError:
            # Fallback: Extract key information from text
            logger.warning("Failed to parse JSON evaluation, using text extraction")
            evaluation = self._extract_evaluation_from_text(evaluation_text)

        return evaluation

    def _build_evaluation_prompt(
        self,
        user_query: str,
        ensemble_response: EnsembleResponse
    ) -> str:
        """
        Build evaluation prompt for frontier model

        PROMPT STRUCTURE:
        1. User's original query
        2. Response A (Mistral)
        3. Response B (LLama)
        4. Evaluation criteria
        5. Expected output format (JSON)

        Args:
            user_query: User's original query
            ensemble_response: Responses from both models

        Returns:
            Complete prompt string

        Example Output:
            '''
            USER QUERY:
            What is Python?

            RESPONSE A (Mistral):
            Python is a high-level programming language...

            RESPONSE B (LLama):
            Python is an interpreted language used for...

            EVALUATION TASK:
            Please evaluate both responses on the following criteria:
            - Accuracy: Is the information correct?
            - Relevance: Does it address the user's query?
            - Completeness: Does it provide sufficient detail?
            - Clarity: Is it easy to understand?

            Return your evaluation as JSON:
            {
                "selected_model": "mistral" or "llama",
                "reasoning": "Explanation of your choice",
                "confidence_score": 0.0 to 1.0,
                "quality_scores": {
                    "mistral": {"accuracy": 0.9, "relevance": 0.85, ...},
                    "llama": {"accuracy": 0.8, "relevance": 0.9, ...}
                }
            }
            '''
        """
        return f"""USER QUERY:
{user_query}

RESPONSE A (Mistral):
{ensemble_response.mistral_response}

RESPONSE B (LLama):
{ensemble_response.llama_response}

EVALUATION TASK:
Please evaluate both responses on the following criteria:
- Accuracy: Is the information correct and factual?
- Relevance: Does it directly address the user's query?
- Completeness: Does it provide sufficient detail without being verbose?
- Clarity: Is it easy to understand and well-structured?

Return your evaluation as a JSON object with this structure:
{{
    "selected_model": "mistral" or "llama",
    "reasoning": "Brief explanation of why you selected this response",
    "confidence_score": 0.0 to 1.0,
    "quality_scores": {{
        "mistral": {{"accuracy": 0.0-1.0, "relevance": 0.0-1.0, "completeness": 0.0-1.0, "clarity": 0.0-1.0}},
        "llama": {{"accuracy": 0.0-1.0, "relevance": 0.0-1.0, "completeness": 0.0-1.0, "clarity": 0.0-1.0}}
    }}
}}
"""

    def _extract_evaluation_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract evaluation information from non-JSON text

        FALLBACK LOGIC:
        If frontier model doesn't return valid JSON, extract key information
        using text parsing heuristics.

        Args:
            text: Evaluation text from frontier model

        Returns:
            Dictionary with evaluation results
        """
        # Simple heuristic: Look for "mistral" or "llama" in the text
        text_lower = text.lower()

        if "mistral" in text_lower and "llama" not in text_lower:
            selected_model = "mistral"
        elif "llama" in text_lower and "mistral" not in text_lower:
            selected_model = "llama"
        else:
            # Default to mistral if unclear
            selected_model = "mistral"

        return {
            "selected_model": selected_model,
            "reasoning": text[:200],  # First 200 chars
            "confidence_score": 0.6  # Lower confidence for text-based extraction
        }

    async def _fallback_selection(
        self,
        ensemble_response: EnsembleResponse,
        start_time: float
    ) -> ConsensusResult:
        """
        Fallback selection when frontier model unavailable

        BUSINESS VALUE:
        System continues to work even if GPT-4/Claude is down. Uses simple
        heuristics to select response (e.g., longer response often more detailed).

        HEURISTIC:
        Select the longer response, as it's often more comprehensive.

        Args:
            ensemble_response: Responses from both models
            start_time: Start time for timing calculation

        Returns:
            ConsensusResult with fallback selection
        """
        logger.info("Using fallback selection heuristic")

        mistral_length = len(ensemble_response.mistral_response or "")
        llama_length = len(ensemble_response.llama_response or "")

        if mistral_length >= llama_length:
            selected_model = "mistral"
            selected_response = ensemble_response.mistral_response
        else:
            selected_model = "llama"
            selected_response = ensemble_response.llama_response

        elapsed_ms = int((time.time() - start_time) * 1000)

        return ConsensusResult(
            selected_response=selected_response,
            selected_model=selected_model,
            reasoning="Fallback selection (frontier model unavailable): Selected longer response",
            confidence_score=0.5,  # Lower confidence for fallback
            evaluation_time_ms=elapsed_ms,
            has_error=False
        )
