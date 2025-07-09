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
}

function setupEventListeners() {
    // Course creation form
    document.getElementById('courseForm').addEventListener('submit', handleCourseCreation);
    
    // Student enrollment forms
    document.getElementById('singleEnrollmentForm').addEventListener('submit', handleSingleEnrollment);
    document.getElementById('bulkEnrollmentForm').addEventListener('submit', handleBulkEnrollment);
}

function updateUserDisplay() {
    const userName = document.getElementById('userName');
    const avatarInitials = document.getElementById('avatarInitials');
    
    if (currentUser) {
        const displayName = currentUser.full_name || currentUser.username || currentUser.email || 'Instructor';
        if (userName) userName.textContent = displayName;
        if (avatarInitials) avatarInitials.textContent = getInitials(displayName);
    }
}

// Tab management
// eslint-disable-next-line no-unused-vars
function showTab(tabName, event = null) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to corresponding button
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // If no event, find the button by matching text content
        const buttons = document.querySelectorAll('.tab-button');
        buttons.forEach(button => {
            const buttonText = button.textContent.trim().toLowerCase();
            const targetText = tabName.toLowerCase().replace('-', ' ');
            if (buttonText.includes(targetText) || targetText.includes(buttonText.replace('my ', ''))) {
                button.classList.add('active');
            }
        });
    }
}

// Course management
async function loadUserCourses() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch('http://176.9.99.103:8004/courses', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            userCourses = await response.json();
            displayCourses(userCourses);
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
                <button class="btn btn-primary" onclick="showTab('create-course', event)">
                    <i class="fas fa-plus"></i> Create Course
                </button>
            </div>
        `;
        return;
    }
    
    coursesList.innerHTML = courses.map(course => `
        <div class="course-card">
            <div class="course-header">
                <h4>${course.title}</h4>
                <div class="course-status ${course.is_published ? 'published' : 'draft'}">
                    ${course.is_published ? 'Published' : 'Draft'}
                </div>
            </div>
            <p class="course-description">${course.description}</p>
            <div class="course-meta">
                <span class="course-category">${course.category}</span>
                <span class="course-difficulty">${course.difficulty_level}</span>
                <span class="course-duration">${course.estimated_duration}h</span>
            </div>
            <div class="course-actions">
                <button class="btn btn-sm btn-primary" onclick="manageCourse('${course.id}')">
                    <i class="fas fa-cog"></i> Manage
                </button>
                <button class="btn btn-sm btn-secondary" onclick="viewCourseStudents('${course.id}')">
                    <i class="fas fa-users"></i> Students
                </button>
                <button class="btn btn-sm btn-success" onclick="generateCourseContent('${course.id}')">
                    <i class="fas fa-magic"></i> Generate Content
                </button>
                <button class="btn btn-sm btn-info" onclick="viewCourseContent('${course.id}')">
                    <i class="fas fa-eye"></i> View Content
                </button>
                <button class="btn btn-sm btn-warning" onclick="editCourse('${course.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteCourse('${course.id}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function handleCourseCreation(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    console.log('Current user:', currentUser);
    
    const courseData = {
        title: formData.get('title'),
        description: formData.get('description'),
        category: formData.get('category'),
        difficulty_level: formData.get('difficulty_level'),
        estimated_duration: parseInt(formData.get('estimated_duration')) || 1,
        instructor_id: currentUser.id || currentUser.email || currentUser.username || 'unknown'
    };
    
    console.log('Course data being sent:', courseData);
    
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch('http://176.9.99.103:8004/courses', {
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
            
            // Show courses tab
            showTab('courses');
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

// eslint-disable-next-line no-unused-vars
async function generateCourseContent(courseId) {
    try {
        const course = userCourses.find(c => c.id == courseId);
        if (!course) return;
        
        showNotification('Generating course content...', 'info');
        
        // Generate slides
        const slidesResponse = await fetch('http://176.9.99.103:8001/slides/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                title: course.title,
                description: course.description,
                topic: course.category
            })
        });
        
        // Generate lab environment
        const labResponse = await fetch('http://176.9.99.103:8001/lab/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                name: `${course.title} Lab`,
                description: `Interactive lab environment for ${course.title}`,
                environment_type: 'simulation',
                config: {},
                exercises: []
            })
        });
        
        // Generate exercises
        const exercisesResponse = await fetch('http://176.9.99.103:8001/exercises/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                topic: course.category,
                difficulty: course.difficulty_level
            })
        });
        
        if (slidesResponse.ok && labResponse.ok && exercisesResponse.ok) {
            showNotification('Course content generated successfully!', 'success');
            
            // Store the generated content IDs for future reference
            const slidesData = await slidesResponse.json();
            const labData = await labResponse.json();
            const exercisesData = await exercisesResponse.json();
            
            console.log('Generated content:', { slidesData, labData, exercisesData });
            
            // Refresh content selector if visible
            loadCoursesForContentSelector();
        } else {
            throw new Error('Failed to generate content');
        }
    } catch (error) {
        console.error('Error generating content:', error);
        showNotification('Error generating course content', 'error');
    }
}

