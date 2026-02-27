/**
 * ProgramWizard Page
 *
 * BUSINESS CONTEXT:
 * Full setup wizard for training programs. Replaces the static detail page
 * for instructors/admins. Students see a read-only program overview.
 *
 * WIZARD FLOW:
 * 1. Program Overview - Edit program metadata
 * 2. Tracks - Add/edit learning tracks
 * 3. Courses - Add courses to each track
 * 4. Syllabi - Generate per-course syllabi with AI
 * 5. Enrollment - Bulk enroll students per track
 * 6. Review & Publish - Summary, validation checklist, publish
 *
 * TECHNICAL IMPLEMENTATION:
 * - URL-synced step state via useWizard hook (?step=N)
 * - Stepper component for visual progress
 * - Role-based: students see read-only overview, instructors/admins get wizard
 * - After create form, redirects to ?step=2 for immediate track setup
 * - React Query for all data fetching
 */

import React, { useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { Stepper } from '../../../components/atoms/Stepper';
import type { StepConfig } from '../../../components/atoms/Stepper';
import { useWizard } from '../../../hooks/useWizard';
import { useAuth } from '../../../hooks/useAuth';
import { trainingProgramService } from '../../../services';
import type { UpdateTrainingProgramRequest } from '../../../services';
import { ProgramOverviewStep } from '../components/wizard/ProgramOverviewStep';
import { TracksStep } from '../components/wizard/TracksStep';
import { CoursesStep } from '../components/wizard/CoursesStep';
import { SyllabiStep } from '../components/wizard/SyllabiStep';
import { EnrollmentStep } from '../components/wizard/EnrollmentStep';
import { ReviewPublishStep } from '../components/wizard/ReviewPublishStep';
import styles from './ProgramWizard.module.css';

const STEP_LABELS = [
  'Overview',
  'Tracks',
  'Courses',
  'Syllabi',
  'Enrollment',
  'Review',
];

export const ProgramWizard: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isStudent, isInstructor, isOrgAdmin, isSiteAdmin } = useAuth();

  const canEdit = isInstructor || isOrgAdmin || isSiteAdmin;
  const readOnly = !canEdit;

  const { data: program, isLoading, isError, error } = useQuery({
    queryKey: ['trainingProgram', courseId],
    queryFn: () => trainingProgramService.getTrainingProgramById(courseId!),
    enabled: !!courseId,
  });

  const updateMutation = useMutation({
    mutationFn: (data: UpdateTrainingProgramRequest) =>
      trainingProgramService.updateTrainingProgram(courseId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingProgram', courseId] });
    },
  });

  const {
    currentStep,
    goToStep,
    goNext,
    goPrevious,
    isFirstStep,
    isLastStep,
    completedSteps,
    stepStatuses,
    markStepCompleted,
  } = useWizard({
    totalSteps: 6,
    initialStep: 1,
  });

  const handleOverviewSave = useCallback(
    async (data: UpdateTrainingProgramRequest) => {
      try {
        await updateMutation.mutateAsync(data);
        markStepCompleted(1);
      } catch (err) {
        // Re-throw so ProgramOverviewStep's catch block can display the error
        throw err;
      }
    },
    [updateMutation, markStepCompleted]
  );

  const stepConfigs: StepConfig[] = useMemo(
    () =>
      STEP_LABELS.map((label, i) => ({
        id: i + 1,
        label,
        status: stepStatuses[i],
      })),
    [stepStatuses]
  );

  const getBackPath = () => {
    const path = window.location.pathname;
    if (path.includes('/organization/')) return '/organization/programs';
    return '/instructor/programs';
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className={styles.loadingContainer}>
          <Spinner size="large" />
        </div>
      </DashboardLayout>
    );
  }

  if (isError || !program) {
    return (
      <DashboardLayout>
        <div className={styles.wizardPage}>
          <div className={styles.errorContainer}>
            <h2 className={styles.errorTitle}>Program Not Found</h2>
            <p className={styles.errorMessage}>
              {(error as Error)?.message || 'Unable to load this training program.'}
            </p>
            <Button variant="primary" onClick={() => navigate(getBackPath())}>
              Back to Programs
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Students see read-only overview (no stepper, no wizard steps)
   */
  if (readOnly) {
    return (
      <DashboardLayout>
        <div className={styles.wizardPage}>
          <Link to="/courses/my-courses" className={styles.backLink}>
            &larr; Back to My Courses
          </Link>

          <div className={styles.pageHeader}>
            <div>
              <Heading level="h1" gutterBottom>
                {program.title}
              </Heading>
              <p className={styles.headerDescription}>{program.description}</p>
            </div>
          </div>

          <div className={styles.readOnlyBanner}>
            You are viewing this program as a student. Contact your instructor for changes.
          </div>

          <Card variant="outlined" padding="large">
            <ProgramOverviewStep program={program} readOnly />
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Instructor/Admin wizard view
   */
  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <ProgramOverviewStep
            program={program}
            onSave={handleOverviewSave}
          />
        );
      case 2:
        return (
          <TracksStep
            programId={courseId!}
            projectId={program.project_id}
          />
        );
      case 3:
        return (
          <CoursesStep
            programId={courseId!}
            projectId={program.project_id}
            organizationId={program.organization_id}
          />
        );
      case 4:
        return (
          <SyllabiStep
            programId={courseId!}
            projectId={program.project_id}
          />
        );
      case 5:
        return (
          <EnrollmentStep
            programId={courseId!}
            projectId={program.project_id}
          />
        );
      case 6:
        return (
          <ReviewPublishStep
            programId={courseId!}
            projectId={program.project_id}
          />
        );
      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <div className={styles.wizardPage}>
        <Link to={getBackPath()} className={styles.backLink}>
          &larr; Back to Programs
        </Link>

        <div className={styles.pageHeader}>
          <div>
            <Heading level="h1" gutterBottom>
              {program.title}
            </Heading>
            <p className={styles.headerDescription}>
              Program Setup Wizard — Step {currentStep} of 6
            </p>
          </div>
        </div>

        <Stepper
          steps={stepConfigs}
          currentStep={currentStep}
          onStepClick={(stepId) => goToStep(stepId)}
          allowJumping
        />

        <Card variant="outlined" padding="large">
          <div className={styles.stepContent}>
            {renderCurrentStep()}
          </div>

          <div className={styles.wizardFooter}>
            <div className={styles.footerLeft}>
              {!isFirstStep && (
                <Button variant="secondary" onClick={goPrevious}>
                  Previous
                </Button>
              )}
            </div>
            <div className={styles.footerRight}>
              {!isLastStep && (
                <Button variant="primary" onClick={goNext}>
                  Next
                </Button>
              )}
              {isLastStep && (
                <Button variant="primary" onClick={() => navigate(getBackPath())}>
                  Done
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

ProgramWizard.displayName = 'ProgramWizard';
