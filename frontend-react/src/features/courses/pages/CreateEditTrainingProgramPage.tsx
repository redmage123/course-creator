/**
 * Create/Edit Training Program Page
 *
 * BUSINESS CONTEXT:
 * Form for instructors to create new training programs or edit existing ones.
 * Handles program metadata, pricing, difficulty, tags, and initial setup.
 * Saves as draft by default, publish separately.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Unified create/edit form with mode detection
 * - Form validation with error messages
 * - Optimistic updates with React Query
 * - Tag management with add/remove
 * - Draft auto-save (future enhancement)
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { useAuth } from '../../../hooks/useAuth';
import { trainingProgramService } from '../../../services';
import type { CreateTrainingProgramRequest } from '../../../services';
import styles from './CreateEditTrainingProgramPage.module.css';

/**
 * Create/Edit Training Program Page Component
 *
 * WHY THIS APPROACH:
 * - Single component handles both create and edit modes
 * - Comprehensive form validation
 * - User-friendly error messages
 * - Tag management with dynamic add/remove
 * - Saves as draft by default for safety
 */
export const CreateEditTrainingProgramPage: React.FC = () => {
  const { programId } = useParams<{ programId?: string }>();
  const { user, userId, organizationId } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const isEditMode = !!programId;

  // Determine context based on current path
  const isOrgAdminContext = window.location.pathname.startsWith('/organization');

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [difficultyLevel, setDifficultyLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [estimatedDuration, setEstimatedDuration] = useState<number>(0);
  const [durationUnit, setDurationUnit] = useState<'hours' | 'days' | 'weeks' | 'months'>('hours');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  // Form validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * Fetch existing program data (edit mode only)
   */
  const { data: existingProgram, isLoading: loadingProgram } = useQuery({
    queryKey: ['trainingProgram', programId],
    queryFn: () => trainingProgramService.getTrainingProgramById(programId!),
    enabled: isEditMode,
  });

  /**
   * Populate form with existing data (edit mode)
   */
  useEffect(() => {
    if (existingProgram) {
      setTitle(existingProgram.title);
      setDescription(existingProgram.description || '');
      setCategory(existingProgram.category || '');
      setDifficultyLevel(existingProgram.difficulty_level);
      setEstimatedDuration(existingProgram.estimated_duration || 0);
      setDurationUnit(existingProgram.duration_unit);
      setTags(existingProgram.tags || []);
    }
  }, [existingProgram]);

  /**
   * Get redirect path based on context
   */
  const getRedirectPath = () => {
    return isOrgAdminContext ? '/organization/programs' : '/instructor/programs';
  };

  /**
   * Create program mutation
   */
  const createMutation = useMutation({
    mutationFn: (data: CreateTrainingProgramRequest) =>
      trainingProgramService.createTrainingProgram(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingPrograms'] });
      navigate(getRedirectPath());
    },
  });

  /**
   * Update program mutation
   */
  const updateMutation = useMutation({
    mutationFn: (data: CreateTrainingProgramRequest) =>
      trainingProgramService.updateTrainingProgram(programId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingPrograms'] });
      queryClient.invalidateQueries({ queryKey: ['trainingProgram', programId] });
      navigate(getRedirectPath());
    },
  });

  /**
   * Validate form
   */
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = 'Program title is required';
    }

    if (title.length > 200) {
      newErrors.title = 'Title must be less than 200 characters';
    }

    if (description.length > 2000) {
      newErrors.description = 'Description must be less than 2000 characters';
    }

    if (estimatedDuration && estimatedDuration <= 0) {
      newErrors.estimatedDuration = 'Duration must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const formData: CreateTrainingProgramRequest = {
      title: title.trim(),
      description: description.trim() || '',
      category: category.trim() || undefined,
      difficulty_level: difficultyLevel,
      estimated_duration: estimatedDuration || undefined,
      duration_unit: durationUnit,
      tags,
      organization_id: organizationId,
      // Note: instructor_id will be set automatically by the backend based on the authenticated user
    };

    try {
      if (isEditMode) {
        await updateMutation.mutateAsync(formData);
      } else {
        await createMutation.mutateAsync(formData);
      }
    } catch (error) {
      console.error('Failed to save program:', error);
    }
  };

  /**
   * Handle add tag
   */
  const handleAddTag = () => {
    const trimmedTag = newTag.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
      setNewTag('');
    }
  };

  /**
   * Handle remove tag
   */
  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  /**
   * Handle cancel
   */
  const handleCancel = () => {
    navigate(getRedirectPath());
  };

  /**
   * Loading State (Edit Mode)
   */
  if (isEditMode && loadingProgram) {
    return (
      <DashboardLayout>
        <div className={styles['form-page']}>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <Spinner size="large" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  /**
   * Form Display
   */
  return (
    <DashboardLayout>
      <div className={styles['form-page']}>
        {/* Page Header */}
        <div className={styles['page-header']}>
          <Heading level="h1" gutterBottom>
            {isEditMode ? 'Edit Training Program' : 'Create New Training Program'}
          </Heading>
          <p className={styles['header-description']}>
            {isEditMode
              ? 'Update program details and save changes'
              : 'Fill in the details below to create a new training program. The program will be saved as a draft.'}
          </p>
        </div>

        {/* Form Card */}
        <Card variant="outlined" padding="large">
          <form onSubmit={handleSubmit} className={styles['program-form']} noValidate>
            {/* Basic Information Section */}
            <div className={styles['form-section']}>
              <Heading level="h3" gutterBottom>
                Basic Information
              </Heading>

              {/* Title */}
              <div className={styles['form-group']}>
                <label htmlFor="title" className={styles['form-label']}>
                  Program Title <span className={styles['required']}>*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={`${styles['form-input']} ${errors.title ? styles['input-error'] : ''}`}
                  placeholder="e.g., Advanced Machine Learning for Data Scientists"
                  required
                />
                {errors.title && (
                  <span className={styles['error-message']} role="alert">{errors.title}</span>
                )}
              </div>

              {/* Description */}
              <div className={styles['form-group']}>
                <label htmlFor="description" className={styles['form-label']}>
                  Program Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={`${styles['form-textarea']} ${errors.description ? styles['input-error'] : ''}`}
                  placeholder="Provide a detailed description of the training program..."
                  rows={6}
                  maxLength={2000}
                />
                <span className={styles['char-count']}>
                  {description.length} / 2000 characters
                </span>
                {errors.description && (
                  <span className={styles['error-message']} role="alert">{errors.description}</span>
                )}
              </div>

              {/* Category */}
              <div className={styles['form-group']}>
                <label htmlFor="category" className={styles['form-label']}>
                  Category
                </label>
                <input
                  id="category"
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className={styles['form-input']}
                  placeholder="e.g., Artificial Intelligence, Cloud Computing, Cybersecurity"
                />
              </div>
            </div>

            {/* Program Details Section */}
            <div className={styles['form-section']}>
              <Heading level="h3" gutterBottom>
                Program Details
              </Heading>

              {/* Difficulty Level */}
              <div className={styles['form-group']}>
                <label htmlFor="difficulty" className={styles['form-label']}>
                  Difficulty Level <span className={styles['required']}>*</span>
                </label>
                <select
                  id="difficulty"
                  value={difficultyLevel}
                  onChange={(e) => setDifficultyLevel(e.target.value as any)}
                  className={styles['form-select']}
                  required
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              {/* Duration */}
              <div className={styles['form-row']}>
                <div className={styles['form-group']}>
                  <label htmlFor="duration" className={styles['form-label']}>
                    Estimated Duration
                  </label>
                  <input
                    id="duration"
                    type="number"
                    value={estimatedDuration || ''}
                    onChange={(e) => setEstimatedDuration(Number(e.target.value))}
                    className={`${styles['form-input']} ${errors.estimatedDuration ? styles['input-error'] : ''}`}
                    placeholder="0"
                    min="0"
                  />
                  {errors.estimatedDuration && (
                    <span className={styles['error-message']} role="alert">{errors.estimatedDuration}</span>
                  )}
                </div>

                <div className={styles['form-group']}>
                  <label htmlFor="durationUnit" className={styles['form-label']}>
                    Duration Unit
                  </label>
                  <select
                    id="durationUnit"
                    value={durationUnit}
                    onChange={(e) => setDurationUnit(e.target.value as any)}
                    className={styles['form-select']}
                  >
                    <option value="hours">Hours</option>
                    <option value="days">Days</option>
                    <option value="weeks">Weeks</option>
                    <option value="months">Months</option>
                  </select>
                </div>
              </div>

            </div>

            {/* Tags Section */}
            <div className={styles['form-section']}>
              <Heading level="h3" gutterBottom>
                Tags
              </Heading>

              <div className={styles['tags-input-group']}>
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  className={styles['form-input']}
                  placeholder="Add a tag (e.g., Python, Machine Learning)"
                />
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleAddTag}
                  disabled={!newTag.trim()}
                >
                  Add Tag
                </Button>
              </div>

              {/* Tags Display */}
              {tags.length > 0 && (
                <div className={styles['tags-display']}>
                  {tags.map((tag, index) => (
                    <span key={index} className={styles['tag']}>
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className={styles['tag-remove']}
                        aria-label={`Remove ${tag} tag`}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Form Actions */}
            <div className={styles['form-actions']}>
              <Button
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <Spinner size="small" />
                    {isEditMode ? 'Saving Changes...' : 'Creating Program...'}
                  </>
                ) : (
                  isEditMode ? 'Save Changes' : 'Create Program'
                )}
              </Button>
            </div>

            {/* Error Display */}
            {(createMutation.isError || updateMutation.isError) && (
              <div className={styles['submission-error']} role="alert">
                {(createMutation.error as Error)?.message || (updateMutation.error as Error)?.message || 'Failed to save program. Please try again.'}
              </div>
            )}
          </form>
        </Card>
      </div>
    </DashboardLayout>
  );
};
