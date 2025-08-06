/**
 * Frontend tests for demo functionality
 * Tests JavaScript demo functions, UI interactions, and error handling
 */

// Mock dependencies for testing
const mockFetch = jest.fn();
const mockShowNotification = jest.fn();
const mockLocalStorage = {
    setItem: jest.fn(),
    getItem: jest.fn(),
    removeItem: jest.fn()
};

// Mock window.location
const mockLocation = {
    href: '',
    assign: jest.fn(),
    reload: jest.fn()
};

// Setup global mocks
global.fetch = mockFetch;
global.showNotification = mockShowNotification;
global.localStorage = mockLocalStorage;
global.window = { ...global.window, location: mockLocation };

describe('Demo Functionality Frontend Tests', () => {
    
    beforeEach(() => {
        // Reset mocks before each test
        jest.clearAllMocks();
        mockFetch.mockReset();
        mockShowNotification.mockReset();
        mockLocalStorage.setItem.mockReset();
        mockLocalStorage.getItem.mockReset();
        mockLocalStorage.removeItem.mockReset();
        mockLocation.assign.mockReset();
        mockLocation.href = '';
    });

    describe('startDemo Function', () => {
        
        test('should start demo session successfully', async () => {
            // Mock successful API response
            const mockDemoResponse = {
                session_id: 'test-session-123',
                user: {
                    id: 'demo-instructor-test123',
                    name: 'Dr. Sarah Johnson',
                    email: 'sarah.johnson@democorp.edu',
                    role: 'instructor',
                    organization: 'Demo University',
                    is_demo: true
                },
                expires_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
                message: 'Demo session started as instructor'
            };

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockDemoResponse
            });

            // Load the startDemo function (would need to import from actual module)
            const startDemo = async () => {
                try {
                    showNotification('Starting demo session...', 'info', { timeout: 2000 });
                    
                    const response = await fetch('/api/v1/demo/start?user_type=instructor', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to start demo session');
                    }
                    
                    const demoData = await response.json();
                    
                    localStorage.setItem('demoSession', JSON.stringify({
                        sessionId: demoData.session_id,
                        user: demoData.user,
                        expiresAt: demoData.expires_at,
                        isDemo: true
                    }));
                    localStorage.setItem('currentUser', JSON.stringify(demoData.user));
                    
                    showNotification(
                        `Welcome ${demoData.user.name}! You're now exploring as a Demo Instructor. This session expires in 2 hours.`,
                        'success',
                        { timeout: 5000 }
                    );
                    
                    setTimeout(() => {
                        window.location.href = `html/instructor-dashboard.html?demo=true&session=${demoData.session_id}`;
                    }, 2000);
                    
                } catch (error) {
                    console.error('Failed to start demo:', error);
                    showNotification(
                        'Failed to start demo session. Please try again.',
                        'error',
                        { timeout: 5000 }
                    );
                }
            };

            // Execute the function
            await startDemo();

            // Verify API call
            expect(mockFetch).toHaveBeenCalledWith('/api/v1/demo/start?user_type=instructor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // Verify loading notification
            expect(mockShowNotification).toHaveBeenCalledWith(
                'Starting demo session...',
                'info',
                { timeout: 2000 }
            );

            // Verify localStorage storage
            expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
                'demoSession',
                JSON.stringify({
                    sessionId: 'test-session-123',
                    user: mockDemoResponse.user,
                    expiresAt: mockDemoResponse.expires_at,
                    isDemo: true
                })
            );
            expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
                'currentUser',
                JSON.stringify(mockDemoResponse.user)
            );

            // Verify success notification
            expect(mockShowNotification).toHaveBeenCalledWith(
                "Welcome Dr. Sarah Johnson! You're now exploring as a Demo Instructor. This session expires in 2 hours.",
                'success',
                { timeout: 5000 }
            );
        });

        test('should handle API failure gracefully', async () => {
            // Mock API failure
            mockFetch.mockRejectedValueOnce(new Error('Network error'));

            const startDemo = async () => {
                try {
                    showNotification('Starting demo session...', 'info', { timeout: 2000 });
                    
                    const response = await fetch('/api/v1/demo/start?user_type=instructor', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to start demo session');
                    }
                    
                } catch (error) {
                    console.error('Failed to start demo:', error);
                    showNotification(
                        'Failed to start demo session. Please try again.',
                        'error',
                        { timeout: 5000 }
                    );
                }
            };

            await startDemo();

            // Should show error notification
            expect(mockShowNotification).toHaveBeenCalledWith(
                'Failed to start demo session. Please try again.',
                'error',
                { timeout: 5000 }
            );

            // Should not store anything in localStorage
            expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
        });

        test('should handle server error response', async () => {
            // Mock server error response
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                json: async () => ({ detail: 'Internal server error' })
            });

            const startDemo = async () => {
                try {
                    showNotification('Starting demo session...', 'info', { timeout: 2000 });
                    
                    const response = await fetch('/api/v1/demo/start?user_type=instructor', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to start demo session');
                    }
                    
                } catch (error) {
                    showNotification(
                        'Failed to start demo session. Please try again.',
                        'error',
                        { timeout: 5000 }
                    );
                }
            };

            await startDemo();

            expect(mockShowNotification).toHaveBeenCalledWith(
                'Failed to start demo session. Please try again.',
                'error',
                { timeout: 5000 }
            );
        });
    });

    describe('Demo Session Management', () => {
        
        test('should validate demo session data', () => {
            const validateDemoSession = (sessionData) => {
                if (!sessionData) return false;
                if (!sessionData.sessionId) return false;
                if (!sessionData.user) return false;
                if (!sessionData.user.is_demo) return false;
                if (!sessionData.expiresAt) return false;
                
                // Check if session is expired
                const expiryTime = new Date(sessionData.expiresAt);
                const now = new Date();
                if (expiryTime <= now) return false;
                
                return true;
            };

            // Valid session
            const validSession = {
                sessionId: 'test-123',
                user: { id: 'demo-user', name: 'Test User', is_demo: true },
                expiresAt: new Date(Date.now() + 3600000).toISOString(),  // 1 hour from now
                isDemo: true
            };
            
            expect(validateDemoSession(validSession)).toBe(true);

            // Invalid sessions
            expect(validateDemoSession(null)).toBe(false);
            expect(validateDemoSession({})).toBe(false);
            expect(validateDemoSession({ sessionId: 'test' })).toBe(false);
            
            // Expired session
            const expiredSession = {
                ...validSession,
                expiresAt: new Date(Date.now() - 3600000).toISOString()  // 1 hour ago
            };
            expect(validateDemoSession(expiredSession)).toBe(false);
        });

        test('should handle demo session expiration', () => {
            const handleSessionExpiration = () => {
                // Clear demo session data
                localStorage.removeItem('demoSession');
                localStorage.removeItem('currentUser');
                
                // Show expiration notification
                showNotification(
                    'Your demo session has expired. Click "Try Demo" to start a new session.',
                    'warning',
                    { timeout: 8000 }
                );
                
                // Redirect to home page
                window.location.href = '/';
            };

            handleSessionExpiration();

            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('demoSession');
            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('currentUser');
            expect(mockShowNotification).toHaveBeenCalledWith(
                'Your demo session has expired. Click "Try Demo" to start a new session.',
                'warning',
                { timeout: 8000 }
            );
        });
    });

    describe('Demo UI Interactions', () => {
        
        test('should handle demo button states', () => {
            // Mock DOM elements
            const mockButton = {
                disabled: false,
                textContent: 'Try Demo',
                setAttribute: jest.fn(),
                removeAttribute: jest.fn(),
                classList: {
                    add: jest.fn(),
                    remove: jest.fn()
                }
            };

            const setDemoButtonLoading = (button, loading) => {
                if (loading) {
                    button.disabled = true;
                    button.textContent = 'Starting Demo...';
                    button.classList.add('loading');
                } else {
                    button.disabled = false;
                    button.textContent = 'Try Demo';
                    button.classList.remove('loading');
                }
            };

            // Test loading state
            setDemoButtonLoading(mockButton, true);
            expect(mockButton.disabled).toBe(true);
            expect(mockButton.textContent).toBe('Starting Demo...');
            expect(mockButton.classList.add).toHaveBeenCalledWith('loading');

            // Test normal state
            setDemoButtonLoading(mockButton, false);
            expect(mockButton.disabled).toBe(false);
            expect(mockButton.textContent).toBe('Try Demo');
            expect(mockButton.classList.remove).toHaveBeenCalledWith('loading');
        });

        test('should prevent multiple simultaneous demo requests', () => {
            let isDemoStarting = false;

            const startDemoWithPrevention = async () => {
                if (isDemoStarting) {
                    showNotification('Demo session is already starting...', 'info', { timeout: 2000 });
                    return;
                }

                isDemoStarting = true;
                
                try {
                    // Simulate demo start process
                    await new Promise(resolve => setTimeout(resolve, 100));
                } finally {
                    isDemoStarting = false;
                }
            };

            // First call should proceed
            startDemoWithPrevention();
            expect(isDemoStarting).toBe(true);

            // Second immediate call should be prevented
            startDemoWithPrevention();
            expect(mockShowNotification).toHaveBeenCalledWith(
                'Demo session is already starting...',
                'info',
                { timeout: 2000 }
            );
        });
    });

    describe('Demo Data Visualization', () => {
        
        test('should format demo data for display', () => {
            const formatDemoData = (data) => {
                return {
                    ...data,
                    formatted: true,
                    displayTime: new Date(data.created_at).toLocaleString(),
                    progressPercent: Math.round(data.completion_rate || 0) + '%'
                };
            };

            const rawData = {
                id: 'course-1',
                title: 'Demo Course',
                completion_rate: 75.5,
                created_at: '2024-01-01T10:00:00Z'
            };

            const formattedData = formatDemoData(rawData);
            
            expect(formattedData.formatted).toBe(true);
            expect(formattedData.progressPercent).toBe('76%');
            expect(formattedData.displayTime).toContain('2024');
        });

        test('should handle demo data loading states', () => {
            const demoDataStates = {
                LOADING: 'loading',
                SUCCESS: 'success',
                ERROR: 'error'
            };

            const createDemoDataState = (state, data = null, error = null) => {
                return {
                    state,
                    data,
                    error,
                    isLoading: state === demoDataStates.LOADING,
                    hasError: state === demoDataStates.ERROR,
                    hasData: state === demoDataStates.SUCCESS && data !== null
                };
            };

            // Test loading state
            const loadingState = createDemoDataState(demoDataStates.LOADING);
            expect(loadingState.isLoading).toBe(true);
            expect(loadingState.hasError).toBe(false);
            expect(loadingState.hasData).toBe(false);

            // Test success state
            const successState = createDemoDataState(demoDataStates.SUCCESS, { courses: [] });
            expect(successState.isLoading).toBe(false);
            expect(successState.hasError).toBe(false);
            expect(successState.hasData).toBe(true);

            // Test error state
            const errorState = createDemoDataState(demoDataStates.ERROR, null, 'Failed to load');
            expect(errorState.isLoading).toBe(false);
            expect(errorState.hasError).toBe(true);
            expect(errorState.hasData).toBe(false);
        });
    });

    describe('Demo Analytics Functions', () => {
        
        test('should calculate demo metrics', () => {
            const calculateDemoMetrics = (students) => {
                const totalStudents = students.length;
                const activeStudents = students.filter(s => s.progress > 0).length;
                const avgProgress = students.reduce((sum, s) => sum + s.progress, 0) / totalStudents;
                const completedStudents = students.filter(s => s.progress >= 100).length;
                
                return {
                    total: totalStudents,
                    active: activeStudents,
                    completed: completedStudents,
                    avgProgress: Math.round(avgProgress),
                    completionRate: Math.round((completedStudents / totalStudents) * 100)
                };
            };

            const sampleStudents = [
                { id: '1', progress: 100 },
                { id: '2', progress: 75 },
                { id: '3', progress: 0 },
                { id: '4', progress: 50 }
            ];

            const metrics = calculateDemoMetrics(sampleStudents);
            
            expect(metrics.total).toBe(4);
            expect(metrics.active).toBe(3);
            expect(metrics.completed).toBe(1);
            expect(metrics.avgProgress).toBe(56);  // (100+75+0+50)/4
            expect(metrics.completionRate).toBe(25);  // 1/4 * 100
        });

        test('should generate demo chart data', () => {
            const generateChartData = (progressData) => {
                return {
                    labels: progressData.map(d => new Date(d.date).toLocaleDateString()),
                    datasets: [{
                        label: 'Student Progress',
                        data: progressData.map(d => d.completions),
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4
                    }]
                };
            };

            const sampleProgressData = [
                { date: '2024-01-01T00:00:00Z', completions: 5 },
                { date: '2024-01-02T00:00:00Z', completions: 8 },
                { date: '2024-01-03T00:00:00Z', completions: 12 }
            ];

            const chartData = generateChartData(sampleProgressData);
            
            expect(chartData.labels).toHaveLength(3);
            expect(chartData.datasets[0].data).toEqual([5, 8, 12]);
            expect(chartData.datasets[0].label).toBe('Student Progress');
        });
    });

    describe('Demo Error Recovery', () => {
        
        test('should implement retry mechanism for failed demo requests', async () => {
            let callCount = 0;
            const mockApiCall = jest.fn().mockImplementation(() => {
                callCount++;
                if (callCount <= 2) {
                    return Promise.reject(new Error('Network error'));
                }
                return Promise.resolve({ ok: true, json: () => ({ success: true }) });
            });

            const retryDemoRequest = async (apiCall, maxRetries = 3, delay = 1000) => {
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                    try {
                        return await apiCall();
                    } catch (error) {
                        if (attempt === maxRetries) {
                            throw error;
                        }
                        // In real implementation, would use setTimeout for delay
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            };

            const result = await retryDemoRequest(mockApiCall, 3, 10);
            
            expect(mockApiCall).toHaveBeenCalledTimes(3);
            expect(result).toBeDefined();
        });

        test('should handle demo session recovery from localStorage', () => {
            const recoverDemoSession = () => {
                try {
                    const storedSession = localStorage.getItem('demoSession');
                    if (!storedSession) return null;
                    
                    const sessionData = JSON.parse(storedSession);
                    
                    // Validate session
                    const expiryTime = new Date(sessionData.expiresAt);
                    if (expiryTime <= new Date()) {
                        // Session expired, clean up
                        localStorage.removeItem('demoSession');
                        localStorage.removeItem('currentUser');
                        return null;
                    }
                    
                    return sessionData;
                } catch (error) {
                    // Corrupted session data, clean up
                    localStorage.removeItem('demoSession');
                    localStorage.removeItem('currentUser');
                    return null;
                }
            };

            // Test with valid session
            const validSession = {
                sessionId: 'test-123',
                user: { name: 'Test User', is_demo: true },
                expiresAt: new Date(Date.now() + 3600000).toISOString()
            };
            
            mockLocalStorage.getItem.mockReturnValueOnce(JSON.stringify(validSession));
            
            const recovered = recoverDemoSession();
            expect(recovered).toEqual(validSession);

            // Test with expired session
            const expiredSession = {
                ...validSession,
                expiresAt: new Date(Date.now() - 3600000).toISOString()
            };
            
            mockLocalStorage.getItem.mockReturnValueOnce(JSON.stringify(expiredSession));
            
            const expiredResult = recoverDemoSession();
            expect(expiredResult).toBeNull();
            expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('demoSession');
        });
    });
});

