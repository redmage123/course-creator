#!/usr/bin/env python3
"""
Course Generator Service - Fixed Hydra Configuration
"""
import logging
import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
import hydra
from pydantic import BaseModel
from datetime import datetime
import time
import uvicorn
import anthropic
import json
import asyncio
import asyncpg
import httpx
import os
import re
from contextlib import asynccontextmanager

# Import services
from services.exercise_generation_service import ExerciseGenerationService
from services.lab_environment_service import LabEnvironmentService
from services.syllabus_service import SyllabusService
from services.ai_service import AIService

# Models
class CourseTemplate(BaseModel):
    id: str
    name: str
    description: str
    parameters: Dict

class GenerateCourseRequest(BaseModel):
    template_id: str
    parameters: Dict

class Job(BaseModel):
    id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict]

class SlideGenerationRequest(BaseModel):
    course_id: str
    title: str
    description: str
    topic: str

class Slide(BaseModel):
    id: str
    title: str
    content: str
    slide_type: str
    order: int

class LabEnvironment(BaseModel):
    id: Optional[str] = None
    course_id: str
    name: str
    description: str
    environment_type: str
    config: Dict
    exercises: List[Dict]

class ExerciseRequest(BaseModel):
    course_id: str
    topic: str
    difficulty: str = "beginner"

class LabLaunchRequest(BaseModel):
    course_id: str
    student_id: str
    course_title: str
    course_description: str
    course_category: str

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None

class Quiz(BaseModel):
    id: Optional[str] = None
    course_id: str
    title: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    created_at: Optional[datetime] = None

class QuizAttempt(BaseModel):
    id: Optional[str] = None
    student_id: str
    quiz_id: str
    course_id: str
    answers: List[int]
    score: float
    total_questions: int
    completed_at: Optional[datetime] = None

class QuizGenerationRequest(BaseModel):
    course_id: str
    topic: str
    difficulty: str = "beginner"
    question_count: int = 12
    difficulty_level: str
    instructor_context: Dict
    student_tracking: Dict

class ChatRequest(BaseModel):
    course_id: str
    student_id: str
    user_message: str
    context: Dict

class DynamicExerciseRequest(BaseModel):
    course_id: str
    student_progress: Dict
    context: Dict

class QuizRequest(BaseModel):
    course_id: str
    student_progress: Dict
    context: Dict

class StudentProgress(BaseModel):
    course_id: str
    student_id: str
    completed_exercises: int
    total_exercises: int
    quiz_scores: List[float]
    knowledge_areas: List[str]
    current_level: str
    last_activity: datetime

class LabSessionRequest(BaseModel):
    course_id: str
    student_id: str
    session_data: Optional[Dict] = {}
    code_files: Optional[Dict] = {}
    current_exercise: Optional[str] = None
    progress_data: Optional[Dict] = {}

class SaveLabStateRequest(BaseModel):
    course_id: str
    student_id: str
    session_data: Dict
    ai_conversation_history: List[Dict]
    code_files: Dict
    current_exercise: Optional[str] = None
    progress_data: Optional[Dict] = {}

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logging.info("Database connection pool created successfully")
        except Exception as e:
            logging.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logging.info("Database connection pool closed")
    
    def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise HTTPException(status_code=500, detail="Database not connected")
        return self.pool.acquire()

class SyllabusRequest(BaseModel):
    course_id: str
    title: str
    description: str
    category: str
    difficulty_level: str
    estimated_duration: int

class SyllabusFeedback(BaseModel):
    course_id: str
    feedback: str
    current_syllabus: dict

