/**
 * CONFIGURATION FOR COURSE CREATOR PLATFORM
 * 
 * PURPOSE: Centralized configuration management for all frontend API communications
 * WHY: Single source of truth for service endpoints prevents configuration drift
 * across different dashboard components and enables easy environment switching
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
 */
const getHost = () => {
    // BROWSER ENVIRONMENT CHECK: Ensure we're running in a web browser context
    // WHY: Prevents errors when this config is imported in Node.js environments
    if (typeof window !== 'undefined' && window.location) {
        const hostname = window.location.hostname;
        
        // EXTERNAL IP ACCESS: Direct external server access scenario
        // WHY: When users access via external IP, API calls must use same IP
        // to avoid CORS issues and routing problems
        if (hostname === '176.9.99.103') {
            return '176.9.99.103';
        }
        
        // DEVELOPMENT ENVIRONMENT: Local development setup
        // WHY: Even in local development, we route API calls to external server
        // because backend services are deployed there, not running locally
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // IMPORTANT: Force external IP even in development
            // WHY: Local frontend connects to remote backend services
            return '176.9.99.103';
        }
        
        // PRODUCTION/OTHER ENVIRONMENTS: Use whatever hostname is being accessed
        // WHY: Allows flexibility for future deployments on different domains
        return hostname;
    }
    
    // FALLBACK SCENARIO: Default to external IP if detection fails
    // WHY: Ensures API calls work even if environment detection logic fails
    return '176.9.99.103';
};

/**
 * MAIN CONFIGURATION OBJECT
 * 
 * PURPOSE: Centralized configuration for all Course Creator Platform services
 * WHY: Object-oriented approach allows dynamic URL generation and easy maintenance
 * STRUCTURE: Uses getters for dynamic property calculation and consistent API structure
 */
