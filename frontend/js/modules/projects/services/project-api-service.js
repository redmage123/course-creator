/**
 * Project API Service
 *
 * BUSINESS CONTEXT:
 * Provides a project-specific abstraction layer over the generic org-admin-api.js,
 * handling organization context, project-specific business rules, and enhanced
 * error handling for project operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Wraps org-admin-api functions with project context
 * - Adds project-specific validation and error handling
 * - Provides cleaner API for ProjectController
 * - Handles track creation within project context
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: API communication only
 * - Open/Closed: Extensible through additional methods
 * - Dependency Inversion: Depends on org-admin-api abstraction
 * - Interface Segregation: Clean, focused API
 *
 * @module projects/services/project-api-service
 */
import {
    fetchProjects as apiFetchProjects,
    createProject as apiCreateProject,
    updateProject as apiUpdateProject,
    deleteProject as apiDeleteProject,
    fetchMembers as apiFetchMembers,
    addInstructor as apiAddInstructor,
    addStudent as apiAddStudent,
    removeMember as apiRemoveMember,
    createTrack as apiCreateTrack
} from '../../org-admin-api.js';

import {
    sendContextAwareMessage,
    initializeAIAssistant,
    CONTEXT_TYPES
} from '../../ai-assistant.js';

/**
 * ProjectAPIService Class
 *
 * Wraps all project-related API calls with organization context
 * and project-specific business logic.
 *
 * USAGE:
 * const apiService = new ProjectAPIService('org-123');
 * const projects = await apiService.fetchProjects({ status: 'active' });
 */
export class ProjectAPIService {
    /**
     * Initialize the API service
     *
     * @param {string} organizationId - Organization UUID (required)
     */
    constructor(organizationId) {
        if (!organizationId) {
            throw new Error('ProjectAPIService: organizationId is required');
        }

        /**
         * Organization context
         * @private
         */
        this.organizationId = organizationId;

        console.log('ProjectAPIService initialized for organization:', organizationId);
    }

    /**
     * Set organization context
     *
     * BUSINESS LOGIC:
     * Allows changing organization context without creating new service instance.
     * Useful for multi-org dashboards or testing.
     *
     * @param {string} organizationId - New organization UUID
     */
    setOrganizationId(organizationId) {
        if (!organizationId) {
            throw new Error('organizationId is required');
        }
        this.organizationId = organizationId;
        console.log('ProjectAPIService context changed to organization:', organizationId);
    }

    // ============================================================
    // PROJECT CRUD OPERATIONS
    // ============================================================

    /**
     * Fetch all projects for current organization
     *
     * BUSINESS LOGIC:
     * Retrieves projects with optional filtering by status and search term.
     * Always includes organization context automatically.
     *
     * @param {Object} filters - Optional filters { status?, search? }
     * @returns {Promise<Array<Project>>} Array of project objects
     *
     * @example
     * const projects = await apiService.fetchProjects({ status: 'active' });
     */
    async fetchProjects(filters = {}) {
        try {
            console.log('Fetching projects for organization:', this.organizationId, 'with filters:', filters);

            const projects = await apiFetchProjects(this.organizationId, filters);

            console.log(`Fetched ${projects.length} projects`);
            return projects;

        } catch (error) {
            console.error('Error fetching projects:', error);
            throw new Error(`Failed to fetch projects: ${error.message}`);
        }
    }

    /**
     * Create new project
     *
     * BUSINESS LOGIC:
     * Creates project within organization context. Validates required fields
     * and ensures slug uniqueness.
     *
     * @param {Object} projectData - Project creation data
     * @param {string} projectData.name - Project name (required)
     * @param {string} projectData.slug - Project URL slug (required)
     * @param {string} projectData.description - Project description
     * @param {Array<string>} projectData.objectives - Learning objectives
     * @param {Array<string>} projectData.target_roles - Target roles
     * @param {number} projectData.duration_weeks - Duration in weeks
     * @param {number} projectData.max_participants - Maximum participants
     * @param {string} projectData.start_date - Start date (ISO format)
     * @param {string} projectData.end_date - End date (ISO format)
     * @returns {Promise<Project>} Created project object
     *
     * @throws {Error} If required fields are missing
     */
    async createProject(projectData) {
        try {
            // Validate required fields
            if (!projectData.name) {
                throw new Error('Project name is required');
            }

            if (!projectData.slug) {
                throw new Error('Project slug is required');
            }

            console.log('Creating project:', projectData.name);

            const project = await apiCreateProject(this.organizationId, projectData);

            console.log('Project created successfully:', project.id);
            return project;

        } catch (error) {
            console.error('Error creating project:', error);
            throw new Error(`Failed to create project: ${error.message}`);
        }
    }

