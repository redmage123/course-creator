/**
 * Lab Controller - Main orchestrator following SOLID principles
 * Single Responsibility: Coordinate all lab modules and manage overall lab state
 * Open/Closed: Extensible through module plugins
 * Liskov Substitution: Uses interface-based modules
 * Interface Segregation: Clean separation of concerns
 * Dependency Inversion: Depends on abstractions
 */
import { LabConfig } from './modules/lab-config.js';
import { VirtualFileSystem } from './modules/file-system.js';
import { TerminalEmulator } from './modules/terminal-emulator.js';
import { ExerciseManager } from './modules/exercise-manager.js';

export class LabController {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        // Initialize configuration
        this.config = new LabConfig();
        
        // Initialize core modules
        this.fileSystem = new VirtualFileSystem(this.config.getSandboxRoot());
        this.exerciseManager = new ExerciseManager(this.config);
        
        // UI state management
        this.panelStates = this.config.getDefaultPanelStates();
        this.currentLanguage = options.defaultLanguage || 'javascript';
        
        // Session management
        this.sessionId = options.sessionId || this.generateSessionId();
        this.studentId = options.studentId || null;
        this.courseId = options.courseId || null;
        this.courseTitle = options.courseTitle || '';
        
        // Performance tracking
        this.labStartTime = new Date();
        this.totalLabTime = 0;
        
        // Initialize terminal after DOM is ready
        this.terminal = null;
        this.isInitialized = false;
        
