/**
 * NAVIGATION MODULE - ROUTING, ACCESS CONTROL, AND PAGE MANAGEMENT
 * 
 * PURPOSE: Centralized navigation system for Course Creator Platform
 * WHY: Unified navigation ensures consistent user experience and proper access control
 * ARCHITECTURE: Event-driven navigation with hash-based routing and security validation
 * 
 * CORE RESPONSIBILITIES:
 * - Hash-based routing for single-page application behavior
 * - Access control enforcement based on user roles and authentication
 * - Link click interception for security validation
 * - Page context detection and navigation state management
 * - Integration with authentication system for protected routes
 */

/**
 * MODULE DEPENDENCIES
 * PURPOSE: Import required modules for navigation functionality
 * WHY: Navigation depends on auth state and UI components for proper operation
 */
import { Auth } from './auth.js';          // Authentication state and user validation
import UIComponents from './ui-components.js'; // UI helper functions and components

/**
 * NAVIGATION MANAGER CLASS
 * PATTERN: Centralized navigation controller with event-driven architecture
 * WHY: Single navigation manager prevents routing conflicts and ensures consistency
 */
export class NavigationManager {
    /**
     * CONSTRUCTOR - NAVIGATION SYSTEM INITIALIZATION
     * PURPOSE: Initialize navigation state and event listeners
     * WHY: Immediate setup ensures navigation works from page load
     */
    constructor() {
        // CURRENT PAGE DETECTION: Determine initial page context
        this.currentPage = this.getCurrentPage();
        
        // EVENT LISTENER SETUP: Enable navigation event handling
        this.setupEventListeners();
    }

    /**
     * CURRENT PAGE DETECTION
     * PURPOSE: Extract current page filename from URL for routing logic
     * WHY: Different pages require different navigation behavior and access control
     * HANDLES: Both root-level and html/ subdirectory structures
     */
    getCurrentPage() {
        const fullPath = window.location.pathname;
        const fileName = fullPath.split('/').pop() || 'index.html';
        
        // DIRECTORY STRUCTURE HANDLING: Support both old and new HTML organization
        // WHY: Platform supports both /page.html and /html/page.html structures
        if (fullPath.includes('/html/')) {
            return fileName;
        }
        return fileName;
    }

    /**
     * NAVIGATION EVENT LISTENER SETUP
     * PURPOSE: Register event handlers for all navigation interactions
     * WHY: Centralized event handling ensures consistent navigation behavior
     * 
     * EVENT TYPES HANDLED:
     * - Hash changes for single-page routing
     * - Link clicks for access control validation
     * - Initial page load routing
     */
    setupEventListeners() {
        // HASH CHANGE HANDLER: Enable hash-based routing
        // WHY: Hash navigation allows SPA behavior without full page reloads
        window.addEventListener('hashchange', () => {
            this.handleHashNavigation();
        });

        // LINK CLICK INTERCEPTION: Validate access before navigation
        // WHY: Prevents unauthorized access to protected pages and resources
        document.addEventListener('click', (e) => {
            this.handleLinkClick(e);
        });

        // INITIAL NAVIGATION: Handle page load routing
        // WHY: Ensure proper navigation state on first page load
        this.handleHashNavigation();
    }

    /**
     * Handle hash-based navigation
     * PURPOSE: Route to different sections while preserving home page content
     */
    handleHashNavigation() {
        const hash = window.location.hash;
        
        // Only handle hash navigation on main index page with specific hashes
        if (this.currentPage === 'index.html' && document.getElementById('main-content')) {
            // Don't route if no hash or if slideshow exists (preserve home page)
            const slideshowExists = document.querySelector('.slideshow-section');
            if (slideshowExists && (!hash || hash === '#' || hash === '')) {
                console.log('Preserving home page content with slideshow');
                return;
            }
            this.routeToSection(hash);
        }
    }

