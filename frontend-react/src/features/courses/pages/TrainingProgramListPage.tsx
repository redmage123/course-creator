/**
 * Training Program List Page
 *
 * BUSINESS CONTEXT:
 * Displays list of training programs for instructors and org admins.
 * Instructors see their own programs, org admins see organization programs.
 * Supports filtering by category, difficulty, publish status, and search.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches programs from backend API with React Query
 * - Client-side filtering and search
 * - Responsive grid layout
 * - Role-based program actions (edit, publish, delete)
 * - Loading states and error handling
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { useAuth } from '../../../hooks/useAuth';
import { trainingProgramService } from '../../../services';
import { TrainingProgramCard } from '../components/TrainingProgramCard';
import type { TrainingProgram, TrainingProgramFilters } from '../../../services';
import styles from './TrainingProgramListPage.module.css';

/**
 * Training Program List Page Props
 */
export interface TrainingProgramListPageProps {
  /** Context: instructor or org_admin */
  context: 'instructor' | 'organization';
}

/**
 * Training Program List Page Component
 *
 * WHY THIS APPROACH:
 * - Reusable for both instructor and org admin contexts
 * - Real-time filtering without API calls (better UX)
 * - Optimistic updates for publish/delete actions
 * - Clean, accessible UI with proper loading states
 */
