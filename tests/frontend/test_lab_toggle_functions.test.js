/**
 * TDD Test for Lab Toggle Functions
 * Tests that all toggle functions are properly defined and accessible
 */

describe('Lab Toggle Functions', () => {
    let mockDocument;
    let mockWindow;
    
    beforeEach(() => {
        // Mock DOM elements
        mockDocument = {
            getElementById: jest.fn(),
            querySelector: jest.fn(),
            querySelectorAll: jest.fn(() => []),
            createElement: jest.fn(() => ({
                className: '',
                textContent: '',
                classList: {
                    add: jest.fn(),
                    remove: jest.fn(),
                    toggle: jest.fn()
                },
                style: {},
                appendChild: jest.fn()
            }))
        };
        
        mockWindow = {
            location: {
                search: '?courseId=test-course&course=Test%20Course'
            }
        };
        
        // Set up global mocks
        global.document = mockDocument;
        global.window = mockWindow;
        global.console = {
            log: jest.fn(),
            error: jest.fn()
        };
    });

    test('togglePanel function should be defined and accessible', () => {
        // RED: Test fails initially
        expect(typeof window.togglePanel).toBe('function');
    });

    test('togglePanel should update panel states correctly', () => {
        // Mock panel states
        const mockPanelStates = {
            exercises: true,
            editor: true,
            terminal: true,
            assistant: true
        };
        
        // Mock DOM elements
        mockDocument.getElementById.mockReturnValue({
            classList: {
                toggle: jest.fn()
            }
        });
        
        mockDocument.querySelector.mockReturnValue({
            className: 'main-layout',
            style: {}
        });
        
        // RED: This should fail initially
        window.togglePanel('exercises');
        
        // GREEN: After implementation, these should pass
        expect(mockPanelStates.exercises).toBe(false);
    });

    test('focusTerminalInput function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.focusTerminalInput).toBe('function');
    });

    test('runCode function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.runCode).toBe('function');
    });

    test('clearCode function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.clearCode).toBe('function');
    });

    test('sendMessage function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.sendMessage).toBe('function');
    });

    test('changeLanguage function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.changeLanguage).toBe('function');
    });

    test('selectExercise function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.selectExercise).toBe('function');
    });

    test('toggleSolution function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.toggleSolution).toBe('function');
    });

    test('displayExercises function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.displayExercises).toBe('function');
    });

    test('forceDisplayExercises function should be defined', () => {
        // RED: Test fails initially
        expect(typeof window.forceDisplayExercises).toBe('function');
    });

    test('all functions should be available immediately after script load', () => {
        // This test ensures functions are available when HTML needs them
        const requiredFunctions = [
            'togglePanel',
            'focusTerminalInput', 
            'runCode',
            'clearCode',
            'sendMessage',
            'changeLanguage',
            'selectExercise',
            'toggleSolution',
            'displayExercises',
            'forceDisplayExercises'
        ];
        
        requiredFunctions.forEach(funcName => {
            expect(typeof window[funcName]).toBe('function');
        });
    });
});

/**
 * Integration Test for Lab Environment
 */
describe('Lab Environment Integration', () => {
    test('should load lab-template.js and expose functions globally', async () => {
        // This test will verify the script loading works correctly
        
        // Mock fetch for config.js
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ exercises: [] })
            })
        );
        
        // Load the lab template script
        // In a real browser, this would be done via script tag
        // Here we'll simulate the script loading
        expect(typeof window.togglePanel).toBe('function');
    });
    
    test('should handle exercise display without errors', () => {
        // Mock exercises array
        const mockExercises = [
            {
                id: 'ex1',
                title: 'Test Exercise',
                description: 'Test description',
                difficulty: 'beginner'
            }
        ];
        
        // Mock DOM elements
        mockDocument.getElementById.mockReturnValue({
            innerHTML: '',
            classList: {
                add: jest.fn(),
                remove: jest.fn()
            }
        });
        
        // This should not throw an error
        expect(() => {
            window.displayExercises();
        }).not.toThrow();
    });
});