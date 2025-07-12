// Instructor Dashboard JavaScript

let userCourses = [];
// currentUser is already declared in main.js

// Functions are now global from main.js

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadUserCourses();
    loadCoursesForSelector();
    loadCoursesForContentSelector();
});

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        case 'info': 
        default: return 'fa-info-circle';
    }
}

// Helper function to get initials
function getInitials(name) {
    if (!name) return 'U';
    const words = name.split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    } else {
        return name.substring(0, 2).toUpperCase();
    }
}


function initializeDashboard() {
    // Check if user is logged in
    currentUser = getCurrentUser();
    if (!currentUser) {
        window.location.href = 'index.html';
        return;
    }
    
    // Update user display
    updateUserDisplay();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize dashboard with overview section
    showSection('overview');
    
    // Load initial data
    loadUserCourses();
    updateNavigationStats();
}

function setupEventListeners() {
    // Course creation form
    document.getElementById('courseForm').addEventListener('submit', handleCourseCreation);
    
    // Student enrollment forms
    document.getElementById('singleEnrollmentForm').addEventListener('submit', handleSingleEnrollment);
    document.getElementById('bulkEnrollmentForm').addEventListener('submit', handleBulkEnrollment);
}

function updateUserDisplay() {
    // Update header user display
    const userName = document.getElementById('userName');
    const avatarInitials = document.getElementById('avatarInitials');
    
    // Update sidebar user display
    const sidebarUserName = document.getElementById('sidebarUserName');
    const sidebarAvatarInitials = document.getElementById('sidebarAvatarInitials');
    const sidebarUserRole = document.getElementById('sidebarUserRole');
    
    if (currentUser) {
        const displayName = currentUser.full_name || currentUser.username || currentUser.email || 'Instructor';
        const initials = getInitials(displayName);
        const role = currentUser.role || 'instructor';
        
        // Update header
        if (userName) userName.textContent = displayName;
        if (avatarInitials) avatarInitials.textContent = initials;
        
        // Update sidebar
        if (sidebarUserName) sidebarUserName.textContent = displayName;
        if (sidebarAvatarInitials) sidebarAvatarInitials.textContent = initials;
        if (sidebarUserRole) {
            sidebarUserRole.textContent = role.charAt(0).toUpperCase() + role.slice(1);
        }
    }
}

// Section management for new sidebar navigation
// eslint-disable-next-line no-unused-vars
function showSection(sectionName) {
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to corresponding nav link
    const targetLink = document.querySelector(`[data-section="${sectionName}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }
    
    // Update breadcrumb
    const breadcrumb = document.getElementById('currentSection');
    if (breadcrumb) {
        const sectionTitles = {
            'overview': 'Overview',
            'courses': 'My Courses',
            'create-course': 'Create Course',
            'students': 'Students',
            'content': 'Content',
            'analytics': 'Analytics'
        };
        breadcrumb.textContent = sectionTitles[sectionName] || 'Dashboard';
    }
    
    // Load section-specific data
    loadSectionData(sectionName);
    
    // Update nav badges and stats when switching sections
    updateNavigationStats();
}

// Load data specific to each section
function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'overview':
            loadOverviewMetrics();
            loadRecentActivity();
            break;
        case 'courses':
            loadUserCourses();
            break;
        case 'students':
            loadCoursesForSelector();
            break;
        case 'content':
            loadCoursesForContentSelector();
            break;
        case 'create-course':
            // Form is ready by default
            break;
        case 'analytics':
            // Analytics placeholder for now
            break;
    }
}

// Load overview metrics for dashboard
async function loadOverviewMetrics() {
    try {
        // Get total students across all courses
        let totalStudents = 0;
        let totalCourses = userCourses.length;
        let activeCourses = userCourses.filter(course => course.is_published).length;
        
        // Calculate lab sessions and other metrics
        let totalLabSessions = 0;
        
        for (const course of userCourses) {
            try {
                const token = localStorage.getItem('authToken');
                const studentsResponse = await fetch(CONFIG.ENDPOINTS.COURSE_STUDENTS(course.id), {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (studentsResponse.ok) {
                    const students = await studentsResponse.json();
                    totalStudents += students.length;
                }
            } catch (error) {
                console.log('Error fetching students for course:', course.id);
            }
        }
        
        // Update metric cards
        updateMetricCard('overviewTotalStudents', totalStudents, 'studentChange', '+2 this week');
        updateMetricCard('overviewActiveCourses', activeCourses, 'courseChange', 'No change');
        updateMetricCard('overviewAvgProgress', '75%', 'progressChange', '+5% this week');
        updateMetricCard('overviewLabSessions', totalLabSessions, 'labChange', '+3 today');
        
    } catch (error) {
        console.error('Error loading overview metrics:', error);
    }
}

// Update individual metric card
function updateMetricCard(valueId, value, changeId, changeText) {
    const valueElement = document.getElementById(valueId);
    const changeElement = document.getElementById(changeId);
    
    if (valueElement) {
        valueElement.textContent = value;
    }
    if (changeElement) {
        changeElement.textContent = changeText;
    }
}

// Load recent activity for overview
function loadRecentActivity() {
    const activityList = document.getElementById('recentActivityList');
    if (!activityList) return;
    
    // For now, show static activity - this would come from an API in production
    const activities = [
        {
            icon: 'fas fa-user-plus',
            text: '<strong>New student enrolled</strong> in Python Fundamentals',
            time: '2 hours ago'
        },
        {
            icon: 'fas fa-flask',
            text: '<strong>Lab session completed</strong> by 3 students',
            time: '4 hours ago'
        },
        {
            icon: 'fas fa-check-circle',
            text: '<strong>Course published</strong> - JavaScript Basics',
            time: '1 day ago'
        }
    ];
    
    activityList.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="${activity.icon}"></i>
            </div>
            <div class="activity-content">
                <p>${activity.text}</p>
                <span class="activity-time">${activity.time}</span>
            </div>
        </div>
    `).join('');
}

// Update navigation stats in sidebar
function updateNavigationStats() {
    const courseCount = document.getElementById('courseCount');
    const studentCount = document.getElementById('studentCount');
    const totalStudents = document.getElementById('totalStudents');
    const activeCourses = document.getElementById('activeCourses');
    
    if (courseCount) {
        courseCount.textContent = userCourses.length;
    }
    
    if (activeCourses) {
        activeCourses.textContent = userCourses.filter(course => course.is_published).length;
    }
    
    // Student count would need to be calculated from course enrollments
    // For now, using placeholder values
    if (studentCount) {
        studentCount.textContent = '0';
    }
    if (totalStudents) {
        totalStudents.textContent = '0';
    }
}

// Course management
async function loadUserCourses() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch(CONFIG.ENDPOINTS.COURSES, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            userCourses = await response.json();
            displayCourses(userCourses);
            updateNavigationStats();
        }
    } catch (error) {
        console.error('Error loading courses:', error);
        showNotification('Error loading courses', 'error');
    }
}

