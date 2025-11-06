/**
 * Course Manager Module
 * Single Responsibility: Handle course creation, editing, and management
 * Following SOLID principles with clean API abstraction
 */
export class CourseManager {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {Object} config - Configuration options
     */
    constructor(config) {
        this.config = config;
        this.courses = [];
        this.currentCourse = null;
        this.filters = {
            status: 'all',
            search: ''
        };
        
        this.initialize();
    }

    /**
     * Initialize course manager system
     *
     * PURPOSE: Set up event listeners and load initial course data
     * WHY: Two-phase initialization separates construction from async operations
     *
     * @returns {void}
     */
    initialize() {
        this.setupEventListeners();
        this.loadCourses();
    }

    /**
     * Set up all event listeners for course management
     *
     * PURPOSE: Establish user interaction handlers for course operations
     * WHY: Centralizes event management for maintainability
     *
     * BUSINESS LOGIC:
     * - Course creation form submission
     * - Search and filter interactions
     * - Section change notifications for course display refresh
     *
     * @returns {void}
     */
    setupEventListeners() {
        // Course creation form
        const courseForm = document.getElementById('courseForm');
        if (courseForm) {
            courseForm.addEventListener('submit', (e) => this.handleCourseSubmission(e));
        }

        // Search and filters
        const searchInput = document.getElementById('course-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        const filterSelect = document.getElementById('course-filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => this.handleFilter(e.target.value));
        }

