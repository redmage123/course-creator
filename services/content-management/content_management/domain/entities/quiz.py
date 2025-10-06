"""
Quiz Entity - Domain Layer  
Single Responsibility: Quiz-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from content_management.domain.entities.base_content import BaseContent, ContentType


class QuestionType(Enum):
    """Question type enumeration"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"


class DifficultyLevel(Enum):
    """Difficulty level enumeration"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuizQuestion:
    """Quiz question value object"""
    
    def __init__(
        self,
        question_text: str,
        question_type: QuestionType,
        points: float = 1.0,
        options: Optional[List[str]] = None,
        correct_answers: Optional[List[str]] = None,
        explanation: Optional[str] = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        tags: Optional[List[str]] = None
    ):
        self.question_text = question_text
        self.question_type = question_type
        self.points = points
        self.options = options or []
        self.correct_answers = correct_answers or []
        self.explanation = explanation or ""
        self.difficulty = difficulty
        self.tags = tags or []
        
        self.validate()
    
    def validate(self) -> None:
        """Validate question"""
        if not self.question_text:
            raise ValueError("Question text is required")
        if self.points <= 0:
            raise ValueError("Points must be positive")
        
        # Type-specific validation
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if len(self.options) < 2:
                raise ValueError("Multiple choice questions need at least 2 options")
            if not self.correct_answers:
                raise ValueError("Multiple choice questions need correct answers")
        
        elif self.question_type == QuestionType.TRUE_FALSE:
            if len(self.options) != 2 or set(self.options) != {"True", "False"}:
                raise ValueError("True/False questions must have exactly True and False options")
            if len(self.correct_answers) != 1 or self.correct_answers[0] not in ["True", "False"]:
                raise ValueError("True/False questions must have exactly one correct answer (True or False)")
    
    def add_option(self, option: str) -> None:
        """Add answer option"""
        if option and option not in self.options:
            self.options.append(option)
    
    def set_correct_answer(self, answer: str) -> None:
        """Set correct answer for single-answer questions"""
        self.correct_answers = [answer]
    
    def add_correct_answer(self, answer: str) -> None:
        """Add correct answer for multiple-answer questions"""
        if answer and answer not in self.correct_answers:
            self.correct_answers.append(answer)
    
    def is_correct_answer(self, answer: str) -> bool:
        """Check if answer is correct"""
        return answer in self.correct_answers
    
    def get_max_points(self) -> float:
        """Get maximum points for this question"""
        return self.points
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "points": self.points,
            "options": self.options,
            "correct_answers": self.correct_answers,
            "explanation": self.explanation,
            "difficulty": self.difficulty.value,
            "tags": self.tags
        }


class QuizSettings:
    """Quiz settings value object"""
    
    def __init__(
        self,
        time_limit_minutes: Optional[int] = None,
        attempts_allowed: int = 1,
        shuffle_questions: bool = False,
        shuffle_options: bool = False,
        show_correct_answers: bool = True,
        show_results_immediately: bool = True,
        require_password: bool = False,
        password: Optional[str] = None
    ):
        self.time_limit_minutes = time_limit_minutes
        self.attempts_allowed = attempts_allowed
        self.shuffle_questions = shuffle_questions
        self.shuffle_options = shuffle_options
        self.show_correct_answers = show_correct_answers
        self.show_results_immediately = show_results_immediately
        self.require_password = require_password
        self.password = password
        
        self.validate()
    
    def validate(self) -> None:
        """Validate quiz settings"""
        if self.time_limit_minutes is not None and self.time_limit_minutes <= 0:
            raise ValueError("Time limit must be positive")
        if self.attempts_allowed <= 0:
            raise ValueError("Attempts allowed must be positive")
        if self.require_password and not self.password:
            raise ValueError("Password is required when password protection is enabled")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "time_limit_minutes": self.time_limit_minutes,
            "attempts_allowed": self.attempts_allowed,
            "shuffle_questions": self.shuffle_questions,
            "shuffle_options": self.shuffle_options,
            "show_correct_answers": self.show_correct_answers,
            "show_results_immediately": self.show_results_immediately,
            "require_password": self.require_password,
            "password": self.password if self.require_password else None
        }


class Quiz(BaseContent):
    """
    Quiz domain entity following SOLID principles
    Single Responsibility: Quiz-specific business logic
    """
    
    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        questions: List[QuizQuestion],
        id: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[QuizSettings] = None,
        passing_score: float = 70.0,
        **kwargs
    ):
        # Initialize base content
        super().__init__(
            title=title,
            course_id=course_id,
            created_by=created_by,
            id=id,
            description=description,
            **kwargs
        )
        
        # Quiz-specific attributes
        self.questions = questions
        self.settings = settings or QuizSettings()
        self.passing_score = passing_score
        
        # Additional validation
        self._validate_quiz()
    
    def get_content_type(self) -> ContentType:
        """Get content type"""
        return ContentType.QUIZ
    
    def _validate_quiz(self) -> None:
        """Validate quiz-specific data"""
        if not self.questions:
            raise ValueError("Quiz must have at least one question")
        if not (0 <= self.passing_score <= 100):
            raise ValueError("Passing score must be between 0 and 100")
    
    def add_question(self, question: QuizQuestion) -> None:
        """Add question to quiz"""
        self.questions.append(question)
        self._mark_updated()
    
    def remove_question(self, index: int) -> bool:
        """Remove question by index"""
        if 0 <= index < len(self.questions):
            del self.questions[index]
            self._mark_updated()
            return True
        return False
    
    def update_question(self, index: int, question: QuizQuestion) -> bool:
        """Update question at index"""
        if 0 <= index < len(self.questions):
            self.questions[index] = question
            self._mark_updated()
            return True
        return False
    
    def get_question(self, index: int) -> Optional[QuizQuestion]:
        """Get question by index"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
    
    def update_settings(self, settings: QuizSettings) -> None:
        """Update quiz settings"""
        self.settings = settings
        self._mark_updated()
    
    def set_passing_score(self, score: float) -> None:
        """Set passing score"""
        if not (0 <= score <= 100):
            raise ValueError("Passing score must be between 0 and 100")
        self.passing_score = score
        self._mark_updated()
    
    def get_total_points(self) -> float:
        """Calculate total points possible"""
        return sum(question.points for question in self.questions)
    
    def get_question_count(self) -> int:
        """Get number of questions"""
        return len(self.questions)
    
    def get_average_difficulty(self) -> str:
        """Get average difficulty level"""
        if not self.questions:
            return DifficultyLevel.MEDIUM.value
        
        difficulty_values = {
            DifficultyLevel.EASY: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HARD: 3
        }
        
        total_difficulty = sum(
            difficulty_values[question.difficulty] for question in self.questions
        )
        avg_difficulty = total_difficulty / len(self.questions)
        
        if avg_difficulty <= 1.5:
            return DifficultyLevel.EASY.value
        elif avg_difficulty <= 2.5:
            return DifficultyLevel.MEDIUM.value
        else:
            return DifficultyLevel.HARD.value
    
    def get_estimated_time_minutes(self) -> int:
        """Estimate time needed to complete quiz"""
        if self.settings.time_limit_minutes:
            return self.settings.time_limit_minutes
        
        # Rough estimation: 1-2 minutes per question
        base_time = len(self.questions) * 1.5
        
        # Add time based on difficulty
        difficulty_multipliers = {
            DifficultyLevel.EASY: 0.8,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.5
        }
        
        adjusted_time = sum(
            1.5 * difficulty_multipliers[question.difficulty] 
            for question in self.questions
        )
        
        return max(int(adjusted_time), len(self.questions))  # At least 1 minute per question
    
    def calculate_score(self, answers: Dict[int, str]) -> Dict[str, Any]:
        """Calculate score based on answers"""
        total_points = 0
        earned_points = 0
        correct_count = 0
        
        for i, question in enumerate(self.questions):
            total_points += question.points
            user_answer = answers.get(i, "")
            
            if question.is_correct_answer(user_answer):
                earned_points += question.points
                correct_count += 1
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = percentage >= self.passing_score
        
        return {
            "total_points": total_points,
            "earned_points": earned_points,
            "percentage": percentage,
            "correct_count": correct_count,
            "total_questions": len(self.questions),
            "passed": passed,
            "passing_score": self.passing_score
        }
    
    def is_timed(self) -> bool:
        """Check if quiz has time limit"""
        return self.settings.time_limit_minutes is not None
    
    def allows_multiple_attempts(self) -> bool:
        """Check if quiz allows multiple attempts"""
        return self.settings.attempts_allowed > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "questions": [question.to_dict() for question in self.questions],
            "settings": self.settings.to_dict(),
            "passing_score": self.passing_score,
            "total_points": self.get_total_points(),
            "question_count": self.get_question_count(),
            "average_difficulty": self.get_average_difficulty(),
            "estimated_time_minutes": self.get_estimated_time_minutes(),
            "is_timed": self.is_timed(),
            "allows_multiple_attempts": self.allows_multiple_attempts()
        })
        return base_dict