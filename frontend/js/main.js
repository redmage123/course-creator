const AUTH_API_BASE = CONFIG.API_URLS.USER_MANAGEMENT;

// Global state
let currentUser = null;
let authToken = null;

// Modal functions - defined early for onclick handlers
// eslint-disable-next-line no-unused-vars
function showLoginModal() {
    showLogin();
}

// eslint-disable-next-line no-unused-vars
function showRegisterModal() {
    showRegister();
}

// Toggle account dropdown - make it global
window.toggleAccountDropdown = function() {
    console.log('Dropdown clicked!');
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        // Get computed style to check actual display
        const computedStyle = window.getComputedStyle(accountMenu);
        console.log('Current display:', computedStyle.display);
        console.log('Current visibility:', computedStyle.visibility);
        
        // Force complete override of all potential hiding styles
        if (accountMenu.style.display === 'block' && accountMenu.style.visibility === 'visible') {
            accountMenu.style.display = 'none';
            accountMenu.style.visibility = 'hidden';
            console.log('Set to none/hidden');
        } else {
            // Force all possible styles to make it visible
            accountMenu.style.display = 'block';
            accountMenu.style.visibility = 'visible';
            accountMenu.style.opacity = '1';
            accountMenu.style.position = 'absolute';
            accountMenu.style.top = '100%';
            accountMenu.style.right = '0';
            accountMenu.style.zIndex = '9999';
            accountMenu.style.background = 'white';
            accountMenu.style.border = '1px solid #ccc';
            accountMenu.style.borderRadius = '8px';
            accountMenu.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            accountMenu.style.minWidth = '200px';
            accountMenu.style.padding = '0.5rem 0';
            accountMenu.style.marginTop = '5px';
            accountMenu.style.left = 'auto';
            accountMenu.style.transform = 'none';
            console.log('Set to block/visible with full styling');
        }
    } else {
        alert('accountMenu not found');
    }
};

// Close account dropdown
// eslint-disable-next-line no-unused-vars
function closeAccountDropdown() {
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.remove('show');
    }
}

