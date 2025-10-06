"""
Exercise Entity - Domain Layer
Single Responsibility: Exercise-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from content_management.domain.entities.base_content import BaseContent, ContentType


class ExerciseType(Enum):
    """Exercise type enumeration"""
    CODING = "coding"
    THEORETICAL = "theoretical"
    PRACTICAL = "practical"
    RESEARCH = "research"
    PRESENTATION = "presentation"
    GROUP_PROJECT = "group_project"
    CASE_STUDY = "case_study"


class DifficultyLevel(Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExerciseStep:
    """Exercise step value object"""
    
    def __init__(
        self,
        step_number: int,
        title: str,
        description: str,
        estimated_time_minutes: Optional[int] = None,
        resources: Optional[List[str]] = None,
        hints: Optional[List[str]] = None
    ):
        self.step_number = step_number
        self.title = title
        self.description = description
        self.estimated_time_minutes = estimated_time_minutes
        self.resources = resources or []
        self.hints = hints or []
        
        self.validate()
    
    def validate(self) -> None:
        """Validate step"""
        if self.step_number < 1:
            raise ValueError("Step number must be positive")
        if not self.title:
            raise ValueError("Step title is required")
        if not self.description:
            raise ValueError("Step description is required")
        if self.estimated_time_minutes is not None and self.estimated_time_minutes <= 0:
            raise ValueError("Estimated time must be positive")
    
    def add_hint(self, hint: str) -> None:
        """Add hint to step"""
        if hint and hint not in self.hints:
            self.hints.append(hint)
    
    def add_resource(self, resource: str) -> None:
        """Add resource to step"""
        if resource and resource not in self.resources:
            self.resources.append(resource)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "estimated_time_minutes": self.estimated_time_minutes,
            "resources": self.resources,
            "hints": self.hints
        }


class GradingRubric:
    """Grading rubric value object"""
    
    def __init__(self, criteria: Dict[str, Dict[str, Any]]):
        self.criteria = criteria
        self.validate()
    
    def validate(self) -> None:
        """Validate grading rubric"""
        if not self.criteria:
            raise ValueError("Grading rubric must have criteria")
        
        total_weight = 0
        for criterion_name, criterion_data in self.criteria.items():
            if "weight" not in criterion_data:
                raise ValueError(f"Criterion '{criterion_name}' must have weight")
            if "levels" not in criterion_data:
                raise ValueError(f"Criterion '{criterion_name}' must have levels")
            
            weight = criterion_data["weight"]
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise ValueError(f"Weight for '{criterion_name}' must be positive number")
            
            total_weight += weight
        
        # Allow some flexibility in total weight (doesn't have to be exactly 100)
        if total_weight <= 0:
            raise ValueError("Total weight must be positive")
    
    def get_criterion_weight(self, criterion: str) -> float:
        """Get weight for a criterion"""
        return self.criteria.get(criterion, {}).get("weight", 0.0)
    
    def get_total_weight(self) -> float:
        """Get total weight of all criteria"""
        return sum(
            criterion_data.get("weight", 0) 
            for criterion_data in self.criteria.values()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.criteria.copy()


class Exercise(BaseContent):
    """
    Exercise domain entity following SOLID principles
    Single Responsibility: Exercise-specific business logic
    """
    
    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        exercise_type: ExerciseType,
        difficulty: DifficultyLevel,
        id: Optional[str] = None,
        description: Optional[str] = None,
        estimated_time_minutes: Optional[int] = None,
        learning_objectives: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        steps: Optional[List[ExerciseStep]] = None,
        solution: Optional[Dict[str, Any]] = None,
        grading_rubric: Optional[GradingRubric] = None,
        resources: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ):
        # Initialize base content
        super().__init__(
            title=title,
            course_id=course_id,
            created_by=created_by,
            id=id,
            description=description,
            **kwargs
        )
        
        # Exercise-specific attributes
        self.exercise_type = exercise_type
        self.difficulty = difficulty
        self.estimated_time_minutes = estimated_time_minutes
        self.learning_objectives = learning_objectives or []
        self.prerequisites = prerequisites or []
        self.steps = steps or []
        self.solution = solution or {}
        self.grading_rubric = grading_rubric
        self.resources = resources or []
        
        # Additional validation
        self._validate_exercise()
    
    def get_content_type(self) -> ContentType:
        """Get content type"""
        return ContentType.EXERCISE
    
    def _validate_exercise(self) -> None:
        """Validate exercise-specific data"""
        if self.estimated_time_minutes is not None and self.estimated_time_minutes <= 0:
            raise ValueError("Estimated time must be positive")
    
    def add_learning_objective(self, objective: str) -> None:
        """Add learning objective"""
        if objective and objective not in self.learning_objectives:
            self.learning_objectives.append(objective)
            self._mark_updated()
    
    def remove_learning_objective(self, objective: str) -> bool:
        """Remove learning objective"""
        if objective in self.learning_objectives:
            self.learning_objectives.remove(objective)
            self._mark_updated()
            return True
        return False
    
    def add_prerequisite(self, prerequisite: str) -> None:
        """Add prerequisite"""
        if prerequisite and prerequisite not in self.prerequisites:
            self.prerequisites.append(prerequisite)
            self._mark_updated()
    
    def remove_prerequisite(self, prerequisite: str) -> bool:
        """Remove prerequisite"""
        if prerequisite in self.prerequisites:
            self.prerequisites.remove(prerequisite)
            self._mark_updated()
            return True
        return False
    
    def add_step(self, step: ExerciseStep) -> None:
        """Add step to exercise"""
        # Check for duplicate step numbers
        existing_steps = [s.step_number for s in self.steps]
        if step.step_number in existing_steps:
            raise ValueError(f"Step {step.step_number} already exists")
        
        self.steps.append(step)
        # Sort steps by step number
        self.steps.sort(key=lambda x: x.step_number)
        self._mark_updated()
    
    def remove_step(self, step_number: int) -> bool:
        """Remove step by number"""
        for i, step in enumerate(self.steps):
            if step.step_number == step_number:
                del self.steps[i]
                self._mark_updated()
                return True
        return False
    
    def get_step(self, step_number: int) -> Optional[ExerciseStep]:
        """Get step by number"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def update_step(self, step_number: int, updated_step: ExerciseStep) -> bool:
        """Update step"""
        for i, step in enumerate(self.steps):
            if step.step_number == step_number:
                self.steps[i] = updated_step
                self._mark_updated()
                return True
        return False
    
    def set_solution(self, solution_type: str, solution_content: Any) -> None:
        """Set solution content"""
        self.solution[solution_type] = solution_content
        self._mark_updated()
    
    def get_solution(self, solution_type: str) -> Any:
        """Get solution content"""
        return self.solution.get(solution_type)
    
    def has_solution(self) -> bool:
        """Check if exercise has solution"""
        return bool(self.solution)
    
    def set_grading_rubric(self, rubric: GradingRubric) -> None:
        """Set grading rubric"""
        self.grading_rubric = rubric
        self._mark_updated()
    
    def add_resource(self, title: str, url: str, resource_type: str = "link") -> None:
        """Add resource"""
        resource = {
            "title": title,
            "url": url,
            "type": resource_type
        }
        self.resources.append(resource)
        self._mark_updated()
    
    def remove_resource(self, title: str) -> bool:
        """Remove resource by title"""
        for i, resource in enumerate(self.resources):
            if resource.get("title") == title:
                del self.resources[i]
                self._mark_updated()
                return True
        return False
    
    def set_estimated_time(self, minutes: int) -> None:
        """Set estimated completion time"""
        if minutes <= 0:
            raise ValueError("Estimated time must be positive")
        self.estimated_time_minutes = minutes
        self._mark_updated()
    
    def get_total_estimated_time(self) -> int:
        """Get total estimated time including steps"""
        base_time = self.estimated_time_minutes or 0
        steps_time = sum(
            step.estimated_time_minutes or 0 
            for step in self.steps
        )
        return base_time + steps_time
    
    def get_steps_count(self) -> int:
        """Get number of steps"""
        return len(self.steps)
    
    def is_coding_exercise(self) -> bool:
        """Check if this is a coding exercise"""
        return self.exercise_type == ExerciseType.CODING
    
    def is_group_exercise(self) -> bool:
        """Check if this is a group exercise"""
        return self.exercise_type == ExerciseType.GROUP_PROJECT
    
    def has_prerequisites(self) -> bool:
        """Check if exercise has prerequisites"""
        return bool(self.prerequisites)
    
    def has_grading_rubric(self) -> bool:
        """Check if exercise has grading rubric"""
        return self.grading_rubric is not None
    
    def is_complete(self) -> bool:
        """Check if exercise definition is complete"""
        return all([
            self.title,
            self.description,
            self.learning_objectives,
            self.steps,
            self.estimated_time_minutes is not None
        ])
    
    def get_difficulty_level_description(self) -> str:
        """Get human-readable difficulty description"""
        descriptions = {
            DifficultyLevel.BEGINNER: "Suitable for beginners with basic knowledge",
            DifficultyLevel.INTERMEDIATE: "Requires intermediate understanding",
            DifficultyLevel.ADVANCED: "Requires advanced knowledge and skills",
            DifficultyLevel.EXPERT: "Expert-level exercise for experienced practitioners"
        }
        return descriptions.get(self.difficulty, "Unknown difficulty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "exercise_type": self.exercise_type.value,
            "difficulty": self.difficulty.value,
            "difficulty_description": self.get_difficulty_level_description(),
            "estimated_time_minutes": self.estimated_time_minutes,
            "total_estimated_time": self.get_total_estimated_time(),
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "steps": [step.to_dict() for step in self.steps],
            "steps_count": self.get_steps_count(),
            "solution": self.solution,
            "has_solution": self.has_solution(),
            "grading_rubric": self.grading_rubric.to_dict() if self.grading_rubric else None,
            "has_grading_rubric": self.has_grading_rubric(),
            "resources": self.resources,
            "is_coding_exercise": self.is_coding_exercise(),
            "is_group_exercise": self.is_group_exercise(),
            "has_prerequisites": self.has_prerequisites(),
            "is_complete": self.is_complete()
        })
        return base_dict