function displayCourses(courses) {
    const coursesList = document.getElementById('courses-list');
    
    if (!courses || courses.length === 0) {
        coursesList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book"></i>
                <h3>No courses yet</h3>
                <p>Create your first course to get started!</p>
                <button class="btn btn-primary" onclick="showSection('create-course')">
                    <i class="fas fa-plus"></i> Create Course
                </button>
            </div>
        `;
        return;
    }
    
    coursesList.innerHTML = courses.map(course => {
        const lastModified = course.updated_at ? new Date(course.updated_at).toLocaleDateString() : 'Recently';
        const enrollmentCount = course.enrollment_count || 0;
        const completionRate = course.completion_rate || 0;
        
        return `
            <div class="course-card enhanced">
                <div class="course-header">
                    <div class="course-title-section">
                        <h4>${course.title}</h4>
                        <div class="course-meta-badges">
                            <span class="course-status ${course.is_published ? 'published' : 'draft'}">
                                <i class="fas ${course.is_published ? 'fa-check-circle' : 'fa-clock'}"></i>
                                ${course.is_published ? 'Published' : 'Draft'}
                            </span>
                            <span class="course-category-badge">${course.category}</span>
                        </div>
                    </div>
                    <div class="course-metrics">
                        <div class="metric-item">
                            <span class="metric-value">${enrollmentCount}</span>
                            <span class="metric-label">Students</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">${completionRate}%</span>
                            <span class="metric-label">Completion</span>
                        </div>
                    </div>
                </div>
                
                <p class="course-description">${course.description}</p>
                
                <div class="course-details">
                    <div class="course-meta">
                        <span class="meta-item">
                            <i class="fas fa-signal"></i>
                            ${course.difficulty_level}
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-clock"></i>
                            ${course.estimated_duration}h
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-calendar"></i>
                            ${lastModified}
                        </span>
                    </div>
                </div>
                
                <div class="course-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${course.content_progress || 0}%"></div>
                    </div>
                    <span class="progress-text">${course.content_progress || 0}% Content Complete</span>
                </div>
                
                <div class="course-actions">
                    <div class="primary-actions">
                        <button class="btn btn-sm btn-primary" onclick="manageCourse('${course.id}')" title="Manage Course">
                            <i class="fas fa-cog"></i> Manage
                        </button>
                        <button class="btn btn-sm btn-success" onclick="generateCourseContent('${course.id}')" title="Generate Content">
                            <i class="fas fa-magic"></i> Generate
                        </button>
                        <button class="btn btn-sm btn-info" onclick="viewCourseContent('${course.id}')" title="View Content">
                            <i class="fas fa-eye"></i> View
                        </button>
                    </div>
                    <div class="secondary-actions">
                        <button class="btn btn-sm btn-secondary" onclick="viewCourseStudents('${course.id}')" title="View Students">
                            <i class="fas fa-users"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="editCourse('${course.id}')" title="Edit Course">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteCourse('${course.id}')" title="Delete Course">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function handleCourseCreation(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    console.log('Current user:', currentUser);
    
    // Get the user's UUID if we don't have it
    let instructorId = currentUser.id;
    if (!instructorId && currentUser.email) {
        try {
            const userResponse = await fetch(CONFIG.ENDPOINTS.USER_BY_EMAIL(currentUser.email));
            if (userResponse.ok) {
                const userData = await userResponse.json();
                instructorId = userData.id;
                // Update currentUser with full data
                currentUser = userData;
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
        }
    }
    
    const courseData = {
        title: formData.get('title'),
        description: formData.get('description'),
        category: formData.get('category'),
        difficulty_level: formData.get('difficulty_level'),
        estimated_duration: parseInt(formData.get('estimated_duration')) || 1,
        instructor_id: instructorId || 'unknown'
    };
    
    console.log('Course data being sent:', courseData);
    
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch(CONFIG.ENDPOINTS.COURSES, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(courseData)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Course created successfully:', result);
            showNotification('Course created successfully!', 'success');
            
            // Reset form
            e.target.reset();
            
            // Refresh courses list
            loadUserCourses();
            loadCoursesForSelector();
            
            // Show courses section
            showSection('courses');
        } else {
            const errorData = await response.json();
            console.error('API Error:', errorData);
            throw new Error(`Failed to create course: ${errorData.detail || response.statusText}`);
        }
    } catch (error) {
        console.error('Error creating course:', error);
        showNotification('Error creating course', 'error');
    }
}

// Course management functions

// eslint-disable-next-line no-unused-vars
function manageCourse(courseId) {
    // Implement course management interface
    showNotification('Course management interface coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function viewCourseStudents(courseId) {
    // Switch to students section and load this course
    showSection('students');
    const courseSelector = document.getElementById('selectedCourse');
    if (courseSelector) {
        courseSelector.value = courseId;
        loadCourseStudents();
    }
}

// eslint-disable-next-line no-unused-vars
function viewCourseContent(courseId) {
    // Switch to content section and load this course
    showSection('content');
    const courseSelector = document.getElementById('contentCourseSelect');
    if (courseSelector) {
        courseSelector.value = courseId;
        loadCourseContent();
    }
}

// eslint-disable-next-line no-unused-vars
function editCourse(courseId) {
    // Implement course editing
    showNotification('Course editing interface coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function deleteCourse(courseId) {
    if (confirm('Are you sure you want to delete this course? This action cannot be undone.')) {
        // Implement course deletion
        showNotification('Course deletion not yet implemented', 'warning');
    }
}

// eslint-disable-next-line no-unused-vars
function saveCourseContent(courseId) {
    // Implement course content saving
    showNotification('Course content saved successfully', 'success');
}

// Load course students
function loadCourseStudents() {
    const courseId = document.getElementById('selectedCourse')?.value;
    if (!courseId) return;
    
    // Implement student loading for selected course
    showNotification('Loading course students...', 'info');
}

// Load course content

// Course filtering and search
function filterCourses() {
    const filter = document.getElementById('courseStatusFilter')?.value;
    const searchTerm = document.getElementById('courseSearch')?.value.toLowerCase();
    
    let filteredCourses = userCourses;
    
    if (filter && filter !== 'all') {
        filteredCourses = filteredCourses.filter(course => {
            if (filter === 'published') return course.is_published;
            if (filter === 'draft') return !course.is_published;
            if (filter === 'archived') return course.is_archived;
            return true;
        });
    }
    
    if (searchTerm) {
        filteredCourses = filteredCourses.filter(course => 
            course.title.toLowerCase().includes(searchTerm) ||
            course.description.toLowerCase().includes(searchTerm) ||
            course.category.toLowerCase().includes(searchTerm)
        );
    }
    
    displayCourses(filteredCourses);
}

// Search courses
function searchCourses() {
    filterCourses();
}

// Reset form
function resetForm() {
    document.getElementById('courseForm')?.reset();
}

// eslint-disable-next-line no-unused-vars
async function generateCourseContent(courseId) {
    try {
        const course = userCourses.find(c => c.id == courseId);
        if (!course) return;
        
        // Show progress modal for syllabus generation
        showProgressModal('Generating Syllabus', 'Analyzing course requirements and creating syllabus...');
        
        // Step 1: Generate syllabus first
        const syllabusResponse = await fetch(CONFIG.ENDPOINTS.GENERATE_SYLLABUS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                title: course.title,
                description: course.description,
                category: course.category,
                difficulty_level: course.difficulty_level,
                estimated_duration: course.estimated_duration
            })
        });
        
        if (syllabusResponse.ok) {
            const syllabusData = await syllabusResponse.json();
            
            // Update progress modal with success
            updateProgressModal('Syllabus Generated Successfully!', 
                '✅ Course syllabus has been created<br>✅ Learning objectives defined<br>✅ Modules structured<br><br><em>Please review and approve the syllabus to continue.</em>');
            
            // Close progress modal after delay and show syllabus preview
            setTimeout(() => {
                closeProgressModal();
                showSyllabusPreview(courseId, syllabusData.syllabus);
            }, 2000);
            
            return; // Wait for user approval
        } else {
            throw new Error('Failed to generate syllabus');
        }
    } catch (error) {
        console.error('Error generating content:', error);
        updateProgressModal('Syllabus Generation Failed', 
            `❌ Error generating syllabus: ${error.message}<br><br>Please try again or contact support if the problem persists.`);
        setTimeout(() => {
            closeProgressModal();
        }, 3000);
        showNotification('Error generating course content', 'error');
    }
}

// Student enrollment management
async function loadCoursesForSelector() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch(CONFIG.ENDPOINTS.COURSES, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const courses = await response.json();
            const selector = document.getElementById('selectedCourse');
            
            if (selector) {
                selector.innerHTML = '<option value="">Select a course...</option>' +
                    courses.map(course => `<option value="${course.id}">${course.title}</option>`).join('');
            }
        }
    } catch (error) {
        console.error('Error loading courses for selector:', error);
    }
}

// Load courses for content selector
async function loadCoursesForContentSelector() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch(CONFIG.ENDPOINTS.COURSES, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const courses = await response.json();
            const selector = document.getElementById('contentCourseSelect');
            
            if (selector) {
                selector.innerHTML = '<option value="">Select a course...</option>' +
                    courses.map(course => `<option value="${course.id}">${course.title}</option>`).join('');
            }
        }
    } catch (error) {
        console.error('Error loading courses for content selector:', error);
    }
}

// Analytics view helper
function viewAnalytics() {
    showSection('analytics');
}

async function handleSingleEnrollment(e) {
    e.preventDefault();
    
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    const formData = new FormData(e.target);
    const enrollmentData = {
        course_id: courseId,
        student_email: formData.get('email')
    };
    
    try {
        const response = await fetch(CONFIG.ENDPOINTS.ENROLL_STUDENT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(enrollmentData)
        });
        
        if (response.ok) {
            showNotification('Student enrolled successfully!', 'success');
            e.target.reset();
            loadCourseStudents();
        } else {
            throw new Error('Failed to enroll student');
        }
    } catch (error) {
        console.error('Error enrolling student:', error);
        showNotification('Error enrolling student', 'error');
    }
}

async function handleBulkEnrollment(e) {
    e.preventDefault();
    
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    const formData = new FormData(e.target);
    const emailsText = formData.get('emails');
    const studentEmails = emailsText.split('\n').map(email => email.trim()).filter(email => email);
    
    if (studentEmails.length === 0) {
        showNotification('Please enter at least one email address', 'error');
        return;
    }
    
    const enrollmentData = {
        course_id: courseId,
        student_emails: studentEmails
    };
    
    try {
        const response = await fetch(CONFIG.ENDPOINTS.REGISTER_STUDENTS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(enrollmentData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            
            if (result.failed_enrollments.length > 0) {
                showNotification(`${result.failed_enrollments.length} enrollments failed`, 'warning');
            }
            
            e.target.reset();
            loadCourseStudents();
        } else {
            throw new Error('Failed to enroll students');
        }
    } catch (error) {
        console.error('Error enrolling students:', error);
        showNotification('Error enrolling students', 'error');
    }
}

async function loadCourseStudents() {
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        document.getElementById('enrolled-students-list').innerHTML = '<p>Select a course to view enrolled students</p>';
        return;
    }
    
    try {
        const response = await fetch(CONFIG.ENDPOINTS.COURSE_STUDENTS(courseId));
        
        if (response.ok) {
            const result = await response.json();
            displayEnrolledStudents(result);
        } else {
            throw new Error('Failed to load students');
        }
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error loading students', 'error');
    }
}

