/**
 * Project Builder Chat Component
 *
 * BUSINESS CONTEXT:
 * AI-powered conversational interface for bulk project creation.
 * Enables organization admins to create multi-location training programs
 * through natural language conversation.
 *
 * FEATURES:
 * - Natural language project configuration
 * - File upload for instructor/student rosters (CSV, Excel, JSON)
 * - Schedule proposal visualization and editing
 * - Track and location configuration
 * - Real-time creation progress tracking
 * - Zoom room creation integration
 *
 * WORKFLOW:
 * 1. Start conversation describing project needs
 * 2. Upload roster files (optional)
 * 3. Review and edit schedule proposal
 * 4. Preview configuration and confirm
 * 5. Execute bulk creation with progress tracking
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { apiClient } from '../../../../services/apiClient';
import { Button } from '../../../../components/atoms/Button';
import styles from './ProjectBuilderChat.module.css';

// State enum from backend - matches ProjectBuilderState
type BuilderState =
  | 'INITIAL'
  | 'GATHERING_INFO'
  | 'COLLECTING_ROSTER'
  | 'REVIEWING_SCHEDULE'
  | 'CONFIRMING'
  | 'CREATING'
  | 'COMPLETED'
  | 'FAILED';

interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    scheduleProposal?: ScheduleProposal;
    fileUpload?: FileUploadResult;
    creationProgress?: CreationProgress;
    actions?: ActionButton[];
  };
}

interface ScheduleProposal {
  totalSessions: number;
  locations: string[];
  tracks: string[];
  dateRange: { start: string; end: string };
  sessions: ScheduleSession[];
  conflicts?: string[];
  warnings?: string[];
}

interface ScheduleSession {
  id: string;
  track: string;
  course: string;
  location: string;
  date: string;
  time: string;
  instructor?: string;
  duration: number;
}

interface FileUploadResult {
  filename: string;
  fileType: string;
  recordCount: number;
  validRecords: number;
  errors?: string[];
}

interface CreationProgress {
  phase: string;
  current: number;
  total: number;
  message: string;
  created: {
    projects?: number;
    subProjects?: number;
    tracks?: number;
    zoomRooms?: number;
  };
}

interface ActionButton {
  id: string;
  label: string;
  action: string;
  variant?: 'primary' | 'secondary' | 'danger';
}

interface ProjectBuilderSession {
  sessionId: string;
  state: BuilderState;
  projectSpec?: any;
}

interface ProjectBuilderChatProps {
  onClose?: () => void;
  onProjectCreated?: (projectId: string) => void;
}

/**
 * Project Builder Chat Component
 *
 * WHY THIS APPROACH:
 * - Conversational UI reduces complexity for multi-location project setup
 * - Inline schedule visualization enables quick review and edits
 * - Progress tracking provides transparency during creation
 * - File upload supports existing roster data import
 */
