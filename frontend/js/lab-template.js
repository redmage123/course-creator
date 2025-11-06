/**
 * Lab Environment JavaScript Functions
 *
 * This file contains all interactive functionality for the multi-panel lab environment.
 * It manages four key panels (exercises, code editor, terminal, AI assistant) and provides
 * comprehensive features for hands-on programming education including:
 *
 * - Exercise management and progress tracking
 * - Multi-language code editor with syntax templates
 * - Simulated Linux terminal with sandboxing
 * - AI-powered learning assistant
 * - Real-time student analytics and session persistence
 *
 * The lab supports both open and sandboxed modes for single-student and multi-tenant
 * Docker containers respectively. All student activities are tracked for instructor insights.
 */
// Import CONFIG or use fallback


// Ensure CONFIG is available globally for legacy compatibility
if (typeof window.CONFIG === 'undefined') {
    window.CONFIG = CONFIG;
}

/**
 * @global
 * @type {Array<Object>} exercises - Array of loaded exercise objects for current course
 */
let exercises = [];

/**
 * @global
 * @type {string} courseTitle - Title of the current course
 */
let courseTitle = '';

/**
 * @global
 * @type {string} currentLanguage - Currently selected programming language (javascript/python/java/etc.)
 */
let currentLanguage = 'javascript';

/**
 * @global
 * @type {Array<string>} terminalHistory - Command history for terminal up/down arrow navigation
 */
let terminalHistory = [];

/**
 * @global
 * @type {number} historyIndex - Current position in terminal history (-1 = newest)
 */
let historyIndex = -1;

/**
 * @global
 * @type {string} currentDirectory - Current working directory in simulated terminal
 */
let currentDirectory = '/home/student';

/**
 * @global
 * @type {Object|null} currentExercise - Currently selected exercise object
 */
let currentExercise = null;

/**
 * @global
 * @type {Object} panelStates - Visibility state of all four lab panels
 * @property {boolean} exercises - Whether exercises panel is visible
 * @property {boolean} editor - Whether code editor panel is visible
 * @property {boolean} terminal - Whether terminal panel is visible
 * @property {boolean} assistant - Whether AI assistant panel is visible
 */
let panelStates = {
    exercises: true,
    editor: true,
    terminal: true,
    assistant: true
};

/**
 * @global
 * @type {Object<string, boolean>} showingSolution - Maps exercise IDs to solution visibility state
 */
let showingSolution = {};

/**
 * @global
 * @type {string} sandboxRoot - Root directory for sandboxed file system access (chroot-like restriction)
 */
let sandboxRoot = '/home/student';

/**
 * @global
 * @type {boolean} isLabSandboxed - Whether lab is running in sandboxed security mode
 */
let isLabSandboxed = false;

/**
 * @global
 * @type {string|null} studentId - Unique identifier for current student
 */
let studentId = null;

/**
 * @global
 * @type {string|null} sessionId - Unique identifier for current lab session
 */
let sessionId = null;

/**
 * @global
 * @type {Array<string>} allowedCommands - Whitelist of permitted terminal commands in sandbox mode
 */
let allowedCommands = ['help', 'ls', 'cd', 'pwd', 'cat', 'echo', 'mkdir', 'touch', 'clear', 'whoami', 'date', 'nano', 'vim', 'python', 'node', 'gcc'];

/**
 * @global
 * @type {Array<string>} blockedPaths - System directories that are off-limits in sandbox mode
 */
let blockedPaths = ['/etc', '/root', '/sys', '/proc', '/dev'];

/**
 * @global
 * @type {string|null} courseId - Unique identifier for current course
 */
let courseId = null;

/**
 * @global
 * @type {Object<string, Object>} exerciseProgress - Maps exercise IDs to progress objects with completion status, attempts, and timestamps
 */
let exerciseProgress = {};

/**
 * @global
 * @type {Date|null} labStartTime - Timestamp when current lab session started
 */
let labStartTime = null;

/**
 * @global
 * @type {number} totalLabTime - Cumulative time spent in lab across all sessions (seconds)
 */
let totalLabTime = 0;

/**
 * @global
 * @type {Object} fileSystem - Simulated file system structure for terminal commands
 * @property {Object} /home/student - Student's home directory with example files
 */
const fileSystem = {
    '/home/student': {
        'readme.txt': 'Welcome to the lab environment!\nThis is a simulated file system.',
        'examples': {
            'hello.sh': '#!/bin/bash\necho "Hello from the lab!"',
            'test.py': 'print("Python in the lab!")',
            'sample.js': 'console.log("JavaScript in the lab!");'
        }
    }
};

/**
 * Toggles the visibility of a lab environment panel.
 *
 * This function manages the four-panel lab interface (exercises, editor, terminal, assistant).
 * Toggling panels allows students to focus on specific aspects of their learning environment
 * while maximizing screen real estate. The layout automatically adjusts based on visible panels.
 *
 * @param {string} panelName - The name of the panel to toggle ('exercises', 'editor', 'terminal', or 'assistant')
 * @returns {void}
 *
 * @example
 * // Hide the assistant panel to focus on coding
 * togglePanel('assistant');
 */
function togglePanel(panelName) {
    panelStates[panelName] = !panelStates[panelName];
    updateLayout();
    updateToggleButtons();
}

// Expose to global scope immediately
window.togglePanel = togglePanel;

/**
 * Updates the lab environment's grid layout based on visible panels.
 *
 * This function dynamically adjusts the CSS grid layout to accommodate different panel
 * configurations. It ensures optimal space utilization whether students have all panels
 * visible or choose to hide some for focus. The layout supports 1-4 panel configurations.
 *
 * @returns {void}
 *
 * @example
 * // Called automatically after panel toggles
 * updateLayout();
 */
function updateLayout() {

    const mainLayout = document.querySelector('.main-layout');
    if (!mainLayout) {
        console.error('Main layout not found!');
        return;
    }

    // Reset all layout classes
    mainLayout.className = 'main-layout';

    // Get visible panels
    const visiblePanels = Object.keys(panelStates).filter(panel => panelStates[panel]);

    // Update panel visibility
    const exercisePanel = document.getElementById('exercisePanel');
    const editorPanel = document.getElementById('editorPanel');
    const terminalPanel = document.getElementById('terminalPanel');
    const assistantPanel = document.getElementById('assistantPanel');


    if (exercisePanel) {
        exercisePanel.classList.toggle('panel-hidden', !panelStates.exercises);
    }
    if (editorPanel) editorPanel.classList.toggle('panel-hidden', !panelStates.editor);
    if (terminalPanel) terminalPanel.classList.toggle('panel-hidden', !panelStates.terminal);
    if (assistantPanel) assistantPanel.classList.toggle('panel-hidden', !panelStates.assistant);

    // Apply appropriate grid layout based on visible panels
    if (visiblePanels.length === 4) {
        mainLayout.style.gridTemplateColumns = '300px 1fr 300px';
        mainLayout.style.gridTemplateRows = '1fr 300px';
    } else if (visiblePanels.length === 3) {
        if (!panelStates.terminal) {
            mainLayout.style.gridTemplateColumns = '300px 1fr 300px';
            mainLayout.style.gridTemplateRows = '1fr';
        } else {
            mainLayout.style.gridTemplateColumns = '300px 1fr';
            mainLayout.style.gridTemplateRows = '1fr 300px';
        }
    } else if (visiblePanels.length === 2) {
        mainLayout.style.gridTemplateColumns = '300px 1fr';
        mainLayout.style.gridTemplateRows = '1fr';
    } else {
        mainLayout.style.gridTemplateColumns = '1fr';
        mainLayout.style.gridTemplateRows = '1fr';
    }
}

/**
 * Updates the visual state of panel toggle buttons.
 *
 * This function synchronizes toggle button states with actual panel visibility.
 * Active buttons are highlighted, inactive ones are dimmed. This provides visual
 * feedback to students about which panels are currently visible in the lab environment.
 *
 * @returns {void}
 */
function updateToggleButtons() {
    const buttons = {
        exercises: document.getElementById('toggleExercises'),
        editor: document.getElementById('toggleEditor'),
        terminal: document.getElementById('toggleTerminal'),
        assistant: document.getElementById('toggleAssistant')
    };


    Object.keys(buttons).forEach(panel => {
        const button = buttons[panel];
        if (button) {
            button.classList.toggle('inactive', !panelStates[panel]);
        }
    });
}

/**
 * Initializes the complete lab environment for student learning.
 *
 * This is the main initialization function that sets up the entire lab interface including:
 * - Sandbox security restrictions (if enabled)
 * - Student session and progress tracking
 * - Course-specific exercises
 * - Programming language configuration
 * - All four panels (exercises, editor, terminal, AI assistant)
 *
 * The function supports both sandboxed (restricted) and open lab environments.
 * Sandboxed labs enforce security constraints for multi-student Docker containers.
 *
 * @async
 * @returns {Promise<void>}
 *
 * @example
 * // Called on page load
 * await initializeLab();
 */
async function initializeLab() {

    // Check if this is a sandboxed environment
    const urlParams = new URLSearchParams(window.location.search);
    isLabSandboxed = urlParams.get('sandboxed') === 'true';
    studentId = urlParams.get('studentId');
    sessionId = urlParams.get('sessionId');
    courseId = urlParams.get('courseId') || window.currentCourseId || 'default';
    courseTitle = urlParams.get('course') || window.currentCourseName || 'Programming Course';

    // Get language from URL parameter and set it
    const urlLanguage = urlParams.get('language');
    if (urlLanguage) {
        currentLanguage = urlLanguage;
    }


    // Initialize progress tracking
    initializeProgressTracking();

    if (isLabSandboxed) {
        initializeSandbox();
    }

    await loadExercises();
    updateLayout();

    // Set the language dropdown to match the current language
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect && currentLanguage) {
        languageSelect.value = currentLanguage;
    }

    const welcomeMessage = isLabSandboxed
        ? `Welcome to your secure lab environment! Session ID: ${sessionId || 'Unknown'}
You are in a sandboxed terminal with restricted access for security.`
        : 'Welcome! Toggle panels using the controls above, select exercises, or ask me anything!';

    addMessage(welcomeMessage, 'system');
}

