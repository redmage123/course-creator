"""
Brain Service - Application Layer

This module implements the core application logic for brain lifecycle management,
including creation, learning, prediction, and continuous intelligence improvement.

Business Context:
    The BrainService orchestrates all brain operations, implementing the continuous
    learning loop where every interaction adjusts neural weights. It coordinates
    between the neural inference engine (NIMCP), LLM fallback, and persistence layer
    to create a self-aware, continuously improving AI system.

Core Workflows:
    1. Brain Creation: Initialize new brain instances with proper topology
    2. Prediction: Neural inference with confidence-based LLM fallback
    3. Learning: Weight adjustment from every interaction
    4. Persistence: Save neural state after N interactions
    5. Cloning: COW clone creation for efficient student brains

Architectural Principles:
    - Single Responsibility: Application logic only (no domain or infrastructure)
    - Open/Closed: Extensible through dependency injection
    - Dependency Inversion: Depends on domain interfaces, not implementations
    - Use Case Pattern: Each public method represents a use case

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID

try:
    import nimcp
except ImportError:
    # NIMCP library not yet installed - will be handled in deployment
    nimcp = None

from nimcp_service.domain.entities.brain import Brain, BrainType, PerformanceMetrics
from nimcp_service.domain.interfaces.brain_repository import BrainRepository


class BrainServiceError(Exception):
    """Base exception for brain service errors."""
    pass


class BrainNotFoundError(BrainServiceError):
    """Raised when brain instance is not found."""
    pass


class BrainCreationError(BrainServiceError):
    """Raised when brain creation fails."""
    pass


class BrainLearningError(BrainServiceError):
    """Raised when brain learning operation fails."""
    pass


class BrainService:
    """
    Application service for brain lifecycle management and continuous learning.

    Business Responsibilities:
        - Create and initialize brain instances with proper neural topology
        - Execute predictions using neural inference or LLM fallback
        - Implement continuous learning loop (weight adjustment every interaction)
        - Persist neural state to filesystem after N interactions
        - Manage COW cloning for memory-efficient student brains
        - Track performance metrics and meta-cognitive self-awareness

    Dependencies:
        - BrainRepository: Domain interface for brain persistence
        - NIMCP Library: Neuromorphic inference and learning engine
        - LLM Client: Fallback for low-confidence predictions (injected)

    Configuration:
        - brain_states_dir: Directory for .bin files with neural weights
        - persistence_interval: Save neural state every N interactions (default: 100)
        - confidence_threshold: Threshold for neural vs LLM decision (default: 0.85)
    """

    def __init__(
        self,
        repository: BrainRepository,
        brain_states_dir: str = "/app/brain_states",
        persistence_interval: int = 100,
        confidence_threshold: float = 0.85,
        llm_client: Optional[Any] = None
    ):
        """
        Initialize brain service with dependencies.

        Args:
            repository: Brain repository for persistence
            brain_states_dir: Directory path for neural state .bin files
            persistence_interval: How often to persist neural state (# interactions)
            confidence_threshold: Confidence threshold for using neural inference
            llm_client: Optional LLM client for low-confidence fallback
        """
        self.repository = repository
        self.brain_states_dir = Path(brain_states_dir)
        self.persistence_interval = persistence_interval
        self.confidence_threshold = confidence_threshold
        self.llm_client = llm_client

        # In-memory cache of loaded NIMCP brain instances
        # Key: brain_id (str), Value: nimcp.Brain instance
        self._brain_cache: Dict[str, Any] = {}

        # Ensure brain states directory exists
        self.brain_states_dir.mkdir(parents=True, exist_ok=True)

        # Interaction counters for persistence (key: brain_id, value: count)
        self._interaction_counts: Dict[str, int] = {}

    async def create_platform_brain(
        self,
        neuron_count: int = 50000,
        enable_ethics: bool = True,
        enable_curiosity: bool = True
    ) -> Brain:
        """
        Create the singleton platform brain (master orchestrator).

        Business Logic:
            Platform brain is created once at system initialization and
            serves as the master brain that orchestrates all sub-brains.
            It should have the largest neuron count and all advanced features enabled.

        Args:
            neuron_count: Number of neurons in the network (default: 50K)
            enable_ethics: Enable Golden Rule ethics engine
            enable_curiosity: Enable autonomous curiosity system

        Returns:
            Created platform brain instance

        Raises:
            BrainCreationError: If platform brain already exists or creation fails
        """
        # Check if platform brain already exists
        existing = await self.repository.get_platform_brain()
        if existing:
            raise BrainCreationError("Platform brain already exists")

        try:
            # Create domain entity
            brain = Brain(
                brain_type=BrainType.PLATFORM,
                owner_id=None,  # Platform brain has no owner
                parent_brain_id=None,  # Platform brain has no parent
                state_file_path=str(self.brain_states_dir / f"platform_{datetime.utcnow().isoformat()}.bin")
            )

            # Initialize NIMCP brain instance
            if nimcp:
                nimcp_brain = nimcp.Brain(
                    name="platform_brain",
                    size=neuron_count,
                    task="CLASSIFICATION"  # Can be extended to support other task types
                )

                # Enable advanced features
                if enable_ethics:
                    nimcp_brain.enable_ethics()
                if enable_curiosity:
                    nimcp_brain.enable_curiosity()

                # Save initial state
                nimcp_brain.save(brain.state_file_path)

                # Cache in memory
                self._brain_cache[str(brain.brain_id)] = nimcp_brain

            # Persist to repository
            brain = await self.repository.create(brain)

            return brain

        except Exception as e:
            raise BrainCreationError(f"Failed to create platform brain: {str(e)}") from e

    async def create_student_brain(
        self,
        student_id: UUID,
        neuron_count: int = 10000,
        clone_from_platform: bool = True
    ) -> Brain:
        """
        Create a personal learning guide brain for a student.

        Business Logic:
            Student brains are COW clones of the platform brain for memory efficiency.
            They learn the student's unique patterns (pace, style, preferences) while
            sharing the platform brain's base knowledge.

        Args:
            student_id: UUID of the student owner
            neuron_count: Number of neurons if not cloning (default: 10K)
            clone_from_platform: Whether to COW clone from platform brain

        Returns:
            Created student brain instance

        Raises:
            BrainCreationError: If student brain already exists or creation fails
        """
        # Check if student already has a brain
        existing = await self.repository.get_by_owner(student_id, BrainType.STUDENT)
        if existing:
            raise BrainCreationError(f"Student {student_id} already has a brain")

        try:
            parent_brain_id = None

            if clone_from_platform:
                # Get platform brain for cloning
                platform_brain = await self.repository.get_platform_brain()
                if not platform_brain:
                    raise BrainCreationError("Platform brain must exist before creating student brains")

                parent_brain_id = platform_brain.brain_id

                # Load platform brain if not cached
                if str(platform_brain.brain_id) not in self._brain_cache:
                    if nimcp:
                        platform_nimcp = nimcp.Brain.load(platform_brain.state_file_path)
                        self._brain_cache[str(platform_brain.brain_id)] = platform_nimcp

            # Create domain entity
            brain = Brain(
                brain_type=BrainType.STUDENT,
                owner_id=student_id,
                parent_brain_id=parent_brain_id,
                state_file_path=str(self.brain_states_dir / f"student_{student_id}_{datetime.utcnow().isoformat()}.bin")
            )

            # Initialize NIMCP brain instance
            if nimcp:
                if clone_from_platform and parent_brain_id:
                    # COW clone from platform brain
                    parent_nimcp = self._brain_cache[str(parent_brain_id)]
                    nimcp_brain = parent_nimcp.clone_cow()

                    # Track COW statistics
                    # Note: Actual COW stats would come from nimcp.brain_get_cow_stats()
                    # For now, we'll set placeholder values
                    brain.cow_stats.is_cow_clone = True
                    brain.cow_stats.cow_shared_bytes = 50 * 1024 * 1024  # ~50MB shared
                    brain.cow_stats.cow_copied_bytes = 0  # Nothing copied yet

                else:
                    # Create independent brain
                    nimcp_brain = nimcp.Brain(
                        name=f"student_{student_id}",
                        size=neuron_count,
                        task="CLASSIFICATION"
                    )

                # Save initial state
                nimcp_brain.save(brain.state_file_path)

                # Cache in memory
                self._brain_cache[str(brain.brain_id)] = nimcp_brain

            # Persist to repository
            brain = await self.repository.create(brain)

            return brain

        except Exception as e:
            raise BrainCreationError(f"Failed to create student brain: {str(e)}") from e

    async def predict(
        self,
        brain_id: UUID,
        features: List[float],
        use_llm_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Make a prediction using the brain with optional LLM fallback.

        Business Logic:
            This implements the core decision flow:
            1. Neural inference (fast, free)
            2. Check confidence
            3. If confidence >= threshold: Use neural prediction
            4. If confidence < threshold: Fall back to LLM
            5. If LLM used: Learn from LLM response (supervised learning)
            6. Record interaction for metrics

        Args:
            brain_id: UUID of the brain to use
            features: Input feature vector for prediction
            use_llm_fallback: Whether to use LLM for low-confidence predictions

        Returns:
            Dictionary with prediction results:
                {
                    "output": [...],  # Prediction output
                    "confidence": 0.87,  # Confidence score
                    "used_llm": False,  # Whether LLM was used
                    "neural_inference_rate": 85.3  # Current neural rate %
                }

        Raises:
            BrainNotFoundError: If brain_id doesn't exist
            BrainLearningError: If prediction operation fails
        """
        # Load brain entity
        brain = await self.repository.get_by_id(brain_id)
        if not brain:
            raise BrainNotFoundError(f"Brain {brain_id} not found")

        try:
            # Load NIMCP brain instance if not cached
            if str(brain_id) not in self._brain_cache:
                if nimcp:
                    nimcp_brain = nimcp.Brain.load(brain.state_file_path)
                    self._brain_cache[str(brain_id)] = nimcp_brain

            # Perform neural inference
            used_llm = False
            confidence = 0.0
            output = []

            if nimcp:
                nimcp_brain = self._brain_cache[str(brain_id)]
                result = nimcp_brain.predict(features)
                output = result.get("output", [])
                confidence = result.get("confidence", 0.0)

                # Decision: Neural vs LLM
                if brain.should_use_llm(confidence, self.confidence_threshold) and use_llm_fallback:
                    # Low confidence - use LLM
                    if self.llm_client:
                        llm_result = await self._query_llm(features)
                        output = llm_result["output"]
                        confidence = llm_result["confidence"]
                        used_llm = True

                        # LEARNING: Learn from LLM response
                        # This is supervised learning - LLM provides ground truth
                        await self._learn_from_llm(brain_id, features, llm_result)

            # Record interaction
            brain.record_interaction(used_llm=used_llm, confidence=confidence)

            # Update interaction count for persistence
            brain_id_str = str(brain_id)
            self._interaction_counts[brain_id_str] = self._interaction_counts.get(brain_id_str, 0) + 1

            # Persist neural state if threshold reached
            if self._interaction_counts[brain_id_str] >= self.persistence_interval:
                await self._persist_brain_state(brain_id)
                self._interaction_counts[brain_id_str] = 0

            # Update brain entity in repository
            await self.repository.update(brain)

            return {
                "output": output,
                "confidence": confidence,
                "used_llm": used_llm,
                "neural_inference_rate": brain.performance.neural_inference_rate,
                "llm_cost_savings_percent": brain.performance.llm_cost_savings_percent
            }

        except Exception as e:
            raise BrainLearningError(f"Prediction failed for brain {brain_id}: {str(e)}") from e

    async def learn(
        self,
        brain_id: UUID,
        features: List[float],
        label: str,
        confidence: float = 0.95
    ) -> None:
        """
        Teach the brain a new example through supervised learning.

        Business Logic:
            This is explicit supervised learning where we provide ground truth.
            The brain adjusts its neural weights to learn this association.
            Future similar inputs will trigger similar outputs with higher confidence.

        Args:
            brain_id: UUID of the brain to teach
            features: Input feature vector
            label: Ground truth label/classification
            confidence: Confidence in this training example (0-1)

        Raises:
            BrainNotFoundError: If brain_id doesn't exist
            BrainLearningError: If learning operation fails
        """
        # Load brain entity
        brain = await self.repository.get_by_id(brain_id)
        if not brain:
            raise BrainNotFoundError(f"Brain {brain_id} not found")

        try:
            # Load NIMCP brain if not cached
            if str(brain_id) not in self._brain_cache:
                if nimcp:
                    nimcp_brain = nimcp.Brain.load(brain.state_file_path)
                    self._brain_cache[str(brain_id)] = nimcp_brain

            # Perform learning
            if nimcp:
                nimcp_brain = self._brain_cache[str(brain_id)]
                nimcp_brain.learn(features=features, label=label, confidence=confidence)

            # Update learning timestamp
            brain.performance.last_learning_timestamp = datetime.utcnow()
            brain.last_updated = datetime.utcnow()

            # Persist to repository
            await self.repository.update(brain)

        except Exception as e:
            raise BrainLearningError(f"Learning failed for brain {brain_id}: {str(e)}") from e

    async def reinforce(
        self,
        brain_id: UUID,
        features: List[float],
        reward: float
    ) -> None:
        """
        Reinforce brain behavior through reward-based learning.

        Business Logic:
            This is reinforcement learning where the brain learns from outcomes.
            Positive rewards strengthen neural pathways, negative rewards weaken them.
            Called after observing the success/failure of a prediction.

        Args:
            brain_id: UUID of the brain to reinforce
            features: Input features from the interaction
            reward: Reward signal (0-1, where 1 = perfect success, 0 = total failure)

        Raises:
            BrainNotFoundError: If brain_id doesn't exist
            BrainLearningError: If reinforcement operation fails
        """
        # Load brain entity
        brain = await self.repository.get_by_id(brain_id)
        if not brain:
            raise BrainNotFoundError(f"Brain {brain_id} not found")

        try:
            # Load NIMCP brain if not cached
            if str(brain_id) not in self._brain_cache:
                if nimcp:
                    nimcp_brain = nimcp.Brain.load(brain.state_file_path)
                    self._brain_cache[str(brain_id)] = nimcp_brain

            # Perform reinforcement learning
            if nimcp:
                nimcp_brain = self._brain_cache[str(brain_id)]
                # Note: NIMCP API would have a reinforce() or reward() method
                # nimcp_brain.reinforce(features=features, reward=reward)
                pass  # Placeholder until NIMCP API is confirmed

            # Update brain metadata
            brain.last_updated = datetime.utcnow()
            await self.repository.update(brain)

        except Exception as e:
            raise BrainLearningError(f"Reinforcement failed for brain {brain_id}: {str(e)}") from e

    async def get_brain(self, brain_id: UUID) -> Brain:
        """Retrieve a brain instance by ID."""
        brain = await self.repository.get_by_id(brain_id)
        if not brain:
            raise BrainNotFoundError(f"Brain {brain_id} not found")
        return brain

    async def get_student_brain(self, student_id: UUID) -> Brain:
        """Retrieve a student's personal brain."""
        brain = await self.repository.get_by_owner(student_id, BrainType.STUDENT)
        if not brain:
            raise BrainNotFoundError(f"Student {student_id} has no brain")
        return brain

    async def get_platform_brain(self) -> Brain:
        """Retrieve the platform brain."""
        brain = await self.repository.get_platform_brain()
        if not brain:
            raise BrainNotFoundError("Platform brain not found")
        return brain

    async def _persist_brain_state(self, brain_id: UUID) -> None:
        """
        Persist neural state to filesystem.

        Business Logic:
            Saves the current neural network weights to a .bin file.
            Called every N interactions to ensure learning is preserved.
        """
        brain = await self.repository.get_by_id(brain_id)
        if not brain:
            return

        if str(brain_id) in self._brain_cache and nimcp:
            nimcp_brain = self._brain_cache[str(brain_id)]
            nimcp_brain.save(brain.state_file_path)

    async def _query_llm(self, features: List[float]) -> Dict[str, Any]:
        """
        Query LLM for ground truth prediction.

        Business Logic:
            Called when neural confidence is below threshold.
            LLM provides high-quality prediction that the brain can learn from.

        Returns:
            Dictionary with LLM prediction:
                {"output": [...], "confidence": 0.95}
        """
        if not self.llm_client:
            # No LLM available - return neutral prediction
            return {"output": [0.5] * len(features), "confidence": 0.5}

        # TODO: Implement actual LLM querying logic
        # This would integrate with the existing AI pipeline in course-creator
        return {"output": [0.8], "confidence": 0.95}

    async def _learn_from_llm(
        self,
        brain_id: UUID,
        features: List[float],
        llm_result: Dict[str, Any]
    ) -> None:
        """
        Learn from LLM response through supervised learning.

        Business Logic:
            When the brain is uncertain and queries the LLM, it learns from
            the LLM's response. This is how the brain becomes smarter over time
            and reduces its dependence on expensive LLM calls.
        """
        # Extract label from LLM output
        # The exact format depends on the LLM response structure
        label = str(llm_result.get("output", ["unknown"])[0])
        confidence = llm_result.get("confidence", 0.95)

        await self.learn(brain_id, features, label, confidence)
