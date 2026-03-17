/**
 * Bulk Enroll Students Page
 *
 * BUSINESS CONTEXT:
 * Org Admin feature for bulk student enrollment operations.
 * Supports organization-wide enrollments, track enrollments, and CSV uploads.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses enrollment service for bulk operations
 * - Supports course-level and track-level enrollments
 * - Enterprise-scale CSV processing with progress feedback
 * - Organization-scoped student and course lists
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Select } from '../components/atoms/Select';
import { Spinner } from '../components/atoms/Spinner';
import { enrollmentService, BulkEnrollmentResponse } from '../services/enrollmentService';
import { trainingProgramService, TrainingProgram } from '../services/trainingProgramService';
import { useAppSelector } from '../store/hooks';

type EnrollmentTarget = 'course' | 'track';

/**
 * Bulk Enroll Students Page Component
 *
 * WHY THIS APPROACH:
 * - Organization-wide perspective (not limited to single instructor)
 * - Track-level enrollments for streamlined onboarding
 * - Enterprise CSV upload for large-scale operations
 * - Detailed reporting for audit and compliance
 */
export const BulkEnrollStudents: React.FC = () => {
  const navigate = useNavigate();
  const user = useAppSelector(state => state.user.profile);

  // Target selection
  const [target, setTarget] = useState<EnrollmentTarget>('course');

  // Programs and tracks list
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [isLoadingPrograms, setIsLoadingPrograms] = useState(true);

  // Form state
  const [selectedId, setSelectedId] = useState(''); // course_id or track_id
  const [bulkStudentIds, setBulkStudentIds] = useState('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [useCSV, setUseCSV] = useState(false);

  // Operation state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [bulkResult, setBulkResult] = useState<BulkEnrollmentResponse | null>(null);

  /**
   * Load organization's training programs
   */
  useEffect(() => {
    const loadPrograms = async () => {
      if (!user?.organizationId) return;

      try {
        setIsLoadingPrograms(true);
        const response = await trainingProgramService.getTrainingPrograms({
          organization_id: user.organizationId,
          published: true
        });
        setPrograms(response.data);
      } catch (err) {
        console.error('Failed to load training programs:', err);
        setError('Failed to load organization training programs. Please refresh the page.');
      } finally {
        setIsLoadingPrograms(false);
      }
    };

    loadPrograms();
  }, [user?.organizationId]);

  /**
   * Get tracks from programs
   */
  const tracks = Array.from(
    new Map(
      programs
        .filter(p => p.track_id)
        .map(p => [p.track_id, { id: p.track_id!, name: `Track ${p.track_id}` }])
    ).values()
  );

  /**
   * Handle bulk enrollment submission
   */
  const handleBulkEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setBulkResult(null);

    if (!selectedId) {
      setError(`Please select a ${target === 'course' ? 'training program' : 'track'}.`);
      return;
    }

    // For CSV mode
    if (useCSV) {
      if (!csvFile) {
        setError('Please upload a CSV file.');
        return;
      }

      try {
        setIsSubmitting(true);

        // Note: For track enrollment, we'd need a dedicated endpoint
        // For now, using course enrollment as demonstration
        const result = await enrollmentService.bulkEnrollFromCSV(selectedId, csvFile);

        setBulkResult(result);

        if (result.success_count > 0) {
          setSuccess(`Successfully enrolled ${result.success_count} student(s) from CSV!`);
        }

        if (result.failed_count > 0) {
          setError(`${result.failed_count} enrollment(s) failed. See details below.`);
        }

        if (result.failed_count === 0) {
          setCsvFile(null);
          setTimeout(() => navigate('/dashboard/org-admin'), 3000);
        }
      } catch (err: any) {
        console.error('Failed to upload CSV:', err);
        setError(err.response?.data?.message || 'Failed to process CSV file. Please check the format and try again.');
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // For manual ID entry
    if (!bulkStudentIds.trim()) {
      setError('Please enter student IDs.');
      return;
    }

    const studentIdList = bulkStudentIds
      .split(/[,\n]/)
      .map(id => id.trim())
      .filter(id => id.length > 0);

    if (studentIdList.length === 0) {
      setError('No valid student IDs found.');
      return;
    }

    try {
      setIsSubmitting(true);

      let result: BulkEnrollmentResponse;

      if (target === 'course') {
        result = await enrollmentService.bulkEnrollStudents({
          course_id: selectedId,
          student_ids: studentIdList
        });
      } else {
        result = await enrollmentService.bulkEnrollStudentsInTrack({
          track_id: selectedId,
          student_ids: studentIdList
        });
      }

      setBulkResult(result);

      if (result.success_count > 0) {
        setSuccess(`Successfully enrolled ${result.success_count} student(s) in ${target}!`);
      }

      if (result.failed_count > 0) {
        setError(`${result.failed_count} enrollment(s) failed. See details below.`);
      }

      if (result.failed_count === 0) {
        setBulkStudentIds('');
        setTimeout(() => navigate('/dashboard/org-admin'), 3000);
      }
    } catch (err: any) {
      console.error('Failed to bulk enroll students:', err);
      setError(err.response?.data?.message || 'Failed to enroll students. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Download CSV template
   */
  const downloadCSVTemplate = () => {
    const template = 'student_id,student_name,student_email\nstudent123,John Doe,john@example.com\nstudent456,Jane Smith,jane@example.com\nstudent789,Bob Wilson,bob@example.com';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'bulk_enrollment_template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  if (isLoadingPrograms) {
    return (
      <DashboardLayout>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Spinner size="large" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Heading level="h1" gutterBottom={true}>
            Bulk Enroll Students
          </Heading>
          <p style={{ color: '#666', fontSize: '0.95rem', marginBottom: '1rem' }}>
            Enroll multiple students across your organization's training programs or tracks
          </p>
          <Card variant="outlined" padding="medium" style={{ backgroundColor: '#eff6ff' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#1e40af' }}>
              <strong>💡 Tip:</strong> Use track enrollment to enroll students in entire learning paths at once.
              CSV upload supports enrolling hundreds of students in seconds.
            </p>
          </Card>
        </div>

        {/* Target Selection */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
            Enrollment Target
          </Heading>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <Card
              variant={target === 'course' ? 'elevated' : 'outlined'}
              padding="medium"
              style={{
                cursor: 'pointer',
                border: target === 'course' ? '2px solid #3b82f6' : undefined,
                transition: 'all 0.2s'
              }}
              onClick={() => setTarget('course')}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📚</div>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                  Single Training Program
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  Enroll students in one specific course
                </div>
              </div>
            </Card>
            <Card
              variant={target === 'track' ? 'elevated' : 'outlined'}
              padding="medium"
              style={{
                cursor: 'pointer',
                border: target === 'track' ? '2px solid #3b82f6' : undefined,
                transition: 'all 0.2s'
              }}
              onClick={() => setTarget('track')}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🎯</div>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                  Complete Learning Track
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  Enroll students in all courses in a track
                </div>
              </div>
            </Card>
          </div>
        </Card>

        {/* Input Method Selection */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
            Input Method
          </Heading>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <Card
              variant={!useCSV ? 'elevated' : 'outlined'}
              padding="medium"
              style={{
                cursor: 'pointer',
                border: !useCSV ? '2px solid #10b981' : undefined,
                transition: 'all 0.2s'
              }}
              onClick={() => setUseCSV(false)}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>✍️</div>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                  Manual Entry
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  Paste student IDs directly
                </div>
              </div>
            </Card>
            <Card
              variant={useCSV ? 'elevated' : 'outlined'}
              padding="medium"
              style={{
                cursor: 'pointer',
                border: useCSV ? '2px solid #10b981' : undefined,
                transition: 'all 0.2s'
              }}
              onClick={() => setUseCSV(true)}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📤</div>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                  CSV Upload
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  Upload file with student list
                </div>
              </div>
            </Card>
          </div>
        </Card>

        {/* Error/Success Messages */}
        {error && (
          <Card variant="outlined" padding="medium" style={{ marginBottom: '1.5rem', borderColor: '#ef4444', backgroundColor: '#fee2e2' }}>
            <p style={{ color: '#dc2626', margin: 0, fontWeight: 500 }}>{error}</p>
          </Card>
        )}

        {success && (
          <Card variant="outlined" padding="medium" style={{ marginBottom: '1.5rem', borderColor: '#10b981', backgroundColor: '#d1fae5' }}>
            <p style={{ color: '#065f46', margin: 0, fontWeight: 500 }}>{success}</p>
          </Card>
        )}

        {/* Bulk Result Details */}
        {bulkResult && bulkResult.failed_students && bulkResult.failed_students.length > 0 && (
          <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem', borderColor: '#f59e0b' }}>
            <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
              Failed Enrollments ({bulkResult.failed_count})
            </Heading>
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '0.5rem', textAlign: 'left', fontWeight: 600 }}>Student ID</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left', fontWeight: 600 }}>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {bulkResult.failed_students.map((failure, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{failure.student_id}</td>
                      <td style={{ padding: '0.5rem', color: '#dc2626' }}>{failure.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Enrollment Form */}
        <Card variant="outlined" padding="large">
          <form onSubmit={handleBulkEnrollment}>
            {/* Target Selection Dropdown */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="target" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                {target === 'course' ? 'Select Training Program *' : 'Select Learning Track *'}
              </label>
              <Select
                id="target"
                name="target"
                value={selectedId}
                onChange={(value) => setSelectedId(value as string)}
                options={
                  target === 'course'
                    ? [
                        { value: '', label: 'Choose a training program...' },
                        ...programs.map(program => ({
                          value: program.id,
                          label: `${program.title} (${program.difficulty_level})`
                        }))
                      ]
                    : [
                        { value: '', label: 'Choose a learning track...' },
                        ...tracks.map(track => ({
                          value: track.id,
                          label: track.name
                        }))
                      ]
                }
                disabled={isSubmitting}
              />
              {programs.length === 0 && (
                <p style={{ fontSize: '0.875rem', color: '#dc2626', marginTop: '0.5rem' }}>
                  No training programs found for your organization.
                </p>
              )}
              {target === 'track' && tracks.length === 0 && (
                <p style={{ fontSize: '0.875rem', color: '#dc2626', marginTop: '0.5rem' }}>
                  No learning tracks configured yet.
                </p>
              )}
            </div>

            {/* Manual Entry */}
            {!useCSV && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label htmlFor="bulkStudentIds" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                  Student IDs (one per line or comma-separated) *
                </label>
                <textarea
                  id="bulkStudentIds"
                  name="bulkStudentIds"
                  rows={10}
                  placeholder="Enter student IDs, one per line:&#10;student123&#10;student456&#10;student789&#10;...&#10;&#10;Or comma-separated: student123, student456, student789"
                  value={bulkStudentIds}
                  onChange={(e) => setBulkStudentIds(e.target.value)}
                  disabled={isSubmitting}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    fontSize: '0.875rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem',
                    fontFamily: 'monospace',
                    resize: 'vertical'
                  }}
                />
                <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                  💡 Tip: You can paste hundreds of IDs at once for bulk processing.
                </p>
              </div>
            )}

            {/* CSV Upload */}
            {useCSV && (
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <label htmlFor="csvFile" style={{ fontWeight: 500 }}>
                    CSV File *
                  </label>
                  <Button
                    type="button"
                    variant="text"
                    size="small"
                    onClick={downloadCSVTemplate}
                  >
                    📥 Download Template
                  </Button>
                </div>
                <input
                  id="csvFile"
                  name="csvFile"
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                  disabled={isSubmitting}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    fontSize: '0.875rem',
                    border: '2px dashed #d1d5db',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    backgroundColor: '#f9fafb'
                  }}
                />
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', border: '1px solid #bae6fd' }}>
                  <p style={{ margin: '0 0 0.5rem', fontWeight: 500, fontSize: '0.875rem', color: '#0c4a6e' }}>
                    CSV Format Requirements:
                  </p>
                  <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e' }}>
                    <li>Required column: <code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>student_id</code></li>
                    <li>Optional columns: <code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>student_name</code>, <code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>student_email</code></li>
                    <li>Maximum recommended: 1000 students per upload</li>
                  </ul>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
              <Link to="/dashboard/org-admin">
                <Button variant="secondary" disabled={isSubmitting}>
                  Cancel
                </Button>
              </Link>
              <Button
                type="submit"
                variant="primary"
                disabled={
                  isSubmitting ||
                  !selectedId ||
                  (useCSV ? !csvFile : !bulkStudentIds.trim())
                }
              >
                {isSubmitting
                  ? 'Processing...'
                  : useCSV
                  ? 'Upload & Enroll'
                  : `Enroll Students in ${target === 'course' ? 'Course' : 'Track'}`}
              </Button>
            </div>
          </form>
        </Card>

        {/* Statistics Card */}
        {bulkResult && (
          <Card variant="elevated" padding="large" style={{ marginTop: '1.5rem', backgroundColor: '#f0fdf4', border: '1px solid #86efac' }}>
            <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#166534' }}>
              Enrollment Summary
            </Heading>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534' }}>Total Processed</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.75rem', fontWeight: 'bold', color: '#166534' }}>
                  {bulkResult.success_count + bulkResult.failed_count}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534' }}>Successful</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.75rem', fontWeight: 'bold', color: '#16a34a' }}>
                  {bulkResult.success_count}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534' }}>Failed</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.75rem', fontWeight: 'bold', color: '#dc2626' }}>
                  {bulkResult.failed_count}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#166534' }}>Success Rate</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.75rem', fontWeight: 'bold', color: '#16a34a' }}>
                  {Math.round((bulkResult.success_count / (bulkResult.success_count + bulkResult.failed_count)) * 100)}%
                </p>
              </div>
            </div>
          </Card>
        )}
      </main>
    </DashboardLayout>
  );
};
