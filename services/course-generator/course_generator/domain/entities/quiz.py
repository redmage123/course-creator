"""
Quiz Domain Entities
Single Responsibility: Represent quiz and assessment domain concepts
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

@dataclass
class QuizQuestion:
    """Domain entity representing a quiz question"""
    question: str
    options: List[str]
    correct_answer: int
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    id: Optional[str] = None
    explanation: Optional[str] = None
    points: int = 1
    difficulty: str = "medium"
    topic: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.question or len(self.question.strip()) == 0:
            raise ValueError("Question text cannot be empty")
        
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if not self.options or len(self.options) < 2:
                raise ValueError("Multiple choice questions must have at least 2 options")
            
            if self.correct_answer < 0 or self.correct_answer >= len(self.options):
                raise ValueError("Correct answer index must be valid for the given options")
        
        if self.question_type == QuestionType.TRUE_FALSE:
            if len(self.options) != 2:
                raise ValueError("True/False questions must have exactly 2 options")
            
            if self.correct_answer not in [0, 1]:
                raise ValueError("True/False correct answer must be 0 or 1")
        
        if self.points <= 0:
            raise ValueError("Question points must be positive")
    
    def is_correct_answer(self, answer_index: int) -> bool:
        """Check if the given answer index is correct"""
        return answer_index == self.correct_answer
    
    def get_correct_option(self) -> str:
        """Get the text of the correct option"""
        if self.options and 0 <= self.correct_answer < len(self.options):
            return self.options[self.correct_answer]
        return ""
    
    def add_option(self, option: str) -> None:
        """Add an option to the question"""
        if not option or len(option.strip()) == 0:
            raise ValueError("Option text cannot be empty")
        
        self.options.append(option.strip())
    
    def update_explanation(self, explanation: str) -> None:
        """Update the explanation for the question"""
        self.explanation = explanation.strip() if explanation else None

@dataclass
class Quiz:
    """Domain entity representing a quiz"""
    course_id: str
    title: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    id: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 1
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_results_immediately: bool = True
    passing_score: int = 70
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Quiz title cannot be empty")
        
        if not self.topic or len(self.topic.strip()) == 0:
            raise ValueError("Quiz topic cannot be empty")
        
        if not self.questions:
            raise ValueError("Quiz must have at least one question")
        
        if self.time_limit_minutes is not None and self.time_limit_minutes <= 0:
            raise ValueError("Time limit must be positive")
        
        if self.max_attempts <= 0:
            raise ValueError("Max attempts must be positive")
        
        if not (0 <= self.passing_score <= 100):
            raise ValueError("Passing score must be between 0 and 100")
        
        # Validate all questions
        for question in self.questions:
            question.validate()
    
    def add_question(self, question: QuizQuestion) -> None:
        """Add a question to the quiz"""
        question.validate()
        self.questions.append(question)
        self.updated_at = datetime.utcnow()
    
    def remove_question(self, question_id: str) -> bool:
        """Remove a question from the quiz"""
        for i, question in enumerate(self.questions):
            if question.id == question_id:
                self.questions.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_question_by_id(self, question_id: str) -> Optional[QuizQuestion]:
        """Get a question by its ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def get_total_points(self) -> int:
        """Get total points for the quiz"""
        return sum(question.points for question in self.questions)
    
    def get_question_count(self) -> int:
        """Get number of questions in the quiz"""
        return len(self.questions)
    
    def calculate_score(self, answers: List[int]) -> Dict[str, any]:
        """Calculate score based on answers"""
        if len(answers) != len(self.questions):
            raise ValueError("Number of answers must match number of questions")
        
        correct_count = 0
        total_points = 0
        earned_points = 0
        
        for i, (question, answer) in enumerate(zip(self.questions, answers)):
            total_points += question.points
            if question.is_correct_answer(answer):
                correct_count += 1
                earned_points += question.points
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return {
            'correct_answers': correct_count,
            'total_questions': len(self.questions),
            'earned_points': earned_points,
            'total_points': total_points,
            'percentage': round(percentage, 2),
            'passed': percentage >= self.passing_score
        }
    
    def is_time_limited(self) -> bool:
        """Check if quiz has a time limit"""
        return self.time_limit_minutes is not None

@dataclass
class QuizAttempt:
    """Domain entity representing a quiz attempt"""
    student_id: str
    quiz_id: str
    course_id: str
    answers: List[int]
    id: Optional[str] = None
    score: Optional[float] = None
    total_questions: Optional[int] = None
    earned_points: Optional[int] = None
    total_points: Optional[int] = None
    passed: Optional[bool] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_taken_minutes: Optional[int] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.started_at:
            self.started_at = datetime.utcnow()
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules"""
        if not self.student_id:
            raise ValueError("Student ID is required")
        
        if not self.quiz_id:
            raise ValueError("Quiz ID is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not isinstance(self.answers, list):
            raise ValueError("Answers must be a list")
        
        if self.score is not None and not (0 <= self.score <= 100):
            raise ValueError("Score must be between 0 and 100")
    
    def complete(self, quiz: Quiz) -> None:
        """Complete the quiz attempt with scoring"""
        if self.completed_at:
            raise ValueError("Quiz attempt is already completed")
        
        # Calculate score
        score_result = quiz.calculate_score(self.answers)
        
        self.score = score_result['percentage']
        self.total_questions = score_result['total_questions']
        self.earned_points = score_result['earned_points']
        self.total_points = score_result['total_points']
        self.passed = score_result['passed']
        self.completed_at = datetime.utcnow()
        
        # Calculate time taken
        if self.started_at:
            time_diff = self.completed_at - self.started_at
            self.time_taken_minutes = int(time_diff.total_seconds() / 60)
    
    def is_completed(self) -> bool:
        """Check if attempt is completed"""
        return self.completed_at is not None
    
    def get_duration_minutes(self) -> Optional[int]:
        """Get attempt duration in minutes"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60)
    
    def is_within_time_limit(self, time_limit_minutes: int) -> bool:
        """Check if attempt is within time limit"""
        duration = self.get_duration_minutes()
        return duration is None or duration <= time_limit_minutes

@dataclass
class QuizGenerationRequest:
    """Value object for quiz generation requests"""
    course_id: str
    topic: str
    difficulty: str
    question_count: int
    difficulty_level: str
    instructor_context: Dict
    student_tracking: Dict
    
    def validate(self) -> None:
        """Validate generation request"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.topic or len(self.topic.strip()) == 0:
            raise ValueError("Topic is required")
        
        if self.question_count <= 0:
            raise ValueError("Question count must be positive")
        
        if self.question_count > 50:
            raise ValueError("Question count cannot exceed 50")
        
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if self.difficulty not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of: {', '.join(valid_difficulties)}")
        
        if not isinstance(self.instructor_context, dict):
            raise ValueError("Instructor context must be a dictionary")
        
        if not isinstance(self.student_tracking, dict):
            raise ValueError("Student tracking must be a dictionary")