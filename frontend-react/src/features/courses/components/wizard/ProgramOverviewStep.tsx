/**
 * ProgramOverviewStep - Step 1 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Allows instructors/admins to view and edit program metadata:
 * title, description, category, difficulty, duration, and tags.
 * Students see a read-only summary.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reuses same fields as CreateEditTrainingProgramPage
 * - Inline editing with save on "Next"
 * - Read-only mode for student role
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../../components/atoms/Button';
import type { TrainingProgram, UpdateTrainingProgramRequest } from '../../../../services';
import styles from './ProgramOverviewStep.module.css';

interface ProgramOverviewStepProps {
  program: TrainingProgram;
  readOnly?: boolean;
  onSave?: (data: UpdateTrainingProgramRequest) => Promise<void>;
}

export const ProgramOverviewStep: React.FC<ProgramOverviewStepProps> = ({
  program,
  readOnly = false,
  onSave,
}) => {
  const [title, setTitle] = useState(program.title);
  const [description, setDescription] = useState(program.description || '');
  const [category, setCategory] = useState(program.category || '');
  const [difficultyLevel, setDifficultyLevel] = useState(program.difficulty_level);
  const [estimatedDuration, setEstimatedDuration] = useState(program.estimated_duration || 0);
  const [durationUnit, setDurationUnit] = useState(program.duration_unit);
  const [tags, setTags] = useState<string[]>(program.tags || []);
  const [newTag, setNewTag] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    setTitle(program.title);
    setDescription(program.description || '');
    setCategory(program.category || '');
    setDifficultyLevel(program.difficulty_level);
    setEstimatedDuration(program.estimated_duration || 0);
    setDurationUnit(program.duration_unit);
    setTags(program.tags || []);
  }, [program]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = 'Program title is required';
    if (title.length > 200) newErrors.title = 'Title must be less than 200 characters';
    if (description.length > 2000) newErrors.description = 'Description must be less than 2000 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate() || !onSave) return;
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await onSave({
        title: title.trim(),
        description: description.trim(),
        category: category.trim() || undefined,
        difficulty_level: difficultyLevel,
        estimated_duration: estimatedDuration || undefined,
        duration_unit: durationUnit,
        tags,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : 'Failed to save program. Please try again.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddTag = () => {
    const trimmed = newTag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const formatDifficulty = (level: string) =>
    level.charAt(0).toUpperCase() + level.slice(1);

  if (readOnly) {
    return (
      <div className={styles.container}>
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>{program.title}</h3>
          {program.description && (
            <p className={styles.readOnlyValue}>{program.description}</p>
          )}
        </div>

        <div className={styles.metadataGrid}>
          <div className={styles.formGroup}>
            <span className={styles.formLabel}>Difficulty</span>
            <span className={styles.readOnlyValue}>{formatDifficulty(program.difficulty_level)}</span>
          </div>
          {program.estimated_duration && (
            <div className={styles.formGroup}>
              <span className={styles.formLabel}>Duration</span>
              <span className={styles.readOnlyValue}>
                {program.estimated_duration} {program.duration_unit}
              </span>
            </div>
          )}
          {program.category && (
            <div className={styles.formGroup}>
              <span className={styles.formLabel}>Category</span>
              <span className={styles.readOnlyValue}>{program.category}</span>
            </div>
          )}
        </div>

        {tags.length > 0 && (
          <div className={styles.tagsDisplay}>
            {tags.map((tag) => (
              <span key={tag} className={styles.tag}>{tag}</span>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Basic Information</h3>

        <div className={styles.formGroup}>
          <label htmlFor="overview-title" className={styles.formLabel}>
            Program Title <span className={styles.required}>*</span>
          </label>
          <input
            id="overview-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={`${styles.formInput} ${errors.title ? styles.inputError : ''}`}
            placeholder="e.g., Advanced Machine Learning for Data Scientists"
          />
          {errors.title && <span className={styles.errorMessage} role="alert">{errors.title}</span>}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="overview-description" className={styles.formLabel}>
            Description
          </label>
          <textarea
            id="overview-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={`${styles.formTextarea} ${errors.description ? styles.inputError : ''}`}
            placeholder="Provide a detailed description..."
            rows={5}
            maxLength={2000}
          />
          <span className={styles.charCount}>{description.length} / 2000</span>
          {errors.description && <span className={styles.errorMessage} role="alert">{errors.description}</span>}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="overview-category" className={styles.formLabel}>Category</label>
          <input
            id="overview-category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className={styles.formInput}
            placeholder="e.g., Artificial Intelligence, Cloud Computing"
          />
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Program Details</h3>

        <div className={styles.formGroup}>
          <label htmlFor="overview-difficulty" className={styles.formLabel}>
            Difficulty Level <span className={styles.required}>*</span>
          </label>
          <select
            id="overview-difficulty"
            value={difficultyLevel}
            onChange={(e) => setDifficultyLevel(e.target.value as typeof difficultyLevel)}
            className={styles.formSelect}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="overview-duration" className={styles.formLabel}>Estimated Duration</label>
            <input
              id="overview-duration"
              type="number"
              value={estimatedDuration || ''}
              onChange={(e) => setEstimatedDuration(Number(e.target.value))}
              className={styles.formInput}
              placeholder="0"
              min="0"
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="overview-duration-unit" className={styles.formLabel}>Unit</label>
            <select
              id="overview-duration-unit"
              value={durationUnit}
              onChange={(e) => setDurationUnit(e.target.value as typeof durationUnit)}
              className={styles.formSelect}
            >
              <option value="hours">Hours</option>
              <option value="days">Days</option>
              <option value="weeks">Weeks</option>
              <option value="months">Months</option>
            </select>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Tags</h3>

        <div className={styles.tagsInputGroup}>
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddTag(); } }}
            className={styles.formInput}
            placeholder="Add a tag..."
          />
          <Button type="button" variant="secondary" size="small" onClick={handleAddTag} disabled={!newTag.trim()}>
            Add
          </Button>
        </div>

        {tags.length > 0 && (
          <div className={styles.tagsDisplay}>
            {tags.map((tag) => (
              <span key={tag} className={styles.tag}>
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className={styles.tagRemove}
                  aria-label={`Remove ${tag} tag`}
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {onSave && (
        <div>
          <Button
            type="button"
            variant="primary"
            onClick={handleSave}
            loading={isSaving}
            disabled={isSaving}
          >
            Save Changes
          </Button>
          {saveError && (
            <p className={styles.saveError} role="alert">{saveError}</p>
          )}
          {saveSuccess && (
            <p className={styles.saveSuccess}>Changes saved.</p>
          )}
        </div>
      )}
    </div>
  );
};

ProgramOverviewStep.displayName = 'ProgramOverviewStep';