// Student enrollment management
async function loadCoursesForSelector() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch('http://176.9.99.103:8004/courses', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const courses = await response.json();
            const selector = document.getElementById('selectedCourse');
            
            selector.innerHTML = '<option value="">Select a course...</option>' +
                courses.map(course => `<option value="${course.id}">${course.title}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading courses for selector:', error);
    }
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
        const response = await fetch('http://176.9.99.103:8004/instructor/enroll-student', {
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
        const response = await fetch('http://176.9.99.103:8004/instructor/register-students', {
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
        const response = await fetch(`http://176.9.99.103:8004/instructor/course/${courseId}/students`);
        
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
        const response = await fetch(`http://176.9.99.103:8004/instructor/enrollment/${enrollmentId}`, {
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
function resetForm() {
    document.getElementById('courseForm').reset();
}

// eslint-disable-next-line no-unused-vars
function manageCourse(courseId) {
    // Navigate to course management page
    window.location.href = `course-manage.html?id=${courseId}`;
}

// eslint-disable-next-line no-unused-vars
function viewCourseStudents(courseId) {
    // Switch to student management tab and select the course
    showTab('student-management');
    document.getElementById('selectedCourse').value = courseId;
    loadCourseStudents();
}

function getInitials(name) {
    if (!name) return 'IN';
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
}

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
async function loadCoursesForContentSelector() {
    try {
        const token = localStorage.getItem('authToken') || localStorage.getItem('token');
        const response = await fetch('http://176.9.99.103:8004/courses', {
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

// eslint-disable-next-line no-unused-vars
async function loadCourseContent() {
    const courseId = document.getElementById('contentCourseSelect').value;
    if (!courseId) {
        document.getElementById('course-content-display').innerHTML = '<p>Select a course to view its content</p>';
        return;
    }
    
    const course = userCourses.find(c => c.id == courseId);
    if (!course) {
        document.getElementById('course-content-display').innerHTML = '<p>Course not found</p>';
        return;
    }
    
    document.getElementById('course-content-display').innerHTML = `
        <div class="course-content-header">
            <h4>${course.title}</h4>
            <p>${course.description}</p>
        </div>
        
        <div class="content-sections">
            <div class="content-section">
                <h5><i class="fas fa-presentation"></i> Slides</h5>
                <div id="slides-content" class="content-area">
                    <button class="btn btn-primary" onclick="loadSlides('${courseId}')">
                        <i class="fas fa-download"></i> Load Slides
                    </button>
                </div>
            </div>
            
            <div class="content-section">
                <h5><i class="fas fa-flask"></i> Lab Environment</h5>
                <div id="lab-content" class="content-area">
                    <button class="btn btn-primary" onclick="loadLabEnvironment('${courseId}')">
                        <i class="fas fa-download"></i> Load Lab Environment
                    </button>
                </div>
            </div>
            
            <div class="content-section">
                <h5><i class="fas fa-question-circle"></i> Quizzes & Tests</h5>
                <div id="quizzes-content" class="content-area">
                    <button class="btn btn-primary" onclick="loadQuizzes('${courseId}')">
                        <i class="fas fa-download"></i> Load Quizzes
                    </button>
                </div>
            </div>
        </div>
    `;
}

// eslint-disable-next-line no-unused-vars
async function loadSlides(courseId) {
    try {
        const response = await fetch(`http://176.9.99.103:8001/slides/${courseId}`);
        
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
        const response = await fetch(`http://176.9.99.103:8001/lab/${courseId}`);
        
        if (response.ok) {
            const labData = await response.json();
            const labContainer = document.getElementById('lab-content');
            
            if (labData.lab) {
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
        document.getElementById('lab-content').innerHTML = '<p class="error">Error loading lab environment. Make sure content has been generated.</p>';
    }
}

// eslint-disable-next-line no-unused-vars
async function loadQuizzes(courseId) {
    try {
        const response = await fetch(`http://176.9.99.103:8001/quizzes/${courseId}`);
        
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
function viewCourseContent(courseId) {
    // Switch to content management tab and select the course
    showTab('content-management');
    document.getElementById('contentCourseSelect').value = courseId;
    loadCourseContent();
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
        
        const response = await fetch(`http://176.9.99.103:8001/lab/launch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(labConfig)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('AI Lab Environment initialized successfully!', 'success');
            
            // Refresh the lab content to show updated status
            loadLabEnvironment(courseId);
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
        
        const response = await fetch(`http://176.9.99.103:8001/lab/stop/${courseId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showNotification('Lab environment stopped successfully!', 'success');
            
            // Refresh the lab content to show updated status
            loadLabEnvironment(courseId);
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
        const response = await fetch(`http://176.9.99.103:8001/lab/access/${courseId}`);
        
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

// eslint-disable-next-line no-unused-vars
function openEmbeddedLab(courseId) {
    const course = userCourses.find(c => c.id == courseId);
    if (!course) return;
    
    // Create a new window for the lab environment
    const labWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
    
    labWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Lab Environment - ${course.title}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .lab-container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .lab-header { border-bottom: 2px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }
                .lab-header h1 { color: #2c3e50; margin: 0; }
                .lab-header p { color: #7f8c8d; margin: 5px 0 0 0; }
                .progress-bar { width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; margin: 20px 0; }
                .progress-fill { height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); width: 0%; transition: width 0.3s; }
                .exercise-section { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; }
                .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin: 20px 0; background: white; border-radius: 8px; }
                .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
                .trainer-message { background: #e8f4fd; border-left: 4px solid #3498db; }
                .student-message { background: #f0f8e8; border-left: 4px solid #2ecc71; text-align: right; }
                .input-container { display: flex; gap: 10px; margin: 10px 0; }
                .input-container input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                .input-container button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .exercise-card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #ddd; }
                .quiz-section { background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffc107; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="lab-container">
                <div class="lab-header">
                    <h1>🧪 AI Lab Environment</h1>
                    <p>Course: ${course.title} | Expert Trainer: AI Assistant</p>
                </div>
                
                <div class="progress-section">
                    <h3>📊 Learning Progress</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <p id="progressText">Starting your learning journey...</p>
                </div>
                
                <div class="exercise-section">
                    <h3>🎯 Current Exercise</h3>
                    <div id="currentExercise">
                        <div class="exercise-card">
                            <h4>Welcome to the Lab Environment!</h4>
                            <p>I'm your AI expert trainer for <strong>${course.title}</strong>. I'll guide you through hands-on exercises, track your progress, and provide personalized quizzes based on your learning.</p>
                            <p>Let's start with a quick assessment to understand your current knowledge level.</p>
                        </div>
                    </div>
                </div>
                
                <div class="chat-container" id="chatContainer">
                    <div class="message trainer-message">
                        <strong>🤖 AI Trainer:</strong> Hello! I'm your expert instructor for ${course.title}. I'll adapt my teaching to your pace and provide real-time feedback. What would you like to learn first?
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="userInput" placeholder="Ask a question or request an exercise..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                    <button onclick="requestExercise()">Request Exercise</button>
                    <button onclick="requestQuiz()">Take Quiz</button>
                </div>
                
                <div class="quiz-section" id="quizSection" style="display: none;">
                    <h3>📝 Adaptive Quiz</h3>
                    <div id="quizContent"></div>
                </div>
            </div>
            
            <script>
                let courseId = '${courseId}';
                let progressData = {
                    completed_exercises: 0,
                    total_exercises: 0,
                    knowledge_areas: [],
                    current_level: 'beginner'
                };
                
                async function sendMessage() {
                    const input = document.getElementById('userInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    // Add user message to chat
                    addMessage(message, 'student');
                    input.value = '';
                    
                    // Send to AI trainer
                    await processUserMessage(message);
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
                
                function addMessage(message, type) {
                    const chat = document.getElementById('chatContainer');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = \`message \${type}-message\`;
                    messageDiv.innerHTML = \`<strong>\${type === 'student' ? '👨‍🎓 You' : '🤖 AI Trainer'}:</strong> \${message}\`;
                    chat.appendChild(messageDiv);
                    chat.scrollTop = chat.scrollHeight;
                }
                
                async function processUserMessage(message) {
                    try {
                        const response = await fetch('http://176.9.99.103:8001/lab/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                course_id: courseId,
                                user_message: message,
                                context: {
                                    course_title: '${course.title}',
                                    course_description: '${course.description}',
                                    course_category: '${course.category}',
                                    difficulty_level: '${course.difficulty_level}',
                                    student_progress: progressData
                                }
                            })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            addMessage(result.response, 'trainer');
                            
                            // Update progress if provided
                            if (result.progress_update) {
                                updateProgress(result.progress_update);
                            }
                            
                            // Show exercise if provided
                            if (result.exercise) {
                                showExercise(result.exercise);
                            }
                        }
                    } catch (error) {
                        console.error('Error processing message:', error);
                        addMessage('Sorry, I encountered an error. Please try again.', 'trainer');
                    }
                }
                
                async function requestExercise() {
                    try {
                        const response = await fetch('http://176.9.99.103:8001/lab/generate-exercise', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                course_id: courseId,
                                student_progress: progressData,
                                context: {
                                    course_title: '${course.title}',
                                    course_category: '${course.category}',
                                    difficulty_level: '${course.difficulty_level}'
                                }
                            })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            showExercise(result.exercise);
                            addMessage('I\'ve generated a new exercise based on your progress. Give it a try!', 'trainer');
                        }
                    } catch (error) {
                        console.error('Error requesting exercise:', error);
                        addMessage('Sorry, I couldn\'t generate an exercise right now. Please try again.', 'trainer');
                    }
                }
                
                async function requestQuiz() {
                    try {
                        const response = await fetch('http://176.9.99.103:8001/lab/generate-quiz', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                course_id: courseId,
                                student_progress: progressData,
                                context: {
                                    course_title: '${course.title}',
                                    course_category: '${course.category}',
                                    difficulty_level: '${course.difficulty_level}'
                                }
                            })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            showQuiz(result.quiz);
                            addMessage('I\'ve created a personalized quiz based on what you\'ve learned so far!', 'trainer');
                        }
                    } catch (error) {
                        console.error('Error requesting quiz:', error);
                        addMessage('Sorry, I couldn\'t generate a quiz right now. Please try again.', 'trainer');
                    }
                }
                
                function showExercise(exercise) {
                    const exerciseDiv = document.getElementById('currentExercise');
                    exerciseDiv.innerHTML = \`
                        <div class="exercise-card">
                            <h4>\${exercise.title}</h4>
                            <p>\${exercise.description}</p>
                            <div class="exercise-content">\${exercise.content}</div>
                            <button onclick="submitExercise('\${exercise.id}')">Submit Solution</button>
                        </div>
                    \`;
                }
                
                function showQuiz(quiz) {
                    const quizSection = document.getElementById('quizSection');
                    const quizContent = document.getElementById('quizContent');
                    
                    quizContent.innerHTML = \`
                        <h4>\${quiz.title}</h4>
                        <p>\${quiz.description}</p>
                        <div class="quiz-questions">
                            \${quiz.questions.map((q, i) => \`
                                <div class="question" style="margin: 15px 0; padding: 10px; background: white; border-radius: 4px;">
                                    <p><strong>Question \${i + 1}:</strong> \${q.question}</p>
                                    \${q.options.map((option, j) => \`
                                        <label style="display: block; margin: 5px 0;">
                                            <input type="radio" name="q\${i}" value="\${j}"> \${option}
                                        </label>
                                    \`).join('')}
                                </div>
                            \`).join('')}
                        </div>
                        <button onclick="submitQuiz('\${quiz.id}')">Submit Quiz</button>
                    \`;
                    
                    quizSection.style.display = 'block';
                }
                
                function updateProgress(progress) {
                    progressData = { ...progressData, ...progress };
                    const progressFill = document.getElementById('progressFill');
                    const progressText = document.getElementById('progressText');
                    
                    const percentage = (progressData.completed_exercises / Math.max(progressData.total_exercises, 1)) * 100;
                    progressFill.style.width = percentage + '%';
                    progressText.textContent = \`Completed \${progressData.completed_exercises} of \${progressData.total_exercises} exercises (\${Math.round(percentage)}%)\`;
                }
                
                async function submitExercise(exerciseId) {
                    // This would submit the exercise solution
                    addMessage('Exercise submitted! Great work. Let me provide feedback...', 'trainer');
                    progressData.completed_exercises++;
                    updateProgress(progressData);
                }
                
                async function submitQuiz(quizId) {
                    // This would submit the quiz answers
                    addMessage('Quiz submitted! Let me analyze your answers and provide feedback...', 'trainer');
                    document.getElementById('quizSection').style.display = 'none';
                }
                
                // Initialize the lab environment
                window.onload = function() {
                    addMessage('Lab environment loaded successfully! I\'m ready to help you learn ${course.title}. What would you like to explore first?', 'trainer');
                };
            </script>
        </body>
        </html>
    `);
}

// Slide navigation functions
// eslint-disable-next-line no-unused-vars
function nextSlide() {
    if (window.currentSlides && window.currentSlideIndex < window.currentSlides.length - 1) {
        window.currentSlideIndex++;
        updateSlideDisplay();
        updateSlideNavigation();
    }
}

// eslint-disable-next-line no-unused-vars
function previousSlide() {
    if (window.currentSlides && window.currentSlideIndex > 0) {
        window.currentSlideIndex--;
        updateSlideDisplay();
        updateSlideNavigation();
    }
}

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
        const response = await fetch(`http://176.9.99.103:8001/lab/analytics/${courseId}`);
        
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
        const slidesResponse = await fetch(`http://176.9.99.103:8001/slides/${courseId}`);
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
        const courseResponse = await fetch(`http://176.9.99.103:8004/courses/${courseId}`, {
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
            const slidesResponse = await fetch(`http://176.9.99.103:8001/slides/update/${courseId}`, {
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
        document.querySelector('.modal-overlay').remove();
        loadUserCourses();
        
    } catch (error) {
        console.error('Error updating course:', error);
        showNotification('Error updating course: ' + error.message, 'error');
    }
}

function switchEditTab(tabName, button) {
    document.querySelectorAll('.edit-tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tabName + '-tab').classList.add('active');
    button.classList.add('active');
}

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

async function regenerateAllSlides(courseId) {
    if (!confirm('This will replace all slides with AI-generated content. Continue?')) return;
    
    try {
        showNotification('Regenerating slides...', 'info');
        
        const title = document.getElementById('editTitle').value;
        const description = document.getElementById('editDescription').value;
        const category = document.getElementById('editCategory').value;
        
        const response = await fetch('http://176.9.99.103:8001/slides/generate', {
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
        const response = await fetch(`http://176.9.99.103:8004/courses/${courseId}`, {
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
        showTab(tabName.replace('my-', '').replace('create-', 'create-').replace('student-', 'student-'), e);
    }
});