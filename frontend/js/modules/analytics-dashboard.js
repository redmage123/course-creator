/**
 * Analytics Dashboard Module
 * Provides comprehensive student analytics visualization and reporting
 */



class AnalyticsDashboard {
    constructor() {
        this.analyticsAPI = window.CONFIG?.API_URLS.ANALYTICS;
        this.currentCourse = null;
        this.charts = {};
        this.initialized = false;
    }

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

    async contactStudent(studentId) {
        // Implement student contact functionality
        // This could open a modal for sending messages, emails, etc.
    }

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

    async updateTimeRange(daysBack) {
        if (this.currentCourse) {
            await this.loadCourseAnalytics(this.currentCourse, parseInt(daysBack));
        }
    }

    async refreshAnalytics() {
        if (this.currentCourse) {
            const timeRange = document.getElementById('analyticsTimeRange')?.value || 30;
            await this.loadCourseAnalytics(this.currentCourse, parseInt(timeRange));
        }
    }

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

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    showModal(modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
    }

    hideModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }

    showLoading(message = 'Loading...') {
        const loadingEl = document.getElementById('analyticsLoading');
        if (loadingEl) {
            loadingEl.textContent = message;
            loadingEl.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingEl = document.getElementById('analyticsLoading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }

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