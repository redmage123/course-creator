// Student Dashboard JavaScript

let enrolledCourses = [];
let labEnvironments = [];
let currentUser = null;
let studentProgress = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadStudentData();
});

function initializeDashboard() {
    // Check if user is logged in and has student role
    currentUser = getCurrentUser();
    if (!currentUser || currentUser.role !== 'student') {
        window.location.href = 'index.html';
        return;
    }
    
    // Update user display
    updateUserDisplay();
    
    // Set up navigation
    setupNavigation();
    
    // Show dashboard by default
    showSection('dashboard');
}

function updateUserDisplay() {
    const elements = [
        { selector: '.user-name', text: currentUser?.full_name || 'Student' },
        { selector: '#userName', text: currentUser?.full_name || 'Student' },
        { selector: '#sidebarUserName', text: currentUser?.full_name || 'Student' },
        { selector: '.avatar-initials', text: getInitials(currentUser?.full_name || 'Student') },
        { selector: '#avatarInitials', text: getInitials(currentUser?.full_name || 'Student') },
        { selector: '#sidebarAvatarInitials', text: getInitials(currentUser?.full_name || 'Student') }
    ];
    
    elements.forEach(({ selector, text }) => {
        const element = document.querySelector(selector);
        if (element) element.textContent = text;
    });
}

// Navigation and section management
function setupNavigation() {
    // Add click handlers to navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            if (section) {
                showSection(section);
                updateNavigation(section);
            }
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update breadcrumb
    const breadcrumb = document.getElementById('currentSection');
    if (breadcrumb) {
        breadcrumb.textContent = getSectionTitle(sectionName);
    }
    
    // Update navigation
    updateNavigation(sectionName);
    
    // Load section-specific data
    loadSectionData(sectionName);
}

function updateNavigation(activeSection) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to current section
    const activeLink = document.querySelector(`[data-section="${activeSection}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function getSectionTitle(sectionName) {
    const titles = {
        'dashboard': 'Dashboard',
        'courses': 'My Courses',
        'progress': 'Learning Progress', 
        'labs': 'Lab Environment'
    };
    return titles[sectionName] || 'Dashboard';
}

function loadSectionData(sectionName) {
    switch(sectionName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'courses':
            loadCoursesData();
            break;
        case 'progress':
            loadProgressData();
            break;
        case 'labs':
            loadLabsData();
            break;
    }
}

async function loadStudentData() {
    try {
        await Promise.all([
            loadEnrolledCourses(),
            loadStudentProgress(),
            loadLabEnvironments()
        ]);
        updateDashboardMetrics();
    } catch (error) {
        console.error('Error loading student data:', error);
    }
}

// Data loading functions
async function loadEnrolledCourses() {
    try {
        const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_STUDENTS(currentUser.id)}`);
        
        if (response.ok) {
            const result = await response.json();
            enrolledCourses = result.enrollments || [];
            return enrolledCourses;
        } else {
            throw new Error('Failed to load enrolled courses');
        }
    } catch (error) {
        console.error('Error loading enrolled courses:', error);
        enrolledCourses = [];
        return [];
    }
}

async function loadStudentProgress() {
    try {
        // This would come from a dedicated progress tracking endpoint
        const response = await fetch(`${CONFIG.API_URLS.COURSE_MANAGEMENT}/student/${currentUser.id}/progress`);
        
        if (response.ok) {
            const result = await response.json();
            studentProgress = result.progress || {};
            return studentProgress;
        } else {
            // Fallback - calculate progress from enrolled courses
            studentProgress = calculateProgressFromCourses();
            return studentProgress;
        }
    } catch (error) {
        console.error('Error loading student progress:', error);
        studentProgress = calculateProgressFromCourses();
        return studentProgress;
    }
}

function calculateProgressFromCourses() {
    const totalCourses = enrolledCourses.length;
    const completedCourses = enrolledCourses.filter(course => course.status === 'completed').length;
    const overallProgress = totalCourses > 0 ? Math.round((completedCourses / totalCourses) * 100) : 0;
    
    return {
        totalCourses,
        completedCourses,
        overallProgress,
        totalExercises: totalCourses * 5, // Estimate
        completedExercises: completedCourses * 5, // Estimate
        labSessions: totalCourses * 2 // Estimate
    };
}

