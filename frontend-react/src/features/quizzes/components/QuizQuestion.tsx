/**
 * Quiz Question Component
 *
 * Renders individual quiz questions with appropriate input based on question type
 * Supports:
 * - Multiple choice (single/multiple selection)
 * - True/False
 * - Short answer
 * - Essay
 * - Fill in the blank
 *
 * @module features/quizzes/components/QuizQuestion
 */

import React from 'react';
import type { Question, QuestionType } from '../QuizTaking';
import styles from './QuizQuestion.module.css';

export interface QuizQuestionProps {
  question: Question;
  questionIndex: number;
  answer: string;
  onAnswerChange: (questionIndex: number, answer: string) => void;
  showCorrectAnswer?: boolean;
  correctAnswer?: string;
  isReview?: boolean;
}

export const QuizQuestion: React.FC<QuizQuestionProps> = ({
  question,
  questionIndex,
  answer,
  onAnswerChange,
  showCorrectAnswer = false,
  correctAnswer,
  isReview = false
}) => {
  const handleChange = (value: string) => {
    if (!isReview) {
      onAnswerChange(questionIndex, value);
    }
  };

  const getDifficultyColor = (difficulty: string): string => {
    switch (difficulty) {
      case 'easy': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'hard': return '#f44336';
      default: return '#666666';
    }
  };

  const renderQuestionInput = () => {
    switch (question.question_type) {
      case 'multiple_choice':
        return (
          <div className={styles.optionsContainer}>
            {question.options.map((option, index) => {
              const isSelected = answer === option;
              const isCorrect = showCorrectAnswer && option === correctAnswer;
              const isWrong = showCorrectAnswer && isSelected && option !== correctAnswer;

              return (
                <label
                  key={index}
                  className={`${styles.option} ${
                    isSelected ? styles.selected : ''
                  } ${
                    isCorrect ? styles.correct : ''
                  } ${
                    isWrong ? styles.wrong : ''
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${questionIndex}`}
                    value={option}
                    checked={isSelected}
                    onChange={(e) => handleChange(e.target.value)}
                    disabled={isReview}
                    className={styles.radioInput}
                  />
                  <span className={styles.optionText}>{option}</span>
                  {isCorrect && <span className={styles.correctBadge}>✓ Correct</span>}
                  {isWrong && <span className={styles.wrongBadge}>✗ Incorrect</span>}
                </label>
              );
            })}
          </div>
        );

      case 'true_false':
        return (
          <div className={styles.optionsContainer}>
            {['True', 'False'].map((option) => {
              const isSelected = answer === option;
              const isCorrect = showCorrectAnswer && option === correctAnswer;
              const isWrong = showCorrectAnswer && isSelected && option !== correctAnswer;

              return (
                <label
                  key={option}
                  className={`${styles.option} ${
                    isSelected ? styles.selected : ''
                  } ${
                    isCorrect ? styles.correct : ''
                  } ${
                    isWrong ? styles.wrong : ''
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${questionIndex}`}
                    value={option}
                    checked={isSelected}
                    onChange={(e) => handleChange(e.target.value)}
                    disabled={isReview}
                    className={styles.radioInput}
                  />
                  <span className={styles.optionText}>{option}</span>
                  {isCorrect && <span className={styles.correctBadge}>✓ Correct</span>}
                  {isWrong && <span className={styles.wrongBadge}>✗ Incorrect</span>}
                </label>
              );
            })}
          </div>
        );

      case 'short_answer':
        return (
          <div className={styles.textInputContainer}>
            <input
              type="text"
              value={answer}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Enter your answer..."
              className={styles.textInput}
              disabled={isReview}
            />
            {showCorrectAnswer && correctAnswer && (
              <div className={styles.correctAnswerDisplay}>
                <strong>Correct Answer:</strong> {correctAnswer}
              </div>
            )}
          </div>
        );

      case 'essay':
        return (
          <div className={styles.textInputContainer}>
            <textarea
              value={answer}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Enter your answer... (Be thorough and specific)"
              className={styles.textArea}
              rows={10}
              disabled={isReview}
            />
            {showCorrectAnswer && question.explanation && (
              <div className={styles.correctAnswerDisplay}>
                <strong>Sample Answer/Key Points:</strong>
                <p>{question.explanation}</p>
              </div>
            )}
          </div>
        );

      case 'fill_in_blank':
        return (
          <div className={styles.textInputContainer}>
            <input
              type="text"
              value={answer}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Fill in the blank..."
              className={styles.textInput}
              disabled={isReview}
            />
            {showCorrectAnswer && correctAnswer && (
              <div className={styles.correctAnswerDisplay}>
                <strong>Correct Answer:</strong> {correctAnswer}
              </div>
            )}
          </div>
        );

      default:
        return <div>Unsupported question type</div>;
    }
  };

  return (
    <div className={styles.questionContainer}>
      {/* Question Header */}
      <div className={styles.questionHeader}>
        <div className={styles.questionMeta}>
          <span className={styles.questionNumber}>Question {questionIndex + 1}</span>
          <span
            className={styles.difficulty}
            style={{ color: getDifficultyColor(question.difficulty) }}
          >
            {question.difficulty.toUpperCase()}
          </span>
          <span className={styles.points}>{question.points} {question.points === 1 ? 'point' : 'points'}</span>
        </div>
      </div>

      {/* Question Text */}
      <div className={styles.questionText}>
        {question.question_text}
      </div>

      {/* Question Input */}
      {renderQuestionInput()}

      {/* Explanation (shown after submission) */}
      {showCorrectAnswer && question.explanation && question.question_type !== 'essay' && (
        <div className={styles.explanation}>
          <strong>Explanation:</strong>
          <p>{question.explanation}</p>
        </div>
      )}

      {/* Tags */}
      {question.tags && question.tags.length > 0 && (
        <div className={styles.tags}>
          {question.tags.map((tag, index) => (
            <span key={index} className={styles.tag}>{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
};

export default QuizQuestion;
