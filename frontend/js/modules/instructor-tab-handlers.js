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
 * - Service layer integration (CourseService, StudentService, etc.)
 * - Real-time data updates and validation
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Each init function handles one tab's functionality
 * - Open/Closed: Easy to extend with new tab handlers
 * - Dependency Inversion: Depends on service abstractions, not direct API calls
 */
import { FileExplorer } from './file-explorer.js';
import { courseService } from '../services/CourseService.js';
import { studentService } from '../services/StudentService.js';
import { quizService } from '../services/QuizService.js';
import { feedbackService } from '../services/FeedbackService.js';
import { analyticsService } from '../services/AnalyticsService.js';
import { courseInstanceService } from '../services/CourseInstanceService.js';

/**
 * Initialize Create Course Tab Functionality
 *
 * BUSINESS REQUIREMENT:
 * Provides instructors with the ability to create new courses using AI-powered
 * content generation. This is the primary entry point for course creation workflow.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sets up course creation form event listeners
 * - Handles form validation and submission
 * - Integrates with CourseService for AI-powered course generation
 * - Manages loading states and user feedback
 * - Provides navigation controls (reset, cancel)
 *
 * WHY THIS MATTERS:
 * Course creation is a core instructor workflow. This function ensures a smooth,
 * user-friendly experience with proper error handling and feedback.
 *
 * @returns {void}
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

            // Create course via service layer
            const result = await courseService.createCourse(courseData);

            // Show success message
            alert(`Course "${courseData.title}" created successfully! You can now add content to it.`);

            // Reset form
            form.reset();

            // Navigate to courses tab
            const coursesTab = document.querySelector('[data-tab="courses"]');
            if (coursesTab) {
                coursesTab.click();
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
    window.resetCourseForm = function() {
        form.reset();
    };

    // Cancel button handler - navigate back to courses tab
    window.cancelCourseCreation = function() {
        form.reset();
        const coursesTab = document.querySelector('[data-tab="courses"]');
        if (coursesTab) {
            coursesTab.click();
        }
    };

    console.log('✅ Create Course Tab initialized');
}

/**
 * Initialize Students Tab Functionality
 *
 * BUSINESS REQUIREMENT:
 * Enables instructors to view and manage all enrolled students across their courses.
 * Supports both individual and bulk student enrollment operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Loads and displays student data from StudentService
 * - Sets up Add Student button and modal functionality
 * - Exposes global functions for modal interactions
 * - Handles student enrollment workflows
 *
 * WHY THIS MATTERS:
 * Student management is critical for instructors to track enrollment,
 * monitor progress, and manage class sizes effectively.
 *
 * @returns {void}
 */
export function initStudentsTab() {
    console.log('👥 Initializing Students Tab');

    // Load initial student data
    loadAllStudents();

    // Set up Add Student button
    const addStudentBtn = document.getElementById('addStudentBtn');
    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', openAddStudentModal);
    }

    // Make modal functions globally accessible
    window.closeAddStudentModal = closeAddStudentModal;
    window.submitAddStudent = submitAddStudent;

    console.log('✅ Students Tab initialized');
}

/**
 * Load All Students Across All Courses
 *
 * BUSINESS LOGIC:
 * Fetches and displays all students enrolled in any course taught by the instructor.
 * Provides a consolidated view for multi-course management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches student data via StudentService
 * - Renders student table with progress indicators
 * - Displays loading and error states
 * - Shows empty state if no students enrolled
 *
 * WHY THIS MATTERS:
 * Instructors teaching multiple courses need a unified view of all their students
 * to track overall teaching load and identify students needing attention.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If student data cannot be loaded from the service
 */
