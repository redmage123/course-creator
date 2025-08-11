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
        // Default to HTTPS for security, but allow HTTP override for development
        return typeof window !== 'undefined' && window.location.protocol === 'http:' 
            ? 'http' 
            : 'https';
    },

    /**
     * DYNAMIC API URL GENERATION
     * PURPOSE: Generates complete API URLs for each microservice dynamically
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
    }
};

// Make CONFIG available globally for script tag usage
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}