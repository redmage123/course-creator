/**
 * EnrollmentStep - Step 5 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Bulk enroll students into tracks. In the B2B model, trainers and admins
 * assign students to tracks (students don't self-enroll).
 * Each track can have students enrolled independently.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches tracks for the program
 * - Textarea for pasting student emails (one per line)
 * - Uses trackService.bulkEnrollStudents() per track
 * - Shows enrollment results (success/failure)
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Button } from '../../../../components/atoms/Button';
import { Spinner } from '../../../../components/atoms/Spinner';
import { trackService } from '../../../../services';
import type { Track, TrackEnrollmentResponse } from '../../../../services';
import styles from './EnrollmentStep.module.css';

interface EnrollmentStepProps {
  programId: string;
  projectId?: string;
  readOnly?: boolean;
}

interface TrackEnrollmentSectionProps {
  track: Track;
  readOnly?: boolean;
}

const TrackEnrollmentSection: React.FC<TrackEnrollmentSectionProps> = ({ track, readOnly }) => {
  const [emails, setEmails] = useState('');
  const [result, setResult] = useState<TrackEnrollmentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: enrollmentData, isLoading: loadingEnrollments } = useQuery({
    queryKey: ['trackEnrollments', track.id],
    queryFn: () => trackService.getTrackEnrollments(track.id),
  });

  const enrollMutation = useMutation({
    mutationFn: (studentEmails: string[]) =>
      trackService.bulkEnrollStudents(track.id, {
        student_emails: studentEmails,
        auto_approve: true,
      }),
    onSuccess: (response) => {
      setResult(response);
      setError(null);
      setEmails('');
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Enrollment failed');
      setResult(null);
    },
  });

  const handleEnroll = () => {
    const emailList = emails
      .split('\n')
      .map((e) => e.trim())
      .filter((e) => e.length > 0 && e.includes('@'));

    if (emailList.length === 0) return;
    enrollMutation.mutate(emailList);
  };

  const currentEnrollments = enrollmentData?.enrollments || [];

  return (
    <div className={styles.trackSection}>
      <div className={styles.trackHeader}>
        <h4 className={styles.trackName}>
          {track.name}
          <span className={styles.enrollCount}> ({track.enrollment_count} enrolled)</span>
        </h4>
      </div>

      <div className={styles.trackBody}>
        {!readOnly && (
          <div className={styles.enrollForm}>
            <label className={styles.formLabel}>
              Enter student emails (one per line)
            </label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              className={styles.emailTextarea}
              placeholder="student1@company.com&#10;student2@company.com&#10;student3@company.com"
              rows={4}
            />
            <span className={styles.helperText}>
              Paste or type email addresses, one per line. Students will be enrolled in all courses within this track.
            </span>
            <div className={styles.enrollActions}>
              <Button
                variant="primary"
                size="small"
                onClick={handleEnroll}
                loading={enrollMutation.isPending}
                disabled={!emails.trim() || enrollMutation.isPending}
              >
                Enroll Students
              </Button>
            </div>
          </div>
        )}

        {result && (
          <div className={`${styles.resultCard} ${styles.resultSuccess}`}>
            <strong>{result.total_enrolled} students enrolled</strong>
            {result.failed_enrollments.length > 0 && (
              <ul className={styles.resultList}>
                {result.failed_enrollments.map((fail, i) => (
                  <li key={i} style={{ color: '#991b1b' }}>
                    {fail.email}: {fail.reason}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {error && (
          <div className={`${styles.resultCard} ${styles.resultError}`}>
            {error}
          </div>
        )}

        {currentEnrollments.length > 0 && (
          <div className={styles.enrollmentList}>
            <h5 className={styles.enrollmentListTitle}>
              Current Enrollments ({currentEnrollments.length})
            </h5>
            {loadingEnrollments ? (
              <Spinner size="small" />
            ) : (
              currentEnrollments.slice(0, 20).map((enrollment: { student_email?: string; student_id: string; status: string }, idx: number) => (
                <div key={idx} className={styles.enrolledStudent}>
                  <span>{enrollment.student_email || enrollment.student_id}</span>
                  <span style={{ color: '#64748b', fontSize: '12px' }}>{enrollment.status}</span>
                </div>
              ))
            )}
            {currentEnrollments.length > 20 && (
              <p style={{ fontSize: '13px', color: '#64748b', marginTop: '8px' }}>
                ...and {currentEnrollments.length - 20} more
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export const EnrollmentStep: React.FC<EnrollmentStepProps> = ({
  programId,
  projectId,
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

  if (tracks.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p className={styles.emptyTitle}>No tracks available</p>
        <p>Create tracks and courses in previous steps before enrolling students.</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>Student Enrollment</h3>
          <p className={styles.subtitle}>
            Enroll students in each track. Students will be enrolled in all courses within the track.
          </p>
        </div>
      </div>

      {tracks.map((track) => (
        <TrackEnrollmentSection key={track.id} track={track} readOnly={readOnly} />
      ))}
    </div>
  );
};

EnrollmentStep.displayName = 'EnrollmentStep';
