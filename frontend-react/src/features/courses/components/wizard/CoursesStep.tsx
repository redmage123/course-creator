/**
 * CoursesStep - Step 3 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Manage courses within each track. Displayed as accordion per track,
 * with inline forms for adding/editing courses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches tracks, then courses per track via courseService.getCoursesByTrack
 * - Accordion UI for track grouping
 * - Inline create/edit form per track
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '../../../../components/atoms/Button';
import { Spinner } from '../../../../components/atoms/Spinner';
import { trackService, courseService } from '../../../../services';
import type { Track, Course, CreateCourseRequest } from '../../../../services';
import styles from './CoursesStep.module.css';

interface CoursesStepProps {
  programId: string;
  projectId?: string;
  organizationId?: string;
  readOnly?: boolean;
}

interface TrackCourseSectionProps {
  track: Track;
  organizationId?: string;
  readOnly?: boolean;
}

const TrackCourseSection: React.FC<TrackCourseSectionProps> = ({
  track,
  organizationId,
  readOnly = false,
}) => {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);

  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formDifficulty, setFormDifficulty] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [formDuration, setFormDuration] = useState<number | ''>('');
  const [formDurationUnit, setFormDurationUnit] = useState<'hours' | 'days' | 'weeks' | 'months'>('hours');

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses', 'track', track.id],
    queryFn: () => courseService.getCoursesByTrack(track.id),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateCourseRequest) => courseService.createCourse(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses', 'track', track.id] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => courseService.deleteCourse(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses', 'track', track.id] });
    },
  });

  const resetForm = () => {
    setShowForm(false);
    setEditingCourse(null);
    setFormTitle('');
    setFormDescription('');
    setFormDifficulty('beginner');
    setFormDuration('');
    setFormDurationUnit('hours');
  };

  const openEditForm = (course: Course) => {
    setEditingCourse(course);
    setFormTitle(course.title);
    setFormDescription(course.description || '');
    setFormDifficulty(course.difficulty_level);
    setFormDuration(course.estimated_duration || '');
    setFormDurationUnit(course.duration_unit);
    setShowForm(true);
  };

  const handleSubmit = () => {
    if (!formTitle.trim()) return;

    if (editingCourse) {
      courseService
        .updateCourse(editingCourse.id, {
          title: formTitle.trim(),
          description: formDescription.trim(),
          difficulty_level: formDifficulty,
          estimated_duration: formDuration ? Number(formDuration) : undefined,
          duration_unit: formDurationUnit,
        })
        .then(() => {
          queryClient.invalidateQueries({ queryKey: ['courses', 'track', track.id] });
          resetForm();
        });
    } else {
      createMutation.mutate({
        title: formTitle.trim(),
        description: formDescription.trim(),
        difficulty_level: formDifficulty,
        estimated_duration: formDuration ? Number(formDuration) : undefined,
        duration_unit: formDurationUnit,
        track_id: track.id,
        organization_id: organizationId,
      });
    }
  };

  const handleDelete = (courseId: string, courseName: string) => {
    if (window.confirm(`Delete course "${courseName}"?`)) {
      deleteMutation.mutate(courseId);
    }
  };

  return (
    <div className={styles.trackAccordion}>
      <button
        className={styles.trackAccordionHeader}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={styles.trackAccordionTitle}>
          <span className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ''}`}>&#9654;</span>
          {track.name}
          <span className={styles.courseCount}>({courses.length} courses)</span>
        </span>
      </button>

      {isOpen && (
        <div className={styles.trackAccordionBody}>
          {isLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '16px' }}>
              <Spinner size="small" />
            </div>
          ) : (
            <>
              {courses.length === 0 && !showForm && (
                <div className={styles.emptyState}>
                  No courses in this track yet.
                  {!readOnly && (
                    <div style={{ marginTop: '8px' }}>
                      <Button variant="secondary" size="small" onClick={() => { resetForm(); setShowForm(true); }}>
                        + Add Course
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {courses.length > 0 && (
                <div className={styles.courseList}>
                  {courses.map((course) => (
                    <div key={course.id} className={styles.courseItem}>
                      <div className={styles.courseInfo}>
                        <h5 className={styles.courseName}>{course.title}</h5>
                        <div className={styles.courseMeta}>
                          {course.difficulty_level}
                          {course.estimated_duration && ` - ${course.estimated_duration} ${course.duration_unit}`}
                        </div>
                      </div>
                      {!readOnly && (
                        <div className={styles.courseActions}>
                          <Button variant="ghost" size="small" onClick={() => openEditForm(course)}>
                            Edit
                          </Button>
                          <Button
                            variant="danger"
                            size="small"
                            onClick={() => handleDelete(course.id, course.title)}
                          >
                            Delete
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {!readOnly && !showForm && courses.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <Button variant="secondary" size="small" onClick={() => { resetForm(); setShowForm(true); }}>
                    + Add Course
                  </Button>
                </div>
              )}

              {showForm && !readOnly && (
                <div className={styles.inlineForm}>
                  <h5 className={styles.formTitle}>
                    {editingCourse ? 'Edit Course' : 'New Course'}
                  </h5>
                  <div className={styles.formGrid}>
                    <div className={styles.formGroup}>
                      <label htmlFor={`course-title-${track.id}`} className={styles.formLabel}>
                        Course Title <span className={styles.required}>*</span>
                      </label>
                      <input
                        id={`course-title-${track.id}`}
                        type="text"
                        value={formTitle}
                        onChange={(e) => setFormTitle(e.target.value)}
                        className={styles.formInput}
                        placeholder="e.g., Introduction to AWS EC2"
                        autoFocus
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label htmlFor={`course-desc-${track.id}`} className={styles.formLabel}>
                        Description
                      </label>
                      <textarea
                        id={`course-desc-${track.id}`}
                        value={formDescription}
                        onChange={(e) => setFormDescription(e.target.value)}
                        className={styles.formTextarea}
                        placeholder="Brief course description..."
                        rows={2}
                      />
                    </div>

                    <div className={styles.formRow}>
                      <div className={styles.formGroup}>
                        <label htmlFor={`course-diff-${track.id}`} className={styles.formLabel}>Difficulty</label>
                        <select
                          id={`course-diff-${track.id}`}
                          value={formDifficulty}
                          onChange={(e) => setFormDifficulty(e.target.value as typeof formDifficulty)}
                          className={styles.formSelect}
                        >
                          <option value="beginner">Beginner</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>

                      <div className={styles.formGroup}>
                        <label htmlFor={`course-dur-${track.id}`} className={styles.formLabel}>Duration</label>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <input
                            id={`course-dur-${track.id}`}
                            type="number"
                            value={formDuration}
                            onChange={(e) => setFormDuration(e.target.value ? Number(e.target.value) : '')}
                            className={styles.formInput}
                            placeholder="0"
                            min="0"
                            style={{ flex: 1 }}
                          />
                          <select
                            value={formDurationUnit}
                            onChange={(e) => setFormDurationUnit(e.target.value as typeof formDurationUnit)}
                            className={styles.formSelect}
                            style={{ flex: 1 }}
                          >
                            <option value="hours">Hours</option>
                            <option value="days">Days</option>
                            <option value="weeks">Weeks</option>
                            <option value="months">Months</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <div className={styles.formActions}>
                      <Button variant="secondary" size="small" onClick={resetForm}>Cancel</Button>
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleSubmit}
                        loading={createMutation.isPending}
                        disabled={!formTitle.trim() || createMutation.isPending}
                      >
                        {editingCourse ? 'Update' : 'Create'}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export const CoursesStep: React.FC<CoursesStepProps> = ({
  programId,
  projectId,
  organizationId,
  readOnly = false,
}) => {
  const effectiveProjectId = projectId || programId;

  const { data: tracks = [], isLoading } = useQuery({
    queryKey: ['tracks', effectiveProjectId],
    queryFn: () => trackService.getProjectTracks(effectiveProjectId),
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <Spinner size="medium" />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>Courses</h3>
          <p className={styles.subtitle}>
            Add courses to each track. Each course can have its own syllabus generated in the next step.
          </p>
        </div>
      </div>

      {tracks.length === 0 ? (
        <div className={styles.noTracks}>
          <p className={styles.noTracksTitle}>No tracks available</p>
          <p>Go back to Step 2 to create learning tracks before adding courses.</p>
        </div>
      ) : (
        tracks.map((track) => (
          <TrackCourseSection
            key={track.id}
            track={track}
            organizationId={organizationId}
            readOnly={readOnly}
          />
        ))
      )}
    </div>
  );
};

CoursesStep.displayName = 'CoursesStep';
