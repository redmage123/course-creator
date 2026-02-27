/**
 * ReviewPublishStep - Step 6 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Final step showing a complete summary of the program, tracks, courses,
 * and enrollment status. Includes a validation checklist and publish action.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches program, tracks, courses data for summary
 * - Validation checklist (has tracks, has courses, has syllabi)
 * - Publish action via trainingProgramService.publishTrainingProgram
 * - Shows publish status
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '../../../../components/atoms/Button';
import { Spinner } from '../../../../components/atoms/Spinner';
import { trainingProgramService, trackService, courseService } from '../../../../services';
import type { TrainingProgram, Track, Course } from '../../../../services';
import styles from './ReviewPublishStep.module.css';

interface ReviewPublishStepProps {
  programId: string;
  projectId?: string;
  readOnly?: boolean;
}

export const ReviewPublishStep: React.FC<ReviewPublishStepProps> = ({
  programId,
  projectId,
  readOnly = false,
}) => {
  const queryClient = useQueryClient();
  const effectiveProjectId = projectId || programId;

  const { data: program, isLoading: loadingProgram } = useQuery({
    queryKey: ['trainingProgram', programId],
    queryFn: () => trainingProgramService.getTrainingProgramById(programId),
  });

  const { data: tracks = [], isLoading: loadingTracks } = useQuery({
    queryKey: ['tracks', effectiveProjectId],
    queryFn: () => trackService.getProjectTracks(effectiveProjectId),
  });

  const { data: allCourses = [], isLoading: loadingCourses } = useQuery({
    queryKey: ['courses', 'allTracks', effectiveProjectId],
    queryFn: async () => {
      if (tracks.length === 0) return [];
      const coursePromises = tracks.map((t) => courseService.getCoursesByTrack(t.id));
      const results = await Promise.all(coursePromises);
      return results.flat();
    },
    enabled: tracks.length > 0,
  });

  const publishMutation = useMutation({
    mutationFn: () => trainingProgramService.publishTrainingProgram(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingProgram', programId] });
      queryClient.invalidateQueries({ queryKey: ['trainingPrograms'] });
    },
  });

  const isLoading = loadingProgram || loadingTracks || loadingCourses;

  if (isLoading || !program) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <Spinner size="medium" />
      </div>
    );
  }

  const hasTracks = tracks.length > 0;
  const hasCourses = allCourses.length > 0;
  const totalEnrollments = tracks.reduce((sum, t) => sum + (t.enrollment_count || 0), 0);
  const formatDifficulty = (level?: string) => level ? level.charAt(0).toUpperCase() + level.slice(1) : 'Not set';

  const coursesPerTrack: Record<string, Course[]> = {};
  tracks.forEach((t) => {
    coursesPerTrack[t.id] = allCourses.filter((c) => c.track_id === t.id);
  });

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Review & Publish</h3>
        <p className={styles.subtitle}>
          Review your program setup before publishing.
        </p>
      </div>

      {/* Program Overview */}
      <div className={styles.summaryCard}>
        <div className={styles.summaryCardHeader}>
          <h4 className={styles.summaryCardTitle}>Program Overview</h4>
          <span className={`${styles.statusBadge} ${program.published ? styles.statusPublished : styles.statusDraft}`}>
            {program.published ? 'Published' : 'Draft'}
          </span>
        </div>
        <div className={styles.summaryCardBody}>
          <div className={styles.metadataRow}>
            <span className={styles.metadataLabel}>Title</span>
            <span className={styles.metadataValue}>{program.title}</span>
          </div>
          {program.category && (
            <div className={styles.metadataRow}>
              <span className={styles.metadataLabel}>Category</span>
              <span className={styles.metadataValue}>{program.category}</span>
            </div>
          )}
          <div className={styles.metadataRow}>
            <span className={styles.metadataLabel}>Difficulty</span>
            <span className={styles.metadataValue}>{formatDifficulty(program.difficulty_level)}</span>
          </div>
          {program.estimated_duration && (
            <div className={styles.metadataRow}>
              <span className={styles.metadataLabel}>Duration</span>
              <span className={styles.metadataValue}>
                {program.estimated_duration} {program.duration_unit}
              </span>
            </div>
          )}
          {program.tags && program.tags.length > 0 && (
            <div className={styles.metadataRow}>
              <span className={styles.metadataLabel}>Tags</span>
              <div className={styles.tagsDisplay}>
                {program.tags.map((tag) => (
                  <span key={tag} className={styles.tag}>{tag}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tracks & Courses Summary */}
      <div className={styles.summaryCard}>
        <div className={styles.summaryCardHeader}>
          <h4 className={styles.summaryCardTitle}>
            Tracks & Courses ({tracks.length} tracks, {allCourses.length} courses)
          </h4>
        </div>
        <div className={styles.summaryCardBody}>
          {tracks.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>No tracks added.</p>
          ) : (
            tracks.map((track) => (
              <div key={track.id} className={styles.trackSummary}>
                <h5 className={styles.trackSummaryName}>
                  {track.name}
                  <span style={{ fontWeight: 400, color: '#64748b' }}>
                    {' '}({track.enrollment_count || 0} enrolled)
                  </span>
                </h5>
                {(coursesPerTrack[track.id] || []).length > 0 ? (
                  <ul className={styles.courseListCompact}>
                    {(coursesPerTrack[track.id] || []).map((course) => (
                      <li key={course.id}>{course.title}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: '#64748b', fontSize: '13px', margin: '2px 0 0 20px' }}>
                    No courses
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Validation Checklist */}
      <div className={styles.summaryCard}>
        <div className={styles.summaryCardHeader}>
          <h4 className={styles.summaryCardTitle}>Readiness Checklist</h4>
        </div>
        <div className={styles.summaryCardBody}>
          <div className={styles.checklist}>
            <div className={`${styles.checkItem} ${hasTracks ? styles.checkItemPass : styles.checkItemWarn}`}>
              <span className={styles.checkIcon}>{hasTracks ? '\u2705' : '\u26A0\uFE0F'}</span>
              {hasTracks
                ? `${tracks.length} learning track${tracks.length > 1 ? 's' : ''} configured`
                : 'No learning tracks added'}
            </div>
            <div className={`${styles.checkItem} ${hasCourses ? styles.checkItemPass : styles.checkItemWarn}`}>
              <span className={styles.checkIcon}>{hasCourses ? '\u2705' : '\u26A0\uFE0F'}</span>
              {hasCourses
                ? `${allCourses.length} course${allCourses.length > 1 ? 's' : ''} created`
                : 'No courses added to tracks'}
            </div>
            <div className={`${styles.checkItem} ${totalEnrollments > 0 ? styles.checkItemPass : styles.checkItemWarn}`}>
              <span className={styles.checkIcon}>{totalEnrollments > 0 ? '\u2705' : '\u26A0\uFE0F'}</span>
              {totalEnrollments > 0
                ? `${totalEnrollments} student${totalEnrollments > 1 ? 's' : ''} enrolled`
                : 'No students enrolled yet (you can enroll later)'}
            </div>
            <div className={`${styles.checkItem} ${program.title ? styles.checkItemPass : styles.checkItemFail}`}>
              <span className={styles.checkIcon}>{program.title ? '\u2705' : '\u274C'}</span>
              Program title and metadata configured
            </div>
          </div>
        </div>
      </div>

      {/* Publish Action */}
      {!readOnly && (
        <div className={styles.publishSection}>
          <h4 className={styles.publishTitle}>
            {program.published ? 'Program is Published' : 'Ready to Publish?'}
          </h4>
          <p className={styles.publishDescription}>
            {program.published
              ? 'This program is live and visible to enrolled students.'
              : 'Publishing will make this program available to enrolled students. You can unpublish at any time.'}
          </p>
          <div className={styles.publishActions}>
            {!program.published ? (
              <Button
                variant="primary"
                onClick={() => publishMutation.mutate()}
                loading={publishMutation.isPending}
                disabled={publishMutation.isPending}
              >
                Publish Program
              </Button>
            ) : (
              <Button variant="secondary" disabled>
                Already Published
              </Button>
            )}
          </div>
          {publishMutation.isError && (
            <p style={{ color: '#dc2626', fontSize: '14px', marginTop: '12px' }}>
              {(publishMutation.error as Error)?.message || 'Failed to publish. Please try again.'}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

ReviewPublishStep.displayName = 'ReviewPublishStep';