/**
 * Initializes student progress tracking for the lab session.
 *
 * Sets up automatic progress saving every 30 seconds and before page unload.
 * Progress includes exercise completion status, time spent, code attempts, and
 * overall session duration. This enables students to resume where they left off
 * and allows instructors to monitor student engagement and struggles.
 *
 * @returns {void}
 */
function initializeProgressTracking() {
    labStartTime = new Date();

    // Load existing progress for this student and course
    if (studentId && courseId) {
        loadStudentProgress();
    }

    // Set up automatic progress saving
    setInterval(saveProgressToServer, 30000); // Save every 30 seconds

    // Save progress when the page is about to unload
    window.addEventListener('beforeunload', function() {
        saveProgressToServer();
    });

}

/**
 * Initializes the sandboxed lab environment with security restrictions.
 *
 * Sandboxing is critical for multi-tenant Docker containers where multiple students
 * share the same environment. This function restricts file system access to the
 * student's home directory, adds security notices, and logs all command executions.
 * Prevents students from accessing system files or other students' work.
 *
 * @returns {void}
 */
function initializeSandbox() {
    // Set up sandbox restrictions

    // Restrict file system access to sandbox root
    const restrictedFS = {};
    restrictedFS[sandboxRoot] = fileSystem[sandboxRoot];

    // Add sandbox-specific files
    if (!restrictedFS[sandboxRoot]['.sandbox_info']) {
        restrictedFS[sandboxRoot]['.sandbox_info'] = `Sandbox Environment
Student ID: ${studentId}
Session ID: ${sessionId}
Restricted to: ${sandboxRoot}
`;
    }

    // Add security notice
    if (!restrictedFS[sandboxRoot]['security_notice.txt']) {
        restrictedFS[sandboxRoot]['security_notice.txt'] =
            'SECURITY NOTICE:\n' +
            '================\n' +
            'This is a sandboxed environment for educational purposes.\n' +
            'You have restricted access to system commands and files.\n' +
            'All activities are logged for security and assessment purposes.\n' +
            'Do not attempt to bypass security restrictions.\n';
    }

    // Update file system to restricted version
    Object.keys(fileSystem).forEach(key => {
        if (!key.startsWith(sandboxRoot)) {
            delete fileSystem[key];
        }
    });

}

/**
 * Loads course-specific exercises from the backend API.
 *
 * This function fetches exercises tailored to the current course. If no exercises
 * exist for the course, it triggers on-demand generation using the course syllabus
 * and AI. Exercises include starter code, solutions, hints, and evaluation criteria.
 * The function gracefully handles API failures and displays exercises after loading.
 *
 * @async
 * @returns {Promise<void>}
 *
 * @example
 * // Called during lab initialization
 * await loadExercises();
 */
async function loadExercises() {

    try {
        const response = await fetch(`${window.CONFIG?.ENDPOINTS.EXERCISES(courseId)}`);

        if (response.ok) {
            const data = await response.json();
            exercises = data.exercises || [];

            // If no exercises found, try to generate them
            if (exercises.length === 0) {
                await generateExercisesOnDemand();
            }
        } else {
            await generateExercisesOnDemand();
        }
    } catch (error) {
        console.error('Error loading exercises:', error);
        exercises = [];
    }


    // Force display with a delay to ensure DOM is ready
    setTimeout(() => {
        displayExercises();
    }, 100);
}

/**
 * Generates lab exercises on-demand using the course syllabus and AI.
 *
 * When no pre-existing exercises are found for a course, this function uses the
 * course syllabus to generate appropriate exercises via the lab management service.
 * The AI analyzes the syllabus content, difficulty level, and learning objectives
 * to create tailored coding exercises with starter code, solutions, and hints.
 *
 * @async
 * @returns {Promise<void>}
 */
