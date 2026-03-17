/**
 * TDD RED Phase: AI Assistant WebSocket Integration Tests
 *
 * BUSINESS PURPOSE:
 * Tests WebSocket integration with production AI assistant service.
 * Ensures real-time communication, authentication, and message handling.
 *
 * TECHNICAL IMPLEMENTATION:
 * Tests WebSocket connection, initialization, message sending/receiving,
 * typing indicators, error handling, and conversation management.
 */

const AIAssistant = require('../../../frontend/static/js/ai-assistant');

// Mock WebSocket
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = MockWebSocket.CONNECTING;
        this.onopen = null;
        this.onmessage = null;
        this.onerror = null;
        this.onclose = null;
        this.sentMessages = [];

        // Simulate connection opening
        setTimeout(() => {
            this.readyState = MockWebSocket.OPEN;
            if (this.onopen) {
                this.onopen(new Event('open'));
            }
        }, 10);
    }

    send(data) {
        if (this.readyState !== MockWebSocket.OPEN) {
            throw new Error('WebSocket is not open');
        }
        this.sentMessages.push(data);
    }

    close() {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onclose) {
            this.onclose(new Event('close'));
        }
    }

    // Simulate receiving message from server
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }

    // Simulate error
    simulateError(error) {
        if (this.onerror) {
            this.onerror(new ErrorEvent('error', { error }));
        }
    }

    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;
}

// Setup DOM and global WebSocket
function setupDOM() {
    document.body.innerHTML = '';

    const container = document.createElement('div');
    container.innerHTML = `
        <button id="aiAssistantBtn">AI</button>
        <div id="aiAssistantPanel"></div>
        <input id="aiInput" type="text" />
        <button id="aiSendBtn">Send</button>
        <button id="closeAIAssistant">Close</button>
        <div id="aiMessages"></div>
    `;
    document.body.appendChild(container);

    // Mock localStorage
    global.localStorage = {
        store: {},
        getItem(key) {
            return this.store[key] || null;
        },
        setItem(key, value) {
            this.store[key] = value;
        },
        clear() {
            this.store = {};
        }
    };

    // Set up auth data
    localStorage.setItem('authToken', 'test-token-123');
    localStorage.setItem('currentUser', JSON.stringify({
        id: 1,
        username: 'test_user',
        role: 'organization_admin',
        organization_id: 1
    }));

    return {
        button: document.getElementById('aiAssistantBtn'),
        panel: document.getElementById('aiAssistantPanel'),
        input: document.getElementById('aiInput'),
        sendBtn: document.getElementById('aiSendBtn'),
        closeBtn: document.getElementById('closeAIAssistant'),
        messages: document.getElementById('aiMessages')
    };
}

