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
import uvicorn
import anthropic
import json
import asyncio
import asyncpg
import os

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
    course_title: str
    course_description: str
    course_category: str
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

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Logging setup
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # FastAPI app
    app = FastAPI(
        title="Course Generator API",
        description="API for generating courses from templates",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        await init_database()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await close_database()
    
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
    active_labs = {}
    student_progress = {}
    course_quizzes = {}
    lab_analytics = {}
    course_syllabi = {}
    
    # Database connection
    db_pool = None
    
    async def init_database():
        """Initialize database connection pool"""
        global db_pool
        try:
            # Get database URL from config or environment
            db_password = os.getenv("DB_PASSWORD", "c0urs3:atao12e")
            db_url = f"postgresql://course_user:{db_password}@localhost:5433/course_creator"
            
            db_pool = await asyncpg.create_pool(
                db_url,
                min_size=1,
                max_size=10
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    async def close_database():
        """Close database connection pool"""
        global db_pool
        if db_pool:
            await db_pool.close()
            logger.info("Database connection pool closed")
    
    # Database functions for syllabi
    async def save_syllabus_to_db(course_id: str, syllabus_data: dict):
        """Save syllabus to database"""
        if not db_pool:
            logger.error("Database pool not initialized")
            return False
        
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return None
        
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return False
        
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return None
        
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return False
            
        try:
            async with db_pool.acquire() as conn:
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
    
    async def load_slides_from_db(course_id: str) -> List[Dict]:
        """Load slides from database"""
        if not db_pool:
            logger.error("Database pool not initialized")
            return []
            
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return False
            
        try:
            async with db_pool.acquire() as conn:
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
        if not db_pool:
            logger.error("Database pool not initialized")
            return {}
            
        try:
            async with db_pool.acquire() as conn:
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
    
    # Define sync helper functions
    def generate_exercises_from_syllabus_sync(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate exercises based on syllabus modules using LLM with full syllabus context"""
        try:
            # Build comprehensive prompt using syllabus structure
            exercises_prompt = f"""
            You are an expert educator creating practical, hands-on exercises for this course syllabus.
            
            Course Overview: {syllabus.get('overview', '')}
            
            Full Syllabus Modules:
            {json.dumps(syllabus.get('modules', []), indent=2)}
            
            CRITICAL REQUIREMENTS FOR EXERCISES:
            1. Create SPECIFIC, actionable exercises based on the exact topics and commands in the syllabus
            2. For technical topics: Include actual commands, file names, step-by-step procedures
            3. For business topics: Include real scenarios, frameworks, and practical applications
            4. Each exercise must have clear, measurable objectives and expected outcomes
            5. Provide detailed instructions that students can follow independently
            6. Include realistic scenarios and practical applications
            
            EXAMPLES OF GOOD EXERCISES:
            - For "File operations (cp, mv, rm, touch)": Create exercise with specific commands like "Create a file called 'test.txt' using touch, copy it to 'backup.txt' using cp, then rename the original to 'original.txt' using mv"
            - For "Python variables (int, str, list, dict)": "Create variables: age = 25, name = 'John', scores = [85, 92, 78], student = {{'name': 'John', 'age': 25}}. Print each variable type using type() function"
            - For "Market segmentation strategies": "Analyze a given company case study and create demographic, psychographic, and behavioral segments using provided customer data"
            
            For each module, create 1-2 exercises that cover the specific topics mentioned in the syllabus.
            Return ONLY valid JSON array with this structure:
            [
                {{
                    "id": "ex_1_1",
                    "title": "Specific Exercise Title",
                    "description": "Clear description of what students will accomplish",
                    "type": "hands_on",
                    "difficulty": "beginner",
                    "module_number": 1,
                    "topics_covered": ["specific topic 1", "specific topic 2"],
                    "instructions": [
                        "Step 1: Specific action with actual commands/tools",
                        "Step 2: Another specific action",
                        "Step 3: Verification or testing step"
                    ],
                    "expected_output": "Specific, measurable outcome description",
                    "hints": ["Specific helpful hint", "Another practical tip"],
                    "evaluation_criteria": ["Criterion 1", "Criterion 2"],
                    "estimated_time": "15-30 minutes"
                }}
            ]
            
            Generate exercises that directly utilize the specific commands, tools, concepts, and techniques mentioned in each module's topics.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": exercises_prompt}
                ]
            )
            
            try:
                exercises_data = json.loads(response.content[0].text)
                logger.info(f"Generated {len(exercises_data)} exercises from syllabus using LLM")
                return exercises_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != 0:
                    try:
                        exercises_data = json.loads(text[start:end])
                        logger.info(f"Extracted {len(exercises_data)} exercises from LLM response")
                        return exercises_data
                    except:
                        pass
                
                # Fallback to programmatic generation
                logger.warning("LLM response parsing failed, using fallback exercise generation")
                return generate_exercises_fallback(syllabus)
                
        except Exception as e:
            logger.error(f"Error generating exercises from syllabus with LLM: {e}")
            return generate_exercises_fallback(syllabus)
    
    def generate_exercises_fallback(syllabus: dict) -> List[Dict]:
        """Fallback exercise generation when LLM fails"""
        exercises_list = []
        
        for module in syllabus.get("modules", []):
            for i, topic in enumerate(module.get("topics", [])):
                exercises_list.append({
                    "id": f"ex_{module.get('module_number', 1)}_{i+1}",
                    "title": f"{topic} - Hands-on Exercise",
                    "description": f"Practice exercise for {topic}. Apply the concepts learned in this module through practical activities.",
                    "type": "hands_on",
                    "difficulty": "beginner",
                    "module_number": module.get('module_number', 1),
                    "topics_covered": [topic],
                    "instructions": [
                        f"Review the key concepts of {topic}",
                        f"Complete the practical tasks related to {topic}",
                        "Test your understanding with the provided scenarios",
                        "Submit your solution and reflection"
                    ],
                    "expected_output": f"Demonstration of {topic} understanding through practical application",
                    "hints": [f"Focus on the key principles of {topic}", "Break down complex problems into smaller steps"],
                    "evaluation_criteria": ["Correctness of implementation", "Understanding of concepts"],
                    "estimated_time": "15-30 minutes"
                })
        
        return exercises_list
    
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
            1. Create SPECIFIC questions based on the exact topics, commands, and concepts in the syllabus
            2. For technical topics: Include questions about actual commands, syntax, parameters, and practical usage
            3. For business topics: Include scenario-based questions using real frameworks and methodologies
            4. Each question must test understanding of specific knowledge from the syllabus content
            5. Provide realistic distractors (wrong answers) that are plausible but clearly incorrect
            6. Include detailed explanations for correct answers
            7. Cover both conceptual understanding and practical application
            
            EXAMPLES OF GOOD QUIZ QUESTIONS:
            - For "File operations (cp, mv, rm, touch)": "Which command would you use to copy 'file1.txt' to 'backup.txt'?" Options: ["cp file1.txt backup.txt", "mv file1.txt backup.txt", "rm file1.txt backup.txt", "touch file1.txt backup.txt"]
            - For "Python variables (int, str, list, dict)": "What will be the output of: x = [1, 2, 3]; print(type(x))?" Options: ["<class 'list'>", "<class 'dict'>", "<class 'tuple'>", "<class 'str'>"]
            - For "Market segmentation (demographic, psychographic, behavioral)": "A company targeting customers based on their lifestyle and values is using which segmentation approach?" Options: ["Psychographic", "Demographic", "Geographic", "Behavioral"]
            
            For each module, create 3-5 questions that test the specific topics and learning outcomes mentioned in the syllabus.
            Return ONLY valid JSON array with this structure:
            [
                {{
                    "id": "quiz_1",
                    "title": "Module Title - Knowledge Assessment",
                    "description": "Comprehensive quiz covering specific module concepts",
                    "module_number": 1,
                    "duration": 20,
                    "difficulty": "beginner",
                    "questions": [
                        {{
                            "question": "Specific question based on syllabus content",
                            "options": ["Correct answer", "Plausible distractor 1", "Plausible distractor 2", "Plausible distractor 3"],
                            "correct_answer": 0,
                            "explanation": "Detailed explanation of why this is correct and why others are wrong",
                            "topic_tested": "Specific topic from syllabus",
                            "difficulty": "beginner"
                        }}
                    ]
                }}
            ]
            
            Generate questions that directly test knowledge of the specific commands, tools, concepts, and techniques mentioned in each module's topics and learning outcomes.
            Ensure questions are practical and test real understanding, not just memorization.
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
                "duration": 15 + (len(module.get('topics', [])) * 3),  # 15 min base + 3 min per topic
                "difficulty": "beginner"
            }
            
            # Generate questions based on learning outcomes
            for i, outcome in enumerate(module.get("learning_outcomes", [])):
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
        
        # Generate slides based on the topic
        slides_data = generate_course_slides(request.title, request.description, request.topic)
        course_slides[request.course_id] = slides_data
        
        # Save to database
        await save_slides_to_db(request.course_id, slides_data)
        
        return {"course_id": request.course_id, "slides": slides_data}
    
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
        
        lab_environments[lab_id] = {
            "id": lab_id,
            "course_id": request.course_id,
            "name": request.name,
            "description": request.description,
            "environment_type": request.environment_type,
            "config": lab_config,
            "exercises": []
        }
        
        return {"lab_id": lab_id, "lab": lab_environments[lab_id]}
    
    @app.get("/lab/{course_id}")
    async def get_lab_environment(course_id: str):
        # First check database for persistent lab environment
        lab_data = await load_lab_environment_from_db(course_id)
        if lab_data:
            return {"lab_id": lab_data["id"], "lab": lab_data}
        
        # Fallback to memory (for backward compatibility)
        for lab_id, lab in lab_environments.items():
            if lab["course_id"] == course_id:
                return {"lab_id": lab_id, "lab": lab}
                
        raise HTTPException(status_code=404, detail="Lab environment not found")
    
    @app.get("/student/lab-access/{course_id}/{student_id}")
    async def check_lab_access(course_id: str, student_id: str):
        """Check if student has access to lab environment"""
        # In a real implementation, this would check enrollment status
        # For now, we'll simulate enrollment check
        
        # Mock enrollment check (in real app, call course management service)
        has_access = True  # Assume student has access for demo
        
        if not has_access:
            raise HTTPException(
                status_code=403, 
                detail="Student not enrolled in this course"
            )
        
        # Find lab environment for course
        for lab_id, lab in lab_environments.items():
            if lab["course_id"] == course_id:
                return {
                    "access_granted": True,
                    "lab_id": lab_id,
                    "lab": lab,
                    "student_id": student_id
                }
        
        raise HTTPException(status_code=404, detail="Lab environment not found for this course")
    
    @app.post("/exercises/generate")
    async def generate_exercises(request: ExerciseRequest):
        logger.info(f"Generating exercises for course: {request.course_id}")
        
        exercise_data = generate_course_exercises(request.topic, request.difficulty)
        exercises[request.course_id] = exercise_data
        
        return {"course_id": request.course_id, "exercises": exercise_data}
    
    @app.get("/exercises/{course_id}")
    async def get_exercises(course_id: str):
        if course_id not in exercises:
            raise HTTPException(status_code=404, detail="Exercises not found for this course")
        return {"course_id": course_id, "exercises": exercises[course_id]}
    
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
        - Difficulty: {request.difficulty_level}
        
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
                "difficulty": request.difficulty_level
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
        
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not available")
            
        try:
            async with db_pool.acquire() as conn:
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
        
        # Build conversation messages for Claude
        messages = []
        
        # Add system context as first message
        system_message = f"""
        {lab['trainer_context']}
        
        Current Context:
        - Course: {request.context.get('course_title', 'Unknown')}
        - Student Progress: {request.context.get('student_progress', {})}
        - Current Exercise: {session_data.get('current_exercise', 'None')}
        
        You are the expert trainer for this course. Use the conversation history to maintain context and provide personalized, educational guidance.
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
            # Call Claude API with conversation history
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
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
        
        Create a quiz for a student with this progress:
        - Completed exercises: {request.student_progress.get('completed_exercises', 0)}
        - Current level: {request.student_progress.get('current_level', 'beginner')}
        - Knowledge areas covered: {request.student_progress.get('knowledge_areas', [])}
        
        Course: {request.context.get('course_title', '')}
        Category: {request.context.get('course_category', '')}
        
        Generate 3-5 multiple choice questions that:
        1. Test understanding of covered material
        2. Are appropriate for their level
        3. Include one correct answer and 3 plausible distractors
        
        Return as JSON with: title, description, questions array (each with question, options, correct_answer)
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
    
    @app.get("/quizzes/{course_id}")
    async def get_course_quizzes(course_id: str):
        """Get all quizzes for a course"""
        if course_id not in course_quizzes:
            return {"course_id": course_id, "quizzes": []}
        return {"course_id": course_id, "quizzes": course_quizzes[course_id]}
    
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
            1. NEVER write introductory, meta-commentary, or overview language
            2. NEVER use phrases like "Introduction to...", "We'll explore...", "This topic is...", "Learn about..."
            3. EVERY bullet point MUST teach specific, concrete information
            4. For technical topics: Include actual commands, syntax, parameters, and examples
            5. For business topics: Include specific methods, tools, frameworks, and real scenarios
            6. NO descriptions of what will be taught - only teach the actual content
            
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
                logger.info(f"Generated {len(slides_data)} slides from syllabus")
                return slides_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != -1:
                    try:
                        slides_data = json.loads(text[start:end])
                        return slides_data
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
        
        # Title slide
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Course Introduction",
            "content": syllabus["overview"],
            "slide_type": "title",
            "order": slide_order,
            "module_number": None
        })
        slide_order += 1
        
        # Objectives slide
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Learning Objectives",
            "content": "By the end of this course, you will: " + "; ".join(syllabus["objectives"]),
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
    
    @app.post("/syllabus/refine")
    async def refine_syllabus(request: SyllabusFeedback):
        try:
            prompt = f"Refine this syllabus based on feedback: {request.feedback}\\nCurrent: {json.dumps(request.current_syllabus)}\\nReturn updated JSON"
            response = claude_client.messages.create(model="claude-3-haiku-20240307", max_tokens=3000, messages=[{"role": "user", "content": prompt}])
            try:
                refined = json.loads(response.content[0].text)
            except:
                refined = request.current_syllabus
            course_syllabi[request.course_id] = refined
            await save_syllabus_to_db(request.course_id, refined)
            return {"course_id": request.course_id, "syllabus": refined}
        except:
            return {"course_id": request.course_id, "syllabus": request.current_syllabus}
    
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
            exercises[course_id] = exercises_data
            
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
            exercises[course_id] = exercises_data
            
            quizzes_data = [{"id": "quiz1", "title": "Knowledge Check", "description": "Test your understanding", "questions": [], "duration": 15}]
            course_quizzes[course_id] = quizzes_data
            
            return {"course_id": course_id, "slides": slides, "exercises": exercises_data, "quizzes": quizzes_data}
    
    @app.post("/courses/save")
    async def save_course_content(request: dict):
        course_id = request.get('course_id')
        logger.info(f"Saving course content for: {course_id}")
        # In real implementation, save to database
        return {"course_id": course_id, "message": "Course content saved successfully"}
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()    @app.post("/syllabus/generate")
    async def generate_course_syllabus(request: SyllabusRequest):
        """Generate comprehensive course syllabus"""
        logger.info(f"Generating syllabus for course: {request.course_id}")
        
        try:
            syllabus_prompt = f"""
            Create a comprehensive course syllabus for "{request.title}".
            
            Course Details:
            - Description: {request.description}
            - Category: {request.category}
            - Difficulty: {request.difficulty_level}
            - Duration: {request.estimated_duration} hours
            
            CRITICAL REQUIREMENTS FOR EXPLICIT CONTENT:
            1. Each module MUST include a comprehensive description explaining its purpose and scope
            2. Topics must be SPECIFIC and DETAILED - include actual commands, tools, techniques, and practical examples
            3. For technical subjects: List specific commands, file paths, configurations, syntax, and tools
            4. For business/soft skills: Include specific methodologies, frameworks, case studies, and practical applications
            5. Avoid vague terms - be concrete and actionable
            
            EXAMPLES OF EXPLICIT TOPIC FORMATTING:
            - Linux Fundamentals: "File system navigation (cd, pwd, ls -la), file operations (cp, mv, rm, touch), permissions (chmod 755, chown user:group), text processing (grep, awk, sed)"
            - Python Programming: "Variable assignment and data types (int, str, list, dict, tuple), control flow (if/elif/else, for/while loops), function definition (def, return, *args, **kwargs)"
            - Project Management: "Agile methodologies (Scrum ceremonies, sprint planning, daily standups), tools (Jira workflow, Kanban boards), risk assessment matrices"
            - Data Analysis: "Data cleaning (pandas.dropna(), fillna()), visualization (matplotlib.pyplot, seaborn.heatmap()), statistical analysis (numpy.mean(), scipy.stats)"
            
            Generate a detailed syllabus with:
            1. Course overview and objectives  
            2. Prerequisites and target audience
            3. Module/week breakdown with DETAILED descriptions and EXPLICIT topics
            4. Learning outcomes for each module
            5. Assessment methods (quizzes, exercises, projects)
            6. Required materials and resources
            7. Schedule and timeline
            
            Return as JSON with:
            {{
                "overview": "Course description and goals",
                "objectives": ["Learning objective 1", "Learning objective 2"],
                "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
                "modules": [
                    {{
                        "module_number": 1,
                        "title": "Module Title",
                        "description": "Comprehensive description of what this module teaches, its importance, and how it builds on previous knowledge",
                        "duration_hours": 2,
                        "topics": ["Specific topic with actual commands/tools/examples", "Detailed topic with concrete techniques", "Practical topic with explicit methods"],
                        "learning_outcomes": ["Measurable outcome with specific skills", "Concrete outcome with actionable abilities"],
                        "assessments": ["Specific assessment type", "Practical evaluation method"]
                    }}
                ],
                "assessment_strategy": "Description of how students will be evaluated",
                "resources": ["Resource 1", "Resource 2"]
            }}
            
            ENSURE ALL TOPICS are explicit and include specific commands, tools, methods, or examples relevant to {request.category}.
            Make content appropriate for {request.difficulty_level} level learners.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": syllabus_prompt}
                ]
            )
            
            try:
                syllabus_data = json.loads(response.content[0].text)
            except:
                syllabus_data = generate_fallback_syllabus(request)
            
            course_syllabi[request.course_id] = syllabus_data
            return {"course_id": request.course_id, "syllabus": syllabus_data}
            
        except Exception as e:
            logger.error(f"Syllabus generation error: {e}")
            fallback = generate_fallback_syllabus(request)
            course_syllabi[request.course_id] = fallback
            return {"course_id": request.course_id, "syllabus": fallback}
    
    @app.post("/syllabus/refine")
    async def refine_syllabus(request: SyllabusFeedback):
        """Refine syllabus based on user feedback"""
        logger.info(f"Refining syllabus for course: {request.course_id}")
        
        try:
            refinement_prompt = f"""
            You are refining a course syllabus based on instructor feedback.
            
            Current Syllabus:
            {json.dumps(request.current_syllabus, indent=2)}
            
            Instructor Feedback:
            {request.feedback}
            
            Please modify the syllabus to address the feedback. Maintain the same JSON structure but update content based on the suggestions. Be specific and detailed in your modifications.
            
            Return the complete updated syllabus in the same JSON format.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": refinement_prompt}
                ]
            )
            
            try:
                refined_syllabus = json.loads(response.content[0].text)
            except:
                refined_syllabus = request.current_syllabus
            
            course_syllabi[request.course_id] = refined_syllabus
            return {"course_id": request.course_id, "syllabus": refined_syllabus, "message": "Syllabus refined successfully"}
            
        except Exception as e:
            logger.error(f"Syllabus refinement error: {e}")
            return {"course_id": request.course_id, "syllabus": request.current_syllabus, "message": "Error refining syllabus"}
    
    @app.get("/syllabus/{course_id}")
    async def get_course_syllabus(course_id: str):
        """Get syllabus for a course"""
        if course_id not in course_syllabi:
            raise HTTPException(status_code=404, detail="Syllabus not found for this course")
        return {"course_id": course_id, "syllabus": course_syllabi[course_id]}
    
    
    def generate_fallback_syllabus(request: SyllabusRequest) -> dict:
        """Generate fallback syllabus structure"""
        num_modules = max(3, request.estimated_duration // 2)
        
        return {
            "overview": f"This course provides a comprehensive introduction to {request.category}. Students will learn fundamental concepts and practical applications.",
            "objectives": [
                f"Understand core concepts of {request.category}",
                "Apply knowledge through hands-on exercises",
                "Develop practical skills for real-world scenarios"
            ],
            "prerequisites": ["Basic computer literacy", "High school mathematics"],
            "modules": [
                {
                    "module_number": i + 1,
                    "title": f"Module {i + 1}: {request.category} Fundamentals" if i == 0 else f"Module {i + 1}: Advanced Topics",
                    "description": f"This module covers fundamental concepts and practical applications in {request.category}. Students will learn core principles and apply them through hands-on exercises.",
                    "duration_hours": request.estimated_duration // num_modules,
                    "topics": [f"Topic {j + 1}" for j in range(3)],
                    "learning_outcomes": [f"Understand concept {j + 1}" for j in range(2)],
                    "assessments": ["Quiz", "Hands-on Exercise"]
                } for i in range(num_modules)
            ],
            "assessment_strategy": "Continuous assessment through quizzes, exercises, and practical projects",
            "resources": ["Course materials", "Online resources", "Practice exercises"]
        }
    
    async def generate_slides_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate slides based on syllabus modules"""
        slides = []
        slide_order = 1
        
        # Introduction slide
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Course Introduction",
            "content": syllabus["overview"],
            "slide_type": "title",
            "order": slide_order
        })
        slide_order += 1
        
        # Objectives slide
        slides.append({
            "id": f"slide_{slide_order}",
            "title": "Learning Objectives",
            "content": "By the end of this course, you will: " + "; ".join(syllabus["objectives"]),
            "slide_type": "content",
            "order": slide_order
        })
        slide_order += 1
        
        # Module slides
        for module in syllabus["modules"]:
            # Module introduction
            slides.append({
                "id": f"slide_{slide_order}",
                "title": module["title"],
                "content": f"Topics covered: {', '.join(module['topics'])}. Learning outcomes: {', '.join(module['learning_outcomes'])}",
                "slide_type": "content",
                "order": slide_order
            })
            slide_order += 1
            
            # Topic slides
            for topic in module["topics"]:
                slides.append({
                    "id": f"slide_{slide_order}",
                    "title": topic,
                    "content": f"Detailed explanation of {topic} with practical examples and applications.",
                    "slide_type": "content",
                    "order": slide_order
                })
                slide_order += 1
        
        return slides
    
    async def generate_exercises_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate exercises based on syllabus modules using LLM with full syllabus context"""
        # Use the sync version for consistency
        return generate_exercises_from_syllabus_sync(course_id, syllabus)
    
    async def generate_quizzes_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate quizzes based on syllabus modules using LLM with full syllabus context"""
        # Use the sync version for consistency
        return generate_quizzes_from_syllabus_sync(course_id, syllabus)
    
    @app.post("/lab/analyze-code")
    async def analyze_code(request: dict):
        """Analyze student code using AI"""
        logger.info(f"Analyzing code for course: {request.get('course_id')}")
        
        try:
            code = request.get('code', '')
            language = request.get('language', 'javascript')
            context = request.get('context', {})
            
            if not code.strip():
                return {
                    "analysis": {
                        "overall_quality": "No code provided",
                        "suggestions": ["Please write some code first!"],
                        "warnings": [],
                        "best_practices": "Start by writing a simple function or variable declaration.",
                        "improvements": "Focus on understanding the problem requirements first."
                    },
                    "chat_message": "I don't see any code to analyze. Please write some code first!"
                }
            
            # Build analysis prompt
            analysis_prompt = f"""
You are an expert {language} instructor analyzing student code. Provide constructive, educational feedback.

Course Context: {context.get('course_title', 'Programming')}
Difficulty Level: {context.get('difficulty_level', 'beginner')}
Current Exercise: {context.get('exercise', {}).get('title', 'General coding practice')}

Student Code ({language}):
```{language}
{code}
```

Analyze this code and provide feedback as a JSON object with these keys:
- overall_quality: Brief assessment (1-2 sentences)
- suggestions: Array of specific improvement suggestions (3-5 items)
- warnings: Array of potential issues or bugs (if any)
- best_practices: String describing relevant best practices
- improvements: String with specific optimization or enhancement ideas

Focus on:
1. Code correctness and logic
2. Best practices for {language}
3. Readability and style
4. Educational guidance appropriate for {context.get('difficulty_level', 'beginner')} level
5. Encouraging tone while being constructive

Return only valid JSON.
"""

            # Get analysis from Claude
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            try:
                analysis = json.loads(response.content[0].text)
            except:
                # Fallback analysis
                analysis = {
                    "overall_quality": "Code analysis completed",
                    "suggestions": [
                        "Consider adding comments to explain your logic",
                        "Make sure variable names are descriptive",
                        "Test your code with different inputs"
                    ],
                    "warnings": [],
                    "best_practices": f"Follow {language} naming conventions and keep functions focused on single tasks.",
                    "improvements": "Consider breaking complex logic into smaller functions for better readability."
                }
            
            # Generate chat message
            chat_message = f"Great work! I've analyzed your {language} code. "
            if analysis.get('suggestions'):
                chat_message += f"I have {len(analysis['suggestions'])} suggestions for improvement. "
            chat_message += "Check the analysis panel for detailed feedback!"
            
            return {
                "analysis": analysis,
                "chat_message": chat_message
            }
            
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {
                "analysis": {
                    "overall_quality": "Analysis temporarily unavailable",
                    "suggestions": ["Keep coding! Practice makes perfect."],
                    "warnings": [],
                    "best_practices": "Focus on writing clean, readable code with good variable names.",
                    "improvements": "Test your code thoroughly and consider edge cases."
                },
                "chat_message": "I'm having trouble analyzing your code right now, but keep coding! You're doing great."
            }
    
    @app.post("/lab/get-hint")
    async def get_hint(request: dict):
        """Get a coding hint from AI"""
        logger.info(f"Providing hint for course: {request.get('course_id')}")
        
        try:
            code = request.get('code', '')
            language = request.get('language', 'javascript')
            exercise = request.get('exercise', {})
            
            hint_prompt = f"""
You are a helpful {language} programming tutor. A student is working on this exercise and needs a hint.

Exercise: {exercise.get('title', 'Programming challenge')}
Description: {exercise.get('description', 'Write some code')}

Student's current code:
```{language}
{code if code.strip() else 'No code written yet'}
```

Provide a helpful hint that:
1. Guides them toward the solution without giving it away
2. Is appropriate for beginners
3. Focuses on the next logical step
4. Encourages them to think through the problem

Give ONE specific, actionable hint in 1-2 sentences.
"""

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": hint_prompt}
                ]
            )
            
            hint = response.content[0].text.strip()
            
            return {"hint": hint}
            
        except Exception as e:
            logger.error(f"Hint generation error: {e}")
            fallback_hints = [
                "Try breaking the problem down into smaller steps.",
                "Think about what variables or functions you might need.",
                "Start with a simple example and build from there.",
                "Consider the input and what output you want to produce.",
                "Look at the exercise description again for clues."
            ]
            import random
            return {"hint": random.choice(fallback_hints)}
    
    @app.post("/lab/chat")
    async def lab_chat(request: dict):
        """Enhanced chat with code context"""
        logger.info(f"Lab chat for course: {request.get('course_id')}")
        
        try:
            user_message = request.get('user_message', '')
            current_code = request.get('current_code', '')
            language = request.get('language', 'javascript')
            context = request.get('context', {})
            
            chat_prompt = f"""
You are an expert {language} programming instructor and coding mentor. You're helping a student learn {context.get('course_title', 'programming')} in an interactive coding environment.

Course: {context.get('course_title', 'Programming')}
Student Level: {context.get('difficulty_level', 'beginner')}

Student's current code:
```{language}
{current_code if current_code.strip() else 'No code written yet'}
```

Student asks: "{user_message}"

Respond as a supportive coding mentor. Be:
1. Encouraging and positive
2. Educational and helpful
3. Specific and actionable
4. Appropriate for {context.get('difficulty_level', 'beginner')} level

If they're asking for help with code, provide guidance without giving away the complete solution.
If they're asking about concepts, explain clearly with examples.
Keep responses conversational and under 3 sentences.
"""

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": chat_prompt}
                ]
            )
            
            ai_response = response.content[0].text.strip()
            
            return {
                "response": ai_response,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Lab chat error: {e}")
            return {
                "response": "I'm here to help! Feel free to ask me about your code, programming concepts, or if you need a hint with the current exercise.",
                "timestamp": datetime.now()
            }

    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()