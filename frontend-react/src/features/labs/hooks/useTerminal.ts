/**
 * useTerminal Hook
 *
 * Manages terminal command execution and history
 * - Command execution in lab container
 * - Command history tracking
 * - Output streaming
 * - Terminal state management
 *
 * @module features/labs/hooks/useTerminal
 */

import { useState, useCallback } from 'react';
import type { TerminalCommand } from '../components/TerminalEmulator';

interface UseTerminalResult {
  history: TerminalCommand[];
  executeCommand: (command: string) => Promise<void>;
  clearTerminal: () => void;
  isExecuting: boolean;
  error: string | null;
}

export const useTerminal = (
  sessionId: string | undefined
): UseTerminalResult => {
  const [history, setHistory] = useState<TerminalCommand[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Execute command
  const executeCommand = useCallback(async (command: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    if (!command.trim()) {
      return;
    }

    try {
      setIsExecuting(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/execute`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            command: command.trim(),
            shell: '/bin/bash'
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Command execution failed');
      }

      const data = await response.json();

      const commandResult: TerminalCommand = {
        command: command.trim(),
        output: data.output || '',
        exitCode: data.exitCode || 0,
        timestamp: new Date()
      };

      setHistory(prev => [...prev, commandResult]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Command execution failed';
      setError(message);

      // Add error to history
      const errorResult: TerminalCommand = {
        command: command.trim(),
        output: `Error: ${message}`,
        exitCode: 1,
        timestamp: new Date()
      };

      setHistory(prev => [...prev, errorResult]);
      throw err;
    } finally {
      setIsExecuting(false);
    }
  }, [sessionId]);

  // Clear terminal history
  const clearTerminal = useCallback(() => {
    setHistory([]);
    setError(null);
  }, []);

  return {
    history,
    executeCommand,
    clearTerminal,
    isExecuting,
    error
  };
};

export default useTerminal;
