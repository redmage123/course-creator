"""
Quiz Generation Service Implementation
Single Responsibility: Implement quiz generation business logic
Dependency Inversion: Depends on repository and AI service abstractions
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from domain.entities.quiz import Quiz, QuizQuestion, QuizAttempt, QuizGenerationRequest, QuestionType, DifficultyLevel
from domain.interfaces.content_generation_service import IQuizGenerationService
# Repository pattern removed - using DAO
from data_access.course_generator_dao import CourseGeneratorDAO
from domain.interfaces.ai_service import IAIService, ContentGenerationType, IPromptTemplateService

class QuizGenerationService(IQuizGenerationService):
    """
    Quiz generation service implementation with business logic
    """
    
    def __init__(self, 
                 dao: CourseGeneratorDAO,
                 ai_service: IAIService,
                 prompt_service: IPromptTemplateService):
        self._dao = dao
        self._ai_service = ai_service
        self._prompt_service = prompt_service
    
    async def generate_quiz(self, request: QuizGenerationRequest) -> Quiz:
        """Generate a complete quiz based on request parameters"""
        # Validate request
        request.validate()
        
        # Generate quiz questions using AI
        questions = await self.generate_quiz_questions(
            request.topic,
            request.difficulty,
            request.question_count,
            {
                'course_id': request.course_id,
                'difficulty_level': request.difficulty_level,
                'instructor_context': request.instructor_context,
                'student_tracking': request.student_tracking
            }
        )
        
        # Create quiz entity
        quiz = Quiz(
            course_id=request.course_id,
            title=f"{request.topic} Quiz",
            topic=request.topic,
            difficulty=request.difficulty,
            questions=questions,
            description=f"Auto-generated quiz on {request.topic}",
            time_limit_minutes=self._calculate_time_limit(request.question_count, request.difficulty),
            passing_score=self._calculate_passing_score(request.difficulty)
        )
        
        # Save to repository
        return await self._dao.create_quiz(quiz)
    
    async def generate_quiz_questions(self, topic: str, difficulty: str, 
                                     question_count: int, context: Dict[str, Any] = None) -> List[QuizQuestion]:
        """Generate quiz questions for a topic"""
        if not topic or len(topic.strip()) == 0:
            raise ValueError("Topic is required")
        
        if question_count <= 0:
            raise ValueError("Question count must be positive")
        
        if question_count > 50:
            raise ValueError("Question count cannot exceed 50")
        
        # Prepare generation context
        generation_context = {
            'topic': topic,
            'difficulty': difficulty,
            'question_count': question_count,
            'context': context or {}
        }
        
        # Get prompt template
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.QUIZ, "multiple_choice"
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, generation_context)
        
        # Generate structured quiz content
        quiz_schema = self._get_quiz_questions_schema(question_count)
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.QUIZ,
            prompt,
            quiz_schema,
            generation_context
        )
        
        # Convert to QuizQuestion entities
        questions = []
        for i, question_data in enumerate(generated_content.get('questions', [])):
            question = QuizQuestion(
                question=question_data['question'],
                options=question_data['options'],
                correct_answer=question_data['correct_answer'],
                explanation=question_data.get('explanation'),
                points=question_data.get('points', 1),
                difficulty=difficulty,
                topic=topic
            )
            questions.append(question)
        
        return questions
    
    async def generate_adaptive_quiz(self, course_id: str, student_progress: Dict[str, Any], 
                                    context: Dict[str, Any]) -> Quiz:
        """Generate an adaptive quiz based on student performance"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not isinstance(student_progress, dict):
            raise ValueError("Student progress must be a dictionary")
        
        # Analyze student performance to determine quiz parameters
        quiz_params = self._analyze_student_performance(student_progress)
        
        # Create adaptive quiz request
        adaptive_request = QuizGenerationRequest(
            course_id=course_id,
            topic=quiz_params['recommended_topic'],
            difficulty=quiz_params['recommended_difficulty'],
            question_count=quiz_params['recommended_question_count'],
            difficulty_level=quiz_params['recommended_difficulty'],
            instructor_context=context.get('instructor_context', {}),
            student_tracking=student_progress
        )
        
        # Generate personalized questions
        questions = await self._generate_personalized_questions(adaptive_request, student_progress)
        
        # Create adaptive quiz
        quiz = Quiz(
            course_id=course_id,
            title=f"Adaptive Quiz - {quiz_params['recommended_topic']}",
            topic=quiz_params['recommended_topic'],
            difficulty=quiz_params['recommended_difficulty'],
            questions=questions,
            description="Personalized quiz based on your learning progress",
            time_limit_minutes=quiz_params['time_limit'],
            passing_score=quiz_params['passing_score'],
            max_attempts=quiz_params['max_attempts']
        )
        
        return await self._dao.create_quiz(quiz)
    
    async def validate_quiz_answers(self, quiz: Quiz, answers: List[int]) -> Dict[str, Any]:
        """Validate quiz answers and calculate score"""
        if not quiz:
            raise ValueError("Quiz is required")
        
        if not isinstance(answers, list):
            raise ValueError("Answers must be a list")
        
        # Use quiz entity's business logic for scoring
        score_result = quiz.calculate_score(answers)
        
        return {
            'quiz_id': quiz.id,
            'total_questions': score_result['total_questions'],
            'correct_answers': score_result['correct_answers'],
            'score_percentage': score_result['percentage'],
            'earned_points': score_result['earned_points'],
            'total_points': score_result['total_points'],
            'passed': score_result['passed'],
            'detailed_results': self._get_detailed_results(quiz, answers)
        }
    
    # Helper methods
    def _calculate_time_limit(self, question_count: int, difficulty: str) -> Optional[int]:
        """Calculate appropriate time limit based on question count and difficulty"""
        base_time_per_question = {
            'beginner': 2,      # 2 minutes per question
            'intermediate': 3,   # 3 minutes per question
            'advanced': 4       # 4 minutes per question
        }
        
        time_per_question = base_time_per_question.get(difficulty, 3)
        return question_count * time_per_question
    
    def _calculate_passing_score(self, difficulty: str) -> int:
        """Calculate passing score based on difficulty"""
        passing_scores = {
            'beginner': 60,
            'intermediate': 70,
            'advanced': 75
        }
        
        return passing_scores.get(difficulty, 70)
    
    def _get_quiz_questions_schema(self, question_count: int) -> Dict[str, Any]:
        """Get schema for quiz questions generation"""
        return {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "minItems": question_count,
                    "maxItems": question_count,
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question text"
                            },
                            "options": {
                                "type": "array",
                                "minItems": 4,
                                "maxItems": 4,
                                "items": {"type": "string"},
                                "description": "Four answer options"
                            },
                            "correct_answer": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 3,
                                "description": "Index of correct answer (0-3)"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Explanation for the correct answer"
                            },
                            "points": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5,
                                "description": "Points for this question"
                            }
                        },
                        "required": ["question", "options", "correct_answer", "explanation"]
                    }
                }
            },
            "required": ["questions"]
        }
    
    def _analyze_student_performance(self, student_progress: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze student performance to determine optimal quiz parameters"""
        # Extract performance metrics
        completion_rate = student_progress.get('completed_exercises', 0) / max(student_progress.get('total_exercises', 1), 1) * 100
        avg_quiz_score = sum(student_progress.get('quiz_scores', [])) / max(len(student_progress.get('quiz_scores', [])), 1)
        current_level = student_progress.get('current_level', 'beginner')
        knowledge_areas = student_progress.get('knowledge_areas', [])
        
        # Determine recommended parameters
        if avg_quiz_score >= 85 and completion_rate >= 70:
            # High performer - give challenging content
            recommended_difficulty = 'advanced'
            recommended_question_count = 15
            time_limit = 45
            passing_score = 80
            max_attempts = 2
        elif avg_quiz_score >= 70 and completion_rate >= 50:
            # Average performer - standard content
            recommended_difficulty = 'intermediate'
            recommended_question_count = 12
            time_limit = 30
            passing_score = 70
            max_attempts = 3
        else:
            # Struggling student - easier content with more support
            recommended_difficulty = 'beginner'
            recommended_question_count = 10
            time_limit = 25
            passing_score = 60
            max_attempts = 3
        
        # Select topic based on knowledge areas or weaknesses
        if knowledge_areas:
            recommended_topic = knowledge_areas[-1]  # Most recent area
        else:
            recommended_topic = 'fundamentals'
        
        return {
            'recommended_difficulty': recommended_difficulty,
            'recommended_question_count': recommended_question_count,
            'recommended_topic': recommended_topic,
            'time_limit': time_limit,
            'passing_score': passing_score,
            'max_attempts': max_attempts
        }
    
    async def _generate_personalized_questions(self, request: QuizGenerationRequest, 
                                             student_progress: Dict[str, Any]) -> List[QuizQuestion]:
        """Generate personalized questions based on student progress"""
        # Prepare personalization context
        personalization_context = {
            'topic': request.topic,
            'difficulty': request.difficulty,
            'question_count': request.question_count,
            'student_progress': student_progress,
            'personalization_enabled': True
        }
        
        # Get personalized prompt template
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.QUIZ, "adaptive"
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, personalization_context)
        
        # Generate personalized questions
        quiz_schema = self._get_quiz_questions_schema(request.question_count)
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.QUIZ,
            prompt,
            quiz_schema,
            personalization_context
        )
        
        # Convert to QuizQuestion entities
        questions = []
        for question_data in generated_content.get('questions', []):
            question = QuizQuestion(
                question=question_data['question'],
                options=question_data['options'],
                correct_answer=question_data['correct_answer'],
                explanation=question_data.get('explanation'),
                points=question_data.get('points', 1),
                difficulty=request.difficulty,
                topic=request.topic
            )
            questions.append(question)
        
        return questions
    
    def _get_detailed_results(self, quiz: Quiz, answers: List[int]) -> List[Dict[str, Any]]:
        """Get detailed results for each question"""
        detailed_results = []
        
        for i, (question, answer) in enumerate(zip(quiz.questions, answers)):
            is_correct = question.is_correct_answer(answer)
            
            result = {
                'question_number': i + 1,
                'question_text': question.question,
                'student_answer_index': answer,
                'student_answer_text': question.options[answer] if 0 <= answer < len(question.options) else "No answer",
                'correct_answer_index': question.correct_answer,
                'correct_answer_text': question.get_correct_option(),
                'is_correct': is_correct,
                'points_awarded': question.points if is_correct else 0,
                'points_possible': question.points,
                'explanation': question.explanation
            }
            
            detailed_results.append(result)
        
        return detailed_results