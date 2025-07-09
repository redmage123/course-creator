// Student Dashboard JavaScript

let enrolledCourses = [];
let labEnvironments = [];
let currentUser = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadEnrolledCourses();
    loadLabEnvironments();
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
}

function updateUserDisplay() {
    const userName = document.querySelector('.user-name');
    const avatarInitials = document.querySelector('.avatar-initials');
    
    if (currentUser) {
        userName.textContent = currentUser.full_name || 'Student';
        avatarInitials.textContent = getInitials(currentUser.full_name || 'Student');
    }
}

// Tab management
function showTab(tabName) {
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
    event.target.classList.add('active');
}

// Load enrolled courses
async function loadEnrolledCourses() {
    try {
        const response = await fetch(`http://localhost:8004/student/my-courses/${currentUser.id}`);
        
        if (response.ok) {
            const result = await response.json();
            enrolledCourses = result.enrollments || [];
            displayEnrolledCourses(enrolledCourses);
        } else {
            throw new Error('Failed to load enrolled courses');
        }
    } catch (error) {
        console.error('Error loading enrolled courses:', error);
        displayEmptyState('enrolled-courses-list', 'No courses enrolled yet');
    }
}

function displayEnrolledCourses(courses) {
    const container = document.getElementById('enrolled-courses-list');
    
    if (!courses || courses.length === 0) {
        displayEmptyState('enrolled-courses-list', 'No courses enrolled yet');
        return;
    }
    
    container.innerHTML = courses.map(enrollment => `
        <div class="course-card">
            <div class="course-header">
                <h4>Course ${enrollment.course_id}</h4>
                <div class="enrollment-status ${enrollment.status}">
                    ${enrollment.status}
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
                <button class="btn btn-success" onclick="accessLabEnvironment('${enrollment.course_id}')">
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
            fetch(`http://localhost:8001/student/lab-access/${enrollment.course_id}/${currentUser.id}`)
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
        const slidesResponse = await fetch(`http://localhost:8001/slides/${courseId}`);
        const exercisesResponse = await fetch(`http://localhost:8001/exercises/${courseId}`);
        
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
        const response = await fetch(`http://localhost:8001/student/lab-access/${courseId}/${currentUser.id}`);
        
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
        const response = await fetch(`http://localhost:8001/exercises/${courseId}`);
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
        const response = await fetch('http://localhost:8001/ai-assistant/help', {
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