export const ProjectBuilderChat: React.FC<ProjectBuilderChatProps> = ({
  onClose,
  onProjectCreated
}) => {
  const { user } = useAuth();

  // Session state
  const [session, setSession] = useState<ProjectBuilderSession | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // Chat state
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Schedule editing state
  const [editingSchedule, setEditingSchedule] = useState<ScheduleProposal | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Start a new project builder session
   */
  const startSession = async () => {
    setIsStarting(true);

    try {
      const response = await apiClient.post<{ session_id: string; message: string }>(
        '/api/v1/ai-assistant/project-builder/start',
        {
          organization_id: user?.organizationId
        }
      );

      const newSession: ProjectBuilderSession = {
        sessionId: response.data.session_id,
        state: 'GATHERING_INFO'
      };

      setSession(newSession);

      // Add welcome message
      const welcomeMessage: AIMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.message || getWelcomeMessage(),
        timestamp: new Date(),
        metadata: {
          actions: [
            { id: 'upload', label: 'Upload Roster File', action: 'upload', variant: 'secondary' },
            { id: 'manual', label: 'Configure Manually', action: 'manual', variant: 'secondary' }
          ]
        }
      };

      setMessages([welcomeMessage]);
    } catch (error) {
      console.error('Failed to start project builder session:', error);
      addErrorMessage('Failed to start project builder. Please try again.');
    } finally {
      setIsStarting(false);
    }
  };

  /**
   * Get welcome message based on user role
   */
  const getWelcomeMessage = (): string => {
    return `Welcome to the Project Builder! I'll help you create a multi-location training program.

You can:
- **Describe your training needs** in natural language
- **Upload roster files** with instructor and student information
- **Review and edit** the generated schedule
- **Create everything** with a single confirmation

What would you like to do first?`;
  };

  /**
   * Send message to project builder
   */
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !session) return;

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post<{
        message: string;
        state: BuilderState;
        schedule_proposal?: ScheduleProposal;
        creation_progress?: CreationProgress;
        actions?: ActionButton[];
      }>('/api/v1/ai-assistant/project-builder/message', {
        session_id: session.sessionId,
        message: userMessage.content
      });

      // Update session state
      setSession((prev) =>
        prev ? { ...prev, state: response.data.state } : null
      );

      const assistantMessage: AIMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        metadata: {
          scheduleProposal: response.data.schedule_proposal,
          creationProgress: response.data.creation_progress,
          actions: response.data.actions
        }
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Handle completed state
      if (response.data.state === 'COMPLETED') {
        // Extract project ID and notify parent
        if (onProjectCreated) {
          // Parse project ID from response or metadata
          const projectId = extractProjectId(response.data.message);
          if (projectId) {
            onProjectCreated(projectId);
          }
        }
      }
    } catch (error) {
      console.error('Project builder error:', error);
      addErrorMessage('Failed to process your request. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle file upload
   */
  const handleFileUpload = async () => {
    if (!selectedFile || !session) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('session_id', session.sessionId);

      const response = await apiClient.post<{
        message: string;
        file_result: FileUploadResult;
        state: BuilderState;
      }>('/api/v1/ai-assistant/project-builder/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSession((prev) =>
        prev ? { ...prev, state: response.data.state } : null
      );

      const uploadMessage: AIMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        metadata: {
          fileUpload: response.data.file_result
        }
      };

      setMessages((prev) => [...prev, uploadMessage]);
      setSelectedFile(null);
    } catch (error) {
      console.error('File upload error:', error);
      addErrorMessage('Failed to upload file. Please check the format and try again.');
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Handle action button clicks
   */
  const handleAction = async (action: string) => {
    switch (action) {
      case 'upload':
        fileInputRef.current?.click();
        break;
      case 'manual':
        setInputMessage('I want to configure the project manually');
        break;
      case 'confirm':
        setInputMessage('Yes, create the project');
        break;
      case 'edit':
        // Open schedule editor
        const lastSchedule = messages
          .slice()
          .reverse()
          .find((m) => m.metadata?.scheduleProposal);
        if (lastSchedule?.metadata?.scheduleProposal) {
          setEditingSchedule(lastSchedule.metadata.scheduleProposal);
        }
        break;
      case 'cancel':
        setInputMessage('Cancel and start over');
        break;
      default:
        setInputMessage(action);
    }
  };

  /**
   * Add error message to chat
   */
  const addErrorMessage = (content: string) => {
    const errorMessage: AIMessage = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content,
      timestamp: new Date()
    };
    setMessages((prev) => [...prev, errorMessage]);
  };

  /**
   * Extract project ID from completion message
   */
  const extractProjectId = (message: string): string | null => {
    const match = message.match(/project[:\s]+([a-f0-9-]{36})/i);
    return match ? match[1] : null;
  };

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTime = (date: Date): string => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  /**
   * Get state indicator
   */
  const getStateIndicator = (): { label: string; color: string } => {
    if (!session) return { label: 'Not Started', color: '#9ca3af' };

    switch (session.state) {
      case 'INITIAL':
        return { label: 'Starting', color: '#3b82f6' };
      case 'GATHERING_INFO':
        return { label: 'Gathering Info', color: '#8b5cf6' };
      case 'COLLECTING_ROSTER':
        return { label: 'Collecting Data', color: '#10b981' };
      case 'REVIEWING_SCHEDULE':
        return { label: 'Reviewing Schedule', color: '#f59e0b' };
      case 'CONFIRMING':
        return { label: 'Ready to Create', color: '#ef4444' };
      case 'CREATING':
        return { label: 'Creating...', color: '#3b82f6' };
      case 'COMPLETED':
        return { label: 'Completed', color: '#10b981' };
      case 'FAILED':
        return { label: 'Failed', color: '#ef4444' };
      default:
        return { label: 'Unknown', color: '#9ca3af' };
    }
  };

  const stateInfo = getStateIndicator();

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <span className={styles.headerIcon}>🏗️</span>
          <span>Project Builder</span>
          <span
            className={styles.stateIndicator}
            style={{ backgroundColor: stateInfo.color }}
          >
            {stateInfo.label}
          </span>
        </div>
        <div className={styles.headerActions}>
          {onClose && (
            <button
              className={styles.headerBtn}
              onClick={onClose}
              title="Close"
              aria-label="Close project builder"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Not started state */}
      {!session && (
        <div className={styles.startScreen}>
          <div className={styles.startIcon}>🚀</div>
          <h2 className={styles.startTitle}>Create Multi-Location Training Program</h2>
          <p className={styles.startDescription}>
            Use AI to help you set up training projects across multiple locations.
            Upload roster files, configure tracks, and create Zoom rooms automatically.
          </p>
          <ul className={styles.featureList}>
            <li>📋 Parse CSV, Excel, or JSON roster files</li>
            <li>📅 Generate optimized training schedules</li>
            <li>📍 Configure multiple locations with tracks</li>
            <li>🎥 Create Zoom rooms automatically</li>
            <li>👥 Assign instructors and students</li>
          </ul>
          <Button
            variant="primary"
            onClick={startSession}
            disabled={isStarting}
          >
            {isStarting ? 'Starting...' : 'Start Project Builder'}
          </Button>
        </div>
      )}

      {/* Chat interface */}
      {session && (
        <>
          {/* Messages */}
          <div className={styles.messagesContainer}>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${styles[message.role]}`}
              >
                <div className={styles.messageHeader}>
                  <span className={styles.messageRole}>
                    {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                  </span>
                  <span className={styles.messageTime}>
                    {formatTime(message.timestamp)}
                  </span>
                </div>

                {/* Message content with markdown-like formatting */}
                <div className={styles.messageContent}>
                  {message.content.split('\n').map((line, idx) => (
                    <p key={idx}>{formatMessageLine(line)}</p>
                  ))}
                </div>

                {/* File upload result */}
                {message.metadata?.fileUpload && (
                  <FileUploadCard result={message.metadata.fileUpload} />
                )}

                {/* Schedule proposal */}
                {message.metadata?.scheduleProposal && (
                  <ScheduleProposalCard
                    proposal={message.metadata.scheduleProposal}
                    onEdit={() => setEditingSchedule(message.metadata!.scheduleProposal!)}
                  />
                )}

                {/* Creation progress */}
                {message.metadata?.creationProgress && (
                  <CreationProgressCard progress={message.metadata.creationProgress} />
                )}

                {/* Action buttons */}
                {message.metadata?.actions && message.metadata.actions.length > 0 && (
                  <div className={styles.actionButtons}>
                    {message.metadata.actions.map((action) => (
                      <Button
                        key={action.id}
                        variant={action.variant || 'secondary'}
                        size="small"
                        onClick={() => handleAction(action.action)}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className={`${styles.message} ${styles.assistant}`}>
                <div className={styles.loadingIndicator}>
                  <span className={styles.loadingDot}></span>
                  <span className={styles.loadingDot}></span>
                  <span className={styles.loadingDot}></span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* File upload area */}
          {selectedFile && (
            <div className={styles.fileUploadArea}>
              <span className={styles.fileName}>{selectedFile.name}</span>
              <div className={styles.fileActions}>
                <Button
                  variant="primary"
                  size="small"
                  onClick={handleFileUpload}
                  disabled={isUploading}
                >
                  {isUploading ? 'Uploading...' : 'Upload'}
                </Button>
                <Button
                  variant="secondary"
                  size="small"
                  onClick={() => setSelectedFile(null)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Input area */}
          <div className={styles.inputContainer}>
            <input
              type="file"
              ref={fileInputRef}
              className={styles.hiddenFileInput}
              accept=".csv,.xlsx,.xls,.json"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
            <button
              className={styles.attachBtn}
              onClick={() => fileInputRef.current?.click()}
              title="Attach roster file"
              aria-label="Attach roster file"
            >
              📎
            </button>
            <textarea
              ref={inputRef}
              className={styles.messageInput}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your training program... (Ctrl+Enter to send)"
              rows={2}
              disabled={isLoading || session.state === 'CREATING'}
            />
            <Button
              variant="primary"
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || session.state === 'CREATING'}
            >
              Send
            </Button>
          </div>
        </>
      )}

      {/* Schedule editor modal */}
      {editingSchedule && (
        <ScheduleEditorModal
          proposal={editingSchedule}
          onSave={(updated) => {
            // Send updated schedule back to AI
            setInputMessage(`Updated schedule: ${JSON.stringify(updated)}`);
            setEditingSchedule(null);
          }}
          onClose={() => setEditingSchedule(null)}
        />
      )}
    </div>
  );
};

/**
 * Format message line with basic markdown
 */
const formatMessageLine = (line: string): React.ReactNode => {
  // Bold text
  let formatted = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Return as HTML
  return <span dangerouslySetInnerHTML={{ __html: formatted }} />;
};

/**
 * File upload result card
 */
const FileUploadCard: React.FC<{ result: FileUploadResult }> = ({ result }) => (
  <div className={styles.card}>
    <div className={styles.cardHeader}>
      <span className={styles.cardIcon}>📄</span>
      <span className={styles.cardTitle}>{result.filename}</span>
    </div>
    <div className={styles.cardBody}>
      <div className={styles.stat}>
        <span className={styles.statLabel}>Records</span>
        <span className={styles.statValue}>{result.recordCount}</span>
      </div>
      <div className={styles.stat}>
        <span className={styles.statLabel}>Valid</span>
        <span className={styles.statValue} style={{ color: '#10b981' }}>
          {result.validRecords}
        </span>
      </div>
      {result.errors && result.errors.length > 0 && (
        <div className={styles.stat}>
          <span className={styles.statLabel}>Errors</span>
          <span className={styles.statValue} style={{ color: '#ef4444' }}>
            {result.errors.length}
          </span>
        </div>
      )}
    </div>
    {result.errors && result.errors.length > 0 && (
      <div className={styles.errorList}>
        {result.errors.slice(0, 3).map((error, idx) => (
          <div key={idx} className={styles.errorItem}>
            ⚠️ {error}
          </div>
        ))}
        {result.errors.length > 3 && (
          <div className={styles.moreErrors}>
            +{result.errors.length - 3} more errors
          </div>
        )}
      </div>
    )}
  </div>
);

/**
 * Schedule proposal card
 */
const ScheduleProposalCard: React.FC<{
  proposal: ScheduleProposal;
  onEdit: () => void;
}> = ({ proposal, onEdit }) => (
  <div className={styles.card}>
    <div className={styles.cardHeader}>
      <span className={styles.cardIcon}>📅</span>
      <span className={styles.cardTitle}>Schedule Proposal</span>
      <button className={styles.editBtn} onClick={onEdit}>
        Edit
      </button>
    </div>
    <div className={styles.cardBody}>
      <div className={styles.scheduleStats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Sessions</span>
          <span className={styles.statValue}>{proposal.totalSessions}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Locations</span>
          <span className={styles.statValue}>{proposal.locations.length}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Tracks</span>
          <span className={styles.statValue}>{proposal.tracks.length}</span>
        </div>
      </div>
      <div className={styles.dateRange}>
        {proposal.dateRange.start} - {proposal.dateRange.end}
      </div>
      {proposal.conflicts && proposal.conflicts.length > 0 && (
        <div className={styles.conflictList}>
          {proposal.conflicts.map((conflict, idx) => (
            <div key={idx} className={styles.conflictItem}>
              ⚠️ {conflict}
            </div>
          ))}
        </div>
      )}
    </div>
  </div>
);

/**
 * Creation progress card
 */
const CreationProgressCard: React.FC<{ progress: CreationProgress }> = ({ progress }) => {
  const percentage = (progress.current / progress.total) * 100;

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.cardIcon}>🔄</span>
        <span className={styles.cardTitle}>{progress.phase}</span>
      </div>
      <div className={styles.cardBody}>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className={styles.progressText}>
          {progress.current} / {progress.total} - {progress.message}
        </div>
        <div className={styles.createdItems}>
          {progress.created.projects !== undefined && (
            <span className={styles.createdItem}>
              📁 {progress.created.projects} Projects
            </span>
          )}
          {progress.created.subProjects !== undefined && (
            <span className={styles.createdItem}>
              📍 {progress.created.subProjects} Locations
            </span>
          )}
          {progress.created.tracks !== undefined && (
            <span className={styles.createdItem}>
              🛤️ {progress.created.tracks} Tracks
            </span>
          )}
          {progress.created.zoomRooms !== undefined && (
            <span className={styles.createdItem}>
              🎥 {progress.created.zoomRooms} Zoom Rooms
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Schedule editor modal
 */
const ScheduleEditorModal: React.FC<{
  proposal: ScheduleProposal;
  onSave: (updated: ScheduleProposal) => void;
  onClose: () => void;
}> = ({ proposal, onSave, onClose }) => {
  const [sessions, setSessions] = useState(proposal.sessions);

  const handleSessionChange = (idx: number, field: keyof ScheduleSession, value: string) => {
    setSessions((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s))
    );
  };

  const handleSave = () => {
    onSave({
      ...proposal,
      sessions
    });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h3>Edit Schedule</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            ✕
          </button>
        </div>
        <div className={styles.modalBody}>
          <table className={styles.scheduleTable}>
            <thead>
              <tr>
                <th>Track</th>
                <th>Course</th>
                <th>Location</th>
                <th>Date</th>
                <th>Time</th>
                <th>Instructor</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session, idx) => (
                <tr key={session.id}>
                  <td>
                    <input
                      value={session.track}
                      onChange={(e) => handleSessionChange(idx, 'track', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      value={session.course}
                      onChange={(e) => handleSessionChange(idx, 'course', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      value={session.location}
                      onChange={(e) => handleSessionChange(idx, 'location', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="date"
                      value={session.date}
                      onChange={(e) => handleSessionChange(idx, 'date', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="time"
                      value={session.time}
                      onChange={(e) => handleSessionChange(idx, 'time', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      value={session.instructor || ''}
                      onChange={(e) => handleSessionChange(idx, 'instructor', e.target.value)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className={styles.modalFooter}>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Apply Changes
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProjectBuilderChat;
