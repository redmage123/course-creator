/**
 * AI Assistant Component
 *
 * Context-aware AI assistance for lab environment
 * Features:
 * - Chat interface with message history
 * - Code explanation and suggestions
 * - Error debugging help
 * - Learning hints and tips
 * - Auto-context from current file and errors
 *
 * @module features/labs/components/AIAssistant
 */

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/atoms/Button';
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

export interface AIAssistantProps {
  messages: AIMessage[];
  onSendMessage: (message: string, context?: any) => Promise<void>;
  isLoading?: boolean;
  currentFile?: string;
  currentCode?: string;
  lastError?: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({
  messages,
  onSendMessage,
  isLoading = false,
  currentFile,
  currentCode,
  lastError
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [includeContext, setIncludeContext] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const context = includeContext ? {
      file: currentFile,
      code: currentCode,
      error: lastError
    } : undefined;

    try {
      await onSendMessage(inputMessage, context);
      setInputMessage('');
      inputRef.current?.focus();
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter to send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Quick action buttons
  const quickActions = [
    {
      id: 'explain-code',
      label: 'Explain Code',
      icon: '📖',
      message: 'Can you explain what this code does?',
      requiresContext: true
    },
    {
      id: 'debug-error',
      label: 'Debug Error',
      icon: '🐛',
      message: 'Help me debug this error',
      requiresContext: true,
      requiresError: true
    },
    {
      id: 'improve-code',
      label: 'Improve Code',
      icon: '✨',
      message: 'How can I improve this code?',
      requiresContext: true
    },
    {
      id: 'hint',
      label: 'Get Hint',
      icon: '💡',
      message: 'Can you give me a hint for this exercise?',
      requiresContext: false
    }
  ];

  const handleQuickAction = (action: typeof quickActions[0]) => {
    const context = action.requiresContext ? {
      file: currentFile,
      code: currentCode,
      error: action.requiresError ? lastError : undefined
    } : undefined;

    onSendMessage(action.message, context);
  };

  // Format timestamp
  const formatTime = (date: Date): string => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <div className={styles.aiAssistant} id="ai-assistant">
      <div className={styles.assistantHeader}>
        <div className={styles.headerTitle}>
          <span className={styles.aiIcon}>🤖</span>
          <h3>AI Assistant</h3>
        </div>
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
        </div>
      </div>

      {/* Quick Actions */}
      <div className={styles.quickActions}>
        {quickActions.map(action => (
          <button
            key={action.id}
            className={styles.quickActionBtn}
            onClick={() => handleQuickAction(action)}
            disabled={
              isLoading ||
              (action.requiresContext && !currentCode) ||
              (action.requiresError && !lastError)
            }
            title={action.label}
          >
            <span className={styles.quickActionIcon}>{action.icon}</span>
            <span className={styles.quickActionLabel}>{action.label}</span>
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.emptyState}>
            <span className={styles.emptyIcon}>💬</span>
            <p>Ask me anything about your code!</p>
            <p className={styles.emptyHint}>
              I can help explain concepts, debug errors, and provide coding tips.
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
          placeholder="Ask a question... (Ctrl+Enter to send)"
          rows={3}
          disabled={isLoading}
        />
        <Button
          id="send-ai-message-btn"
          variant="primary"
          size="small"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || isLoading}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default AIAssistant;
