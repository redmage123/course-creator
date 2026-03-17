"""Course-related data models."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class LearningObjective:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    bloom_level: str = "understand"
    assessment_criteria: str = ""
    time_allocation: int = 10

@dataclass
class CourseOutlineSection:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    duration_minutes: int = 30
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    practical_activities: List[str] = field(default_factory=list)
    order: int = 0

@dataclass
class CourseOutline:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    target_audience: str = ""
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    total_duration_hours: float = 4.0
    sections: List[CourseOutlineSection] = field(default_factory=list)
    overall_objectives: List[LearningObjective] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
