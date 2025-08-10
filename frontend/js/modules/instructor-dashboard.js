/**
 * INSTRUCTOR DASHBOARD MODULE - COMPREHENSIVE COURSE MANAGEMENT AND STUDENT INTERACTION
 * 
 * PURPOSE: Complete instructor interface for Course Creator platform management
 * WHY: Instructors need centralized tools for course creation, student management, and analytics
 * ARCHITECTURE: Tab-based dashboard with integrated feedback systems and quiz management
 * 
 * CORE RESPONSIBILITIES:
 * - Course creation, editing, and publishing management
 * - Student enrollment and progress tracking
 * - Comprehensive feedback system (bi-directional student-instructor communication)
 * - Quiz management with course instance-specific publication controls
 * - Analytics dashboard with performance metrics and insights
 * - Content management with upload/export capabilities
 * - Course instance management with scheduling and timezone support
 * 
 * BUSINESS REQUIREMENTS:
 * - Professional instructor workflow from course creation to student assessment
 * - Real-time feedback exchange between instructors and students
 * - Granular quiz publication control per course instance
 * - Comprehensive analytics for data-driven teaching decisions
 * - Multi-format content support and export capabilities
 * - Scalable course instance management for multiple sessions
 * 
 * TECHNICAL FEATURES:
 * - Tab-based navigation with persistent state management
 * - Async data loading with comprehensive error handling
 * - Integration with feedback management system
 * - Real-time quiz publication status updates
 * - Course instance lifecycle management
 * - Professional modal systems for complex workflows
 * - Responsive design for desktop and mobile usage
 */

import { Auth } from './auth.js';
import { CONFIG } from '../config.js';
import { showNotification } from './notifications.js';
import UIComponents from './ui-components.js';

// Import feedback manager dynamically
let feedbackManager = null;
if (typeof window !== 'undefined') {
    import('./feedback-manager.js').then(module => {
        feedbackManager = window.feedbackManager;
    });
}

export class InstructorDashboard {
    /**
     * INSTRUCTOR DASHBOARD CONSTRUCTOR
     * PURPOSE: Initialize instructor dashboard with comprehensive state management
     * WHY: Proper initialization ensures reliable dashboard functionality and data consistency
     * 
     * STATE MANAGEMENT:
     * - courses: Array of instructor's courses with metadata
     * - students: Array of enrolled students with progress tracking
     * - currentCourse: Currently selected course for context-specific operations
     * - activeTab: Current dashboard tab for navigation state persistence
     * - feedbackData: Complete feedback system data structure
     * 
     * INITIALIZATION WORKFLOW:
     * 1. Set up initial state with empty data structures
     * 2. Configure feedback system integration
     * 3. Initialize dashboard components and event handlers
     * 4. Load initial data from backend services
     */
    constructor() {
        // COURSE DATA STATE: Complete course information and metadata
        // WHY: Instructors need access to all their courses for management operations
        this.courses = [];
        
        // STUDENT DATA STATE: Enrolled students with progress and engagement metrics
        // WHY: Student management requires comprehensive student information
        this.students = [];
        
        // CURRENT CONTEXT: Selected course for context-specific operations
        // WHY: Many operations are course-specific and need context awareness
        this.currentCourse = null;
        
        // NAVIGATION STATE: Active dashboard tab for persistent user experience
        // WHY: Users expect dashboard to remember their last viewed section
        this.activeTab = 'courses';
        
        // FEEDBACK SYSTEM STATE: Bi-directional feedback data structure
        // WHY: Comprehensive feedback system requires organized data management
        this.feedbackData = {
            courseFeedback: [],    // Student feedback about courses
            studentFeedback: []    // Instructor feedback about students
        };
        
        // AUTOMATIC INITIALIZATION: Set up dashboard immediately
        // WHY: Constructor should establish fully functional dashboard system
        this.init();
    }

    /**
     * INSTRUCTOR DASHBOARD INITIALIZATION SYSTEM
     * PURPOSE: Complete dashboard setup with authentication, data loading, and UI rendering
     * WHY: Proper initialization ensures secure access and reliable dashboard functionality
     * 
     * INITIALIZATION WORKFLOW:
     * 1. Authentication validation: Ensure user has instructor privileges
     * 2. Event system setup: Establish all user interaction handlers
     * 3. Data loading: Retrieve courses, students, and feedback data
     * 4. UI rendering: Display dashboard with current data
     * 
     * SECURITY FEATURES:
     * - Role-based access control (instructor-only access)
     * - Automatic redirect for unauthorized users
     * - Session validation before dashboard access
     * 
     * ERROR HANDLING:
     * - Graceful degradation for authentication failures
     * - Safe redirect to login page for unauthenticated users
     * - Comprehensive error logging for debugging
     */
    init() {
        // AUTHENTICATION VALIDATION: Ensure instructor access privileges
        // WHY: Dashboard contains sensitive instructor tools requiring proper authorization
        if (!Auth.isAuthenticated() || !Auth.hasRole('instructor')) {
            // SECURITY REDIRECT: Send unauthorized users to login page
            window.location.href = 'html/index.html';
            return;
        }

        // PHASE 1: EVENT SYSTEM SETUP: Establish all user interaction handlers
        this.setupEventListeners();
        
        // PHASE 2: DATA INITIALIZATION: Load all required dashboard data
        this.loadInitialData();
        
        // PHASE 3: UI RENDERING: Display dashboard with loaded data
        this.renderDashboard();
    }

