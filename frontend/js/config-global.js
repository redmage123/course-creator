/**
 * GLOBAL CONFIG FOR SCRIPT TAG USAGE
 * 
 * PURPOSE: Provides CONFIG object for HTML pages using regular <script> tags
 * WHY: Avoids ES6 export syntax errors in non-module contexts
 * USAGE: Include with <script src="config-global.js"></script>
 */

/**
 * DYNAMIC HOST DETECTION FUNCTION
 * 
 * PURPOSE: Automatically detects the appropriate API host based on current environment
 * WHY: Allows the same frontend code to work in development, staging, and production
 * without hardcoded environment-specific values
 * 
 * LOGIC FLOW:
 * 1. Check if running in browser environment (window object exists)
 * 2. Extract hostname from current URL to determine environment context
 * 3. Apply environment-specific routing rules for API calls
 * 4. Fall back to external IP if detection fails
 * 
 * SUPPORTED ENVIRONMENTS:
 * - localhost: Development environment with Docker services
 * - 192.168.x.x: Local network development  
 * - External hosts: Production deployment with proper DNS
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
     */
    get PROTOCOL() {
        // For API calls, always use HTTP in development (localhost)
        if (typeof window !== 'undefined') {
            const hostname = window.location.hostname;
            // Use HTTP for localhost and local IPs for development
            if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.')) {
                return 'http';
            }
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
            USER_BY_EMAIL: (email) => `${urls.USER_MANAGEMENT}/users/by-email/${email}`,
            
            /* ================================================================
             * COURSE MANAGEMENT SERVICE ENDPOINTS (Port 8004)
             * PURPOSE: Course CRUD operations, enrollment, instructor tools
             * ================================================================ */
            COURSES: `${urls.COURSE_MANAGEMENT}/courses`,
            COURSE_BY_ID: (id) => `${urls.COURSE_MANAGEMENT}/courses/${id}`,
            ENROLL_STUDENT: `${urls.COURSE_MANAGEMENT}/instructor/enroll-student`,
            REGISTER_STUDENTS: `${urls.COURSE_MANAGEMENT}/instructor/register-students`,
            COURSE_STUDENTS: (courseId) => `${urls.COURSE_MANAGEMENT}/instructor/course/${courseId}/students`,
            REMOVE_ENROLLMENT: (enrollmentId) => `${urls.COURSE_MANAGEMENT}/instructor/enrollment/${enrollmentId}`,
            
            /* ================================================================
             * COURSE GENERATOR SERVICE ENDPOINTS (Port 8001)
             * PURPOSE: AI-powered content generation using Claude/OpenAI APIs
             * ================================================================ */
            
            /* SYLLABUS GENERATION */
            GENERATE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/generate`,
            REFINE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/refine`,
            SYLLABUS: (courseId) => `${urls.COURSE_GENERATOR}/syllabus/${courseId}`,
            
            /* CONTENT GENERATION */
            GENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/generate-from-syllabus`,
            REGENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/regenerate`,
            SAVE_COURSE: `${urls.COURSE_GENERATOR}/courses/save`,
            
            /* SLIDE GENERATION */
            SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/${courseId}`,
            UPDATE_SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/update/${courseId}`,
            GENERATE_SLIDES: `${urls.COURSE_GENERATOR}/slides/generate`,
            
            /* QUIZ SYSTEM */
            QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quizzes/${courseId}`,
            QUIZ_GENERATE_FOR_COURSE: `${urls.COURSE_GENERATOR}/quiz/generate-for-course`,
            QUIZ_GENERATE: `${urls.COURSE_GENERATOR}/quiz/generate`,
            QUIZ_GET_COURSE_QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quiz/course/${courseId}`,
            QUIZ_GET_BY_ID: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}`,
            QUIZ_SUBMIT: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}/submit`,
            QUIZ_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/quiz/analytics/${courseId}`,
            
            /* LAB ENVIRONMENT MANAGEMENT */
            LAB_BY_COURSE: (courseId) => `${urls.COURSE_GENERATOR}/lab/${courseId}`,
            LAB_LAUNCH: `${urls.COURSE_GENERATOR}/lab/launch`,
            LAB_STOP: (courseId) => `${urls.COURSE_GENERATOR}/lab/stop/${courseId}`,
            LAB_ACCESS: (courseId) => `${urls.COURSE_GENERATOR}/lab/access/${courseId}`,
            LAB_GENERATE_EXERCISE: `${urls.COURSE_GENERATOR}/lab/generate-exercise`,
            LAB_GENERATE_QUIZ: `${urls.COURSE_GENERATOR}/lab/generate-quiz`,
            LAB_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/lab/analytics/${courseId}`,
            GENERATE_CUSTOM_LAB: `${urls.COURSE_GENERATOR}/lab/generate-custom`,
            REFRESH_LAB_EXERCISES: `${urls.COURSE_GENERATOR}/lab/refresh-exercises`,
            EXERCISES: (courseId) => `${urls.COURSE_GENERATOR}/exercises/${courseId}`,
            
            /* LAB SESSION MANAGEMENT */
            LAB_CHAT: `${urls.COURSE_GENERATOR}/lab/chat`,
            LAB_SESSION_SAVE: `${urls.COURSE_GENERATOR}/lab/session/save`,
            LAB_SESSION_LOAD: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
            LAB_SESSION_CLEAR: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
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