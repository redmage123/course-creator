/**
 * useJupyterNotebook Hook
 *
 * BUSINESS CONTEXT:
 * Provides integration with Jupyter notebooks running in lab containers.
 * Fetches notebook content and provides it to the AI Assistant for
 * context-aware coding help.
 *
 * FEATURES:
 * - Polls for active notebook content
 * - Extracts code cells and errors
 * - Provides formatted context for AI
 * - Caches notebook state to reduce API calls
 *
 * @module features/labs/hooks/useJupyterNotebook
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '@/services';

/**
 * Notebook cell representation
 */
export interface NotebookCell {
  index: number;
  cellType: 'code' | 'markdown' | 'raw';
  source: string;
  executionCount?: number;
  hasError: boolean;
  errorMessage?: string;
  outputs?: Array<{
    outputType: string;
    text?: string;
    data?: Record<string, unknown>;
  }>;
}

/**
 * Active notebook context for AI
 */
export interface JupyterNotebookContext {
  hasActiveNotebook: boolean;
  notebookName: string;
  notebookPath: string;
  totalCells: number;
  codeCells: number;
  kernelStatus: 'idle' | 'busy' | 'starting' | 'unknown';
  recentCodeCells: NotebookCell[];
  errorCells: NotebookCell[];
  hasErrors: boolean;
  lastUpdated: Date;
}

/**
 * Hook options
 */
export interface UseJupyterNotebookOptions {
  /** Lab session ID */
  labId?: string;
  /** Enable automatic polling */
  enablePolling?: boolean;
  /** Polling interval in milliseconds (default: 5000) */
  pollInterval?: number;
  /** Only poll when Jupyter IDE is active */
  isJupyterActive?: boolean;
}

/**
 * Hook return type
 */
export interface UseJupyterNotebookReturn {
  /** Current notebook context */
  context: JupyterNotebookContext | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Manually refresh notebook content */
  refresh: () => Promise<void>;
  /** Get formatted context string for AI */
  getAIContext: () => string;
  /** Get specific cell content */
  getCell: (index: number) => Promise<NotebookCell | null>;
  /** List all notebooks in workspace */
  listNotebooks: () => Promise<string[]>;
}

/**
 * Default context when no notebook is active
 */
const DEFAULT_CONTEXT: JupyterNotebookContext = {
  hasActiveNotebook: false,
  notebookName: '',
  notebookPath: '',
  totalCells: 0,
  codeCells: 0,
  kernelStatus: 'unknown',
  recentCodeCells: [],
  errorCells: [],
  hasErrors: false,
  lastUpdated: new Date()
};

/**
 * Hook for Jupyter notebook integration
 */
