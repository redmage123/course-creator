/**
 * useQuizSession Hook - Manages quiz session state and operations
 * @module features/quizzes/hooks/useQuizSession
 */

import { useState, useEffect, useCallback } from 'react';
import type { Quiz, QuizAttempt } from '../QuizTaking';
import { quizService } from '../services/quizService';

interface UseQuizSessionResult {
  quiz: Quiz | null;
  attempt: QuizAttempt | null;
  answers: Record<number, string>;
  currentQuestionIndex: number;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  startQuiz: () => Promise<void>;
  saveAnswer: (questionIndex: number, answer: string) => Promise<void>;
  submitQuiz: () => Promise<QuizAttempt | null>;
  setCurrentQuestionIndex: (index: number) => void;
}

export const useQuizSession = (
  quizId: string | undefined,
  courseId: string | undefined
): UseQuizSessionResult => {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load quiz and check for existing attempt
  useEffect(() => {
    if (!quizId || !courseId) return;

    const loadQuiz = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load quiz
        const quizData = await quizService.getQuiz(quizId);
        setQuiz(quizData);

        // Check for existing attempt
        const existingAttempt = await quizService.getActiveAttempt(quizId);
        if (existingAttempt) {
          setAttempt(existingAttempt);
          setAnswers(existingAttempt.answers || {});
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load quiz');
      } finally {
        setIsLoading(false);
      }
    };

    loadQuiz();
  }, [quizId, courseId]);

  // Start quiz
  const startQuiz = useCallback(async () => {
    if (!quizId) return;

    try {
      setIsLoading(true);
      setError(null);

      const newAttempt = await quizService.startQuiz(quizId);
      setAttempt(newAttempt);
      setAnswers({});
      setCurrentQuestionIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start quiz');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [quizId]);

  // Save answer
  const saveAnswer = useCallback(async (questionIndex: number, answer: string) => {
    if (!attempt) return;

    try {
      const updatedAnswers = { ...answers, [questionIndex]: answer };
      setAnswers(updatedAnswers);

      // Auto-save to backend
      await quizService.saveAnswer(attempt.id, questionIndex, answer);
    } catch (err) {
      console.error('Failed to save answer:', err);
      // Don't throw - allow local save to persist
    }
  }, [attempt, answers]);

  // Submit quiz
  const submitQuiz = useCallback(async (): Promise<QuizAttempt | null> => {
    if (!attempt) return null;

    try {
      setIsSubmitting(true);
      setError(null);

      const submittedAttempt = await quizService.submitQuiz(attempt.id, answers);
      setAttempt(submittedAttempt);
      return submittedAttempt;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit quiz');
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, [attempt, answers]);

  return {
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
  };
};

export default useQuizSession;
