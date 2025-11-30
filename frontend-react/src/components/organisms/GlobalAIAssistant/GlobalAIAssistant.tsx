/**
 * Global AI Assistant Widget
 *
 * BUSINESS CONTEXT:
 * Floating AI assistant available across all dashboards and pages.
 * Provides contextual help based on current page and user role.
 * Uses RAG (Retrieval Augmented Generation) for intelligent responses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Floating widget that can be minimized/expanded
 * - Context-aware based on current route and user role
 * - Connects to AI assistant backend service
 * - Persists conversation in session storage
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Button } from '../../atoms/Button';
import { useAuth } from '../../../hooks/useAuth';
import { apiClient } from '../../../services/apiClient';
import styles from './GlobalAIAssistant.module.css';

interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface AIAssistantResponse {
  response: string;
  sources?: string[];
}

/**
 * Global AI Assistant Component
 *
 * WHY THIS APPROACH:
 * - Floating widget for accessibility from any page
 * - Minimized state to not obstruct UI
 * - Context-aware responses based on current page
 * - Session persistence for conversation continuity
 */
export const GlobalAIAssistant: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  // Widget state
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Chat state
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
    if (isOpen && !isMinimized) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, isMinimized]);

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
   * Send message to AI backend
   */
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const context = {
        page: getPageContext(),
        role: user?.role || 'guest',
        organization: user?.organizationName
      };

      const response = await apiClient.post<AIAssistantResponse>(
        '/api/v1/ai-assistant/chat',
        {
          message: userMessage.content,
          context,
          history: messages.slice(-10).map(m => ({
            role: m.role,
            content: m.content
          }))
        }
      );

      const assistantMessage: AIMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI Assistant error:', error);

      const errorMessage: AIMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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
   * Clear conversation
   */
  const clearConversation = () => {
    setMessages([]);
    sessionStorage.removeItem('ai_assistant_messages');
  };

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
        <div className={`${styles.chatWidget} ${isMinimized ? styles.minimized : ''}`}>
          {/* Header */}
          <div className={styles.header}>
            <div className={styles.headerTitle}>
              <span className={styles.aiIcon}>🤖</span>
              <span>AI Assistant</span>
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
              {/* Messages */}
              <div className={styles.messagesContainer}>
                {messages.length === 0 && (
                  <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>💬</div>
                    <p className={styles.emptyTitle}>Hi! I'm your AI Assistant</p>
                    <p className={styles.emptyHint}>
                      I can help you navigate the platform, answer questions about courses, and provide guidance.
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
                  placeholder="Ask me anything... (Ctrl+Enter to send)"
                  rows={2}
                  disabled={isLoading}
                />
                <Button
                  variant="primary"
                  size="small"
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
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