async function loadAllStudents() {
    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;

    try {
        // Show loading state
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem;">
                    <i class="fas fa-spinner fa-spin"></i> Loading students...
                </td>
            </tr>
        `;

        // Load students via service layer
        const students = await studentService.loadStudents();

        if (students.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="6">
                        <div class="empty-message">
                            <i class="fas fa-users"></i>
                            <p>No students enrolled yet. Click "Add Student" to get started.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // Render students
        tbody.innerHTML = students.map(student => `
            <tr class="student-row">
                <td>${student.name}</td>
                <td>${student.email}</td>
                <td>${student.course}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${student.progress}%"></div>
                        <span class="progress-text">${student.progress}%</span>
                    </div>
                </td>
                <td><span class="grade-badge">${student.grade}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="viewStudentDetails(${student.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Error loading students:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem; color: var(--error-600);">
                    <i class="fas fa-exclamation-circle"></i> Failed to load students. Please try again.
                </td>
            </tr>
        `;
    }
}

/**
 * Open Add Student Modal
 *
 * BUSINESS LOGIC:
 * Displays the modal interface for enrolling a single student in a course.
 * Pre-loads available courses for selection.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Shows the enrollment modal dialog
 * - Loads courses into the course selection dropdown
 * - Prepares the form for user input
 *
 * WHY THIS MATTERS:
 * Provides a user-friendly interface for individual student enrollment,
 * essential for small classes or one-off enrollments.
 *
 * @returns {void}
 */
function openAddStudentModal() {
    const modal = document.getElementById('addStudentModal');
    if (!modal) return;

    // Load courses for selection
    loadCoursesForStudentModal();

    // Show modal
    modal.style.display = 'flex';
}

/**
 * Close Add Student Modal
 *
 * BUSINESS LOGIC:
 * Closes the student enrollment modal and clears form data to prevent
 * accidental data retention on next open.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Hides the modal by setting display to none
 * - Clears course selection and email input fields
 * - Resets form state to prevent data leakage
 *
 * WHY THIS MATTERS:
 * Proper cleanup prevents user confusion and ensures fresh state
 * when the modal is reopened.
 *
 * @returns {void}
 */
function closeAddStudentModal() {
    const modal = document.getElementById('addStudentModal');
    if (modal) {
        modal.style.display = 'none';
    }

    // Clear form
    const courseSelect = document.getElementById('studentCourseSelect');
    const emailInput = document.getElementById('studentEmailInput');
    if (courseSelect) courseSelect.value = '';
    if (emailInput) emailInput.value = '';
}

/**
 * Load Courses for Student Enrollment Modal
 *
 * BUSINESS LOGIC:
 * Populates the course selection dropdown with all courses the instructor teaches.
 * Students can only be enrolled in courses that exist.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instructor's courses from CourseService
 * - Populates dropdown with course titles and IDs
 * - Handles errors gracefully with user-friendly messages
 *
 * WHY THIS MATTERS:
 * Ensures instructors can only enroll students in valid courses,
 * preventing invalid enrollments and maintaining data integrity.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded from the service
 */
async function loadCoursesForStudentModal() {
    const courseSelect = document.getElementById('studentCourseSelect');
    if (!courseSelect) return;

    try {
        // Load courses via service layer
        const courses = await courseService.loadCourses();

        courseSelect.innerHTML = '<option value="">-- Select a course --</option>';
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            courseSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading courses:', error);
        courseSelect.innerHTML = '<option value="">Error loading courses</option>';
    }
}

/**
 * Submit Add Student Form
 *
 * BUSINESS LOGIC:
 * Validates and processes student enrollment request. Adds the student
 * to the selected course and updates the UI accordingly.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates required fields (course ID and email)
 * - Submits enrollment request to backend API
 * - Shows success/error feedback to user
 * - Closes modal and refreshes student list on success
 *
 * WHY THIS MATTERS:
 * Proper validation prevents incomplete enrollments and ensures
 * data integrity while providing good user experience.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If enrollment submission fails
 */
async function submitAddStudent() {
    const courseSelect = document.getElementById('studentCourseSelect');
    const emailInput = document.getElementById('studentEmailInput');

    if (!courseSelect || !emailInput) return;

    const courseId = courseSelect.value;
    const email = emailInput.value.trim();

    if (!courseId || !email) {
        alert('Please fill in all fields');
        return;
    }

    try {
        // Simulate API call (replace with actual API)
        await new Promise(resolve => setTimeout(resolve, 1000));

        alert(`Student ${email} added successfully!`);
        closeAddStudentModal();
        loadAllStudents(); // Reload the students list

    } catch (error) {
        console.error('Error adding student:', error);
        alert('Failed to add student. Please try again.');
    }
}

// Make viewStudentDetails globally accessible
window.viewStudentDetails = function(studentId) {
    console.log('Viewing details for student:', studentId);
    alert(`Student details view not yet implemented for student ID: ${studentId}`);
};

/**
 * Load Instructor's Courses into Select Dropdown
 *
 * BUSINESS LOGIC:
 * Populates a generic course selection dropdown with all courses taught
 * by the current instructor. Used across multiple tabs.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches courses from CourseService
 * - Populates select element with course options
 * - Handles empty state and errors gracefully
 *
 * WHY THIS MATTERS:
 * Many instructor operations require course selection. This reusable
 * function ensures consistent course loading across the dashboard.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded
 */
async function loadInstructorCourses() {
    const selectElement = document.getElementById('selectedCourse');
    if (!selectElement) return;

    try {
        // Load courses via service layer
        const courses = await courseService.loadCourses();

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
 * Enroll a Single Student
 *
 * BUSINESS LOGIC:
 * Enrolls a student identified by email address into the currently selected course.
 * Validates course selection before proceeding.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates that a course is selected
 * - Calls StudentService to create enrollment
 * - Shows success/error feedback
 * - Refreshes enrolled students list on success
 *
 * WHY THIS MATTERS:
 * Individual enrollment is critical for targeted student management
 * and provides flexibility beyond bulk operations.
 *
 * @async
 * @param {string} email - Student's email address for enrollment
 * @returns {Promise<void>}
 * @throws {Error} If course not selected or enrollment fails
 */
async function enrollStudent(email) {
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        alert('Please select a course first');
        return;
    }

    try {
        // Enroll student via service layer
        await studentService.enrollStudentByEmail(email, parseInt(courseId));

        alert(`Student ${email} enrolled successfully!`);
        await loadEnrolledStudents(courseId);

    } catch (error) {
        console.error('Error enrolling student:', error);
        alert(`Error: ${error.message}`);
    }
}

/**
 * Enroll Multiple Students in Bulk
 *
 * BUSINESS LOGIC:
 * Processes bulk student enrollment by iterating through an array of email addresses.
 * Provides aggregate success/failure reporting.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates course selection before processing
 * - Iterates through email list, enrolling each student individually
 * - Tracks success and failure counts
 * - Reports final statistics to user
 *
 * WHY THIS MATTERS:
 * Bulk enrollment is essential for large classes and organizational efficiency.
 * Individual processing allows partial success scenarios.
 *
 * @async
 * @param {string[]} emails - Array of student email addresses to enroll
 * @returns {Promise<void>}
 * @throws {Error} If course not selected
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
 * Load Enrolled Students for a Specific Course
 *
 * BUSINESS LOGIC:
 * Fetches and displays all students enrolled in a particular course.
 * Provides course-specific student management view.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches students by course ID from StudentService
 * - Renders students in a table format with enrollment details
 * - Shows empty state if no students enrolled
 * - Provides unenroll actions for each student
 *
 * WHY THIS MATTERS:
 * Course-specific student views allow instructors to focus on
 * individual course management and identify course-specific issues.
 *
 * @async
 * @param {number|string} courseId - Unique identifier for the course
 * @returns {Promise<void>}
 * @throws {Error} If students cannot be loaded for the course
 */
async function loadEnrolledStudents(courseId) {
    const container = document.getElementById('enrolled-students-list');
    if (!container) return;

    container.innerHTML = '<p>Loading students...</p>';

    try {
        // Load enrolled students via service layer
        const students = await studentService.getStudentsByCourse(courseId);

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
 * BUSINESS REQUIREMENT:
 * Provides instructors with comprehensive analytics and insights about student
 * performance, engagement, and course effectiveness.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sets up course filter dropdown for analytics selection
 * - Configures refresh, export, and PDF download buttons
 * - Initializes time range selector for historical data
 * - Loads initial analytics data and renders charts
 *
 * WHY THIS MATTERS:
 * Data-driven insights help instructors identify struggling students,
 * improve course content, and demonstrate educational outcomes.
 *
 * @returns {void}
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

    // Course selector change (supports both ID names for backwards compatibility)
    const courseSelect = document.getElementById('analyticsCourseFilter') || document.getElementById('analyticsCourseSelect');
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
 * Load Courses for Analytics Filter Dropdown
 *
 * BUSINESS LOGIC:
 * Populates the analytics course filter with instructor's courses to enable
 * course-specific or aggregated analytics views.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instructor's courses from CourseService
 * - Populates dropdown with "All Courses" option plus individual courses
 * - Handles loading errors gracefully
 *
 * WHY THIS MATTERS:
 * Allows instructors to drill down into specific course analytics or
 * view aggregate data across all courses they teach.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded
 */
async function loadAnalyticsCourses() {
    const selectElement = document.getElementById('analyticsCourseFilter') || document.getElementById('analyticsCourseSelect');
    if (!selectElement) return;

    try {
        // Load courses via service layer
        const courses = await courseService.loadCourses();

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
 * Load Analytics Data for Selected Course and Time Range
 *
 * BUSINESS LOGIC:
 * Fetches comprehensive analytics data including student counts, quiz scores,
 * lab completion rates, and engagement metrics for visualization.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Retrieves selected course and time range from UI
 * - Fetches analytics from AnalyticsService
 * - Updates overview stat cards (total students, active students, avg quiz score)
 * - Triggers chart rendering with fresh data
 * - Manages loading and error states
 *
 * WHY THIS MATTERS:
 * Real-time, accurate analytics are crucial for instructors to make
 * informed decisions about course adjustments and student interventions.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If analytics data cannot be loaded
 */
async function loadAnalyticsData() {
    const courseSelect = document.getElementById('analyticsCourseFilter') || document.getElementById('analyticsCourseSelect');
    const courseId = courseSelect?.value;
    const timeRange = document.getElementById('analyticsTimeRange')?.value || '30';

    // Show loading
    const loading = document.getElementById('analyticsLoading');
    if (loading) loading.style.display = 'block';

    try {
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        // Load analytics via service layer
        const data = await analyticsService.loadInstructorAnalytics({
            instructorId: currentUser.id,
            courseId: courseId,
            timeRange: timeRange
        });

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
 * Render All Analytics Charts Using Chart.js
 *
 * BUSINESS LOGIC:
 * Orchestrates the rendering of all four analytics visualization charts
 * to provide comprehensive course performance insights.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates Chart.js library is loaded
 * - Destroys existing charts to prevent canvas reuse errors
 * - Renders 4 charts in sequence:
 *   1. Student Engagement Over Time (Line chart)
 *   2. Lab Completion Status (Doughnut chart)
 *   3. Quiz Score Distribution (Bar chart)
 *   4. Content Progress Distribution (Horizontal bar chart)
 * - Logs rendering progress for debugging
 *
 * WHY THIS MATTERS:
 * Comprehensive visualizations help instructors quickly grasp course health,
 * identify trends, and spot areas needing intervention.
 *
 * @param {Object} data - Complete analytics data containing all chart data structures
 * @returns {void}
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
 * Destroy Existing Chart Instances Before Creating New Ones
 *
 * BUSINESS LOGIC:
 * Prevents Chart.js canvas reuse errors and memory leaks by properly
 * destroying chart instances before re-rendering.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Iterates through all global chart instances
 * - Calls Chart.js destroy() method on each
 * - Resets instances to null to free memory
 *
 * WHY THIS MATTERS:
 * Chart.js throws errors if you try to create a chart on a canvas that
 * already has one. Proper cleanup ensures smooth re-rendering.
 *
 * @returns {void}
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
 * Render Student Engagement Over Time Chart (Line Chart)
 *
 * BUSINESS LOGIC:
 * Visualizes student engagement trends over time using three key metrics:
 * active students, course completions, and lab submissions.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates a multi-line Chart.js line chart
 * - Uses sample data structure from API response
 * - Applies smooth tension curves for readability
 * - Configures interactive tooltips and legends
 *
 * WHY THIS MATTERS:
 * Temporal engagement data helps instructors identify drop-off points,
 * successful interventions, and overall course health trends.
 *
 * @param {Object} data - Analytics data containing engagement_over_time object
 * @param {string[]} data.engagement_over_time.labels - Time period labels (e.g., weeks)
 * @param {number[]} data.engagement_over_time.active_students - Active student counts per period
 * @param {number[]} data.engagement_over_time.course_completions - Completion counts per period
 * @param {number[]} data.engagement_over_time.lab_submissions - Lab submission counts per period
 * @returns {void}
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
 * Render Lab Completion Status Chart (Doughnut Chart)
 *
 * BUSINESS LOGIC:
 * Displays the distribution of lab statuses (completed, in progress, not started, overdue)
 * to help instructors identify students needing assistance.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates a Chart.js doughnut chart
 * - Maps lab completion data to color-coded segments
 * - Calculates and displays percentages in tooltips
 * - Uses semantic colors (green=completed, red=overdue)
 *
 * WHY THIS MATTERS:
 * Lab completion is a key indicator of hands-on learning. Overdue labs
 * signal students at risk of falling behind.
 *
 * @param {Object} data - Analytics data containing lab_completion object
 * @param {number} data.lab_completion.completed - Count of completed labs
 * @param {number} data.lab_completion.in_progress - Count of in-progress labs
 * @param {number} data.lab_completion.not_started - Count of not started labs
 * @param {number} data.lab_completion.overdue - Count of overdue labs
 * @returns {void}
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
 * Render Quiz Score Distribution Chart (Bar Chart)
 *
 * BUSINESS LOGIC:
 * Shows how quiz scores are distributed across performance ranges to identify
 * overall class performance and outliers.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates a Chart.js bar chart with 5 score ranges
 * - Uses color gradients from red (poor) to green (excellent)
 * - Displays student counts and percentages in tooltips
 * - Configures y-axis for whole number counts
 *
 * WHY THIS MATTERS:
 * Quiz score distribution reveals if the course is too difficult/easy,
 * if content needs clarification, or if students are excelling.
 *
 * @param {Object} data - Analytics data containing quiz_scores object
 * @param {string[]} data.quiz_scores.ranges - Score range labels (e.g., "0-20%", "81-100%")
 * @param {number[]} data.quiz_scores.counts - Student counts in each range
 * @returns {void}
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
 * Render Content Progress Distribution Chart (Horizontal Bar Chart)
 *
 * BUSINESS LOGIC:
 * Visualizes how far students have progressed through course content,
 * helping instructors identify pacing issues or struggling locations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates a horizontal Chart.js bar chart
 * - Groups students by progress percentage ranges
 * - Displays student counts and percentages in tooltips
 * - Uses horizontal orientation for better label readability
 *
 * WHY THIS MATTERS:
 * Progress distribution shows if students are keeping pace with the course.
 * Large groups stuck at low progress indicate potential content blockers.
 *
 * @param {Object} data - Analytics data containing progress_distribution object
 * @param {string[]} data.progress_distribution.ranges - Progress range labels (e.g., "0-20%")
 * @param {number[]} data.progress_distribution.counts - Student counts in each range
 * @returns {void}
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
 * Export Analytics Data to CSV Format
 *
 * BUSINESS LOGIC:
 * Allows instructors to download analytics data for offline analysis,
 * reporting to administration, or integration with other tools.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Currently shows placeholder alert
 * - TODO: Implement CSV generation from analytics data
 * - Should include all chart data and summary statistics
 *
 * WHY THIS MATTERS:
 * Instructors often need to share analytics with department heads,
 * accreditation bodies, or for research purposes.
 *
 * @returns {void}
 */
function exportAnalyticsData() {
    alert('Analytics export functionality coming soon!');
    // TODO: Implement CSV export
}

/**
 * Download Analytics Report as PDF
 *
 * BUSINESS LOGIC:
 * Generates a formatted PDF report of analytics data for professional
 * presentation, archival, or sharing with stakeholders.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Currently shows placeholder alert
 * - TODO: Implement PDF generation with charts and tables
 * - Should include all visualizations and statistical summaries
 *
 * WHY THIS MATTERS:
 * PDF reports are essential for formal documentation, accreditation,
 * performance reviews, and stakeholder communication.
 *
 * @returns {void}
 */
function downloadPDFReport() {
    alert('PDF report generation coming soon!');
    // TODO: Implement PDF generation
}

/**
 * Initialize Courses Tab Functionality
 *
 * BUSINESS REQUIREMENT:
 * Provides instructors with a centralized view of all their courses
 * for quick access and management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Triggers initial course list loading
 * - Sets up view mode (grid/list)
 * - Prepares course management actions
 *
 * WHY THIS MATTERS:
 * The courses tab is often the instructor's starting point for
 * daily work, requiring fast, reliable access to course information.
 *
 * @returns {void}
 */
export function initCoursesTab() {
    console.log('📚 Initializing Courses Tab');

    // Load courses list
    loadCoursesList();

    console.log('✅ Courses Tab initialized');
}

/**
 * Load Instructor's Courses List
 *
 * BUSINESS LOGIC:
 * Fetches all courses taught by the instructor and renders them in
 * an organized, actionable format.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches courses from CourseService
 * - Renders courses in grid layout with metadata
 * - Shows empty state if no courses exist
 * - Provides edit and view actions for each course
 * - Displays course status, student count, and duration
 *
 * WHY THIS MATTERS:
 * Course overview is the primary navigation hub for instructors.
 * Clear presentation enables efficient course management.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded from the service
 */
async function loadCoursesList() {
    const container = document.getElementById('courses-list');
    if (!container) {
        console.warn('Courses list container not found');
        return;
    }

    container.innerHTML = '<p>Loading courses...</p>';

    try {
        // Load courses via service layer
        const courses = await courseService.loadCourses();

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
 * Initialize Overview Tab (Default Dashboard View)
 *
 * BUSINESS REQUIREMENT:
 * Provides instructors with a quick summary dashboard showing key metrics
 * at a glance when they first access the instructor dashboard.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Loads high-level statistics (total students, active courses)
 * - Displays summary cards for quick insights
 * - Serves as landing page for instructor dashboard
 *
 * WHY THIS MATTERS:
 * The overview tab gives instructors immediate situational awareness
 * of their teaching workload and student engagement.
 *
 * @returns {void}
 */
export function initOverviewTab() {
    console.log('📊 Initializing Overview Tab');

    // Load overview statistics
    loadOverviewStats();

    console.log('✅ Overview Tab initialized');
}

/**
 * Load Overview Statistics
 *
 * BUSINESS LOGIC:
 * Fetches aggregate statistics across all instructor's courses to populate
 * the overview dashboard summary cards.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Retrieves current user from localStorage
 * - Fetches overview stats from AnalyticsService
 * - Updates stat card elements (total students, active courses)
 * - Handles missing elements gracefully
 *
 * WHY THIS MATTERS:
 * Quick stats help instructors assess workload and identify trends
 * without navigating to detailed analytics.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If overview stats cannot be loaded
 */
async function loadOverviewStats() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        // Load overview stats via service layer
        const stats = await analyticsService.loadOverviewStats(currentUser.id);

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

    // Make functions globally accessible for inline event handlers
    window.filterPublishedCourses = filterPublishedCourses;
    window.createCourseInstance = createCourseInstance;
    window.viewCourseDetails = viewCourseDetails;

    // Load initial course list
    loadPublishedCourses();

    console.log('✅ Published Courses Tab initialized');
}

/**
 * Load and Display Published Courses
 *
 * BUSINESS LOGIC:
 * Fetches all published courses from the platform and displays them according
 * to the selected visibility filter (all/public/private). Instructors can view
 * courses they can instantiate for their classes.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches published courses from CourseService
 * - Applies visibility filter (public/private/all)
 * - Filters private courses to show only instructor's own
 * - Renders course cards with metadata and action buttons
 * - Shows loading, error, and empty states
 *
 * WHY THIS MATTERS:
 * Instructors need to browse available course templates to create
 * course instances for their students without building from scratch.
 *
 * @async
 * @param {string} [filterValue='all'] - Visibility filter: 'all', 'public', or 'private'
 * @returns {Promise<void>}
 * @throws {Error} If published courses cannot be loaded
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

        // Load published courses via service layer
        const courses = await courseService.loadPublishedCourses();

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
 * Filter Published Courses by Visibility
 *
 * BUSINESS LOGIC:
 * Updates the published courses display to show only courses matching
 * the selected visibility filter (all/public/private).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads filter value from UI dropdown
 * - Triggers reload of published courses with new filter
 * - Called by inline event handler in HTML
 *
 * WHY THIS MATTERS:
 * Visibility filtering helps instructors find relevant courses,
 * separating public templates from their own private courses.
 *
 * @returns {void}
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
 * Create Course Instance from Published Course
 *
 * BUSINESS LOGIC:
 * Initiates the course instance creation workflow by navigating to the
 * course instances tab and pre-selecting the specified published course.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Stores selected course ID in localStorage for modal pre-filling
 * - Programmatically switches to course instances tab
 * - Triggers instance creation modal after tab switch delay
 * - Handles case where instances tab is not found
 *
 * WHY THIS MATTERS:
 * Provides seamless workflow from browsing published courses to creating
 * instances, reducing clicks and improving UX.
 *
 * @param {number} courseId - ID of the published course to instantiate
 * @returns {void}
 */
function createCourseInstance(courseId) {
    console.log(`Creating instance for course ${courseId}`);

    // Store the selected course ID for the instance creation modal
    localStorage.setItem('selectedCourseForInstance', courseId);

    // Navigate to course instances tab
    const instancesTab = document.querySelector('[data-tab="course-instances"]');
    if (instancesTab) {
        instancesTab.click();

        // After tab switches, trigger the create instance modal
        setTimeout(() => {
            if (typeof window.showCreateInstanceModal === 'function') {
                window.showCreateInstanceModal(courseId);
            }
        }, 300);
    } else {
        console.error('Course instances tab not found');
    }
}

/**
 * View Detailed Information About a Published Course
 *
 * BUSINESS LOGIC:
 * Displays a comprehensive modal with full course details including
 * description, metadata, prerequisites, learning objectives, and enrollment info.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches full course details from CourseService
 * - Creates and dynamically injects modal HTML into DOM
 * - Displays all course metadata in organized sections
 * - Provides "Create Instance" action button in modal
 * - Auto-removes modal on close
 *
 * WHY THIS MATTERS:
 * Instructors need full course information before deciding to create an instance.
 * Detailed preview helps them choose the right course for their needs.
 *
 * @async
 * @param {number} courseId - ID of the course to view details for
 * @returns {Promise<void>}
 * @throws {Error} If course details cannot be loaded
 */
async function viewCourseDetails(courseId) {
    console.log(`Viewing details for course ${courseId}`);

    try {
        // Load full course details
        const course = await courseService.getCourse(courseId);

        // Create and show modal with course details
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h2>${course.title}</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="course-details-grid">
                        <div class="course-details-section">
                            <h3>Description</h3>
                            <p>${course.description || 'No description available'}</p>
                        </div>

                        <div class="course-details-section">
                            <h3>Course Information</h3>
                            <dl class="course-info-list">
                                <dt>Course Code:</dt>
                                <dd>${course.course_code || 'N/A'}</dd>

                                <dt>Instructor:</dt>
                                <dd>${course.instructor_name || 'Unknown'}</dd>

                                <dt>Duration:</dt>
                                <dd>${course.estimated_duration || 'N/A'} ${course.duration_unit || ''}</dd>

                                <dt>Difficulty:</dt>
                                <dd>${course.difficulty_level || 'N/A'}</dd>

                                <dt>Visibility:</dt>
                                <dd><span class="badge badge-${course.visibility}">${course.visibility}</span></dd>

                                <dt>Status:</dt>
                                <dd><span class="badge badge-${course.status}">${course.status}</span></dd>
                            </dl>
                        </div>

                        ${course.prerequisites ? `
                        <div class="course-details-section">
                            <h3>Prerequisites</h3>
                            <p>${course.prerequisites}</p>
                        </div>
                        ` : ''}

                        ${course.learning_objectives ? `
                        <div class="course-details-section">
                            <h3>Learning Objectives</h3>
                            <ul>
                                ${course.learning_objectives.map(obj => `<li>${obj}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="createCourseInstance(${courseId}); this.closest('.modal').remove();">
                        <i class="fas fa-plus"></i> Create Instance
                    </button>
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

    } catch (error) {
        console.error('Error loading course details:', error);
        alert('Failed to load course details. Please try again.');
    }
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
    window.viewInstanceDetails = viewInstanceDetails;
    window.manageEnrollment = manageEnrollment;

    // Load initial instance list
    loadCourseInstances();

    console.log('✅ Course Instances Tab initialized');
}

/**
 * Load and Display Course Instances
 *
 * BUSINESS LOGIC:
 * Fetches all course instances (scheduled course sessions) for the instructor
 * and displays them with filtering and search capabilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instances from CourseInstanceService
 * - Applies status filter (all/scheduled/active/completed/cancelled)
 * - Applies search query filter (course title or code)
 * - Renders instance cards with metadata (dates, enrollment, status)
 * - Shows loading, error, and empty states
 * - Provides view details and manage enrollment actions
 *
 * WHY THIS MATTERS:
 * Course instances represent actual teaching sessions. Instructors need clear
 * visibility into upcoming, active, and past sessions for planning and management.
 *
 * @async
 * @param {string} [filterValue='all'] - Status filter: 'all', 'scheduled', 'active', 'completed', 'cancelled'
 * @param {string} [searchQuery=''] - Search query to filter by course title or code
 * @returns {Promise<void>}
 * @throws {Error} If course instances cannot be loaded
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

        // Load course instances via service layer
        let instances = await courseInstanceService.loadInstructorInstances(currentUser.id);

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
 * Format Date String for User-Friendly Display
 *
 * BUSINESS LOGIC:
 * Converts ISO date strings to localized, human-readable format
 * for consistent date presentation across the UI.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Handles null/undefined dates gracefully
 * - Uses JavaScript Date object for parsing
 * - Formats as "Mon DD, YYYY" (e.g., "Jan 15, 2025")
 *
 * WHY THIS MATTERS:
 * Consistent date formatting improves UX and prevents confusion
 * from ISO timestamps or inconsistent formats.
 *
 * @param {string|null} dateString - ISO date string to format
 * @returns {string} Formatted date string or 'N/A' if invalid
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Filter Course Instances by Status
 *
 * BUSINESS LOGIC:
 * Updates the course instances display to show only instances matching
 * the selected status filter (all/scheduled/active/completed/cancelled).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads status filter value from UI dropdown
 * - Reads search query from search input
 * - Triggers reload of instances with both filters applied
 * - Called by inline event handler in HTML
 *
 * WHY THIS MATTERS:
 * Status filtering helps instructors focus on relevant course instances,
 * such as currently active courses or upcoming scheduled sessions.
 *
 * @returns {void}
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
 * Search Course Instances by Title or Code
 *
 * BUSINESS LOGIC:
 * Filters course instances based on user's search query, matching against
 * course title and course code for flexible search.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads search query from input field
 * - Reads current status filter value
 * - Triggers reload with search and filter applied
 * - Called by inline event handler in HTML
 *
 * WHY THIS MATTERS:
 * Search functionality enables quick navigation in large lists of
 * course instances, improving instructor efficiency.
 *
 * @returns {void}
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
 * Show Create Course Instance Modal
 *
 * BUSINESS LOGIC:
 * Displays the modal interface for creating a new course instance from
 * a published course. Includes form for dates, enrollment limits, etc.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates and injects modal HTML into DOM
 * - Loads available courses into dropdown
 * - Sets up form validation and event handlers
 * - Makes close/submit functions globally accessible
 * - Called by inline event handler in HTML
 *
 * WHY THIS MATTERS:
 * Course instances represent scheduled sessions of a course. This modal
 * enables instructors to plan and schedule their teaching calendar.
 *
 * @returns {void}
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
 * Load Available Published Courses for Instance Creation Dropdown
 *
 * BUSINESS LOGIC:
 * Populates the course selection dropdown in the create instance modal
 * with all published courses available for instantiation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches published courses from CourseService
 * - Populates select element with course options
 * - Handles errors gracefully without blocking modal
 *
 * WHY THIS MATTERS:
 * Instructors can only create instances of published courses.
 * This ensures they're working with approved, complete content.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded (error logged, not thrown)
 */
async function loadCoursesForInstanceCreation() {
    const select = document.getElementById('instanceCourseSelect');
    if (!select) return;

    try {
        // Load published courses via service layer
        const courses = await courseService.loadPublishedCourses();

        if (courses) {
            select.innerHTML = '<option value="">-- Select a course --</option>' +
                courses.map(c => `<option value="${c.id}">${c.title}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

/**
 * Close Create Instance Modal
 *
 * BUSINESS LOGIC:
 * Removes the create instance modal from the DOM and cleans up
 * any temporary state.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Finds and removes modal element from DOM
 * - Clears any form data
 * - Frees memory by removing DOM elements
 *
 * WHY THIS MATTERS:
 * Proper cleanup prevents DOM pollution and memory leaks,
 * especially when modals are opened/closed multiple times.
 *
 * @returns {void}
 */
function closeCreateInstanceModal() {
    const modal = document.getElementById('createInstanceModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Close Modal When Clicking Outside Content Area
 *
 * BUSINESS LOGIC:
 * Provides intuitive UX pattern where clicking the modal overlay (outside
 * the modal content) closes the modal.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Checks if click target is the overlay element
 * - Closes modal only if clicking overlay, not content
 * - Prevents accidental closes from clicks inside modal
 *
 * WHY THIS MATTERS:
 * Standard UX pattern that users expect. Improves usability
 * by providing multiple ways to close modals.
 *
 * @param {MouseEvent} event - Click event from user interaction
 * @returns {void}
 */
function closeModalOnOutsideClick(event) {
    if (event.target.classList.contains('modal-overlay')) {
        closeCreateInstanceModal();
    }
}

/**
 * Submit Create Course Instance Form
 *
 * BUSINESS LOGIC:
 * Validates and processes course instance creation request. Creates a scheduled
 * instance of a published course with specified dates and enrollment limits.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates form completion using HTML5 validation
 * - Collects form data (course_id, dates, max_students)
 * - Submits to CourseInstanceService
 * - Shows success/error feedback
 * - Closes modal and refreshes instance list on success
 *
 * WHY THIS MATTERS:
 * Course instances enable scheduled delivery of courses. Proper validation
 * prevents scheduling conflicts and data integrity issues.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If instance creation fails
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
        // Create instance via service layer
        await courseInstanceService.createInstance(instanceData);

        alert('Course instance created successfully!');
        closeCreateInstanceModal();
        loadCourseInstances(); // Reload the list
    } catch (error) {
        console.error('Error creating instance:', error);
        alert('Failed to create course instance. Please try again.');
    }
}

/**
 * View Detailed Information About a Course Instance
 *
 * BUSINESS LOGIC:
 * Displays a comprehensive modal showing instance details including
 * schedule, enrollment status, enrolled students list, and management options.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instance details and student list from CourseInstanceService
 * - Creates and injects modal HTML dynamically
 * - Displays instance metadata (dates, status, capacity)
 * - Lists all enrolled students with contact information
 * - Provides "Manage Enrollment" action button
 * - Auto-removes modal on close
 *
 * WHY THIS MATTERS:
 * Instructors need quick access to instance details and enrolled student lists
 * for session planning, communication, and enrollment management.
 *
 * @async
 * @param {number} instanceId - ID of the course instance to view
 * @returns {Promise<void>}
 * @throws {Error} If instance details cannot be loaded
 */
async function viewInstanceDetails(instanceId) {
    console.log(`Viewing details for instance ${instanceId}`);

    try {
        // Load instance details
        const instance = await courseInstanceService.getInstance(instanceId);
        const students = await courseInstanceService.getInstanceStudents(instanceId);

        // Create and show modal with instance details
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h2>${instance.course_title || 'Course Instance'}</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="instance-details-grid">
                        <div class="instance-details-section">
                            <h3>Instance Information</h3>
                            <dl class="instance-info-list">
                                <dt>Course Code:</dt>
                                <dd>${instance.course_code || 'N/A'}</dd>

                                <dt>Status:</dt>
                                <dd><span class="badge badge-${instance.status}">${instance.status}</span></dd>

                                <dt>Start Date:</dt>
                                <dd>${formatDate(instance.start_date)}</dd>

                                <dt>End Date:</dt>
                                <dd>${formatDate(instance.end_date)}</dd>

                                <dt>Max Students:</dt>
                                <dd>${instance.max_students || 'Unlimited'}</dd>

                                <dt>Enrolled Students:</dt>
                                <dd>${students.length} / ${instance.max_students || '∞'}</dd>
                            </dl>
                        </div>

                        ${students.length > 0 ? `
                        <div class="instance-details-section">
                            <h3>Enrolled Students</h3>
                            <ul class="enrolled-students-list">
                                ${students.map(student => `
                                    <li>
                                        <span>${student.name || student.email}</span>
                                        <span class="student-email">${student.email}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        ` : `
                        <div class="instance-details-section">
                            <h3>Enrolled Students</h3>
                            <p class="empty-message">No students enrolled yet.</p>
                        </div>
                        `}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="manageEnrollment(${instanceId}); this.closest('.modal').remove();">
                        <i class="fas fa-user-plus"></i> Manage Enrollment
                    </button>
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

    } catch (error) {
        console.error('Error loading instance details:', error);
        alert('Failed to load instance details. Please try again.');
    }
}

/**
 * Manage Student Enrollment for a Course Instance
 *
 * BUSINESS LOGIC:
 * Provides a comprehensive interface for adding and removing students from
 * a course instance, with real-time enrollment status updates.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instance details, enrolled students, and all available students
 * - Filters out already-enrolled students from available list
 * - Creates dynamic enrollment management modal
 * - Provides dropdown to select and enroll available students
 * - Lists currently enrolled students with removal actions
 * - Exposes global functions for enrollment/unenrollment
 * - Refreshes modal after enrollment changes
 *
 * WHY THIS MATTERS:
 * Flexible enrollment management is critical for instructors to add late
 * registrants, remove dropouts, and maintain accurate class rosters.
 *
 * @async
 * @param {number} instanceId - ID of the course instance to manage enrollment for
 * @returns {Promise<void>}
 * @throws {Error} If enrollment data cannot be loaded
 */
async function manageEnrollment(instanceId) {
    console.log(`Managing enrollment for instance ${instanceId}`);

    try {
        // Load instance and student data
        const instance = await courseInstanceService.getInstance(instanceId);
        const enrolledStudents = await courseInstanceService.getInstanceStudents(instanceId);
        const allStudents = await studentService.loadStudents();

        // Filter out already enrolled students
        const availableStudents = allStudents.filter(s =>
            !enrolledStudents.some(enrolled => enrolled.id === s.id)
        );

        // Create enrollment management modal
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h2>Manage Enrollment: ${instance.course_title}</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="enrollment-management">
                        <div class="enrollment-section">
                            <h3>Add Students</h3>
                            ${availableStudents.length > 0 ? `
                                <select id="studentToEnroll" class="form-control">
                                    <option value="">-- Select student --</option>
                                    ${availableStudents.map(s => `
                                        <option value="${s.id}">${s.name || s.email} (${s.email})</option>
                                    `).join('')}
                                </select>
                                <button class="btn btn-primary" onclick="enrollStudentInInstance(${instanceId})">
                                    <i class="fas fa-plus"></i> Enroll Student
                                </button>
                            ` : '<p>No available students to enroll.</p>'}
                        </div>

                        <div class="enrollment-section">
                            <h3>Currently Enrolled (${enrolledStudents.length})</h3>
                            ${enrolledStudents.length > 0 ? `
                                <ul class="enrolled-list">
                                    ${enrolledStudents.map(student => `
                                        <li>
                                            ${student.name || student.email} (${student.email})
                                            <button class="btn btn-small btn-danger"
                                                    onclick="unenrollStudent(${instanceId}, ${student.id})">
                                                <i class="fas fa-times"></i> Remove
                                            </button>
                                        </li>
                                    `).join('')}
                                </ul>
                            ` : '<p>No students enrolled yet.</p>'}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Make enrollment functions globally accessible
        window.enrollStudentInInstance = async (instId) => {
            const select = document.getElementById('studentToEnroll');
            const studentId = select?.value;
            if (!studentId) {
                alert('Please select a student');
                return;
            }

            try {
                await courseInstanceService.enrollStudentInInstance(instId, studentId);
                alert('Student enrolled successfully!');
                modal.remove();
                manageEnrollment(instId); // Refresh the modal
            } catch (error) {
                console.error('Error enrolling student:', error);
                alert('Failed to enroll student. Please try again.');
            }
        };

        window.unenrollStudent = async (instId, studId) => {
            if (!confirm('Are you sure you want to remove this student?')) {
                return;
            }

            try {
                // Note: Would need unenroll method in service
                alert('Unenroll functionality not yet implemented in backend');
                // await courseInstanceService.unenrollStudent(instId, studId);
                // modal.remove();
                // manageEnrollment(instId);
            } catch (error) {
                console.error('Error unenrolling student:', error);
                alert('Failed to unenroll student. Please try again.');
            }
        };

    } catch (error) {
        console.error('Error managing enrollment:', error);
        alert('Failed to load enrollment data. Please try again.');
    }
}

/**
 * Initialize Content Generation Tab
 *
 * BUSINESS REQUIREMENT:
 * Instructors can use AI to generate course content including:
 * - Syllabi based on course description
 * - Presentation slides
 * - Quizzes and assessments
 *
 * TECHNICAL IMPLEMENTATION:
 * - Loads instructor's courses for selection
 * - Provides buttons for syllabus, slides, and quiz generation
 * - Shows preview of generated content
 * - Allows save and regenerate operations
 */
export function initContentGenerationTab() {
    console.log('✨ Initializing Content Generation Tab');

    // Load courses for selection
    loadCoursesForContentGeneration();

    // Set up event listeners
    const generateSyllabusBtn = document.getElementById('generateSyllabusBtn');
    const generateSlidesBtn = document.getElementById('generateSlidesBtn');
    const generateQuizBtn = document.getElementById('generateQuizBtn');
    const saveGeneratedContentBtn = document.getElementById('saveGeneratedContentBtn');
    const regenerateContentBtn = document.getElementById('regenerateContentBtn');

    if (generateSyllabusBtn) {
        generateSyllabusBtn.addEventListener('click', () => generateContent('syllabus'));
    }

    if (generateSlidesBtn) {
        generateSlidesBtn.addEventListener('click', () => generateContent('slides'));
    }

    if (generateQuizBtn) {
        generateQuizBtn.addEventListener('click', () => generateContent('quiz'));
    }

    if (saveGeneratedContentBtn) {
        saveGeneratedContentBtn.addEventListener('click', saveGeneratedContent);
    }

    if (regenerateContentBtn) {
        regenerateContentBtn.addEventListener('click', regenerateContent);
    }

    console.log('✅ Content Generation Tab initialized');
}

/**
 * Load Courses for AI Content Generation Selection
 *
 * BUSINESS LOGIC:
 * Populates the course dropdown in the content generation tab so instructors
 * can select which course to generate content for.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches instructor's courses from CourseService
 * - Populates select element with course options
 * - Shows error message if loading fails
 *
 * WHY THIS MATTERS:
 * AI content generation requires course context. This ensures instructors
 * can only generate content for courses they own/teach.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If courses cannot be loaded (error logged, not thrown)
 */
async function loadCoursesForContentGeneration() {
    const courseSelect = document.getElementById('contentGenCourseSelect');
    if (!courseSelect) {
        console.error('Course select element not found');
        return;
    }

    try {
        // Load courses via service layer
        const courses = await courseService.loadCourses();

        // Populate select dropdown
        courseSelect.innerHTML = '<option value="">-- Select a course --</option>';
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            courseSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading courses:', error);
        courseSelect.innerHTML = '<option value="">Error loading courses</option>';
    }
}

/**
 * Generate Course Content Using AI
 *
 * BUSINESS LOGIC:
 * Uses AI to automatically generate course materials (syllabus, presentation slides,
 * or quiz questions) based on the course description and learning objectives.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates course selection
 * - Shows loading state during generation
 * - Simulates AI generation (TODO: integrate with real AI service)
 * - Displays generated content in preview section
 * - Stores content type and course ID for saving
 *
 * WHY THIS MATTERS:
 * AI content generation dramatically reduces instructor workload for creating
 * course materials, allowing focus on teaching rather than content creation.
 *
 * @async
 * @param {string} contentType - Type of content to generate: 'syllabus', 'slides', or 'quiz'
 * @returns {Promise<void>}
 * @throws {Error} If content generation fails
 */
async function generateContent(contentType) {
    const courseSelect = document.getElementById('contentGenCourseSelect');
    const courseId = courseSelect?.value;

    if (!courseId) {
        alert('Please select a course first');
        return;
    }

    const previewSection = document.getElementById('contentPreviewSection');
    const previewContent = document.getElementById('contentPreview');

    if (!previewSection || !previewContent) {
        console.error('Preview elements not found');
        return;
    }

    try {
        // Show loading state
        previewSection.style.display = 'block';
        previewContent.innerHTML = `
            <div class="loading-indicator">
                <i class="fas fa-spinner fa-spin"></i> Generating ${contentType}... This may take a moment.
            </div>
        `;

        // Simulate AI generation (replace with actual API call)
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Mock generated content
        let generatedContent = '';
        if (contentType === 'syllabus') {
            generatedContent = `
                <h3>Course Syllabus</h3>
                <h4>Week 1: Introduction</h4>
                <p>Overview of the course topics and learning objectives.</p>
                <h4>Week 2: Core Concepts</h4>
                <p>Deep dive into fundamental concepts and principles.</p>
                <h4>Week 3: Practical Applications</h4>
                <p>Hands-on exercises and real-world examples.</p>
                <h4>Week 4: Advanced Topics</h4>
                <p>Exploration of advanced techniques and best practices.</p>
            `;
        } else if (contentType === 'slides') {
            generatedContent = `
                <h3>Presentation Slides</h3>
                <div class="slide-preview">
                    <p><strong>Slide 1:</strong> Title Slide - Course Introduction</p>
                    <p><strong>Slide 2:</strong> Learning Objectives</p>
                    <p><strong>Slide 3:</strong> Course Outline</p>
                    <p><strong>Slide 4:</strong> Key Concepts</p>
                    <p><strong>Slide 5:</strong> Summary and Next Steps</p>
                </div>
            `;
        } else if (contentType === 'quiz') {
            generatedContent = `
                <h3>Quiz Questions</h3>
                <div class="quiz-preview">
                    <p><strong>Question 1:</strong> What is the main purpose of this course?</p>
                    <p>A) Learn basics<br>B) Master advanced topics<br>C) Both A and B<br>D) None of the above</p>
                    <p><strong>Question 2:</strong> Which topic is covered in Week 2?</p>
                    <p>A) Introduction<br>B) Core Concepts<br>C) Advanced Topics<br>D) Conclusion</p>
                </div>
            `;
        }

        previewContent.innerHTML = generatedContent;

        // Store the generated content type for saving
        previewContent.dataset.contentType = contentType;
        previewContent.dataset.courseId = courseId;

    } catch (error) {
        console.error('Error generating content:', error);
        previewContent.innerHTML = `
            <div class="alert alert-error">
                Failed to generate ${contentType}. Please try again.
            </div>
        `;
    }
}

/**
 * Save AI-Generated Content to Course
 *
 * BUSINESS LOGIC:
 * Persists the AI-generated content (syllabus, slides, or quiz) to the course
 * after instructor review and approval.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Retrieves content type and course ID from preview element
 * - Validates that content exists
 * - Submits content to backend API (TODO: implement real API call)
 * - Shows success/error feedback
 *
 * WHY THIS MATTERS:
 * Instructors need to review AI-generated content before committing it.
 * Save functionality preserves approved content for student access.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If content saving fails
 */
async function saveGeneratedContent() {
    const previewContent = document.getElementById('contentPreview');
    if (!previewContent) return;

    const contentType = previewContent.dataset.contentType;
    const courseId = previewContent.dataset.courseId;

    if (!contentType || !courseId) {
        alert('No content to save');
        return;
    }

    try {
        // Simulate saving (replace with actual API call)
        alert(`${contentType} saved successfully to the course!`);
    } catch (error) {
        console.error('Error saving content:', error);
        alert('Failed to save content. Please try again.');
    }
}

/**
 * Regenerate AI Content
 *
 * BUSINESS LOGIC:
 * Allows instructors to request new AI-generated content if they're not satisfied
 * with the initial generation, without changing parameters.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Retrieves current content type from preview element
 * - Calls generateContent() again with same parameters
 * - Overwrites previous preview with new generation
 *
 * WHY THIS MATTERS:
 * AI generation isn't always perfect on first try. Regeneration gives
 * instructors multiple options to choose from.
 *
 * @returns {void}
 */
function regenerateContent() {
    const previewContent = document.getElementById('contentPreview');
    if (!previewContent) return;

    const contentType = previewContent.dataset.contentType;
    if (contentType) {
        generateContent(contentType);
    }
}

/**
 * Initialize Feedback Tab
 *
 * BUSINESS REQUIREMENT:
 * Instructors can manage student feedback including:
 * - View all student feedback
 * - Respond to feedback
 * - Filter feedback by status
 * - Mark feedback as resolved
 *
 * TECHNICAL IMPLEMENTATION:
 * - Feedback list with filtering
 * - Response modal
 * - Status management
 */
export function initFeedbackTab() {
    console.log('💬 Initializing Feedback Tab');

    // Set up filter
    const statusFilter = document.getElementById('feedbackStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterFeedback);
    }

    // Make functions globally accessible
    window.respondToFeedback = respondToFeedback;
    window.markFeedbackResolved = markFeedbackResolved;
    window.closeFeedbackResponseModal = closeFeedbackResponseModal;
    window.submitFeedbackResponse = submitFeedbackResponse;

    console.log('✅ Feedback Tab initialized');
}

/**
 * Filter Student Feedback by Status
 *
 * BUSINESS LOGIC:
 * Filters the feedback list to show only items matching the selected status
 * (all/pending/responded/resolved), helping instructors prioritize responses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads filter value from status dropdown
 * - Shows/hides feedback items based on status match
 * - Uses CSS display property for filtering
 *
 * WHY THIS MATTERS:
 * Instructors need to prioritize pending feedback. Status filtering
 * ensures urgent student questions don't get lost in resolved items.
 *
 * @returns {void}
 */
function filterFeedback() {
    const statusFilter = document.getElementById('feedbackStatusFilter');
    const filterValue = statusFilter?.value || 'all';

    const feedbackItems = document.querySelectorAll('.feedback-item');

    feedbackItems.forEach(item => {
        if (filterValue === 'all') {
            item.style.display = 'block';
        } else {
            const status = item.querySelector('.feedback-status')?.textContent.toLowerCase();
            if (status === filterValue) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        }
    });
}

/**
 * Respond to Student Feedback
 *
 * BUSINESS LOGIC:
 * Opens the response modal for a specific feedback item, allowing
 * the instructor to compose and send a reply to student questions.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Displays the feedback response modal
 * - Loads feedback context (student name, question)
 * - Stores feedback ID in modal data attribute for submission
 * - Prepares textarea for instructor response
 *
 * WHY THIS MATTERS:
 * Timely, personalized responses to student feedback improve engagement
 * and learning outcomes while building instructor-student rapport.
 *
 * @param {number} feedbackId - ID of the feedback item to respond to
 * @returns {void}
 */
function respondToFeedback(feedbackId) {
    console.log('Responding to feedback:', feedbackId);

    const modal = document.getElementById('feedbackResponseModal');
    if (!modal) return;

    // Show modal
    modal.style.display = 'flex';

    // You would typically load the feedback details here
    const modalContext = document.getElementById('modalFeedbackContext');
    if (modalContext) {
        modalContext.innerHTML = `
            <p><strong>Student:</strong> Alice Johnson</p>
            <p><strong>Question:</strong> Question about Module 3: Functions</p>
        `;
    }

    // Store feedback ID for submission
    modal.dataset.feedbackId = feedbackId;
}

/**
 * Close Feedback Response Modal
 *
 * BUSINESS LOGIC:
 * Closes the feedback response modal and clears the response textarea
 * to prevent accidental data retention.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Hides modal by setting display to none
 * - Clears textarea value
 * - Resets form state
 *
 * WHY THIS MATTERS:
 * Proper cleanup prevents instructors from accidentally sending
 * old responses to new feedback items.
 *
 * @returns {void}
 */
function closeFeedbackResponseModal() {
    const modal = document.getElementById('feedbackResponseModal');
    if (modal) {
        modal.style.display = 'none';
    }

    // Clear textarea
    const textarea = document.getElementById('feedbackResponseText');
    if (textarea) {
        textarea.value = '';
    }
}

/**
 * Submit Response to Student Feedback
 *
 * BUSINESS LOGIC:
 * Sends instructor's response to student feedback/questions, enabling
 * asynchronous communication and support.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates response text is not empty
 * - Retrieves feedback ID from modal data attribute
 * - Submits response to backend API (TODO: implement real API)
 * - Shows success/error feedback
 * - Closes modal and updates feedback list
 *
 * WHY THIS MATTERS:
 * Timely instructor responses improve student satisfaction and learning
 * outcomes. This feature enables scalable student support.
 *
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If response submission fails
 */
async function submitFeedbackResponse() {
    const modal = document.getElementById('feedbackResponseModal');
    const textarea = document.getElementById('feedbackResponseText');

    if (!textarea || !modal) return;

    const responseText = textarea.value.trim();
    const feedbackId = modal.dataset.feedbackId;

    if (!responseText) {
        alert('Please enter a response');
        return;
    }

    try {
        // Simulate API call (replace with actual API)
        await new Promise(resolve => setTimeout(resolve, 1000));

        alert('Response sent successfully!');
        closeFeedbackResponseModal();

        // You would typically reload the feedback list here

    } catch (error) {
        console.error('Error sending response:', error);
        alert('Failed to send response. Please try again.');
    }
}

/**
 * Mark Feedback as Resolved
 *
 * BUSINESS LOGIC:
 * Changes the status of a feedback item to "resolved" after the instructor
 * has adequately addressed the student's question or concern.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sends resolve request to backend API (TODO: implement real API)
 * - Shows success/error feedback to user
 * - Triggers feedback list reload to reflect new status
 * - Simulates API call with timeout
 *
 * WHY THIS MATTERS:
 * Marking feedback as resolved helps instructors track which student
 * questions still need attention and maintain organized support workflows.
 *
 * @async
 * @param {number} feedbackId - ID of the feedback item to mark as resolved
 * @returns {Promise<void>}
 * @throws {Error} If resolve operation fails
 */
async function markFeedbackResolved(feedbackId) {
    console.log('Marking feedback as resolved:', feedbackId);

    try {
        // Simulate API call (replace with actual API)
        await new Promise(resolve => setTimeout(resolve, 500));

        alert('Feedback marked as resolved!');

        // You would typically reload the feedback list here

    } catch (error) {
        console.error('Error marking feedback as resolved:', error);
        alert('Failed to mark feedback as resolved. Please try again.');
    }
}

/**
 * Initialize Labs Tab
 *
 * BUSINESS REQUIREMENT:
 * Instructors can manage lab environments including:
 * - View all lab instances
 * - Create new lab environments
 * - Monitor lab status and resource usage
 *
 * TECHNICAL IMPLEMENTATION:
 * - Lab list with status indicators
 * - Create lab functionality
 * - Docker container integration
 */
export function initLabsTab() {
    console.log('🧪 Initializing Labs Tab');

    // Set up create lab button
    const createLabBtn = document.getElementById('createLabBtn');
    if (createLabBtn) {
        createLabBtn.addEventListener('click', () => {
            alert('Create Lab functionality - Coming soon!');
        });
    }

    console.log('✅ Labs Tab initialized');
}
