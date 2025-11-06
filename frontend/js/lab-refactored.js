/**
 * Refactored Lab Environment - SOLID Principles Implementation
 * 
 * This replaces the monolithic lab-template.js (1,824 lines) with a modular,
 * maintainable architecture following SOLID principles.
 */
import { LabController } from './lab/lab-controller.js';

// Global lab instance
let labController = null;

// Initialize lab environment
async function initializeLab(options = {}) {
    try {
        // Extract options from URL parameters or provided options
        const urlParams = new URLSearchParams(window.location.search);
        const labOptions = {
            courseId: options.courseId || urlParams.get('courseId') || null,
            studentId: options.studentId || urlParams.get('studentId') || null,
            sessionId: options.sessionId || urlParams.get('sessionId') || null,
            courseTitle: options.courseTitle || urlParams.get('courseTitle') || 'Lab Environment',
            defaultLanguage: options.defaultLanguage || 'javascript'
        };

        // Create lab controller
        labController = new LabController(labOptions);

        // Set up event listeners for UI integration
        setupLabEventHandlers();

        // Initialize the lab
        await labController.initialize('terminal-output');

        // Try to load previous state
        if (labOptions.sessionId) {
            labController.loadState(labOptions.sessionId);
        }

        return labController;

    } catch (error) {
        console.error('Failed to initialize lab environment:', error);
        throw error;
    }
}

// Set up event handlers for UI integration
    /**
     * SET LAB EVENT HANDLERS VALUE
     * PURPOSE: Set lab event handlers value
     * WHY: Maintains data integrity through controlled mutation
     */
function setupLabEventHandlers() {
    if (!labController) return;

    // Exercise management
    labController.addEventListener('exercises:loaded', (event) => {
        updateExercisesList(event.data.exercises);
    });

    labController.addEventListener('exercise:selected', (event) => {
        displayExercise(event.data.exercise);
    });

    labController.addEventListener('exercise:submitted', (event) => {
        handleExerciseSubmission(event.data);
    });

    // Terminal integration
    labController.addEventListener('terminal:command', (event) => {
        displayTerminalOutput(event.data.output, event.data.command);
    });

    // Panel management
    labController.addEventListener('panel:toggled', (event) => {
        updatePanelButton(event.data.panel, event.data.visible);
    });

    // Progress tracking
    labController.addEventListener('state:loaded', () => {
        updateProgressDisplay();
    });
}

// UI Integration Functions
    /**
     * UPDATE EXERCISES LIST STATE
     * PURPOSE: Update exercises list state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} exercises - Exercises parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
function updateExercisesList(exercises) {
    const exercisesList = document.getElementById('exercises-list');
    if (!exercisesList) return;

    exercisesList.innerHTML = '';
    
    exercises.forEach(exercise => {
        const exerciseElement = createExerciseElement(exercise);
        exercisesList.appendChild(exerciseElement);
    });
}

    /**
     * CREATE NEW EXERCISE ELEMENT INSTANCE
     * PURPOSE: Create new exercise element instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} exercise - Exercise parameter
     *
     * @returns {Object} Newly created instance
     *
     * @throws {Error} If operation fails or validation errors occur
     */
function createExerciseElement(exercise) {
    const div = document.createElement('div');
    div.className = 'exercise-item';
    div.dataset.exerciseId = exercise.id;
    
    const progress = labController.exerciseManager.getExerciseProgress(exercise.id);
    const statusClass = progress ? progress.status : 'not_started';
    
    div.innerHTML = `
        <div class="exercise-header">
            <h4>${exercise.title}</h4>
            <span class="exercise-status ${statusClass}">${statusClass.replace('_', ' ')}</span>
        </div>
        <p class="exercise-description">${exercise.description}</p>
        <div class="exercise-meta">
            <span class="difficulty ${exercise.difficulty}">${exercise.difficulty}</span>
            <span class="language">${exercise.language}</span>
        </div>
    `;
    
    div.addEventListener('click', () => {
        selectExercise(exercise.id);
    });
    
    return div;
}

    /**
     * DISPLAY EXERCISE INTERFACE
     * PURPOSE: Display exercise interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} exercise - Exercise parameter
     */
