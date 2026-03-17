/**
 * Quiz Timer Component - Countdown timer for timed quizzes
 * @module features/quizzes/components/QuizTimer
 */

import React, { useEffect, useState } from 'react';
import styles from './QuizTimer.module.css';

export interface QuizTimerProps {
  timeRemaining: number; // seconds
  onTimeExpired: () => void;
}

export const QuizTimer: React.FC<QuizTimerProps> = ({
  timeRemaining: initialTime,
  onTimeExpired
}) => {
  const [timeLeft, setTimeLeft] = useState(initialTime);

  useEffect(() => {
    if (timeLeft <= 0) {
      onTimeExpired();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, onTimeExpired]);

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getWarningLevel = (): string => {
    if (timeLeft <= 60) return styles.critical;
    if (timeLeft <= 300) return styles.warning;
    return styles.normal;
  };

  return (
    <div className={`${styles.timer} ${getWarningLevel()}`}>
      <span className={styles.timerIcon}>⏱️</span>
      <span className={styles.timerText}>{formatTime(timeLeft)}</span>
      {timeLeft <= 60 && <span className={styles.urgentBadge}>Hurry!</span>}
    </div>
  );
};

export default QuizTimer;
