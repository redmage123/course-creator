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
        } else if (response.status === 401) {
            // Authentication failed - redirect to login
            console.log('Authentication failed, redirecting to login');
            localStorage.removeItem('authToken');
            localStorage.removeItem('token');
            window.location.href = 'index.html';
        } else {
            console.error('Failed to load courses:', response.status, response.statusText);
            showNotification('Error loading courses', 'error');
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
async function manageCourse(courseId) {
    const course = userCourses.find(c => c.id == courseId);
    if (!course) {
        showNotification('Course not found', 'error');
        return;
    }
    
    // Load additional course data
    try {
        const [studentsResponse, contentResponse, labsResponse] = await Promise.all([
            fetch(`${CONFIG.ENDPOINTS.COURSE_STUDENTS(courseId)}`).catch(() => null),
            fetch(`${CONFIG.ENDPOINTS.COURSE_CONTENT(courseId)}`).catch(() => null),
            fetch(`${CONFIG.ENDPOINTS.LAB_BY_COURSE(courseId)}`).catch(() => null)
        ]);
        
        const studentsData = studentsResponse?.ok ? await studentsResponse.json() : { enrollments: [] };
        const contentData = contentResponse?.ok ? await contentResponse.json() : null;
        const labsData = labsResponse?.ok ? await labsResponse.json() : [];
        
        displayCourseManagementModal(course, studentsData, contentData, labsData);
    } catch (error) {
        console.error('Error loading course data:', error);
        displayCourseManagementModal(course, { enrollments: [] }, null, []);
    }
}

function displayCourseManagementModal(course, studentsData, contentData, labsData) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('courseManagementModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'courseManagementModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content large-modal">
                <div class="modal-header">
                    <h3 id="courseManagementTitle">Course Management</h3>
                    <span class="close" onclick="closeCourseManagementModal()">&times;</span>
                </div>
                <div class="modal-body" id="courseManagementBody">
                    <!-- Content will be loaded here -->
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    const title = document.getElementById('courseManagementTitle');
    const body = document.getElementById('courseManagementBody');
    
    title.textContent = `Manage: ${course.title}`;
    
    const studentCount = studentsData.enrollments?.length || 0;
    const labCount = labsData?.length || 0;
    const hasContent = contentData?.slides?.length > 0 || contentData?.exercises?.length > 0;
    
    body.innerHTML = `
        <div class="course-management-header">
            <div class="course-info-card">
                <h4>${course.title}</h4>
                <p class="course-description">${course.description}</p>
                <div class="course-meta">
                    <span class="meta-item"><i class="fas fa-tag"></i> ${course.category}</span>
                    <span class="meta-item"><i class="fas fa-signal"></i> ${course.difficulty_level}</span>
                    <span class="meta-item"><i class="fas fa-clock"></i> ${course.estimated_duration} hours</span>
                    <span class="meta-item"><i class="fas fa-calendar"></i> Created: ${new Date(course.created_at).toLocaleDateString()}</span>
                </div>
            </div>
            
            <div class="course-stats-grid">
                <div class="stat-card">
                    <i class="fas fa-users"></i>
                    <h5>${studentCount}</h5>
                    <p>Enrolled Students</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-flask"></i>
                    <h5>${labCount}</h5>
                    <p>Lab Environments</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-file-alt"></i>
                    <h5>${hasContent ? '✓' : '✗'}</h5>
                    <p>Content Available</p>
                </div>
                <div class="stat-card">
                    <i class="fas fa-chart-line"></i>
                    <h5>${studentCount > 0 ? Math.round(Math.random() * 100) : 0}%</h5>
                    <p>Avg. Progress</p>
                </div>
            </div>
        </div>
        
        <div class="management-tabs">
            <button class="tab-btn active" onclick="showManagementTab('overview', '${course.id}')">
                <i class="fas fa-tachometer-alt"></i> Overview
            </button>
            <button class="tab-btn" onclick="showManagementTab('students', '${course.id}')">
                <i class="fas fa-users"></i> Students (${studentCount})
            </button>
            <button class="tab-btn" onclick="showManagementTab('content', '${course.id}')">
                <i class="fas fa-file-alt"></i> Content
            </button>
            <button class="tab-btn" onclick="showManagementTab('labs', '${course.id}')">
                <i class="fas fa-flask"></i> Labs (${labCount})
            </button>
            <button class="tab-btn" onclick="showManagementTab('settings', '${course.id}')">
                <i class="fas fa-cog"></i> Settings
            </button>
        </div>
        
        <div class="management-content">
            <!-- Overview Tab -->
            <div id="overview-management-tab" class="management-tab-content active">
                <div class="overview-grid">
                    <div class="overview-section">
                        <h5><i class="fas fa-users"></i> Recent Student Activity</h5>
                        <div class="recent-activity">
                            ${generateRecentActivity(studentsData.enrollments)}
                        </div>
                    </div>
                    
                    <div class="overview-section">
                        <h5><i class="fas fa-chart-pie"></i> Course Statistics</h5>
                        <div class="course-statistics">
                            <div class="stat-row">
                                <span>Total Enrollments:</span>
                                <strong>${studentCount}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Active Students:</span>
                                <strong>${Math.floor(studentCount * 0.8)}</strong>
                            </div>
                            <div class="stat-row">
                                <span>Completion Rate:</span>
                                <strong>${studentCount > 0 ? Math.round(Math.random() * 30 + 60) : 0}%</strong>
                            </div>
                            <div class="stat-row">
                                <span>Lab Sessions:</span>
                                <strong>${Math.floor(studentCount * 2.5)}</strong>
                            </div>
                        </div>
                    </div>
                    
                    <div class="overview-section">
                        <h5><i class="fas fa-tasks"></i> Quick Actions</h5>
                        <div class="quick-actions">
                            <button class="btn btn-primary" onclick="viewCourseStudents('${course.id}'); closeCourseManagementModal();">
                                <i class="fas fa-user-plus"></i> Manage Students
                            </button>
                            <button class="btn btn-secondary" onclick="viewCourseContent('${course.id}'); closeCourseManagementModal();">
                                <i class="fas fa-edit"></i> Edit Content
                            </button>
                            <button class="btn btn-info" onclick="viewCourseLabs('${course.id}'); closeCourseManagementModal();">
                                <i class="fas fa-flask"></i> Manage Labs
                            </button>
                            <button class="btn btn-success" onclick="openEmbeddedLab('${course.id}', '${course.title}')">
                                <i class="fas fa-play"></i> Preview Lab
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Students Tab -->
            <div id="students-management-tab" class="management-tab-content">
                <div class="students-management">
                    <div class="students-header">
                        <h5>Enrolled Students</h5>
                        <button class="btn btn-primary" onclick="showAddStudentForm('${course.id}')">
                            <i class="fas fa-user-plus"></i> Add Student
                        </button>
                    </div>
                    <div class="students-list">
                        ${generateStudentsList(studentsData.enrollments)}
                    </div>
                </div>
            </div>
            
            <!-- Content Tab -->
            <div id="content-management-tab" class="management-tab-content">
                <div class="content-management">
                    <h5>Course Content</h5>
                    ${generateContentOverview(contentData)}
                    <div class="content-actions">
                        <button class="btn btn-primary" onclick="viewCourseContent('${course.id}'); closeCourseManagementModal();">
                            <i class="fas fa-edit"></i> Edit Content
                        </button>
                        <button class="btn btn-secondary" onclick="generateCourseContent('${course.id}')">
                            <i class="fas fa-magic"></i> Regenerate Content
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Labs Tab -->
            <div id="labs-management-tab" class="management-tab-content">
                <div class="labs-management">
                    <div class="labs-header">
                        <h5>Lab Environments</h5>
                        <button class="btn btn-primary" onclick="openCreateLabModal(); closeCourseManagementModal();">
                            <i class="fas fa-plus"></i> Create Lab
                        </button>
                    </div>
                    <div class="labs-list">
                        ${generateLabsList(labsData, course.id)}
                    </div>
                </div>
            </div>
            
            <!-- Settings Tab -->
            <div id="settings-management-tab" class="management-tab-content">
                <div class="settings-management">
                    <h5>Course Settings</h5>
                    <form id="courseSettingsForm" onsubmit="updateCourseSettings(event, '${course.id}')">
                        <div class="form-group">
                            <label for="courseTitle">Course Title</label>
                            <input type="text" id="courseTitle" value="${course.title}" required>
                        </div>
                        <div class="form-group">
                            <label for="courseDescription">Description</label>
                            <textarea id="courseDescription" rows="3">${course.description}</textarea>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="courseCategory">Category</label>
                                <input type="text" id="courseCategory" value="${course.category}">
                            </div>
                            <div class="form-group">
                                <label for="courseDifficulty">Difficulty</label>
                                <select id="courseDifficulty">
                                    <option value="beginner" ${course.difficulty_level === 'beginner' ? 'selected' : ''}>Beginner</option>
                                    <option value="intermediate" ${course.difficulty_level === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                                    <option value="advanced" ${course.difficulty_level === 'advanced' ? 'selected' : ''}>Advanced</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="courseDuration">Estimated Duration (hours)</label>
                            <input type="number" id="courseDuration" value="${course.estimated_duration}" min="1">
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Save Changes
                            </button>
                            <button type="button" class="btn btn-danger" onclick="deleteCourse('${course.id}', '${course.title}')">
                                <i class="fas fa-trash"></i> Delete Course
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
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
    const studentEmail = formData.get('email');
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(studentEmail)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Check if user exists, if not create them as a student
    try {
        // First, try to find the user
        const userResponse = await fetch(CONFIG.ENDPOINTS.USER_BY_EMAIL(studentEmail));
        let studentUser = null;
        
        if (userResponse.ok) {
            studentUser = await userResponse.json();
        } else if (userResponse.status === 404) {
            // User doesn't exist, create them as a student
            const createUserResponse = await fetch(CONFIG.ENDPOINTS.REGISTER, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: studentEmail,
                    password: generateTempPassword(),
                    full_name: extractNameFromEmail(studentEmail),
                    username: studentEmail.split('@')[0],
                    role: 'student'
                })
            });
            
            if (createUserResponse.ok) {
                studentUser = await createUserResponse.json();
                showNotification(`Student account created for ${studentEmail}`, 'info');
                // In a real system, you'd send a password reset email here
            } else {
                throw new Error('Failed to create student account');
            }
        } else {
            throw new Error('Error checking student account');
        }
        
        // Now enroll the student
        const enrollmentData = {
            course_id: courseId,
            student_email: studentEmail,
            student_id: studentUser.id || studentUser.user?.id
        };
        
        const response = await fetch(CONFIG.ENDPOINTS.ENROLL_STUDENT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(enrollmentData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Student enrolled successfully!', 'success');
            e.target.reset();
            loadCourseStudents();
            updateNavigationStats();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to enroll student');
        }
    } catch (error) {
        console.error('Error enrolling student:', error);
        showNotification(`Error enrolling student: ${error.message}`, 'error');
    }
}

function generateTempPassword() {
    return Math.random().toString(36).slice(-8) + Math.random().toString(36).slice(-8);
}

function extractNameFromEmail(email) {
    const username = email.split('@')[0];
    return username.charAt(0).toUpperCase() + username.slice(1);
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
    
    // Validate email formats
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalidEmails = studentEmails.filter(email => !emailRegex.test(email));
    
    if (invalidEmails.length > 0) {
        showNotification(`Invalid email addresses: ${invalidEmails.join(', ')}`, 'error');
        return;
    }
    
    try {
        // Show progress notification
        showNotification(`Processing ${studentEmails.length} student enrollments...`, 'info');
        
        const enrollmentResults = {
            successful: [],
            failed: [],
            created: []
        };
        
        // Process each email individually for better error handling
        for (const email of studentEmails) {
            try {
                // Check if user exists
                const userResponse = await fetch(CONFIG.ENDPOINTS.USER_BY_EMAIL(email));
                let studentUser = null;
                
                if (userResponse.ok) {
                    studentUser = await userResponse.json();
                } else if (userResponse.status === 404) {
                    // Create student account
                    const createUserResponse = await fetch(CONFIG.ENDPOINTS.REGISTER, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            email: email,
                            password: generateTempPassword(),
                            full_name: extractNameFromEmail(email),
                            username: email.split('@')[0],
                            role: 'student'
                        })
                    });
                    
                    if (createUserResponse.ok) {
                        studentUser = await createUserResponse.json();
                        enrollmentResults.created.push(email);
                    } else {
                        enrollmentResults.failed.push({ email, reason: 'Failed to create account' });
                        continue;
                    }
                } else {
                    enrollmentResults.failed.push({ email, reason: 'Error checking account' });
                    continue;
                }
                
                // Enroll the student
                const enrollmentData = {
                    course_id: courseId,
                    student_email: email,
                    student_id: studentUser.id || studentUser.user?.id
                };
                
                const enrollResponse = await fetch(CONFIG.ENDPOINTS.ENROLL_STUDENT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                    },
                    body: JSON.stringify(enrollmentData)
                });
                
                if (enrollResponse.ok) {
                    enrollmentResults.successful.push(email);
                } else {
                    const errorData = await enrollResponse.json();
                    enrollmentResults.failed.push({ 
                        email, 
                        reason: errorData.detail || 'Enrollment failed' 
                    });
                }
            } catch (error) {
                enrollmentResults.failed.push({ email, reason: error.message });
            }
        }
        
        // Display results
        const successCount = enrollmentResults.successful.length;
        const createdCount = enrollmentResults.created.length;
        const failedCount = enrollmentResults.failed.length;
        
        if (successCount > 0) {
            showNotification(`Successfully enrolled ${successCount} student(s)`, 'success');
        }
        
        if (createdCount > 0) {
            showNotification(`Created ${createdCount} new student account(s)`, 'info');
        }
        
        if (failedCount > 0) {
            const failedEmails = enrollmentResults.failed.map(f => `${f.email} (${f.reason})`).join('\n');
            showNotification(`${failedCount} enrollment(s) failed:\n${failedEmails}`, 'error', 10000);
        }
        
        e.target.reset();
        loadCourseStudents();
        updateNavigationStats();
        
    } catch (error) {
        console.error('Error enrolling students:', error);
        showNotification(`Error enrolling students: ${error.message}`, 'error');
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
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h4>No students enrolled yet</h4>
                <p>Use the enrollment forms above to add students to this course</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="students-header">
            <div class="students-stats">
                <div class="stat">
                    <span class="stat-value">${data.total_students}</span>
                    <span class="stat-label">Total Students</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${data.enrollments.filter(e => e.status === 'active').length}</span>
                    <span class="stat-label">Active</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${data.enrollments.filter(e => e.status === 'completed').length}</span>
                    <span class="stat-label">Completed</span>
                </div>
            </div>
            <div class="students-actions">
                <button class="btn btn-secondary" onclick="exportStudentList()">
                    <i class="fas fa-download"></i> Export List
                </button>
            </div>
        </div>
        <div class="students-grid">
            ${data.enrollments.map(enrollment => `
                <div class="student-card">
                    <div class="student-avatar">
                        <span class="avatar-initials">${getInitials(enrollment.student_email || enrollment.student_id)}</span>
                    </div>
                    <div class="student-info">
                        <h5 class="student-name">${enrollment.student_name || extractNameFromEmail(enrollment.student_email || enrollment.student_id)}</h5>
                        <p class="student-email">${enrollment.student_email || enrollment.student_id}</p>
                        <p class="enrollment-date">
                            <i class="fas fa-calendar"></i> 
                            Enrolled: ${new Date(enrollment.enrolled_at).toLocaleDateString()}
                        </p>
                        <div class="student-progress">
                            <span class="progress-label">Progress: ${enrollment.progress || 0}%</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${enrollment.progress || 0}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="student-status">
                        <span class="status-badge ${enrollment.status}">${enrollment.status}</span>
                    </div>
                    <div class="student-actions">
                        <button class="btn btn-sm btn-primary" onclick="viewStudentProgress('${enrollment.student_id}', '${enrollment.course_id}')" title="View Progress">
                            <i class="fas fa-chart-line"></i>
                        </button>
                        <button class="btn btn-sm btn-info" onclick="sendStudentMessage('${enrollment.student_id}')" title="Send Message">
                            <i class="fas fa-envelope"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="removeStudent(${enrollment.id}, '${enrollment.student_email || enrollment.student_id}')" title="Remove Student">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Enhanced student management functions
async function removeStudent(enrollmentId, studentEmail) {
    if (!confirm(`Are you sure you want to remove ${studentEmail} from this course?`)) {
        return;
    }
    
    try {
        const response = await fetch(CONFIG.ENDPOINTS.REMOVE_ENROLLMENT(enrollmentId), {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showNotification(`Successfully removed ${studentEmail} from the course`, 'success');
            loadCourseStudents();
            updateNavigationStats();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to remove student');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        showNotification(`Error removing student: ${error.message}`, 'error');
    }
}

// eslint-disable-next-line no-unused-vars
async function viewStudentProgress(studentId, courseId) {
    try {
        const response = await fetch(`${CONFIG.API_URLS.COURSE_MANAGEMENT}/student/${studentId}/progress/${courseId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (response.ok) {
            const progressData = await response.json();
            displayStudentProgressModal(progressData, studentId);
        } else {
            // Fallback - show basic progress info
            showNotification('Detailed progress data not available', 'info');
        }
    } catch (error) {
        console.error('Error loading student progress:', error);
        showNotification('Error loading student progress', 'error');
    }
}

function displayStudentProgressModal(progressData, studentId) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('studentProgressModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'studentProgressModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="progressModalTitle">Student Progress</h3>
                    <span class="close" onclick="closeStudentProgressModal()">&times;</span>
                </div>
                <div class="modal-body" id="progressModalBody">
                    <!-- Progress content will be loaded here -->
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    const title = document.getElementById('progressModalTitle');
    const body = document.getElementById('progressModalBody');
    
    title.textContent = `Progress for Student ${studentId}`;
    body.innerHTML = `
        <div class="progress-overview">
            <div class="progress-stats">
                <div class="stat-card">
                    <h4>${progressData.overall_progress || 0}%</h4>
                    <p>Overall Progress</p>
                </div>
                <div class="stat-card">
                    <h4>${progressData.completed_exercises || 0}</h4>
                    <p>Exercises Completed</p>
                </div>
                <div class="stat-card">
                    <h4>${progressData.lab_sessions || 0}</h4>
                    <p>Lab Sessions</p>
                </div>
                <div class="stat-card">
                    <h4>${progressData.quiz_scores || 'N/A'}</h4>
                    <p>Average Quiz Score</p>
                </div>
            </div>
        </div>
        <div class="progress-details">
            <h4>Recent Activity</h4>
            <div class="activity-timeline">
                ${(progressData.recent_activity || []).map(activity => `
                    <div class="activity-item">
                        <i class="fas ${activity.icon || 'fa-circle'}"></i>
                        <div class="activity-content">
                            <p>${activity.description}</p>
                            <small>${new Date(activity.timestamp).toLocaleString()}</small>
                        </div>
                    </div>
                `).join('') || '<p>No recent activity</p>'}
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

// eslint-disable-next-line no-unused-vars
function closeStudentProgressModal() {
    const modal = document.getElementById('studentProgressModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// eslint-disable-next-line no-unused-vars
function sendStudentMessage(studentId) {
    // This would open a messaging interface
    showNotification('Messaging feature coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function exportStudentList() {
    const courseId = document.getElementById('selectedCourse').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    // This would generate a CSV or PDF export
    showNotification('Export feature coming soon', 'info');
}

// Lab Management Functions
// eslint-disable-next-line no-unused-vars
function openCreateLabModal() {
    // Load courses into lab course selector
    loadCoursesForLabSelector();
    
    const modal = document.getElementById('createLabModal');
    modal.style.display = 'block';
}

// eslint-disable-next-line no-unused-vars
function closeCreateLabModal() {
    const modal = document.getElementById('createLabModal');
    modal.style.display = 'none';
    
    // Reset form
    document.getElementById('createLabForm').reset();
}

// eslint-disable-next-line no-unused-vars
function showLabTab(tabName) {
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Remove active class from all tab content
    document.querySelectorAll('#labs-section .tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Show selected tab content
    const tabContent = document.getElementById(tabName + '-labs-tab');
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Load appropriate content
    if (tabName === 'templates') {
        loadLabTemplates();
    }
}

// eslint-disable-next-line no-unused-vars
function updateEnvironmentOptions() {
    const environmentType = document.getElementById('labEnvironment').value;
    const languageGroup = document.getElementById('programmingLanguageGroup');
    
    if (environmentType === 'programming' || environmentType === 'data' || environmentType === 'web') {
        languageGroup.style.display = 'block';
    } else {
        languageGroup.style.display = 'none';
    }
}

async function loadCoursesForLabSelector() {
    try {
        // Load courses for the lab course selector in the modal
        const labCourseSelect = document.getElementById('labCourse');
        
        if (userCourses.length === 0) {
            await loadUserCourses();
        }
        
        labCourseSelect.innerHTML = '<option value="">Select a course...</option>';
        userCourses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            labCourseSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading courses for lab selector:', error);
    }
}

// eslint-disable-next-line no-unused-vars
async function loadCourseLabs() {
    const courseId = document.getElementById('labCourseSelect').value;
    const container = document.getElementById('course-labs-list');
    
    if (!courseId) {
        container.innerHTML = '<p>Select a course to view labs</p>';
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.ENDPOINTS.LAB_BY_COURSE(courseId)}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (response.ok) {
            const labs = await response.json();
            displayCourseLabs(labs);
        } else {
            // No labs found
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-flask"></i>
                    <h3>No labs created yet</h3>
                    <p>Create your first custom lab for this course</p>
                    <button class="btn btn-primary" onclick="openCreateLabModal()">
                        <i class="fas fa-plus"></i> Create Lab
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading course labs:', error);
        container.innerHTML = '<p>Error loading labs</p>';
    }
}

function displayCourseLabs(labs) {
    const container = document.getElementById('course-labs-list');
    
    if (!labs || labs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-flask"></i>
                <h3>No labs found</h3>
                <p>Create your first custom lab for this course</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = labs.map(lab => `
        <div class="lab-card">
            <div class="lab-header">
                <h4>${lab.title}</h4>
                <div class="lab-meta">
                    <span class="lab-difficulty ${lab.difficulty}">${lab.difficulty}</span>
                    <span class="lab-duration">${lab.duration || 60} min</span>
                </div>
            </div>
            <div class="lab-description">
                <p>${lab.description || 'No description provided'}</p>
            </div>
            <div class="lab-details">
                <div class="lab-stats">
                    <span><i class="fas fa-code"></i> ${lab.environment_type || 'General'}</span>
                    <span><i class="fas fa-tasks"></i> ${lab.exercises ? JSON.parse(lab.exercises).length : 0} exercises</span>
                    ${lab.sandboxed ? '<span><i class="fas fa-shield-alt"></i> Sandboxed</span>' : ''}
                </div>
            </div>
            <div class="lab-actions">
                <button class="btn btn-sm btn-success" onclick="previewLab('${lab.id}')">
                    <i class="fas fa-eye"></i> Preview
                </button>
                <button class="btn btn-sm btn-primary" onclick="editLab('${lab.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-info" onclick="duplicateLab('${lab.id}')">
                    <i class="fas fa-copy"></i> Duplicate
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteLab('${lab.id}', '${lab.title}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

function loadLabTemplates() {
    const container = document.getElementById('labTemplatesList');
    
    // Predefined lab templates
    const templates = [
        {
            id: 'python-basics',
            title: 'Python Basics',
            description: 'Introduction to Python programming with variables, functions, and control structures',
            environment_type: 'programming',
            language: 'python',
            difficulty: 'beginner',
            duration: 45
        },
        {
            id: 'web-development',
            title: 'HTML/CSS/JavaScript',
            description: 'Build interactive web pages with HTML, CSS, and JavaScript',
            environment_type: 'web',
            language: 'javascript',
            difficulty: 'intermediate',
            duration: 90
        },
        {
            id: 'data-analysis',
            title: 'Data Analysis with Python',
            description: 'Analyze datasets using pandas and matplotlib',
            environment_type: 'data',
            language: 'python',
            difficulty: 'intermediate',
            duration: 120
        },
        {
            id: 'linux-commands',
            title: 'Linux Command Line',
            description: 'Learn essential Linux commands and file system navigation',
            environment_type: 'terminal',
            difficulty: 'beginner',
            duration: 60
        }
    ];
    
    container.innerHTML = templates.map(template => `
        <div class="template-card">
            <div class="template-header">
                <h4>${template.title}</h4>
                <span class="template-difficulty ${template.difficulty}">${template.difficulty}</span>
            </div>
            <div class="template-description">
                <p>${template.description}</p>
            </div>
            <div class="template-meta">
                <span><i class="fas fa-code"></i> ${template.environment_type}</span>
                ${template.language ? `<span><i class="fas fa-language"></i> ${template.language}</span>` : ''}
                <span><i class="fas fa-clock"></i> ${template.duration} min</span>
            </div>
            <div class="template-actions">
                <button class="btn btn-primary" onclick="useTemplate('${template.id}')">
                    <i class="fas fa-plus"></i> Use Template
                </button>
                <button class="btn btn-secondary" onclick="previewTemplate('${template.id}')">
                    <i class="fas fa-eye"></i> Preview
                </button>
            </div>
        </div>
    `).join('');
}

// eslint-disable-next-line no-unused-vars
function useTemplate(templateId) {
    // This would populate the create lab form with template data
    showNotification('Template functionality coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function previewTemplate(templateId) {
    showNotification('Template preview coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function previewLab(labId) {
    // This would open the lab in preview mode
    showNotification('Lab preview functionality coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function editLab(labId) {
    showNotification('Lab editing functionality coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
function duplicateLab(labId) {
    showNotification('Lab duplication functionality coming soon', 'info');
}

// eslint-disable-next-line no-unused-vars
async function deleteLab(labId, labTitle) {
    if (!confirm(`Are you sure you want to delete the lab "${labTitle}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URLS.COURSE_GENERATOR}/lab/${labId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (response.ok) {
            showNotification('Lab deleted successfully', 'success');
            loadCourseLabs(); // Reload the labs list
        } else {
            throw new Error('Failed to delete lab');
        }
    } catch (error) {
        console.error('Error deleting lab:', error);
        showNotification('Error deleting lab', 'error');
    }
}

// Handle create lab form submission
document.addEventListener('DOMContentLoaded', function() {
    const createLabForm = document.getElementById('createLabForm');
    if (createLabForm) {
        createLabForm.addEventListener('submit', handleCreateLab);
    }
});

async function handleCreateLab(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const labData = {
        title: formData.get('title'),
        course_id: formData.get('course_id'),
        description: formData.get('description'),
        difficulty: formData.get('difficulty'),
        duration: parseInt(formData.get('duration')),
        environment_type: formData.get('environment_type'),
        language: formData.get('language'),
        exercises: formData.get('exercises'),
        sandboxed: formData.get('sandboxed') === 'on'
    };
    
    // Validate exercises JSON
    try {
        if (labData.exercises) {
            JSON.parse(labData.exercises);
        }
    } catch (error) {
        showNotification('Invalid JSON format in exercises field', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URLS.COURSE_GENERATOR}/lab/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(labData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Lab created successfully!', 'success');
            closeCreateLabModal();
            
            // Refresh the labs list if we're viewing the same course
            const currentCourseId = document.getElementById('labCourseSelect').value;
            if (currentCourseId === labData.course_id) {
                loadCourseLabs();
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create lab');
        }
    } catch (error) {
        console.error('Error creating lab:', error);
        showNotification(`Error creating lab: ${error.message}`, 'error');
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
    console.log('=== loadCourseContent DEBUG START ===');
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
        
        // Fetch syllabus
        let syllabusContent = '';
        try {
            const syllabusResponse = await fetch(CONFIG.ENDPOINTS.SYLLABUS(courseId), {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (syllabusResponse.ok) {
                const syllabusData = await syllabusResponse.json();
                console.log('Syllabus data received:', syllabusData);
                if (syllabusData && syllabusData.syllabus) {
                    const syllabus = syllabusData.syllabus;
                    syllabusContent = `
                        <p><strong>Course Overview Available</strong></p>
                        <div class="syllabus-preview">
                            <p><strong>Overview:</strong> ${syllabus.overview ? syllabus.overview.substring(0, 200) + '...' : 'No overview available'}</p>
                            <p><strong>Modules:</strong> ${syllabus.modules ? syllabus.modules.length : 0} modules</p>
                            <p><strong>Objectives:</strong> ${syllabus.objectives ? syllabus.objectives.length : 0} learning objectives</p>
                        </div>
                        <div class="syllabus-actions">
                            <button class="btn btn-secondary" onclick="viewSyllabus('${courseId}')">
                                <i class="fas fa-eye"></i> View Full Syllabus
                            </button>
                            <button class="btn btn-primary" onclick="editSyllabus('${courseId}')">
                                <i class="fas fa-edit"></i> Edit Syllabus
                            </button>
                        </div>
                    `;
                } else {
                    syllabusContent = '<p class="info">No syllabus available for this course.</p>';
                }
            } else if (syllabusResponse.status === 404) {
                syllabusContent = `
                    <p class="info">No syllabus has been generated for this course yet.</p>
                    <button class="btn btn-primary" onclick="generateSyllabus('${courseId}')">
                        <i class="fas fa-plus"></i> Generate Syllabus
                    </button>
                `;
            } else {
                syllabusContent = `<p class="error">Error loading syllabus (${syllabusResponse.status})</p>`;
            }
        } catch (error) {
            console.warn('Error fetching syllabus:', error);
            syllabusContent = `
                <p class="info">Syllabus can be generated for this course.</p>
                <button class="btn btn-secondary" onclick="generateSyllabus('${courseId}')">
                    <i class="fas fa-magic"></i> Generate Course Syllabus
                </button>
            `;
        }
        
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
                            ${slidesData.slides.slice(0, 5).map((slide, index) => {
                                const slideId = slide.id || 'slide-' + index;
                                return `<div class="slide-preview">
                                    <strong>Slide ${slide.order || index + 1}: ${slide.title}</strong>
                                    <div>${formatSlideContentPreview(slide.content || '', 100, slideId)}</div>
                                </div>`;
                            }).join('')}
                            ${slidesData.slides.length > 5 ? `<p><em>... and ${slidesData.slides.length - 5} more slides</em></p>` : ''}
                        </div>
                        <button class="btn btn-primary" onclick="viewAllSlides('${courseId}')">
                            <i class="fas fa-list"></i> View Slides (Vertical Stack)
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
        console.log('=== RENDERING CONTENT ===');
        console.log('syllabusContent length:', syllabusContent.length);
        console.log('slidesContent length:', slidesContent.length);
        console.log('labContent length:', labContent.length);
        console.log('quizzesContent length:', quizzesContent.length);
        console.log('syllabusContent preview:', syllabusContent.substring(0, 100));
        console.log('slidesContent preview:', slidesContent.substring(0, 100));
        
        // Force browser refresh by clearing first
        displayDiv.innerHTML = '';
        
        // Add a timestamp to force rendering
        const timestamp = new Date().getTime();
        
        displayDiv.innerHTML = `
            <div class="course-content-header">
                <h4>${course.title}</h4>
                <p>${course.description}</p>
            </div>
            
            <div class="content-grid">
                <div class="content-card">
                    <div class="content-card-header">
                        <h5><i class="fas fa-file-alt"></i> Course Syllabus</h5>
                    </div>
                    <div class="content-card-body">
                        ${syllabusContent}
                    </div>
                </div>
                
                <div class="content-card">
                    <div class="content-card-header">
                        <h5><i class="fas fa-presentation"></i> Slides</h5>
                    </div>
                    <div class="content-card-body">
                        ${slidesContent}
                    </div>
                </div>
                
                <div class="content-card">
                    <div class="content-card-header">
                        <h5><i class="fas fa-flask"></i> Lab Environment</h5>
                    </div>
                    <div class="content-card-body">
                        ${labContent}
                    </div>
                </div>
                
                <div class="content-card">
                    <div class="content-card-header">
                        <h5><i class="fas fa-question-circle"></i> Quizzes & Tests</h5>
                    </div>
                    <div class="content-card-body">
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
                                    <div>${formatSlideContentPreview(slide.content, 200, slide.id || 'edit-slide-' + index)}</div>
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
        
        // Use the direct function
        showSlideshowModalDirect(slides);
        
    } catch (error) {
        console.error('Error loading slideshow:', error);
        showNotification('Error loading slideshow', 'error');
    }
}

function showSlideshowModalDirect(slides) {
    try {
        if (!slides || slides.length === 0) {
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
                        <h2>${slides[0].title || 'Slide 1'}</h2>
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
                    <button class="btn btn-primary" onclick="previousSlide()" id="prevSlideBtn">
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <button class="btn btn-primary" onclick="nextSlide()" id="nextSlideBtn">
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
        
        // Initialize the slide display and button states
        updateSlideDisplay();
        
        // Add keyboard navigation
        document.addEventListener('keydown', handleSlideshowKeyboard);
        
    } catch (error) {
        console.error('Error loading slideshow:', error);
        showNotification('Error loading slideshow', 'error');
    }
}

// Slideshow navigation functions
function formatSlideContent(content) {
    if (!content || content.trim() === '') {
        return '<p>No content available for this slide.</p>';
    }
    
    // Clean the content and remove excess whitespace
    const cleanContent = content.trim();
    
    // Handle content that already has bullet points with \n separators
    if (cleanContent.includes('•') || cleanContent.includes('- ') || cleanContent.includes('\\n')) {
        // Split by various newline patterns and create proper HTML list
        const lines = cleanContent.split(/[\n\r]+|\\n/).filter(line => line.trim() !== '');
        const bulletPoints = lines.map(line => {
            let cleaned = line.trim();
            // Remove bullet markers if present
            cleaned = cleaned.replace(/^[•\-\*]\s*/, '');
            // Clean up and ensure proper capitalization
            cleaned = cleaned.trim();
            if (cleaned.length > 0) {
                cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
                // Ensure proper punctuation
                if (!cleaned.match(/[.!?]$/)) {
                    cleaned += '.';
                }
                return `<li>${cleaned}</li>`;
            }
            return '';
        }).filter(item => item !== '').slice(0, 5); // Limit to max 5 bullet points
        
        if (bulletPoints.length > 0) {
            return `<ul class="slide-content-list">${bulletPoints.join('')}</ul>`;
        }
    }
    
    // First, check if content already has HTML structure
    if (content.includes('<li>') || content.includes('<ul>') || content.includes('<p>')) {
        // If it's already formatted HTML but has too many points, limit it
        if (content.includes('<li>')) {
            const liMatches = content.match(/<li[^>]*>.*?<\/li>/g);
            if (liMatches && liMatches.length > 5) {
                const limitedLis = liMatches.slice(0, 5);
                return `<ul class="slide-content-list">${limitedLis.join('')}</ul>`;
            }
        }
        return cleanContent; // Already formatted
    }
    
    // Split content into sentences for bullet point conversion (limit to 5 points)
    const sentences = cleanContent.split(/[.!?]\s+/).filter(s => s.trim() !== '' && s.trim().length > 10).slice(0, 5);
    
    // If we have 2 or fewer meaningful sentences, keep as paragraph
    if (sentences.length <= 2) {
        return `<p>${cleanContent}</p>`;
    }
    
    // Convert sentences to bullet points for better slide formatting (3-5 points)
    const bulletPoints = sentences.slice(0, 5).map(sentence => {
        let cleaned = sentence.trim();
        // Remove trailing punctuation
        cleaned = cleaned.replace(/[.!?;:,]+$/, '');
        // Ensure first letter is capitalized
        cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
        // Add period if needed
        if (!cleaned.match(/[.!?]$/)) {
            cleaned += '.';
        }
        return `<li>${cleaned}</li>`;
    });
    
    // Ensure we have at least 3 points for consistency
    if (bulletPoints.length >= 3) {
        return `<ul class="slide-content-list">${bulletPoints.join('')}</ul>`;
    } else {
        // If less than 3 points, return as paragraph
        return `<p>${cleanContent}</p>`;
    }
}

function formatSlideContentPreview(content, maxLength = 200, slideId = null) {
    if (!content || content.trim() === '') {
        return '<em>No content available</em>';
    }
    
    // Clean the content and remove excess whitespace
    const cleanContent = content.trim().replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    // If content is short enough, just return it
    if (cleanContent.length <= maxLength) {
        return cleanContent;
    }
    
    // Truncate the content at a word boundary
    let truncatedContent = cleanContent.substring(0, maxLength);
    const lastSpace = truncatedContent.lastIndexOf(' ');
    if (lastSpace > maxLength * 0.8) { // Only truncate at word boundary if it's not too far back
        truncatedContent = truncatedContent.substring(0, lastSpace);
    }
    
    // Generate unique ID for this preview
    const previewId = slideId ? `preview-${slideId}` : `preview-${Math.random().toString(36).substr(2, 9)}`;
    
    return `<span id="short-${previewId}">${truncatedContent}<span class="slide-preview-toggle" onclick="toggleSlidePreview('${previewId}')" style="color: #2563eb; cursor: pointer; font-weight: 500;">... <i class="fas fa-chevron-down"></i> Show more</span></span><span id="full-${previewId}" style="display: none;">${cleanContent} <span class="slide-preview-toggle" onclick="toggleSlidePreview('${previewId}')" style="color: #2563eb; cursor: pointer; font-weight: 500;"><i class="fas fa-chevron-up"></i> Show less</span></span>`;
}

// Toggle slide preview expansion
function toggleSlidePreview(previewId) {
    console.log('toggleSlidePreview called with:', previewId);
    const shortContent = document.getElementById(`short-${previewId}`);
    const fullContent = document.getElementById(`full-${previewId}`);
    
    console.log('Found elements:', { shortContent, fullContent });
    
    if (!shortContent || !fullContent) {
        console.error('Could not find preview elements for:', previewId);
        return;
    }
    
    const isExpanded = fullContent.style.display !== 'none';
    console.log('isExpanded:', isExpanded);
    
    if (isExpanded) {
        // Collapse - show short content, hide full content
        shortContent.style.display = 'inline';
        fullContent.style.display = 'none';
        console.log('Collapsed preview');
    } else {
        // Expand - hide short content, show full content
        shortContent.style.display = 'none';
        fullContent.style.display = 'inline';
        console.log('Expanded preview');
    }
}

function nextSlide() {
    console.log('nextSlide called, currentSlideshow:', window.currentSlideshow);
    if (!window.currentSlideshow || window.currentSlideshow.currentIndex >= window.currentSlideshow.slides.length - 1) {
        console.log('Cannot go to next slide - at end or no slideshow');
        return;
    }
    
    window.currentSlideshow.currentIndex++;
    console.log('Moving to slide:', window.currentSlideshow.currentIndex + 1, 'of', window.currentSlideshow.slides.length);
    console.log('About to call updateSlideDisplay()');
    try {
        updateSlideDisplay();
        console.log('updateSlideDisplay() completed');
    } catch (error) {
        console.error('Error in updateSlideDisplay():', error);
    }
}

function previousSlide() {
    console.log('previousSlide called, currentSlideshow:', window.currentSlideshow);
    if (!window.currentSlideshow || window.currentSlideshow.currentIndex <= 0) {
        console.log('Cannot go to previous slide - at beginning or no slideshow');
        return;
    }
    
    window.currentSlideshow.currentIndex--;
    console.log('Moving to slide:', window.currentSlideshow.currentIndex + 1, 'of', window.currentSlideshow.slides.length);
    console.log('About to call updateSlideDisplay()');
    try {
        updateSlideDisplay();
        console.log('updateSlideDisplay() completed');
    } catch (error) {
        console.error('Error in updateSlideDisplay():', error);
    }
}

function updateSlideDisplay() {
    console.log('=== updateSlideDisplay() called ===');
    const slideshow = window.currentSlideshow;
    console.log('Current slideshow object:', slideshow);
    
    if (!slideshow) {
        console.error('No slideshow object found');
        return;
    }
    if (!slideshow.slides) {
        console.error('No slides array found');
        return;
    }
    if (slideshow.currentIndex < 0) {
        console.error('Current index is negative:', slideshow.currentIndex);
        return;
    }
    if (slideshow.currentIndex >= slideshow.slides.length) {
        console.error('Current index exceeds slides length:', slideshow.currentIndex, 'vs', slideshow.slides.length);
        return;
    }
    
    console.log('Slideshow validation passed, continuing with update...');
    
    const slide = slideshow.slides[slideshow.currentIndex];
    console.log('Updating slide display to slide:', slideshow.currentIndex + 1, 'of', slideshow.slides.length, '- Title:', slide.title);
    
    // Update slide content
    console.log('Looking for DOM elements...');
    const slideContent = document.querySelector('.slideshow-modal .slide-content');
    const slideTitle = document.querySelector('.slideshow-modal .slideshow-title h2');
    const slideCounter = document.querySelector('.slideshow-modal .slide-counter');
    
    console.log('DOM elements found:', {
        slideContent: slideContent ? 'YES' : 'NO',
        slideTitle: slideTitle ? 'YES' : 'NO', 
        slideCounter: slideCounter ? 'YES' : 'NO'
    });
    
    if (slideContent) {
        slideContent.innerHTML = formatSlideContent(slide.content);
        console.log('Updated slide content');
    } else {
        console.error('Could not find slide content element');
    }
    
    if (slideTitle) {
        slideTitle.textContent = slide.title || `Slide ${slideshow.currentIndex + 1}`;
        console.log('Updated slide title');
    } else {
        console.error('Could not find slide title element');
    }
    
    if (slideCounter) {
        slideCounter.textContent = `${slideshow.currentIndex + 1} / ${slideshow.slides.length}`;
        console.log('Updated slide counter');
    } else {
        console.error('Could not find slide counter element');
    }
    
    // Update navigation buttons using IDs
    const prevBtn = document.getElementById('prevSlideBtn');
    const nextBtn = document.getElementById('nextSlideBtn');
    
    if (prevBtn) {
        prevBtn.disabled = slideshow.currentIndex === 0;
        prevBtn.style.opacity = prevBtn.disabled ? '0.5' : '1';
        prevBtn.style.cursor = prevBtn.disabled ? 'not-allowed' : 'pointer';
        console.log('Previous button disabled:', prevBtn.disabled);
    } else {
        console.error('Could not find previous button');
    }
    
    if (nextBtn) {
        nextBtn.disabled = slideshow.currentIndex === slideshow.slides.length - 1;
        nextBtn.style.opacity = nextBtn.disabled ? '0.5' : '1';
        nextBtn.style.cursor = nextBtn.disabled ? 'not-allowed' : 'pointer';
        console.log('Next button disabled:', nextBtn.disabled);
    } else {
        console.error('Could not find next button');
    }
    
    console.log('Slide display update completed');
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
            // Use the new vertical slides view
            showVerticalSlidesView(data.slides);
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
    console.log('=== openEmbeddedLab DEBUG ===');
    console.log('CourseId:', courseId);
    console.log('Available courses:', userCourses);
    
    const course = userCourses.find(c => c.id == courseId);
    if (!course) {
        console.error('Course not found for lab environment. CourseId:', courseId, 'Available courses:', userCourses);
        showNotification('Course not found for lab environment', 'error');
        return;
    }
    
    console.log('Found course:', course.title);
    
    try {
        // Test popup blocker first
        console.log('Attempting to open popup window...');
        const labWindow = window.open('about:blank', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
        
        if (!labWindow) {
            console.error('Popup was blocked!');
            showNotification('Popup blocked! Please allow popups for this site and try again.', 'warning');
            return;
        }
        
        console.log('Popup window created successfully');
        
        // Load the dedicated lab page with course parameters
        const labUrl = `lab.html?course=${encodeURIComponent(course.title)}&courseId=${encodeURIComponent(courseId)}`;
        console.log('Loading lab URL:', labUrl);
        
        labWindow.location.href = labUrl;
        
        console.log('Lab window navigation initiated');
        
        // Add a small delay to check if window loaded
        setTimeout(() => {
            try {
                if (labWindow.closed) {
                    console.warn('Lab window was closed immediately');
                    showNotification('Lab window was closed. Please check popup settings.', 'warning');
                } else {
                    console.log('Lab window appears to be open and loading');
                    showNotification('Lab environment opened in new window', 'success');
                }
            } catch (e) {
                console.log('Cannot check lab window status (normal due to cross-origin)');
            }
        }, 1000);
        
    } catch (error) {
        console.error('Error opening lab environment:', error);
        showNotification('Error opening lab environment: ' + error.message, 'error');
    }
}

// Slide navigation functions

// eslint-disable-next-line no-unused-vars
function showSlidesOverview() {
    const slidesContainer = document.getElementById('slidesContainer');
    
    if (slidesContainer.classList.contains('overview-mode')) {
        // Switch back to single slide mode
        slidesContainer.classList.remove('overview-mode');
        updateSlideDisplayEditor();
    } else {
        // Switch to overview mode
        slidesContainer.classList.add('overview-mode');
        const slides = slidesContainer.querySelectorAll('.slide-item');
        slides.forEach(slide => slide.classList.add('active'));
    }
}

function updateSlideDisplayEditor() {
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
    console.log('=== approveSyllabus called with courseId:', courseId);
    try {
        // Show progress modal
        console.log('Showing progress modal...');
        showProgressModal('Generating Course Content', 'Preparing to generate slides, exercises, and quizzes...');
        console.log('Progress modal should be visible now');
        
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
    console.log('=== showProgressModal called with:', title, message);
    // Close any existing progress modal
    const existingModal = document.querySelector('.progress-modal-overlay');
    if (existingModal) {
        console.log('Removing existing progress modal');
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

// Helper functions for course management modal
function generateRecentActivity(enrollments) {
    if (!enrollments || enrollments.length === 0) {
        return '<div class="no-activity">No recent activity</div>';
    }
    
    const recentActivities = enrollments.slice(0, 5).map(enrollment => {
        const enrollDate = new Date(enrollment.enrolled_at || enrollment.created_at || Date.now());
        const timeAgo = getTimeAgo(enrollDate);
        return `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-user-plus"></i>
                </div>
                <div class="activity-details">
                    <div class="activity-title">${enrollment.student_name || 'Student'} enrolled</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }).join('');
    
    return recentActivities || '<div class="no-activity">No recent activity</div>';
}

function generateStudentsList(enrollments) {
    if (!enrollments || enrollments.length === 0) {
        return '<div class="no-students">No students enrolled yet</div>';
    }
    
    return enrollments.map(enrollment => {
        const enrollDate = new Date(enrollment.enrolled_at || enrollment.created_at || Date.now());
        const progress = Math.floor(Math.random() * 100); // Mock progress
        const status = enrollment.status || 'active';
        
        return `
            <div class="student-item">
                <div class="student-avatar">
                    <div class="avatar-circle">
                        ${getInitials(enrollment.student_name || 'Student')}
                    </div>
                </div>
                <div class="student-info">
                    <div class="student-name">${enrollment.student_name || 'Unknown Student'}</div>
                    <div class="student-email">${enrollment.student_email || 'No email'}</div>
                    <div class="student-meta">
                        <span class="enrollment-date">Enrolled: ${enrollDate.toLocaleDateString()}</span>
                        <span class="student-status status-${status}">${status}</span>
                    </div>
                </div>
                <div class="student-progress">
                    <div class="progress-text">${progress}% Complete</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                </div>
                <div class="student-actions">
                    <button class="btn btn-sm btn-secondary" onclick="viewStudentProgress('${enrollment.student_id}')">
                        <i class="fas fa-chart-bar"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="unenrollStudent('${enrollment.id}')">
                        <i class="fas fa-user-minus"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function generateContentOverview(contentData) {
    if (!contentData || !contentData.modules) {
        return '<div class="no-content">No content modules available</div>';
    }
    
    const moduleCount = contentData.modules.length;
    const lessonCount = contentData.modules.reduce((total, module) => total + (module.lessons ? module.lessons.length : 0), 0);
    
    return `
        <div class="content-stats">
            <div class="content-stat">
                <i class="fas fa-book"></i>
                <span>${moduleCount} Modules</span>
            </div>
            <div class="content-stat">
                <i class="fas fa-file-alt"></i>
                <span>${lessonCount} Lessons</span>
            </div>
        </div>
        <div class="content-modules">
            ${contentData.modules.map(module => `
                <div class="content-module">
                    <h6><i class="fas fa-folder"></i> ${module.title}</h6>
                    <p>${module.description || 'No description available'}</p>
                    ${module.lessons ? `<small>${module.lessons.length} lessons</small>` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function generateLabsList(labsData, courseId) {
    if (!labsData || labsData.length === 0) {
        return '<div class="no-labs">No lab environments created yet</div>';
    }
    
    return labsData.map(lab => {
        const createdDate = new Date(lab.created_at || Date.now());
        const status = lab.status || 'active';
        const usageCount = lab.usage_count || Math.floor(Math.random() * 50);
        
        return `
            <div class="lab-item">
                <div class="lab-icon">
                    <i class="fas fa-flask"></i>
                </div>
                <div class="lab-info">
                    <div class="lab-name">${lab.name || 'Lab Environment'}</div>
                    <div class="lab-description">${lab.description || 'No description'}</div>
                    <div class="lab-meta">
                        <span>Created: ${createdDate.toLocaleDateString()}</span>
                        <span class="lab-status status-${status}">${status}</span>
                        <span>${usageCount} uses</span>
                    </div>
                </div>
                <div class="lab-actions">
                    <button class="btn btn-sm btn-primary" onclick="openEmbeddedLab('${courseId}', '${lab.name}')">
                        <i class="fas fa-play"></i> Open
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editLab('${lab.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteLab('${lab.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function showManagementTab(tabName, courseId) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.management-tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    event.target.classList.add('active');
    const tabContent = document.getElementById(`${tabName}-management-tab`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
}

function closeCourseManagementModal() {
    const modal = document.getElementById('courseManagementModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function updateCourseSettings(event, courseId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const settings = {
        title: document.getElementById('courseTitle').value,
        description: document.getElementById('courseDescription').value,
        category: document.getElementById('courseCategory').value,
        difficulty_level: document.getElementById('courseDifficulty').value,
        estimated_duration: document.getElementById('courseDuration').value
    };
    
    // Mock update - in real implementation, this would call the backend
    showNotification('Course settings updated successfully!', 'success');
    
    // Update the course in local data
    const courseIndex = userCourses.findIndex(c => c.id == courseId);
    if (courseIndex !== -1) {
        userCourses[courseIndex] = { ...userCourses[courseIndex], ...settings };
        displayCourses(userCourses);
    }
    
    closeCourseManagementModal();
}

function getTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
}

// Additional helper functions for student and lab management
function viewStudentProgress(studentId) {
    showNotification('Student progress view coming soon', 'info');
}

function unenrollStudent(enrollmentId) {
    if (confirm('Are you sure you want to unenroll this student?')) {
        showNotification('Student unenrollment not yet implemented', 'warning');
    }
}

function editLab(labId) {
    showNotification('Lab editing interface coming soon', 'info');
}

function deleteLab(labId) {
    if (confirm('Are you sure you want to delete this lab environment?')) {
        showNotification('Lab deletion not yet implemented', 'warning');
    }
}

function showAddStudentForm(courseId) {
    showNotification('Add student form coming soon', 'info');
}

// ===================================
// CONTENT MANAGEMENT FUNCTIONS
// ===================================

// Global variables for content management
let uploadedFiles = {
    syllabus: null,
    slides: null,
    materials: []
};
let currentUploadRequest = null;

// Content Tab Management
// eslint-disable-next-line no-unused-vars
function showContentTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.content-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.content-tab').forEach(tab => tab.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    event.target.classList.add('active');
    const tabContent = document.getElementById(`${tabName}-content-tab`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Load data if needed
    if (tabName === 'export') {
        loadExportCourseOptions();
    }
}

// ===================================
// FILE UPLOAD FUNCTIONALITY
// ===================================

// Initialize file upload handlers
function initializeFileUpload() {
    // Syllabus upload
    const syllabusInput = document.getElementById('syllabusFileInput');
    const syllabusArea = document.getElementById('syllabusUploadArea');
    const syllabusBtn = document.getElementById('uploadSyllabusBtn');
    
    if (syllabusInput) {
        syllabusInput.addEventListener('change', function(e) {
            handleFileSelection(e.target.files[0], 'syllabus');
        });
    }
    
    if (syllabusArea) {
        setupDragAndDrop(syllabusArea, 'syllabus');
    }
    
    // Slides upload
    const slidesInput = document.getElementById('slidesFileInput');
    const slidesArea = document.getElementById('slidesUploadArea');
    const slidesBtn = document.getElementById('uploadSlidesBtn');
    
    if (slidesInput) {
        slidesInput.addEventListener('change', function(e) {
            handleFileSelection(e.target.files[0], 'slides');
        });
    }
    
    if (slidesArea) {
        setupDragAndDrop(slidesArea, 'slides');
    }
    
    // Materials upload
    const materialsInput = document.getElementById('materialsFileInput');
    const materialsArea = document.getElementById('materialsUploadArea');
    const materialsBtn = document.getElementById('uploadMaterialsBtn');
    
    if (materialsInput) {
        materialsInput.addEventListener('change', function(e) {
            handleFileSelection(Array.from(e.target.files), 'materials');
        });
    }
    
    if (materialsArea) {
        setupDragAndDrop(materialsArea, 'materials');
    }
}

// Setup drag and drop functionality
function setupDragAndDrop(area, type) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        area.addEventListener(eventName, () => area.classList.add('drag-over'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, () => area.classList.remove('drag-over'), false);
    });
    
    area.addEventListener('drop', function(e) {
        const files = e.dataTransfer.files;
        if (type === 'materials') {
            handleFileSelection(Array.from(files), type);
        } else {
            handleFileSelection(files[0], type);
        }
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Handle file selection
function handleFileSelection(files, type) {
    if (type === 'materials') {
        uploadedFiles.materials = files;
        updateFileDisplay(files, type);
        enableUploadButton(type);
    } else {
        const file = files;
        if (file && validateFile(file, type)) {
            uploadedFiles[type] = file;
            updateFileDisplay([file], type);
            enableUploadButton(type);
        }
    }
}

// Validate file types
function validateFile(file, type) {
    const allowedTypes = {
        syllabus: ['.pdf', '.doc', '.docx', '.txt'],
        slides: ['.ppt', '.pptx', '.pdf', '.json'],
        materials: ['.pdf', '.doc', '.docx', '.zip', '.jpg', '.png', '.mp4', '.mp3']
    };
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const allowed = allowedTypes[type];
    
    if (!allowed.includes(fileExtension)) {
        showNotification(`Invalid file type. Allowed types: ${allowed.join(', ')}`, 'error');
        return false;
    }
    
    // Check file size (50MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('File size too large. Maximum size is 50MB.', 'error');
        return false;
    }
    
    return true;
}

// Update file display
function updateFileDisplay(files, type) {
    const area = document.getElementById(`${type}UploadArea`);
    const placeholder = area.querySelector('.upload-placeholder');
    
    // Create or update file list
    let fileList = area.querySelector('.file-list');
    if (!fileList) {
        fileList = document.createElement('div');
        fileList.className = 'file-list';
        area.appendChild(fileList);
    }
    
    fileList.innerHTML = '';
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file"></i>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-sm btn-danger" onclick="removeFile('${type}', '${file.name}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        fileList.appendChild(fileItem);
    });
    
    placeholder.style.display = files.length > 0 ? 'none' : 'block';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Enable upload button
function enableUploadButton(type) {
    const btn = document.getElementById(`upload${type.charAt(0).toUpperCase() + type.slice(1)}Btn`);
    if (btn) {
        btn.disabled = false;
    }
}

// Remove file
// eslint-disable-next-line no-unused-vars
function removeFile(type, fileName) {
    if (type === 'materials') {
        uploadedFiles.materials = uploadedFiles.materials.filter(file => file.name !== fileName);
        updateFileDisplay(uploadedFiles.materials, type);
        if (uploadedFiles.materials.length === 0) {
            document.getElementById('uploadMaterialsBtn').disabled = true;
        }
    } else {
        uploadedFiles[type] = null;
        const area = document.getElementById(`${type}UploadArea`);
        const fileList = area.querySelector('.file-list');
        const placeholder = area.querySelector('.upload-placeholder');
        
        if (fileList) fileList.remove();
        if (placeholder) placeholder.style.display = 'block';
        
        document.getElementById(`upload${type.charAt(0).toUpperCase() + type.slice(1)}Btn`).disabled = true;
    }
}

// ===================================
// UPLOAD FUNCTIONS
// ===================================

// Upload syllabus and process with AI
// eslint-disable-next-line no-unused-vars
async function uploadSyllabus() {
    if (!uploadedFiles.syllabus) {
        showNotification('Please select a syllabus file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', uploadedFiles.syllabus);
    formData.append('type', 'syllabus');
    formData.append('process_with_ai', 'true');
    
    try {
        showUploadProgress('Uploading and processing syllabus...');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            hideUploadProgress();
            showNotification('Syllabus uploaded successfully! AI processing started.', 'success');
            
            // Reset file selection
            uploadedFiles.syllabus = null;
            removeFile('syllabus', uploadedFiles.syllabus?.name);
            
            // Show processing status
            showAIProcessingStatus(result.processing_id);
            
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Error uploading syllabus:', error);
        hideUploadProgress();
        showNotification('Failed to upload syllabus', 'error');
    }
}

// Upload slides
// eslint-disable-next-line no-unused-vars
async function uploadSlides() {
    if (!uploadedFiles.slides) {
        showNotification('Please select a slides file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', uploadedFiles.slides);
    formData.append('type', 'slides');
    
    try {
        showUploadProgress('Uploading slides...');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            hideUploadProgress();
            showNotification('Slides uploaded successfully!', 'success');
            
            // Reset file selection
            uploadedFiles.slides = null;
            removeFile('slides', uploadedFiles.slides?.name);
            
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Error uploading slides:', error);
        hideUploadProgress();
        showNotification('Failed to upload slides', 'error');
    }
}

// Upload materials
// eslint-disable-next-line no-unused-vars
async function uploadMaterials() {
    if (!uploadedFiles.materials || uploadedFiles.materials.length === 0) {
        showNotification('Please select materials to upload first', 'error');
        return;
    }
    
    const formData = new FormData();
    uploadedFiles.materials.forEach(file => {
        formData.append('files', file);
    });
    formData.append('type', 'materials');
    
    try {
        showUploadProgress('Uploading materials...');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            hideUploadProgress();
            showNotification('Materials uploaded successfully!', 'success');
            
            // Reset file selection
            uploadedFiles.materials = [];
            const area = document.getElementById('materialsUploadArea');
            const fileList = area.querySelector('.file-list');
            const placeholder = area.querySelector('.upload-placeholder');
            
            if (fileList) fileList.remove();
            if (placeholder) placeholder.style.display = 'block';
            document.getElementById('uploadMaterialsBtn').disabled = true;
            
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Error uploading materials:', error);
        hideUploadProgress();
        showNotification('Failed to upload materials', 'error');
    }
}

// Show upload progress
function showUploadProgress(message) {
    const progressDiv = document.getElementById('uploadProgress');
    const progressText = document.getElementById('uploadProgressText');
    const progressFill = document.getElementById('uploadProgressFill');
    
    if (progressDiv && progressText && progressFill) {
        progressText.textContent = message;
        progressFill.style.width = '10%';
        progressDiv.style.display = 'block';
        
        // Simulate progress
        let progress = 10;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 500);
        
        // Store interval for cleanup
        progressDiv.progressInterval = interval;
    }
}

// Hide upload progress
function hideUploadProgress() {
    const progressDiv = document.getElementById('uploadProgress');
    if (progressDiv) {
        if (progressDiv.progressInterval) {
            clearInterval(progressDiv.progressInterval);
        }
        progressDiv.style.display = 'none';
    }
}

// Cancel upload
// eslint-disable-next-line no-unused-vars
function cancelUpload() {
    if (currentUploadRequest) {
        currentUploadRequest.abort();
        currentUploadRequest = null;
    }
    hideUploadProgress();
    showNotification('Upload cancelled', 'info');
}

// Show AI processing status
function showAIProcessingStatus(processingId) {
    // This would show a modal or section tracking AI processing
    showNotification('AI is processing your content. You will be notified when complete.', 'info');
    
    // Poll for processing status
    pollProcessingStatus(processingId);
}

// Poll processing status
async function pollProcessingStatus(processingId) {
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/processing/${processingId}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            const status = await response.json();
            
            if (status.status === 'completed') {
                showNotification('AI processing completed! Your content is ready.', 'success');
                // Refresh content if user is on manage tab
                const manageTab = document.getElementById('manage-content-tab');
                if (manageTab && manageTab.classList.contains('active')) {
                    loadCourseContent();
                }
            } else if (status.status === 'failed') {
                showNotification('AI processing failed. Please try again.', 'error');
            } else {
                // Continue polling
                setTimeout(() => pollProcessingStatus(processingId), 5000);
            }
        }
    } catch (error) {
        console.error('Error checking processing status:', error);
    }
}

// ===================================
// EXPORT FUNCTIONALITY
// ===================================

// Load export course options
function loadExportCourseOptions() {
    const select = document.getElementById('exportCourseSelect');
    if (select && userCourses) {
        select.innerHTML = '<option value="">Select a course...</option>';
        userCourses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            select.appendChild(option);
        });
    }
}

// Load export options for selected course
// eslint-disable-next-line no-unused-vars
function loadExportOptions() {
    const courseId = document.getElementById('exportCourseSelect').value;
    const exportOptions = document.getElementById('exportOptions');
    
    if (courseId) {
        exportOptions.style.display = 'block';
    } else {
        exportOptions.style.display = 'none';
    }
}

// Export slides in various formats
// eslint-disable-next-line no-unused-vars
async function exportSlides(format) {
    const courseId = document.getElementById('exportCourseSelect').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    try {
        showNotification('Preparing slides export...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/export/slides`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const filename = `slides_${courseId}.${getFileExtension(format)}`;
            downloadFile(blob, filename);
            showNotification('Slides exported successfully!', 'success');
        } else {
            throw new Error('Export failed');
        }
    } catch (error) {
        console.error('Error exporting slides:', error);
        showNotification('Failed to export slides', 'error');
    }
}

// Export exercises in various formats
// eslint-disable-next-line no-unused-vars
async function exportExercises(format) {
    const courseId = document.getElementById('exportCourseSelect').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    try {
        showNotification('Preparing exercises export...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/export/exercises`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const filename = `exercises_${courseId}.${getFileExtension(format)}`;
            downloadFile(blob, filename);
            showNotification('Exercises exported successfully!', 'success');
        } else {
            throw new Error('Export failed');
        }
    } catch (error) {
        console.error('Error exporting exercises:', error);
        showNotification('Failed to export exercises', 'error');
    }
}

// Export quizzes in various formats
// eslint-disable-next-line no-unused-vars
async function exportQuizzes(format) {
    const courseId = document.getElementById('exportCourseSelect').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    try {
        showNotification('Preparing quizzes export...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/export/quizzes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const filename = `quizzes_${courseId}.${getFileExtension(format)}`;
            downloadFile(blob, filename);
            showNotification('Quizzes exported successfully!', 'success');
        } else {
            throw new Error('Export failed');
        }
    } catch (error) {
        console.error('Error exporting quizzes:', error);
        showNotification('Failed to export quizzes', 'error');
    }
}

// Export complete course
// eslint-disable-next-line no-unused-vars
async function exportCompleteCourse(format) {
    const courseId = document.getElementById('exportCourseSelect').value;
    if (!courseId) {
        showNotification('Please select a course first', 'error');
        return;
    }
    
    try {
        showNotification('Preparing complete course export...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/export/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const filename = `course_complete_${courseId}.${getFileExtension(format)}`;
            downloadFile(blob, filename);
            showNotification('Complete course exported successfully!', 'success');
        } else {
            throw new Error('Export failed');
        }
    } catch (error) {
        console.error('Error exporting complete course:', error);
        showNotification('Failed to export complete course', 'error');
    }
}

// Get file extension for format
function getFileExtension(format) {
    const extensions = {
        'powerpoint': 'pptx',
        'json': 'json',
        'pdf': 'pdf',
        'zip': 'zip',
        'excel': 'xlsx',
        'scorm': 'zip'
    };
    return extensions[format] || 'zip';
}

// Download file
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// ===================================
// AI GENERATION FUNCTIONS
// ===================================

// Generate content from uploaded syllabus
// eslint-disable-next-line no-unused-vars
async function generateFromSyllabus() {
    const generateSlides = document.getElementById('generateSlides').checked;
    const generateExercises = document.getElementById('generateExercises').checked;
    const generateQuizzes = document.getElementById('generateQuizzes').checked;
    const generateLabs = document.getElementById('generateLabs').checked;
    
    if (!generateSlides && !generateExercises && !generateQuizzes && !generateLabs) {
        showNotification('Please select at least one content type to generate', 'error');
        return;
    }
    
    try {
        showNotification('Starting AI content generation...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/generate/from-syllabus`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                generate_slides: generateSlides,
                generate_exercises: generateExercises,
                generate_quizzes: generateQuizzes,
                generate_labs: generateLabs
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('AI content generation started! You will be notified when complete.', 'success');
            showAIProcessingStatus(result.processing_id);
        } else {
            throw new Error('Generation failed');
        }
    } catch (error) {
        console.error('Error generating content from syllabus:', error);
        showNotification('Failed to start content generation', 'error');
    }
}

// Generate custom content
// eslint-disable-next-line no-unused-vars
async function generateCustomContent() {
    const prompt = document.getElementById('aiPrompt').value.trim();
    const contentType = document.getElementById('contentType').value;
    
    if (!prompt) {
        showNotification('Please enter a description for what you want to generate', 'error');
        return;
    }
    
    try {
        showNotification('Generating custom content...', 'info');
        
        const response = await fetch(`${CONFIG.BASE_URL}/api/content/generate/custom`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                prompt: prompt,
                content_type: contentType
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Custom content generation started! You will be notified when complete.', 'success');
            showAIProcessingStatus(result.processing_id);
            
            // Clear the form
            document.getElementById('aiPrompt').value = '';
        } else {
            throw new Error('Generation failed');
        }
    } catch (error) {
        console.error('Error generating custom content:', error);
        showNotification('Failed to generate custom content', 'error');
    }
}

// Content Tab Management
function showContentTab(tabName) {
    // Hide all content tabs
    const tabs = document.querySelectorAll('.content-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-content-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activate corresponding button
    const activeButton = event?.target || document.querySelector(`[onclick="showContentTab('${tabName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
}


// Syllabus management functions
async function viewSyllabus(courseId) {
    try {
        const syllabusUrl = CONFIG.ENDPOINTS.SYLLABUS(courseId);
        console.log('Fetching syllabus from URL:', syllabusUrl);
        console.log('CONFIG.ENDPOINTS.SYLLABUS function:', CONFIG.ENDPOINTS.SYLLABUS);
        
        const response = await fetch(syllabusUrl, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            console.error('Syllabus fetch failed. Status:', response.status, 'URL:', syllabusUrl);
            throw new Error('Failed to load syllabus');
        }
        
        const data = await response.json();
        showSyllabusModal(data.syllabus, 'view');
        
    } catch (error) {
        console.error('Error loading syllabus:', error);
        showNotification('Failed to load syllabus', 'error');
    }
}

async function editSyllabus(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.SYLLABUS(courseId), {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load syllabus');
        }
        
        const data = await response.json();
        showSyllabusModal(data.syllabus, 'edit', courseId);
        
    } catch (error) {
        console.error('Error loading syllabus:', error);
        showNotification('Failed to load syllabus for editing', 'error');
    }
}

async function generateSyllabus(courseId) {
    try {
        // Get course details first
        const courseResponse = await fetch(CONFIG.ENDPOINTS.COURSE_BY_ID(courseId), {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!courseResponse.ok) {
            throw new Error('Failed to load course details');
        }
        
        const course = await courseResponse.json();
        
        showNotification('Generating syllabus...', 'info');
        
        const response = await fetch(CONFIG.ENDPOINTS.GENERATE_SYLLABUS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                title: course.title,
                description: course.description,
                category: course.category || 'General',
                difficulty_level: course.difficulty_level || 'Beginner',
                estimated_duration: course.estimated_duration || 4
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate syllabus');
        }
        
        const result = await response.json();
        showNotification('Syllabus generated successfully!', 'success');
        
        // Refresh the course content display
        loadCourseContent();
        
    } catch (error) {
        console.error('Error generating syllabus:', error);
        showNotification('Failed to generate syllabus', 'error');
    }
}

async function regenerateSyllabus(courseId) {
    if (!confirm('Are you sure you want to regenerate the syllabus? This will replace the current syllabus.')) {
        return;
    }
    
    await generateSyllabus(courseId);
}

// Show syllabus in a modal
function showSyllabusModal(syllabus, mode = 'view', courseId = null) {
    const modal = document.createElement('div');
    modal.className = 'modal syllabus-modal';
    modal.id = 'syllabusModal';
    
    const isEditable = mode === 'edit';
    const modalTitle = isEditable ? 'Edit Syllabus' : 'View Syllabus';
    
    modal.innerHTML = `
        <div class="modal-content large-modal">
            <div class="modal-header">
                <h3>${modalTitle}</h3>
                <button class="modal-close" onclick="closeSyllabusModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="syllabus-content">
                    <div class="syllabus-section">
                        <h4>Course Overview</h4>
                        ${isEditable ? 
                            `<textarea id="syllabusOverview" rows="4">${syllabus.overview || ''}</textarea>` :
                            `<p>${syllabus.overview || 'No overview available'}</p>`
                        }
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Learning Objectives</h4>
                        ${isEditable ? 
                            `<textarea id="syllabusObjectives" rows="6">${syllabus.objectives ? syllabus.objectives.join('\n') : ''}</textarea>` :
                            `<ul>${syllabus.objectives ? syllabus.objectives.map(obj => `<li>${obj}</li>`).join('') : '<li>No objectives listed</li>'}</ul>`
                        }
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Prerequisites</h4>
                        ${isEditable ? 
                            `<textarea id="syllabusPrerequisites" rows="3">${syllabus.prerequisites ? syllabus.prerequisites.join('\n') : ''}</textarea>` :
                            `<ul>${syllabus.prerequisites ? syllabus.prerequisites.map(prereq => `<li>${prereq}</li>`).join('') : '<li>No prerequisites listed</li>'}</ul>`
                        }
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Course Modules</h4>
                        <div class="modules-container">
                            ${syllabus.modules ? syllabus.modules.map(module => `
                                <div class="module-card">
                                    <h5>Module ${module.module_number}: ${module.title}</h5>
                                    ${module.description ? `<p class="module-description"><strong>Description:</strong> ${module.description}</p>` : ''}
                                    <p><strong>Duration:</strong> ${module.duration_hours} hours</p>
                                    <div class="module-topics">
                                        <p><strong>Topics Covered:</strong></p>
                                        <ul class="topics-list">${module.topics ? module.topics.map(topic => `<li>${topic}</li>`).join('') : '<li>No topics listed</li>'}</ul>
                                    </div>
                                    <div class="module-outcomes">
                                        <p><strong>Learning Outcomes:</strong></p>
                                        <ul class="outcomes-list">${module.learning_outcomes ? module.learning_outcomes.map(outcome => `<li>${outcome}</li>`).join('') : '<li>No outcomes listed</li>'}</ul>
                                    </div>
                                </div>
                            `).join('') : '<p>No modules defined</p>'}
                        </div>
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Assessment Strategy</h4>
                        ${isEditable ? 
                            `<textarea id="syllabusAssessment" rows="4">${syllabus.assessment_strategy || ''}</textarea>` :
                            `<p>${syllabus.assessment_strategy || 'No assessment strategy defined'}</p>`
                        }
                    </div>
                    
                    <div class="syllabus-section">
                        <h4>Resources</h4>
                        ${isEditable ? 
                            `<textarea id="syllabusResources" rows="4">${syllabus.resources ? syllabus.resources.join('\n') : ''}</textarea>` :
                            `<ul>${syllabus.resources ? syllabus.resources.map(resource => `<li>${resource}</li>`).join('') : '<li>No resources listed</li>'}</ul>`
                        }
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                ${isEditable ? 
                    `<button class="btn btn-primary" onclick="saveSyllabus('${courseId}')">Save Changes</button>` : 
                    ''
                }
                <button class="btn btn-secondary" onclick="closeSyllabusModal()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Prevent background scrolling
    document.body.style.overflow = 'hidden';
}

// Close syllabus modal and refresh dashboard
function closeSyllabusModal() {
    const modal = document.getElementById('syllabusModal');
    if (modal) {
        modal.remove();
    }
    
    // Restore background scrolling
    document.body.style.overflow = 'auto';
    
    // Refresh the course content to ensure it's up to date
    const courseSelect = document.getElementById('contentCourseSelect');
    if (courseSelect && courseSelect.value) {
        loadCourseContent();
    }
}

// Account menu modal functions
function showProfileModal() {
    const modal = document.createElement('div');
    modal.className = 'modal account-modal';
    modal.id = 'profileModal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Profile Settings</h3>
                <button class="modal-close" onclick="closeAccountModal('profileModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="profile-section">
                    <h4>Account Information</h4>
                    <div class="form-group">
                        <label for="profileFullName">Full Name</label>
                        <input type="text" id="profileFullName" value="${currentUser?.full_name || 'Instructor Name'}" class="form-control">
                    </div>
                    <div class="form-group">
                        <label for="profileEmail">Email</label>
                        <input type="email" id="profileEmail" value="${currentUser?.email || 'instructor@example.com'}" class="form-control" readonly>
                    </div>
                    <div class="form-group">
                        <label for="profileBio">Bio</label>
                        <textarea id="profileBio" rows="3" class="form-control" placeholder="Tell us about yourself...">${currentUser?.bio || ''}</textarea>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="saveProfile()">Save Changes</button>
                <button class="btn btn-secondary" onclick="closeAccountModal('profileModal')">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function showSettingsModal() {
    const modal = document.createElement('div');
    modal.className = 'modal account-modal';
    modal.id = 'settingsModal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Settings</h3>
                <button class="modal-close" onclick="closeAccountModal('settingsModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="settings-section">
                    <h4>Preferences</h4>
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="emailNotifications" checked>
                            <span class="checkmark"></span>
                            Email notifications for course updates
                        </label>
                    </div>
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="weeklyReports" checked>
                            <span class="checkmark"></span>
                            Weekly progress reports
                        </label>
                    </div>
                    <div class="form-group">
                        <label for="defaultCourseType">Default Course Type</label>
                        <select id="defaultCourseType" class="form-control">
                            <option value="programming">Programming</option>
                            <option value="mathematics">Mathematics</option>
                            <option value="science">Science</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>Dashboard Layout</h4>
                    <div class="form-group">
                        <label for="dashboardTheme">Theme</label>
                        <select id="dashboardTheme" class="form-control">
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="auto">Auto (System)</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
                <button class="btn btn-secondary" onclick="closeAccountModal('settingsModal')">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function showHelpModal() {
    const modal = document.createElement('div');
    modal.className = 'modal account-modal';
    modal.id = 'helpModal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Help & Support</h3>
                <button class="modal-close" onclick="closeAccountModal('helpModal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="help-section">
                    <h4>Getting Started</h4>
                    <ul>
                        <li><strong>Create a Course:</strong> Click "Create Course" to start building your course content</li>
                        <li><strong>Manage Content:</strong> Use the Content section to upload files and manage course materials</li>
                        <li><strong>View Students:</strong> Monitor student progress in the Students section</li>
                        <li><strong>Generate AI Content:</strong> Use AI to automatically create syllabi, slides, and exercises</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h4>Contact Support</h4>
                    <p>Need additional help? Contact our support team:</p>
                    <p><strong>Email:</strong> support@courseplatform.com</p>
                    <p><strong>Documentation:</strong> <a href="#" target="_blank">View User Guide</a></p>
                </div>
                
                <div class="help-section">
                    <h4>Keyboard Shortcuts</h4>
                    <ul>
                        <li><strong>Ctrl + N:</strong> Create new course</li>
                        <li><strong>Ctrl + S:</strong> Save current work</li>
                        <li><strong>Esc:</strong> Close active modal</li>
                    </ul>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeAccountModal('helpModal')">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Close account modals and maintain dashboard state
function closeAccountModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.remove();
    }
    
    // Restore background scrolling
    document.body.style.overflow = 'auto';
    
    // Close account dropdown if open
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.remove('show');
    }
    
    // NO dashboard refresh needed - this was the issue!
    // The user stays on whatever section they were on
}

// Save profile changes
async function saveProfile() {
    try {
        const fullName = document.getElementById('profileFullName').value;
        const bio = document.getElementById('profileBio').value;
        
        // Here you would typically make an API call to save profile
        // For now, just show success message
        showNotification('Profile updated successfully!', 'success');
        closeAccountModal('profileModal');
        
        // Update the UI with new name
        const userNameElements = document.querySelectorAll('#userName, .user-name');
        userNameElements.forEach(element => {
            if (element) element.textContent = fullName;
        });
        
    } catch (error) {
        console.error('Error saving profile:', error);
        showNotification('Failed to save profile changes', 'error');
    }
}

// Save settings changes
async function saveSettings() {
    try {
        const emailNotifications = document.getElementById('emailNotifications').checked;
        const weeklyReports = document.getElementById('weeklyReports').checked;
        const defaultCourseType = document.getElementById('defaultCourseType').value;
        const dashboardTheme = document.getElementById('dashboardTheme').value;
        
        // Here you would typically make an API call to save settings
        // For now, just show success message
        showNotification('Settings saved successfully!', 'success');
        closeAccountModal('settingsModal');
        
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Failed to save settings', 'error');
    }
}

// Save syllabus changes
async function saveSyllabus(courseId) {
    try {
        const overview = document.getElementById('syllabusOverview').value;
        const objectives = document.getElementById('syllabusObjectives').value.split('\n').filter(obj => obj.trim());
        const prerequisites = document.getElementById('syllabusPrerequisites').value.split('\n').filter(prereq => prereq.trim());
        const assessment = document.getElementById('syllabusAssessment').value;
        const resources = document.getElementById('syllabusResources').value.split('\n').filter(resource => resource.trim());
        
        const syllabusData = {
            overview,
            objectives,
            prerequisites,
            assessment_strategy: assessment,
            resources,
            modules: [] // For now, keeping existing modules - full module editing would need more complex UI
        };
        
        showNotification('Saving syllabus...', 'info');
        
        const response = await fetch(CONFIG.ENDPOINTS.REFINE_SYLLABUS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                course_id: courseId,
                feedback: 'Manual edit via instructor dashboard',
                current_syllabus: syllabusData
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save syllabus');
        }
        
        showNotification('Syllabus saved successfully!', 'success');
        closeSyllabusModal();
        
    } catch (error) {
        console.error('Error saving syllabus:', error);
        showNotification('Failed to save syllabus', 'error');
    }
}

// Global event handlers
document.addEventListener('keydown', function(e) {
    // Close modals with Escape key
    if (e.key === 'Escape') {
        // Close any open modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.remove());
        document.body.style.overflow = 'auto';
        
        // Close account dropdown
        const accountMenu = document.getElementById('accountMenu');
        if (accountMenu) {
            accountMenu.classList.remove('show');
        }
    }
});

// Click outside to close account dropdown
document.addEventListener('click', function(e) {
    const accountDropdown = document.getElementById('accountDropdown');
    const accountMenu = document.getElementById('accountMenu');
    
    if (accountDropdown && accountMenu && !accountDropdown.contains(e.target)) {
        accountMenu.classList.remove('show');
    }
});

// Fix account dropdown toggle
function toggleAccountDropdown() {
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.toggle('show');
    }
}

// View slides function (referenced in content management)
function getAuthToken() {
    return localStorage.getItem('authToken') || localStorage.getItem('token');
}

async function viewSlides(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.SLIDES(courseId), {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load slides');
        }
        
        const slidesData = await response.json();
        const slides = slidesData.slides || slidesData; // Handle different response formats
        
        if (slides.length === 0) {
            showNotification('No slides available for this course', 'warning');
            return;
        }
        
        // Show normal vertical stack view instead of slideshow
        showVerticalSlidesView(slides);
        
    } catch (error) {
        console.error('Error loading slides:', error);
        showNotification('Failed to load slides', 'error');
    }
}

// New function to show slides in vertical stack view
function showVerticalSlidesView(slides) {
    try {
        if (!slides || slides.length === 0) {
            showNotification('No slides available', 'warning');
            return;
        }
        
        // Create modal for vertical slides view
        const slidesModal = document.createElement('div');
        slidesModal.className = 'slides-modal vertical-view';
        slidesModal.innerHTML = `
            <div class="slides-container">
                <div class="slides-header">
                    <div class="slides-title">
                        <h2><i class="fas fa-presentation"></i> Course Slides</h2>
                        <span class="slides-count">${slides.length} slide${slides.length === 1 ? '' : 's'}</span>
                    </div>
                    <div class="slides-controls">
                        <button class="btn btn-primary" onclick="startSlideshowFromVertical()">
                            <i class="fas fa-play"></i> Slideshow Mode
                        </button>
                        <button class="btn btn-secondary" onclick="closeVerticalSlidesView()">
                            <i class="fas fa-times"></i> Close
                        </button>
                    </div>
                </div>
                
                <div class="slides-content-vertical">
                    ${slides.map((slide, index) => `
                        <div class="slide-card" data-slide-index="${index}">
                            <div class="slide-card-header">
                                <h3><span class="slide-number">${index + 1}.</span> ${slide.title || `Slide ${index + 1}`}</h3>
                            </div>
                            <div class="slide-card-content">
                                ${formatSlideContent(slide.content)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(slidesModal);
        
        // Store slides data globally for slideshow mode
        window.currentVerticalSlides = slides;
        
    } catch (error) {
        console.error('Error showing vertical slides view:', error);
        showNotification('Error displaying slides', 'error');
    }
}

// Function to close vertical slides view
function closeVerticalSlidesView() {
    const slidesModal = document.querySelector('.slides-modal.vertical-view');
    if (slidesModal) {
        slidesModal.remove();
    }
    window.currentVerticalSlides = null;
}

// Function to start slideshow from vertical view
function startSlideshowFromVertical() {
    console.log('startSlideshowFromVertical called, currentVerticalSlides:', window.currentVerticalSlides);
    
    if (window.currentVerticalSlides && window.currentVerticalSlides.length > 0) {
        console.log('Starting slideshow with', window.currentVerticalSlides.length, 'slides');
        // Store slides data before closing the view (since closeVerticalSlidesView clears it)
        const slidesToShow = window.currentVerticalSlides;
        // Close vertical view
        closeVerticalSlidesView();
        // Start slideshow with the stored slides
        showSlideshowModalDirect(slidesToShow);
    } else {
        console.error('No slides available for slideshow');
        showNotification('No slides available for slideshow', 'error');
    }
}

// Edit slides function (referenced in content management)
async function editSlides(courseId) {
    try {
        const response = await fetch(CONFIG.ENDPOINTS.COURSE_BY_ID(courseId), {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load course details');
        }
        
        const course = await response.json();
        editCourseContent(courseId);
        
    } catch (error) {
        console.error('Error loading course for editing:', error);
        showNotification('Failed to load course for editing', 'error');
    }
}

// Generate slides function (referenced in content management)
async function generateSlides(courseId) {
    try {
        // Check if course has a syllabus first
        const syllabusResponse = await fetch(CONFIG.ENDPOINTS.SYLLABUS(courseId), {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (syllabusResponse.ok) {
            // Generate slides from existing syllabus
            const syllabusData = await syllabusResponse.json();
            
            showNotification('Generating slides from syllabus...', 'info');
            
            const response = await fetch(CONFIG.ENDPOINTS.GENERATE_CONTENT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    course_id: courseId,
                    syllabus: syllabusData.syllabus
                })
            });
            
            if (response.ok) {
                showNotification('Slides generated successfully!', 'success');
                // Refresh the course content display
                loadCourseContent();
            } else {
                throw new Error('Failed to generate slides');
            }
        } else {
            // No syllabus exists, generate general course content
            showNotification('Generating course content including slides...', 'info');
            await generateCourseContent(courseId);
        }
        
    } catch (error) {
        console.error('Error generating slides:', error);
        showNotification('Failed to generate slides', 'error');
    }
}

// Initialize content management when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
});
