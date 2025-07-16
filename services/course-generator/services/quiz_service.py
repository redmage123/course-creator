"""
QuizService implementation following SOLID principles.
Handles quiz generation, storage, and retrieval with proper error handling.
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class QuizService:
    """
    Service for managing quiz operations following Single Responsibility Principle.
    Handles quiz CRUD operations, generation, and validation.
    """
    
    def __init__(self, db, ai_service, syllabus_service):
        """
        Initialize QuizService with dependencies.
        
        Args:
            db: Database connection/pool
            ai_service: AI service for quiz generation
            syllabus_service: Service for syllabus operations
        """
        self.db = db
        self.ai_service = ai_service
        self.syllabus_service = syllabus_service
        self._memory_cache = {}  # In-memory fallback cache
        self.repository = None  # Will be set by dependency injection
    
    async def get_course_quizzes(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get all quizzes for a course, with database-first approach and memory fallback.
        
        Args:
            course_id: The course ID to get quizzes for
            
        Returns:
            List of quiz dictionaries
        """
        try:
            # First, try to get from database
            return await self._get_quizzes_from_database(course_id)
        except Exception as e:
            logger.warning(f"Database unavailable for course {course_id}: {e}")
            # Fallback to memory cache
            return self._get_quizzes_from_memory(course_id)
    
    async def _get_quizzes_from_database(self, course_id: str) -> List[Dict[str, Any]]:
        """Get quizzes from database."""
        if not self.db:
            raise Exception("Database not available")
        
        try:
            # Query using the actual database schema: quizzes -> lessons -> courses
            query = """
                SELECT q.id, l.course_id, q.title, q.description, q.time_limit_minutes, 
                       q.passing_score, q.max_attempts, q.is_active, q.created_at, q.updated_at
                FROM quizzes q
                JOIN lessons l ON q.lesson_id = l.id
                WHERE l.course_id = $1 
                ORDER BY q.created_at DESC
            """
            
            rows = await self.db.fetch(query, course_id)
            
            # Transform database rows to quiz format
            quizzes = []
            for row in rows:
                # Load questions for this quiz
                questions = await self._load_quiz_questions(row['id'])
                
                quiz = {
                    'id': str(row['id']),
                    'course_id': str(row['course_id']),
                    'title': row['title'],
                    'description': row['description'],
                    'duration': row['time_limit_minutes'],  # Map time_limit_minutes to duration
                    'passing_score': float(row['passing_score']) if row['passing_score'] else 70.0,
                    'max_attempts': row['max_attempts'],
                    'is_published': row['is_active'],  # Map is_active to is_published
                    'questions': questions,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
                # Add difficulty from questions if available
                if quiz['questions']:
                    # Determine difficulty based on question complexity
                    quiz['difficulty'] = self._determine_quiz_difficulty(quiz['questions'])
                else:
                    quiz['difficulty'] = 'beginner'
                
                quizzes.append(quiz)
            
            return quizzes
            
        except Exception as e:
            logger.error(f"Database error getting quizzes for course {course_id}: {e}")
            raise
    
    def _get_quizzes_from_memory(self, course_id: str) -> List[Dict[str, Any]]:
        """Get quizzes from memory cache."""
        return self._memory_cache.get(course_id, [])
    
    async def _load_quiz_questions(self, quiz_id: str) -> List[Dict[str, Any]]:
        """Load questions for a specific quiz from the database."""
        if not self.db:
            return []
        
        try:
            query = """
                SELECT id, question_text, question_type, correct_answer, points, order_index
                FROM quiz_questions
                WHERE quiz_id = $1
                ORDER BY order_index ASC
            """
            
            rows = await self.db.fetch(query, quiz_id)
            
            questions = []
            for row in rows:
                question = {
                    'id': str(row['id']),
                    'question': row['question_text'],
                    'type': row['question_type'],
                    'correct_answer': row['correct_answer'],
                    'points': float(row['points']) if row['points'] else 1.0,
                    'order': row['order_index']
                }
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error loading quiz questions for quiz {quiz_id}: {e}")
            return []
    
    def _determine_quiz_difficulty(self, questions: List[Dict]) -> str:
        """Determine quiz difficulty based on question complexity."""
        if not questions:
            return 'beginner'
        
        # Simple heuristic: count question types and complexity
        complex_count = 0
        for question in questions:
            if question.get('type') in ['code', 'essay', 'fill_in_the_blank']:
                complex_count += 1
            elif len(question.get('options', [])) > 4:
                complex_count += 1
        
        complexity_ratio = complex_count / len(questions)
        
        if complexity_ratio > 0.6:
            return 'advanced'
        elif complexity_ratio > 0.3:
            return 'intermediate'
        else:
            return 'beginner'
    
    async def generate_quizzes_for_course(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Generate quizzes for a course based on its syllabus.
        
        Args:
            course_id: The course ID to generate quizzes for
            
        Returns:
            List of generated quiz dictionaries
        """
        try:
            # Get syllabus data
            syllabus = await self.syllabus_service.get_syllabus(course_id)
            if not syllabus:
                raise ValueError(f"No syllabus found for course {course_id}")
            
            # Generate quizzes using AI service
            ai_response = await self.ai_service.generate_quizzes(syllabus)
            
            if not ai_response or 'quizzes' not in ai_response:
                raise ValueError("Invalid AI response for quiz generation")
            
            quizzes = ai_response['quizzes']
            
            # Process and validate each quiz
            processed_quizzes = []
            for quiz_data in quizzes:
                # Add metadata
                quiz_data['id'] = str(uuid.uuid4())
                quiz_data['course_id'] = course_id
                quiz_data['created_at'] = datetime.now().isoformat()
                quiz_data['is_published'] = False
                
                # Validate quiz data
                if self.validate_quiz_data(quiz_data):
                    processed_quizzes.append(quiz_data)
                    
                    # Save to database
                    try:
                        await self.save_quiz_to_database(quiz_data)
                    except Exception as e:
                        logger.error(f"Failed to save quiz to database: {e}")
                        # Still add to memory cache for immediate use
                        self._add_to_memory_cache(course_id, quiz_data)
                else:
                    logger.warning(f"Invalid quiz data generated for course {course_id}")
            
            return processed_quizzes
            
        except Exception as e:
            logger.error(f"Error generating quizzes for course {course_id}: {e}")
            raise
    
    async def save_quiz_to_database(self, quiz_data: Dict[str, Any]) -> None:
        """
        Save quiz to database with proper schema mapping.
        
        Args:
            quiz_data: Quiz data dictionary
        """
        if not self.db:
            raise Exception("Database not available")
        
        try:
            # Map quiz data to database schema
            query = """
                INSERT INTO quizzes (
                    id, course_id, title, description, time_limit, passing_score, 
                    max_attempts, is_published, questions_data, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    time_limit = EXCLUDED.time_limit,
                    passing_score = EXCLUDED.passing_score,
                    max_attempts = EXCLUDED.max_attempts,
                    is_published = EXCLUDED.is_published,
                    questions_data = EXCLUDED.questions_data,
                    updated_at = EXCLUDED.updated_at
            """
            
            values = (
                quiz_data['id'],
                quiz_data['course_id'],
                quiz_data['title'],
                quiz_data['description'],
                quiz_data.get('duration', 30),  # duration -> time_limit
                quiz_data.get('passing_score', 70),
                quiz_data.get('max_attempts', 3),
                quiz_data.get('is_published', False),
                json.dumps(quiz_data.get('questions', [])),
                quiz_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            )
            
            await self.db.execute(query, values)
            logger.info(f"Quiz {quiz_data['id']} saved to database")
            
        except Exception as e:
            logger.error(f"Error saving quiz to database: {e}")
            raise
    
    def validate_quiz_data(self, quiz_data: Dict[str, Any]) -> bool:
        """
        Validate quiz data structure and content.
        
        Args:
            quiz_data: Quiz data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['title', 'description']
            for field in required_fields:
                if not quiz_data.get(field) or quiz_data[field].strip() == '':
                    logger.warning(f"Quiz missing required field: {field}")
                    return False
            
            # Check questions
            questions = quiz_data.get('questions', [])
            if not questions:
                logger.warning("Quiz has no questions")
                return False
            
            # Validate each question
            for question in questions:
                if not self._validate_question(question):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating quiz data: {e}")
            return False
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate individual question data."""
        try:
            # Check required fields
            if not question.get('question') or question['question'].strip() == '':
                return False
            
            # Check question type
            question_type = question.get('type', 'multiple_choice')
            if question_type not in ['multiple_choice', 'true_false', 'fill_in_the_blank', 'essay', 'code']:
                return False
            
            # Type-specific validation
            if question_type == 'multiple_choice':
                options = question.get('options', [])
                if len(options) < 2:
                    return False
                if not question.get('correct_answer'):
                    return False
                if question['correct_answer'] not in options:
                    return False
            
            elif question_type == 'true_false':
                if question.get('correct_answer') not in ['true', 'false', True, False]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return False
    
    def _add_to_memory_cache(self, course_id: str, quiz_data: Dict[str, Any]) -> None:
        """Add quiz to memory cache."""
        if course_id not in self._memory_cache:
            self._memory_cache[course_id] = []
        self._memory_cache[course_id].append(quiz_data)
    
    async def get_course_quizzes_via_repository(self, course_id: str) -> List[Dict[str, Any]]:
        """Get quizzes via repository pattern (if available)."""
        if not self.repository:
            return await self.get_course_quizzes(course_id)
        
        try:
            return await self.repository.get_by_course_id(course_id)
        except Exception as e:
            logger.warning(f"Repository unavailable, falling back to direct database: {e}")
            return await self.get_course_quizzes(course_id)
    
    async def delete_quiz(self, quiz_id: str) -> bool:
        """
        Delete a quiz by ID.
        
        Args:
            quiz_id: The quiz ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self.db:
                raise Exception("Database not available")
            
            query = "DELETE FROM quizzes WHERE id = $1"
            await self.db.execute(query, quiz_id)
            
            # Also remove from memory cache
            for course_id, quizzes in self._memory_cache.items():
                self._memory_cache[course_id] = [q for q in quizzes if q.get('id') != quiz_id]
            
            logger.info(f"Quiz {quiz_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            return False
    
    async def update_quiz(self, quiz_id: str, quiz_data: Dict[str, Any]) -> bool:
        """
        Update an existing quiz.
        
        Args:
            quiz_id: The quiz ID to update
            quiz_data: Updated quiz data
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.validate_quiz_data(quiz_data):
                return False
            
            quiz_data['id'] = quiz_id
            quiz_data['updated_at'] = datetime.now().isoformat()
            
            await self.save_quiz_to_database(quiz_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating quiz {quiz_id}: {e}")
            return False