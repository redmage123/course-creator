/**
 * Manage Students Page
 *
 * BUSINESS CONTEXT:
 * Instructor feature for managing students across all training programs.
 * Instructors can view student enrollments, track progress, and manage assignments.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses enrollment service to fetch and manage student data
 * - Displays enrollments with filtering and search capabilities
 * - Provides quick actions for common instructor tasks
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Select } from '../components/atoms/Select';
import { Spinner } from '../components/atoms/Spinner';
import { enrollmentService, Enrollment, EnrollmentStatus } from '../services/enrollmentService';
import { useAppSelector } from '../store/hooks';

/**
 * Manage Students Page Component
 *
 * WHY THIS APPROACH:
 * - Centralized view of all student enrollments for instructor
 * - Quick filters for status, progress, and search
 * - Direct actions for enrollment management
 * - Responsive table design for various screen sizes
 */
export const ManageStudents: React.FC = () => {
  const user = useAppSelector(state => state.user.profile);

  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [filteredEnrollments, setFilteredEnrollments] = useState<Enrollment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<EnrollmentStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'progress' | 'date'>('name');

  /**
   * Load all enrollments for this instructor
   */
  useEffect(() => {
    const loadEnrollments = async () => {
      if (!user?.id) return;

      try {
        setIsLoading(true);
        setError(null);

        // Get enrollment summary for instructor
        const summary = await enrollmentService.getInstructorEnrollmentSummary(user.id);

        // Transform summary into enrollment list format
        // Note: In production, you'd have a dedicated API endpoint that returns full enrollment details
        const enrollmentData: Enrollment[] = [];
        for (const studentSummary of summary) {
          const studentEnrollments = await enrollmentService.getStudentEnrollments(studentSummary.student_id);
          enrollmentData.push(...studentEnrollments);
        }

        setEnrollments(enrollmentData);
        setFilteredEnrollments(enrollmentData);
      } catch (err) {
        console.error('Failed to load enrollments:', err);
        setError('Failed to load student enrollments. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadEnrollments();
  }, [user?.id]);

  /**
   * Apply filters and search
   */
  useEffect(() => {
    let filtered = [...enrollments];

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(e => e.status === statusFilter);
    }

    // Apply search query (student name, email, or course title)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(e =>
        e.student_name?.toLowerCase().includes(query) ||
        e.student_email?.toLowerCase().includes(query) ||
        e.course_title?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.student_name || '').localeCompare(b.student_name || '');
        case 'progress':
          return b.progress_percentage - a.progress_percentage;
        case 'date':
          return new Date(b.enrollment_date).getTime() - new Date(a.enrollment_date).getTime();
        default:
          return 0;
      }
    });

    setFilteredEnrollments(filtered);
  }, [enrollments, searchQuery, statusFilter, sortBy]);

  /**
   * Handle enrollment status update
   */
  const handleStatusUpdate = async (enrollmentId: string, newStatus: EnrollmentStatus) => {
    try {
      await enrollmentService.updateEnrollmentStatus(enrollmentId, newStatus);

      // Update local state
      setEnrollments(prev =>
        prev.map(e => e.id === enrollmentId ? { ...e, status: newStatus } : e)
      );
    } catch (err) {
      console.error('Failed to update enrollment status:', err);
      alert('Failed to update enrollment status. Please try again.');
    }
  };

  /**
   * Handle unenroll student
   */
  const handleUnenroll = async (enrollmentId: string, studentName: string) => {
    if (!confirm(`Are you sure you want to unenroll ${studentName}?`)) {
      return;
    }

    try {
      await enrollmentService.unenrollStudent(enrollmentId);

      // Remove from local state
      setEnrollments(prev => prev.filter(e => e.id !== enrollmentId));
    } catch (err) {
      console.error('Failed to unenroll student:', err);
      alert('Failed to unenroll student. Please try again.');
    }
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  /**
   * Get status badge color
   */
  const getStatusColor = (status: EnrollmentStatus) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'completed': return '#3b82f6';
      case 'dropped': return '#ef4444';
      case 'pending': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  if (isLoading) {
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
      <main style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Manage Students
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              View and manage student enrollments across all your training programs
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/instructor/students/enroll">
              <Button variant="primary">
                Enroll Students
              </Button>
            </Link>
            <Link to="/dashboard/instructor">
              <Button variant="secondary">
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card variant="outlined" padding="medium" style={{ marginBottom: '1.5rem', borderColor: '#ef4444', backgroundColor: '#fee2e2' }}>
            <p style={{ color: '#dc2626', margin: 0 }}>{error}</p>
          </Card>
        )}

        {/* Filters */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div>
              <Input
                id="search"
                name="search"
                type="text"
                placeholder="Search by name, email, or course..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <Select
                id="status"
                name="status"
                value={statusFilter}
                onChange={(value) => setStatusFilter(value as EnrollmentStatus | 'all')}
                options={[
                  { value: 'all', label: 'All Statuses' },
                  { value: 'active', label: 'Active' },
                  { value: 'completed', label: 'Completed' },
                  { value: 'pending', label: 'Pending' },
                  { value: 'dropped', label: 'Dropped' }
                ]}
              />
            </div>
            <div>
              <Select
                id="sort"
                name="sort"
                value={sortBy}
                onChange={(value) => setSortBy(value as 'name' | 'progress' | 'date')}
                options={[
                  { value: 'name', label: 'Sort by Name' },
                  { value: 'progress', label: 'Sort by Progress' },
                  { value: 'date', label: 'Sort by Date' }
                ]}
              />
            </div>
          </div>
        </Card>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Enrollments</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
              {enrollments.length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Active Students</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {enrollments.filter(e => e.status === 'active').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Completed</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {enrollments.filter(e => e.status === 'completed').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Average Progress</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {enrollments.length > 0
                ? Math.round(enrollments.reduce((sum, e) => sum + e.progress_percentage, 0) / enrollments.length)
                : 0}%
            </p>
          </Card>
        </div>

        {/* Enrollments Table */}
        <Card variant="outlined" padding="none">
          {filteredEnrollments.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
                {searchQuery || statusFilter !== 'all'
                  ? 'No enrollments match your filters'
                  : 'No student enrollments yet'}
              </p>
              <Link to="/instructor/students/enroll">
                <Button variant="primary">
                  Enroll Your First Students
                </Button>
              </Link>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Student</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Course</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Progress</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Status</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Enrolled</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEnrollments.map((enrollment) => (
                    <tr key={enrollment.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {enrollment.student_name || 'Unknown Student'}
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {enrollment.student_email}
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <Link to={`/courses/${enrollment.course_id}`} style={{ color: '#3b82f6', textDecoration: 'none' }}>
                          {enrollment.course_title || 'Unknown Course'}
                        </Link>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{
                            flex: 1,
                            height: '8px',
                            backgroundColor: '#e5e7eb',
                            borderRadius: '4px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              height: '100%',
                              width: `${enrollment.progress_percentage}%`,
                              backgroundColor: '#3b82f6',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                          <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
                            {enrollment.progress_percentage}%
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          backgroundColor: `${getStatusColor(enrollment.status)}20`,
                          color: getStatusColor(enrollment.status)
                        }}>
                          {enrollment.status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {formatDate(enrollment.enrollment_date)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <Link to={`/instructor/students/${enrollment.student_id}/analytics`}>
                            <Button variant="secondary" size="small">
                              View
                            </Button>
                          </Link>
                          <select
                            value={enrollment.status}
                            onChange={(e) => handleStatusUpdate(enrollment.id, e.target.value as EnrollmentStatus)}
                            style={{
                              padding: '0.375rem 0.5rem',
                              fontSize: '0.875rem',
                              borderRadius: '0.375rem',
                              border: '1px solid #d1d5db',
                              backgroundColor: 'white',
                              cursor: 'pointer'
                            }}
                          >
                            <option value="active">Active</option>
                            <option value="completed">Completed</option>
                            <option value="pending">Pending</option>
                            <option value="dropped">Dropped</option>
                          </select>
                          <Button
                            variant="danger"
                            size="small"
                            onClick={() => handleUnenroll(enrollment.id, enrollment.student_name || 'this student')}
                          >
                            Unenroll
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </main>
    </DashboardLayout>
  );
};
