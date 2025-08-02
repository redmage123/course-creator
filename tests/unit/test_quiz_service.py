"""
Unit tests for QuizService following TDD principles.
Tests for fixing quiz display issues in instructor dashboard.
"""
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

# Add course-generator to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/course-generator'))

class TestQuizService:
    """Test suite for QuizService implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_ai_service = Mock()
        self.mock_syllabus_service = Mock()
        
        # Set up AsyncMock for async methods
        self.mock_db.fetch_all = AsyncMock()
        self.mock_db.execute = AsyncMock(return_value=None)
        self.mock_ai_service.generate_quizzes = AsyncMock()
        self.mock_syllabus_service.get_syllabus = AsyncMock()
        
    def test_quiz_service_init(self):
        """Test QuizService initialization."""
        # This test will fail until we implement QuizService
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        assert service.db == self.mock_db
        assert service.ai_service == self.mock_ai_service
        assert service.syllabus_service == self.mock_syllabus_service
    
    @pytest.mark.asyncio
    async def test_get_course_quizzes_from_database(self):
        """Test retrieving quizzes from database first."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        # Mock database response (as it would come from database)
        mock_db_rows = [
            {
                'id': 'quiz_1',
                'course_id': 'course_123',
                'title': 'Test Quiz 1',
                'description': 'Test Description',
                'time_limit': 30,
                'passing_score': 70,
                'max_attempts': 3,
                'is_published': True,
                'questions_data': '[{"question": "What is Python?", "options": ["A language", "A snake", "A tool", "All of the above"], "correct_answer": "A language"}]',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': '2023-01-01T00:00:00'
            }
        ]
        
        # Expected result after processing
        expected_quizzes = [
            {
                'id': 'quiz_1',
                'course_id': 'course_123',
                'title': 'Test Quiz 1',
                'description': 'Test Description',
                'duration': 30,
                'passing_score': 70,
                'max_attempts': 3,
                'is_published': True,
                'questions': [
                    {
                        'question': 'What is Python?',
                        'options': ['A language', 'A snake', 'A tool', 'All of the above'],
                        'correct_answer': 'A language'
                    }
                ],
                'difficulty': 'beginner',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': '2023-01-01T00:00:00'
            }
        ]
        
        self.mock_db.fetch_all = AsyncMock(return_value=mock_db_rows)
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        result = await service.get_course_quizzes("course_123")
        
        assert result == expected_quizzes
        self.mock_db.fetch_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_course_quizzes_fallback_to_memory(self):
        """Test fallback to memory when database fails."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        # Mock database failure
        self.mock_db.fetch_all.side_effect = Exception("Database unavailable")
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        # Set up memory fallback
        service._memory_cache = {
            "course_123": [
                {
                    'id': 'quiz_1',
                    'title': 'Cached Quiz',
                    'description': 'From memory',
                    'difficulty': 'intermediate'
                }
            ]
        }
        
        result = await service.get_course_quizzes("course_123")
        
        assert len(result) == 1
        assert result[0]['title'] == 'Cached Quiz'
    
    @pytest.mark.asyncio
    async def test_generate_quizzes_from_syllabus(self):
        """Test quiz generation from syllabus."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        # Mock syllabus data
        mock_syllabus = {
            'modules': [
                {
                    'title': 'Python Basics',
                    'learning_objectives': ['Understand variables', 'Learn loops']
                }
            ]
        }
        
        # Mock AI response
        mock_ai_response = {
            'quizzes': [
                {
                    'title': 'Python Basics Quiz',
                    'description': 'Test your Python knowledge',
                    'difficulty': 'beginner',
                    'questions': [
                        {
                            'question': 'What is a variable?',
                            'type': 'multiple_choice',
                            'options': ['A container', 'A function', 'A loop', 'A class'],
                            'correct_answer': 'A container',
                            'explanation': 'Variables store data values'
                        }
                    ]
                }
            ]
        }
        
        self.mock_syllabus_service.get_syllabus.return_value = mock_syllabus
        self.mock_ai_service.generate_quizzes.return_value = mock_ai_response
        self.mock_db.execute.return_value = None
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        result = await service.generate_quizzes_for_course("course_123")
        
        assert len(result) == 1
        assert result[0]['title'] == 'Python Basics Quiz'
        assert len(result[0]['questions']) == 1
        
        # Verify AI service was called with syllabus
        self.mock_ai_service.generate_quizzes.assert_called_once()
        
        # Verify database save was attempted
        self.mock_db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_save_quizzes_to_database(self):
        """Test saving quizzes to database with correct schema."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        quiz_data = {
            'id': 'quiz_1',
            'course_id': 'course_123',
            'title': 'Test Quiz',
            'description': 'Test Description',
            'difficulty': 'beginner',
            'duration': 30,
            'questions': [
                {
                    'question': 'Test question?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A'
                }
            ]
        }
        
        self.mock_db.execute.return_value = None
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        await service.save_quiz_to_database(quiz_data)
        
        # Verify the correct SQL was executed with proper field mapping
        self.mock_db.execute.assert_called_once()
        call_args = self.mock_db.execute.call_args
        sql_query = call_args[0][0]
        
        # Check that the SQL maps to the correct database schema
        assert 'INSERT INTO quizzes' in sql_query
        assert 'title' in sql_query
        assert 'description' in sql_query
        assert 'time_limit' in sql_query  # duration -> time_limit
        assert 'questions_data' in sql_query  # questions as JSON
    
    @pytest.mark.asyncio
    async def test_quiz_validation(self):
        """Test quiz data validation."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        
        # Test valid quiz data
        valid_quiz = {
            'title': 'Valid Quiz',
            'description': 'Valid description',
            'difficulty': 'beginner',
            'questions': [
                {
                    'question': 'Valid question?',
                    'type': 'multiple_choice',
                    'options': ['A', 'B', 'C', 'D'],
                    'correct_answer': 'A'
                }
            ]
        }
        
        assert service.validate_quiz_data(valid_quiz) is True
        
        # Test invalid quiz data
        invalid_quiz = {
            'title': '',  # Empty title
            'description': 'Valid description',
            'questions': []  # No questions
        }
        
        assert service.validate_quiz_data(invalid_quiz) is False
    
    @pytest.mark.asyncio
    async def test_quiz_repository_integration(self):
        """Test integration with QuizRepository."""
        from application.services.quiz_generation_service import QuizGenerationService as QuizService
        from repositories.quiz_repository import QuizRepository
        
        mock_repository = Mock(spec=QuizRepository)
        mock_repository.get_by_course_id.return_value = []
        mock_repository.save.return_value = None
        
        service = QuizService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service
        )
        service.repository = mock_repository
        
        # Test getting quizzes through repository
        result = await service.get_course_quizzes_via_repository("course_123")
        
        mock_repository.get_by_course_id.assert_called_once_with("course_123")
        assert result == []