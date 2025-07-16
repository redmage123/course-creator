"""
Unit tests for ExerciseGenerationService following TDD principles.
Tests for replacing default exercises with AI-generated labs.
"""
import sys
import os
sys.path.insert(0, '/home/bbrelin/course-creator/services/course-generator')

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

class TestExerciseGenerationService:
    """Test suite for ExerciseGenerationService implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_ai_service = Mock()
        self.mock_syllabus_service = Mock()
        self.mock_lab_service = Mock()
        
        # Set up AsyncMock for async methods
        self.mock_db.execute = AsyncMock(return_value=None)
        self.mock_ai_service.generate_interactive_exercises = AsyncMock()
        self.mock_syllabus_service.get_syllabus = AsyncMock()
        self.mock_lab_service.create_lab_environment = AsyncMock()
        
    def test_exercise_generation_service_init(self):
        """Test ExerciseGenerationService initialization."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        assert service.db == self.mock_db
        assert service.ai_service == self.mock_ai_service
        assert service.syllabus_service == self.mock_syllabus_service
        assert service.lab_service == self.mock_lab_service
    
    @pytest.mark.asyncio
    async def test_generate_ai_powered_exercises(self):
        """Test generating AI-powered exercises from syllabus."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        # Mock syllabus data
        mock_syllabus = {
            'overview': 'Python programming course',
            'modules': [
                {
                    'module_number': 1,
                    'title': 'Python Basics',
                    'topics': ['Variables', 'Data Types', 'Control Flow'],
                    'learning_outcomes': ['Understand Python syntax', 'Write basic programs'],
                    'duration_hours': 4
                },
                {
                    'module_number': 2,
                    'title': 'Object-Oriented Programming',
                    'topics': ['Classes', 'Inheritance', 'Polymorphism'],
                    'learning_outcomes': ['Design classes', 'Implement OOP principles'],
                    'duration_hours': 6
                }
            ]
        }
        
        # Mock AI response
        mock_ai_response = {
            'exercises': [
                {
                    'title': 'Interactive Python Variables Lab',
                    'description': 'Hands-on lab exploring Python variable manipulation',
                    'type': 'interactive_lab',
                    'difficulty': 'beginner',
                    'module_number': 1,
                    'estimated_time': '30 minutes',
                    'learning_objectives': ['Master variable assignment', 'Understand data types'],
                    'lab_environment': {
                        'type': 'python',
                        'version': '3.9',
                        'packages': ['numpy', 'pandas']
                    },
                    'exercises': [
                        {
                            'step': 1,
                            'title': 'Variable Assignment',
                            'description': 'Practice creating and modifying variables',
                            'starter_code': 'name = ""\n# Your code here',
                            'solution': 'name = "Alice"\nage = 25\nprint(f"Hello, {name}!")',
                            'validation': 'assert name != ""'
                        }
                    ]
                },
                {
                    'title': 'OOP Design Challenge',
                    'description': 'Design and implement a class hierarchy',
                    'type': 'design_challenge',
                    'difficulty': 'intermediate',
                    'module_number': 2,
                    'estimated_time': '45 minutes',
                    'learning_objectives': ['Design class hierarchies', 'Implement inheritance'],
                    'lab_environment': {
                        'type': 'python',
                        'version': '3.9',
                        'packages': ['pytest']
                    },
                    'exercises': [
                        {
                            'step': 1,
                            'title': 'Base Class Design',
                            'description': 'Create a base Animal class',
                            'starter_code': 'class Animal:\n    # Your code here',
                            'solution': 'class Animal:\n    def __init__(self, name):\n        self.name = name',
                            'validation': 'assert hasattr(Animal, "__init__")'
                        }
                    ]
                }
            ]
        }
        
        self.mock_syllabus_service.get_syllabus = AsyncMock(return_value=mock_syllabus)
        self.mock_ai_service.generate_interactive_exercises = AsyncMock(return_value=mock_ai_response)
        self.mock_db.execute = AsyncMock(return_value=None)
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        result = await service.generate_ai_powered_exercises("course_123")
        
        assert len(result) == 2
        assert result[0]['title'] == 'Interactive Python Variables Lab'
        assert result[0]['type'] == 'interactive_lab'
        assert result[1]['title'] == 'OOP Design Challenge'
        assert result[1]['type'] == 'design_challenge'
        
        # Verify AI service was called with syllabus
        self.mock_ai_service.generate_interactive_exercises.assert_called_once()
        
        # Verify database save was attempted
        self.mock_db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_interactive_lab_environment(self):
        """Test generating interactive lab environment for exercises."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        exercise_data = {
            'title': 'Python Variables Lab',
            'module_number': 1,
            'topics': ['Variables', 'Data Types'],
            'difficulty': 'beginner',
            'lab_environment': {
                'type': 'python',
                'version': '3.9',
                'packages': ['numpy', 'pandas']
            }
        }
        
        mock_lab_env = {
            'id': 'lab_env_123',
            'name': 'Python Variables Lab Environment',
            'environment_type': 'python',
            'config': {
                'language': 'python',
                'version': '3.9',
                'packages': ['numpy', 'pandas']
            },
            'exercises': [
                {
                    'title': 'Variable Assignment',
                    'starter_code': 'name = ""\n# Your code here',
                    'solution': 'name = "Alice"'
                }
            ]
        }
        
        self.mock_lab_service.create_lab_environment = AsyncMock(return_value=mock_lab_env)
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        result = await service.generate_interactive_lab_environment("course_123", exercise_data)
        
        assert result['name'] == 'Python Variables Lab Environment'
        assert result['environment_type'] == 'python'
        assert len(result['exercises']) == 1
        
        # Verify lab service was called
        self.mock_lab_service.create_lab_environment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_exercise_quality(self):
        """Test exercise quality validation."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        # Test valid exercise
        valid_exercise = {
            'title': 'Python Variables Lab',
            'description': 'Learn Python variables through hands-on practice',
            'type': 'interactive_lab',
            'difficulty': 'beginner',
            'module_number': 1,
            'estimated_time': '30 minutes',
            'learning_objectives': ['Master variable assignment'],
            'exercises': [
                {
                    'step': 1,
                    'title': 'Variable Assignment',
                    'description': 'Practice creating variables',
                    'starter_code': 'name = ""',
                    'solution': 'name = "Alice"',
                    'validation': 'assert name != ""'
                }
            ]
        }
        
        assert service.validate_exercise_quality(valid_exercise) is True
        
        # Test invalid exercise
        invalid_exercise = {
            'title': '',  # Empty title
            'description': 'Learn Python variables',
            'type': 'invalid_type',  # Invalid type
            'exercises': []  # No exercises
        }
        
        assert service.validate_exercise_quality(invalid_exercise) is False
    
    @pytest.mark.asyncio
    async def test_fallback_to_enhanced_exercises(self):
        """Test fallback to enhanced exercises when AI fails."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        # Mock syllabus data
        mock_syllabus = {
            'modules': [
                {
                    'module_number': 1,
                    'title': 'Python Basics',
                    'topics': ['Variables', 'Control Flow']
                }
            ]
        }
        
        # Mock AI service failure
        self.mock_ai_service.generate_interactive_exercises.side_effect = Exception("AI service unavailable")
        self.mock_syllabus_service.get_syllabus = AsyncMock(return_value=mock_syllabus)
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        result = await service.generate_ai_powered_exercises("course_123")
        
        # Should fallback to enhanced exercises
        assert len(result) == 1
        assert result[0]['title'] == 'Python Basics - Interactive Lab'
        assert result[0]['type'] == 'interactive_lab'
        assert 'lab_environment' in result[0]
    
    @pytest.mark.asyncio
    async def test_exercise_personalization(self):
        """Test exercise personalization based on course context."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        # Mock course context
        course_context = {
            'id': 'course_123',
            'title': 'Advanced Python for Data Science',
            'category': 'Data Science',
            'difficulty_level': 'advanced',
            'target_audience': 'professionals'
        }
        
        mock_syllabus = {
            'modules': [
                {
                    'module_number': 1,
                    'title': 'Data Manipulation',
                    'topics': ['Pandas', 'NumPy']
                }
            ]
        }
        
        self.mock_syllabus_service.get_syllabus = AsyncMock(return_value=mock_syllabus)
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        result = await service.personalize_exercises_for_course(course_context, mock_syllabus)
        
        # Should generate personalized exercises
        assert len(result) == 1
        assert 'Data Science' in result[0]['description']
        assert result[0]['difficulty'] == 'advanced'
        assert result[0]['lab_environment']['packages'] == ['pandas', 'numpy', 'matplotlib', 'scikit-learn', 'seaborn']
    
    @pytest.mark.asyncio
    async def test_exercise_progressive_difficulty(self):
        """Test progressive difficulty in exercise generation."""
        from services.exercise_generation_service import ExerciseGenerationService
        
        mock_syllabus = {
            'modules': [
                {'module_number': 1, 'title': 'Basics', 'topics': ['Variables']},
                {'module_number': 2, 'title': 'Functions', 'topics': ['Functions']},
                {'module_number': 3, 'title': 'OOP', 'topics': ['Classes']},
                {'module_number': 4, 'title': 'Advanced', 'topics': ['Decorators']}
            ]
        }
        
        self.mock_syllabus_service.get_syllabus = AsyncMock(return_value=mock_syllabus)
        
        service = ExerciseGenerationService(
            db=self.mock_db,
            ai_service=self.mock_ai_service,
            syllabus_service=self.mock_syllabus_service,
            lab_service=self.mock_lab_service
        )
        
        result = await service.generate_progressive_exercises("course_123")
        
        # Should generate exercises with progressive difficulty
        assert len(result) == 4
        assert result[0]['difficulty'] == 'beginner'
        assert result[1]['difficulty'] == 'beginner'
        assert result[2]['difficulty'] == 'intermediate'
        assert result[3]['difficulty'] == 'advanced'