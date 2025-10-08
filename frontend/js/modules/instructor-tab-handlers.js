/**
 * Instructor Dashboard Tab Handlers
 *
 * BUSINESS REQUIREMENT:
 * Provides interactive functionality for all instructor dashboard tabs including
 * course creation, student management, analytics, and content generation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Modular initialization functions for each tab
 * - Event handlers for forms and buttons
 * - API integration with backend services
 * - Real-time data updates and validation
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Each init function handles one tab's functionality
 * - Open/Closed: Easy to extend with new tab handlers
 * - Dependency Inversion: Uses CONFIG for API endpoints
 */

import { FileExplorer } from './file-explorer.js';

/**
 * Initialize Create Course Tab Functionality
 *
 * Handles course creation form submission and AI generation
 */
export function initCreateCourseTab() {
    console.log('🎓 Initializing Create Course Tab');

    const form = document.getElementById('courseForm');
    if (!form) {
        console.warn('Course form not found');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const courseData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: formData.get('category'),
            difficulty_level: formData.get('difficulty_level'),
            estimated_duration: parseInt(formData.get('estimated_duration')),
            duration_unit: formData.get('duration_unit')
        };

        try {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

            // Get auth token and user info
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            // Create course via API
            const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/courses`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    ...courseData,
                    instructor_id: currentUser.id,
                    organization_id: currentUser.organization_id,
                    status: 'draft'
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to create course: ${response.statusText}`);
            }

            const result = await response.json();

            // Show success message
            alert(`Course "${courseData.title}" created successfully! You can now add content to it.`);

            // Reset form
            form.reset();

            // Navigate to courses tab
            if (typeof showSection === 'function') {
                showSection('courses');
            }

        } catch (error) {
            console.error('Error creating course:', error);
            alert(`Error creating course: ${error.message}`);
        } finally {
            // Restore button
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Course with AI';
            }
        }
    });

    // Reset button handler
    window.resetForm = function() {
        form.reset();
    };

    console.log('✅ Create Course Tab initialized');
}

/**
 * Initialize Students Tab Functionality
 *
 * Handles student enrollment (single and bulk) and student listing
 */
export function initStudentsTab() {
    console.log('👥 Initializing Students Tab');

    // Load courses for selection
    loadInstructorCourses();

    // Single enrollment form
    const singleForm = document.getElementById('singleEnrollmentForm');
    if (singleForm) {
        singleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await enrollStudent(document.getElementById('studentEmail').value);
            singleForm.reset();
        });
    }

    // Bulk enrollment form
    const bulkForm = document.getElementById('bulkEnrollmentForm');
    if (bulkForm) {
        bulkForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emails = document.getElementById('studentEmails').value
                .split('\n')
                .map(email => email.trim())
                .filter(email => email.length > 0);

            await enrollStudentsBulk(emails);
            bulkForm.reset();
        });
    }

    // Course selector change handler
    window.loadCourseStudents = async function() {
        const courseId = document.getElementById('selectedCourse').value;
        if (!courseId) return;

        await loadEnrolledStudents(courseId);
    };

    console.log('✅ Students Tab initialized');
}

/**
 * Load instructor's courses into select dropdown
 */
async function loadInstructorCourses() {
    const selectElement = document.getElementById('selectedCourse');
    if (!selectElement) return;

    try {
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/courses?instructor_id=${currentUser.id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to load courses');

        const courses = await response.json();

        selectElement.innerHTML = '<option value="">Select a course...</option>';
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            selectElement.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

/**
 * Enroll a single student
 */
async function enrollStudent(email) {
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        alert('Please select a course first');
        return;
    }

    try {
        const authToken = localStorage.getItem('authToken');

        const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/enrollments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                course_id: parseInt(courseId),
                student_email: email
            })
        });

        if (!response.ok) throw new Error('Enrollment failed');

        alert(`Student ${email} enrolled successfully!`);
        await loadEnrolledStudents(courseId);

    } catch (error) {
        console.error('Error enrolling student:', error);
        alert(`Error: ${error.message}`);
    }
}

/**
 * Enroll multiple students in bulk
 */
