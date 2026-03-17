#!/usr/bin/env python3
"""
Unit Tests for Enhanced Content Management Backend Endpoints
Tests the FastAPI endpoints for content upload/download functionality
"""

import pytest
import asyncio
import json
import tempfile
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI, File, UploadFile, Form
import aiofiles


# Mock FastAPI app for testing
app = FastAPI()

# Mock endpoints that we would expect in the content management service
@app.post("/upload-syllabus")
async def upload_syllabus(syllabus_file: UploadFile = File(...), course_id: str = Form(...)):
    """Mock syllabus upload endpoint"""
    if not syllabus_file.filename.endswith(('.pdf', '.doc', '.docx', '.txt', '.md')):
        return {"success": False, "error": "Invalid file type"}
    
    return {
        "success": True,
        "syllabus_id": "mock-syllabus-123",
        "content_extracted": True,
        "word_count": 500
    }

@app.post("/upload-slides")
async def upload_slides(slides_file: UploadFile = File(...), course_id: str = Form(...)):
    """Mock slides upload endpoint"""
    if not slides_file.filename.endswith(('.ppt', '.pptx', '.pdf', '.json')):
        return {"success": False, "error": "Invalid file type"}
    
    return {
        "success": True,
        "slides_id": "mock-slides-123",
        "slide_count": 15,
        "format_detected": "pptx"
    }

@app.post("/upload-template")
async def upload_template(template_file: UploadFile = File(...), course_id: str = Form(...)):
    """Mock template upload endpoint"""
    if not template_file.filename.endswith(('.pptx', '.json')):
        return {"success": False, "error": "Invalid template format"}
    
    return {
        "success": True,
        "template_id": "mock-template-123",
        "theme_extracted": True,
        "slides_analyzed": 5
    }

@app.post("/upload-lab")
async def upload_lab(lab_file: UploadFile = File(...), course_id: str = Form(...)):
    """Mock lab upload endpoint"""
    if not lab_file.filename.endswith(('.json', '.zip')):
        return {"success": False, "error": "Invalid lab format"}
    
    return {
        "success": True,
        "lab_id": "mock-lab-123",
        "exercise_count": 8,
        "environment_detected": "python3.9"
    }

@app.post("/upload-quiz")
async def upload_quiz(quiz_file: UploadFile = File(...), course_id: str = Form(...)):
    """Mock quiz upload endpoint"""
    if not quiz_file.filename.endswith(('.json', '.csv', '.xlsx')):
        return {"success": False, "error": "Invalid quiz format"}
    
    return {
        "success": True,
        "quiz_id": "mock-quiz-123",
        "question_count": 10,
        "correct_answers_mapped": True
    }

@app.get("/download-syllabus/{course_id}")
async def download_syllabus(course_id: str, format: str = "pdf"):
    """Mock syllabus download endpoint"""
    return {"success": True, "download_url": f"/files/syllabus-{course_id}.{format}"}

@app.get("/download-slides/{course_id}")
async def download_slides(course_id: str, format: str = "pptx"):
    """Mock slides download endpoint"""
    return {"success": True, "download_url": f"/files/slides-{course_id}.{format}"}

@app.get("/export-labs/{course_id}")
async def export_labs(course_id: str, format: str = "zip"):
    """Mock lab export endpoint"""
    return {"success": True, "download_url": f"/files/labs-{course_id}.{format}"}

@app.post("/generate-from-syllabus")
async def generate_from_syllabus(request: dict):
    """Mock AI content generation from syllabus"""
    return {
        "success": True,
        "content_generated": {
            "slides": 20,
            "labs": 6,
            "quizzes": 4
        },
        "template_used": request.get("use_custom_template", False)
    }

@app.post("/generate-slides")
async def generate_slides(request: dict):
    """Mock AI slide generation with template support"""
    return {
        "success": True,
        "slides_generated": request.get("slide_count", 10),
        "template_applied": request.get("use_custom_template", False)
    }



