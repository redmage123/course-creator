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
    getCurrentDirectory() {
        return this.fileSystem.getCurrentDirectory();
    }

    // Get terminal prompt
    getTerminalPrompt() {
        return this.terminal ? this.terminal.getPrompt() : '$ ';
    }

    // Panel management
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

    isPanelVisible(panelName) {
        return this.panelStates[panelName] || false;
    }

    showPanel(panelName) {
        if (panelName in this.panelStates) {
            this.panelStates[panelName] = true;
            this.updatePanelVisibility(panelName);
        }
    }

    hidePanel(panelName) {
        if (panelName in this.panelStates) {
            this.panelStates[panelName] = false;
            this.updatePanelVisibility(panelName);
        }
    }

    // Exercise management
    getExercises() {
        return this.exerciseManager.getExercises();
    }

    setCurrentExercise(exerciseId) {
        const exercise = this.exerciseManager.setCurrentExercise(exerciseId);
        if (exercise) {
            this.dispatchEvent('exercise:selected', { exercise });
        }
        return exercise;
    }

    getCurrentExercise() {
        return this.exerciseManager.getCurrentExercise();
    }

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
    readFile(path) {
        return this.fileSystem.readFile(path);
    }

    writeFile(path, content) {
        const result = this.fileSystem.writeFile(path, content);
        this.dispatchEvent('file:written', { path, size: content.length });
        return result;
    }

    listDirectory(path) {
        return this.fileSystem.listDirectory(path);
    }

    // Language management
    setCurrentLanguage(language) {
        if (this.config.getSupportedLanguages().includes(language)) {
            this.currentLanguage = language;
            this.dispatchEvent('language:changed', { language });
        }
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    // Progress tracking
    getProgressStats() {
        return this.exerciseManager.getProgressStats();
    }

    getSessionDuration() {
        return new Date() - this.labStartTime;
    }

    // State persistence
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
    addEventListener(eventType, handler) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(handler);
    }

    removeEventListener(eventType, handler) {
        if (this.eventListeners.has(eventType)) {
            const handlers = this.eventListeners.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

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
    generateSessionId() {
        return 'lab-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    // Private methods
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

    updatePanelVisibility(panelName) {
        const panelElement = document.getElementById(`${panelName}-panel`);
        if (panelElement) {
            panelElement.style.display = this.panelStates[panelName] ? 'block' : 'none';
        }
    }

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