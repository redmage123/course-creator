/**
 * Instructor Dashboard Module
 * Handles instructor-specific functionality
 */

import { Auth } from './auth.js';
import { CONFIG } from '../config.js';
import { showNotification } from './notifications.js';
import UIComponents from './ui-components.js';

export class InstructorDashboard {
    constructor() {
        this.courses = [];
        this.students = [];
        this.currentCourse = null;
        this.activeTab = 'courses';
        
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
     * Switch tab
     */
    switchTab(tabName) {
        this.activeTab = tabName;
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
}

// Initialize if on instructor dashboard page
if (window.location.pathname.includes('instructor-dashboard.html')) {
    new InstructorDashboard();
}

export default InstructorDashboard;