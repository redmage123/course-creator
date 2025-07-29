"""
Exercise Generation Service Implementation
Single Responsibility: Implement exercise generation business logic
Dependency Inversion: Depends on repository and AI service abstractions
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from ...domain.entities.course_content import Exercise, ExerciseType, DifficultyLevel
from ...domain.interfaces.content_generation_service import IExerciseGenerationService
from ...domain.interfaces.content_repository import IExerciseRepository, ISyllabusRepository
from ...domain.interfaces.ai_service import IAIService, ContentGenerationType, IPromptTemplateService

class ExerciseGenerationService(IExerciseGenerationService):
    """
    Exercise generation service implementation with business logic
    """
    
    def __init__(self, 
                 exercise_repository: IExerciseRepository,
                 syllabus_repository: ISyllabusRepository,
                 ai_service: IAIService,
                 prompt_service: IPromptTemplateService):
        self._exercise_repository = exercise_repository
        self._syllabus_repository = syllabus_repository
        self._ai_service = ai_service
        self._prompt_service = prompt_service
    
    async def generate_exercise(self, course_id: str, topic: str, difficulty: str, 
                               exercise_type: str = "coding", 
                               context: Dict[str, Any] = None) -> Exercise:
        """Generate an exercise for a course topic using AI"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not topic or len(topic.strip()) == 0:
            raise ValueError("Topic is required")
        
        # Validate difficulty
        try:
            difficulty_enum = DifficultyLevel(difficulty.lower())
        except ValueError:
            raise ValueError(f"Invalid difficulty level: {difficulty}")
        
        # Validate exercise type
        try:
            exercise_type_enum = ExerciseType(exercise_type.lower())
        except ValueError:
            raise ValueError(f"Invalid exercise type: {exercise_type}")
        
        # Get course context
        syllabus = await self._syllabus_repository.get_by_course_id(course_id)
        course_context = self._extract_course_context(syllabus) if syllabus else {}
        
        # Prepare generation context
        generation_context = {
            'course_id': course_id,
            'topic': topic,
            'difficulty': difficulty,
            'exercise_type': exercise_type,
            'context': context or {},
            'course_context': course_context
        }
        
        # Get appropriate template
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.EXERCISE, exercise_type
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, generation_context)
        
        # Generate structured exercise content
        exercise_schema = self._get_exercise_schema(exercise_type)
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.EXERCISE,
            prompt,
            exercise_schema,
            generation_context
        )
        
        # Create exercise entity
        exercise = Exercise(
            course_id=course_id,
            title=generated_content.get('title', f"{topic} Exercise"),
            description=generated_content.get('description', ''),
            topic=topic,
            difficulty=difficulty_enum,
            exercise_type=exercise_type_enum,
            instructions=generated_content.get('instructions', ''),
            starter_code=generated_content.get('starter_code', ''),
            solution_code=generated_content.get('solution_code', ''),
            test_cases=generated_content.get('test_cases', []),
            estimated_time_minutes=generated_content.get('estimated_time_minutes', 30),
            learning_objectives=generated_content.get('learning_objectives', []),
            prerequisites=generated_content.get('prerequisites', [])
        )
        
        # Add type-specific metadata
        self._add_type_specific_metadata(exercise, generated_content, exercise_type)
        
        # Save exercise
        return await self._exercise_repository.create(exercise)
    
    async def generate_exercise_series(self, course_id: str, topic: str, 
                                      difficulty_progression: List[str],
                                      exercise_types: List[str] = None,
                                      context: Dict[str, Any] = None) -> List[Exercise]:
        """Generate a series of progressive exercises for a topic"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not topic:
            raise ValueError("Topic is required")
        
        if not difficulty_progression:
            raise ValueError("Difficulty progression is required")
        
        # Default exercise types if not provided
        if not exercise_types:
            exercise_types = ["coding"] * len(difficulty_progression)
        
        # Ensure exercise types match difficulty progression
        if len(exercise_types) != len(difficulty_progression):
            raise ValueError("Exercise types must match difficulty progression length")
        
        exercises = []
        cumulative_context = context or {}
        
        for i, (difficulty, exercise_type) in enumerate(zip(difficulty_progression, exercise_types)):
            # Add progression context
            progression_context = {
                **cumulative_context,
                'exercise_number': i + 1,
                'total_exercises': len(difficulty_progression),
                'previous_exercises': [ex.title for ex in exercises],
                'is_final_exercise': (i == len(difficulty_progression) - 1)
            }
            
            exercise = await self.generate_exercise(
                course_id=course_id,
                topic=topic,
                difficulty=difficulty,
                exercise_type=exercise_type,
                context=progression_context
            )
            
            exercises.append(exercise)
            
            # Update cumulative context with completed exercise
            cumulative_context['completed_concepts'] = cumulative_context.get('completed_concepts', [])
            cumulative_context['completed_concepts'].extend(exercise.learning_objectives)
        
        return exercises
    
    async def generate_adaptive_exercise(self, course_id: str, student_progress: Dict[str, Any],
                                        learning_goals: List[str],
                                        context: Dict[str, Any] = None) -> Exercise:
        """Generate an exercise adapted to student's current level and progress"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not isinstance(student_progress, dict):
            raise ValueError("Student progress must be a dictionary")
        
        # Analyze student performance to determine exercise parameters
        exercise_params = self._analyze_student_performance_for_exercise(student_progress, learning_goals)
        
        # Prepare adaptive context
        adaptive_context = {
            'student_progress': student_progress,
            'learning_goals': learning_goals,
            'recommended_difficulty': exercise_params['difficulty'],
            'recommended_type': exercise_params['exercise_type'],
            'focus_areas': exercise_params['focus_areas'],
            'avoid_concepts': exercise_params['concepts_to_avoid'],
            'context': context or {}
        }
        
        # Generate personalized exercise
        return await self.generate_exercise(
            course_id=course_id,
            topic=exercise_params['topic'],
            difficulty=exercise_params['difficulty'],
            exercise_type=exercise_params['exercise_type'],
            context=adaptive_context
        )
    
    async def validate_exercise_solution(self, exercise_id: str, 
                                       student_solution: str,
                                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate student's exercise solution"""
        if not exercise_id:
            raise ValueError("Exercise ID is required")
        
        if not student_solution:
            raise ValueError("Student solution is required")
        
        # Get exercise
        exercise = await self._exercise_repository.get_by_id(exercise_id)
        if not exercise:
            raise ValueError(f"Exercise with ID {exercise_id} not found")
        
        # Prepare validation context
        validation_context = {
            'exercise': {
                'title': exercise.title,
                'instructions': exercise.instructions,
                'test_cases': exercise.test_cases,
                'expected_solution': exercise.solution_code
            },
            'student_solution': student_solution,
            'context': context or {}
        }
        
        # Get validation template
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.EXERCISE, "solution_validation"
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, validation_context)
        
        # Validate solution using AI
        validation_schema = self._get_solution_validation_schema()
        validation_result = await self._ai_service.generate_structured_content(
            ContentGenerationType.EXERCISE,
            prompt,
            validation_schema,
            validation_context
        )
        
        return validation_result
    
    # Helper methods
    def _extract_course_context(self, syllabus) -> Dict[str, Any]:
        """Extract relevant context from syllabus"""
        if not syllabus:
            return {}
        
        return {
            'learning_objectives': syllabus.learning_objectives,
            'topics': syllabus.topics,
            'difficulty_level': syllabus.difficulty_level.value,
            'category': syllabus.category,
            'prerequisites': syllabus.prerequisites
        }
    
    def _add_type_specific_metadata(self, exercise: Exercise, generated_content: Dict[str, Any], 
                                   exercise_type: str) -> None:
        """Add type-specific metadata to exercise"""
        if exercise_type == "coding":
            exercise.metadata.update({
                'programming_language': generated_content.get('programming_language', 'python'),
                'libraries_required': generated_content.get('libraries_required', []),
                'complexity_factors': generated_content.get('complexity_factors', [])
            })
        elif exercise_type == "theory":
            exercise.metadata.update({
                'key_concepts': generated_content.get('key_concepts', []),
                'reference_materials': generated_content.get('reference_materials', []),
                'discussion_points': generated_content.get('discussion_points', [])
            })
        elif exercise_type == "practical":
            exercise.metadata.update({
                'tools_required': generated_content.get('tools_required', []),
                'deliverables': generated_content.get('deliverables', []),
                'evaluation_criteria': generated_content.get('evaluation_criteria', [])
            })
    
    def _analyze_student_performance_for_exercise(self, student_progress: Dict[str, Any], 
                                                 learning_goals: List[str]) -> Dict[str, Any]:
        """Analyze student performance to determine optimal exercise parameters"""
        # Extract performance metrics
        completed_exercises = student_progress.get('completed_exercises', 0)
        success_rate = student_progress.get('success_rate', 0.5)
        avg_completion_time = student_progress.get('avg_completion_time_minutes', 30)
        struggling_concepts = student_progress.get('struggling_concepts', [])
        mastered_concepts = student_progress.get('mastered_concepts', [])
        
        # Determine difficulty
        if success_rate >= 0.8 and completed_exercises >= 5:
            difficulty = 'advanced'
            exercise_type = 'practical'
        elif success_rate >= 0.6 and completed_exercises >= 2:
            difficulty = 'intermediate'
            exercise_type = 'coding'
        else:
            difficulty = 'beginner'
            exercise_type = 'theory'
        
        # Determine focus areas
        focus_areas = []
        if struggling_concepts:
            focus_areas.extend(struggling_concepts[:2])  # Focus on top 2 struggling areas
        
        # Add learning goals that aren't mastered yet
        for goal in learning_goals:
            if goal not in mastered_concepts:
                focus_areas.append(goal)
        
        # Determine topic from focus areas or learning goals
        topic = focus_areas[0] if focus_areas else (learning_goals[0] if learning_goals else 'fundamentals')
        
        return {
            'difficulty': difficulty,
            'exercise_type': exercise_type,
            'topic': topic,
            'focus_areas': focus_areas,
            'concepts_to_avoid': mastered_concepts[-3:] if len(mastered_concepts) > 3 else [],  # Avoid recently mastered
            'estimated_time': min(avg_completion_time * 1.2, 60)  # Slightly longer than average, max 60 min
        }
    
    def _get_exercise_schema(self, exercise_type: str) -> Dict[str, Any]:
        """Get schema for exercise generation based on type"""
        base_schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Exercise title"
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of the exercise"
                },
                "instructions": {
                    "type": "string",
                    "description": "Detailed instructions for completing the exercise"
                },
                "estimated_time_minutes": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 180,
                    "description": "Estimated time to complete the exercise"
                },
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Learning objectives covered by this exercise"
                },
                "prerequisites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Prerequisites for this exercise"
                }
            },
            "required": ["title", "description", "instructions"]
        }
        
        # Add type-specific properties
        if exercise_type == "coding":
            base_schema["properties"].update({
                "starter_code": {
                    "type": "string",
                    "description": "Starting code template"
                },
                "solution_code": {
                    "type": "string",
                    "description": "Complete solution code"
                },
                "test_cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string"},
                            "expected_output": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "programming_language": {
                    "type": "string",
                    "description": "Programming language for the exercise"
                },
                "libraries_required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required libraries or imports"
                }
            })
        elif exercise_type == "theory":
            base_schema["properties"].update({
                "key_concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key theoretical concepts covered"
                },
                "discussion_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Points for discussion or reflection"
                },
                "reference_materials": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recommended reading or references"
                }
            })
        elif exercise_type == "practical":
            base_schema["properties"].update({
                "tools_required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tools or software required"
                },
                "deliverables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Expected deliverables from the exercise"
                },
                "evaluation_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Criteria for evaluating the exercise"
                }
            })
        
        return base_schema
    
    def _get_solution_validation_schema(self) -> Dict[str, Any]:
        """Get schema for solution validation"""
        return {
            "type": "object",
            "properties": {
                "is_correct": {
                    "type": "boolean",
                    "description": "Whether the solution is correct"
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Score out of 100"
                },
                "feedback": {
                    "type": "string",
                    "description": "Detailed feedback on the solution"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Strengths of the solution"
                },
                "areas_for_improvement": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas where the solution can be improved"
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions for improvement"
                },
                "test_results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test_case": {"type": "string"},
                            "passed": {"type": "boolean"},
                            "expected": {"type": "string"},
                            "actual": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["is_correct", "score", "feedback"]
        }