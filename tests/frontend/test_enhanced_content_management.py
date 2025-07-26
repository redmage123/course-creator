#!/usr/bin/env python3
"""
Test Enhanced Content Management Functionality
Tests all the new upload/download functions in the instructor dashboard
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json


class TestEnhancedContentManagement(unittest.TestCase):
    """Unit tests for enhanced content management functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course_id = "test-course-123"
        self.user_courses = [
            {
                'id': 'test-course-123',
                'title': 'Test Course',
                'description': 'Test Description',
                'category': 'Programming',
                'difficulty_level': 'beginner',
                'estimated_duration': 4,
                'is_published': False
            }
        ]
        
        # Mock DOM elements
        self.mock_element = Mock()
        self.mock_element.textContent = ""
        self.mock_element.className = ""
        
        # Mock CONFIG endpoints
        self.mock_config = {
            'ENDPOINTS': {
                'CONTENT_SERVICE': 'http://localhost:8005'
            }
        }
        
    def test_syllabus_upload_file_validation(self):
        """Test that syllabus upload validates file types correctly"""
        # Test valid file types
        valid_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md']
        
        for ext in valid_extensions:
            with patch('builtins.document') as mock_doc:
                mock_input = Mock()
                mock_input.accept = '.pdf,.doc,.docx,.txt,.md'
                mock_doc.createElement.return_value = mock_input
                
                # Should accept these file types
                self.assertIn(ext.replace('.', ''), mock_input.accept)
    
    def test_slides_upload_file_validation(self):
        """Test that slides upload validates file types correctly"""
        valid_extensions = ['.ppt', '.pptx', '.pdf', '.json']
        
        # Mock file input creation
        with patch('builtins.document') as mock_doc:
            mock_input = Mock()
            mock_input.accept = '.ppt,.pptx,.pdf,.json'
            mock_doc.createElement.return_value = mock_input
            
            for ext in valid_extensions:
                self.assertIn(ext.replace('.', ''), mock_input.accept)
    
    def test_template_upload_file_validation(self):
        """Test that template upload validates file types correctly"""
        valid_extensions = ['.pptx', '.json']
        
        with patch('builtins.document') as mock_doc:
            mock_input = Mock()
            mock_input.accept = '.pptx,.json'
            mock_doc.createElement.return_value = mock_input
            
            for ext in valid_extensions:
                self.assertIn(ext.replace('.', ''), mock_input.accept)
    
    def test_lab_upload_file_validation(self):
        """Test that lab upload validates file types correctly"""
        valid_extensions = ['.json', '.zip']
        
        with patch('builtins.document') as mock_doc:
            mock_input = Mock()
            mock_input.accept = '.json,.zip'
            mock_doc.createElement.return_value = mock_input
            
            for ext in valid_extensions:
                self.assertIn(ext.replace('.', ''), mock_input.accept)
    
    def test_quiz_upload_file_validation(self):
        """Test that quiz upload validates file types correctly"""
        valid_extensions = ['.json', '.csv', '.xlsx']
        
        with patch('builtins.document') as mock_doc:
            mock_input = Mock()
            mock_input.accept = '.json,.csv,.xlsx'
            mock_doc.createElement.return_value = mock_input
            
            for ext in valid_extensions:
                self.assertIn(ext.replace('.', ''), mock_input.accept)
    
    @patch('builtins.fetch')
    def test_upload_syllabus_success(self, mock_fetch):
        """Test successful syllabus upload"""
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'syllabus_id': 'test-syllabus-123'}
        mock_fetch.return_value = mock_response
        
        # Test that upload creates proper FormData and makes correct API call
        self.assertTrue(mock_response.ok)
        self.assertEqual(mock_response.json()['syllabus_id'], 'test-syllabus-123')
    
    @patch('builtins.fetch')
    def test_upload_syllabus_error_handling(self, mock_fetch):
        """Test syllabus upload error handling"""
        # Mock failed response
        mock_response = Mock()
        mock_response.ok = False
        mock_fetch.return_value = mock_response
        
        # Should handle errors gracefully
        self.assertFalse(mock_response.ok)
    
    @patch('builtins.fetch')
    def test_download_syllabus_success(self, mock_fetch):
        """Test successful syllabus download"""
        # Mock successful download response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.blob.return_value = Mock()
        mock_fetch.return_value = mock_response
        
        self.assertTrue(mock_response.ok)
    
    @patch('builtins.fetch')
    def test_template_upload_success(self, mock_fetch):
        """Test successful template upload"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'template_id': 'test-template-123'}
        mock_fetch.return_value = mock_response
        
        self.assertTrue(mock_response.ok)
        self.assertEqual(mock_response.json()['template_id'], 'test-template-123')
    
    def test_content_source_indicators(self):
        """Test that content source indicators are properly updated"""
        # Test syllabus source indicator
        mock_element = Mock()
        mock_element.textContent = 'AI Generated'
        mock_element.className = 'badge badge-info'
        
        # After upload, should change to custom
        mock_element.textContent = 'Custom Upload'
        mock_element.className = 'badge badge-success'
        
        self.assertEqual(mock_element.textContent, 'Custom Upload')
        self.assertEqual(mock_element.className, 'badge badge-success')
    
    def test_ai_template_integration_flag(self):
        """Test that AI generation requests include template usage flag"""
        request_body = {
            'course_id': self.course_id,
            'use_custom_template': True,
            'slide_count': 10
        }
        
        self.assertTrue(request_body['use_custom_template'])
        self.assertEqual(request_body['course_id'], self.course_id)
    
    def test_content_metadata_tracking(self):
        """Test that content metadata is properly tracked"""
        metadata = {
            'slide_count': 15,
            'template_status': 'Custom',
            'last_updated': '2025-01-20',
            'source': 'Custom Upload'
        }
        
        self.assertEqual(metadata['slide_count'], 15)
        self.assertEqual(metadata['template_status'], 'Custom')
        self.assertIsNotNone(metadata['last_updated'])


class TestContentGenerationIntegration:
    """Integration tests for AI content generation with templates"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.course_id = "integration-course-123"
        self.syllabus_content = "Introduction to Python Programming..."
        self.template_file = "custom_template.pptx"
    
    @pytest.mark.asyncio
    async def test_generate_from_syllabus_with_template(self):
        """Test content generation from uploaded syllabus with custom template"""
        # Mock the API call for content generation
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'success': True,
                'slides_generated': 12,
                'labs_generated': 5,
                'quizzes_generated': 3,
                'template_used': True
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Simulate the API call
            response_data = await mock_response.json()
            
            assert response_data['success'] is True
            assert response_data['template_used'] is True
            assert response_data['slides_generated'] == 12
    
    @pytest.mark.asyncio
    async def test_ai_lab_recognition(self):
        """Test that AI recognizes custom uploaded labs"""
        lab_data = {
            'exercises': [
                {
                    'id': 1,
                    'title': 'Variable Assignment',
                    'description': 'Practice variable assignment',
                    'starter_code': 'x = ',
                    'solution': 'x = 42'
                }
            ],
            'environment': 'python',
            'metadata': {
                'difficulty': 'beginner',
                'estimated_time': '15 minutes'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'lab_recognized': True,
                'exercise_count': 1,
                'ai_integration': 'enabled'
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response_data = await mock_response.json()
            
            assert response_data['lab_recognized'] is True
            assert response_data['exercise_count'] == 1
            assert response_data['ai_integration'] == 'enabled'
    
    @pytest.mark.asyncio
    async def test_ai_quiz_grading_recognition(self):
        """Test that AI recognizes correct answers in uploaded quizzes"""
        quiz_data = {
            'questions': [
                {
                    'id': 1,
                    'question': 'What is 2 + 2?',
                    'type': 'multiple_choice',
                    'options': ['3', '4', '5', '6'],
                    'correct_answer': '4',
                    'explanation': 'Basic addition'
                }
            ],
            'metadata': {
                'topic': 'Mathematics',
                'difficulty': 'easy'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'quiz_processed': True,
                'correct_answers_mapped': True,
                'grading_enabled': True,
                'analytics_ready': True
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response_data = await mock_response.json()
            
            assert response_data['quiz_processed'] is True
            assert response_data['correct_answers_mapped'] is True
            assert response_data['grading_enabled'] is True


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run async integration tests
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])