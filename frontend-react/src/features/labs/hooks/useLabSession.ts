/**
 * useLabSession Hook
 *
 * Manages lab session lifecycle and state
 * - Session creation and management
 * - Lab status (stopped, starting, running, paused, stopping)
 * - Resource usage tracking
 * - WebSocket connection for real-time updates
 *
 * @module features/labs/hooks/useLabSession
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { LabSession, LabStatus } from '../LabEnvironment';

interface UseLabSessionResult {
  session: LabSession | null;
  status: LabStatus;
  startLab: () => Promise<void>;
  pauseLab: () => Promise<void>;
  resumeLab: () => Promise<void>;
  stopLab: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const useLabSession = (
  labId: string | undefined,
  courseId: string | undefined
): UseLabSessionResult => {
  const [session, setSession] = useState<LabSession | null>(null);
  const [status, setStatus] = useState<LabStatus>('stopped');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize session on mount
  useEffect(() => {
    if (!labId || !courseId) return;

    const checkExistingSession = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `https://176.9.99.103:8005/api/v1/labs/session?labId=${labId}&courseId=${courseId}`,
          {
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.ok) {
          const data = await response.json();
          if (data.session) {
            setSession(data.session);
            setStatus(data.session.status);

            // Connect to WebSocket if session is active
            if (data.session.status === 'running' || data.session.status === 'paused') {
              connectWebSocket(data.session.id);
            }
          }
        }
      } catch (err) {
        console.error('Failed to check existing session:', err);
        setError('Failed to check for existing lab session');
      } finally {
        setIsLoading(false);
      }
    };

    checkExistingSession();

    return () => {
      // Cleanup WebSocket on unmount
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [labId, courseId]);

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback((sessionId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`wss://176.9.99.103:8005/ws/lab/${sessionId}`);

    ws.onopen = () => {
      console.log('WebSocket connected for lab session:', sessionId);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'status_update') {
          setStatus(data.status);
        } else if (data.type === 'resource_update') {
          setSession(prev => prev ? {
            ...prev,
            resourceUsage: data.resourceUsage
          } : null);
        } else if (data.type === 'session_update') {
          setSession(data.session);
          setStatus(data.session.status);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      wsRef.current = null;
    };

    wsRef.current = ws;
  }, []);

  // Start lab
  const startLab = useCallback(async () => {
    if (!labId || !courseId) {
      setError('Lab ID and Course ID are required');
      return;
    }

    try {
      setIsLoading(true);
      setStatus('starting');
      setError(null);

      const response = await fetch(
        'https://176.9.99.103:8005/api/v1/labs/start',
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ labId, courseId })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start lab');
      }

      const data = await response.json();
      setSession(data.session);
      setStatus(data.session.status);

      // Connect to WebSocket
      connectWebSocket(data.session.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start lab';
      setError(message);
      setStatus('stopped');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [labId, courseId, connectWebSocket]);

  // Pause lab
  const pauseLab = useCallback(async () => {
    if (!session) {
      setError('No active session');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${session.id}/pause`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to pause lab');
      }

      const data = await response.json();
      setSession(data.session);
      setStatus(data.session.status);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to pause lab';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  // Resume lab
  const resumeLab = useCallback(async () => {
    if (!session) {
      setError('No active session');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${session.id}/resume`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to resume lab');
      }

      const data = await response.json();
      setSession(data.session);
      setStatus(data.session.status);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resume lab';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  // Stop lab
  const stopLab = useCallback(async () => {
    if (!session) {
      setError('No active session');
      return;
    }

    try {
      setIsLoading(true);
      setStatus('stopping');
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${session.id}/stop`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to stop lab');
      }

      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      setSession(null);
      setStatus('stopped');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop lab';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  return {
    session,
    status,
    startLab,
    pauseLab,
    resumeLab,
    stopLab,
    isLoading,
    error
  };
};

export default useLabSession;