async function enrollStudentsBulk(emails) {
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        alert('Please select a course first');
        return;
    }

    let successCount = 0;
    let failCount = 0;

    for (const email of emails) {
        try {
            await enrollStudent(email);
            successCount++;
        } catch (error) {
            failCount++;
        }
    }

    alert(`Bulk enrollment complete!\nSuccess: ${successCount}\nFailed: ${failCount}`);
}

/**
 * Load enrolled students for a course
 */
async function loadEnrolledStudents(courseId) {
    const container = document.getElementById('enrolled-students-list');
    if (!container) return;

    container.innerHTML = '<p>Loading students...</p>';

    try {
        const authToken = localStorage.getItem('authToken');

        const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/courses/${courseId}/students`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to load students');

        const students = await response.json();

        if (students.length === 0) {
            container.innerHTML = '<p>No students enrolled yet.</p>';
            return;
        }

        container.innerHTML = `
            <table class="students-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Enrolled Date</th>
                        <th>Progress</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(student => `
                        <tr>
                            <td>${student.name || 'N/A'}</td>
                            <td>${student.email}</td>
                            <td>${new Date(student.enrolled_at).toLocaleDateString()}</td>
                            <td>${student.progress || 0}%</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" onclick="unenrollStudent(${courseId}, ${student.id})">
                                    <i class="fas fa-user-minus"></i> Remove
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        console.error('Error loading students:', error);
        container.innerHTML = '<p class="error">Error loading students.</p>';
    }
}

/**
 * Initialize Analytics Tab Functionality
 *
 * Handles analytics data loading and chart rendering
 */
export function initAnalyticsTab() {
    console.log('📊 Initializing Analytics Tab');

    // Load courses for analytics filter
    loadAnalyticsCourses();

    // Refresh button
    const refreshBtn = document.getElementById('refreshAnalyticsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAnalyticsData);
    }

    // Export button
    const exportBtn = document.getElementById('exportAnalyticsBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportAnalyticsData);
    }

    // PDF download button
    const pdfBtn = document.getElementById('downloadPDFReportBtn');
    if (pdfBtn) {
        pdfBtn.addEventListener('click', downloadPDFReport);
    }

    // Course selector change
    const courseSelect = document.getElementById('analyticsCourseSelect');
    if (courseSelect) {
        courseSelect.addEventListener('change', loadAnalyticsData);
    }

    // Time range selector change
    const timeRange = document.getElementById('analyticsTimeRange');
    if (timeRange) {
        timeRange.addEventListener('change', loadAnalyticsData);
    }

    // Load initial data
    loadAnalyticsData();

    console.log('✅ Analytics Tab initialized');
}

/**
 * Load courses for analytics filter
 */
async function loadAnalyticsCourses() {
    const selectElement = document.getElementById('analyticsCourseSelect');
    if (!selectElement) return;

    try {
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/courses?instructor_id=${currentUser.id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to load courses');

        const courses = await response.json();

        selectElement.innerHTML = '<option value="">All Courses</option>';
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            selectElement.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

/**
 * Load analytics data
 */
async function loadAnalyticsData() {
    const courseId = document.getElementById('analyticsCourseSelect')?.value;
    const timeRange = document.getElementById('analyticsTimeRange')?.value || '30';

    // Show loading
    const loading = document.getElementById('analyticsLoading');
    if (loading) loading.style.display = 'block';

    try {
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        const url = new URL(`${window.CONFIG.API_URLS.ANALYTICS}/instructor/analytics`);
        url.searchParams.append('instructor_id', currentUser.id);
        if (courseId) url.searchParams.append('course_id', courseId);
        url.searchParams.append('time_range', timeRange);

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to load analytics');

        const data = await response.json();

        // Update overview cards
        document.getElementById('totalStudentsCount').textContent = data.total_students || 0;
        document.getElementById('activeStudentsCount').textContent = data.active_students || 0;
        document.getElementById('avgQuizScore').textContent = `${data.avg_quiz_score || 0}%`;

        // Update lab completion rate if present
        const labCompletionEl = document.getElementById('labCompletionRate');
        if (labCompletionEl) {
            labCompletionEl.textContent = `${data.lab_completion_rate || 0}%`;
        }

        // Render charts with Chart.js
        renderAnalyticsCharts(data);

    } catch (error) {
        console.error('Error loading analytics:', error);
        const errorDiv = document.getElementById('analyticsError');
        if (errorDiv) {
            errorDiv.textContent = `Error loading analytics: ${error.message}`;
            errorDiv.style.display = 'block';
        }
    } finally {
        if (loading) loading.style.display = 'none';
    }
}

/**
 * Render analytics charts using Chart.js
 *
 * Creates 4 interactive charts:
 * 1. Student Engagement Over Time (Line chart)
 * 2. Lab Completion Status (Doughnut chart)
 * 3. Quiz Score Distribution (Bar chart)
 * 4. Content Progress Distribution (Horizontal bar chart)
 */
function renderAnalyticsCharts(data) {
    console.log('📊 Rendering analytics charts with data:', data);

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }

    // Destroy existing charts to prevent canvas reuse errors
    destroyExistingCharts();

    // 1. Student Engagement Over Time (Line Chart)
    renderEngagementChart(data);

    // 2. Lab Completion Status (Doughnut Chart)
    renderLabCompletionChart(data);

    // 3. Quiz Score Distribution (Bar Chart)
    renderQuizPerformanceChart(data);

    // 4. Content Progress Distribution (Horizontal Bar Chart)
    renderProgressDistributionChart(data);

    console.log('✅ All charts rendered successfully');
}

/**
 * Global chart instances for cleanup
 */
let chartInstances = {
    engagement: null,
    labCompletion: null,
    quizPerformance: null,
    progressDistribution: null
};

/**
 * Destroy existing charts before creating new ones
 */
function destroyExistingCharts() {
    Object.keys(chartInstances).forEach(key => {
        if (chartInstances[key]) {
            chartInstances[key].destroy();
            chartInstances[key] = null;
        }
    });
}

/**
 * Render Student Engagement Over Time Chart (Line)
 */
function renderEngagementChart(data) {
    const ctx = document.getElementById('engagementChart');
    if (!ctx) return;

    // Sample data - replace with real data from API
    const engagementData = data.engagement_over_time || {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
        active_students: [45, 52, 48, 55, 58, 54, 60, 62],
        course_completions: [5, 8, 12, 15, 18, 22, 25, 28],
        lab_submissions: [30, 35, 40, 45, 48, 50, 55, 58]
    };

    chartInstances.engagement = new Chart(ctx, {
        type: 'line',
        data: {
            labels: engagementData.labels,
            datasets: [
                {
                    label: 'Active Students',
                    data: engagementData.active_students,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Course Completions',
                    data: engagementData.course_completions,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Lab Submissions',
                    data: engagementData.lab_submissions,
                    borderColor: 'rgb(168, 85, 247)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Render Lab Completion Status Chart (Doughnut)
 */
function renderLabCompletionChart(data) {
    const ctx = document.getElementById('labCompletionChart');
    if (!ctx) return;

    const labData = data.lab_completion || {
        completed: 45,
        in_progress: 28,
        not_started: 15,
        overdue: 12
    };

    chartInstances.labCompletion = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Progress', 'Not Started', 'Overdue'],
            datasets: [{
                data: [
                    labData.completed,
                    labData.in_progress,
                    labData.not_started,
                    labData.overdue
                ],
                backgroundColor: [
                    'rgb(34, 197, 94)',   // Green - Completed
                    'rgb(59, 130, 246)',  // Blue - In Progress
                    'rgb(156, 163, 175)', // Gray - Not Started
                    'rgb(239, 68, 68)'    // Red - Overdue
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render Quiz Score Distribution Chart (Bar)
 */
function renderQuizPerformanceChart(data) {
    const ctx = document.getElementById('quizPerformanceChart');
    if (!ctx) return;

    const quizData = data.quiz_scores || {
        ranges: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
        counts: [2, 8, 15, 25, 50]
    };

    chartInstances.quizPerformance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: quizData.ranges,
            datasets: [{
                label: 'Number of Students',
                data: quizData.counts,
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',   // Red - Very Low
                    'rgba(251, 146, 60, 0.8)',  // Orange - Low
                    'rgba(250, 204, 21, 0.8)',  // Yellow - Medium
                    'rgba(132, 204, 22, 0.8)',  // Light Green - Good
                    'rgba(34, 197, 94, 0.8)'    // Green - Excellent
                ],
                borderColor: [
                    'rgb(239, 68, 68)',
                    'rgb(251, 146, 60)',
                    'rgb(250, 204, 21)',
                    'rgb(132, 204, 22)',
                    'rgb(34, 197, 94)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${value} students (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: 'Number of Students'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Score Range'
                    }
                }
            }
        }
    });
}

/**
 * Render Content Progress Distribution Chart (Horizontal Bar)
 */
function renderProgressDistributionChart(data) {
    const ctx = document.getElementById('progressDistributionChart');
    if (!ctx) return;

    const progressData = data.progress_distribution || {
        ranges: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
        counts: [5, 12, 20, 30, 33]
    };

    chartInstances.progressDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: progressData.ranges,
            datasets: [{
                label: 'Number of Students',
                data: progressData.counts,
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 2,
                indexAxis: 'y' // This makes it horizontal
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.x;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${value} students (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: 'Number of Students'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Progress Range'
                    }
                }
            }
        }
    });
}

/**
 * Export analytics data to CSV
 */
function exportAnalyticsData() {
    alert('Analytics export functionality coming soon!');
    // TODO: Implement CSV export
}

/**
 * Download PDF report
 */
function downloadPDFReport() {
    alert('PDF report generation coming soon!');
    // TODO: Implement PDF generation
}

/**
 * Initialize Courses Tab Functionality
 *
 * Handles course listing and management
 */
export function initCoursesTab() {
    console.log('📚 Initializing Courses Tab');

    // Load courses list
    loadCoursesList();

    console.log('✅ Courses Tab initialized');
}

/**
 * Load instructor's courses list
 */
async function loadCoursesList() {
    const container = document.getElementById('courses-list');
    if (!container) {
        console.warn('Courses list container not found');
        return;
    }

    container.innerHTML = '<p>Loading courses...</p>';

    try {
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        const response = await fetch(`${window.CONFIG.API_URLS.COURSE_MANAGEMENT}/courses?instructor_id=${currentUser.id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) throw new Error('Failed to load courses');

        const courses = await response.json();

        if (courses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book-open fa-3x"></i>
                    <h3>No courses yet</h3>
                    <p>Create your first course to get started!</p>
                    <button class="btn btn-primary" onclick="showSection('create-course')">
                        <i class="fas fa-plus"></i> Create Course
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="courses-grid">
                ${courses.map(course => `
                    <div class="course-card">
                        <div class="course-card-header">
                            <h3>${course.title}</h3>
                            <span class="course-badge ${course.status}">${course.status}</span>
                        </div>
                        <p class="course-description">${course.description || 'No description'}</p>
                        <div class="course-meta">
                            <span><i class="fas fa-users"></i> ${course.student_count || 0} students</span>
                            <span><i class="fas fa-clock"></i> ${course.estimated_duration || 0} ${course.duration_unit || 'hours'}</span>
                        </div>
                        <div class="course-actions">
                            <button class="btn btn-sm btn-primary" onclick="editCourse(${course.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewCourse(${course.id})">
                                <i class="fas fa-eye"></i> View
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

    } catch (error) {
        console.error('Error loading courses:', error);
        container.innerHTML = '<p class="error">Error loading courses.</p>';
    }
}

/**
 * Initialize Overview Tab (default tab)
 */
export function initOverviewTab() {
    console.log('📊 Initializing Overview Tab');

    // Load overview statistics
    loadOverviewStats();

    console.log('✅ Overview Tab initialized');
}

/**
 * Load overview statistics
 */
async function loadOverviewStats() {
    try {
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        // Load quick stats
        const response = await fetch(`${window.CONFIG.API_URLS.ANALYTICS}/instructor/overview?instructor_id=${currentUser.id}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            console.warn('Failed to load overview stats');
            return;
        }

        const stats = await response.json();

        // Update stat cards
        if (document.getElementById('totalStudents')) {
            document.getElementById('totalStudents').textContent = stats.total_students || 0;
        }
        if (document.getElementById('activeCourses')) {
            document.getElementById('activeCourses').textContent = stats.active_courses || 0;
        }

    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

/**
 * Initialize Files Tab
 *
 * BUSINESS REQUIREMENT:
 * Provides instructors with file management capabilities for course materials
 * including upload, delete, download, and preview of files.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses FileExplorer widget for full file management UI
 * - Automatically loads files for instructor's organization
 * - Enforces RBAC for file operations
 */
export function initFilesTab() {
    console.log('📁 Initializing Files Tab');

    const container = document.getElementById('instructorFileExplorerContainer');
    if (!container) {
        console.error('File explorer container not found');
        return;
    }

    // Get current user context for filtering
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const organizationId = currentUser.organization_id;

    // Initialize File Explorer widget with instructor-specific options
    const fileExplorer = new FileExplorer(container, {
        organizationId: organizationId,
        allowUpload: true,
        allowDelete: true,
        allowDownload: true,
        allowPreview: true,
        enableDragDrop: true,
        multiSelect: true,
        viewMode: 'grid',
        sortBy: 'date',
        sortOrder: 'desc'
    });

    console.log('✅ Files Tab initialized with FileExplorer widget');
}

/**
 * Initialize Published Courses Tab
 *
 * BUSINESS REQUIREMENT:
 * Displays all published courses available for instantiation by instructors.
 * Instructors can filter by visibility (public/private) and view course details.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches published courses from course management API
 * - Filters courses by visibility setting
 * - Displays courses in responsive grid layout
 */
export function initPublishedCoursesTab() {
    console.log('🎓 Initializing Published Courses Tab');

    // Make filter function globally accessible for inline event handler
    window.filterPublishedCourses = filterPublishedCourses;

    // Load initial course list
    loadPublishedCourses();

    console.log('✅ Published Courses Tab initialized');
}

/**
 * Load and display published courses
 *
 * BUSINESS LOGIC:
 * - Fetches all published courses from API
 * - Applies current visibility filter
 * - Renders course cards with metadata
 */
async function loadPublishedCourses(filterValue = 'all') {
    const container = document.getElementById('publishedCoursesContainer');
    if (!container) {
        console.error('Published courses container not found');
        return;
    }

    try {
        // Show loading state
        container.innerHTML = `
            <div class="loading-indicator">
                <i class="fas fa-spinner fa-spin"></i> Loading published courses...
            </div>
        `;

        // Get current user context
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
        const authToken = localStorage.getItem('authToken');

        // Fetch published courses from API
        const response = await fetch('https://localhost:8002/api/v1/courses?status=published', {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch courses: ${response.status}`);
        }

        const courses = await response.json();

        // Apply filter
        let filteredCourses = courses;
        if (filterValue === 'public') {
            filteredCourses = courses.filter(c => c.visibility === 'public');
        } else if (filterValue === 'private') {
            filteredCourses = courses.filter(c => c.visibility === 'private' && c.instructor_id === currentUser.id);
        }

        // Render courses
        if (filteredCourses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book"></i>
                    <h3>No published courses found</h3>
                    <p>There are currently no published courses matching your filter criteria.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredCourses.map(course => `
            <div class="course-card">
                <div class="course-card-header">
                    <h3>${course.title}</h3>
                    <span class="badge badge-${course.visibility}">${course.visibility}</span>
                </div>
                <div class="course-card-body">
                    <p>${course.description || 'No description available'}</p>
                    <div class="course-metadata">
                        <span><i class="fas fa-user"></i> ${course.instructor_name || 'Unknown'}</span>
                        <span><i class="fas fa-clock"></i> ${course.estimated_duration || 'N/A'} ${course.duration_unit || ''}</span>
                        <span><i class="fas fa-signal"></i> ${course.difficulty_level || 'N/A'}</span>
                    </div>
                </div>
                <div class="course-card-footer">
                    <button class="btn btn-primary" onclick="createCourseInstance(${course.id})">
                        <i class="fas fa-plus"></i> Create Instance
                    </button>
                    <button class="btn btn-secondary" onclick="viewCourseDetails(${course.id})">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading published courses:', error);
        container.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-exclamation-circle"></i>
                <div>
                    <strong>Error Loading Courses</strong>
                    <p>Failed to load published courses. Please try again.</p>
                </div>
            </div>
        `;
    }
}

/**
 * Filter published courses by visibility
 *
 * Called by inline event handler in HTML
 */
function filterPublishedCourses() {
    const filterSelect = document.getElementById('courseVisibilityFilter');
    if (!filterSelect) {
        console.error('Visibility filter not found');
        return;
    }

    const filterValue = filterSelect.value;
    loadPublishedCourses(filterValue);
}

/**
 * Initialize Course Instances Tab
 *
 * BUSINESS REQUIREMENT:
 * Allows instructors to manage course instances (scheduled sessions)
 * including creation, filtering by status, and searching.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches course instances from course management API
 * - Provides filtering by status (scheduled, active, completed, cancelled)
 * - Includes search functionality
 * - Modal interface for creating new instances
 */
export function initCourseInstancesTab() {
    console.log('📋 Initializing Course Instances Tab');

    // Make functions globally accessible for inline event handlers
    window.showCreateInstanceModal = showCreateInstanceModal;
    window.filterInstances = filterInstances;
    window.searchInstances = searchInstances;

    // Load initial instance list
    loadCourseInstances();

    console.log('✅ Course Instances Tab initialized');
}

/**
 * Load and display course instances
 *
 * BUSINESS LOGIC:
 * - Fetches all course instances for the instructor
 * - Applies status filter and search query
 * - Renders instance cards with metadata
 */
async function loadCourseInstances(filterValue = 'all', searchQuery = '') {
    const container = document.getElementById('courseInstancesContainer');
    if (!container) {
        console.error('Course instances container not found');
        return;
    }

    try {
        // Show loading state
        container.innerHTML = `
            <div class="loading-indicator">
                <i class="fas fa-spinner fa-spin"></i> Loading course instances...
            </div>
        `;

        // Get current user context
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
        const authToken = localStorage.getItem('authToken');

        // Fetch course instances from API
        const response = await fetch('https://localhost:8002/api/v1/course-instances?instructor_id=' + currentUser.id, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch course instances: ${response.status}`);
        }

        let instances = await response.json();

        // Apply status filter
        if (filterValue !== 'all') {
            instances = instances.filter(inst => inst.status === filterValue);
        }

        // Apply search filter
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            instances = instances.filter(inst =>
                (inst.course_title || '').toLowerCase().includes(query) ||
                (inst.course_code || '').toLowerCase().includes(query)
            );
        }

        // Render instances
        if (instances.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <h3>No course instances found</h3>
                    <p>Create a new course instance to get started.</p>
                    <button class="btn btn-primary" onclick="showCreateInstanceModal()">
                        <i class="fas fa-plus"></i> Create New Instance
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = instances.map(instance => `
            <div class="instance-card" data-instance-id="${instance.id}">
                <div class="instance-card-header">
                    <div>
                        <h3>${instance.course_title || 'Untitled Course'}</h3>
                        <span class="instance-code">${instance.course_code || ''}</span>
                    </div>
                    <span class="badge badge-${instance.status || 'scheduled'}">${instance.status || 'Scheduled'}</span>
                </div>
                <div class="instance-card-body">
                    <div class="instance-metadata">
                        <div class="metadata-item">
                            <i class="fas fa-calendar"></i>
                            <span>Start: ${formatDate(instance.start_date)}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-calendar-check"></i>
                            <span>End: ${formatDate(instance.end_date)}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-users"></i>
                            <span>${instance.enrolled_count || 0} / ${instance.max_students || 'unlimited'} students</span>
                        </div>
                    </div>
                </div>
                <div class="instance-card-footer">
                    <button class="btn btn-primary" onclick="viewInstanceDetails(${instance.id})">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    <button class="btn btn-secondary" onclick="manageEnrollment(${instance.id})">
                        <i class="fas fa-user-plus"></i> Manage Enrollment
                    </button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading course instances:', error);
        container.innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-exclamation-circle"></i>
                <div>
                    <strong>Error Loading Instances</strong>
                    <p>Failed to load course instances. Please try again.</p>
                </div>
            </div>
        `;
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Filter course instances by status
 *
 * Called by inline event handler in HTML
 */
function filterInstances() {
    const filterSelect = document.getElementById('instanceStatusFilter');
    const searchInput = document.getElementById('instanceSearch');

    if (!filterSelect) {
        console.error('Status filter not found');
        return;
    }

    const filterValue = filterSelect.value;
    const searchQuery = searchInput ? searchInput.value : '';

    loadCourseInstances(filterValue, searchQuery);
}

/**
 * Search course instances
 *
 * Called by inline event handler in HTML
 */
function searchInstances() {
    const searchInput = document.getElementById('instanceSearch');
    const filterSelect = document.getElementById('instanceStatusFilter');

    if (!searchInput) {
        console.error('Search input not found');
        return;
    }

    const searchQuery = searchInput.value;
    const filterValue = filterSelect ? filterSelect.value : 'all';

    loadCourseInstances(filterValue, searchQuery);
}

/**
 * Show modal for creating a new course instance
 *
 * Called by inline event handler in HTML
 */
function showCreateInstanceModal() {
    console.log('Opening create instance modal...');

    // Create and show modal
    const modalHTML = `
        <div class="modal-overlay" id="createInstanceModal" onclick="closeModalOnOutsideClick(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2>Create New Course Instance</h2>
                    <button class="modal-close-btn" onclick="closeCreateInstanceModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="createInstanceForm">
                        <div class="form-group">
                            <label for="instanceCourseSelect">Select Course</label>
                            <select id="instanceCourseSelect" name="course_id" required>
                                <option value="">-- Select a course --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="instanceStartDate">Start Date</label>
                            <input type="date" id="instanceStartDate" name="start_date" required>
                        </div>
                        <div class="form-group">
                            <label for="instanceEndDate">End Date</label>
                            <input type="date" id="instanceEndDate" name="end_date" required>
                        </div>
                        <div class="form-group">
                            <label for="instanceMaxStudents">Max Students</label>
                            <input type="number" id="instanceMaxStudents" name="max_students" min="1" placeholder="Leave empty for unlimited">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeCreateInstanceModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="submitCreateInstance()">
                        <i class="fas fa-plus"></i> Create Instance
                    </button>
                </div>
            </div>
        </div>
    `;

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Load available courses into dropdown
    loadCoursesForInstanceCreation();

    // Make close functions globally accessible
    window.closeCreateInstanceModal = closeCreateInstanceModal;
    window.submitCreateInstance = submitCreateInstance;
    window.closeModalOnOutsideClick = closeModalOnOutsideClick;
}

/**
 * Load available courses for instance creation dropdown
 */
async function loadCoursesForInstanceCreation() {
    const select = document.getElementById('instanceCourseSelect');
    if (!select) return;

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('https://localhost:8002/api/v1/courses?status=published', {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const courses = await response.json();
            select.innerHTML = '<option value="">-- Select a course --</option>' +
                courses.map(c => `<option value="${c.id}">${c.title}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

/**
 * Close create instance modal
 */
function closeCreateInstanceModal() {
    const modal = document.getElementById('createInstanceModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Close modal when clicking outside
 */
function closeModalOnOutsideClick(event) {
    if (event.target.classList.contains('modal-overlay')) {
        closeCreateInstanceModal();
    }
}

/**
 * Submit create instance form
 */
async function submitCreateInstance() {
    const form = document.getElementById('createInstanceForm');
    if (!form || !form.checkValidity()) {
        alert('Please fill in all required fields');
        return;
    }

    const formData = new FormData(form);
    const instanceData = {
        course_id: formData.get('course_id'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        max_students: formData.get('max_students') || null,
        status: 'scheduled'
    };

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('https://localhost:8002/api/v1/course-instances', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instanceData)
        });

        if (response.ok) {
            alert('Course instance created successfully!');
            closeCreateInstanceModal();
            loadCourseInstances(); // Reload the list
        } else {
            throw new Error(`Failed to create instance: ${response.status}`);
        }
    } catch (error) {
        console.error('Error creating instance:', error);
        alert('Failed to create course instance. Please try again.');
    }
}
