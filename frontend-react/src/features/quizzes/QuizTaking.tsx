/**
 * Quiz Taking Component
 *
 * Main quiz interface for students to take assessments
 * Features:
 * - Question navigation
 * - Answer selection and submission
 * - Timer countdown (if timed quiz)
 * - Progress tracking
 * - Auto-save draft answers
 * - Final submission with confirmation
 *
 * @module features/quizzes/QuizTaking
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/atoms/Button';
import { QuizQuestion } from './components/QuizQuestion';
import { QuizTimer } from './components/QuizTimer';
import { QuizResults } from './components/QuizResults';
import { useQuizSession } from './hooks/useQuizSession';
import styles from './QuizTaking.module.css';

export interface Quiz {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  settings: QuizSettings;
  passing_score: number;
  total_points: number;
  question_count: number;
  estimated_time_minutes: number;
  is_timed: boolean;
  allows_multiple_attempts: boolean;
}

export interface Question {
  question_text: string;
  question_type: QuestionType;
  points: number;
  options: string[];
  explanation?: string;
  difficulty: DifficultyLevel;
  tags: string[];
}

export type QuestionType =
  | 'multiple_choice'
  | 'true_false'
  | 'short_answer'
  | 'essay'
  | 'matching'
  | 'fill_in_blank';

export type DifficultyLevel = 'easy' | 'medium' | 'hard';

export interface QuizSettings {
  time_limit_minutes: number | null;
  attempts_allowed: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  show_correct_answers: boolean;
  show_results_immediately: boolean;
  require_password: boolean;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  student_id: string;
  answers: Record<number, string>;
  score: QuizScore | null;
  started_at: Date;
  submitted_at: Date | null;
  time_spent_seconds: number;
}

export interface QuizScore {
  total_points: number;
  earned_points: number;
  percentage: number;
  correct_count: number;
  total_questions: number;
  passed: boolean;
  passing_score: number;
}

export const QuizTaking: React.FC = () => {
  const { quizId, courseId } = useParams<{ quizId: string; courseId: string }>();
  const navigate = useNavigate();

  // Quiz session management
  const {
    quiz,
    attempt,
    answers,
    currentQuestionIndex,
    isLoading,
    isSubmitting,
    error,
    startQuiz,
    saveAnswer,
    submitQuiz,
    setCurrentQuestionIndex
  } = useQuizSession(quizId, courseId);

  // Local state
  const [showResults, setShowResults] = useState(false);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  // Initialize time remaining
  useEffect(() => {
    if (quiz?.is_timed && quiz.settings.time_limit_minutes && attempt) {
      const startTime = new Date(attempt.started_at).getTime();
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000);
      const totalSeconds = quiz.settings.time_limit_minutes * 60;
      const remaining = Math.max(0, totalSeconds - elapsed);
      setTimeRemaining(remaining);
    }
  }, [quiz, attempt]);

  // Handle time expiration
  const handleTimeExpired = useCallback(async () => {
    if (!isSubmitting) {
      await submitQuiz();
      setShowResults(true);
    }
  }, [isSubmitting, submitQuiz]);

  // Handle answer change
  const handleAnswerChange = useCallback(async (questionIndex: number, answer: string) => {
    await saveAnswer(questionIndex, answer);
  }, [saveAnswer]);

  // Handle navigation
  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleNext = () => {
    if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  // Handle submission
  const handleSubmit = async () => {
    setShowSubmitConfirm(false);
    const result = await submitQuiz();
    if (result) {
      setShowResults(true);
    }
  };

  // Calculate progress
  const getProgress = (): number => {
    if (!quiz) return 0;
    const answered = Object.keys(answers).length;
    return (answered / quiz.questions.length) * 100;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <p>Loading quiz...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error Loading Quiz</h2>
        <p>{error}</p>
        <Button onClick={() => navigate(-1)}>Go Back</Button>
      </div>
    );
  }

  // Quiz not found
  if (!quiz || !attempt) {
    return (
      <div className={styles.errorContainer}>
        <h2>Quiz Not Found</h2>
        <Button onClick={() => navigate(-1)}>Go Back</Button>
      </div>
    );
  }

  // Show results if quiz is submitted
  if (showResults && attempt.score) {
    return (
      <QuizResults
        quiz={quiz}
        attempt={attempt}
        onRetake={quiz.allows_multiple_attempts ? () => startQuiz() : undefined}
        onClose={() => navigate(`/courses/${courseId}`)}
      />
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === quiz.questions.length - 1;

  return (
    <div className={styles.quizContainer}>
      {/* Quiz Header */}
      <div className={styles.quizHeader}>
        <div className={styles.quizInfo}>
          <h1>{quiz.title}</h1>
          {quiz.description && (
            <p className={styles.quizDescription}>{quiz.description}</p>
          )}
        </div>

        {quiz.is_timed && timeRemaining !== null && (
          <QuizTimer
            timeRemaining={timeRemaining}
            onTimeExpired={handleTimeExpired}
          />
        )}
      </div>

      {/* Progress Bar */}
      <div className={styles.progressSection}>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${getProgress()}%` }}
          />
        </div>
        <div className={styles.progressText}>
          <span>{Object.keys(answers).length} of {quiz.questions.length} answered</span>
          <span>Question {currentQuestionIndex + 1} of {quiz.questions.length}</span>
        </div>
      </div>

      {/* Question */}
      <div className={styles.questionSection}>
        <QuizQuestion
          question={currentQuestion}
          questionIndex={currentQuestionIndex}
          answer={answers[currentQuestionIndex] || ''}
          onAnswerChange={handleAnswerChange}
        />
      </div>

      {/* Navigation */}
      <div className={styles.navigationSection}>
        <Button
          variant="secondary"
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
        >
          ← Previous
        </Button>

        <div className={styles.navigationCenter}>
          <span className={styles.questionIndicator}>
            {currentQuestionIndex + 1} / {quiz.questions.length}
          </span>
        </div>

        {!isLastQuestion ? (
          <Button
            variant="primary"
            onClick={handleNext}
          >
            Next →
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={() => setShowSubmitConfirm(true)}
            disabled={isSubmitting}
          >
            Submit Quiz
          </Button>
        )}
      </div>

      {/* Question Grid Navigation */}
      <div className={styles.questionGrid}>
        <h3>Questions</h3>
        <div className={styles.questionButtons}>
          {quiz.questions.map((_, index) => (
            <button
              key={index}
              className={`${styles.questionButton} ${
                index === currentQuestionIndex ? styles.active : ''
              } ${
                answers[index] ? styles.answered : ''
              }`}
              onClick={() => setCurrentQuestionIndex(index)}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>Submit Quiz?</h2>
            <p>
              You have answered {Object.keys(answers).length} out of {quiz.questions.length} questions.
            </p>
            {Object.keys(answers).length < quiz.questions.length && (
              <p className={styles.warningText}>
                ⚠️ Some questions are unanswered. Are you sure you want to submit?
              </p>
            )}
            <div className={styles.modalActions}>
              <Button
                variant="secondary"
                onClick={() => setShowSubmitConfirm(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Yes, Submit'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizTaking;