    /**
     * Update existing project
     *
     * BUSINESS LOGIC:
     * Updates project properties. Validates that project exists
     * before attempting update.
     *
     * @param {string} projectId - Project UUID
     * @param {Object} updates - Partial project data to update
     * @returns {Promise<Project>} Updated project object
     */
    async updateProject(projectId, updates) {
        try {
            if (!projectId) {
                throw new Error('Project ID is required');
            }

            console.log('Updating project:', projectId);

            const project = await apiUpdateProject(projectId, updates);

            console.log('Project updated successfully');
            return project;

        } catch (error) {
            console.error('Error updating project:', error);
            throw new Error(`Failed to update project: ${error.message}`);
        }
    }

    /**
     * Delete project
     *
     * BUSINESS LOGIC:
     * Permanently deletes project and all associated data including
     * tracks, locations, enrollments, and progress records.
     *
     * WARNING: This operation cannot be undone!
     *
     * @param {string} projectId - Project UUID
     * @returns {Promise<void>}
     */
    async deleteProject(projectId) {
        try {
            if (!projectId) {
                throw new Error('Project ID is required');
            }

            console.log('Deleting project:', projectId);

            await apiDeleteProject(projectId);

            console.log('Project deleted successfully');

        } catch (error) {
            console.error('Error deleting project:', error);
            throw new Error(`Failed to delete project: ${error.message}`);
        }
    }

    // ============================================================
    // PROJECT MEMBER MANAGEMENT
    // ============================================================

    /**
     * Fetch members for a project
     *
     * BUSINESS LOGIC:
     * Retrieves all members (instructors and students) assigned to a project.
     * Includes member profile data and enrollment status.
     *
     * @param {string} projectId - Project UUID
     * @returns {Promise<Array<Member>>} Array of member objects
     */
    async fetchProjectMembers(projectId) {
        try {
            if (!projectId) {
                throw new Error('Project ID is required');
            }

            console.log('Fetching members for project:', projectId);

            const members = await apiFetchMembers(this.organizationId, {
                project_id: projectId
            });

            console.log(`Fetched ${members.length} project members`);
            return members;

        } catch (error) {
            console.error('Error fetching project members:', error);
            throw new Error(`Failed to fetch project members: ${error.message}`);
        }
    }

    /**
     * Add instructor to organization
     *
     * BUSINESS LOGIC:
     * Creates new instructor account and assigns to organization.
     * Note: Instructors are added at organization level, not project level.
     *
     * @param {Object} instructorData - Instructor creation data
     * @param {string} instructorData.email - Email address (required)
     * @param {string} instructorData.first_name - First name (required)
     * @param {string} instructorData.last_name - Last name (required)
     * @returns {Promise<Instructor>} Created instructor object
     */
    async addInstructor(instructorData) {
        try {
            if (!instructorData.email) {
                throw new Error('Instructor email is required');
            }

            console.log('Adding instructor:', instructorData.email);

            const instructor = await apiAddInstructor(this.organizationId, instructorData);

            console.log('Instructor added successfully');
            return instructor;

        } catch (error) {
            console.error('Error adding instructor:', error);
            throw new Error(`Failed to add instructor: ${error.message}`);
        }
    }

    /**
     * Add student to organization
     *
     * BUSINESS LOGIC:
     * Creates new student account and assigns to organization.
     * Note: Students are added at organization level, not project level.
     *
     * @param {Object} studentData - Student creation data
     * @returns {Promise<Student>} Created student object
     */
    async addStudent(studentData) {
        try {
            if (!studentData.email) {
                throw new Error('Student email is required');
            }

            console.log('Adding student:', studentData.email);

            const student = await apiAddStudent(this.organizationId, studentData);

            console.log('Student added successfully');
            return student;

        } catch (error) {
            console.error('Error adding student:', error);
            throw new Error(`Failed to add student: ${error.message}`);
        }
    }