function displayExercise(exercise) {
    const exerciseDetail = document.getElementById('exercise-detail');
    if (!exerciseDetail) return;

    exerciseDetail.innerHTML = `
        <div class="exercise-content">
            <h3>${exercise.title}</h3>
            <div class="exercise-description">${exercise.description}</div>
            <div class="exercise-instructions">${exercise.instructions || ''}</div>
            
            ${exercise.hints ? `
                <div class="exercise-hints">
                    <h4>Hints:</h4>
                    <ul>
                        ${exercise.hints.map(hint => `<li>${hint}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="exercise-actions">
                <button onclick="toggleSolution('${exercise.id}')" class="btn btn-secondary">
                    Toggle Solution
                </button>
                <button onclick="submitCurrentSolution()" class="btn btn-primary">
                    Submit Solution  
                </button>
            </div>
        </div>
    `;
}

    /**
     * DISPLAY TERMINAL OUTPUT INTERFACE
     * PURPOSE: Display terminal output interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} output - Output parameter
     * @param {*} command - Command parameter
     */
function displayTerminalOutput(output, command) {
    const terminalOutput = document.getElementById('terminal-output');
    if (!terminalOutput) return;

    const commandDiv = document.createElement('div');
    commandDiv.className = 'terminal-line';
    
    const prompt = labController.getTerminalPrompt();
    commandDiv.innerHTML = `
        <span class="terminal-prompt">${prompt}</span>
        <span class="terminal-command">${command}</span>
    `;
    
    const outputDiv = document.createElement('div');
    outputDiv.className = 'terminal-output';
    outputDiv.textContent = output;
    
    terminalOutput.appendChild(commandDiv);
    if (output) {
        terminalOutput.appendChild(outputDiv);
    }
    
    // Scroll to bottom
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

    /**
     * UPDATE PANEL BUTTON STATE
     * PURPOSE: Update panel button state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} panelName - Panelname parameter
     * @param {*} visible - Visible parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
function updatePanelButton(panelName, visible) {
    const button = document.getElementById(`toggle-${panelName}`);
    if (button) {
        button.classList.toggle('active', visible);
        button.textContent = visible ? `Hide ${panelName}` : `Show ${panelName}`;
    }
}

    /**
     * UPDATE PROGRESS DISPLAY STATE
     * PURPOSE: Update progress display state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
function updateProgressDisplay() {
    const stats = labController.getProgressStats();
    const progressElement = document.getElementById('progress-stats');
    
    if (progressElement) {
        progressElement.innerHTML = `
            <div class="progress-item">
                <span class="progress-label">Completed:</span>
                <span class="progress-value">${stats.completed}/${stats.total}</span>
            </div>
            <div class="progress-item">
                <span class="progress-label">Progress:</span>
                <span class="progress-value">${stats.completionRate.toFixed(1)}%</span>
            </div>
            <div class="progress-item">
                <span class="progress-label">Time:</span>
                <span class="progress-value">${formatTime(stats.totalTimeSpent)}</span>
            </div>
        `;
    }
}

// Global functions for backward compatibility and HTML onclick handlers
window.initializeLab = initializeLab;

window.selectExercise = function(exerciseId) {
    if (labController) {
        labController.setCurrentExercise(exerciseId);
    }
};

window.togglePanel = function(panelName) {
    if (labController) {
        labController.togglePanel(panelName);
    }
};

window.executeTerminalCommand = async function(command) {
    if (labController) {
        return await labController.executeCommand(command);
    }
};

window.submitCurrentSolution = async function() {
    if (labController) {
        const currentExercise = labController.getCurrentExercise();
        if (currentExercise) {
            const editor = document.getElementById('code-editor');
            const userCode = editor ? editor.value : '';
            return await labController.submitSolution(currentExercise.id, userCode);
        }
    }
};

window.toggleSolution = function(exerciseId) {
    if (labController) {
        const showing = labController.exerciseManager.toggleSolution(exerciseId);
        const solutionElement = document.getElementById(`solution-${exerciseId}`);
        if (solutionElement) {
            solutionElement.style.display = showing ? 'block' : 'none';
        }
    }
};

window.setLanguage = function(language) {
    if (labController) {
        labController.setCurrentLanguage(language);
    }
};

window.saveLabState = function() {
    if (labController) {
        return labController.saveState();
    }
};

window.loadLabState = function(sessionId) {
    if (labController) {
        return labController.loadState(sessionId);
    }
};

// Utility functions
    /**
     * FORMAT TIME FOR DISPLAY
     * PURPOSE: Format time for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} milliseconds - Milliseconds parameter
     *
     * @returns {string} Formatted string
     */
function formatTime(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

    /**
     * HANDLE EXERCISE SUBMISSION EVENT
     * PURPOSE: Handle exercise submission event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {Object} data - Data object
     */
function handleExerciseSubmission(data) {
    const { exerciseId, result } = data;
    
    // Show submission result
    const notification = document.createElement('div');
    notification.className = `notification ${result.success ? 'success' : 'error'}`;
    notification.textContent = result.message;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
    
    // Update progress display
    updateProgressDisplay();
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on a lab page
    if (document.getElementById('terminal-output')) {
        initializeLab().catch(error => {
            console.error('Auto-initialization failed:', error);
        });
    }
});

// Export for module usage
export { initializeLab, LabController };