export const TrainingProgramListPage: React.FC<TrainingProgramListPageProps> = ({
  context,
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [publishStatusFilter, setPublishStatusFilter] = useState<string>('all');

  /**
   * Fetch training programs based on context
   */
  const { data: programs, isLoading, error } = useQuery({
    queryKey: ['trainingPrograms', context, user?.id],
    queryFn: async () => {
      if (context === 'instructor') {
        // Instructors see only their own programs
        return trainingProgramService.getInstructorPrograms(user!.id);
      } else {
        // Org admins see organization programs
        return trainingProgramService.getOrganizationPrograms(user!.organizationId!);
      }
    },
    enabled: !!user?.id && (context === 'instructor' || !!user?.organizationId),
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });

  /**
   * Publish/Unpublish mutation
   */
  const togglePublishMutation = useMutation({
    mutationFn: ({ programId, shouldPublish }: { programId: string; shouldPublish: boolean }) =>
      shouldPublish
        ? trainingProgramService.publishTrainingProgram(programId)
        : trainingProgramService.unpublishTrainingProgram(programId),
    onSuccess: () => {
      // Invalidate and refetch programs list
      queryClient.invalidateQueries({ queryKey: ['trainingPrograms'] });
    },
  });

  /**
   * Delete program mutation
   */
  const deleteMutation = useMutation({
    mutationFn: (programId: string) => trainingProgramService.deleteTrainingProgram(programId),
    onSuccess: () => {
      // Invalidate and refetch programs list
      queryClient.invalidateQueries({ queryKey: ['trainingPrograms'] });
    },
  });

  /**
   * Filter and search programs (client-side for better UX)
   */
  const filteredPrograms = useMemo(() => {
    if (!programs?.data) return [];

    return programs.data.filter((program) => {
      // Search filter (title, description, tags)
      const matchesSearch =
        !searchQuery ||
        program.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        program.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        program.tags?.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));

      // Category filter
      const matchesCategory =
        categoryFilter === 'all' || program.category === categoryFilter;

      // Difficulty filter
      const matchesDifficulty =
        difficultyFilter === 'all' || program.difficulty_level === difficultyFilter;

      // Publish status filter
      const matchesPublishStatus =
        publishStatusFilter === 'all' ||
        (publishStatusFilter === 'published' && program.published) ||
        (publishStatusFilter === 'draft' && !program.published);

      return matchesSearch && matchesCategory && matchesDifficulty && matchesPublishStatus;
    });
  }, [programs, searchQuery, categoryFilter, difficultyFilter, publishStatusFilter]);

  /**
   * Get unique categories from programs
   */
  const availableCategories = useMemo(() => {
    if (!programs?.data) return [];
    const categories = programs.data
      .map((p) => p.category)
      .filter((c): c is string => !!c);
    return Array.from(new Set(categories)).sort();
  }, [programs]);

  /**
   * Handle edit program
   */
  const handleEdit = (programId: string) => {
    navigate(`/instructor/programs/${programId}/edit`);
  };

  /**
   * Handle delete program
   */
  const handleDelete = async (programId: string) => {
    if (window.confirm('Are you sure you want to delete this training program?')) {
      await deleteMutation.mutateAsync(programId);
    }
  };

  /**
   * Handle toggle publish status
   */
  const handleTogglePublish = async (programId: string, currentStatus: boolean) => {
    await togglePublishMutation.mutateAsync({
      programId,
      shouldPublish: !currentStatus,
    });
  };

  /**
   * Get page title based on context
   */
  const getPageTitle = () => {
    return context === 'instructor'
      ? 'My Training Programs'
      : 'Organization Training Programs';
  };

  /**
   * Get create button path based on context
   */
  const getCreatePath = () => {
    return context === 'instructor' ? '/instructor/programs/create' : undefined;
  };

  /**
   * Loading State
   */
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className={styles['list-page']}>
          <div className={styles['page-header']}>
            <Heading level="h1" gutterBottom>
              {getPageTitle()}
            </Heading>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <Spinner size="large" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Error State
   */
  if (error) {
    return (
      <DashboardLayout>
        <div className={styles['list-page']}>
          <div className={styles['page-header']}>
            <Heading level="h1" gutterBottom>
              {getPageTitle()}
            </Heading>
          </div>
          <Card variant="outlined" padding="large">
            <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
              Unable to load training programs. Please try refreshing the page.
            </p>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Success State - Display Programs List
   */
  return (
    <DashboardLayout>
      <div className={styles['list-page']}>
        {/* Page Header */}
        <div className={styles['page-header']}>
          <div className={styles['header-content']}>
            <Heading level="h1" gutterBottom>
              {getPageTitle()}
            </Heading>
            <p className={styles['header-description']}>
              {context === 'instructor'
                ? 'Manage your IT training programs, create new courses, and track student progress'
                : 'View and manage all training programs in your organization'}
            </p>
          </div>
          {getCreatePath() && (
            <Button variant="primary" onClick={() => navigate(getCreatePath()!)}>
              Create New Program
            </Button>
          )}
        </div>

        {/* Filters Section */}
        <Card variant="outlined" padding="medium" className={styles['filters-card']}>
          <div className={styles['filters-grid']}>
            {/* Search Input */}
            <div className={styles['filter-group']}>
              <label htmlFor="search" className={styles['filter-label']}>
                Search
              </label>
              <input
                id="search"
                type="text"
                placeholder="Search by title, description, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles['search-input']}
              />
            </div>

            {/* Category Filter */}
            <div className={styles['filter-group']}>
              <label htmlFor="category" className={styles['filter-label']}>
                Category
              </label>
              <select
                id="category"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className={styles['filter-select']}
              >
                <option value="all">All Categories</option>
                {availableCategories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* Difficulty Filter */}
            <div className={styles['filter-group']}>
              <label htmlFor="difficulty" className={styles['filter-label']}>
                Difficulty
              </label>
              <select
                id="difficulty"
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                className={styles['filter-select']}
              >
                <option value="all">All Levels</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            {/* Publish Status Filter (Instructor only) */}
            {context === 'instructor' && (
              <div className={styles['filter-group']}>
                <label htmlFor="publishStatus" className={styles['filter-label']}>
                  Status
                </label>
                <select
                  id="publishStatus"
                  value={publishStatusFilter}
                  onChange={(e) => setPublishStatusFilter(e.target.value)}
                  className={styles['filter-select']}
                >
                  <option value="all">All Status</option>
                  <option value="published">Published</option>
                  <option value="draft">Draft</option>
                </select>
              </div>
            )}
          </div>

          {/* Results Count */}
          <div className={styles['results-count']}>
            Showing {filteredPrograms.length} of {programs?.data.length || 0} programs
          </div>
        </Card>

        {/* Programs Grid */}
        {filteredPrograms.length === 0 ? (
          <Card variant="outlined" padding="large" className={styles['empty-state']}>
            <Heading level="h3" gutterBottom>
              No Training Programs Found
            </Heading>
            <p>
              {searchQuery || categoryFilter !== 'all' || difficultyFilter !== 'all'
                ? 'Try adjusting your filters to see more results.'
                : context === 'instructor'
                ? 'Get started by creating your first training program.'
                : 'No training programs have been created yet.'}
            </p>
            {context === 'instructor' && getCreatePath() && (
              <Button
                variant="primary"
                onClick={() => navigate(getCreatePath()!)}
                style={{ marginTop: '1rem' }}
              >
                Create First Program
              </Button>
            )}
          </Card>
        ) : (
          <div className={styles['programs-grid']}>
            {filteredPrograms.map((program) => (
              <TrainingProgramCard
                key={program.id}
                program={program}
                viewerRole={context === 'instructor' ? 'instructor' : 'org_admin'}
                onEdit={context === 'instructor' ? handleEdit : undefined}
                onDelete={context === 'instructor' ? handleDelete : undefined}
                onTogglePublish={context === 'instructor' ? handleTogglePublish : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
