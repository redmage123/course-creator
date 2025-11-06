/**
 * Lab Environment Component
 *
 * Main lab interface component providing:
 * - Multi-IDE support (VSCode, Jupyter, Terminal)
 * - File system management
 * - Code execution
 * - Terminal emulator
 * - Resource monitoring
 * - AI assistant integration
 *
 * Architecture:
 * - Uses React hooks for state management
 * - Integrates with lab-manager service (port 8005)
 * - Follows SOLID principles
 * - Implements WebSocket for real-time updates
 *
 * @module features/labs/LabEnvironment
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '@/components/atoms/Card';
import { Button } from '@/components/atoms/Button';
import { Spinner } from '@/components/atoms/Spinner';
import { useAuth } from '@/hooks/useAuth';
import { IDESelector } from './components/IDESelector';
import { FileExplorer } from './components/FileExplorer';
import { CodeEditor } from './components/CodeEditor';
import { TerminalEmulator } from './components/TerminalEmulator';
import { ResourceMonitor } from './components/ResourceMonitor';
import { AIAssistant } from './components/AIAssistant';
import { LabControls } from './components/LabControls';
import { useLabSession } from './hooks/useLabSession';
import { useFileSystem } from './hooks/useFileSystem';
import { useTerminal } from './hooks/useTerminal';
import styles from './LabEnvironment.module.css';

export type IDEType = 'vscode' | 'jupyter' | 'terminal';

export type LabStatus = 'stopped' | 'starting' | 'running' | 'paused' | 'stopping';

export interface LabFile {
  id: string;
  name: string;
  path: string;
  content: string;
  language: string;
  isModified: boolean;
  lastModified: Date;
}

export interface LabSession {
  id: string;
  studentId: string;
  courseId: string;
  status: LabStatus;
  startTime: Date;
  endTime?: Date;
  resourceUsage: {
    cpu: number;
    memory: number;
    disk: number;
  };
}

export const LabEnvironment: React.FC = () => {
  const { labId, courseId } = useParams<{ labId: string; courseId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Lab session management
  const {
    session,
    status,
    startLab,
    pauseLab,
    resumeLab,
    stopLab,
    isLoading: sessionLoading,
    error: sessionError
  } = useLabSession(labId, courseId);

  // File system management
  const {
    files,
    currentFile,
    createFile,
    openFile,
    saveFile,
    deleteFile,
    renameFile,
    createFolder,
    isLoading: filesLoading
  } = useFileSystem(session?.id);

  // Terminal management
  const {
    history,
    executeCommand,
    clearTerminal,
    isExecuting
  } = useTerminal(session?.id);

  // UI State
  const [selectedIDE, setSelectedIDE] = useState<IDEType>('vscode');
  const [isFileExplorerOpen, setIsFileExplorerOpen] = useState(true);
  const [isTerminalOpen, setIsTerminalOpen] = useState(true);
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false);
  const [codeContent, setCodeContent] = useState('');
  const [sessionTimer, setSessionTimer] = useState(0);

  // Refs
  const timerInterval = useRef<NodeJS.Timeout | null>(null);
  const editorRef = useRef<any>(null);

  /**
   * Initialize lab session timer
   */
  useEffect(() => {
    if (status === 'running' && session) {
      timerInterval.current = setInterval(() => {
        const elapsed = Math.floor(
          (Date.now() - new Date(session.startTime).getTime()) / 1000
        );
        setSessionTimer(elapsed);
      }, 1000);
    } else {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
        timerInterval.current = null;
      }
    }

    return () => {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
    };
  }, [status, session]);

  /**
   * Load current file content when file changes
   */
  useEffect(() => {
    if (currentFile) {
      setCodeContent(currentFile.content);
    }
  }, [currentFile]);

  /**
   * Handle starting lab session
   */
  const handleStartLab = useCallback(async () => {
    try {
      await startLab();
    } catch (error) {
      console.error('Failed to start lab:', error);
    }
  }, [startLab]);

  /**
   * Handle pausing lab session
   */
  const handlePauseLab = useCallback(async () => {
    try {
      await pauseLab();
    } catch (error) {
      console.error('Failed to pause lab:', error);
    }
  }, [pauseLab]);

  /**
   * Handle resuming lab session
   */
  const handleResumeLab = useCallback(async () => {
    try {
      await resumeLab();
    } catch (error) {
      console.error('Failed to resume lab:', error);
    }
  }, [resumeLab]);

  /**
   * Handle stopping lab session
   */
  const handleStopLab = useCallback(async () => {
    if (window.confirm('Are you sure you want to stop the lab? Unsaved changes will be lost.')) {
      try {
        await stopLab();
        navigate('/dashboard/student');
      } catch (error) {
        console.error('Failed to stop lab:', error);
      }
    }
  }, [stopLab, navigate]);

  /**
   * Handle IDE selection change
   */
  const handleIDEChange = useCallback((ide: IDEType) => {
    setSelectedIDE(ide);
  }, []);

  /**
   * Handle file selection from file explorer
   */
  const handleFileSelect = useCallback(async (fileId: string) => {
    try {
      await openFile(fileId);
    } catch (error) {
      console.error('Failed to open file:', error);
    }
  }, [openFile]);

  /**
   * Handle code content change
   */
  const handleCodeChange = useCallback((newContent: string) => {
    setCodeContent(newContent);
    if (currentFile) {
      // Mark file as modified
      // This would be handled by the file system hook
    }
  }, [currentFile]);

  /**
   * Handle saving current file
   */
  const handleSaveFile = useCallback(async () => {
    if (!currentFile) return;

    try {
      await saveFile(currentFile.id, codeContent);
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  }, [currentFile, codeContent, saveFile]);

  /**
   * Handle running code
   */
  const handleRunCode = useCallback(async () => {
    if (!currentFile) return;

    try {
      const command = getRunCommand(currentFile.language, currentFile.name);
      await executeCommand(command);
    } catch (error) {
      console.error('Failed to run code:', error);
    }
  }, [currentFile, executeCommand]);

  /**
   * Handle terminal command execution
   */
  const handleTerminalCommand = useCallback(async (command: string) => {
    try {
      await executeCommand(command);
    } catch (error) {
      console.error('Failed to execute command:', error);
    }
  }, [executeCommand]);

  /**
   * Get run command based on file language
   */
  const getRunCommand = (language: string, fileName: string): string => {
    const commands: Record<string, string> = {
      python: `python ${fileName}`,
      javascript: `node ${fileName}`,
      typescript: `ts-node ${fileName}`,
      java: `javac ${fileName} && java ${fileName.replace('.java', '')}`,
      cpp: `g++ ${fileName} -o output && ./output`,
      c: `gcc ${fileName} -o output && ./output`,
    };

    return commands[language] || `cat ${fileName}`;
  };

  /**
   * Format session timer as HH:MM:SS
   */
  const formatTimer = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return [hours, minutes, secs]
      .map(v => v.toString().padStart(2, '0'))
      .join(':');
  };

  /**
   * Handle keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + S: Save file
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSaveFile();
      }

      // Ctrl/Cmd + Enter: Run code
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleRunCode();
      }

      // Ctrl/Cmd + B: Toggle file explorer
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        setIsFileExplorerOpen(prev => !prev);
      }

      // Ctrl/Cmd + `: Toggle terminal
      if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault();
        setIsTerminalOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSaveFile, handleRunCode]);

  // Loading state
  if (sessionLoading || filesLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="large" />
        <p>Loading lab environment...</p>
      </div>
    );
  }

  // Error state
  if (sessionError) {
    return (
      <div className={styles.errorContainer}>
        <Card variant="outlined" padding="large">
          <h2>Failed to Load Lab</h2>
          <p>{sessionError}</p>
          <Button variant="primary" onClick={() => navigate('/dashboard/student')}>
            Return to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className={styles.labContainer} data-testid="lab-environment">
      {/* Lab Header */}
      <header className={styles.labHeader}>
        <div className={styles.labTitle}>
          <h1>Lab Environment</h1>
          {courseId && <span className={styles.courseId}>Course: {courseId}</span>}
        </div>

        <div className={styles.headerControls}>
          {/* Session Timer */}
          {status === 'running' && (
            <div className={styles.sessionTimer} id="lab-timer">
              <span className={styles.timerIcon}>⏱</span>
              <span className={styles.timerValue}>{formatTimer(sessionTimer)}</span>
            </div>
          )}

          {/* Session Status */}
          <div className={styles.sessionStatus} id="lab-status">
            <span className={`${styles.statusIndicator} ${styles[status]}`}></span>
            <span className={styles.statusText}>{status.toUpperCase()}</span>
          </div>

          {/* Session ID */}
          {session && (
            <div className={styles.sessionId} id="session-id">
              Session: {session.id.substring(0, 8)}
            </div>
          )}

          {/* Lab Controls */}
          <LabControls
            status={status}
            onStart={handleStartLab}
            onPause={handlePauseLab}
            onResume={handleResumeLab}
            onStop={handleStopLab}
          />
        </div>
      </header>

      {/* Main Lab Content */}
      <div className={styles.labContent}>
        {/* File Explorer Sidebar */}
        {isFileExplorerOpen && (
          <aside className={styles.fileExplorerPanel}>
            <FileExplorer
              files={files}
              currentFile={currentFile}
              onFileSelect={handleFileSelect}
              // @ts-ignore - onFileCreate returns Promise<LabFile> but expects Promise<void>
              onFileCreate={createFile}
              onFileDelete={deleteFile}
              onFileRename={renameFile}
              onFolderCreate={createFolder}
            />
          </aside>
        )}

        {/* Main Editor Area */}
        <main className={styles.editorPanel}>
          {/* IDE Selector */}
          <IDESelector
            selectedIDE={selectedIDE}
            onIDEChange={handleIDEChange}
            disabled={status !== 'running'}
          />

          {/* IDE Content Area */}
          <div className={styles.ideContainer}>
            {selectedIDE === 'vscode' && (
              <div className={styles.vscodeContainer} id="vscode-iframe">
                <CodeEditor
                  ref={editorRef}
                  value={codeContent}
                  language={currentFile?.language || 'javascript'}
                  onChange={handleCodeChange}
                  onSave={handleSaveFile}
                  onRun={handleRunCode}
                  readOnly={status !== 'running'}
                />
              </div>
            )}

            {selectedIDE === 'jupyter' && (
              <div className={styles.jupyterContainer} id="jupyter-iframe">
                <iframe
                  src={`/api/v1/labs/${session?.id}/jupyter`}
                  className={styles.jupyterIframe}
                  title="Jupyter Notebook"
                />
              </div>
            )}

            {selectedIDE === 'terminal' && (
              <div className={styles.terminalFullContainer} id="terminal-container">
                <TerminalEmulator
                  history={history}
                  // @ts-ignore - onCommand prop exists but not in type definition
                  onCommand={handleTerminalCommand}
                  isExecuting={isExecuting}
                  disabled={status !== 'running'}
                />
              </div>
            )}
          </div>

          {/* Bottom Terminal Panel (when not in terminal IDE mode) */}
          {selectedIDE !== 'terminal' && isTerminalOpen && (
            <div className={styles.terminalPanel}>
              <div className={styles.terminalHeader}>
                <span>Terminal</span>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={() => setIsTerminalOpen(false)}
                >
                  ✕
                </Button>
              </div>
              <TerminalEmulator
                history={history}
                // @ts-ignore - onCommand prop exists but not in type definition
                onCommand={handleTerminalCommand}
                isExecuting={isExecuting}
                disabled={status !== 'running'}
              />
            </div>
          )}
        </main>

        {/* Right Sidebar (Resource Monitor & AI Assistant) */}
        <aside className={styles.rightSidebar}>
          {/* Resource Monitor */}
          {session && status === 'running' && (
            <div className={styles.resourcePanel}>
              {/* @ts-expect-error - ResourceMonitor props type mismatch - TODO: fix interface */}
              <ResourceMonitor sessionId={session.id} />
            </div>
          )}

          {/* AI Assistant Toggle */}
          <div className={styles.aiAssistantToggle}>
            <Button
              id="ai-assistant-btn"
              variant={isAIAssistantOpen ? 'primary' : 'secondary'}
              onClick={() => setIsAIAssistantOpen(!isAIAssistantOpen)}
              fullWidth
            >
              🤖 AI Assistant
            </Button>
          </div>

          {/* AI Assistant Panel */}
          {isAIAssistantOpen && (
            <div className={styles.aiAssistantPanel} id="ai-assistant-panel">
              <AIAssistant
                // @ts-ignore - currentFile is LabFile | null but expects string | undefined
                currentFile={currentFile}
                codeContent={codeContent}
                terminalHistory={history}
              />
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default LabEnvironment;
