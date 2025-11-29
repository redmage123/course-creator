/**
 * Sync Status Widget Component
 *
 * BUSINESS CONTEXT:
 * Displays offline content sync status and progress.
 * Shows download queue, active downloads, and storage usage.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses useOfflineSync hook to display real-time sync status.
 * Provides controls to manage offline content downloads.
 */

import React from 'react';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { SyncStatus, ContentType } from '@services/mobileExperienceService';
import styles from './SyncStatusWidget.module.css';

export interface SyncStatusWidgetProps {
  /**
   * Whether to show detailed progress
   * @default false
   */
  showDetails?: boolean;

  /**
   * Whether to allow user to manage sync
   * @default true
   */
  allowManagement?: boolean;

  /**
   * Callback when sync item is cancelled
   */
  onCancelSync?: (syncId: string) => void;

  /**
   * Callback when sync is retried
   */
  onRetrySync?: (syncId: string) => void;
}

/**
 * Sync Status Widget Component
 *
 * WHY THIS APPROACH:
 * - Compact summary view with expandable details
 * - Real-time progress indicators
 * - One-tap sync management
 * - Storage quota visualization
 *
 * @param props - Component props
 */
export const SyncStatusWidget: React.FC<SyncStatusWidgetProps> = ({
  showDetails = false,
  allowManagement = true,
  onCancelSync,
  onRetrySync,
}) => {
  const {
    syncItems,
    syncProgress,
    stats,
    cancelSync,
    retryDownload,
  } = useOfflineSync();

  const [isExpanded, setIsExpanded] = React.useState(showDetails);

  /**
   * Handle cancel sync
   */
  const handleCancel = async (syncId: string) => {
    try {
      await cancelSync(syncId);
      onCancelSync?.(syncId);
    } catch (error) {
      console.error('[SyncStatusWidget] Cancel failed:', error);
    }
  };

  /**
   * Handle retry sync
   */
  const handleRetry = async (syncId: string) => {
    try {
      await retryDownload(syncId);
      onRetrySync?.(syncId);
    } catch (error) {
      console.error('[SyncStatusWidget] Retry failed:', error);
    }
  };

  /**
   * Get status icon
   */
  const getStatusIcon = (status: SyncStatus): string => {
    switch (status) {
      case SyncStatus.PENDING:
        return '⏱';
      case SyncStatus.DOWNLOADING:
        return '⬇';
      case SyncStatus.DOWNLOADED:
      case SyncStatus.SYNCED:
        return '✓';
      case SyncStatus.ERROR:
        return '⚠';
      default:
        return '•';
    }
  };

  /**
   * Get content type label
   */
  const getContentTypeLabel = (type: ContentType): string => {
    const labels: Record<ContentType, string> = {
      [ContentType.COURSE]: 'Course',
      [ContentType.MODULE]: 'Module',
      [ContentType.LESSON]: 'Lesson',
      [ContentType.QUIZ]: 'Quiz',
      [ContentType.LAB]: 'Lab',
      [ContentType.VIDEO]: 'Video',
      [ContentType.DOCUMENT]: 'Document',
      [ContentType.SLIDE]: 'Slide',
    };
    return labels[type] || type;
  };

  // Don't render if no sync items
  if (syncItems.length === 0) {
    return null;
  }

  return (
    <div className={styles.syncStatusWidget} role="region" aria-label="Offline sync status">
      {/* Summary */}
      <button
        className={styles.summary}
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="sync-details"
      >
        <div className={styles.summaryContent}>
          <span className={styles.icon} aria-hidden="true">
            {stats.hasActiveDownloads ? '⬇' : '📁'}
          </span>
          <div className={styles.summaryText}>
            <div className={styles.title}>
              {stats.hasActiveDownloads
                ? `Downloading ${stats.downloadingItems} item${stats.downloadingItems !== 1 ? 's' : ''}`
                : `${stats.downloadedItems} item${stats.downloadedItems !== 1 ? 's' : ''} offline`}
            </div>
            <div className={styles.subtitle}>
              {stats.storageUsedMB} MB / {stats.storageQuotaMB} MB ({stats.storageUsedPercent}%)
            </div>
          </div>
        </div>
        <span className={styles.expandIcon} aria-hidden="true">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>

      {/* Storage bar */}
      <div className={styles.storageBar} role="progressbar" aria-valuenow={stats.storageUsedPercent} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`${styles.storageBarFill} ${stats.storageUsedPercent > 90 ? styles.storageWarning : ''}`}
          style={{ width: `${stats.storageUsedPercent}%` }}
        />
      </div>

      {/* Details */}
      {isExpanded && (
        <div id="sync-details" className={styles.details}>
          {syncItems.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No offline content yet</p>
              <p className={styles.hint}>Download courses to access them offline</p>
            </div>
          ) : (
            <ul className={styles.itemList}>
              {syncItems.map((item) => {
                const progress = syncProgress.get(item.id);
                const isDownloading = item.sync_status === SyncStatus.DOWNLOADING;
                const hasError = item.sync_status === SyncStatus.ERROR;

                return (
                  <li key={item.id} className={styles.item}>
                    <div className={styles.itemHeader}>
                      <span className={styles.statusIcon} aria-label={item.sync_status}>
                        {getStatusIcon(item.sync_status)}
                      </span>
                      <div className={styles.itemInfo}>
                        <div className={styles.itemTitle}>
                          {getContentTypeLabel(item.content_type)}
                        </div>
                        <div className={styles.itemMeta}>
                          {item.storage_size_bytes && (
                            <span>{Math.round(item.storage_size_bytes / (1024 * 1024))} MB</span>
                          )}
                          {item.sync_status === SyncStatus.DOWNLOADED && item.last_synced_at && (
                            <span>• {new Date(item.last_synced_at).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Progress bar */}
                    {isDownloading && progress && (
                      <div className={styles.progress}>
                        <div
                          className={styles.progressBar}
                          role="progressbar"
                          aria-valuenow={progress.progress}
                          aria-valuemin={0}
                          aria-valuemax={100}
                        >
                          <div
                            className={styles.progressBarFill}
                            style={{ width: `${progress.progress}%` }}
                          />
                        </div>
                        <div className={styles.progressText}>
                          {progress.progress}% ({Math.round(progress.bytesDownloaded / (1024 * 1024))} MB)
                        </div>
                      </div>
                    )}

                    {/* Error message */}
                    {hasError && item.last_error && (
                      <div className={styles.error}>
                        <span className={styles.errorIcon}>⚠</span>
                        <span className={styles.errorMessage}>{item.last_error}</span>
                      </div>
                    )}

                    {/* Actions */}
                    {allowManagement && (
                      <div className={styles.itemActions}>
                        {hasError && item.retry_count < item.max_retries && (
                          <button
                            className={`${styles.actionButton} ${styles.retryButton}`}
                            onClick={() => handleRetry(item.id)}
                            aria-label="Retry download"
                          >
                            ↻ Retry
                          </button>
                        )}
                        <button
                          className={`${styles.actionButton} ${styles.cancelButton}`}
                          onClick={() => handleCancel(item.id)}
                          aria-label={isDownloading ? 'Cancel download' : 'Remove offline content'}
                        >
                          {isDownloading ? '✕ Cancel' : '🗑 Remove'}
                        </button>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
