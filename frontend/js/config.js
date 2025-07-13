// Configuration for Course Creator Platform
// This file contains all API endpoints and host configurations

// Get host from environment or use default
const getHost = () => {
    // Check for environment-specific host
    if (typeof window !== 'undefined' && window.location) {
        const hostname = window.location.hostname;
        
        // If accessing via the external IP, use that for API calls too
        if (hostname === '176.9.99.103') {
            return '176.9.99.103';
        }
        
        // Development environments
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Even in development, use the external IP for API calls
            return '176.9.99.103';
        }
        
        // Production or other environments
        return hostname;
    }
    
    // Fallback - use the external IP
    return '176.9.99.103';
};

// Configuration object
const CONFIG = {
    // Host configuration - force to external IP
    HOST: '176.9.99.103',
    
    // Service ports
    PORTS: {
        USER_MANAGEMENT: 8000,
        COURSE_GENERATOR: 8001,
        CONTENT_STORAGE: 8003,
        COURSE_MANAGEMENT: 8004,
        FRONTEND: 3000
    },
    
    // Build API URLs
    get API_URLS() {
        const host = this.HOST;
        return {
            USER_MANAGEMENT: `http://${host}:${this.PORTS.USER_MANAGEMENT}`,
            COURSE_GENERATOR: `http://${host}:${this.PORTS.COURSE_GENERATOR}`,
            CONTENT_STORAGE: `http://${host}:${this.PORTS.CONTENT_STORAGE}`,
            COURSE_MANAGEMENT: `http://${host}:${this.PORTS.COURSE_MANAGEMENT}`
        };
    },
    
    // Specific API endpoints
    get ENDPOINTS() {
        const urls = this.API_URLS;
        return {
            // User Management
            AUTH: `${urls.USER_MANAGEMENT}/auth`,
            LOGIN: `${urls.USER_MANAGEMENT}/auth/login`,
            REGISTER: `${urls.USER_MANAGEMENT}/auth/register`,
            RESET_PASSWORD: `${urls.USER_MANAGEMENT}/auth/reset-password`,
            PROFILE: `${urls.USER_MANAGEMENT}/users/profile`,
            USER_BY_EMAIL: (email) => `${urls.USER_MANAGEMENT}/users/by-email/${email}`,
            
            // Course Management
            COURSES: `${urls.COURSE_MANAGEMENT}/courses`,
            COURSE_BY_ID: (id) => `${urls.COURSE_MANAGEMENT}/courses/${id}`,
            ENROLL_STUDENT: `${urls.COURSE_MANAGEMENT}/instructor/enroll-student`,
            REGISTER_STUDENTS: `${urls.COURSE_MANAGEMENT}/instructor/register-students`,
            COURSE_STUDENTS: (courseId) => `${urls.COURSE_MANAGEMENT}/instructor/course/${courseId}/students`,
            REMOVE_ENROLLMENT: (enrollmentId) => `${urls.COURSE_MANAGEMENT}/instructor/enrollment/${enrollmentId}`,
            
            // Course Generator
            GENERATE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/generate`,
            REFINE_SYLLABUS: `${urls.COURSE_GENERATOR}/syllabus/refine`,
            GENERATE_CONTENT: `${urls.COURSE_GENERATOR}/content/generate-from-syllabus`,
            SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/${courseId}`,
            UPDATE_SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/update/${courseId}`,
            GENERATE_SLIDES: `${urls.COURSE_GENERATOR}/slides/generate`,
            SYLLABUS: (courseId) => `${urls.COURSE_GENERATOR}/syllabus/${courseId}`,
            LAB_BY_COURSE: (courseId) => `${urls.COURSE_GENERATOR}/lab/${courseId}`,
            QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quizzes/${courseId}`,
            LAB_LAUNCH: `${urls.COURSE_GENERATOR}/lab/launch`,
            LAB_STOP: (courseId) => `${urls.COURSE_GENERATOR}/lab/stop/${courseId}`,
            LAB_ACCESS: (courseId) => `${urls.COURSE_GENERATOR}/lab/access/${courseId}`,
            LAB_CHAT: `${urls.COURSE_GENERATOR}/lab/chat`,
            LAB_GENERATE_EXERCISE: `${urls.COURSE_GENERATOR}/lab/generate-exercise`,
            LAB_GENERATE_QUIZ: `${urls.COURSE_GENERATOR}/lab/generate-quiz`,
            LAB_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/lab/analytics/${courseId}`,
            LAB_SESSION_SAVE: `${urls.COURSE_GENERATOR}/lab/session/save`,
            LAB_SESSION_LOAD: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
            LAB_SESSION_CLEAR: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
            SAVE_COURSE: `${urls.COURSE_GENERATOR}/courses/save`
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
}