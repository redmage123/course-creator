"""
EnsembleModelService - Parallel execution of multiple LLM models

BUSINESS PURPOSE:
Calls both Mistral and LLama models in parallel to get diverse perspectives
on the same query. This provides robustness and enables consensus evaluation
by a frontier model.

TECHNICAL IMPLEMENTATION:
Uses asyncio.gather() to execute both model calls concurrently, significantly
reducing latency compared to sequential execution. Handles partial failures
gracefully.

USAGE:
    local_llm = LocalLLMService(...)
    ensemble = EnsembleModelService(local_llm_service=local_llm)

    result = await ensemble.generate_ensemble_responses(
        user_message="What is Python?",
        system_prompt="You are a helpful assistant",
        rag_context="Python docs...",
        kg_context="Related: Python courses",
        metadata_context="Course: Python Programming"
    )

    # result.mistral_response: Mistral's answer
    # result.llama_response: LLama's answer
    # result.generation_time_ms: Total time (parallel)
"""

import logging
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class EnsembleResponse:
    """
    Response from ensemble of models

    BUSINESS VALUE:
    Contains responses from both models plus metadata for consensus evaluation.
    Tracks which models succeeded/failed for transparency and debugging.

    ATTRIBUTES:
        mistral_response: Response from Mistral model (or None if failed)
        llama_response: Response from LLama model (or None if failed)
        mistral_model: Model identifier for Mistral
        llama_model: Model identifier for LLama
        generation_time_ms: Total generation time in milliseconds
        mistral_error: Error message if Mistral failed
        llama_error: Error message if LLama failed
    """
    mistral_response: Optional[str]
    llama_response: Optional[str]
    mistral_model: str
    llama_model: str
    generation_time_ms: int
    mistral_error: Optional[str] = None
    llama_error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class EnsembleModelService:
    """
    Ensemble model service for parallel LLM execution

    RESPONSIBILITIES:
    - Call Mistral and LLama models in parallel
    - Build comprehensive prompts with all context types
    - Handle partial failures gracefully
    - Track performance metrics
    - Return structured ensemble responses

    ATTRIBUTES:
        local_llm_service: Service for calling local Ollama models
        mistral_model: Model identifier for Mistral (fine-tuned)
        llama_model: Model identifier for LLama
    """

    def __init__(self, local_llm_service):
        """
        Initialize ensemble model service

        Args:
            local_llm_service: LocalLLMService instance for Ollama integration
        """
        self.local_llm_service = local_llm_service

        # Model identifiers
        self.mistral_model = "course-creator-assistant"  # Fine-tuned Mistral 7B
        self.llama_model = "llama3.1:8b-instruct-q4_K_M"  # LLama 3.1

        logger.info(
            f"EnsembleModelService initialized: "
            f"Mistral={self.mistral_model}, LLama={self.llama_model}"
        )

    async def generate_ensemble_responses(
        self,
        user_message: str,
        system_prompt: str,
        rag_context: Optional[str] = None,
        kg_context: Optional[str] = None,
        metadata_context: Optional[str] = None
    ) -> EnsembleResponse:
        """
        Generate responses from both models in parallel

        BUSINESS VALUE:
        - Faster response time (parallel execution)
        - Multiple perspectives on same query
        - Robustness (continues even if one model fails)
        - Quality assurance (enables consensus evaluation)

        Args:
            user_message: User's query
            system_prompt: System instructions for the models
            rag_context: RAG-retrieved relevant content (optional)
            kg_context: Knowledge graph relationships (optional)
            metadata_context: Fuzzy-matched course/content metadata (optional)

        Returns:
            EnsembleResponse with both model outputs and metadata

        Example:
            result = await ensemble.generate_ensemble_responses(
                user_message="Explain Python decorators",
                system_prompt="You are a helpful programming tutor",
                rag_context="Decorators are a design pattern...",
                kg_context="Related concepts: Functions, Closures",
                metadata_context="Course: Advanced Python (similarity: 0.92)"
            )

            if result.mistral_response and result.llama_response:
                # Both models succeeded
                print(f"Mistral: {result.mistral_response}")
                print(f"LLama: {result.llama_response}")
            elif result.mistral_response:
                # Only Mistral succeeded
                print(f"Mistral only: {result.mistral_response}")
            elif result.llama_response:
                # Only LLama succeeded
                print(f"LLama only: {result.llama_response}")
            else:
                # Both failed
                print("Both models failed")
        """
        start_time = time.time()

        # Build comprehensive prompt with all context
        prompt = self._build_prompt(
            user_message=user_message,
            system_prompt=system_prompt,
            rag_context=rag_context,
            kg_context=kg_context,
            metadata_context=metadata_context
        )

        logger.info(
            f"Generating ensemble responses for query: '{user_message[:50]}...'"
        )

        # Call both models in parallel using asyncio.gather
        mistral_task = self._generate_with_model(
            prompt=prompt,
            model=self.mistral_model
        )

        llama_task = self._generate_with_model(
            prompt=prompt,
            model=self.llama_model
        )

        # Execute in parallel
        results = await asyncio.gather(
            mistral_task,
            llama_task,
            return_exceptions=True
        )

        # Parse results
        mistral_result = results[0]
        llama_result = results[1]

        # Extract responses and errors
        mistral_response = None
        mistral_error = None
        if isinstance(mistral_result, Exception):
            mistral_error = str(mistral_result)
            logger.warning(f"Mistral model failed: {mistral_error}")
        else:
            mistral_response = mistral_result

        llama_response = None
        llama_error = None
        if isinstance(llama_result, Exception):
            llama_error = str(llama_result)
            logger.warning(f"LLama model failed: {llama_error}")
        else:
            llama_response = llama_result

        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Ensemble generation complete in {elapsed_ms}ms: "
            f"Mistral={'OK' if mistral_response else 'FAILED'}, "
            f"LLama={'OK' if llama_response else 'FAILED'}"
        )

        return EnsembleResponse(
            mistral_response=mistral_response,
            llama_response=llama_response,
            mistral_model=self.mistral_model,
            llama_model=self.llama_model,
            generation_time_ms=elapsed_ms,
            mistral_error=mistral_error,
            llama_error=llama_error
        )

    async def _generate_with_model(
        self,
        prompt: str,
        model: str
    ) -> str:
        """
        Generate response with specific model

        TECHNICAL IMPLEMENTATION:
        Wrapper around local_llm_service.generate_response() that adds
        model-specific error handling and logging.

        Args:
            prompt: Complete prompt with all context
            model: Model identifier (mistral or llama)

        Returns:
            Generated response text

        Raises:
            Exception: If model generation fails
        """
        try:
            response = await self.local_llm_service.generate_response(
                prompt=prompt,
                model=model
            )
            return response
        except Exception as e:
            logger.error(f"Model {model} failed: {e}")
            raise

    def _build_prompt(
        self,
        user_message: str,
        system_prompt: str,
        rag_context: Optional[str] = None,
        kg_context: Optional[str] = None,
        metadata_context: Optional[str] = None
    ) -> str:
        """
        Build comprehensive prompt with all context types

        BUSINESS CONTEXT:
        Combines multiple context sources into a single coherent prompt
        that provides the model with all relevant information for answering
        the user's query.

        PROMPT STRUCTURE:
        1. System prompt (role and instructions)
        2. RAG context (relevant content from knowledge base)
        3. Knowledge graph context (related concepts and relationships)
        4. Metadata context (fuzzy-matched courses/content)
        5. User message (the actual query)

        Args:
            user_message: User's query
            system_prompt: System instructions
            rag_context: RAG-retrieved content (optional)
            kg_context: Knowledge graph relationships (optional)
            metadata_context: Fuzzy-matched metadata (optional)

        Returns:
            Complete prompt string

        Example Output:
            '''
            SYSTEM: You are a helpful programming tutor

            CONTEXT FROM KNOWLEDGE BASE:
            Decorators are a design pattern in Python...

            RELATED CONCEPTS:
            - Functions
            - Closures
            - Higher-order functions

            RELEVANT COURSES:
            - Course: 'Advanced Python' (similarity: 0.92)
              Python programming techniques and patterns

            USER QUESTION:
            Explain Python decorators
            '''
        """
        prompt_parts = []

        # System prompt
        if system_prompt:
            prompt_parts.append(f"SYSTEM: {system_prompt}\n")

        # RAG context
        if rag_context:
            prompt_parts.append(f"CONTEXT FROM KNOWLEDGE BASE:\n{rag_context}\n")

        # Knowledge graph context
        if kg_context:
            prompt_parts.append(f"RELATED CONCEPTS:\n{kg_context}\n")

        # Metadata context
        if metadata_context:
            prompt_parts.append(f"RELEVANT COURSES:\n{metadata_context}\n")

        # User message
        prompt_parts.append(f"USER QUESTION:\n{user_message}")

        return "\n".join(prompt_parts)