async function generateExercisesOnDemand() {

    try {
        // First try to get the syllabus for this course
        const syllabusResponse = await fetch(`${window.CONFIG?.ENDPOINTS.SYLLABUS(courseId)}`);

        if (syllabusResponse.ok) {
            const syllabusData = await syllabusResponse.json();

            // Use the lab refresh endpoint to generate exercises from syllabus
            const generateResponse = await fetch(`${window.CONFIG?.ENDPOINTS.REFRESH_LAB_EXERCISES}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: courseId
                })
            });

            if (generateResponse.ok) {
                const result = await generateResponse.json();
                exercises = result.exercises || [];
            } else {
                exercises = [];
            }
        } else {

            // Cannot generate proper exercises without syllabus
            exercises = [];
        }
    } catch (error) {
        console.error('Error generating exercises on-demand:', error);
        exercises = [];
    }
}

/**
 * Loads generic fallback exercises when course-specific exercises cannot be loaded.
 *
 * This function provides a safety net when both the API and on-demand generation fail.
 * It returns basic exercises tailored to the course topic (Linux, Python, etc.) based
 * on the course title. While not ideal, this ensures students always have something
 * to practice even if the backend is unavailable.
 *
 * @async
 * @returns {Promise<Array<Object>>} Array of fallback exercise objects
 */
async function loadFallbackExercises() {

    // Generate course-appropriate exercises based on course title/topic
    if (courseTitle && courseTitle.toLowerCase().includes('linux')) {
        return [
            {
                id: 1,
                title: "Basic Linux Commands",
                description: "Practice fundamental Linux commands like ls, cd, pwd, and mkdir.",
                difficulty: "easy",
                starterCode: "# Basic Linux Commands Practice\
# 1. List files in current directory\
# 2. Create a new directory\
# 3. Navigate to different directories\
# 4. Check current working directory\
\
# Your commands here:",
                solution: "ls -la\
mkdir test_directory\
cd test_directory\
pwd\
cd ..\
rmdir test_directory"
            },
            {
                id: 2,
                title: "File Permissions",
                description: "Learn to manage file permissions using chmod and understand permission modes.",
                difficulty: "medium",
                starterCode: "# File Permissions Exercise\
# 1. Create a file\
# 2. Check its permissions\
# 3. Change permissions\
# 4. Verify changes\
\
# Your commands here:",
                solution: "touch myfile.txt\
ls -l myfile.txt\
chmod 755 myfile.txt\
ls -l myfile.txt\
chmod u+x,g-w,o-r myfile.txt\
ls -l myfile.txt"
            }
        ];
    } else if (courseTitle && courseTitle.toLowerCase().includes('python')) {
        return [
            {
                id: 1,
                title: "Python Variables and Types",
                description: "Practice with Python variables, data types, and basic operations.",
                difficulty: "easy",
                starterCode: "# Python Variables and Types\
# 1. Create variables of different types\
# 2. Perform operations\
# 3. Print results\
\
# Your code here:",
                solution: "name = 'Python Student'\
age = 25\
is_learning = True\
height = 5.8\
\
print(f'Name: {name}')\
print(f'Age: {age}')\
print(f'Learning: {is_learning}')\
print(f'Height: {height}ft')"
            },
            {
                id: 2,
                title: "Python Functions",
                description: "Create and use functions with parameters and return values.",
                difficulty: "medium",
                starterCode: "# Python Functions Exercise\
# 1. Define a function with parameters\
# 2. Use return values\
# 3. Call the function\
\
# Your code here:",
                solution: "def calculate_area(length, width):\
    return length * width\
\
def greet_user(name):\
    return f'Hello, {name}!'\
\
# Test the functions\
area = calculate_area(10, 5)\
greeting = greet_user('Python Student')\
\
print(f'Area: {area}')\
print(greeting)"
            }
        ];
    } else {
        // Generic programming exercises
        return [
            {
                id: 1,
                title: "Getting Started",
                description: "Basic programming concepts and syntax for this course.",
                difficulty: "easy",
                starterCode: "// Getting Started Exercise\
// Follow the instructions provided by your instructor\
\
// Your code here:",
                solution: "// Solution will be provided by instructor"
            }
        ];
    }
    
    displayExercises();
}

/**
 * Displays the list of exercises in the exercises sidebar panel.
 *
 * This function renders all loaded exercises as clickable items with titles, descriptions,
 * difficulty badges, and solution toggle buttons. Each exercise can be selected to load
 * its starter code into the editor. The function ensures the exercises panel is visible
 * and provides a helpful message if no exercises are available.
 *
 * @returns {void}
 */
function displayExercises() {

    const exerciseList = document.getElementById('exerciseList');
    if (!exerciseList) {
        console.error('Exercise list element not found!');
        return;
    }


    // Ensure the exercises panel is visible
    const exercisePanel = document.getElementById('exercisePanel');
    if (exercisePanel) {
        exercisePanel.classList.remove('panel-hidden');
        panelStates.exercises = true;
    } else {
        console.error('Exercise panel not found!');
    }

    if (exercises.length === 0) {
        exerciseList.innerHTML = '<div class="no-exercises">No exercises available. Try refreshing the exercises.</div>';
    } else {
        exerciseList.innerHTML = exercises.map(exercise => `
            <div class="exercise-item" onclick="selectExercise('${exercise.id}')">
                <h4>${exercise.title}</h4>
                <p>${exercise.description}</p>
                <span class="exercise-difficulty difficulty-${exercise.difficulty}">${exercise.difficulty.toUpperCase()}</span>
                <div class="exercise-controls">
                    <button class="solution-toggle-btn" onclick="event.stopPropagation(); toggleSolution('${exercise.id}')" id="solutionBtn${exercise.id}">
                        👁️ Show Solution
                    </button>
                </div>
            </div>
        `).join('');

    }

    // Update the toggle button state
    const toggleButton = document.getElementById('toggleExercises');
    if (toggleButton) {
        toggleButton.classList.add('active');
    }

    // Force layout update
    updateLayout();
}

/**
 * Selects and loads an exercise into the lab environment.
 *
 * This function is triggered when a student clicks on an exercise. It loads the starter
 * code into the editor, displays a modal with instructions/hints/objectives, updates
 * the AI assistant's context, and begins tracking progress for analytics. The selected
 * exercise is highlighted in the sidebar and the terminal is notified.
 *
 * @param {string|number} exerciseId - The unique identifier of the exercise to select
 * @returns {void}
 *
 * @example
 * // Select exercise when student clicks on it
 * selectExercise('exercise-123');
 */
function selectExercise(exerciseId) {

    // Track exercise selection for progress
    trackExerciseStart(exerciseId);

    currentExercise = exercises.find(ex => ex.id === exerciseId);
    if (!currentExercise) {
        console.error('Exercise not found:', exerciseId);
        return;
    }

    // Update UI
    document.querySelectorAll('.exercise-item').forEach(item => item.classList.remove('active'));
    const exerciseItem = document.querySelector(`[onclick="selectExercise('${exerciseId}')"]`);
    if (exerciseItem) {
        exerciseItem.classList.add('active');
    }

    // Load exercise code (always start with starter code)
    const editor = document.getElementById('codeEditor');
    if (editor) {
        const starterCode = currentExercise.starterCode || currentExercise.starter_code || '// Write your code here\n';
        editor.value = starterCode.replace(/\\n/g, '\n');
        // Reset solution toggle state
        showingSolution[exerciseId] = false;
        const button = document.getElementById('solutionBtn' + exerciseId);
        if (button) {
            button.textContent = '👁️ Show Solution';
            button.classList.remove('active');
        }
    }

    // Update terminal with exercise info
    addToTerminal(`Exercise loaded: ${currentExercise.title}
Run your code to see the output.`, 'output');

    // Show lab notes popup instead of auto-messaging AI
    showLabNotesModal(currentExercise);

    // Update AI assistant context (but don't auto-send message)
    updateAIAssistantContext(currentExercise);
}

/**
 * Displays a modal dialog with detailed lab instructions and exercise information.
 *
 * When students select an exercise, this modal provides comprehensive guidance including:
 * - Learning objectives and purpose
 * - Step-by-step instructions
 * - Hints and tips
 * - Expected output and evaluation criteria
 * - Formulas and references
 * The modal helps students understand requirements before diving into coding.
 *
 * @param {Object} exercise - The exercise object containing all metadata
 * @param {string} exercise.title - Exercise title
 * @param {string} exercise.description - Exercise description
 * @param {string} exercise.difficulty - Difficulty level (beginner/intermediate/advanced)
 * @param {Array<string>} [exercise.instructions] - Step-by-step instructions
 * @param {Array<string>} [exercise.hints] - Helpful hints
 * @param {string} [exercise.expected_output] - Expected output example
 * @returns {void}
 *
 * @example
 * // Called automatically when exercise is selected
 * showLabNotesModal(currentExercise);
 */
function showLabNotesModal(exercise) {

    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalContent.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 8px;
        max-width: 80%;
        max-height: 80%;
        overflow-y: auto;
        position: relative;
    `;
    
    // Create lab notes content
    const labNotesHTML = `
        <div class="lab-notes-header">
            <h2>🧪 Lab Instructions: ${exercise.title}</h2>
            <button class="close-btn" onclick="this.closest('.modal-overlay').remove()" style="
                position: absolute;
                top: 10px;
                right: 15px;
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
            ">×</button>
        </div>
        <div class="lab-notes-content">
            <div class="exercise-meta">
                <span class="difficulty-badge difficulty-${exercise.difficulty}">${exercise.difficulty.toUpperCase()}</span>
                <span class="exercise-type">${exercise.type || 'Programming Exercise'}</span>
                <span class="estimated-time">${exercise.estimated_time || '30-45 minutes'}</span>
            </div>
            
            <div class="exercise-description">
                <h3>📝 Description</h3>
                <p>${exercise.description}</p>
            </div>
            
            ${exercise.purpose ? `
                <div class="exercise-purpose">
                    <h3>🎯 Learning Objectives</h3>
                    <p>${exercise.purpose}</p>
                </div>
            ` : ''}
            
            ${exercise.instructions && exercise.instructions.length > 0 ? `
                <div class="exercise-instructions">
                    <h3>📋 Instructions</h3>
                    <ol>
                        ${exercise.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                    </ol>
                </div>
            ` : ''}
            
            ${exercise.hints && exercise.hints.length > 0 ? `
                <div class="exercise-hints">
                    <h3>💡 Hints</h3>
                    <ul>
                        ${exercise.hints.map(hint => `<li>${hint}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${exercise.formulas && exercise.formulas.length > 0 ? `
                <div class="exercise-formulas">
                    <h3>📐 Formulas & References</h3>
                    <div class="formulas-list">
                        ${exercise.formulas.map(formula => `<div class="formula-item"><code>${formula}</code></div>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${exercise.expected_output ? `
                <div class="exercise-expected">
                    <h3>✅ Expected Output</h3>
                    <pre>${exercise.expected_output}</pre>
                </div>
            ` : ''}
            
            ${exercise.evaluation_criteria && exercise.evaluation_criteria.length > 0 ? `
                <div class="exercise-evaluation">
                    <h3>📊 Evaluation Criteria</h3>
                    <ul>
                        ${exercise.evaluation_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
        <div class="lab-notes-footer">
            <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove(); focusCodeEditor();">
                Start Coding
            </button>
            <button class="btn btn-secondary" onclick="askAIForHelp('${exercise.id}')">
                Ask AI for Help
            </button>
        </div>
    `;
    
    modalContent.innerHTML = labNotesHTML;
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Add styles for the modal
    const style = document.createElement('style');
    style.textContent = `
        .lab-notes-header h2 {
            margin-top: 0;
            color: #333;
        }
        .exercise-meta {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .difficulty-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .difficulty-beginner { background: #d4edda; color: #155724; }
        .difficulty-intermediate { background: #fff3cd; color: #856404; }
        .difficulty-advanced { background: #f8d7da; color: #721c24; }
        .exercise-type, .estimated-time {
            padding: 4px 8px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 12px;
        }
        .lab-notes-content h3 {
            color: #495057;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .lab-notes-content pre {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }
        .lab-notes-footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn:hover {
            opacity: 0.9;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Updates the AI assistant's context with current exercise information.
 *
 * This function enables context-aware AI assistance by providing the AI with details
 * about the student's current exercise. The AI can then give targeted help, explain
 * concepts related to the exercise, provide relevant hints, and debug code in the
 * context of the specific learning objectives. A visual context indicator is shown.
 *
 * @param {Object} exercise - The exercise object to set as context
 * @param {string|number} exercise.id - Exercise unique identifier
 * @param {string} exercise.title - Exercise title
 * @param {string} exercise.description - Exercise description
 * @param {string} exercise.difficulty - Difficulty level
 * @param {Array<string>} [exercise.topics_covered] - Topics covered in exercise
 * @returns {void}
 */
function updateAIAssistantContext(exercise) {

    // Store current exercise context for AI
    window.currentExerciseContext = {
        id: exercise.id,
        title: exercise.title,
        description: exercise.description,
        difficulty: exercise.difficulty,
        type: exercise.type,
        topics: exercise.topics_covered || [],
        instructions: exercise.instructions || [],
        hints: exercise.hints || [],
        courseId: courseId,
        courseTitle: courseTitle
    };
    
    // Update AI assistant display to show context
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        // Add a subtle context indicator
        const contextIndicator = document.createElement('div');
        contextIndicator.className = 'ai-context-indicator';
        contextIndicator.style.cssText = `
            padding: 8px 12px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            margin-bottom: 10px;
            font-size: 12px;
            color: #1976d2;
        `;
        contextIndicator.innerHTML = `
            <strong>Current Lab:</strong> ${exercise.title} (${exercise.difficulty})
        `;
        
        // Remove any existing context indicators
        const existingIndicators = chatContainer.querySelectorAll('.ai-context-indicator');
        existingIndicators.forEach(indicator => indicator.remove());
        
        // Add new context indicator at the top
        chatContainer.insertBefore(contextIndicator, chatContainer.firstChild);
    }
}

/**
 * Focuses the code editor for immediate typing.
 *
 * Helper function to programmatically focus the code editor textarea, typically
 * called after closing the lab instructions modal so students can start coding
 * immediately without needing to manually click the editor.
 *
 * @returns {void}
 */
function focusCodeEditor() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        editor.focus();
    }
}

/**
 * Initiates an AI help request for a specific exercise.
 *
 * Called when students click "Ask AI for Help" in the lab instructions modal.
 * Closes the modal, sends a contextual message to the AI assistant with exercise
 * details, and displays an initial helpful response with hints. This provides
 * students with immediate, exercise-specific guidance from the AI tutor.
 *
 * @param {string|number} exerciseId - The ID of the exercise needing help
 * @returns {void}
 *
 * @example
 * // Student clicks "Ask AI for Help" button
 * askAIForHelp('exercise-123');
 */
function askAIForHelp(exerciseId) {
    const exercise = exercises.find(ex => ex.id === exerciseId);
    if (!exercise) return;

    // Close modal first
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();

    // Send contextual message to AI
    const contextMessage = `I need help with the current lab exercise: "${exercise.title}". This is a ${exercise.difficulty} level exercise in ${courseTitle}. Can you provide guidance?`;

    addMessage(contextMessage, 'user');

    // Simulate AI response with context
    setTimeout(() => {
        let aiResponse = `I'd be happy to help you with **${exercise.title}**! This is a *${exercise.difficulty}* level exercise.\n\nLet me provide some guidance:\n\n${exercise.hints && exercise.hints.length > 0 ?
    `Here are some hints to get you started:\n• ${exercise.hints.join('\n• ')}\n\n` :
    'Feel free to ask specific questions about the requirements or share your code if you need help debugging.\n\n'}What specific part would you like help with?`;

        addMessage(aiResponse, 'assistant');
    }, 1000);
}

// Expose to global scope immediately
window.selectExercise = selectExercise;
window.showLabNotesModal = showLabNotesModal;
window.updateAIAssistantContext = updateAIAssistantContext;
window.focusCodeEditor = focusCodeEditor;
window.askAIForHelp = askAIForHelp;

/**
 * Toggles between showing the exercise solution and starter code in the editor.
 *
 * Students can reveal solutions to understand correct approaches or verify their work.
 * The function swaps between starter code and solution code, updates the button text,
 * and notifies the terminal. This supports self-directed learning by allowing students
 * to compare their attempts with model solutions.
 *
 * @param {string|number} exerciseId - The ID of the exercise to toggle solution for
 * @returns {void}
 *
 * @example
 * // Student clicks "Show Solution" button
 * toggleSolution('exercise-123');
 */
function toggleSolution(exerciseId) {
    const exercise = exercises.find(ex => ex.id === exerciseId);
    if (!exercise) return;

    const editor = document.getElementById('codeEditor');
    const button = document.getElementById('solutionBtn' + exerciseId);

    if (!editor || !button) return;

    if (showingSolution[exerciseId]) {
        // Hide solution - show starter code
        const starterCode = exercise.starterCode || exercise.starter_code || '// Write your code here\n';
        editor.value = starterCode.replace(/\\n/g, '\n');
        button.textContent = '👁️ Show Solution';
        button.classList.remove('active');
        showingSolution[exerciseId] = false;
        addToTerminal('Switched back to starter code', 'output');
    } else {
        // Show solution
        const solution = exercise.solution || exercise.expected_output || '// Solution not available
';
        editor.value = solution.replace(/\
/g, '
');
        button.textContent = '🚫 Hide Solution';
        button.classList.add('active');
        showingSolution[exerciseId] = true;
        addToTerminal('Showing solution code', 'output');
    }
}

// Expose to global scope immediately
window.toggleSolution = toggleSolution;

/**
 * Changes the programming language for the code editor and exercises.
 *
 * Students can switch between multiple programming languages (JavaScript, Python, Java,
 * C++, C, Go, Rust, Shell, HTML, CSS). The function updates the current language,
 * loads appropriate starter code templates, and notifies the AI assistant of the change.
 * Exercise code is preserved if showing solution, otherwise default template is loaded.
 *
 * @returns {void}
 *
 * @example
 * // Called when student selects different language from dropdown
 * changeLanguage();
 */
function changeLanguage() {
    const select = document.getElementById('languageSelect');
    currentLanguage = select.value;
    
    const editor = document.getElementById('codeEditor');
    if (editor) {
        // Set appropriate starter code for the language
        if (currentExercise) {
            // If showing solution, keep showing solution, otherwise show starter code
            if (showingSolution[currentExercise.id]) {
                editor.value = currentExercise.solution.replace(/\
/g, '
');
            } else {
                editor.value = currentExercise.starterCode.replace(/\
/g, '
');
            }
        } else {
            // Default starter code for each language
            if (currentLanguage === 'python') {
                editor.value = '# Python code
print("Hello, World!")';
            } else if (currentLanguage === 'shell') {
                editor.value = '#!/bin/bash
# Bash script
echo "Hello, World!"';
            } else if (currentLanguage === 'html') {
                editor.value = '<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
</body>
</html>';
            } else if (currentLanguage === 'css') {
                editor.value = '/* CSS Styles */
body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
}

h1 {
    color: #333;
}';
            } else if (currentLanguage === 'java') {
                editor.value = '// Java code
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}';
            } else if (currentLanguage === 'cpp') {
                editor.value = '// C++ code
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}';
            } else if (currentLanguage === 'c') {
                editor.value = '// C code
#include <stdio.h>

int main() {
    printf("Hello, World!\
");
    return 0;
}';
            } else if (currentLanguage === 'go') {
                editor.value = '// Go code
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}';
            } else if (currentLanguage === 'rust') {
                editor.value = '// Rust code
fn main() {
    println!("Hello, World!");
}';
            } else if (currentLanguage === 'javascript') {
                editor.value = '// JavaScript code
console.log("Hello, World!");';
            } else {
                editor.value = '// Code
console.log("Hello, World!");';
            }
        }
    }
    
    addMessage(`Switched to ${currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1)}. Ready to code!`, 'assistant');
}

// Expose to global scope immediately
window.changeLanguage = changeLanguage;

/**
 * Adds a styled line of text to the terminal output.
 *
 * Helper function for displaying messages in the simulated terminal with color coding:
 * - Normal messages (white)
 * - Output messages (light green)
 * - Error messages (light red)
 * Automatically scrolls terminal to show the newest message. Used by code execution,
 * command simulation, and system notifications.
 *
 * @param {string} text - The text to display in the terminal
 * @param {string} [type='normal'] - The message type ('normal', 'output', or 'error')
 * @returns {void}
 *
 * @example
 * // Show successful code execution
 * addToTerminal('Code executed successfully', 'output');
 *
 * @example
 * // Show error message
 * addToTerminal('SyntaxError: Unexpected token', 'error');
 */
function addToTerminal(text, type = 'normal') {
    const terminalContent = document.getElementById('terminalContent');
    if (!terminalContent) return;

    const div = document.createElement('div');
    div.className = 'terminal-line';
    if (type === 'output') {
        div.style.color = '#ccffcc';
    } else if (type === 'error') {
        div.style.color = '#ffcccc';
    }
    div.textContent = text;

    terminalContent.appendChild(div);

    // Auto-scroll terminal
    const terminalWindow = document.getElementById('terminalWindow');
    if (terminalWindow) {
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }
}

/**
 * Executes the code from the editor in the lab environment.
 *
 * This is the primary function for running student code. For JavaScript, it uses eval()
 * with console.log capture to display output. For other languages, it shows a simulation
 * message (actual execution requires backend processing). The function:
 * - Validates code exists
 * - Tracks execution attempts for analytics
 * - Displays output in terminal
 * - Checks for exercise completion
 * - Provides AI assistance on errors
 *
 * @returns {void}
 *
 * @example
 * // Student clicks "Run Code" button
 * runCode();
 */
function runCode() {
    const editor = document.getElementById('codeEditor');

    if (!editor) {
        addMessage('Code editor not available. Enable it using the panel controls above.', 'assistant');
        return;
    }

    const code = editor.value;

    if (!code.trim()) {
        addToTerminal('Please write some code first!', 'error');
        return;
    }

    // Track code execution for progress
    if (currentExercise) {
        trackCodeExecution(currentExercise.id, code);
    }

    addToTerminal('> Running code...', 'normal');
    
    try {
        if (currentLanguage === 'javascript') {
            // JavaScript execution
            let logs = [];
            const originalLog = console.log;
            console.log = function(...args) {
                logs.push(args.join(' '));
                originalLog.apply(console, arguments);
            };
            
            // Execute the code
            eval(code);
            
            // Restore console.log
            console.log = originalLog;
            
            // Show output
            if (logs.length > 0) {
                addToTerminal(logs.join('
'), 'output');
            } else {
                addToTerminal('Code executed successfully (no console output)', 'output');
            }
        } else {
            // For other languages, show simulation message
            addToTerminal(`${currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1)} code simulation:`, 'output');
            addToTerminal(code, 'output');
            addToTerminal('(Note: Actual execution requires server-side processing)', 'output');
        }
        
        // Check for exercise completion
        if (currentExercise) {
            checkForExerciseCompletion(currentExercise.id, code);
        }
        
        // Add success message to chat
        addMessage('Great! Your code ran successfully. Check the terminal for the output!', 'assistant');
        
    } catch (error) {
        addToTerminal('Error: ' + error.message, 'error');
        
        // Add error help to chat
        addMessage(`I see there's an error: "${error.message}". Would you like me to help you fix it?`, 'assistant');
    }
}

// Expose to global scope immediately
window.runCode = runCode;

/**
 * Clears the code editor and resets to appropriate starter code.
 *
 * If an exercise is selected, returns to that exercise's starter code. Otherwise,
 * loads a language-specific "Hello, World!" template. This allows students to
 * start fresh when they want to retry an exercise or clear experimental code.
 * Provides visual confirmation in the terminal.
 *
 * @returns {void}
 *
 * @example
 * // Student clicks "Clear Code" button
 * clearCode();
 */
function clearCode() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        if (currentExercise) {
            editor.value = currentExercise.starterCode.replace(/\
/g, '
');
        } else {
            if (currentLanguage === 'python') {
                editor.value = '# Write your Python code here...
print("Hello, World!")';
            } else if (currentLanguage === 'shell') {
                editor.value = '#!/bin/bash
# Write your bash script here...
echo "Hello, World!"';
            } else if (currentLanguage === 'java') {
                editor.value = '// Write your Java code here...
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}';
            } else if (currentLanguage === 'cpp') {
                editor.value = '// Write your C++ code here...
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}';
            } else if (currentLanguage === 'c') {
                editor.value = '// Write your C code here...
#include <stdio.h>

int main() {
    printf("Hello, World!\
");
    return 0;
}';
            } else if (currentLanguage === 'go') {
                editor.value = '// Write your Go code here...
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}';
            } else if (currentLanguage === 'rust') {
                editor.value = '// Write your Rust code here...
fn main() {
    println!("Hello, World!");
}';
            } else if (currentLanguage === 'javascript') {
                editor.value = '// JavaScript code
console.log("Hello, World!");';
            } else {
                editor.value = '// Code
console.log("Hello, World!");';
            }
        }
    }
    addToTerminal('Code cleared. Ready to start fresh!', 'output');
}

// Expose to global scope immediately
window.clearCode = clearCode;

/**
 * Adds a message to the AI assistant chat interface.
 *
 * Displays messages from users, the AI assistant, or system notifications. Assistant
 * messages are formatted with markdown support (bold, italic, code blocks, lists).
 * Messages are styled based on type and automatically scroll to remain visible.
 * This enables conversational AI interaction throughout the lab experience.
 *
 * @param {string} message - The message text to display
 * @param {string} type - Message type ('user', 'assistant', or 'system')
 * @param {string} [extraClass=''] - Additional CSS class for special styling (e.g., 'loading')
 * @returns {void}
 *
 * @example
 * // Student sends a message
 * addMessage('How do I loop through an array?', 'user');
 *
 * @example
 * // AI responds
 * addMessage('You can use a for loop or forEach method...', 'assistant');
 */
function addMessage(message, type, extraClass = '') {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message ${extraClass}`;

    // Format the message content for better readability
    if (type === 'assistant') {
        messageDiv.innerHTML = formatAssistantMessage(message);
    } else {
        messageDiv.textContent = message;
    }

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Formats AI assistant messages with markdown-style rendering.
 *
 * Converts markdown-like syntax in AI responses to HTML for better readability:
 * - Code blocks (```code```) and inline code (`code`)
 * - Bold text (**text**)
 * - Italics (*text*)
 * - Numbered lists and bullet points
 * - Section headers (Hints, Instructions, etc.)
 * This makes AI responses more visually appealing and easier to scan in the narrow panel.
 *
 * @param {string} message - The raw message text from the AI
 * @returns {string} HTML-formatted message string
 */
function formatAssistantMessage(message) {
    // Clean up the message and normalize whitespace
    let formatted = message.trim();
    
    // Handle code blocks (backticks)
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre class="code-block">$1</pre>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Handle numbered lists
    formatted = formatted.replace(/^(\d+\.\s)/gm, '<span class="list-number">$1</span>');
    
    // Handle bullet points
    formatted = formatted.replace(/^[•·*-]\s/gm, '<span class="bullet-point">• </span>');
    
    // Handle bold text (markdown style)
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle emphasis/italics
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle line breaks and paragraphs
    formatted = formatted.replace(/

/g, '</p><p>');
    formatted = formatted.replace(/
/g, '<br>');
    
    // Wrap in paragraph tags if not already wrapped
    if (!formatted.includes('<p>') && !formatted.includes('<pre>')) {
        formatted = '<p>' + formatted + '</p>';
    }
    
    // Handle special sections with better formatting
    formatted = formatted.replace(/Here are some hints:/g, '<div class="hint-section"><strong>💡 Hints:</strong></div>');
    formatted = formatted.replace(/Instructions:/g, '<div class="instruction-section"><strong>📋 Instructions:</strong></div>');
    formatted = formatted.replace(/Steps:/g, '<div class="steps-section"><strong>🔄 Steps:</strong></div>');
    formatted = formatted.replace(/Solution:/g, '<div class="solution-section"><strong>✅ Solution:</strong></div>');
    formatted = formatted.replace(/Error:/g, '<div class="error-section"><strong>❌ Error:</strong></div>');
    
    return formatted;
}

/**
 * Sends a student's message to the AI assistant and displays the response.
 *
 * This is the main chat interaction function. It sends the student's question along
 * with current exercise context to the backend AI service (LAB_CHAT endpoint). The
 * AI provides contextual help, debugging assistance, concept explanations, and hints.
 * Falls back to local context-aware responses if the backend is unavailable.
 *
 * @async
 * @returns {Promise<void>}
 *
 * @example
 * // Triggered when student presses Enter in chat input
 * await sendMessage();
 */
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message) {
        addMessage(message, 'user');
        input.value = '';

        // Show loading indicator
        addMessage('...', 'assistant', 'loading');
        
        try {
            // Prepare request data with debugging
            const requestData = {
                course_id: window.currentCourseId || '6460e0c5-f819-4b2e-be50-cf835903b9b4', // Fallback to known working course ID
                student_id: window.currentStudentId || 'frontend-user-' + Date.now(),
                user_message: message,
                context: {
                    course_title: window.currentCourseTitle || 'Introduction to Python',
                    student_progress: window.currentExerciseContext || {},
                    current_exercise: window.currentExerciseContext?.title || null
                }
            };
            
            // Debug logging
            
            // Call the real AI chat API with exercise context
            const response = await fetch(window.CONFIG?.ENDPOINTS.LAB_CHAT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                const data = await response.json();
                
                // Remove loading message
                const chatContainer = document.getElementById('chatContainer');
                const loadingMsg = chatContainer.querySelector('.loading');
                if (loadingMsg) {
                    loadingMsg.remove();
                }
                
                // Add the real AI response
                addMessage(data.response, 'assistant');
                
                // If AI suggested an exercise, handle it
                if (data.exercise && data.exercise.title !== 'Suggested Exercise') {
                    // Could add exercise suggestions to UI here
                }
            } else {
                const errorText = await response.text();
                console.error('AI Chat API Error:', response.status, errorText);
                throw new Error(`Failed to get AI response: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            console.error('Error calling AI chat:', error);
            console.error('Full error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            // Remove loading message
            const chatContainer = document.getElementById('chatContainer');
            const loadingMsg = chatContainer.querySelector('.loading');
            if (loadingMsg) {
                loadingMsg.remove();
            }
            
            // Fallback response
            let aiResponse = '';
            
            if (window.currentExerciseContext) {
                const exercise = window.currentExerciseContext;
                aiResponse = `I'm here to help with your current lab: **${exercise.title}** (*${exercise.difficulty}* level).

I'm ready to help with any questions about this exercise. You can ask me about:
• Requirements and instructions
• Coding help and debugging
• Hints and guidance
• Solutions and explanations

What would you like help with?`;
            } else {
                aiResponse = 'I can help you with that! Can you share your code so I can provide specific feedback?';
            }
            
            addMessage(aiResponse, 'assistant');
        }
    }
}

// Expose to global scope immediately
window.sendMessage = sendMessage;

/**
 * Handles keyboard input in the terminal for command execution and history navigation.
 *
 * Processes special keys for terminal interaction:
 * - Enter: Executes the current command and adds to history
 * - ArrowUp: Navigate to previous command in history
 * - ArrowDown: Navigate to next command in history
 * This provides a realistic Bash-like terminal experience with command recall.
 *
 * @param {KeyboardEvent} event - The keyboard event from terminal input
 * @returns {void}
 *
 * @example
 * // Attached to terminal input's onkeydown event
 * <input onkeydown="handleTerminalInput(event)" />
 */
function handleTerminalInput(event) {
    if (event.key === 'Enter') {
        const input = document.getElementById('terminalInput');
        const command = input.value.trim();

        if (command) {
            executeTerminalCommand(command);
            terminalHistory.push(command);
            historyIndex = terminalHistory.length;
        }

        input.value = '';
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (historyIndex > 0) {
            historyIndex--;
            document.getElementById('terminalInput').value = terminalHistory[historyIndex];
        }
    } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (historyIndex < terminalHistory.length - 1) {
            historyIndex++;
            document.getElementById('terminalInput').value = terminalHistory[historyIndex];
        } else {
            historyIndex = terminalHistory.length;
            document.getElementById('terminalInput').value = '';
        }
    }
}

/**
 * Executes a terminal command in the simulated Bash environment.
 *
 * Parses and executes common Linux commands (ls, cd, pwd, cat, mkdir, etc.) in a
 * simulated file system. In sandboxed mode, enforces security restrictions by:
 * - Validating commands against allowlist
 * - Logging all command execution for security auditing
 * - Restricting file system access to student's home directory
 * Provides realistic terminal output and error messages.
 *
 * @param {string} command - The complete command string to execute
 * @returns {void}
 *
 * @example
 * // Student types "ls -la" and presses Enter
 * executeTerminalCommand('ls -la');
 */
function executeTerminalCommand(command) {
    const terminalOutput = document.getElementById('terminalOutput');
    if (!terminalOutput) return;

    // Log command execution for security monitoring
    if (isLabSandboxed) {
        logCommandExecution(command);
    }

    const promptLine = `student@lab:${currentDirectory.replace(sandboxRoot, '~')}$ ${command}
`;

    terminalOutput.textContent += promptLine;

    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Security check: validate command is allowed
    if (isLabSandboxed && !isCommandAllowed(cmd)) {
        const output = `Permission denied: Command '${cmd}' is not allowed in this sandboxed environment.
Type 'help' to see available commands.
`;
        terminalOutput.textContent += output;
        addPrompt();
        scrollToBottom();
        return;
    }

    let output = '';
    
    switch (cmd) {
        case 'help':
            output = 'Available commands:
' +
                   'ls [path]          - List directory contents
' +
                   'cd <path>          - Change directory
' +
                   'pwd                - Print working directory
' +
                   'cat <file>         - Display file contents
' +
                   'echo <text>        - Display text
' +
                   'mkdir <dir>        - Create directory
' +
                   'touch <file>       - Create empty file
' +
                   'clear              - Clear terminal
' +
                   'whoami             - Display current user
' +
                   'date               - Display current date
' +
                   'help               - Show this help
';
            break;
        
        case 'ls':
            output = simulateLS(args[0] || currentDirectory);
            break;
        
        case 'pwd':
            output = currentDirectory + '
';
            break;
        
        case 'cd':
            output = simulateCD(args[0] || sandboxRoot);
            break;
        
        case 'cat':
            output = simulateCAT(args[0]);
            break;
        
        case 'echo':
            output = args.join(' ') + '
';
            break;
        
        case 'whoami':
            output = 'student
';
            break;
        
        case 'date':
            output = new Date().toString() + '
';
            break;
        
        case 'clear':
            clearTerminal();
            return;
        
        case 'mkdir':
            output = simulateMKDIR(args[0]);
            break;
        
        case 'touch':
            output = simulateTOUCH(args[0]);
            break;
        
        default:
            output = `bash: ${cmd}: command not found
`;
            break;
    }
    
    terminalOutput.textContent += output;
    terminalOutput.textContent += `student@lab:${currentDirectory.replace('/home/student', '~')}$ `;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

/**
 * Simulates the Linux 'ls' command for file/directory listing.
 *
 * Returns a formatted list of files and directories for the specified path.
 * Supports current directory (.) and subdirectories. Used to help students
 * navigate the simulated file system and understand directory structure.
 *
 * @param {string} path - The path to list (defaults to current directory)
 * @returns {string} Formatted file listing or error message
 */
function simulateLS(path) {
    // Simplified file listing
    if (path === '.' || path === currentDirectory || !path) {
        return 'readme.txt  examples/
';
    } else if (path === 'examples') {
        return 'hello.sh  test.py  sample.js
';
    } else {
        return `ls: cannot access '${path}': No such file or directory
`;
    }
}

/**
 * Simulates the Linux 'cd' (change directory) command.
 *
 * Handles absolute paths (/path), relative paths (subdir), parent directory (..),
 * and home directory (~). In sandboxed mode, prevents navigation outside the
 * student's restricted directory tree. Updates currentDirectory on success.
 *
 * @param {string} path - The target directory path
 * @returns {string} Empty string on success, error message on failure
 *
 * @example
 * // Navigate to parent directory
 * simulateCD('..');
 */
function simulateCD(path) {
    // Resolve target path
    let targetPath;

    if (path === '.' || path === currentDirectory) {
        return '';
    } else if (path === '..') {
        if (currentDirectory === sandboxRoot) {
            return ''; // Can't go above sandbox root
        }
        targetPath = currentDirectory.substring(0, currentDirectory.lastIndexOf('/')) || sandboxRoot;
    } else if (path === '~') {
        targetPath = sandboxRoot;
    } else if (path.startsWith('/')) {
        targetPath = path; // Absolute path
    } else {
        targetPath = currentDirectory + '/' + path; // Relative path
    }

    // Validate sandbox access
    const accessCheck = validateSandboxAccess(targetPath);
    if (!accessCheck.allowed) {
        return accessCheck.message + '
';
    }

    // Check if directory exists in our simulated file system
    if (targetPath === sandboxRoot ||
        targetPath === sandboxRoot + '/examples' ||
        (fileSystem[targetPath] && typeof fileSystem[targetPath] === 'object')) {
        currentDirectory = targetPath;
        return '';
    } else {
        return `bash: cd: ${path}: No such file or directory
`;
    }
}

/**
 * Simulates the Linux 'cat' command to display file contents.
 *
 * Retrieves and displays the contents of files in the simulated file system.
 * Students can read example code files, documentation, and security notices.
 * Returns appropriate error messages for missing files or missing operands.
 *
 * @param {string} filename - The name of the file to display
 * @returns {string} File contents or error message
 *
 * @example
 * // Display readme file
 * simulateCAT('readme.txt');
 */
function simulateCAT(filename) {
    if (!filename) {
        return 'cat: missing file operand
';
    }

    if (filename === 'readme.txt' && currentDirectory === '/home/student') {
        return 'Welcome to the lab environment!
This is a simulated file system.
';
    } else if (filename === 'hello.sh' && currentDirectory.includes('examples')) {
        return '#!/bin/bash
echo "Hello from the lab!"
';
    } else {
        return `cat: ${filename}: No such file or directory
`;
    }
}

/**
 * Simulates the Linux 'mkdir' command to create directories.
 *
 * Provides feedback for directory creation in the simulated file system.
 * Used to teach students basic Linux file system management commands.
 *
 * @param {string} dirname - The name of the directory to create
 * @returns {string} Success message or error if dirname missing
 */
function simulateMKDIR(dirname) {
    if (!dirname) {
        return 'mkdir: missing operand
';
    }
    return `Directory '${dirname}' created (simulated)
`;
}

/**
 * Simulates the Linux 'touch' command to create empty files.
 *
 * Provides feedback for file creation in the simulated file system.
 * Used to teach students basic Linux file manipulation commands.
 *
 * @param {string} filename - The name of the file to create
 * @returns {string} Success message or error if filename missing
 */
function simulateTOUCH(filename) {
    if (!filename) {
        return 'touch: missing file operand
';
    }
    return `File '${filename}' created (simulated)
`;
}

/**
 * Validates if a command is allowed in sandboxed lab environment.
 *
 * Security function that checks commands against an allowlist in sandboxed mode.
 * Prevents students from running potentially dangerous or disruptive commands
 * when multiple students share the same Docker container. Non-sandboxed labs
 * allow all commands.
 *
 * @param {string} cmd - The command to validate
 * @returns {boolean} True if command is allowed, false if blocked
 */
function isCommandAllowed(cmd) {
    if (!isLabSandboxed) return true;
    return allowedCommands.includes(cmd);
}

/**
 * Validates if a file path is accessible within sandbox restrictions.
 *
 * Security function that enforces file system boundaries in sandboxed mode.
 * Prevents access to:
 * - Paths outside sandbox root (/home/student)
 * - System directories (/etc, /root, /sys, /proc, /dev)
 * Essential for multi-tenant lab security to prevent student interference.
 *
 * @param {string} path - The file path to validate
 * @returns {boolean} True if path is accessible, false if restricted
 */
function isPathAllowed(path) {
    if (!isLabSandboxed) return true;

    // Resolve relative paths
    const resolvedPath = resolvePath(path);

    // Check if path is within sandbox root
    if (!resolvedPath.startsWith(sandboxRoot)) {
        return false;
    }

    // Check if path is in blocked paths
    for (const blockedPath of blockedPaths) {
        if (resolvedPath.startsWith(blockedPath)) {
            return false;
        }
    }

    return true;
}

/**
 * Resolves relative file paths to absolute paths.
 *
 * Converts relative paths to absolute paths based on current working directory.
 * Handles both relative (./file, ../dir) and absolute (/path/to/file) paths.
 * Used by security validation functions to ensure proper path checking.
 *
 * @param {string} path - The path to resolve (relative or absolute)
 * @returns {string} The resolved absolute path
 */
function resolvePath(path) {
    if (!path) return currentDirectory;

    if (path.startsWith('/')) {
        return path; // Absolute path
    } else {
        // Relative path - resolve relative to current directory
        return currentDirectory + '/' + path;
    }
}

/**
 * Logs terminal command execution for security auditing and analytics.
 *
 * Records all commands executed by students in sandboxed environments including:
 * - Timestamp of execution
 * - Student and session IDs
 * - Full command text
 * - Current working directory
 * Logs are stored locally (production would send to backend). Enables detection
 * of security violations and provides insights into student learning patterns.
 *
 * @param {string} command - The command that was executed
 * @returns {void}
 */
function logCommandExecution(command) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        studentId: studentId,
        sessionId: sessionId,
        command: command,
        directory: currentDirectory
    };

    // Store in localStorage for now - in production this would be sent to server
    const logs = JSON.parse(localStorage.getItem('commandLogs') || '[]');
    logs.push(logEntry);

    // Keep only last 1000 entries
    if (logs.length > 1000) {
        logs.splice(0, logs.length - 1000);
    }

    localStorage.setItem('commandLogs', JSON.stringify(logs));

}

/**
 * Validates sandbox access for a given file path.
 *
 * Wrapper function that checks if a path is accessible within sandbox restrictions.
 * Returns an object with allowed status and optional error message. Used before
 * file system operations to enforce security boundaries.
 *
 * @param {string} path - The file path to validate
 * @returns {Object} Object with 'allowed' boolean and optional 'message' string
 */
function validateSandboxAccess(path) {
    if (!isLabSandboxed) return { allowed: true };

    if (!isPathAllowed(path)) {
        return {
            allowed: false,
            message: `Access denied: Path '${path}' is outside the sandbox or in a restricted area.`
        };
    }

    return { allowed: true };
}

/**
 * Tracks when a student begins working on an exercise.
 *
 * Initializes progress tracking for an exercise including start time, attempt count,
 * and completion status. This data enables instructors to see which exercises
 * students struggle with and how long they spend on each one. Also used for
 * calculating time-on-task metrics.
 *
 * @param {string|number} exerciseId - The unique identifier of the exercise
 * @returns {void}
 */
function trackExerciseStart(exerciseId) {
    if (!exerciseProgress[exerciseId]) {
        exerciseProgress[exerciseId] = {
            started: new Date().toISOString(),
            attempts: 0,
            completed: false,
            timeSpent: 0,
            lastActivity: new Date().toISOString()
        };
    }

    exerciseProgress[exerciseId].lastActivity = new Date().toISOString();
    saveProgressToLocalStorage();
}

/**
 * Marks an exercise as completed and updates analytics.
 *
 * Records exercise completion timestamp, saves progress to server and localStorage,
 * and updates UI with completion checkmark. Triggers congratulatory messages and
 * overall progress summary updates. Critical for tracking student achievement.
 *
 * @param {string|number} exerciseId - The ID of the completed exercise
 * @returns {void}
 */
function trackExerciseCompletion(exerciseId) {
    if (!exerciseProgress[exerciseId]) {
        trackExerciseStart(exerciseId);
    }

    exerciseProgress[exerciseId].completed = true;
    exerciseProgress[exerciseId].completedAt = new Date().toISOString();
    exerciseProgress[exerciseId].lastActivity = new Date().toISOString();

    saveProgressToLocalStorage();
    saveProgressToServer();

    // Update UI to show completion
    updateExerciseUI(exerciseId, true);

}

/**
 * Tracks each code execution attempt for analytics and progress detection.
 *
 * Records student code attempts including:
 * - Attempt counter increment
 * - Full code snapshot
 * - Timestamp
 * Stores last 10 attempts per exercise for debugging and learning pattern analysis.
 * Helps instructors identify common mistakes and student coding evolution.
 *
 * @param {string|number} exerciseId - The exercise being attempted
 * @param {string} code - The student's code at time of execution
 * @returns {void}
 */
function trackCodeExecution(exerciseId, code) {
    if (!exerciseProgress[exerciseId]) {
        trackExerciseStart(exerciseId);
    }

    exerciseProgress[exerciseId].attempts++;
    exerciseProgress[exerciseId].lastActivity = new Date().toISOString();

    // Store the code attempt
    if (!exerciseProgress[exerciseId].codeAttempts) {
        exerciseProgress[exerciseId].codeAttempts = [];
    }

    exerciseProgress[exerciseId].codeAttempts.push({
        code: code,
        timestamp: new Date().toISOString()
    });

    // Keep only last 10 attempts
    if (exerciseProgress[exerciseId].codeAttempts.length > 10) {
        exerciseProgress[exerciseId].codeAttempts.splice(0, 1);
    }

    saveProgressToLocalStorage();
}

/**
 * Updates the exercise UI to visually indicate completion status.
 *
 * Adds completion styling (checkmark icon, 'completed' CSS class) to exercises
 * in the sidebar when students complete them. Provides immediate visual feedback
 * and helps students track their progress through the exercise list.
 *
 * @param {string|number} exerciseId - The exercise ID to update
 * @param {boolean} completed - Whether the exercise is completed
 * @returns {void}
 */
function updateExerciseUI(exerciseId, completed) {
    const exerciseElement = document.querySelector(`[onclick="selectExercise(${exerciseId})"]`);
    if (exerciseElement) {
        if (completed) {
            exerciseElement.classList.add('completed');
            const checkmark = exerciseElement.querySelector('.completion-checkmark');
            if (!checkmark) {
                const checkmarkElement = document.createElement('div');
                checkmarkElement.className = 'completion-checkmark';
                checkmarkElement.innerHTML = '<i class="fas fa-check-circle"></i>';
                exerciseElement.appendChild(checkmarkElement);
            }
        }
    }
}

/**
 * Loads student's previous lab progress from backend server or localStorage.
 *
 * Attempts to fetch progress from backend first (for cross-device continuity),
 * falls back to localStorage if unavailable. Restores exercise completion status,
 * attempt counts, code history, and total time spent. Updates UI to show completed
 * exercises with checkmarks. Enables seamless session resumption.
 *
 * @async
 * @returns {Promise<void>}
 */
async function loadStudentProgress() {
    try {
        // Try to load from server first
        const response = await fetch(`${window.CONFIG?.ENDPOINTS?.LAB_SESSION_LOAD(courseId, studentId)}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        if (response.ok) {
            const serverProgress = await response.json();
            exerciseProgress = serverProgress.exerciseProgress || {};
            totalLabTime = serverProgress.totalLabTime || 0;
        } else {
            // Fallback to localStorage
            loadProgressFromLocalStorage();
        }
    } catch (error) {
        console.error('Error loading progress from server:', error);
        // Fallback to localStorage
        loadProgressFromLocalStorage();
    }

    // Update UI for completed exercises
    Object.keys(exerciseProgress).forEach(exerciseId => {
        if (exerciseProgress[exerciseId].completed) {
            updateExerciseUI(parseInt(exerciseId), true);
        }
    });
}

/**
 * Loads student progress from browser's localStorage.
 *
 * Fallback mechanism when server is unavailable. Parses and restores progress
 * data stored locally in browser. Each student+course combination has unique
 * storage key to prevent data conflicts.
 *
 * @returns {void}
 */
function loadProgressFromLocalStorage() {
    const progressKey = `labProgress_${studentId}_${courseId}`;
    const savedProgress = localStorage.getItem(progressKey);

    if (savedProgress) {
        try {
            const progressData = JSON.parse(savedProgress);
            exerciseProgress = progressData.exerciseProgress || {};
            totalLabTime = progressData.totalLabTime || 0;
        } catch (error) {
            console.error('Error parsing saved progress:', error);
        }
    }
}

/**
 * Saves current lab progress to browser's localStorage.
 *
 * Persists progress locally for offline resilience and quick access. Includes
 * exercise progress, total lab time, and last update timestamp. Called frequently
 * to ensure minimal data loss if browser crashes or connection is lost.
 *
 * @returns {void}
 */
function saveProgressToLocalStorage() {
    if (!studentId || !courseId) return;

    const progressKey = `labProgress_${studentId}_${courseId}`;
    const progressData = {
        exerciseProgress: exerciseProgress,
        totalLabTime: calculateTotalLabTime(),
        lastUpdated: new Date().toISOString()
    };

    localStorage.setItem(progressKey, JSON.stringify(progressData));
}

/**
 * Saves current lab progress to backend server for persistence.
 *
 * Sends progress data to LAB_SESSION_SAVE endpoint including:
 * - Exercise completion status and timestamps
 * - Code attempt history
 * - Total session time
 * - Student/course/session identifiers
 * Falls back to localStorage on network failure. Enables cross-device continuity
 * and instructor analytics dashboard.
 *
 * @async
 * @returns {Promise<void>}
 */
async function saveProgressToServer() {
    if (!studentId || !courseId) return;

    try {
        const progressData = {
            student_id: studentId,
            course_id: courseId,
            session_id: sessionId,
            exercise_progress: exerciseProgress,
            total_lab_time: calculateTotalLabTime(),
            last_activity: new Date().toISOString()
        };

        const response = await fetch(`${window.CONFIG?.ENDPOINTS?.LAB_SESSION_SAVE}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(progressData)
        });

        if (response.ok) {
        } else {
            console.warn('Failed to save progress to server, using localStorage fallback');
            saveProgressToLocalStorage();
        }
    } catch (error) {
        console.error('Error saving progress to server:', error);
        saveProgressToLocalStorage();
    }
}

/**
 * Calculates total time spent in lab environment across all sessions.
 *
 * Combines previous session time with current session duration. Used for
 * time-on-task analytics and student engagement metrics. Time is calculated
 * in seconds from session start to current moment.
 *
 * @returns {number} Total lab time in seconds
 */
function calculateTotalLabTime() {
    if (!labStartTime) return totalLabTime;

    const currentTime = new Date();
    const sessionTime = Math.floor((currentTime - labStartTime) / 1000); // in seconds
    return totalLabTime + sessionTime;
}

/**
 * Generates a summary of student's overall lab progress.
 *
 * Calculates and returns key progress metrics including:
 * - Total number of exercises available
 * - Number of completed exercises
 * - Completion percentage
 * - Total time spent in lab
 * Used for progress bars, completion certificates, and instructor dashboards.
 *
 * @returns {Object} Progress summary object
 * @returns {number} returns.totalExercises - Total available exercises
 * @returns {number} returns.completedExercises - Number completed
 * @returns {number} returns.progressPercentage - Completion percentage (0-100)
 * @returns {number} returns.totalTime - Total lab time in seconds
 */
function getProgressSummary() {
    const totalExercises = exercises.length;
    const completedExercises = Object.values(exerciseProgress).filter(p => p.completed).length;
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;

    return {
        totalExercises,
        completedExercises,
        progressPercentage,
        totalTime: calculateTotalLabTime()
    };
}

/**
 * Automatically detects and marks exercise completion based on code analysis.
 *
 * Uses intelligent keyword matching to determine if student's code meets exercise
 * requirements. Compares student code to solution, looking for 70% keyword match.
 * Falls back to line count heuristic if no solution available. When completion
 * detected, triggers celebration message, checkmark UI, and progress updates.
 * Prevents duplicate completion notifications.
 *
 * @param {string|number} exerciseId - The exercise to check for completion
 * @param {string} code - The student's current code
 * @returns {void}
 */
function checkForExerciseCompletion(exerciseId, code) {
    const exercise = exercises.find(ex => ex.id === exerciseId);
    if (!exercise || exerciseProgress[exerciseId]?.completed) {
        return; // Exercise not found or already completed
    }

    // Simple completion detection based on code content and patterns
    let isCompleted = false;

    // Check if the code contains key elements from the solution
    if (exercise.solution) {
        const solutionKeywords = extractKeywords(exercise.solution);
        const codeKeywords = extractKeywords(code);

        // If code contains at least 70% of solution keywords, consider it complete
        const matchingKeywords = solutionKeywords.filter(keyword =>
            codeKeywords.some(codeKeyword => codeKeyword.includes(keyword) || keyword.includes(codeKeyword))
        );

        const completionThreshold = Math.max(1, Math.floor(solutionKeywords.length * 0.7));
        isCompleted = matchingKeywords.length >= completionThreshold;
    } else {
        // Fallback: check for basic completion indicators
        const codeLines = code.split('
').filter(line => line.trim().length > 0);
        isCompleted = codeLines.length >= 3; // At least 3 non-empty lines
    }

    if (isCompleted) {
        trackExerciseCompletion(exerciseId);

        // Show completion message
        addMessage(`🎉 Congratulations! You've completed the exercise "${exercise.title}"! Great work!`, 'assistant');
        addToTerminal(`✅ Exercise "${exercise.title}" completed!`, 'success');

        // Update progress summary display if it exists
        updateProgressDisplay();
    }
}

/**
 * Extracts meaningful keywords from code for completion analysis.
 *
 * Parses code to identify variable names, function names, and other identifiers
 * while filtering out:
 * - Comments (// and /* */)
 * - String literals
 * - Common language keywords (var, if, while, etc.)
 * Returns unique set of significant identifiers that represent actual code logic.
 *
 * @param {string} code - The code to extract keywords from
 * @returns {Array<string>} Array of unique meaningful identifiers
 */
    /**
     * EXECUTE EXTRACTKEYWORDS OPERATION
     * PURPOSE: Execute extractKeywords operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} code - Code parameter
     */
function extractKeywords(code) {
    // Extract meaningful keywords from code (variables, functions, etc.)
    const keywords = [];

    // Remove comments and strings to focus on actual code
    const cleanCode = code
        .replace(/\/\*[\s\S]*?\*\//g, '') // Remove /* */ comments
        .replace(/\/\/.*$/gm, '') // Remove // comments
        .replace(/"[^"]*"/g, '') // Remove double-quoted strings
        .replace(/'[^']*'/g, ''); // Remove single-quoted strings

    // Extract words that look like identifiers (letters, numbers, underscore)
    const matches = cleanCode.match(/[a-zA-Z_][a-zA-Z0-9_]*/g);

    if (matches) {
        // Filter out common language keywords
        const commonKeywords = ['var', 'let', 'const', 'function', 'if', 'else', 'for', 'while', 'return', 'console', 'log', 'print'];
        keywords.push(...matches.filter(word =>
            word.length > 2 && !commonKeywords.includes(word.toLowerCase())
        ));
    }

    return [...new Set(keywords)]; // Remove duplicates
}

/**
 * Updates all progress indicator displays in the UI.
 *
 * Refreshes progress indicators with current completion statistics. Updates
 * elements with class 'progress-indicator' to show X/Y exercises completed
 * and percentage. Called after exercise completion to provide immediate
 * visual feedback on overall progress.
 *
 * @returns {void}
 */
function updateProgressDisplay() {
    const summary = getProgressSummary();

    // Update any progress indicators in the UI
    const progressElements = document.querySelectorAll('.progress-indicator');
    progressElements.forEach(element => {
        element.textContent = `${summary.completedExercises}/${summary.totalExercises} exercises completed (${summary.progressPercentage}%)`;
    });

    // Log progress for debugging
}

/**
 * Clears all content from the terminal window.
 *
 * Removes all previous terminal output and displays a "Terminal cleared" message.
 * In sandboxed mode, also shows session ID reminder. Useful for students who
 * want to clean up cluttered terminal output and start fresh. The command
 * prompt is updated to reflect current directory.
 *
 * @returns {void}
 */
function clearTerminal() {
    const terminalContent = document.getElementById('terminalContent');
    if (terminalContent) {
        terminalContent.innerHTML = '';
        const clearLine = document.createElement('div');
        clearLine.className = 'terminal-line';
        clearLine.textContent = 'Terminal cleared.';
        terminalContent.appendChild(clearLine);

        if (isLabSandboxed) {
            const sessionLine = document.createElement('div');
            sessionLine.className = 'terminal-line';
            sessionLine.textContent = `Secure Lab Environment - Session: ${sessionId}`;
            terminalContent.appendChild(sessionLine);
        }

        const emptyLine = document.createElement('div');
        emptyLine.className = 'terminal-line';
        emptyLine.textContent = '';
        terminalContent.appendChild(emptyLine);
    }

    updatePrompt();
}

/**
 * Focuses the terminal input field for immediate typing.
 *
 * Programmatically moves keyboard focus to the terminal input, allowing students
 * to start typing commands immediately without clicking. Called on page load
 * and after certain operations to improve user experience.
 *
 * @returns {void}
 */
function focusTerminalInput() {
    const terminalInput = document.getElementById('terminalInput');
    if (terminalInput) {
        terminalInput.focus();
    }
}

// Expose to global scope immediately
window.focusTerminalInput = focusTerminalInput;

/**
 * Updates the terminal command prompt to show current directory.
 *
 * Refreshes the prompt display with current working directory. Replaces
 * /home/student with ~ for brevity (standard Bash convention). Called after
 * directory changes to keep prompt accurate.
 *
 * @returns {void}
 */
function updatePrompt() {
    const promptSpan = document.querySelector('.terminal-prompt');
    if (promptSpan) {
        promptSpan.textContent = `student@lab:${currentDirectory.replace('/home/student', '~')}$`;
    }
}

/**
 * Scrolls terminal window to bottom to show latest output.
 *
 * Automatically scrolls terminal view after new output is added, ensuring
 * students always see the most recent command results without manual scrolling.
 * Improves terminal usability and mimics real terminal behavior.
 *
 * @returns {void}
 */
function scrollToBottom() {
    const terminalWindow = document.getElementById('terminalWindow');
    if (terminalWindow) {
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }
}

/**
 * Initializes the terminal after DOM load with auto-focus.
 *
 * Sets up terminal with a small delay to ensure DOM elements are ready.
 * Automatically focuses terminal input so students can start typing commands
 * immediately when the lab environment loads. Improves initial user experience.
 *
 * @returns {void}
 */
function initializeTerminal() {
    setTimeout(() => {
        focusTerminalInput();
    }, 100);
}

/**
 * Global Function Exports
 *
 * Expose all lab functions to the global window object for accessibility from HTML
 * event handlers and external scripts. This enables inline onclick handlers and
 * integration with other frontend modules.
 */
window.togglePanel = togglePanel;
window.toggleSolution = toggleSolution;
window.initializeLab = initializeLab;
window.initializeTerminal = initializeTerminal;
window.displayExercises = displayExercises;
window.selectExercise = selectExercise;
window.changeLanguage = changeLanguage;
window.runCode = runCode;
window.clearCode = clearCode;
window.handleTerminalInput = handleTerminalInput;
window.sendMessage = sendMessage;
window.focusTerminalInput = focusTerminalInput;
window.updateToggleButtons = updateToggleButtons;

/**
 * Forces the exercises to display immediately.
 *
 * Debug/test function that bypasses normal loading flow to render exercises.
 * Useful for troubleshooting when exercises fail to appear due to timing issues
 * or API failures. Can be invoked from browser console during development.
 *
 * @function forceDisplayExercises
 * @global
 * @returns {void}
 *
 * @example
 * // From browser console
 * window.forceDisplayExercises();
 */
window.forceDisplayExercises = function() {
    displayExercises();
};

/**
 * Forces the exercise panel to become visible.
 *
 * Debug/test function that unhides the exercise panel and updates layout state.
 * Useful for troubleshooting panel visibility issues during development or when
 * panels get hidden accidentally. Can be invoked from browser console.
 *
 * @function forceShowExercisePanel
 * @global
 * @returns {void}
 *
 * @example
 * // From browser console
 * window.forceShowExercisePanel();
 */
window.forceShowExercisePanel = function() {
    const exercisePanel = document.getElementById('exercisePanel');
    if (exercisePanel) {
        exercisePanel.classList.remove('panel-hidden');
        panelStates.exercises = true;
        updateLayout();
    }
};

/**
 * Initializes the lab environment after DOM is fully loaded.
 *
 * Master initialization function that orchestrates all lab components:
 * 1. Resets all panel states to visible (four-panel layout)
 * 2. Updates layout and toggle button states
 * 3. Calls main lab initialization (exercises, progress, AI)
 * 4. Initializes terminal with auto-focus
 * Ensures all DOM elements exist before attempting initialization.
 *
 * @returns {void}
 */
function initializeLabAfterDOM() {

    // First, ensure all panels are properly initialized
    panelStates = {
        exercises: true,
        editor: true,
        terminal: true,
        assistant: true
    };


    // Force update layout to ensure panels are visible
    updateLayout();
    updateToggleButtons();

    // Call the main initialization
    if (typeof window.initializeLab === 'function') {
        window.initializeLab();
    }

    // Initialize terminal
    if (typeof window.initializeTerminal === 'function') {
        window.initializeTerminal();
    }
}

/**
 * Wrapper function to initialize lab after page load.
 *
 * Intelligently waits for DOM to be ready before initializing. If document is
 * still loading, attaches DOMContentLoaded listener. If already loaded, initializes
 * immediately. This ensures reliable initialization regardless of when script runs.
 * Exposed globally for manual invocation if needed.
 *
 * @returns {void}
 *
 * @example
 * // Called from HTML onload or script
 * window.initializeAfterLoad();
 */
window.initializeAfterLoad = function() {

    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeLabAfterDOM();
        });
    } else {
        initializeLabAfterDOM();
    }
};

window.initializeLabAfterDOM = initializeLabAfterDOM;