// Dashboard data display functions
function updateDashboardMetrics() {
    const metrics = {
        enrolledCourses: enrolledCourses.length,
        completedCourses: studentProgress.completedCourses || 0,
        overallProgress: studentProgress.overallProgress || 0,
        labSessions: studentProgress.labSessions || 0
    };
    
    // Update dashboard metrics
    updateElement('dashboardEnrolledCourses', metrics.enrolledCourses);
    updateElement('dashboardCompletedCourses', metrics.completedCourses);
    updateElement('dashboardOverallProgress', `${metrics.overallProgress}%`);
    updateElement('dashboardLabSessions', metrics.labSessions);
    
    // Update sidebar stats
    updateElement('enrolledCourseCount', metrics.enrolledCourses);
    updateElement('completedCourses', metrics.completedCourses);
    updateElement('totalProgress', `${metrics.overallProgress}%`);
    
    // Update progress section
    updateElement('overallProgressValue', `${metrics.overallProgress}%`);
    updateElement('progressCompletedCourses', metrics.completedCourses);
    updateElement('progressTotalExercises', studentProgress.totalExercises || 0);
    updateElement('progressLabSessions', metrics.labSessions);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function loadDashboardData() {
    displayCurrentCourses();
    displayRecentActivity();
}

function displayCurrentCourses() {
    const container = document.getElementById('current-courses-list');
    const inProgressCourses = enrolledCourses.filter(course => 
        course.status === 'active' || course.status === 'in-progress'
    ).slice(0, 3); // Show max 3 courses
    
    if (!inProgressCourses.length) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book-open"></i>
                <h3>No courses in progress</h3>
                <p>Your enrolled courses will appear here</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = inProgressCourses.map(enrollment => `
        <div class="course-card current-course">
            <div class="course-header">
                <h4>Course ${enrollment.course_id}</h4>
                <div class="course-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${enrollment.progress || 0}%"></div>
                    </div>
                    <span class="progress-text">${enrollment.progress || 0}%</span>
                </div>
            </div>
            <div class="course-actions">
                <button class="btn btn-primary" onclick="viewCourseDetails('${enrollment.course_id}')">
                    <i class="fas fa-play"></i> Continue
                </button>
                <button class="btn btn-secondary" onclick="openLabEnvironment('${enrollment.course_id}')">
                    <i class="fas fa-flask"></i> Lab
                </button>
            </div>
        </div>
    `).join('');
}

function displayRecentActivity() {
    const container = document.getElementById('studentActivityList');
    // This would come from an activity tracking system
    const activities = [
        { type: 'course_progress', message: 'Completed exercise in Python Fundamentals', time: '2 hours ago', icon: 'fa-check-circle' },
        { type: 'lab_session', message: 'Started lab session for Web Development', time: '1 day ago', icon: 'fa-flask' },
        { type: 'course_enrolled', message: 'Enrolled in Data Science Basics', time: '3 days ago', icon: 'fa-user-plus' }
    ];
    
    container.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="fas ${activity.icon}"></i>
            </div>
            <div class="activity-content">
                <p><strong>${activity.message}</strong></p>
                <span class="activity-time">${activity.time}</span>
            </div>
        </div>
    `).join('');
}

function loadCoursesData() {
    displayStudentCourses();
}

function displayStudentCourses() {
    const container = document.getElementById('student-courses-list');
    
    if (!enrolledCourses || enrolledCourses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book"></i>
                <h3>No courses enrolled yet</h3>
                <p>You will see your enrolled courses here once an instructor adds you to a course</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = enrolledCourses.map(enrollment => `
        <div class="course-card enhanced">
            <div class="course-header">
                <h4>Course ${enrollment.course_id}</h4>
                <div class="enrollment-status ${enrollment.status}">
                    ${enrollment.status}
                </div>
            </div>
            <div class="course-progress">
                <div class="progress-info">
                    <span>Progress: ${enrollment.progress || 0}%</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${enrollment.progress || 0}%"></div>
                    </div>
                </div>
            </div>
            <div class="course-meta">
                <span class="enrollment-date">
                    <i class="fas fa-calendar"></i> 
                    Enrolled: ${new Date(enrollment.enrolled_at).toLocaleDateString()}
                </span>
            </div>
            <div class="course-actions">
                <button class="btn btn-primary" onclick="viewCourseDetails('${enrollment.course_id}')">
                    <i class="fas fa-eye"></i> View Course
                </button>
                <button class="btn btn-success" onclick="openLabEnvironment('${enrollment.course_id}')">
                    <i class="fas fa-flask"></i> Access Lab
                </button>
            </div>
        </div>
    `).join('');
}

function loadProgressData() {
    displayCourseProgress();
}

function displayCourseProgress() {
    const container = document.getElementById('courseProgressList');
    
    if (!enrolledCourses.length) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chart-line"></i>
                <h3>No progress data yet</h3>
                <p>Start working on your courses to see progress here</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = enrolledCourses.map(enrollment => `
        <div class="course-progress-card">
            <div class="course-info">
                <h4>Course ${enrollment.course_id}</h4>
                <p class="course-status">Status: ${enrollment.status}</p>
            </div>
            <div class="progress-details">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${enrollment.progress || 0}%"></div>
                </div>
                <div class="progress-stats">
                    <span>Exercises: ${Math.floor((enrollment.progress || 0) / 20)}/5</span>
                    <span>Labs: ${Math.floor((enrollment.progress || 0) / 50)}/2</span>
                    <span>Overall: ${enrollment.progress || 0}%</span>
                </div>
            </div>
        </div>
    `).join('');
}

function loadLabsData() {
    // This loads the labs section content - the main lab environment button
    // No additional loading needed as it's static content
}

// Enhanced lab environment with sandboxing
async function openLabEnvironment(courseId = null) {
    try {
        // Request access to sandboxed lab environment
        const labAccessResponse = await fetch(`${CONFIG.ENDPOINTS.LAB_ACCESS(courseId || 'general')}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: currentUser.id,
                course_id: courseId
            })
        });
        
        if (labAccessResponse.ok) {
            const labAccess = await labAccessResponse.json();
            launchSandboxedLab(labAccess, courseId);
        } else {
            // Fallback to existing lab environment
            launchStandardLab(courseId);
        }
    } catch (error) {
        console.error('Error accessing lab environment:', error);
        // Fallback to existing lab environment
        launchStandardLab(courseId);
    }
}

