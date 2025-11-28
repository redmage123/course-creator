/**
 * Course Create Page
 *
 * BUSINESS CONTEXT:
 * Allows instructors to create new courses. Supports both standalone course creation
 * (individual instructors) and organizational course creation (corporate training with
 * track/project hierarchy).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Form validation with real-time feedback
 * - Integration with course-management API
 * - Automatic redirect after creation
 * - Support for organizational context (track_id) from URL params
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { courseService, type CreateCourseRequest, type DifficultyLevel, type DurationUnit } from '../../../services';
import { useAuth } from '../../../hooks/useAuth';
import styles from './CourseCreatePage.module.css';

export const CourseCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  // Get track_id from URL params if provided (for organizational course creation)
  const trackIdFromUrl = searchParams.get('track_id');
  const organizationId = user?.organization_id;

  const [formData, setFormData] = useState<CreateCourseRequest>({
    title: '',
    description: '',
    category: '',
    difficulty_level: 'beginner',
    estimated_duration: undefined,
    duration_unit: 'weeks',
    price: 0,
    tags: [],
    organization_id: organizationId,
    track_id: trackIdFromUrl || undefined,
  });

  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const difficultyOptions: DifficultyLevel[] = ['beginner', 'intermediate', 'advanced'];
  const durationUnits: DurationUnit[] = ['hours', 'days', 'weeks', 'months'];

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: name === 'estimated_duration' || name === 'price'
        ? value ? parseFloat(value) : undefined
        : value,
    }));
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((tag) => tag !== tagToRemove) || [],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.title.trim()) {
        throw new Error('Course title is required');
      }
      if (!formData.description.trim()) {
        throw new Error('Course description is required');
      }

      await courseService.createCourse(formData);

      // Redirect based on context
      if (trackIdFromUrl) {
        // If created from a track, redirect back to tracks page
        navigate('/organization/tracks');
      } else {
        // Otherwise redirect to courses list (when implemented)
        navigate('/dashboard/org-admin');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create course');
      console.error('Course creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Create New Course</h1>
        <p className={styles.subtitle}>
          {trackIdFromUrl
            ? 'Add a new course to your learning track'
            : 'Create a standalone course'}
        </p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        {error && (
          <div className={styles.error} role="alert">
            {error}
          </div>
        )}

        {/* Basic Information */}
        <section className={styles.section}>
          <h2>Basic Information</h2>

          <div className={styles.formGroup}>
            <label htmlFor="title">
              Course Title <span className={styles.required}>*</span>
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="e.g., Introduction to Python Programming"
              required
              maxLength={200}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">
              Description <span className={styles.required}>*</span>
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Provide a detailed description of the course..."
              required
              maxLength={2000}
              rows={5}
            />
            <span className={styles.charCount}>
              {formData.description.length} / 2000
            </span>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="category">Category</label>
            <input
              type="text"
              id="category"
              name="category"
              value={formData.category || ''}
              onChange={handleInputChange}
              placeholder="e.g., Programming, Data Science, Business"
            />
          </div>
        </section>

        {/* Course Settings */}
        <section className={styles.section}>
          <h2>Course Settings</h2>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="difficulty_level">Difficulty Level</label>
              <select
                id="difficulty_level"
                name="difficulty_level"
                value={formData.difficulty_level}
                onChange={handleInputChange}
              >
                {difficultyOptions.map((level) => (
                  <option key={level} value={level}>
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="estimated_duration">Estimated Duration</label>
              <input
                type="number"
                id="estimated_duration"
                name="estimated_duration"
                value={formData.estimated_duration || ''}
                onChange={handleInputChange}
                min="1"
                placeholder="e.g., 8"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="duration_unit">Duration Unit</label>
              <select
                id="duration_unit"
                name="duration_unit"
                value={formData.duration_unit}
                onChange={handleInputChange}
              >
                {durationUnits.map((unit) => (
                  <option key={unit} value={unit}>
                    {unit.charAt(0).toUpperCase() + unit.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="price">Price (USD)</label>
            <input
              type="number"
              id="price"
              name="price"
              value={formData.price}
              onChange={handleInputChange}
              min="0"
              step="0.01"
              placeholder="0.00"
            />
            <span className={styles.helpText}>Set to 0 for free courses</span>
          </div>
        </section>

        {/* Tags */}
        <section className={styles.section}>
          <h2>Tags</h2>
          <div className={styles.formGroup}>
            <label htmlFor="tag-input">Add Tags</label>
            <div className={styles.tagInputContainer}>
              <input
                type="text"
                id="tag-input"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                placeholder="Type a tag and press Enter"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className={styles.addTagBtn}
              >
                Add Tag
              </button>
            </div>

            {formData.tags && formData.tags.length > 0 && (
              <div className={styles.tagsList}>
                {formData.tags.map((tag) => (
                  <span key={tag} className={styles.tag}>
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className={styles.removeTagBtn}
                      aria-label={`Remove ${tag}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Form Actions */}
        <div className={styles.actions}>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className={styles.cancelBtn}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className={styles.submitBtn}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Course'}
          </button>
        </div>
      </form>
    </div>
  );
};
