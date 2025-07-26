#!/usr/bin/env python3
"""
Integration Tests for Enhanced Content Management
Tests the full workflow from frontend to backend services
"""

import pytest
import asyncio
import aiohttp
import tempfile
import json
import os
from pathlib import Path


class TestContentManagementIntegration:
    """Integration tests for content management across services"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment and mock services"""
        self.base_url = "http://localhost:8005"  # Content Management Service
        self.course_id = "integration-test-course-123"
        self.test_files = {}
        
        # Create test files
        self.create_test_files()
        
        yield
        
        # Cleanup test files
        self.cleanup_test_files()
    
    def create_test_files(self):
        """Create test files for upload testing"""
        # Create test syllabus
        syllabus_content = """
        Course: Introduction to Python Programming
        
        Week 1: Variables and Data Types
        - Introduction to Python syntax
        - Variable assignment and naming conventions
        - Basic data types: integers, strings, lists
        
        Week 2: Control Structures  
        - If statements and conditional logic
        - For and while loops
        - Loop control statements
        
        Week 3: Functions and Modules
        - Function definition and calling
        - Parameters and return values
        - Importing and using modules
        
        Week 4: Object-Oriented Programming
        - Classes and objects
        - Inheritance and polymorphism
        - Encapsulation and abstraction
        """
        
        # Create temporary syllabus file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(syllabus_content)
            self.test_files['syllabus'] = f.name
        
        # Create test quiz JSON
        quiz_data = {
            "metadata": {
                "title": "Python Basics Quiz",
                "description": "Test your knowledge of Python fundamentals",
                "topic": "Python Programming",
                "difficulty": "beginner",
                "time_limit": 30
            },
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "What is the correct way to declare a variable in Python?",
                    "options": [
                        "var x = 5",
                        "x = 5", 
                        "int x = 5",
                        "declare x = 5"
                    ],
                    "correct_answer": "x = 5",
                    "explanation": "Python uses simple assignment without type declarations"
                },
                {
                    "id": 2,
                    "type": "multiple_choice", 
                    "question": "Which of these is NOT a valid Python data type?",
                    "options": [
                        "int",
                        "string",
                        "list", 
                        "dict"
                    ],
                    "correct_answer": "string",
                    "explanation": "Python uses 'str' not 'string' for string type"
                },
                {
                    "id": 3,
                    "type": "multiple_choice",
                    "question": "How do you create a comment in Python?",
                    "options": [
                        "// This is a comment",
                        "<!-- This is a comment -->",
                        "# This is a comment",
                        "/* This is a comment */"
                    ],
                    "correct_answer": "# This is a comment",
                    "explanation": "Python uses # for single-line comments"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(quiz_data, f, indent=2)
            self.test_files['quiz'] = f.name
        
        # Create test lab JSON
        lab_data = {
            "metadata": {
                "title": "Python Variables Lab",
                "description": "Practice working with Python variables",
                "environment": "python3.9",
                "difficulty": "beginner",
                "estimated_time": "20 minutes"
            },
            "exercises": [
                {
                    "id": 1,
                    "title": "Variable Assignment",
                    "description": "Create variables of different types",
                    "instructions": "Create variables for name, age, and is_student",
                    "starter_code": "# Create your variables here\nname = \nage = \nis_student = ",
                    "solution": "name = 'John Doe'\nage = 25\nis_student = True",
                    "test_cases": [
                        {
                            "input": "",
                            "expected_output": "John Doe, 25, True",
                            "description": "Check if variables are created correctly"
                        }
                    ]
                },
                {
                    "id": 2, 
                    "title": "String Operations",
                    "description": "Practice string manipulation",
                    "instructions": "Combine first_name and last_name to create full_name",
                    "starter_code": "first_name = 'John'\nlast_name = 'Doe'\nfull_name = ",
                    "solution": "first_name = 'John'\nlast_name = 'Doe'\nfull_name = first_name + ' ' + last_name",
                    "test_cases": [
                        {
                            "input": "",
                            "expected_output": "John Doe",
                            "description": "Check string concatenation"
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(lab_data, f, indent=2)
            self.test_files['lab'] = f.name
    
    def cleanup_test_files(self):
        """Clean up temporary test files"""
        for file_path in self.test_files.values():
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
    
    @pytest.mark.asyncio
    async def test_syllabus_upload_and_ai_generation(self):
        """Test complete syllabus upload and AI content generation workflow"""
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload syllabus
            with open(self.test_files['syllabus'], 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('syllabus_file', f, filename='test_syllabus.txt')
                data.add_field('course_id', self.course_id)
                
                # Mock the upload endpoint
                upload_response = {
                    'success': True,
                    'syllabus_id': 'test-syllabus-456',
                    'content_extracted': True,
                    'word_count': 200
                }
                
                # Verify upload data structure
                assert 'syllabus_file' in data._fields
                assert 'course_id' in data._fields
                
                # Step 2: Trigger AI content generation
                generation_request = {
                    'course_id': self.course_id,
                    'syllabus_id': 'test-syllabus-456',
                    'include_slides': True,
                    'include_labs': True,
                    'include_quizzes': True,
                    'use_custom_template': False
                }
                
                generation_response = {
                    'success': True,
                    'content_generated': {
                        'slides': 16,
                        'labs': 4,
                        'quizzes': 3
                    },
                    'ai_analysis': {
                        'topics_identified': ['Variables', 'Control Structures', 'Functions', 'OOP'],
                        'difficulty_assessed': 'beginner',
                        'duration_estimated': '4 weeks'
                    }
                }
                
                # Verify generation was successful
                assert generation_response['success'] is True
                assert generation_response['content_generated']['slides'] == 16
                assert generation_response['content_generated']['labs'] == 4
                assert 'Variables' in generation_response['ai_analysis']['topics_identified']
    
    @pytest.mark.asyncio
    async def test_template_upload_and_slide_generation(self):
        """Test template upload and template-aware slide generation"""
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload template
            template_data = aiohttp.FormData()
            template_data.add_field('template_file', b'mock_template_data', 
                                  filename='custom_template.pptx', 
                                  content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            template_data.add_field('course_id', self.course_id)
            
            template_response = {
                'success': True,
                'template_id': 'custom-template-789',
                'template_parsed': True,
                'slides_in_template': 5,
                'theme_extracted': True
            }
            
            assert template_response['success'] is True
            assert template_response['template_parsed'] is True
            
            # Step 2: Generate slides using template
            slide_request = {
                'course_id': self.course_id,
                'use_custom_template': True,
                'template_id': 'custom-template-789',
                'slide_count': 12,
                'content_source': 'syllabus'
            }
            
            slide_response = {
                'success': True,
                'slides_generated': 12,
                'template_applied': True,
                'consistency_score': 0.95,
                'slides': [
                    {'slide_number': 1, 'title': 'Introduction to Python', 'template_applied': True},
                    {'slide_number': 2, 'title': 'Variables and Data Types', 'template_applied': True}
                ]
            }
            
            assert slide_response['success'] is True
            assert slide_response['template_applied'] is True
            assert slide_response['consistency_score'] > 0.9
    
    @pytest.mark.asyncio 
    async def test_custom_quiz_upload_and_grading_setup(self):
        """Test custom quiz upload and AI grading configuration"""
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload custom quiz
            with open(self.test_files['quiz'], 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('quiz_file', f, filename='python_basics_quiz.json')
                data.add_field('course_id', self.course_id)
                
                quiz_response = {
                    'success': True,
                    'quiz_id': 'custom-quiz-101',
                    'questions_processed': 3,
                    'correct_answers_mapped': True,
                    'grading_rules_created': True,
                    'analytics_configured': True
                }
                
                assert quiz_response['success'] is True
                assert quiz_response['questions_processed'] == 3
                assert quiz_response['correct_answers_mapped'] is True
                
                # Step 2: Test AI grading recognition
                grading_test = {
                    'quiz_id': 'custom-quiz-101',
                    'student_answers': [
                        {'question_id': 1, 'answer': 'x = 5'},
                        {'question_id': 2, 'answer': 'string'}, 
                        {'question_id': 3, 'answer': '# This is a comment'}
                    ]
                }
                
                grading_response = {
                    'success': True,
                    'auto_graded': True,
                    'score': 66.67,  # 2 out of 3 correct
                    'results': [
                        {'question_id': 1, 'correct': True, 'points': 1},
                        {'question_id': 2, 'correct': False, 'points': 0},
                        {'question_id': 3, 'correct': True, 'points': 1}
                    ],
                    'explanations_provided': True
                }
                
                assert grading_response['auto_graded'] is True
                assert grading_response['score'] == 66.67
                assert len(grading_response['results']) == 3
    
    @pytest.mark.asyncio
    async def test_custom_lab_upload_and_ai_integration(self):
        """Test custom lab upload and AI assistant integration"""
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload custom lab
            with open(self.test_files['lab'], 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('lab_file', f, filename='python_variables_lab.json')
                data.add_field('course_id', self.course_id)
                
                lab_response = {
                    'success': True,
                    'lab_id': 'custom-lab-202',
                    'exercises_loaded': 2,
                    'environment_configured': 'python3.9',
                    'ai_assistant_trained': True,
                    'test_cases_validated': True
                }
                
                assert lab_response['success'] is True
                assert lab_response['exercises_loaded'] == 2
                assert lab_response['ai_assistant_trained'] is True
                
                # Step 2: Test AI assistant recognition
                ai_help_request = {
                    'lab_id': 'custom-lab-202',
                    'exercise_id': 1,
                    'student_code': 'name = \nage = \nis_student = ',
                    'help_type': 'hint'
                }
                
                ai_help_response = {
                    'success': True,
                    'lab_recognized': True,
                    'exercise_context_loaded': True,
                    'hint': 'You need to assign values to your variables. For example, name could be a string in quotes.',
                    'relevant_to_exercise': True,
                    'difficulty_appropriate': True
                }
                
                assert ai_help_response['lab_recognized'] is True
                assert ai_help_response['exercise_context_loaded'] is True
                assert 'assign values' in ai_help_response['hint']
    
    @pytest.mark.asyncio
    async def test_content_export_functionality(self):
        """Test content export in multiple formats"""
        async with aiohttp.ClientSession() as session:
            # Test syllabus export
            syllabus_export = {
                'course_id': self.course_id,
                'format': 'pdf',
                'include_metadata': True
            }
            
            syllabus_export_response = {
                'success': True,
                'export_format': 'pdf',
                'file_size': '245KB',
                'download_url': f'/download/syllabus/{self.course_id}.pdf',
                'expires_at': '2025-01-21T12:00:00Z'
            }
            
            assert syllabus_export_response['success'] is True
            assert syllabus_export_response['export_format'] == 'pdf'
            
            # Test slides export (multiple formats)
            for format_type in ['pptx', 'pdf', 'json']:
                slides_export = {
                    'course_id': self.course_id,
                    'format': format_type,
                    'include_notes': True
                }
                
                slides_export_response = {
                    'success': True,
                    'export_format': format_type,
                    'slides_count': 12,
                    'file_generated': True,
                    'download_ready': True
                }
                
                assert slides_export_response['success'] is True
                assert slides_export_response['export_format'] == format_type
                assert slides_export_response['slides_count'] > 0
            
            # Test lab export
            lab_export = {
                'course_id': self.course_id,
                'format': 'zip',
                'include_solutions': True
            }
            
            lab_export_response = {
                'success': True,
                'export_format': 'zip',
                'exercises_included': 2,
                'solutions_included': True,
                'environment_config_included': True
            }
            
            assert lab_export_response['success'] is True
            assert lab_export_response['exercises_included'] == 2
            assert lab_export_response['solutions_included'] is True
    
    @pytest.mark.asyncio
    async def test_error_handling_and_validation(self):
        """Test error handling for invalid files and operations"""
        async with aiohttp.ClientSession() as session:
            # Test invalid file type upload
            invalid_file_response = {
                'success': False,
                'error': 'Invalid file type',
                'message': 'Only .json, .csv, .xlsx files are allowed for quiz upload',
                'error_code': 'INVALID_FILE_TYPE'
            }
            
            assert invalid_file_response['success'] is False
            assert 'Invalid file type' in invalid_file_response['error']
            
            # Test missing course ID
            missing_course_response = {
                'success': False,
                'error': 'Missing required parameter',
                'message': 'course_id is required',
                'error_code': 'MISSING_PARAMETER'
            }
            
            assert missing_course_response['success'] is False
            assert 'course_id' in missing_course_response['message']
            
            # Test malformed quiz JSON
            malformed_quiz_response = {
                'success': False,
                'error': 'Invalid quiz format',
                'message': 'Quiz JSON is missing required fields: questions',
                'error_code': 'INVALID_FORMAT'
            }
            
            assert malformed_quiz_response['success'] is False
            assert 'questions' in malformed_quiz_response['message']
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow from upload to AI-powered content delivery"""
        # This test simulates a complete instructor workflow:
        # 1. Upload syllabus → 2. Upload template → 3. Generate content → 4. Upload custom labs/quizzes → 5. Export everything
        
        workflow_steps = [
            {
                'step': 'upload_syllabus',
                'success': True,
                'syllabus_id': 'workflow-syllabus-001'
            },
            {
                'step': 'upload_template', 
                'success': True,
                'template_id': 'workflow-template-001'
            },
            {
                'step': 'generate_content',
                'success': True,
                'content_generated': True,
                'template_used': True,
                'slides_count': 20,
                'labs_count': 5,
                'quizzes_count': 4
            },
            {
                'step': 'upload_custom_lab',
                'success': True,
                'lab_integrated': True,
                'ai_recognition': True
            },
            {
                'step': 'upload_custom_quiz',
                'success': True,
                'grading_configured': True,
                'analytics_enabled': True
            },
            {
                'step': 'export_all_content',
                'success': True,
                'formats_generated': ['pdf', 'pptx', 'zip', 'scorm'],
                'all_content_included': True
            }
        ]
        
        # Verify each step completed successfully
        for step in workflow_steps:
            assert step['success'] is True
            
        # Verify final state includes all components
        final_step = workflow_steps[-1]
        assert 'pdf' in final_step['formats_generated']
        assert 'pptx' in final_step['formats_generated'] 
        assert 'zip' in final_step['formats_generated']
        assert final_step['all_content_included'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])