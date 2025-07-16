"""
QuizRepository implementation following Repository pattern.
Provides data access layer for quiz operations.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class QuizRepository:
    """
    Repository for quiz data operations following Repository pattern.
    Provides abstraction over database operations for quizzes.
    """
    
    def __init__(self, db):
        """
        Initialize QuizRepository with database connection.
        
        Args:
            db: Database connection/pool
        """
        self.db = db
    
    async def get_by_course_id(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get all quizzes for a specific course.
        
        Args:
            course_id: The course ID to get quizzes for
            
        Returns:
            List of quiz dictionaries
        """
        try:
            query = """
                SELECT id, course_id, title, description, time_limit, passing_score, 
                       max_attempts, is_published, questions_data, created_at, updated_at
                FROM quizzes 
                WHERE course_id = %s 
                ORDER BY created_at DESC
            """
            
            rows = await self.db.fetch_all(query, (course_id,))
            
            quizzes = []
            for row in rows:
                quiz = self._row_to_quiz(row)
                quizzes.append(quiz)
            
            return quizzes
            
        except Exception as e:
            logger.error(f"Error getting quizzes for course {course_id}: {e}")
            raise
    
    async def get_by_id(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a quiz by its ID.
        
        Args:
            quiz_id: The quiz ID
            
        Returns:
            Quiz dictionary or None if not found
        """
        try:
            query = """
                SELECT id, course_id, title, description, time_limit, passing_score, 
                       max_attempts, is_published, questions_data, created_at, updated_at
                FROM quizzes 
                WHERE id = %s
            """
            
            row = await self.db.fetch_one(query, (quiz_id,))
            
            if row:
                return self._row_to_quiz(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting quiz {quiz_id}: {e}")
            raise
    
    async def save(self, quiz_data: Dict[str, Any]) -> str:
        """
        Save a quiz to the database.
        
        Args:
            quiz_data: Quiz data dictionary
            
        Returns:
            Quiz ID
        """
        try:
            query = """
                INSERT INTO quizzes (
                    id, course_id, title, description, time_limit, passing_score, 
                    max_attempts, is_published, questions_data, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            return quiz_data['id']
            
        except Exception as e:
            logger.error(f"Error saving quiz: {e}")
            raise
    
    async def delete(self, quiz_id: str) -> bool:
        """
        Delete a quiz by ID.
        
        Args:
            quiz_id: The quiz ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM quizzes WHERE id = %s"
            result = await self.db.execute(query, (quiz_id,))
            
            # Check if any row was affected
            return result is not None
            
        except Exception as e:
            logger.error(f"Error deleting quiz {quiz_id}: {e}")
            return False
    
    async def update(self, quiz_id: str, quiz_data: Dict[str, Any]) -> bool:
        """
        Update an existing quiz.
        
        Args:
            quiz_id: The quiz ID to update
            quiz_data: Updated quiz data
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            query = """
                UPDATE quizzes SET
                    title = %s,
                    description = %s,
                    time_limit = %s,
                    passing_score = %s,
                    max_attempts = %s,
                    is_published = %s,
                    questions_data = %s,
                    updated_at = %s
                WHERE id = %s
            """
            
            values = (
                quiz_data['title'],
                quiz_data['description'],
                quiz_data.get('duration', 30),
                quiz_data.get('passing_score', 70),
                quiz_data.get('max_attempts', 3),
                quiz_data.get('is_published', False),
                json.dumps(quiz_data.get('questions', [])),
                datetime.now().isoformat(),
                quiz_id
            )
            
            result = await self.db.execute(query, values)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating quiz {quiz_id}: {e}")
            return False
    
    async def get_all_quizzes(self) -> List[Dict[str, Any]]:
        """
        Get all quizzes from the database.
        
        Returns:
            List of all quiz dictionaries
        """
        try:
            query = """
                SELECT id, course_id, title, description, time_limit, passing_score, 
                       max_attempts, is_published, questions_data, created_at, updated_at
                FROM quizzes 
                ORDER BY created_at DESC
            """
            
            rows = await self.db.fetch_all(query)
            
            quizzes = []
            for row in rows:
                quiz = self._row_to_quiz(row)
                quizzes.append(quiz)
            
            return quizzes
            
        except Exception as e:
            logger.error(f"Error getting all quizzes: {e}")
            raise
    
    async def get_published_quizzes(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get only published quizzes for a course.
        
        Args:
            course_id: The course ID
            
        Returns:
            List of published quiz dictionaries
        """
        try:
            query = """
                SELECT id, course_id, title, description, time_limit, passing_score, 
                       max_attempts, is_published, questions_data, created_at, updated_at
                FROM quizzes 
                WHERE course_id = %s AND is_published = TRUE
                ORDER BY created_at DESC
            """
            
            rows = await self.db.fetch_all(query, (course_id,))
            
            quizzes = []
            for row in rows:
                quiz = self._row_to_quiz(row)
                quizzes.append(quiz)
            
            return quizzes
            
        except Exception as e:
            logger.error(f"Error getting published quizzes for course {course_id}: {e}")
            raise
    
    def _row_to_quiz(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert database row to quiz dictionary.
        
        Args:
            row: Database row dictionary
            
        Returns:
            Quiz dictionary
        """
        quiz = {
            'id': row['id'],
            'course_id': row['course_id'],
            'title': row['title'],
            'description': row['description'],
            'duration': row['time_limit'],  # Map time_limit to duration
            'passing_score': row['passing_score'],
            'max_attempts': row['max_attempts'],
            'is_published': row['is_published'],
            'questions': json.loads(row['questions_data']) if row['questions_data'] else [],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
        
        # Add difficulty based on questions
        if quiz['questions']:
            quiz['difficulty'] = self._determine_difficulty(quiz['questions'])
        else:
            quiz['difficulty'] = 'beginner'
        
        return quiz
    
    def _determine_difficulty(self, questions: List[Dict]) -> str:
        """
        Determine quiz difficulty based on question complexity.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Difficulty level string
        """
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