    /**
     * Route to specific section based on hash
     * PURPOSE: Handle hash-based routing while preserving home page content
     */
    routeToSection(hash) {
        // If no hash or empty hash, preserve the existing home page content
        if (!hash || hash === '#' || hash === '') {
            return;
        }
        
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
        const orgAdminLink = document.getElementById('org-admin-link');

        if (user && Auth.isAuthenticated()) {
            if (user.role === 'admin') {
                if (adminLink) adminLink.style.display = 'inline';
                if (instructorLink) instructorLink.style.display = 'none';
                if (studentLink) studentLink.style.display = 'none';
                if (orgAdminLink) orgAdminLink.style.display = 'none';
            } else if (user.role === 'organization_admin') {
                if (adminLink) adminLink.style.display = 'none';
                if (instructorLink) instructorLink.style.display = 'none';
                if (studentLink) studentLink.style.display = 'none';
                if (orgAdminLink) orgAdminLink.style.display = 'inline';
            } else if (user.role === 'instructor') {
                if (adminLink) adminLink.style.display = 'none';
                if (instructorLink) instructorLink.style.display = 'inline';
                if (studentLink) studentLink.style.display = 'none';
                if (orgAdminLink) orgAdminLink.style.display = 'none';
            } else if (user.role === 'student') {
                if (adminLink) adminLink.style.display = 'none';
                if (instructorLink) instructorLink.style.display = 'none';
                if (studentLink) studentLink.style.display = 'inline';
                if (orgAdminLink) orgAdminLink.style.display = 'none';
            } else {
                // Default to instructor dashboard for users without specific roles
                if (adminLink) adminLink.style.display = 'none';
                if (instructorLink) instructorLink.style.display = 'inline';
                if (studentLink) studentLink.style.display = 'none';
                if (orgAdminLink) orgAdminLink.style.display = 'none';
            }
        } else {
            // No user logged in - hide all dashboard links
            if (adminLink) adminLink.style.display = 'none';
            if (instructorLink) instructorLink.style.display = 'none';
            if (studentLink) studentLink.style.display = 'none';
            if (orgAdminLink) orgAdminLink.style.display = 'none';
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
            } else if (user.role === 'organization_admin') {
                userAvatar.style.background = 'linear-gradient(45deg, #9b59b6, #8e44ad)';
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
        // Check if we're already on the home page with rich content
        const main = document.getElementById('main-content');
        if (!main) return;
        
        // If the page already has rich home page content (slideshow, features, etc.)
        // don't replace it - this preserves the rich home page layout
        const slideshowExists = document.querySelector('.hero-slideshow');
        const featuresExist = main.querySelector('.features-section') || main.querySelector('.hero-section');
        
        if (slideshowExists || featuresExist) {
            // We're already showing the rich home page content, don't replace it
            return;
        }

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
            <section class="login-section" style="max-width: 600px; margin: 4rem auto; padding: 0 1rem;">
                <div style="text-align: center; margin-bottom: 2rem;">
                    <h2 style="font-size: 2rem; margin-bottom: 0.5rem;">Welcome Back</h2>
                    <p style="color: var(--text-secondary); font-size: 1.125rem;">Sign in to your account</p>
                </div>

                <div class="login-card" style="background: var(--surface-color); border-radius: var(--radius-lg); padding: 2.5rem; box-shadow: var(--shadow-lg);">
                    <form id="login-form">
                        <div class="form-group" style="margin-bottom: 1.5rem;">
                            <label for="login-username" style="display: block; margin-bottom: 0.5rem; font-weight: 500; font-size: 1.125rem; color: var(--text-primary);">Username or Email</label>
                            <input type="text" id="login-username" name="username" required
                                   placeholder="Enter your username or email"
                                   autocomplete="username"
                                   aria-label="Username or Email"
                                   style="width: 100%; padding: 0.875rem 1rem; border: 2px solid var(--border-color); border-radius: var(--radius-md); font-size: 1rem; transition: all 0.2s; box-sizing: border-box; cursor: text;">
                        </div>
                        <div class="form-group" style="margin-bottom: 1.5rem;">
                            <label for="login-password" style="display: block; margin-bottom: 0.5rem; font-weight: 500; font-size: 1.125rem; color: var(--text-primary);">Password</label>
                            <div class="password-input-container" style="position: relative;">
                                <input type="password" id="login-password" name="password" required
                                       autocomplete="current-password"
                                       aria-label="Password"
                                       style="width: 100%; padding: 0.875rem 1rem; border: 2px solid var(--border-color); border-radius: var(--radius-md); font-size: 1rem; transition: all 0.2s; box-sizing: border-box; cursor: text; padding-right: 3rem;">
                            </div>
                        </div>
                        <div class="form-actions" style="margin-top: 2rem;">
                            <button type="submit" class="btn btn-primary"
                                    style="width: 100%; padding: 1rem 1.25rem !important; font-size: 1.125rem !important; font-weight: 600; border-radius: var(--radius-md); margin-bottom: 1rem; box-sizing: border-box !important; height: 52px !important; line-height: 1.5 !important; border: none !important; display: flex !important; align-items: center !important; justify-content: center !important;">
                                Sign In
                            </button>
                            <button type="button" onclick="window.location.hash='#home'" class="btn btn-secondary"
                                    style="width: 100%; padding: 1rem 1.25rem !important; font-size: 1.125rem !important; font-weight: 600; border-radius: var(--radius-md); box-sizing: border-box !important; height: 52px !important; line-height: 1.5 !important; border: none !important; display: flex !important; align-items: center !important; justify-content: center !important;">
                                Cancel
                            </button>
                        </div>
                        <div class="form-links" style="text-align: center; margin-top: 1.5rem;">
                            <a href="#password-reset" style="color: var(--primary-color); text-decoration: none; font-size: 1rem;">Forgot Password?</a>
                        </div>
                    </form>
                </div>
            </section>
            <style>
                .login-section input {
                    cursor: text !important;
                }
                .login-section input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                }
                .login-section input::placeholder {
                    color: var(--text-muted);
                    font-size: 1rem;
                }
            </style>
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
    /**
     * Show registration options page
     * PURPOSE: Present users with clear choice between organization and instructor registration
     * WHY: Different registration flows require different information and permissions
     */
    showRegister() {
        try {
            const main = document.getElementById('main-content');
            if (!main) {
                console.error('❌ main-content element not found');
                return;
            }

            main.innerHTML = `
            <section class="registration-options">
                <div class="registration-header">
                    <h2>Join the Course Creator Platform</h2>
                    <p>Choose your registration path to get started with course creation and management.</p>
                </div>

                <div class="registration-cards">
                    <div class="registration-card" id="org-registration-card">
                        <div class="card-icon">
                            <i class="fas fa-building"></i>
                        </div>
                        <h3>Register New Organization</h3>
                        <p>Set up a new organization account with full administrative controls. Perfect for companies, schools, or training institutions starting fresh.</p>
                        <ul class="feature-list">
                            <li><i class="fas fa-check"></i> Create organization admin account</li>
                            <li><i class="fas fa-check"></i> Full organization management</li>
                            <li><i class="fas fa-check"></i> User role management</li>
                            <li><i class="fas fa-check"></i> Custom branding options</li>
                        </ul>
                        <button class="btn btn-primary" onclick="window.location.href='html/organization-registration.html'">
                            <i class="fas fa-building"></i> Register Organization
                        </button>
                    </div>

                    <div class="registration-card" id="instructor-registration-card">
                        <div class="card-icon">
                            <i class="fas fa-chalkboard-teacher"></i>
                        </div>
                        <h3>Join Existing Organization</h3>
                        <p>Register as an instructor within an existing organization. Get access to course creation tools and student management features.</p>
                        <ul class="feature-list">
                            <li><i class="fas fa-check"></i> Course creation & management</li>
                            <li><i class="fas fa-check"></i> Student progress tracking</li>
                            <li><i class="fas fa-check"></i> Lab environment access</li>
                            <li><i class="fas fa-check"></i> Organization collaboration</li>
                        </ul>
                        <button class="btn btn-secondary" onclick="Navigation.showInstructorRegistration()">
                            <i class="fas fa-user-plus"></i> Join as Instructor
                        </button>
                    </div>
                </div>

                <div class="registration-help">
                    <div class="help-section">
                        <h4><i class="fas fa-question-circle"></i> Need Help Choosing?</h4>
                        <p><strong>Choose "Register Organization"</strong> if you're setting up courses for your company, school, or institution for the first time.</p>
                        <p><strong>Choose "Join Existing Organization"</strong> if someone from your organization has already registered and you need instructor access.</p>
                    </div>
                    <div class="back-option">
                        <button type="button" onclick="window.location.hash='#home'" class="btn btn-text">
                            <i class="fas fa-arrow-left"></i> Back to Home
                        </button>
                    </div>
                </div>
            </section>

            <style>
                .registration-options {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }

                .registration-header {
                    text-align: center;
                    margin-bottom: 3rem;
                }

                .registration-header h2 {
                    color: var(--primary-color);
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                }

                .registration-cards {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 2rem;
                    margin-bottom: 3rem;
                }

                .registration-card {
                    background: var(--card-background);
                    border: 2px solid var(--border-color);
                    border-radius: 16px;
                    padding: 2rem;
                    text-align: center;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }

                .registration-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                }

                .registration-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                    border-color: var(--primary-color);
                }

                .card-icon {
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2rem;
                }

                .registration-card h3 {
                    color: var(--primary-color);
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                }

                .registration-card p {
                    color: var(--text-secondary);
                    margin-bottom: 1.5rem;
                    line-height: 1.6;
                }

                .feature-list {
                    list-style: none;
                    padding: 0;
                    margin: 1.5rem 0;
                    text-align: left;
                }

                .feature-list li {
                    display: flex;
                    align-items: center;
                    margin-bottom: 0.75rem;
                    color: var(--text-secondary);
                }

                .feature-list i {
                    color: var(--success-color);
                    margin-right: 0.75rem;
                    font-size: 0.875rem;
                }

                .registration-help {
                    background: var(--surface-color);
                    border-radius: 12px;
                    padding: 2rem;
                    border: 1px solid var(--border-color);
                }

                .help-section h4 {
                    color: var(--primary-color);
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-bottom: 1rem;
                }

                .help-section p {
                    margin-bottom: 0.75rem;
                    color: var(--text-secondary);
                }

                .back-option {
                    text-align: center;
                    margin-top: 2rem;
                }

                @media (max-width: 768px) {
                    .registration-cards {
                        grid-template-columns: 1fr;
                    }
                    
                    .registration-header h2 {
                        font-size: 2rem;
                    }
                }
            </style>
        `;
        
        } catch (error) {
            console.error('❌ Navigation.showRegister() error:', error);
            
            // Show a fallback error message to the user
            const main = document.getElementById('main-content');
            if (main) {
                main.innerHTML = '<div class="error-message">Unable to load registration page. Please try again later.</div>';
            }
        }
    }

    /**
     * Show instructor registration form for existing organization
     * PURPOSE: Allow instructors to join existing organizations
     * WHY: Not all users need to create organizations, many join existing ones
     */
    showInstructorRegistration() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <section class="instructor-registration">
                <div class="registration-header">
                    <h2>Join as Instructor</h2>
                    <p>Register to join an existing organization as an instructor.</p>
                </div>

                <form id="instructor-register-form" class="registration-form">
                    <div class="form-section">
                        <h3><i class="fas fa-user"></i> Personal Information</h3>
                        
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
                                   placeholder="Enter your professional email address">
                            <div class="form-help">Use your organization's email domain if available</div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3><i class="fas fa-building"></i> Organization Information</h3>
                        
                        <div class="form-group">
                            <label for="organization-select">Select Organization: <span class="required">*</span></label>
                            <select id="organization-select" name="organization_id" required>
                                <option value="">Select your organization...</option>
                                <option value="lookup">🔍 Look up organization by domain</option>
                            </select>
                            <div class="form-help">Choose the organization you want to join</div>
                        </div>

                        <div class="form-group" id="organization-lookup" style="display: none;">
                            <label for="organization-domain">Organization Domain:</label>
                            <input type="text" id="organization-domain" name="organization_domain" 
                                   placeholder="e.g., company.com">
                            <div class="form-help">Enter your organization's domain to find them</div>
                            <button type="button" id="lookup-org-btn" class="btn btn-secondary">
                                <i class="fas fa-search"></i> Find Organization
                            </button>
                        </div>

                        <div id="organization-info" style="display: none;" class="organization-preview">
                            <div class="org-card">
                                <div class="org-details">
                                    <h4 id="selected-org-name">Organization Name</h4>
                                    <p id="selected-org-description">Organization description</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3><i class="fas fa-lock"></i> Account Security</h3>
                        
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
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-user-plus"></i> Join Organization
                        </button>
                        <button type="button" onclick="Navigation.showRegister()" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back to Options
                        </button>
                    </div>
                </form>
            </section>

            <style>
                .instructor-registration {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                }

                .registration-form {
                    background: var(--card-background);
                    border-radius: 16px;
                    padding: 2rem;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }

                .form-section {
                    margin-bottom: 2rem;
                    padding: 1.5rem;
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    background: var(--surface-color);
                }

                .form-section h3 {
                    color: var(--primary-color);
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    margin-bottom: 1.5rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 2px solid var(--border-color);
                }

                .organization-preview {
                    margin-top: 1rem;
                }

                .org-card {
                    background: var(--background-color);
                    border: 2px solid var(--primary-color);
                    border-radius: 8px;
                    padding: 1rem;
                }

                .org-details h4 {
                    color: var(--primary-color);
                    margin-bottom: 0.5rem;
                }

                .org-details p {
                    color: var(--text-secondary);
                    margin: 0;
                }

                .form-help {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                    margin-top: 0.25rem;
                }
            </style>
        `;

        this.setupInstructorRegistrationForm();
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
     * Setup instructor registration form handler
     * PURPOSE: Handle organization lookup and instructor registration 
     * WHY: Instructors need to associate with existing organizations
     */
    setupInstructorRegistrationForm() {
        const form = document.getElementById('instructor-register-form');
        if (!form) return;

        // Organization selection and lookup
        const orgSelect = document.getElementById('organization-select');
        const orgLookup = document.getElementById('organization-lookup');
        const domainInput = document.getElementById('organization-domain');
        const lookupBtn = document.getElementById('lookup-org-btn');
        const orgInfo = document.getElementById('organization-info');

        orgSelect.addEventListener('change', function() {
            if (this.value === 'lookup') {
                orgLookup.style.display = 'block';
                orgInfo.style.display = 'none';
            } else {
                orgLookup.style.display = 'none';
                if (this.value) {
                    // Show selected organization info
                    orgInfo.style.display = 'block';
                }
            }
        });

        // Load available organizations when form loads
        this.loadAvailableOrganizations();

        // Organization lookup functionality
        lookupBtn.addEventListener('click', async () => {
            const domain = domainInput.value.trim();
            if (!domain) {
                alert('Please enter a domain name');
                return;
            }

            alert('Domain-based organization lookup is not yet implemented. Please select from the dropdown above or contact your organization administrator.');
        });

        // Password matching validation
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

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const password = formData.get('password');
            const passwordConfirm = formData.get('password_confirm');
            
            if (password !== passwordConfirm) {
                alert('Passwords do not match. Please check your passwords and try again.');
                return;
            }

            // Check if organization is selected
            const orgId = formData.get('organization_id');
            if (!orgId || orgId === 'lookup' || orgId === '') {
                alert('Please select your organization from the dropdown.');
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
                role: 'instructor',
                organization_id: orgId
            };

            const result = await Auth.register(userData);
            
            if (result.success) {
                alert('Registration successful! Your account is pending approval by your organization admin. You will receive an email confirmation once approved.');
                window.location.hash = '#login';
            } else {
                alert('Registration failed: ' + result.error);
            }
        });
    }

    /**
     * Load available organizations for instructor registration
     * PURPOSE: Populate organization dropdown with available organizations
     * WHY: Allow instructors to select which organization to join
     */
    async loadAvailableOrganizations() {
        try {
            const response = await fetch(`${window.CONFIG?.PORTS?.ORGANIZATION_MANAGEMENT ? 
                `http://localhost:${window.window.CONFIG?.PORTS.ORGANIZATION_MANAGEMENT}` : 
                'http://localhost:8008'}/api/v1/organizations`);
            
            if (response.ok) {
                const organizations = await response.json();
                const orgSelect = document.getElementById('organization-select');
                
                if (orgSelect && organizations && Array.isArray(organizations)) {
                    // Add organizations to dropdown while keeping default options
                    organizations.forEach(org => {
                        const option = document.createElement('option');
                        option.value = org.id;
                        option.textContent = org.name;
                        orgSelect.insertBefore(option, orgSelect.querySelector('option[value="lookup"]'));
                    });
                }
            } else {
                console.warn('Failed to load organizations for registration form');
            }
        } catch (error) {
            console.error('Error loading organizations:', error);
        }
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

        // Listen for auth state changes to update navigation
        window.addEventListener('storage', (e) => {
            if (e.key === 'authToken' || e.key === 'currentUser') {
                this.updateNavigation();
                this.updateAccountSection();
            }
        });

        // Listen for custom login event
        window.addEventListener('userLoggedIn', () => {
            this.updateNavigation();
            this.updateAccountSection();
        });
    }
}

// Create singleton instance
const navigationManager = new NavigationManager();

export { navigationManager as Navigation };
export default navigationManager;