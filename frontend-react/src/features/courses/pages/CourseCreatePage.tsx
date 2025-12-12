/**
 * Course Create Page
 *
 * BUSINESS CONTEXT:
 * Allows instructors to create new courses. Supports both standalone course creation
 * (individual instructors) and organizational course creation (corporate training with
 * track/project hierarchy).
 *
 * URL-BASED GENERATION (v3.3.2):
 * Instructors can now provide external documentation URLs (Salesforce, AWS, internal wikis)
 * to automatically generate course syllabi and content. The system fetches, parses, and
 * uses RAG to create comprehensive training materials from third-party documentation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Form validation with real-time feedback
 * - Integration with course-management API
 * - URL-based generation with progress tracking
 * - Automatic redirect after creation
 * - Support for organizational context (track_id) from URL params
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  courseService,
  syllabusService,
  type CreateCourseRequest,
  type DifficultyLevel,
  type DurationUnit,
  type GenerateSyllabusRequest,
  type SyllabusData,
  type GenerationProgress,
  type CourseLevel,
} from '../../../services';
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

  // URL-based generation state
  const [useUrlGeneration, setUseUrlGeneration] = useState(false);
  const [sourceUrls, setSourceUrls] = useState<string[]>(['']);
  const [urlErrors, setUrlErrors] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress | null>(null);
  const [generatedSyllabus, setGeneratedSyllabus] = useState<SyllabusData | null>(null);
  const [useRagEnhancement, setUseRagEnhancement] = useState(true);
  const [includeCodeExamples, setIncludeCodeExamples] = useState(true);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const difficultyOptions: DifficultyLevel[] = ['beginner', 'intermediate', 'advanced'];
  const courseLevelOptions: CourseLevel[] = ['beginner', 'intermediate', 'advanced'];
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

  // URL-based generation handlers
  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...sourceUrls];
    newUrls[index] = value;
    setSourceUrls(newUrls);

    // Validate as user types
    const newErrors = [...urlErrors];
    if (value.trim()) {
      const validation = syllabusService.validateUrl(value);
      newErrors[index] = validation.error || '';
    } else {
      newErrors[index] = '';
    }
    setUrlErrors(newErrors);
  };

  const handleAddUrl = () => {
    if (sourceUrls.length < 10) {
      setSourceUrls([...sourceUrls, '']);
      setUrlErrors([...urlErrors, '']);
    }
  };

  const handleRemoveUrl = (index: number) => {
    if (sourceUrls.length > 1) {
      const newUrls = sourceUrls.filter((_, i) => i !== index);
      const newErrors = urlErrors.filter((_, i) => i !== index);
      setSourceUrls(newUrls);
      setUrlErrors(newErrors);
    }
  };

  const getValidUrls = useCallback(() => {
    return sourceUrls.filter((url) => {
      const trimmed = url.trim();
      return trimmed && syllabusService.validateUrl(trimmed).valid;
    });
  }, [sourceUrls]);

  // Cleanup progress polling on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  const startProgressPolling = useCallback((requestId: string) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    progressIntervalRef.current = setInterval(async () => {
      try {
        const response = await syllabusService.getGenerationProgress(requestId);
        if (response.success) {
          setGenerationProgress(response.progress);

          // Stop polling when complete
          if (response.progress.generation_complete) {
            if (progressIntervalRef.current) {
              clearInterval(progressIntervalRef.current);
              progressIntervalRef.current = null;
            }
          }
        }
      } catch (err) {
        console.error('Progress polling error:', err);
      }
    }, 2000);
  }, []);

  const handleGenerateSyllabus = async () => {
    const validUrls = getValidUrls();
    if (validUrls.length === 0) {
      setError('Please enter at least one valid URL');
      return;
    }

    if (!formData.title.trim()) {
      setError('Please enter a course title before generating');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedSyllabus(null);
    setGenerationProgress(null);

    try {
      const request: GenerateSyllabusRequest = {
        title: formData.title,
        description: formData.description || `Training course generated from external documentation`,
        level: formData.difficulty_level as CourseLevel,
        source_urls: validUrls,
        use_rag_enhancement: useRagEnhancement,
        include_code_examples: includeCodeExamples,
      };

      const response = await syllabusService.generateSyllabus(request);

      if (response.request_id) {
        startProgressPolling(response.request_id);
      }

      if (response.success && response.syllabus) {
        setGeneratedSyllabus(response.syllabus);

        // Auto-fill form with generated content
        if (response.syllabus.description && !formData.description) {
          setFormData((prev) => ({
            ...prev,
            description: response.syllabus!.description,
          }));
        }
      } else {
        setError(response.message || 'Failed to generate syllabus');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      console.error('Syllabus generation error:', err);
    } finally {
      setIsGenerating(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }
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

        {/* URL-Based Generation Section */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>AI-Powered Content Generation</h2>
            <label className={styles.toggleLabel}>
              <input
                type="checkbox"
                checked={useUrlGeneration}
                onChange={(e) => setUseUrlGeneration(e.target.checked)}
                className={styles.toggleCheckbox}
              />
              <span className={styles.toggleSwitch} />
              Generate from external documentation
            </label>
          </div>

          {useUrlGeneration && (
            <div className={styles.urlGenerationContent}>
              <p className={styles.featureDescription}>
                Automatically generate course content by providing URLs to external documentation.
                Works with Salesforce docs, AWS documentation, internal wikis, and more.
              </p>

              {/* URL Input Fields */}
              <div className={styles.formGroup}>
                <label>Documentation URLs</label>
                <div className={styles.urlInputList}>
                  {sourceUrls.map((url, index) => (
                    <div key={index} className={styles.urlInputRow}>
                      <input
                        type="url"
                        value={url}
                        onChange={(e) => handleUrlChange(index, e.target.value)}
                        placeholder="https://docs.example.com/guide"
                        className={urlErrors[index] ? styles.inputError : ''}
                        disabled={isGenerating}
                      />
                      {sourceUrls.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveUrl(index)}
                          className={styles.removeUrlBtn}
                          disabled={isGenerating}
                          aria-label="Remove URL"
                        >
                          ×
                        </button>
                      )}
                      {urlErrors[index] && (
                        <span className={styles.urlError}>{urlErrors[index]}</span>
                      )}
                    </div>
                  ))}
                </div>
                {sourceUrls.length < 10 && (
                  <button
                    type="button"
                    onClick={handleAddUrl}
                    className={styles.addUrlBtn}
                    disabled={isGenerating}
                  >
                    + Add another URL
                  </button>
                )}
                <span className={styles.helpText}>
                  Add up to 10 URLs. Supports HTTP/HTTPS documentation pages.
                </span>
              </div>

              {/* Generation Options */}
              <div className={styles.generationOptions}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={useRagEnhancement}
                    onChange={(e) => setUseRagEnhancement(e.target.checked)}
                    disabled={isGenerating}
                  />
                  Use RAG enhancement for better context
                </label>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={includeCodeExamples}
                    onChange={(e) => setIncludeCodeExamples(e.target.checked)}
                    disabled={isGenerating}
                  />
                  Include code examples from documentation
                </label>
              </div>

              {/* Generate Button */}
              <button
                type="button"
                onClick={handleGenerateSyllabus}
                className={styles.generateBtn}
                disabled={isGenerating || getValidUrls().length === 0 || !formData.title.trim()}
              >
                {isGenerating ? 'Generating...' : 'Generate Syllabus from URLs'}
              </button>

              {/* Generation Progress */}
              {isGenerating && generationProgress && (
                <div className={styles.progressContainer}>
                  <div className={styles.progressHeader}>
                    <span className={styles.progressStep}>{generationProgress.current_step}</span>
                    <span className={styles.progressTime}>
                      {Math.round(generationProgress.elapsed_seconds)}s
                    </span>
                  </div>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{
                        width: `${Math.min(
                          ((generationProgress.urls_fetched + generationProgress.chunks_ingested) /
                            (generationProgress.total_urls * 2 + 10)) *
                            100,
                          95
                        )}%`,
                      }}
                    />
                  </div>
                  <div className={styles.progressDetails}>
                    <span>URLs: {generationProgress.urls_fetched}/{generationProgress.total_urls}</span>
                    {generationProgress.urls_failed > 0 && (
                      <span className={styles.progressWarning}>
                        ({generationProgress.urls_failed} failed)
                      </span>
                    )}
                    <span>Chunks: {generationProgress.chunks_ingested}</span>
                  </div>
                </div>
              )}

              {/* Generated Syllabus Preview */}
              {generatedSyllabus && (
                <div className={styles.syllabusPreview}>
                  <h3>Generated Syllabus Preview</h3>
                  <div className={styles.syllabusContent}>
                    <div className={styles.syllabusHeader}>
                      <strong>{generatedSyllabus.title}</strong>
                      <span className={styles.syllabusLevel}>{generatedSyllabus.level}</span>
                    </div>
                    {generatedSyllabus.description && (
                      <p className={styles.syllabusDescription}>{generatedSyllabus.description}</p>
                    )}
                    {generatedSyllabus.objectives && generatedSyllabus.objectives.length > 0 && (
                      <div className={styles.syllabusObjectives}>
                        <strong>Learning Objectives:</strong>
                        <ul>
                          {generatedSyllabus.objectives.map((obj, i) => (
                            <li key={i}>{obj}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className={styles.syllabusModules}>
                      <strong>Modules ({generatedSyllabus.modules.length}):</strong>
                      <ol>
                        {generatedSyllabus.modules.map((module, i) => (
                          <li key={i}>
                            <strong>{module.title}</strong>
                            {module.description && (
                              <p className={styles.moduleDescription}>{module.description}</p>
                            )}
                          </li>
                        ))}
                      </ol>
                    </div>
                    {generatedSyllabus.external_sources && generatedSyllabus.external_sources.length > 0 && (
                      <div className={styles.syllabusSources}>
                        <strong>Sources:</strong>
                        <ul>
                          {generatedSyllabus.external_sources.map((source, i) => (
                            <li key={i}>
                              <a href={source.url} target="_blank" rel="noopener noreferrer">
                                {source.title || source.url}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
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
