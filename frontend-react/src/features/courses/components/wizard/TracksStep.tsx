/**
 * TracksStep - Step 2 of Program Setup Wizard
 *
 * BUSINESS CONTEXT:
 * Manage learning tracks within a training program. Tracks are structured
 * learning paths containing courses. Instructors add, edit, and remove tracks
 * with inline forms (no modals).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches tracks via trackService.getProjectTracks(projectId)
 * - Inline create/edit form with track name, description, difficulty, duration
 * - React Query for data fetching and cache invalidation
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '../../../../components/atoms/Button';
import { Spinner } from '../../../../components/atoms/Spinner';
import { trackService } from '../../../../services';
import type { Track, CreateTrackRequest, UpdateTrackRequest } from '../../../../services';
import styles from './TracksStep.module.css';

interface TracksStepProps {
  programId: string;
  projectId?: string;
  readOnly?: boolean;
}

export const TracksStep: React.FC<TracksStepProps> = ({
  programId,
  projectId,
  readOnly = false,
}) => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingTrack, setEditingTrack] = useState<Track | null>(null);

  // Form state
  const [formName, setFormName] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formDifficulty, setFormDifficulty] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [formDuration, setFormDuration] = useState<number | ''>('');

  const effectiveProjectId = projectId || programId;

  const { data: tracks = [], isLoading } = useQuery({
    queryKey: ['tracks', effectiveProjectId],
    queryFn: () => trackService.getProjectTracks(effectiveProjectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateTrackRequest) => trackService.createTrack(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tracks', effectiveProjectId] });
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTrackRequest }) =>
      trackService.updateTrack(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tracks', effectiveProjectId] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => trackService.deleteTrack(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tracks', effectiveProjectId] });
    },
  });

  const resetForm = () => {
    setShowForm(false);
    setEditingTrack(null);
    setFormName('');
    setFormDescription('');
    setFormDifficulty('beginner');
    setFormDuration('');
  };

  const openEditForm = (track: Track) => {
    setEditingTrack(track);
    setFormName(track.name);
    setFormDescription(track.description || '');
    setFormDifficulty(track.difficulty_level);
    setFormDuration(track.duration_weeks || '');
    setShowForm(true);
  };

  const openCreateForm = () => {
    resetForm();
    setShowForm(true);
  };

  const handleSubmit = () => {
    if (!formName.trim()) return;

    if (editingTrack) {
      updateMutation.mutate({
        id: editingTrack.id,
        data: {
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          difficulty_level: formDifficulty,
          duration_weeks: formDuration ? Number(formDuration) : undefined,
        },
      });
    } else {
      createMutation.mutate({
        name: formName.trim(),
        description: formDescription.trim() || undefined,
        project_id: effectiveProjectId,
        difficulty_level: formDifficulty,
        duration_weeks: formDuration ? Number(formDuration) : undefined,
      });
    }
  };

  const handleDelete = (trackId: string, trackName: string) => {
    if (window.confirm(`Delete track "${trackName}"? This cannot be undone.`)) {
      deleteMutation.mutate(trackId);
    }
  };

  const getStatusClass = (status: string) => {
    if (status === 'active') return styles.statusActive;
    if (status === 'archived') return styles.statusArchived;
    return styles.statusDraft;
  };

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
          <h3 className={styles.title}>Learning Tracks</h3>
          <p className={styles.subtitle}>
            Organize your program into learning tracks. Each track contains a set of courses.
          </p>
        </div>
        {!readOnly && !showForm && (
          <Button variant="primary" size="small" onClick={openCreateForm}>
            + Add Track
          </Button>
        )}
      </div>

      {showForm && !readOnly && (
        <div className={styles.inlineForm}>
          <h4 className={styles.formTitle}>
            {editingTrack ? 'Edit Track' : 'New Track'}
          </h4>
          <div className={styles.formGrid}>
            <div className={styles.formGroup}>
              <label htmlFor="track-name" className={styles.formLabel}>
                Track Name <span className={styles.required}>*</span>
              </label>
              <input
                id="track-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className={styles.formInput}
                placeholder="e.g., Cloud Fundamentals"
                autoFocus
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="track-description" className={styles.formLabel}>Description</label>
              <textarea
                id="track-description"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                className={styles.formTextarea}
                placeholder="Brief description of this track..."
                rows={3}
              />
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="track-difficulty" className={styles.formLabel}>Difficulty</label>
                <select
                  id="track-difficulty"
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
                <label htmlFor="track-duration" className={styles.formLabel}>Duration (weeks)</label>
                <input
                  id="track-duration"
                  type="number"
                  value={formDuration}
                  onChange={(e) => setFormDuration(e.target.value ? Number(e.target.value) : '')}
                  className={styles.formInput}
                  placeholder="0"
                  min="1"
                />
              </div>
            </div>

            <div className={styles.formActions}>
              <Button variant="secondary" size="small" onClick={resetForm}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="small"
                onClick={handleSubmit}
                loading={createMutation.isPending || updateMutation.isPending}
                disabled={!formName.trim() || createMutation.isPending || updateMutation.isPending}
              >
                {editingTrack ? 'Update Track' : 'Create Track'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {tracks.length === 0 && !showForm ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>No tracks yet</p>
          <p>Add learning tracks to organize your courses into structured paths.</p>
          {!readOnly && (
            <Button variant="primary" size="small" onClick={openCreateForm}>
              + Add Your First Track
            </Button>
          )}
        </div>
      ) : (
        <div className={styles.trackList}>
          {tracks.map((track) => (
            <div key={track.id} className={styles.trackCard}>
              <div className={styles.trackCardHeader}>
                <div>
                  <h4 className={styles.trackName}>{track.name}</h4>
                  {track.description && (
                    <p className={styles.trackDescription}>{track.description}</p>
                  )}
                  <div className={styles.trackMeta}>
                    <span className={`${styles.statusBadge} ${getStatusClass(track.status)}`}>
                      {track.status}
                    </span>
                    <span>{track.difficulty_level}</span>
                    {track.duration_weeks && <span>{track.duration_weeks} weeks</span>}
                    <span>{track.enrollment_count} enrolled</span>
                  </div>
                </div>
                {!readOnly && (
                  <div className={styles.trackActions}>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={() => openEditForm(track)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="danger"
                      size="small"
                      onClick={() => handleDelete(track.id, track.name)}
                      disabled={deleteMutation.isPending}
                    >
                      Delete
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

TracksStep.displayName = 'TracksStep';
