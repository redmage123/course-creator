"""
Content repository for Content Management Service.

This module provides repository implementations for all content types
including syllabus, slides, exercises, quizzes, and labs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import json

from repositories.base_repository import BaseRepository
from models.content import (
    SyllabusContent, SyllabusResponse, SlidesCollection, SlideResponse,
    Quiz, QuizResponse, Exercise, ExerciseResponse, LabEnvironment,
    LabEnvironmentResponse, CourseInfo, LearningObjective, CourseModule,
    SlideContent, QuizQuestion, ExerciseStep
)
from models.common import ContentType


class SyllabusRepository(BaseRepository[SyllabusContent]):
    """Repository for syllabus content"""
    
    @property
    def table_name(self) -> str:
        return "syllabi"
    
    def _row_to_model(self, row: asyncpg.Record) -> SyllabusContent:
        """Convert database row to SyllabusContent model"""
        data = dict(row)
        
        # Deserialize JSON fields
        json_fields = ['learning_objectives', 'modules', 'assessment_methods', 
                      'grading_scheme', 'policies', 'schedule', 'textbooks', 'tags']
        data = self._deserialize_json_fields(data, json_fields)
        
        # Convert nested objects
        if data.get('course_info'):
            data['course_info'] = CourseInfo(**json.loads(data['course_info']))
        
        if data.get('learning_objectives'):
            data['learning_objectives'] = [
                LearningObjective(**obj) for obj in data['learning_objectives']
            ]
        
        if data.get('modules'):
            data['modules'] = [
                CourseModule(**module) for module in data['modules']
            ]
        
        return SyllabusContent(**data)
    
    def _model_to_dict(self, model: SyllabusContent) -> Dict[str, Any]:
        """Convert SyllabusContent model to dictionary"""
        data = model.dict()
        
        # Serialize JSON fields
        json_fields = ['learning_objectives', 'modules', 'assessment_methods',
                      'grading_scheme', 'policies', 'schedule', 'textbooks', 'tags']
        data = self._serialize_json_fields(data, json_fields)
        
        # Serialize course_info separately
        if 'course_info' in data:
            data['course_info'] = json.dumps(data['course_info'])
        
        return data
    
    async def find_by_course_id(self, course_id: str) -> List[SyllabusContent]:
        """Find syllabi by course ID"""
        return await self.find_by_field('course_id', course_id)
    
    async def search_by_title(self, title: str) -> List[SyllabusContent]:
        """Search syllabi by title"""
        return await self.search(title, ['title', 'description'])


class SlideRepository(BaseRepository[SlideContent]):
    """Repository for slide content"""
    
    @property
    def table_name(self) -> str:
        return "slides"
    
    def _row_to_model(self, row: asyncpg.Record) -> SlideContent:
        """Convert database row to SlideContent model"""
        data = dict(row)
        
        # Deserialize JSON fields
        json_fields = ['animations', 'tags']
        data = self._deserialize_json_fields(data, json_fields)
        
        return SlideContent(**data)
    
    def _model_to_dict(self, model: SlideContent) -> Dict[str, Any]:
        """Convert SlideContent model to dictionary"""
        data = model.dict()
        
        # Serialize JSON fields
        json_fields = ['animations', 'tags']
        data = self._serialize_json_fields(data, json_fields)
        
        return data
    
    async def find_by_course_id(self, course_id: str) -> List[SlideContent]:
        """Find slides by course ID"""
        return await self.find_by_field('course_id', course_id)
    
    async def find_by_slide_collection(self, collection_id: str) -> List[SlideContent]:
        """Find slides by collection ID"""
        return await self.find_by_field('collection_id', collection_id)
    
    async def get_ordered_slides(self, course_id: str) -> List[SlideContent]:
        """Get slides ordered by slide number"""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE course_id = $1
            ORDER BY slide_number ASC
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, course_id)
            return [self._row_to_model(row) for row in rows]


class QuizRepository(BaseRepository[Quiz]):
    """Repository for quiz content"""
    
    @property
    def table_name(self) -> str:
        return "quizzes"
    
    def _row_to_model(self, row: asyncpg.Record) -> Quiz:
        """Convert database row to Quiz model"""
        data = dict(row)
        
        # Deserialize JSON fields
        json_fields = ['questions', 'tags']
        data = self._deserialize_json_fields(data, json_fields)
        
        # Convert questions to QuizQuestion objects
        if data.get('questions'):
            data['questions'] = [
                QuizQuestion(**question) for question in data['questions']
            ]
        
        return Quiz(**data)
    
    def _model_to_dict(self, model: Quiz) -> Dict[str, Any]:
        """Convert Quiz model to dictionary"""
        data = model.dict()
        
        # Serialize JSON fields
        json_fields = ['questions', 'tags']
        data = self._serialize_json_fields(data, json_fields)
        
        return data
    
    async def find_by_course_id(self, course_id: str) -> List[Quiz]:
        """Find quizzes by course ID"""
        return await self.find_by_field('course_id', course_id)
    
    async def find_by_difficulty(self, difficulty: str) -> List[Quiz]:
        """Find quizzes by difficulty level"""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE questions::text ILIKE $1
            ORDER BY created_at DESC
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, f'%"difficulty": "{difficulty}"%')
            return [self._row_to_model(row) for row in rows]


class ExerciseRepository(BaseRepository[Exercise]):
    """Repository for exercise content"""
    
    @property
    def table_name(self) -> str:
        return "exercises"
    
    def _row_to_model(self, row: asyncpg.Record) -> Exercise:
        """Convert database row to Exercise model"""
        data = dict(row)
        
        # Deserialize JSON fields
        json_fields = ['learning_objectives', 'prerequisites', 'steps', 
                      'grading_rubric', 'resources', 'tags']
        data = self._deserialize_json_fields(data, json_fields)
        
        # Convert steps to ExerciseStep objects
        if data.get('steps'):
            data['steps'] = [
                ExerciseStep(**step) for step in data['steps']
            ]
        
        return Exercise(**data)
    
    def _model_to_dict(self, model: Exercise) -> Dict[str, Any]:
        """Convert Exercise model to dictionary"""
        data = model.dict()
        
        # Serialize JSON fields
        json_fields = ['learning_objectives', 'prerequisites', 'steps',
                      'grading_rubric', 'resources', 'tags']
        data = self._serialize_json_fields(data, json_fields)
        
        return data
    
    async def find_by_course_id(self, course_id: str) -> List[Exercise]:
        """Find exercises by course ID"""
        return await self.find_by_field('course_id', course_id)
    
    async def find_by_type(self, exercise_type: str) -> List[Exercise]:
        """Find exercises by type"""
        return await self.find_by_field('exercise_type', exercise_type)
    
    async def find_by_difficulty(self, difficulty: str) -> List[Exercise]:
        """Find exercises by difficulty level"""
        return await self.find_by_field('difficulty', difficulty)


class LabEnvironmentRepository(BaseRepository[LabEnvironment]):
    """Repository for lab environment content"""
    
    @property
    def table_name(self) -> str:
        return "lab_environments"
    
    def _row_to_model(self, row: asyncpg.Record) -> LabEnvironment:
        """Convert database row to LabEnvironment model"""
        data = dict(row)
        
        # Deserialize JSON fields
        json_fields = ['tools', 'datasets', 'setup_scripts', 
                      'resource_requirements', 'tags']
        data = self._deserialize_json_fields(data, json_fields)
        
        return LabEnvironment(**data)
    
    def _model_to_dict(self, model: LabEnvironment) -> Dict[str, Any]:
        """Convert LabEnvironment model to dictionary"""
        data = model.dict()
        
        # Serialize JSON fields
        json_fields = ['tools', 'datasets', 'setup_scripts',
                      'resource_requirements', 'tags']
        data = self._serialize_json_fields(data, json_fields)
        
        return data
    
    async def find_by_course_id(self, course_id: str) -> List[LabEnvironment]:
        """Find lab environments by course ID"""
        return await self.find_by_field('course_id', course_id)
    
    async def find_by_environment_type(self, environment_type: str) -> List[LabEnvironment]:
        """Find lab environments by type"""
        return await self.find_by_field('environment_type', environment_type)
    
    async def find_by_base_image(self, base_image: str) -> List[LabEnvironment]:
        """Find lab environments by base image"""
        return await self.find_by_field('base_image', base_image)


class ContentRepository:
    """Unified content repository providing access to all content types"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.syllabus_repo = SyllabusRepository(db_pool)
        self.slide_repo = SlideRepository(db_pool)
        self.quiz_repo = QuizRepository(db_pool)
        self.exercise_repo = ExerciseRepository(db_pool)
        self.lab_repo = LabEnvironmentRepository(db_pool)
    
    def get_repository(self, content_type: ContentType):
        """Get repository for specific content type"""
        repository_map = {
            ContentType.SYLLABUS: self.syllabus_repo,
            ContentType.SLIDES: self.slide_repo,
            ContentType.QUIZZES: self.quiz_repo,
            ContentType.EXERCISES: self.exercise_repo,
            ContentType.LABS: self.lab_repo
        }
        
        return repository_map.get(content_type)
    
    async def get_course_content(self, course_id: str) -> Dict[str, Any]:
        """Get all content for a course"""
        result = {
            'syllabus': await self.syllabus_repo.find_by_course_id(course_id),
            'slides': await self.slide_repo.find_by_course_id(course_id),
            'quizzes': await self.quiz_repo.find_by_course_id(course_id),
            'exercises': await self.exercise_repo.find_by_course_id(course_id),
            'labs': await self.lab_repo.find_by_course_id(course_id)
        }
        
        return result
    
    async def search_all_content(self, query: str, content_types: Optional[List[ContentType]] = None) -> Dict[str, Any]:
        """Search across all content types"""
        result = {}
        
        search_types = content_types or [
            ContentType.SYLLABUS, ContentType.SLIDES, ContentType.QUIZZES,
            ContentType.EXERCISES, ContentType.LABS
        ]
        
        for content_type in search_types:
            repo = self.get_repository(content_type)
            if repo:
                if content_type == ContentType.SYLLABUS:
                    result['syllabus'] = await repo.search(query, ['title', 'description'])
                elif content_type == ContentType.SLIDES:
                    result['slides'] = await repo.search(query, ['title', 'content'])
                elif content_type == ContentType.QUIZZES:
                    result['quizzes'] = await repo.search(query, ['title', 'description'])
                elif content_type == ContentType.EXERCISES:
                    result['exercises'] = await repo.search(query, ['title', 'description'])
                elif content_type == ContentType.LABS:
                    result['labs'] = await repo.search(query, ['title', 'description'])
        
        return result
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get statistics about content"""
        stats = {}
        
        # Count content by type
        stats['syllabi_count'] = await self.syllabus_repo.count()
        stats['slides_count'] = await self.slide_repo.count()
        stats['quizzes_count'] = await self.quiz_repo.count()
        stats['exercises_count'] = await self.exercise_repo.count()
        stats['labs_count'] = await self.lab_repo.count()
        
        # Total content count
        stats['total_content'] = sum([
            stats['syllabi_count'],
            stats['slides_count'],
            stats['quizzes_count'],
            stats['exercises_count'],
            stats['labs_count']
        ])
        
        return stats
    
    async def get_recent_content(self, limit: int = 10) -> List[Any]:
        """Get recently created content across all types"""
        # This would need a more sophisticated query to combine all content types
        # For now, return empty list
        return []
    
    async def delete_course_content(self, course_id: str) -> Dict[str, int]:
        """Delete all content for a course"""
        deleted_counts = {}
        
        # Get all content for the course
        course_content = await self.get_course_content(course_id)
        
        # Delete each content type
        for content_type, items in course_content.items():
            if items:
                repo = self.get_repository(ContentType(content_type))
                if repo:
                    ids = [item.id for item in items]
                    deleted_counts[content_type] = await repo.bulk_delete(ids)
        
        return deleted_counts