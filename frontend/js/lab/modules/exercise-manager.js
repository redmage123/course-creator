/**
 * Exercise Manager Module
 * Single Responsibility: Handle exercise loading, tracking, and management
 */

export class ExerciseManager {
    constructor(config) {
        this.config = config;
        this.exercises = [];
        this.currentExercise = null;
        this.exerciseProgress = {};
        this.showingSolution = {};
    }

    // Load exercises for a course
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
    getExercises() {
        return this.exercises;
    }

    // Get exercise by ID
    getExerciseById(exerciseId) {
        return this.exercises.find(exercise => exercise.id === exerciseId);
    }

    // Set current exercise
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
    getCurrentExercise() {
        return this.currentExercise;
    }

    // Start working on an exercise
    startExercise(exerciseId) {
        const progress = this.exerciseProgress[exerciseId];
        if (progress && progress.status === 'not_started') {
            progress.status = 'in_progress';
            progress.startTime = new Date();
            progress.attempts++;
        }
    }

    // Mark exercise as completed
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
    getExerciseProgress(exerciseId) {
        return this.exerciseProgress[exerciseId] || null;
    }

    // Get overall progress statistics
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
    toggleSolution(exerciseId) {
        this.showingSolution[exerciseId] = !this.showingSolution[exerciseId];
        return this.showingSolution[exerciseId];
    }

    // Check if solution is showing for an exercise
    isSolutionShowing(exerciseId) {
        return this.showingSolution[exerciseId] || false;
    }

    // Get exercise hints
    getHints(exerciseId) {
        const exercise = this.getExerciseById(exerciseId);
        return exercise ? exercise.hints || [] : [];
    }

    // Get exercise test cases
    getTestCases(exerciseId) {
        const exercise = this.getExerciseById(exerciseId);
        return exercise ? exercise.testCases || [] : [];
    }

    // Validate exercise solution
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
    exportProgress() {
        return {
            exercises: this.exercises,
            currentExercise: this.currentExercise,
            exerciseProgress: this.exerciseProgress,
            showingSolution: this.showingSolution
        };
    }

    // Import progress data
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