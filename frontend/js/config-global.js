/**
 * GLOBAL CONFIG FOR SCRIPT TAG USAGE
 * 
 * PURPOSE: Provides CONFIG object for HTML pages using regular <script> tags
 * WHY: Avoids ES6 export syntax errors in non-module contexts
 * USAGE: Include with <script src="config-global.js"></script>
 */
function detectHost() {
    // Check if we're in a browser environment
    if (typeof window === 'undefined' || !window.location) {
        return 'localhost'; // Fallback for non-browser environments
    }
    
    const hostname = window.location.hostname;
    
    // Local development patterns
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'localhost';
    }
    
    // Local network development (e.g., 192.168.1.100)
    if (hostname.match(/^192\.168\.\d+\.\d+$/)) {
        return hostname;
    }
    
    // Production or other external hosts
    return hostname;
}

/**
 * MAIN CONFIGURATION OBJECT
 * PURPOSE: Centralized configuration for all Course Creator Platform services
 * WHY: Single source of truth prevents configuration drift and enables easy updates
 */
const CONFIG = {
    /**
     * HOST CONFIGURATION
     * PURPOSE: Dynamic host detection for multi-environment deployment
     * WHY: Enables same codebase to work across development, staging, production
     */
    get HOST() {
        return detectHost();
    },
    
    /**
     * SERVICE PORT MAPPING
     * PURPOSE: Maps each microservice to its dedicated port number
     * WHY: Microservices architecture requires port-based service discovery
     * MAINTENANCE: Update these when service ports change in deployment
     */
    PORTS: {
        USER_MANAGEMENT: 8000,    // Authentication, user profiles, session management
        COURSE_GENERATOR: 8001,   // AI-powered content generation (syllabus, slides, labs)
        CONTENT_STORAGE: 8003,    // File storage and content management
        COURSE_MANAGEMENT: 8004,  // Course CRUD, enrollment, feedback systems
        FRONTEND: 3000,           // Static frontend serving (this application)
        LAB_MANAGER: 8006,        // Lab container management and student environments
        ANALYTICS: 8007,          // Analytics service and reporting
        ORGANIZATION: 8008        // Organization management and RBAC
    },
    
    /**
     * PROTOCOL CONFIGURATION
     * PURPOSE: Defines default protocol for all API communications
     * WHY: Centralized protocol management enables easy HTTPS migration
     * SECURITY: HTTPS preferred for production environments
     * FLEXIBILITY: Can be overridden for specific development needs
     *
     * BUSINESS CONTEXT:
     * The platform runs on HTTPS in all environments (including localhost on port 3000).
     * All API calls should use the same protocol as the current page to avoid mixed content errors.
     *
     * TECHNICAL RATIONALE:
     * - nginx serves frontend on https://localhost:3000
     * - All API calls go through nginx reverse proxy on same port
     * - Using HTTP would cause the browser to redirect to HTTPS on default port 443, bypassing nginx
     */
    get PROTOCOL() {
        // Use the current page's protocol to ensure consistency
        if (typeof window !== 'undefined' && window.location.protocol) {
            return window.location.protocol.replace(':', '');  // Returns 'http' or 'https'
        }
        // Default to HTTPS for production environments
        return 'https';
    },

    /**
     * DYNAMIC API URL GENERATION
     * PURPOSE: Generates complete API URLs for each microservice dynamically
     * WHY: Getter pattern ensures URLs are always current if protocol/host/ports change
     * USAGE: Accessed as window.CONFIG?.API_URLS.USER_MANAGEMENT
     */
    get API_URLS() {
        const protocol = this.PROTOCOL;
        const host = this.HOST;
        return {
            /* CORE MICROSERVICE URLS: Base URLs for each platform service */
            USER_MANAGEMENT: `${protocol}://${host}:${this.PORTS.USER_MANAGEMENT}`,
            COURSE_GENERATOR: `${protocol}://${host}:${this.PORTS.COURSE_GENERATOR}`,
            CONTENT_STORAGE: `${protocol}://${host}:${this.PORTS.CONTENT_STORAGE}`,
            COURSE_MANAGEMENT: `${protocol}://${host}:${this.PORTS.COURSE_MANAGEMENT}`,
            LAB_MANAGER: `${protocol}://${host}:${this.PORTS.LAB_MANAGER}`,
            ANALYTICS: `${protocol}://${host}:${this.PORTS.ANALYTICS}`,
            ORGANIZATION: `${protocol}://${host}:${this.PORTS.ORGANIZATION}`,
            ORGANIZATION_MANAGEMENT: `${protocol}://${host}:${this.PORTS.ORGANIZATION}`  // Alias for org-admin-api.js
        };
    },

    /**
     * COMPLETE API ENDPOINT CATALOG
     * PURPOSE: Provides ready-to-use endpoint URLs for all platform functionality
     * WHY: Centralized endpoint management prevents URL drift and enables easy maintenance
     * ORGANIZATION: Grouped by service for easy discovery and maintenance
     * 
     * CONSOLIDATED FROM: Merged endpoints from config.js to eliminate duplication
     * ENHANCED WITH: Dynamic protocol and host detection for all environments
     */
    get ENDPOINTS() {
        const urls = this.API_URLS;
        return {
            /* ================================================================
             * USER MANAGEMENT SERVICE ENDPOINTS (Port 8000)
             * PURPOSE: Authentication, user profiles, session management
             * ================================================================ */
            AUTH: `${urls.USER_MANAGEMENT}/auth`,
            LOGIN: `${urls.USER_MANAGEMENT}/auth/login`,
            REGISTER: `${urls.USER_MANAGEMENT}/auth/register`,
            RESET_PASSWORD: `${urls.USER_MANAGEMENT}/auth/reset-password`,
            PROFILE: `${urls.USER_MANAGEMENT}/users/profile`,
    /**
     * EXECUTE USER BY EMAIL OPERATION
     * PURPOSE: Execute USER BY EMAIL operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} email - Email address
     */
            USER_BY_EMAIL: (email) => `${urls.USER_MANAGEMENT}/users/by-email/${email}`,
            
            /* ================================================================
             * COURSE MANAGEMENT SERVICE ENDPOINTS (Port 8004)
             * PURPOSE: Course CRUD operations, enrollment, instructor tools
             * ================================================================ */
            COURSES: `${urls.COURSE_MANAGEMENT}/courses`,
            COURSE_SERVICE: `/api/v1/courses`,  // Via nginx proxy (relative URL)
    /**
     * EXECUTE COURSE BY ID OPERATION
     * PURPOSE: Execute COURSE BY ID operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} id - Unique identifier
     */
            COURSE_BY_ID: (id) => `${urls.COURSE_MANAGEMENT}/courses/${id}`,
            ENROLL_STUDENT: `${urls.COURSE_MANAGEMENT}/instructor/enroll-student`,
            REGISTER_STUDENTS: `${urls.COURSE_MANAGEMENT}/instructor/register-students`,
    /**
     * EXECUTE COURSE STUDENTS OPERATION
     * PURPOSE: Execute COURSE STUDENTS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            COURSE_STUDENTS: (courseId) => `${urls.COURSE_MANAGEMENT}/instructor/course/${courseId}/students`,
    /**
     * EXECUTE REMOVE ENROLLMENT OPERATION
     * PURPOSE: Execute REMOVE ENROLLMENT operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} enrollmentId - Enrollmentid parameter
     */
            REMOVE_ENROLLMENT: (enrollmentId) => `${urls.COURSE_MANAGEMENT}/instructor/enrollment/${enrollmentId}`,
            
            /* ================================================================
             * COURSE GENERATOR SERVICE ENDPOINTS (Port 8001)
             * PURPOSE: AI-powered content generation using Claude/OpenAI APIs
             * ================================================================ */
            
            /* SYLLABUS GENERATION */
            GENERATE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/generate`,
            REFINE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/refine`,
    /**
     * EXECUTE SYLLABUS OPERATION
     * PURPOSE: Execute SYLLABUS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            SYLLABUS: (courseId) => `${urls.COURSE_GENERATOR}/syllabus/${courseId}`,
            
            /* CONTENT GENERATION */
            GENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/generate-from-syllabus`,
            REGENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/regenerate`,
            SAVE_COURSE: `${urls.COURSE_GENERATOR}/courses/save`,
            
            /* SLIDE GENERATION */
    /**
     * EXECUTE SLIDES OPERATION
     * PURPOSE: Execute SLIDES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/${courseId}`,
    /**
     * EXECUTE UPDATE SLIDES OPERATION
     * PURPOSE: Execute UPDATE SLIDES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            UPDATE_SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/update/${courseId}`,
            GENERATE_SLIDES: `${urls.COURSE_GENERATOR}/slides/generate`,
            
            /* QUIZ SYSTEM */
    /**
     * EXECUTE QUIZZES OPERATION
     * PURPOSE: Execute QUIZZES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quizzes/${courseId}`,
            QUIZ_GENERATE_FOR_COURSE: `${urls.COURSE_GENERATOR}/quiz/generate-for-course`,
            QUIZ_GENERATE: `${urls.COURSE_GENERATOR}/quiz/generate`,
    /**
     * EXECUTE QUIZ GET COURSE QUIZZES OPERATION
     * PURPOSE: Execute QUIZ GET COURSE QUIZZES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            QUIZ_GET_COURSE_QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quiz/course/${courseId}`,
    /**
     * EXECUTE QUIZ GET BY ID OPERATION
     * PURPOSE: Execute QUIZ GET BY ID operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} quizId - Quizid parameter
     */
            QUIZ_GET_BY_ID: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}`,
    /**
     * EXECUTE QUIZ SUBMIT OPERATION
     * PURPOSE: Execute QUIZ SUBMIT operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} quizId - Quizid parameter
     */
            QUIZ_SUBMIT: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}/submit`,
    /**
     * EXECUTE QUIZ ANALYTICS OPERATION
     * PURPOSE: Execute QUIZ ANALYTICS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            QUIZ_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/quiz/analytics/${courseId}`,
            
            /* LAB ENVIRONMENT MANAGEMENT */
    /**
     * EXECUTE LAB BY COURSE OPERATION
     * PURPOSE: Execute LAB BY COURSE operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            LAB_BY_COURSE: (courseId) => `${urls.COURSE_GENERATOR}/lab/${courseId}`,
            LAB_LAUNCH: `${urls.COURSE_GENERATOR}/lab/launch`,
    /**
     * EXECUTE LAB STOP OPERATION
     * PURPOSE: Execute LAB STOP operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            LAB_STOP: (courseId) => `${urls.COURSE_GENERATOR}/lab/stop/${courseId}`,
    /**
     * EXECUTE LAB ACCESS OPERATION
     * PURPOSE: Execute LAB ACCESS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            LAB_ACCESS: (courseId) => `${urls.COURSE_GENERATOR}/lab/access/${courseId}`,
            LAB_GENERATE_EXERCISE: `${urls.COURSE_GENERATOR}/lab/generate-exercise`,
            LAB_GENERATE_QUIZ: `${urls.COURSE_GENERATOR}/lab/generate-quiz`,
    /**
     * EXECUTE LAB ANALYTICS OPERATION
     * PURPOSE: Execute LAB ANALYTICS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            LAB_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/lab/analytics/${courseId}`,
            GENERATE_CUSTOM_LAB: `${urls.COURSE_GENERATOR}/lab/generate-custom`,
            REFRESH_LAB_EXERCISES: `${urls.COURSE_GENERATOR}/lab/refresh-exercises`,
    /**
     * EXECUTE EXERCISES OPERATION
     * PURPOSE: Execute EXERCISES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
            EXERCISES: (courseId) => `${urls.COURSE_GENERATOR}/exercises/${courseId}`,
            
            /* LAB SESSION MANAGEMENT */
            LAB_CHAT: `${urls.COURSE_GENERATOR}/lab/chat`,
            LAB_SESSION_SAVE: `${urls.COURSE_GENERATOR}/lab/session/save`,
    /**
     * EXECUTE LAB SESSION LOAD OPERATION
     * PURPOSE: Execute LAB SESSION LOAD operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     * @param {string|number} studentId - Studentid parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            LAB_SESSION_LOAD: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
    /**
     * EXECUTE LAB SESSION CLEAR OPERATION
     * PURPOSE: Execute LAB SESSION CLEAR operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     * @param {string|number} studentId - Studentid parameter
     */
            LAB_SESSION_CLEAR: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,

            /* ================================================================
             * COURSE INSTANCE MANAGEMENT ENDPOINTS
             * PURPOSE: Manage course instances and published courses
             * ================================================================ */
            PUBLISHED_COURSES: `https://localhost:8004/courses?status=published`,
            COURSE_INSTANCES: `https://localhost:8004/course-instances`,
    /**
     * EXECUTE COURSES BY STATUS OPERATION
     * PURPOSE: Execute COURSES BY STATUS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} status - Status parameter
     */
            COURSES_BY_STATUS: (status) => `https://localhost:8004/courses?status=${status}`,
    /**
     * EXECUTE INSTRUCTOR INSTANCES OPERATION
     * PURPOSE: Execute INSTRUCTOR INSTANCES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} instructorId - Instructorid parameter
     */
            INSTRUCTOR_INSTANCES: (instructorId) => `https://localhost:8004/course-instances?instructor_id=${instructorId}`,
        }
    }
};

// Make CONFIG available globally for script tag usage
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}

// Export for ES6 module usage (commented out for script tag compatibility)
// export { CONFIG };

// Also export as default for flexibility  
// export default CONFIG;

// Export for CommonJS module usage (only if module context)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG };
}