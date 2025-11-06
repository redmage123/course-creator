/**
 * Analytics Dashboard Module
 *
 * BUSINESS REQUIREMENT:
 * Provides instructors with comprehensive student analytics visualization and reporting
 * capabilities to track student performance, engagement, and learning outcomes.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Class-based module for analytics visualization
 * - Integrates with Chart.js for interactive charts
 * - Supports course-specific and aggregated analytics
 * - Time range filtering for historical analysis
 * - PDF and JSON export capabilities
 *
 * WHY THIS MATTERS:
 * Data-driven insights enable instructors to identify at-risk students early,
 * optimize course content, and demonstrate educational effectiveness to stakeholders.
 *
 * @module analytics-dashboard
 */
class AnalyticsDashboard {
    /**
     * Analytics Dashboard Constructor
     *
     * BUSINESS LOGIC:
     * Initializes the analytics dashboard with default configuration and
     * empty state for charts and data.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Reads Analytics API URL from global CONFIG
     * - Initializes chart instances storage
     * - Sets initialization flag to false
     * - Prepares current course tracker
     *
     * WHY THIS MATTERS:
     * Proper initialization ensures the dashboard is ready to load and
     * display analytics data when requested.
     *
     * @constructor
     */
    constructor() {
        this.analyticsAPI = window.CONFIG?.API_URLS.ANALYTICS;
        this.currentCourse = null;
        this.charts = {};
        this.initialized = false;
    }

    /**
     * Initialize Analytics Dashboard
     *
     * BUSINESS LOGIC:
     * Performs one-time initialization of the analytics dashboard, setting up
     * event listeners and loading initial data if a course is specified.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Sets current course context
     * - Registers event listeners for UI controls
     * - Loads course analytics if course ID provided
     * - Sets initialized flag to prevent re-initialization
     * - Handles initialization errors gracefully
     *
     * WHY THIS MATTERS:
     * Proper initialization ensures all dashboard functionality is ready
     * and prevents duplicate event listener registration.
     *
     * @async
     * @param {number|null} [courseId=null] - Optional course ID to load analytics for
     * @returns {Promise<void>}
     * @throws {Error} If initialization fails
     */
    async initialize(courseId = null) {
        try {
            this.currentCourse = courseId;
            this.setupEventListeners();
            
            if (courseId) {
                await this.loadCourseAnalytics(courseId);
            }
            
            this.initialized = true;
            
        } catch (error) {
            console.error('Error initializing analytics dashboard:', error);
            this.showError('Failed to initialize analytics dashboard');
        }
    }

