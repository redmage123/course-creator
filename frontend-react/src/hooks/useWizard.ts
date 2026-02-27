/**
 * useWizard Hook
 *
 * BUSINESS CONTEXT:
 * Manages multi-step wizard state with URL synchronization.
 * Enables deep-linking to specific steps via ?step=N query parameter,
 * browser back/forward navigation, and step completion tracking.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads/writes step to URL search params via useSearchParams
 * - Tracks completed steps for stepper status rendering
 * - Supports onStepChange callback for validation/save before navigation
 * - Clamps step values to valid range [1, totalSteps]
 */

import { useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { StepStatus } from '../components/atoms/Stepper';

interface UseWizardOptions {
  totalSteps: number;
  initialStep?: number;
  onStepChange?: (fromStep: number, toStep: number) => boolean | Promise<boolean>;
}

interface UseWizardReturn {
  currentStep: number;
  totalSteps: number;
  goToStep: (step: number) => Promise<void>;
  goNext: () => Promise<void>;
  goPrevious: () => Promise<void>;
  isFirstStep: boolean;
  isLastStep: boolean;
  completedSteps: Set<number>;
  markStepCompleted: (step: number) => void;
  markStepIncomplete: (step: number) => void;
  stepStatuses: StepStatus[];
}

export function useWizard({
  totalSteps,
  initialStep = 1,
  onStepChange,
}: UseWizardOptions): UseWizardReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const clamp = (n: number) => Math.max(1, Math.min(totalSteps, n));

  const currentStep = useMemo(() => {
    const urlStep = searchParams.get('step');
    if (urlStep) {
      const parsed = parseInt(urlStep, 10);
      if (!isNaN(parsed)) return clamp(parsed);
    }
    return clamp(initialStep);
  }, [searchParams, initialStep, totalSteps]);

  const setStep = useCallback(
    (step: number) => {
      const clamped = clamp(step);
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('step', String(clamped));
          return next;
        },
        { replace: false }
      );
    },
    [setSearchParams, totalSteps]
  );

  const goToStep = useCallback(
    async (step: number) => {
      if (onStepChange) {
        const allowed = await onStepChange(currentStep, step);
        if (!allowed) return;
      }
      setStep(step);
    },
    [currentStep, onStepChange, setStep]
  );

  const goNext = useCallback(async () => {
    if (currentStep >= totalSteps) return;
    if (onStepChange) {
      const allowed = await onStepChange(currentStep, currentStep + 1);
      if (!allowed) return;
    }
    setCompletedSteps((prev) => new Set(prev).add(currentStep));
    setStep(currentStep + 1);
  }, [currentStep, totalSteps, onStepChange, setStep]);

  const goPrevious = useCallback(async () => {
    if (currentStep <= 1) return;
    if (onStepChange) {
      const allowed = await onStepChange(currentStep, currentStep - 1);
      if (!allowed) return;
    }
    setStep(currentStep - 1);
  }, [currentStep, onStepChange, setStep]);

  const markStepCompleted = useCallback((step: number) => {
    setCompletedSteps((prev) => new Set(prev).add(step));
  }, []);

  const markStepIncomplete = useCallback((step: number) => {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      next.delete(step);
      return next;
    });
  }, []);

  const stepStatuses: StepStatus[] = useMemo(() => {
    return Array.from({ length: totalSteps }, (_, i) => {
      const stepNum = i + 1;
      if (stepNum === currentStep) return 'active';
      if (completedSteps.has(stepNum)) return 'completed';
      return 'upcoming';
    });
  }, [totalSteps, currentStep, completedSteps]);

  return {
    currentStep,
    totalSteps,
    goToStep,
    goNext,
    goPrevious,
    isFirstStep: currentStep === 1,
    isLastStep: currentStep === totalSteps,
    completedSteps,
    markStepCompleted,
    markStepIncomplete,
    stepStatuses,
  };
}
