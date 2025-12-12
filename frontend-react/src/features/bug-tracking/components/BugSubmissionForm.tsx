/**
 * Bug Submission Form Component
 *
 * BUSINESS CONTEXT:
 * Allows users to submit bug reports to the automated bug tracking system.
 * Bugs are analyzed by Claude AI, which generates fixes and opens PRs.
 *
 * TECHNICAL IMPLEMENTATION:
 * React form with validation using controlled components.
 * Submits to bug-tracking microservice via bugService.
 *
 * ACCESSIBILITY:
 * - All inputs have proper labels and aria attributes
 * - Form validation errors are announced to screen readers
 * - Keyboard navigation support
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { bugService, BugSubmissionRequest, BugSeverity } from '../../../services/bugService';
import { Input } from '../../../components/atoms/Input';
import { Button } from '../../../components/atoms/Button';
import { Textarea } from '../../../components/atoms/Textarea';
import { Select } from '../../../components/atoms/Select';
import styles from './BugSubmissionForm.module.css';

// ============================================================
// Type Definitions
// ============================================================

interface FormData {
  title: string;
  description: string;
  steps_to_reproduce: string;
  expected_behavior: string;
  actual_behavior: string;
  severity: BugSeverity;
  affected_component: string;
  submitter_email: string;
}

interface FormErrors {
  title?: string;
  description?: string;
  submitter_email?: string;
  general?: string;
}

// ============================================================
// Component Implementation
// ============================================================

/**
 * Bug Submission Form
 *
 * Features:
 * - Title and description (required)
 * - Steps to reproduce (optional)
 * - Expected vs actual behavior (optional)
 * - Severity selection
 * - Affected component selection
 * - Auto-populates email if logged in
 */
