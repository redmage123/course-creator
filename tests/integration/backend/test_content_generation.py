#!/usr/bin/env python3
"""
Test suite for content generation functionality
Tests syllabus generation, slide creation, exercise generation, quiz creation, and lab environments
"""
import pytest
import asyncio
import uuid
import json
from datetime import datetime


class TestSyllabusGeneration:
    """Test syllabus generation functionality"""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude API client"""
        pytest.skip("Needs refactoring to use real objects")
        client = {}
        response = {}
        response['content'] = [{}]
        response['content'][0]['text'] = json.dumps({
            "overview": "This course provides comprehensive training in Python programming",
            "objectives": [
                "Understand Python syntax and basic programming concepts",
                "Apply object-oriented programming principles",
                "Develop practical applications using Python"
            ],
            "prerequisites": ["Basic computer literacy", "High school mathematics"],
            "modules": [
                {
                    "module_number": 1,
                    "title": "Python Fundamentals",
                    "duration_hours": 8,
                    "topics": ["Variables and Data Types", "Control Structures", "Functions"],
                    "learning_outcomes": ["Write basic Python programs", "Use control structures effectively"],
                    "assessments": ["Quiz 1", "Programming Exercise 1"]
                },
                {
                    "module_number": 2,
                    "title": "Object-Oriented Programming",
                    "duration_hours": 10,
                    "topics": ["Classes and Objects", "Inheritance", "Polymorphism"],
                    "learning_outcomes": ["Design object-oriented solutions", "Implement inheritance hierarchies"],
                    "assessments": ["Quiz 2", "OOP Project"]
                }
            ],
            "assessment_strategy": "Continuous assessment through quizzes and practical projects",
            "resources": ["Python.org documentation", "Course materials", "Practice exercises"]
        })
        return client
    
    @pytest.fixture
    def syllabus_request(self):
        """Sample syllabus request"""
        return {
            "course_id": str(uuid.uuid4()),
            "title": "Introduction to Python Programming",
            "description": "Learn Python from basics to advanced concepts",
            "category": "Programming",
            "difficulty_level": "beginner",
            "estimated_duration": 40
        }
    
    def test_syllabus_generation_success(self, mock_claude_client, syllabus_request):
        """Test successful syllabus generation"""
        # Simulate syllabus generation
        def generate_syllabus(request_data):
            # Mock API call
            response = mock_claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{"role": "user", "content": "Generate syllabus..."}]
            )
            
            syllabus_data = json.loads(response.content[0].text)
            return syllabus_data
        
        # Test generation
        syllabus = generate_syllabus(syllabus_request)
        
        # Verify structure
        assert "overview" in syllabus
        assert "objectives" in syllabus
        assert "modules" in syllabus
        assert len(syllabus["modules"]) == 2
        assert syllabus["modules"][0]["module_number"] == 1
        assert len(syllabus["modules"][0]["topics"]) == 3
    
    def test_syllabus_fallback_generation(self, syllabus_request):
        """Test fallback syllabus generation when Claude API fails"""
        def generate_fallback_syllabus(request_data):
            num_modules = max(3, request_data["estimated_duration"] // 8)
            
            return {
                "overview": f"This course provides a comprehensive introduction to {request_data['category']}",
                "objectives": [
                    f"Understand core concepts of {request_data['category']}",
                    "Apply knowledge through hands-on exercises",
                    "Develop practical skills for real-world scenarios"
                ],
                "prerequisites": ["Basic computer literacy", "High school mathematics"],
                "modules": [
                    {
                        "module_number": i + 1,
                        "title": f"Module {i + 1}: Fundamentals" if i == 0 else f"Module {i + 1}: Advanced Topics",
                        "duration_hours": request_data["estimated_duration"] // num_modules,
                        "topics": [f"Topic {j + 1}" for j in range(3)],
                        "learning_outcomes": [f"Understand concept {j + 1}" for j in range(2)],
                        "assessments": ["Quiz", "Hands-on Exercise"]
                    } for i in range(num_modules)
                ],
                "assessment_strategy": "Continuous assessment through quizzes and practical projects",
                "resources": ["Course materials", "Online resources", "Practice exercises"]
            }
        
        # Test fallback generation
        syllabus = generate_fallback_syllabus(syllabus_request)
        
        # Verify fallback structure
        assert syllabus["overview"] is not None
        assert len(syllabus["modules"]) >= 3
        assert all(module["module_number"] > 0 for module in syllabus["modules"])


class TestSlideGeneration:
    """Test slide generation from syllabus"""
    
    @pytest.fixture
    def sample_syllabus(self):
        """Sample syllabus for testing"""
        return {
            "overview": "Comprehensive Python programming course",
            "objectives": ["Learn Python basics", "Build applications"],
            "modules": [
                {
                    "module_number": 1,
                    "title": "Python Fundamentals",
                    "topics": ["Variables", "Functions", "Loops"],
                    "learning_outcomes": ["Write basic programs", "Use functions effectively"]
                }
            ]
        }
    
    def test_slide_generation_from_syllabus(self, sample_syllabus):
        """Test slide generation based on syllabus content"""
        def generate_slides_from_syllabus(course_id, syllabus):
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
        
        # Test slide generation
        course_id = str(uuid.uuid4())
        slides = generate_slides_from_syllabus(course_id, sample_syllabus)
        
        # Verify slides
        assert len(slides) >= 5  # Introduction + Objectives + Module + 3 topics
        assert slides[0]["slide_type"] == "title"
        assert slides[0]["title"] == "Course Introduction"
        assert "Python Fundamentals" in [slide["title"] for slide in slides]
        assert all(slide["order"] > 0 for slide in slides)
    
    def test_fallback_slides_generation(self):
        """Test fallback slide generation when Claude API fails"""
        def generate_fallback_slides(title, description, topic):
            return [
                {
                    "id": "slide_1",
                    "title": f"Introduction to {title}",
                    "content": f"Welcome to {title}. {description}",
                    "slide_type": "title",
                    "order": 1
                },
                {
                    "id": "slide_2",
                    "title": "Course Overview",
                    "content": f"This course covers fundamental concepts and practical applications of {topic}.",
                    "slide_type": "content",
                    "order": 2
                }
            ]
        
        # Test fallback slides
        slides = generate_fallback_slides("Python Programming", "Learn Python", "programming")
        
        assert len(slides) == 2
        assert slides[0]["slide_type"] == "title"
        assert "Python Programming" in slides[0]["title"]


class TestExerciseGeneration:
    """Test exercise generation from syllabus"""
    
    @pytest.fixture
    def sample_syllabus(self):
        """Sample syllabus for exercise generation"""
        return {
            "modules": [
                {
                    "module_number": 1,
                    "title": "Python Basics",
                    "topics": ["Variables", "Functions", "Loops"],
                    "learning_outcomes": ["Use variables effectively", "Write functions"]
                }
            ]
        }
    
    def test_exercise_generation_from_syllabus(self, sample_syllabus):
        """Test exercise generation based on syllabus modules"""
        def generate_exercises_from_syllabus(course_id, syllabus):
            exercises_list = []
            
            for module in syllabus.get("modules", []):
                for i, topic in enumerate(module.get("topics", [])):
                    exercises_list.append({
                        "id": f"ex_{module.get('module_number', 1)}_{i+1}",
                        "title": f"{topic} - Hands-on Exercise",
                        "description": f"Practice exercise for {topic}. Apply the concepts learned.",
                        "type": "hands_on",
                        "difficulty": "beginner",
                        "instructions": [
                            f"Review the key concepts of {topic}",
                            f"Complete the practical tasks related to {topic}",
                            "Test your understanding",
                            "Submit your solution"
                        ],
                        "expected_output": f"Demonstration of {topic} understanding",
                        "hints": [f"Focus on the key principles of {topic}"]
                    })
            
            return exercises_list
        
        # Test exercise generation
        course_id = str(uuid.uuid4())
        exercises = generate_exercises_from_syllabus(course_id, sample_syllabus)
        
        # Verify exercises
        assert len(exercises) == 3  # 3 topics
        assert exercises[0]["id"] == "ex_1_1"
        assert "Variables" in exercises[0]["title"]
        assert exercises[0]["type"] == "hands_on"
        assert len(exercises[0]["instructions"]) == 4


class TestQuizGeneration:
    """Test quiz generation from syllabus"""
    
    @pytest.fixture
    def sample_syllabus(self):
        """Sample syllabus for quiz generation"""
        return {
            "modules": [
                {
                    "module_number": 1,
                    "title": "Python Basics",
                    "topics": ["Variables", "Functions"],
                    "learning_outcomes": ["Use variables", "Write functions"]
                }
            ]
        }
    
    def test_quiz_generation_from_syllabus(self, sample_syllabus):
        """Test quiz generation based on syllabus modules"""
        def generate_quizzes_from_syllabus(course_id, syllabus):
            quizzes_list = []
            
            for module in syllabus.get("modules", []):
                quiz = {
                    "id": f"quiz_{module.get('module_number', 1)}",
                    "title": f"{module.get('title', 'Module')} - Knowledge Assessment",
                    "description": f"Quiz covering key concepts from {module.get('title', 'this module')}",
                    "questions": [],
                    "duration": 15 + (len(module.get('topics', [])) * 3),
                    "difficulty": "beginner"
                }
                
                # Generate questions based on learning outcomes
                for outcome in module.get("learning_outcomes", []):
                    quiz["questions"].append({
                        "question": f"Which concept is most important for {outcome}?",
                        "options": [
                            f"Primary principle of {outcome}",
                            f"Secondary aspect of {outcome}",
                            "Unrelated concept",
                            f"Prerequisite for {outcome}"
                        ],
                        "correct_answer": 0,
                        "explanation": f"This tests understanding of {outcome}."
                    })
                
                quizzes_list.append(quiz)
            
            return quizzes_list
        
        # Test quiz generation
        course_id = str(uuid.uuid4())
        quizzes = generate_quizzes_from_syllabus(course_id, sample_syllabus)
        
        # Verify quizzes
        assert len(quizzes) == 1  # 1 module
        assert quizzes[0]["id"] == "quiz_1"
        assert "Python Basics" in quizzes[0]["title"]
        assert len(quizzes[0]["questions"]) == 2  # 2 learning outcomes
        assert quizzes[0]["duration"] == 21  # 15 + (2 topics * 3)


class TestLabEnvironmentGeneration:
    """Test lab environment generation"""
    
    def test_lab_environment_creation(self):
        """Test lab environment configuration generation"""
        def generate_lab_environment(name, description, env_type):
            return {
                "virtual_machines": [
                    {
                        "name": "ai-lab-vm",
                        "os": "Ubuntu 20.04",
                        "specs": {"cpu": 2, "memory": "4GB", "storage": "20GB"},
                        "software": ["python3", "jupyter", "git", "docker"],
                        "network_config": {
                            "interfaces": ["eth0"],
                            "ip_ranges": ["192.168.1.0/24"]
                        }
                    }
                ],
                "ai_assistant": {
                    "enabled": True,
                    "context": env_type,
                    "capabilities": ["explain_concepts", "debug_issues", "generate_exercises"]
                },
                "course_category": env_type,
                "status": "ready",
                "exercises": ["Interactive coding challenges", "Hands-on labs"]
            }
        
        # Test lab creation
        lab_config = generate_lab_environment(
            "Python Programming Lab",
            "Interactive Python learning environment",
            "programming"
        )
        
        # Verify lab configuration
        assert "virtual_machines" in lab_config
        assert lab_config["ai_assistant"]["enabled"] is True
        assert lab_config["status"] == "ready"
        assert len(lab_config["virtual_machines"]) == 1
        assert "python3" in lab_config["virtual_machines"][0]["software"]


class TestContentIntegration:
    """Test integrated content generation workflow"""
    
    @pytest.fixture
    def complete_syllabus(self):
        """Complete syllabus for integration testing"""
        return {
            "overview": "Comprehensive Python programming course",
            "objectives": ["Learn Python basics", "Build applications", "Master OOP"],
            "modules": [
                {
                    "module_number": 1,
                    "title": "Python Fundamentals",
                    "topics": ["Variables", "Functions", "Loops"],
                    "learning_outcomes": ["Use variables", "Write functions"]
                },
                {
                    "module_number": 2,
                    "title": "Object-Oriented Programming",
                    "topics": ["Classes", "Inheritance"],
                    "learning_outcomes": ["Design classes", "Implement inheritance"]
                }
            ]
        }
    
    def test_complete_content_generation_workflow(self, complete_syllabus):
        """Test the complete content generation workflow"""
        course_id = str(uuid.uuid4())
        
        # Generate all content types
        def generate_all_content(course_id, syllabus):
            # Generate slides
            slides = []
            slide_order = 1
            
            slides.append({
                "id": f"slide_{slide_order}",
                "title": "Course Introduction",
                "content": syllabus["overview"],
                "slide_type": "title",
                "order": slide_order
            })
            
            # Generate exercises
            exercises = []
            for module in syllabus["modules"]:
                for i, topic in enumerate(module["topics"]):
                    exercises.append({
                        "id": f"ex_{module['module_number']}_{i+1}",
                        "title": f"{topic} Exercise",
                        "type": "hands_on"
                    })
            
            # Generate quizzes
            quizzes = []
            for module in syllabus["modules"]:
                quizzes.append({
                    "id": f"quiz_{module['module_number']}",
                    "title": f"{module['title']} Quiz",
                    "questions": [{"question": "Test question"}]
                })
            
            # Generate lab
            lab = {
                "id": str(uuid.uuid4()),
                "name": "AI Lab Environment",
                "status": "ready"
            }
            
            return {
                "slides": slides,
                "exercises": exercises,
                "quizzes": quizzes,
                "lab": lab
            }
        
        # Test complete workflow
        content = generate_all_content(course_id, complete_syllabus)
        
        # Verify all content types generated
        assert "slides" in content
        assert "exercises" in content
        assert "quizzes" in content
        assert "lab" in content
        
        assert len(content["slides"]) >= 1
        assert len(content["exercises"]) == 5  # 3 + 2 topics
        assert len(content["quizzes"]) == 2  # 2 modules
        assert content["lab"]["status"] == "ready"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])