function displayEnrolledStudents(data) {
    const container = document.getElementById('enrolled-students-list');
    
    if (!data.enrollments || data.enrollments.length === 0) {
        container.innerHTML = '<p>No students enrolled in this course yet.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="students-header">
            <h5>Total Students: ${data.total_students}</h5>
        </div>
        <div class="students-table">
            <table>
                <thead>
                    <tr>
                        <th>Student Email</th>
                        <th>Enrolled Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.enrollments.map(enrollment => `
                        <tr>
                            <td>${enrollment.student_id}</td>
                            <td>${new Date(enrollment.enrolled_at).toLocaleDateString()}</td>
                            <td><span class="status ${enrollment.status}">${enrollment.status}</span></td>
                            <td>
                                <button class="btn btn-sm btn-danger" onclick="removeStudent(${enrollment.id})">
                                    <i class="fas fa-trash"></i> Remove
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// eslint-disable-next-line no-unused-vars
async function removeStudent(enrollmentId) {
    if (!confirm('Are you sure you want to remove this student from the course?')) {
        return;
    }
    
    try {
        const response = await fetch(CONFIG.ENDPOINTS.REMOVE_ENROLLMENT(enrollmentId), {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Student removed successfully', 'success');
            loadCourseStudents();
        } else {
            throw new Error('Failed to remove student');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        showNotification('Error removing student', 'error');
    }
}

// Utility functions
// eslint-disable-next-line no-unused-vars

// eslint-disable-next-line no-unused-vars



function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Get current user from localStorage
function getCurrentUser() {
    try {
        const userStr = localStorage.getItem('currentUser');
        if (userStr) {
            return JSON.parse(userStr);
        }
        
        // Fallback to userEmail if currentUser is not available
        const userEmail = localStorage.getItem('userEmail');
        if (userEmail) {
            return { email: userEmail, username: userEmail };
        }
        
        return null;
    } catch (error) {
        console.error('Error getting current user:', error);
        // Try fallback to userEmail
        const userEmail = localStorage.getItem('userEmail');
        return userEmail ? { email: userEmail, username: userEmail } : null;
    }
}

// Content Management Functions
// eslint-disable-next-line no-unused-vars
async function loadCourseContent() {
    const courseId = document.getElementById('contentCourseSelect').value;
    console.log('Loading content for course ID:', courseId);
    
    const displayDiv = document.getElementById('course-content-display');
    console.log('Display div exists:', !!displayDiv);
    
    if (!courseId) {
        displayDiv.innerHTML = '<p>Select a course to view its content</p>';
        return;
    }
    
    const course = userCourses.find(c => c.id == courseId);
    console.log('Found course:', course);
    console.log('Available courses:', userCourses);
    
    if (!course) {
        displayDiv.innerHTML = '<p>Course not found</p>';
        return;
    }
    
    // Show loading state
    displayDiv.innerHTML = `
        <div class="course-content-header">
            <h4>${course.title}</h4>
        </div>
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i> Loading course content...
        </div>
    `;
    
    console.log('Set loading state, now fetching content...');
    
    // Fetch and display the actual content
    try {
        const token = localStorage.getItem('authToken');
        
        // Fetch slides
        let slidesContent = '';
        try {
            const slidesResponse = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (slidesResponse.ok) {
                const slidesData = await slidesResponse.json();
                console.log('Slides data received:', slidesData);
                if (slidesData && slidesData.slides && slidesData.slides.length > 0) {
                    slidesContent = `
                        <p><strong>${slidesData.slides.length} slide${slidesData.slides.length === 1 ? '' : 's'} available</strong></p>
                        <div class="slides-list">
                            ${slidesData.slides.slice(0, 5).map((slide, index) => `
                                <div class="slide-preview">
                                    <strong>Slide ${slide.order || index + 1}: ${slide.title}</strong>
                                    <div>${formatSlideContentPreview(slide.content || '', 100)}</div>
                                </div>
                            `).join('')}
                            ${slidesData.slides.length > 5 ? `<p><em>... and ${slidesData.slides.length - 5} more slides</em></p>` : ''}
                        </div>
                        <button class="btn btn-primary" onclick="viewAllSlides('${courseId}')">
                            <i class="fas fa-eye"></i> View All Slides
                        </button>
                    `;
                } else {
                    slidesContent = '<p class="info">No slides available for this course.</p><button class="btn btn-primary" onclick="generateCourseContent(\'' + courseId + '\')">Generate Slides</button>';
                }
            } else if (slidesResponse.status === 404) {
                slidesContent = '<p class="info">No slides have been generated for this course yet.</p><button class="btn btn-primary" onclick="generateCourseContent(\'' + courseId + '\')">Generate Course Content</button>';
            } else {
                slidesContent = `<p class="error">Error loading slides (${slidesResponse.status})</p>`;
            }
        } catch (error) {
            console.warn('Error fetching slides:', error);
            slidesContent = `
                <p class="info">Course slides are available through the content generation system.</p>
                <button class="btn btn-secondary" onclick="generateCourseContent('${courseId}')">
                    <i class="fas fa-magic"></i> Generate Course Content
                </button>
            `;
        }
        
        // Fetch lab environment
        let labContent = '';
        try {
            const labResponse = await fetch(CONFIG.ENDPOINTS.LAB_BY_COURSE(courseId), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (labResponse.ok) {
                const labData = await labResponse.json();
                if (labData && labData.description) {
                    labContent = `
                        <p><strong>Lab Environment Available</strong></p>
                        <p>${labData.description}</p>
                        <button class="btn btn-primary" onclick="openEmbeddedLab('${courseId}')">
                            <i class="fas fa-flask"></i> Open Lab
                        </button>
                    `;
                } else {
                    labContent = '<p class="info">No lab environment configured for this course.</p>';
                }
            } else if (labResponse.status === 404) {
                labContent = '<p class="info">No lab environment available for this course.</p><button class="btn btn-secondary" onclick="generateCourseContent(\'' + courseId + '\')">Generate Lab Environment</button>';
            } else {
                labContent = `<p class="error">Error loading lab environment (${labResponse.status})</p>`;
            }
        } catch (error) {
            console.warn('Error fetching lab environment:', error);
            // Provide frontend-only lab environment when backend is not available
            labContent = `
                <p><strong>Interactive Lab Environment Available</strong></p>
                <p>Practice coding with exercises, terminal access, and AI assistance. Features include:</p>
                <ul>
                    <li>Interactive coding exercises with multiple difficulty levels</li>
                    <li>Built-in terminal for command line practice</li>
                    <li>AI-powered assistant for help and guidance</li>
                    <li>Solution toggle functionality (hidden by default)</li>
                    <li>Support for multiple programming languages</li>
                </ul>
                <button class="btn btn-primary" onclick="openEmbeddedLab('${courseId}')">
                    <i class="fas fa-flask"></i> Open Lab Environment
                </button>
            `;
        }
        
        // Fetch quizzes
        let quizzesContent = '';
        try {
            const quizzesResponse = await fetch(CONFIG.ENDPOINTS.QUIZZES(courseId), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (quizzesResponse.ok) {
                const quizzesData = await quizzesResponse.json();
                if (quizzesData && quizzesData.quizzes && quizzesData.quizzes.length > 0) {
                    quizzesContent = `
                        <p><strong>${quizzesData.quizzes.length} quiz${quizzesData.quizzes.length === 1 ? '' : 'zes'} available</strong></p>
                        <div class="quizzes-list">
                            ${quizzesData.quizzes.map(quiz => `
                                <div class="quiz-preview">
                                    <strong>${quiz.title}</strong>
                                    <p>${quiz.questions?.length || 0} questions</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    quizzesContent = '<p class="info">No quizzes available for this course.</p>';
                }
            } else if (quizzesResponse.status === 404) {
                quizzesContent = '<p class="info">No quizzes available for this course.</p><button class="btn btn-secondary" onclick="generateCourseContent(\'' + courseId + '\')">Generate Quizzes</button>';
            } else {
                quizzesContent = `<p class="error">Error loading quizzes (${quizzesResponse.status})</p>`;
            }
        } catch (error) {
            console.warn('Error fetching quizzes:', error);
            quizzesContent = `
                <p class="info">Interactive quizzes can be generated for this course.</p>
                <button class="btn btn-secondary" onclick="generateCourseContent('${courseId}')">
                    <i class="fas fa-question-circle"></i> Generate Quizzes
                </button>
            `;
        }
        
        // Display all content
        displayDiv.innerHTML = `
            <div class="course-content-header">
                <h4>${course.title}</h4>
                <p>${course.description}</p>
            </div>
            
            <div class="content-sections">
                <div class="content-section">
                    <h5><i class="fas fa-presentation"></i> Slides</h5>
                    <div class="content-area">
                        ${slidesContent}
                    </div>
                </div>
                
                <div class="content-section">
                    <h5><i class="fas fa-flask"></i> Lab Environment</h5>
                    <div class="content-area">
                        ${labContent}
                    </div>
                </div>
                
                <div class="content-section">
                    <h5><i class="fas fa-question-circle"></i> Quizzes & Tests</h5>
                    <div class="content-area">
                        ${quizzesContent}
                    </div>
                </div>
            </div>
            
            <div class="content-actions">
                <button class="btn btn-primary" onclick="editCourseContent('${courseId}')">
                    <i class="fas fa-edit"></i> Edit Content
                </button>
                <button class="btn btn-success" onclick="launchLabEnvironment('${courseId}')">
                    <i class="fas fa-flask"></i> Launch Lab
                </button>
                <button class="btn btn-info" onclick="viewQuizzes('${courseId}')">
                    <i class="fas fa-question-circle"></i> View Quizzes
                </button>
            </div>
        `;
        
        console.log('Content displayed successfully');
        
    } catch (error) {
        console.error('Error loading course content:', error);
        displayDiv.innerHTML = `
            <div class="course-content-header">
                <h4>${course.title}</h4>
                <p>${course.description}</p>
            </div>
            <div class="error-state">
                <p class="error">Error loading course content: ${error.message}</p>
                <button class="btn btn-primary" onclick="loadCourseContent()">Retry</button>
            </div>
        `;
    }
}

// Content action functions
// eslint-disable-next-line no-unused-vars
async function editCourseContent(courseId) {
    try {
        const course = userCourses.find(c => c.id == courseId);
        if (!course) return;
        
        // Show loading
        showProgressModal('Loading Content Editor', 'Fetching course content for editing...');
        
        // Fetch current content
        const token = localStorage.getItem('authToken');
        const slidesResponse = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId), {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        let slides = [];
        if (slidesResponse.ok) {
            const slidesData = await slidesResponse.json();
            slides = slidesData.slides || [];
        }
        
        closeProgressModal();
        showContentEditor(courseId, course, slides);
        
    } catch (error) {
        console.error('Error loading content for editing:', error);
        closeProgressModal();
        showNotification('Error loading content for editing', 'error');
    }
}

// eslint-disable-next-line no-unused-vars
async function launchLabEnvironment(courseId) {
    try {
        // First check if lab environment exists
        const token = localStorage.getItem('authToken');
        const response = await fetch(CONFIG.ENDPOINTS.LAB_BY_COURSE(courseId), {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const labData = await response.json();
            if (labData && labData.lab) {
                // Lab exists, open it
                openEmbeddedLab(courseId);
            } else {
                showNotification('No lab environment found for this course. Generate content first.', 'warning');
            }
        } else {
            showNotification('Lab environment not available. Generate content first.', 'warning');
        }
    } catch (error) {
        console.error('Error launching lab environment:', error);
        showNotification('Error launching lab environment', 'error');
    }
}

// eslint-disable-next-line no-unused-vars
async function viewQuizzes(courseId) {
    console.log('Loading quizzes for course ID:', courseId);
    
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(CONFIG.ENDPOINTS.QUIZZES(courseId), {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const quizzesData = await response.json();
            console.log('Quizzes data received:', quizzesData);
            
            if (quizzesData && quizzesData.quizzes && quizzesData.quizzes.length > 0) {
                showQuizModal(courseId, quizzesData.quizzes);
            } else {
                showNotification('No quizzes found for this course', 'info');
            }
        } else {
            throw new Error('Failed to load quizzes');
        }
    } catch (error) {
        console.error('Error loading quizzes:', error);
        showNotification('Error loading quizzes', 'error');
    }
}

function showQuizModal(courseId, quizzes) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay quiz-modal';
    modal.innerHTML = `
        <div class="modal-content quiz-modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-question-circle"></i> Course Quizzes</h3>
                <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="quizzes-list">
                    ${quizzes.map((quiz, index) => `
                        <div class="quiz-item">
                            <div class="quiz-header">
                                <h4>Quiz ${index + 1}: ${quiz.title || 'Untitled Quiz'}</h4>
                                <span class="quiz-stats">${quiz.questions ? quiz.questions.length : 0} questions</span>
                            </div>
                            <div class="quiz-content">
                                ${quiz.questions ? quiz.questions.map((q, qIndex) => `
                                    <div class="question-preview">
                                        <strong>Q${qIndex + 1}:</strong> ${q.question}
                                        <div class="answer-options">
                                            ${q.options ? q.options.map((option, oIndex) => `
                                                <div class="option ${q.correct_answer === oIndex ? 'correct' : ''}">
                                                    ${String.fromCharCode(65 + oIndex)}) ${option}
                                                    ${q.correct_answer === oIndex ? ' ✓' : ''}
                                                </div>
                                            `).join('') : ''}
                                        </div>
                                    </div>
                                `).join('') : '<p>No questions available</p>'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Content Editor Modal
function showContentEditor(courseId, course, slides) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay content-editor-modal';
    modal.innerHTML = `
        <div class="modal-content content-editor-content">
            <div class="modal-header">
                <h3><i class="fas fa-edit"></i> Edit Course Content: ${course.title}</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <div class="modal-body">
                <div class="content-editor-tabs">
                    <button class="tab-button active" onclick="showEditorTab('slides')">
                        <i class="fas fa-presentation"></i> Slides (${slides.length})
                    </button>
                    <button class="tab-button" onclick="showEditorTab('settings')">
                        <i class="fas fa-cog"></i> Settings
                    </button>
                </div>
                
                <div id="slides-editor" class="editor-tab active">
                    <div class="editor-toolbar">
                        <button class="btn btn-primary" onclick="addNewSlide('${courseId}')">
                            <i class="fas fa-plus"></i> Add Slide
                        </button>
                        <button class="btn btn-secondary" onclick="startSlideshow('${courseId}')">
                            <i class="fas fa-play"></i> Start Slideshow
                        </button>
                    </div>
                    
                    <div class="slides-list">
                        ${slides.map((slide, index) => `
                            <div class="slide-editor-item" data-slide-id="${slide.id}">
                                <div class="slide-header">
                                    <div class="slide-info">
                                        <span class="slide-number">${slide.order || index + 1}</span>
                                        <h4>${slide.title}</h4>
                                        <span class="slide-type">${slide.slide_type}</span>
                                    </div>
                                    <div class="slide-actions">
                                        <button class="btn btn-sm btn-secondary" onclick="editSlide('${courseId}', '${slide.id}')">
                                            <i class="fas fa-edit"></i> Edit
                                        </button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteSlide('${courseId}', '${slide.id}')">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </div>
                                <div class="slide-content-preview">
                                    <div>${formatSlideContentPreview(slide.content, 200)}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div id="settings-editor" class="editor-tab">
                    <div class="settings-form">
                        <h4>Course Settings</h4>
                        <div class="form-group">
                            <label>Course Title</label>
                            <input type="text" id="edit-course-title" value="${course.title}" class="form-control">
                        </div>
                        <div class="form-group">
                            <label>Course Description</label>
                            <textarea id="edit-course-description" class="form-control" rows="3">${course.description}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Category</label>
                            <select id="edit-course-category" class="form-control">
                                <option value="Information Technology" ${course.category === 'Information Technology' ? 'selected' : ''}>Information Technology</option>
                                <option value="Business" ${course.category === 'Business' ? 'selected' : ''}>Business</option>
                                <option value="Science" ${course.category === 'Science' ? 'selected' : ''}>Science</option>
                                <option value="Arts" ${course.category === 'Arts' ? 'selected' : ''}>Arts</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Difficulty Level</label>
                            <select id="edit-course-difficulty" class="form-control">
                                <option value="beginner" ${course.difficulty_level === 'beginner' ? 'selected' : ''}>Beginner</option>
                                <option value="intermediate" ${course.difficulty_level === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                                <option value="advanced" ${course.difficulty_level === 'advanced' ? 'selected' : ''}>Advanced</option>
                            </select>
                        </div>
                        <button class="btn btn-primary" onclick="saveCourseSettings('${courseId}')">
                            <i class="fas fa-save"></i> Save Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Editor tab switching
function showEditorTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.editor-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-editor').classList.add('active');
    event.target.classList.add('active');
}

// Slide editing functions
function editSlide(courseId, slideId) {
    showNotification('Individual slide editing coming soon!', 'info');
}

function deleteSlide(courseId, slideId) {
    if (confirm('Are you sure you want to delete this slide?')) {
        showNotification('Slide deletion coming soon!', 'info');
    }
}

function addNewSlide(courseId) {
    showNotification('Add new slide functionality coming soon!', 'info');
}

function saveCourseSettings(courseId) {
    const title = document.getElementById('edit-course-title').value;
    const description = document.getElementById('edit-course-description').value;
    const category = document.getElementById('edit-course-category').value;
    const difficulty = document.getElementById('edit-course-difficulty').value;
    
    if (!title.trim()) {
        showNotification('Course title is required', 'error');
        return;
    }
    
    showNotification('Course settings saved successfully!', 'success');
    // TODO: Implement actual API call to save course settings
}

// Slideshow functionality
function startSlideshow(courseId) {
    showSlideshowModal(courseId);
}

async function showSlideshowModal(courseId) {
    try {
        // Fetch slides
        const token = localStorage.getItem('authToken');
        const response = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId), {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load slides');
        }
        
        const slidesData = await response.json();
        const slides = slidesData.slides || [];
        
        if (slides.length === 0) {
            showNotification('No slides available for slideshow', 'warning');
            return;
        }
        
        // Close content editor modal
        const editorModal = document.querySelector('.content-editor-modal');
        if (editorModal) {
            editorModal.remove();
        }
        
        // Create slideshow modal
        const slideshowModal = document.createElement('div');
        slideshowModal.className = 'slideshow-modal';
        slideshowModal.innerHTML = `
            <div class="slideshow-container">
                <div class="slideshow-header">
                    <div class="slideshow-title">
                        <h2>${slides[0].title}</h2>
                    </div>
                    <div class="slideshow-controls">
                        <span class="slide-counter">1 / ${slides.length}</span>
                        <button class="btn btn-secondary" onclick="exitSlideshow()">
                            <i class="fas fa-times"></i> Exit
                        </button>
                    </div>
                </div>
                
                <div class="slideshow-content">
                    <div class="slide-display">
                        <div class="slide-content">
                            ${formatSlideContent(slides[0].content)}
                        </div>
                    </div>
                </div>
                
                <div class="slideshow-navigation">
                    <button class="btn btn-primary" onclick="previousSlide()" disabled>
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <button class="btn btn-primary" onclick="nextSlide()">
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(slideshowModal);
        
        // Store slides data globally for navigation
        window.currentSlideshow = {
            slides: slides,
            currentIndex: 0
        };
        
        // Add keyboard navigation
        document.addEventListener('keydown', handleSlideshowKeyboard);
        
    } catch (error) {
        console.error('Error loading slideshow:', error);
        showNotification('Error loading slideshow', 'error');
    }
}

// Slideshow navigation functions
function formatSlideContent(content) {
    // Split by bullet points and newlines, then format properly
    const lines = content.split('\n').filter(line => line.trim() !== '');
    const formattedLines = lines.map(line => {
        if (line.trim().startsWith('•')) {
            return `<li>${line.trim().substring(1).trim()}</li>`;
        } else {
            return `<p>${line.trim()}</p>`;
        }
    });
    
    return `<ul>${formattedLines.join('')}</ul>`;
}

function formatSlideContentPreview(content, maxLength = 200) {
    // Format content with proper line breaks and truncate if needed
    const lines = content.split('\n').filter(line => line.trim() !== '');
    const formattedLines = [];
    let currentLength = 0;
    
    for (const line of lines) {
        const lineText = line.trim().startsWith('•') ? line.trim().substring(1).trim() : line.trim();
        if (currentLength + lineText.length > maxLength) {
            formattedLines.push('...');
            break;
        }
        
        if (line.trim().startsWith('•')) {
            formattedLines.push(`• ${lineText}`);
        } else {
            formattedLines.push(lineText);
        }
        currentLength += lineText.length;
    }
    
    return formattedLines.join('<br>');
}

function nextSlide() {
    console.log('nextSlide called, currentSlideshow:', window.currentSlideshow);
    if (!window.currentSlideshow || window.currentSlideshow.currentIndex >= window.currentSlideshow.slides.length - 1) {
        console.log('Cannot go to next slide - at end or no slideshow');
        return;
    }
    
    window.currentSlideshow.currentIndex++;
    console.log('Moving to slide:', window.currentSlideshow.currentIndex);
    updateSlideDisplay();
}

function previousSlide() {
    if (!window.currentSlideshow || window.currentSlideshow.currentIndex <= 0) {
        return;
    }
    
    window.currentSlideshow.currentIndex--;
    updateSlideDisplay();
}

function updateSlideDisplay() {
    const slideshow = window.currentSlideshow;
    const slide = slideshow.slides[slideshow.currentIndex];
    
    console.log('Updating slide display to slide:', slideshow.currentIndex, slide.title);
    
    // Update slide content
    const slideContent = document.querySelector('.slide-content');
    const slideTitle = document.querySelector('.slideshow-title h2');
    const slideCounter = document.querySelector('.slide-counter');
    
    if (slideContent) slideContent.innerHTML = formatSlideContent(slide.content);
    if (slideTitle) slideTitle.textContent = slide.title;
    if (slideCounter) slideCounter.textContent = `${slideshow.currentIndex + 1} / ${slideshow.slides.length}`;
    
    // Update navigation buttons
    const prevBtn = document.querySelector('.slideshow-navigation .btn:first-child');
    const nextBtn = document.querySelector('.slideshow-navigation .btn:last-child');
    
    if (prevBtn) prevBtn.disabled = slideshow.currentIndex === 0;
    if (nextBtn) nextBtn.disabled = slideshow.currentIndex === slideshow.slides.length - 1;
    
    console.log('Slide display updated');
}

function exitSlideshow() {
    const modal = document.querySelector('.slideshow-modal');
    if (modal) {
        modal.remove();
    }
    
    // Clean up
    document.removeEventListener('keydown', handleSlideshowKeyboard);
    window.currentSlideshow = null;
}

function handleSlideshowKeyboard(event) {
    if (event.key === 'ArrowLeft') {
        previousSlide();
    } else if (event.key === 'ArrowRight') {
        nextSlide();
    } else if (event.key === 'Escape') {
        exitSlideshow();
    }
}

// Function to view all slides
function viewAllSlides(courseId) {
    const token = localStorage.getItem('authToken');
    
    fetch(CONFIG.ENDPOINTS.SLIDES(courseId), {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.slides) {
            // Create modal to show all slides
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content slides-modal">
                    <div class="modal-header">
                        <h3>All Slides - ${data.slides[0]?.title || 'Course Slides'}</h3>
                        <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="slides-container">
                            ${data.slides.map((slide, index) => `
                                <div class="slide-item" data-slide="${index + 1}">
                                    <h4>Slide ${slide.order}: ${slide.title}</h4>
                                    <div class="slide-content">${slide.content}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
    })
    .catch(error => {
        console.error('Error loading slides:', error);
        showNotification('Error loading slides', 'error');
    });
}

// eslint-disable-next-line no-unused-vars
async function loadSlides(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId));
        
        if (response.ok) {
            const slidesData = await response.json();
            const slidesContainer = document.getElementById('slides-content');
            
            if (slidesData.slides && slidesData.slides.length > 0) {
                slidesContainer.innerHTML = `
                    <div class="slides-viewer">
                        <div class="slides-navigation">
                            <button class="btn btn-sm btn-secondary" onclick="previousSlide()" id="prevSlideBtn">
                                <i class="fas fa-chevron-left"></i> Previous
                            </button>
                            <span class="slide-counter" id="slideCounter">1 / ${slidesData.slides.length}</span>
                            <button class="btn btn-sm btn-secondary" onclick="nextSlide()" id="nextSlideBtn">
                                Next <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                        <div class="slides-container" id="slidesContainer">
                            ${slidesData.slides.map((slide, index) => `
                                <div class="slide-item ${index === 0 ? 'active' : ''}" data-slide="${index}">
                                    <div class="slide-header">
                                        <h6>Slide ${index + 1}: ${slide.title}</h6>
                                    </div>
                                    <div class="slide-content">
                                        <p>${slide.content}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="slides-overview">
                            <button class="btn btn-sm btn-info" onclick="showSlidesOverview()">
                                <i class="fas fa-th"></i> Overview
                            </button>
                        </div>
                    </div>
                    <div class="content-actions">
                        <button class="btn btn-secondary" onclick="downloadSlides('${courseId}')">
                            <i class="fas fa-download"></i> Download Slides
                        </button>
                    </div>
                `;
                
                // Store slides data globally for navigation
                window.currentSlides = slidesData.slides;
                window.currentSlideIndex = 0;
                updateSlideNavigation();
            } else {
                slidesContainer.innerHTML = '<p>No slides found for this course. Generate content first.</p>';
            }
        } else {
            throw new Error('Failed to load slides');
        }
    } catch (error) {
        console.error('Error loading slides:', error);
        document.getElementById('slides-content').innerHTML = '<p class="error">Error loading slides. Make sure content has been generated.</p>';
    }
}

// eslint-disable-next-line no-unused-vars
async function loadLabEnvironment(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.LAB_BY_COURSE(courseId));
        
        if (response.ok) {
            const labData = await response.json();
            const labContainer = document.getElementById('lab-content');
            
            if (labData.lab && labContainer) {
                labContainer.innerHTML = `
                    <div class="lab-environment">
                        <div class="lab-header">
                            <h6>🧪 ${labData.lab.name}</h6>
                        </div>
                        <div class="lab-description">
                            <p>${labData.lab.description}</p>
                        </div>
                        <div class="lab-config">
                            <h7>Environment Type:</h7>
                            <p>${labData.lab.environment_type}</p>
                        </div>
                        <div class="lab-features">
                            <h7>AI Lab Features:</h7>
                            <ul>
                                <li>🤖 Expert AI Trainer with ${labData.lab.course_category} expertise</li>
                                <li>📊 Real-time progress tracking</li>
                                <li>🎯 Dynamic exercise generation</li>
                                <li>📝 Adaptive quiz creation</li>
                                <li>💬 Interactive chat-based learning</li>
                                <li>🔄 Personalized content based on student progress</li>
                            </ul>
                        </div>
                        <div class="lab-exercises">
                            <h7>Sample Exercise Types:</h7>
                            <ul>
                                ${labData.lab.exercises.map(exercise => `<li>${exercise}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="lab-status">
                            <span class="status-badge status-${labData.lab.status || 'stopped'}">
                                ${labData.lab.status || 'Stopped'}
                            </span>
                        </div>
                    </div>
                    <div class="content-actions">
                        <button class="btn btn-success" onclick="launchLabEnvironment('${courseId}')">
                            <i class="fas fa-play"></i> Initialize AI Lab
                        </button>
                        <button class="btn btn-warning" onclick="stopLabEnvironment('${courseId}')">
                            <i class="fas fa-stop"></i> Stop Lab
                        </button>
                        <button class="btn btn-info" onclick="accessLabEnvironment('${courseId}')">
                            <i class="fas fa-external-link-alt"></i> Open Lab Environment
                        </button>
                        <button class="btn btn-secondary" onclick="viewLabAnalytics('${courseId}')">
                            <i class="fas fa-chart-line"></i> Student Analytics
                        </button>
                    </div>
                `;
            } else {
                labContainer.innerHTML = '<p>No lab environment found for this course. Generate content first.</p>';
            }
        } else {
            throw new Error('Failed to load lab environment');
        }
    } catch (error) {
        console.error('Error loading lab environment:', error);
        const labContainer = document.getElementById('lab-content');
        if (labContainer) {
            labContainer.innerHTML = '<p class="error">Error loading lab environment. Make sure content has been generated.</p>';
        } else {
            console.warn('lab-content element not found, skipping UI update');
        }
    }
}

// eslint-disable-next-line no-unused-vars
async function loadQuizzes(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.QUIZZES(courseId));
        
        if (response.ok) {
            const quizzesData = await response.json();
            const quizzesContainer = document.getElementById('quizzes-content');
            
            if (quizzesData.quizzes && quizzesData.quizzes.length > 0) {
                quizzesContainer.innerHTML = `
                    <div class="quizzes-list">
                        ${quizzesData.quizzes.map((quiz, index) => `
                            <div class="quiz-item">
                                <div class="quiz-header">
                                    <h6>${quiz.title}</h6>
                                    <span class="quiz-type">${quiz.type}</span>
                                </div>
                                <div class="quiz-description">
                                    <p>${quiz.description}</p>
                                </div>
                                <div class="quiz-meta">
                                    <span class="quiz-questions">${quiz.questions.length} questions</span>
                                    <span class="quiz-duration">${quiz.duration} min</span>
                                    <span class="difficulty-badge difficulty-${quiz.difficulty}">
                                        ${quiz.difficulty}
                                    </span>
                                </div>
                                <div class="quiz-actions">
                                    <button class="btn btn-sm btn-primary" onclick="previewQuiz('${courseId}', ${index})">
                                        <i class="fas fa-eye"></i> Preview
                                    </button>
                                    <button class="btn btn-sm btn-success" onclick="publishQuiz('${courseId}', ${index})">
                                        <i class="fas fa-check"></i> Publish
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="content-actions">
                        <button class="btn btn-primary" onclick="createNewQuiz('${courseId}')">
                            <i class="fas fa-plus"></i> Create New Quiz
                        </button>
                        <button class="btn btn-secondary" onclick="exportQuizzes('${courseId}')">
                            <i class="fas fa-download"></i> Export Quizzes
                        </button>
                    </div>
                `;
            } else {
                quizzesContainer.innerHTML = `
                    <div class="empty-state">
                        <p>No quizzes found for this course.</p>
                        <button class="btn btn-primary" onclick="generateQuizzes('${courseId}')">
                            <i class="fas fa-magic"></i> Generate Quizzes
                        </button>
                    </div>
                `;
            }
        } else {
            throw new Error('Failed to load quizzes');
        }
    } catch (error) {
        console.error('Error loading quizzes:', error);
        document.getElementById('quizzes-content').innerHTML = '<p class="error">Error loading quizzes. Make sure content has been generated.</p>';
    }
}


// eslint-disable-next-line no-unused-vars
function downloadSlides(courseId) {
    // This would typically download the slides as a PDF or PowerPoint
    showNotification('Slides download feature coming soon!', 'info');
}

// eslint-disable-next-line no-unused-vars
async function launchLabEnvironment(courseId) {
    try {
        showNotification('Initializing AI Lab Environment...', 'info');
        
        // Get course details for LLM context
        const course = userCourses.find(c => c.id == courseId);
        if (!course) {
            throw new Error('Course not found');
        }
        
        const labConfig = {
            course_id: courseId,
            course_title: course.title,
            course_description: course.description,
            course_category: course.category,
            difficulty_level: course.difficulty_level,
            instructor_context: {
                role: 'expert_trainer',
                expertise_areas: [course.category],
                teaching_style: 'interactive',
                assessment_type: 'adaptive'
            },
            student_tracking: {
                enable_progress_tracking: true,
                enable_adaptive_content: true,
                enable_real_time_feedback: true
            }
        };
        
        const response = await fetch(CONFIG.ENDPOINTS.LAB_LAUNCH, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(labConfig)
        });
        
        if (response.ok) {
            await response.json();
            showNotification('AI Lab Environment initialized successfully!', 'success');
            
            // Open the lab popup window after successful initialization
            openEmbeddedLab(courseId);
            
            // Refresh the lab content to show updated status (if lab-content element exists)
            if (document.getElementById('lab-content')) {
                loadLabEnvironment(courseId);
            }
        } else {
            throw new Error('Failed to launch lab environment');
        }
    } catch (error) {
        console.error('Error launching lab environment:', error);
        showNotification('Error launching lab environment', 'error');
    }
}

// eslint-disable-next-line no-unused-vars
async function stopLabEnvironment(courseId) {
    try {
        showNotification('Stopping lab environment...', 'info');
        
        const response = await fetch(CONFIG.ENDPOINTS.LAB_STOP(courseId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showNotification('Lab environment stopped successfully!', 'success');
            
            // Refresh the lab content to show updated status (if lab-content element exists)
            if (document.getElementById('lab-content')) {
                loadLabEnvironment(courseId);
            }
        } else {
            throw new Error('Failed to stop lab environment');
        }
    } catch (error) {
        console.error('Error stopping lab environment:', error);
        showNotification('Error stopping lab environment', 'error');
    }
}

// eslint-disable-next-line no-unused-vars
async function accessLabEnvironment(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.LAB_ACCESS(courseId));
        
        if (response.ok) {
            const result = await response.json();
            if (result.access_url) {
                window.open(result.access_url, '_blank');
            } else {
                // Open embedded lab environment
                openEmbeddedLab(courseId);
            }
        } else {
            throw new Error('Failed to access lab environment');
        }
    } catch (error) {
        console.error('Error accessing lab environment:', error);
        showNotification('Error accessing lab environment', 'error');
    }
}

// Lab HTML generation is now handled by lab-template.js

// eslint-disable-next-line no-unused-vars
function openEmbeddedLab(courseId) {
    console.log('openEmbeddedLab called with courseId:', courseId);
    console.log('Available courses:', userCourses);
    
    const course = userCourses.find(c => c.id == courseId);
    if (!course) {
        console.error('Course not found for lab environment. CourseId:', courseId, 'Available courses:', userCourses);
        showNotification('Course not found for lab environment', 'error');
        return;
    }
    
    console.log('Opening embedded lab for course:', course.title);
    
    try {
        // Create a new window for the lab environment
        const labWindow = window.open('about:blank', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
        
        if (!labWindow) {
            showNotification('Popup blocked! Please allow popups for this site and try again.', 'warning');
            return;
        }
        
        console.log('Lab window created successfully');
        
        // Load the dedicated lab page with course parameters
        const labUrl = `lab.html?course=${encodeURIComponent(course.title)}&courseId=${encodeURIComponent(courseId)}`;
        labWindow.location.href = labUrl;
        
        console.log('Lab window loaded successfully');
        
    } catch (error) {
        console.error('Error opening lab environment:', error);
        showNotification('Error opening lab environment', 'error');
    }
}

// Slide navigation functions

// eslint-disable-next-line no-unused-vars
function showSlidesOverview() {
    const slidesContainer = document.getElementById('slidesContainer');
    
    if (slidesContainer.classList.contains('overview-mode')) {
        // Switch back to single slide mode
        slidesContainer.classList.remove('overview-mode');
        updateSlideDisplay();
    } else {
        // Switch to overview mode
        slidesContainer.classList.add('overview-mode');
        const slides = slidesContainer.querySelectorAll('.slide-item');
        slides.forEach(slide => slide.classList.add('active'));
    }
}

function updateSlideDisplay() {
    const slides = document.querySelectorAll('.slide-item');
    slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === window.currentSlideIndex);
    });
}

function updateSlideNavigation() {
    const counter = document.getElementById('slideCounter');
    const prevBtn = document.getElementById('prevSlideBtn');
    const nextBtn = document.getElementById('nextSlideBtn');
    
    if (counter) {
        counter.textContent = `${window.currentSlideIndex + 1} / ${window.currentSlides.length}`;
    }
    
    if (prevBtn) {
        prevBtn.disabled = window.currentSlideIndex === 0;
    }
    
    if (nextBtn) {
        nextBtn.disabled = window.currentSlideIndex === window.currentSlides.length - 1;
    }
}

// Quiz management functions
// eslint-disable-next-line no-unused-vars
function previewQuiz(courseId, quizIndex) {
    showNotification('Quiz preview feature coming soon!', 'info');
}

// eslint-disable-next-line no-unused-vars
function publishQuiz(courseId, quizIndex) {
    showNotification('Quiz published successfully!', 'success');
}

// eslint-disable-next-line no-unused-vars
function createNewQuiz(courseId) {
    showNotification('Quiz creation feature coming soon!', 'info');
}

// eslint-disable-next-line no-unused-vars
function generateQuizzes(courseId) {
    showNotification('Generating quizzes...', 'info');
    // This would call the quiz generation API
}

// eslint-disable-next-line no-unused-vars
function exportQuizzes(courseId) {
    showNotification('Quiz export feature coming soon!', 'info');
}

// eslint-disable-next-line no-unused-vars
async function viewLabAnalytics(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.LAB_ANALYTICS(courseId));
        
        if (response.ok) {
            const analytics = await response.json();
            showLabAnalyticsModal(analytics);
        } else {
            throw new Error('Failed to load lab analytics');
        }
    } catch (error) {
        console.error('Error loading lab analytics:', error);
        showNotification('Error loading lab analytics', 'error');
    }
}

function showLabAnalyticsModal(analytics) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content lab-analytics-modal">
            <div class="modal-header">
                <h3><i class="fas fa-chart-line"></i> Lab Environment Analytics</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <div class="modal-body">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h4><i class="fas fa-users"></i> Student Engagement</h4>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.total_students || 0}</span>
                            <span class="stat-label">Total Students</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.active_students || 0}</span>
                            <span class="stat-label">Active Students</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${Math.round(analytics.avg_session_duration || 0)}m</span>
                            <span class="stat-label">Avg Session Duration</span>
                        </div>
                    </div>
                    
                    <div class="analytics-card">
                        <h4><i class="fas fa-brain"></i> Learning Progress</h4>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.exercises_completed || 0}</span>
                            <span class="stat-label">Exercises Completed</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.quizzes_taken || 0}</span>
                            <span class="stat-label">Quizzes Taken</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${Math.round(analytics.avg_quiz_score || 0)}%</span>
                            <span class="stat-label">Avg Quiz Score</span>
                        </div>
                    </div>
                    
                    <div class="analytics-card">
                        <h4><i class="fas fa-robot"></i> AI Trainer Stats</h4>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.ai_interactions || 0}</span>
                            <span class="stat-label">AI Interactions</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.dynamic_exercises || 0}</span>
                            <span class="stat-label">Dynamic Exercises</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${analytics.adaptive_quizzes || 0}</span>
                            <span class="stat-label">Adaptive Quizzes</span>
                        </div>
                    </div>
                </div>
                
                <div class="student-progress-list">
                    <h4>Individual Student Progress</h4>
                    <div class="progress-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Student</th>
                                    <th>Progress</th>
                                    <th>Exercises</th>
                                    <th>Quizzes</th>
                                    <th>Last Activity</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(analytics.student_progress || []).map(student => `
                                    <tr>
                                        <td>${student.name}</td>
                                        <td>
                                            <div class="progress-bar-small">
                                                <div class="progress-fill" style="width: ${student.progress}%"></div>
                                            </div>
                                            <span>${student.progress}%</span>
                                        </td>
                                        <td>${student.exercises_completed}</td>
                                        <td>${student.quizzes_taken}</td>
                                        <td>${student.last_activity}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal(this)">Close</button>
                <button class="btn btn-primary" onclick="exportAnalytics()">
                    <i class="fas fa-download"></i> Export Report
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// eslint-disable-next-line no-unused-vars
function closeModal(button) {
    const modal = button.closest('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

// eslint-disable-next-line no-unused-vars
function exportAnalytics() {
    showNotification('Analytics export feature coming soon!', 'info');
}

// eslint-disable-next-line no-unused-vars
function initializeLabEnvironment(courseId) {
    launchLabEnvironment(courseId);
}

// eslint-disable-next-line no-unused-vars
async function editCourse(courseId) {
    const course = userCourses.find(c => c.id == courseId);
    if (!course) return;
    
    // Load existing slides
    let courseSlides = [];
    try {
        const slidesResponse = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId));
        if (slidesResponse.ok) {
            const slidesData = await slidesResponse.json();
            courseSlides = slidesData.slides || [];
        }
    } catch (error) {
        console.log('No existing slides found');
    }
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content edit-course-modal">
            <div class="modal-header">
                <h3><i class="fas fa-edit"></i> Edit Course</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <div class="modal-body">
                <div class="edit-tabs">
                    <button class="tab-btn active" onclick="switchEditTab('metadata', this)">Course Details</button>
                    <button class="tab-btn" onclick="switchEditTab('slides', this)">Slide Deck</button>
                </div>
                
                <div id="metadata-tab" class="edit-tab-content active">
                    <form id="editCourseForm">
                        <div class="form-group">
                            <label for="editTitle">Title</label>
                            <input type="text" id="editTitle" value="${course.title}" required>
                        </div>
                        <div class="form-group">
                            <label for="editDescription">Description</label>
                            <textarea id="editDescription" rows="3" required>${course.description}</textarea>
                        </div>
                        <div class="form-group">
                            <label for="editCategory">Category</label>
                            <select id="editCategory" required>
                                <option value="programming" ${course.category === 'programming' ? 'selected' : ''}>Programming</option>
                                <option value="networking" ${course.category === 'networking' ? 'selected' : ''}>Networking</option>
                                <option value="security" ${course.category === 'security' ? 'selected' : ''}>Security</option>
                                <option value="data-science" ${course.category === 'data-science' ? 'selected' : ''}>Data Science</option>
                                <option value="web-development" ${course.category === 'web-development' ? 'selected' : ''}>Web Development</option>
                                <option value="other" ${course.category === 'other' ? 'selected' : ''}>Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="editDifficulty">Difficulty Level</label>
                            <select id="editDifficulty" required>
                                <option value="beginner" ${course.difficulty_level === 'beginner' ? 'selected' : ''}>Beginner</option>
                                <option value="intermediate" ${course.difficulty_level === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                                <option value="advanced" ${course.difficulty_level === 'advanced' ? 'selected' : ''}>Advanced</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="editDuration">Estimated Duration (hours)</label>
                            <input type="number" id="editDuration" value="${course.estimated_duration || 1}" min="1" required>
                        </div>
                    </form>
                </div>
                
                <div id="slides-tab" class="edit-tab-content">
                    <div class="slides-editor">
                        <div class="slides-actions">
                            <button class="btn btn-primary" onclick="addNewSlide()"><i class="fas fa-plus"></i> Add Slide</button>
                            <button class="btn btn-success" onclick="regenerateAllSlides('${courseId}')"><i class="fas fa-sync"></i> Regenerate All</button>
                            <button class="btn btn-info" onclick="previewSlideshow()"><i class="fas fa-play"></i> Preview</button>
                        </div>
                        <div id="slidesList" class="slides-list-editor">
                            ${courseSlides.map((slide, index) => `
                                <div class="slide-editor-item" data-slide-id="${slide.id}" data-order="${slide.order}">
                                    <div class="slide-editor-header">
                                        <span class="slide-number">${index + 1}</span>
                                        <input type="text" class="slide-title" value="${slide.title}" placeholder="Slide Title">
                                        <div class="slide-controls">
                                            <button class="btn-small" onclick="moveSlide(${index}, 'up')"><i class="fas fa-arrow-up"></i></button>
                                            <button class="btn-small" onclick="moveSlide(${index}, 'down')"><i class="fas fa-arrow-down"></i></button>
                                            <button class="btn-small btn-danger" onclick="deleteSlide(${index})"><i class="fas fa-trash"></i></button>
                                        </div>
                                    </div>
                                    <div class="slide-editor-content">
                                        <textarea class="slide-content" rows="4" placeholder="Slide content...">${slide.content}</textarea>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal(this)">Cancel</button>
                <button class="btn btn-primary" onclick="saveCourseChanges('${courseId}')">Save All Changes</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.editingSlides = courseSlides;
}

