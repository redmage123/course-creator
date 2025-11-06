/**
 * AI Assistant Module - Production WebSocket Implementation
 *
 * BUSINESS PURPOSE:
 * Provides natural language interface for administrative tasks using
 * production AI service with LLM, RAG, and function calling capabilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * WebSocket client connecting to AI Assistant Service (port 8011).
 * Real-time bidirectional communication with typing indicators,
 * conversation history, and function execution notifications.
 */

/**
 * AIAssistant class - Production WebSocket client
 */
class AIAssistant {
    /**
     * Initialize AI Assistant
     * @param {Object} config - Configuration object
     * @param {string} config.buttonId - ID of the floating button element
     * @param {string} config.panelId - ID of the panel element
     * @param {string} config.inputId - ID of the input field
     * @param {string} config.sendBtnId - ID of the send button
     * @param {string} config.closeBtnId - ID of the close button
     * @param {string} config.messagesId - ID of the messages container
     * @param {string} config.websocketUrl - WebSocket URL (default: wss://localhost:8011/ws/ai-assistant)
     */
    constructor(config) {
        this.config = {
            websocketUrl: 'wss://localhost:8011/ws/ai-assistant',
            maxReconnectAttempts: 5,
            reconnectDelay: 2000,
            ...config
        };

        this.elements = {
            button: document.getElementById(config.buttonId),
            panel: document.getElementById(config.panelId),
            input: document.getElementById(config.inputId),
            sendBtn: document.getElementById(config.sendBtnId),
            closeBtn: document.getElementById(config.closeBtnId),
            messages: document.getElementById(config.messagesId)
        };

        this.isOpen = false;
        this.ws = null;
        this.conversationId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = config.maxReconnectAttempts || 5;

        this._validateElements();
        this._attachEventListeners();
        this._connectWebSocket();
    }

    /**
     * Validate required DOM elements exist
     */
    _validateElements() {
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                throw new Error(`Required element not found: ${key}`);
            }
        }
    }

    /**
     * Attach event listeners to UI elements
     */
    _attachEventListeners() {
        this.elements.button.addEventListener('click', () => this.open());
        this.elements.closeBtn.addEventListener('click', () => this.close());
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    /**
     * Connect to WebSocket AI Assistant service
     */
    _connectWebSocket() {
        // Get authentication data
        const authToken = localStorage.getItem('authToken');
        const currentUserJson = localStorage.getItem('currentUser');

        if (!authToken) {
            console.warn('No auth token found. AI assistant disabled.');
            this.ws = null;
            return;
        }

        const currentUser = currentUserJson ? JSON.parse(currentUserJson) : {};

        try {
            // Create WebSocket connection
            this.ws = new WebSocket(this.config.websocketUrl);

            // Connection opened
            this.ws.onopen = () => {
                console.log('AI Assistant WebSocket connected');
                this.reconnectAttempts = 0;

                // Send initialization message
                const initMessage = {
                    type: 'init',
                    user_context: {
                        user_id: currentUser.id || 0,
                        username: currentUser.username || 'Unknown',
                        role: currentUser.role || 'student',
                        organization_id: currentUser.organization_id || null,
                        current_page: window.location.pathname
                    },
                    auth_token: authToken
                };

                this.ws.send(JSON.stringify(initMessage));
            };

            // Handle incoming messages
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._handleServerMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            // Handle errors
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            // Handle connection close
            this.ws.onclose = () => {
                console.log('WebSocket connection closed');
                this._attemptReconnect();
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.ws = null;
        }
    }

    /**
     * Attempt to reconnect WebSocket
     */
    _attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);

            setTimeout(() => {
                this._connectWebSocket();
            }, this.config.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached. AI assistant unavailable.');
            this._showConnectionError();
        }
    }

    /**
     * Handle messages from server
     * @param {Object} data - Parsed message data
     */
    _handleServerMessage(data) {
        switch (data.type) {
            case 'connected':
                this.conversationId = data.conversation_id;
                console.log('Conversation started:', this.conversationId);
                break;

            case 'thinking':
                this._showThinkingIndicator();
                break;

            case 'response':
                this._hideThinkingIndicator();
                this.addMessage(data.content, false);

                // Show function execution result if applicable
                if (data.function_call && data.action_success !== undefined) {
                    const status = data.action_success ? '✅' : '❌';
                    console.log(`${status} Function executed: ${data.function_call}`);
                }
                break;

            case 'error':
                this._hideThinkingIndicator();
                this._showError(data.content || 'An error occurred. Please try again.');
                break;

            case 'history_cleared':
                this._clearUIMessages();
                break;

            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    /**
     * Show thinking indicator
     */
    _showThinkingIndicator() {
        // Remove existing indicator if present
        this._hideThinkingIndicator();

        const indicator = document.createElement('div');
        indicator.className = 'ai-message thinking-indicator';
        indicator.id = 'thinking-indicator';
        indicator.innerHTML = `
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
            <span class="thinking-text">AI is thinking...</span>
        `;

        this.elements.messages.appendChild(indicator);
        this._scrollToBottom();
    }

    /**
     * Hide thinking indicator
     */
    _hideThinkingIndicator() {
        const indicator = document.getElementById('thinking-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Show error message
     * @param {string} errorText - Error message to display
     */
    _showError(errorText) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = errorText;

        this.elements.messages.appendChild(errorDiv);
        this._scrollToBottom();
    }

    /**
     * Show connection error in UI
     */
    _showConnectionError() {
        this._showError(
            '⚠️ Unable to connect to AI assistant. Please check your connection and try again.'
        );
    }

    /**
     * Open AI assistant panel
     */
    open() {
        this.isOpen = true;
        this.elements.panel.classList.add('open');
        this.elements.input.focus();
    }

    /**
     * Close AI assistant panel
     */
    close() {
        this.isOpen = false;
        this.elements.panel.classList.remove('open');
    }

    /**
     * Send user message to AI assistant
     */
    sendMessage() {
        const message = this.elements.input.value.trim();

        if (!message) {
            return;
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this._showError('Not connected to AI assistant. Please try again later.');
            return;
        }

        // Add user message to UI
        this.addMessage(message, true);

        // Clear input
        this.elements.input.value = '';

        // Send to WebSocket
        try {
            const messageData = {
                type: 'user_message',
                content: message
            };

            this.ws.send(JSON.stringify(messageData));
        } catch (error) {
            console.error('Failed to send message:', error);
            this._showError('Failed to send message. Please try again.');
        }
    }

    /**
     * Add message to conversation display
     * @param {string} content - Message content
     * @param {boolean} isUser - Whether message is from user (true) or AI (false)
     */
    addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'ai-message';

        // Escape HTML to prevent XSS
        const escapedContent = this._escapeHtml(content);

        // Format message with line breaks
        messageDiv.innerHTML = escapedContent.replace(/\n/g, '<br>');

        this.elements.messages.appendChild(messageDiv);
        this._scrollToBottom();
    }

    /**
     * Escape HTML to prevent XSS attacks
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Scroll messages container to bottom
     */
    _scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    /**
     * Clear conversation history
     */
    clearHistory() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this._clearUIMessages();
            return;
        }

        try {
            const clearMessage = {
                type: 'clear_history'
            };

            this.ws.send(JSON.stringify(clearMessage));
            this._clearUIMessages();
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    }

    /**
     * Clear all UI messages
     */
    _clearUIMessages() {
        this.elements.messages.innerHTML = '';
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Export for Node.js (testing)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIAssistant;
}
