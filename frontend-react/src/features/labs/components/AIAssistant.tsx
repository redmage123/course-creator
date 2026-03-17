/**
 * AI Assistant Component for Lab Environment
 *
 * BUSINESS CONTEXT:
 * Context-aware AI assistance specifically for the lab environment.
 * Uses the FULL CC AI Pipeline via WebSocket with lab-specific context:
 *   NLP Preprocessing → Knowledge Graph → RAG → Hybrid LLM Router → LLM
 *
 * FEATURES:
 * - WebSocket connection to /ws/ai-assistant (same pipeline as Global AI)
 * - Automatically includes code context (current file, code, errors)
 * - Quick actions: Explain Code, Debug Error, Improve Code, Get Hint
 * - Lab-specific prompts optimized for coding assistance
 *
 * @module features/labs/components/AIAssistant
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/atoms/Button';
import { useAuth } from '@/hooks/useAuth';
import styles from './AIAssistant.module.css';

export interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  context?: {
    file?: string;
    code?: string;
    error?: string;
  };
}

/**
 * Jupyter notebook context from useJupyterNotebook hook
 */
export interface JupyterNotebookContext {
  hasActiveNotebook: boolean;
  notebookName: string;
  notebookPath: string;
  totalCells: number;
  codeCells: number;
  kernelStatus: 'idle' | 'busy' | 'starting' | 'unknown';
  recentCodeCells: Array<{
    index: number;
    source: string;
    hasError: boolean;
    errorMessage?: string;
  }>;
  errorCells: Array<{
    index: number;
    source: string;
    hasError: boolean;
    errorMessage?: string;
  }>;
  hasErrors: boolean;
}

export interface AIAssistantProps {
  /** Current file being edited (LabFile object or filename string) */
  currentFile?: { name: string; path: string; language?: string } | string | null;
  /** Current code content in the editor */
  codeContent?: string;
  /** Terminal command history for context */
  terminalHistory?: Array<{ command: string; output: string }>;
  /** Last error from code execution */
  lastError?: string;
  /** Lab session ID for context */
  sessionId?: string;
  /** Course ID for context */
  courseId?: string;
  /** Jupyter notebook context (when Jupyter IDE is active) */
  jupyterContext?: JupyterNotebookContext | null;
  /** Function to get formatted Jupyter context for AI */
  getJupyterAIContext?: () => string;
}

/**
 * WebSocket message types from the AI Assistant service
 */
type WSMessageType = 'connected' | 'thinking' | 'response' | 'error' | 'history_cleared';

interface WSMessage {
  type: WSMessageType;
  conversation_id?: string;
  content?: string;
  function_call?: string;
  action_success?: boolean;
}

/**
 * Lab AI Assistant Component
 *
 * Uses WebSocket connection to the CC AI Pipeline with lab-specific context
 * for code explanation, debugging, and learning assistance.
 */
