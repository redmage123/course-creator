/**
 * Navigation Module
 * Handles navigation, routing, and access control
 */

import { Auth } from './auth.js';
import UIComponents from './ui-components.js';

export class NavigationManager {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.setupEventListeners();
    }

    /**
     * Get current page filename
     */
    getCurrentPage() {
        const fullPath = window.location.pathname;
        const fileName = fullPath.split('/').pop() || 'index.html';
        // Handle new html/ directory structure
        if (fullPath.includes('/html/')) {
            return fileName;
        }
        return fileName;
    }

    /**
     * Setup navigation event listeners
     */
    setupEventListeners() {
        // Handle hash changes
        window.addEventListener('hashchange', () => {
            this.handleHashNavigation();
        });

        // Handle link clicks for access control
        document.addEventListener('click', (e) => {
            this.handleLinkClick(e);
        });

        // Handle initial hash navigation
        this.handleHashNavigation();
    }

    /**
     * Handle hash-based navigation
     */
    handleHashNavigation() {
        const hash = window.location.hash;
        
        // Only handle hash navigation on main index page
        if (this.currentPage === 'index.html' && document.getElementById('main-content')) {
            this.routeToSection(hash);
        }
    }

    /**
     * Route to specific section based on hash
     */
    routeToSection(hash) {
        switch (hash) {
            case '#login':
                this.showLogin();
                break;
            case '#register':
                this.showRegister();
                break;
            case '#profile':
                this.showProfile();
                break;
            case '#settings':
                this.showSettings();
                break;
            case '#help':
                this.showHelp();
                break;
            case '#password-reset':
                this.showPasswordReset();
                break;
            case '#home':
            default:
                this.showHome();
                break;
        }
    }

    /**
     * Handle link clicks for access control
     */
    handleLinkClick(e) {
        const link = e.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.includes('://')) {
            return; // Skip anchors, javascript links, and external links
        }

        const targetPage = href.split('/').pop();
        if (!Auth.hasPageAccess(targetPage)) {
            e.preventDefault();
            this.showAccessDenied(targetPage);
        }
    }

    /**
     * Show access denied message
     */
    showAccessDenied(page) {
        const modal = UIComponents.createModal(
            'Access Denied',
            `<p>You don't have permission to access <strong>${page}</strong>.</p>
             <p>Please contact your administrator if you believe this is an error.</p>`
        );
    }

    /**
     * Update navigation based on user role
     */
    updateNavigation() {
        const user = Auth.getCurrentUser();
        
        // Update role-specific navigation links
        const adminLink = document.getElementById('admin-link');
        const instructorLink = document.getElementById('instructor-link');
        const studentLink = document.getElementById('student-link');
        
        if (user && Auth.isAuthenticated()) {
            if (user.role === 'admin') {
                if (adminLink) adminLink.style.display = 'inline';
                if (instructorLink) instructorLink.style.display = 'none';
                if (studentLink) studentLink.style.display = 'none';
            } else if (user.role === 'instructor') {
                if (adminLink) adminLink.style.display = 'none';
                if (instructorLink) instructorLink.style.display = 'inline';
                if (studentLink) studentLink.style.display = 'none';
            } else if (user.role === 'student') {
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
    }

    /**
     * Update account section based on login status
     */
    updateAccountSection() {
        const accountDropdown = document.getElementById('accountDropdown');
        const authButtons = document.getElementById('authButtons');
        const user = Auth.getCurrentUser();

        if (user && Auth.isAuthenticated()) {
            // User is logged in - show account dropdown
            if (accountDropdown) accountDropdown.style.display = 'block';
            if (authButtons) authButtons.style.display = 'none';
            
            // Update account info
            this.updateAccountInfo(user);
        } else {
            // User is not logged in - show auth buttons
            if (accountDropdown) accountDropdown.style.display = 'none';
            if (authButtons) authButtons.style.display = 'flex';
        }
    }

    /**
     * Update account info in dropdown
     */
    updateAccountInfo(user) {
        const userName = document.getElementById('userName');
        const avatarInitials = document.getElementById('avatarInitials');
        const userAvatar = document.getElementById('userAvatar');
        
        if (userName) {
            userName.textContent = user.full_name || user.username || user.email || 'User';
        }
        
        // Set avatar initials
        const initials = UIComponents.getInitials(user.full_name || user.username || user.email);
        if (avatarInitials) {
            avatarInitials.textContent = initials;
        }
        
        // Update avatar color based on role
        if (userAvatar && user) {
            if (user.role === 'admin') {
                userAvatar.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
            } else if (user.role === 'instructor') {
                userAvatar.style.background = 'linear-gradient(45deg, #f39c12, #e67e22)';
            } else {
                userAvatar.style.background = 'linear-gradient(45deg, #3498db, #2980b9)';
            }
        }
    }

    /**
     * Show home page
     */
    showHome() {
        const main = document.getElementById('main-content');
        if (!main) return;

        const user = Auth.getCurrentUser();
        
        if (user && Auth.isAuthenticated()) {
            // User is logged in - show welcome message
            main.innerHTML = `
                <section id="home">
                    <h2>Welcome back, ${user.full_name || user.username || user.email}!</h2>
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
                        <button onclick="window.location.hash='#login'" class="btn btn-primary">Login</button>
                        <button onclick="window.location.hash='#register'" class="btn btn-secondary">Register</button>
                    </div>
                </section>
            `;
        }
    }

    /**
     * Show login page
     */
    showLogin() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <section>
                <h2>Login</h2>
                <form id="login-form">
                    <div class="form-group">
                        <label for="login-email">Email:</label>
                        <input type="email" id="login-email" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="login-password">Password:</label>
                        <div class="password-input-container">
                            <input type="password" id="login-password" name="password" required>
                        </div>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Login</button>
                        <button type="button" onclick="window.location.hash='#home'" class="btn btn-secondary">Cancel</button>
                    </div>
                    <div class="form-links">
                        <a href="#password-reset">Forgot Password?</a>
                    </div>
                </form>
            </section>
        `;

        // Add password toggle
        const passwordContainer = main.querySelector('.password-input-container');
        const passwordToggle = UIComponents.createPasswordToggle('login-password');
        passwordContainer.appendChild(passwordToggle);

        // Setup form handler
        this.setupLoginForm();
    }

    /**
     * Setup login form handler
     */
    setupLoginForm() {
        const form = document.getElementById('login-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const credentials = {
                username: formData.get('username'),
                password: formData.get('password')
            };

            const result = await Auth.login(credentials);
            
            if (result.success) {
                // Redirect based on role
                window.location.href = Auth.getRedirectUrl();
            } else {
                alert('Login failed: ' + result.error);
            }
        });
    }

    /**
     * Show register page
     */
    showRegister() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <section>
                <h2>Instructor Registration</h2>
                <p>Create your instructor account to start building and managing courses.</p>
                <form id="register-form">
                    <div class="form-row">
                        <div class="form-group half-width">
                            <label for="register-first-name">First Name: <span class="required">*</span></label>
                            <input type="text" id="register-first-name" name="first_name" required 
                                   placeholder="Enter your first name">
                        </div>
                        <div class="form-group half-width">
                            <label for="register-last-name">Last Name: <span class="required">*</span></label>
                            <input type="text" id="register-last-name" name="last_name" required 
                                   placeholder="Enter your last name">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="register-email">Email Address: <span class="required">*</span></label>
                        <input type="email" id="register-email" name="email" required 
                               placeholder="Enter your email address">
                    </div>
                    <div class="form-group">
                        <label for="register-organization">Organization:</label>
                        <input type="text" id="register-organization" name="organization" 
                               placeholder="Enter your organization or institution (optional)">
                    </div>
                    <div class="form-group">
                        <label for="register-password">Password: <span class="required">*</span></label>
                        <div class="password-input-container">
                            <input type="password" id="register-password" name="password" required 
                                   placeholder="Create a secure password">
                            <button type="button" class="password-toggle" 
                                    onclick="togglePasswordVisibility('register-password', 'password-toggle-1')" 
                                    id="password-toggle-1" 
                                    title="Show password">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                        <div class="password-requirements">
                            <small>Password must be at least 8 characters long</small>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="register-password-confirm">Confirm Password: <span class="required">*</span></label>
                        <div class="password-input-container">
                            <input type="password" id="register-password-confirm" name="password_confirm" required 
                                   placeholder="Confirm your password">
                            <button type="button" class="password-toggle" 
                                    onclick="togglePasswordVisibility('register-password-confirm', 'password-toggle-2')" 
                                    id="password-toggle-2" 
                                    title="Show password">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                    <div id="password-match-indicator"></div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Create Instructor Account</button>
                        <button type="button" onclick="window.location.hash='#home'" class="btn btn-secondary">Cancel</button>
                    </div>
                    <div class="form-footer">
                        <p><span class="required">*</span> Required fields</p>
                    </div>
                </form>
            </section>
        `;

        // Add password toggles
        const passwordContainers = main.querySelectorAll('.password-input-container');
        passwordContainers.forEach((container, index) => {
            const input = container.querySelector('input');
            const toggle = UIComponents.createPasswordToggle(input.id);
            container.appendChild(toggle);
        });

        // Setup form handler
        this.setupRegisterForm();
    }

    /**
     * Setup register form handler
     */
    setupRegisterForm() {
        const form = document.getElementById('register-form');
        if (!form) return;

        // Setup password matching validation
        const passwordInput = document.getElementById('register-password');
        const confirmInput = document.getElementById('register-password-confirm');
        const indicator = document.getElementById('password-match-indicator');

        const checkPasswordMatch = () => {
            const password = passwordInput.value;
            const confirmPassword = confirmInput.value;
            
            if (confirmPassword.length === 0) {
                indicator.textContent = '';
                indicator.className = '';
            } else if (password === confirmPassword) {
                indicator.textContent = '✅ Passwords match';
                indicator.className = 'success';
            } else {
                indicator.textContent = '❌ Passwords do not match';
                indicator.className = 'error';
            }
        };

        passwordInput.addEventListener('input', checkPasswordMatch);
        confirmInput.addEventListener('input', checkPasswordMatch);

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const password = formData.get('password');
            const passwordConfirm = formData.get('password_confirm');
            
            if (password !== passwordConfirm) {
                alert('Passwords do not match. Please check your passwords and try again.');
                return;
            }
            
            // Combine first and last name for full_name
            const firstName = formData.get('first_name');
            const lastName = formData.get('last_name');
            const fullName = `${firstName} ${lastName}`.trim();
            
            const userData = {
                email: formData.get('email'),
                full_name: fullName,
                first_name: firstName,
                last_name: lastName,
                username: formData.get('email'), // Use email as username
                password: password,
                organization: formData.get('organization') || null
            };

            const result = await Auth.register(userData);
            
            if (result.success) {
                alert('Registration successful! Please login.');
                window.location.hash = '#login';
            } else {
                alert('Registration failed: ' + result.error);
            }
        });
    }

    /**
     * Show profile page
     */
    showProfile() {
        if (!Auth.isAuthenticated()) {
            window.location.hash = '#login';
            return;
        }

        const main = document.getElementById('main-content');
        if (!main) return;

        const user = Auth.getCurrentUser();
        
        main.innerHTML = `
            <section>
                <h2>👤 User Profile</h2>
                <div class="profile-info">
                    <div class="profile-avatar">
                        <div class="large-avatar">
                            <span>${UIComponents.getInitials(user?.full_name || user?.email)}</span>
                        </div>
                    </div>
                    <div class="profile-details">
                        <h3>${user?.full_name || 'User'}</h3>
                        <p><strong>Email:</strong> ${user?.email || 'Unknown'}</p>
                        <p><strong>Username:</strong> ${user?.username || 'N/A'}</p>
                        <p><strong>Role:</strong> <span class="role-badge role-${user?.role || 'student'}">${user?.role || 'student'}</span></p>
                        <p><strong>Status:</strong> <span class="status-active">Active</span></p>
                    </div>
                </div>
                <div class="profile-actions">
                    <button onclick="window.location.hash='#settings'" class="btn btn-secondary">⚙️ Settings</button>
                    <button onclick="window.location.hash='#home'" class="btn btn-primary">🏠 Back to Home</button>
                </div>
            </section>
        `;
    }

    /**
     * Show settings page
     */
    showSettings() {
        if (!Auth.isAuthenticated()) {
            window.location.hash = '#login';
            return;
        }

        const main = document.getElementById('main-content');
        if (!main) return;

        const user = Auth.getCurrentUser();
        
        main.innerHTML = `
            <section>
                <h2>⚙️ Account Settings</h2>
                <div class="settings-section">
                    <h3>Profile Information</h3>
                    <form id="profile-form">
                        <div class="form-group">
                            <label for="settings-name">Full Name:</label>
                            <input type="text" id="settings-name" value="${user?.full_name || ''}" required>
                        </div>
                        <div class="form-group">
                            <label for="settings-email">Email:</label>
                            <input type="email" id="settings-email" value="${user?.email || ''}" required>
                        </div>
                        <div class="form-group">
                            <label for="settings-username">Username:</label>
                            <input type="text" id="settings-username" value="${user?.username || ''}" required>
                        </div>
                        <button type="submit" class="btn btn-primary">💾 Save Changes</button>
                    </form>
                </div>
                
                <div class="settings-section">
                    <h3>Security</h3>
                    <button onclick="window.location.hash='#change-password'" class="btn btn-secondary">🔒 Change Password</button>
                </div>
                
                <div class="settings-actions">
                    <button onclick="window.location.hash='#profile'" class="btn btn-secondary">👤 Back to Profile</button>
                    <button onclick="window.location.hash='#home'" class="btn btn-primary">🏠 Back to Home</button>
                </div>
            </section>
        `;
    }

    /**
     * Show help page
     */
    showHelp() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <section>
                <h2>❓ Help & Support</h2>
                
                <div class="help-section">
                    <h3>Getting Started</h3>
                    <ul>
                        <li><strong>Registration:</strong> Create an account to access all features</li>
                        <li><strong>Login:</strong> Use your email and password to sign in</li>
                        <li><strong>Course Creation:</strong> Navigate to your dashboard to build new courses</li>
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
                    <h3>Contact Support</h3>
                    <p>For technical support or questions, please contact:</p>
                    <p><strong>Email:</strong> support@courseplatform.com</p>
                </div>
                
                <div class="help-actions">
                    <button onclick="window.location.hash='#home'" class="btn btn-primary">🏠 Back to Home</button>
                </div>
            </section>
        `;
    }

    /**
     * Show password reset page
     */
    showPasswordReset() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <section>
                <h2>Reset Password</h2>
                <p>Enter your email address and new password to reset your password.</p>
                <form id="password-reset-form">
                    <div class="form-group">
                        <label for="reset-email">Email:</label>
                        <input type="email" id="reset-email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="new-password">New Password:</label>
                        <div class="password-input-container">
                            <input type="password" id="new-password" name="new_password" required minlength="6">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="confirm-password">Confirm New Password:</label>
                        <div class="password-input-container">
                            <input type="password" id="confirm-password" name="confirm_password" required minlength="6">
                        </div>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Reset Password</button>
                        <button type="button" onclick="window.location.hash='#login'" class="btn btn-secondary">Back to Login</button>
                    </div>
                </form>
            </section>
        `;

        // Add password toggles
        const passwordContainers = main.querySelectorAll('.password-input-container');
        passwordContainers.forEach((container) => {
            const input = container.querySelector('input');
            const toggle = UIComponents.createPasswordToggle(input.id);
            container.appendChild(toggle);
        });

        // Setup form handler
        this.setupPasswordResetForm();
    }

    /**
     * Setup password reset form handler
     */
    setupPasswordResetForm() {
        const form = document.getElementById('password-reset-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const newPassword = formData.get('new_password');
            const confirmPassword = formData.get('confirm_password');
            
            if (newPassword !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }

            const result = await Auth.resetPassword(
                formData.get('email'),
                newPassword
            );
            
            if (result.success) {
                alert('Password reset successfully! You can now login with your new password.');
                window.location.hash = '#login';
            } else {
                alert('Password reset failed: ' + result.error);
            }
        });
    }

    /**
     * Navigate to specific page
     */
    navigateTo(page) {
        if (Auth.hasPageAccess(page)) {
            window.location.href = page;
        } else {
            this.showAccessDenied(page);
        }
    }

    /**
     * Initialize navigation
     */
    init() {
        Auth.initializeAuth();
        this.updateNavigation();
        this.updateAccountSection();
    }
}

// Create singleton instance
const navigationManager = new NavigationManager();

export { navigationManager as Navigation };
export default navigationManager;