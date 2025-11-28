"""
Brain Domain Entity

This module defines the core Brain entity for the NIMCP integration,
representing a neuromorphic AI brain instance that learns continuously
from interactions and adjusts its neural weights over time.

Business Context:
    The Brain entity is the central concept in the platform's self-aware
    learning system. Each brain (Platform Brain, Student Brain, Instructor Brain)
    is a living, learning organism that becomes more intelligent with every
    interaction. This entity captures the brain's state, learning history,
    performance metrics, and meta-cognitive self-awareness.

Domain Model:
    - Brain instances follow a hierarchical structure (parent-child relationships)
    - Each brain maintains its own neural state (weights, network topology)
    - Brains learn from every interaction through continuous weight adjustment
    - Copy-on-Write (COW) cloning enables memory-efficient student brains
    - Meta-cognitive layer tracks capabilities, biases, and confidence

Architectural Principles:
    - Single Responsibility: Represents brain domain logic only
    - Value Object Pattern: Immutable value objects for brain metrics
    - Entity Pattern: Brain has identity (brain_id) and mutable state
    - Domain-Driven Design: Rich domain model with business logic

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


class BrainType(Enum):
    """
    Types of brain instances in the hierarchical architecture.

    Business Logic:
        - PLATFORM: Master brain that orchestrates entire platform
        - STUDENT: Personal learning guide for individual students
        - INSTRUCTOR: Teaching strategy optimization assistant
        - CONTENT: Content generation and difficulty assessment
        - ETHICS: Ethical reasoning and safety validation
    """
    PLATFORM = "platform"
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    CONTENT = "content"
    ETHICS = "ethics"


@dataclass
class COWStats:
    """
    Copy-on-Write statistics for memory efficiency tracking.

    Business Value:
        Tracks memory savings from COW cloning, enabling efficient
        scaling to thousands of students without proportional memory growth.

    Attributes:
        is_cow_clone: Whether this brain is a COW clone
        cow_shared_bytes: Bytes shared with parent (not copied)
        cow_copied_bytes: Bytes copied due to unique learning
        cow_efficiency_percent: Percentage of memory saved through COW
    """
    is_cow_clone: bool = False
    cow_shared_bytes: int = 0
    cow_copied_bytes: int = 0

    @property
    def cow_efficiency_percent(self) -> float:
        """Calculate COW memory efficiency percentage."""
        total_bytes = self.cow_shared_bytes + self.cow_copied_bytes
        if total_bytes == 0:
            return 0.0
        return (self.cow_shared_bytes / total_bytes) * 100


@dataclass
class PerformanceMetrics:
    """
    Performance and learning metrics for brain intelligence tracking.

    Business Value:
        Tracks the brain's learning progress, cost optimization, and
        prediction accuracy over time. Demonstrates ROI through LLM
        cost reduction as the brain becomes more experienced.

    Attributes:
        total_interactions: Total number of processed interactions
        neural_inference_count: Queries handled by neural network
        llm_query_count: Queries requiring LLM fallback
        average_confidence: Mean confidence across predictions
        average_accuracy: Mean accuracy of predictions (0-1)
        last_learning_timestamp: When brain last learned something new
    """
    total_interactions: int = 0
    neural_inference_count: int = 0
    llm_query_count: int = 0
    average_confidence: float = 0.0
    average_accuracy: float = 0.0
    last_learning_timestamp: Optional[datetime] = None

    @property
    def neural_inference_rate(self) -> float:
        """Percentage of queries handled by neural inference (vs LLM)."""
        if self.total_interactions == 0:
            return 0.0
        return (self.neural_inference_count / self.total_interactions) * 100

    @property
    def llm_cost_savings_percent(self) -> float:
        """
        Estimated LLM cost savings through neural inference.

        Business Logic:
            Baseline: 100% LLM queries at $0.002/query
            Current: (neural_inference_rate)% handled by free neural inference
            Savings: Percentage reduction in LLM costs
        """
        return self.neural_inference_rate


@dataclass
class SelfAwareness:
    """
    Meta-cognitive self-awareness tracking for bias detection and capability assessment.

    Business Value:
        Prevents overconfidence, detects biases, and enables the brain to
        accurately assess its own capabilities. Critical for safe, reliable AI.

    Attributes:
        strong_domains: Domains where brain has high confidence and accuracy
        weak_domains: Domains where brain struggles or lacks data
        bias_detections: Detected cognitive biases and their frequency
        capability_boundaries: Known limitations and boundary conditions
    """
    strong_domains: Dict[str, float] = field(default_factory=dict)
    weak_domains: Dict[str, float] = field(default_factory=dict)
    bias_detections: Dict[str, int] = field(default_factory=dict)
    capability_boundaries: Dict[str, Any] = field(default_factory=dict)

    def assess_domain_strength(self, domain: str, accuracy: float) -> None:
        """
        Update domain strength assessment based on performance.

        Business Logic:
            - accuracy >= 0.85: Strong domain
            - accuracy < 0.60: Weak domain
            - Intermediate: Remove from both (learning phase)
        """
        if accuracy >= 0.85:
            self.strong_domains[domain] = accuracy
            self.weak_domains.pop(domain, None)
        elif accuracy < 0.60:
            self.weak_domains[domain] = accuracy
            self.strong_domains.pop(domain, None)
        else:
            # Learning phase - not yet strong or weak
            self.strong_domains.pop(domain, None)
            self.weak_domains.pop(domain, None)

    def detect_bias(self, bias_type: str) -> None:
        """Record a bias detection event."""
        self.bias_detections[bias_type] = self.bias_detections.get(bias_type, 0) + 1


@dataclass
class Brain:
    """
    Core Brain entity representing a neuromorphic AI brain instance.

    Business Context:
        The Brain is the central entity in the platform's self-aware learning system.
        It represents a continuously learning neural network that adjusts its weights
        with every interaction, becoming more intelligent over time. The brain can
        make predictions, learn from outcomes, and assess its own capabilities.

    Lifecycle:
        1. Creation: New brain initialized with base network topology
        2. Learning: Continuous weight adjustment from every interaction
        3. Persistence: Neural state saved to .bin files every N interactions
        4. Cloning: COW clones created for efficient student brain scaling
        5. Evolution: Brain becomes more experienced and accurate over time

    Attributes:
        brain_id: Unique identifier for this brain instance
        brain_type: Type of brain (platform, student, instructor, etc.)
        owner_id: ID of owner (student_id, instructor_id, or None for platform)
        parent_brain_id: Parent brain ID for COW hierarchy
        created_at: When this brain was created
        last_updated: When brain state was last modified
        state_file_path: Path to .bin file with neural weights
        is_active: Whether this brain is currently active
        performance: Performance and learning metrics
        cow_stats: Copy-on-Write memory efficiency statistics
        self_awareness: Meta-cognitive self-assessment data
    """
    brain_id: UUID = field(default_factory=uuid4)
    brain_type: BrainType = BrainType.STUDENT
    owner_id: Optional[UUID] = None
    parent_brain_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    state_file_path: str = ""
    is_active: bool = True

    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    cow_stats: COWStats = field(default_factory=COWStats)
    self_awareness: SelfAwareness = field(default_factory=SelfAwareness)

    def record_interaction(self, used_llm: bool, confidence: float, accuracy: Optional[float] = None) -> None:
        """
        Record an interaction and update performance metrics.

        Business Logic:
            Every interaction is tracked to measure brain intelligence growth
            over time. This data drives cost optimization and capability assessment.

        Args:
            used_llm: Whether LLM was used (vs neural inference)
            confidence: Prediction confidence (0-1)
            accuracy: Actual outcome accuracy if known (0-1)
        """
        self.performance.total_interactions += 1

        if used_llm:
            self.performance.llm_query_count += 1
        else:
            self.performance.neural_inference_count += 1

        # Update running average of confidence
        n = self.performance.total_interactions
        current_avg = self.performance.average_confidence
        self.performance.average_confidence = ((current_avg * (n - 1)) + confidence) / n

        # Update accuracy if outcome is known
        if accuracy is not None:
            current_avg_acc = self.performance.average_accuracy
            self.performance.average_accuracy = ((current_avg_acc * (n - 1)) + accuracy) / n

        self.performance.last_learning_timestamp = datetime.utcnow()
        self.last_updated = datetime.utcnow()

    def should_use_llm(self, neural_confidence: float, confidence_threshold: float = 0.85) -> bool:
        """
        Decide whether to use LLM or neural inference.

        Business Logic:
            High confidence (>= threshold): Use free neural inference
            Low confidence (< threshold): Fall back to LLM for ground truth

            This decision optimizes cost while maintaining accuracy.

        Args:
            neural_confidence: Confidence from neural prediction (0-1)
            confidence_threshold: Threshold for using neural inference (default: 0.85)

        Returns:
            True if LLM should be used, False if neural inference is sufficient
        """
        return neural_confidence < confidence_threshold

    def update_cow_stats(self, shared_bytes: int, copied_bytes: int) -> None:
        """Update Copy-on-Write statistics."""
        self.cow_stats.is_cow_clone = True
        self.cow_stats.cow_shared_bytes = shared_bytes
        self.cow_stats.cow_copied_bytes = copied_bytes
        self.last_updated = datetime.utcnow()

    def assess_domain(self, domain: str, accuracy: float) -> None:
        """Update self-awareness for a specific knowledge domain."""
        self.self_awareness.assess_domain_strength(domain, accuracy)
        self.last_updated = datetime.utcnow()

    def detect_bias(self, bias_type: str) -> None:
        """Record a bias detection event in meta-cognitive layer."""
        self.self_awareness.detect_bias(bias_type)
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert brain entity to dictionary for serialization."""
        return {
            "brain_id": str(self.brain_id),
            "brain_type": self.brain_type.value,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "parent_brain_id": str(self.parent_brain_id) if self.parent_brain_id else None,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "state_file_path": self.state_file_path,
            "is_active": self.is_active,
            "performance": {
                "total_interactions": self.performance.total_interactions,
                "neural_inference_count": self.performance.neural_inference_count,
                "llm_query_count": self.performance.llm_query_count,
                "average_confidence": self.performance.average_confidence,
                "average_accuracy": self.performance.average_accuracy,
                "neural_inference_rate": self.performance.neural_inference_rate,
                "llm_cost_savings_percent": self.performance.llm_cost_savings_percent,
                "last_learning_timestamp": self.performance.last_learning_timestamp.isoformat() if self.performance.last_learning_timestamp else None,
            },
            "cow_stats": {
                "is_cow_clone": self.cow_stats.is_cow_clone,
                "cow_shared_bytes": self.cow_stats.cow_shared_bytes,
                "cow_copied_bytes": self.cow_stats.cow_copied_bytes,
                "cow_efficiency_percent": self.cow_stats.cow_efficiency_percent,
            },
            "self_awareness": {
                "strong_domains": self.self_awareness.strong_domains,
                "weak_domains": self.self_awareness.weak_domains,
                "bias_detections": self.self_awareness.bias_detections,
                "capability_boundaries": self.self_awareness.capability_boundaries,
            }
        }