const CONFIG = {
    /**
     * HOST CONFIGURATION
     * PURPOSE: Primary host for all backend API services
     * WHY: Hardcoded to external IP because all microservices run on same server
     * NOTE: Could be made dynamic in future for multi-server deployments
     */
    HOST: '176.9.99.103',
    
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
     * WHY: HTTPS provides encrypted communication and is production security standard
     * 
     * SECURITY REQUIREMENT: Always use HTTPS for secure communication
     * All Course Creator Platform services must use encrypted connections
     */
    PROTOCOL: 'https',
    
    /**
     * DYNAMIC API URL BUILDER
     * PURPOSE: Constructs complete service URLs from protocol, host and port configuration
     * WHY: Getter pattern ensures URLs are always current if protocol/host/ports change
     * USAGE: Accessed as CONFIG.API_URLS.USER_MANAGEMENT
     */
    get API_URLS() {
        const protocol = this.PROTOCOL;
        const host = this.HOST;
        return {
            // Build HTTPS URLs for each microservice (secure by default)
            // WHY: HTTPS provides encryption and authentication for production security
            // NOTE: Protocol can be overridden to HTTP for local development if needed
            USER_MANAGEMENT: `${protocol}://${host}:${this.PORTS.USER_MANAGEMENT}`,
            COURSE_GENERATOR: `${protocol}://${host}:${this.PORTS.COURSE_GENERATOR}`,
            CONTENT_STORAGE: `${protocol}://${host}:${this.PORTS.CONTENT_STORAGE}`,
            COURSE_MANAGEMENT: `${protocol}://${host}:${this.PORTS.COURSE_MANAGEMENT}`,
            LAB_MANAGER: `${protocol}://${host}:${this.PORTS.LAB_MANAGER}`,
            ANALYTICS: `${protocol}://${host}:${this.PORTS.ANALYTICS}`,
            ORGANIZATION: `${protocol}://${host}:${this.PORTS.ORGANIZATION}`
        };
    },
    
    /**
     * COMPLETE API ENDPOINT CATALOG
     * PURPOSE: Provides ready-to-use endpoint URLs for all platform functionality
     * WHY: Getter pattern ensures endpoints reflect current service URLs
     * ORGANIZATION: Grouped by service for easy maintenance and discovery
     */
    get ENDPOINTS() {
        const urls = this.API_URLS;
        return {
            // ================================================================
            // USER MANAGEMENT SERVICE ENDPOINTS (Port 8000)
            // PURPOSE: Authentication, user profiles, session management
            // ================================================================
            AUTH: `${urls.USER_MANAGEMENT}/auth`,                          // General auth operations
            LOGIN: `${urls.USER_MANAGEMENT}/auth/login`,                   // User login with credentials
            REGISTER: `${urls.USER_MANAGEMENT}/auth/register`,             // New user registration
            RESET_PASSWORD: `${urls.USER_MANAGEMENT}/auth/reset-password`, // Password reset workflow
            PROFILE: `${urls.USER_MANAGEMENT}/users/profile`,              // User profile CRUD operations
            USER_BY_EMAIL: (email) => `${urls.USER_MANAGEMENT}/users/by-email/${email}`, // User lookup by email
            
            // ================================================================
            // COURSE MANAGEMENT SERVICE ENDPOINTS (Port 8004)
            // PURPOSE: Course CRUD operations, enrollment, instructor tools
            // ================================================================
            COURSES: `${urls.COURSE_MANAGEMENT}/courses`,                  // List all courses
            COURSE_BY_ID: (id) => `${urls.COURSE_MANAGEMENT}/courses/${id}`, // Get specific course details
            ENROLL_STUDENT: `${urls.COURSE_MANAGEMENT}/instructor/enroll-student`, // Single student enrollment
            REGISTER_STUDENTS: `${urls.COURSE_MANAGEMENT}/instructor/register-students`, // Bulk student registration
            COURSE_STUDENTS: (courseId) => `${urls.COURSE_MANAGEMENT}/instructor/course/${courseId}/students`, // List course enrollments
            REMOVE_ENROLLMENT: (enrollmentId) => `${urls.COURSE_MANAGEMENT}/instructor/enrollment/${enrollmentId}`, // Remove student from course
            
            // ================================================================
            // COURSE GENERATOR SERVICE ENDPOINTS (Port 8001)
            // PURPOSE: AI-powered content generation using Claude/OpenAI APIs
            // ================================================================
            
            // SYLLABUS GENERATION
            GENERATE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/generate`,      // AI syllabus creation from requirements
            REFINE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/refine`,          // Iterative syllabus improvement
            SYLLABUS: (courseId) => `${urls.COURSE_GENERATOR}/syllabus/${courseId}`, // Retrieve course syllabus
            
            // CONTENT GENERATION
            GENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/generate-from-syllabus`, // Generate all content from syllabus
            REGENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/regenerate`,    // Regenerate specific content sections
            SAVE_COURSE: `${urls.COURSE_GENERATOR}/courses/save`,                 // Persist generated course content
            
            // SLIDE GENERATION
            SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/${courseId}`,        // Get course slide deck
            UPDATE_SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/update/${courseId}`, // Update existing slides
            GENERATE_SLIDES: `${urls.COURSE_GENERATOR}/slides/generate`,          // Create new slide presentations
            
            // QUIZ SYSTEM
            QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quizzes/${courseId}`,      // Get course quizzes
            QUIZ_GENERATE_FOR_COURSE: `${urls.COURSE_GENERATOR}/quiz/generate-for-course`, // Generate course-specific quiz
            QUIZ_GENERATE: `${urls.COURSE_GENERATOR}/quiz/generate`,              // General quiz generation
            QUIZ_GET_COURSE_QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quiz/course/${courseId}`, // List all course quizzes
            QUIZ_GET_BY_ID: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}`, // Get specific quiz
            QUIZ_SUBMIT: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}/submit`, // Submit quiz answers
            QUIZ_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/quiz/analytics/${courseId}`, // Quiz performance analytics
            
            // LAB ENVIRONMENT MANAGEMENT
            LAB_BY_COURSE: (courseId) => `${urls.COURSE_GENERATOR}/lab/${courseId}`,    // Get course lab configuration
            LAB_LAUNCH: `${urls.COURSE_GENERATOR}/lab/launch`,                    // Start new lab environment
            LAB_STOP: (courseId) => `${urls.COURSE_GENERATOR}/lab/stop/${courseId}`,    // Stop lab environment
            LAB_ACCESS: (courseId) => `${urls.COURSE_GENERATOR}/lab/access/${courseId}`, // Get lab access details
            LAB_GENERATE_EXERCISE: `${urls.COURSE_GENERATOR}/lab/generate-exercise`, // AI exercise generation
            LAB_GENERATE_QUIZ: `${urls.COURSE_GENERATOR}/lab/generate-quiz`,      // AI quiz generation for labs
            LAB_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/lab/analytics/${courseId}`, // Lab usage analytics
            GENERATE_CUSTOM_LAB: `${urls.COURSE_GENERATOR}/lab/generate-custom`,  // Custom lab environment creation
            REFRESH_LAB_EXERCISES: `${urls.COURSE_GENERATOR}/lab/refresh-exercises`, // Regenerate lab exercises
            EXERCISES: (courseId) => `${urls.COURSE_GENERATOR}/exercises/${courseId}`, // Get course exercises
            
            // LAB SESSION MANAGEMENT
            LAB_CHAT: `${urls.COURSE_GENERATOR}/lab/chat`,                        // AI assistant chat in labs
            LAB_SESSION_SAVE: `${urls.COURSE_GENERATOR}/lab/session/save`,        // Save student lab progress
            LAB_SESSION_LOAD: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`, // Load student progress
            LAB_SESSION_CLEAR: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`, // Clear session data
        }
    }
};

/**
 * MODULE EXPORT CONFIGURATION
 * PURPOSE: Provides multiple export patterns for different JavaScript environments
 * WHY: Ensures compatibility with both modern ES6 modules and legacy script tags
 */

// ES6 MODULE EXPORTS: For modern JavaScript applications using import/export
// WHY: Named export allows 'import { CONFIG }' syntax for explicit imports
export { CONFIG };

// ES6 DEFAULT EXPORT: For applications using 'import CONFIG from' syntax  
// WHY: Default export provides cleaner import syntax when CONFIG is the main export
export default CONFIG;

// LEGACY BROWSER SUPPORT: For older browsers and script tag inclusion
// PURPOSE: Makes CONFIG available as global window.CONFIG for non-module scripts
// WHY: Enables backwards compatibility with HTML <script> tag usage
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}