export const BugSubmissionForm: React.FC = () => {
  const navigate = useNavigate();

  // Form state
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    steps_to_reproduce: '',
    expected_behavior: '',
    actual_behavior: '',
    severity: 'medium',
    affected_component: '',
    submitter_email: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submittedBugId, setSubmittedBugId] = useState<string | null>(null);

  // Severity options
  const severityOptions = [
    { value: 'low', label: 'Low - Minor issue, workaround exists' },
    { value: 'medium', label: 'Medium - Moderate impact on functionality' },
    { value: 'high', label: 'High - Significant impact, no workaround' },
    { value: 'critical', label: 'Critical - System unusable, data loss risk' },
  ];

  // Component options (based on platform services)
  const componentOptions = [
    { value: '', label: 'Select affected component...' },
    { value: 'authentication', label: 'Authentication / Login' },
    { value: 'dashboard', label: 'Dashboard' },
    { value: 'courses', label: 'Courses / Training Programs' },
    { value: 'labs', label: 'Lab Environment' },
    { value: 'quizzes', label: 'Quizzes / Assessments' },
    { value: 'analytics', label: 'Analytics / Reports' },
    { value: 'content-generation', label: 'AI Content Generation' },
    { value: 'ai-assistant', label: 'AI Assistant' },
    { value: 'organization', label: 'Organization Management' },
    { value: 'user-management', label: 'User Management' },
    { value: 'notifications', label: 'Notifications / Email' },
    { value: 'api', label: 'API / Backend' },
    { value: 'frontend', label: 'Frontend / UI' },
    { value: 'other', label: 'Other' },
  ];

  /**
   * Handle input change
   */
  const handleChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  }, [errors]);

  /**
   * Validate form data
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    // Title validation
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.length < 10) {
      newErrors.title = 'Title must be at least 10 characters';
    } else if (formData.title.length > 255) {
      newErrors.title = 'Title must be less than 255 characters';
    }

    // Description validation
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
    }

    // Email validation
    if (!formData.submitter_email.trim()) {
      newErrors.submitter_email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.submitter_email)) {
      newErrors.submitter_email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      // Prepare submission data
      const submissionData: BugSubmissionRequest = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        severity: formData.severity,
        submitter_email: formData.submitter_email.trim(),
        browser_info: navigator.userAgent,
      };

      // Add optional fields if provided
      if (formData.steps_to_reproduce.trim()) {
        submissionData.steps_to_reproduce = formData.steps_to_reproduce.trim();
      }
      if (formData.expected_behavior.trim()) {
        submissionData.expected_behavior = formData.expected_behavior.trim();
      }
      if (formData.actual_behavior.trim()) {
        submissionData.actual_behavior = formData.actual_behavior.trim();
      }
      if (formData.affected_component) {
        submissionData.affected_component = formData.affected_component;
      }

      // Submit bug
      const result = await bugService.submitBug(submissionData);

      setSubmitSuccess(true);
      setSubmittedBugId(result.id);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to submit bug report';
      setErrors({ general: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm]);

  /**
   * Handle view bug status
   */
  const handleViewStatus = useCallback(() => {
    if (submittedBugId) {
      navigate(`/bugs/${submittedBugId}`);
    }
  }, [navigate, submittedBugId]);

  /**
   * Handle submit another bug
   */
  const handleSubmitAnother = useCallback(() => {
    setFormData({
      title: '',
      description: '',
      steps_to_reproduce: '',
      expected_behavior: '',
      actual_behavior: '',
      severity: 'medium',
      affected_component: '',
      submitter_email: formData.submitter_email, // Keep email for convenience
    });
    setSubmitSuccess(false);
    setSubmittedBugId(null);
  }, [formData.submitter_email]);

  // Success state
  if (submitSuccess && submittedBugId) {
    return (
      <div className={styles.successContainer}>
        <div className={styles.successIcon}>&#x2714;</div>
        <h2 className={styles.successTitle}>Bug Report Submitted</h2>
        <p className={styles.successMessage}>
          Your bug report has been received and is being analyzed by our AI system.
          You will receive an email with the analysis results and any automated fixes.
        </p>
        <div className={styles.trackingInfo}>
          <span className={styles.trackingLabel}>Tracking ID:</span>
          <code className={styles.trackingId}>{submittedBugId}</code>
        </div>
        <div className={styles.successActions}>
          <Button onClick={handleViewStatus} variant="primary">
            View Bug Status
          </Button>
          <Button onClick={handleSubmitAnother} variant="secondary">
            Submit Another Bug
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      {/* General Error */}
      {errors.general && (
        <div className={styles.errorBanner} role="alert">
          {errors.general}
        </div>
      )}

      {/* Title */}
      <div className={styles.formGroup}>
        <label htmlFor="title" className={styles.label}>
          Bug Title <span className={styles.required}>*</span>
        </label>
        <Input
          id="title"
          name="title"
          type="text"
          value={formData.title}
          onChange={handleChange}
          placeholder="Brief summary of the issue"
          aria-invalid={!!errors.title}
          aria-describedby={errors.title ? 'title-error' : undefined}
        />
        {errors.title && (
          <span id="title-error" className={styles.error} role="alert">
            {errors.title}
          </span>
        )}
      </div>

      {/* Description */}
      <div className={styles.formGroup}>
        <label htmlFor="description" className={styles.label}>
          Description <span className={styles.required}>*</span>
        </label>
        <Textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Detailed description of the bug. Include any error messages you see."
          rows={5}
          aria-invalid={!!errors.description}
          aria-describedby={errors.description ? 'description-error' : undefined}
        />
        {errors.description && (
          <span id="description-error" className={styles.error} role="alert">
            {errors.description}
          </span>
        )}
      </div>

      {/* Steps to Reproduce */}
      <div className={styles.formGroup}>
        <label htmlFor="steps_to_reproduce" className={styles.label}>
          Steps to Reproduce
        </label>
        <Textarea
          id="steps_to_reproduce"
          name="steps_to_reproduce"
          value={formData.steps_to_reproduce}
          onChange={handleChange}
          placeholder="1. Go to ...&#10;2. Click on ...&#10;3. Observe ..."
          rows={4}
        />
        <span className={styles.hint}>
          List the exact steps to reproduce this bug
        </span>
      </div>

      {/* Expected vs Actual */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label htmlFor="expected_behavior" className={styles.label}>
            Expected Behavior
          </label>
          <Textarea
            id="expected_behavior"
            name="expected_behavior"
            value={formData.expected_behavior}
            onChange={handleChange}
            placeholder="What should happen?"
            rows={3}
          />
        </div>
        <div className={styles.formGroup}>
          <label htmlFor="actual_behavior" className={styles.label}>
            Actual Behavior
          </label>
          <Textarea
            id="actual_behavior"
            name="actual_behavior"
            value={formData.actual_behavior}
            onChange={handleChange}
            placeholder="What actually happens?"
            rows={3}
          />
        </div>
      </div>

      {/* Severity and Component */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label htmlFor="severity" className={styles.label}>
            Severity
          </label>
          <Select
            id="severity"
            name="severity"
            value={formData.severity}
            onChange={handleChange}
            options={severityOptions}
          />
        </div>
        <div className={styles.formGroup}>
          <label htmlFor="affected_component" className={styles.label}>
            Affected Component
          </label>
          <Select
            id="affected_component"
            name="affected_component"
            value={formData.affected_component}
            onChange={handleChange}
            options={componentOptions}
          />
        </div>
      </div>

      {/* Email */}
      <div className={styles.formGroup}>
        <label htmlFor="submitter_email" className={styles.label}>
          Your Email <span className={styles.required}>*</span>
        </label>
        <Input
          id="submitter_email"
          name="submitter_email"
          type="email"
          value={formData.submitter_email}
          onChange={handleChange}
          placeholder="you@example.com"
          aria-invalid={!!errors.submitter_email}
          aria-describedby={errors.submitter_email ? 'email-error' : undefined}
        />
        {errors.submitter_email && (
          <span id="email-error" className={styles.error} role="alert">
            {errors.submitter_email}
          </span>
        )}
        <span className={styles.hint}>
          Analysis results will be sent to this email
        </span>
      </div>

      {/* Submit Button */}
      <div className={styles.formActions}>
        <Button
          type="submit"
          variant="primary"
          disabled={isSubmitting}
          className={styles.submitButton}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Bug Report'}
        </Button>
      </div>

      {/* Info Box */}
      <div className={styles.infoBox}>
        <h4>What happens next?</h4>
        <ol>
          <li>Your bug report will be analyzed by our AI system</li>
          <li>The AI will identify the root cause and affected files</li>
          <li>If possible, an automated fix will be generated</li>
          <li>A pull request will be created for review</li>
          <li>You&apos;ll receive an email with the full analysis and fix details</li>
        </ol>
      </div>
    </form>
  );
};

export default BugSubmissionForm;
