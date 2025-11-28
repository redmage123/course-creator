/**
 * Create Track Modal Component
 *
 * BUSINESS CONTEXT:
 * Modal for creating new learning tracks within a project.
 * Organization admins use this to structure courses into learning paths.
 * Validates input and provides immediate feedback.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Form validation with real-time error messages
 * - React Query mutation for API integration
 * - Loading states and error handling
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Modal } from '../../../components/atoms/Modal';
import { Button } from '../../../components/atoms/Button';
import { Input } from '../../../components/atoms/Input';
import { Select } from '../../../components/atoms/Select';
import { Textarea } from '../../../components/atoms/Textarea';
import { trackService, type CreateTrackRequest } from '../../../services';
import styles from './CreateTrackModal.module.css';

/**
 * Create Track Modal Props
 */
export interface CreateTrackModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Project ID for the track */
  projectId: string;
  /** Optional callback when track is created successfully */
  onSuccess?: (trackId: string) => void;
}

/**
 * Form Data Interface
 */
interface TrackFormData {
  name: string;
  description: string;
  duration_weeks: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  max_students: string;
  target_audience: string;
  prerequisites: string;
  learning_objectives: string;
}

/**
 * Initial Form State
 */
const initialFormData: TrackFormData = {
  name: '',
  description: '',
  duration_weeks: '',
  difficulty_level: 'beginner',
  max_students: '',
  target_audience: '',
  prerequisites: '',
  learning_objectives: '',
};

/**
 * Create Track Modal Component
 *
 * WHY THIS APPROACH:
 * - Controlled form with local state for responsiveness
 * - React Query mutation for optimistic updates
 * - Form validation before submission
 * - Clear error messaging
 */
