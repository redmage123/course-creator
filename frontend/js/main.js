const API_BASE = 'http://localhost:8004';
const AUTH_API_BASE = 'http://localhost:8000';

// Global state
let currentUser = null;
let authToken = null;

async function loadCourses() {
    try {
        const response = await fetch(`${API_BASE}/courses`);
        const data = await response.json();
        displayCourses(data || []);
    } catch (error) {
        console.error('Error loading courses:', error);
        alert('Failed to load courses');
    }
}

function displayCourses(courses) {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Available Courses</h2>
            <div id="courses-list">
                ${courses.map(course => `
                    <div class="course-card">
                        <h3>${course.name}</h3>
                        <p>${course.description}</p>
                        <button onclick="viewCourse(${course.id})">View Course</button>
                    </div>
                `).join('')}
            </div>
        </section>
    `;
}

async function viewCourse(courseId) {
    try {
        const response = await fetch(`${API_BASE}/courses/${courseId}`);
        const course = await response.json();
        
        const main = document.getElementById('main-content');
        main.innerHTML = `
            <section>
                <h2>${course.name}</h2>
                <p>${course.description}</p>
                <p>Instructor: ${course.instructor}</p>
                <p>Created: ${new Date(course.created_at).toLocaleDateString()}</p>
                <button onclick="loadCourses()">Back to Courses</button>
            </section>
        `;
    } catch (error) {
        console.error('Error loading course:', error);
        alert('Failed to load course details');
    }
}

function showCreateCourse() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Create New Course</h2>
            <form id="create-course-form">
                <div>
                    <label for="course-name">Course Name:</label>
                    <input type="text" id="course-name" name="name" required>
                </div>
                <div>
                    <label for="course-description">Description:</label>
                    <textarea id="course-description" name="description" required></textarea>
                </div>
                <div>
                    <label for="course-instructor">Instructor:</label>
                    <input type="text" id="course-instructor" name="instructor" required>
                </div>
                <div>
                    <button type="submit">Create Course</button>
                    <button type="button" onclick="showHome()">Cancel</button>
                </div>
            </form>
        </section>
    `;
    
    document.getElementById('create-course-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const courseData = {
            name: formData.get('name'),
            description: formData.get('description'),
            instructor: formData.get('instructor')
        };
        
        try {
            const response = await fetch(`${API_BASE}/courses`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(courseData)
            });
            
            if (response.ok) {
                alert('Course created successfully!');
                loadCourses();
            } else {
                alert('Failed to create course');
            }
        } catch (error) {
            console.error('Error creating course:', error);
            alert('Failed to create course');
        }
    });
}

function showHome() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section id="home">
            <h2>Welcome to Course Creator</h2>
            <p>Create and manage online courses with AI assistance.</p>
            <button onclick="loadCourses()">View Courses</button>
        </section>
    `;
}

function showLogin() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Login</h2>
            <form id="login-form">
                <div>
                    <label for="login-email">Email:</label>
                    <input type="email" id="login-email" name="username" required>
                </div>
                <div>
                    <label for="login-password">Password:</label>
                    <input type="password" id="login-password" name="password" required>
                </div>
                <div>
                    <button type="submit">Login</button>
                    <button type="button" onclick="showHome()">Cancel</button>
                </div>
            </form>
        </section>
    `;
    
    document.getElementById('login-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        
        try {
            const response = await fetch(`${AUTH_API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(formData)
            });
            
            if (response.ok) {
                const data = await response.json();
                authToken = data.access_token;
                currentUser = { email: formData.get('username') };
                localStorage.setItem('authToken', authToken);
                localStorage.setItem('userEmail', formData.get('username'));
                alert('Login successful!');
                showHome();
                updateNavigation();
            } else {
                alert('Login failed');
            }
        } catch (error) {
            console.error('Error logging in:', error);
            alert('Login failed');
        }
    });
}

function showRegister() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Register</h2>
            <form id="register-form">
                <div>
                    <label for="register-email">Email:</label>
                    <input type="email" id="register-email" name="email" required>
                </div>
                <div>
                    <label for="register-name">Full Name:</label>
                    <input type="text" id="register-name" name="full_name">
                </div>
                <div>
                    <label for="register-password">Password:</label>
                    <input type="password" id="register-password" name="password" required>
                </div>
                <div>
                    <button type="submit">Register</button>
                    <button type="button" onclick="showHome()">Cancel</button>
                </div>
            </form>
        </section>
    `;
    
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const userData = {
            email: formData.get('email'),
            full_name: formData.get('full_name'),
            password: formData.get('password')
        };
        
        try {
            const response = await fetch(`${AUTH_API_BASE}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            if (response.ok) {
                alert('Registration successful! Please login.');
                showLogin();
            } else {
                alert('Registration failed');
            }
        } catch (error) {
            console.error('Error registering:', error);
            alert('Registration failed');
        }
    });
}

function showProfile() {
    if (!authToken) {
        alert('Please login first');
        showLogin();
        return;
    }
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>User Profile</h2>
            <p><strong>Email:</strong> ${currentUser?.email || 'Unknown'}</p>
            <button onclick="logout()">Logout</button>
            <button onclick="showHome()">Back to Home</button>
        </section>
    `;
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    alert('Logged out successfully');
    showHome();
    updateNavigation();
}

function updateNavigation() {
    // This could update the navigation to show/hide login/logout buttons
    // For now, just refresh the current view
}

function checkAuth() {
    // Check if user was previously logged in
    const savedToken = localStorage.getItem('authToken');
    const savedEmail = localStorage.getItem('userEmail');
    if (savedToken && savedEmail) {
        authToken = savedToken;
        currentUser = { email: savedEmail };
    }
}

// Handle navigation
function handleNavigation() {
    const hash = window.location.hash;
    switch(hash) {
        case '#courses':
            loadCourses();
            break;
        case '#create':
            showCreateCourse();
            break;
        case '#login':
            showLogin();
            break;
        case '#register':
            showRegister();
            break;
        case '#profile':
            showProfile();
            break;
        case '#home':
        default:
            showHome();
            break;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Course Creator Platform loaded');
    checkAuth();
    handleNavigation();
});

window.addEventListener('hashchange', handleNavigation);