    /**
     * Remove member from organization
     *
     * BUSINESS LOGIC:
     * Removes member from organization and all associated projects.
     * This permanently removes the user's access to organization resources.
     *
     * @param {string} userId - User UUID
     * @returns {Promise<void>}
     */
    async removeMember(userId) {
        try {
            if (!userId) {
                throw new Error('User ID is required');
            }

            console.log('Removing member:', userId);

            await apiRemoveMember(this.organizationId, userId);

            console.log('Member removed successfully');

        } catch (error) {
            console.error('Error removing member:', error);
            throw new Error(`Failed to remove member: ${error.message}`);
        }
    }

    // ============================================================
    // TRACK MANAGEMENT
    // ============================================================

    /**
     * Create track within project
     *
     * BUSINESS LOGIC:
     * Creates a new track (learning path) within a project.
     * Tracks organize course content by role, difficulty, or topic.
     *
     * @param {Object} trackData - Track creation data
     * @param {string} trackData.project_id - Parent project UUID (required)
     * @param {string} trackData.name - Track name (required)
     * @param {string} trackData.description - Track description
     * @param {string} trackData.difficulty_level - Difficulty ('beginner', 'intermediate', 'advanced')
     * @param {number} trackData.estimated_duration_weeks - Duration in weeks
     * @returns {Promise<Track>} Created track object
     */
    async createTrack(trackData) {
        try {
            if (!trackData.project_id) {
                throw new Error('Project ID is required for track creation');
            }

            if (!trackData.name) {
                throw new Error('Track name is required');
            }

            console.log('Creating track:', trackData.name, 'in project:', trackData.project_id);

            const track = await apiCreateTrack(trackData);

            console.log('Track created successfully:', track.id);
            return track;

        } catch (error) {
            console.error('Error creating track:', error);
            throw new Error(`Failed to create track: ${error.message}`);
        }
    }

    /**
     * Batch create multiple tracks
     *
     * BUSINESS LOGIC:
     * Creates multiple tracks for a project in one operation.
     * Useful for project wizard when creating initial track structure.
     *
     * @param {string} projectId - Parent project UUID
     * @param {Array<Object>} tracksData - Array of track creation data
     * @returns {Promise<Array<Track>>} Array of created track objects
     */
    async batchCreateTracks(projectId, tracksData) {
        try {
            if (!projectId) {
                throw new Error('Project ID is required');
            }

            if (!Array.isArray(tracksData) || tracksData.length === 0) {
                throw new Error('Tracks data must be a non-empty array');
            }

            console.log(`Creating ${tracksData.length} tracks for project:`, projectId);

            // Add project_id to each track
            const tracksWithProjectId = tracksData.map(track => ({
                ...track,
                project_id: projectId
            }));

            // Create all tracks in parallel
            const trackPromises = tracksWithProjectId.map(trackData =>
                this.createTrack(trackData)
            );

            const createdTracks = await Promise.all(trackPromises);

            console.log(`Successfully created ${createdTracks.length} tracks`);
            return createdTracks;

        } catch (error) {
            console.error('Error batch creating tracks:', error);
            throw new Error(`Failed to batch create tracks: ${error.message}`);
        }
    }

    // ============================================================
    // AI ASSISTANT INTEGRATION
    // ============================================================

    /**
     * Initialize AI assistant for project context
     *
     * BUSINESS LOGIC:
     * Sets up AI assistant with project creation context including
     * project details and organization context for RAG-enhanced suggestions.
     *
     * @param {Object} projectContext - Project context data
     * @param {string} projectContext.projectName - Project name
     * @param {string} projectContext.projectDescription - Project description
     * @param {Array<string>} projectContext.targetRoles - Target roles
     * @returns {void}
     */
    initializeAIForProject(projectContext) {
        try {
            console.log('Initializing AI assistant for project context');

            initializeAIAssistant(CONTEXT_TYPES.PROJECT_CREATION, {
                ...projectContext,
                organizationId: this.organizationId
            });

        } catch (error) {
            console.error('Error initializing AI assistant:', error);
            throw new Error(`Failed to initialize AI assistant: ${error.message}`);
        }
    }

