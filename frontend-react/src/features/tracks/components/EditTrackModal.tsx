/**
 * Edit Track Modal Component
 *
 * BUSINESS CONTEXT:
 * Organization admins can update track details including name, description,
 * difficulty level, duration, and status.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Controlled form with validation
 * - React Query mutation for API calls
 * - Pre-populated with existing track data
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Modal } from '../../../components/atoms/Modal';
import { Button } from '../../../components/atoms/Button';
import { Input } from '../../../components/atoms/Input';
import { Select } from '../../../components/atoms/Select';
import { Textarea } from '../../../components/atoms/Textarea';
import { Spinner } from '../../../components/atoms/Spinner';
import { trackService, type Track, type UpdateTrackRequest } from '../../../services';
import styles from './EditTrackModal.module.css';

/**
 * Edit Track Modal Props
 */
export interface EditTrackModalProps {
  isOpen: boolean;
  track: Track;
  onClose: () => void;
  onSuccess: () => void;
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
  status: 'draft' | 'active' | 'archived';
  target_audience: string;
  prerequisites: string;
  learning_objectives: string;
}

/**
 * Edit Track Modal Component
 */
export const EditTrackModal: React.FC<EditTrackModalProps> = ({
  isOpen,
  track,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

  /**
   * Initialize form with existing track data
   */
  const [formData, setFormData] = useState<TrackFormData>({
    name: track.name,
    description: track.description || '',
    duration_weeks: track.duration_weeks?.toString() || '',
    difficulty_level: track.difficulty_level,
    max_students: track.max_students?.toString() || '',
    status: track.status,
    target_audience: track.target_audience?.join(', ') || '',
    prerequisites: track.prerequisites?.join(', ') || '',
    learning_objectives: track.learning_objectives?.join(', ') || '',
  });

  /**
   * Handle input changes
   */
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  /**
   * Update track mutation
   */
  const updateMutation = useMutation({
    mutationFn: (data: UpdateTrackRequest) => trackService.updateTrack(track.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tracks'] });
      onSuccess();
      setSubmitError(null);
    },
    onError: (error: any) => {
      setSubmitError(error.message || 'Failed to update track');
    },
  });

  /**
   * Handle form submission
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    // Validate required fields
    if (!formData.name.trim()) {
      setSubmitError('Track name is required');
      return;
    }

    // Prepare update data
    const updateData: UpdateTrackRequest = {
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      duration_weeks: formData.duration_weeks ? parseInt(formData.duration_weeks, 10) : undefined,
      difficulty_level: formData.difficulty_level,
      max_students: formData.max_students ? parseInt(formData.max_students, 10) : undefined,
      status: formData.status,
      target_audience: formData.target_audience
        ? formData.target_audience.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
      prerequisites: formData.prerequisites
        ? formData.prerequisites.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
      learning_objectives: formData.learning_objectives
        ? formData.learning_objectives.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
    };

    updateMutation.mutate(updateData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Track"
      size="large"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={updateMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? <Spinner size="small" /> : 'Save Changes'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Basic Information */}
        <div className={styles['form-section']}>
          <h3 className={styles['section-title']}>Basic Information</h3>

          <Input
            name="name"
            label="Track Name"
            type="text"
            placeholder="Enter track name"
            value={formData.name}
            onChange={handleChange}
            required
            fullWidth
          />

          <Textarea
            name="description"
            label="Description"
            placeholder="Describe this learning track"
            value={formData.description}
            onChange={handleChange}
            fullWidth
            rows={3}
          />
        </div>

        {/* Track Settings */}
        <div className={styles['form-section']}>
          <h3 className={styles['section-title']}>Track Settings</h3>

          <div className={styles['form-row']}>
            <Select
              name="difficulty_level"
              label="Difficulty Level"
              value={formData.difficulty_level}
              onChange={handleChange}
              fullWidth
              required
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </Select>

            <Select
              name="status"
              label="Status"
              value={formData.status}
              onChange={handleChange}
              fullWidth
              required
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </Select>
          </div>

          <div className={styles['form-row']}>
            <Input
              name="duration_weeks"
              label="Duration (weeks)"
              type="number"
              placeholder="e.g., 12"
              value={formData.duration_weeks}
              onChange={handleChange}
              fullWidth
              min="1"
            />

            <Input
              name="max_students"
              label="Max Students"
              type="number"
              placeholder="e.g., 30"
              value={formData.max_students}
              onChange={handleChange}
              fullWidth
              min="1"
            />
          </div>
        </div>

        {/* Additional Details */}
        <div className={styles['form-section']}>
          <h3 className={styles['section-title']}>Additional Details</h3>

          <Textarea
            name="target_audience"
            label="Target Audience"
            placeholder="e.g., Web developers, Data scientists (comma-separated)"
            value={formData.target_audience}
            onChange={handleChange}
            fullWidth
            rows={2}
            helperText="Comma-separated list"
          />

          <Textarea
            name="prerequisites"
            label="Prerequisites"
            placeholder="e.g., Basic programming, HTML/CSS (comma-separated)"
            value={formData.prerequisites}
            onChange={handleChange}
            fullWidth
            rows={2}
            helperText="Comma-separated list"
          />

          <Textarea
            name="learning_objectives"
            label="Learning Objectives"
            placeholder="e.g., Build web apps, Understand React (comma-separated)"
            value={formData.learning_objectives}
            onChange={handleChange}
            fullWidth
            rows={3}
            helperText="Comma-separated list"
          />
        </div>

        {/* Error message */}
        {submitError && (
          <div className={styles.error} role="alert">
            {submitError}
          </div>
        )}
      </form>
    </Modal>
  );
};