export const CreateTrackModal: React.FC<CreateTrackModalProps> = ({
  isOpen,
  onClose,
  projectId,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<TrackFormData>(initialFormData);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  /**
   * Create track mutation
   */
  const createMutation = useMutation({
    mutationFn: (data: CreateTrackRequest) => {
      console.log('[CreateTrackModal] mutationFn called with data:', data);
      return trackService.createTrack(data);
    },
    onSuccess: (createdTrack) => {
      console.log('[CreateTrackModal] Track created successfully:', createdTrack);

      // Invalidate tracks query to refresh list
      queryClient.invalidateQueries({ queryKey: ['tracks'] });

      // Call success callback
      if (onSuccess) {
        onSuccess(createdTrack.id);
      }

      // Reset form and close modal
      setFormData(initialFormData);
      setValidationErrors({});
      onClose();
    },
    onError: (error: any) => {
      console.error('[CreateTrackModal] Failed to create track:', error);
      console.error('[CreateTrackModal] Error details:', {
        message: error.message,
        response: error.response,
        stack: error.stack,
      });
      // Show error message in form
      setValidationErrors({
        submit: error.message || 'Failed to create track. Please try again.',
      });
    },
  });

  /**
   * Handle input change
   */
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required fields
    if (!formData.name.trim()) {
      errors.name = 'Track name is required';
    } else if (formData.name.length < 3) {
      errors.name = 'Track name must be at least 3 characters';
    } else if (formData.name.length > 200) {
      errors.name = 'Track name must be less than 200 characters';
    }

    // Optional numeric fields validation
    if (formData.duration_weeks && isNaN(Number(formData.duration_weeks))) {
      errors.duration_weeks = 'Duration must be a number';
    } else if (formData.duration_weeks && Number(formData.duration_weeks) < 1) {
      errors.duration_weeks = 'Duration must be at least 1 week';
    } else if (formData.duration_weeks && Number(formData.duration_weeks) > 52) {
      errors.duration_weeks = 'Duration must be less than 52 weeks';
    }

    if (formData.max_students && isNaN(Number(formData.max_students))) {
      errors.max_students = 'Max students must be a number';
    } else if (formData.max_students && Number(formData.max_students) < 1) {
      errors.max_students = 'Max students must be at least 1';
    } else if (formData.max_students && Number(formData.max_students) > 1000) {
      errors.max_students = 'Max students must be less than 1000';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent | React.MouseEvent) => {
    console.log('[CreateTrackModal] handleSubmit called');
    console.log('[CreateTrackModal] Project ID:', projectId);
    console.log('[CreateTrackModal] Form data:', formData);

    e.preventDefault();

    // Validate form
    const isValid = validateForm();
    console.log('[CreateTrackModal] Validation result:', isValid);
    console.log('[CreateTrackModal] Validation errors:', validationErrors);

    if (!isValid) {
      console.error('[CreateTrackModal] Validation failed, not submitting');
      return;
    }

    // Parse array fields (comma-separated strings)
    const parseArrayField = (value: string): string[] => {
      return value
        .split('\n')
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
    };

    // Build request data
    const requestData: CreateTrackRequest = {
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      project_id: projectId,
      duration_weeks: formData.duration_weeks ? Number(formData.duration_weeks) : undefined,
      difficulty_level: formData.difficulty_level,
      max_students: formData.max_students ? Number(formData.max_students) : undefined,
      target_audience: parseArrayField(formData.target_audience),
      prerequisites: parseArrayField(formData.prerequisites),
      learning_objectives: parseArrayField(formData.learning_objectives),
    };

    console.log('[CreateTrackModal] Submitting request data:', requestData);

    // Submit mutation
    createMutation.mutate(requestData);
    console.log('[CreateTrackModal] Mutation called');
  };

  /**
   * Handle modal close
   */
  const handleClose = () => {
    if (!createMutation.isPending) {
      setFormData(initialFormData);
      setValidationErrors({});
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New Track"
      size="large"
      preventClose={createMutation.isPending}
    >
      <form className={styles.form} onSubmit={handleSubmit}>
        {/* Track Name */}
        <div className={styles.formGroup}>
          <label htmlFor="name" className={styles.label}>
            Track Name <span className={styles.required}>*</span>
          </label>
          <Input
            id="name"
            name="name"
            type="text"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g., Web Development Bootcamp"
            disabled={createMutation.isPending}
            error={validationErrors.name}
          />
          {validationErrors.name && (
            <span className={styles.errorText}>{validationErrors.name}</span>
          )}
        </div>

        {/* Description */}
        <div className={styles.formGroup}>
          <label htmlFor="description" className={styles.label}>
            Description
          </label>
          <Textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe what students will learn in this track..."
            rows={3}
            disabled={createMutation.isPending}
          />
        </div>

        {/* Two Column Grid */}
        <div className={styles.gridTwo}>
          {/* Difficulty Level */}
          <div className={styles.formGroup}>
            <label htmlFor="difficulty_level" className={styles.label}>
              Difficulty Level
            </label>
            <Select
              id="difficulty_level"
              name="difficulty_level"
              value={formData.difficulty_level}
              onChange={(value) => {
                const event = {
                  target: { name: 'difficulty_level', value }
                } as React.ChangeEvent<HTMLSelectElement>;
                handleChange(event);
              }}
              disabled={createMutation.isPending}
              options={[
                { value: 'beginner', label: 'Beginner' },
                { value: 'intermediate', label: 'Intermediate' },
                { value: 'advanced', label: 'Advanced' },
              ]}
            />
          </div>

          {/* Duration */}
          <div className={styles.formGroup}>
            <label htmlFor="duration_weeks" className={styles.label}>
              Duration (weeks)
            </label>
            <Input
              id="duration_weeks"
              name="duration_weeks"
              type="number"
              value={formData.duration_weeks}
              onChange={handleChange}
              placeholder="e.g., 12"
              min="1"
              max="52"
              disabled={createMutation.isPending}
              error={validationErrors.duration_weeks}
            />
            {validationErrors.duration_weeks && (
              <span className={styles.errorText}>{validationErrors.duration_weeks}</span>
            )}
          </div>
        </div>

        {/* Max Students */}
        <div className={styles.formGroup}>
          <label htmlFor="max_students" className={styles.label}>
            Maximum Students (Optional)
          </label>
          <Input
            id="max_students"
            name="max_students"
            type="number"
            value={formData.max_students}
            onChange={handleChange}
            placeholder="Leave empty for unlimited"
            min="1"
            max="1000"
            disabled={createMutation.isPending}
            error={validationErrors.max_students}
          />
          {validationErrors.max_students && (
            <span className={styles.errorText}>{validationErrors.max_students}</span>
          )}
        </div>

        {/* Target Audience */}
        <div className={styles.formGroup}>
          <label htmlFor="target_audience" className={styles.label}>
            Target Audience
          </label>
          <Textarea
            id="target_audience"
            name="target_audience"
            value={formData.target_audience}
            onChange={handleChange}
            placeholder="Enter each audience on a new line&#10;e.g., Junior developers&#10;Career changers"
            rows={3}
            disabled={createMutation.isPending}
          />
          <span className={styles.helpText}>One item per line</span>
        </div>

        {/* Prerequisites */}
        <div className={styles.formGroup}>
          <label htmlFor="prerequisites" className={styles.label}>
            Prerequisites
          </label>
          <Textarea
            id="prerequisites"
            name="prerequisites"
            value={formData.prerequisites}
            onChange={handleChange}
            placeholder="Enter each prerequisite on a new line&#10;e.g., Basic HTML knowledge&#10;Familiarity with command line"
            rows={3}
            disabled={createMutation.isPending}
          />
          <span className={styles.helpText}>One item per line</span>
        </div>

        {/* Learning Objectives */}
        <div className={styles.formGroup}>
          <label htmlFor="learning_objectives" className={styles.label}>
            Learning Objectives
          </label>
          <Textarea
            id="learning_objectives"
            name="learning_objectives"
            value={formData.learning_objectives}
            onChange={handleChange}
            placeholder="Enter each objective on a new line&#10;e.g., Build responsive web applications&#10;Deploy to production"
            rows={4}
            disabled={createMutation.isPending}
          />
          <span className={styles.helpText}>One objective per line</span>
        </div>

        {/* Submit Error */}
        {validationErrors.submit && (
          <div className={styles.errorBox}>
            <strong>Error:</strong> {validationErrors.submit}
          </div>
        )}

        {/* Form Actions */}
        <div className={styles.actions}>
          <Button
            type="button"
            variant="ghost"
            onClick={handleClose}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Track'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