        // Listen for section changes
        document.addEventListener('sectionChanged', (e) => {
            if (e.detail.section === 'courses') {
                this.refreshCoursesDisplay();
            }
        });
    }

    /**
     * Handle course creation form submission
     *
     * PURPOSE: Process new course creation with validation and API submission
     * WHY: Centralized form handling ensures consistent course creation workflow
     *
     * BUSINESS LOGIC:
     * - Extracts form data including title, description, category, level, duration, price, tags
     * - Submits to course creation API endpoint
     * - Shows success/error notifications
     * - Resets form on success
     * - Navigates to courses section after creation
     *
     * @param {Event} e - Form submission event
     * @returns {Promise<void>}
     * @throws {Error} If course creation fails
     */
    async handleCourseSubmission(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const courseData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: formData.get('category'),
            level: formData.get('level'),
            duration: formData.get('duration'),
            duration_unit: formData.get('duration_unit'),
            price: parseFloat(formData.get('price')) || 0,
            tags: formData.get('tags') ? formData.get('tags').split(',').map(tag => tag.trim()) : []
        };

        try {
            await this.createCourse(courseData);
            this.showNotification('Course created successfully!', 'success');
            e.target.reset();
            
            // Navigate to courses section
            if (window.dashboardNavigation) {
                window.dashboardNavigation.navigateTo('courses');
            }
        } catch (error) {
            console.error('Course creation error:', error);
            this.showNotification('Failed to create course: ' + error.message, 'error');
        }
    }

    /**
     * CREATE NEW COURSE INSTANCE
     * PURPOSE: Create new course instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} courseData - Coursedata parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async createCourse(courseData) {
        const response = await fetch(this.config.ENDPOINTS.COURSE_SERVICE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(courseData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to create course');
        }

        const result = await response.json();
        
        // Add to local courses array
        this.courses.unshift(result.course);
        
        return result.course;
    }

    /**
     * LOAD COURSES DATA FROM SERVER
     * PURPOSE: Load courses data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadCourses() {
        try {
            const response = await fetch(this.config.ENDPOINTS.COURSE_SERVICE, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load courses');
            }

            const data = await response.json();
            this.courses = Array.isArray(data) ? data : [];
            
            this.updateCoursesDisplay();
            this.updateOverviewStats();
            
        } catch (error) {
            console.error('Error loading courses:', error);
            this.showNotification('Failed to load courses: ' + error.message, 'error');
        }
    }

    /**
     * UPDATE COURSES DISPLAY STATE
     * PURPOSE: Update courses display state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updateCoursesDisplay() {
        const coursesContainer = document.getElementById('courses-list');
        const emptyState = document.getElementById('courses-empty');
        
        if (!coursesContainer) return;

        // Apply filters
        const filteredCourses = this.getFilteredCourses();

        if (filteredCourses.length === 0) {
            coursesContainer.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        coursesContainer.style.display = 'grid';

        coursesContainer.innerHTML = filteredCourses.map(course => this.createCourseCard(course)).join('');
    }

    /**
     * RETRIEVE FILTERED COURSES INFORMATION
     * PURPOSE: Retrieve filtered courses information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getFilteredCourses() {
        return this.courses.filter(course => {
            // Status filter
            if (this.filters.status !== 'all') {
                if (this.filters.status === 'published' && !course.is_published) return false;
                if (this.filters.status === 'draft' && course.is_published) return false;
                if (this.filters.status === 'archived' && !course.archived) return false;
            }

            // Search filter
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const matchesTitle = course.title.toLowerCase().includes(searchTerm);
                const matchesDescription = course.description.toLowerCase().includes(searchTerm);
                const matchesTags = course.tags && course.tags.some(tag => 
                    tag.toLowerCase().includes(searchTerm)
                );
                
                if (!matchesTitle && !matchesDescription && !matchesTags) return false;
            }

            return true;
        });
    }

    /**
     * CREATE NEW COURSE CARD INSTANCE
     * PURPOSE: Create new course card instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} course - Course parameter
     *
     * @returns {Object} Newly created instance
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    createCourseCard(course) {
        const statusBadge = course.is_published ? 
            '<span class="status-badge published">Published</span>' :
            '<span class="status-badge draft">Draft</span>';

        const tags = course.tags ? 
            course.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('') : '';

        return `
            <div class="course-card" data-course-id="${course.id}">
                <div class="course-header">
                    <h3 class="course-title">${course.title}</h3>
                    ${statusBadge}
                </div>
                
                <div class="course-meta">
                    <span class="course-category">${course.category || 'Uncategorized'}</span>
                    <span class="course-level">${course.level || 'All Levels'}</span>
                </div>
                
                <p class="course-description">${course.description}</p>
                
                <div class="course-stats">
                    <div class="stat">
                        <i class="fas fa-users"></i>
                        <span>${course.enrolled_count || 0} students</span>
                    </div>
                    <div class="stat">
                        <i class="fas fa-clock"></i>
                        <span>${course.duration || 0} ${course.duration_unit || 'weeks'}</span>
                    </div>
                </div>
                
                <div class="course-tags">
                    ${tags}
                </div>
                
                <div class="course-actions">
                    <button onclick="courseManager.viewCourse('${course.id}')" class="btn btn-primary">
                        <i class="fas fa-eye"></i>
                        View
                    </button>
                    <button onclick="courseManager.editCourse('${course.id}')" class="btn btn-secondary">
                        <i class="fas fa-edit"></i>
                        Edit
                    </button>
                    <div class="dropdown">
                        <button class="btn btn-outline dropdown-toggle" onclick="courseManager.toggleCourseMenu('${course.id}')">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="dropdown-menu" id="course-menu-${course.id}">
                            <a href="#" onclick="courseManager.duplicateCourse('${course.id}')">
                                <i class="fas fa-copy"></i> Duplicate
                            </a>
                            <a href="#" onclick="courseManager.exportCourse('${course.id}')">
                                <i class="fas fa-download"></i> Export
                            </a>
                            <a href="#" onclick="courseManager.archiveCourse('${course.id}')" class="text-warning">
                                <i class="fas fa-archive"></i> Archive
                            </a>
                            <a href="#" onclick="courseManager.deleteCourse('${course.id}')" class="text-danger">
                                <i class="fas fa-trash"></i> Delete
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * HANDLE SEARCH EVENT
     * PURPOSE: Handle search event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {*} searchTerm - Searchterm parameter
     */
    handleSearch(searchTerm) {
        this.filters.search = searchTerm;
        this.updateCoursesDisplay();
    }

    /**
     * HANDLE FILTER EVENT
     * PURPOSE: Handle filter event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {*} status - Status parameter
     */
    handleFilter(status) {
        this.filters.status = status;
        this.updateCoursesDisplay();
    }

    /**
     * EXECUTE VIEWCOURSE OPERATION
     * PURPOSE: Execute viewCourse operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
    viewCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (course) {
            this.currentCourse = course;
            window.currentCourse = course; // For backward compatibility
            
            // Show course content view
            if (typeof window.showCourseContentView === 'function') {
                window.showCourseContentView(course);
            }
        }
    }

    /**
     * EXECUTE EDITCOURSE OPERATION
     * PURPOSE: Execute editCourse operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
    editCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (course) {
            // Populate edit form and show edit modal
            this.populateEditForm(course);
            this.showEditModal(course);
        }
    }

    /**
     * REMOVE COURSE FROM SYSTEM
     * PURPOSE: Remove course from system
     * WHY: Manages resource cleanup and data consistency
     *
     * @param {string|number} courseId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async deleteCourse(courseId) {
        if (!confirm('Are you sure you want to delete this course? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`${this.config.ENDPOINTS.COURSE_SERVICE}/courses/${courseId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete course');
            }

            // Remove from local array
            this.courses = this.courses.filter(c => c.id !== courseId);
            this.updateCoursesDisplay();
            this.updateOverviewStats();
            
            this.showNotification('Course deleted successfully', 'success');
            
        } catch (error) {
            console.error('Error deleting course:', error);
            this.showNotification('Failed to delete course: ' + error.message, 'error');
        }
    }

    /**
     * UPDATE OVERVIEW STATS STATE
     * PURPOSE: Update overview stats state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updateOverviewStats() {
        // Update overview section statistics
        const totalCoursesEl = document.getElementById('total-courses');
        const publishedCoursesEl = document.getElementById('published-courses');
        
        if (totalCoursesEl) {
            totalCoursesEl.textContent = this.courses.length;
        }
        
        if (publishedCoursesEl) {
            const publishedCount = this.courses.filter(c => c.is_published).length;
            publishedCoursesEl.textContent = publishedCount;
        }
    }

    /**
     * EXECUTE REFRESHCOURSESDISPLAY OPERATION
     * PURPOSE: Execute refreshCoursesDisplay operation
     * WHY: Implements required business logic for system functionality
     */
    refreshCoursesDisplay() {
        this.loadCourses();
    }

    /**
     * DISPLAY NOTIFICATION INTERFACE
     * PURPOSE: Display notification interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} message - Message parameter
     * @param {*} type - Type identifier
     */
    showNotification(message, type = 'info') {
        // Use existing notification system or create simple notification
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
        }
    }

    // Public API
    /**
     * RETRIEVE COURSES INFORMATION
     * PURPOSE: Retrieve courses information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCourses() {
        return this.courses;
    }

    /**
     * RETRIEVE CURRENT COURSE INFORMATION
     * PURPOSE: Retrieve current course information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentCourse() {
        return this.currentCourse;
    }

    /**
     * RETRIEVE COURSE BY ID INFORMATION
     * PURPOSE: Retrieve course by id information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} courseId - Unique identifier
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCourseById(courseId) {
        return this.courses.find(c => c.id === courseId);
    }
}

// Global instance
let courseManagerInstance = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.CONFIG) {
        courseManagerInstance = new CourseManager(window.CONFIG);
        window.courseManager = courseManagerInstance;
        
        // Backward compatibility
        window.loadUserCourses = () => courseManagerInstance.loadCourses();
        window.viewCourseDetails = (id) => courseManagerInstance.viewCourse(id);
        window.filterCourses = () => courseManagerInstance.handleFilter(document.getElementById('course-filter').value);
        window.searchCourses = () => courseManagerInstance.handleSearch(document.getElementById('course-search').value);
    }
});

export default CourseManager;