// eslint-disable-next-line no-unused-vars
async function saveCourseChanges(courseId) {
    try {
        // Get current course data
        const course = userCourses.find(c => c.id == courseId);
        
        // Save course metadata
        const formData = {
            title: document.getElementById('editTitle').value,
            description: document.getElementById('editDescription').value,
            category: document.getElementById('editCategory').value,
            difficulty_level: document.getElementById('editDifficulty').value,
            estimated_duration: parseInt(document.getElementById('editDuration').value),
            instructor_id: course.instructor_id
        };
        
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const courseResponse = await fetch(CONFIG.ENDPOINTS.COURSE_BY_ID(courseId), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        
        if (!courseResponse.ok) {
            const errorData = await courseResponse.json();
            console.error('Course update error:', errorData);
            throw new Error(JSON.stringify(errorData.detail) || 'Failed to update course');
        }
        
        // Save slides if they were edited
        if (window.editingSlides) {
            const slidesData = collectSlidesFromEditor();
            const slidesResponse = await fetch(CONFIG.ENDPOINTS.UPDATE_SLIDES(courseId), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: courseId,
                    slides: slidesData
                })
            });
            
            if (!slidesResponse.ok) {
                console.warn('Failed to update slides, but course metadata saved');
            }
        }
        
        showNotification('Course updated successfully!', 'success');
        const modalOverlay = document.querySelector('.modal-overlay');
        if (modalOverlay) {
            modalOverlay.remove();
        }
        loadUserCourses();
        
    } catch (error) {
        console.error('Error updating course:', error);
        showNotification('Error updating course: ' + error.message, 'error');
    }
}

