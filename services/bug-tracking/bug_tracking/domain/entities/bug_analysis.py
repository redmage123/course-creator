"""
Bug Analysis Result Domain Entity

BUSINESS CONTEXT:
Stores Claude AI's analysis of a bug report, including:
- Root cause identification
- Suggested fix approach
- Affected files list
- Confidence score for the analysis

TECHNICAL CONTEXT:
- Links to parent BugReport via bug_report_id
- Tracks Claude API usage for cost monitoring
- Supports multiple analysis attempts per bug
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class ComplexityEstimate(Enum):
    """
    Estimated complexity for implementing the fix.

    TRIVIAL: Simple one-line change (typo, config value)
    SIMPLE: Small isolated change (single file, few lines)
    MODERATE: Multiple files, clear scope
    COMPLEX: Significant changes, careful testing needed
    MAJOR: Architectural changes, extensive testing required
    """
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MAJOR = "major"


@dataclass
class BugAnalysisResult:
    """
    Domain entity representing Claude's analysis of a bug.

    Attributes:
        id: Unique identifier
        bug_report_id: Reference to the analyzed bug
        root_cause_analysis: Claude's explanation of the root cause
        suggested_fix: Detailed fix recommendation
        affected_files: List of files that need modification
        confidence_score: 0-100 confidence in the analysis
        complexity_estimate: Estimated fix complexity
        claude_model_used: Claude model identifier
        tokens_used: Total tokens consumed
        analysis_duration_ms: Analysis time in milliseconds
        analysis_started_at: When analysis began
        analysis_completed_at: When analysis finished
        created_at: Record creation timestamp

    Example:
        analysis = BugAnalysisResult(
            id=str(uuid.uuid4()),
            bug_report_id="bug-123",
            root_cause_analysis="The issue is caused by a race condition...",
            suggested_fix="Add a mutex lock around the shared resource...",
            affected_files=["services/auth/login.py", "tests/test_auth.py"],
            confidence_score=85.5,
            complexity_estimate=ComplexityEstimate.MODERATE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=2500
        )
    """
    id: str
    bug_report_id: str
    root_cause_analysis: str
    suggested_fix: str
    affected_files: List[str]
    confidence_score: float
    claude_model_used: str
    tokens_used: int
    complexity_estimate: ComplexityEstimate = ComplexityEstimate.MODERATE
    analysis_duration_ms: Optional[int] = None
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate analysis data after initialization."""
        if not 0 <= self.confidence_score <= 100:
            raise ValueError("Confidence score must be between 0 and 100")
        if self.tokens_used < 0:
            raise ValueError("Tokens used cannot be negative")

    @classmethod
    def create(
        cls,
        bug_report_id: str,
        root_cause_analysis: str,
        suggested_fix: str,
        affected_files: List[str],
        confidence_score: float,
        claude_model_used: str,
        tokens_used: int,
        complexity_estimate: str = "moderate",
        analysis_duration_ms: Optional[int] = None
    ) -> "BugAnalysisResult":
        """
        Factory method to create a new analysis result.

        Args:
            bug_report_id: ID of the bug being analyzed
            root_cause_analysis: Claude's root cause explanation
            suggested_fix: Recommended fix approach
            affected_files: Files to modify
            confidence_score: Analysis confidence (0-100)
            claude_model_used: Claude model identifier
            tokens_used: Tokens consumed
            complexity_estimate: Fix complexity estimate
            analysis_duration_ms: Time taken for analysis

        Returns:
            BugAnalysisResult: New analysis result
        """
        return cls(
            id=str(uuid.uuid4()),
            bug_report_id=bug_report_id,
            root_cause_analysis=root_cause_analysis,
            suggested_fix=suggested_fix,
            affected_files=affected_files,
            confidence_score=confidence_score,
            complexity_estimate=ComplexityEstimate(complexity_estimate),
            claude_model_used=claude_model_used,
            tokens_used=tokens_used,
            analysis_duration_ms=analysis_duration_ms,
            analysis_completed_at=datetime.utcnow()
        )

    def is_high_confidence(self, threshold: float = 80.0) -> bool:
        """
        Check if analysis has high confidence for auto-fixing.

        Args:
            threshold: Minimum confidence threshold (default 80%)

        Returns:
            bool: True if confidence meets threshold
        """
        return self.confidence_score >= threshold

    def is_safe_to_autofix(self) -> bool:
        """
        Determine if this bug is safe for automated fixing.

        Criteria:
        - High confidence (>= 80%)
        - Not major complexity
        - Fewer than 5 affected files

        Returns:
            bool: True if safe for auto-fix
        """
        return (
            self.is_high_confidence(80.0) and
            self.complexity_estimate != ComplexityEstimate.MAJOR and
            len(self.affected_files) < 5
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "bug_report_id": self.bug_report_id,
            "root_cause_analysis": self.root_cause_analysis,
            "suggested_fix": self.suggested_fix,
            "affected_files": self.affected_files,
            "confidence_score": self.confidence_score,
            "complexity_estimate": self.complexity_estimate.value,
            "claude_model_used": self.claude_model_used,
            "tokens_used": self.tokens_used,
            "analysis_duration_ms": self.analysis_duration_ms,
            "analysis_started_at": self.analysis_started_at.isoformat()
                if self.analysis_started_at else None,
            "analysis_completed_at": self.analysis_completed_at.isoformat()
                if self.analysis_completed_at else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BugAnalysisResult":
        """Create BugAnalysisResult from dictionary."""
        return cls(
            id=data["id"],
            bug_report_id=data["bug_report_id"],
            root_cause_analysis=data["root_cause_analysis"],
            suggested_fix=data["suggested_fix"],
            affected_files=data.get("affected_files", []),
            confidence_score=data["confidence_score"],
            complexity_estimate=ComplexityEstimate(
                data.get("complexity_estimate", "moderate")
            ),
            claude_model_used=data["claude_model_used"],
            tokens_used=data.get("tokens_used", 0),
            analysis_duration_ms=data.get("analysis_duration_ms"),
            analysis_started_at=datetime.fromisoformat(data["analysis_started_at"])
                if data.get("analysis_started_at") else None,
            analysis_completed_at=datetime.fromisoformat(data["analysis_completed_at"])
                if data.get("analysis_completed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.utcnow()),
        )
