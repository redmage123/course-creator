"""
PostgreSQL Content Repository Implementations
Single Responsibility: Content data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interfaces
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import json

from ...domain.interfaces.content_repository import (
    ISyllabusRepository, ISlideRepository, IQuizRepository,
    IExerciseRepository, ILabEnvironmentRepository, IContentSearchRepository
)
from ...domain.entities.base_content import ContentType, ContentStatus
from ...domain.entities.syllabus import Syllabus, SyllabusModule, GradingScheme
from ...domain.entities.slide import Slide, SlideContent, SlideAnimation, SlideType, SlideLayout
from ...domain.entities.quiz import Quiz, QuizQuestion, QuizSettings, QuestionType, DifficultyLevel
from ...domain.entities.exercise import Exercise, ExerciseStep, GradingRubric, ExerciseType
from ...domain.entities.lab_environment import LabEnvironment, LabTool, Dataset, SetupScript, ResourceRequirement, EnvironmentType


class PostgreSQLSyllabusRepository(ISyllabusRepository):
    """PostgreSQL implementation of syllabus repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, syllabus: Syllabus) -> Syllabus:
        """Create a new syllabus"""
        query = """
        INSERT INTO content_syllabi (
            id, title, description, course_id, created_by, tags, status,
            course_info, learning_objectives, modules, assessment_methods,
            grading_scheme, policies, schedule, textbooks, created_at, updated_at, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
        ) RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                syllabus.id, syllabus.title, syllabus.description, syllabus.course_id,
                syllabus.created_by, json.dumps(syllabus.tags), syllabus.status.value,
                json.dumps(syllabus.course_info), json.dumps(syllabus.learning_objectives),
                json.dumps([module.to_dict() for module in syllabus.modules]),
                json.dumps(syllabus.assessment_methods),
                json.dumps(syllabus.grading_scheme.to_dict() if syllabus.grading_scheme else None),
                json.dumps(syllabus.policies), json.dumps(syllabus.schedule),
                json.dumps(syllabus.textbooks), syllabus.created_at, syllabus.updated_at,
                json.dumps(syllabus.metadata)
            )
            
            return self._row_to_syllabus(row)
    
    async def get_by_id(self, syllabus_id: str) -> Optional[Syllabus]:
        """Get syllabus by ID"""
        query = "SELECT * FROM content_syllabi WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, syllabus_id)
            return self._row_to_syllabus(row) if row else None
    
    async def update(self, syllabus_id: str, updates: Dict[str, Any]) -> Optional[Syllabus]:
        """Update syllabus"""
        # Build dynamic update query
        set_clauses = []
        values = []
        param_idx = 1
        
        # Handle special fields that need JSON serialization
        json_fields = {
            'tags', 'course_info', 'learning_objectives', 'modules',
            'assessment_methods', 'grading_scheme', 'policies', 'schedule',
            'textbooks', 'metadata'
        }
        
        for field, value in updates.items():
            if field in json_fields:
                if field == 'modules' and isinstance(value, list):
                    # Convert SyllabusModule objects to dicts
                    value = [module.to_dict() if hasattr(module, 'to_dict') else module for module in value]
                elif field == 'grading_scheme' and hasattr(value, 'to_dict'):
                    value = value.to_dict()
                
                set_clauses.append(f"{field} = ${param_idx}")
                values.append(json.dumps(value))
            else:
                set_clauses.append(f"{field} = ${param_idx}")
                values.append(value)
            param_idx += 1
        
        # Always update the updated_at field
        set_clauses.append(f"updated_at = ${param_idx}")
        values.append(datetime.utcnow())
        param_idx += 1
        
        # Add WHERE clause
        values.append(syllabus_id)
        
        query = f"""
        UPDATE content_syllabi SET {', '.join(set_clauses)}
        WHERE id = ${param_idx}
        RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, *values)
            return self._row_to_syllabus(row) if row else None
    
    async def delete(self, syllabus_id: str) -> bool:
        """Delete syllabus"""
        query = "DELETE FROM content_syllabi WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, syllabus_id)
            return result.split()[-1] == "1"
    
    async def get_by_course_id(self, course_id: str) -> List[Syllabus]:
        """Get all syllabi for a course"""
        query = """
        SELECT * FROM content_syllabi 
        WHERE course_id = $1 
        ORDER BY created_at DESC
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, course_id)
            return [self._row_to_syllabus(row) for row in rows]
    
    async def get_published_by_course_id(self, course_id: str) -> List[Syllabus]:
        """Get published syllabi for a course"""
        query = """
        SELECT * FROM content_syllabi 
        WHERE course_id = $1 AND status = 'published'
        ORDER BY created_at DESC
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, course_id)
            return [self._row_to_syllabus(row) for row in rows]
    
    async def search_by_title(self, title: str, limit: int = 50) -> List[Syllabus]:
        """Search syllabi by title"""
        query = """
        SELECT * FROM content_syllabi 
        WHERE title ILIKE $1 
        ORDER BY created_at DESC 
        LIMIT $2
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, f"%{title}%", limit)
            return [self._row_to_syllabus(row) for row in rows]
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Syllabus]:
        """List all syllabi with pagination"""
        query = """
        SELECT * FROM content_syllabi 
        ORDER BY created_at DESC 
        LIMIT $1 OFFSET $2
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, limit, offset)
            return [self._row_to_syllabus(row) for row in rows]
    
    async def count_by_course_id(self, course_id: str) -> int:
        """Count syllabi for a course"""
        query = "SELECT COUNT(*) FROM content_syllabi WHERE course_id = $1"
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, course_id)
    
    async def delete_by_course_id(self, course_id: str) -> int:
        """Delete all syllabi for a course"""
        query = "DELETE FROM content_syllabi WHERE course_id = $1"
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, course_id)
            return int(result.split()[-1])
    
    def _row_to_syllabus(self, row) -> Optional[Syllabus]:
        """Convert database row to Syllabus entity"""
        if not row:
            return None
        
        try:
            # Parse JSON fields
            course_info = json.loads(row['course_info']) if row['course_info'] else {}
            learning_objectives = json.loads(row['learning_objectives']) if row['learning_objectives'] else []
            modules_data = json.loads(row['modules']) if row['modules'] else []
            assessment_methods = json.loads(row['assessment_methods']) if row['assessment_methods'] else []
            grading_scheme_data = json.loads(row['grading_scheme']) if row['grading_scheme'] else None
            policies = json.loads(row['policies']) if row['policies'] else {}
            schedule = json.loads(row['schedule']) if row['schedule'] else {}
            textbooks = json.loads(row['textbooks']) if row['textbooks'] else []
            tags = json.loads(row['tags']) if row['tags'] else []
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            
            # Convert modules data to SyllabusModule objects
            modules = []
            for module_data in modules_data:
                module = SyllabusModule(
                    title=module_data['title'],
                    description=module_data['description'],
                    week_number=module_data['week_number'],
                    topics=module_data['topics'],
                    learning_outcomes=module_data.get('learning_outcomes', []),
                    duration_hours=module_data.get('duration_hours')
                )
                modules.append(module)
            
            # Convert grading scheme
            grading_scheme = None
            if grading_scheme_data:
                grading_scheme = GradingScheme(grading_scheme_data)
            
            syllabus = Syllabus(
                title=row['title'],
                course_id=row['course_id'],
                created_by=row['created_by'],
                id=row['id'],
                description=row['description'],
                course_info=course_info,
                learning_objectives=learning_objectives,
                modules=modules,
                assessment_methods=assessment_methods,
                grading_scheme=grading_scheme,
                policies=policies,
                schedule=schedule,
                textbooks=textbooks,
                tags=tags,
                status=ContentStatus(row['status']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=metadata
            )
            
            return syllabus
            
        except Exception as e:
            # Log error in production
            print(f"Error converting row to syllabus: {e}")
            return None


# Mock implementations for other repositories (would be fully implemented in a complete system)
class PostgreSQLSlideRepository(ISlideRepository):
    """Mock PostgreSQL implementation of slide repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, slide: Slide) -> Slide:
        return slide
    
    async def get_by_id(self, slide_id: str) -> Optional[Slide]:
        return None
    
    async def update(self, slide_id: str, updates: Dict[str, Any]) -> Optional[Slide]:
        return None
    
    async def delete(self, slide_id: str) -> bool:
        return True
    
    async def get_by_course_id(self, course_id: str) -> List[Slide]:
        return []
    
    async def get_ordered_slides(self, course_id: str) -> List[Slide]:
        return []
    
    async def get_by_slide_number(self, course_id: str, slide_number: int) -> Optional[Slide]:
        return None
    
    async def reorder_slides(self, course_id: str, slide_orders: Dict[str, int]) -> bool:
        return True
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Slide]:
        return []
    
    async def count_by_course_id(self, course_id: str) -> int:
        return 0
    
    async def delete_by_course_id(self, course_id: str) -> int:
        return 0


class PostgreSQLQuizRepository(IQuizRepository):
    """Mock PostgreSQL implementation of quiz repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, quiz: Quiz) -> Quiz:
        return quiz
    
    async def get_by_id(self, quiz_id: str) -> Optional[Quiz]:
        return None
    
    async def update(self, quiz_id: str, updates: Dict[str, Any]) -> Optional[Quiz]:
        return None
    
    async def delete(self, quiz_id: str) -> bool:
        return True
    
    async def get_by_course_id(self, course_id: str) -> List[Quiz]:
        return []
    
    async def get_published_by_course_id(self, course_id: str) -> List[Quiz]:
        return []
    
    async def search_by_difficulty(self, difficulty: str, limit: int = 50) -> List[Quiz]:
        return []
    
    async def get_timed_quizzes(self, course_id: str) -> List[Quiz]:
        return []
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Quiz]:
        return []
    
    async def count_by_course_id(self, course_id: str) -> int:
        return 0
    
    async def delete_by_course_id(self, course_id: str) -> int:
        return 0