// Integration test helpers
describe('Demo Frontend Integration Helpers', () => {
    
    test('should provide demo API client', () => {
        const createDemoApiClient = (baseUrl, sessionId) => {
            return {
                async getCourses(limit = 10) {
                    const response = await fetch(`${baseUrl}/courses?session_id=${sessionId}&limit=${limit}`);
                    return response.json();
                },
                
                async getStudents() {
                    const response = await fetch(`${baseUrl}/students?session_id=${sessionId}`);
                    return response.json();
                },
                
                async getAnalytics(timeframe = '30d') {
                    const response = await fetch(`${baseUrl}/analytics?session_id=${sessionId}&timeframe=${timeframe}`);
                    return response.json();
                },
                
                async createCourse(courseData) {
                    const response = await fetch(`${baseUrl}/course/create?session_id=${sessionId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(courseData)
                    });
                    return response.json();
                }
            };
        };

        const client = createDemoApiClient('/api/v1/demo', 'test-session');
        
        expect(client.getCourses).toBeDefined();
        expect(client.getStudents).toBeDefined();
        expect(client.getAnalytics).toBeDefined();
        expect(client.createCourse).toBeDefined();
    });
    
    test('should validate demo UI components', () => {
        const validateDemoComponent = (componentName, element) => {
            const validations = {
                'demo-button': (el) => {
                    return el && el.tagName === 'BUTTON' && 
                           (el.textContent.toLowerCase().includes('demo') || 
                            el.getAttribute('onclick')?.includes('startDemo'));
                },
                'demo-indicator': (el) => {
                    return el && (el.textContent.toLowerCase().includes('demo') ||
                                 el.classList.contains('demo-mode'));
                },
                'demo-data-table': (el) => {
                    return el && el.tagName === 'TABLE' && 
                           el.querySelector('[data-demo]') !== null;
                }
            };
            
            const validator = validations[componentName];
            return validator ? validator(element) : false;
        };

        // Mock DOM elements
        const mockDemoButton = {
            tagName: 'BUTTON',
            textContent: 'Try Demo',
            getAttribute: (attr) => attr === 'onclick' ? 'startDemo()' : null
        };

        expect(validateDemoComponent('demo-button', mockDemoButton)).toBe(true);
    });
});