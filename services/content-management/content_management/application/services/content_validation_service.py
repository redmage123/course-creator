"""
Content Validation Application Service
Single Responsibility: Content validation and completeness checking
"""
from typing import Dict, Any
from content_management.domain.interfaces.content_service import IContentValidationService
from content_management.domain.entities.base_content import BaseContent
from content_management.domain.entities.syllabus import Syllabus
from content_management.domain.entities.slide import Slide
from content_management.domain.entities.quiz import Quiz
from content_management.domain.entities.exercise import Exercise
from content_management.domain.entities.lab_environment import LabEnvironment


class ContentValidationService(IContentValidationService):
    """
    Service for validating content entities and checking permissions
    """
    
    def __init__(self):
        pass
    
    async def validate_content(self, content: BaseContent) -> Dict[str, Any]:
        """Validate content entity"""
        try:
            errors = []
            warnings = []
            
            # Basic validation (all content types)
            if not content.title:
                errors.append("Title is required")
            elif len(content.title) < 3:
                warnings.append("Title is very short")
            
            if not content.course_id:
                errors.append("Course ID is required")
            
            if not content.created_by:
                errors.append("Created by is required")
            
            # Content type specific validation
            if isinstance(content, Syllabus):
                syllabus_validation = self._validate_syllabus(content)
                errors.extend(syllabus_validation.get("errors", []))
                warnings.extend(syllabus_validation.get("warnings", []))
                
            elif isinstance(content, Slide):
                slide_validation = self._validate_slide(content)
                errors.extend(slide_validation.get("errors", []))
                warnings.extend(slide_validation.get("warnings", []))
                
            elif isinstance(content, Quiz):
                quiz_validation = self._validate_quiz(content)
                errors.extend(quiz_validation.get("errors", []))
                warnings.extend(quiz_validation.get("warnings", []))
                
            elif isinstance(content, Exercise):
                exercise_validation = self._validate_exercise(content)
                errors.extend(exercise_validation.get("errors", []))
                warnings.extend(exercise_validation.get("warnings", []))
                
            elif isinstance(content, LabEnvironment):
                lab_validation = self._validate_lab_environment(content)
                errors.extend(lab_validation.get("errors", []))
                warnings.extend(lab_validation.get("warnings", []))
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_score": self._calculate_validation_score(errors, warnings)
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "validation_score": 0
            }
    
    async def check_content_completeness(self, content: BaseContent) -> Dict[str, Any]:
        """Check if content is complete for publishing"""
        try:
            missing_items = []
            completeness_score = 0
            total_items = 0
            
            # Base completeness checks
            total_items += 4
            if content.title:
                completeness_score += 1
            else:
                missing_items.append("Title")
            
            if content.description:
                completeness_score += 1
            else:
                missing_items.append("Description")
            
            if content.tags:
                completeness_score += 1
            else:
                missing_items.append("Tags")
            
            if content.metadata:
                completeness_score += 1
            else:
                missing_items.append("Metadata")
            
            # Content type specific completeness
            if isinstance(content, Syllabus):
                syllabus_completeness = self._check_syllabus_completeness(content)
                missing_items.extend(syllabus_completeness.get("missing_items", []))
                completeness_score += syllabus_completeness.get("score", 0)
                total_items += syllabus_completeness.get("total_items", 0)
                
            elif isinstance(content, Slide):
                slide_completeness = self._check_slide_completeness(content)
                missing_items.extend(slide_completeness.get("missing_items", []))
                completeness_score += slide_completeness.get("score", 0)
                total_items += slide_completeness.get("total_items", 0)
                
            elif isinstance(content, Quiz):
                quiz_completeness = self._check_quiz_completeness(content)
                missing_items.extend(quiz_completeness.get("missing_items", []))
                completeness_score += quiz_completeness.get("score", 0)
                total_items += quiz_completeness.get("total_items", 0)
                
            elif isinstance(content, Exercise):
                exercise_completeness = self._check_exercise_completeness(content)
                missing_items.extend(exercise_completeness.get("missing_items", []))
                completeness_score += exercise_completeness.get("score", 0)
                total_items += exercise_completeness.get("total_items", 0)
                
            elif isinstance(content, LabEnvironment):
                lab_completeness = self._check_lab_completeness(content)
                missing_items.extend(lab_completeness.get("missing_items", []))
                completeness_score += lab_completeness.get("score", 0)
                total_items += lab_completeness.get("total_items", 0)
            
            completeness_percentage = (completeness_score / total_items * 100) if total_items > 0 else 0
            
            return {
                "is_complete": len(missing_items) == 0,
                "missing_items": missing_items,
                "completeness_score": completeness_score,
                "total_items": total_items,
                "completeness_percentage": completeness_percentage,
                "ready_for_publish": completeness_percentage >= 80  # 80% threshold for publishing
            }
            
        except Exception as e:
            return {
                "is_complete": False,
                "missing_items": [f"Completeness check error: {str(e)}"],
                "completeness_score": 0,
                "total_items": 1,
                "completeness_percentage": 0,
                "ready_for_publish": False
            }
    
    async def validate_content_permissions(self, user_id: str, content_id: str, action: str) -> bool:
        """Validate user permissions for content action"""
        try:
            # Simplified permission check - in a real system, this would:
            # 1. Check user roles and permissions
            # 2. Check content ownership
            # 3. Check organizational permissions
            # 4. Check action-specific permissions
            
            # For now, always return True (implement actual logic based on your auth system)
            return True
            
        except Exception:
            return False
    
    def _validate_syllabus(self, syllabus: Syllabus) -> Dict[str, Any]:
        """Validate syllabus-specific content"""
        errors = []
        warnings = []
        
        if not syllabus.course_info:
            errors.append("Course info is required")
        else:
            required_fields = ["course_code", "course_name", "credits"]
            for field in required_fields:
                if field not in syllabus.course_info:
                    errors.append(f"Course info must include {field}")
        
        if not syllabus.learning_objectives:
            errors.append("Learning objectives are required")
        elif len(syllabus.learning_objectives) < 2:
            warnings.append("Consider adding more learning objectives")
        
        if not syllabus.modules:
            errors.append("At least one module is required")
        elif len(syllabus.modules) < 4:
            warnings.append("Consider adding more modules for a complete course")
        
        if not syllabus.assessment_methods:
            warnings.append("Assessment methods should be specified")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_slide(self, slide: Slide) -> Dict[str, Any]:
        """Validate slide-specific content"""
        errors = []
        warnings = []
        
        if slide.slide_number < 1:
            errors.append("Slide number must be positive")
        
        if not slide.has_content():
            warnings.append("Slide has no content")
        
        if slide.duration_minutes and slide.duration_minutes > 30:
            warnings.append("Slide duration seems very long")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_quiz(self, quiz: Quiz) -> Dict[str, Any]:
        """Validate quiz-specific content"""
        errors = []
        warnings = []
        
        if not quiz.questions:
            errors.append("Quiz must have at least one question")
        elif len(quiz.questions) < 3:
            warnings.append("Consider adding more questions")
        
        if not (0 <= quiz.passing_score <= 100):
            errors.append("Passing score must be between 0 and 100")
        
        if quiz.settings.time_limit_minutes and quiz.settings.time_limit_minutes < len(quiz.questions):
            warnings.append("Time limit seems too short for the number of questions")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_exercise(self, exercise: Exercise) -> Dict[str, Any]:
        """Validate exercise-specific content"""
        errors = []
        warnings = []
        
        if not exercise.learning_objectives:
            warnings.append("Learning objectives should be specified")
        
        if not exercise.steps:
            warnings.append("Exercise steps should be provided")
        
        if exercise.estimated_time_minutes and exercise.estimated_time_minutes > 240:  # 4 hours
            warnings.append("Exercise duration seems very long")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_lab_environment(self, lab: LabEnvironment) -> Dict[str, Any]:
        """Validate lab environment-specific content"""
        errors = []
        warnings = []
        
        if not lab.base_image:
            errors.append("Base image is required")
        
        if not lab.access_instructions:
            warnings.append("Access instructions should be provided")
        
        if not lab.tools:
            warnings.append("Consider specifying required tools")
        
        if lab.resource_requirements.memory_gb > 8:
            warnings.append("High memory requirement may limit accessibility")
        
        return {"errors": errors, "warnings": warnings}
    
    def _check_syllabus_completeness(self, syllabus: Syllabus) -> Dict[str, Any]:
        """Check syllabus completeness"""
        missing_items = []
        score = 0
        total_items = 6
        
        if syllabus.learning_objectives:
            score += 1
        else:
            missing_items.append("Learning objectives")
        
        if syllabus.modules and len(syllabus.modules) >= 4:
            score += 1
        else:
            missing_items.append("Sufficient modules (minimum 4)")
        
        if syllabus.assessment_methods:
            score += 1
        else:
            missing_items.append("Assessment methods")
        
        if syllabus.grading_scheme:
            score += 1
        else:
            missing_items.append("Grading scheme")
        
        if syllabus.policies:
            score += 1
        else:
            missing_items.append("Course policies")
        
        if syllabus.textbooks:
            score += 1
        else:
            missing_items.append("Textbooks/References")
        
        return {"missing_items": missing_items, "score": score, "total_items": total_items}
    
    def _check_slide_completeness(self, slide: Slide) -> Dict[str, Any]:
        """Check slide completeness"""
        missing_items = []
        score = 0
        total_items = 3
        
        if slide.has_content():
            score += 1
        else:
            missing_items.append("Slide content")
        
        if slide.speaker_notes:
            score += 1
        else:
            missing_items.append("Speaker notes")
        
        if slide.duration_minutes:
            score += 1
        else:
            missing_items.append("Duration estimate")
        
        return {"missing_items": missing_items, "score": score, "total_items": total_items}
    
    def _check_quiz_completeness(self, quiz: Quiz) -> Dict[str, Any]:
        """Check quiz completeness"""
        missing_items = []
        score = 0
        total_items = 3
        
        if quiz.questions and len(quiz.questions) >= 5:
            score += 1
        else:
            missing_items.append("Sufficient questions (minimum 5)")
        
        if quiz.settings.time_limit_minutes:
            score += 1
        else:
            missing_items.append("Time limit")
        
        if quiz.description:
            score += 1
        else:
            missing_items.append("Quiz instructions")
        
        return {"missing_items": missing_items, "score": score, "total_items": total_items}
    
    def _check_exercise_completeness(self, exercise: Exercise) -> Dict[str, Any]:
        """Check exercise completeness"""
        missing_items = []
        score = 0
        total_items = 4
        
        if exercise.learning_objectives:
            score += 1
        else:
            missing_items.append("Learning objectives")
        
        if exercise.steps:
            score += 1
        else:
            missing_items.append("Exercise steps")
        
        if exercise.estimated_time_minutes:
            score += 1
        else:
            missing_items.append("Time estimate")
        
        if exercise.has_grading_rubric():
            score += 1
        else:
            missing_items.append("Grading rubric")
        
        return {"missing_items": missing_items, "score": score, "total_items": total_items}
    
    def _check_lab_completeness(self, lab: LabEnvironment) -> Dict[str, Any]:
        """Check lab environment completeness"""
        missing_items = []
        score = 0
        total_items = 4
        
        if lab.access_instructions:
            score += 1
        else:
            missing_items.append("Access instructions")
        
        if lab.tools:
            score += 1
        else:
            missing_items.append("Required tools")
        
        if lab.estimated_setup_time_minutes:
            score += 1
        else:
            missing_items.append("Setup time estimate")
        
        if lab.has_setup_scripts():
            score += 1
        else:
            missing_items.append("Setup scripts")
        
        return {"missing_items": missing_items, "score": score, "total_items": total_items}
    
    def _calculate_validation_score(self, errors: list, warnings: list) -> int:
        """Calculate validation score (0-100)"""
        if errors:
            return 0
        elif warnings:
            return max(50, 100 - len(warnings) * 10)
        else:
            return 100