class PostgreSQLExerciseRepository(IExerciseRepository):
    """Mock PostgreSQL implementation of exercise repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, exercise: Exercise) -> Exercise:
        return exercise
    
    async def get_by_id(self, exercise_id: str) -> Optional[Exercise]:
        return None
    
    async def update(self, exercise_id: str, updates: Dict[str, Any]) -> Optional[Exercise]:
        return None
    
    async def delete(self, exercise_id: str) -> bool:
        return True
    
    async def get_by_course_id(self, course_id: str) -> List[Exercise]:
        return []
    
    async def get_by_difficulty(self, difficulty: str, course_id: Optional[str] = None) -> List[Exercise]:
        return []
    
    async def get_by_type(self, exercise_type: str, course_id: Optional[str] = None) -> List[Exercise]:
        return []
    
    async def search_by_objective(self, objective: str, limit: int = 50) -> List[Exercise]:
        return []
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Exercise]:
        return []
    
    async def count_by_course_id(self, course_id: str) -> int:
        return 0
    
    async def delete_by_course_id(self, course_id: str) -> int:
        return 0


class PostgreSQLLabEnvironmentRepository(ILabEnvironmentRepository):
    """Mock PostgreSQL implementation of lab environment repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, lab_environment: LabEnvironment) -> LabEnvironment:
        return lab_environment
    
    async def get_by_id(self, lab_id: str) -> Optional[LabEnvironment]:
        return None
    
    async def update(self, lab_id: str, updates: Dict[str, Any]) -> Optional[LabEnvironment]:
        return None
    
    async def delete(self, lab_id: str) -> bool:
        return True
    
    async def get_by_course_id(self, course_id: str) -> List[LabEnvironment]:
        return []
    
    async def get_by_environment_type(self, env_type: str, course_id: Optional[str] = None) -> List[LabEnvironment]:
        return []
    
    async def get_by_base_image(self, base_image: str) -> List[LabEnvironment]:
        return []
    
    async def get_gpu_required_environments(self, course_id: Optional[str] = None) -> List[LabEnvironment]:
        return []
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[LabEnvironment]:
        return []
    
    async def count_by_course_id(self, course_id: str) -> int:
        return 0
    
    async def delete_by_course_id(self, course_id: str) -> int:
        return 0


class PostgreSQLContentSearchRepository(IContentSearchRepository):
    """Mock PostgreSQL implementation of content search repository"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def search_all_content(
        self, 
        query: str, 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, List[Any]]:
        """Search across all content types"""
        return {
            "syllabi": [],
            "slides": [],
            "quizzes": [],
            "exercises": [],
            "lab_environments": []
        }
    
    async def search_by_tags(
        self, 
        tags: List[str], 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """Search content by tags"""
        return {
            "syllabi": [],
            "slides": [],
            "quizzes": [],
            "exercises": [],
            "lab_environments": []
        }
    
    async def get_content_statistics(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """Get content statistics"""
        return {
            "total_content": 0,
            "syllabi_count": 0,
            "slides_count": 0,
            "quizzes_count": 0,
            "exercises_count": 0,
            "lab_environments_count": 0
        }
    
    async def get_recent_content(
        self, 
        content_types: Optional[List[ContentType]] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Any]:
        """Get recently created/updated content"""
        return []