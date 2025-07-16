"""
Content service for Content Management Service.

This module provides business logic for content management operations
including CRUD operations, validation, and content processing.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import asyncio
import uuid
from fastapi import HTTPException

from models.common import ContentType, ProcessingStatus, create_error_response, create_success_response
from models.content import (
    SyllabusContent, SyllabusCreate, SyllabusUpdate, SyllabusResponse,
    SlideContent, SlideCreate, SlideUpdate, SlideResponse,
    Quiz, QuizCreate, QuizUpdate, QuizResponse,
    Exercise, ExerciseCreate, ExerciseUpdate, ExerciseResponse,
    LabEnvironment, LabEnvironmentCreate, LabEnvironmentUpdate, LabEnvironmentResponse,
    ContentGenerationRequest, CustomGenerationRequest, AIGenerationRequest
)
from repositories.content_repository import ContentRepository


class ContentService:
    """Service for managing content operations"""
    
    def __init__(self, content_repository: ContentRepository):
        self.content_repository = content_repository
    
    # Syllabus operations
    async def create_syllabus(self, syllabus_data: SyllabusCreate, created_by: str) -> SyllabusResponse:
        """Create a new syllabus"""
        try:
            # Create syllabus content model
            syllabus_content = SyllabusContent(
                id=str(uuid.uuid4()),
                title=syllabus_data.title,
                description=syllabus_data.description,
                course_info=syllabus_data.course_info,
                learning_objectives=syllabus_data.learning_objectives,
                modules=syllabus_data.modules,
                assessment_methods=syllabus_data.assessment_methods,
                grading_scheme=syllabus_data.grading_scheme,
                policies=syllabus_data.policies,
                schedule=syllabus_data.schedule,
                textbooks=syllabus_data.textbooks,
                course_id=syllabus_data.course_id,
                tags=syllabus_data.tags,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to repository
            created_syllabus = await self.content_repository.syllabus_repo.create(syllabus_content)
            
            # Return response
            return SyllabusResponse(
                id=created_syllabus.id,
                title=created_syllabus.title,
                description=created_syllabus.description,
                course_info=created_syllabus.course_info,
                learning_objectives=created_syllabus.learning_objectives,
                modules=created_syllabus.modules,
                assessment_methods=created_syllabus.assessment_methods,
                grading_scheme=created_syllabus.grading_scheme,
                policies=created_syllabus.policies,
                schedule=created_syllabus.schedule,
                textbooks=created_syllabus.textbooks,
                course_id=created_syllabus.course_id,
                tags=created_syllabus.tags,
                created_at=created_syllabus.created_at,
                updated_at=created_syllabus.updated_at,
                created_by=created_syllabus.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create syllabus: {str(e)}")
    
    async def get_syllabus(self, syllabus_id: str) -> Optional[SyllabusResponse]:
        """Get syllabus by ID"""
        try:
            syllabus = await self.content_repository.syllabus_repo.get_by_id(syllabus_id)
            if not syllabus:
                return None
            
            return SyllabusResponse(
                id=syllabus.id,
                title=syllabus.title,
                description=syllabus.description,
                course_info=syllabus.course_info,
                learning_objectives=syllabus.learning_objectives,
                modules=syllabus.modules,
                assessment_methods=syllabus.assessment_methods,
                grading_scheme=syllabus.grading_scheme,
                policies=syllabus.policies,
                schedule=syllabus.schedule,
                textbooks=syllabus.textbooks,
                course_id=syllabus.course_id,
                tags=syllabus.tags,
                created_at=syllabus.created_at,
                updated_at=syllabus.updated_at,
                created_by=syllabus.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get syllabus: {str(e)}")
    
    async def update_syllabus(self, syllabus_id: str, updates: SyllabusUpdate) -> Optional[SyllabusResponse]:
        """Update syllabus"""
        try:
            # Get current syllabus
            current_syllabus = await self.content_repository.syllabus_repo.get_by_id(syllabus_id)
            if not current_syllabus:
                return None
            
            # Prepare update data
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            # Update syllabus
            updated_syllabus = await self.content_repository.syllabus_repo.update(syllabus_id, update_data)
            if not updated_syllabus:
                return None
            
            return SyllabusResponse(
                id=updated_syllabus.id,
                title=updated_syllabus.title,
                description=updated_syllabus.description,
                course_info=updated_syllabus.course_info,
                learning_objectives=updated_syllabus.learning_objectives,
                modules=updated_syllabus.modules,
                assessment_methods=updated_syllabus.assessment_methods,
                grading_scheme=updated_syllabus.grading_scheme,
                policies=updated_syllabus.policies,
                schedule=updated_syllabus.schedule,
                textbooks=updated_syllabus.textbooks,
                course_id=updated_syllabus.course_id,
                tags=updated_syllabus.tags,
                created_at=updated_syllabus.created_at,
                updated_at=updated_syllabus.updated_at,
                created_by=updated_syllabus.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update syllabus: {str(e)}")
    
    async def delete_syllabus(self, syllabus_id: str) -> bool:
        """Delete syllabus"""
        try:
            return await self.content_repository.syllabus_repo.delete(syllabus_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete syllabus: {str(e)}")
    
    async def list_syllabi(self, course_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[SyllabusResponse]:
        """List syllabi with optional filtering"""
        try:
            if course_id:
                syllabi = await self.content_repository.syllabus_repo.find_by_course_id(course_id)
            else:
                syllabi = await self.content_repository.syllabus_repo.list_all(limit, offset)
            
            return [
                SyllabusResponse(
                    id=syllabus.id,
                    title=syllabus.title,
                    description=syllabus.description,
                    course_info=syllabus.course_info,
                    learning_objectives=syllabus.learning_objectives,
                    modules=syllabus.modules,
                    assessment_methods=syllabus.assessment_methods,
                    grading_scheme=syllabus.grading_scheme,
                    policies=syllabus.policies,
                    schedule=syllabus.schedule,
                    textbooks=syllabus.textbooks,
                    course_id=syllabus.course_id,
                    tags=syllabus.tags,
                    created_at=syllabus.created_at,
                    updated_at=syllabus.updated_at,
                    created_by=syllabus.created_by
                )
                for syllabus in syllabi
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list syllabi: {str(e)}")
    
    # Slide operations
    async def create_slide(self, slide_data: SlideCreate, created_by: str) -> SlideResponse:
        """Create a new slide"""
        try:
            slide_content = SlideContent(
                id=str(uuid.uuid4()),
                title=slide_data.title,
                slide_number=slide_data.slide_number,
                slide_type=slide_data.slide_type,
                content=slide_data.content,
                speaker_notes=slide_data.speaker_notes,
                layout=slide_data.layout,
                background=slide_data.background,
                animations=slide_data.animations,
                duration_minutes=slide_data.duration_minutes,
                course_id=slide_data.course_id,
                tags=slide_data.tags,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_slide = await self.content_repository.slide_repo.create(slide_content)
            
            return SlideResponse(
                id=created_slide.id,
                title=created_slide.title,
                slide_number=created_slide.slide_number,
                slide_type=created_slide.slide_type,
                content=created_slide.content,
                speaker_notes=created_slide.speaker_notes,
                layout=created_slide.layout,
                background=created_slide.background,
                animations=created_slide.animations,
                duration_minutes=created_slide.duration_minutes,
                course_id=created_slide.course_id,
                tags=created_slide.tags,
                created_at=created_slide.created_at,
                updated_at=created_slide.updated_at,
                created_by=created_slide.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create slide: {str(e)}")
    
    async def get_slide(self, slide_id: str) -> Optional[SlideResponse]:
        """Get slide by ID"""
        try:
            slide = await self.content_repository.slide_repo.get_by_id(slide_id)
            if not slide:
                return None
            
            return SlideResponse(
                id=slide.id,
                title=slide.title,
                slide_number=slide.slide_number,
                slide_type=slide.slide_type,
                content=slide.content,
                speaker_notes=slide.speaker_notes,
                layout=slide.layout,
                background=slide.background,
                animations=slide.animations,
                duration_minutes=slide.duration_minutes,
                course_id=slide.course_id,
                tags=slide.tags,
                created_at=slide.created_at,
                updated_at=slide.updated_at,
                created_by=slide.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get slide: {str(e)}")
    
    async def update_slide(self, slide_id: str, updates: SlideUpdate) -> Optional[SlideResponse]:
        """Update slide"""
        try:
            current_slide = await self.content_repository.slide_repo.get_by_id(slide_id)
            if not current_slide:
                return None
            
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            updated_slide = await self.content_repository.slide_repo.update(slide_id, update_data)
            if not updated_slide:
                return None
            
            return SlideResponse(
                id=updated_slide.id,
                title=updated_slide.title,
                slide_number=updated_slide.slide_number,
                slide_type=updated_slide.slide_type,
                content=updated_slide.content,
                speaker_notes=updated_slide.speaker_notes,
                layout=updated_slide.layout,
                background=updated_slide.background,
                animations=updated_slide.animations,
                duration_minutes=updated_slide.duration_minutes,
                course_id=updated_slide.course_id,
                tags=updated_slide.tags,
                created_at=updated_slide.created_at,
                updated_at=updated_slide.updated_at,
                created_by=updated_slide.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update slide: {str(e)}")
    
    async def delete_slide(self, slide_id: str) -> bool:
        """Delete slide"""
        try:
            return await self.content_repository.slide_repo.delete(slide_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete slide: {str(e)}")
    
    async def list_slides(self, course_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[SlideResponse]:
        """List slides with optional filtering"""
        try:
            if course_id:
                slides = await self.content_repository.slide_repo.get_ordered_slides(course_id)
            else:
                slides = await self.content_repository.slide_repo.list_all(limit, offset)
            
            return [
                SlideResponse(
                    id=slide.id,
                    title=slide.title,
                    slide_number=slide.slide_number,
                    slide_type=slide.slide_type,
                    content=slide.content,
                    speaker_notes=slide.speaker_notes,
                    layout=slide.layout,
                    background=slide.background,
                    animations=slide.animations,
                    duration_minutes=slide.duration_minutes,
                    course_id=slide.course_id,
                    tags=slide.tags,
                    created_at=slide.created_at,
                    updated_at=slide.updated_at,
                    created_by=slide.created_by
                )
                for slide in slides
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list slides: {str(e)}")
    
    # Quiz operations
    async def create_quiz(self, quiz_data: QuizCreate, created_by: str) -> QuizResponse:
        """Create a new quiz"""
        try:
            quiz = Quiz(
                id=str(uuid.uuid4()),
                title=quiz_data.title,
                description=quiz_data.description,
                questions=quiz_data.questions,
                time_limit_minutes=quiz_data.time_limit_minutes,
                attempts_allowed=quiz_data.attempts_allowed,
                shuffle_questions=quiz_data.shuffle_questions,
                shuffle_options=quiz_data.shuffle_options,
                show_correct_answers=quiz_data.show_correct_answers,
                passing_score=quiz_data.passing_score,
                course_id=quiz_data.course_id,
                tags=quiz_data.tags,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_quiz = await self.content_repository.quiz_repo.create(quiz)
            
            return QuizResponse(
                id=created_quiz.id,
                title=created_quiz.title,
                description=created_quiz.description,
                questions=created_quiz.questions,
                time_limit_minutes=created_quiz.time_limit_minutes,
                attempts_allowed=created_quiz.attempts_allowed,
                shuffle_questions=created_quiz.shuffle_questions,
                shuffle_options=created_quiz.shuffle_options,
                show_correct_answers=created_quiz.show_correct_answers,
                passing_score=created_quiz.passing_score,
                course_id=created_quiz.course_id,
                tags=created_quiz.tags,
                created_at=created_quiz.created_at,
                updated_at=created_quiz.updated_at,
                created_by=created_quiz.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")
    
    async def get_quiz(self, quiz_id: str) -> Optional[QuizResponse]:
        """Get quiz by ID"""
        try:
            quiz = await self.content_repository.quiz_repo.get_by_id(quiz_id)
            if not quiz:
                return None
            
            return QuizResponse(
                id=quiz.id,
                title=quiz.title,
                description=quiz.description,
                questions=quiz.questions,
                time_limit_minutes=quiz.time_limit_minutes,
                attempts_allowed=quiz.attempts_allowed,
                shuffle_questions=quiz.shuffle_questions,
                shuffle_options=quiz.shuffle_options,
                show_correct_answers=quiz.show_correct_answers,
                passing_score=quiz.passing_score,
                course_id=quiz.course_id,
                tags=quiz.tags,
                created_at=quiz.created_at,
                updated_at=quiz.updated_at,
                created_by=quiz.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get quiz: {str(e)}")
    
    async def update_quiz(self, quiz_id: str, updates: QuizUpdate) -> Optional[QuizResponse]:
        """Update quiz"""
        try:
            current_quiz = await self.content_repository.quiz_repo.get_by_id(quiz_id)
            if not current_quiz:
                return None
            
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            updated_quiz = await self.content_repository.quiz_repo.update(quiz_id, update_data)
            if not updated_quiz:
                return None
            
            return QuizResponse(
                id=updated_quiz.id,
                title=updated_quiz.title,
                description=updated_quiz.description,
                questions=updated_quiz.questions,
                time_limit_minutes=updated_quiz.time_limit_minutes,
                attempts_allowed=updated_quiz.attempts_allowed,
                shuffle_questions=updated_quiz.shuffle_questions,
                shuffle_options=updated_quiz.shuffle_options,
                show_correct_answers=updated_quiz.show_correct_answers,
                passing_score=updated_quiz.passing_score,
                course_id=updated_quiz.course_id,
                tags=updated_quiz.tags,
                created_at=updated_quiz.created_at,
                updated_at=updated_quiz.updated_at,
                created_by=updated_quiz.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update quiz: {str(e)}")
    
    async def delete_quiz(self, quiz_id: str) -> bool:
        """Delete quiz"""
        try:
            return await self.content_repository.quiz_repo.delete(quiz_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete quiz: {str(e)}")
    
    async def list_quizzes(self, course_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[QuizResponse]:
        """List quizzes with optional filtering"""
        try:
            if course_id:
                quizzes = await self.content_repository.quiz_repo.find_by_course_id(course_id)
            else:
                quizzes = await self.content_repository.quiz_repo.list_all(limit, offset)
            
            return [
                QuizResponse(
                    id=quiz.id,
                    title=quiz.title,
                    description=quiz.description,
                    questions=quiz.questions,
                    time_limit_minutes=quiz.time_limit_minutes,
                    attempts_allowed=quiz.attempts_allowed,
                    shuffle_questions=quiz.shuffle_questions,
                    shuffle_options=quiz.shuffle_options,
                    show_correct_answers=quiz.show_correct_answers,
                    passing_score=quiz.passing_score,
                    course_id=quiz.course_id,
                    tags=quiz.tags,
                    created_at=quiz.created_at,
                    updated_at=quiz.updated_at,
                    created_by=quiz.created_by
                )
                for quiz in quizzes
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list quizzes: {str(e)}")
    
    # Exercise operations
    async def create_exercise(self, exercise_data: ExerciseCreate, created_by: str) -> ExerciseResponse:
        """Create a new exercise"""
        try:
            exercise = Exercise(
                id=str(uuid.uuid4()),
                title=exercise_data.title,
                description=exercise_data.description,
                exercise_type=exercise_data.exercise_type,
                difficulty=exercise_data.difficulty,
                estimated_time_minutes=exercise_data.estimated_time_minutes,
                learning_objectives=exercise_data.learning_objectives,
                prerequisites=exercise_data.prerequisites,
                steps=exercise_data.steps,
                solution=exercise_data.solution,
                grading_rubric=exercise_data.grading_rubric,
                resources=exercise_data.resources,
                course_id=exercise_data.course_id,
                tags=exercise_data.tags,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_exercise = await self.content_repository.exercise_repo.create(exercise)
            
            return ExerciseResponse(
                id=created_exercise.id,
                title=created_exercise.title,
                description=created_exercise.description,
                exercise_type=created_exercise.exercise_type,
                difficulty=created_exercise.difficulty,
                estimated_time_minutes=created_exercise.estimated_time_minutes,
                learning_objectives=created_exercise.learning_objectives,
                prerequisites=created_exercise.prerequisites,
                steps=created_exercise.steps,
                solution=created_exercise.solution,
                grading_rubric=created_exercise.grading_rubric,
                resources=created_exercise.resources,
                course_id=created_exercise.course_id,
                tags=created_exercise.tags,
                created_at=created_exercise.created_at,
                updated_at=created_exercise.updated_at,
                created_by=created_exercise.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create exercise: {str(e)}")
    
    async def get_exercise(self, exercise_id: str) -> Optional[ExerciseResponse]:
        """Get exercise by ID"""
        try:
            exercise = await self.content_repository.exercise_repo.get_by_id(exercise_id)
            if not exercise:
                return None
            
            return ExerciseResponse(
                id=exercise.id,
                title=exercise.title,
                description=exercise.description,
                exercise_type=exercise.exercise_type,
                difficulty=exercise.difficulty,
                estimated_time_minutes=exercise.estimated_time_minutes,
                learning_objectives=exercise.learning_objectives,
                prerequisites=exercise.prerequisites,
                steps=exercise.steps,
                solution=exercise.solution,
                grading_rubric=exercise.grading_rubric,
                resources=exercise.resources,
                course_id=exercise.course_id,
                tags=exercise.tags,
                created_at=exercise.created_at,
                updated_at=exercise.updated_at,
                created_by=exercise.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get exercise: {str(e)}")
    
    async def update_exercise(self, exercise_id: str, updates: ExerciseUpdate) -> Optional[ExerciseResponse]:
        """Update exercise"""
        try:
            current_exercise = await self.content_repository.exercise_repo.get_by_id(exercise_id)
            if not current_exercise:
                return None
            
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            updated_exercise = await self.content_repository.exercise_repo.update(exercise_id, update_data)
            if not updated_exercise:
                return None
            
            return ExerciseResponse(
                id=updated_exercise.id,
                title=updated_exercise.title,
                description=updated_exercise.description,
                exercise_type=updated_exercise.exercise_type,
                difficulty=updated_exercise.difficulty,
                estimated_time_minutes=updated_exercise.estimated_time_minutes,
                learning_objectives=updated_exercise.learning_objectives,
                prerequisites=updated_exercise.prerequisites,
                steps=updated_exercise.steps,
                solution=updated_exercise.solution,
                grading_rubric=updated_exercise.grading_rubric,
                resources=updated_exercise.resources,
                course_id=updated_exercise.course_id,
                tags=updated_exercise.tags,
                created_at=updated_exercise.created_at,
                updated_at=updated_exercise.updated_at,
                created_by=updated_exercise.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update exercise: {str(e)}")
    
    async def delete_exercise(self, exercise_id: str) -> bool:
        """Delete exercise"""
        try:
            return await self.content_repository.exercise_repo.delete(exercise_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete exercise: {str(e)}")
    
    async def list_exercises(self, course_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[ExerciseResponse]:
        """List exercises with optional filtering"""
        try:
            if course_id:
                exercises = await self.content_repository.exercise_repo.find_by_course_id(course_id)
            else:
                exercises = await self.content_repository.exercise_repo.list_all(limit, offset)
            
            return [
                ExerciseResponse(
                    id=exercise.id,
                    title=exercise.title,
                    description=exercise.description,
                    exercise_type=exercise.exercise_type,
                    difficulty=exercise.difficulty,
                    estimated_time_minutes=exercise.estimated_time_minutes,
                    learning_objectives=exercise.learning_objectives,
                    prerequisites=exercise.prerequisites,
                    steps=exercise.steps,
                    solution=exercise.solution,
                    grading_rubric=exercise.grading_rubric,
                    resources=exercise.resources,
                    course_id=exercise.course_id,
                    tags=exercise.tags,
                    created_at=exercise.created_at,
                    updated_at=exercise.updated_at,
                    created_by=exercise.created_by
                )
                for exercise in exercises
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list exercises: {str(e)}")
    
    # Lab Environment operations
    async def create_lab_environment(self, lab_data: LabEnvironmentCreate, created_by: str) -> LabEnvironmentResponse:
        """Create a new lab environment"""
        try:
            lab_environment = LabEnvironment(
                id=str(uuid.uuid4()),
                title=lab_data.title,
                description=lab_data.description,
                environment_type=lab_data.environment_type,
                base_image=lab_data.base_image,
                tools=lab_data.tools,
                datasets=lab_data.datasets,
                setup_scripts=lab_data.setup_scripts,
                access_instructions=lab_data.access_instructions,
                estimated_setup_time_minutes=lab_data.estimated_setup_time_minutes,
                resource_requirements=lab_data.resource_requirements,
                course_id=lab_data.course_id,
                tags=lab_data.tags,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_lab = await self.content_repository.lab_repo.create(lab_environment)
            
            return LabEnvironmentResponse(
                id=created_lab.id,
                title=created_lab.title,
                description=created_lab.description,
                environment_type=created_lab.environment_type,
                base_image=created_lab.base_image,
                tools=created_lab.tools,
                datasets=created_lab.datasets,
                setup_scripts=created_lab.setup_scripts,
                access_instructions=created_lab.access_instructions,
                estimated_setup_time_minutes=created_lab.estimated_setup_time_minutes,
                resource_requirements=created_lab.resource_requirements,
                course_id=created_lab.course_id,
                tags=created_lab.tags,
                created_at=created_lab.created_at,
                updated_at=created_lab.updated_at,
                created_by=created_lab.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create lab environment: {str(e)}")
    
    async def get_lab_environment(self, lab_id: str) -> Optional[LabEnvironmentResponse]:
        """Get lab environment by ID"""
        try:
            lab = await self.content_repository.lab_repo.get_by_id(lab_id)
            if not lab:
                return None
            
            return LabEnvironmentResponse(
                id=lab.id,
                title=lab.title,
                description=lab.description,
                environment_type=lab.environment_type,
                base_image=lab.base_image,
                tools=lab.tools,
                datasets=lab.datasets,
                setup_scripts=lab.setup_scripts,
                access_instructions=lab.access_instructions,
                estimated_setup_time_minutes=lab.estimated_setup_time_minutes,
                resource_requirements=lab.resource_requirements,
                course_id=lab.course_id,
                tags=lab.tags,
                created_at=lab.created_at,
                updated_at=lab.updated_at,
                created_by=lab.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get lab environment: {str(e)}")
    
    async def update_lab_environment(self, lab_id: str, updates: LabEnvironmentUpdate) -> Optional[LabEnvironmentResponse]:
        """Update lab environment"""
        try:
            current_lab = await self.content_repository.lab_repo.get_by_id(lab_id)
            if not current_lab:
                return None
            
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            updated_lab = await self.content_repository.lab_repo.update(lab_id, update_data)
            if not updated_lab:
                return None
            
            return LabEnvironmentResponse(
                id=updated_lab.id,
                title=updated_lab.title,
                description=updated_lab.description,
                environment_type=updated_lab.environment_type,
                base_image=updated_lab.base_image,
                tools=updated_lab.tools,
                datasets=updated_lab.datasets,
                setup_scripts=updated_lab.setup_scripts,
                access_instructions=updated_lab.access_instructions,
                estimated_setup_time_minutes=updated_lab.estimated_setup_time_minutes,
                resource_requirements=updated_lab.resource_requirements,
                course_id=updated_lab.course_id,
                tags=updated_lab.tags,
                created_at=updated_lab.created_at,
                updated_at=updated_lab.updated_at,
                created_by=updated_lab.created_by
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update lab environment: {str(e)}")
    
    async def delete_lab_environment(self, lab_id: str) -> bool:
        """Delete lab environment"""
        try:
            return await self.content_repository.lab_repo.delete(lab_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete lab environment: {str(e)}")
    
    async def list_lab_environments(self, course_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[LabEnvironmentResponse]:
        """List lab environments with optional filtering"""
        try:
            if course_id:
                labs = await self.content_repository.lab_repo.find_by_course_id(course_id)
            else:
                labs = await self.content_repository.lab_repo.list_all(limit, offset)
            
            return [
                LabEnvironmentResponse(
                    id=lab.id,
                    title=lab.title,
                    description=lab.description,
                    environment_type=lab.environment_type,
                    base_image=lab.base_image,
                    tools=lab.tools,
                    datasets=lab.datasets,
                    setup_scripts=lab.setup_scripts,
                    access_instructions=lab.access_instructions,
                    estimated_setup_time_minutes=lab.estimated_setup_time_minutes,
                    resource_requirements=lab.resource_requirements,
                    course_id=lab.course_id,
                    tags=lab.tags,
                    created_at=lab.created_at,
                    updated_at=lab.updated_at,
                    created_by=lab.created_by
                )
                for lab in labs
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list lab environments: {str(e)}")
    
    # Search and statistics
    async def search_content(self, query: str, content_types: Optional[List[ContentType]] = None) -> Dict[str, Any]:
        """Search content across all types"""
        try:
            return await self.content_repository.search_all_content(query, content_types)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search content: {str(e)}")
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get content statistics"""
        try:
            return await self.content_repository.get_content_statistics()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get content statistics: {str(e)}")
    
    async def get_course_content(self, course_id: str) -> Dict[str, Any]:
        """Get all content for a course"""
        try:
            return await self.content_repository.get_course_content(course_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get course content: {str(e)}")
    
    async def delete_course_content(self, course_id: str) -> Dict[str, int]:
        """Delete all content for a course"""
        try:
            return await self.content_repository.delete_course_content(course_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete course content: {str(e)}")
    
    # Validation methods
    def _validate_content_data(self, content_data: Any) -> bool:
        """Validate content data"""
        # Add validation logic here
        return True
    
    def _validate_permissions(self, user_id: str, content_id: str) -> bool:
        """Validate user permissions for content"""
        # Add permission validation logic here
        return True