export function useJupyterNotebook(options: UseJupyterNotebookOptions): UseJupyterNotebookReturn {
  const {
    labId,
    enablePolling = true,
    pollInterval = 5000,
    isJupyterActive = false
  } = options;

  const [context, setContext] = useState<JupyterNotebookContext | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastFetchRef = useRef<number>(0);

  /**
   * Transform API response to NotebookCell format
   */
  const transformCell = (cell: Record<string, unknown>, index: number): NotebookCell => ({
    index: typeof cell.index === 'number' ? cell.index : index,
    cellType: (cell.cell_type || cell.cellType || 'code') as 'code' | 'markdown' | 'raw',
    source: (cell.source as string) || '',
    executionCount: cell.execution_count as number | undefined,
    hasError: Boolean(cell.has_error || cell.hasError),
    errorMessage: (cell.error_message || cell.error || cell.errorMessage) as string | undefined,
    outputs: cell.outputs as NotebookCell['outputs']
  });

  /**
   * Fetch active notebook context from backend
   */
  const fetchNotebookContext = useCallback(async () => {
    if (!labId) {
      setContext(DEFAULT_CONTEXT);
      return;
    }

    // Throttle requests - minimum 2 seconds between fetches
    const now = Date.now();
    if (now - lastFetchRef.current < 2000) {
      return;
    }
    lastFetchRef.current = now;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/api/v1/labs/${labId}/jupyter/active-notebook`);
      const data = response.data;

      if (!data.has_active_notebook) {
        setContext({
          ...DEFAULT_CONTEXT,
          hasActiveNotebook: false,
          lastUpdated: new Date()
        });
        return;
      }

      // Transform API response
      const recentCells = (data.recent_code_cells || []).map(
        (cell: Record<string, unknown>, i: number) => transformCell(cell, i)
      );

      const errorCells = (data.error_cells || []).map(
        (cell: Record<string, unknown>, i: number) => transformCell(cell, i)
      );

      setContext({
        hasActiveNotebook: true,
        notebookName: data.notebook_name || '',
        notebookPath: data.notebook_path || '',
        totalCells: data.total_cells || 0,
        codeCells: data.code_cells || 0,
        kernelStatus: data.kernel_status || 'unknown',
        recentCodeCells: recentCells,
        errorCells: errorCells,
        hasErrors: data.has_errors || errorCells.length > 0,
        lastUpdated: new Date()
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch notebook';
      setError(message);
      console.error('[useJupyterNotebook] Error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [labId]);

  /**
   * Get a specific cell with context
   */
  const getCell = useCallback(async (cellIndex: number): Promise<NotebookCell | null> => {
    if (!labId || !context?.notebookPath) {
      return null;
    }

    try {
      const response = await apiClient.get(
        `/api/v1/labs/${labId}/jupyter/notebook/${context.notebookPath}/cell/${cellIndex}`
      );
      const data = response.data;

      return {
        index: data.cell_index,
        cellType: data.cell_type,
        source: data.source,
        executionCount: data.execution_count,
        hasError: data.has_error,
        errorMessage: data.error_message,
        outputs: data.outputs
      };
    } catch (err) {
      console.error('[useJupyterNotebook] Failed to get cell:', err);
      return null;
    }
  }, [labId, context?.notebookPath]);

  /**
   * List all notebooks in workspace
   */
  const listNotebooks = useCallback(async (): Promise<string[]> => {
    if (!labId) {
      return [];
    }

    try {
      const response = await apiClient.get(`/api/v1/labs/${labId}/jupyter/contents`);
      const files = response.data || [];

      return files
        .filter((f: { type: string }) => f.type === 'notebook')
        .map((f: { path: string }) => f.path);
    } catch (err) {
      console.error('[useJupyterNotebook] Failed to list notebooks:', err);
      return [];
    }
  }, [labId]);

  /**
   * Format context for AI Assistant
   */
  const getAIContext = useCallback((): string => {
    if (!context?.hasActiveNotebook) {
      return '';
    }

    const parts: string[] = [];

    parts.push(`[Jupyter Notebook: ${context.notebookName}]`);
    parts.push(`[Kernel Status: ${context.kernelStatus}]`);
    parts.push(`[Total Cells: ${context.totalCells}, Code Cells: ${context.codeCells}]`);

    // Add recent code cells
    if (context.recentCodeCells.length > 0) {
      parts.push('\n--- Recent Code Cells ---');
      context.recentCodeCells.forEach((cell, i) => {
        const execLabel = cell.executionCount ? `[${cell.executionCount}]` : '[*]';
        parts.push(`\nIn ${execLabel}:`);
        parts.push('```python');
        parts.push(cell.source);
        parts.push('```');
      });
    }

    // Add error cells
    if (context.errorCells.length > 0) {
      parts.push('\n--- Cells with Errors ---');
      context.errorCells.forEach((cell) => {
        parts.push(`\nCell ${cell.index}:`);
        parts.push('```python');
        parts.push(cell.source);
        parts.push('```');
        if (cell.errorMessage) {
          parts.push(`Error: ${cell.errorMessage}`);
        }
      });
    }

    return parts.join('\n');
  }, [context]);

  /**
   * Manual refresh
   */
  const refresh = useCallback(async () => {
    lastFetchRef.current = 0; // Reset throttle
    await fetchNotebookContext();
  }, [fetchNotebookContext]);

  /**
   * Set up polling when Jupyter is active
   */
  useEffect(() => {
    // Clear existing interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    // Only poll when Jupyter is active and we have a lab ID
    if (!enablePolling || !isJupyterActive || !labId) {
      return;
    }

    // Initial fetch
    fetchNotebookContext();

    // Set up polling
    pollIntervalRef.current = setInterval(() => {
      fetchNotebookContext();
    }, pollInterval);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [enablePolling, isJupyterActive, labId, pollInterval, fetchNotebookContext]);

  return {
    context,
    isLoading,
    error,
    refresh,
    getAIContext,
    getCell,
    listNotebooks
  };
}

export default useJupyterNotebook;