function launchSandboxedLab(labAccess, courseId) {
    // Create a secure, sandboxed lab environment
    const labWindow = window.open('', '_blank', 'width=1400,height=900,resizable=yes,scrollbars=yes');
    
    if (!labWindow) {
        alert('Popup blocked. Please allow popups for this site to access the lab environment.');
        return;
    }
    
    // Set up the sandboxed lab with security restrictions
    const labUrl = new URL('lab.html', window.location.origin);
    if (courseId) {
        labUrl.searchParams.set('courseId', courseId);
        labUrl.searchParams.set('course', `Course ${courseId}`);
    }
    labUrl.searchParams.set('studentId', currentUser.id);
    labUrl.searchParams.set('sandboxed', 'true');
    labUrl.searchParams.set('sessionId', labAccess.session_id || generateSessionId());
    
    labWindow.location.href = labUrl;
    
    // Store lab session info for tracking
    storeLabSession(courseId, labAccess.session_id || generateSessionId());
}

function launchStandardLab(courseId) {
    // Fallback to existing lab environment
    const labWindow = window.open('', '_blank', 'width=1400,height=900,resizable=yes,scrollbars=yes');
    
    if (!labWindow) {
        alert('Popup blocked. Please allow popups for this site to access the lab environment.');
        return;
    }
    
    const labUrl = new URL('lab.html', window.location.origin);
    if (courseId) {
        labUrl.searchParams.set('courseId', courseId);
        labUrl.searchParams.set('course', `Course ${courseId}`);
    }
    labUrl.searchParams.set('studentId', currentUser.id);
    
    labWindow.location.href = labUrl;
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function storeLabSession(courseId, sessionId) {
    const labSession = {
        courseId,
        sessionId,
        studentId: currentUser.id,
        startTime: new Date().toISOString()
    };
    
    // Store in localStorage for now - in production this would go to the backend
    const sessions = JSON.parse(localStorage.getItem('labSessions') || '[]');
    sessions.push(labSession);
    localStorage.setItem('labSessions', JSON.stringify(sessions));
// Search and filter functions for student courses
function filterStudentCourses() {
    const filter = document.getElementById('courseStatusFilter').value;
    const searchTerm = document.getElementById('courseSearch').value.toLowerCase();
    
    let filteredCourses = enrolledCourses;
    
    // Apply status filter
    if (filter !== 'all') {
        filteredCourses = filteredCourses.filter(course => {
            switch(filter) {
                case 'in-progress':
                    return course.status === 'active' || course.status === 'in-progress';
                case 'completed':
                    return course.status === 'completed';
                case 'not-started':
                    return !course.progress || course.progress === 0;
                default:
                    return true;
            }
        });
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredCourses = filteredCourses.filter(course => 
            course.course_id.toLowerCase().includes(searchTerm) ||
            (course.title && course.title.toLowerCase().includes(searchTerm))
        );
    }
    
    displayFilteredCourses(filteredCourses);
}

function searchStudentCourses() {
    filterStudentCourses(); // Use the same filtering logic
}

function displayFilteredCourses(courses) {
    const container = document.getElementById('student-courses-list');
    
    if (!courses || courses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>No courses found</h3>
                <p>Try adjusting your search or filter criteria</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = courses.map(enrollment => `
        <div class="course-card enhanced">
            <div class="course-header">
                <h4>Course ${enrollment.course_id}</h4>
                <div class="enrollment-status ${enrollment.status}">
                    ${enrollment.status}
                </div>
            </div>
            <div class="course-progress">
                <div class="progress-info">
                    <span>Progress: ${enrollment.progress || 0}%</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${enrollment.progress || 0}%"></div>
                    </div>
                </div>
            </div>
            <div class="course-meta">
                <span class="enrollment-date">
                    <i class="fas fa-calendar"></i> 
                    Enrolled: ${new Date(enrollment.enrolled_at).toLocaleDateString()}
                </span>
            </div>
            <div class="course-actions">
                <button class="btn btn-primary" onclick="viewCourseDetails('${enrollment.course_id}')">
                    <i class="fas fa-eye"></i> View Course
                </button>
                <button class="btn btn-success" onclick="openLabEnvironment('${enrollment.course_id}')">
                    <i class="fas fa-flask"></i> Access Lab
                </button>
            </div>
        </div>
    `).join('');
}

// Load lab environments
async function loadLabEnvironments() {
    try {
        // Get lab environments for all enrolled courses
        const labPromises = enrolledCourses.map(enrollment => 
            fetch(`http://176.9.99.103:8001/student/lab-access/${enrollment.course_id}/${currentUser.id}`)
                .then(response => response.ok ? response.json() : null)
                .catch(() => null)
        );
        
        const labResults = await Promise.all(labPromises);
        labEnvironments = labResults.filter(lab => lab !== null);
        
        displayLabEnvironments(labEnvironments);
    } catch (error) {
        console.error('Error loading lab environments:', error);
        displayEmptyState('lab-environments-list', 'No lab environments available');
    }
}

function displayLabEnvironments(labs) {
    const container = document.getElementById('lab-environments-list');
    
    if (!labs || labs.length === 0) {
        displayEmptyState('lab-environments-list', 'No lab environments available');
        return;
    }
    
    container.innerHTML = labs.map(labAccess => `
        <div class="lab-card">
            <div class="lab-header">
                <h4>${labAccess.lab.name}</h4>
                <div class="lab-status ${labAccess.access_granted ? 'active' : 'inactive'}">
                    ${labAccess.access_granted ? 'Access Granted' : 'Access Denied'}
                </div>
            </div>
            <p class="lab-description">${labAccess.lab.description}</p>
            <div class="lab-specs">
                <div class="spec-item">
                    <i class="fas fa-desktop"></i>
                    <span>Virtual Environment</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-tools"></i>
                    <span>Pre-configured Tools</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-robot"></i>
                    <span>AI Assistant</span>
                </div>
            </div>
            <div class="lab-actions">
                <button class="btn btn-primary" onclick="launchLabEnvironment('${labAccess.lab_id}', '${labAccess.lab.course_id}')" 
                        ${!labAccess.access_granted ? 'disabled' : ''}>
                    <i class="fas fa-play"></i> Launch Lab
                </button>
                <button class="btn btn-secondary" onclick="viewLabDetails('${labAccess.lab_id}')">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </div>
        </div>
    `).join('');
}

// Course interaction
// eslint-disable-next-line no-unused-vars
async function viewCourseDetails(courseId) {
    try {
        // Get course details
        const courseResponse = await fetch(`http://localhost:8004/courses/${courseId}`);
        const slidesResponse = await fetch(`http://176.9.99.103:8001/slides/${courseId}`);
        const exercisesResponse = await fetch(`http://176.9.99.103:8001/exercises/${courseId}`);
        
        const course = courseResponse.ok ? await courseResponse.json() : null;
        const slides = slidesResponse.ok ? await slidesResponse.json() : null;
        const exercises = exercisesResponse.ok ? await exercisesResponse.json() : null;
        
        displayCourseModal(course, slides, exercises);
    } catch (error) {
        console.error('Error loading course details:', error);
        showNotification('Error loading course details', 'error');
    }
}

function displayCourseModal(course, slides, exercises) {
    const modal = document.getElementById('courseModal');
    const title = document.getElementById('modalCourseTitle');
    const content = document.getElementById('modalCourseContent');
    
    title.textContent = course ? course.title : 'Course Details';
    
    let modalContent = '';
    
    if (course) {
        modalContent += `
            <div class="course-info">
                <h4>Course Information</h4>
                <p><strong>Description:</strong> ${course.description}</p>
                <p><strong>Category:</strong> ${course.category}</p>
                <p><strong>Difficulty:</strong> ${course.difficulty_level}</p>
                <p><strong>Duration:</strong> ${course.estimated_duration} hours</p>
            </div>
        `;
    }
    
    if (slides && slides.slides) {
        modalContent += `
            <div class="course-slides">
                <h4>Course Slides</h4>
                <div class="slides-list">
                    ${slides.slides.map(slide => `
                        <div class="slide-item">
                            <h5>${slide.title}</h5>
                            <p>${slide.content}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (exercises && exercises.exercises) {
        modalContent += `
            <div class="course-exercises">
                <h4>Exercises</h4>
                <div class="exercises-list">
                    ${exercises.exercises.map(exercise => `
                        <div class="exercise-item">
                            <h5>${exercise.title}</h5>
                            <p>${exercise.description}</p>
                            <div class="exercise-difficulty">${exercise.difficulty}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    content.innerHTML = modalContent || '<p>No course content available.</p>';
    modal.style.display = 'block';
}

// Lab environment interaction
// eslint-disable-next-line no-unused-vars
async function accessLabEnvironment(courseId) {
    try {
        const response = await fetch(`http://176.9.99.103:8001/student/lab-access/${courseId}/${currentUser.id}`);
        
        if (response.ok) {
            const labAccess = await response.json();
            if (labAccess.access_granted) {
                launchLabEnvironment(labAccess.lab_id, courseId);
            } else {
                showNotification('Access denied to lab environment', 'error');
            }
        } else {
            throw new Error('Failed to access lab environment');
        }
    } catch (error) {
        console.error('Error accessing lab environment:', error);
        showNotification('Error accessing lab environment', 'error');
    }
}

function launchLabEnvironment(labId, courseId) {
    // In a real implementation, this would launch a virtual environment
    // For now, we'll show a simulation
    
    const labAccess = labEnvironments.find(lab => lab.lab_id === labId);
    if (labAccess) {
        displayLabModal(labAccess.lab, courseId);
    } else {
        showNotification('Lab environment not found', 'error');
    }
}

function displayLabModal(lab, courseId) {
    const modal = document.getElementById('labModal');
    const title = document.getElementById('modalLabTitle');
    const content = document.getElementById('modalLabContent');
    
    title.textContent = lab.name;
    
    content.innerHTML = `
        <div class="lab-environment">
            <div class="lab-info">
                <h4>Lab Environment Details</h4>
                <p>${lab.description}</p>
            </div>
            
            <div class="lab-config">
                <h4>Virtual Machine Configuration</h4>
                ${lab.config.virtual_machines ? lab.config.virtual_machines.map(vm => `
                    <div class="vm-config">
                        <h5>${vm.name}</h5>
                        <p><strong>OS:</strong> ${vm.os}</p>
                        <p><strong>CPU:</strong> ${vm.specs.cpu} cores</p>
                        <p><strong>Memory:</strong> ${vm.specs.memory}</p>
                        <p><strong>Storage:</strong> ${vm.specs.storage}</p>
                        <p><strong>Software:</strong> ${vm.software.join(', ')}</p>
                    </div>
                `).join('') : '<p>No VM configuration available</p>'}
            </div>
            
            <div class="lab-terminal">
                <h4>Terminal Simulation</h4>
                <div class="terminal-window">
                    <div class="terminal-header">
                        <span class="terminal-title">student@lab-vm:~$</span>
                    </div>
                    <div class="terminal-content">
                        <div class="terminal-line">Welcome to the ${lab.name}!</div>
                        <div class="terminal-line">Type 'help' for available commands.</div>
                        <div class="terminal-line terminal-prompt">student@lab-vm:~$ <span class="cursor">|</span></div>
                    </div>
                </div>
            </div>
            
            <div class="lab-ai-assistant">
                <h4>AI Assistant</h4>
                <div class="ai-chat">
                    <div class="ai-message">
                        <i class="fas fa-robot"></i>
                        <span>Hi! I'm your lab assistant. Ask me anything about the exercises or concepts!</span>
                    </div>
                    <div class="ai-input">
                        <input type="text" id="aiQuestion" placeholder="Ask a question...">
                        <button onclick="askAI('${courseId}')">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="lab-exercises">
                <h4>Lab Exercises</h4>
                <div id="labExercises">
                    Loading exercises...
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
    
    // Load exercises for this course
    loadLabExercises(courseId);
}

async function loadLabExercises(courseId) {
    try {
        const response = await fetch(`http://176.9.99.103:8001/exercises/${courseId}`);
        if (response.ok) {
            const exercises = await response.json();
            displayLabExercises(exercises.exercises);
        }
    } catch (error) {
        console.error('Error loading lab exercises:', error);
        document.getElementById('labExercises').innerHTML = '<p>Error loading exercises</p>';
    }
}

function displayLabExercises(exercises) {
    const container = document.getElementById('labExercises');
    
    if (!exercises || exercises.length === 0) {
        container.innerHTML = '<p>No exercises available for this lab</p>';
        return;
    }
    
    container.innerHTML = exercises.map(exercise => `
        <div class="exercise-card">
            <h5>${exercise.title}</h5>
            <p>${exercise.description}</p>
            <div class="exercise-instructions">
                <h6>Instructions:</h6>
                <ol>
                    ${exercise.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                </ol>
            </div>
            <div class="exercise-hints">
                <h6>Hints:</h6>
                <ul>
                    ${exercise.hints.map(hint => `<li>${hint}</li>`).join('')}
                </ul>
            </div>
            <div class="exercise-expected">
                <h6>Expected Output:</h6>
                <p>${exercise.expected_output}</p>
            </div>
        </div>
    `).join('');
}

// eslint-disable-next-line no-unused-vars
async function askAI(courseId) {
    const input = document.getElementById('aiQuestion');
    const question = input.value.trim();
    
    if (!question) return;
    
    try {
        const response = await fetch('http://176.9.99.103:8001/ai-assistant/help', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                course_id: courseId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayAIResponse(question, result.response);
        } else {
            throw new Error('Failed to get AI response');
        }
    } catch (error) {
        console.error('Error asking AI:', error);
        showNotification('Error getting AI response', 'error');
    }
    
    input.value = '';
}

function displayAIResponse(question, response) {
    const chatContainer = document.querySelector('.ai-chat');
    
    // Add user question
    const userMessage = document.createElement('div');
    userMessage.className = 'user-message';
    userMessage.innerHTML = `<i class="fas fa-user"></i><span>${question}</span>`;
    
    // Add AI response
    const aiMessage = document.createElement('div');
    aiMessage.className = 'ai-message';
    aiMessage.innerHTML = `<i class="fas fa-robot"></i><span>${response}</span>`;
    
    // Insert before input
    const inputDiv = chatContainer.querySelector('.ai-input');
    chatContainer.insertBefore(userMessage, inputDiv);
    chatContainer.insertBefore(aiMessage, inputDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// eslint-disable-next-line no-unused-vars
function viewLabDetails(labId) {
    const labAccess = labEnvironments.find(lab => lab.lab_id === labId);
    if (labAccess) {
        alert(`Lab Details:\n\nName: ${labAccess.lab.name}\nDescription: ${labAccess.lab.description}\nType: ${labAccess.lab.environment_type}`);
    }
}

// Modal management
// eslint-disable-next-line no-unused-vars
function closeModal() {
    document.getElementById('courseModal').style.display = 'none';
}

// eslint-disable-next-line no-unused-vars
function closeLabModal() {
    document.getElementById('labModal').style.display = 'none';
}

// Utility functions
function displayEmptyState(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <h3>${message}</h3>
            <p>Content will appear here when available.</p>
        </div>
    `;
}

function getInitials(name) {
    if (!name) return 'ST';
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function getCurrentUser() {
    try {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
        console.error('Error getting current user:', error);
        return null;
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const courseModal = document.getElementById('courseModal');
    const labModal = document.getElementById('labModal');
    
    if (event.target === courseModal) {
        courseModal.style.display = 'none';
    }
    if (event.target === labModal) {
        labModal.style.display = 'none';
    }
};

// Tab button event delegation
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('tab-button')) {
        const tabName = e.target.textContent.trim().toLowerCase()
            .replace(/\s+/g, '-')
            .replace('lab-environments', 'lab-environments')
            .replace('enrolled-courses', 'enrolled-courses');
        showTab(tabName);
    }
});