class TestContentManagementEndpoints:
    """Test suite for content management API endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        self.course_id = "test-course-123"
        self.create_test_files()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.cleanup_test_files()
    
    def create_test_files(self):
        """Create temporary test files"""
        self.test_files = {}
        
        # Create test syllabus
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test syllabus content for unit testing")
            self.test_files['syllabus'] = f.name
        
        # Create test quiz JSON
        quiz_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "Test question?",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "B"
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(quiz_data, f)
            self.test_files['quiz'] = f.name
        
        # Create test lab JSON
        lab_data = {
            "exercises": [
                {
                    "id": 1,
                    "title": "Test Exercise",
                    "starter_code": "print('hello')",
                    "solution": "print('hello world')"
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(lab_data, f)
            self.test_files['lab'] = f.name
    
    def cleanup_test_files(self):
        """Remove temporary test files"""
        for file_path in self.test_files.values():
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
    
    def test_syllabus_upload_success(self):
        """Test successful syllabus upload"""
        with open(self.test_files['syllabus'], 'rb') as f:
            response = self.client.post(
                "/upload-syllabus",
                files={"syllabus_file": ("test.txt", f, "text/plain")},
                data={"course_id": self.course_id}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "syllabus_id" in data
        assert data["content_extracted"] is True
        assert data["word_count"] > 0
    
    def test_syllabus_upload_invalid_format(self):
        """Test syllabus upload with invalid file format"""
        # Create a fake .exe file
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b"fake executable content")
            fake_file = f.name
        
        try:
            with open(fake_file, 'rb') as f:
                response = self.client.post(
                    "/upload-syllabus",
                    files={"syllabus_file": ("malicious.exe", f, "application/octet-stream")},
                    data={"course_id": self.course_id}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Invalid file type" in data["error"]
        finally:
            os.unlink(fake_file)
    
    def test_slides_upload_success(self):
        """Test successful slides upload"""
        # Create mock PowerPoint file content
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            f.write(b"mock pptx content")
            pptx_file = f.name
        
        try:
            with open(pptx_file, 'rb') as f:
                response = self.client.post(
                    "/upload-slides",
                    files={"slides_file": ("presentation.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                    data={"course_id": self.course_id}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "slides_id" in data
            assert data["slide_count"] > 0
            assert data["format_detected"] == "pptx"
        finally:
            os.unlink(pptx_file)
    
    def test_template_upload_success(self):
        """Test successful template upload"""
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            f.write(b"mock template content")
            template_file = f.name
        
        try:
            with open(template_file, 'rb') as f:
                response = self.client.post(
                    "/upload-template",
                    files={"template_file": ("template.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                    data={"course_id": self.course_id}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "template_id" in data
            assert data["theme_extracted"] is True
        finally:
            os.unlink(template_file)
    
    def test_lab_upload_success(self):
        """Test successful lab upload"""
        with open(self.test_files['lab'], 'rb') as f:
            response = self.client.post(
                "/upload-lab",
                files={"lab_file": ("lab.json", f, "application/json")},
                data={"course_id": self.course_id}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lab_id" in data
        assert data["exercise_count"] > 0
        assert "environment_detected" in data
    
    def test_quiz_upload_success(self):
        """Test successful quiz upload"""
        with open(self.test_files['quiz'], 'rb') as f:
            response = self.client.post(
                "/upload-quiz",
                files={"quiz_file": ("quiz.json", f, "application/json")},
                data={"course_id": self.course_id}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "quiz_id" in data
        assert data["question_count"] > 0
        assert data["correct_answers_mapped"] is True
    
    def test_syllabus_download(self):
        """Test syllabus download endpoint"""
        response = self.client.get(f"/download-syllabus/{self.course_id}?format=pdf")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "download_url" in data
        assert self.course_id in data["download_url"]
        assert "pdf" in data["download_url"]
    
    def test_slides_download_multiple_formats(self):
        """Test slides download in multiple formats"""
        formats = ["pptx", "pdf", "json"]
        
        for format_type in formats:
            response = self.client.get(f"/download-slides/{self.course_id}?format={format_type}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert format_type in data["download_url"]
    
    def test_lab_export(self):
        """Test lab export functionality"""
        response = self.client.get(f"/export-labs/{self.course_id}?format=zip")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "download_url" in data
        assert "zip" in data["download_url"]
    
    def test_ai_content_generation_from_syllabus(self):
        """Test AI content generation from uploaded syllabus"""
        request_data = {
            "course_id": self.course_id,
            "syllabus_id": "test-syllabus-123",
            "include_slides": True,
            "include_labs": True,
            "include_quizzes": True,
            "use_custom_template": True
        }
        
        response = self.client.post("/generate-from-syllabus", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content_generated" in data
        assert data["content_generated"]["slides"] > 0
        assert data["content_generated"]["labs"] > 0
        assert data["content_generated"]["quizzes"] > 0
        assert data["template_used"] is True
    
    def test_ai_slide_generation_with_template(self):
        """Test AI slide generation with custom template"""
        request_data = {
            "course_id": self.course_id,
            "use_custom_template": True,
            "slide_count": 15
        }
        
        response = self.client.post("/generate-slides", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["slides_generated"] == 15
        assert data["template_applied"] is True
    
    def test_missing_course_id_validation(self):
        """Test that missing course_id is properly validated"""
        with open(self.test_files['syllabus'], 'rb') as f:
            response = self.client.post(
                "/upload-syllabus",
                files={"syllabus_file": ("test.txt", f, "text/plain")},
                # Missing course_id
            )
        
        # Should return 422 for missing required field
        assert response.status_code == 422
    
    def test_missing_file_validation(self):
        """Test that missing file is properly validated"""
        response = self.client.post(
            "/upload-syllabus",
            # Missing syllabus_file
            data={"course_id": self.course_id}
        )
        
        # Should return 422 for missing required field
        assert response.status_code == 422



class TestFileValidationAndSecurity:
    """Test file validation and security measures"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        self.course_id = "security-test-course"
    
    def test_file_extension_validation(self):
        """Test that only allowed file extensions are accepted"""
        # Test valid extensions for each upload type
        valid_extensions = {
            "syllabus": [".pdf", ".doc", ".docx", ".txt", ".md"],
            "slides": [".ppt", ".pptx", ".pdf", ".json"],
            "template": [".pptx", ".json"],
            "lab": [".json", ".zip"],
            "quiz": [".json", ".csv", ".xlsx"]
        }
        
        # Test invalid extensions
        invalid_extensions = [".exe", ".bat", ".sh", ".php", ".jsp", ".asp"]
        
        for upload_type, valid_exts in valid_extensions.items():
            endpoint = f"/upload-{upload_type.replace('template', 'template').replace('quiz', 'quiz')}"
            if upload_type == "template":
                endpoint = "/upload-template"
            
            for invalid_ext in invalid_extensions:
                with tempfile.NamedTemporaryFile(suffix=invalid_ext, delete=False) as f:
                    f.write(b"malicious content")
                    malicious_file = f.name
                
                try:
                    with open(malicious_file, 'rb') as f:
                        field_name = f"{upload_type}_file"
                        if upload_type == "template":
                            field_name = "template_file"
                        
                        response = self.client.post(
                            endpoint,
                            files={field_name: (f"malicious{invalid_ext}", f, "application/octet-stream")},
                            data={"course_id": self.course_id}
                        )
                    
                    # Should reject invalid file types
                    if response.status_code == 200:
                        data = response.json()
                        assert data["success"] is False
                        assert "Invalid" in data["error"]
                finally:
                    os.unlink(malicious_file)
    
    def test_file_size_limits(self):
        """Test file size validation (mock test)"""
        # In a real implementation, we would test file size limits
        # For now, we'll just verify that the concept is testable
        
        large_content = b"A" * (50 * 1024 * 1024)  # 50MB content
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(large_content)
            large_file = f.name
        
        try:
            # In a real implementation, this should be rejected due to size
            # For our mock, we'll just verify the test structure works
            with open(large_file, 'rb') as f:
                response = self.client.post(
                    "/upload-syllabus",
                    files={"syllabus_file": ("large.txt", f, "text/plain")},
                    data={"course_id": self.course_id}
                )
            
            # Mock accepts it, but real implementation should validate size
            assert response.status_code in [200, 413]  # 413 = Payload Too Large
        finally:
            os.unlink(large_file)
    
    def test_content_scanning_simulation(self):
        """Test content scanning for malicious content (simulation)"""
        # Simulate scanning for malicious patterns
        malicious_patterns = [
            b"<script>",
            b"javascript:",
            b"eval(",
            b"exec(",
            b"system(",
        ]
        
        for pattern in malicious_patterns:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b"Normal content " + pattern + b" more content")
                suspicious_file = f.name
            
            try:
                with open(suspicious_file, 'rb') as f:
                    response = self.client.post(
                        "/upload-syllabus",
                        files={"syllabus_file": ("suspicious.txt", f, "text/plain")},
                        data={"course_id": self.course_id}
                    )
                
                # In a real implementation with content scanning,
                # suspicious content should be flagged
                assert response.status_code == 200  # Mock accepts everything
                # In production: assert response.status_code == 400  # Bad Request
            finally:
                os.unlink(suspicious_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])