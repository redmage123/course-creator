"""
Syllabus Entity - Domain Layer
Single Responsibility: Syllabus-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_content import BaseContent, ContentType


class SyllabusModule:
    """Syllabus module value object"""
    
    def __init__(
        self,
        title: str,
        description: str,
        week_number: int,
        topics: List[str],
        learning_outcomes: Optional[List[str]] = None,
        duration_hours: Optional[float] = None
    ):
        self.title = title
        self.description = description
        self.week_number = week_number
        self.topics = topics
        self.learning_outcomes = learning_outcomes or []
        self.duration_hours = duration_hours
        
        self.validate()
    
    def validate(self) -> None:
        """Validate module"""
        if not self.title:
            raise ValueError("Module title is required")
        if not self.description:
            raise ValueError("Module description is required")
        if self.week_number < 1:
            raise ValueError("Week number must be positive")
        if not self.topics:
            raise ValueError("Module must have at least one topic")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "description": self.description,
            "week_number": self.week_number,
            "topics": self.topics,
            "learning_outcomes": self.learning_outcomes,
            "duration_hours": self.duration_hours
        }


class GradingScheme:
    """Grading scheme value object"""
    
    def __init__(self, components: Dict[str, float]):
        self.components = components
        self.validate()
    
    def validate(self) -> None:
        """Validate grading scheme"""
        if not self.components:
            raise ValueError("Grading scheme must have components")
        
        total_weight = sum(self.components.values())
        if abs(total_weight - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Grading components must sum to 100%, got {total_weight}%")
        
        for component, weight in self.components.items():
            if weight < 0 or weight > 100:
                raise ValueError(f"Invalid weight for {component}: {weight}%")
    
    def get_component_weight(self, component: str) -> float:
        """Get weight for a component"""
        return self.components.get(component, 0.0)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return self.components.copy()


class Syllabus(BaseContent):
    """
    Syllabus domain entity following SOLID principles
    Single Responsibility: Syllabus-specific business logic
    """
    
    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        course_info: Dict[str, Any],
        learning_objectives: List[str],
        id: Optional[str] = None,
        description: Optional[str] = None,
        modules: Optional[List[SyllabusModule]] = None,
        assessment_methods: Optional[List[str]] = None,
        grading_scheme: Optional[GradingScheme] = None,
        policies: Optional[Dict[str, str]] = None,
        schedule: Optional[Dict[str, Any]] = None,
        textbooks: Optional[List[Dict[str, str]]] = None,
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
        
        # Syllabus-specific attributes
        self.course_info = course_info
        self.learning_objectives = learning_objectives
        self.modules = modules or []
        self.assessment_methods = assessment_methods or []
        self.grading_scheme = grading_scheme
        self.policies = policies or {}
        self.schedule = schedule or {}
        self.textbooks = textbooks or []
        
        # Additional validation
        self._validate_syllabus()
    
    def get_content_type(self) -> ContentType:
        """Get content type"""
        return ContentType.SYLLABUS
    
    def _validate_syllabus(self) -> None:
        """Validate syllabus-specific data"""
        if not self.course_info:
            raise ValueError("Course info is required")
        if not self.learning_objectives:
            raise ValueError("Learning objectives are required")
        
        # Validate required course info fields
        required_course_fields = ["course_code", "course_name", "credits"]
        for field in required_course_fields:
            if field not in self.course_info:
                raise ValueError(f"Course info must include {field}")
    
    def add_module(self, module: SyllabusModule) -> None:
        """Add module to syllabus"""
        # Check for duplicate week numbers
        existing_weeks = [m.week_number for m in self.modules]
        if module.week_number in existing_weeks:
            raise ValueError(f"Module for week {module.week_number} already exists")
        
        self.modules.append(module)
        self._mark_updated()
    
    def remove_module(self, week_number: int) -> bool:
        """Remove module by week number"""
        for i, module in enumerate(self.modules):
            if module.week_number == week_number:
                del self.modules[i]
                self._mark_updated()
                return True
        return False
    
    def get_module_by_week(self, week_number: int) -> Optional[SyllabusModule]:
        """Get module by week number"""
        for module in self.modules:
            if module.week_number == week_number:
                return module
        return None
    
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
    
    def update_grading_scheme(self, grading_scheme: GradingScheme) -> None:
        """Update grading scheme"""
        self.grading_scheme = grading_scheme
        self._mark_updated()
    
    def add_assessment_method(self, method: str) -> None:
        """Add assessment method"""
        if method and method not in self.assessment_methods:
            self.assessment_methods.append(method)
            self._mark_updated()
    
    def update_policy(self, policy_name: str, policy_text: str) -> None:
        """Update a policy"""
        self.policies[policy_name] = policy_text
        self._mark_updated()
    
    def add_textbook(self, title: str, author: str, isbn: Optional[str] = None, 
                    publisher: Optional[str] = None, edition: Optional[str] = None) -> None:
        """Add textbook"""
        textbook = {
            "title": title,
            "author": author,
            "isbn": isbn,
            "publisher": publisher,
            "edition": edition
        }
        self.textbooks.append(textbook)
        self._mark_updated()
    
    def get_total_course_hours(self) -> float:
        """Calculate total course hours from modules"""
        return sum(
            module.duration_hours for module in self.modules 
            if module.duration_hours is not None
        )
    
    def get_weeks_count(self) -> int:
        """Get number of weeks in syllabus"""
        return len(self.modules)
    
    def is_complete(self) -> bool:
        """Check if syllabus is complete"""
        required_components = [
            self.course_info,
            self.learning_objectives,
            self.modules,
            self.assessment_methods
        ]
        return all(required_components) and len(self.modules) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "course_info": self.course_info,
            "learning_objectives": self.learning_objectives,
            "modules": [module.to_dict() for module in self.modules],
            "assessment_methods": self.assessment_methods,
            "grading_scheme": self.grading_scheme.to_dict() if self.grading_scheme else None,
            "policies": self.policies,
            "schedule": self.schedule,
            "textbooks": self.textbooks,
            "total_hours": self.get_total_course_hours(),
            "weeks_count": self.get_weeks_count(),
            "is_complete": self.is_complete()
        })
        return base_dict