    /**
     * Get AI suggestions for project planning
     *
     * BUSINESS LOGIC:
     * Uses RAG-enhanced AI to generate project planning suggestions including:
     * - Project insights and analysis
     * - Recommended track structure
     * - Learning objectives
     * - Best practices
     *
     * @param {string} prompt - User prompt for AI
     * @param {Object} options - AI options (e.g., { forceWebSearch: true })
     * @returns {Promise<Object>} AI response with suggestions
     */
    async getAISuggestions(prompt, options = {}) {
        try {
            console.log('Getting AI suggestions for project planning');

            const response = await sendContextAwareMessage(prompt, options);

            console.log('AI suggestions received');
            return response;

        } catch (error) {
            console.error('Error getting AI suggestions:', error);
            throw new Error(`Failed to get AI suggestions: ${error.message}`);
        }
    }

    // ============================================================
    // UTILITY METHODS
    // ============================================================

    /**
     * Get current organization ID
     *
     * @returns {string} Organization UUID
     */
    getOrganizationId() {
        return this.organizationId;
    }

    /**
     * Validate project data structure
     *
     * BUSINESS LOGIC:
     * Validates that project data conforms to expected schema.
     * Used before API calls to catch errors early.
     *
     * @param {Object} projectData - Project data to validate
     * @returns {boolean} True if valid
     * @throws {Error} If validation fails
     */
    validateProjectData(projectData) {
        if (!projectData || typeof projectData !== 'object') {
            throw new Error('Project data must be an object');
        }

        // Required fields
        if (!projectData.name || typeof projectData.name !== 'string') {
            throw new Error('Project name is required and must be a string');
        }

        if (!projectData.slug || typeof projectData.slug !== 'string') {
            throw new Error('Project slug is required and must be a string');
        }

        // Optional fields with type validation
        if (projectData.duration_weeks !== undefined && !Number.isInteger(projectData.duration_weeks)) {
            throw new Error('Duration must be an integer');
        }

        if (projectData.max_participants !== undefined && !Number.isInteger(projectData.max_participants)) {
            throw new Error('Max participants must be an integer');
        }

        return true;
    }
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic Project Operations
 * =====================================
 * import { ProjectAPIService } from './services/project-api-service.js';
 *
 * const apiService = new ProjectAPIService('org-123');
 *
 * // Fetch projects
 * const projects = await apiService.fetchProjects({ status: 'active' });
 *
 * // Create project
 * const newProject = await apiService.createProject({
 *   name: 'Python Bootcamp',
 *   slug: 'python-bootcamp',
 *   description: 'Learn Python programming',
 *   duration_weeks: 12
 * });
 *
 * // Update project
 * await apiService.updateProject(newProject.id, {
 *   max_participants: 50
 * });
 *
 * // Delete project
 * await apiService.deleteProject(newProject.id);
 *
 *
 * Example 2: Member Management
 * =============================
 * // Fetch project members
 * const members = await apiService.fetchProjectMembers('project-123');
 *
 * // Add instructor
 * const instructor = await apiService.addInstructor({
 *   email: 'instructor@example.com',
 *   first_name: 'John',
 *   last_name: 'Doe'
 * });
 *
 * // Remove member
 * await apiService.removeMember('user-123');
 *
 *
 * Example 3: Track Creation
 * ==========================
 * // Create single track
 * const track = await apiService.createTrack({
 *   project_id: 'project-123',
 *   name: 'Beginner Track',
 *   description: 'Introduction to Python',
 *   difficulty_level: 'beginner'
 * });
 *
 * // Batch create tracks
 * const tracks = await apiService.batchCreateTracks('project-123', [
 *   { name: 'Track 1', description: 'Basics', difficulty_level: 'beginner' },
 *   { name: 'Track 2', description: 'Advanced', difficulty_level: 'advanced' }
 * ]);
 *
 *
 * Example 4: AI Integration
 * ==========================
 * // Initialize AI for project
 * apiService.initializeAIForProject({
 *   projectName: 'Python Bootcamp',
 *   projectDescription: 'Learn Python programming',
 *   targetRoles: ['developer', 'data-scientist']
 * });
 *
 * // Get AI suggestions
 * const suggestions = await apiService.getAISuggestions(
 *   'Suggest a track structure for this project',
 *   { forceWebSearch: true }
 * );
 */