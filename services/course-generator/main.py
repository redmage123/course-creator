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
    
    def generate_course_slides_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate slides based on approved syllabus modules and topics"""
        try:
            # Build comprehensive prompt using syllabus structure
            slides_prompt = f"""
            You are an expert course designer. Create a comprehensive slide deck based on this approved course syllabus:
            
            Course Overview: {syllabus['overview']}
            
            Syllabus Modules:
            {json.dumps(syllabus['modules'], indent=2)}
            
            Generate slides that cover each module and topic systematically:
            
            1. Create 1 title slide introducing the course
            2. Create 1 slide for learning objectives  
            3. For each module, create:
               - 1 module introduction slide
               - 2-3 slides per topic (covering the topic thoroughly)
               - 1 module summary slide
            4. Create 1 final course summary slide
            
            Each slide should have:
            - Specific, educational content (3-5 sentences)
            - Practical examples where relevant
            - Clear connection to learning outcomes
            - Professional, detailed information
            
            Return as JSON array with this exact structure:
            [
                {{
                    "id": "slide_1",
                    "title": "Course Title",
                    "content": "Detailed slide content...",
                    "slide_type": "title",
                    "order": 1,
                    "module_number": null
                }},
                {{
                    "id": "slide_2", 
                    "title": "Topic Title",
                    "content": "Detailed educational content...",
                    "slide_type": "content",
                    "order": 2,
                    "module_number": 1
                }}
            ]
            
            Make content specific to each topic and learning outcome. Avoid generic statements.
            """
            
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=6000,
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
            # Module introduction slide
            slides.append({
                "id": f"slide_{slide_order}",
                "title": module["title"],
                "content": f"This module covers: {', '.join(module['topics'])}. Learning outcomes: {', '.join(module['learning_outcomes'])}",
                "slide_type": "content",
                "order": slide_order,
                "module_number": module["module_number"]
            })
            slide_order += 1
            
            # Topic slides (2 slides per topic)
            for topic in module["topics"]:
                slides.append({
                    "id": f"slide_{slide_order}",
                    "title": f"{topic} - Overview",
                    "content": f"Introduction to {topic}. This topic is fundamental to understanding {module['title']}. We'll explore key concepts, practical applications, and real-world examples.",
                    "slide_type": "content",
                    "order": slide_order,
                    "module_number": module["module_number"]
                })
                slide_order += 1
                
                slides.append({
                    "id": f"slide_{slide_order}",
                    "title": f"{topic} - Implementation",
                    "content": f"Practical implementation of {topic}. Learn how to apply these concepts in real scenarios. Includes best practices, common pitfalls, and hands-on examples.",
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
            
            Generate a detailed, professional syllabus that includes:
            1. Course overview and description
            2. Learning objectives (5-7 specific objectives)
            3. Prerequisites
            4. Module breakdown with topics and learning outcomes
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
                        "duration_hours": 2,
                        "topics": ["Topic 1", "Topic 2", "Topic 3"],
                        "learning_outcomes": ["Outcome 1", "Outcome 2"],
                        "assessments": ["Assessment 1", "Assessment 2"]
                    }}
                ],
                "assessment_strategy": "How students will be evaluated",
                "resources": ["Resource 1", "Resource 2", ...]
            }}
            
            Make the content specific to {request.category} and {request.difficulty_level} level.
            Create {max(4, request.estimated_duration // 8)} modules with {request.estimated_duration // max(4, request.estimated_duration // 8)} hours each.
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
            
            # Store and return
            course_syllabi[request.course_id] = syllabus_data
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
            return {"course_id": request.course_id, "syllabus": refined}
        except:
            return {"course_id": request.course_id, "syllabus": request.current_syllabus}
    
    @app.get("/syllabus/{course_id}")
    async def get_course_syllabus(course_id: str):
        if course_id not in course_syllabi:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return {"course_id": course_id, "syllabus": course_syllabi[course_id]}
    
    @app.post("/content/generate-from-syllabus")
    async def generate_content_from_syllabus(request: dict):
        course_id = request.get('course_id')
        if course_id not in course_syllabi:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        syllabus = course_syllabi[course_id]
        slides = [{"id": f"slide_{i}", "title": f"Slide {i}", "content": "Content", "slide_type": "content", "order": i} for i in range(1, 6)]
        exercises_data = [{"id": "ex1", "title": "Exercise 1", "description": "Practice", "type": "hands_on", "difficulty": "beginner"}]
        quizzes_data = [{"id": "quiz1", "title": "Quiz 1", "description": "Test", "questions": [], "duration": 15}]
        course_slides[course_id] = slides
        exercises[course_id] = exercises_data
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
            
            Generate a detailed syllabus with:
            1. Course overview and objectives
            2. Prerequisites and target audience
            3. Module/week breakdown with topics
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
                        "duration_hours": 2,
                        "topics": ["Topic 1", "Topic 2"],
                        "learning_outcomes": ["Outcome 1", "Outcome 2"],
                        "assessments": ["Quiz 1", "Exercise 1"]
                    }}
                ],
                "assessment_strategy": "Description of how students will be evaluated",
                "resources": ["Resource 1", "Resource 2"]
            }}
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
    
    @app.post("/content/generate-from-syllabus")
    async def generate_content_from_syllabus(request: dict):
        """Generate slides, exercises, and quizzes from approved syllabus"""
        course_id = request.get('course_id')
        
        if course_id not in course_syllabi:
            raise HTTPException(status_code=404, detail="Syllabus not found. Generate syllabus first.")
        
        syllabus = course_syllabi[course_id]
        
        try:
            # Generate slides based on syllabus
            slides = generate_course_slides_from_syllabus(course_id, syllabus)
            course_slides[course_id] = slides
            
            # Generate exercises based on syllabus
            exercises_data = await generate_exercises_from_syllabus(course_id, syllabus)
            exercises[course_id] = exercises_data
            
            # Generate quizzes based on syllabus
            quizzes_data = await generate_quizzes_from_syllabus(course_id, syllabus)
            course_quizzes[course_id] = quizzes_data
            
            return {
                "course_id": course_id,
                "slides": slides,
                "exercises": exercises_data,
                "quizzes": quizzes_data,
                "message": "All content generated successfully from syllabus"
            }
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")
    
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
        """Generate exercises based on syllabus modules"""
        exercises_list = []
        
        for module in syllabus["modules"]:
            for i, topic in enumerate(module["topics"]):
                exercises_list.append({
                    "id": f"ex_{module['module_number']}_{i+1}",
                    "title": f"{topic} - Hands-on Exercise",
                    "description": f"Practice exercise for {topic}",
                    "type": "hands_on",
                    "difficulty": "beginner",
                    "instructions": [
                        f"Review the concepts of {topic}",
                        "Complete the practical tasks",
                        "Submit your solution"
                    ],
                    "expected_output": f"Demonstration of {topic} understanding",
                    "hints": [f"Focus on the key principles of {topic}"]
                })
        
        return exercises_list
    
    async def generate_quizzes_from_syllabus(course_id: str, syllabus: dict) -> List[Dict]:
        """Generate quizzes based on syllabus modules"""
        quizzes_list = []
        
        for module in syllabus["modules"]:
            quiz = {
                "id": f"quiz_{module['module_number']}",
                "title": f"{module['title']} - Assessment",
                "description": f"Quiz covering {module['title']}",
                "questions": [],
                "duration": 15,
                "difficulty": "beginner"
            }
            
            for outcome in module["learning_outcomes"]:
                quiz["questions"].append({
                    "question": f"What is the key concept related to {outcome}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0
                })
            
            quizzes_list.append(quiz)
        
        return quizzes_list