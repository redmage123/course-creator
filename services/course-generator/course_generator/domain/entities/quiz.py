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
    """
    Quiz Question Type Enumeration

    BUSINESS REQUIREMENT:
    Different question types require different validation rules and scoring mechanisms.
    Instructors need flexibility to create diverse assessments.

    TECHNICAL IMPLEMENTATION:
    - MULTIPLE_CHOICE: Questions with 2+ options, single correct answer
    - TRUE_FALSE: Binary questions with exactly 2 options
    - SHORT_ANSWER: Open-ended text responses (manual grading)
    - ESSAY: Long-form text responses (manual grading)
    """
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

@dataclass
class QuizQuestion:
    """
    Quiz Question Domain Entity

    BUSINESS REQUIREMENT:
    Instructors create quiz questions to assess student learning. Each question
    has a type, difficulty level, point value, and optional explanation to help
    students understand mistakes after submission.

    TECHNICAL IMPLEMENTATION:
    - Immutable after creation (dataclass with validation)
    - Supports multiple question types with type-specific validation
    - Auto-generates UUID and timestamp on creation
    - Validates business rules in __post_init__

    WHY: Ensures data integrity for AI-generated and instructor-created questions
    """
    question: str  # Question text displayed to student
    options: List[str]  # Answer choices (multiple choice) or empty list (essay/short answer)
    correct_answer: int  # Index of correct option (multiple choice/true-false)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    id: Optional[str] = None  # Auto-generated UUID
    explanation: Optional[str] = None  # Shown after student submits answer
    points: int = 1  # Point value for correct answer
    difficulty: str = "medium"  # beginner, medium, advanced
    topic: Optional[str] = None  # Knowledge area being assessed
    created_at: Optional[datetime] = None  # Auto-generated timestamp
    
    def __post_init__(self):
        """
        Initialize question with generated ID and timestamp, then validate

        WHY: Ensures all questions have unique identifiers and creation timestamps
        before being persisted to database or used in quizzes
        """
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.validate()

    def validate(self) -> None:
        """
        Validate business rules for quiz questions

        BUSINESS REQUIREMENT:
        Questions must meet quality standards:
        - Non-empty question text
        - Correct number of options for question type
        - Valid correct answer index
        - Positive point value

        Raises:
            ValueError: If any business rule is violated

        WHY: Prevents invalid questions from being saved, ensuring assessment integrity
        """
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
        """
        Check if student's answer is correct

        Args:
            answer_index: The index of the option the student selected (0-based)

        Returns:
            True if answer is correct, False otherwise

        WHY: Core grading logic - determines if student earns points for this question
        """
        return answer_index == self.correct_answer

    def get_correct_option(self) -> str:
        """
        Get the text of the correct answer option

        Returns:
            The correct answer text, or empty string if invalid

        WHY: Used in explanations and feedback to show students the right answer
        """
        if self.options and 0 <= self.correct_answer < len(self.options):
            return self.options[self.correct_answer]
        return ""

    def add_option(self, option: str) -> None:
        """
        Add an answer option to the question

        Args:
            option: The option text to add

        Raises:
            ValueError: If option text is empty

        WHY: Allows dynamic question building by AI or instructors
        """
        if not option or len(option.strip()) == 0:
            raise ValueError("Option text cannot be empty")

        self.options.append(option.strip())

    def update_explanation(self, explanation: str) -> None:
        """
        Update the explanation shown to students after answering

        Args:
            explanation: The explanation text, or None to clear

        WHY: Helps students learn from mistakes by providing context for correct answers
        """
        self.explanation = explanation.strip() if explanation else None

