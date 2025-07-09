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
        allow_origins=cfg.cors.origins,
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
    active_labs = {}
    student_progress = {}
    course_quizzes = {}
    lab_analytics = {}
    
    # Initialize Claude client
    import os
    claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_CLAUDE_API_KEY"))
    
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
        
        return {"course_id": request.course_id, "slides": slides_data}
    
    @app.get("/slides/{course_id}")
    async def get_course_slides(course_id: str):
        if course_id not in course_slides:
            raise HTTPException(status_code=404, detail="Slides not found for this course")
        return {"course_id": course_id, "slides": course_slides[course_id]}
    
    @app.put("/slides/update/{course_id}")
    async def update_course_slides(course_id: str, request: dict):
        """Update slides for a course"""
        logger.info(f"Updating slides for course: {course_id}")
        
        slides_data = request.get('slides', [])
        course_slides[course_id] = slides_data
        
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
        
        return {"access_url": f"lab://localhost:8001/lab/{course_id}", "status": "running"}
    
    @app.post("/lab/chat")
    async def chat_with_trainer(request: ChatRequest):
        """Chat with AI expert trainer"""
        if request.course_id not in active_labs:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        lab = active_labs[request.course_id]
        
        # Update analytics
        lab_analytics[request.course_id]["ai_interactions"] += 1
        
        # Create context-aware prompt
        context_prompt = f"""
        {lab['trainer_context']}
        
        Current Context:
        - Course: {request.context.get('course_title', 'Unknown')}
        - Student Progress: {request.context.get('student_progress', {})}
        - User Message: {request.user_message}
        
        Respond as the expert trainer, providing helpful, educational guidance.
        """
        
        try:
            # Call Claude API
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": context_prompt}
                ]
            )
            
            trainer_response = response.content[0].text
            
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
                "progress_update": None
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
    
    def generate_course_slides(title: str, description: str, topic: str) -> List[Dict]:
        """Generate comprehensive course slides using Claude AI"""
        try:
            slides_prompt = f"""
            You are an expert course designer. Create a comprehensive slide deck for "{title}" covering {topic}.
            Course description: {description}
            
            Create 10-15 slides with substantial, educational content. Each slide should have 3-5 sentences of detailed information.
            
            Requirements:
            1. Start with introduction slide
            2. Cover fundamental concepts thoroughly  
            3. Include practical examples and use cases
            4. Add implementation details where relevant
            5. Include best practices and common pitfalls
            6. End with summary and next steps
            
            Make content educational and detailed - avoid generic statements. Include specific examples, code snippets (if applicable), and actionable insights.
            
            Return as JSON array: [{{"id": "slide_1", "title": "Slide Title", "content": "Detailed educational content with specific examples and practical information.", "slide_type": "title", "order": 1}}]
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
                # Ensure each slide has an ID and proper order
                for i, slide in enumerate(slides_data):
                    slide["id"] = f"slide_{i+1}"
                    slide["order"] = i + 1
                return slides_data
            except:
                # Fallback to parsing text response
                return parse_slides_from_text(response.content[0].text, title, topic)
                
        except Exception as e:
            logger.error(f"Claude slide generation error: {e}")
            return generate_fallback_slides(title, description, topic)
    
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
    main()