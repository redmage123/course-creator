/**
 * Quiz Results Component - Display quiz results and performance
 * @module features/quizzes/components/QuizResults
 */

import React from 'react';
import { Button } from '@/components/atoms/Button';
import type { Quiz, QuizAttempt } from '../QuizTaking';
import styles from './QuizResults.module.css';

export interface QuizResultsProps {
  quiz: Quiz;
  attempt: QuizAttempt;
  onRetake?: () => void;
  onClose: () => void;
}

export const QuizResults: React.FC<QuizResultsProps> = ({
  quiz,
  attempt,
  onRetake,
  onClose
}) => {
  if (!attempt.score) return null;

  const { score } = attempt;
  const isPassed = score.passed;
  const percentage = Math.round(score.percentage);

  const getPerformanceMessage = (): string => {
    if (percentage >= 90) return 'Excellent work!';
    if (percentage >= 80) return 'Great job!';
    if (percentage >= 70) return 'Good effort!';
    if (percentage >= 60) return 'Keep practicing!';
    return 'Review the material and try again.';
  };

  return (
    <div className={styles.resultsContainer}>
      <div className={styles.resultsCard}>
        <div className={`${styles.resultBanner} ${isPassed ? styles.passed : styles.failed}`}>
          <span className={styles.resultIcon}>{isPassed ? '🎉' : '📚'}</span>
          <h1>{isPassed ? 'Congratulations!' : 'Not Quite There'}</h1>
          <p className={styles.performanceMessage}>{getPerformanceMessage()}</p>
        </div>

        <div className={styles.scoreSection}>
          <div className={styles.mainScore}>
            <div className={styles.scoreCircle}>
              <span className={styles.scorePercentage}>{percentage}%</span>
            </div>
            <div className={styles.scoreDetails}>
              <p><strong>{score.earned_points}</strong> / {score.total_points} points</p>
              <p><strong>{score.correct_count}</strong> / {score.total_questions} correct</p>
              <p className={isPassed ? styles.passedText : styles.failedText}>
                {isPassed ? '✓ Passed' : '✗ Did not pass'} (Passing: {score.passing_score}%)
              </p>
            </div>
          </div>
        </div>

        <div className={styles.statsSection}>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Time Spent</span>
            <span className={styles.statValue}>
              {Math.floor(attempt.time_spent_seconds / 60)}min {attempt.time_spent_seconds % 60}s
            </span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Accuracy</span>
            <span className={styles.statValue}>{percentage}%</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Questions</span>
            <span className={styles.statValue}>{score.total_questions}</span>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          {onRetake && !isPassed && (
            <Button variant="primary" onClick={onRetake}>
              Retake Quiz
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizResults;
