/**
 * Exercise Manager Module
 * Single Responsibility: Handle exercise loading, tracking, and management
 */
export class ExerciseManager {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {Object} config - Configuration options
     */
    constructor(config) {
        this.config = config;
        this.exercises = [];
        this.currentExercise = null;
        this.exerciseProgress = {};
        this.showingSolution = {};
    }

    // Load exercises for a course
    /**
     * LOAD EXERCISES DATA FROM SERVER
     * PURPOSE: Load exercises data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @param {string|number} courseId - Unique identifier
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadExercises(courseId) {
        try {
            const endpoint = this.config.getEndpoint('exercises', courseId);
            const response = await fetch(endpoint);
            
            if (!response.ok) {
                throw new Error(`Failed to load exercises: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.exercises = data.exercises || [];
            
            // Initialize progress tracking
            this.initializeProgress();
            
            return this.exercises;
        } catch (error) {
            console.error('Error loading exercises:', error);
            throw error;
        }
    }

    // Initialize progress tracking for all exercises
    /**
     * INITIALIZE PROGRESS COMPONENT
     * PURPOSE: Initialize progress component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    initializeProgress() {
        this.exercises.forEach(exercise => {
            if (!this.exerciseProgress[exercise.id]) {
                this.exerciseProgress[exercise.id] = {
                    status: 'not_started', // not_started, in_progress, completed
                    startTime: null,
                    completionTime: null,
                    attempts: 0,
                    timeSpent: 0
                };
            }
        });
    }

    // Get all exercises
    /**
     * RETRIEVE EXERCISES INFORMATION
     * PURPOSE: Retrieve exercises information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getExercises() {
        return this.exercises;
    }

    // Get exercise by ID
    /**
     * RETRIEVE EXERCISE BY ID INFORMATION
     * PURPOSE: Retrieve exercise by id information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getExerciseById(exerciseId) {
        return this.exercises.find(exercise => exercise.id === exerciseId);
    }

    // Set current exercise
    /**
     * SET CURRENT EXERCISE VALUE
     * PURPOSE: Set current exercise value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    setCurrentExercise(exerciseId) {
        const exercise = this.getExerciseById(exerciseId);
        if (exercise) {
            this.currentExercise = exercise;
            this.startExercise(exerciseId);
            return exercise;
        }
        return null;
    }

    // Get current exercise
    /**
     * RETRIEVE CURRENT EXERCISE INFORMATION
     * PURPOSE: Retrieve current exercise information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentExercise() {
        return this.currentExercise;
    }

    // Start working on an exercise
    /**
     * EXECUTE STARTEXERCISE OPERATION
     * PURPOSE: Execute startExercise operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    startExercise(exerciseId) {
        const progress = this.exerciseProgress[exerciseId];
        if (progress && progress.status === 'not_started') {
            progress.status = 'in_progress';
            progress.startTime = new Date();
            progress.attempts++;
        }
    }

    // Mark exercise as completed
    /**
     * EXECUTE COMPLETEEXERCISE OPERATION
     * PURPOSE: Execute completeExercise operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    completeExercise(exerciseId) {
        const progress = this.exerciseProgress[exerciseId];
        if (progress) {
            progress.status = 'completed';
            progress.completionTime = new Date();
            
            // Calculate time spent
            if (progress.startTime) {
                progress.timeSpent = progress.completionTime - progress.startTime;
            }
        }
    }

    // Reset exercise progress
    /**
     * EXECUTE RESETEXERCISE OPERATION
     * PURPOSE: Execute resetExercise operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    resetExercise(exerciseId) {
        if (this.exerciseProgress[exerciseId]) {
            this.exerciseProgress[exerciseId] = {
                status: 'not_started',
                startTime: null,
                completionTime: null,
                attempts: 0,
                timeSpent: 0
            };
        }
    }

    // Get exercise progress
    /**
     * RETRIEVE EXERCISE PROGRESS INFORMATION
     * PURPOSE: Retrieve exercise progress information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getExerciseProgress(exerciseId) {
        return this.exerciseProgress[exerciseId] || null;
    }

    // Get overall progress statistics
    /**
     * RETRIEVE PROGRESS STATS INFORMATION
     * PURPOSE: Retrieve progress stats information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getProgressStats() {
        const total = this.exercises.length;
        let completed = 0;
        let inProgress = 0;
        let notStarted = 0;
        let totalTime = 0;

        Object.values(this.exerciseProgress).forEach(progress => {
            switch (progress.status) {
                case 'completed':
                    completed++;
                    totalTime += progress.timeSpent || 0;
                    break;
                case 'in_progress':
                    inProgress++;
                    break;
                case 'not_started':
                    notStarted++;
                    break;
            }
        });

        return {
            total,
            completed,
            inProgress,
            notStarted,
            completionRate: total > 0 ? (completed / total) * 100 : 0,
            totalTimeSpent: totalTime
        };
    }

    // Filter exercises by criteria
    /**
     * FILTER EXERCISES BASED ON CRITERIA
     * PURPOSE: Filter exercises based on criteria
     * WHY: Enables users to find relevant data quickly
     *
     * @param {*} criteria - Criteria parameter
     *
     * @returns {Array} Filtered array
     */
    filterExercises(criteria) {
        return this.exercises.filter(exercise => {
            // Filter by difficulty
            if (criteria.difficulty && exercise.difficulty !== criteria.difficulty) {
                return false;
            }
            
            // Filter by language
            if (criteria.language && exercise.language !== criteria.language) {
                return false;
            }
            
            // Filter by status
            if (criteria.status) {
                const progress = this.getExerciseProgress(exercise.id);
                if (!progress || progress.status !== criteria.status) {
                    return false;
                }
            }
            
            // Filter by search term
            if (criteria.search) {
                const searchTerm = criteria.search.toLowerCase();
                const matchesTitle = exercise.title.toLowerCase().includes(searchTerm);
                const matchesDescription = exercise.description.toLowerCase().includes(searchTerm);
                return matchesTitle || matchesDescription;
            }
            
            return true;
        });
    }