    /**
     * Setup Event Listeners for Dashboard Controls
     *
     * BUSINESS LOGIC:
     * Registers event handlers for all user interactions with the analytics
     * dashboard including course selection, time range, search, export, and refresh.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Course selection dropdown change handler
     * - Time range selector change handler
     * - Student search input handler (debounced)
     * - Export analytics button click handler
     * - PDF report download button click handler
     * - Refresh analytics button click handler
     *
     * WHY THIS MATTERS:
     * Event listeners enable interactive, responsive analytics filtering
     * and data exploration.
     *
     * @returns {void}
     */
    setupEventListeners() {
        // Course selection change
        const courseSelect = document.getElementById('analyticsCourseSelect');
        if (courseSelect) {
            courseSelect.addEventListener('change', (e) => {
                this.loadCourseAnalytics(e.target.value);
            });
        }

        // Time range selector
        const timeRangeSelect = document.getElementById('analyticsTimeRange');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', (e) => {
                this.updateTimeRange(e.target.value);
            });
        }

        // Student search
        const studentSearch = document.getElementById('studentSearchInput');
        if (studentSearch) {
            studentSearch.addEventListener('input', (e) => {
                this.searchStudents(e.target.value);
            });
        }

        // Export buttons
        const exportBtn = document.getElementById('exportAnalyticsBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportAnalytics();
            });
        }

        // PDF Report button
        const pdfReportBtn = document.getElementById('downloadPDFReportBtn');
        if (pdfReportBtn) {
            pdfReportBtn.addEventListener('click', () => {
                this.downloadPDFReport();
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshAnalyticsBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAnalytics();
            });
        }
    }

    /**
     * Load Course Analytics Data
     *
     * BUSINESS LOGIC:
     * Fetches comprehensive analytics data for a specific course over a specified
     * time period, then renders all visualizations and student lists.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Shows loading state during fetch
     * - Fetches analytics from Analytics API with authentication
     * - Handles HTTP errors gracefully
     * - Renders analytics charts and overview cards
     * - Loads student-specific analytics list
     * - Hides loading state on completion/error
     *
     * WHY THIS MATTERS:
     * Course analytics provide instructors with actionable insights into
     * student performance and engagement trends.
     *
     * @async
     * @param {number} courseId - ID of the course to load analytics for
     * @param {number} [daysBack=30] - Number of days of historical data to fetch
     * @returns {Promise<void>}
     * @throws {Error} If analytics data cannot be loaded
     */
    async loadCourseAnalytics(courseId, daysBack = 30) {
        try {
            this.showLoading('Loading course analytics...');
            
            const response = await fetch(`${this.analyticsAPI}/analytics/course/${courseId}?days_back=${daysBack}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const analytics = await response.json();
            
            await this.renderCourseAnalytics(analytics);
            await this.loadStudentsList(courseId);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading course analytics:', error);
            this.showError('Failed to load course analytics');
            this.hideLoading();
        }
    }

    /**
     * Render Course Analytics Visualizations
     *
     * BUSINESS LOGIC:
     * Orchestrates the rendering of all analytics components including
     * overview cards and four interactive charts.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates overview statistics cards
     * - Renders engagement trend chart
     * - Renders lab completion status chart
     * - Renders quiz performance distribution chart
     * - Renders content progress distribution chart
     * - Handles rendering errors gracefully
     *
     * WHY THIS MATTERS:
     * Visual representations make complex data accessible and actionable,
     * enabling quick identification of trends and issues.
     *
     * @async
     * @param {Object} analytics - Complete analytics data object from API
     * @returns {Promise<void>}
     */
    async renderCourseAnalytics(analytics) {
        try {
            // Update overview cards
            this.updateOverviewCards(analytics);
            
            // Render charts
            await this.renderEngagementChart(analytics);
            await this.renderLabCompletionChart(analytics);
            await this.renderQuizPerformanceChart(analytics);
            await this.renderProgressDistributionChart(analytics);
            
        } catch (error) {
            console.error('Error rendering course analytics:', error);
        }
    }

    /**
     * Update Overview Statistics Cards
     *
     * BUSINESS LOGIC:
     * Updates the summary cards at the top of the analytics dashboard with
     * key performance indicators.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates total students count
     * - Updates active students count
     * - Calculates and displays average quiz score
     * - Calculates and displays lab completion rate
     * - Handles missing elements gracefully
     *
     * WHY THIS MATTERS:
     * Overview cards provide at-a-glance metrics for quick assessment
     * of overall course health.
     *
     * @param {Object} analytics - Analytics data containing enrollment and performance metrics
     * @param {Object} analytics.enrollment - Enrollment data with total and active student counts
     * @param {Object} analytics.quiz_performance - Quiz performance data with average scores
     * @param {Object} analytics.lab_completion - Lab completion data with completion rates
     * @returns {void}
     */
    updateOverviewCards(analytics) {
        // Total students
        const totalStudentsEl = document.getElementById('totalStudentsCount');
        if (totalStudentsEl) {
            totalStudentsEl.textContent = analytics.enrollment.total_students;
        }

        // Active students
        const activeStudentsEl = document.getElementById('activeStudentsCount');
        if (activeStudentsEl) {
            activeStudentsEl.textContent = analytics.enrollment.active_students;
        }

        // Average quiz score
        const avgQuizScoreEl = document.getElementById('avgQuizScore');
        if (avgQuizScoreEl) {
            avgQuizScoreEl.textContent = `${analytics.quiz_performance.average_score.toFixed(1)}%`;
        }

        // Lab completion rate
        const labCompletionEl = document.getElementById('labCompletionRate');
        if (labCompletionEl) {
            const completed = analytics.lab_completion.completion_rates.find(r => r.status === 'completed');
            const total = analytics.lab_completion.completion_rates.reduce((sum, r) => sum + r.count, 0);
            const rate = completed && total > 0 ? (completed.count / total * 100).toFixed(1) : 0;
            labCompletionEl.textContent = `${rate}%`;
        }
    }

    /**
     * Render Student Engagement Trend Chart
     *
     * BUSINESS LOGIC:
     * Visualizes student engagement trends over time using a line chart
     * to show active student patterns.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Destroys existing chart instance if present
     * - Creates Chart.js line chart with engagement data
     * - Simulates weekly trend data (TODO: use real API data)
     * - Configures responsive chart with proper scaling
     * - Stores chart instance for cleanup
     *
     * WHY THIS MATTERS:
     * Engagement trends help instructors identify drop-off points and
     * assess the effectiveness of course content and interventions.
     *
     * @async
     * @param {Object} analytics - Analytics data containing enrollment metrics
     * @param {Object} analytics.enrollment - Enrollment data with active student counts
     * @returns {Promise<void>}
     */
    async renderEngagementChart(analytics) {
        const ctx = document.getElementById('engagementChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.engagement) {
            this.charts.engagement.destroy();
        }

        // Create engagement trend chart
        this.charts.engagement = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'], // This would be dynamic
                datasets: [{
                    label: 'Active Students',
                    data: [analytics.enrollment.active_students, 
                           analytics.enrollment.active_students * 0.9,
                           analytics.enrollment.active_students * 0.85,
                           analytics.enrollment.active_students * 0.8],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Student Engagement Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Render Lab Completion Status Chart
     *
     * BUSINESS LOGIC:
     * Displays lab completion status distribution using a doughnut chart
     * to show proportions of completed, in-progress, failed, and not-started labs.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Destroys existing chart instance if present
     * - Extracts lab completion rates from analytics data
     * - Maps status labels and counts to chart data
     * - Creates Chart.js doughnut chart with color-coded segments
     * - Configures legend and responsive behavior
     * - Stores chart instance for cleanup
     *
     * WHY THIS MATTERS:
     * Lab completion distribution reveals hands-on learning engagement
     * and helps identify students struggling with practical exercises.
     *
     * @async
     * @param {Object} analytics - Analytics data containing lab completion metrics
     * @param {Object} analytics.lab_completion - Lab completion data
     * @param {Array} analytics.lab_completion.completion_rates - Array of completion status objects
     * @returns {Promise<void>}
     */
    async renderLabCompletionChart(analytics) {
        const ctx = document.getElementById('labCompletionChart');
        if (!ctx) return;

        if (this.charts.labCompletion) {
            this.charts.labCompletion.destroy();
        }

        const labels = analytics.lab_completion.completion_rates.map(r => 
            r.status.charAt(0).toUpperCase() + r.status.slice(1)
        );
        const data = analytics.lab_completion.completion_rates.map(r => r.count);
        const colors = ['#4CAF50', '#FF9800', '#F44336', '#2196F3'];

        this.charts.labCompletion = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Lab Completion Status'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * Render Quiz Performance Distribution Chart
     *
     * BUSINESS LOGIC:
     * Visualizes quiz score distribution using a bar chart to show
     * how student performance is distributed across score ranges.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Destroys existing chart instance if present
     * - Generates score distribution from average and standard deviation
     * - Creates Chart.js bar chart with 5 score ranges (0-20%, 21-40%, etc.)
     * - Configures responsive behavior and proper scaling
     * - Stores chart instance for cleanup
     *
     * WHY THIS MATTERS:
     * Quiz score distribution reveals assessment difficulty appropriateness
     * and overall class performance patterns.
     *
     * @async
     * @param {Object} analytics - Analytics data containing quiz performance metrics
     * @param {Object} analytics.quiz_performance - Quiz performance data
     * @param {number} analytics.quiz_performance.average_score - Average quiz score
     * @param {number} analytics.quiz_performance.score_standard_deviation - Score standard deviation
     * @param {number} analytics.quiz_performance.total_attempts - Total quiz attempts
     * @returns {Promise<void>}
     */
    async renderQuizPerformanceChart(analytics) {
        const ctx = document.getElementById('quizPerformanceChart');
        if (!ctx) return;

        if (this.charts.quizPerformance) {
            this.charts.quizPerformance.destroy();
        }

        // Generate score distribution data (simulated)
        const scoreRanges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'];
        const avgScore = analytics.quiz_performance.average_score;
        const stdDev = analytics.quiz_performance.score_standard_deviation || 15;
        
        // Simulate distribution based on average and standard deviation
        const distribution = this.generateScoreDistribution(avgScore, stdDev, analytics.quiz_performance.total_attempts);

        this.charts.quizPerformance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: scoreRanges,
                datasets: [{
                    label: 'Number of Students',
                    data: distribution,
                    backgroundColor: '#2196F3',
                    borderColor: '#1976D2',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Quiz Score Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    /**
     * Render Content Progress Distribution Chart
     *
     * BUSINESS LOGIC:
     * Displays how course content progress is distributed using a bar chart
     * to show counts of content items in different completion states.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Destroys existing chart instance if present
     * - Extracts progress distribution from analytics data
     * - Formats status labels for display
     * - Creates Chart.js bar chart with color-coded bars
     * - Configures responsive behavior and proper scaling
     * - Stores chart instance for cleanup
     *
     * WHY THIS MATTERS:
     * Progress distribution shows pacing and helps identify content items
     * causing bottlenecks or confusion.
     *
     * @async
     * @param {Object} analytics - Analytics data containing progress metrics
     * @param {Array} analytics.progress_distribution - Array of progress status objects
     * @returns {Promise<void>}
     */
    async renderProgressDistributionChart(analytics) {
        const ctx = document.getElementById('progressDistributionChart');
        if (!ctx) return;

        if (this.charts.progressDistribution) {
            this.charts.progressDistribution.destroy();
        }

        const labels = analytics.progress_distribution.map(p => 
            p.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
        );
        const data = analytics.progress_distribution.map(p => p.count);
        const colors = ['#FF5722', '#FF9800', '#4CAF50', '#8BC34A'];

        this.charts.progressDistribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Content Items',
                    data: data,
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace('0.8', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Content Progress Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    /**
     * Load Students List for Analytics
     *
     * BUSINESS LOGIC:
     * Fetches and displays a list of students with their individual analytics
     * metrics for the selected course.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Shows loading indicator
     * - Fetches student list (currently simulated, TODO: use real API)
     * - Renders student cards with engagement and progress metrics
     * - Handles errors gracefully
     *
     * WHY THIS MATTERS:
     * Individual student analytics help instructors identify specific
     * students needing intervention or recognition.
     *
     * @async
     * @param {number} courseId - ID of the course to load students for
     * @returns {Promise<void>}
     * @throws {Error} If student list cannot be loaded
     */
    async loadStudentsList(courseId) {
        try {
            // This would typically fetch from a students endpoint
            // For now, we'll simulate student data
            const studentsContainer = document.getElementById('studentsAnalyticsList');
            if (!studentsContainer) return;

            studentsContainer.innerHTML = '<div class="loading">Loading students...</div>';

            // Simulate student data - in real implementation, this would be fetched from API
            const students = await this.fetchStudentsList(courseId);
            
            this.renderStudentsList(students, studentsContainer);
            
        } catch (error) {
            console.error('Error loading students list:', error);
        }
    }

    /**
     * Fetch Students List from API
     *
     * BUSINESS LOGIC:
     * Retrieves student data with analytics metrics for display in the
     * students list section.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Currently returns simulated student data
     * - TODO: Replace with actual API endpoint call
     * - Returns array of student objects with metrics
     *
     * WHY THIS MATTERS:
     * Student-level data enables personalized interventions and
     * individualized support.
     *
     * @async
     * @param {number} courseId - ID of the course to fetch students for
     * @returns {Promise<Array>} Array of student objects with analytics data
     */
    async fetchStudentsList(courseId) {
        // Simulate API call - replace with actual endpoint
        return [
            {
                id: 'student-1',
                name: 'Alice Johnson',
                email: 'alice@example.com',
                engagement_score: 85,
                last_active: '2025-07-26T10:30:00Z',
                progress_percentage: 78
            },
            {
                id: 'student-2', 
                name: 'Bob Smith',
                email: 'bob@example.com',
                engagement_score: 62,
                last_active: '2025-07-25T15:45:00Z',
                progress_percentage: 45
            },
            {
                id: 'student-3',
                name: 'Carol Davis',
                email: 'carol@example.com', 
                engagement_score: 92,
                last_active: '2025-07-26T09:15:00Z',
                progress_percentage: 89
            }
        ];
    }

    /**
     * Render Students List in Container
     *
     * BUSINESS LOGIC:
     * Generates HTML for student analytics cards showing individual metrics
     * and action buttons.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Iterates through student array
     * - Creates card HTML with avatar, name, email, last active time
     * - Displays engagement and progress as visual progress bars
     * - Provides action buttons for details and contact
     * - Injects HTML into container element
     *
     * WHY THIS MATTERS:
     * Visual student cards make it easy to scan and identify students
     * needing attention or praise.
     *
     * @param {Array} students - Array of student objects to render
     * @param {HTMLElement} container - DOM element to render student cards into
     * @returns {void}
     */
    renderStudentsList(students, container) {
        const studentsHTML = students.map(student => `
            <div class="student-analytics-card" data-student-id="${student.id}">
                <div class="student-info">
                    <div class="student-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="student-details">
                        <h4>${student.name}</h4>
                        <p class="student-email">${student.email}</p>
                        <p class="last-active">Last active: ${this.formatDate(student.last_active)}</p>
                    </div>
                </div>
                <div class="student-metrics">
                    <div class="metric">
                        <label>Engagement</label>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${student.engagement_score}%"></div>
                        </div>
                        <span class="metric-value">${student.engagement_score}%</span>
                    </div>
                    <div class="metric">
                        <label>Progress</label>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${student.progress_percentage}%"></div>
                        </div>
                        <span class="metric-value">${student.progress_percentage}%</span>
                    </div>
                </div>
                <div class="student-actions">
                    <button class="btn btn-sm btn-primary" onclick="analyticsDashboard.viewStudentDetails('${student.id}')">
                        <i class="fas fa-chart-line"></i> Details
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="analyticsDashboard.contactStudent('${student.id}')">
                        <i class="fas fa-envelope"></i> Contact
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = studentsHTML;
    }

    /**
     * View Detailed Analytics for a Specific Student
     *
     * BUSINESS LOGIC:
     * Fetches and displays comprehensive analytics for an individual student
     * in a modal, including activity, lab performance, quiz results, and recommendations.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Shows loading state
     * - Fetches student analytics from API with authentication
     * - Renders detailed modal with multiple analytics sections
     * - Shows modal and hides loading on completion
     * - Handles errors gracefully
     *
     * WHY THIS MATTERS:
     * Detailed individual analytics enable instructors to provide personalized
     * feedback and targeted interventions.
     *
     * @async
     * @param {string} studentId - Unique identifier for the student
     * @returns {Promise<void>}
     * @throws {Error} If student details cannot be loaded
     */
    async viewStudentDetails(studentId) {
        try {
            // Show student details modal
            const modal = document.getElementById('studentDetailsModal');
            if (!modal) return;

            this.showLoading('Loading student details...');
            
            const response = await fetch(`${this.analyticsAPI}/analytics/student/${studentId}?course_id=${this.currentCourse}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const studentAnalytics = await response.json();
            
            this.renderStudentDetailsModal(studentAnalytics);
            this.showModal(modal);
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading student details:', error);
            this.showError('Failed to load student details');
            this.hideLoading();
        }
    }

    /**
     * Render Student Details Modal Content
     *
     * BUSINESS LOGIC:
     * Generates HTML for student analytics modal showing comprehensive
     * performance data and AI-generated recommendations.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Renders activity summary metrics
     * - Displays lab performance statistics
     * - Shows quiz performance data
     * - Lists AI-generated recommendations
     * - Formats dates and numbers for display
     * - Injects HTML into modal body
     *
     * WHY THIS MATTERS:
     * Organized presentation of student data helps instructors quickly
     * assess performance and identify action items.
     *
     * @param {Object} analytics - Student analytics data object
     * @param {string} analytics.student_id - Student identifier
     * @param {Object} analytics.analysis_period - Date range of analysis
     * @param {Object} analytics.activity_summary - Student activity metrics
     * @param {Object} analytics.lab_metrics - Lab performance data
     * @param {Object} analytics.quiz_performance - Quiz performance data
     * @param {number} analytics.engagement_score - Overall engagement score
     * @param {Array} analytics.recommendations - AI-generated recommendations
     * @returns {void}
     */
    renderStudentDetailsModal(analytics) {
        const modalBody = document.querySelector('#studentDetailsModal .modal-body');
        if (!modalBody) return;

        modalBody.innerHTML = `
            <div class="student-analytics-details">
                <div class="analytics-header">
                    <h3>Student Analytics: ${analytics.student_id}</h3>
                    <p class="analysis-period">
                        Analysis Period: ${this.formatDate(analytics.analysis_period.start_date)} - 
                        ${this.formatDate(analytics.analysis_period.end_date)}
                    </p>
                </div>
                
                <div class="analytics-sections">
                    <div class="analytics-section">
                        <h4><i class="fas fa-chart-bar"></i> Activity Summary</h4>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <span class="metric-label">Total Activities</span>
                                <span class="metric-value">${analytics.activity_summary.total_activities}</span>
                            </div>
                            <div class="metric-item">  
                                <span class="metric-label">Engagement Score</span>
                                <span class="metric-value">${analytics.engagement_score}%</span>
                            </div>
                        </div>
                    </div>

                    <div class="analytics-section">
                        <h4><i class="fas fa-flask"></i> Lab Performance</h4>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <span class="metric-label">Total Sessions</span>
                                <span class="metric-value">${analytics.lab_metrics.total_sessions}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Avg Duration</span>
                                <span class="metric-value">${analytics.lab_metrics.average_session_duration.toFixed(1)} min</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Code Executions</span>
                                <span class="metric-value">${analytics.lab_metrics.average_code_executions.toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Avg Errors</span>
                                <span class="metric-value">${analytics.lab_metrics.average_errors.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>

                    <div class="analytics-section">
                        <h4><i class="fas fa-question-circle"></i> Quiz Performance</h4>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <span class="metric-label">Average Score</span>
                                <span class="metric-value">${analytics.quiz_performance.average_score.toFixed(1)}%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Total Quizzes</span>
                                <span class="metric-value">${analytics.quiz_performance.total_quizzes}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Pass Rate</span>
                                <span class="metric-value">${analytics.quiz_performance.pass_rate.toFixed(1)}%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Avg Duration</span>
                                <span class="metric-value">${analytics.quiz_performance.average_duration.toFixed(1)} min</span>
                            </div>
                        </div>
                    </div>

                    <div class="analytics-section">
                        <h4><i class="fas fa-lightbulb"></i> Recommendations</h4>
                        <ul class="recommendations-list">
                            ${analytics.recommendations.map(rec => `<li><i class="fas fa-arrow-right"></i> ${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Contact Student (Placeholder)
     *
     * BUSINESS LOGIC:
     * Opens interface for contacting a student via email, messaging, or
     * other communication channels.
     *
     * TECHNICAL IMPLEMENTATION:
     * - TODO: Implement student contact functionality
     * - Could open email modal, messaging interface, or external tool
     *
     * WHY THIS MATTERS:
     * Easy student contact enables quick follow-up on analytics insights.
     *
     * @async
     * @param {string} studentId - Unique identifier for the student to contact
     * @returns {Promise<void>}
     */
    async contactStudent(studentId) {
        // Implement student contact functionality
        // This could open a modal for sending messages, emails, etc.
    }

    /**
     * Search Students by Name or Email
     *
     * BUSINESS LOGIC:
     * Filters the displayed student list based on user's search query,
     * matching against student name and email.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Converts query to lowercase for case-insensitive search
     * - Iterates through all student card elements
     * - Shows/hides cards based on name/email match
     * - Uses CSS display property for filtering
     *
     * WHY THIS MATTERS:
     * Search enables quick navigation to specific students in large classes.
     *
     * @param {string} query - Search query string
     * @returns {void}
     */
    searchStudents(query) {
        const studentCards = document.querySelectorAll('.student-analytics-card');
        const searchTerm = query.toLowerCase();

        studentCards.forEach(card => {
            const studentName = card.querySelector('.student-details h4').textContent.toLowerCase();
            const studentEmail = card.querySelector('.student-email').textContent.toLowerCase();
            
            if (studentName.includes(searchTerm) || studentEmail.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    /**
     * Update Analytics Time Range
     *
     * BUSINESS LOGIC:
     * Reloads analytics data for the currently selected course with a new
     * time range (number of days back).
     *
     * TECHNICAL IMPLEMENTATION:
     * - Validates current course is selected
     * - Converts daysBack string to integer
     * - Triggers analytics reload with new time range
     *
     * WHY THIS MATTERS:
     * Time range flexibility enables historical analysis and trend identification.
     *
     * @async
     * @param {string|number} daysBack - Number of days of historical data to load
     * @returns {Promise<void>}
     */
    async updateTimeRange(daysBack) {
        if (this.currentCourse) {
            await this.loadCourseAnalytics(this.currentCourse, parseInt(daysBack));
        }
    }

    /**
     * Refresh Analytics Data
     *
     * BUSINESS LOGIC:
     * Reloads analytics data for the currently selected course and time range,
     * fetching fresh data from the API.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Validates current course is selected
     * - Reads current time range from UI
     * - Triggers full analytics reload
     *
     * WHY THIS MATTERS:
     * Manual refresh ensures instructors see the most current data after
     * student activity or system updates.
     *
     * @async
     * @returns {Promise<void>}
     */
    async refreshAnalytics() {
        if (this.currentCourse) {
            const timeRange = document.getElementById('analyticsTimeRange')?.value || 30;
            await this.loadCourseAnalytics(this.currentCourse, parseInt(timeRange));
        }
    }

    /**
     * Export Analytics Data as JSON
     *
     * BUSINESS LOGIC:
     * Downloads analytics data as a JSON file for offline analysis,
     * archival, or integration with external tools.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Shows loading state
     * - Creates export data object with course, date, and chart data
     * - Converts to JSON blob
     * - Triggers browser download
     * - Cleans up blob URL
     * - Shows success message
     *
     * WHY THIS MATTERS:
     * Data export enables external analysis, reporting, and long-term archival.
     *
     * @async
     * @returns {Promise<void>}
     * @throws {Error} If export fails
     */
    async exportAnalytics() {
        try {
            this.showLoading('Exporting analytics...');
            
            // Create export data
            const exportData = {
                course_id: this.currentCourse,
                export_date: new Date().toISOString(),
                charts_data: this.charts
            };

            // Download as JSON
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `course-analytics-${this.currentCourse}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.hideLoading();
            this.showSuccess('Analytics exported successfully');
            
        } catch (error) {
            console.error('Error exporting analytics:', error);
            this.showError('Failed to export analytics');
            this.hideLoading();
        }
    }

    // Utility methods

    /**
     * Generate Score Distribution from Average and Standard Deviation
     *
     * BUSINESS LOGIC:
     * Simulates a normal distribution of quiz scores based on average
     * and standard deviation to visualize performance distribution.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Uses Gaussian distribution formula
     * - Calculates weights for 5 score ranges (0-20%, 21-40%, etc.)
     * - Distributes total attempts across ranges based on weights
     * - Returns array of counts for each range
     *
     * WHY THIS MATTERS:
     * Distribution simulation provides realistic visualization when
     * detailed score breakdowns aren't available from API.
     *
     * @param {number} avgScore - Average quiz score (0-100)
     * @param {number} stdDev - Standard deviation of scores
     * @param {number} totalAttempts - Total number of quiz attempts
     * @returns {number[]} Array of student counts for each score range
     */
    generateScoreDistribution(avgScore, stdDev, totalAttempts) {
        // Simple distribution simulation based on normal distribution
        const ranges = [10, 30, 50, 70, 90]; // Mid-points of ranges
        const distribution = [];
        
        for (let i = 0; i < ranges.length; i++) {
            const distance = Math.abs(ranges[i] - avgScore);
            const weight = Math.exp(-(distance * distance) / (2 * stdDev * stdDev));
            distribution.push(Math.round(weight * totalAttempts / 5));
        }
        
        return distribution;
    }

    /**
     * Format Date String for Display
     *
     * BUSINESS LOGIC:
     * Converts ISO date strings to localized, human-readable format for
     * consistent date presentation in analytics displays.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Parses ISO date string to Date object
     * - Formats to localized date and time strings
     * - Combines date and time with space separator
     *
     * WHY THIS MATTERS:
     * Consistent, readable date formatting improves UX and prevents
     * confusion from technical date formats.
     *
     * @param {string} dateString - ISO format date string
     * @returns {string} Formatted date and time string
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    /**
     * Show Modal Dialog
     *
     * BUSINESS LOGIC:
     * Displays a modal dialog element by setting display and adding show class.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Sets modal display to block
     * - Adds show class for CSS transitions
     *
     * WHY THIS MATTERS:
     * Centralized modal display logic ensures consistent modal behavior.
     *
     * @param {HTMLElement} modal - Modal element to show
     * @returns {void}
     */
    showModal(modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
    }

    /**
     * Hide Modal Dialog
     *
     * BUSINESS LOGIC:
     * Hides a modal dialog element by removing display and show class.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Sets modal display to none
     * - Removes show class for CSS transitions
     *
     * WHY THIS MATTERS:
     * Centralized modal hiding logic ensures consistent modal behavior.
     *
     * @param {HTMLElement} modal - Modal element to hide
     * @returns {void}
     */
    hideModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }

    /**
     * Show Loading Indicator
     *
     * BUSINESS LOGIC:
     * Displays a loading message to inform users that data is being fetched.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates loading element text content
     * - Sets loading element display to block
     *
     * WHY THIS MATTERS:
     * Loading indicators improve perceived performance and prevent
     * user confusion during data fetches.
     *
     * @param {string} [message='Loading...'] - Custom loading message to display
     * @returns {void}
     */
    showLoading(message = 'Loading...') {
        const loadingEl = document.getElementById('analyticsLoading');
        if (loadingEl) {
            loadingEl.textContent = message;
            loadingEl.style.display = 'block';
        }
    }

    /**
     * Hide Loading Indicator
     *
     * BUSINESS LOGIC:
     * Hides the loading indicator when data fetching completes.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Sets loading element display to none
     *
     * WHY THIS MATTERS:
     * Removing loading indicators signals task completion to users.
     *
     * @returns {void}
     */
    hideLoading() {
        const loadingEl = document.getElementById('analyticsLoading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }

    /**
     * Show Error Message
     *
     * BUSINESS LOGIC:
     * Displays an error message to the user and auto-hides after 5 seconds.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates error element text content
     * - Sets error element display to block
     * - Sets 5-second timeout to auto-hide
     *
     * WHY THIS MATTERS:
     * User-friendly error messages improve experience and help with
     * troubleshooting without blocking the UI permanently.
     *
     * @param {string} message - Error message to display
     * @returns {void}
     */
    showError(message) {
        const errorEl = document.getElementById('analyticsError');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * Show Success Message
     *
     * BUSINESS LOGIC:
     * Displays a success message to the user and auto-hides after 3 seconds.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates success element text content
     * - Sets success element display to block
     * - Sets 3-second timeout to auto-hide
     *
     * WHY THIS MATTERS:
     * Success feedback confirms user actions completed successfully
     * and provides positive reinforcement.
     *
     * @param {string} message - Success message to display
     * @returns {void}
     */
    showSuccess(message) {
        const successEl = document.getElementById('analyticsSuccess');
        if (successEl) {
            successEl.textContent = message;
            successEl.style.display = 'block';
            setTimeout(() => {
                successEl.style.display = 'none';
            }, 3000);
        }
    }

    /**
     * Download PDF Analytics Report
     *
     * BUSINESS LOGIC:
     * Generates and downloads a formatted PDF report of analytics data for
     * the selected course and time range.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Validates course selection
     * - Shows loading state
     * - Retrieves time range from UI
     * - Previews report data before download
     * - Fetches PDF from Analytics API with authentication
     * - Triggers browser download of PDF blob
     * - Cleans up blob URL after download
     * - Shows success/error feedback
     *
     * WHY THIS MATTERS:
     * PDF reports enable professional presentation, sharing with stakeholders,
     * and archival of analytics data.
     *
     * @async
     * @returns {Promise<void>}
     * @throws {Error} If PDF generation or download fails
     */
    async downloadPDFReport() {
        try {
            if (!this.currentCourse) {
                this.showError('Please select a course first');
                return;
            }

            this.showLoading('Generating PDF report...');

            // Get date range from UI
            const timeRange = this.getSelectedTimeRange();
            
            // Preview the report data first
            await this.previewReportData();

            // Construct PDF download URL
            const params = new URLSearchParams();
            if (timeRange.startDate) {
                params.append('start_date', timeRange.startDate);
            }
            if (timeRange.endDate) {
                params.append('end_date', timeRange.endDate);
            }

            const url = `${this.analyticsAPI}/analytics/reports/course/${this.currentCourse}/pdf?${params}`;

            // Create download link
            const link = document.createElement('a');
            link.href = url;
            link.download = `analytics_report_${this.currentCourse}_${new Date().toISOString().split('T')[0]}.pdf`;
            
            // Add authorization header by using fetch and blob
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            link.href = downloadUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up
            window.URL.revokeObjectURL(downloadUrl);

            this.hideLoading();
            this.showSuccess('PDF report downloaded successfully!');

        } catch (error) {
            console.error('Error downloading PDF report:', error);
            this.showError('Failed to download PDF report: ' + error.message);
            this.hideLoading();
        }
    }

    /**
     * Preview Report Data Before PDF Generation
     *
     * BUSINESS LOGIC:
     * Fetches a preview of report data to show users what will be included
     * in the PDF before generation.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Constructs preview API URL with time range parameters
     * - Fetches preview data from Analytics API
     * - Displays preview modal/notification
     * - Continues with download even if preview fails
     *
     * WHY THIS MATTERS:
     * Preview functionality helps users verify report contents and
     * understand what data will be included.
     *
     * @async
     * @returns {Promise<Object|null>} Preview data object or null if fails
     */
    async previewReportData() {
        try {
            const timeRange = this.getSelectedTimeRange();
            const params = new URLSearchParams();
            if (timeRange.startDate) {
                params.append('start_date', timeRange.startDate);
            }
            if (timeRange.endDate) {
                params.append('end_date', timeRange.endDate);
            }

            const response = await fetch(`${this.analyticsAPI}/analytics/reports/preview/${this.currentCourse}?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const previewData = await response.json();
            
            // Show preview modal or notification
            this.showReportPreview(previewData);
            
            return previewData;

        } catch (error) {
            console.error('Error previewing report data:', error);
            // Continue with download even if preview fails
            return null;
        }
    }

    /**
     * Show Report Preview Information
     *
     * BUSINESS LOGIC:
     * Displays a preview summary of the PDF report contents including
     * course info, date range, student count, and estimated pages.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Formats preview data into user-friendly message
     * - Displays success message with preview info
     * - Could be enhanced to show modal in future
     *
     * WHY THIS MATTERS:
     * Preview information sets expectations and confirms the report
     * will contain the desired data.
     *
     * @param {Object} previewData - Report preview data from API
     * @param {Object} previewData.course_info - Course information
     * @param {Object} previewData.date_range - Report date range
     * @param {Object} previewData.key_metrics - Summary metrics
     * @param {number} previewData.estimated_pages - Estimated PDF page count
     * @returns {void}
     */
    showReportPreview(previewData) {
        const message = `
            Report Preview:
            • Course: ${previewData.course_info?.title || 'Unknown'}
            • Date Range: ${previewData.date_range?.start_date?.split('T')[0]} to ${previewData.date_range?.end_date?.split('T')[0]}
            • Students: ${previewData.key_metrics?.total_students || 0}
            • Estimated Pages: ${previewData.estimated_pages || 'Unknown'}
        `;
        
        
        // Could show a modal here in the future
        this.showSuccess('Report preview loaded - generating PDF...');
    }

    /**
     * Get Selected Time Range as Date Objects
     *
     * BUSINESS LOGIC:
     * Converts the selected time range dropdown value into start and end
     * date objects for API queries.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Reads selected time range from UI (default 30 days)
     * - Calculates start date by subtracting days from current date
     * - Returns ISO date strings for API compatibility
     *
     * WHY THIS MATTERS:
     * Proper date range calculation ensures accurate historical data
     * retrieval from the API.
     *
     * @returns {Object} Object with startDate and endDate as ISO strings
     * @returns {string} return.startDate - ISO format start date
     * @returns {string} return.endDate - ISO format end date (today)
     */
    getSelectedTimeRange() {
        const timeRangeSelect = document.getElementById('analyticsTimeRange');
        const selectedRange = timeRangeSelect ? timeRangeSelect.value : '30';
        
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - parseInt(selectedRange));
        
        return {
            startDate: startDate.toISOString().split('T')[0],
            endDate: endDate.toISOString().split('T')[0]
        };
    }

    /**
     * Download PDF Report for Individual Student
     *
     * BUSINESS LOGIC:
     * Generates and downloads a personalized PDF analytics report for
     * a specific student showing their performance and progress.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Validates student ID is provided
     * - Shows loading state
     * - Constructs API URL with course and date range parameters
     * - Fetches PDF from Analytics API with authentication
     * - Triggers browser download of PDF blob
     * - Cleans up blob URL after download
     * - Shows success/error feedback
     *
     * WHY THIS MATTERS:
     * Individual student reports enable personalized feedback and
     * documentation of student progress for academic records.
     *
     * @async
     * @param {string} studentId - Unique identifier for the student
     * @returns {Promise<void>}
     * @throws {Error} If PDF generation or download fails
     */
    async downloadStudentPDFReport(studentId) {
        try {
            if (!studentId) {
                this.showError('Student ID is required');
                return;
            }

            this.showLoading('Generating student PDF report...');

            const timeRange = this.getSelectedTimeRange();
            const params = new URLSearchParams();
            if (this.currentCourse) {
                params.append('course_id', this.currentCourse);
            }
            if (timeRange.startDate) {
                params.append('start_date', timeRange.startDate);
            }
            if (timeRange.endDate) {
                params.append('end_date', timeRange.endDate);
            }

            const url = `${this.analyticsAPI}/analytics/reports/student/${studentId}/pdf?${params}`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `student_report_${studentId}_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            window.URL.revokeObjectURL(downloadUrl);

            this.hideLoading();
            this.showSuccess('Student PDF report downloaded successfully!');

        } catch (error) {
            console.error('Error downloading student PDF report:', error);
            this.showError('Failed to download student PDF report: ' + error.message);
            this.hideLoading();
        }
    }
}

// Create global instance
const analyticsDashboard = new AnalyticsDashboard();

// Export for ES6 modules
export default AnalyticsDashboard;