@dataclass
class Quiz:
    """
    Quiz Domain Entity - Container for Assessment Questions

    BUSINESS REQUIREMENT:
    Instructors create quizzes to assess student knowledge. Quizzes can be
    AI-generated or manually created, with configurable time limits, attempt
    limits, randomization, and passing scores.

    TECHNICAL IMPLEMENTATION:
    - Aggregate root containing QuizQuestion entities
    - Supports various configuration options for academic integrity
    - Auto-generates scoring and analytics
    - Validates all questions before accepting them

    WHY: Centralizes quiz logic and ensures consistent assessment behavior
    across the platform
    """
    course_id: str  # Course this quiz belongs to
    title: str  # Quiz title shown to students
    topic: str  # Knowledge area being assessed
    difficulty: str  # beginner, intermediate, advanced
    questions: List[QuizQuestion]  # List of questions in this quiz
    id: Optional[str] = None  # Auto-generated UUID
    description: Optional[str] = None  # Instructions shown before quiz starts
    time_limit_minutes: Optional[int] = None  # Time limit, None = unlimited
    max_attempts: int = 1  # Maximum number of attempts per student
    shuffle_questions: bool = False  # Randomize question order per attempt
    shuffle_options: bool = False  # Randomize answer options per attempt
    show_results_immediately: bool = True  # Show score after submission
    passing_score: int = 70  # Minimum percentage to pass
    created_at: Optional[datetime] = None  # Auto-generated timestamp
    updated_at: Optional[datetime] = None  # Last modification timestamp
    
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
        """
        Add a question to the quiz

        Args:
            question: The QuizQuestion entity to add

        Raises:
            ValueError: If question validation fails

        WHY: Allows dynamic quiz building by AI content generator or instructors
        """
        question.validate()
        self.questions.append(question)
        self.updated_at = datetime.utcnow()

    def remove_question(self, question_id: str) -> bool:
        """
        Remove a question from the quiz by ID

        Args:
            question_id: UUID of the question to remove

        Returns:
            True if question was found and removed, False otherwise

        WHY: Allows instructors to edit AI-generated quizzes and remove poor questions
        """
        for i, question in enumerate(self.questions):
            if question.id == question_id:
                self.questions.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def get_question_by_id(self, question_id: str) -> Optional[QuizQuestion]:
        """
        Retrieve a specific question by its unique ID

        Args:
            question_id: UUID of the question to find

        Returns:
            QuizQuestion if found, None otherwise

        WHY: Enables question-level operations like editing or analytics
        """
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def get_total_points(self) -> int:
        """
        Calculate total points available in this quiz

        Returns:
            Sum of all question point values

        WHY: Used for percentage score calculation and grade normalization
        """
        return sum(question.points for question in self.questions)

    def get_question_count(self) -> int:
        """
        Get the number of questions in this quiz

        Returns:
            Total question count

        WHY: Used in UI display and attempt validation
        """
        return len(self.questions)
    
    def calculate_score(self, answers: List[int]) -> Dict[str, any]:
        """
        Calculate quiz score from student answers

        Args:
            answers: List of answer indices corresponding to questions

        Returns:
            Dictionary containing:
            - correct_answers: Number of correct responses
            - total_questions: Total number of questions
            - earned_points: Points earned
            - total_points: Total points available
            - percentage: Score as percentage (0-100)
            - passed: Boolean indicating if passing_score was met

        Raises:
            ValueError: If answer count doesn't match question count

        WHY: Core grading algorithm - determines student performance and course progression
        """
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
        """
        Check if quiz has a time constraint

        Returns:
            True if time_limit_minutes is set, False otherwise

        WHY: Determines if timer UI should be displayed and attempt monitoring needed
        """
        return self.time_limit_minutes is not None

