/**
 * Unit Tests for AI Assistant Module
 *
 * Tests all core functionality of the AIAssistant class:
 * - Initialization and validation
 * - Message handling
 * - Intent recognition
 * - Conversation history
 * - UI interactions
 */

const AIAssistant = require('../../../frontend/static/js/ai-assistant');

// Setup DOM elements
function setupDOM() {
    // Clear document body
    document.body.innerHTML = '';

    // Create container
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

    // Return references to elements
    return {
        button: document.getElementById('aiAssistantBtn'),
        panel: document.getElementById('aiAssistantPanel'),
        input: document.getElementById('aiInput'),
        sendBtn: document.getElementById('aiSendBtn'),
        closeBtn: document.getElementById('closeAIAssistant'),
        messages: document.getElementById('aiMessages')
    };
}

describe('AIAssistant', () => {
    let assistant;
    let elements;

    beforeEach(() => {
        elements = setupDOM();
        assistant = new AIAssistant({
            buttonId: 'aiAssistantBtn',
            panelId: 'aiAssistantPanel',
            inputId: 'aiInput',
            sendBtnId: 'aiSendBtn',
            closeBtnId: 'closeAIAssistant',
            messagesId: 'aiMessages',
            responseDelay: 0 // No delay for tests
        });
    });

    describe('Initialization', () => {
        test('should initialize with valid configuration', () => {
            expect(assistant).toBeDefined();
            expect(assistant.isOpen).toBe(false);
            expect(assistant.conversationHistory).toEqual([]);
        });

        test('should throw error if required element is missing', () => {
            // Save original
            const originalGetElementById = document.getElementById;

            // Mock to return null
            document.getElementById = () => null;

            expect(() => {
                new AIAssistant({
                    buttonId: 'missing',
                    panelId: 'aiAssistantPanel',
                    inputId: 'aiInput',
                    sendBtnId: 'aiSendBtn',
                    closeBtnId: 'closeAIAssistant',
                    messagesId: 'aiMessages'
                });
            }).toThrow('Required element');

            // Restore original
            document.getElementById = originalGetElementById;
        });

        test('should attach event listeners on initialization', () => {
            expect(elements.button.eventListeners.click).toBeDefined();
            expect(elements.closeBtn.eventListeners.click).toBeDefined();
            expect(elements.sendBtn.eventListeners.click).toBeDefined();
            expect(elements.input.eventListeners.keypress).toBeDefined();
        });
    });

    describe('Panel Operations', () => {
        test('should open panel when open() is called', () => {
            assistant.open();
            expect(assistant.isOpen).toBe(true);
            expect(elements.panel.classList.has('open')).toBe(true);
            expect(elements.input.focused).toBe(true);
        });

        test('should close panel when close() is called', () => {
            assistant.open();
            assistant.close();
            expect(assistant.isOpen).toBe(false);
            expect(elements.panel.classList.has('open')).toBe(false);
        });

        test('should open panel when button is clicked', () => {
            elements.button.trigger('click');
            expect(assistant.isOpen).toBe(true);
        });

        test('should close panel when close button is clicked', () => {
            assistant.open();
            elements.closeBtn.trigger('click');
            expect(assistant.isOpen).toBe(false);
        });
    });

    describe('Message Handling', () => {
        test('should add user message', () => {
            assistant.addMessage('Hello', true);
            expect(elements.messages.children.length).toBe(1);
        });

        test('should add AI message', () => {
            assistant.addMessage('Hi there!', false);
            expect(elements.messages.children.length).toBe(1);
        });

        test('should escape HTML in messages to prevent XSS', () => {
            const maliciousInput = '<script>alert("xss")</script>';
            const escaped = assistant._escapeHtml(maliciousInput);
            expect(escaped).not.toContain('<script>');
            expect(escaped).toContain('&lt;script&gt;');
        });

        test('should not send empty messages', () => {
            elements.input.value = '   ';
            assistant.sendMessage();
            expect(elements.messages.children.length).toBe(0);
        });

        test('should clear input after sending message', () => {
            elements.input.value = 'Test message';
            assistant.sendMessage();
            expect(elements.input.value).toBe('');
        });

        test('should send message when Enter key is pressed', () => {
            elements.input.value = 'Test message';
            elements.input.trigger('keypress', { key: 'Enter' });
            expect(elements.input.value).toBe('');
        });
    });

    describe('Intent Recognition', () => {
        test('should recognize create project intent', () => {
            const response = assistant.getAIResponse('create a new project');
            expect(response).toContain('project');
            expect(response.toLowerCase()).toContain('name');
        });

        test('should recognize create track intent', () => {
            const response = assistant.getAIResponse('I want to create a track');
            expect(response).toContain('track');
            expect(response.toLowerCase()).toContain('project');
        });

        test('should recognize detailed track creation request', () => {
            const response = assistant.getAIResponse(
                'Create an intermediate track called Machine Learning Basics for the Data Science project'
            );
            expect(response).toContain('created');
            expect(response).toContain('track');
        });

        test('should recognize onboard instructor intent', () => {
            const response = assistant.getAIResponse('add a new instructor');
            expect(response).toContain('instructor');
            expect(response.toLowerCase()).toContain('email');
        });

        test('should recognize create course intent', () => {
            const response = assistant.getAIResponse('create a course');
            expect(response).toContain('course');
        });

        test('should return default response for unknown intent', () => {
            const response = assistant.getAIResponse('what is the weather today');
            expect(response).toContain('help you with');
        });

        test('should match intents case-insensitively', () => {
            const response1 = assistant.getAIResponse('CREATE A PROJECT');
            const response2 = assistant.getAIResponse('create a project');
            expect(response1).toBe(response2);
        });
    });

    describe('Conversation History', () => {
        test('should track user messages in history', () => {
            elements.input.value = 'Create a project';
            assistant.sendMessage();
            expect(assistant.conversationHistory.length).toBeGreaterThan(0);
            expect(assistant.conversationHistory[0].role).toBe('user');
            expect(assistant.conversationHistory[0].content).toBe('Create a project');
        });

        test('should track AI responses in history', (done) => {
            elements.input.value = 'Create a project';
            assistant.sendMessage();

            setTimeout(() => {
                expect(assistant.conversationHistory.length).toBe(2);
                expect(assistant.conversationHistory[1].role).toBe('assistant');
                done();
            }, 10);
        });

        test('should return copy of history from getHistory()', () => {
            elements.input.value = 'Test';
            assistant.sendMessage();
            const history = assistant.getHistory();
            history.push({ role: 'user', content: 'Modified' });
            expect(assistant.conversationHistory.length).toBe(1);
        });

        test('should clear history when clearHistory() is called', () => {
            elements.input.value = 'Test';
            assistant.sendMessage();
            assistant.clearHistory();
            expect(assistant.conversationHistory.length).toBe(0);
        });
    });

    describe('Edge Cases', () => {
        test('should handle multiple rapid messages', () => {
            elements.input.value = 'Message 1';
            assistant.sendMessage();
            elements.input.value = 'Message 2';
            assistant.sendMessage();
            elements.input.value = 'Message 3';
            assistant.sendMessage();

            // Should have 3 user messages
            const userMessages = assistant.conversationHistory.filter(m => m.role === 'user');
            expect(userMessages.length).toBe(3);
        });

        test('should handle very long messages', () => {
            const longMessage = 'a'.repeat(1000);
            elements.input.value = longMessage;
            assistant.sendMessage();
            expect(assistant.conversationHistory[0].content).toBe(longMessage);
        });

        test('should handle special characters in messages', () => {
            const specialChars = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/";
            elements.input.value = specialChars;
            assistant.sendMessage();
            expect(assistant.conversationHistory[0].content).toBe(specialChars);
        });

        test('should trim whitespace from messages', () => {
            elements.input.value = '  Test message  ';
            assistant.sendMessage();
            expect(assistant.conversationHistory[0].content).toBe('Test message');
        });
    });

    describe('Response Delay', () => {
        test('should delay AI response by configured amount', (done) => {
            const delayedAssistant = new AIAssistant({
                buttonId: 'aiAssistantBtn',
                panelId: 'aiAssistantPanel',
                inputId: 'aiInput',
                sendBtnId: 'aiSendBtn',
                closeBtnId: 'closeAIAssistant',
                messagesId: 'aiMessages',
                responseDelay: 100
            });

            elements.input.value = 'Test';
            delayedAssistant.sendMessage();

            // Should only have user message immediately
            expect(delayedAssistant.conversationHistory.length).toBe(1);

            setTimeout(() => {
                // Should have both messages after delay
                expect(delayedAssistant.conversationHistory.length).toBe(2);
                done();
            }, 150);
        });
    });
});
