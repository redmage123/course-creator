/**
 * Screenshot Course Creator Component
 *
 * BUSINESS CONTEXT:
 * Allows instructors to create courses by uploading screenshots of existing
 * educational content (slides, diagrams, documentation). AI automatically
 * extracts content and generates a complete course structure.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Drag-and-drop file upload with validation
 * - Image preview with cropping/adjustment
 * - Real-time analysis progress tracking
 * - Course structure preview and editing
 * - Integration with multi-provider LLM system
 *
 * SUPPORTED PROVIDERS:
 * OpenAI, Anthropic, Deepseek, Qwen, Ollama, Llama, Gemini, Mistral
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  screenshotService,
  type ScreenshotUploadResponse,
  type ScreenshotStatus,
  type ScreenshotAnalysisResult,
  type CourseStructure,
  type LLMProviderConfig,
  type SimilarScreenshot,
} from '../../../services/screenshotService';
import { useAuth } from '../../../hooks/useAuth';
import styles from './ScreenshotCourseCreator.module.css';

interface ScreenshotCourseCreatorProps {
  onCourseCreated?: (courseId: string) => void;
  trackId?: string;
  className?: string;
}

export const ScreenshotCourseCreator: React.FC<ScreenshotCourseCreatorProps> = ({
  onCourseCreated,
  trackId,
  className,
}) => {
  const { user } = useAuth();
  const organizationId = user?.organization_id || '';
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [uploadedScreenshots, setUploadedScreenshots] = useState<ScreenshotUploadResponse[]>([]);
  const [currentScreenshotId, setCurrentScreenshotId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<ScreenshotStatus | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ScreenshotAnalysisResult | null>(null);
  const [similarScreenshots, setSimilarScreenshots] = useState<SimilarScreenshot[]>([]);
  const [llmProviders, setLlmProviders] = useState<LLMProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [step, setStep] = useState<'upload' | 'analyzing' | 'preview' | 'create'>('upload');

  // Load available LLM providers on mount
  useEffect(() => {
    const loadProviders = async () => {
      if (organizationId) {
        try {
          const providers = await screenshotService.getLLMProviders(organizationId);
          setLlmProviders(providers);
          // Set default provider if available
          const defaultProvider = providers.find((p) => p.is_default);
          if (defaultProvider) {
            setSelectedProvider(defaultProvider.provider_name);
          } else if (providers.length > 0) {
            setSelectedProvider(providers[0].provider_name);
          }
        } catch (err) {
          console.error('Failed to load LLM providers:', err);
        }
      }
    };
    loadProviders();
  }, [organizationId]);

  // Handle file selection
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;

    const validFiles: File[] = [];
    const newPreviews: string[] = [];
    const errors: string[] = [];

    Array.from(files).forEach((file) => {
      const validation = screenshotService.validateImageFile(file);
      if (validation.valid) {
        validFiles.push(file);
        // Create preview URL
        const previewUrl = URL.createObjectURL(file);
        newPreviews.push(previewUrl);
      } else {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });

    if (errors.length > 0) {
      setError(errors.join('\n'));
    } else {
      setError(null);
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
    setPreviews((prev) => [...prev, ...newPreviews]);
  }, []);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  // Remove a selected file
  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => {
      // Revoke the URL to prevent memory leaks
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  // Upload screenshots
  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !organizationId) return;

    setLoading(true);
    setError(null);

    try {
      if (selectedFiles.length === 1) {
        const response = await screenshotService.uploadScreenshot(
          selectedFiles[0],
          organizationId
        );
        setUploadedScreenshots([response]);
        setCurrentScreenshotId(response.id);
      } else {
        const response = await screenshotService.uploadScreenshotBatch(
          selectedFiles,
          organizationId
        );
        setUploadedScreenshots(response.screenshots);
        if (response.screenshots.length > 0) {
          setCurrentScreenshotId(response.screenshots[0].id);
        }
      }

      setStep('analyzing');
      await startAnalysis();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload screenshots');
    } finally {
      setLoading(false);
    }
  };

  // Start analysis
  const startAnalysis = async () => {
    if (!currentScreenshotId) return;

    setLoading(true);
    setError(null);

    try {
      // Trigger analysis
      await screenshotService.analyzeScreenshot(currentScreenshotId, selectedProvider || undefined);

      // Poll for completion
      const finalStatus = await screenshotService.pollUntilComplete(
        currentScreenshotId,
        (status) => setAnalysisStatus(status)
      );

      // Get analysis result
      const result = await screenshotService.getAnalysisResult(currentScreenshotId);
      setAnalysisResult(result);

      // Find similar screenshots
      if (result.extracted_text) {
        const similar = await screenshotService.findSimilarScreenshots(
          result.extracted_text,
          organizationId,
          5
        );
        setSimilarScreenshots(similar);
      }

      setStep('preview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setStep('upload');
    } finally {
      setLoading(false);
    }
  };

  // Create course from analysis
  const handleCreateCourse = async () => {
    if (!currentScreenshotId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await screenshotService.generateCourseFromScreenshot({
        screenshot_id: currentScreenshotId,
        organization_id: organizationId,
        track_id: trackId,
        create_course: true,
        llm_provider: selectedProvider || undefined,
      });

      if (response.course_id && onCourseCreated) {
        onCourseCreated(response.course_id);
      }

      setStep('create');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create course');
    } finally {
      setLoading(false);
    }
  };

  // Reset to start over
  const handleReset = () => {
    // Clean up preview URLs
    previews.forEach((url) => URL.revokeObjectURL(url));

    setSelectedFiles([]);
    setPreviews([]);
    setUploadedScreenshots([]);
    setCurrentScreenshotId(null);
    setAnalysisStatus(null);
    setAnalysisResult(null);
    setSimilarScreenshots([]);
    setError(null);
    setStep('upload');
  };

  return (
    <div className={`${styles.container} ${className || ''}`}>
      <div className={styles.header}>
        <h2>Create Course from Screenshots</h2>
        <p className={styles.description}>
          Upload screenshots of existing course content (slides, diagrams, documentation)
          and let AI generate a complete course structure.
        </p>
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <span className={styles.errorIcon}>⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className={styles.dismissBtn}>
            ×
          </button>
        </div>
      )}

      {/* Step 1: Upload */}
      {step === 'upload' && (
        <div className={styles.uploadSection}>
          {/* LLM Provider Selection */}
          {llmProviders.length > 0 && (
            <div className={styles.providerSelect}>
              <label htmlFor="llm-provider">AI Provider:</label>
              <select
                id="llm-provider"
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                disabled={loading}
              >
                {llmProviders.map((provider) => (
                  <option key={provider.id} value={provider.provider_name}>
                    {provider.provider_name} ({provider.model_name})
                    {provider.is_default ? ' - Default' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Drop Zone */}
          <div
            className={`${styles.dropZone} ${isDragOver ? styles.dragOver : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => handleFileSelect(e.target.files)}
              accept="image/png,image/jpeg,image/webp"
              multiple
              hidden
            />
            <div className={styles.dropZoneContent}>
              <span className={styles.uploadIcon}>📸</span>
              <p className={styles.dropZoneText}>
                Drag & drop screenshots here or <span className={styles.browseLink}>browse</span>
              </p>
              <p className={styles.dropZoneHint}>
                Supports PNG, JPEG, WEBP (max 10MB each)
              </p>
            </div>
          </div>

          {/* Preview Grid */}
          {previews.length > 0 && (
            <div className={styles.previewGrid}>
              {previews.map((preview, index) => (
                <div key={index} className={styles.previewItem}>
                  <img src={preview} alt={`Preview ${index + 1}`} />
                  <button
                    className={styles.removeBtn}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFile(index);
                    }}
                    aria-label="Remove image"
                  >
                    ×
                  </button>
                  <span className={styles.fileName}>{selectedFiles[index]?.name}</span>
                </div>
              ))}
            </div>
          )}

          {/* Upload Button */}
          {selectedFiles.length > 0 && (
            <button
              className={styles.uploadBtn}
              onClick={handleUpload}
              disabled={loading}
            >
              {loading ? 'Uploading...' : `Analyze ${selectedFiles.length} Screenshot${selectedFiles.length > 1 ? 's' : ''}`}
            </button>
          )}
        </div>
      )}

      {/* Step 2: Analyzing */}
      {step === 'analyzing' && (
        <div className={styles.analyzingSection}>
          <div className={styles.spinner} />
          <h3>Analyzing Screenshots...</h3>
          {analysisStatus && (
            <div className={styles.progressInfo}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${analysisStatus.progress_percent}%` }}
                />
              </div>
              <p className={styles.progressStep}>{analysisStatus.current_step}</p>
              <p className={styles.progressPercent}>{analysisStatus.progress_percent}%</p>
            </div>
          )}
          <p className={styles.analyzingHint}>
            Our AI is extracting content and building your course structure...
          </p>
        </div>
      )}

      {/* Step 3: Preview */}
      {step === 'preview' && analysisResult && (
        <div className={styles.previewSection}>
          <div className={styles.analysisInfo}>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Content Type:</span>
              <span className={styles.infoValue}>{analysisResult.content_type}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Subject Area:</span>
              <span className={styles.infoValue}>{analysisResult.subject_area || 'General'}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Difficulty:</span>
              <span className={styles.infoValue}>{analysisResult.difficulty_level}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Confidence:</span>
              <span className={styles.infoValue}>
                {Math.round(analysisResult.confidence_score * 100)}%
              </span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Provider:</span>
              <span className={styles.infoValue}>{analysisResult.llm_provider}</span>
            </div>
          </div>

          {/* Course Structure Preview */}
          <div className={styles.courseStructure}>
            <h3>{analysisResult.course_structure.title}</h3>
            <p className={styles.courseDescription}>
              {analysisResult.course_structure.description}
            </p>

            {/* Learning Objectives */}
            {analysisResult.course_structure.learning_objectives.length > 0 && (
              <div className={styles.objectives}>
                <h4>Learning Objectives</h4>
                <ul>
                  {analysisResult.course_structure.learning_objectives.map((obj, i) => (
                    <li key={i}>{obj}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Modules */}
            <div className={styles.modules}>
              <h4>Modules ({analysisResult.course_structure.modules.length})</h4>
              {analysisResult.course_structure.modules.map((module, mi) => (
                <div key={mi} className={styles.module}>
                  <h5>
                    {mi + 1}. {module.title}
                  </h5>
                  <p>{module.description}</p>
                  <ul className={styles.lessons}>
                    {module.lessons.map((lesson, li) => (
                      <li key={li}>{lesson.title}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {/* Similar Courses */}
          {similarScreenshots.length > 0 && (
            <div className={styles.similarCourses}>
              <h4>Similar Existing Courses</h4>
              <p className={styles.similarHint}>
                These courses have similar content. Consider reviewing before creating a new one.
              </p>
              <ul>
                {similarScreenshots.map((similar) => (
                  <li key={similar.screenshot_id}>
                    <span className={styles.similarTitle}>
                      {similar.course_title || 'Untitled Course'}
                    </span>
                    <span className={styles.similarScore}>
                      {Math.round(similar.similarity_score * 100)}% match
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className={styles.actions}>
            <button
              className={styles.secondaryBtn}
              onClick={handleReset}
              disabled={loading}
            >
              Start Over
            </button>
            <button
              className={styles.primaryBtn}
              onClick={handleCreateCourse}
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Course'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Success */}
      {step === 'create' && (
        <div className={styles.successSection}>
          <span className={styles.successIcon}>✅</span>
          <h3>Course Created Successfully!</h3>
          <p>Your course has been created from the uploaded screenshots.</p>
          <button className={styles.primaryBtn} onClick={handleReset}>
            Create Another Course
          </button>
        </div>
      )}
    </div>
  );
};

export default ScreenshotCourseCreator;