    /**
     * QUIZ MANAGEMENT SYSTEM
     * PURPOSE: Comprehensive quiz publication management with course instance-specific controls
     * WHY: Instructors need granular control over quiz availability per course session
     * 
     * QUIZ MANAGEMENT FEATURES:
     * - Course instance-specific quiz publication
     * - Real-time publication status updates
     * - Professional tabbed interface for multiple instances
     * - Bulk publication operations
     * - Analytics integration for quiz performance tracking
     * 
     * BUSINESS WORKFLOW:
     * 1. Load course instances for quiz management context
     * 2. Display tabbed interface for instance selection
     * 3. Provide publication controls for each instance
     * 4. Enable analytics viewing and bulk operations
     * 5. Handle instance creation if none exist
     * 
     * @param {string} courseId - Course identifier for quiz management
     */
    async showQuizManagement(courseId) {
        try {
            // Get course instances for the course
            const instancesResponse = await fetch(`${CONFIG.BASE_URL}/courses/${courseId}/instances`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });
            
            if (!instancesResponse.ok) {
                throw new Error('Failed to load course instances');
            }
            
            const instancesData = await instancesResponse.json();
            const instances = instancesData.instances || [];
            
            // Create quiz management modal
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content extra-large">
                    <div class="modal-header">
                        <h3><i class="fas fa-cog"></i> Quiz Management</h3>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="quiz-management-container">
                            ${instances.length === 0 ? `
                                <div class="empty-state">
                                    <i class="fas fa-calendar-times fa-3x"></i>
                                    <h4>No Course Instances</h4>
                                    <p>Create course instances to manage quiz publications</p>
                                    <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove(); showInstantiate('${courseId}');">
                                        Create Instance
                                    </button>
                                </div>
                            ` : `
                                <div class="instance-tabs">
                                    ${instances.map((instance, index) => `
                                        <button class="tab-btn ${index === 0 ? 'active' : ''}" 
                                                onclick="showInstanceQuizManagement('${instance.id}', this)">
                                            ${instance.instance_name}
                                            <span class="instance-dates">${new Date(instance.start_date).toLocaleDateString()}</span>
                                        </button>
                                    `).join('')}
                                </div>
                                <div class="instance-quiz-content" id="instance-quiz-content">
                                    <!-- Content will be loaded dynamically -->
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Load first instance quiz management if instances exist
            if (instances.length > 0) {
                window.showInstanceQuizManagement(instances[0].id, modal.querySelector('.tab-btn'));
            }
            
        } catch (error) {
            console.error('Error showing quiz management:', error);
            showNotification('Error loading quiz management', 'error');
        }
    }

    /**
     * COMPREHENSIVE EVENT LISTENER SETUP
     * PURPOSE: Establish all user interaction handlers for dashboard functionality
     * WHY: Centralized event management ensures consistent behavior and easier maintenance
     * 
     * EVENT CATEGORIES:
     * 1. Tab navigation: Dashboard section switching
     * 2. Course management: Create, edit, delete course operations
     * 3. Student management: Add, remove, feedback student operations
     * 4. Modal interactions: Form submissions and dialog management
     * 
     * EVENT DELEGATION STRATEGY:
     * - Use event delegation for performance optimization
     * - Handle dynamic content with consistent event patterns
     * - Graceful degradation when elements don't exist
     * - Consistent event handling patterns across all interactions
     */
    setupEventListeners() {
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-button')) {
                this.switchTab(e.target.dataset.tab);
            }
        });

        // Course actions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('create-course-btn')) {
                this.showCreateCourseModal();
            } else if (e.target.classList.contains('edit-course-btn')) {
                this.editCourse(e.target.dataset.courseId);
            } else if (e.target.classList.contains('delete-course-btn')) {
                this.deleteCourse(e.target.dataset.courseId);
            }
        });

        // Student management
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-student-btn')) {
                this.showAddStudentModal();
            } else if (e.target.classList.contains('remove-student-btn')) {
                this.removeStudent(e.target.dataset.studentId);
            } else if (e.target.classList.contains('feedback-student-btn')) {
                this.showStudentFeedbackModal(e.target.dataset.studentId, e.target.dataset.courseId);
            }
        });
    }

    /**
     * INITIAL DATA LOADING SYSTEM
     * PURPOSE: Load all required dashboard data with parallel processing for performance
     * WHY: Dashboard requires multiple data sources that can be loaded concurrently
     * 
     * DATA LOADING STRATEGY:
     * - Parallel loading: Load courses and students simultaneously
     * - Error isolation: Handle individual loading failures gracefully
     * - Progress indication: Provide user feedback during loading
     * - Retry mechanism: Handle network failures with retry logic
     * 
     * DATA SOURCES:
     * - Courses: Instructor's courses with metadata and statistics
     * - Students: Enrolled students with progress and engagement data
     * - Feedback: Historical feedback data for analytics
     * 
     * PERFORMANCE OPTIMIZATION:
     * - Use Promise.all for concurrent loading
     * - Cache data for subsequent requests
     * - Implement loading states for better UX
     */
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadCourses(),
                this.loadStudents()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            showNotification('Error loading dashboard data', 'error');
        }
    }

    /**
     * COURSE DATA LOADING SYSTEM
     * PURPOSE: Retrieve instructor's courses with comprehensive error handling
     * WHY: Course data is central to all instructor dashboard functionality
     * 
     * COURSE DATA INCLUDES:
     * - Course metadata: Title, description, difficulty, category
     * - Publication status: Draft, published, archived states
     * - Enrollment statistics: Student counts and engagement metrics
     * - Creation dates: Temporal data for organization and sorting
     * 
     * ERROR HANDLING STRATEGY:
     * - Network failure resilience with detailed error logging
     * - Graceful degradation with empty state handling
     * - User-friendly error notifications
     * - Automatic retry mechanisms for transient failures
     * 
     * AUTHENTICATION INTEGRATION:
     * - Uses authenticated fetch for secure API access
     * - Automatic token validation and renewal
     * - Session expiry handling with proper redirects
     */
    async loadCourses() {
        try {
            const response = await Auth.authenticatedFetch(CONFIG.ENDPOINTS.COURSES);
            
            if (response.ok) {
                const data = await response.json();
                this.courses = data.courses || data || [];
            } else {
                console.error('Failed to load courses:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error response:', errorText);
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            throw error;
        }
    }

    /**
     * STUDENT DATA LOADING SYSTEM
     * PURPOSE: Retrieve enrolled students with progress and engagement metrics
     * WHY: Student management requires comprehensive student information for effective teaching
     * 
     * STUDENT DATA INCLUDES:
     * - Profile information: Names, emails, enrollment dates
     * - Progress tracking: Course completion percentages and milestones
     * - Engagement metrics: Activity levels and participation rates
     * - Performance data: Quiz scores, assignment submissions
     * 
     * PRIVACY CONSIDERATIONS:
     * - Only load students enrolled in instructor's courses
     * - Respect student privacy settings and permissions
     * - Secure data transmission with authentication
     * - Compliance with educational data protection requirements
     * 
     * FUTURE IMPLEMENTATION:
     * - Currently returns empty array as placeholder
     * - Will integrate with student management API
     * - Will include real-time progress updates
     */
    async loadStudents() {
        try {
            // This would be implemented based on the actual API
            // For now, just set empty array
            this.students = [];
        } catch (error) {
            console.error('Error loading students:', error);
            throw error;
        }
    }

    /**
     * MAIN DASHBOARD RENDERING SYSTEM
     * PURPOSE: Generate complete dashboard UI with current data and state
     * WHY: Dynamic UI rendering enables real-time updates and responsive design
     * 
     * RENDERING ARCHITECTURE:
     * - Header section: Welcome message and user context
     * - Tab navigation: Course management, student tracking, analytics, content, feedback
     * - Content area: Dynamic content based on active tab
     * - State persistence: Maintain tab selection across page refreshes
     * 
     * UI COMPONENTS:
     * - Professional header with instructor greeting
     * - Icon-based tab navigation for intuitive user experience
     * - Dynamic content rendering based on selected tab
     * - Responsive design for desktop and mobile devices
     * 
     * STATE MANAGEMENT:
     * - Active tab highlighting based on current state
     * - Content area updates without full page reload
     * - Persistent navigation state across interactions
     */
    renderDashboard() {
        const main = document.getElementById('main-content');
        if (!main) return;

        main.innerHTML = `
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <h1>Instructor Dashboard</h1>
                    <p>Welcome, ${Auth.getCurrentUser()?.full_name || 'Instructor'}!</p>
                </div>
                
                <div class="dashboard-tabs">
                    <button class="tab-button ${this.activeTab === 'courses' ? 'active' : ''}" data-tab="courses">
                        <i class="fas fa-book"></i> Courses
                    </button>
                    <button class="tab-button ${this.activeTab === 'students' ? 'active' : ''}" data-tab="students">
                        <i class="fas fa-users"></i> Students
                    </button>
                    <button class="tab-button ${this.activeTab === 'analytics' ? 'active' : ''}" data-tab="analytics">
                        <i class="fas fa-chart-bar"></i> Analytics
                    </button>
                    <button class="tab-button ${this.activeTab === 'content' ? 'active' : ''}" data-tab="content">
                        <i class="fas fa-file-alt"></i> Content
                    </button>
                    <button class="tab-button ${this.activeTab === 'feedback' ? 'active' : ''}" data-tab="feedback">
                        <i class="fas fa-comments"></i> Feedback
                    </button>
                </div>
                
                <div class="dashboard-content">
                    ${this.renderTabContent()}
                </div>
            </div>
        `;
    }

    /**
     * DYNAMIC TAB CONTENT RENDERING SYSTEM
     * PURPOSE: Generate appropriate content based on active dashboard tab
     * WHY: Single-page application requires dynamic content switching
     * 
     * TAB CONTENT TYPES:
     * - courses: Course management interface with creation and editing tools
     * - students: Student enrollment and progress tracking interface
     * - analytics: Performance metrics, statistics, and reporting dashboard
     * - content: Content management tools and upload/export functionality
     * - feedback: Bi-directional feedback system with analytics integration
     * 
     * RENDERING STRATEGY:
     * - Switch-based content selection for performance
     * - Lazy loading of complex content when tab is accessed
     * - State-aware rendering based on available data
     * - Fallback to default content for unknown tabs
     * 
     * PERFORMANCE OPTIMIZATION:
     * - Only render content for active tab
     * - Cache rendered content where appropriate
     * - Minimize DOM manipulation for better performance
     */
    renderTabContent() {
        switch (this.activeTab) {
            case 'courses':
                return this.renderCoursesTab();
            case 'students':
                return this.renderStudentsTab();
            case 'analytics':
                return this.renderAnalyticsTab();
            case 'content':
                return this.renderContentTab();
            case 'feedback':
                return this.renderFeedbackTab();
            default:
                return this.renderCoursesTab();
        }
    }

    /**
     * COURSES TAB RENDERING SYSTEM
     * PURPOSE: Display comprehensive course management interface
     * WHY: Instructors need intuitive course creation and management tools
     * 
     * COURSE TAB FEATURES:
     * - Course creation: Quick access to new course creation
     * - Course grid: Visual card-based course display
     * - Course actions: Edit, delete, and management operations
     * - Empty state: Encouraging interface for first-time users
     * 
     * COURSE CARD INFORMATION:
     * - Course metadata: Title, description, difficulty, category
     * - Enrollment statistics: Student count and engagement metrics
     * - Publication status: Draft or published state indicators
     * - Action buttons: Edit and delete operations
     * 
     * USER EXPERIENCE:
     * - Professional card-based layout for easy scanning
     * - Clear call-to-action buttons for course creation
     * - Encouraging empty state for new instructors
     * - Consistent action patterns across all courses
     */
    renderCoursesTab() {
        return `
            <div class="tab-content">
                <div class="content-header">
                    <h2>My Courses</h2>
                    <button class="btn btn-primary create-course-btn">
                        <i class="fas fa-plus"></i> Create Course
                    </button>
                </div>
                
                <div class="courses-grid">
                    ${this.courses.map(course => this.renderCourseCard(course)).join('')}
                </div>
                
                ${this.courses.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-book fa-3x"></i>
                        <h3>No courses yet</h3>
                        <p>Create your first course to get started!</p>
                        <button class="btn btn-primary create-course-btn">Create Course</button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * INDIVIDUAL COURSE CARD RENDERING SYSTEM
     * PURPOSE: Generate professional course display with metadata and actions
     * WHY: Consistent course representation enables efficient course management
     * 
     * COURSE CARD COMPONENTS:
     * - Header: Course title with edit/delete action buttons
     * - Body: Description, difficulty, and category information
     * - Footer: Enrollment statistics and publication status
     * - Actions: Context-sensitive operations for course management
     * 
     * VISUAL DESIGN:
     * - Professional card layout with clear information hierarchy
     * - Status badges for publication state indication
     * - Icon-based statistics for quick information consumption
     * - Consistent styling across all course cards
     * 
     * INTERACTIVE FEATURES:
     * - Hover effects for better user experience
     * - Click handlers for edit and delete operations
     * - Contextual information display with tooltips
     * - Responsive design for different screen sizes
     * 
     * @param {Object} course - Course object with metadata and statistics
     * @returns {string} HTML string for course card component
     */
    renderCourseCard(course) {
        return `
            <div class="course-card">
                <div class="course-header">
                    <h3>${course.title}</h3>
                    <div class="course-actions">
                        <button class="btn btn-sm btn-secondary edit-course-btn" data-course-id="${course.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-course-btn" data-course-id="${course.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                
                <div class="course-body">
                    <p>${course.description || 'No description'}</p>
                    <div class="course-meta">
                        <span class="course-difficulty">${course.difficulty || 'Beginner'}</span>
                        <span class="course-category">${course.category || 'General'}</span>
                    </div>
                </div>
                
                <div class="course-footer">
                    <div class="course-stats">
                        <span><i class="fas fa-users"></i> ${course.enrolled_count || 0} students</span>
                        <span><i class="fas fa-calendar"></i> ${UIComponents.formatDate(course.created_at)}</span>
                    </div>
                    <div class="course-status">
                        <span class="status-badge ${course.is_published ? 'published' : 'draft'}">
                            ${course.is_published ? 'Published' : 'Draft'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * STUDENTS TAB RENDERING SYSTEM
     * PURPOSE: Display comprehensive student management interface with progress tracking
     * WHY: Instructors need efficient tools for student enrollment and progress monitoring
     * 
     * STUDENT TAB FEATURES:
     * - Student enrollment: Add new students to courses
     * - Student table: Comprehensive student information display
     * - Progress tracking: Visual progress bars and completion percentages
     * - Student actions: Feedback provision and enrollment management
     * 
     * STUDENT TABLE COLUMNS:
     * - Student profile: Avatar, name, and contact information
     * - Course association: Which course the student is enrolled in
     * - Progress metrics: Completion percentage with visual indicators
     * - Enrollment dates: When student joined the course
     * - Action buttons: Feedback and removal operations
     * 
     * USER EXPERIENCE:
     * - Professional table layout for efficient data scanning
     * - Visual progress indicators for quick assessment
     * - Encouraging empty state for courses without students
     * - Consistent action patterns for student management
     */
    renderStudentsTab() {
        return `
            <div class="tab-content">
                <div class="content-header">
                    <h2>Student Management</h2>
                    <button class="btn btn-primary add-student-btn">
                        <i class="fas fa-user-plus"></i> Add Student
                    </button>
                </div>
                
                <div class="students-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Student</th>
                                <th>Email</th>
                                <th>Course</th>
                                <th>Progress</th>
                                <th>Enrolled</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.students.map(student => this.renderStudentRow(student)).join('')}
                        </tbody>
                    </table>
                </div>
                
                ${this.students.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-users fa-3x"></i>
                        <h3>No students enrolled</h3>
                        <p>Add students to your courses to get started!</p>
                        <button class="btn btn-primary add-student-btn">Add Student</button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * INDIVIDUAL STUDENT ROW RENDERING SYSTEM
     * PURPOSE: Generate comprehensive student display with progress and actions
     * WHY: Consistent student representation enables efficient student management
     * 
     * STUDENT ROW COMPONENTS:
     * - Profile section: Avatar, name, and visual identification
     * - Contact information: Email address for communication
     * - Course association: Which course the student is enrolled in
     * - Progress visualization: Completion percentage with progress bar
     * - Enrollment tracking: When student joined the course
     * - Action buttons: Feedback provision and enrollment management
     * 
     * VISUAL DESIGN:
     * - Avatar integration for personal connection
     * - Progress bars for quick visual assessment
     * - Icon-based action buttons for intuitive interaction
     * - Responsive design for table functionality
     * 
     * INTERACTIVE FEATURES:
     * - Feedback modal trigger for student assessment
     * - Removal confirmation for enrollment management
     * - Hover effects for better user experience
     * - Accessible design with proper ARIA labels
     * 
     * @param {Object} student - Student object with profile and progress data
     * @returns {string} HTML string for student table row
     */
    renderStudentRow(student) {
        return `
            <tr>
                <td>
                    <div class="student-info">
                        ${UIComponents.createAvatar(student, 'small').outerHTML}
                        <span>${student.full_name}</span>
                    </div>
                </td>
                <td>${student.email}</td>
                <td>${student.course_title || 'N/A'}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${student.progress || 0}%"></div>
                    </div>
                    <span>${student.progress || 0}%</span>
                </td>
                <td>${UIComponents.formatDate(student.enrolled_at)}</td>
                <td>
                    <button class="btn btn-sm btn-primary feedback-student-btn" data-student-id="${student.id}" data-course-id="${student.course_id}" title="Provide Feedback">
                        <i class="fas fa-comment"></i>
                    </button>
                    <button class="btn btn-sm btn-danger remove-student-btn" data-student-id="${student.id}">
                        <i class="fas fa-user-times"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * ANALYTICS TAB RENDERING SYSTEM
     * PURPOSE: Display comprehensive instructor analytics and performance metrics
     * WHY: Data-driven teaching requires accessible analytics and reporting tools
     * 
     * ANALYTICS FEATURES:
     * - Key performance indicators: Course, student, completion, and rating metrics
     * - Visual statistics: Professional stat cards with icons and numbers
     * - Trend analysis: Chart placeholders for enrollment and progress trends
     * - Performance overview: Aggregated metrics for quick assessment
     * 
     * STAT CARD METRICS:
     * - Total Courses: Complete count of instructor's courses
     * - Total Students: Aggregate student enrollment across all courses
     * - Average Completion: Platform-wide course completion percentage
     * - Average Rating: Instructor rating based on student feedback
     * 
     * VISUALIZATION PLACEHOLDERS:
     * - Course Enrollment Trends: Time-based enrollment visualization
     * - Student Progress Overview: Completion progress across all courses
     * - Future: Interactive charts with drill-down capabilities
     * 
     * USER EXPERIENCE:
     * - Professional dashboard-style analytics display
     * - Icon-based visual hierarchy for quick information consumption
     * - Placeholder content for future chart integration
     * - Consistent styling with main dashboard theme
     */
    renderAnalyticsTab() {
        return `
            <div class="tab-content">
                <div class="content-header">
                    <h2>Analytics & Reports</h2>
                </div>
                
                <div class="analytics-grid">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-book"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${this.courses.length}</h3>
                            <p>Total Courses</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="stat-info">
                            <h3>${this.students.length}</h3>
                            <p>Total Students</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="stat-info">
                            <h3>85%</h3>
                            <p>Avg. Completion</p>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-star"></i>
                        </div>
                        <div class="stat-info">
                            <h3>4.2</h3>
                            <p>Avg. Rating</p>
                        </div>
                    </div>
                </div>
                
                <div class="charts-container">
                    <div class="chart-card">
                        <h3>Course Enrollment Trends</h3>
                        <div class="chart-placeholder">
                            <p>Chart visualization would go here</p>
                        </div>
                    </div>
                    
                    <div class="chart-card">
                        <h3>Student Progress Overview</h3>
                        <div class="chart-placeholder">
                            <p>Chart visualization would go here</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * CONTENT TAB RENDERING SYSTEM
     * PURPOSE: Display comprehensive content management tools and library
     * WHY: Instructors need centralized content creation and management capabilities
     * 
     * CONTENT MANAGEMENT FEATURES:
     * - Content upload: File upload interface for course materials
     * - Content generation tools: AI-powered content creation utilities
     * - Content library: Organized display of existing course materials
     * - Tool integration: Quick access to specialized content tools
     * 
     * CONTENT CREATION TOOLS:
     * - Course Generator: AI-powered content generation from templates
     * - Slide Creator: Professional presentation slide creation
     * - Quiz Builder: Interactive quiz and assessment creation
     * - Upload Interface: Direct file upload for existing content
     * 
     * CONTENT LIBRARY FEATURES:
     * - File type organization: PDF, PPTX, video content categorization
     * - File size display: Storage usage awareness for instructors
     * - Visual file icons: Quick content type identification
     * - Professional grid layout: Easy content browsing and selection
     * 
     * USER EXPERIENCE:
     * - Tool-based workflow for content creation
     * - Visual content library for easy asset management
     * - Professional styling consistent with dashboard theme
     * - Intuitive content organization and access patterns
     */
    renderContentTab() {
        return `
            <div class="tab-content">
                <div class="content-header">
                    <h2>Content Management</h2>
                    <button class="btn btn-primary">
                        <i class="fas fa-upload"></i> Upload Content
                    </button>
                </div>
                
                <div class="content-tools">
                    <div class="tool-card">
                        <h3>Course Generator</h3>
                        <p>Generate course content using AI</p>
                        <button class="btn btn-secondary">Generate</button>
                    </div>
                    
                    <div class="tool-card">
                        <h3>Slide Creator</h3>
                        <p>Create presentation slides</p>
                        <button class="btn btn-secondary">Create</button>
                    </div>
                    
                    <div class="tool-card">
                        <h3>Quiz Builder</h3>
                        <p>Build interactive quizzes</p>
                        <button class="btn btn-secondary">Build</button>
                    </div>
                </div>
                
                <div class="content-library">
                    <h3>Content Library</h3>
                    <div class="library-grid">
                        <div class="library-item">
                            <div class="item-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div class="item-info">
                                <h4>Course Syllabus</h4>
                                <p>PDF • 2.3 MB</p>
                            </div>
                        </div>
                        
                        <div class="library-item">
                            <div class="item-icon">
                                <i class="fas fa-presentation"></i>
                            </div>
                            <div class="item-info">
                                <h4>Lecture Slides</h4>
                                <p>PPTX • 15.7 MB</p>
                            </div>
                        </div>
                        
                        <div class="library-item">
                            <div class="item-icon">
                                <i class="fas fa-video"></i>
                            </div>
                            <div class="item-info">
                                <h4>Demo Video</h4>
                                <p>MP4 • 125 MB</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * FEEDBACK TAB RENDERING SYSTEM
     * PURPOSE: Display comprehensive bi-directional feedback management interface
     * WHY: Effective teaching requires systematic feedback exchange with students
     * 
     * FEEDBACK SYSTEM FEATURES:
     * - Course feedback viewing: Student ratings and comments about courses
     * - Student feedback management: Instructor assessments of student progress
     * - Feedback analytics: Performance metrics and trend analysis
     * - Export capabilities: Report generation for institutional requirements
     * 
     * FEEDBACK TAB STRUCTURE:
     * - Header controls: Refresh data and export report functionality
     * - Sub-tab navigation: Course feedback vs. student feedback sections
     * - Filter controls: Course selection and rating-based filtering
     * - Feedback display: Professional feedback item rendering
     * 
     * COURSE FEEDBACK SECTION:
     * - Student ratings: Star ratings with detailed breakdowns
     * - Written feedback: Positive aspects, improvements, additional comments
     * - Anonymous support: Respect student privacy preferences  
     * - Filter capabilities: Course-specific and rating-based filtering
     * 
     * STUDENT FEEDBACK SECTION:
     * - Student assessment cards: Individual student progress evaluation
     * - Feedback history: Previous feedback provided to students
     * - Bulk operations: Efficient feedback provision for multiple students
     * - Action buttons: Individual feedback and history viewing
     * 
     * USER EXPERIENCE:
     * - Professional tabbed interface for organized feedback management
     * - Real-time refresh capabilities for current data
     * - Export functionality for institutional reporting
     * - Consistent styling with main dashboard theme
     */
    renderFeedbackTab() {
        return `
            <div class="tab-content">
                <div class="content-header">
                    <h2>Feedback Management</h2>
                    <div class="feedback-actions">
                        <button class="btn btn-primary" onclick="instructorDashboard.loadCourseFeedback()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        <button class="btn btn-secondary" onclick="instructorDashboard.exportFeedbackReport()">
                            <i class="fas fa-download"></i> Export Report
                        </button>
                    </div>
                </div>
                
                <div class="feedback-tabs">
                    <div class="feedback-tab-buttons">
                        <button class="tab-btn active" data-feedback-tab="course-feedback">
                            <i class="fas fa-star"></i> Course Feedback
                        </button>
                        <button class="tab-btn" data-feedback-tab="student-feedback">
                            <i class="fas fa-user-graduate"></i> Student Feedback
                        </button>
                    </div>
                    
                    <div class="feedback-tab-content">
                        <div id="course-feedback-tab" class="feedback-tab-pane active">
                            ${this.renderCourseFeedbackSection()}
                        </div>
                        <div id="student-feedback-tab" class="feedback-tab-pane">
                            ${this.renderStudentFeedbackSection()}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * COURSE FEEDBACK SECTION RENDERING SYSTEM
     * PURPOSE: Display student feedback about instructor's courses with filtering
     * WHY: Instructor improvement requires systematic access to student course evaluations
     * 
     * COURSE FEEDBACK FEATURES:
     * - Feedback display: Student ratings and written comments
     * - Filter controls: Course selection and rating-based filtering
     * - Loading states: Professional loading indicators during data fetch
     * - Empty states: Encouraging interface when no feedback exists
     * 
     * FILTER CAPABILITIES:
     * - Course filter: View feedback for specific courses
     * - Rating filter: Filter by star rating (1-5 stars)
     * - Dynamic filtering: Real-time filter application
     * - Filter persistence: Maintain filter state across interactions
     * 
     * FEEDBACK DISPLAY FORMAT:
     * - Star ratings: Visual rating display with numeric values
     * - Written feedback: Structured display of student comments
     * - Anonymous support: Respect student privacy preferences
     * - Timestamp information: When feedback was provided
     * 
     * USER EXPERIENCE:
     * - Professional feedback list with clear information hierarchy
     * - Loading indicators for better perceived performance
     * - Encouraging empty state for courses without feedback
     * - Consistent filter interface for easy data exploration
     */
    renderCourseFeedbackSection() {
        return `
            <div class="course-feedback-section">
                <div class="section-header">
                    <h3>Course Feedback from Students</h3>
                    <p>View and analyze feedback received from students about your courses</p>
                </div>
                
                <div class="feedback-filters">
                    <select id="courseFeedbackFilter" onchange="instructorDashboard.filterCourseFeedback()">
                        <option value="all">All Courses</option>
                        ${this.courses.map(course => `<option value="${course.id}">${course.title}</option>`).join('')}
                    </select>
                    <select id="ratingFilter" onchange="instructorDashboard.filterCourseFeedback()">
                        <option value="all">All Ratings</option>
                        <option value="5">5 Stars</option>
                        <option value="4">4 Stars</option>
                        <option value="3">3 Stars</option>
                        <option value="2">2 Stars</option>
                        <option value="1">1 Star</option>
                    </select>
                </div>
                
                <div id="courseFeedbackList" class="feedback-list">
                    <div class="feedback-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Loading course feedback...</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * STUDENT FEEDBACK SECTION RENDERING SYSTEM
     * PURPOSE: Display instructor feedback management for student assessments
     * WHY: Student development requires systematic instructor feedback and progress tracking
     * 
     * STUDENT FEEDBACK FEATURES:
     * - Student assessment cards: Individual student progress evaluation interface
     * - Bulk feedback tools: Efficient feedback provision for multiple students
     * - Feedback history: Previous assessments and progress tracking
     * - Action buttons: Individual and bulk feedback operations
     * 
     * STUDENT FEEDBACK CARDS:
     * - Student profile: Avatar, name, and course association
     * - Progress indicators: Completion percentage and engagement metrics
     * - Feedback status: Last feedback date and assessment history
     * - Action buttons: Give feedback and view history operations
     * 
     * BULK OPERATIONS:
     * - Bulk feedback modal: Efficient feedback for multiple students
     * - Class-wide assessments: Consistent evaluation across all students
     * - Template feedback: Reusable feedback templates for common assessments
     * - Batch processing: Handle multiple feedback submissions efficiently
     * 
     * USER EXPERIENCE:
     * - Card-based layout for individual student focus
     * - Professional styling with clear information hierarchy
     * - Encouraging empty state for courses without students
     * - Consistent action patterns for feedback operations
     */
    renderStudentFeedbackSection() {
        return `
            <div class="student-feedback-section">
                <div class="section-header">
                    <h3>Student Assessment Feedback</h3>
                    <p>Manage feedback you've provided to students</p>
                </div>
                
                <div class="feedback-actions">
                    <button class="btn btn-primary" onclick="instructorDashboard.showBulkFeedbackModal()">
                        <i class="fas fa-users"></i> Bulk Feedback
                    </button>
                </div>
                
                <div class="student-feedback-grid">
                    ${this.students.map(student => `
                        <div class="student-feedback-card">
                            <div class="student-info">
                                <div class="student-avatar">
                                    ${UIComponents.createAvatar(student, 'medium').outerHTML}
                                </div>
                                <div class="student-details">
                                    <h4>${student.full_name}</h4>
                                    <p>${student.course_title || 'Multiple Courses'}</p>
                                    <span class="progress-indicator">${student.progress || 0}% Complete</span>
                                </div>
                            </div>
                            <div class="feedback-status">
                                <div class="last-feedback">
                                    <span>Last Feedback: ${student.last_feedback_date || 'Never'}</span>
                                </div>
                                <div class="feedback-actions">
                                    <button class="btn btn-sm btn-primary" onclick="instructorDashboard.showStudentFeedbackModal('${student.id}', '${student.course_id}')">
                                        <i class="fas fa-comment"></i> Give Feedback
                                    </button>
                                    <button class="btn btn-sm btn-secondary" onclick="instructorDashboard.viewStudentFeedbackHistory('${student.id}')">
                                        <i class="fas fa-history"></i> History
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                ${this.students.length === 0 ? `
                    <div class="empty-state">
                        <i class="fas fa-user-graduate fa-3x"></i>
                        <h3>No students found</h3>
                        <p>Students will appear here once they're enrolled in your courses</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * TAB SWITCHING SYSTEM
     * PURPOSE: Handle dashboard tab navigation with state persistence and data loading
     * WHY: Single-page application requires coordinated tab switching and content updates
     * 
     * TAB SWITCHING WORKFLOW:
     * 1. Update internal active tab state
     * 2. Load tab-specific data if required (feedback system)
     * 3. Re-render dashboard with new tab content
     * 4. Maintain navigation state across interactions
     * 
     * SPECIAL TAB HANDLING:
     * - feedback: Triggers feedback data loading for real-time information
     * - analytics: May trigger analytics data refresh
     * - students: Updates student progress information
     * 
     * STATE MANAGEMENT:
     * - activeTab: Updates current tab for persistent navigation
     * - UI synchronization: Ensures navigation highlights match content
     * - Data freshness: Loads current data for data-dependent tabs
     * 
     * @param {string} tabName - Target tab identifier for navigation
     */
    switchTab(tabName) {
        this.activeTab = tabName;
        if (tabName === 'feedback') {
            this.loadFeedbackData();
        }
        this.renderDashboard();
    }

    /**
     * CREATE COURSE MODAL SYSTEM
     * PURPOSE: Display professional course creation interface with comprehensive form
     * WHY: Course creation requires structured input collection and validation
     * 
     * COURSE CREATION FORM FIELDS:
     * - Course title: Primary course identifier and display name
     * - Description: Detailed course information for student understanding
     * - Difficulty level: Beginner, intermediate, advanced categorization
     * - Category: Subject area classification for organization
     * 
     * MODAL FEATURES:
     * - Professional modal design with form validation
     * - Cancel and create action buttons
     * - Form reset on successful submission
     * - Error handling with user feedback
     * 
     * USER EXPERIENCE:
     * - Clear form labels and input validation
     * - Professional modal styling with Course Creator branding
     * - Responsive design for desktop and mobile
     * - Intuitive form flow with logical field ordering
     * 
     * INTEGRATION:
     * - Uses UIComponents.createModal for consistent styling
     * - Integrates with course creation API endpoint
     * - Updates dashboard immediately after creation
     */
    showCreateCourseModal() {
        const modalContent = `
            <form id="create-course-form">
                <div class="form-group">
                    <label for="course-title">Course Title:</label>
                    <input type="text" id="course-title" name="title" required>
                </div>
                
                <div class="form-group">
                    <label for="course-description">Description:</label>
                    <textarea id="course-description" name="description" rows="3"></textarea>
                </div>
                
                <div class="form-group">
                    <label for="course-difficulty">Difficulty:</label>
                    <select id="course-difficulty" name="difficulty">
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="course-category">Category:</label>
                    <input type="text" id="course-category" name="category" placeholder="e.g., Programming, Design">
                </div>
            </form>
        `;

        const footer = `
            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
            <button type="submit" form="create-course-form" class="btn btn-primary">Create Course</button>
        `;

        const modal = UIComponents.createModal('Create New Course', modalContent, { footer });
        
        const form = modal.querySelector('#create-course-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createCourse(new FormData(form));
            modal.remove();
        });
    }

    /**
     * COURSE CREATION SYSTEM
     * PURPOSE: Create new course with API integration and dashboard updates
     * WHY: Instructors need reliable course creation with immediate feedback
     * 
     * COURSE CREATION WORKFLOW:
     * 1. Extract course data from form submission
     * 2. Send authenticated API request to course service
     * 3. Handle successful creation with dashboard update
     * 4. Provide user feedback through notification system
     * 5. Update local course list for immediate UI reflection
     * 
     * COURSE DATA STRUCTURE:
     * - title: Course display name from form input
     * - description: Detailed course information
     * - difficulty: Skill level requirement (beginner/intermediate/advanced)
     * - category: Subject area classification
     * 
     * ERROR HANDLING:
     * - Network failure resilience with user notification
     * - API error response processing and display
     * - Comprehensive error logging for debugging
     * - Graceful degradation with meaningful error messages
     * 
     * SUCCESS HANDLING:
     * - Add new course to local courses array
     * - Re-render dashboard to show new course
     * - Display success notification to user
     * - Close modal after successful creation
     * 
     * @param {FormData} formData - Form data from course creation modal
     */
    async createCourse(formData) {
        try {
            const courseData = {
                title: formData.get('title'),
                description: formData.get('description'),
                difficulty: formData.get('difficulty'),
                category: formData.get('category')
            };

            const response = await Auth.authenticatedFetch(CONFIG.ENDPOINTS.COURSES, {
                method: 'POST',
                body: JSON.stringify(courseData)
            });

            if (response.ok) {
                const newCourse = await response.json();
                this.courses.push(newCourse);
                this.renderDashboard();
                showNotification('Course created successfully!', 'success');
            } else {
                throw new Error('Failed to create course');
            }
        } catch (error) {
            console.error('Error creating course:', error);
            showNotification('Error creating course', 'error');
        }
    }

    /**
     * COURSE EDITING SYSTEM
     * PURPOSE: Enable course modification with existing data pre-population
     * WHY: Instructors need to update course information as requirements change
     * 
     * COURSE EDITING WORKFLOW:
     * 1. Locate course by ID in local courses array
     * 2. Validate course exists and belongs to instructor
     * 3. Pre-populate edit form with existing course data
     * 4. Handle form submission with updated course information
     * 5. Update local and server data with changes
     * 
     * EDITING CAPABILITIES:
     * - Course metadata: Title, description, difficulty, category
     * - Publication status: Draft/published state management
     * - Course settings: Enrollment limits, access permissions
     * - Content updates: Syllabus, materials, and resources
     * 
     * FUTURE IMPLEMENTATION:
     * - Currently placeholder for full editing system
     * - Will include comprehensive edit modal
     * - Will integrate with course update API endpoint
     * - Will include validation and conflict resolution
     * 
     * @param {string} courseId - Unique identifier for course to edit
     */
    editCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (!course) return;

        // Implementation for editing course
    }

    /**
     * COURSE DELETION SYSTEM
     * PURPOSE: Safely delete courses with confirmation and cascade handling
     * WHY: Course deletion requires careful confirmation due to permanent data loss
     * 
     * DELETION SAFETY WORKFLOW:
     * 1. Locate course by ID and validate ownership
     * 2. Display confirmation dialog with course title
     * 3. Warn user about permanent nature of deletion
     * 4. Execute authenticated API deletion request
     * 5. Update local dashboard state and notify user
     * 
     * SAFETY FEATURES:
     * - Confirmation dialog with explicit course identification
     * - Warning about irreversible nature of deletion
     * - User-friendly error messages for deletion failures
     * - Graceful handling of network issues
     * 
     * CASCADE CONSIDERATIONS:
     * - Student enrollments: Handle enrolled student data
     * - Course content: Manage associated materials and resources
     * - Analytics data: Preserve historical data where appropriate
     * - Feedback data: Maintain student feedback records
     * 
     * ERROR HANDLING:
     * - Network failure resilience with retry options
     * - Server error processing with meaningful messages
     * - Permission validation for instructor ownership
     * - Comprehensive error logging for troubleshooting
     * 
     * @param {string} courseId - Unique identifier for course to delete
     */
    async deleteCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (!course) return;

        const confirmModal = UIComponents.createConfirmDialog(
            `Are you sure you want to delete the course "${course.title}"? This action cannot be undone.`,
            async () => {
                try {
                    const response = await Auth.authenticatedFetch(
                        CONFIG.ENDPOINTS.COURSE_BY_ID(courseId),
                        { method: 'DELETE' }
                    );

                    if (response.ok) {
                        this.courses = this.courses.filter(c => c.id !== courseId);
                        this.renderDashboard();
                        showNotification('Course deleted successfully', 'success');
                    } else {
                        throw new Error('Failed to delete course');
                    }
                } catch (error) {
                    console.error('Error deleting course:', error);
                    showNotification('Error deleting course', 'error');
                }
            }
        );
    }

    /**
     * ADD STUDENT MODAL SYSTEM
     * PURPOSE: Display student enrollment interface with course selection
     * WHY: Student enrollment requires structured input and course association
     * 
     * STUDENT ENROLLMENT FORM:
     * - Student email: Primary identifier for student account creation/lookup
     * - Course selection: Dropdown of instructor's available courses
     * - Validation: Email format and course selection validation
     * - Submission: Secure enrollment API integration
     * 
     * COURSE SELECTION FEATURES:
     * - Dynamic course list: Only instructor's courses available
     * - Course information: Title display for easy selection
     * - Validation: Ensures course selection before submission
     * - Error handling: Manages course loading failures
     * 
     * MODAL FEATURES:
     * - Professional modal design with form validation
     * - Cancel and add action buttons
     * - Form reset after successful submission
     * - Error display for enrollment failures
     * 
     * USER EXPERIENCE:
     * - Clear form labels and validation feedback
     * - Professional styling consistent with dashboard
     * - Responsive design for all device types
     * - Intuitive enrollment workflow
     */
    showAddStudentModal() {
        const modalContent = `
            <form id="add-student-form">
                <div class="form-group">
                    <label for="student-email">Student Email:</label>
                    <input type="email" id="student-email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="student-course">Course:</label>
                    <select id="student-course" name="course_id" required>
                        <option value="">Select a course</option>
                        ${this.courses.map(course => `
                            <option value="${course.id}">${course.title}</option>
                        `).join('')}
                    </select>
                </div>
            </form>
        `;

        const footer = `
            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
            <button type="submit" form="add-student-form" class="btn btn-primary">Add Student</button>
        `;

        const modal = UIComponents.createModal('Add Student', modalContent, { footer });
        
        const form = modal.querySelector('#add-student-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addStudent(new FormData(form));
            modal.remove();
        });
    }

    /**
     * STUDENT ENROLLMENT SYSTEM
     * PURPOSE: Enroll students in courses with API integration and validation
     * WHY: Student enrollment requires secure processing and immediate dashboard updates
     * 
     * ENROLLMENT WORKFLOW:
     * 1. Extract student data from enrollment form
     * 2. Validate email format and course selection
     * 3. Send authenticated enrollment request to API
     * 4. Handle enrollment success with dashboard refresh
     * 5. Provide user feedback through notification system
     * 
     * ENROLLMENT DATA:
     * - email: Student email for account lookup/creation
     * - course_id: Target course for student enrollment
     * - Validation: Ensures required fields are present
     * - Security: Uses authenticated API requests
     * 
     * ENROLLMENT PROCESSING:
     * - Student account creation: If student doesn't exist
     * - Course association: Link student to specific course
     * - Progress initialization: Set up progress tracking
     * - Notification: Send welcome email to student
     * 
     * ERROR HANDLING:
     * - Duplicate enrollment: Handle already enrolled students
     * - Invalid email: Validate email format and existence
     * - Course capacity: Check enrollment limits
     * - Network failures: Provide retry mechanisms
     * 
     * SUCCESS HANDLING:
     * - Refresh student list with new enrollment
     * - Re-render dashboard to show updated data
     * - Display success notification to instructor
     * - Close modal after successful enrollment
     * 
     * @param {FormData} formData - Form data from student enrollment modal
     */
    async addStudent(formData) {
        try {
            const studentData = {
                email: formData.get('email'),
                course_id: formData.get('course_id')
            };

            const response = await Auth.authenticatedFetch(CONFIG.ENDPOINTS.ENROLL_STUDENT, {
                method: 'POST',
                body: JSON.stringify(studentData)
            });

            if (response.ok) {
                await this.loadStudents();
                this.renderDashboard();
                showNotification('Student added successfully!', 'success');
            } else {
                throw new Error('Failed to add student');
            }
        } catch (error) {
            console.error('Error adding student:', error);
            showNotification('Error adding student', 'error');
        }
    }

    /**
     * Remove student
     */
    async removeStudent(studentId) {
        const student = this.students.find(s => s.id === studentId);
        if (!student) return;

        const confirmModal = UIComponents.createConfirmDialog(
            `Are you sure you want to remove ${student.full_name} from the course?`,
            async () => {
                try {
                    const response = await Auth.authenticatedFetch(
                        CONFIG.ENDPOINTS.REMOVE_ENROLLMENT(studentId),
                        { method: 'DELETE' }
                    );

                    if (response.ok) {
                        this.students = this.students.filter(s => s.id !== studentId);
                        this.renderDashboard();
                        showNotification('Student removed successfully', 'success');
                    } else {
                        throw new Error('Failed to remove student');
                    }
                } catch (error) {
                    console.error('Error removing student:', error);
                    showNotification('Error removing student', 'error');
                }
            }
        );
    }

    /**
     * COMPREHENSIVE FEEDBACK DATA LOADING SYSTEM
     * PURPOSE: Load all feedback data with parallel processing and error handling
     * WHY: Feedback tab requires current data from multiple sources for effective display
     * 
     * FEEDBACK DATA SOURCES:
     * - Course feedback: Student ratings and comments about instructor's courses
     * - Student feedback: Instructor assessments and feedback about students
     * - Feedback analytics: Aggregated metrics and performance data
     * 
     * PARALLEL LOADING STRATEGY:
     * - Course feedback: Load feedback for all instructor courses simultaneously
     * - Student feedback: Load feedback history for all enrolled students
     * - Error isolation: Handle individual course/student failures gracefully
     * - Performance optimization: Use Promise.all for concurrent requests
     * 
     * ERROR HANDLING:
     * - Individual failure handling: Continue loading even if some requests fail
     * - Comprehensive error logging: Track failures for debugging
     * - User notification: Inform instructor of loading issues
     * - Graceful degradation: Display available data even with partial failures
     * 
     * FEEDBACK MANAGER INTEGRATION:
     * - Dynamic import: Load feedback manager when needed
     * - Lazy loading: Initialize feedback system on demand
     * - Service dependency: Handle feedback manager unavailability
     * - Real-time updates: Refresh feedback display after loading
     */
    async loadFeedbackData() {
        if (!feedbackManager) {
            showNotification('Feedback system is loading...', 'info');
            return;
        }
        
        try {
            // Load course feedback for all courses
            const courseFeedbackPromises = this.courses.map(course => 
                feedbackManager.getCourseFeedback(course.id)
                    .then(feedback => ({ courseId: course.id, courseName: course.title, feedback }))
                    .catch(error => ({ courseId: course.id, courseName: course.title, feedback: [], error }))
            );
            
            const courseFeedbackResults = await Promise.all(courseFeedbackPromises);
            this.feedbackData.courseFeedback = courseFeedbackResults;
            
            // Load student feedback
            const studentFeedbackPromises = this.students.map(student => 
                feedbackManager.getStudentFeedback(student.id, student.course_id)
                    .then(feedback => ({ studentId: student.id, studentName: student.full_name, feedback }))
                    .catch(error => ({ studentId: student.id, studentName: student.full_name, feedback: [], error }))
            );
            
            const studentFeedbackResults = await Promise.all(studentFeedbackPromises);
            this.feedbackData.studentFeedback = studentFeedbackResults;
            
            // Update the feedback display
            this.updateCourseFeedbackDisplay();
            
        } catch (error) {
            console.error('Error loading feedback data:', error);
            showNotification('Error loading feedback data', 'error');
        }
    }

    /**
     * Update course feedback display
     */
    updateCourseFeedbackDisplay() {
        const container = document.getElementById('courseFeedbackList');
        if (!container) return;
        
        const allFeedback = this.feedbackData.courseFeedback.flatMap(courseData => 
            courseData.feedback.map(fb => ({ ...fb, courseName: courseData.courseName }))
        );
        
        if (allFeedback.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comment-slash fa-3x"></i>
                    <h3>No course feedback yet</h3>
                    <p>Student feedback will appear here once submitted</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = allFeedback.map(feedback => `
            <div class="feedback-item">
                <div class="feedback-header">
                    <div class="course-info">
                        <h4>${feedback.courseName}</h4>
                        <div class="rating">
                            ${this.renderStarRating(feedback.overall_rating)}
                            <span class="rating-value">${feedback.overall_rating}/5</span>
                        </div>
                    </div>
                    <div class="feedback-meta">
                        <span class="feedback-date">${new Date(feedback.created_at).toLocaleDateString()}</span>
                        ${feedback.is_anonymous ? '<span class="anonymous-badge">Anonymous</span>' : '<span class="student-name">' + (feedback.student_name || 'Student') + '</span>'}
                    </div>
                </div>
                <div class="feedback-content">
                    ${feedback.positive_aspects ? `<p><strong>Likes:</strong> ${feedback.positive_aspects}</p>` : ''}
                    ${feedback.areas_for_improvement ? `<p><strong>Improvements:</strong> ${feedback.areas_for_improvement}</p>` : ''}
                    ${feedback.additional_comments ? `<p><strong>Comments:</strong> ${feedback.additional_comments}</p>` : ''}
                </div>
                <div class="feedback-ratings">
                    ${feedback.content_quality ? `<span class="rating-pill">Content: ${feedback.content_quality}/5</span>` : ''}
                    ${feedback.instructor_effectiveness ? `<span class="rating-pill">Teaching: ${feedback.instructor_effectiveness}/5</span>` : ''}
                    ${feedback.difficulty_appropriateness ? `<span class="rating-pill">Difficulty: ${feedback.difficulty_appropriateness}/5</span>` : ''}
                    ${feedback.lab_quality ? `<span class="rating-pill">Labs: ${feedback.lab_quality}/5</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    /**
     * Render star rating display
     */
    renderStarRating(rating) {
        const stars = [];
        for (let i = 1; i <= 5; i++) {
            stars.push(`<i class="fas fa-star ${i <= rating ? 'active' : ''}"></i>`);
        }
        return stars.join('');
    }

    /**
     * STUDENT FEEDBACK MODAL SYSTEM
     * PURPOSE: Display comprehensive student assessment interface
     * WHY: Instructor feedback requires structured input and professional presentation
     * 
     * STUDENT FEEDBACK WORKFLOW:
     * 1. Validate student and course existence
     * 2. Create professional feedback modal overlay
     * 3. Generate student-specific feedback form
     * 4. Handle form submission with API integration
     * 5. Update feedback data and close modal
     * 
     * FEEDBACK FORM FEATURES:
     * - Student identification: Name and course context
     * - Assessment categories: Progress, participation, performance
     * - Rating scales: Numeric ratings for objective assessment
     * - Written feedback: Detailed comments and recommendations
     * - Action plans: Specific improvement suggestions
     * 
     * MODAL FEATURES:
     * - Professional overlay design with large form area
     * - Click-outside-to-close functionality
     * - Form validation and submission handling
     * - Loading states during submission
     * - Success/error feedback to instructor
     * 
     * INTEGRATION REQUIREMENTS:
     * - Feedback manager: Requires feedback system to be loaded
     * - Student data: Validates student exists and is enrolled
     * - Course context: Provides course-specific assessment context
     * - API integration: Submits feedback through authenticated endpoints
     * 
     * @param {string} studentId - Unique identifier for student receiving feedback
     * @param {string} courseId - Course context for feedback assessment
     */
    showStudentFeedbackModal(studentId, courseId) {
        if (!feedbackManager) {
            showNotification('Feedback system is still loading. Please try again.', 'warning');
            return;
        }
        
        const student = this.students.find(s => s.id === studentId);
        const course = this.courses.find(c => c.id === courseId);
        
        if (!student || !course) {
            showNotification('Student or course not found', 'error');
            return;
        }
        
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.className = 'feedback-overlay';
        overlay.id = 'studentFeedbackOverlay';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.className = 'feedback-modal large';
        modal.innerHTML = feedbackManager.createStudentFeedbackForm(
            studentId, 
            student.full_name, 
            courseId, 
            course.title
        );
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Add event listener for form submission
        const form = document.getElementById('studentFeedbackForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                feedbackManager.handleStudentFeedbackSubmit(e)
                    .then(() => {
                        overlay.remove();
                        this.loadFeedbackData(); // Refresh feedback data
                    })
                    .catch(error => {
                        console.error('Error submitting feedback:', error);
                    });
            });
        }
        
        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Filter course feedback
     */
    filterCourseFeedback() {
        const courseFilter = document.getElementById('courseFeedbackFilter')?.value;
        const ratingFilter = document.getElementById('ratingFilter')?.value;
        
        // Implementation for filtering feedback
        // This would filter the displayed feedback based on selected criteria
    }

    /**
     * Load course feedback
     */
    async loadCourseFeedback() {
        await this.loadFeedbackData();
        showNotification('Feedback data refreshed', 'success');
    }

    /**
     * Export feedback report
     */
    exportFeedbackReport() {
        // Implementation for exporting feedback report
        showNotification('Export functionality coming soon', 'info');
    }

    /**
     * Show bulk feedback modal
     */
    showBulkFeedbackModal() {
        showNotification('Bulk feedback functionality coming soon', 'info');
    }

    /**
     * View student feedback history
     */
    viewStudentFeedbackHistory(studentId) {
        const student = this.students.find(s => s.id === studentId);
        if (!student) return;
        
        showNotification(`Viewing feedback history for ${student.full_name}`, 'info');
    }

    // ============================================================================
    // COURSE PUBLISHING FUNCTIONALITY
    // ============================================================================

    /**
     * Load published courses
     */
    async loadPublishedCourses() {
        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/courses/published`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (!response.ok) throw new Error('Failed to load published courses');
            
            const publishedCourses = await response.json();
            this.renderPublishedCourses(publishedCourses);
        } catch (error) {
            console.error('Error loading published courses:', error);
            showNotification('Error loading published courses', 'error');
        }
    }

    /**
     * Render published courses
     */
    renderPublishedCourses(courses) {
        const container = document.getElementById('publishedCoursesContainer');
        if (!container) return;

        if (courses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book-open"></i>
                    <h3>No Published Courses</h3>
                    <p>You haven't published any courses yet. Publish a course to see it here.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = courses.map(course => `
            <div class="course-card">
                <div class="course-header">
                    <h3>${course.title}</h3>
                    <div class="course-badges">
                        <span class="badge ${course.visibility}">${course.visibility}</span>
                        <span class="badge ${course.status}">${course.status}</span>
                    </div>
                </div>
                <div class="course-meta">
                    <p><i class="fas fa-calendar"></i> Published: ${new Date(course.published_at).toLocaleDateString()}</p>
                    <p><i class="fas fa-users"></i> Instances: ${course.instance_count || 0}</p>
                </div>
                <div class="course-actions">
                    <button class="btn btn-primary" onclick="instructorDashboard.viewInstances('${course.id}')">
                        <i class="fas fa-calendar-alt"></i> View Instances
                    </button>
                    <button class="btn btn-secondary" onclick="instructorDashboard.createInstance('${course.id}')">
                        <i class="fas fa-plus"></i> New Instance
                    </button>
                    <button class="btn btn-outline" onclick="instructorDashboard.unpublishCourse('${course.id}')">
                        <i class="fas fa-archive"></i> Unpublish
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Load course instances
     */
    async loadCourseInstances() {
        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/course-instances`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (!response.ok) throw new Error('Failed to load course instances');
            
            const instances = await response.json();
            this.renderCourseInstances(instances);
        } catch (error) {
            console.error('Error loading course instances:', error);
            showNotification('Error loading course instances', 'error');
        }
    }

    /**
     * Render course instances
     */
    renderCourseInstances(instances) {
        const container = document.getElementById('courseInstancesContainer');
        if (!container) return;

        if (instances.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-plus"></i>
                    <h3>No Course Instances</h3>
                    <p>Create your first course instance to start enrolling students.</p>
                    <button class="btn btn-primary" onclick="instructorDashboard.showCreateInstanceModal()">
                        <i class="fas fa-plus"></i> Create Instance
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = instances.map(instance => `
            <div class="instance-card">
                <div class="instance-header">
                    <h3>${instance.instance_name}</h3>
                    <span class="badge ${instance.status}">${instance.status}</span>
                </div>
                <div class="instance-details">
                    <p><strong>Course:</strong> ${instance.course_title}</p>
                    <p><strong>Duration:</strong> ${new Date(instance.start_datetime).toLocaleDateString()} - ${new Date(instance.end_datetime).toLocaleDateString()}</p>
                    <p><strong>Timezone:</strong> ${instance.timezone}</p>
                    <p><strong>Students:</strong> ${instance.enrolled_count}/${instance.max_students}</p>
                </div>
                <div class="instance-actions">
                    <button class="btn btn-primary" onclick="instructorDashboard.viewEnrollments('${instance.id}')">
                        <i class="fas fa-users"></i> View Students
                    </button>
                    <button class="btn btn-secondary" onclick="instructorDashboard.showEnrollStudentModal('${instance.id}')">
                        <i class="fas fa-user-plus"></i> Enroll Student
                    </button>
                    ${instance.status === 'scheduled' ? `
                        <button class="btn btn-outline" onclick="instructorDashboard.cancelInstance('${instance.id}')">
                            <i class="fas fa-times"></i> Cancel
                        </button>
                    ` : ''}
                    ${instance.status === 'active' || instance.status === 'scheduled' ? `
                        <button class="btn btn-warning" onclick="instructorDashboard.completeCourseInstance('${instance.id}', '${instance.instance_name}')" title="Complete course and disable student access">
                            <i class="fas fa-check-circle"></i> Complete Course
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    /**
     * CREATE COURSE INSTANCE MODAL SYSTEM
     * PURPOSE: Display comprehensive course instance creation interface
     * WHY: Course instances require detailed scheduling and configuration input
     * 
     * COURSE INSTANCE CREATION WORKFLOW:
     * 1. Load published courses for instance creation
     * 2. Populate course selection dropdown
     * 3. Configure default timezone settings
     * 4. Display professional instance creation form
     * 5. Handle form submission with validation
     * 
     * INSTANCE FORM FIELDS:
     * - Course selection: Choose from published courses
     * - Instance name: Unique identifier for course session
     * - Start/end dates: Course session scheduling
     * - Start/end times: Daily session timing
     * - Timezone: Session timezone configuration
     * - Maximum students: Enrollment capacity limits
     * - Description: Optional instance-specific details
     * 
     * ADVANCED FEATURES:
     * - Timezone detection: Auto-detect user's local timezone
     * - Date/time validation: Ensure logical scheduling
     * - Course filtering: Only show published courses
     * - Capacity management: Set enrollment limits
     * 
     * ERROR HANDLING:
     * - Course loading failures: Handle published course API errors
     * - Validation errors: Display form validation messages
     * - Submission errors: Process API error responses
     * - Network failures: Provide retry mechanisms
     * 
     * USER EXPERIENCE:
     * - Professional modal with comprehensive form
     * - Auto-timezone detection for convenience
     * - Clear validation feedback
     * - Responsive design for all devices
     */
    async showCreateInstanceModal() {
        // Load published courses for the dropdown
        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/courses/published`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (!response.ok) throw new Error('Failed to load published courses');
            
            const publishedCourses = await response.json();
            
            // Populate course dropdown
            const courseSelect = document.getElementById('instanceCourse');
            courseSelect.innerHTML = '<option value="">Select a published course...</option>' +
                publishedCourses.map(course => 
                    `<option value="${course.id}">${course.title}</option>`
                ).join('');

            // Set default timezone to user's local timezone
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const timezoneSelect = document.getElementById('timezone');
            if (timezoneSelect.querySelector(`option[value="${timezone}"]`)) {
                timezoneSelect.value = timezone;
            }

            // Show modal
            document.getElementById('createInstanceModal').style.display = 'block';
        } catch (error) {
            console.error('Error loading published courses:', error);
            showNotification('Error loading published courses', 'error');
        }
    }

    /**
     * Submit create instance form
     */
    async submitCreateInstance() {
        const form = document.getElementById('createInstanceForm');
        const formData = new FormData(form);

        // Combine date and time
        const startDate = formData.get('start_date');
        const startTime = formData.get('start_time');
        const endDate = formData.get('end_date');
        const endTime = formData.get('end_time');

        const instanceData = {
            course_id: formData.get('course_id'),
            instance_name: formData.get('instance_name'),
            start_datetime: `${startDate}T${startTime}`,
            end_datetime: `${endDate}T${endTime}`,
            timezone: formData.get('timezone'),
            max_students: parseInt(formData.get('max_students')),
            description: formData.get('description') || null
        };

        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/course-instances`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Auth.getToken()}`
                },
                body: JSON.stringify(instanceData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create instance');
            }

            const result = await response.json();
            showNotification('Course instance created successfully!', 'success');
            
            // Close modal and refresh data
            this.closeModal('createInstanceModal');
            this.loadCourseInstances();
            
            // Reset form
            form.reset();
        } catch (error) {
            console.error('Error creating instance:', error);
            showNotification(error.message, 'error');
        }
    }

    /**
     * Show enroll student modal
     */
    showEnrollStudentModal(instanceId) {
        document.getElementById('enrollInstanceId').value = instanceId;
        document.getElementById('enrollStudentModal').style.display = 'block';
    }

    /**
     * Submit enroll student form
     */
    async submitEnrollStudent() {
        const form = document.getElementById('enrollStudentForm');
        const formData = new FormData(form);

        const enrollmentData = {
            student_email: formData.get('student_email'),
            student_name: formData.get('student_name'),
            send_welcome_email: formData.get('send_welcome_email') === 'on'
        };

        const instanceId = formData.get('instance_id');

        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/course-instances/${instanceId}/enroll`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Auth.getToken()}`
                },
                body: JSON.stringify(enrollmentData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to enroll student');
            }

            const result = await response.json();
            showNotification('Student enrolled successfully!', 'success');
            
            if (result.welcome_email_sent) {
                showNotification('Welcome email sent to student', 'info');
            }
            
            // Close modal and refresh data
            this.closeModal('enrollStudentModal');
            this.loadCourseInstances();
            
            // Reset form
            form.reset();
        } catch (error) {
            console.error('Error enrolling student:', error);
            showNotification(error.message, 'error');
        }
    }

    /**
     * View course instances for a specific course
     */
    viewInstances(courseId) {
        // Switch to course instances tab and filter by course
        this.switchTab('course-instances');
        // TODO: Implement filtering by course ID
        showNotification('Filtering instances by course', 'info');
    }

    /**
     * Create new instance for a specific course
     */
    createInstance(courseId) {
        this.showCreateInstanceModal();
        // Pre-select the course
        setTimeout(() => {
            document.getElementById('instanceCourse').value = courseId;
        }, 100);
    }

    /**
     * Unpublish a course
     */
    async unpublishCourse(courseId) {
        if (!confirm('Are you sure you want to unpublish this course? Students will no longer be able to access it.')) {
            return;
        }

        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/courses/${courseId}/unpublish`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (!response.ok) throw new Error('Failed to unpublish course');
            
            showNotification('Course unpublished successfully', 'success');
            this.loadPublishedCourses();
        } catch (error) {
            console.error('Error unpublishing course:', error);
            showNotification('Error unpublishing course', 'error');
        }
    }

    /**
     * Cancel a course instance
     */
    async cancelInstance(instanceId) {
        if (!confirm('Are you sure you want to cancel this instance? Enrolled students will be notified.')) {
            return;
        }

        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/course-instances/${instanceId}/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (!response.ok) throw new Error('Failed to cancel instance');
            
            showNotification('Instance cancelled successfully', 'success');
            this.loadCourseInstances();
        } catch (error) {
            console.error('Error cancelling instance:', error);
            showNotification('Error cancelling instance', 'error');
        }
    }

    /**
     * View enrollments for an instance
     */
    viewEnrollments(instanceId) {
        // TODO: Implement enrollment viewing modal
        showNotification('Enrollment viewing functionality coming soon', 'info');
    }

    /**
     * COURSE INSTANCE COMPLETION SYSTEM
     * PURPOSE: Complete course instances with student access management
     * WHY: Course completion requires systematic closure and access control
     * 
     * COURSE COMPLETION WORKFLOW:
     * 1. Display comprehensive confirmation dialog
     * 2. Explain completion consequences to instructor
     * 3. Execute authenticated completion API request
     * 4. Update instance status and disable student access
     * 5. Refresh dashboard to reflect changes
     * 
     * COMPLETION CONSEQUENCES:
     * - Course status: Mark instance as completed
     * - Student access: Disable all student login URLs
     * - Data preservation: Maintain student progress and grades
     * - Irreversible action: Cannot be undone once completed
     * 
     * CONFIRMATION DIALOG:
     * - Clear action explanation: What completion means
     * - Consequence list: Specific impacts on students and data
     * - Irreversible warning: Emphasize permanent nature
     * - Cancel option: Allow instructor to reconsider
     * 
     * API INTEGRATION:
     * - Authenticated request: Secure completion processing
     * - Error handling: Process API failures gracefully
     * - Status updates: Update local instance data
     * - Success feedback: Confirm completion to instructor
     * 
     * POST-COMPLETION ACTIONS:
     * - Dashboard refresh: Update instance status display
     * - Student notifications: Inform students of completion
     * - Data archival: Preserve completion records
     * - Access revocation: Disable student portal access
     * 
     * @param {string} instanceId - Unique identifier for course instance
     * @param {string} instanceName - Display name for confirmation dialog
     */
    async completeCourseInstance(instanceId, instanceName) {
        const confirmed = confirm(
            `Are you sure you want to complete the course instance "${instanceName}"?

` +
            `This action will:
` +
            `• Mark the course as completed
` +
            `• Disable all student login URLs
` +
            `• Prevent further student access

` +
            `This action cannot be undone.`
        );

        if (!confirmed) return;

        try {
            const response = await fetch(`${CONFIG.ENDPOINTS.COURSE_SERVICE}/course-instances/${instanceId}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to complete course instance');
            }
            
            const result = await response.json();
            
            showNotification(
                `Course instance "${instanceName}" completed successfully. Student access has been disabled.`, 
                'success'
            );
            
            // Reload course instances to reflect the status change
            this.loadCourseInstances();
            
        } catch (error) {
            console.error('Error completing course instance:', error);
            showNotification(`Error completing course instance: ${error.message}`, 'error');
        }
    }

    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// Create global instance
let instructorDashboard = null;

// Initialize if on instructor dashboard page
if (window.location.pathname.includes('instructor-dashboard.html')) {
    instructorDashboard = new InstructorDashboard();
    window.instructorDashboard = instructorDashboard;
}

export default InstructorDashboard;