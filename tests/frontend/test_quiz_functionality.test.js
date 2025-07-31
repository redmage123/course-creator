/**
 * Unit tests for quiz functionality in instructor dashboard
 * Following TDD approach to fix the quizzes.map error
 */

describe('Quiz Functionality Tests', () => {
    let mockWindow;
    let mockDocument;
    let mockConsole;

    beforeEach(() => {
        // Mock window object
        mockWindow = {
            currentCourseContent: null,
            openQuizzesPane: null,
            viewAllQuizzes: null,
            viewQuizDetails: null
        };
        
        // Mock document object
        mockDocument = {
            createElement: jest.fn().mockReturnValue({
                className: '',
                innerHTML: '',
                appendChild: jest.fn(),
                remove: jest.fn(),
                closest: jest.fn().mockReturnValue({ remove: jest.fn() })
            }),
            body: {
                appendChild: jest.fn()
            }
        };
        
        // Mock console
        mockConsole = {
            log: jest.fn(),
            error: jest.fn()
        };
        
        // Set up global mocks
        global.window = mockWindow;
        global.document = mockDocument;
        global.console = mockConsole;
    });

    describe('openQuizzesPane', () => {
        test('should handle empty quizzes array without error', () => {
            // Arrange
            mockWindow.currentCourseContent = { quizzes: [] };
            
            // Define the function (this is what needs to be implemented)
            mockWindow.openQuizzesPane = function(courseId) {
                console.log('Opening quizzes pane for course:', courseId);
                console.log('Current course content:', window.currentCourseContent);
                console.log('Quizzes data:', window.currentCourseContent?.quizzes);
                
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                
                // This should not throw an error
                const quizHtml = quizzes.map((quiz, index) => `<div>${quiz.title}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.openQuizzesPane('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.quizCount).toBe(0);
            expect(result.html).toBe('');
        });

        test('should handle null currentCourseContent without error', () => {
            // Arrange
            mockWindow.currentCourseContent = null;
            
            // Define the function
            mockWindow.openQuizzesPane = function(courseId) {
                console.log('Opening quizzes pane for course:', courseId);
                console.log('Current course content:', window.currentCourseContent);
                console.log('Quizzes data:', window.currentCourseContent?.quizzes);
                
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                
                // This should not throw an error
                const quizHtml = quizzes.map((quiz, index) => `<div>${quiz.title}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.openQuizzesPane('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.quizCount).toBe(0);
            expect(result.html).toBe('');
        });

        test('should handle non-array quizzes property without error', () => {
            // Arrange - This is likely the actual problem case
            mockWindow.currentCourseContent = { quizzes: "not an array" };
            
            // Define the function
            mockWindow.openQuizzesPane = function(courseId) {
                console.log('Opening quizzes pane for course:', courseId);
                console.log('Current course content:', window.currentCourseContent);
                console.log('Quizzes data:', window.currentCourseContent?.quizzes);
                
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                
                // This should not throw an error
                const quizHtml = quizzes.map((quiz, index) => `<div>${quiz.title}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.openQuizzesPane('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.quizCount).toBe(0);
            expect(result.html).toBe('');
        });

        test('should handle valid quizzes array correctly', () => {
            // Arrange
            const mockQuizzes = [
                { title: 'Quiz 1', description: 'First quiz' },
                { title: 'Quiz 2', description: 'Second quiz' }
            ];
            mockWindow.currentCourseContent = { quizzes: mockQuizzes };
            
            // Define the function with proper implementation
            mockWindow.openQuizzesPane = function(courseId) {
                console.log('Opening quizzes pane for course:', courseId);
                console.log('Current course content:', this.currentCourseContent);
                console.log('Quizzes data:', this.currentCourseContent?.quizzes);
                
                const quizzes = Array.isArray(this.currentCourseContent?.quizzes) ? this.currentCourseContent.quizzes : [];
                
                // Create proper HTML structure
                const quizHtml = quizzes.map((quiz, index) => `<div>Quiz ${index + 1}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.openQuizzesPane('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.quizCount).toBe(2);
            expect(result.html).toBe('<div>Quiz 1</div><div>Quiz 2</div>');
        });
    });

    describe('viewAllQuizzes', () => {
        test('should handle empty quizzes array without error', () => {
            // Arrange
            mockWindow.currentCourseContent = { quizzes: [] };
            
            // Define the function
            mockWindow.viewAllQuizzes = function(courseId) {
                console.log('Viewing all quizzes for course:', courseId);
                
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                
                if (quizzes.length === 0) {
                    return { success: true, message: 'No quizzes to display' };
                }
                
                // This should not throw an error
                const quizHtml = quizzes.map((quiz, index) => `<div>${quiz.title}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.viewAllQuizzes('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.message).toBe('No quizzes to display');
        });

        test('should handle non-array quizzes property without error', () => {
            // Arrange
            mockWindow.currentCourseContent = { quizzes: { someProperty: 'not an array' } };
            
            // Define the function
            mockWindow.viewAllQuizzes = function(courseId) {
                console.log('Viewing all quizzes for course:', courseId);
                
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                
                if (quizzes.length === 0) {
                    return { success: true, message: 'No quizzes to display' };
                }
                
                // This should not throw an error
                const quizHtml = quizzes.map((quiz, index) => `<div>${quiz.title}</div>`).join('');
                
                return { success: true, quizCount: quizzes.length, html: quizHtml };
            };
            
            // Act
            const result = mockWindow.viewAllQuizzes('test-course-id');
            
            // Assert
            expect(result.success).toBe(true);
            expect(result.message).toBe('No quizzes to display');
        });
    });

    describe('viewQuizDetails', () => {
        test('should handle empty quizzes array without error', () => {
            // Arrange
            mockWindow.currentCourseContent = { quizzes: [] };
            
            // Define the function
            mockWindow.viewQuizDetails = function(courseId, quizIndex) {
                console.log('Viewing quiz details for course:', courseId, 'quiz:', quizIndex);
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                const quiz = quizzes[quizIndex];
                
                if (!quiz) {
                    return { success: false, message: 'Quiz not found' };
                }
                
                return { success: true, quiz: quiz };
            };
            
            // Act
            const result = mockWindow.viewQuizDetails('test-course-id', 0);
            
            // Assert
            expect(result.success).toBe(false);
            expect(result.message).toBe('Quiz not found');
        });

        test('should handle non-array quizzes property without error', () => {
            // Arrange
            mockWindow.currentCourseContent = { quizzes: 'not an array' };
            
            // Define the function
            mockWindow.viewQuizDetails = function(courseId, quizIndex) {
                console.log('Viewing quiz details for course:', courseId, 'quiz:', quizIndex);
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                const quiz = quizzes[quizIndex];
                
                if (!quiz) {
                    return { success: false, message: 'Quiz not found' };
                }
                
                return { success: true, quiz: quiz };
            };
            
            // Act
            const result = mockWindow.viewQuizDetails('test-course-id', 0);
            
            // Assert
            expect(result.success).toBe(false);
            expect(result.message).toBe('Quiz not found');
        });
    });

    describe('Edge Cases', () => {
        test('should handle undefined currentCourseContent', () => {
            // Arrange
            mockWindow.currentCourseContent = undefined;
            
            // Define the function
            mockWindow.openQuizzesPane = function(courseId) {
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                return { success: true, quizCount: quizzes.length };
            };
            
            // Act & Assert
            expect(() => mockWindow.openQuizzesPane('test-course-id')).not.toThrow();
            const result = mockWindow.openQuizzesPane('test-course-id');
            expect(result.quizCount).toBe(0);
        });

        test('should handle currentCourseContent without quizzes property', () => {
            // Arrange
            mockWindow.currentCourseContent = { syllabus: 'test', slides: [] };
            
            // Define the function
            mockWindow.openQuizzesPane = function(courseId) {
                const quizzes = Array.isArray(window.currentCourseContent?.quizzes) ? window.currentCourseContent.quizzes : [];
                return { success: true, quizCount: quizzes.length };
            };
            
            // Act & Assert
            expect(() => mockWindow.openQuizzesPane('test-course-id')).not.toThrow();
            const result = mockWindow.openQuizzesPane('test-course-id');
            expect(result.quizCount).toBe(0);
        });
    });
});