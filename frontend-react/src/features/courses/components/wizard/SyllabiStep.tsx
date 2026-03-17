/**
 * SyllabiStep - Step 4 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Generate per-course syllabi using AI. Each course within each track gets
 * its own syllabus. Supports both standard generation (from title/description)
 * and URL-based generation from external documentation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches tracks then courses per track
 * - Uses syllabusService.generateSyllabus() per course
 * - Shows progress tracking for URL-based generation
 * - Displays generated syllabus modules as preview
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '../../../../components/atoms/Button';
import { Spinner } from '../../../../components/atoms/Spinner';
import { trackService, courseService, syllabusService } from '../../../../services';
import type { Course, SyllabusData, GenerationProgress } from '../../../../services';
import styles from './SyllabiStep.module.css';

interface SyllabiStepProps {
  programId: string;
  projectId?: string;
  readOnly?: boolean;
}

interface CourseSyllabusState {
  status: 'pending' | 'generating' | 'generated' | 'error';
  syllabus?: SyllabusData;
  requestId?: string;
  progress?: GenerationProgress;
  error?: string;
}

interface CourseSyllabusCardProps {
  course: Course;
  readOnly?: boolean;
}

const CourseSyllabusCard: React.FC<CourseSyllabusCardProps> = ({ course, readOnly }) => {
  const [state, setState] = useState<CourseSyllabusState>({ status: 'pending' });
  const [sourceUrl, setSourceUrl] = useState('');
  const [showForm, setShowForm] = useState(false);

  const handleGenerate = useCallback(async () => {
    setState({ status: 'generating' });

    try {
      const response = await syllabusService.generateSyllabus({
        title: course.title,
        description: course.description,
        level: course.difficulty_level,
        source_url: sourceUrl.trim() || undefined,
      });

      if (response.success && response.syllabus) {
        setState({ status: 'generated', syllabus: response.syllabus });
      } else {
        setState({ status: 'error', error: response.message || 'Generation failed' });
      }
    } catch (err) {
      setState({
        status: 'error',
        error: err instanceof Error ? err.message : 'Generation failed',
      });
    }
  }, [course, sourceUrl]);

  const getStatusBadgeClass = () => {
    switch (state.status) {
      case 'generated': return styles.statusGenerated;
      case 'generating': return styles.statusGenerating;
      case 'error': return styles.statusError;
      default: return styles.statusPending;
    }
  };

  const getStatusLabel = () => {
    switch (state.status) {
      case 'generated': return 'Generated';
      case 'generating': return 'Generating...';
      case 'error': return 'Error';
      default: return 'Not generated';
    }
  };

  return (
    <div className={styles.courseCard}>
      <div className={styles.courseCardHeader}>
        <h5 className={styles.courseName}>{course.title}</h5>
        <span className={`${styles.syllabusStatus} ${getStatusBadgeClass()}`}>
          {getStatusLabel()}
        </span>
      </div>

      {state.status === 'generating' && (
        <div className={styles.generateForm}>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: '50%' }} />
          </div>
          <p className={styles.progressText}>
            Generating syllabus for "{course.title}"...
          </p>
        </div>
      )}

      {state.status === 'error' && (
        <div className={styles.generateForm}>
          <p style={{ color: '#dc2626', fontSize: '13px', margin: 0 }}>
            {state.error}
          </p>
          {!readOnly && (
            <Button variant="secondary" size="small" onClick={() => setState({ status: 'pending' })}>
              Try Again
            </Button>
          )}
        </div>
      )}

      {state.status === 'pending' && !readOnly && (
        <>
          {!showForm ? (
            <div style={{ marginTop: '12px' }}>
              <Button variant="primary" size="small" onClick={() => setShowForm(true)}>
                Generate Syllabus
              </Button>
            </div>
          ) : (
            <div className={styles.generateForm}>
              <div className={styles.urlInputGroup}>
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="Optional: documentation URL (e.g., https://docs.aws.amazon.com/...)"
                />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button variant="secondary" size="small" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="small" onClick={handleGenerate}>
                  Generate
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {state.status === 'generated' && state.syllabus && (
        <div className={styles.syllabusPreview}>
          <h5>Syllabus: {state.syllabus.modules.length} modules</h5>
          <ul className={styles.moduleList}>
            {state.syllabus.modules.slice(0, 8).map((mod) => (
              <li key={mod.module_number} className={styles.moduleItem}>
                <span className={styles.moduleNumber}>Module {mod.module_number}:</span>
                {mod.title}
              </li>
            ))}
            {state.syllabus.modules.length > 8 && (
              <li className={styles.moduleItem} style={{ color: '#64748b' }}>
                ...and {state.syllabus.modules.length - 8} more modules
              </li>
            )}
          </ul>
          {!readOnly && (
            <div style={{ marginTop: '8px' }}>
              <Button
                variant="ghost"
                size="small"
                onClick={() => setState({ status: 'pending' })}
              >
                Regenerate
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const SyllabiStep: React.FC<SyllabiStepProps> = ({
  programId,
  projectId,
  readOnly = false,
}) => {
  const effectiveProjectId = projectId || programId;

  const { data: tracks = [], isLoading: loadingTracks, isError: tracksError } = useQuery({
    queryKey: ['tracks', effectiveProjectId],
    queryFn: () => trackService.getProjectTracks(effectiveProjectId),
    retry: 1,
  });

  if (loadingTracks) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <Spinner size="medium" />
      </div>
    );
  }

  if (tracksError || tracks.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p className={styles.emptyTitle}>No tracks or courses available yet</p>
        <p>Add tracks (Step 2) and courses (Step 3) before generating syllabi.</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>Course Syllabi</h3>
          <p className={styles.subtitle}>
            Generate AI-powered syllabi for each course. Optionally provide documentation URLs for richer content.
          </p>
        </div>
      </div>

      {tracks.map((track) => (
        <TrackSyllabiSection
          key={track.id}
          track={track}
          readOnly={readOnly}
        />
      ))}
    </div>
  );
};

const TrackSyllabiSection: React.FC<{ track: { id: string; name: string }; readOnly?: boolean }> = ({
  track,
  readOnly,
}) => {
  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses', 'track', track.id],
    queryFn: () => courseService.getCoursesByTrack(track.id),
  });

  if (isLoading) {
    return (
      <div className={styles.trackSection}>
        <h4 className={styles.trackName}>{track.name}</h4>
        <Spinner size="small" />
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div className={styles.trackSection}>
        <h4 className={styles.trackName}>{track.name}</h4>
        <p style={{ fontSize: '14px', color: '#64748b' }}>No courses in this track.</p>
      </div>
    );
  }

  return (
    <div className={styles.trackSection}>
      <h4 className={styles.trackName}>{track.name}</h4>
      <div className={styles.courseList}>
        {courses.map((course) => (
          <CourseSyllabusCard key={course.id} course={course} readOnly={readOnly} />
        ))}
      </div>
    </div>
  );
};

SyllabiStep.displayName = 'SyllabiStep';
