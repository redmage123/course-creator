/**
 * Instructor Dashboard Module
 * Handles instructor-specific functionality
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
    constructor() {
        this.courses = [];
        this.students = [];
        this.currentCourse = null;
        this.activeTab = 'courses';
        this.feedbackData = {
            courseFeedback: [],
            studentFeedback: []
        };
        
        this.init();
    }

    /**
     * Initialize the instructor dashboard
     */
    init() {
        if (!Auth.isAuthenticated() || !Auth.hasRole('instructor')) {
            window.location.href = 'index.html';
            return;
        }

        this.setupEventListeners();
        this.loadInitialData();
        this.renderDashboard();
    }

    /**
     * Quiz Management Methods
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
     * Setup event listeners
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
     * Load initial data
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
     * Load courses
     */
    async loadCourses() {
        try {
            console.log('Loading courses from:', CONFIG.ENDPOINTS.COURSES);
            const response = await Auth.authenticatedFetch(CONFIG.ENDPOINTS.COURSES);
            console.log('Courses response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Courses data received:', data);
                this.courses = data.courses || data || [];
                console.log('Courses loaded:', this.courses.length);
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
     * Load students
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
     * Render the dashboard
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
     * Render tab content
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
     * Render courses tab
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
     * Render course card
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
     * Render students tab
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
     * Render student row
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
     * Render analytics tab
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
     * Render content tab
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
     * Render feedback tab
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
     * Render course feedback section
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
     * Render student feedback section
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
     * Switch tab
     */
    switchTab(tabName) {
        this.activeTab = tabName;
        if (tabName === 'feedback') {
            this.loadFeedbackData();
        }
        this.renderDashboard();
    }

    /**
     * Show create course modal
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
     * Create course
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
     * Edit course
     */
    editCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (!course) return;

        // Implementation for editing course
        console.log('Edit course:', course);
    }

    /**
     * Delete course
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
     * Show add student modal
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
     * Add student
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
     * Load feedback data
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
     * Show student feedback modal
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
        console.log('Filtering feedback by course:', courseFilter, 'rating:', ratingFilter);
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
     * Show create instance modal
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
     * Complete a course instance and disable student access
     */
    async completeCourseInstance(instanceId, instanceName) {
        const confirmed = confirm(
            `Are you sure you want to complete the course instance "${instanceName}"?\n\n` +
            `This action will:\n` +
            `• Mark the course as completed\n` +
            `• Disable all student login URLs\n` +
            `• Prevent further student access\n\n` +
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