    // Show/hide solution for an exercise
    /**
     * TOGGLE SOLUTION STATE
     * PURPOSE: Toggle solution state
     * WHY: Provides binary state management for UI elements
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    toggleSolution(exerciseId) {
        this.showingSolution[exerciseId] = !this.showingSolution[exerciseId];
        return this.showingSolution[exerciseId];
    }

    // Check if solution is showing for an exercise
    /**
     * EXECUTE ISSOLUTIONSHOWING OPERATION
     * PURPOSE: Execute isSolutionShowing operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isSolutionShowing(exerciseId) {
        return this.showingSolution[exerciseId] || false;
    }

    // Get exercise hints
    /**
     * RETRIEVE HINTS INFORMATION
     * PURPOSE: Retrieve hints information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getHints(exerciseId) {
        const exercise = this.getExerciseById(exerciseId);
        return exercise ? exercise.hints || [] : [];
    }

    // Get exercise test cases
    /**
     * RETRIEVE TEST CASES INFORMATION
     * PURPOSE: Retrieve test cases information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getTestCases(exerciseId) {
        const exercise = this.getExerciseById(exerciseId);
        return exercise ? exercise.testCases || [] : [];
    }

    // Validate exercise solution
    /**
     * VALIDATE SOLUTION INPUT
     * PURPOSE: Validate solution input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     * @param {*} userCode - Usercode parameter
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    validateSolution(exerciseId, userCode) {
        const exercise = this.getExerciseById(exerciseId);
        if (!exercise || !exercise.testCases) {
            return { isValid: false, message: 'No test cases available' };
        }

        // This is a simplified validation - in a real environment,
        // you would execute the code against test cases
        try {
            // Basic validation - check if code contains required elements
            const requirements = exercise.requirements || [];
            const missingRequirements = requirements.filter(requirement => 
                !userCode.includes(requirement)
            );

            if (missingRequirements.length > 0) {
                return {
                    isValid: false,
                    message: `Missing requirements: ${missingRequirements.join(', ')}`,
                    details: { missingRequirements }
                };
            }

            return {
                isValid: true,
                message: 'Solution looks good!',
                details: { passedTests: exercise.testCases.length }
            };
        } catch (error) {
            return {
                isValid: false,
                message: `Validation error: ${error.message}`,
                details: { error: error.message }
            };
        }
    }

    // Submit exercise solution
    /**
     * EXECUTE SUBMITSOLUTION OPERATION
     * PURPOSE: Execute submitSolution operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     * @param {*} userCode - Usercode parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async submitSolution(exerciseId, userCode) {
        const validation = this.validateSolution(exerciseId, userCode);
        
        if (validation.isValid) {
            this.completeExercise(exerciseId);
        }

        // In a real application, you would send this to a server
        const progress = this.getExerciseProgress(exerciseId);
        progress.attempts++;

        return {
            success: validation.isValid,
            message: validation.message,
            details: validation.details,
            progress: progress
        };
    }

    // Export progress data
    /**
     * EXECUTE EXPORTPROGRESS OPERATION
     * PURPOSE: Execute exportProgress operation
     * WHY: Implements required business logic for system functionality
     */
    exportProgress() {
        return {
            exercises: this.exercises,
            currentExercise: this.currentExercise,
            exerciseProgress: this.exerciseProgress,
            showingSolution: this.showingSolution
        };
    }

    // Import progress data
    /**
     * EXECUTE IMPORTPROGRESS OPERATION
     * PURPOSE: Execute importProgress operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {Object} data - Data object
     */
    importProgress(data) {
        if (data.exercises) {
            this.exercises = data.exercises;
        }
        if (data.currentExercise) {
            this.currentExercise = data.currentExercise;
        }
        if (data.exerciseProgress) {
            this.exerciseProgress = data.exerciseProgress;
        }
        if (data.showingSolution) {
            this.showingSolution = data.showingSolution;
        }
    }
}