@dataclass
class QuizAttempt:
    """
    Quiz Attempt Domain Entity - Tracks Student Quiz Submissions

    BUSINESS REQUIREMENT:
    Students can attempt quizzes multiple times (within max_attempts limit).
    Each attempt is tracked separately for analytics, grading, and progress monitoring.

    TECHNICAL IMPLEMENTATION:
    - Stores student answers and calculated scores
    - Tracks timing for time-limited quizzes
    - Immutable after completion (completed_at is set)
    - Integrates with Quiz entity for scoring

    WHY: Enables student progress tracking, gradebook integration, and learning analytics
    """
    student_id: str  # Student who took the quiz
    quiz_id: str  # Quiz that was attempted
    course_id: str  # Course context
    answers: List[int]  # Student's answer indices
    id: Optional[str] = None  # Auto-generated UUID
    score: Optional[float] = None  # Percentage score (0-100)
    total_questions: Optional[int] = None  # Number of questions
    earned_points: Optional[int] = None  # Points earned
    total_points: Optional[int] = None  # Total points available
    passed: Optional[bool] = None  # Whether passing_score was met
    started_at: Optional[datetime] = None  # Attempt start time
    completed_at: Optional[datetime] = None  # Attempt completion time
    time_taken_minutes: Optional[int] = None  # Duration in minutes
    
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
        """
        Complete the quiz attempt and calculate final score

        Args:
            quiz: The Quiz entity being attempted (for scoring logic)

        Raises:
            ValueError: If attempt is already completed

        WHY: Finalizes the attempt, calculates score, and stores results for gradebook
        """
        if self.completed_at:
            raise ValueError("Quiz attempt is already completed")

        # Calculate score using Quiz's scoring algorithm
        score_result = quiz.calculate_score(self.answers)

        self.score = score_result['percentage']
        self.total_questions = score_result['total_questions']
        self.earned_points = score_result['earned_points']
        self.total_points = score_result['total_points']
        self.passed = score_result['passed']
        self.completed_at = datetime.utcnow()

        # Calculate time taken for analytics
        if self.started_at:
            time_diff = self.completed_at - self.started_at
            self.time_taken_minutes = int(time_diff.total_seconds() / 60)

    def is_completed(self) -> bool:
        """
        Check if this attempt has been completed and scored

        Returns:
            True if completed_at is set, False otherwise

        WHY: Prevents students from modifying answers after submission
        """
        return self.completed_at is not None

    def get_duration_minutes(self) -> Optional[int]:
        """
        Calculate how long this attempt has taken or took

        Returns:
            Duration in minutes, or None if started_at not set

        WHY: Used for time limit enforcement and analytics on quiz difficulty
        """
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60)

    def is_within_time_limit(self, time_limit_minutes: int) -> bool:
        """
        Check if attempt is within allowed time limit

        Args:
            time_limit_minutes: Maximum allowed time for this quiz

        Returns:
            True if within limit or no duration, False if exceeded

        WHY: Enforces time limits for academic integrity in timed assessments
        """
        duration = self.get_duration_minutes()
        return duration is None or duration <= time_limit_minutes

@dataclass
class QuizGenerationRequest:
    """
    Quiz Generation Request Value Object

    BUSINESS REQUIREMENT:
    Instructors request AI-generated quizzes by providing topic, difficulty,
    and question count. The AI content generator uses instructor context and
    student tracking data to create personalized, relevant assessments.

    TECHNICAL IMPLEMENTATION:
    - Value object (no identity, only values matter)
    - Validates all parameters before AI generation begins
    - Limits question count to 50 for performance
    - Includes context for RAG-enhanced question generation

    WHY: Ensures AI receives valid, complete parameters for quality quiz generation
    """
    course_id: str  # Course context for AI generation
    topic: str  # Subject matter for questions
    difficulty: str  # Difficulty level: beginner, intermediate, advanced
    question_count: int  # Number of questions to generate (1-50)
    difficulty_level: str  # Same as difficulty (deprecated, kept for compatibility)
    instructor_context: Dict  # Teaching style, focus areas, preferences
    student_tracking: Dict  # Class performance data for adaptive difficulty

    def validate(self) -> None:
        """
        Validate all quiz generation parameters

        BUSINESS REQUIREMENT:
        Invalid requests waste AI tokens and instructor time. All parameters
        must be validated before expensive AI generation begins.

        Raises:
            ValueError: If any parameter fails validation

        WHY: Prevents invalid AI requests and ensures quality quiz generation
        """
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