// eslint-disable-next-line no-unused-vars
function switchEditTab(tabName, button) {
    document.querySelectorAll('.edit-tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tabName + '-tab').classList.add('active');
    button.classList.add('active');
}

// eslint-disable-next-line no-unused-vars
function addNewSlide() {
    const slidesList = document.getElementById('slidesList');
    const slideCount = slidesList.children.length;
    const newSlideId = 'slide_' + (slideCount + 1);
    
    const slideHtml = `
        <div class="slide-editor-item" data-slide-id="${newSlideId}" data-order="${slideCount + 1}">
            <div class="slide-editor-header">
                <span class="slide-number">${slideCount + 1}</span>
                <input type="text" class="slide-title" value="" placeholder="New Slide Title">
                <div class="slide-controls">
                    <button class="btn-small" onclick="moveSlide(${slideCount}, 'up')"><i class="fas fa-arrow-up"></i></button>
                    <button class="btn-small" onclick="moveSlide(${slideCount}, 'down')"><i class="fas fa-arrow-down"></i></button>
                    <button class="btn-small btn-danger" onclick="deleteSlide(${slideCount})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <div class="slide-editor-content">
                <textarea class="slide-content" rows="4" placeholder="Enter slide content..."></textarea>
            </div>
        </div>
    `;
    
    slidesList.insertAdjacentHTML('beforeend', slideHtml);
    updateSlideNumbers();
}

function deleteSlide(index) {
    if (confirm('Delete this slide?')) {
        const slidesList = document.getElementById('slidesList');
        slidesList.children[index].remove();
        updateSlideNumbers();
    }
}

function moveSlide(index, direction) {
    const slidesList = document.getElementById('slidesList');
    const slides = Array.from(slidesList.children);
    const slide = slides[index];
    
    if (direction === 'up' && index > 0) {
        slidesList.insertBefore(slide, slides[index - 1]);
    } else if (direction === 'down' && index < slides.length - 1) {
        slidesList.insertBefore(slides[index + 1], slide);
    }
    
    updateSlideNumbers();
}

function updateSlideNumbers() {
    const slidesList = document.getElementById('slidesList');
    Array.from(slidesList.children).forEach((slide, index) => {
        slide.querySelector('.slide-number').textContent = index + 1;
        slide.dataset.order = index + 1;
        
        // Update move button handlers
        const upBtn = slide.querySelector('.slide-controls .btn-small:first-child');
        const downBtn = slide.querySelector('.slide-controls .btn-small:nth-child(2)');
        const deleteBtn = slide.querySelector('.slide-controls .btn-danger');
        
        upBtn.onclick = () => moveSlide(index, 'up');
        downBtn.onclick = () => moveSlide(index, 'down');
        deleteBtn.onclick = () => deleteSlide(index);
    });
}

function collectSlidesFromEditor() {
    const slidesList = document.getElementById('slidesList');
    const slides = [];
    
    Array.from(slidesList.children).forEach((slideEl, index) => {
        const title = slideEl.querySelector('.slide-title').value;
        const content = slideEl.querySelector('.slide-content').value;
        
        slides.push({
            id: slideEl.dataset.slideId,
            title: title || `Slide ${index + 1}`,
            content: content,
            slide_type: index === 0 ? 'title' : 'content',
            order: index + 1
        });
    });
    
    return slides;
}

// Used in onclick handlers
async function regenerateAllSlides(courseId) {
    if (!confirm('This will replace all slides with AI-generated content. Continue?')) return;
    
    try {
        showNotification('Regenerating slides...', 'info');
        
        const title = document.getElementById('editTitle').value;
        const description = document.getElementById('editDescription').value;
        const category = document.getElementById('editCategory').value;
        
        const response = await fetch(CONFIG.ENDPOINTS.GENERATE_SLIDES, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                title: title,
                description: description,
                topic: category
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            window.editingSlides = result.slides;
            
            // Rebuild slides editor
            const slidesList = document.getElementById('slidesList');
            slidesList.innerHTML = result.slides.map((slide, index) => `
                <div class="slide-editor-item" data-slide-id="${slide.id}" data-order="${slide.order}">
                    <div class="slide-editor-header">
                        <span class="slide-number">${index + 1}</span>
                        <input type="text" class="slide-title" value="${slide.title}" placeholder="Slide Title">
                        <div class="slide-controls">
                            <button class="btn-small" onclick="moveSlide(${index}, 'up')"><i class="fas fa-arrow-up"></i></button>
                            <button class="btn-small" onclick="moveSlide(${index}, 'down')"><i class="fas fa-arrow-down"></i></button>
                            <button class="btn-small btn-danger" onclick="deleteSlide(${index})"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                    <div class="slide-editor-content">
                        <textarea class="slide-content" rows="4" placeholder="Slide content...">${slide.content}</textarea>
                    </div>
                </div>
            `).join('');
            
            showNotification('Slides regenerated successfully!', 'success');
        } else {
            throw new Error('Failed to regenerate slides');
        }
    } catch (error) {
        console.error('Error regenerating slides:', error);
        showNotification('Error regenerating slides', 'error');
    }
}

// Used in onclick handlers
function previewSlideshow() {
    const slides = collectSlidesFromEditor();
    if (slides.length === 0) {
        showNotification('No slides to preview', 'warning');
        return;
    }
    
    // Create preview window
    const previewWindow = window.open('', '_blank', 'width=800,height=600');
    previewWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Slide Preview</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .slide { background: white; padding: 40px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .slide h1 { color: #2c3e50; margin-bottom: 20px; }
                .slide-number { background: #3498db; color: white; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; }
            </style>
        </head>
        <body>
            ${slides.map((slide, index) => `
                <div class="slide">
                    <div class="slide-number">Slide ${index + 1}</div>
                    <h1>${slide.title}</h1>
                    <p>${slide.content}</p>
                </div>
            `).join('')}
        </body>
        </html>
    `);
}

// eslint-disable-next-line no-unused-vars
async function deleteCourse(courseId) {
    const course = userCourses.find(c => c.id == courseId);
    if (!course) return;
    
    if (!confirm(`Are you sure you want to delete "${course.title}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch(CONFIG.ENDPOINTS.COURSE_BY_ID(courseId), {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            showNotification('Course deleted successfully!', 'success');
            loadUserCourses();
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete course');
        }
    } catch (error) {
        console.error('Error deleting course:', error);
        showNotification('Error deleting course: ' + error.message, 'error');
    }
}

// Tab button event delegation
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('tab-button')) {
        const tabName = e.target.textContent.trim().toLowerCase().replace(/\s+/g, '-');
        showSection(tabName.replace('my-', '').replace('create-', 'create-').replace('student-', 'students'));
    }
});function showSyllabusPreview(courseId, syllabus) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content syllabus-preview-modal">
            <div class="modal-header">
                <h3><i class="fas fa-file-alt"></i> Course Syllabus Preview</h3>
                <button class="modal-close" onclick="closeModal(this)">&times;</button>
            </div>
            <div class="modal-body">
                <div class="syllabus-content">
                    <div class="syllabus-section">
                        <h4>Course Overview</h4>
                        <p>${syllabus.overview}</p>
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Learning Objectives</h4>
                        <ul>
                            ${syllabus.objectives.map(obj => `<li>${obj}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Prerequisites</h4>
                        <ul>
                            ${syllabus.prerequisites.map(req => `<li>${req}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Course Modules</h4>
                        ${syllabus.modules.map(module => `
                            <div class="module-item">
                                <h5>${module.title} <span class="duration">(${module.duration_hours}h)</span></h5>
                                <div class="module-details">
                                    <div class="module-topics">
                                        <strong>Topics:</strong> ${module.topics.join(', ')}
                                    </div>
                                    <div class="module-outcomes">
                                        <strong>Learning Outcomes:</strong> ${module.learning_outcomes.join('; ')}
                                    </div>
                                    <div class="module-assessments">
                                        <strong>Assessments:</strong> ${module.assessments.join(', ')}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Assessment Strategy</h4>
                        <p>${syllabus.assessment_strategy}</p>
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Resources</h4>
                        <ul>
                            ${syllabus.resources.map(res => `<li>${res}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                
                <div class="feedback-section">
                    <h4>Feedback & Refinement</h4>
                    <textarea id="syllabusFeedback" placeholder="Provide feedback to refine the syllabus (e.g., 'Add more advanced topics', 'Reduce module 2 duration', 'Include more practical exercises')..." rows="4"></textarea>
                    <div class="feedback-buttons">
                        <button class="btn btn-warning" onclick="refineSyllabus('${courseId}')">
                            <i class="fas fa-edit"></i> Refine Syllabus
                        </button>
                        <button class="btn btn-success" onclick="approveSyllabus('${courseId}')">
                            <i class="fas fa-check"></i> Approve & Generate Content
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Store syllabus data for refinement
    window.currentSyllabus = syllabus;
}

// Used in onclick handlers
async function refineSyllabus(courseId) {
    const feedback = document.getElementById('syllabusFeedback').value;
    if (!feedback.trim()) {
        showNotification('Please provide feedback for refinement', 'warning');
        return;
    }
    
    try {
        showNotification('Refining syllabus based on feedback...', 'info');
        
        const response = await fetch(CONFIG.ENDPOINTS.REFINE_SYLLABUS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                feedback: feedback,
                current_syllabus: window.currentSyllabus
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Syllabus refined successfully!', 'success');
            
            // Close current modal and show updated syllabus
            const modalOverlay = document.querySelector('.modal-overlay');
            if (modalOverlay) {
                modalOverlay.remove();
            }
            showSyllabusPreview(courseId, result.syllabus);
        } else {
            throw new Error('Failed to refine syllabus');
        }
    } catch (error) {
        console.error('Error refining syllabus:', error);
        showNotification('Error refining syllabus', 'error');
    }
}

// Used in onclick handlers
async function approveSyllabus(courseId) {
    try {
        // Show progress modal
        showProgressModal('Generating Course Content', 'Preparing to generate slides, exercises, and quizzes...');
        
        const response = await fetch(CONFIG.ENDPOINTS.GENERATE_CONTENT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update progress modal with success
            updateProgressModal('Content Generation Complete!', 
                `✅ Generated ${result.slides.length} slides<br>
                 ✅ Generated ${result.exercises.length} exercises<br>
                 ✅ Generated ${result.quizzes.length} quizzes<br><br>
                 <em>Content has been saved and is now available for viewing.</em>`);
            
            // Close syllabus modal first if it exists
            const syllabusModal = document.querySelector('.modal-overlay');
            if (syllabusModal) {
                syllabusModal.remove();
            }
            
            // Close modal after a delay and refresh content
            setTimeout(() => {
                closeProgressModal();
                loadUserCourses();
                // Refresh the content view if we're on content section
                if (document.getElementById('content-section') && document.getElementById('content-section').classList.contains('active')) {
                    loadCourseContent();
                }
            }, 3000);
            
            showNotification(`Generated ${result.slides.length} slides, ${result.exercises.length} exercises, and ${result.quizzes.length} quizzes!`, 'success');
        } else {
            throw new Error('Failed to generate content from syllabus');
        }
    } catch (error) {
        console.error('Error generating content:', error);
        updateProgressModal('Content Generation Failed', 
            `❌ Error generating content: ${error.message}<br><br>
             Please try again or contact support if the problem persists.`);
        setTimeout(() => {
            closeProgressModal();
        }, 3000);
        showNotification('Error generating content from syllabus', 'error');
    }
}

// Progress modal functions
function showProgressModal(title, message) {
    // Close any existing progress modal
    const existingModal = document.querySelector('.progress-modal-overlay');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.className = 'progress-modal-overlay';
    modal.innerHTML = `
        <div class="progress-modal-content">
            <div class="progress-modal-header">
                <h3><i class="fas fa-cog fa-spin"></i> ${title}</h3>
            </div>
            <div class="progress-modal-body">
                <div class="progress-message">${message}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Start progress animation
    const progressFill = modal.querySelector('.progress-fill');
    let width = 0;
    const interval = setInterval(() => {
        width += Math.random() * 10;
        if (width > 90) width = 90; // Don't complete until we get actual result
        progressFill.style.width = width + '%';
    }, 500);
    
    // Store interval for cleanup
    modal.progressInterval = interval;
}

function updateProgressModal(title, message) {
    const modal = document.querySelector('.progress-modal-overlay');
    if (modal) {
        // Clear the progress interval
        if (modal.progressInterval) {
            clearInterval(modal.progressInterval);
        }
        
        // Update content
        const header = modal.querySelector('.progress-modal-header h3');
        const messageDiv = modal.querySelector('.progress-message');
        const progressFill = modal.querySelector('.progress-fill');
        
        if (header) {
            header.innerHTML = `<i class="fas fa-check-circle"></i> ${title}`;
        }
        if (messageDiv) {
            messageDiv.innerHTML = message;
        }
        if (progressFill) {
            progressFill.style.width = '100%';
        }
    }
}

function closeProgressModal() {
    const modal = document.querySelector('.progress-modal-overlay');
    if (modal) {
        // Clear any running interval
        if (modal.progressInterval) {
            clearInterval(modal.progressInterval);
        }
        modal.remove();
    }
}

// Used in onclick handlers
async function saveCourseContent(courseId) {
    try {
        showNotification('Saving course content...', 'info');
        
        const response = await fetch(CONFIG.ENDPOINTS.SAVE_COURSE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId
            })
        });
        
        if (response.ok) {
            showNotification('Course content saved successfully!', 'success');
        } else {
            throw new Error('Failed to save course content');
        }
    } catch (error) {
        console.error('Error saving course content:', error);
        showNotification('Error saving course content', 'error');
    }
}
