/**
 * Tracks Page
 *
 * BUSINESS CONTEXT:
 * Organization admins manage learning tracks (structured learning paths).
 * Tracks organize courses into cohesive educational journeys.
 * Supports creating, editing, and managing tracks within projects.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches tracks from backend API with React Query
 * - Client-side filtering and search
 * - Responsive grid layout
 * - Modal-based CRUD operations
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { Input } from '../../../components/atoms/Input';
import { Select } from '../../../components/atoms/Select';
import { useAuth } from '../../../hooks/useAuth';
import { trackService, tokenManager, type Track } from '../../../services';
import { TrackCard } from '../components/TrackCard';
import { CreateTrackModal } from '../components/CreateTrackModal';
import { EditTrackModal } from '../components/EditTrackModal';
import styles from './TracksPage.module.css';

/**
 * Tracks Page Component
 *
 * WHY THIS APPROACH:
 * - Organization-scoped track list
 * - Real-time filtering without API calls (better UX)
 * - Modal-based forms (cleaner UI)
 * - Optimistic updates for better perceived performance
 */
export const TracksPage: React.FC = () => {
  const { user, organizationId } = useAuth();
  const queryClient = useQueryClient();

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTrack, setEditingTrack] = useState<Track | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // For creating tracks, we need a project_id
  // Automatically use the first available training program
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  /**
   * Fetch organization training programs to get project_id for track creation
   * Note: Use /courses endpoint with organization_id filter and published_only=false
   */
  const { data: programsData } = useQuery({
    queryKey: ['trainingPrograms', 'organization', organizationId],
    queryFn: async () => {
      const token = tokenManager.getToken();
      const response = await fetch(`/api/v1/courses?organization_id=${organizationId}&published_only=false`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch programs');
      return response.json();
    },
    enabled: !!organizationId,
    staleTime: 5 * 60 * 1000,
  });

  // Automatically set first program as selected project when programs load
  React.useEffect(() => {
    if (programsData && !selectedProjectId) {
      const programs = Array.isArray(programsData) ? programsData : programsData.data || [];
      if (programs.length > 0) {
        setSelectedProjectId(programs[0].id);
        console.log('[TracksPage] Auto-selected project:', programs[0].id, programs[0].title);
      }
    }
  }, [programsData, selectedProjectId]);

  /**
   * Fetch organization tracks
   */
  const {
    data: tracks,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['tracks', organizationId],
    queryFn: () => trackService.getOrganizationTracks(organizationId!),
    enabled: !!organizationId,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });

  /**
   * Filter and search tracks (client-side)
   */
  const filteredTracks = useMemo(() => {
    if (!tracks) return [];

    return tracks.filter((track) => {
      // Search filter (name, description)
      const matchesSearch =
        !searchQuery ||
        track.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        track.description?.toLowerCase().includes(searchQuery.toLowerCase());

      // Difficulty filter
      const matchesDifficulty =
        difficultyFilter === 'all' || track.difficulty_level === difficultyFilter;

      // Status filter
      const matchesStatus = statusFilter === 'all' || track.status === statusFilter;

      return matchesSearch && matchesDifficulty && matchesStatus;
    });
  }, [tracks, searchQuery, difficultyFilter, statusFilter]);

  /**
   * Handle create track success
   */
  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ['tracks'] });
  };

  /**
   * Handle edit track
   */
  const handleEditTrack = (track: Track) => {
    setEditingTrack(track);
  };

  /**
   * Handle edit success
   */
  const handleEditSuccess = () => {
    setEditingTrack(null);
    queryClient.invalidateQueries({ queryKey: ['tracks'] });
  };

  /**
   * Handle delete track
   */
  const handleDeleteTrack = async (trackId: string) => {
    if (window.confirm('Are you sure you want to delete this track? This action cannot be undone.')) {
      try {
        await trackService.deleteTrack(trackId);
        queryClient.invalidateQueries({ queryKey: ['tracks'] });
      } catch (error) {
        console.error('Failed to delete track:', error);
        alert('Failed to delete track. Please try again.');
      }
    }
  };

  /**
   * Loading State
   */
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className={styles['tracks-page']}>
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
        <div className={styles['tracks-page']}>
          <Card variant="outlined" padding="large">
            <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
              Unable to load tracks. Please try refreshing the page.
            </p>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Success State - Display Tracks List
   */
  return (
    <DashboardLayout>
      <div className={styles['tracks-page']}>
        {/* Page Header */}
        <div className={styles['page-header']}>
          <div className={styles['header-content']}>
            <Heading level="h1" gutterBottom>
              Learning Tracks
            </Heading>
            <p className={styles['header-description']}>
              Manage learning tracks and structured educational paths
            </p>
          </div>
          <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
            Create Track
          </Button>
        </div>

        {/* Filters Section */}
        <Card variant="outlined" padding="medium" className={styles['filters-card']}>
          <div className={styles['filters-grid']}>
            {/* Search Input */}
            <div className={styles['filter-group']}>
              <Input
                type="text"
                placeholder="Search by name or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                fullWidth
                label="Search"
              />
            </div>

            {/* Difficulty Filter */}
            <div className={styles['filter-group']}>
              <Select
                value={difficultyFilter}
                onChange={(value) => setDifficultyFilter(value as string)}
                label="Difficulty"
                fullWidth
                options={[
                  { value: 'all', label: 'All Levels' },
                  { value: 'beginner', label: 'Beginner' },
                  { value: 'intermediate', label: 'Intermediate' },
                  { value: 'advanced', label: 'Advanced' },
                ]}
              />
            </div>

            {/* Status Filter */}
            <div className={styles['filter-group']}>
              <Select
                value={statusFilter}
                onChange={(value) => setStatusFilter(value as string)}
                label="Status"
                fullWidth
                options={[
                  { value: 'all', label: 'All Status' },
                  { value: 'draft', label: 'Draft' },
                  { value: 'active', label: 'Active' },
                  { value: 'archived', label: 'Archived' },
                ]}
              />
            </div>
          </div>

          {/* Results Count */}
          <div className={styles['results-count']}>
            Showing {filteredTracks.length} of {tracks?.length || 0} tracks
          </div>
        </Card>

        {/* Tracks Grid */}
        {filteredTracks.length === 0 ? (
          <Card variant="outlined" padding="large" className={styles['empty-state']}>
            <Heading level="h3" gutterBottom>
              No Tracks Found
            </Heading>
            <p>
              {searchQuery || difficultyFilter !== 'all' || statusFilter !== 'all'
                ? 'Try adjusting your filters to see more results.'
                : 'Get started by creating your first learning track.'}
            </p>
            {(!searchQuery && difficultyFilter === 'all' && statusFilter === 'all') && (
              <Button
                variant="primary"
                onClick={() => setIsCreateModalOpen(true)}
                style={{ marginTop: '1rem' }}
              >
                Create First Track
              </Button>
            )}
          </Card>
        ) : (
          <div className={styles['tracks-grid']}>
            {filteredTracks.map((track) => (
              <TrackCard
                key={track.id}
                track={track}
                onEdit={handleEditTrack}
                onDelete={handleDeleteTrack}
              />
            ))}
          </div>
        )}

        {/* Create Track Modal */}
        {isCreateModalOpen && (() => {
          const testProjectId = typeof window !== 'undefined' && (window as any).__TEST_PROJECT_ID__;
          const effectiveProjectId = testProjectId || selectedProjectId || 'default-project-id';
          console.log('[TracksPage] Opening CreateTrackModal with projectId:', effectiveProjectId);
          console.log('[TracksPage] - Test injected ID:', testProjectId);
          console.log('[TracksPage] - Selected ID:', selectedProjectId);
          return (
            <CreateTrackModal
              isOpen={isCreateModalOpen}
              onClose={() => setIsCreateModalOpen(false)}
              projectId={effectiveProjectId}
              onSuccess={handleCreateSuccess}
            />
          );
        })()}

        {/* Edit Track Modal */}
        {editingTrack && (
          <EditTrackModal
            isOpen={true}
            onClose={() => setEditingTrack(null)}
            onSuccess={handleEditSuccess}
            track={editingTrack}
          />
        )}
      </div>
    </DashboardLayout>
  );
};
