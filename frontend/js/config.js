/**
 * Frontend Configuration
 *
 * Central configuration for all API endpoints and application settings
 */
export const CONFIG = {
    ENDPOINTS: {
        // Core Services (via nginx proxy on port 3000)
        COURSES: 'https://localhost:3000/api/v1/courses',
        CONTENT_SERVICE: 'https://localhost:8002',
        METADATA_SERVICE: 'https://localhost:8003',
        LAB_MANAGER: 'https://localhost:8001',
        USER_MANAGEMENT: 'https://localhost:8000',
        COURSE_MANAGEMENT: 'https://localhost:3000/api/v1/courses',
        COURSE_SERVICE: 'https://localhost:3000/api/v1/courses',  // Via nginx proxy
        COURSE_GENERATOR: 'https://localhost:8009',
        ANALYTICS: 'https://localhost:8004',
        NLP_PREPROCESSING: 'https://localhost:8005',
        KNOWLEDGE_GRAPH: 'https://localhost:8006',
        ORGANIZATION_MANAGEMENT: 'https://localhost:8007',
        DEMO_SERVICE: 'https://localhost:8010',

        // Specific Endpoints
    /**
     * EXECUTE SYLLABUS OPERATION
     * PURPOSE: Execute SYLLABUS operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
        SYLLABUS: (courseId) => `https://localhost:8002/courses/${courseId}/syllabus`,
    /**
     * EXECUTE SLIDES OPERATION
     * PURPOSE: Execute SLIDES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
        SLIDES: (courseId) => `https://localhost:8002/courses/${courseId}/slides`,
    /**
     * EXECUTE LAB BY COURSE OPERATION
     * PURPOSE: Execute LAB BY COURSE operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
        LAB_BY_COURSE: (courseId) => `https://localhost:8001/labs/course/${courseId}`,
    /**
     * EXECUTE QUIZZES OPERATION
     * PURPOSE: Execute QUIZZES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
        QUIZZES: (courseId) => `https://localhost:8000/quizzes/course/${courseId}`,
    /**
     * EXECUTE QUIZ GET COURSE QUIZZES OPERATION
     * PURPOSE: Execute QUIZ GET COURSE QUIZZES operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
        QUIZ_GET_COURSE_QUIZZES: (courseId) => `https://localhost:8000/quizzes/course/${courseId}`,
        REFRESH_LAB_EXERCISES: 'https://localhost:8001/lab/refresh-exercises',

        // Course Management API
        PUBLISHED_COURSES: 'https://localhost:8004/courses?status=published',
        COURSE_INSTANCES: 'https://localhost:8004/course-instances',
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
        INSTRUCTOR_INSTANCES: (instructorId) => `https://localhost:8004/course-instances?instructor_id=${instructorId}`
    },

    API_URLS: {
        // Used by various modules (via nginx proxy on port 3000)
        CONTENT_MANAGEMENT: 'https://localhost:8002',
        LAB_MANAGER: 'https://localhost:8001',
        METADATA_SERVICE: 'https://localhost:8003',
        USER_SERVICE: 'https://localhost:8000',
        COURSE_SERVICE: 'https://localhost:3000/api/v1/courses',  // Via nginx proxy
        ANALYTICS_SERVICE: 'https://localhost:8004',
        NLP_SERVICE: 'https://localhost:8005',
        KNOWLEDGE_GRAPH_SERVICE: 'https://localhost:8006',
        ORGANIZATION_SERVICE: 'https://localhost:8007',
        COURSE_GENERATOR_SERVICE: 'https://localhost:8009',
        DEMO_SERVICE: 'https://localhost:8010'
    },

    // Application Settings
    SETTINGS: {
        DEFAULT_PAGE_SIZE: 20,
        MAX_FILE_SIZE_MB: 50,
        SUPPORTED_VIDEO_TYPES: ['youtube', 'vimeo', 'upload', 'link'],
        SUPPORTED_UPLOAD_FORMATS: {
            syllabus: ['.pdf', '.doc', '.docx', '.txt', '.md'],
            slides: ['.ppt', '.pptx', '.pdf', '.json'],
            labs: ['.json', '.zip'],
            quizzes: ['.json']
        }
    }
};

export default CONFIG;
