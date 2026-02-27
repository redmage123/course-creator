/**
 * Stepper Component
 *
 * BUSINESS CONTEXT:
 * Horizontal progress indicator for multi-step wizards.
 * Used in program setup, course creation, and organization onboarding flows.
 * Provides visual feedback on completion progress and allows navigation
 * between completed steps.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Numbered circles with connecting lines
 * - Step states: completed, active, upcoming, error
 * - Click navigation for completed steps (configurable)
 * - ARIA attributes for screen reader support
 * - Responsive: horizontal on desktop, vertical on mobile
 */

import React from 'react';
import styles from './Stepper.module.css';

export type StepStatus = 'completed' | 'active' | 'upcoming' | 'error';

export interface StepConfig {
  id: number;
  label: string;
  status: StepStatus;
}

export interface StepperProps {
  steps: StepConfig[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
  allowJumping?: boolean;
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepClick,
  allowJumping = false,
}) => {
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const progressPercent = steps.length > 1
    ? (completedCount / (steps.length - 1)) * 100
    : 0;

  const handleStepClick = (step: StepConfig) => {
    if (!onStepClick) return;
    if (allowJumping && step.status === 'completed') {
      onStepClick(step.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, step: StepConfig) => {
    if ((e.key === 'Enter' || e.key === ' ') && allowJumping && step.status === 'completed') {
      e.preventDefault();
      onStepClick?.(step.id);
    }
  };

  return (
    <nav className={styles.stepper} aria-label="Progress">
      <div className={styles.line}>
        <div
          className={styles.lineFill}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <ol className={styles.stepList}>
        {steps.map((step) => {
          const isClickable = allowJumping && step.status === 'completed' && !!onStepClick;

          return (
            <li
              key={step.id}
              className={[
                styles.step,
                styles[`step--${step.status}`],
                isClickable ? styles['step--clickable'] : '',
              ].filter(Boolean).join(' ')}
              onClick={() => handleStepClick(step)}
              onKeyDown={(e) => handleKeyDown(e, step)}
              tabIndex={isClickable ? 0 : undefined}
              role={isClickable ? 'button' : undefined}
              aria-current={step.status === 'active' ? 'step' : undefined}
              aria-label={`Step ${step.id}: ${step.label} - ${step.status}`}
            >
              <div className={styles.circle}>
                {step.status === 'completed' ? (
                  <svg
                    className={styles.checkIcon}
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M3.5 8.5L6.5 11.5L12.5 4.5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : step.status === 'error' ? (
                  <span className={styles.errorIcon} aria-hidden="true">!</span>
                ) : (
                  <span className={styles.number}>{step.id}</span>
                )}
              </div>
              <span className={styles.label}>{step.label}</span>
            </li>
          );
        })}
      </ol>

      <div className={styles.srOnly}>
        Step {currentStep} of {steps.length}
      </div>
    </nav>
  );
};

Stepper.displayName = 'Stepper';
