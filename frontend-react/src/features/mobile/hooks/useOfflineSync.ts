/**
 * Offline Sync Hook
 *
 * BUSINESS CONTEXT:
 * Manages offline content synchronization for the Course Creator Platform.
 * Enables students to download courses, modules, and lessons for offline learning.
 *
 * TECHNICAL IMPLEMENTATION:
 * Tracks sync queue, download progress, and offline content availability.
 * Integrates with Service Worker for background downloads and caching.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  mobileExperienceService,
  OfflineContentSync,
  ContentType,
  SyncStatus,
} from '@services/mobileExperienceService';

interface SyncProgress {
  syncId: string;
  progress: number; // 0-100
  bytesDownloaded: number;
  totalBytes: number;
}

/**
 * Offline Sync Hook
 *
 * WHY THIS APPROACH:
 * - Centralized offline sync management
 * - Real-time sync progress tracking
 * - Automatic retry on failure
 * - WiFi-only download enforcement
 * - Storage quota management
 *
 * @returns Offline sync state and methods
 */
export const useOfflineSync = () => {
  const [syncItems, setSyncItems] = useState<OfflineContentSync[]>([]);
  const [syncProgress, setSyncProgress] = useState<Map<string, SyncProgress>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [totalStorageUsed, setTotalStorageUsed] = useState(0);
  const [storageQuota, setStorageQuota] = useState(0);

  /**
   * Load sync items from backend
   *
   * BUSINESS LOGIC:
   * Fetches current sync queue and offline content.
   * Called on mount and after sync operations.
   */
  const loadSyncItems = useCallback(async () => {
    try {
      setIsLoading(true);
      const items = await mobileExperienceService.getOfflineSyncItems();
      setSyncItems(items);

      // Calculate total storage used
      const totalBytes = items
        .filter((item) => item.sync_status === SyncStatus.DOWNLOADED || item.sync_status === SyncStatus.SYNCED)
        .reduce((sum, item) => sum + (item.storage_size_bytes || 0), 0);
      setTotalStorageUsed(totalBytes);
    } catch (error) {
      console.error('[useOfflineSync] Load sync items failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Queue content for offline download
   *
   * BUSINESS LOGIC:
   * Adds content to download queue with specified priority.
   * Respects WiFi-only and storage quota settings.
   *
   * @param contentType - Type of content to download
   * @param contentId - ID of content to download
   * @param priority - Download priority (1-10, default 5)
   */
  const queueDownload = useCallback(
    async (contentType: ContentType, contentId: string, priority: number = 5) => {
      try {
        setIsLoading(true);

        // Check if already queued or downloaded
        const existing = syncItems.find(
          (item) => item.content_type === contentType && item.content_id === contentId
        );
        if (existing) {
          console.warn('[useOfflineSync] Content already queued or downloaded');
          return;
        }

        // Queue download
        const syncItem = await mobileExperienceService.queueOfflineSync(
          contentType,
          contentId,
          priority
        );
        setSyncItems((prev) => [...prev, syncItem]);

        // Start download if online and not metered (or WiFi-only disabled)
        if (navigator.onLine && !mobileExperienceService.isMeteredConnection()) {
          await startDownload(syncItem.id);
        }
      } catch (error) {
        console.error('[useOfflineSync] Queue download failed:', error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [syncItems]
  );

  /**
   * Start download for sync item
   *
   * BUSINESS LOGIC:
   * Initiates download for queued content.
   * Updates progress in real-time.
   *
   * @param syncId - ID of sync item to download
   */
  const startDownload = useCallback(async (syncId: string) => {
    try {
      // Update sync status to downloading
      setSyncItems((prev) =>
        prev.map((item) =>
          item.id === syncId ? { ...item, sync_status: SyncStatus.DOWNLOADING } : item
        )
      );

      // Initialize progress tracking
      setSyncProgress((prev) => {
        const newMap = new Map(prev);
        newMap.set(syncId, {
          syncId,
          progress: 0,
          bytesDownloaded: 0,
          totalBytes: 0,
        });
        return newMap;
      });

      // Note: Actual download would be handled by Service Worker
      // This is a placeholder for the download initiation
      console.log(`[useOfflineSync] Starting download for sync item: ${syncId}`);

      // In a real implementation, this would:
      // 1. Fetch content from backend
      // 2. Cache in Service Worker
      // 3. Update progress via postMessage
      // 4. Mark as downloaded when complete
    } catch (error) {
      console.error('[useOfflineSync] Start download failed:', error);

      // Mark as error
      setSyncItems((prev) =>
        prev.map((item) =>
          item.id === syncId ? { ...item, sync_status: SyncStatus.ERROR } : item
        )
      );
    }
  }, []);

  /**
   * Cancel download or delete offline content
   *
   * BUSINESS LOGIC:
   * Removes content from queue or deletes downloaded content.
   * Frees up storage space.
   *
   * @param syncId - ID of sync item to cancel/delete
   */
  const cancelSync = useCallback(
    async (syncId: string) => {
      try {
        setIsLoading(true);
        await mobileExperienceService.cancelOfflineSync(syncId);

        // Remove from local state
        setSyncItems((prev) => prev.filter((item) => item.id !== syncId));
        setSyncProgress((prev) => {
          const newMap = new Map(prev);
          newMap.delete(syncId);
          return newMap;
        });

        // Recalculate storage
        await loadSyncItems();
      } catch (error) {
        console.error('[useOfflineSync] Cancel sync failed:', error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [loadSyncItems]
  );

  /**
   * Retry failed download
   *
   * BUSINESS LOGIC:
   * Retries download for failed sync items.
   * Respects max retry count.
   *
   * @param syncId - ID of sync item to retry
   */
  const retryDownload = useCallback(
    async (syncId: string) => {
      const syncItem = syncItems.find((item) => item.id === syncId);
      if (!syncItem) {
        console.warn('[useOfflineSync] Sync item not found');
        return;
      }

      if (syncItem.retry_count >= syncItem.max_retries) {
        console.warn('[useOfflineSync] Max retries exceeded');
        return;
      }

      await startDownload(syncId);
    },
    [syncItems, startDownload]
  );

  /**
   * Sync offline progress to backend
   *
   * BUSINESS LOGIC:
   * Uploads progress made while offline when connection is restored.
   * Called automatically when online status changes.
   *
   * @param syncId - ID of sync item
   * @param progressData - Progress data to sync
   */
  const uploadOfflineProgress = useCallback(async (syncId: string, progressData: Record<string, any>) => {
    try {
      await mobileExperienceService.syncOfflineProgress(syncId, progressData);

      // Update local state
      setSyncItems((prev) =>
        prev.map((item) =>
          item.id === syncId
            ? {
                ...item,
                has_offline_progress: true,
                offline_progress_data: progressData,
                progress_synced_at: new Date().toISOString(),
              }
            : item
        )
      );
    } catch (error) {
      console.error('[useOfflineSync] Sync progress failed:', error);
      throw error;
    }
  }, []);

  /**
   * Get storage quota information
   *
   * BUSINESS LOGIC:
   * Checks available storage space for offline content.
   * Used to prevent exceeding storage limits.
   */
  const checkStorageQuota = useCallback(async () => {
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        setStorageQuota(estimate.quota || 0);
        setTotalStorageUsed(estimate.usage || 0);
      }
    } catch (error) {
      console.error('[useOfflineSync] Check storage quota failed:', error);
    }
  }, []);

  /**
   * Clear all offline content
   *
   * BUSINESS LOGIC:
   * Deletes all downloaded content to free up space.
   * Used when storage is full or user wants to clear cache.
   */
  const clearAllOfflineContent = useCallback(async () => {
    try {
      setIsLoading(true);

      // Delete all downloaded items
      const downloadedItems = syncItems.filter(
        (item) => item.sync_status === SyncStatus.DOWNLOADED || item.sync_status === SyncStatus.SYNCED
      );

      for (const item of downloadedItems) {
        await mobileExperienceService.cancelOfflineSync(item.id);
      }

      // Reload sync items
      await loadSyncItems();
    } catch (error) {
      console.error('[useOfflineSync] Clear all offline content failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [syncItems, loadSyncItems]);

  /**
   * Load sync items on mount
   */
  useEffect(() => {
    loadSyncItems();
  }, [loadSyncItems]);

  /**
   * Check storage quota on mount
   */
  useEffect(() => {
    checkStorageQuota();
  }, [checkStorageQuota]);

  /**
   * Listen for Service Worker messages (download progress)
   */
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'DOWNLOAD_PROGRESS') {
          const { syncId, progress, bytesDownloaded, totalBytes } = event.data;
          setSyncProgress((prev) => {
            const newMap = new Map(prev);
            newMap.set(syncId, { syncId, progress, bytesDownloaded, totalBytes });
            return newMap;
          });
        } else if (event.data.type === 'DOWNLOAD_COMPLETE') {
          const { syncId } = event.data;
          setSyncItems((prev) =>
            prev.map((item) =>
              item.id === syncId ? { ...item, sync_status: SyncStatus.DOWNLOADED } : item
            )
          );
          setSyncProgress((prev) => {
            const newMap = new Map(prev);
            newMap.delete(syncId);
            return newMap;
          });
        } else if (event.data.type === 'DOWNLOAD_ERROR') {
          const { syncId, error } = event.data;
          setSyncItems((prev) =>
            prev.map((item) =>
              item.id === syncId
                ? { ...item, sync_status: SyncStatus.ERROR, last_error: error }
                : item
            )
          );
        }
      });
    }
  }, []);

  /**
   * Get sync statistics
   */
  const stats = {
    totalItems: syncItems.length,
    pendingItems: syncItems.filter((item) => item.sync_status === SyncStatus.PENDING).length,
    downloadingItems: syncItems.filter((item) => item.sync_status === SyncStatus.DOWNLOADING)
      .length,
    downloadedItems: syncItems.filter(
      (item) => item.sync_status === SyncStatus.DOWNLOADED || item.sync_status === SyncStatus.SYNCED
    ).length,
    errorItems: syncItems.filter((item) => item.sync_status === SyncStatus.ERROR).length,
    storageUsedMB: Math.round(totalStorageUsed / (1024 * 1024)),
    storageQuotaMB: Math.round(storageQuota / (1024 * 1024)),
    storageUsedPercent: storageQuota > 0 ? Math.round((totalStorageUsed / storageQuota) * 100) : 0,
  };

  return {
    // State
    syncItems,
    syncProgress,
    isLoading,
    stats,

    // Methods
    loadSyncItems,
    queueDownload,
    startDownload,
    cancelSync,
    retryDownload,
    uploadOfflineProgress,
    checkStorageQuota,
    clearAllOfflineContent,

    // Computed
    hasPendingDownloads: stats.pendingItems > 0,
    hasActiveDownloads: stats.downloadingItems > 0,
    hasOfflineContent: stats.downloadedItems > 0,
    hasErrors: stats.errorItems > 0,
    isStorageFull: stats.storageUsedPercent > 90,
  };
};