describe('AIAssistant WebSocket Integration', () => {
    let assistant;
    let elements;
    let mockWebSocket;

    beforeEach(() => {
        // Mock WebSocket globally
        global.WebSocket = MockWebSocket;

        elements = setupDOM();
        assistant = new AIAssistant({
            buttonId: 'aiAssistantBtn',
            panelId: 'aiAssistantPanel',
            inputId: 'aiInput',
            sendBtnId: 'aiSendBtn',
            closeBtnId: 'closeAIAssistant',
            messagesId: 'aiMessages',
            websocketUrl: 'wss://localhost:8011/ws/ai-assistant'
        });

        // Get reference to created WebSocket
        mockWebSocket = assistant.ws;
    });

    afterEach(() => {
        if (assistant && assistant.ws) {
            assistant.ws.close();
        }
        localStorage.clear();
    });

    describe('WebSocket Connection', () => {
        test('should create WebSocket connection on initialization', () => {
            expect(assistant.ws).toBeDefined();
            expect(assistant.ws.url).toBe('wss://localhost:8011/ws/ai-assistant');
        });

        test('should send initialization message when WebSocket opens', (done) => {
            setTimeout(() => {
                expect(mockWebSocket.sentMessages.length).toBeGreaterThan(0);

                const initMessage = JSON.parse(mockWebSocket.sentMessages[0]);
                expect(initMessage.type).toBe('init');
                expect(initMessage.user_context).toBeDefined();
                expect(initMessage.user_context.user_id).toBe(1);
                expect(initMessage.user_context.username).toBe('test_user');
                expect(initMessage.user_context.role).toBe('organization_admin');
                expect(initMessage.auth_token).toBe('test-token-123');
                done();
            }, 50);
        });

        test('should set conversationId when connected message received', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'connected',
                    conversation_id: 'conv-123-456'
                });

                expect(assistant.conversationId).toBe('conv-123-456');
                done();
            }, 50);
        });

        test('should handle connection errors gracefully', (done) => {
            setTimeout(() => {
                const error = new Error('Connection failed');
                mockWebSocket.simulateError(error);

                // Should still be functional
                expect(assistant).toBeDefined();
                done();
            }, 50);
        });
    });

    describe('Message Sending', () => {
        test('should send user message via WebSocket', (done) => {
            setTimeout(() => {
                // Clear init message
                mockWebSocket.sentMessages = [];

                elements.input.value = 'Create a project';
                assistant.sendMessage();

                expect(mockWebSocket.sentMessages.length).toBe(1);

                const message = JSON.parse(mockWebSocket.sentMessages[0]);
                expect(message.type).toBe('user_message');
                expect(message.content).toBe('Create a project');
                done();
            }, 50);
        });

        test('should add user message to UI before sending', (done) => {
            setTimeout(() => {
                elements.input.value = 'Test message';
                assistant.sendMessage();

                const userMessages = elements.messages.querySelectorAll('.user-message');
                expect(userMessages.length).toBeGreaterThan(0);
                done();
            }, 50);
        });

        test('should clear input after sending message', (done) => {
            setTimeout(() => {
                elements.input.value = 'Test message';
                assistant.sendMessage();

                expect(elements.input.value).toBe('');
                done();
            }, 50);
        });

        test('should not send empty messages', (done) => {
            setTimeout(() => {
                mockWebSocket.sentMessages = [];

                elements.input.value = '   ';
                assistant.sendMessage();

                expect(mockWebSocket.sentMessages.length).toBe(0);
                done();
            }, 50);
        });
    });

    describe('Message Receiving', () => {
        test('should display AI response when received', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'response',
                    content: 'I can help you create a project. What name would you like?'
                });

                setTimeout(() => {
                    const aiMessages = elements.messages.querySelectorAll('.ai-message');
                    expect(aiMessages.length).toBeGreaterThan(0);

                    const lastMessage = aiMessages[aiMessages.length - 1];
                    expect(lastMessage.textContent).toContain('I can help you create a project');
                    done();
                }, 10);
            }, 50);
        });

        test('should show thinking indicator when AI is processing', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'thinking'
                });

                const thinkingIndicator = document.getElementById('thinking-indicator');
                expect(thinkingIndicator).toBeDefined();
                expect(thinkingIndicator).not.toBeNull();
                done();
            }, 50);
        });

        test('should hide thinking indicator when response received', (done) => {
            setTimeout(() => {
                // Show thinking indicator
                mockWebSocket.simulateMessage({ type: 'thinking' });

                setTimeout(() => {
                    // Send response
                    mockWebSocket.simulateMessage({
                        type: 'response',
                        content: 'Here is your answer'
                    });

                    setTimeout(() => {
                        const thinkingIndicator = document.getElementById('thinking-indicator');
                        expect(thinkingIndicator).toBeNull();
                        done();
                    }, 10);
                }, 10);
            }, 50);
        });

        test('should display error messages', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'error',
                    content: 'An error occurred. Please try again.'
                });

                setTimeout(() => {
                    const errorMessages = elements.messages.querySelectorAll('.error-message');
                    expect(errorMessages.length).toBeGreaterThan(0);
                    done();
                }, 10);
            }, 50);
        });
    });

    describe('Function Execution', () => {
        test('should indicate when function is being executed', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'response',
                    content: '✓ Created project "Machine Learning"',
                    function_call: 'create_project',
                    action_success: true
                });

                setTimeout(() => {
                    const messages = elements.messages.querySelectorAll('.ai-message');
                    const lastMessage = messages[messages.length - 1];
                    expect(lastMessage.textContent).toContain('✓ Created project');
                    done();
                }, 10);
            }, 50);
        });

        test('should handle function execution failures', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'response',
                    content: '❌ Failed to create project: Insufficient permissions',
                    function_call: 'create_project',
                    action_success: false
                });

                setTimeout(() => {
                    const messages = elements.messages.querySelectorAll('.ai-message');
                    const lastMessage = messages[messages.length - 1];
                    expect(lastMessage.textContent).toContain('❌ Failed');
                    done();
                }, 10);
            }, 50);
        });
    });

    describe('Conversation History', () => {
        test('should clear conversation history', (done) => {
            setTimeout(() => {
                // Send a message
                elements.input.value = 'Test';
                assistant.sendMessage();

                // Clear history
                mockWebSocket.sentMessages = [];
                assistant.clearHistory();

                expect(mockWebSocket.sentMessages.length).toBe(1);
                const message = JSON.parse(mockWebSocket.sentMessages[0]);
                expect(message.type).toBe('clear_history');
                done();
            }, 50);
        });

        test('should clear UI messages when history cleared', (done) => {
            setTimeout(() => {
                // Add some messages
                elements.input.value = 'Test 1';
                assistant.sendMessage();

                mockWebSocket.simulateMessage({
                    type: 'response',
                    content: 'Response 1'
                });

                setTimeout(() => {
                    // Clear history
                    assistant.clearHistory();

                    setTimeout(() => {
                        expect(elements.messages.children.length).toBe(0);
                        done();
                    }, 10);
                }, 10);
            }, 50);
        });
    });

    describe('WebSocket Reconnection', () => {
        test('should attempt to reconnect when connection is lost', (done) => {
            setTimeout(() => {
                const originalWs = assistant.ws;

                // Simulate connection loss
                mockWebSocket.close();

                setTimeout(() => {
                    // Should have created new WebSocket
                    expect(assistant.ws).toBeDefined();
                    // Should be different instance (reconnected)
                    expect(assistant.reconnectAttempts).toBeGreaterThan(0);
                    done();
                }, 100);
            }, 50);
        });

        test('should stop reconnecting after max attempts', (done) => {
            setTimeout(() => {
                assistant.maxReconnectAttempts = 3;

                // Simulate multiple connection failures
                for (let i = 0; i < 5; i++) {
                    mockWebSocket.close();
                }

                setTimeout(() => {
                    expect(assistant.reconnectAttempts).toBeLessThanOrEqual(3);
                    done();
                }, 200);
            }, 50);
        });
    });

    describe('Authentication', () => {
        test('should not connect without auth token', () => {
            localStorage.clear();

            const newAssistant = new AIAssistant({
                buttonId: 'aiAssistantBtn',
                panelId: 'aiAssistantPanel',
                inputId: 'aiInput',
                sendBtnId: 'aiSendBtn',
                closeBtnId: 'closeAIAssistant',
                messagesId: 'aiMessages'
            });

            expect(newAssistant.ws).toBeNull();
        });

        test('should include current page in user context', (done) => {
            setTimeout(() => {
                const initMessage = JSON.parse(mockWebSocket.sentMessages[0]);
                expect(initMessage.user_context.current_page).toBeDefined();
                done();
            }, 50);
        });
    });

    describe('Edge Cases', () => {
        test('should handle malformed server messages', (done) => {
            setTimeout(() => {
                // Send invalid JSON
                if (mockWebSocket.onmessage) {
                    mockWebSocket.onmessage({ data: '{invalid json}' });
                }

                // Should not crash
                expect(assistant).toBeDefined();
                done();
            }, 50);
        });

        test('should handle unknown message types', (done) => {
            setTimeout(() => {
                mockWebSocket.simulateMessage({
                    type: 'unknown_type',
                    content: 'Unknown message'
                });

                // Should not crash
                expect(assistant).toBeDefined();
                done();
            }, 50);
        });

        test('should handle rapid message sending', (done) => {
            setTimeout(() => {
                mockWebSocket.sentMessages = [];

                for (let i = 0; i < 10; i++) {
                    elements.input.value = `Message ${i}`;
                    assistant.sendMessage();
                }

                expect(mockWebSocket.sentMessages.length).toBe(10);
                done();
            }, 50);
        });
    });
});