// Logout function - make it global
window.logout = async function() {
    try {
        // Call server logout endpoint to invalidate session
        if (authToken) {
            const response = await fetch(`${AUTH_API_BASE}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log('Server session invalidated successfully');
            } else {
                console.warn('Failed to invalidate server session, continuing with client logout');
            }
        }
    } catch (error) {
        console.error('Error during server logout:', error);
        // Continue with client-side logout even if server logout fails
    }
    
    // Stop idle monitoring
    stopIdleMonitoring();
    
    // Clear client-side data
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('currentUser');
    alert('Logged out successfully');
    
    // If we're on a dashboard page, redirect to home
    if (window.location.pathname.includes('dashboard') || window.location.pathname.includes('admin')) {
        window.location.href = 'index.html';
    } else {
        showHome();
        updateAccountSection();
        updateNavigation();
        setupAccountDropdownListener();
    }
};

// Function references for onclick handlers will be resolved when functions are defined later



function showHome() {
    const main = document.getElementById('main-content');
    if (main) {
        if (currentUser && authToken) {
            // User is logged in - show welcome message (dashboard link is now in top menu)
            main.innerHTML = `
                <section id="home">
                    <h2>Welcome back, ${currentUser.full_name || currentUser.username || currentUser.email}!</h2>
                    <p>Ready to continue your work on the Course Creator platform.</p>
                    <p>Use the Dashboard link in the top menu to access your workspace.</p>
                </section>
            `;
        } else {
            // User is not logged in - show welcome message and login/register options
            main.innerHTML = `
                <section id="home">
                    <h2>Welcome to Course Creator</h2>
                    <p>Create and manage online courses with AI assistance.</p>
                    <div class="auth-actions">
                        <button onclick="showLogin()" class="btn btn-primary">Login</button>
                        <button onclick="showRegister()" class="btn btn-secondary">Register</button>
                    </div>
                </section>
            `;
        }
    }
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
                    <div style="position: relative;">
                        <input type="password" id="login-password" name="password" required>
                        <button type="button" onclick="togglePasswordVisibility('login-password', 'toggle-login-password')" id="toggle-login-password" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <button type="submit">Login</button>
                    <button type="button" onclick="showHome()">Cancel</button>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <a href="#" onclick="showPasswordReset()" style="color: #007bff; text-decoration: none; font-size: 14px;">Forgot Password?</a>
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
                localStorage.setItem('authToken', authToken);
                localStorage.setItem('userEmail', formData.get('username'));
                
                // Start idle monitoring
                startIdleMonitoring();
                
                // Get user profile to check role
                try {
                    const profileResponse = await fetch(`${AUTH_API_BASE}/users/profile`, {
                        headers: {
                            'Authorization': `Bearer ${data.access_token}`
                        }
                    });
                    
                    if (profileResponse.ok) {
                        const profileData = await profileResponse.json();
                        currentUser = profileData.user || { email: formData.get('username') };
                        
                        // Store user data in localStorage
                        localStorage.setItem('currentUser', JSON.stringify(currentUser));
                        
                        // Redirect based on role
                        if (currentUser.role === 'admin') {
                            window.location.href = 'admin.html';
                            return;
                        } else if (currentUser.role === 'instructor') {
                            alert('Login successful! Redirecting to instructor dashboard...');
                            window.location.href = 'instructor-dashboard.html';
                            return;
                        } else if (currentUser.role === 'student') {
                            alert('Login successful! Redirecting to student dashboard...');
                            window.location.href = 'student-dashboard.html';
                            return;
                        } else {
                            alert('Login successful!');
                            showHome();
                            updateAccountSection();
                            updateNavigation();
                            setupAccountDropdownListener();
                        }
                    } else {
                        currentUser = { email: formData.get('username') };
                        localStorage.setItem('currentUser', JSON.stringify(currentUser));
                        alert('Login successful!');
                        showHome();
                        updateAccountSection();
                        updateNavigation();
                        setupAccountDropdownListener();
                    }
                } catch (error) {
                    console.error('Error getting profile:', error);
                    currentUser = { email: formData.get('username') };
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    alert('Login successful!');
                    showHome();
                    updateAccountSection();
                    updateNavigation();
                    setupAccountDropdownListener();
                }
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
                    <input type="text" id="register-name" name="full_name" required>
                </div>
                <div>
                    <label for="register-username">Login Name:</label>
                    <input type="text" id="register-username" name="username" required placeholder="Choose a unique username">
                </div>
                <div>
                    <label for="register-password">Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="register-password" name="password" required>
                        <button type="button" onclick="togglePasswordVisibility('register-password', 'toggle-password-1')" id="toggle-password-1" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <label for="register-password-confirm">Confirm Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="register-password-confirm" name="password_confirm" required>
                        <button type="button" onclick="togglePasswordVisibility('register-password-confirm', 'toggle-password-2')" id="toggle-password-2" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div id="password-match-indicator" style="margin-top: 10px; font-size: 0.9em; font-weight: bold;"></div>
                <div>
                    <button type="submit">Register</button>
                    <button type="button" onclick="showHome()">Cancel</button>
                </div>
            </form>
        </section>
    `;
    
    // Password visibility toggle is handled by onclick attributes in HTML
    
    // Add real-time password matching validation
    setupPasswordMatchValidation();
    
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const password = formData.get('password');
        const passwordConfirm = formData.get('password_confirm');
        
        // Check if passwords match
        if (password !== passwordConfirm) {
            alert('Passwords do not match. Please check your passwords and try again.');
            return;
        }
        
        const userData = {
            email: formData.get('email'),
            full_name: formData.get('full_name'),
            username: formData.get('username'),
            password: password
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
                const errorData = await response.json();
                alert('Registration failed: ' + (errorData.detail || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error registering:', error);
            const errorMessage = error.message || 'Network error - please check if services are running';
            alert('Registration failed: ' + errorMessage + '\n\nPlease try refreshing the page or contact support if the problem persists.');
        }
    });
}

// Password visibility toggle function
// eslint-disable-next-line no-unused-vars
function togglePasswordVisibility(inputId, buttonId) {
    const passwordInput = document.getElementById(inputId);
    const toggleButton = document.getElementById(buttonId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleButton.textContent = '🙈';
        toggleButton.title = 'Hide password';
    } else {
        passwordInput.type = 'password';
        toggleButton.textContent = '👁️';
        toggleButton.title = 'Show password';
    }
}

// Password visibility toggle is handled by onclick attributes in HTML
// No need for additional event listeners

// Password reset functionality
function showPasswordReset() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Reset Password</h2>
            <p>Enter your email address and new password to reset your password.</p>
            <form id="password-reset-form">
                <div>
                    <label for="reset-email">Email:</label>
                    <input type="email" id="reset-email" name="email" required>
                </div>
                <div>
                    <label for="new-password">New Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="new-password" name="new_password" required minlength="6">
                        <button type="button" onclick="togglePasswordVisibility('new-password', 'toggle-new-password')" id="toggle-new-password" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <label for="confirm-password">Confirm New Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="confirm-password" name="confirm_password" required minlength="6">
                        <button type="button" onclick="togglePasswordVisibility('confirm-password', 'toggle-confirm-password')" id="toggle-confirm-password" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <button type="submit">Reset Password</button>
                    <button type="button" onclick="showLogin()">Back to Login</button>
                </div>
            </form>
        </section>
    `;
    
    document.getElementById('password-reset-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');
        
        if (newPassword !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }
        
        try {
            const response = await fetch(CONFIG.ENDPOINTS.RESET_PASSWORD, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formData.get('email'),
                    new_password: newPassword
                })
            });
            
            if (response.ok) {
                alert('Password reset successfully! You can now login with your new password.');
                showLogin();
            } else {
                const errorData = await response.json();
                alert('Password reset failed: ' + (errorData.detail || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error resetting password:', error);
            alert('Password reset failed: Network error - please check if services are running');
        }
    });
}

// Setup password matching validation
function setupPasswordMatchValidation() {
    const passwordInput = document.getElementById('register-password');
    const confirmPasswordInput = document.getElementById('register-password-confirm');
    const indicator = document.getElementById('password-match-indicator');
    
    function checkPasswordMatch() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword.length === 0) {
            indicator.textContent = '';
            indicator.style.color = '';
        } else if (password === confirmPassword) {
            indicator.textContent = '✅ Passwords match';
            indicator.style.color = 'green';
        } else {
            indicator.textContent = '❌ Passwords do not match';
            indicator.style.color = 'red';
        }
    }
    
    passwordInput.addEventListener('input', checkPasswordMatch);
    confirmPasswordInput.addEventListener('input', checkPasswordMatch);
}

function showProfile() {
    if (!authToken) {
        alert('Please login first');
        showLogin();
        return;
    }
    
    // Close dropdown when navigating
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.remove('show');
    }
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>👤 User Profile</h2>
            <div class="profile-info">
                <div class="profile-avatar">
                    <div class="large-avatar">
                        <span>${getInitials(currentUser?.full_name || currentUser?.email)}</span>
                    </div>
                </div>
                <div class="profile-details">
                    <h3>${currentUser?.full_name || 'User'}</h3>
                    <p><strong>Email:</strong> ${currentUser?.email || 'Unknown'}</p>
                    <p><strong>Username:</strong> ${currentUser?.username || 'N/A'}</p>
                    <p><strong>Role:</strong> <span class="role-badge role-${currentUser?.role || 'student'}">${currentUser?.role || 'student'}</span></p>
                    <p><strong>Status:</strong> <span class="status-active">Active</span></p>
                </div>
            </div>
            <div class="profile-actions">
                <button onclick="showSettings()">⚙️ Settings</button>
                <button onclick="showHome()">🏠 Back to Home</button>
            </div>
        </section>
    `;
}

// eslint-disable-next-line no-unused-vars
function showSettings() {
    if (!authToken) {
        alert('Please login first');
        showLogin();
        return;
    }
    
    // Close dropdown when navigating
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.remove('show');
    }
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>⚙️ Account Settings</h2>
            <div class="settings-section">
                <h3>Profile Information</h3>
                <form id="profile-form">
                    <div>
                        <label for="settings-name">Full Name:</label>
                        <input type="text" id="settings-name" value="${currentUser?.full_name || ''}" required>
                    </div>
                    <div>
                        <label for="settings-email">Email:</label>
                        <input type="email" id="settings-email" value="${currentUser?.email || ''}" required>
                    </div>
                    <div>
                        <label for="settings-username">Username:</label>
                        <input type="text" id="settings-username" value="${currentUser?.username || ''}" required>
                    </div>
                    <button type="submit">💾 Save Changes</button>
                </form>
            </div>
            
            <div class="settings-section">
                <h3>Security</h3>
                <button onclick="showChangePassword()">🔒 Change Password</button>
            </div>
            
            <div class="settings-section">
                <h3>Preferences</h3>
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="email-notifications" checked>
                        Email Notifications
                    </label>
                </div>
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="dark-mode">
                        Dark Mode
                    </label>
                </div>
            </div>
            
            <div class="settings-actions">
                <button onclick="showProfile()">👤 Back to Profile</button>
                <button onclick="showHome()">🏠 Back to Home</button>
            </div>
        </section>
    `;
}

// eslint-disable-next-line no-unused-vars
function showHelp() {
    // Close dropdown when navigating
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu) {
        accountMenu.classList.remove('show');
    }
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>❓ Help & Support</h2>
            
            <div class="help-section">
                <h3>Getting Started</h3>
                <ul>
                    <li><strong>Registration:</strong> Create an account to access all features</li>
                    <li><strong>Login:</strong> Use your email and password to sign in</li>
                    <li><strong>Course Creation:</strong> Navigate to "Create Course" to build new courses</li>
                    <li><strong>Course Management:</strong> View and manage your enrolled courses</li>
                </ul>
            </div>
            
            <div class="help-section">
                <h3>User Roles</h3>
                <ul>
                    <li><strong>Student:</strong> Can view and enroll in courses</li>
                    <li><strong>Instructor:</strong> Can create and manage courses</li>
                    <li><strong>Admin:</strong> Full system access and user management</li>
                </ul>
            </div>
            
            <div class="help-section">
                <h3>Frequently Asked Questions</h3>
                <details>
                    <summary>How do I reset my password?</summary>
                    <p>Go to Settings and click "Change Password" to update your password.</p>
                </details>
                <details>
                    <summary>How do I change my profile information?</summary>
                    <p>Click on your account avatar in the top right, then go to Profile → Settings.</p>
                </details>
                <details>
                    <summary>How do I contact support?</summary>
                    <p>Email us at support@courseplatform.com for assistance.</p>
                </details>
            </div>
            
            <div class="help-actions">
                <button onclick="showHome()">🏠 Back to Home</button>
            </div>
        </section>
    `;
}

// eslint-disable-next-line no-unused-vars
function showChangePassword() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>🔒 Change Password</h2>
            <form id="change-password-form">
                <div>
                    <label for="current-password">Current Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="current-password" required>
                        <button type="button" onclick="togglePasswordVisibility('current-password', 'toggle-current')" id="toggle-current" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <label for="new-password">New Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="new-password" required>
                        <button type="button" onclick="togglePasswordVisibility('new-password', 'toggle-new')" id="toggle-new" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div>
                    <label for="confirm-new-password">Confirm New Password:</label>
                    <div style="position: relative;">
                        <input type="password" id="confirm-new-password" required>
                        <button type="button" onclick="togglePasswordVisibility('confirm-new-password', 'toggle-confirm')" id="toggle-confirm" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 14px;">👁️</button>
                    </div>
                </div>
                <div id="password-change-indicator" style="margin-top: 10px; font-size: 0.9em; font-weight: bold;"></div>
                <button type="submit">🔒 Change Password</button>
                <button type="button" onclick="showSettings()">Cancel</button>
            </form>
        </section>
    `;
    
    // Add password matching validation
    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-new-password');
    const indicator = document.getElementById('password-change-indicator');
    
    function checkPasswordMatch() {
        const password = newPassword.value;
        const confirmPass = confirmPassword.value;
        
        if (confirmPass.length === 0) {
            indicator.textContent = '';
            indicator.style.color = '';
        } else if (password === confirmPass) {
            indicator.textContent = '✅ New passwords match';
            indicator.style.color = 'green';
        } else {
            indicator.textContent = '❌ New passwords do not match';
            indicator.style.color = 'red';
        }
    }
    
    newPassword.addEventListener('input', checkPasswordMatch);
    confirmPassword.addEventListener('input', checkPasswordMatch);
}

// Logout function is now defined at the top of the file

function updateNavigation() {
    // Show role-based navigation links
    const adminLink = document.getElementById('admin-link');
    const instructorLink = document.getElementById('instructor-link');
    const studentLink = document.getElementById('student-link');
    
    if (currentUser && authToken) {
        if (currentUser.role === 'admin') {
            if (adminLink) adminLink.style.display = 'inline';
            if (instructorLink) instructorLink.style.display = 'none';
            if (studentLink) studentLink.style.display = 'none';
        } else if (currentUser.role === 'instructor') {
            if (adminLink) adminLink.style.display = 'none';
            if (instructorLink) instructorLink.style.display = 'inline';
            if (studentLink) studentLink.style.display = 'none';
        } else if (currentUser.role === 'student') {
            if (adminLink) adminLink.style.display = 'none';
            if (instructorLink) instructorLink.style.display = 'none';
            if (studentLink) studentLink.style.display = 'inline';
        } else {
            // Default to instructor dashboard for users without specific roles
            if (adminLink) adminLink.style.display = 'none';
            if (instructorLink) instructorLink.style.display = 'inline';
            if (studentLink) studentLink.style.display = 'none';
        }
    } else {
        // No user logged in - hide all dashboard links
        if (adminLink) adminLink.style.display = 'none';
        if (instructorLink) instructorLink.style.display = 'none';
        if (studentLink) studentLink.style.display = 'none';
    }
    
    // Update account section based on login status
    updateAccountSection();
}

// Update account section based on login status
function updateAccountSection() {
    const accountDropdown = document.getElementById('accountDropdown');
    const authButtons = document.getElementById('authButtons');
    
    if (currentUser && authToken) {
        // User is logged in - show account dropdown
        if (accountDropdown) accountDropdown.style.display = 'block';
        if (authButtons) authButtons.style.display = 'none';
        
        // Update account info
        const userName = document.getElementById('userName');
        const avatarInitials = document.getElementById('avatarInitials');
        const userAvatar = document.getElementById('userAvatar');
        
        if (userName) {
            userName.textContent = currentUser.full_name || currentUser.username || currentUser.email || 'User';
        }
        
        // Set avatar initials
        const initials = getInitials(currentUser.full_name || currentUser.username || currentUser.email);
        if (avatarInitials) {
            avatarInitials.textContent = initials;
        }
        
        // Update avatar color based on role
        if (userAvatar && currentUser) {
            if (currentUser.role === 'admin') {
                userAvatar.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
            } else if (currentUser.role === 'instructor') {
                userAvatar.style.background = 'linear-gradient(45deg, #f39c12, #e67e22)';
            } else {
                userAvatar.style.background = 'linear-gradient(45deg, #3498db, #2980b9)';
            }
        }
    } else {
        // User is not logged in - show auth buttons
        if (accountDropdown) accountDropdown.style.display = 'none';
        if (authButtons) authButtons.style.display = 'flex';
    }
}

// Get initials from name
function getInitials(name) {
    if (!name) return 'U';
    
    const words = name.split(' ');
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    } else {
        return name.substring(0, 2).toUpperCase();
    }
}

// Additional account dropdown functionality handled by the function at top of file

function checkAuth() {
    // Check if user was previously logged in
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    const savedEmail = localStorage.getItem('userEmail');
    
    if (savedToken && (savedUser || savedEmail)) {
        authToken = savedToken;
        if (savedUser) {
            try {
                currentUser = JSON.parse(savedUser);
            } catch (error) {
                currentUser = { email: savedEmail || 'unknown@example.com' };
            }
        } else {
            currentUser = { email: savedEmail };
        }
        
        // Start idle monitoring for existing session
        startIdleMonitoring();
    }
}

// Handle navigation
function handleNavigation() {
    const hash = window.location.hash;
    switch(hash) {
        case '#login':
            showLogin();
            break;
        case '#register':
            showRegister();
            break;
        case '#profile':
            showProfile();
            break;
        case '#settings':
            showSettings();
            break;
        case '#help':
            showHelp();
            break;
        case '#home':
        default:
            showHome();
            break;
    }
}

// Modal functions are now defined at the top of the file

// Duplicate updateAccountSection function removed - using the one defined earlier

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const accountDropdown = document.getElementById('accountDropdown');
    const accountMenu = document.getElementById('accountMenu');
    
    if (accountMenu && accountDropdown && !accountDropdown.contains(event.target)) {
        accountMenu.classList.remove('show');
    }
});

// Prevent dropdown from closing when clicking inside it
document.addEventListener('click', function(event) {
    const accountMenu = document.getElementById('accountMenu');
    if (accountMenu && accountMenu.contains(event.target)) {
        // Don't close dropdown when clicking inside it (except for logout)
        if (!event.target.textContent.includes('Logout')) {
            event.stopPropagation();
        }
    }
});

// Idle timeout management
let idleTimer = null;
let warningTimer = null;
let lastActivityTime = Date.now();
const IDLE_TIMEOUT_MINUTES = 15; // User idle timeout
const WARNING_MINUTES = 2; // Warn 2 minutes before timeout
const ACTIVITY_EVENTS = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

function startIdleMonitoring() {
    if (!authToken) return;
    
    // Reset activity tracking
    lastActivityTime = Date.now();
    
    // Add activity listeners
    ACTIVITY_EVENTS.forEach(event => {
        document.addEventListener(event, resetIdleTimer, true);
    });
    
    // Start the idle timer
    resetIdleTimer();
}

function stopIdleMonitoring() {
    // Remove activity listeners
    ACTIVITY_EVENTS.forEach(event => {
        document.removeEventListener(event, resetIdleTimer, true);
    });
    
    // Clear timers
    if (idleTimer) {
        clearTimeout(idleTimer);
        idleTimer = null;
    }
    if (warningTimer) {
        clearTimeout(warningTimer);
        warningTimer = null;
    }
}

// Make resetIdleTimer globally available
window.resetIdleTimer = function resetIdleTimer() {
    lastActivityTime = Date.now();
    
    // Clear existing timers
    if (idleTimer) {
        clearTimeout(idleTimer);
    }
    if (warningTimer) {
        clearTimeout(warningTimer);
    }
    
    // Remove any existing warning notification
    const existingWarning = document.querySelector('.idle-warning-notification');
    if (existingWarning) {
        existingWarning.remove();
    }
    
    // Set warning timer (warn X minutes before idle timeout)
    const warningTimeMs = (IDLE_TIMEOUT_MINUTES - WARNING_MINUTES) * 60 * 1000;
    warningTimer = setTimeout(showIdleWarning, warningTimeMs);
    
    // Set idle timeout timer
    const idleTimeMs = IDLE_TIMEOUT_MINUTES * 60 * 1000;
    idleTimer = setTimeout(handleIdleTimeout, idleTimeMs);
}

function showIdleWarning() {
    const message = `You will be logged out in ${WARNING_MINUTES} minute${WARNING_MINUTES !== 1 ? 's' : ''} due to inactivity. Move your mouse or press a key to stay logged in.`;
    
    // Create persistent warning notification
    const warning = document.createElement('div');
    warning.className = 'notification notification-warning idle-warning-notification';
    warning.style.position = 'fixed';
    warning.style.top = '20px';
    warning.style.right = '20px';
    warning.style.zIndex = '10001';
    warning.style.minWidth = '350px';
    warning.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove(); resetIdleTimer();">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(warning);
    
    // Add countdown
    let secondsLeft = WARNING_MINUTES * 60;
    const countdownInterval = setInterval(() => {
        secondsLeft--;
        const minutesLeft = Math.floor(secondsLeft / 60);
        const secondsRemaining = secondsLeft % 60;
        
        const messageSpan = warning.querySelector('.notification-content span');
        if (messageSpan) {
            if (secondsLeft > 60) {
                messageSpan.textContent = `You will be logged out in ${minutesLeft}:${secondsRemaining.toString().padStart(2, '0')} due to inactivity. Move your mouse or press a key to stay logged in.`;
            } else {
                messageSpan.textContent = `You will be logged out in ${secondsLeft} second${secondsLeft !== 1 ? 's' : ''} due to inactivity!`;
            }
        }
        
        if (secondsLeft <= 0 || !document.body.contains(warning)) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

function handleIdleTimeout() {
    stopIdleMonitoring();
    showNotification('You have been logged out due to inactivity.', 'info', 5000);
    setTimeout(() => {
        logout();
    }, 1000);
}

// Enhanced fetch wrapper to handle 401 responses automatically
window.authenticatedFetch = async function(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(url, { ...options, ...defaultOptions });
    
    if (response.status === 401) {
        handleSessionExpired();
        throw new Error('Session expired');
    }
    
    return response;
};

// Set up account dropdown event listener (now using onclick attribute instead)
function setupAccountDropdownListener() {
    // This function is no longer needed since we're using onclick attribute
    // but keeping it for any future event listener setup
}

// Access control functions
function checkPageAccess() {
    const currentUser = getCurrentUser();
    const currentPage = window.location.pathname.split('/').pop();
    
    // If user is not logged in, allow access to main pages only
    if (!currentUser || !currentUser.role) {
        const allowedPages = ['index.html', ''];
        if (!allowedPages.includes(currentPage)) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    }
    
    // Role-based access control
    const userRole = currentUser.role;
    
    // Define page access rules
    const pageAccess = {
        'student': ['student-dashboard.html', 'lab.html'],
        'instructor': ['instructor-dashboard.html', 'lab.html'],
        'admin': ['admin.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html']
    };
    
    // Check if current user role has access to current page
    const allowedPages = pageAccess[userRole] || [];
    
    // Add general pages that all authenticated users can access
    const generalPages = ['index.html', ''];
    const allAllowedPages = [...allowedPages, ...generalPages];
    
    if (!allAllowedPages.includes(currentPage)) {
        // Redirect to appropriate dashboard based on role
        switch (userRole) {
            case 'student':
                window.location.href = 'student-dashboard.html';
                break;
            case 'instructor':
                window.location.href = 'instructor-dashboard.html';
                break;
            case 'admin':
                window.location.href = 'admin.html';
                break;
            default:
                window.location.href = 'index.html';
        }
        return false;
    }
    
    return true;
}

function preventUnauthorizedAccess() {
    // Add event listeners to prevent navigation to unauthorized pages
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href]');
        if (!link) return;
        
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.includes('://')) {
            return; // Skip anchors, javascript links, and external links
        }
        
        const currentUser = getCurrentUser();
        if (!currentUser || !currentUser.role) return;
        
        // Check if the target page is allowed for current user
        const targetPage = href.split('/').pop();
        const userRole = currentUser.role;
        
        const pageAccess = {
            'student': ['student-dashboard.html', 'lab.html', 'index.html', ''],
            'instructor': ['instructor-dashboard.html', 'lab.html', 'index.html', ''],
            'admin': ['admin.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html', 'index.html', '']
        };
        
        const allowedPages = pageAccess[userRole] || [];
        
        if (!allowedPages.includes(targetPage)) {
            e.preventDefault();
            showNotification(`Access denied: You don't have permission to access ${targetPage}`, 'error');
        }
    });
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Course Creator Platform loaded');
    
    // Check page access before initializing
    if (!checkPageAccess()) {
        return; // Access denied, redirect happened
    }
    
    checkAuth();
    updateAccountSection();
    updateNavigation();
    
    // Set up access control
    preventUnauthorizedAccess();
    
    // Set up account dropdown event listener
    setupAccountDropdownListener();
    
    // Only handle navigation on main pages, not on dashboard pages
    if (document.getElementById('main-content')) {
        handleNavigation();
    }
});

window.addEventListener('hashchange', handleNavigation);