export const AIAssistant: React.FC<AIAssistantProps> = ({
  currentFile,
  codeContent = '',
  terminalHistory = [],
  lastError,
  sessionId,
  courseId,
  jupyterContext,
  getJupyterAIContext
}) => {
  const { user, token } = useAuth();

  // Chat state
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [includeContext, setIncludeContext] = useState(true);

  // WebSocket state
  const wsRef = useRef<WebSocket | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Get current file name from props
   */
  const getFileName = useCallback((): string | undefined => {
    if (!currentFile) return undefined;
    if (typeof currentFile === 'string') return currentFile;
    return currentFile.name || currentFile.path;
  }, [currentFile]);

  /**
   * Get current file language
   */
  const getFileLanguage = useCallback((): string | undefined => {
    if (!currentFile || typeof currentFile === 'string') return undefined;
    return currentFile.language;
  }, [currentFile]);

  /**
   * Get last terminal error from history
   */
  const getLastTerminalError = useCallback((): string | undefined => {
    if (lastError) return lastError;

    // Check terminal history for errors
    for (let i = terminalHistory.length - 1; i >= 0; i--) {
      const entry = terminalHistory[i];
      if (entry.output && (
        entry.output.toLowerCase().includes('error') ||
        entry.output.toLowerCase().includes('exception') ||
        entry.output.toLowerCase().includes('traceback')
      )) {
        return entry.output;
      }
    }
    return undefined;
  }, [lastError, terminalHistory]);

  /**
   * Connect to WebSocket
   */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ai-assistant`;

    console.log('[Lab AI Assistant] Connecting to WebSocket:', wsUrl);
    setConnectionError(null);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Lab AI Assistant] WebSocket connected');
        reconnectAttemptsRef.current = 0;

        // Send initialization message with lab context
        const initMessage = {
          type: 'init',
          user_context: {
            user_id: user?.id || 'anonymous',
            username: user?.username || 'User',
            role: user?.role || 'student',
            organization_id: user?.organizationId,
            current_page: 'lab environment',
            // Lab-specific context
            lab_context: {
              session_id: sessionId,
              course_id: courseId,
              current_file: getFileName(),
              file_language: getFileLanguage(),
              is_coding_session: true
            }
          },
          auth_token: token || ''
        };

        ws.send(JSON.stringify(initMessage));
      };

      ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          console.log('[Lab AI Assistant] Received:', data.type);

          switch (data.type) {
            case 'connected':
              setIsConnected(true);
              conversationIdRef.current = data.conversation_id || null;
              console.log('[Lab AI Assistant] Conversation started:', data.conversation_id);
              break;

            case 'thinking':
              setIsLoading(true);
              break;

            case 'response':
              setIsLoading(false);
              if (data.content) {
                const assistantMessage: AIMessage = {
                  id: `assistant-${Date.now()}`,
                  role: 'assistant',
                  content: data.content,
                  timestamp: new Date()
                };
                setMessages(prev => [...prev, assistantMessage]);
              }
              break;

            case 'error':
              setIsLoading(false);
              const errorMessage: AIMessage = {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: data.content || 'An error occurred. Please try again.',
                timestamp: new Date()
              };
              setMessages(prev => [...prev, errorMessage]);
              break;

            case 'history_cleared':
              setMessages([]);
              break;
          }
        } catch (e) {
          console.error('[Lab AI Assistant] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[Lab AI Assistant] WebSocket error:', error);
        setConnectionError('Connection error. Retrying...');
      };

      ws.onclose = (event) => {
        console.log('[Lab AI Assistant] WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        conversationIdRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          console.log(`[Lab AI Assistant] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
        } else {
          setConnectionError('Unable to connect. Please refresh the page.');
        }
      };
    } catch (e) {
      console.error('[Lab AI Assistant] Failed to create WebSocket:', e);
      setConnectionError('Failed to connect to AI assistant.');
    }
  }, [user, token, sessionId, courseId, getFileName, getFileLanguage]);

  /**
   * Disconnect WebSocket
   */
  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    conversationIdRef.current = null;
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, [connectWebSocket, disconnectWebSocket]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Check if Jupyter context is available
   */
  const hasJupyterContext = Boolean(jupyterContext?.hasActiveNotebook);

  /**
   * Send message via WebSocket with lab context
   */
  const sendMessage = useCallback((messageText?: string) => {
    const text = messageText || inputMessage.trim();
    if (!text || isLoading) return;

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('[Lab AI Assistant] WebSocket not connected');
      setConnectionError('Not connected. Reconnecting...');
      connectWebSocket();
      return;
    }

    // Build context if enabled - use Jupyter context when available
    const context = includeContext ? {
      file: hasJupyterContext ? jupyterContext?.notebookName : getFileName(),
      code: hasJupyterContext ? undefined : codeContent?.substring(0, 2000),
      error: getLastTerminalError(),
      jupyter: hasJupyterContext
    } : undefined;

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
      context
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageText) setInputMessage('');
    setIsLoading(true);

    // Build message with lab context
    let fullMessage = text;

    if (includeContext) {
      const contextParts: string[] = [];

      // Use Jupyter context when available
      if (hasJupyterContext && getJupyterAIContext) {
        const jupyterContextStr = getJupyterAIContext();
        if (jupyterContextStr) {
          contextParts.push(jupyterContextStr);
        }
      } else {
        // Use VSCode/file context
        if (context?.file) {
          contextParts.push(`[Current file: ${context.file}]`);
        }

        if (context?.code) {
          contextParts.push(`[Code context:\n\`\`\`\n${context.code}\n\`\`\`]`);
        }
      }

      if (context?.error) {
        contextParts.push(`[Error output:\n${context.error}]`);
      }

      if (contextParts.length > 0) {
        fullMessage = `${text}\n\n--- Lab Context ---\n${contextParts.join('\n')}`;
      }
    }

    // Send message via WebSocket
    const wsMessage = {
      type: 'user_message',
      content: fullMessage
    };

    wsRef.current.send(JSON.stringify(wsMessage));
    console.log('[Lab AI Assistant] Sent message with context');
  }, [inputMessage, isLoading, includeContext, codeContent, getFileName, getLastTerminalError, connectWebSocket, hasJupyterContext, jupyterContext, getJupyterAIContext]);

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
   * Quick action buttons for lab assistance
   * Includes Jupyter-specific actions when notebook is active
   */
  const quickActions = hasJupyterContext ? [
    {
      id: 'explain-cell',
      label: 'Explain Cell',
      icon: '📖',
      message: 'Can you explain what the code in my current notebook cells does?',
      requiresCode: false
    },
    {
      id: 'debug-notebook',
      label: 'Debug Notebook',
      icon: '🐛',
      message: 'Help me debug the errors in my Jupyter notebook. What is causing them and how can I fix them?',
      requiresError: true
    },
    {
      id: 'next-step',
      label: 'Next Step',
      icon: '➡️',
      message: 'Based on my notebook so far, what should I do next?',
      requiresCode: false
    },
    {
      id: 'hint',
      label: 'Get Hint',
      icon: '💡',
      message: 'Can you give me a hint for solving this exercise without giving away the full solution?',
      requiresCode: false
    }
  ] : [
    {
      id: 'explain-code',
      label: 'Explain Code',
      icon: '📖',
      message: 'Can you explain what this code does step by step?',
      requiresCode: true
    },
    {
      id: 'debug-error',
      label: 'Debug Error',
      icon: '🐛',
      message: 'Help me debug this error. What is causing it and how can I fix it?',
      requiresError: true
    },
    {
      id: 'improve-code',
      label: 'Improve Code',
      icon: '✨',
      message: 'How can I improve this code? Are there any best practices I should follow?',
      requiresCode: true
    },
    {
      id: 'hint',
      label: 'Get Hint',
      icon: '💡',
      message: 'Can you give me a hint for solving this exercise without giving away the full solution?',
      requiresCode: false
    }
  ];

  /**
   * Handle quick action click
   */
  const handleQuickAction = (action: typeof quickActions[0]) => {
    sendMessage(action.message);
  };

  /**
   * Clear conversation
   */
  const clearConversation = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear_history' }));
    }
    setMessages([]);
  }, []);

  /**
   * Format timestamp
   */
  const formatTime = (date: Date): string => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Check for code availability - from VSCode or Jupyter
  const hasCode = hasJupyterContext
    ? Boolean(jupyterContext?.codeCells && jupyterContext.codeCells > 0)
    : Boolean(codeContent);

  // Check for errors - from terminal or Jupyter notebook
  const hasError = hasJupyterContext
    ? Boolean(jupyterContext?.hasErrors)
    : Boolean(getLastTerminalError());

  return (
    <div className={styles.aiAssistant} id="ai-assistant">
      <div className={styles.assistantHeader}>
        <div className={styles.headerTitle}>
          <span className={styles.aiIcon}>🤖</span>
          <h3>AI Assistant</h3>
          {isConnected && <span className={styles.connectedDot} title="Connected to AI Pipeline">●</span>}
        </div>
        <div className={styles.headerActions}>
          <button
            className={styles.clearBtn}
            onClick={clearConversation}
            title="Clear conversation"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Context Toggle */}
      <div className={styles.contextToggle}>
        <input
          type="checkbox"
          id="include-context"
          checked={includeContext}
          onChange={(e) => setIncludeContext(e.target.checked)}
          className={styles.checkbox}
        />
        <label htmlFor="include-context" className={styles.checkboxLabel}>
          Include code context
        </label>
        {includeContext && (hasCode || hasJupyterContext) && (
          <span className={styles.contextIndicator} title={hasJupyterContext ? "Notebook context will be included" : "Code will be included"}>
            {hasJupyterContext ? '📓' : '📄'} {hasJupyterContext ? jupyterContext?.notebookName : getFileName() || 'code'}
          </span>
        )}
      </div>

      {/* Connection Status */}
      {connectionError && (
        <div className={styles.connectionError}>
          {connectionError}
        </div>
      )}

      {!isConnected && !connectionError && (
        <div className={styles.connecting}>
          <span className={styles.connectingSpinner}></span>
          Connecting to AI Pipeline...
        </div>
      )}

      {/* Quick Actions */}
      {isConnected && (
        <div className={styles.quickActions}>
          {quickActions.map(action => (
            <button
              key={action.id}
              className={styles.quickActionBtn}
              onClick={() => handleQuickAction(action)}
              disabled={
                isLoading ||
                (action.requiresCode && !hasCode) ||
                (action.requiresError && !hasError)
              }
              title={
                action.requiresCode && !hasCode
                  ? 'Requires code in editor'
                  : action.requiresError && !hasError
                  ? 'No error detected'
                  : action.label
              }
            >
              <span className={styles.quickActionIcon}>{action.icon}</span>
              <span className={styles.quickActionLabel}>{action.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className={styles.messagesContainer}>
        {messages.length === 0 && isConnected && (
          <div className={styles.emptyState}>
            <span className={styles.emptyIcon}>💬</span>
            <p>Ask me anything about your code!</p>
            <p className={styles.emptyHint}>
              I can help explain concepts, debug errors, and provide coding tips.
              {includeContext && ' Your code context will be automatically included.'}
            </p>
          </div>
        )}

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
            <div className={styles.messageContent}>
              {message.content}
            </div>
            {message.context && (
              <div className={styles.messageContext}>
                {message.context.file && (
                  <span className={styles.contextTag}>📄 {message.context.file}</span>
                )}
                {message.context.error && (
                  <span className={styles.contextTag}>❌ Error context included</span>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className={`${styles.message} ${styles.assistant}`}>
            <div className={styles.messageHeader}>
              <span className={styles.messageRole}>🤖 Assistant</span>
            </div>
            <div className={styles.loadingIndicator}>
              <span className={styles.loadingDot}></span>
              <span className={styles.loadingDot}></span>
              <span className={styles.loadingDot}></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className={styles.inputContainer}>
        <textarea
          ref={inputRef}
          id="ai-message-input"
          className={styles.messageInput}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isConnected ? "Ask about your code... (Ctrl+Enter to send)" : "Connecting..."}
          rows={3}
          disabled={isLoading || !isConnected}
        />
        <Button
          id="send-ai-message-btn"
          variant="primary"
          size="small"
          onClick={() => sendMessage()}
          disabled={!inputMessage.trim() || isLoading || !isConnected}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default AIAssistant;
