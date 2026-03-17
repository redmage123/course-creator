/**
 * SyncStatusWidget Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the SyncStatusWidget provides real-time feedback
 * on data synchronization status for offline-capable features.
 *
 * TEST COVERAGE:
 * - Component rendering with different sync states
 * - Progress indication during sync
 * - Error state handling
 * - Sync management actions
 * - Accessibility features
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing.
 * Mocks useOfflineSync hook to control sync state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SyncStatusWidget } from './SyncStatusWidget';
import { SyncStatus, ContentType } from '@services/mobileExperienceService';

// Mock the useOfflineSync hook
vi.mock('../hooks/useOfflineSync', () => ({
  useOfflineSync: vi.fn(),
}));

import { useOfflineSync } from '../hooks/useOfflineSync';

const mockUseOfflineSync = useOfflineSync as ReturnType<typeof vi.fn>;

// Default mock return value
const createMockHookReturn = (overrides: Record<string, any> = {}) => {
  // Extract stats from overrides if present
  const statsOverrides = overrides.stats || {};

  // Compute hasActiveDownloads from stats.downloadingItems if not explicitly set
  const downloadingItems = statsOverrides.downloadingItems ?? 0;
  const hasActiveDownloads = overrides.hasActiveDownloads ?? downloadingItems > 0;

  // Build stats with hasActiveDownloads included
  const stats = {
    totalItems: 0,
    pendingItems: 0,
    downloadingItems: 0,
    downloadedItems: 0,
    errorItems: 0,
    storageUsedMB: 0,
    storageQuotaMB: 500,
    storageUsedPercent: 0,
    ...statsOverrides,
    // Component uses stats.hasActiveDownloads
    hasActiveDownloads,
  };

  // Remove stats from overrides to avoid double-spreading
  const { stats: _stats, ...restOverrides } = overrides;

  return {
    syncItems: [],
    syncProgress: new Map(),
    isLoading: false,
    stats,
    loadSyncItems: vi.fn(),
    queueDownload: vi.fn(),
    startDownload: vi.fn(),
    cancelSync: vi.fn().mockResolvedValue(undefined),
    retryDownload: vi.fn().mockResolvedValue(undefined),
    uploadOfflineProgress: vi.fn(),
    checkStorageQuota: vi.fn(),
    clearAllOfflineContent: vi.fn(),
    hasPendingDownloads: false,
    hasActiveDownloads,
    hasOfflineContent: false,
    hasErrors: false,
    isStorageFull: false,
    ...restOverrides,
  };
};

// Sample sync item
const createSyncItem = (overrides = {}) => ({
  id: 'sync-1',
  user_id: 'user-1',
  content_type: ContentType.COURSE,
  content_id: 'course-1',
  sync_status: SyncStatus.DOWNLOADED,
  priority: 5,
  storage_size_bytes: 50 * 1024 * 1024, // 50 MB
  retry_count: 0,
  max_retries: 3,
  wifi_only: true,
  has_offline_progress: false,
  offline_progress_data: null,
  progress_synced_at: null,
  last_synced_at: '2024-01-15T10:30:00Z',
  last_error: null,
  created_at: '2024-01-01T00:00:00Z',
  expires_at: null,
  ...overrides,
});

describe('SyncStatusWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('returns null when no sync items exist', () => {
      mockUseOfflineSync.mockReturnValue(createMockHookReturn());

      const { container } = render(<SyncStatusWidget />);

      expect(container.firstChild).toBeNull();
    });

    it('renders when sync items exist', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: {
            totalItems: 1,
            pendingItems: 0,
            downloadingItems: 0,
            downloadedItems: 1,
            errorItems: 0,
            storageUsedMB: 50,
            storageQuotaMB: 500,
            storageUsedPercent: 10,
          },
        })
      );

      render(<SyncStatusWidget />);

      expect(screen.getByRole('region', { name: /offline sync status/i })).toBeInTheDocument();
    });

    it('shows downloaded item count in summary', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem(), createSyncItem({ id: 'sync-2' })],
          stats: {
            totalItems: 2,
            pendingItems: 0,
            downloadingItems: 0,
            downloadedItems: 2,
            errorItems: 0,
            storageUsedMB: 100,
            storageQuotaMB: 500,
            storageUsedPercent: 20,
          },
        })
      );

      render(<SyncStatusWidget />);

      expect(screen.getByText(/2 items offline/i)).toBeInTheDocument();
    });

    it('shows downloading state when active downloads exist', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.DOWNLOADING })],
          stats: {
            totalItems: 1,
            pendingItems: 0,
            downloadingItems: 1,
            downloadedItems: 0,
            errorItems: 0,
            storageUsedMB: 0,
            storageQuotaMB: 500,
            storageUsedPercent: 0,
          },
          hasActiveDownloads: true,
        })
      );

      render(<SyncStatusWidget />);

      expect(screen.getByText(/downloading 1 item/i)).toBeInTheDocument();
    });
  });

  describe('Expandable Details', () => {
    it('expands to show details when clicked', async () => {
      const user = userEvent.setup();
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget />);

      // Click to expand
      await user.click(screen.getByRole('button', { expanded: false }));

      // Should show item list
      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    it('shows content type label in details', async () => {
      const user = userEvent.setup();
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ content_type: ContentType.COURSE })],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      expect(screen.getByText('Course')).toBeInTheDocument();
    });
  });

  describe('Storage Display', () => {
    it('shows storage usage in summary', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: {
            totalItems: 1,
            downloadedItems: 1,
            storageUsedMB: 150,
            storageQuotaMB: 500,
            storageUsedPercent: 30,
            pendingItems: 0,
            downloadingItems: 0,
            errorItems: 0,
          },
        })
      );

      render(<SyncStatusWidget />);

      expect(screen.getByText(/150 MB.*500 MB.*30%/)).toBeInTheDocument();
    });

    it('displays storage progress bar', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: {
            totalItems: 1,
            downloadedItems: 1,
            storageUsedMB: 250,
            storageQuotaMB: 500,
            storageUsedPercent: 50,
            pendingItems: 0,
            downloadingItems: 0,
            errorItems: 0,
          },
        })
      );

      render(<SyncStatusWidget />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    });
  });

  describe('Download Progress', () => {
    it('shows progress bar for downloading items', async () => {
      const user = userEvent.setup();
      const progressMap = new Map();
      progressMap.set('sync-1', { syncId: 'sync-1', progress: 75, bytesDownloaded: 37.5 * 1024 * 1024, totalBytes: 50 * 1024 * 1024 });

      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.DOWNLOADING })],
          syncProgress: progressMap,
          stats: { totalItems: 1, downloadedItems: 0, downloadingItems: 1, storageUsedMB: 0, storageQuotaMB: 500, storageUsedPercent: 0, pendingItems: 0, errorItems: 0 },
          hasActiveDownloads: true,
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      // Find the item progress bar (not the storage bar)
      const progressBars = screen.getAllByRole('progressbar');
      const itemProgressBar = progressBars.find(bar => bar.getAttribute('aria-valuenow') === '75');
      expect(itemProgressBar).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('shows error message for failed sync', async () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.ERROR, last_error: 'Network timeout' })],
          stats: { totalItems: 1, downloadedItems: 0, errorItems: 1, storageUsedMB: 0, storageQuotaMB: 500, storageUsedPercent: 0, pendingItems: 0, downloadingItems: 0 },
          hasErrors: true,
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      expect(screen.getByText('Network timeout')).toBeInTheDocument();
    });

    it('shows retry button for failed items', async () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.ERROR, last_error: 'Failed', retry_count: 0, max_retries: 3 })],
          stats: { totalItems: 1, downloadedItems: 0, errorItems: 1, storageUsedMB: 0, storageQuotaMB: 500, storageUsedPercent: 0, pendingItems: 0, downloadingItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('calls retryDownload when retry clicked', async () => {
      const user = userEvent.setup();
      const mockRetry = vi.fn().mockResolvedValue(undefined);

      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.ERROR, last_error: 'Failed', retry_count: 0, max_retries: 3 })],
          retryDownload: mockRetry,
          stats: { totalItems: 1, downloadedItems: 0, errorItems: 1, storageUsedMB: 0, storageQuotaMB: 500, storageUsedPercent: 0, pendingItems: 0, downloadingItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      await user.click(screen.getByRole('button', { name: /retry/i }));

      expect(mockRetry).toHaveBeenCalledWith('sync-1');
    });
  });

  describe('Sync Management', () => {
    it('shows cancel/remove button for items', async () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument();
    });

    it('calls cancelSync when remove clicked', async () => {
      const user = userEvent.setup();
      const mockCancel = vi.fn().mockResolvedValue(undefined);

      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          cancelSync: mockCancel,
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      await user.click(screen.getByRole('button', { name: /remove/i }));

      expect(mockCancel).toHaveBeenCalledWith('sync-1');
    });

    it('hides management buttons when allowManagement is false', async () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} allowManagement={false} />);

      expect(screen.queryByRole('button', { name: /remove/i })).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible region', () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget />);

      expect(screen.getByRole('region', { name: /offline sync status/i })).toBeInTheDocument();
    });

    it('has expandable button with aria-expanded', async () => {
      const user = userEvent.setup();
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget />);

      const button = screen.getByRole('button', { expanded: false });
      expect(button).toHaveAttribute('aria-expanded', 'false');

      await user.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('has accessible action buttons', async () => {
      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} />);

      const removeButton = screen.getByRole('button', { name: /remove offline content/i });
      expect(removeButton).toHaveAccessibleName();
    });
  });

  describe('Callbacks', () => {
    it('calls onCancelSync callback when cancel succeeds', async () => {
      const user = userEvent.setup();
      const mockCancel = vi.fn().mockResolvedValue(undefined);
      const onCancelSync = vi.fn();

      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem()],
          cancelSync: mockCancel,
          stats: { totalItems: 1, downloadedItems: 1, storageUsedMB: 50, storageQuotaMB: 500, storageUsedPercent: 10, pendingItems: 0, downloadingItems: 0, errorItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} onCancelSync={onCancelSync} />);

      await user.click(screen.getByRole('button', { name: /remove/i }));

      await waitFor(() => {
        expect(onCancelSync).toHaveBeenCalledWith('sync-1');
      });
    });

    it('calls onRetrySync callback when retry succeeds', async () => {
      const user = userEvent.setup();
      const mockRetry = vi.fn().mockResolvedValue(undefined);
      const onRetrySync = vi.fn();

      mockUseOfflineSync.mockReturnValue(
        createMockHookReturn({
          syncItems: [createSyncItem({ sync_status: SyncStatus.ERROR, last_error: 'Failed', retry_count: 0, max_retries: 3 })],
          retryDownload: mockRetry,
          stats: { totalItems: 1, downloadedItems: 0, errorItems: 1, storageUsedMB: 0, storageQuotaMB: 500, storageUsedPercent: 0, pendingItems: 0, downloadingItems: 0 },
        })
      );

      render(<SyncStatusWidget showDetails={true} onRetrySync={onRetrySync} />);

      await user.click(screen.getByRole('button', { name: /retry/i }));

      await waitFor(() => {
        expect(onRetrySync).toHaveBeenCalledWith('sync-1');
      });
    });
  });
});
