/**
 * Global AI Assistant Widget
 *
 * BUSINESS CONTEXT:
 * Floating AI assistant available across all dashboards and pages.
 * Provides contextual help based on current page and user role.
 * Uses the FULL CC AI Pipeline via WebSocket:
 *   NLP Preprocessing → Knowledge Graph → RAG → Hybrid LLM Router → LLM
 *
 * TECHNICAL IMPLEMENTATION:
 * - WebSocket connection to /ws/ai-assistant for full AI pipeline
 * - Floating widget that can be minimized/expanded
 * - Context-aware based on current route and user role
 * - Persists conversation in session storage
 * - Auto-reconnect on connection loss
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Button } from '../../atoms/Button';
import { useAuth } from '../../../hooks/useAuth';
import styles from './GlobalAIAssistant.module.css';

interface Position {
  x: number;
  y: number;
}

interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  functionCall?: string;
  actionSuccess?: boolean;
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
 * Global AI Assistant Component
 *
 * WHY WebSocket:
 * - Uses the full CC AI Pipeline (NLP → KG → RAG → LLM)
 * - Real-time "thinking" indicators during processing
 * - Supports function calling for platform actions
 * - More efficient for conversational AI
 */
export const GlobalAIAssistant: React.FC = () => {
  const { user, isAuthenticated, token } = useAuth();
  const location = useLocation();

  // Widget state
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Drag state
  const [position, setPosition] = useState<Position | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState<Position>({ x: 0, y: 0 });

  // Chat state
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // WebSocket state
  const wsRef = useRef<WebSocket | null>(null);
  const conversationIdRef = useRef<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const widgetRef = useRef<HTMLDivElement>(null);

  /**
   * Get current page context for AI
   */
  const getPageContext = useCallback((): string => {
    const path = location.pathname;

    if (path.includes('/dashboard/student')) return 'student dashboard';
    if (path.includes('/dashboard/instructor')) return 'instructor dashboard';
    if (path.includes('/dashboard/org-admin')) return 'organization admin dashboard';
    if (path.includes('/dashboard/site-admin')) return 'site admin dashboard';
    if (path.includes('/courses')) return 'courses page';
    if (path.includes('/labs')) return 'lab environment';
    if (path.includes('/quizzes')) return 'quizzes page';
    if (path.includes('/analytics')) return 'analytics dashboard';
    if (path.includes('/organization')) return 'organization management';
    if (path.includes('/instructor')) return 'instructor tools';

    return 'Course Creator Platform';
  }, [location.pathname]);

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

    console.log('[AI Assistant] Connecting to WebSocket:', wsUrl);
    setConnectionError(null);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[AI Assistant] WebSocket connected');
        reconnectAttemptsRef.current = 0;

        // Send initialization message with user context
        const initMessage = {
          type: 'init',
          user_context: {
            user_id: user?.id || 'anonymous',
            username: user?.username || 'User',
            role: user?.role || 'guest',
            organization_id: user?.organizationId,
            current_page: getPageContext()
          },
          auth_token: token || ''
        };

        ws.send(JSON.stringify(initMessage));
      };

      ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          console.log('[AI Assistant] Received:', data.type);

          switch (data.type) {
            case 'connected':
              setIsConnected(true);
              conversationIdRef.current = data.conversation_id || null;
              console.log('[AI Assistant] Conversation started:', data.conversation_id);
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
                  timestamp: new Date(),
                  functionCall: data.function_call,
                  actionSuccess: data.action_success
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
          console.error('[AI Assistant] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[AI Assistant] WebSocket error:', error);
        setConnectionError('Connection error. Retrying...');
      };

      ws.onclose = (event) => {
        console.log('[AI Assistant] WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        conversationIdRef.current = null;

        // Attempt reconnection if widget is still open
        if (isOpen && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          console.log(`[AI Assistant] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setConnectionError('Unable to connect. Please refresh the page.');
        }
      };
    } catch (e) {
      console.error('[AI Assistant] Failed to create WebSocket:', e);
      setConnectionError('Failed to connect to AI assistant.');
    }
  }, [user, token, getPageContext, isOpen]);

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

  // Connect when widget opens, disconnect when it closes
  useEffect(() => {
    if (isOpen && isAuthenticated) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isOpen, isAuthenticated, connectWebSocket, disconnectWebSocket]);

  // Update page context when location changes
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && isConnected) {
      // Could send a context update message here if needed
      console.log('[AI Assistant] Page context changed:', getPageContext());
    }
  }, [location.pathname, isConnected, getPageContext]);

  // Load messages from session storage on mount
  useEffect(() => {
    const savedMessages = sessionStorage.getItem('ai_assistant_messages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        })));
      } catch (e) {
        console.error('Failed to parse saved messages:', e);
      }
    }
  }, []);

  // Save messages to session storage on update
  useEffect(() => {
    if (messages.length > 0) {
      sessionStorage.setItem('ai_assistant_messages', JSON.stringify(messages));
    }
  }, [messages]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isMinimized]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen && !isMinimized && isConnected) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, isMinimized, isConnected]);

  // Handle Escape key to close the widget
  useEffect(() => {
    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isOpen]);

  /**
   * Handle drag start on header
   */
  const handleDragStart = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest('button')) return;

    e.preventDefault();
    setIsDragging(true);

    const widget = widgetRef.current;
    if (widget) {
      const rect = widget.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      if (!position) {
        setPosition({ x: rect.left, y: rect.top });
      }
    }
  }, [position]);

  /**
   * Handle drag move
   */
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;

      const widget = widgetRef.current;
      if (widget) {
        const rect = widget.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;

        setPosition({
          x: Math.max(0, Math.min(newX, maxX)),
          y: Math.max(0, Math.min(newY, maxY))
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  /**
   * Send message via WebSocket
   */
  const sendMessage = useCallback(() => {
    if (!inputMessage.trim() || isLoading) return;

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('[AI Assistant] WebSocket not connected');
      setConnectionError('Not connected. Reconnecting...');
      connectWebSocket();
      return;
    }

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Send message via WebSocket
    const wsMessage = {
      type: 'user_message',
      content: userMessage.content
    };

    wsRef.current.send(JSON.stringify(wsMessage));
    console.log('[AI Assistant] Sent message:', userMessage.content.substring(0, 50));
  }, [inputMessage, isLoading, connectWebSocket]);

  /**
   * Handle keyboard shortcuts
   * Enter: Send message
   * Shift+Enter: Add new line
   * Ctrl/Cmd+Enter: Also send message (for consistency)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /**
   * Quick action prompts
   */
  const quickActions = [
    { label: 'Help with this page', prompt: `What can I do on this ${getPageContext()}?` },
    { label: 'How to create a course', prompt: 'How do I create a new training course?' },
    { label: 'Explain my role', prompt: `What are my capabilities as a ${user?.role || 'user'}?` },
    { label: 'Get started guide', prompt: 'How do I get started with the Course Creator Platform?' }
  ];

  /**
   * Handle quick action click
   */
  const handleQuickAction = (prompt: string) => {
    setInputMessage(prompt);
    setTimeout(() => sendMessage(), 100);
  };

  /**
   * Clear conversation via WebSocket
   */
  const clearConversation = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear_history' }));
    }
    setMessages([]);
    sessionStorage.removeItem('ai_assistant_messages');
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

  // Don't render for unauthenticated users
  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          className={styles.floatingButton}
          onClick={() => setIsOpen(true)}
          aria-label="Open AI Assistant"
          data-testid="ai-assistant-button"
        >
          <span className={styles.buttonIcon}>🤖</span>
          <span className={styles.buttonLabel}>AI Help</span>
        </button>
      )}

      {/* Chat Widget */}
      {isOpen && (
        <div
          ref={widgetRef}
          className={`${styles.chatWidget} ${isMinimized ? styles.minimized : ''} ${isDragging ? styles.dragging : ''}`}
          style={position ? {
            left: position.x,
            top: position.y,
            right: 'auto',
            bottom: 'auto'
          } : undefined}
        >
          {/* Header - Draggable */}
          <div
            className={styles.header}
            onMouseDown={handleDragStart}
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
          >
            <div className={styles.headerTitle}>
              <span className={styles.aiIcon}>🤖</span>
              <span>AI Assistant</span>
              {isConnected && <span className={styles.connectedDot} title="Connected to AI Pipeline">●</span>}
            </div>
            <div className={styles.headerActions}>
              <button
                className={styles.headerBtn}
                onClick={clearConversation}
                title="Clear conversation"
              >
                🗑️
              </button>
              <button
                className={styles.headerBtn}
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? 'Expand' : 'Minimize'}
              >
                {isMinimized ? '⬆️' : '⬇️'}
              </button>
              <button
                className={styles.headerBtn}
                onClick={() => setIsOpen(false)}
                title="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Connection Status */}
              {connectionError && (
                <div className={styles.connectionError}>
                  {connectionError}
                </div>
              )}

              {/* Connecting State */}
              {!isConnected && !connectionError && (
                <div className={styles.connecting}>
                  <span className={styles.connectingSpinner}></span>
                  Connecting to AI Pipeline...
                </div>
              )}

              {/* Messages */}
              <div className={styles.messagesContainer}>
                {messages.length === 0 && isConnected && (
                  <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>💬</div>
                    <p className={styles.emptyTitle}>Hi! I'm your AI Assistant</p>
                    <p className={styles.emptyHint}>
                      I use the full AI pipeline with NLP, Knowledge Graph, and RAG to provide intelligent, context-aware responses.
                    </p>

                    {/* Quick Actions */}
                    <div className={styles.quickActions}>
                      {quickActions.map((action, idx) => (
                        <button
                          key={idx}
                          className={styles.quickActionBtn}
                          onClick={() => handleQuickAction(action.prompt)}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
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
                    {message.functionCall && (
                      <div className={styles.functionCallBadge}>
                        {message.actionSuccess ? '✅' : '❌'} Action: {message.functionCall}
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
                  className={styles.messageInput}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isConnected ? "Ask me anything... (Enter to send, Shift+Enter for new line)" : "Connecting..."}
                  rows={2}
                  disabled={isLoading || !isConnected}
                />
                <Button
                  variant="primary"
                  size="small"
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading || !isConnected}
                >
                  Send
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default GlobalAIAssistant;
