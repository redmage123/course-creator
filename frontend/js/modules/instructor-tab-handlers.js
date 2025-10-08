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

        // Update charts (if Chart.js is available)
        if (typeof Chart !== 'undefined') {
            renderAnalyticsCharts(data);
        }

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
 * Render analytics charts
 */
function renderAnalyticsCharts(data) {
    // This is a placeholder for chart rendering
    // In a real implementation, you would use Chart.js or similar library
    console.log('Rendering charts with data:', data);
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
 */
export function initFilesTab() {
    console.log('📁 Initializing Files Tab');
    console.log('✅ Files Tab initialized');
}

/**
 * Initialize Published Courses Tab
 */
export function initPublishedCoursesTab() {
    console.log('🎓 Initializing Published Courses Tab');
    console.log('✅ Published Courses Tab initialized');
}

/**
 * Initialize Course Instances Tab
 */
export function initCourseInstancesTab() {
    console.log('📋 Initializing Course Instances Tab');
    console.log('✅ Course Instances Tab initialized');
}
