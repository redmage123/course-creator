/**
 * Quiz List Page
 *
 * BUSINESS CONTEXT:
 * Student-facing page to view all available quizzes across their enrolled courses.
 * Students are assigned courses by trainers and need to see which assessments
 * are pending, completed, or available for review.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches quizzes from student's enrolled courses
 * - Shows quiz status (pending, completed, in_progress)
 * - Links to quiz taking and results review
 * - React Query for data fetching and caching
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Spinner } from '../components/atoms/Spinner';
import { apiClient } from '../services/apiClient';

interface Quiz {
  id: string;
  title: string;
  description: string;
  course_id: string;
  course_title: string;
  num_questions: number;
  time_limit_minutes: number | null;
  passing_score: number;
  status: 'pending' | 'in_progress' | 'completed';
  score?: number;
  completed_at?: string;
}

interface QuizListResponse {
  quizzes: Quiz[];
  total: number;
}

/**
 * Quiz List Page Component
 *
 * WHY THIS APPROACH:
 * - Card-based layout for clear quiz visibility
 * - Status indicators for progress tracking
 * - Direct links to quiz taking
 * - Separate sections for pending and completed quizzes
 */
export const QuizListPage: React.FC = () => {
  /**
   * Fetch student's quizzes from enrolled courses
   */
  const { data, isLoading, error } = useQuery<QuizListResponse>({
    queryKey: ['studentQuizzes'],
    queryFn: async () => {
      const response = await apiClient.get<QuizListResponse>('/api/v1/quizzes/my-quizzes');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });

  const quizzes = data?.quizzes || [];
  const pendingQuizzes = quizzes.filter(q => q.status === 'pending' || q.status === 'in_progress');
  const completedQuizzes = quizzes.filter(q => q.status === 'completed');

  /**
   * Get status badge styling
   */
  const getStatusBadge = (status: Quiz['status'], score?: number, passingScore?: number) => {
    const styles: Record<string, React.CSSProperties> = {
      pending: { backgroundColor: '#fef3c7', color: '#92400e', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 },
      in_progress: { backgroundColor: '#dbeafe', color: '#1e40af', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 },
      completed: { backgroundColor: score && passingScore && score >= passingScore ? '#d1fae5' : '#fee2e2', color: score && passingScore && score >= passingScore ? '#065f46' : '#991b1b', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 },
    };

    const labels: Record<string, string> = {
      pending: 'Not Started',
      in_progress: 'In Progress',
      completed: score && passingScore && score >= passingScore ? 'Passed' : 'Needs Review',
    };

    return <span style={styles[status]}>{labels[status]}</span>;
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

  if (error) {
    return (
      <DashboardLayout>
        <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
          <Card variant="outlined" padding="large" style={{ textAlign: 'center' }}>
            <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
              Unable to load quizzes. Please try refreshing the page.
            </p>
            <Button variant="primary" onClick={() => window.location.reload()}>
              Refresh Page
            </Button>
          </Card>
        </main>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Heading level="h1" gutterBottom={true}>
            Quizzes & Assessments
          </Heading>
          <p style={{ color: '#666', fontSize: '0.95rem' }}>
            Complete quizzes to test your knowledge and track your progress
          </p>
        </div>

        {/* Stats Overview */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>{pendingQuizzes.length}</div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Pending Quizzes</div>
            </div>
          </Card>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>{completedQuizzes.length}</div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Completed</div>
            </div>
          </Card>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#8b5cf6' }}>
                {completedQuizzes.length > 0
                  ? Math.round(completedQuizzes.reduce((sum, q) => sum + (q.score || 0), 0) / completedQuizzes.length)
                  : 0}%
              </div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Average Score</div>
            </div>
          </Card>
        </div>

        {/* Pending Quizzes */}
        {pendingQuizzes.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
              📝 Ready to Take
            </Heading>
            <div style={{ display: 'grid', gap: '1rem' }}>
              {pendingQuizzes.map(quiz => (
                <Card key={quiz.id} variant="outlined" padding="large">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Heading level="h3" style={{ fontSize: '1.1rem', margin: 0 }}>
                          {quiz.title}
                        </Heading>
                        {getStatusBadge(quiz.status)}
                      </div>
                      <p style={{ color: '#666', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                        {quiz.description}
                      </p>
                      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem', color: '#666' }}>
                        <span>📚 {quiz.course_title}</span>
                        <span>❓ {quiz.num_questions} questions</span>
                        {quiz.time_limit_minutes && <span>⏱️ {quiz.time_limit_minutes} min</span>}
                        <span>✅ Pass: {quiz.passing_score}%</span>
                      </div>
                    </div>
                    <div>
                      <Link to={`/quizzes/${quiz.id}/course/${quiz.course_id}`}>
                        <Button variant="primary" size="medium" data-action="take-quiz">
                          {quiz.status === 'in_progress' ? 'Continue Quiz' : 'Start Quiz'}
                        </Button>
                      </Link>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Completed Quizzes */}
        {completedQuizzes.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
              ✅ Completed Quizzes
            </Heading>
            <div style={{ display: 'grid', gap: '1rem' }}>
              {completedQuizzes.map(quiz => (
                <Card key={quiz.id} variant="outlined" padding="large" style={{ backgroundColor: '#f9fafb' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Heading level="h3" style={{ fontSize: '1.1rem', margin: 0 }}>
                          {quiz.title}
                        </Heading>
                        {getStatusBadge(quiz.status, quiz.score, quiz.passing_score)}
                      </div>
                      <p style={{ color: '#666', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                        📚 {quiz.course_title}
                      </p>
                      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem' }}>
                        <span style={{ fontWeight: 600, color: quiz.score && quiz.score >= quiz.passing_score ? '#10b981' : '#dc2626' }}>
                          Score: {quiz.score}%
                        </span>
                        {quiz.completed_at && (
                          <span style={{ color: '#666' }}>
                            Completed: {new Date(quiz.completed_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Link to={`/quizzes/${quiz.id}/course/${quiz.course_id}/results`}>
                        <Button variant="secondary" size="medium">
                          View Results
                        </Button>
                      </Link>
                      {quiz.score && quiz.score < quiz.passing_score && (
                        <Link to={`/quizzes/${quiz.id}/course/${quiz.course_id}`}>
                          <Button variant="primary" size="medium">
                            Retake Quiz
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {quizzes.length === 0 && (
          <Card variant="outlined" padding="large" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📝</div>
            <Heading level="h3" style={{ marginBottom: '0.5rem' }}>
              No Quizzes Available
            </Heading>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
              Quizzes will appear here once your trainer assigns them to your enrolled courses.
            </p>
            <Link to="/courses/my-courses">
              <Button variant="primary">View My Courses</Button>
            </Link>
          </Card>
        )}
      </main>
    </DashboardLayout>
  );
};