        // Event listeners storage
        this.eventListeners = new Map();
    }

    // Initialize the lab environment
    /**
     * INITIALIZE  COMPONENT
     * PURPOSE: Initialize  component
     * WHY: Proper initialization ensures component reliability and correct state
     *
     * @param {string|number} terminalElementId - Terminalelementid parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async initialize(terminalElementId = 'terminal-output') {
        try {
            // Get terminal output element
            const terminalElement = document.getElementById(terminalElementId);
            if (!terminalElement) {
                throw new Error(`Terminal element with id '${terminalElementId}' not found`);
            }

            // Initialize terminal emulator
            this.terminal = new TerminalEmulator(
                this.fileSystem,
                this.config,
                terminalElement
            );

            // Load exercises if course ID is provided
            if (this.courseId) {
                await this.loadCourseExercises();
            }

            // Setup UI event handlers
            this.setupEventHandlers();

            // Initialize UI state
            this.updateUI();

            this.isInitialized = true;
            this.dispatchEvent('lab:initialized', { sessionId: this.sessionId });

            return true;
        } catch (error) {
            console.error('Failed to initialize lab:', error);
            throw error;
        }
    }

    // Load exercises for the current course
    /**
     * LOAD COURSE EXERCISES DATA FROM SERVER
     * PURPOSE: Load course exercises data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadCourseExercises() {
        try {
            const exercises = await this.exerciseManager.loadExercises(this.courseId);
            this.dispatchEvent('exercises:loaded', { 
                exercises, 
                count: exercises.length 
            });
            return exercises;
        } catch (error) {
            console.error('Failed to load exercises:', error);
            this.dispatchEvent('exercises:error', { error: error.message });
            throw error;
        }
    }

    // Execute terminal command
    /**
     * EXECUTE EXECUTECOMMAND OPERATION
     * PURPOSE: Execute executeCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} command - Command parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async executeCommand(command) {
        if (!this.terminal) {
            throw new Error('Terminal not initialized');
        }

        const output = await this.terminal.executeCommand(command);
        this.dispatchEvent('terminal:command', { 
            command, 
            output,
            timestamp: new Date()
        });
        
        return output;
    }

    // Get current working directory
    /**
     * RETRIEVE CURRENT DIRECTORY INFORMATION
     * PURPOSE: Retrieve current directory information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentDirectory() {
        return this.fileSystem.getCurrentDirectory();
    }

    // Get terminal prompt
    /**
     * RETRIEVE TERMINAL PROMPT INFORMATION
     * PURPOSE: Retrieve terminal prompt information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getTerminalPrompt() {
        return this.terminal ? this.terminal.getPrompt() : '$ ';
    }

    // Panel management
    /**
     * TOGGLE PANEL STATE
     * PURPOSE: Toggle panel state
     * WHY: Provides binary state management for UI elements
     *
     * @param {*} panelName - Panelname parameter
     */
    togglePanel(panelName) {
        if (panelName in this.panelStates) {
            this.panelStates[panelName] = !this.panelStates[panelName];
            this.updatePanelVisibility(panelName);
            this.dispatchEvent('panel:toggled', { 
                panel: panelName, 
                visible: this.panelStates[panelName] 
            });
        }
    }

    /**
     * EXECUTE ISPANELVISIBLE OPERATION
     * PURPOSE: Execute isPanelVisible operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} panelName - Panelname parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isPanelVisible(panelName) {
        return this.panelStates[panelName] || false;
    }

    /**
     * DISPLAY PANEL INTERFACE
     * PURPOSE: Display panel interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} panelName - Panelname parameter
     */
    showPanel(panelName) {
        if (panelName in this.panelStates) {
            this.panelStates[panelName] = true;
            this.updatePanelVisibility(panelName);
        }
    }

    /**
     * HIDE PANEL INTERFACE
     * PURPOSE: Hide panel interface
     * WHY: Improves UX by managing interface visibility and state
     *
     * @param {*} panelName - Panelname parameter
     */
    hidePanel(panelName) {
        if (panelName in this.panelStates) {
            this.panelStates[panelName] = false;
            this.updatePanelVisibility(panelName);
        }
    }

    // Exercise management
    /**
     * RETRIEVE EXERCISES INFORMATION
     * PURPOSE: Retrieve exercises information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getExercises() {
        return this.exerciseManager.getExercises();
    }

    /**
     * SET CURRENT EXERCISE VALUE
     * PURPOSE: Set current exercise value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {string|number} exerciseId - Exerciseid parameter
     */
    setCurrentExercise(exerciseId) {
        const exercise = this.exerciseManager.setCurrentExercise(exerciseId);
        if (exercise) {
            this.dispatchEvent('exercise:selected', { exercise });
        }
        return exercise;
    }

    /**
     * RETRIEVE CURRENT EXERCISE INFORMATION
     * PURPOSE: Retrieve current exercise information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentExercise() {
        return this.exerciseManager.getCurrentExercise();
    }

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
        const result = await this.exerciseManager.submitSolution(exerciseId, userCode);
        this.dispatchEvent('exercise:submitted', { 
            exerciseId, 
            userCode, 
            result 
        });
        return result;
    }

    // File operations
    /**
     * EXECUTE READFILE OPERATION
     * PURPOSE: Execute readFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    readFile(path) {
        return this.fileSystem.readFile(path);
    }

    /**
     * EXECUTE WRITEFILE OPERATION
     * PURPOSE: Execute writeFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     * @param {*} content - Content parameter
     */
    writeFile(path, content) {
        const result = this.fileSystem.writeFile(path, content);
        this.dispatchEvent('file:written', { path, size: content.length });
        return result;
    }

    /**
     * EXECUTE LISTDIRECTORY OPERATION
     * PURPOSE: Execute listDirectory operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    listDirectory(path) {
        return this.fileSystem.listDirectory(path);
    }

    // Language management
    /**
     * SET CURRENT LANGUAGE VALUE
     * PURPOSE: Set current language value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {*} language - Language parameter
     */
    setCurrentLanguage(language) {
        if (this.config.getSupportedLanguages().includes(language)) {
            this.currentLanguage = language;
            this.dispatchEvent('language:changed', { language });
        }
    }

    /**
     * RETRIEVE CURRENT LANGUAGE INFORMATION
     * PURPOSE: Retrieve current language information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    // Progress tracking
    /**
     * RETRIEVE PROGRESS STATS INFORMATION
     * PURPOSE: Retrieve progress stats information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getProgressStats() {
        return this.exerciseManager.getProgressStats();
    }

    /**
     * RETRIEVE SESSION DURATION INFORMATION
     * PURPOSE: Retrieve session duration information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getSessionDuration() {
        return new Date() - this.labStartTime;
    }

    // State persistence
    /**
     * SAVE STATE TO STORAGE
     * PURPOSE: Save state to storage
     * WHY: Persists user data and application state
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    saveState() {
        const state = {
            sessionId: this.sessionId,
            studentId: this.studentId,
            courseId: this.courseId,
            courseTitle: this.courseTitle,
            currentLanguage: this.currentLanguage,
            panelStates: this.panelStates,
            fileSystemState: this.fileSystem.serialize(),
            exerciseProgress: this.exerciseManager.exportProgress(),
            terminalHistory: this.terminal ? this.terminal.history : [],
            labStartTime: this.labStartTime.toISOString(),
            totalLabTime: this.getSessionDuration()
        };

        localStorage.setItem(`lab-state-${this.sessionId}`, JSON.stringify(state));
        return state;
    }

    /**
     * LOAD STATE DATA FROM SERVER
     * PURPOSE: Load state data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @param {string|number} sessionId - Sessionid parameter
     *
     * @returns {*} Operation result
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    loadState(sessionId = null) {
        const targetSessionId = sessionId || this.sessionId;
        const stateData = localStorage.getItem(`lab-state-${targetSessionId}`);
        
        if (stateData) {
            try {
                const state = JSON.parse(stateData);
                
                // Restore basic properties
                this.studentId = state.studentId;
                this.courseId = state.courseId;
                this.courseTitle = state.courseTitle;
                this.currentLanguage = state.currentLanguage;
                this.panelStates = state.panelStates || this.config.getDefaultPanelStates();
                
                // Restore file system
                if (state.fileSystemState) {
                    this.fileSystem.deserialize(state.fileSystemState);
                }
                
                // Restore exercise progress
                if (state.exerciseProgress) {
                    this.exerciseManager.importProgress(state.exerciseProgress);
                }
                
                // Restore timing
                if (state.labStartTime) {
                    this.labStartTime = new Date(state.labStartTime);
                }
                
                this.dispatchEvent('state:loaded', { sessionId: targetSessionId });
                return true;
            } catch (error) {
                console.error('Failed to load lab state:', error);
                return false;
            }
        }
        
        return false;
    }

    // Event system
    /**
     * EXECUTE ADDEVENTLISTENER OPERATION
     * PURPOSE: Execute addEventListener operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} eventType - Eventtype parameter
     * @param {*} handler - Handler parameter
     */
    addEventListener(eventType, handler) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(handler);
    }

    /**
     * REMOVE EVENT LISTENER FROM SYSTEM
     * PURPOSE: Remove event listener from system
     * WHY: Manages resource cleanup and data consistency
     *
     * @param {*} eventType - Eventtype parameter
     * @param {*} handler - Handler parameter
     */
    removeEventListener(eventType, handler) {
        if (this.eventListeners.has(eventType)) {
            const handlers = this.eventListeners.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * EXECUTE DISPATCHEVENT OPERATION
     * PURPOSE: Execute dispatchEvent operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} eventType - Eventtype parameter
     * @param {Object} data - Data object
     */
    dispatchEvent(eventType, data = {}) {
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).forEach(handler => {
                try {
                    handler({ type: eventType, data, timestamp: new Date() });
                } catch (error) {
                    console.error(`Error in event handler for ${eventType}:`, error);
                }
            });
        }
    }

    // Utility methods
    /**
     * EXECUTE GENERATESESSIONID OPERATION
     * PURPOSE: Execute generateSessionId operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {string|Object} Generated content
     */
    generateSessionId() {
        return 'lab-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    // Private methods
    /**
     * SET EVENT HANDLERS VALUE
     * PURPOSE: Set event handlers value
     * WHY: Maintains data integrity through controlled mutation
     */
    setupEventHandlers() {
        // Auto-save state periodically
        setInterval(() => {
            if (this.isInitialized) {
                this.saveState();
            }
        }, 30000); // Save every 30 seconds

        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
    }

    /**
     * UPDATE PANEL VISIBILITY STATE
     * PURPOSE: Update panel visibility state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} panelName - Panelname parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updatePanelVisibility(panelName) {
        const panelElement = document.getElementById(`${panelName}-panel`);
        if (panelElement) {
            panelElement.style.display = this.panelStates[panelName] ? 'block' : 'none';
        }
    }

    /**
     * UPDATE U I STATE
     * PURPOSE: Update u i state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updateUI() {
        // Update all panel visibility
        Object.keys(this.panelStates).forEach(panelName => {
            this.updatePanelVisibility(panelName);
        });

        // Update language selector
        const languageSelector = document.getElementById('language-selector');
        if (languageSelector) {
            languageSelector.value = this.currentLanguage;
        }

        // Update course title
        const courseTitleElement = document.getElementById('course-title');
        if (courseTitleElement) {
            courseTitleElement.textContent = this.courseTitle;
        }
    }

    // Cleanup
    /**
     * EXECUTE DESTROY OPERATION
     * PURPOSE: Execute destroy operation
     * WHY: Implements required business logic for system functionality
     */
    destroy() {
        // Save final state
        this.saveState();
        
        // Clear event listeners
        this.eventListeners.clear();
        
        // Clear intervals and cleanup
        this.isInitialized = false;
        
        this.dispatchEvent('lab:destroyed', { sessionId: this.sessionId });
    }
}