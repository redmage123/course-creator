/**
 * Enroll Students Page
 *
 * BUSINESS CONTEXT:
 * Instructor feature for enrolling students in training programs.
 * Provides search interface to find and select students for enrollment.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Student search with real-time results
 * - Multi-select with checkboxes
 * - Real-time validation and error handling
 * - Success notifications and navigation
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Checkbox } from '../components/atoms/Checkbox';
import { Spinner } from '../components/atoms/Spinner';
import { enrollmentService } from '../services/enrollmentService';
import { trainingProgramService, TrainingProgram } from '../services/trainingProgramService';
import { useAppSelector } from '../store/hooks';

interface Student {
  id: string;
  name: string;
  email: string;
}

/**
 * Enroll Students Page Component
 *
 * WHY THIS APPROACH:
 * - Search interface for finding students
 * - Multi-select with checkboxes for batch enrollment
 * - Real-time validation prevents enrollment errors
 * - Clear feedback on success/failure
 */
export const EnrollStudents: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = useAppSelector(state => state.user.profile);

  // Get course ID from URL params
  const courseIdFromParams = searchParams.get('courseId');

  // Training programs list
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [isLoadingPrograms, setIsLoadingPrograms] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState(courseIdFromParams || '');

  // Student search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Student[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [enrolledStudentIds, setEnrolledStudentIds] = useState<string[]>([]);

  // Selected students for enrollment
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);

  // Operation state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /**
   * Load instructor's training programs
   */
  useEffect(() => {
    const loadPrograms = async () => {
      if (!user?.id) return;

      try {
        setIsLoadingPrograms(true);
        const response = await trainingProgramService.getTrainingPrograms({
          instructor_id: user.id,
          published: true
        });
        setPrograms(response.data);
      } catch (err) {
        console.error('Failed to load training programs:', err);
        setError('Failed to load your training programs. Please refresh the page.');
      } finally {
        setIsLoadingPrograms(false);
      }
    };

    loadPrograms();
  }, [user?.id]);

  /**
   * Load enrolled students when course is selected
   */
  useEffect(() => {
    const loadEnrolledStudents = async () => {
      if (!selectedCourseId) return;

      try {
        const enrolled = await enrollmentService.getEnrolledStudents(selectedCourseId);
        setEnrolledStudentIds(enrolled);
      } catch (err) {
        console.error('Failed to load enrolled students:', err);
      }
    };

    loadEnrolledStudents();
  }, [selectedCourseId]);

  /**
   * Handle student search
   */
  useEffect(() => {
    const searchStudents = async () => {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        return;
      }

      try {
        setIsSearching(true);
        const results = await enrollmentService.searchStudents(searchQuery);
        setSearchResults(results);
      } catch (err) {
        console.error('Failed to search students:', err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(searchStudents, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  /**
   * Toggle student selection
   */
  const handleStudentToggle = (studentId: string) => {
    setSelectedStudentIds(prev =>
      prev.includes(studentId)
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  /**
   * Handle enrollment submission
   */
  const handleEnrollment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validation
    if (!selectedCourseId) {
      setError('Please select a course.');
      return;
    }

    if (selectedStudentIds.length === 0) {
      setError('Please select at least one student to enroll.');
      return;
    }

    try {
      setIsSubmitting(true);
      const result = await enrollmentService.enrollStudents({
        courseId: selectedCourseId,
        studentIds: selectedStudentIds,
      });

      // Check for partial failures
      const failedCount = result.failed?.length || 0;
      if (failedCount > 0) {
        // Partial success - some enrolled, some failed
        setSuccess(`${result.enrolledCount} student(s) enrolled, ${failedCount} failed.`);
      } else {
        // Complete success
        setSuccess(`Successfully enrolled ${result.enrolledCount} student(s)!`);
      }

      setSelectedStudentIds([]);
      setSearchQuery('');
      setSearchResults([]);

      // Reload enrolled students
      const enrolled = await enrollmentService.getEnrolledStudents(selectedCourseId);
      setEnrolledStudentIds(enrolled);

      // Navigate back after 2 seconds
      setTimeout(() => {
        navigate('/instructor/students');
      }, 2000);
    } catch (err: any) {
      console.error('Failed to enroll students:', err);
      setError(err.response?.data?.message || err.message || 'Failed to enroll students. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Only show loading spinner if we're loading programs AND don't have a courseId from URL
  if (isLoadingPrograms && !courseIdFromParams) {
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
      <main style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Heading level="h1" gutterBottom={true}>
            Enroll Students
          </Heading>
          <p style={{ color: '#666', fontSize: '0.95rem' }}>
            Search for students and enroll them in your training programs
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <Card
            variant="outlined"
            padding="medium"
            style={{ marginBottom: '1.5rem', borderColor: '#ef4444', backgroundColor: '#fee2e2' }}
          >
            <p style={{ color: '#dc2626', margin: 0, fontWeight: 500 }} role="alert">{error}</p>
          </Card>
        )}

        {success && (
          <Card
            variant="outlined"
            padding="medium"
            style={{ marginBottom: '1.5rem', borderColor: '#10b981', backgroundColor: '#d1fae5' }}
          >
            <p style={{ color: '#065f46', margin: 0, fontWeight: 500 }} role="alert">{success}</p>
          </Card>
        )}

        {/* Enrollment Form */}
        <Card variant="outlined" padding="large">
          <form onSubmit={handleEnrollment}>
            {/* Course Selection */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="course" style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem' }}>
                Select Course
              </label>
              <select
                id="course"
                value={selectedCourseId}
                onChange={(e) => setSelectedCourseId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '1rem',
                }}
                required
              >
                <option value="">Choose a course...</option>
                {programs.map(program => (
                  <option key={program.id} value={program.id}>
                    {program.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Student Search */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="search" style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem' }}>
                Search Students
              </label>
              <Input
                id="search"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search students by name, email, or ID"
                disabled={!selectedCourseId}
              />
              {!selectedCourseId && (
                <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                  Please select a course first
                </p>
              )}
            </div>

            {/* Search Results */}
            {isSearching && (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <Spinner size="medium" />
              </div>
            )}

            {!isSearching && searchResults.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontWeight: 600, marginBottom: '0.75rem' }}>
                  Search Results ({searchResults.length})
                </p>
                <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}>
                  {searchResults.map(student => {
                    const isAlreadyEnrolled = enrolledStudentIds.includes(student.id);
                    const isSelected = selectedStudentIds.includes(student.id);

                    return (
                      <div
                        key={student.id}
                        style={{
                          padding: '0.75rem 1rem',
                          borderBottom: '1px solid #e5e7eb',
                          backgroundColor: isSelected ? '#eff6ff' : 'white',
                          opacity: isAlreadyEnrolled ? 0.6 : 1,
                        }}
                      >
                        <Checkbox
                          label={
                            <div>
                              <div style={{ fontWeight: 500 }}>{student.name}</div>
                              <div style={{ fontSize: '0.875rem', color: '#666' }}>{student.email}</div>
                              {isAlreadyEnrolled && (
                                <div style={{ fontSize: '0.75rem', color: '#f59e0b', marginTop: '0.25rem' }}>
                                  Already enrolled
                                </div>
                              )}
                            </div>
                          }
                          checked={isSelected}
                          onChange={() => handleStudentToggle(student.id)}
                          disabled={isAlreadyEnrolled}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {!isSearching && searchQuery && searchResults.length === 0 && (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                No students found matching "{searchQuery}"
              </div>
            )}

            {/* Selected Students Summary */}
            {selectedStudentIds.length > 0 && (
              <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f3f4f6', borderRadius: '0.375rem' }}>
                <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                  Selected Students: {selectedStudentIds.length}
                </p>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  {selectedStudentIds.map(id => {
                    const student = searchResults.find(s => s.id === id);
                    return student ? (
                      <div key={id} style={{ marginBottom: '0.25rem' }}>
                        • {student.name} ({student.email})
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/instructor/students')}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Spinner size="small" />
                    Enrolling...
                  </>
                ) : (
                  selectedStudentIds.length > 0
                    ? `Enroll ${selectedStudentIds.length} Student${selectedStudentIds.length !== 1 ? 's' : ''}`
                    : 'Enroll Students'
                )}
              </Button>
            </div>
          </form>
        </Card>
      </main>
    </DashboardLayout>
  );
};