async def save_exercises_to_db(course_id: str, exercises_data: List[Dict]) -> bool:
    """Save exercises to database"""
    logger = logging.getLogger(__name__)
    global db_manager
    logger.info(f"Attempting to save {len(exercises_data)} exercises for course {course_id}")
    if not db_manager:
        logger.error("Database manager not initialized")
        return False
    try:
        async with db_manager.get_connection() as conn:
            # First check if exercises table exists, if not create it
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS exercises (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR(255) NOT NULL,
                    exercise_id VARCHAR(255) NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    type VARCHAR(50),
                    difficulty VARCHAR(20),
                    module_number INTEGER,
                    topics_covered JSONB,
                    instructions TEXT,
                    expected_output TEXT,
                    hints TEXT,
                    sample_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(course_id, exercise_id)
                )
            """)
            
            # Delete existing exercises for this course
            await conn.execute("DELETE FROM exercises WHERE course_id = $1", course_id)
            
            # Insert new exercises
            for exercise in exercises_data:
                await conn.execute("""
                    INSERT INTO exercises (
                        course_id, exercise_id, title, description, type, difficulty,
                        module_number, topics_covered, instructions, expected_output,
                        hints, sample_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, 
                    course_id,
                    exercise.get('id', ''),
                    exercise.get('title', ''),
                    exercise.get('description', ''),
                    exercise.get('type', ''),
                    exercise.get('difficulty', ''),
                    exercise.get('module_number', 0),
                    json.dumps(exercise.get('topics_covered', [])),
                    json.dumps(exercise.get('instructions', [])) if isinstance(exercise.get('instructions'), list) else exercise.get('instructions', ''),
                    exercise.get('expected_output', ''),
                    json.dumps(exercise.get('hints', [])) if isinstance(exercise.get('hints'), list) else exercise.get('hints', ''),
                    exercise.get('sample_data', '')
                )
            
            logger.info(f"Successfully saved {len(exercises_data)} exercises to database for course {course_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error saving exercises to database: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def parse_exercise_references(user_message: str) -> List[str]:
    """Parse user message to extract exercise references like 'lab 1', 'exercise 2', etc."""
    import re
    references = []
    
    # Common patterns for exercise references
    patterns = [
        r'lab\s+(\d+)',
        r'exercise\s+(\d+)', 
        r'lab\s+(\w+)',
        r'exercise\s+(\w+)',
        r'question\s+(\d+)',
        r'problem\s+(\d+)',
        r'task\s+(\d+)',
        r'step\s+(\d+)'
    ]
    
    user_message_lower = user_message.lower()
    for pattern in patterns:
        matches = re.findall(pattern, user_message_lower)
        for match in matches:
            references.append(match)
    
    return references

async def get_course_difficulty(course_id: str) -> str:
    """Get course difficulty level from syllabus data"""
    try:
        # Try to get syllabus from database first
        syllabus = await load_syllabus_from_db(course_id)
        if not syllabus:
            # Fallback to memory
            syllabus = course_syllabi.get(course_id, {})
        
        if syllabus:
            # Check if level field exists
            level = syllabus.get('level', '').lower()
            if level in ['beginner', 'intermediate', 'advanced']:
                return level
            
            # Fallback to overview analysis (same logic as exercise generation)
            overview = syllabus.get('overview', '').lower()
            if ("introduction" in overview or "comprehensive introduction" in overview or 
                "beginner" in overview or "fundamental" in overview or 
                "start their journey" in overview or "foundation" in overview):
                return "beginner"
            elif ("advanced course" in overview or "expert level" in overview):
                return "advanced"
            elif "intermediate" in overview or "prior experience" in overview:
                return "intermediate"
        
        # Default fallback
        return "beginner"
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting course difficulty: {e}")
        return "beginner"

async def get_exercise_context(course_id: str, exercise_references: List[str] = None) -> str:
    """Get detailed exercise context for AI assistant"""
    try:
        # Load all exercises for the course
        exercises = await load_exercises_from_db(course_id)
        if not exercises:
            # Fallback to memory
            exercises = exercises_cache.get(course_id, [])
        
        if not exercises:
            return "No exercises available for this course."
        
        context_parts = []
        
        # If specific exercises referenced, focus on those
        if exercise_references:
            context_parts.append("**Referenced Exercises:**")
            for ref in exercise_references:
                # Try to match exercise by number or title
                matching_exercises = []
                for i, exercise in enumerate(exercises):
                    # Match by index (lab 1 = first exercise)
                    if ref.isdigit() and int(ref) == i + 1:
                        matching_exercises.append((i + 1, exercise))
                    # Match by title words
                    elif not ref.isdigit() and ref.lower() in exercise.get('title', '').lower():
                        matching_exercises.append((i + 1, exercise))
                
                for idx, exercise in matching_exercises:
                    context_parts.append(f"\n**Exercise {idx}: {exercise.get('title', 'Untitled')}**")
                    context_parts.append(f"Description: {exercise.get('description', 'No description')}")
                    
                    # Include instructions if available
                    if 'instructions' in exercise:
                        context_parts.append(f"Instructions: {exercise['instructions']}")
                    
                    # Include starter code if available
                    if 'starter_code' in exercise:
                        context_parts.append(f"Starter Code:\n```\n{exercise['starter_code']}\n```")
                    
                    # Include learning objectives
                    if 'learning_objectives' in exercise:
                        objectives = exercise['learning_objectives']
                        if isinstance(objectives, list):
                            context_parts.append(f"Learning Objectives: {', '.join(objectives)}")
                        else:
                            context_parts.append(f"Learning Objectives: {objectives}")
                    
                    context_parts.append("---")
        
        # Always include exercise overview
        context_parts.append(f"\n**All Course Exercises ({len(exercises)} total):**")
        for i, exercise in enumerate(exercises):
            title = exercise.get('title', 'Untitled')
            difficulty = exercise.get('difficulty', 'unknown')
            context_parts.append(f"{i + 1}. {title} (Difficulty: {difficulty})")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error getting exercise context: {e}")
        return "Error loading exercise context."

async def load_exercises_from_db(course_id: str) -> List[Dict]:
    """Load exercises from database"""
    logger = logging.getLogger(__name__)
    global db_manager
    if not db_manager:
        logger.error("Database manager not initialized")
        return []
    try:
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM exercises 
                WHERE course_id = $1 
                ORDER BY module_number, exercise_id
            """, course_id)
            
            exercises_data = []
            for row in rows:
                exercise = {
                    'id': row['exercise_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'type': row['type'],
                    'difficulty': row['difficulty'],
                    'module_number': row['module_number'],
                    'topics_covered': json.loads(row['topics_covered']) if row['topics_covered'] else [],
                    'instructions': row['instructions'],
                    'expected_output': row['expected_output'],
                    'hints': row['hints'],
                    'sample_data': row['sample_data']
                }
                exercises_data.append(exercise)
            
            logger.info(f"Loaded {len(exercises_data)} exercises from database for course {course_id}")
            return exercises_data
            
    except Exception as e:
        logger.error(f"Error loading exercises from database: {e}")
        return []

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Logging setup
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """FastAPI lifespan event handler"""
        global db_manager
        
        # Startup
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Use the correct database configuration on port 5433
        if db_password:
            database_url = f"postgresql://course_user:{db_password}@localhost:5433/course_creator"
        else:
            raise ValueError("DB_PASSWORD environment variable is required")
        db_manager = DatabaseManager(database_url)
        await db_manager.connect()
        
        # Make sure the global db_manager is accessible to other functions
        globals()['db_manager'] = db_manager
        
        # Initialize services after database is ready
        nonlocal ai_service, syllabus_service, lab_environment_service, exercise_generation_service
        ai_service = AIService(claude_client)
        syllabus_service = SyllabusService(db_manager.pool, ai_service)
        lab_environment_service = LabEnvironmentService(db_manager.pool, ai_service, storage=None)
        exercise_generation_service = ExerciseGenerationService(
            db=db_manager.pool,
            ai_service=ai_service,
            syllabus_service=syllabus_service,
            lab_service=lab_environment_service
        )
        
        # Load existing exercises from database on startup
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("SELECT DISTINCT course_id FROM exercises")
                for row in rows:
                    course_id = row['course_id']
                    exercises_data = await load_exercises_from_db(course_id)
                    exercises[course_id] = exercises_data
                    logger.info(f"Loaded {len(exercises_data)} exercises for course {course_id}")
        except Exception as e:
            logger.error(f"Error loading exercises on startup: {e}")
        
        yield
        
        # Shutdown
        await db_manager.disconnect()
    
    # FastAPI app with lifespan
    app = FastAPI(
        title="Course Generator API",
        description="API for generating courses from templates",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    
    # In-memory storage for demo
    templates = {
        "basic": {
            "id": "basic",
            "name": "Basic Course Template",
            "description": "Simple course structure",
            "parameters": {"title": "string", "duration": "integer"}
        }
    }
    jobs = {}
    course_slides = {}
    lab_environments = {}
    exercises = {}
    exercises_cache = exercises  # Alias for exercise context functions
    active_labs = {}
    student_progress = {}
    course_quizzes = {}
    lab_analytics = {}
    course_syllabi = {}
    
    # Global database manager (initialized in lifespan function)
    db_manager = None
    
    # Database functions for syllabi
    async def save_syllabus_to_db(course_id: str, syllabus_data: dict):
        """Save syllabus to database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
        
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO syllabi (course_id, syllabus_data, updated_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (course_id) 
                    DO UPDATE SET syllabus_data = EXCLUDED.syllabus_data, updated_at = NOW()
                """, 
                uuid.UUID(course_id), 
                json.dumps(syllabus_data)
                )
                
                logger.info(f"Saved syllabus to database for course {course_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving syllabus to database: {e}")
            return False

    async def load_syllabus_from_db(course_id: str) -> dict:
        """Load syllabus from database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return None
        
        try:
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT syllabus_data
                    FROM syllabi 
                    WHERE course_id = $1
                """, uuid.UUID(course_id))
                
                if row:
                    syllabus_data = json.loads(row['syllabus_data'])
                    logger.info(f"Loaded syllabus from database for course {course_id}")
                    return syllabus_data
                else:
                    logger.info(f"No syllabus found in database for course {course_id}")
                    return None
        except Exception as e:
            logger.error(f"Error loading syllabus from database: {e}")
            return None

    # Database functions for lab environments
    async def save_lab_environment_to_db(course_id: str, lab_data: dict):
        """Save lab environment to database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
        
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO lab_environments (course_id, name, description, environment_type, config, exercises, status, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (course_id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        environment_type = EXCLUDED.environment_type,
                        config = EXCLUDED.config,
                        exercises = EXCLUDED.exercises,
                        status = EXCLUDED.status,
                        updated_at = NOW()
                """, 
                uuid.UUID(course_id), 
                lab_data.get('name', 'AI Lab Environment'),
                lab_data.get('description', 'Interactive lab environment'),
                lab_data.get('environment_type', 'ai_assisted'),
                json.dumps(lab_data.get('config', {})),
                json.dumps(lab_data.get('exercises', [])),
                lab_data.get('status', 'ready')
                )
                
                logger.info(f"Saved lab environment to database for course {course_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving lab environment to database: {e}")
            return False

    async def load_lab_environment_from_db(course_id: str) -> dict:
        """Load lab environment from database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return None
        
        try:
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, name, description, environment_type, config, exercises, status
                    FROM lab_environments 
                    WHERE course_id = $1
                """, uuid.UUID(course_id))
                
                if row:
                    lab_data = {
                        "id": str(row['id']),
                        "course_id": course_id,
                        "name": row['name'],
                        "description": row['description'],
                        "environment_type": row['environment_type'],
                        "config": json.loads(row['config']) if row['config'] else {},
                        "exercises": json.loads(row['exercises']) if row['exercises'] else [],
                        "status": row['status']
                    }
                    logger.info(f"Loaded lab environment from database for course {course_id}")
                    return lab_data
                else:
                    logger.info(f"No lab environment found in database for course {course_id}")
                    return None
        except Exception as e:
            logger.error(f"Error loading lab environment from database: {e}")
            return None

    # Database functions for slides
    async def save_slides_to_db(course_id: str, slides_data: List[Dict]):
        """Save slides to database"""
        global db_manager
        if not db_manager:
            logger.error("Database pool not initialized")
            return False
            
        try:
            async with db_manager.get_connection() as conn:
                # Delete existing slides for this course
                await conn.execute("DELETE FROM slides WHERE course_id = $1", course_id)
                
                # Insert new slides
                for slide in slides_data:
                    await conn.execute("""
                        INSERT INTO slides (course_id, title, content, slide_type, order_number, module_number)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, 
                    course_id, 
                    slide.get('title', ''),
                    slide.get('content', ''),
                    slide.get('slide_type', 'content'),
                    slide.get('order', 0),
                    slide.get('module_number')
                    )
                
                logger.info(f"Saved {len(slides_data)} slides to database for course {course_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving slides to database: {e}")
            return False

    async def save_quizzes_to_db(course_id: str, quizzes_data: List[Dict]):
        """Save quizzes to database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
            
        try:
            async with db_manager.get_connection() as conn:
                # Delete existing quizzes for this course
                await conn.execute("DELETE FROM quizzes WHERE course_id = $1", course_id)
                
                # Insert new quizzes
                for quiz in quizzes_data:
                    quiz_id = quiz.get('id', str(uuid.uuid4()))
                    await conn.execute("""
                        INSERT INTO quizzes (id, course_id, title, description, duration, difficulty, module_number, questions_data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, 
                    quiz_id,
                    course_id, 
                    quiz.get('title', ''),
                    quiz.get('description', ''),
                    quiz.get('duration', 20),
                    quiz.get('difficulty', 'beginner'),
                    quiz.get('module_number', 1),
                    json.dumps(quiz.get('questions', []))
                    )
                
                logger.info(f"Saved {len(quizzes_data)} quizzes to database for course {course_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving quizzes to database: {e}")
            return False
    
    async def delete_quiz_from_db(quiz_id: str):
        """Delete a specific quiz from database"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
            
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("DELETE FROM quizzes WHERE id = $1", quiz_id)
                logger.info(f"Deleted quiz {quiz_id} from database")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting quiz from database: {e}")
            return False
    
    async def load_slides_from_db(course_id: str) -> List[Dict]:
        """Load slides from database"""
        global db_manager
        if not db_manager:
            logger.error("Database pool not initialized")
            return []
            
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT title, content, slide_type, order_number, module_number
                    FROM slides 
                    WHERE course_id = $1 
                    ORDER BY order_number ASC
                """, course_id)
                
                slides = []
                for row in rows:
                    slides.append({
                        'id': f"slide_{row['order_number']}",
                        'title': row['title'],
                        'content': row['content'],
                        'slide_type': row['slide_type'],
                        'order': row['order_number'],
                        'module_number': row['module_number']
                    })
                
                logger.info(f"Loaded {len(slides)} slides from database for course {course_id}")
                return slides
        except Exception as e:
            logger.error(f"Error loading slides from database: {e}")
            return []

    # Database functions for lab sessions
    async def save_lab_session(course_id: str, student_id: str, session_data: dict, ai_history: list, code_files: dict, current_exercise: str = None, progress_data: dict = None):
        """Save or update lab session state"""
        global db_manager
        if not db_manager:
            logger.error("Database pool not initialized")
            return False
            
        try:
            async with db_manager.get_connection() as conn:
                # Use UPSERT (INSERT ... ON CONFLICT) to update existing session
                await conn.execute("""
                    INSERT INTO lab_sessions 
                    (course_id, student_id, session_data, ai_conversation_history, code_files, current_exercise, progress_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (course_id, student_id) 
                    DO UPDATE SET 
                        session_data = EXCLUDED.session_data,
                        ai_conversation_history = EXCLUDED.ai_conversation_history,
                        code_files = EXCLUDED.code_files,
                        current_exercise = EXCLUDED.current_exercise,
                        progress_data = EXCLUDED.progress_data,
                        updated_at = CURRENT_TIMESTAMP,
                        last_accessed_at = CURRENT_TIMESTAMP
                """, 
                course_id, 
                student_id,
                json.dumps(session_data) if session_data else '{}',
                json.dumps(ai_history) if ai_history else '[]',
                json.dumps(code_files) if code_files else '{}',
                current_exercise,
                json.dumps(progress_data) if progress_data else '{}'
                )
                
                logger.info(f"Saved lab session for student {student_id} in course {course_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving lab session: {e}")
            return False
    
    async def load_lab_session(course_id: str, student_id: str) -> dict:
        """Load lab session state from database"""
        global db_manager
        if not db_manager:
            logger.error("Database pool not initialized")
            return {}
            
        try:
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT session_data, ai_conversation_history, code_files, 
                           current_exercise, progress_data, last_accessed_at
                    FROM lab_sessions 
                    WHERE course_id = $1 AND student_id = $2
                """, course_id, student_id)
                
                if row:
                    # Update last accessed time
                    await conn.execute("""
                        UPDATE lab_sessions 
                        SET last_accessed_at = CURRENT_TIMESTAMP 
                        WHERE course_id = $1 AND student_id = $2
                    """, course_id, student_id)
                    
                    return {
                        'session_data': json.loads(row['session_data']) if row['session_data'] else {},
                        'ai_conversation_history': json.loads(row['ai_conversation_history']) if row['ai_conversation_history'] else [],
                        'code_files': json.loads(row['code_files']) if row['code_files'] else {},
                        'current_exercise': row['current_exercise'],
                        'progress_data': json.loads(row['progress_data']) if row['progress_data'] else {},
                        'last_accessed_at': row['last_accessed_at'].isoformat() if row['last_accessed_at'] else None
                    }
                else:
                    logger.info(f"No existing lab session found for student {student_id} in course {course_id}")
                    return {}
        except Exception as e:
            logger.error(f"Error loading lab session: {e}")
            return {}

    # Initialize Claude client
    claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_CLAUDE_API_KEY"))
    
    # Services will be initialized after database is ready
    ai_service = None
    syllabus_service = None
    lab_environment_service = None
    exercise_generation_service = None
    
    # Define sync helper functions
    def generate_exercises_from_syllabus_sync(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate exercises based on syllabus modules using LLM with full syllabus context"""
        # Get logger from current context
        logger = logging.getLogger(__name__)
        try:
            # Determine course level from syllabus - check level field first, then overview
            course_level = syllabus.get('level', '').lower()  # Check level field first
            if not course_level:
                # Fallback to overview field analysis - prioritize beginner indicators
                course_overview = syllabus.get('overview', '').lower()
                course_level = "beginner"  # Default to beginner
                
                # Check for beginner indicators first (higher priority)
                if ("introduction" in course_overview or "comprehensive introduction" in course_overview or 
                    "beginner" in course_overview or "no prior" in course_overview or 
                    "fundamental" in course_overview or "basic" in course_overview or
                    "start their journey" in course_overview or "foundation" in course_overview):
                    course_level = "beginner"
                # Only consider advanced if explicitly stated as an advanced course
                elif ("advanced course" in course_overview or "expert level" in course_overview or
                      "prerequisite" in course_overview):
                    course_level = "advanced"
                elif "intermediate" in course_overview or "prior experience" in course_overview:
                    course_level = "intermediate"
            
            # Ensure course_level is one of the expected values
            if course_level not in ["beginner", "intermediate", "advanced"]:
                course_level = "beginner"
            
            logger.info(f"Detected course level: {course_level} for course {course_id}")
            
            # Debug the syllabus structure
            logger.info(f"Syllabus structure: {syllabus}")
            logger.info(f"Syllabus keys: {list(syllabus.keys()) if isinstance(syllabus, dict) else 'Not a dict'}")
            
            # Build comprehensive prompt using syllabus structure
            # Serialize modules separately to avoid f-string issues
            modules_json = json.dumps(syllabus.get('modules', []), indent=2, ensure_ascii=False)
            
            exercises_prompt = """
            You are an expert educator creating SPECIFIC, CONCRETE lab exercises for this course syllabus.
            
            Course Overview: """ + syllabus.get('overview', '') + """
            
            🚨 CRITICAL COURSE LEVEL REQUIREMENT 🚨
            Course Level: """ + course_level.upper() + """
            
            MANDATORY: ALL EXERCISES MUST BE """ + course_level.upper() + """ LEVEL ONLY!
            DO NOT create exercises above """ + course_level.upper() + """ difficulty!
            Each exercise "difficulty" field MUST be """ + course_level + """!
            
            Full Syllabus Modules:
            """ + modules_json + """
            
            🎯 EXAMPLES OF PERFECT LAB EXERCISES FOR DIFFERENT SUBJECTS:
            
            PROGRAMMING EXAMPLE:
            {{
                "title": "Circle Area and Circumference Calculator",
                "description": "Design a program that takes a value r (radius of a circle) and calculates the area and circumference.",
                "instructions": [
                    "Step 1: Define r as a constant in the Python code (e.g., r = 5.0)",
                    "Step 2: Take radius value from standard input using input()",
                    "Step 3: Import math library and use math.pi for pi value",
                    "Step 4: Calculate area using formula: area = π × r²",
                    "Step 5: Calculate circumference using formula: circumference = 2 × π × r",
                    "Step 6: Display both results with proper formatting"
                ],
                "expected_output": "For radius 5: 'Area: 78.54' and 'Circumference: 31.42'",
                "formulas": ["Area = π × r²", "Circumference = 2 × π × r"]
            }}
            
            LINUX/SHELL EXAMPLE:
            {{
                "title": "File System Navigation and Management",
                "description": "Practice essential Linux commands for navigating and managing files and directories.",
                "instructions": [
                    "Step 1: Use 'pwd' command to display current directory",
                    "Step 2: Use 'ls -la' to list all files with detailed information",
                    "Step 3: Create a new directory called 'test_lab' using 'mkdir'",
                    "Step 4: Navigate into the directory using 'cd test_lab'",
                    "Step 5: Create a text file using 'touch sample.txt'",
                    "Step 6: Use 'echo' to add content: echo 'Hello Linux' > sample.txt",
                    "Step 7: View file content using 'cat sample.txt'",
                    "Step 8: Copy the file using 'cp sample.txt backup.txt'"
                ],
                "expected_output": "Directory created, file created with content 'Hello Linux', backup file created",
                "formulas": []
            }}
            
            MATHEMATICS EXAMPLE:
            {{
                "title": "Quadratic Equation Solver",
                "description": "Solve quadratic equations using the quadratic formula and analyze the results.",
                "instructions": [
                    "Step 1: Given equation ax² + bx + c = 0, identify coefficients a=2, b=5, c=3",
                    "Step 2: Calculate the discriminant: Δ = b² - 4ac",
                    "Step 3: Determine if discriminant is positive, negative, or zero",
                    "Step 4: Apply quadratic formula: x = (-b ± √Δ) / (2a)",
                    "Step 5: Calculate both possible solutions (x₁ and x₂)",
                    "Step 6: Verify solutions by substituting back into original equation"
                ],
                "expected_output": "For 2x² + 5x + 3 = 0: x₁ = -1, x₂ = -1.5",
                "formulas": ["Quadratic Formula: x = (-b ± √(b² - 4ac)) / (2a)", "Discriminant: Δ = b² - 4ac"]
            }}
            
            CRITICAL REQUIREMENTS FOR EXERCISES:
            1. Create ONE SPECIFIC exercise per major topic within each module
            2. For each module, generate exercises that cover ALL topics listed in that module
            3. Each exercise MUST have a clear, concrete goal with measurable outcome
            4. Provide EXACT step-by-step instructions that are actionable
            5. Include CLEAR expected inputs and outputs with examples
            6. Supply any formulas, commands, or concepts needed
            7. Use realistic, practical problems appropriate for the subject
            8. Each step should be a specific task, not vague instructions
            9. MANDATORY: If a module has multiple topics, create separate exercises for each topic
            
            EXERCISE STRUCTURE REQUIREMENTS:
            - Title: Clear, specific goal (e.g., "File Permissions Lab", "Essay Structure Analysis")
            - Description: One sentence explaining what the student will accomplish
            - Instructions: 4-8 specific steps, each building on the previous
            - Expected Output: Exact example of what the student should achieve
            - Hints: Specific tools, commands, functions, or techniques to use
            - Formulas: Any formulas, commands, or reference materials needed
            
            SUBJECT-SPECIFIC ADAPTATIONS:
            - PROGRAMMING: Code exercises with specific functions, inputs, outputs
            - LINUX/SYSTEMS: Command-line exercises with specific commands and file operations
            - MATHEMATICS: Problem-solving with specific numbers, formulas, and calculations
            - ENGLISH/WRITING: Analysis exercises with specific texts, writing tasks with clear criteria
            - HISTORY: Timeline creation, source analysis, comparison exercises with specific events
            - SCIENCE: Experiments, calculations, data analysis with specific procedures
            - BUSINESS: Case studies, calculations, analysis with specific scenarios
            
            BEGINNER-FRIENDLY EXAMPLES BY SUBJECT:
            - Programming: "BMI Calculator", "Temperature Converter", "Grade Calculator"
            - Linux: "File Navigation", "Permission Management", "Process Monitoring"
            - Math: "Equation Solver", "Geometry Calculator", "Statistical Analysis"
            - English: "Paragraph Analysis", "Grammar Check", "Essay Outline"
            - History: "Timeline Creation", "Source Comparison", "Event Analysis"
            
            CRITICAL: ALL EXERCISES MUST BE """ + course_level.upper() + """ LEVEL. Do not mix difficulty levels.
            
            UNIVERSAL PRINCIPLES FOR EXCELLENT LABS:
            - Transform theoretical concepts into hands-on practice
            - Solve real problems that professionals encounter in this field
            - Use actual tools, commands, and methods from the industry
            - Include sample data or scenarios that mirror real-world situations
            - Build something tangible that students can see working
            - Connect individual topics into comprehensive projects
            
            STRUCTURE REQUIREMENTS:
            - Each lab must have a clear practical purpose
            - Include specific sample data, files, or scenarios appropriate to the subject
            - Provide detailed step-by-step instructions with actual commands/code
            - Give specific expected outputs or results
            - Include troubleshooting hints for common issues
            - Add starter templates or setup instructions when appropriate
            
            For each module, create ONE separate exercise for EACH topic listed in that module.
            If a module has 3 topics, generate 3 separate exercises.
            Base your exercises on the specific topics listed in each module - don't make assumptions about the subject matter.
            Each exercise should focus on one specific topic to ensure comprehensive coverage.
            
            Return ONLY a valid JSON array. Do not include any explanatory text, markdown formatting, or code blocks.
            The response must be a single JSON array starting with [ and ending with ].
            
            Example format:
            [
                {{
                    "id": "ex_1_1",
                    "title": "Practical Lab Title",
                    "description": "Clear description of the task",
                    "type": "hands_on",
                    "difficulty": """ + course_level + """,
                    "module_number": 1,
                    "topics_covered": ["topic 1", "topic 2"],
                    "purpose": "Why this lab is useful",
                    "sample_data": "Sample data to use",
                    "instructions": [
                        "Step 1: Setup",
                        "Step 2: Execute",
                        "Step 3: Test",
                        "Step 4: Verify"
                    ],
                    "expected_output": "Expected outcome",
                    "hints": ["Hint 1", "Hint 2"],
                    "evaluation_criteria": ["Criteria 1", "Criteria 2"],
                    "estimated_time": "30-45 minutes",
                    "starter_code": "Optional starter code"
                }}
            ]
            
            Generate labs that teach practical skills through meaningful projects students would actually want to complete in this subject area.
            """
            
            # Add more detailed logging
            logger.info(f"Generating exercises for course {course_id} with syllabus: {syllabus.get('overview', 'No overview')}")
            
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",  # Using more capable model
                max_tokens=4096,  # Fixed to comply with model limit
                messages=[
                    {"role": "user", "content": exercises_prompt}
                ]
            )
            
            try:
                raw_response = response.content[0].text
                logger.info(f"Raw AI response length: {len(raw_response)}")
                logger.info(f"Raw AI response preview: {raw_response[:200]}...")
                
                # Clean the response first
                cleaned_response = raw_response.strip()
                
                # Try direct JSON parsing first
                try:
                    exercises_data = json.loads(cleaned_response)
                except json.JSONDecodeError:
                    # If direct parsing fails, try to extract JSON
                    logger.info("Direct JSON parsing failed, attempting to extract JSON from response...")
                    
                    # Look for JSON array markers
                    start = cleaned_response.find('[')
                    end = cleaned_response.rfind(']') + 1
                    
                    if start != -1 and end != 0:
                        extracted_json = cleaned_response[start:end]
                        logger.info(f"Extracted JSON length: {len(extracted_json)}")
                        logger.info(f"Extracted JSON preview: {extracted_json[:500]}...")
                        
                        # Clean up common JSON issues
                        extracted_json = extracted_json.replace('\n', ' ').replace('\t', ' ')
                        # Remove any markdown code block markers
                        extracted_json = extracted_json.replace('```json', '').replace('```', '')
                        # Remove leading/trailing whitespace and fix common formatting issues
                        extracted_json = extracted_json.strip()
                        # Handle cases where JSON has unescaped quotes or control characters
                        # Remove invalid control characters that might cause parsing issues
                        extracted_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', extracted_json)
                        # Fix common issues with trailing commas
                        extracted_json = re.sub(r',\s*}', '}', extracted_json)
                        extracted_json = re.sub(r',\s*]', ']', extracted_json)
                        
                        try:
                            exercises_data = json.loads(extracted_json)
                        except json.JSONDecodeError as inner_e:
                            logger.error(f"JSON extraction failed: {inner_e}")
                            logger.error(f"Error position: line {inner_e.lineno}, column {inner_e.colno}")
                            logger.error(f"Problematic JSON: {extracted_json[:1000]}...")
                            logger.error(f"Raw response for debugging: {raw_response[:2000]}...")
                            return []
                    else:
                        logger.error("Could not find JSON array markers in response")
                        return []
                
                # Validate the parsed data
                if not isinstance(exercises_data, list):
                    logger.error(f"Expected JSON array, got {type(exercises_data)}")
                    return []
                
                # CRITICAL: Force all exercises to use the correct difficulty level
                for exercise in exercises_data:
                    if isinstance(exercise, dict):
                        exercise['difficulty'] = course_level
                        logger.info(f"Forced exercise '{exercise.get('title', 'Unknown')}' to {course_level} level")
                
                logger.info(f"Generated {len(exercises_data)} exercises from syllabus using LLM")
                return exercises_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Failed to parse AI response: {raw_response[:1000]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error generating exercises from syllabus with LLM: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    
    def generate_quizzes_from_syllabus_sync(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate quizzes based on syllabus modules using LLM with full syllabus context"""
        try:
            # Build comprehensive prompt using syllabus structure
            quizzes_prompt = f"""
            You are an expert educator creating comprehensive assessment quizzes for this course syllabus.
            
            Course Overview: {syllabus.get('overview', '')}
            
            Full Syllabus Modules:
            {json.dumps(syllabus.get('modules', []), indent=2)}
            
            CRITICAL REQUIREMENTS FOR QUIZZES:
            1. Create SPECIFIC questions based on the exact topics, concepts, and learning outcomes in the syllabus
            2. Test both conceptual understanding and practical application of the subject matter
            3. Include scenario-based questions that mirror real-world situations in this field
            4. Each question must test understanding of specific knowledge from the syllabus content
            5. Provide realistic distractors (wrong answers) that are plausible but clearly incorrect
            6. Include detailed explanations for correct answers that enhance learning
            7. Cover different cognitive levels: recall, comprehension, application, and analysis
            8. Questions should be appropriate for professionals working in this field
            
            UNIVERSAL PRINCIPLES FOR EXCELLENT QUIZ QUESTIONS:
            - Test practical knowledge students would use in real-world scenarios
            - Include situation-based questions that require applying concepts
            - Use terminology and examples specific to the subject field
            - Create distractors that represent common misconceptions or mistakes
            - Focus on understanding "why" and "how" rather than just memorization
            - Include questions that test problem-solving and critical thinking
            - Ensure questions are clear, unambiguous, and professionally relevant
            
            QUESTION TYPES TO INCLUDE:
            - Definition/Concept questions: Test understanding of key terms and principles
            - Application questions: Test ability to apply concepts to new situations
            - Scenario questions: Present realistic situations requiring knowledge application
            - Analysis questions: Test ability to break down complex problems
            - Comparison questions: Test understanding of differences and similarities
            - Troubleshooting questions: Test problem-solving skills in context
            
            STRUCTURE REQUIREMENTS:
            - Each quiz should have 3-5 well-crafted questions per module
            - Questions should progress from basic to more complex within each quiz
            - Include variety in question types and difficulty levels
            - Provide comprehensive explanations that teach as well as assess
            - Ensure all questions are directly tied to specific syllabus content
            - Base questions on the actual topics and learning outcomes listed
            
            For each module, create 3-5 questions that comprehensively test the specific topics and learning outcomes mentioned in the syllabus.
            Base your questions on the specific content listed in each module - don't make assumptions about the subject matter.
            
            Return ONLY valid JSON array with this structure:
            [
                {{
                    "id": "quiz_1",
                    "title": "Module Title - Knowledge Assessment",
                    "description": "Comprehensive quiz covering key concepts and practical applications",
                    "module_number": 1,
                    "duration": 20,
                    "difficulty": "beginner",
                    "topics_covered": ["specific topic 1", "specific topic 2"],
                    "learning_objectives": ["what students should demonstrate after taking this quiz"],
                    "questions": [
                        {{
                            "question": "Clear, specific question based on syllabus content",
                            "question_type": "scenario|definition|application|analysis|comparison",
                            "options": ["Correct answer", "Plausible distractor 1", "Plausible distractor 2", "Plausible distractor 3"],
                            "correct_answer": 0,
                            "explanation": "Detailed explanation of why this is correct, why others are wrong, and additional context",
                            "topic_tested": "Specific topic from syllabus",
                            "difficulty": "beginner|intermediate|advanced",
                            "cognitive_level": "recall|comprehension|application|analysis"
                        }}
                    ]
                }}
            ]
            
            Generate questions that test real understanding and practical knowledge relevant to this subject area.
            Focus on questions that professionals in this field would need to know and apply.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": quizzes_prompt}
                ]
            )
            
            try:
                quizzes_data = json.loads(response.content[0].text)
                logger.info(f"Generated {len(quizzes_data)} quizzes from syllabus using LLM")
                return quizzes_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != 0:
                    try:
                        quizzes_data = json.loads(text[start:end])
                        logger.info(f"Extracted {len(quizzes_data)} quizzes from LLM response")
                        return quizzes_data
                    except:
                        pass
                
                # Fallback to programmatic generation
                logger.warning("LLM response parsing failed, using fallback quiz generation")
                return generate_quizzes_fallback(syllabus)
                
        except Exception as e:
            logger.error(f"Error generating quizzes from syllabus with LLM: {e}")
            return generate_quizzes_fallback(syllabus)
    
    def generate_quizzes_fallback(syllabus: dict) -> List[Dict]:
        """Fallback quiz generation when LLM fails"""
        quizzes_list = []
        
        for module in syllabus.get("modules", []):
            quiz = {
                "id": f"quiz_{module.get('module_number', 1)}",
                "title": f"{module.get('title', 'Module')} - Knowledge Assessment",
                "description": f"Quiz covering the key concepts from {module.get('title', 'this module')}",
                "module_number": module.get('module_number', 1),
                "questions": [],
                "duration": 30,  # 30 minutes for 10 questions
                "difficulty": "beginner"
            }
            
            # Generate questions based on learning outcomes - ensure at least 10 questions
            learning_outcomes = module.get("learning_outcomes", [])
            topics = module.get("topics", [])
            
            # Create questions from learning outcomes
            for i, outcome in enumerate(learning_outcomes):
                quiz["questions"].append({
                    "question": f"Which of the following best describes the key concept related to {outcome}?",
                    "options": [
                        f"The primary principle of {outcome}",
                        f"A secondary aspect of {outcome}",
                        f"An unrelated concept",
                        f"A prerequisite for {outcome}"
                    ],
                    "correct_answer": 0,
                    "explanation": f"This question tests understanding of {outcome} as covered in the module.",
                    "topic_tested": outcome,
                    "difficulty": "beginner"
                })
            
            # Add questions from topics if needed to reach 10 questions
            for i, topic in enumerate(topics):
                if len(quiz["questions"]) >= 10:
                    break
                quiz["questions"].append({
                    "question": f"What is the main focus of {topic}?",
                    "options": [
                        f"Understanding {topic} fundamentals",
                        f"Advanced {topic} applications",
                        f"Historical background of {topic}",
                        f"Unrelated concepts"
                    ],
                    "correct_answer": 0,
                    "explanation": f"This question tests knowledge of {topic} as covered in the module.",
                    "topic_tested": topic,
                    "difficulty": "beginner"
                })
            
            # Fill remaining questions to reach minimum 10
            while len(quiz["questions"]) < 10:
                question_num = len(quiz["questions"]) + 1
                quiz["questions"].append({
                    "question": f"Question {question_num} about {module.get('title', 'this module')}?",
                    "options": [
                        "Option A - Correct answer",
                        "Option B - Incorrect",
                        "Option C - Incorrect", 
                        "Option D - Incorrect"
                    ],
                    "correct_answer": 0,
                    "explanation": f"This is a generated question for {module.get('title', 'this module')}.",
                    "topic_tested": module.get('title', 'Module'),
                    "difficulty": "beginner"
                })
            
            # Add topic-based questions
            for i, topic in enumerate(module.get("topics", [])):
                quiz["questions"].append({
                    "question": f"What is the most important aspect of {topic} in practical applications?",
                    "options": [
                        f"Implementation strategies for {topic}",
                        f"Historical background of {topic}",
                        f"Theoretical foundations only",
                        f"Advanced variations of {topic}"
                    ],
                    "correct_answer": 0,
                    "explanation": f"This focuses on practical application of {topic}.",
                    "topic_tested": topic,
                    "difficulty": "beginner"
                })
            
            quizzes_list.append(quiz)
        
        return quizzes_list
    
    @app.get("/")
    async def root():
        return {"message": "Course Generator Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.get("/templates")
    async def get_templates():
        return {"templates": list(templates.values())}
    
    @app.post("/generate")
    async def generate_course(request: GenerateCourseRequest):
        logger.info(f"Generating course with template: {request.template_id}")
        
        if request.template_id not in templates:
            raise HTTPException(status_code=404, detail="Template not found")
        
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            status="completed",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            result={"course_id": f"course_{job_id[:8]}", "title": request.parameters.get("title", "Generated Course")}
        )
        jobs[job_id] = job
        
        return {"job_id": job_id, "status": "completed", "result": job.result}
    
    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str):
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        return jobs[job_id]
    
    @app.post("/slides/generate")
    async def generate_slides(request: SlideGenerationRequest):
        logger.info(f"Generating slides for course: {request.course_id}")
        
        # Try to get syllabus from database first
        syllabus_data = await load_syllabus_from_db(request.course_id)
        
        if syllabus_data:
            # Generate slides based on syllabus
            logger.info(f"Using existing syllabus from database for course: {request.course_id}")
            slides_data = generate_course_slides_from_syllabus(request.course_id, syllabus_data)
        else:
            # Fallback: check in-memory storage
            if request.course_id in course_syllabi:
                logger.info(f"Using existing syllabus from memory for course: {request.course_id}")
                slides_data = generate_course_slides_from_syllabus(request.course_id, course_syllabi[request.course_id])
            else:
                # Last resort: generate basic slides from request parameters
                logger.warning(f"No syllabus found for course {request.course_id}, generating basic slides")
                slides_data = generate_basic_slides(request.title, request.description, request.topic)
        
        course_slides[request.course_id] = slides_data
        
        # Save to database
        await save_slides_to_db(request.course_id, slides_data)
        
        return {"course_id": request.course_id, "slides": slides_data}
    
    def generate_basic_slides(title: str, description: str, topic: str) -> List[Dict]:
        """Generate basic slides when no syllabus is available"""
        slides = []
        
        # Title slide with bullet points
        title_content = f"• {description}" if description else "• Course overview and introduction"
        slides.append({
            "id": "slide_1",
            "title": title,
            "content": title_content,
            "slide_type": "content",
            "order": 1
        })
        
        # Content slides based on topic
        topics = topic.split(',') if ',' in topic else [topic]
        for i, t in enumerate(topics[:5], 2):  # Max 5 additional slides
            slides.append({
                "id": f"slide_{i}",
                "title": f"{t.strip()} Fundamentals",
                "content": f"• Key concepts in {t.strip()}\n• Practical applications\n• Common techniques\n• Best practices",
                "slide_type": "content",
                "order": i
            })
        
        return slides
    
    @app.get("/slides/{course_id}")
    async def get_course_slides(course_id: str):
        # Try to load from database first
        slides_data = await load_slides_from_db(course_id)
        
        if not slides_data:
            # Fallback to in-memory storage
            if course_id in course_slides:
                slides_data = course_slides[course_id]
            else:
                raise HTTPException(status_code=404, detail="Slides not found for this course")
        
        return {"course_id": course_id, "slides": slides_data}
    
    @app.put("/slides/update/{course_id}")
    async def update_course_slides(course_id: str, request: dict):
        """Update slides for a course"""
        logger.info(f"Updating slides for course: {course_id}")
        
        slides_data = request.get('slides', [])
        course_slides[course_id] = slides_data
        
        # Save to database
        await save_slides_to_db(course_id, slides_data)
        
        return {"course_id": course_id, "slides": slides_data, "message": "Slides updated successfully"}
    
    @app.post("/lab/create")
    async def create_lab_environment(request: LabEnvironment):
        logger.info(f"Creating lab environment for course: {request.course_id}")
        
        lab_id = str(uuid.uuid4())
        lab_config = generate_lab_environment(request.name, request.description, request.environment_type)
        
        # Automatically generate exercises when creating lab
        exercises_data = []
        try:
            # Get syllabus from database
            syllabus = await load_syllabus_from_db(request.course_id)
            if not syllabus:
                # Try to get from memory if not in database
                syllabus = course_syllabi.get(request.course_id)
            
            if syllabus:
                logger.info(f"Generating exercises for new lab environment: {request.course_id}")
                exercises_data = generate_exercises_from_syllabus_sync(request.course_id, syllabus)
                
                # Store exercises in memory and database
                exercises[request.course_id] = exercises_data
                await save_exercises_to_db(request.course_id, exercises_data)
                
                logger.info(f"Generated {len(exercises_data)} exercises for lab environment")
            else:
                logger.warning(f"No syllabus found for course {request.course_id}, lab created without exercises")
        except Exception as e:
            logger.error(f"Error generating exercises for lab: {e}")
            # Continue with lab creation even if exercise generation fails
        
        lab_environments[lab_id] = {
            "id": lab_id,
            "course_id": request.course_id,
            "name": request.name,
            "description": request.description,
            "environment_type": request.environment_type,
            "config": lab_config,
            "exercises": exercises_data
        }
        
        return {"lab_id": lab_id, "lab": lab_environments[lab_id]}
    
    @app.get("/lab/{course_id}")
    async def get_lab_environment(course_id: str):
        """Get lab environment for a course with improved error handling."""
        try:
            # First check database for persistent lab environment
            lab_data = await load_lab_environment_from_db(course_id)
            if lab_data:
                return {"lab_id": lab_data["id"], "lab": lab_data}
            
            # Fallback to memory (for backward compatibility)
            for lab_id, lab in lab_environments.items():
                if lab["course_id"] == course_id:
                    return {"lab_id": lab_id, "lab": lab}
            
            # If no lab environment found, provide helpful information
            logger.warning(f"Lab environment not found for course {course_id}")
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "Lab environment not found",
                    "course_id": course_id,
                    "suggestions": [
                        "Generate course content to create lab environment",
                        "Check if course content generation completed successfully",
                        "Verify database connectivity"
                    ]
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting lab environment for course {course_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "message": "Failed to retrieve lab environment"
                }
            )
    
    @app.get("/student/lab-access/{course_id}/{student_id}")
    async def check_lab_access(course_id: str, student_id: str):
        """Check if student has access to lab environment with improved error handling."""
        try:
            # Check if lab environment exists (database first, then memory)
            lab_data = await load_lab_environment_from_db(course_id)
            lab_found = False
            lab_id = None
            lab = None
            
            if lab_data:
                lab_found = True
                lab_id = lab_data["id"]
                lab = lab_data
            else:
                # Fallback to memory
                for memory_lab_id, memory_lab in lab_environments.items():
                    if memory_lab["course_id"] == course_id:
                        lab_found = True
                        lab_id = memory_lab_id
                        lab = memory_lab
                        break
            
            if not lab_found:
                # Provide helpful error information
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": "Lab environment not found",
                        "course_id": course_id,
                        "student_id": student_id,
                        "access_granted": False,
                        "suggestions": [
                            "Contact instructor to generate lab environment",
                            "Verify course content has been created",
                            "Check course enrollment status"
                        ]
                    }
                )
            
            # TODO: In a real implementation, check enrollment status
            # For now, we'll simulate enrollment check
            has_access = True  # Assume student has access for demo
            
            if not has_access:
                raise HTTPException(
                    status_code=403, 
                    detail={
                        "error": "Access denied",
                        "message": "Student not enrolled in this course",
                        "course_id": course_id,
                        "student_id": student_id,
                        "access_granted": False
                    }
                )
            
            return {
                "access_granted": True,
                "lab_id": lab_id,
                "lab": lab,
                "student_id": student_id,
                "course_id": course_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking lab access for student {student_id} in course {course_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "message": "Failed to check lab access",
                    "access_granted": False
                }
            )
    
    @app.post("/exercises/generate")
    async def generate_exercises(request: ExerciseRequest):
        logger.info(f"Generating exercises for course: {request.course_id}")
        
        exercise_data = generate_course_exercises(request.topic, request.difficulty)
        logger.info(f"STORING exercises for course_id: '{request.course_id}'")
        logger.info(f"Number of exercises generated: {len(exercise_data)}")
        logger.info(f"Exercise titles: {[ex.get('title', 'No title') for ex in exercise_data]}")
        
        exercises[request.course_id] = exercise_data
        
        # Save to database
        await save_exercises_to_db(request.course_id, exercise_data)
        
        logger.info(f"After storing, exercises dictionary now has keys: {list(exercises.keys())}")
        logger.info(f"Total exercises in dictionary: {sum(len(v) for v in exercises.values())}")
        
        return {"course_id": request.course_id, "exercises": exercise_data}
    
    @app.get("/exercises/{course_id}")
    async def get_exercises(course_id: str):
        logger.info(f"GET /exercises/{course_id} - Requested course_id: {course_id}")
        logger.info(f"Available exercise keys: {list(exercises.keys())}")
        
        if course_id not in exercises:
            logger.error(f"Course ID '{course_id}' not found in exercises dictionary")
            logger.info(f"Current exercises keys: {list(exercises.keys())}")
            raise HTTPException(status_code=404, detail="Exercises not found for this course")
        
        exercise_data = exercises[course_id]
        logger.info(f"Returning {len(exercise_data)} exercises for course '{course_id}'")
        logger.info(f"Exercise titles: {[ex.get('title', 'No title') for ex in exercise_data]}")
        
        return {"course_id": course_id, "exercises": exercise_data}
    
    @app.get("/debug/exercises")
    async def debug_exercises():
        """Debug endpoint to view all exercises in memory"""
        logger.info("DEBUG: Exercises dictionary accessed")
        
        debug_info = {
            "total_courses_with_exercises": len(exercises),
            "course_ids": list(exercises.keys()),
            "exercises_by_course": {}
        }
        
        for course_id, course_exercises in exercises.items():
            debug_info["exercises_by_course"][course_id] = {
                "count": len(course_exercises),
                "titles": [ex.get('title', 'No title') for ex in course_exercises]
            }
        
        logger.info(f"DEBUG: Returning exercises debug info: {debug_info}")
        return debug_info
    
    @app.post("/debug/generate-test-exercises")
    async def generate_test_exercises(request: dict):
        """Debug endpoint to generate test exercises for a course"""
        course_id = request.get("course_id", "test-course")
        course_title = request.get("course_title", "Test Course")
        
        logger.info(f"DEBUG: Generating test exercises for course: {course_id}")
        
        # Generate generic exercises based on course title
        if "linux" in course_title.lower() or "system" in course_title.lower():
            test_exercises = [
                {
                    "id": 1,
                    "title": "System Administration Log Analyzer",
                    "description": "Build a script to analyze system logs and identify potential security issues",
                    "difficulty": "beginner",
                    "purpose": "Learn log analysis skills essential for system administration",
                    "sample_data": "Sample auth.log and syslog files with various entries",
                    "instructions": [
                        "Create a sample log file with failed login attempts",
                        "Write a bash script to count failed login attempts by IP",
                        "Use grep, awk, and sort to process the log data",
                        "Generate a report showing top 10 suspicious IPs"
                    ],
                    "expected_output": "Formatted report showing IP addresses and failed attempt counts",
                    "hints": ["Use grep to filter failed logins", "Use awk to extract IP addresses"],
                    "type": "hands_on"
                },
                {
                    "id": 2,
                    "title": "Automated Backup System",
                    "description": "Create a comprehensive backup script for important directories",
                    "difficulty": "intermediate",
                    "purpose": "Learn essential backup strategies used in production environments",
                    "sample_data": "Sample directories with various file types to backup",
                    "instructions": [
                        "Create directories with sample files (documents, configs, etc.)",
                        "Write a script that compresses directories with timestamp",
                        "Implement rotation to keep only 5 most recent backups",
                        "Add logging to track backup operations"
                    ],
                    "expected_output": "Compressed backup files with timestamps and rotation log",
                    "hints": ["Use tar with compression", "Use find to manage old backups"],
                    "type": "hands_on"
                }
            ]
        elif "python" in course_title.lower() or "programming" in course_title.lower():
            test_exercises = [
                {
                    "id": 1,
                    "title": "Student Grade Analysis System",
                    "description": "Build a complete grade management system using lists, dictionaries, and file I/O",
                    "difficulty": "beginner",
                    "purpose": "Learn data structures through practical grade management",
                    "sample_data": "CSV file with student names, subjects, and grades: 'Alice,85,92,78\nBob,90,87,85\nCarol,88,94,91'",
                    "instructions": [
                        "Create a CSV file with student data (name, math, science, english grades)",
                        "Read the file and store data in dictionaries and lists",
                        "Calculate class average, highest/lowest scores per subject",
                        "Generate a formatted report showing student rankings",
                        "Save results to a new file"
                    ],
                    "expected_output": "Formatted report with statistics and student rankings saved to file",
                    "hints": ["Use csv module for reading", "Use dict comprehensions for calculations", "Format numbers to 2 decimal places"],
                    "evaluation_criteria": ["Working code that runs without errors", "Produces correct output for sample data", "Handles file I/O properly"],
                    "estimated_time": "30-45 minutes",
                    "type": "coding"
                },
                {
                    "id": 2,
                    "title": "Coordinate Converter Tool",
                    "description": "Build a coordinate conversion tool with functions and user interface",
                    "difficulty": "intermediate",
                    "purpose": "Learn functions and math operations through practical geometry tool",
                    "sample_data": "Test coordinates: (3,4), (5,12), (0,0), (-3,4), (1,1)",
                    "instructions": [
                        "Create functions to convert Cartesian to polar coordinates",
                        "Create functions to convert polar to Cartesian coordinates",
                        "Add input validation and error handling",
                        "Create a menu system for user interaction",
                        "Test with provided sample coordinates"
                    ],
                    "expected_output": "Interactive program that converts coordinates with proper formatting",
                    "hints": ["Use math.sqrt() and math.atan2()", "Format output to 2 decimal places", "Handle division by zero"],
                    "evaluation_criteria": ["Functions work correctly", "Proper error handling", "User-friendly interface"],
                    "estimated_time": "45-60 minutes",
                    "type": "coding"
                }
            ]
        else:
            test_exercises = [
                {
                    "id": 1,
                    "title": "Getting Started",
                    "description": "Basic introduction to the course concepts",
                    "difficulty": "beginner",
                    "instructions": ["Follow the course materials", "Complete the exercises", "Ask questions if needed"],
                    "type": "general"
                }
            ]
        
        logger.info(f"DEBUG: Generated {len(test_exercises)} test exercises")
        logger.info(f"DEBUG: Exercise titles: {[ex['title'] for ex in test_exercises]}")
        
        exercises[course_id] = test_exercises
        
        logger.info(f"DEBUG: Stored exercises for course_id: {course_id}")
        logger.info(f"DEBUG: Total courses with exercises: {len(exercises)}")
        
        return {"course_id": course_id, "exercises": test_exercises, "count": len(test_exercises)}
    
    @app.post("/lab/launch")
    async def launch_lab(request: LabLaunchRequest):
        """Launch LLM-powered lab environment with expert trainer"""
        logger.info(f"Launching AI lab for course: {request.course_id}")
        
        # Create expert trainer context
        trainer_prompt = f"""
        You are an expert {request.course_category} instructor and trainer. You have:
        - Deep expertise in {request.course_category}
        - Years of teaching experience
        - Ability to adapt to student learning styles
        - Real-time progress tracking capabilities
        
        Course Context:
        - Title: {request.course_title}
        - Description: {request.course_description}
        - Category: {request.course_category}
        
        Your role is to:
        1. Provide expert guidance and instruction
        2. Generate dynamic exercises based on student progress
        3. Create adaptive quizzes covering learned material
        4. Track student understanding and adjust difficulty
        5. Offer encouragement and constructive feedback
        
        Always respond as a knowledgeable, patient instructor who adapts to the student's pace.
        """
        
        lab_id = str(uuid.uuid4())
        active_labs[request.course_id] = {
            "lab_id": lab_id,
            "course_id": request.course_id,
            "trainer_context": trainer_prompt,
            "status": "running",
            "created_at": datetime.now(),
            "course_info": {
                "title": request.course_title,
                "description": request.course_description,
                "category": request.course_category,
                "difficulty": await get_course_difficulty(request.course_id)
            }
        }
        
        # Initialize analytics
        lab_analytics[request.course_id] = {
            "total_students": 0,
            "active_students": 0,
            "avg_session_duration": 0,
            "exercises_completed": 0,
            "quizzes_taken": 0,
            "avg_quiz_score": 0,
            "ai_interactions": 0,
            "dynamic_exercises": 0,
            "adaptive_quizzes": 0,
            "student_progress": []
        }
        
        # Generate exercises from syllabus and slides during lab initialization
        try:
            # Get syllabus from database
            syllabus = await load_syllabus_from_db(request.course_id)
            if not syllabus:
                # Try to get from memory if not in database
                syllabus = course_syllabi.get(request.course_id)
            
            if syllabus:
                logger.info(f"Generating exercises from syllabus for lab: {request.course_id}")
                exercises_data = generate_exercises_from_syllabus_sync(request.course_id, syllabus)
                
                # Store exercises in memory and database
                exercises[request.course_id] = exercises_data
                
                # Save exercises to database
                await save_exercises_to_db(request.course_id, exercises_data)
                
                logger.info(f"Generated {len(exercises_data)} exercises for lab")
                active_labs[request.course_id]["exercises"] = exercises_data
            else:
                logger.warning(f"No syllabus found for course {request.course_id} - lab launched without exercises")
                active_labs[request.course_id]["exercises"] = []
                
        except Exception as e:
            logger.error(f"Error generating exercises during lab launch: {e}")
            active_labs[request.course_id]["exercises"] = []
        
        return {"lab_id": lab_id, "status": "running", "message": "AI Lab environment launched successfully"}
    
    @app.post("/lab/stop/{course_id}")
    async def stop_lab(course_id: str):
        """Stop lab environment"""
        if course_id in active_labs:
            active_labs[course_id]["status"] = "stopped"
            return {"message": "Lab environment stopped"}
        raise HTTPException(status_code=404, detail="Lab not found")
    
    @app.get("/lab/access/{course_id}")
    async def get_lab_access(course_id: str):
        """Get lab access information"""
        if course_id not in active_labs:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        lab = active_labs[course_id]
        if lab["status"] != "running":
            return {"access_url": None, "status": lab["status"]}
        
        # Return null access_url to force frontend to use embedded lab
        return {"access_url": None, "status": "running"}
    
    @app.post("/lab/session/save")
    async def save_lab_session_state(request: SaveLabStateRequest):
        """Save lab session state with AI conversation history"""
        logger.info(f"Saving lab session for student {request.student_id} in course {request.course_id}")
        
        success = await save_lab_session(
            request.course_id,
            request.student_id,
            request.session_data,
            request.ai_conversation_history,
            request.code_files,
            request.current_exercise,
            request.progress_data
        )
        
        if success:
            return {"message": "Lab session saved successfully", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=500, detail="Failed to save lab session")
    
    @app.get("/lab/session/{course_id}/{student_id}")
    async def load_lab_session_state(course_id: str, student_id: str):
        """Load lab session state with AI conversation history"""
        logger.info(f"Loading lab session for student {student_id} in course {course_id}")
        
        session_data = await load_lab_session(course_id, student_id)
        
        if session_data:
            return {
                "course_id": course_id,
                "student_id": student_id,
                "session_found": True,
                "session_data": session_data
            }
        else:
            return {
                "course_id": course_id,
                "student_id": student_id,
                "session_found": False,
                "session_data": {
                    "session_data": {},
                    "ai_conversation_history": [],
                    "code_files": {},
                    "current_exercise": None,
                    "progress_data": {},
                    "last_accessed_at": None
                }
            }
    
    @app.delete("/lab/session/{course_id}/{student_id}")
    async def clear_lab_session(course_id: str, student_id: str):
        """Clear/reset lab session for a student"""
        logger.info(f"Clearing lab session for student {student_id} in course {course_id}")
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
            
        try:
            async with db_manager.get_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM lab_sessions 
                    WHERE course_id = $1 AND student_id = $2
                """, course_id, student_id)
                
                return {"message": "Lab session cleared successfully", "course_id": course_id, "student_id": student_id}
        except Exception as e:
            logger.error(f"Error clearing lab session: {e}")
            raise HTTPException(status_code=500, detail="Failed to clear lab session")
    
    @app.post("/lab/chat")
    async def chat_with_trainer(request: ChatRequest):
        """Chat with AI expert trainer using persistent conversation history"""
        if request.course_id not in active_labs:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        lab = active_labs[request.course_id]
        
        # Load existing conversation history
        session_data = await load_lab_session(request.course_id, request.student_id)
        conversation_history = session_data.get('ai_conversation_history', [])
        
        # Update analytics
        lab_analytics[request.course_id]["ai_interactions"] += 1
        
        # Parse exercise references from user message
        exercise_references = parse_exercise_references(request.user_message)
        
        # Get exercise context based on user message
        exercise_context = await get_exercise_context(request.course_id, exercise_references)
        
        # Log exercise context for debugging
        if exercise_references:
            logger.info(f"Found exercise references: {exercise_references} for message: '{request.user_message}'")
        logger.debug(f"Exercise context length: {len(exercise_context)} characters")
        
        # Build conversation messages for Claude
        messages = []
        
        # Enhanced system context with exercise information
        system_message = f"""
        {lab['trainer_context']}
        
        Current Context:
        - Course: {request.context.get('course_title', 'Unknown')}
        - Student Progress: {request.context.get('student_progress', {})}
        - Current Exercise: {session_data.get('current_exercise', 'None')}
        
        Exercise Context:
        {exercise_context}
        
        Instructions for AI Assistant:
        1. You are an expert trainer for this course with full access to all exercises and course materials
        2. When students ask about specific labs or exercises (e.g., "lab 1", "exercise 2"), refer to the Exercise Context above
        3. Provide helpful hints without giving away the complete solution
        4. Focus on guiding students to discover the answer themselves
        5. Reference specific exercise instructions, learning objectives, and starter code when relevant
        6. If a student is stuck, break down the problem into smaller steps
        7. Always maintain an encouraging and educational tone
        8. Use the conversation history to provide personalized guidance
        
        You have access to all course exercises and can help with any questions about labs, exercises, or course content.
        """
        
        # Add conversation history
        for msg in conversation_history:
            if msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current user message
        messages.append({
            "role": "user", 
            "content": request.user_message
        })
        
        try:
            # Call Claude API with conversation history and enhanced context
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,  # Increased for detailed exercise help
                system=system_message,
                messages=messages
            )
            
            trainer_response = response.content[0].text
            
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": request.user_message,
                "timestamp": datetime.now().isoformat()
            })
            conversation_history.append({
                "role": "assistant", 
                "content": trainer_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save updated session with conversation history
            await save_lab_session(
                request.course_id,
                request.student_id,
                session_data.get('session_data', {}),
                conversation_history,
                session_data.get('code_files', {}),
                session_data.get('current_exercise'),
                session_data.get('progress_data', {})
            )
            
            # Check if response suggests an exercise
            exercise = None
            if "exercise" in trainer_response.lower() or "try this" in trainer_response.lower():
                exercise = {
                    "id": str(uuid.uuid4()),
                    "title": "Suggested Exercise",
                    "description": "Based on our conversation",
                    "content": "Follow the trainer's guidance above"
                }
            
            return {
                "response": trainer_response,
                "exercise": exercise,
                "progress_update": None,
                "conversation_length": len(conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "response": "I'm having trouble connecting right now. Please try again in a moment.",
                "exercise": None,
                "progress_update": None
            }
    
    @app.post("/lab/generate-exercise")
    async def generate_dynamic_exercise(request: DynamicExerciseRequest):
        """Generate dynamic exercise based on student progress"""
        if request.course_id not in active_labs:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        lab = active_labs[request.course_id]
        lab_analytics[request.course_id]["dynamic_exercises"] += 1
        
        exercise_prompt = f"""
        {lab['trainer_context']}
        
        Generate a hands-on exercise for a student with this progress:
        - Completed exercises: {request.student_progress.get('completed_exercises', 0)}
        - Current level: {request.student_progress.get('current_level', 'beginner')}
        - Knowledge areas: {request.student_progress.get('knowledge_areas', [])}
        
        Course: {request.context.get('course_title', '')}
        Category: {request.context.get('course_category', '')}
        
        Create an exercise that:
        1. Builds on previous knowledge
        2. Introduces new concepts appropriately
        3. Includes clear instructions
        4. Has measurable outcomes
        
        Return as JSON with: title, description, instructions, expected_outcome, difficulty
        """
        
        try:
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=400,
                messages=[
                    {"role": "user", "content": exercise_prompt}
                ]
            )
            
            # Try to parse as JSON, fallback to structured response
            try:
                exercise_data = json.loads(response.content[0].text)
            except:
                exercise_data = {
                    "id": str(uuid.uuid4()),
                    "title": "Dynamic Exercise",
                    "description": response.content[0].text,
                    "instructions": ["Follow the description above"],
                    "expected_outcome": "Complete the exercise as described",
                    "difficulty": request.student_progress.get('current_level', 'beginner')
                }
            
            exercise_data["id"] = str(uuid.uuid4())
            return {"exercise": exercise_data}
            
        except Exception as e:
            logger.error(f"Exercise generation error: {e}")
            return {
                "exercise": {
                    "id": str(uuid.uuid4()),
                    "title": "Practice Exercise",
                    "description": "Continue practicing the concepts we've been discussing.",
                    "instructions": ["Review previous material", "Try applying concepts in new ways"],
                    "expected_outcome": "Better understanding of the topic",
                    "difficulty": "beginner"
                }
            }
    
    @app.post("/lab/generate-quiz")
    async def generate_adaptive_quiz(request: QuizRequest):
        """Generate adaptive quiz based on student progress"""
        if request.course_id not in active_labs:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        lab = active_labs[request.course_id]
        lab_analytics[request.course_id]["adaptive_quizzes"] += 1
        
        quiz_prompt = f"""
        {lab['trainer_context']}
        
        Create an adaptive quiz for a student with this progress:
        - Completed exercises: {request.student_progress.get('completed_exercises', 0)}
        - Current level: {request.student_progress.get('current_level', 'beginner')}
        - Knowledge areas covered: {request.student_progress.get('knowledge_areas', [])}
        
        Course: {request.context.get('course_title', '')}
        Category: {request.context.get('course_category', '')}
        
        ADAPTIVE QUIZ REQUIREMENTS:
        1. Generate 3-5 multiple choice questions appropriate for their current level
        2. Test understanding of material they've actually covered in exercises
        3. Include scenario-based questions that apply concepts to real situations
        4. Provide realistic distractors that represent common misconceptions
        5. Include detailed explanations that help reinforce learning
        6. Adjust question difficulty based on student's demonstrated level
        
        QUESTION GUIDELINES:
        - For beginners: Focus on basic concepts and definitions with clear examples
        - For intermediate: Include application questions requiring concept usage
        - For advanced: Present complex scenarios requiring analysis and synthesis
        - Always relate questions to practical, real-world applications
        - Ensure questions test understanding, not just memorization
        
        Return as JSON with this structure:
        {{
            "title": "Adaptive Knowledge Check",
            "description": "Personalized quiz based on your progress and current level",
            "questions": [
                {{
                    "question": "Clear, specific question based on covered material",
                    "question_type": "scenario|definition|application|analysis",
                    "options": ["Correct answer", "Plausible distractor 1", "Plausible distractor 2", "Plausible distractor 3"],
                    "correct_answer": 0,
                    "explanation": "Detailed explanation of correct answer and why others are wrong",
                    "difficulty": "beginner|intermediate|advanced",
                    "topic_tested": "Specific topic from their progress"
                }}
            ]
        }}
        """
        
        try:
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[
                    {"role": "user", "content": quiz_prompt}
                ]
            )
            
            try:
                quiz_data = json.loads(response.content[0].text)
            except:
                # Fallback quiz
                quiz_data = {
                    "title": "Knowledge Check",
                    "description": "Test your understanding of recent topics",
                    "questions": [
                        {
                            "question": "What have you learned so far in this course?",
                            "options": ["A lot", "Some things", "Basic concepts", "Still learning"],
                            "correct_answer": 0
                        }
                    ]
                }
            
            quiz_data["id"] = str(uuid.uuid4())
            quiz_data["duration"] = len(quiz_data.get("questions", [])) * 2  # 2 min per question
            quiz_data["difficulty"] = request.student_progress.get('current_level', 'beginner')
            
            # Store quiz
            if request.course_id not in course_quizzes:
                course_quizzes[request.course_id] = []
            course_quizzes[request.course_id].append(quiz_data)
            
            return {"quiz": quiz_data}
            
        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            return {
                "quiz": {
                    "id": str(uuid.uuid4()),
                    "title": "Quick Review",
                    "description": "Review what you've learned",
                    "questions": [
                        {
                            "question": "How would you rate your understanding so far?",
                            "options": ["Excellent", "Good", "Fair", "Need more practice"],
                            "correct_answer": 0
                        }
                    ],
                    "duration": 5,
                    "difficulty": "beginner"
                }
            }
    
    @app.post("/lab/generate-custom")
    async def generate_custom_lab(request: dict):
        """Generate custom lab based on instructor description"""
        try:
            course_id = request.get('course_id')
            lab_description = request.get('description', '')
            course_context = request.get('course_context', {})
            
            if not course_id or not lab_description:
                raise HTTPException(status_code=400, detail="course_id and description are required")
            
            # Get syllabus context if available
            syllabus = await load_syllabus_from_db(course_id)
            if not syllabus:
                syllabus = course_syllabi.get(course_id, {})
            
            # Generate lab exercise using AI
            custom_lab_prompt = f"""
            You are an expert educator creating a custom lab exercise based on instructor specifications.
            
            Course Context:
            {json.dumps(course_context, indent=2)}
            
            Course Syllabus (for reference):
            {json.dumps(syllabus, indent=2)}
            
            Instructor Lab Description:
            {lab_description}
            
            REQUIREMENTS:
            1. Create a comprehensive lab exercise that fulfills the instructor's description
            2. Make it engaging, fun, and interactive
            3. Include specific step-by-step instructions
            4. Add practical examples and sample data
            5. Include expected outcomes and troubleshooting tips
            6. Match the difficulty level to the course content
            7. Use real-world scenarios and interesting contexts
            8. Include clear learning objectives
            
            Return ONLY valid JSON with this structure:
            {{
                "id": "custom_lab_<timestamp>",
                "title": "Descriptive Lab Title",
                "description": "Clear description of what students will accomplish",
                "type": "custom",
                "difficulty": "beginner|intermediate|advanced",
                "module_number": 0,
                "topics_covered": ["topic1", "topic2"],
                "instructions": "Detailed step-by-step instructions",
                "expected_output": "What students should see as results",
                "hints": "Helpful hints for common issues",
                "sample_data": "Sample data or starting materials",
                "learning_objectives": ["objective1", "objective2"],
                "estimated_duration": "30-45 minutes"
            }}
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": custom_lab_prompt}
                ]
            )
            
            # Parse the response
            try:
                lab_exercise = json.loads(response.content[0].text)
                # Add unique ID with timestamp
                lab_exercise['id'] = f"custom_lab_{int(time.time())}"
                
                # Add to exercises for this course
                if course_id not in exercises:
                    exercises[course_id] = []
                exercises[course_id].append(lab_exercise)
                
                # Save to database
                await save_exercises_to_db(course_id, exercises[course_id])
                
                logger.info(f"Generated custom lab for course {course_id}: {lab_exercise.get('title', 'Untitled')}")
                
                return {
                    "success": True,
                    "lab_exercise": lab_exercise,
                    "message": "Custom lab generated successfully"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse custom lab JSON: {e}")
                return {
                    "success": False,
                    "message": "Failed to generate custom lab - invalid AI response"
                }
                
        except Exception as e:
            logger.error(f"Error generating custom lab: {e}")
            return {
                "success": False,
                "message": f"Error generating custom lab: {str(e)}"
            }
    
    @app.post("/lab/refresh-exercises")
    async def refresh_lab_exercises(request: dict):
        """Refresh exercises for an existing lab setup"""
        try:
            course_id = request.get('course_id')
            
            if not course_id:
                raise HTTPException(status_code=400, detail="course_id is required")
            
            # Get syllabus from database
            syllabus = await load_syllabus_from_db(course_id)
            if not syllabus:
                # Try to get from memory if not in database
                syllabus = course_syllabi.get(course_id)
            
            if not syllabus:
                return {
                    "success": False,
                    "message": "No syllabus found for this course. Please generate a syllabus first."
                }
            
            logger.info(f"Refreshing exercises for course: {course_id}")
            
            # Generate new exercises from syllabus
            exercises_data = generate_exercises_from_syllabus_sync(course_id, syllabus)
            
            # Store exercises in memory and database
            exercises[course_id] = exercises_data
            
            # Save exercises to database
            await save_exercises_to_db(course_id, exercises_data)
            
            # Update active lab if it exists
            if course_id in active_labs:
                active_labs[course_id]["exercises"] = exercises_data
                logger.info(f"Updated active lab with {len(exercises_data)} refreshed exercises")
            
            logger.info(f"Successfully refreshed {len(exercises_data)} exercises for course {course_id}")
            
            return {
                "success": True,
                "exercises": exercises_data,
                "message": f"Successfully refreshed {len(exercises_data)} exercises"
            }
            
        except Exception as e:
            logger.error(f"Error refreshing lab exercises: {e}")
            return {
                "success": False,
                "message": f"Error refreshing exercises: {str(e)}"
            }
    
    @app.get("/quizzes/{course_id}")
    async def get_course_quizzes(course_id: str):
        """Get all quizzes for a course"""
        if course_id not in course_quizzes:
            return {"course_id": course_id, "quizzes": []}
        return {"course_id": course_id, "quizzes": course_quizzes[course_id]}
    
    @app.post("/generate-quizzes/{course_id}")
    async def generate_course_quizzes(course_id: str):
        """Generate quizzes for a course based on its syllabus"""
        try:
            # Get course syllabus
            syllabus_data = await load_syllabus_from_db(course_id)
            if not syllabus_data:
                # Try to get from course management service
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"http://localhost:8004/courses/{course_id}")
                        if response.status_code == 200:
                            course_data = response.json()
                            syllabus_data = course_data.get('syllabus', {})
                        else:
                            raise HTTPException(status_code=404, detail="Course not found")
                except:
                    raise HTTPException(status_code=404, detail="Course syllabus not found")
            
            # Generate quizzes using the improved prompt
            generated_quizzes = generate_quizzes_from_syllabus_sync(course_id, syllabus_data)
            
            # Store generated quizzes
            course_quizzes[course_id] = generated_quizzes
            
            # Also save to database
            await save_quizzes_to_db(course_id, generated_quizzes)
            
            logger.info(f"Generated {len(generated_quizzes)} quizzes for course {course_id}")
            
            return {
                "course_id": course_id,
                "quizzes": generated_quizzes,
                "count": len(generated_quizzes)
            }
            
        except Exception as e:
            logger.error(f"Error generating quizzes for course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate quizzes")
    
    @app.delete("/quizzes/{quiz_id}")
    async def delete_quiz(quiz_id: str):
        """Delete a specific quiz"""
        try:
            # Find the quiz across all courses
            course_id = None
            quiz_index = None
            
            for cid, quizzes in course_quizzes.items():
                for i, quiz in enumerate(quizzes):
                    if quiz.get('id') == quiz_id:
                        course_id = cid
                        quiz_index = i
                        break
                if course_id:
                    break
            
            if not course_id or quiz_index is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            # Remove quiz from memory
            del course_quizzes[course_id][quiz_index]
            
            # Also remove from database
            await delete_quiz_from_db(quiz_id)
            
            logger.info(f"Deleted quiz {quiz_id} from course {course_id}")
            
            return {"message": "Quiz deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete quiz")
    
    @app.get("/lab/analytics/{course_id}")
    async def get_lab_analytics(course_id: str):
        """Get lab environment analytics"""
        if course_id not in lab_analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")
        return lab_analytics[course_id]
    
    @app.post("/ai-assistant/help")
    async def ai_assistant_help(request: Dict):
        logger.info(f"AI Assistant help requested for: {request.get('question', 'No question')}")
        
        # Simple AI assistant simulation
        question = request.get("question", "")
        course_id = request.get("course_id", "")
        
        response = generate_ai_response(question, course_id)
        
        return {"response": response, "timestamp": datetime.now()}
    
    def generate_course_slides_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate slides based on approved syllabus modules and topics"""
        try:
            # Build comprehensive prompt using syllabus structure
            slides_prompt = f"""
            You are an expert educator creating actual teaching content. Create detailed, educational slides for this course syllabus.

            Course Overview: {syllabus['overview']}
            
            Syllabus Modules:
            {json.dumps(syllabus['modules'], indent=2)}
            
            ABSOLUTE REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTION:
            1. ALL slides MUST use bullet points (•) - NO paragraph text or "wall of text"
            2. EVERY slide must have a title and bullet points - no exceptions
            3. NEVER write introductory, meta-commentary, or overview language
            4. NEVER use phrases like "Introduction to...", "We'll explore...", "This topic is...", "Learn about..."
            5. EVERY bullet point MUST teach specific, concrete information
            6. For technical topics: Include actual commands, syntax, parameters, and examples
            7. For business topics: Include specific methods, tools, frameworks, and real scenarios
            8. NO descriptions of what will be taught - only teach the actual content
            
            BANNED PHRASES (DO NOT USE ANY OF THESE):
            - "Introduction to..."
            - "We'll explore..."
            - "This topic is fundamental..."
            - "Learn about..."
            - "Understanding..."
            - "Overview of..."
            - "Key concepts..."
            - "Important aspects..."
            - "Real-world applications..."
            - "Practical examples..."
            
            REQUIRED APPROACH:
            - Start immediately with specific facts, commands, or procedures
            - Use actual syntax, commands, and concrete examples
            - Provide step-by-step instructions where applicable
            - Give specific parameter values and real-world examples
            
            GOOD Linux Commands Example:
            "• ls command lists directory contents: ls -la shows detailed file info
            • cd command changes directories: cd /home/user navigates to user directory  
            • cp copies files: cp file1.txt backup.txt creates a copy
            • rm deletes files: rm file.txt removes the file permanently
            • chmod changes permissions: chmod 755 file.txt gives read/write/execute to owner"
            
            BAD Example (NEVER DO THIS):
            "• Introduction to Essential Linux commands for file and directory management
            • This topic is fundamental to understanding Linux Command Line Essentials
            • We'll explore key concepts, practical applications, and real-world examples"
            
            For the topic "Essential Linux commands for file and directory management", write:
            "• ls lists files: ls shows filenames, ls -l shows details, ls -la includes hidden files
            • cd changes directory: cd /home goes to home, cd .. goes up one level
            • pwd shows current directory path: /home/username/documents
            • mkdir creates directories: mkdir newfolder creates a new folder
            • cp copies files: cp source.txt destination.txt duplicates the file"
            
            Generate slides covering each module and topic with ONLY actual educational content.
            Return ONLY valid JSON array with this structure:
            [
                {{
                    "id": "slide_1",
                    "title": "Actual Topic Title",
                    "content": "• Specific fact with actual command/syntax/example\\n• Another concrete fact with details\\n• Third specific point with real information\\n• Fourth practical detail with exact syntax",
                    "slide_type": "content", 
                    "order": 1,
                    "module_number": 1
                }}
            ]
            
            CRITICAL FORMATTING REQUIREMENT:
            - Each bullet point (•) MUST be followed by \\n (newline character)
            - The content field must use \\n between bullet points for proper display
            - Example: "• First point\\n• Second point\\n• Third point"
            - NEVER put bullet points on the same line
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": slides_prompt}
                ]
            )
            
            try:
                slides_data = json.loads(response.content[0].text)
                
                # Post-process slides to ensure proper formatting
                formatted_slides = []
                for slide in slides_data:
                    formatted_slide = slide.copy()
                    if 'content' in formatted_slide and formatted_slide['content']:
                        content = formatted_slide['content']
                        
                        # Convert paragraph text to bullet points if no bullets exist
                        if '•' not in content and content.strip():
                            # Split long content into bullet points
                            sentences = content.split('. ')
                            if len(sentences) > 1:
                                content = '\n'.join([f"• {sentence.strip()}" for sentence in sentences if sentence.strip()])
                                if not content.endswith('.'):
                                    content = content.rstrip() + '.'
                            else:
                                content = f"• {content}"
                        
                        # Ensure bullet points have proper newlines
                        content = content.replace('• ', '\n• ').strip()
                        # Remove any double newlines that might have been created
                        content = content.replace('\n\n•', '\n•')
                        # Ensure content starts with bullet point (remove leading newline if present)
                        if content.startswith('\n'):
                            content = content[1:]
                        
                        formatted_slide['content'] = content
                    formatted_slides.append(formatted_slide)
                
                logger.info(f"Generated {len(formatted_slides)} slides from syllabus")
                return formatted_slides
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != -1:
                    try:
                        slides_data = json.loads(text[start:end])
                        
                        # Post-process slides to ensure proper formatting
                        formatted_slides = []
                        for slide in slides_data:
                            formatted_slide = slide.copy()
                            if 'content' in formatted_slide and formatted_slide['content']:
                                content = formatted_slide['content']
                                
                                # Convert paragraph text to bullet points if no bullets exist
                                if '•' not in content and content.strip():
                                    # Split long content into bullet points
                                    sentences = content.split('. ')
                                    if len(sentences) > 1:
                                        content = '\n'.join([f"• {sentence.strip()}" for sentence in sentences if sentence.strip()])
                                        if not content.endswith('.'):
                                            content = content.rstrip() + '.'
                                    else:
                                        content = f"• {content}"
                                
                                # Ensure bullet points have proper newlines
                                content = content.replace('• ', '\n• ').strip()
                                # Remove any double newlines that might have been created
                                content = content.replace('\n\n•', '\n•')
                                # Ensure content starts with bullet point (remove leading newline if present)
                                if content.startswith('\n'):
                                    content = content[1:]
                                
                                formatted_slide['content'] = content
                            formatted_slides.append(formatted_slide)
                        
                        return formatted_slides
                    except:
                        pass
                
                # Fallback: generate slides manually from syllabus
                return generate_slides_manually_from_syllabus(syllabus)
                
        except Exception as e:
            logger.error(f"Error generating slides from syllabus: {e}")
            return generate_slides_manually_from_syllabus(syllabus)
    
    def generate_slides_manually_from_syllabus(syllabus: dict) -> List[Dict]:
        """Fallback: Generate slides manually from syllabus structure"""
        slides = []
        slide_order = 1
        
        # Title slide with bullet points
        overview_bullets = f"• {syllabus['overview']}" if syllabus.get('overview') else "• Course overview and introduction"
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Course Introduction",
            "content": overview_bullets,
            "slide_type": "content",
            "order": slide_order,
            "module_number": None
        })
        slide_order += 1
        
        # Objectives slide with bullet points
        objectives_bullets = '\n'.join([f"• {obj}" for obj in syllabus.get("objectives", ["Learn key concepts", "Apply practical skills", "Complete course successfully"])])
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Learning Objectives",
            "content": objectives_bullets,
            "slide_type": "content",
            "order": slide_order,
            "module_number": None
        })
        slide_order += 1
        
        # Module slides
        for module in syllabus["modules"]:
            # Module introduction slide with actual topics listed as bullet points
            topics_bullets = '\n'.join([f"• {topic}" for topic in module["topics"]])
            slides.append({
                "id": f"slide_{slide_order}",
                "title": module["title"],
                "content": topics_bullets,
                "slide_type": "content",
                "order": slide_order,
                "module_number": module["module_number"]
            })
            slide_order += 1
            
            # Topic slides (2 slides per topic)
            for topic in module["topics"]:
                # Generate actual educational content for each topic
                if "python" in topic.lower() and "variable" in topic.lower():
                    content = "• Variables store data using assignment operator (=): name = 'John', age = 25\n• Python uses dynamic typing - no need to declare variable types\n• Variable names must start with letter or underscore, can contain letters, numbers, underscores\n• Use descriptive names: student_count instead of sc"
                elif "python" in topic.lower() and "data type" in topic.lower():
                    content = "• Integers: whole numbers like 42, -17, 0\n• Floats: decimal numbers like 3.14, -2.5, 1.0\n• Strings: text in quotes like 'hello', \"Python\", '''multi-line'''\n• Booleans: True or False values for logical operations\n• Check type with type() function: type(42) returns <class 'int'>"
                elif "python" in topic.lower() and ("loop" in topic.lower() or "conditional" in topic.lower()):
                    content = "• if statement: if age >= 18: print('Adult')\n• elif for multiple conditions: elif age >= 13: print('Teen')\n• else for default case: else: print('Child')\n• for loop iterates over sequences: for i in range(5): print(i)\n• while loop repeats while condition true: while x < 10: x += 1"
                elif "function" in topic.lower():
                    content = "• Define function with def keyword: def greet(name): return f'Hello {name}'\n• Call function: result = greet('Alice')\n• Parameters are inputs: def add(x, y): return x + y\n• Return statement sends value back: return x * 2\n• Functions promote code reuse and organization"
                elif "class" in topic.lower() or "object" in topic.lower():
                    content = "• Class definition: class Person: def __init__(self, name): self.name = name\n• Create object: person = Person('John')\n• Methods are functions in classes: def speak(self): return f'{self.name} says hello'\n• Attributes store object data: person.name, person.age\n• Constructor __init__ initializes new objects"
                else:
                    # Generate more specific content based on topic keywords
                    topic_lower = topic.lower()
                    if any(word in topic_lower for word in ['command', 'linux', 'bash', 'terminal']):
                        content = f"• {topic} syntax and basic usage\n• Common parameters and options available\n• Example commands with real file/directory names\n• Output interpretation and error handling\n• Practical use cases in daily system administration"
                    elif any(word in topic_lower for word in ['file', 'directory', 'folder']):
                        content = f"• File operations: create, copy, move, delete using touch, cp, mv, rm\n• Directory navigation: ls, cd, pwd commands\n• File permissions: chmod, chown commands with numeric values\n• File content viewing: cat, less, head, tail commands\n• Wildcards and pattern matching: *.txt, file?, [abc]*.log"
                    elif any(word in topic_lower for word in ['database', 'sql', 'query']):
                        content = f"• SQL syntax: SELECT column FROM table WHERE condition\n• Data manipulation: INSERT, UPDATE, DELETE statements\n• Table relationships: JOIN operations and foreign keys\n• Database design: normalization and primary keys\n• Query optimization and indexing strategies"
                    elif any(word in topic_lower for word in ['network', 'protocol', 'tcp', 'ip']):
                        content = f"• Network protocols: TCP/IP, HTTP, HTTPS, DNS fundamentals\n• IP addressing: IPv4 classes, subnetting, CIDR notation\n• Port numbers: well-known ports (80, 443, 22, 21)\n• Network troubleshooting: ping, traceroute, netstat commands\n• Network security: firewalls, VPNs, SSL/TLS encryption"
                    else:
                        # Last resort - still try to be more specific
                        content = f"• Key terminology and definitions for {topic}\n• Step-by-step procedures and methodologies\n• Practical examples with specific parameters\n• Common tools and techniques used\n• Best practices and troubleshooting approaches"
                
                slides.append({
                    "id": f"slide_{slide_order}",
                    "title": f"{topic}",
                    "content": content,
                    "slide_type": "content",
                    "order": slide_order,
                    "module_number": module["module_number"]
                })
                slide_order += 1
        
        # Summary slide
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Course Summary",
            "content": f"We've covered {len(syllabus['modules'])} modules with comprehensive topics. You now have the knowledge to {syllabus['objectives'][0].lower()} and apply these skills in real-world scenarios.",
            "slide_type": "content",
            "order": slide_order,
            "module_number": None
        })
        
        return slides
    
    def parse_slides_from_text(text: str, title: str, topic: str) -> List[Dict]:
        """Parse slides from Claude text response"""
        slides = []
        lines = text.split('\n')
        current_slide = None
        slide_count = 1
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or 'slide' in line.lower():
                if current_slide:
                    slides.append(current_slide)
                current_slide = {
                    "id": f"slide_{slide_count}",
                    "title": line.replace('#', '').strip(),
                    "content": "",
                    "slide_type": "content" if slide_count > 1 else "title",
                    "order": slide_count
                }
                slide_count += 1
            elif current_slide and line:
                current_slide["content"] += line + " "
        
        if current_slide:
            slides.append(current_slide)
            
        return slides if slides else generate_fallback_slides(title, "", topic)
    
    def generate_fallback_slides(title: str, description: str, topic: str) -> List[Dict]:
        """Generate fallback slides when Claude fails"""
        return [
            {
                "id": "slide_1",
                "title": f"Introduction to {title}",
                "content": f"Welcome to {title}. {description} In this comprehensive course, we'll explore all aspects of {topic}.",
                "slide_type": "title",
                "order": 1
            },
            {
                "id": "slide_2",
                "title": "Course Overview",
                "content": f"This course covers fundamental concepts, practical applications, and advanced topics in {topic}. You'll gain hands-on experience and real-world knowledge.",
                "slide_type": "content",
                "order": 2
            },
            {
                "id": "slide_3",
                "title": "Key Concepts",
                "content": f"Understanding the core principles of {topic} is essential for success. We'll break down complex ideas into manageable concepts.",
                "slide_type": "content",
                "order": 3
            },
            {
                "id": "slide_4",
                "title": "Practical Applications",
                "content": f"Learn how {topic} is applied in real-world scenarios. We'll examine case studies and industry best practices.",
                "slide_type": "content",
                "order": 4
            },
            {
                "id": "slide_5",
                "title": "Hands-on Practice",
                "content": f"Practice makes perfect. You'll work through exercises and projects that reinforce your understanding of {topic}.",
                "slide_type": "content",
                "order": 5
            },
            {
                "id": "slide_6",
                "title": "Advanced Topics",
                "content": f"Dive deeper into advanced aspects of {topic}. Explore cutting-edge techniques and emerging trends.",
                "slide_type": "content",
                "order": 6
            },
            {
                "id": "slide_7",
                "title": "Best Practices",
                "content": f"Learn industry best practices and proven methodologies for working with {topic}. Avoid common pitfalls and optimize your approach.",
                "slide_type": "content",
                "order": 7
            },
            {
                "id": "slide_8",
                "title": "Summary and Next Steps",
                "content": f"Congratulations on completing this comprehensive overview of {topic}. Continue your learning journey with advanced courses and practical projects.",
                "slide_type": "content",
                "order": 8
            }
        ]
    
    def generate_lab_environment(name: str, description: str, env_type: str) -> Dict:
        """Generate lab environment configuration"""
        return {
            "virtual_machines": [
                {
                    "name": "ai-lab-vm",
                    "os": "Ubuntu 20.04",
                    "specs": {"cpu": 2, "memory": "4GB", "storage": "20GB"},
                    "software": ["wireshark", "nmap", "tcpdump", "iperf3"],
                    "network_config": {
                        "interfaces": ["eth0", "eth1"],
                        "ip_ranges": ["192.168.1.0/24", "10.0.0.0/24"]
                    }
                }
            ],
            "network_topology": {
                "subnets": ["192.168.1.0/24", "10.0.0.0/24"],
                "routers": ["router1", "router2"],
                "switches": ["switch1", "switch2"]
            },
            "ai_assistant": {
                "enabled": True,
                "context": env_type,
                "capabilities": ["explain_concepts", "debug_issues", "suggest_solutions", "generate_exercises", "adaptive_quizzes"]
            },
            "course_category": env_type,
            "status": "stopped",
            "exercises": ["Interactive coding challenges", "Hands-on labs", "Real-world scenarios", "Guided tutorials"]
        }
    
    def generate_course_exercises(topic: str, difficulty: str) -> List[Dict]:
        """Generate exercises for the course"""
        if "network" in topic.lower():
            return [
                {
                    "id": "ex_1",
                    "title": "Network Ping Test",
                    "description": "Use ping command to test connectivity between two network nodes",
                    "type": "hands_on",
                    "difficulty": difficulty,
                    "instructions": [
                        "Open terminal on the lab VM",
                        "Run: ping 8.8.8.8",
                        "Analyze the output and record latency",
                        "Try pinging your local gateway"
                    ],
                    "expected_output": "Successful ping responses with latency measurements",
                    "hints": ["Check your network configuration if ping fails", "Use -c option to limit ping count"]
                },
                {
                    "id": "ex_2",
                    "title": "Port Scanning with Nmap",
                    "description": "Discover open ports on a target system using nmap",
                    "type": "hands_on",
                    "difficulty": difficulty,
                    "instructions": [
                        "Run: nmap -sS 192.168.1.1",
                        "Identify open ports",
                        "Try a more comprehensive scan: nmap -A 192.168.1.1",
                        "Document your findings"
                    ],
                    "expected_output": "List of open ports and services",
                    "hints": ["Use sudo for SYN scan", "Be careful with aggressive scans"]
                },
                {
                    "id": "ex_3",
                    "title": "Packet Capture Analysis",
                    "description": "Capture and analyze network traffic using Wireshark",
                    "type": "hands_on",
                    "difficulty": difficulty,
                    "instructions": [
                        "Open Wireshark",
                        "Start capturing on eth0 interface",
                        "Generate some traffic (web browsing, ping)",
                        "Stop capture and analyze HTTP traffic"
                    ],
                    "expected_output": "Captured packets with HTTP requests and responses",
                    "hints": ["Use filters to focus on specific protocols", "Look for HTTP GET/POST requests"]
                }
            ]
        else:
            return [
                {
                    "id": "ex_1",
                    "title": f"Basic {topic} Exercise",
                    "description": f"Introduction exercise for {topic}",
                    "type": "hands_on",
                    "difficulty": difficulty,
                    "instructions": ["Complete the basic tasks"],
                    "expected_output": "Task completion",
                    "hints": ["Follow the course materials"]
                }
            ]
    
    def generate_ai_response(question: str, course_id: str) -> str:
        """Generate AI assistant response"""
        question_lower = question.lower()
        
        if "network" in question_lower or "tcp" in question_lower or "ip" in question_lower:
            if "tcp" in question_lower:
                return "TCP (Transmission Control Protocol) is a connection-oriented protocol that provides reliable data transmission. It ensures data integrity through error checking, flow control, and retransmission of lost packets."
            elif "ping" in question_lower:
                return "Ping is a network utility that tests connectivity between two network nodes. It sends ICMP Echo Request packets and measures the round-trip time. Use 'ping <hostname or IP>' to test connectivity."
            elif "port" in question_lower:
                return "Network ports are communication endpoints. Well-known ports include 80 (HTTP), 443 (HTTPS), 22 (SSH), 21 (FTP), and 25 (SMTP). Port numbers range from 0-65535."
            elif "wireshark" in question_lower:
                return "Wireshark is a network protocol analyzer that captures and displays network traffic in real-time. It's useful for troubleshooting network issues, analyzing security threats, and understanding network protocols."
            else:
                return "I'm your networking lab assistant! I can help you with network concepts, troubleshooting, and exercises. What specific networking topic would you like to explore?"
        else:
            return "I'm here to help with your course! Please ask me about the topics we're covering, and I'll do my best to explain concepts or help with exercises."
    
    # Syllabus endpoints
    @app.post("/syllabus/generate")
    async def generate_course_syllabus(request: SyllabusRequest):
        logger.info(f"Generating syllabus for course: {request.course_id}")
        
        try:
            # Build prompt from user metadata
            syllabus_prompt = f"""
            Create a comprehensive course syllabus for "{request.title}".
            
            Course Information:
            - Title: {request.title}
            - Description: {request.description}
            - Category: {request.category}
            - Difficulty Level: {request.difficulty_level}
            - Duration: {request.estimated_duration} hours
            
            CRITICAL REQUIREMENTS FOR MODULE CONTENT:
            1. Each module MUST have a detailed description explaining what the module covers
            2. Topics must be SPECIFIC and EXPLICIT - include actual commands, tools, concepts, and techniques
            3. For technical courses, list specific commands, file names, configurations, and practical examples
            4. For non-technical courses, include specific methods, frameworks, theories, and case studies
            
            EXAMPLES OF EXPLICIT CONTENT:
            - For Linux: "File system hierarchy (/bin, /etc, /home, /var), commands (ls, cd, pwd, cp, mv, rm, chmod, chown)"
            - For Python: "Data types (int, str, list, dict), control structures (if/else, for/while loops), functions (def, return, parameters)"
            - For Marketing: "Market segmentation strategies (demographic, psychographic, behavioral), tools (Google Analytics, Facebook Ads Manager)"
            
            Generate a detailed, professional syllabus that includes:
            1. Course overview and description
            2. Learning objectives (5-7 specific objectives)
            3. Prerequisites
            4. Module breakdown with DETAILED descriptions and SPECIFIC topics
            5. Assessment strategy
            6. Required resources
            
            Structure the response as JSON with this exact format:
            {{
                "overview": "Detailed course description and goals",
                "objectives": ["Specific learning objective 1", "Specific learning objective 2", ...],
                "prerequisites": ["Prerequisite 1", "Prerequisite 2", ...],
                "modules": [
                    {{
                        "module_number": 1,
                        "title": "Module Title",
                        "description": "Detailed explanation of what this module covers, its importance, and what students will learn",
                        "duration_hours": 2,
                        "topics": ["Specific topic with actual commands/tools/examples", "Another specific topic with details", "Concrete concept with practical application"],
                        "learning_outcomes": ["Specific measurable outcome", "Another specific outcome"],
                        "assessments": ["Specific assessment type", "Another assessment"]
                    }}
                ],
                "assessment_strategy": "How students will be evaluated",
                "resources": ["Resource 1", "Resource 2", ...]
            }}
            
            Make the content specific to {request.category} and {request.difficulty_level} level.
            Create {max(4, request.estimated_duration // 8)} modules with {request.estimated_duration // max(4, request.estimated_duration // 8)} hours each.
            ENSURE each module has explicit, detailed topics that include specific commands, tools, concepts, or examples relevant to the subject matter.
            """
            
            # Call Claude API
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": syllabus_prompt}
                ]
            )
            
            # Parse Claude's response
            try:
                syllabus_data = json.loads(response.content[0].text)
                logger.info(f"Claude generated syllabus successfully")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                # Extract content between first { and last }
                text = response.content[0].text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    try:
                        syllabus_data = json.loads(text[start:end])
                    except:
                        raise Exception("Could not parse Claude response")
                else:
                    raise Exception("No JSON found in Claude response")
            
            # Store in memory and database
            course_syllabi[request.course_id] = syllabus_data
            save_result = await save_syllabus_to_db(request.course_id, syllabus_data)
            if not save_result:
                logger.warning(f"Failed to save syllabus to database for course {request.course_id}")
            return {"course_id": request.course_id, "syllabus": syllabus_data}
            
        except Exception as e:
            logger.error(f"Error generating syllabus: {e}")
            # Fallback response
            fallback_syllabus = {
                "overview": f"Error generating syllabus for {request.title}. Please try again.",
                "objectives": ["Learn basic concepts", "Apply knowledge practically"],
                "prerequisites": ["Basic knowledge recommended"],
                "modules": [
                    {
                        "module_number": 1,
                        "title": "Introduction",
                        "duration_hours": request.estimated_duration // 2,
                        "topics": ["Basic concepts"],
                        "learning_outcomes": ["Understand fundamentals"],
                        "assessments": ["Quiz"]
                    }
                ],
                "assessment_strategy": "Quizzes and assignments",
                "resources": ["Course materials"]
            }
            return {"course_id": request.course_id, "syllabus": fallback_syllabus}
    
    
    @app.get("/syllabus/{course_id}")
    async def get_course_syllabus(course_id: str):
        # Try to load from database first
        syllabus_data = await load_syllabus_from_db(course_id)
        
        if not syllabus_data:
            # Fallback to in-memory storage
            if course_id in course_syllabi:
                syllabus_data = course_syllabi[course_id]
            else:
                raise HTTPException(status_code=404, detail="Syllabus not found for this course")
        
        return {"course_id": course_id, "syllabus": syllabus_data}
    
    @app.post("/content/generate-from-syllabus")
    async def generate_content_from_syllabus(request: dict):
        course_id = request.get('course_id')
        
        # Try to load syllabus from database first
        syllabus = await load_syllabus_from_db(course_id)
        
        if not syllabus:
            # Fallback to in-memory storage
            if course_id in course_syllabi:
                syllabus = course_syllabi[course_id]
            else:
                raise HTTPException(status_code=404, detail="Syllabus not found for this course")
        
        logger.info(f"Generating content from syllabus for course: {course_id}")
        
        try:
            # Generate slides based on syllabus
            slides = generate_course_slides_from_syllabus(course_id, syllabus)
            course_slides[course_id] = slides
            
            # Save slides to database
            await save_slides_to_db(course_id, slides)
            
            # Generate exercises based on syllabus
            exercises_data = generate_exercises_from_syllabus_sync(course_id, syllabus)
            logger.info(f"STORING exercises from syllabus for course_id: '{course_id}'")
            logger.info(f"Number of syllabus exercises generated: {len(exercises_data)}")
            logger.info(f"Syllabus exercise titles: {[ex.get('title', 'No title') for ex in exercises_data]}")
            
            exercises[course_id] = exercises_data
            
            logger.info(f"After storing syllabus exercises, dictionary keys: {list(exercises.keys())}")
            logger.info(f"Total exercises in dictionary: {sum(len(v) for v in exercises.values())}")
            
            # Generate quizzes based on syllabus
            quizzes_data = generate_quizzes_from_syllabus_sync(course_id, syllabus)
            course_quizzes[course_id] = quizzes_data
            
            # Create lab environment for this course
            lab_id = str(uuid.uuid4())
            lab_config = generate_lab_environment(
                f"AI Lab for {syllabus.get('overview', 'Course')[:50]}...", 
                f"Interactive lab environment for hands-on learning", 
                "ai_assisted"
            )
            
            lab_data = {
                "id": lab_id,
                "course_id": course_id,
                "name": f"AI Lab Environment",
                "description": f"Interactive learning environment with AI assistance",
                "environment_type": "ai_assisted",
                "config": lab_config,
                "exercises": exercises_data[:3],  # First 3 exercises for lab
                "status": "ready"
            }
            
            # Save to both memory (for backward compatibility) and database
            lab_environments[lab_id] = lab_data
            await save_lab_environment_to_db(course_id, lab_data)
            
            logger.info(f"Generated {len(slides)} slides, {len(exercises_data)} exercises, {len(quizzes_data)} quizzes, and lab environment")
            
            return {
                "course_id": course_id,
                "slides": slides,
                "exercises": exercises_data,
                "quizzes": quizzes_data,
                "lab": lab_data,
                "message": "All content generated successfully from syllabus"
            }
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            # Fallback to simple content
            slides = generate_fallback_slides("Course Content", syllabus.get('overview', ''), 'General')
            course_slides[course_id] = slides
            
            # Save fallback slides to database
            await save_slides_to_db(course_id, slides)
            
            exercises_data = [{"id": "ex1", "title": "Practice Exercise", "description": "Complete the learning activities", "type": "hands_on", "difficulty": "beginner"}]
            logger.info(f"STORING exercises from syllabus for course_id: '{course_id}'")
            logger.info(f"Number of syllabus exercises generated: {len(exercises_data)}")
            logger.info(f"Syllabus exercise titles: {[ex.get('title', 'No title') for ex in exercises_data]}")
            
            exercises[course_id] = exercises_data
            
            logger.info(f"After storing syllabus exercises, dictionary keys: {list(exercises.keys())}")
            logger.info(f"Total exercises in dictionary: {sum(len(v) for v in exercises.values())}")
            
            quizzes_data = [{"id": "quiz1", "title": "Knowledge Check", "description": "Test your understanding", "questions": [], "duration": 15}]
            course_quizzes[course_id] = quizzes_data
            
            return {"course_id": course_id, "slides": slides, "exercises": exercises_data, "quizzes": quizzes_data}
    
    @app.post("/content/regenerate")
    async def regenerate_content(request: dict):
        """Regenerate specific content types from existing syllabus with progress tracking"""
        course_id = request.get('course_id')
        content_types = request.get('content_types', ['slides', 'exercises', 'quizzes', 'lab'])
        
        # Try to load syllabus from database first
        syllabus = await load_syllabus_from_db(course_id)
        
        if not syllabus:
            # Fallback to in-memory storage
            if course_id in course_syllabi:
                syllabus = course_syllabi[course_id]
            else:
                raise HTTPException(status_code=404, detail="Syllabus not found for this course")
        
        logger.info(f"Regenerating content types {content_types} for course: {course_id}")
        
        result = {"course_id": course_id}
        progress = 0
        total_steps = len(content_types)
        
        try:
            # Generate slides if requested
            if 'slides' in content_types:
                progress += 1
                slides = generate_course_slides_from_syllabus(course_id, syllabus)
                course_slides[course_id] = slides
                await save_slides_to_db(course_id, slides)
                result['slides'] = slides
                result['progress'] = int((progress / total_steps) * 100)
            
            # Generate exercises if requested
            if 'exercises' in content_types:
                progress += 1
                exercises_data = generate_exercises_from_syllabus_sync(course_id, syllabus)
                exercises[course_id] = exercises_data
                result['exercises'] = exercises_data
                result['progress'] = int((progress / total_steps) * 100)
            
            # Generate quizzes if requested
            if 'quizzes' in content_types:
                progress += 1
                quizzes_data = generate_quizzes_from_syllabus_sync(course_id, syllabus)
                course_quizzes[course_id] = quizzes_data
                result['quizzes'] = quizzes_data
                result['progress'] = int((progress / total_steps) * 100)
            
            # Generate lab if requested
            if 'lab' in content_types:
                progress += 1
                lab_id = str(uuid.uuid4())
                lab_config = generate_lab_environment(
                    f"AI Lab for {syllabus.get('overview', 'Course')[:50]}...", 
                    f"Interactive lab environment for hands-on learning", 
                    "ai_assisted"
                )
                
                lab_data = {
                    "id": lab_id,
                    "course_id": course_id,
                    "name": f"Lab for {syllabus.get('overview', 'Course')[:50]}...",
                    "description": "Interactive lab environment for hands-on learning",
                    "environment_type": "ai_assisted",
                    "config": lab_config,
                    "exercises": exercises.get(course_id, [])
                }
                
                labs[course_id] = lab_data
                result['lab'] = lab_data
                result['progress'] = int((progress / total_steps) * 100)
            
            result['progress'] = 100
            result['message'] = f"Successfully regenerated {', '.join(content_types)} from existing syllabus"
            
        except Exception as e:
            logger.error(f"Content regeneration error: {e}")
            result['error'] = str(e)
            result['progress'] = int((progress / total_steps) * 100)
        
        return result
    
    @app.post("/courses/save")
    async def save_course_content(request: dict):
        course_id = request.get('course_id')
        logger.info(f"Saving course content for: {course_id}")
        # In real implementation, save to database
        return {"course_id": course_id, "message": "Course content saved successfully"}
    
    @app.post("/syllabus/refine")
    async def refine_syllabus(request: SyllabusFeedback):
        """Refine syllabus based on user feedback"""
        print(f"DEBUG: Refine syllabus endpoint called for course: {request.course_id}")
        logger.info(f"Refining syllabus for course: {request.course_id}")
        
        try:
            refinement_prompt = f"""
            You are refining a course syllabus based on instructor feedback. You MUST make changes to address the feedback.
            
            Current Syllabus:
            {json.dumps(request.current_syllabus, indent=2)}
            
            Instructor Feedback:
            {request.feedback}
            
            IMPORTANT: You must modify the syllabus to address the feedback. Do not return the original syllabus unchanged. If the feedback requests:
            - Adding modules: Insert them in the appropriate location
            - Reordering content: Adjust the sequence accordingly
            - Changing topics: Update the relevant sections
            - Adding prerequisites: Include them in the requirements
            - Modifying objectives: Update learning outcomes
            
            Maintain the same JSON structure but ensure all content reflects the requested changes. Be specific and detailed in your modifications.
            
            Return ONLY the complete updated syllabus as valid JSON. Do not include any explanation text, markdown, or additional comments. Return only the JSON object.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": refinement_prompt}
                ]
            )
            
            try:
                response_text = response.content[0].text
                logger.info(f"Claude refinement response: {response_text[:500]}...")
                
                # Try to extract JSON from the response
                try:
                    # First try direct JSON parsing
                    refined_syllabus = json.loads(response_text)
                except json.JSONDecodeError:
                    # If direct parsing fails, try to find JSON in the text
                    import re
                    json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        refined_syllabus = json.loads(json_str)
                    else:
                        logger.error("No JSON found in response")
                        refined_syllabus = request.current_syllabus
                
                logger.info(f"Successfully parsed refined syllabus")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.content[0].text}")
                refined_syllabus = request.current_syllabus
            except Exception as e:
                logger.error(f"Unexpected error parsing response: {e}")
                refined_syllabus = request.current_syllabus
            
            course_syllabi[request.course_id] = refined_syllabus
            save_result = await save_syllabus_to_db(request.course_id, refined_syllabus)
            if not save_result:
                logger.warning(f"Failed to save refined syllabus to database for course {request.course_id}")
            return {"course_id": request.course_id, "syllabus": refined_syllabus, "message": "Syllabus refined successfully"}
            
        except Exception as e:
            logger.error(f"Syllabus refinement error: {e}")
            return {"course_id": request.course_id, "syllabus": request.current_syllabus, "message": "Error refining syllabus"}
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    # ===== QUIZ API ENDPOINTS =====
    
    @app.post("/quiz/generate")
    async def generate_quiz_endpoint(request: QuizGenerationRequest):
        """Generate a new quiz for a topic on-demand"""
        try:
            # Convert request to dict
            topic_request = {
                "course_id": request.course_id,
                "topic": request.topic,
                "difficulty": request.difficulty,
                "question_count": request.question_count
            }
            
            # Generate quiz
            quiz = generate_quiz_for_topic(topic_request)
            
            # Save to database
            success = await save_quiz_to_db(quiz)
            
            if success:
                return {
                    "success": True,
                    "quiz_id": quiz["id"],
                    "quiz": quiz,
                    "message": f"Generated quiz '{quiz['title']}' with {len(quiz['questions'])} questions"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to save quiz to database"
                }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error generating quiz: {str(e)}"}
            )
    
    @app.get("/quiz/{quiz_id}")
    async def get_quiz_endpoint(quiz_id: str, user_type: str = "student"):
        """Get quiz by ID with different versions for students and instructors"""
        try:
            # Get quiz from database
            quiz = await get_quiz_from_db(quiz_id)
            
            if not quiz:
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Quiz not found"}
                )
            
            # Return different versions based on user type
            if user_type == "instructor":
                instructor_quiz = create_instructor_quiz_version(quiz)
                return {
                    "success": True,
                    "quiz": instructor_quiz,
                    "version": "instructor"
                }
            else:
                student_quiz = create_student_quiz_version(quiz)
                return {
                    "success": True,
                    "quiz": student_quiz,
                    "version": "student"
                }
            
        except Exception as e:
            logger.error(f"Error getting quiz: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error getting quiz: {str(e)}"}
            )
    
    @app.get("/quiz/course/{course_id}")
    async def get_course_quizzes_endpoint(course_id: str):
        """Get all quizzes for a course"""
        try:
            quizzes = await get_course_quizzes(course_id)
            
            return {
                "success": True,
                "quizzes": quizzes,
                "total_quizzes": len(quizzes),
                "course_id": course_id
            }
            
        except Exception as e:
            logger.error(f"Error getting course quizzes: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error getting course quizzes: {str(e)}"}
            )
    
    @app.get("/quiz/{quiz_id}")
    async def get_quiz_by_id_endpoint(quiz_id: str, user_type: str = "student"):
        """Get a specific quiz by ID"""
        try:
            # Search for quiz across all courses
            for course_id, quizzes in course_quizzes.items():
                for quiz in quizzes:
                    if quiz.get("id") == quiz_id:
                        if user_type == "instructor":
                            # Return instructor version with answers
                            return {
                                "success": True,
                                "quiz": quiz,
                                "version": "instructor"
                            }
                        else:
                            # Return student version without answers
                            student_quiz = create_student_quiz_version(quiz)
                            return {
                                "success": True,
                                "quiz": student_quiz,
                                "version": "student"
                            }
            
            return JSONResponse(
                status_code=404,
                content={"detail": f"Quiz {quiz_id} not found"}
            )
        except Exception as e:
            logger.error(f"Error getting quiz: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error getting quiz: {str(e)}"}
            )
    
    @app.post("/quiz/{quiz_id}/submit")
    async def submit_quiz_endpoint(quiz_id: str, submission: dict):
        """Submit quiz answers and get score"""
        try:
            # Get quiz to check answers
            quiz = await get_quiz_from_db(quiz_id)
            
            if not quiz:
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Quiz not found"}
                )
            
            # Extract correct answers
            correct_answers = [q["correct_answer"] for q in quiz["questions"]]
            student_answers = submission.get("answers", [])
            
            # Calculate score
            score = calculate_quiz_score(correct_answers, student_answers)
            
            # Save quiz attempt
            attempt = {
                "student_id": submission.get("student_id", "anonymous"),
                "quiz_id": quiz_id,
                "course_id": quiz["course_id"],
                "answers": student_answers,
                "score": score,
                "total_questions": len(quiz["questions"])
            }
            
            success = await save_quiz_attempt(attempt)
            
            return {
                "success": True,
                "score": score,
                "total_questions": len(quiz["questions"]),
                "correct_answers": sum(1 for i, ans in enumerate(student_answers) 
                                     if i < len(correct_answers) and ans == correct_answers[i]),
                "percentage": score,
                "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F",
                "attempt_saved": success
            }
            
        except Exception as e:
            logger.error(f"Error submitting quiz: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error submitting quiz: {str(e)}"}
            )
    
    @app.get("/quiz/analytics/{course_id}")
    async def get_quiz_analytics_endpoint(course_id: str):
        """Get quiz analytics for a course"""
        try:
            analytics = await get_course_grade_analytics(course_id)
            
            return {
                "success": True,
                "analytics": analytics,
                "course_id": course_id
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz analytics: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error getting quiz analytics: {str(e)}"}
            )
    
    @app.get("/quiz/student/{student_id}/history/{course_id}")
    async def get_student_quiz_history_endpoint(student_id: str, course_id: str):
        """Get student's quiz history for a course"""
        try:
            history = await get_student_quiz_history(student_id, course_id)
            
            return {
                "success": True,
                "history": history,
                "total_attempts": len(history),
                "student_id": student_id,
                "course_id": course_id
            }
            
        except Exception as e:
            logger.error(f"Error getting student quiz history: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error getting student quiz history: {str(e)}"}
            )
    
    @app.post("/quiz/generate-for-course")
    async def generate_course_quizzes_endpoint(request: dict):
        """Generate quizzes for all topics in a course"""
        try:
            course_id = request.get("course_id")
            if not course_id:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "course_id is required"}
                )
            
            # Get course materials
            syllabus = await load_syllabus_from_db(course_id)
            slides = course_slides.get(course_id, [])
            labs = exercises.get(course_id, [])
            
            # Detect course difficulty
            course_overview = syllabus.get('overview', '').lower() if syllabus else ''
            difficulty = "beginner"
            
            if "advanced" in course_overview or "expert" in course_overview:
                difficulty = "advanced"
            elif "intermediate" in course_overview or "prior experience" in course_overview:
                difficulty = "intermediate"
            elif "beginner" in course_overview or "no prior" in course_overview or "introduction" in course_overview:
                difficulty = "beginner"
            
            # Generate quizzes for all topics
            quizzes = generate_quizzes_for_course(course_id, syllabus, slides, labs, difficulty)
            
            # Save all quizzes to memory cache (database save disabled)
            course_quizzes[course_id] = quizzes
            saved_count = len(quizzes)
            
            # Also call save_quiz_to_db for each quiz for logging
            for quiz in quizzes:
                await save_quiz_to_db(quiz)
            
            return {
                "success": True,
                "generated_quizzes": len(quizzes),
                "saved_quizzes": saved_count,
                "quizzes": quizzes,
                "difficulty": difficulty
            }
            
        except Exception as e:
            logger.error(f"Error generating course quizzes: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error generating course quizzes: {str(e)}"}
            )
    
    # ===== QUIZ SYSTEM FUNCTIONS =====
    
    def generate_quiz_from_content(course_id: str, course_content: dict, difficulty: str) -> dict:
        """Generate quiz from course content including syllabus, slides, and labs"""
        try:
            # Extract content from course materials
            syllabus = course_content.get("syllabus", {})
            slides = course_content.get("slides", [])
            labs = course_content.get("labs", [])
            
            # Get first module/topic for quiz generation
            modules = syllabus.get("modules", [])
            if not modules:
                raise ValueError("No modules found in syllabus")
                
            topic = modules[0].get("title", "General Knowledge")
            
            # Build comprehensive quiz prompt
            quiz_prompt = f"""
            You are creating a comprehensive multiple-choice quiz for this course content.
            
            Course Difficulty: {difficulty.upper()}
            Topic: {topic}
            
            Syllabus Content:
            {json.dumps(syllabus, indent=2)}
            
            Slides Content:
            {json.dumps(slides, indent=2)}
            
            Lab Exercises:
            {json.dumps(labs, indent=2)}
            
            Create a quiz with EXACTLY 10 multiple choice questions that:
            1. Test understanding of key concepts from the syllabus
            2. Reference specific content from the slides
            3. Connect to practical skills from the labs
            4. Match the {difficulty} difficulty level
            5. Have exactly 4 answer options each
            6. Include explanations for correct answers
            
            Return ONLY a JSON object with this structure:
            {{
                "title": "Quiz Title",
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "questions": [
                    {{
                        "question": "What is...?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "Detailed explanation of why this is correct"
                    }}
                ]
            }}
            """
            
            # Generate quiz using LLM
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            
            quiz_data = json.loads(response.content[0].text)
            quiz_data["id"] = str(uuid.uuid4())
            quiz_data["course_id"] = course_id
            quiz_data["created_at"] = datetime.now()
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            # Return fallback quiz with minimum 10 questions
            fallback_questions = [
                {
                    "question": f"What is the main focus of {topic}?",
                    "options": [
                        "Core concepts and fundamentals",
                        "Advanced theoretical frameworks",
                        "Practical implementation details",
                        "Historical background information"
                    ],
                    "correct_answer": 0,
                    "explanation": f"The main focus is on core concepts and fundamentals of {topic}."
                }
            ]
            
            # Fill remaining questions to reach minimum 10
            while len(fallback_questions) < 10:
                question_num = len(fallback_questions) + 1
                fallback_questions.append({
                    "question": f"Question {question_num} about {topic}?",
                    "options": [
                        "Option A - Correct answer",
                        "Option B - Incorrect",
                        "Option C - Incorrect", 
                        "Option D - Incorrect"
                    ],
                    "correct_answer": 0,
                    "explanation": f"This is a generated question for {topic}.",
                    "topic_tested": topic,
                    "difficulty": difficulty
                })
            
            return {
                "id": str(uuid.uuid4()),
                "course_id": course_id,
                "title": f"{topic} Quiz",
                "topic": topic,
                "difficulty": difficulty,
                "questions": fallback_questions,
                "created_at": datetime.now()
            }
    
    def generate_quizzes_for_course(course_id: str, syllabus: dict, slides: list, labs: list, difficulty: str) -> list:
        """Generate one quiz per module/topic in the course"""
        quizzes = []
        modules = syllabus.get("modules", [])
        
        for module in modules:
            topic = module.get("title", "General Knowledge")
            
            # Create course content for this specific module
            module_content = {
                "syllabus": {"modules": [module]},
                "slides": [slide for slide in slides if topic.lower() in slide.get("title", "").lower()],
                "labs": [lab for lab in labs if topic.lower() in lab.get("title", "").lower()]
            }
            
            quiz = generate_quiz_from_content(course_id, module_content, difficulty)
            quiz["topic"] = topic
            quiz["title"] = f"{topic} Quiz"
            
            quizzes.append(quiz)
        
        return quizzes
    
    def create_student_quiz_version(instructor_quiz: dict) -> dict:
        """Create student version without correct answers"""
        student_quiz = instructor_quiz.copy()
        
        # Remove correct answers from questions
        for question in student_quiz["questions"]:
            if "correct_answer" in question:
                del question["correct_answer"]
            if "explanation" in question:
                del question["explanation"]
        
        return student_quiz
    
    def create_instructor_quiz_version(base_quiz: dict) -> dict:
        """Create instructor version with answers marked"""
        instructor_quiz = base_quiz.copy()
        
        # Mark correct answers for instructor view
        for question in instructor_quiz["questions"]:
            question["answer_marked"] = True
        
        return instructor_quiz
    
    def calculate_quiz_score(correct_answers: list, student_answers: list) -> float:
        """Calculate quiz score as percentage"""
        if not correct_answers or not student_answers:
            return 0.0
            
        correct_count = sum(1 for i, answer in enumerate(student_answers) 
                          if i < len(correct_answers) and answer == correct_answers[i])
        
        return (correct_count / len(correct_answers)) * 100
    
    def generate_quiz_for_topic(topic_request: dict) -> dict:
        """Generate quiz for specific topic on-demand"""
        try:
            # Get course materials for context
            course_id = topic_request["course_id"]
            topic = topic_request["topic"]
            difficulty = topic_request["difficulty"]
            question_count = topic_request.get("question_count", 12)
            
            # Create focused quiz prompt
            quiz_prompt = f"""
            Create a focused {difficulty} level quiz about "{topic}" with exactly {question_count} questions.
            
            Requirements:
            - All questions must be multiple choice with 4 options
            - Questions should test both conceptual understanding and practical application
            - Difficulty level: {difficulty.upper()}
            - Include explanations for correct answers
            
            Return ONLY a JSON object with this structure:
            {{
                "title": "{topic} Quiz",
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "questions": [
                    {{
                        "question": "Question text here?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "Why this answer is correct"
                    }}
                ]
            }}
            """
            
            response = claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            
            quiz_data = json.loads(response.content[0].text)
            quiz_data["id"] = str(uuid.uuid4())
            quiz_data["course_id"] = course_id
            quiz_data["created_at"] = datetime.now()
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating on-demand quiz: {e}")
            # Return fallback quiz
            return {
                "id": str(uuid.uuid4()),
                "course_id": course_id,
                "title": f"{topic} Quiz",
                "topic": topic,
                "difficulty": difficulty,
                "questions": [
                    {
                        "question": f"What is a key concept in {topic}?",
                        "options": [
                            "Fundamental principles",
                            "Advanced techniques",
                            "Historical context",
                            "Future applications"
                        ],
                        "correct_answer": 0,
                        "explanation": f"Fundamental principles are key to understanding {topic}."
                    }
                ],
                "created_at": datetime.now()
            }
    
    # Database functions for quizzes
    async def save_quiz_to_db(quiz: dict) -> bool:
        """Save quiz to database using the actual schema (quizzes -> lessons -> courses)"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
            
        try:
            async with db_manager.get_connection() as conn:
                # First, find or create a lesson for this quiz
                course_id = quiz.get('course_id')
                if not course_id:
                    logger.error("No course_id provided for quiz")
                    return False
                
                # Check if there's already a lesson for this course and quiz topic
                lesson_title = f"Quiz: {quiz.get('title', 'Untitled Quiz')}"
                lesson_id = None
                
                # Look for existing lesson
                existing_lesson = await conn.fetchrow("""
                    SELECT id FROM lessons 
                    WHERE course_id = $1 AND title = $2
                    LIMIT 1
                """, course_id, lesson_title)
                
                if existing_lesson:
                    lesson_id = existing_lesson['id']
                else:
                    # Create new lesson for this quiz
                    lesson_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO lessons (id, course_id, title, description, lesson_order, lesson_type, is_published, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, 
                    lesson_id,
                    course_id,
                    lesson_title,
                    f"Quiz lesson for: {quiz.get('title', '')}",
                    999,  # Put quizzes at the end
                    'quiz',
                    True,
                    datetime.now(),
                    datetime.now()
                    )
                    logger.info(f"Created lesson {lesson_id} for quiz {quiz['id']}")
                
                # Now insert the quiz with the lesson_id
                await conn.execute("""
                    INSERT INTO quizzes (id, lesson_id, title, description, time_limit_minutes, passing_score, max_attempts, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        time_limit_minutes = EXCLUDED.time_limit_minutes,
                        passing_score = EXCLUDED.passing_score,
                        max_attempts = EXCLUDED.max_attempts,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at
                """, 
                quiz['id'],
                lesson_id,
                quiz['title'],
                quiz.get('description', quiz.get('topic', '')),
                quiz.get('duration', 30),
                quiz.get('passing_score', 70),
                quiz.get('max_attempts', 3),
                True,
                datetime.now(),
                datetime.now()
                )
                
                # Insert quiz questions
                if quiz.get('questions'):
                    # First, clear existing questions
                    await conn.execute("DELETE FROM quiz_questions WHERE quiz_id = $1", quiz['id'])
                    
                    # Insert new questions
                    for i, question in enumerate(quiz['questions']):
                        await conn.execute("""
                            INSERT INTO quiz_questions (id, quiz_id, question_text, question_type, correct_answer, points, order_index, options, explanation)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        str(uuid.uuid4()),
                        quiz['id'],
                        question.get('question', ''),
                        'multiple_choice',
                        json.dumps(question.get('correct_answer', 0)),
                        question.get('points', 1),
                        i + 1,
                        json.dumps(question.get('options', [])),
                        question.get('explanation', '')
                        )
                
                logger.info(f"Quiz {quiz['id']} saved to database successfully with lesson {lesson_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving quiz to database: {e}")
            return False
    
    async def get_quiz_from_db(quiz_id: str) -> dict:
        """Retrieve quiz from database using actual schema"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return None
            
        try:
            async with db_manager.get_connection() as conn:
                # Get quiz with course_id via lessons table
                row = await conn.fetchrow("""
                    SELECT q.id, l.course_id, q.title, q.description, q.time_limit_minutes, 
                           q.passing_score, q.max_attempts, q.is_active, q.created_at, q.updated_at
                    FROM quizzes q
                    JOIN lessons l ON q.lesson_id = l.id
                    WHERE q.id = $1
                """, quiz_id)
                
                if row:
                    # Get quiz questions
                    questions = await conn.fetch("""
                        SELECT question_text, question_type, correct_answer, points, order_index, options, explanation
                        FROM quiz_questions
                        WHERE quiz_id = $1
                        ORDER BY order_index
                    """, quiz_id)
                    
                    # Convert questions to expected format
                    quiz_questions = []
                    for q in questions:
                        quiz_questions.append({
                            'question': q['question_text'],
                            'type': q['question_type'],
                            'correct_answer': json.loads(q['correct_answer']) if q['correct_answer'] else 0,
                            'points': q['points'],
                            'order': q['order_index'],
                            'options': json.loads(q['options']) if q['options'] else [],
                            'explanation': q['explanation'] if q['explanation'] else ''
                        })
                    
                    quiz = {
                        'id': str(row['id']),
                        'course_id': str(row['course_id']),
                        'title': row['title'],
                        'description': row['description'],
                        'duration': row['time_limit_minutes'],
                        'passing_score': float(row['passing_score']) if row['passing_score'] else 70.0,
                        'max_attempts': row['max_attempts'],
                        'is_active': row['is_active'],
                        'questions': quiz_questions,
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    logger.info(f"Quiz {quiz_id} retrieved from database")
                    return quiz
                else:
                    logger.warning(f"Quiz {quiz_id} not found in database")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving quiz from database: {e}")
            # Fallback to memory cache
            for course_id, quizzes in course_quizzes.items():
                for quiz in quizzes:
                    if quiz.get('id') == quiz_id:
                        return quiz
            return None
    
    async def get_course_quizzes(course_id: str) -> list:
        """Get all quizzes for a course using actual schema"""
        global db_manager
        
        # First try to get from database
        if db_manager:
            try:
                async with db_manager.get_connection() as conn:
                    # Get quizzes via lessons table
                    rows = await conn.fetch("""
                        SELECT q.id, l.course_id, q.title, q.description, q.time_limit_minutes, 
                               q.passing_score, q.max_attempts, q.is_active, q.created_at, q.updated_at
                        FROM quizzes q
                        JOIN lessons l ON q.lesson_id = l.id
                        WHERE l.course_id = $1
                        ORDER BY q.created_at DESC
                    """, course_id)
                    
                    quizzes = []
                    for row in rows:
                        # Get questions for this quiz
                        questions = await conn.fetch("""
                            SELECT question_text, question_type, correct_answer, points, order_index, options, explanation
                            FROM quiz_questions
                            WHERE quiz_id = $1
                            ORDER BY order_index
                        """, row['id'])
                        
                        # Convert questions to expected format
                        quiz_questions = []
                        for q in questions:
                            quiz_questions.append({
                                'question': q['question_text'],
                                'type': q['question_type'],
                                'correct_answer': json.loads(q['correct_answer']) if q['correct_answer'] else 0,
                                'points': q['points'],
                                'order': q['order_index'],
                                'options': json.loads(q['options']) if q['options'] else [],
                                'explanation': q['explanation'] if q['explanation'] else ''
                            })
                        
                        quiz = {
                            'id': str(row['id']),
                            'course_id': str(row['course_id']),
                            'title': row['title'],
                            'description': row['description'],
                            'duration': row['time_limit_minutes'],
                            'passing_score': float(row['passing_score']) if row['passing_score'] else 70.0,
                            'max_attempts': row['max_attempts'],
                            'is_active': row['is_active'],
                            'questions': quiz_questions,
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at']
                        }
                        quizzes.append(quiz)
                    
                    if quizzes:
                        logger.info(f"Retrieved {len(quizzes)} quizzes from database for course {course_id}")
                        return quizzes
                        
            except Exception as e:
                logger.error(f"Error retrieving quizzes from database: {e}")
        
        # Fallback to memory cache
        if course_id in course_quizzes:
            logger.info(f"Retrieved {len(course_quizzes[course_id])} quizzes from memory cache for course {course_id}")
            return course_quizzes[course_id]
        else:
            logger.info(f"No quizzes found for course {course_id}")
            return []
    
    async def save_quiz_attempt(attempt: dict) -> bool:
        """Save student quiz attempt"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return False
        
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO quiz_attempts (id, student_id, quiz_id, course_id, answers, score, total_questions, completed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                str(uuid.uuid4()),
                attempt["student_id"],
                uuid.UUID(attempt["quiz_id"]),
                uuid.UUID(attempt["course_id"]),
                json.dumps(attempt["answers"]),
                attempt["score"],
                attempt["total_questions"],
                attempt.get("completed_at", datetime.now())
                )
                
                logger.info(f"Saved quiz attempt for student {attempt['student_id']}")
                return True
        except Exception as e:
            logger.error(f"Error saving quiz attempt: {e}")
            return False
    
    async def get_student_quiz_history(student_id: str, course_id: str) -> list:
        """Get student's quiz history for a course"""
        global db_manager
        if not db_manager:
            logger.error("Database manager not initialized")
            return []
        
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT qa.id, qa.student_id, qa.quiz_id, qa.course_id, qa.answers, 
                           qa.score, qa.total_questions, qa.completed_at, q.title, q.topic
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.id
                    WHERE qa.student_id = $1 AND qa.course_id = $2
                    ORDER BY qa.completed_at DESC
                """, student_id, uuid.UUID(course_id))
                
                return [
                    {
                        "id": str(row["id"]),
                        "student_id": row["student_id"],
                        "quiz_id": str(row["quiz_id"]),
                        "course_id": row["course_id"],
                        "answers": json.loads(row["answers"]),
                        "score": row["score"],
                        "total_questions": row["total_questions"],
                        "completed_at": row["completed_at"],
                        "quiz_title": row["title"],
                        "quiz_topic": row["topic"]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting student quiz history: {e}")
            return []
    
    async def get_course_grade_analytics(course_id: str) -> dict:
        """Get course-wide grade analytics"""
        global db_manager
        if not db_manager:
            logger.error("Database pool not initialized")
            return {}
        
        try:
            async with db_manager.get_connection() as conn:
                # Get overall analytics
                analytics_row = await conn.fetchrow("""
                    SELECT 
                        AVG(score) as average_score,
                        COUNT(*) as total_attempts,
                        COUNT(DISTINCT student_id) as unique_students
                    FROM quiz_attempts 
                    WHERE course_id = $1
                """, uuid.UUID(course_id))
                
                # Get score distribution
                distribution_rows = await conn.fetch("""
                    SELECT 
                        CASE 
                            WHEN score >= 90 THEN 'A'
                            WHEN score >= 80 THEN 'B'
                            WHEN score >= 70 THEN 'C'
                            WHEN score >= 60 THEN 'D'
                            ELSE 'F'
                        END as grade,
                        COUNT(*) as count
                    FROM quiz_attempts 
                    WHERE course_id = $1
                    GROUP BY grade
                """, uuid.UUID(course_id))
                
                # Get topic performance
                topic_rows = await conn.fetch("""
                    SELECT q.topic, AVG(qa.score) as avg_score, COUNT(*) as attempts
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.id
                    WHERE qa.course_id = $1
                    GROUP BY q.topic
                """, uuid.UUID(course_id))
                
                return {
                    "average_score": float(analytics_row["average_score"]) if analytics_row["average_score"] else 0,
                    "total_attempts": analytics_row["total_attempts"],
                    "unique_students": analytics_row["unique_students"],
                    "score_distribution": {row["grade"]: row["count"] for row in distribution_rows},
                    "topic_performance": {row["topic"]: {
                        "average_score": float(row["avg_score"]),
                        "attempts": row["attempts"]
                    } for row in topic_rows}
                }
        except Exception as e:
            logger.error(f"Error getting course grade analytics: {e}")
            return {}
    
    def get_quiz_pane_data(course_id: str) -> dict:
        """Get quiz pane data for dashboard"""
        # This will be implemented with async call in the actual endpoint
        return {
            "quizzes": [],
            "total_quizzes": 0,
            "course_id": course_id
        }
    
    def get_student_quiz_progress(student_id: str, course_id: str) -> dict:
        """Get student's quiz progress"""
        # This will be implemented with async call in the actual endpoint
        return {
            "completed_quizzes": 0,
            "total_quizzes": 0,
            "average_score": 0,
            "completion_percentage": 0
        }
    
    def generate_and_save_quiz_for_topic(topic_request: dict) -> str:
        """Generate and save quiz for topic"""
        quiz = generate_quiz_for_topic(topic_request)
        # This will be implemented with async save in the actual endpoint
        return quiz["id"]

    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()
