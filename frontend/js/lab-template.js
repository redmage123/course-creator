// Lab environment JavaScript functions (global scope)

// Fallback CONFIG if not loaded yet
if (typeof window.CONFIG === 'undefined') {
    window.CONFIG = {
        ENDPOINTS: {
            EXERCISES: (courseId) => `http://176.9.99.103:8001/exercises/${courseId}`,
            SYLLABUS: (courseId) => `http://176.9.99.103:8001/syllabus/${courseId}`,
            GENERATE_EXERCISES: () => `http://176.9.99.103:8001/generate-exercises`,
            REFRESH_LAB_EXERCISES: `http://176.9.99.103:8001/lab/refresh-exercises`
        }
    };
}

let exercises = [];
let courseTitle = '';
let currentLanguage = 'javascript';
let terminalHistory = [];
let historyIndex = -1;
let currentDirectory = '/home/student';
let currentExercise = null;
let panelStates = {
    exercises: true,
    editor: true,
    terminal: true,
    assistant: true
};
let showingSolution = {};

// Sandboxed lab environment variables
let sandboxRoot = '/home/student'; // Chroot-like restriction
let isLabSandboxed = false;
let studentId = null;
let sessionId = null;
let allowedCommands = ['help', 'ls', 'cd', 'pwd', 'cat', 'echo', 'mkdir', 'touch', 'clear', 'whoami', 'date', 'nano', 'vim', 'python', 'node', 'gcc'];
let blockedPaths = ['/etc', '/root', '/sys', '/proc', '/dev'];

// Progress tracking variables
let courseId = null;
let exerciseProgress = {};
let labStartTime = null;
let totalLabTime = 0;

// File system simulation with sandbox restrictions
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

// Panel management
function togglePanel(panelName) {
    console.log('togglePanel called with:', panelName);
    console.log('Current panelStates:', panelStates);
    panelStates[panelName] = !panelStates[panelName];
    console.log('Updated panelStates:', panelStates);
    updateLayout();
    updateToggleButtons();
}

// Expose to global scope immediately
window.togglePanel = togglePanel;

function updateLayout() {
    console.log('updateLayout called');
    console.log('Current panelStates:', panelStates);
    
    const mainLayout = document.querySelector('.main-layout');
    if (!mainLayout) {
        console.error('Main layout not found!');
        return;
    }
    
    // Reset all layout classes
    mainLayout.className = 'main-layout';
    
    // Get visible panels
    const visiblePanels = Object.keys(panelStates).filter(panel => panelStates[panel]);
    console.log('Visible panels:', visiblePanels);
    
    // Update panel visibility
    const exercisePanel = document.getElementById('exercisePanel');
    const editorPanel = document.getElementById('editorPanel');
    const terminalPanel = document.getElementById('terminalPanel');
    const assistantPanel = document.getElementById('assistantPanel');
    
    console.log('Exercise panel found:', !!exercisePanel);
    console.log('Exercise panel state:', panelStates.exercises);
    
    if (exercisePanel) {
        exercisePanel.classList.toggle('panel-hidden', !panelStates.exercises);
        console.log('Exercise panel classes:', exercisePanel.className);
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

function updateToggleButtons() {
    console.log('updateToggleButtons called');
    const buttons = {
        exercises: document.getElementById('toggleExercises'),
        editor: document.getElementById('toggleEditor'),
        terminal: document.getElementById('toggleTerminal'),
        assistant: document.getElementById('toggleAssistant')
    };
    
    console.log('Toggle buttons found:', Object.keys(buttons).map(key => `${key}: ${!!buttons[key]}`));
    
    Object.keys(buttons).forEach(panel => {
        const button = buttons[panel];
        if (button) {
            button.classList.toggle('inactive', !panelStates[panel]);
            console.log(`Button ${panel} state: ${panelStates[panel]}, classes: ${button.className}`);
        }
    });
}

// Initialize the lab environment
async function initializeLab() {
    console.log('Initializing lab environment...');
    console.log('Current window functions:', Object.keys(window).filter(k => typeof window[k] === 'function' && k.includes('toggle')));
    
    // Check if this is a sandboxed environment
    const urlParams = new URLSearchParams(window.location.search);
    isLabSandboxed = urlParams.get('sandboxed') === 'true';
    studentId = urlParams.get('studentId');
    sessionId = urlParams.get('sessionId');
    courseId = urlParams.get('courseId') || window.currentCourseId || 'default';
    courseTitle = urlParams.get('course') || window.currentCourseName || 'Programming Course';
    
    console.log('Initialized courseId:', courseId);
    console.log('Initialized courseTitle:', courseTitle);
    console.log('CONFIG available:', typeof CONFIG);
    console.log('CONFIG.ENDPOINTS available:', typeof CONFIG?.ENDPOINTS);
    
    // Initialize progress tracking
    initializeProgressTracking();
    
    if (isLabSandboxed) {
        console.log('Lab running in sandboxed mode');
        initializeSandbox();
    }
    
    await loadExercises();
    updateLayout();
    
    const welcomeMessage = isLabSandboxed 
        ? `Welcome to your secure lab environment! Session ID: ${sessionId || 'Unknown'}\nYou are in a sandboxed terminal with restricted access for security.`
        : 'Welcome! Toggle panels using the controls above, select exercises, or ask me anything!';
    
    addMessage(welcomeMessage, 'system');
    console.log('Lab initialization complete');
}

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
    
    console.log('Progress tracking initialized');
}

function initializeSandbox() {
    // Set up sandbox restrictions
    console.log('Setting up sandbox restrictions...');
    
    // Restrict file system access to sandbox root
    const restrictedFS = {};
    restrictedFS[sandboxRoot] = fileSystem[sandboxRoot];
    
    // Add sandbox-specific files
    if (!restrictedFS[sandboxRoot]['.sandbox_info']) {
        restrictedFS[sandboxRoot]['.sandbox_info'] = `Sandbox Environment\nStudent ID: ${studentId}\nSession ID: ${sessionId}\nRestricted to: ${sandboxRoot}\n`;
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
    
    console.log('Sandbox initialized successfully');
}

// Load course-specific exercises from API
async function loadExercises() {
    console.log('Loading exercises for course:', courseId);
    console.log('Course title:', courseTitle);
    console.log('URL params:', window.location.search);
    
    try {
        const response = await fetch(`${CONFIG.ENDPOINTS.EXERCISES(courseId)}`);
        console.log('API response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            exercises = data.exercises || [];
            console.log(`Loaded ${exercises.length} exercises for course ${courseId}`);
            console.log('Exercise titles:', exercises.map(ex => ex.title));
            
            // If no exercises found, try to generate them
            if (exercises.length === 0) {
                console.log('No exercises found, attempting to generate...');
                await generateExercisesOnDemand();
            }
        } else {
            console.log('No exercises found for course, attempting to generate...');
            await generateExercisesOnDemand();
        }
    } catch (error) {
        console.error('Error loading exercises:', error);
        exercises = await loadFallbackExercises();
    }
    
    console.log('Final exercises count:', exercises.length);
    console.log('About to display exercises');
    console.log('exercises array before display:', exercises);
    
    // Force display with a delay to ensure DOM is ready
    setTimeout(() => {
        console.log('Delayed display exercises call');
        displayExercises();
    }, 100);
}

async function generateExercisesOnDemand() {
    console.log('Generating exercises on-demand for course:', courseId);
    
    try {
        // First try to get the syllabus for this course
        const syllabusResponse = await fetch(`${CONFIG.ENDPOINTS.SYLLABUS(courseId)}`);
        
        if (syllabusResponse.ok) {
            const syllabusData = await syllabusResponse.json();
            console.log('Found syllabus for course, generating exercises...');
            
            // Generate exercises using the topic from course title
            const generateRequest = {
                course_id: courseId,
                topic: courseTitle || 'Programming',
                difficulty: 'beginner'
            };
            
            const generateResponse = await fetch(`${CONFIG.API_URLS.COURSE_GENERATOR}/exercises/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(generateRequest)
            });
            
            if (generateResponse.ok) {
                const result = await generateResponse.json();
                exercises = result.exercises || [];
                console.log(`Generated ${exercises.length} exercises for course ${courseId}`);
                console.log('Generated exercise titles:', exercises.map(ex => ex.title));
            } else {
                console.log('Failed to generate exercises, using fallback');
                exercises = await loadFallbackExercises();
            }
        } else {
            console.log('No syllabus found for course, generating exercises from course title...');
            
            // Generate exercises using the topic from course title
            const generateRequest = {
                course_id: courseId,
                topic: courseTitle || 'Programming',
                difficulty: 'beginner'
            };
            
            const generateResponse = await fetch(`${CONFIG.API_URLS.COURSE_GENERATOR}/exercises/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(generateRequest)
            });
            
            if (generateResponse.ok) {
                const result = await generateResponse.json();
                exercises = result.exercises || [];
                console.log(`Generated ${exercises.length} exercises for course ${courseId}`);
                console.log('Generated exercise titles:', exercises.map(ex => ex.title));
            } else {
                console.log('Failed to generate exercises, using fallback');
                exercises = await loadFallbackExercises();
            }
        }
    } catch (error) {
        console.error('Error generating exercises on-demand:', error);
        exercises = await loadFallbackExercises();
    }
}

// Fallback exercises if none exist for the course
async function loadFallbackExercises() {
    console.log('Loading fallback exercises based on course topic');
    
    // Generate course-appropriate exercises based on course title/topic
    if (courseTitle && courseTitle.toLowerCase().includes('linux')) {
        return [
            {
                id: 1,
                title: "Basic Linux Commands",
                description: "Practice fundamental Linux commands like ls, cd, pwd, and mkdir.",
                difficulty: "easy",
                starterCode: "# Basic Linux Commands Practice\\n# 1. List files in current directory\\n# 2. Create a new directory\\n# 3. Navigate to different directories\\n# 4. Check current working directory\\n\\n# Your commands here:",
                solution: "ls -la\\nmkdir test_directory\\ncd test_directory\\npwd\\ncd ..\\nrmdir test_directory"
            },
            {
                id: 2,
                title: "File Permissions",
                description: "Learn to manage file permissions using chmod and understand permission modes.",
                difficulty: "medium",
                starterCode: "# File Permissions Exercise\\n# 1. Create a file\\n# 2. Check its permissions\\n# 3. Change permissions\\n# 4. Verify changes\\n\\n# Your commands here:",
                solution: "touch myfile.txt\\nls -l myfile.txt\\nchmod 755 myfile.txt\\nls -l myfile.txt\\nchmod u+x,g-w,o-r myfile.txt\\nls -l myfile.txt"
            }
        ];
    } else if (courseTitle && courseTitle.toLowerCase().includes('python')) {
        return [
            {
                id: 1,
                title: "Python Variables and Types",
                description: "Practice with Python variables, data types, and basic operations.",
                difficulty: "easy",
                starterCode: "# Python Variables and Types\\n# 1. Create variables of different types\\n# 2. Perform operations\\n# 3. Print results\\n\\n# Your code here:",
                solution: "name = 'Python Student'\\nage = 25\\nis_learning = True\\nheight = 5.8\\n\\nprint(f'Name: {name}')\\nprint(f'Age: {age}')\\nprint(f'Learning: {is_learning}')\\nprint(f'Height: {height}ft')"
            },
            {
                id: 2,
                title: "Python Functions",
                description: "Create and use functions with parameters and return values.",
                difficulty: "medium",
                starterCode: "# Python Functions Exercise\\n# 1. Define a function with parameters\\n# 2. Use return values\\n# 3. Call the function\\n\\n# Your code here:",
                solution: "def calculate_area(length, width):\\n    return length * width\\n\\ndef greet_user(name):\\n    return f'Hello, {name}!'\\n\\n# Test the functions\\narea = calculate_area(10, 5)\\ngreeting = greet_user('Python Student')\\n\\nprint(f'Area: {area}')\\nprint(greeting)"
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
                starterCode: "// Getting Started Exercise\\n// Follow the instructions provided by your instructor\\n\\n// Your code here:",
                solution: "// Solution will be provided by instructor"
            }
        ];
    }
    
    console.log('Loaded', exercises.length, 'exercises');
    displayExercises();
}

// Display exercises in the sidebar
function displayExercises() {
    console.log('Displaying exercises...');
    console.log('exercises array:', exercises);
    console.log('exercises.length:', exercises.length);
    
    const exerciseList = document.getElementById('exerciseList');
    if (!exerciseList) {
        console.error('Exercise list element not found!');
        return;
    }
    
    console.log('Exercise list element found:', exerciseList);
    
    // Ensure the exercises panel is visible
    const exercisePanel = document.getElementById('exercisePanel');
    if (exercisePanel) {
        exercisePanel.classList.remove('panel-hidden');
        panelStates.exercises = true;
        console.log('Exercise panel made visible');
    } else {
        console.error('Exercise panel not found!');
    }
    
    if (exercises.length === 0) {
        exerciseList.innerHTML = '<div class="no-exercises">No exercises available. Try refreshing the exercises.</div>';
        console.log('No exercises to display');
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
        
        console.log('Exercises displayed in DOM, count:', exercises.length);
        console.log('Exercise list innerHTML length:', exerciseList.innerHTML.length);
    }
    
    // Update the toggle button state
    const toggleButton = document.getElementById('toggleExercises');
    if (toggleButton) {
        toggleButton.classList.add('active');
    }
    
    // Force layout update
    updateLayout();
}

// Exercise selection
function selectExercise(exerciseId) {
    console.log('Selecting exercise:', exerciseId);
    
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
    addToTerminal(`Exercise loaded: ${currentExercise.title}\nRun your code to see the output.`, 'output');
    
    // Show lab notes popup instead of auto-messaging AI
    showLabNotesModal(currentExercise);
    
    // Update AI assistant context (but don't auto-send message)
    updateAIAssistantContext(currentExercise);
}

// Show lab notes modal when exercise is clicked
function showLabNotesModal(exercise) {
    console.log('Showing lab notes for exercise:', exercise.title);
    
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

// Update AI assistant context without auto-sending message
function updateAIAssistantContext(exercise) {
    console.log('Updating AI assistant context for exercise:', exercise.title);
    
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

// Focus code editor helper
function focusCodeEditor() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        editor.focus();
    }
}

// Ask AI for help with specific exercise
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
        const aiResponse = `I'd be happy to help you with "${exercise.title}"! This is a ${exercise.difficulty} level exercise. Let me provide some guidance:

${exercise.hints && exercise.hints.length > 0 ? 
    `Here are some hints to get you started:
• ${exercise.hints.join('\n• ')}` : 
    'Feel free to ask specific questions about the requirements or share your code if you need help debugging.'
}

What specific part would you like help with?`;
        
        addMessage(aiResponse, 'assistant');
    }, 1000);
}

// Expose to global scope immediately
window.selectExercise = selectExercise;
window.showLabNotesModal = showLabNotesModal;
window.updateAIAssistantContext = updateAIAssistantContext;
window.focusCodeEditor = focusCodeEditor;
window.askAIForHelp = askAIForHelp;

// Solution toggle functionality
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
        const solution = exercise.solution || exercise.expected_output || '// Solution not available\n';
        editor.value = solution.replace(/\\n/g, '\n');
        button.textContent = '🚫 Hide Solution';
        button.classList.add('active');
        showingSolution[exerciseId] = true;
        addToTerminal('Showing solution code', 'output');
    }
}

// Expose to global scope immediately
window.toggleSolution = toggleSolution;

// Change programming language
function changeLanguage() {
    const select = document.getElementById('languageSelect');
    currentLanguage = select.value;
    
    const editor = document.getElementById('codeEditor');
    if (editor) {
        // Set appropriate starter code for the language
        if (currentExercise) {
            // If showing solution, keep showing solution, otherwise show starter code
            if (showingSolution[currentExercise.id]) {
                editor.value = currentExercise.solution.replace(/\\n/g, '\n');
            } else {
                editor.value = currentExercise.starterCode.replace(/\\n/g, '\n');
            }
        } else {
            // Default starter code for each language
            if (currentLanguage === 'python') {
                editor.value = '# Python code\nprint("Hello, World!")';
            } else if (currentLanguage === 'shell') {
                editor.value = '#!/bin/bash\n# Bash script\necho "Hello, World!"';
            } else if (currentLanguage === 'html') {
                editor.value = '<!DOCTYPE html>\n<html>\n<head>\n    <title>My Page</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>';
            } else if (currentLanguage === 'css') {
                editor.value = '/* CSS Styles */\nbody {\n    font-family: Arial, sans-serif;\n    background-color: #f0f0f0;\n}\n\nh1 {\n    color: #333;\n}';
            } else {
                editor.value = '// JavaScript code\nconsole.log("Hello, World!");';
            }
        }
    }
    
    addMessage(`Switched to ${currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1)}. Ready to code!`, 'assistant');
}

// Expose to global scope immediately
window.changeLanguage = changeLanguage;

// Helper function to add styled output to terminal
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

// Code execution
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
                addToTerminal(logs.join('\n'), 'output');
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

// Clear code
function clearCode() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        if (currentExercise) {
            editor.value = currentExercise.starterCode.replace(/\\n/g, '\n');
        } else {
            if (currentLanguage === 'python') {
                editor.value = '# Write your Python code here...\nprint("Hello, World!")';
            } else if (currentLanguage === 'shell') {
                editor.value = '#!/bin/bash\n# Write your bash script here...\necho "Hello, World!"';
            } else {
                editor.value = '// Write your JavaScript code here...\nconsole.log("Hello, World!");';
            }
        }
    }
    addToTerminal('Code cleared. Ready to start fresh!', 'output');
}

// Expose to global scope immediately
window.clearCode = clearCode;

// Chat functionality
function addMessage(message, type) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message) {
        addMessage(message, 'user');
        input.value = '';
        
        // Generate contextual AI response based on current exercise
        setTimeout(() => {
            let aiResponse = '';
            
            if (window.currentExerciseContext) {
                const exercise = window.currentExerciseContext;
                aiResponse = `I'm here to help with your current lab: "${exercise.title}" (${exercise.difficulty} level). `;
                
                // Provide contextual response based on the message
                if (message.toLowerCase().includes('help') || message.toLowerCase().includes('stuck')) {
                    aiResponse += `Here are some hints for this ${exercise.difficulty} level exercise:\n\n`;
                    
                    if (exercise.hints && exercise.hints.length > 0) {
                        aiResponse += exercise.hints.map(hint => `• ${hint}`).join('\n');
                    } else {
                        aiResponse += `• Break down the problem into smaller steps\n• Review the exercise instructions carefully\n• Test your code incrementally`;
                    }
                } else if (message.toLowerCase().includes('code') || message.toLowerCase().includes('error')) {
                    aiResponse += `I can help you with your code! Since this is a ${exercise.difficulty} level exercise, `;
                    
                    if (exercise.difficulty === 'beginner') {
                        aiResponse += 'let me provide detailed guidance. Please share your code and I\'ll help you step by step.';
                    } else if (exercise.difficulty === 'intermediate') {
                        aiResponse += 'I can provide targeted guidance. Share your code and describe what you\'re trying to achieve.';
                    } else {
                        aiResponse += 'I can help you debug. Share your code and the error message you\'re seeing.';
                    }
                } else if (message.toLowerCase().includes('what') || message.toLowerCase().includes('how')) {
                    aiResponse += `For this ${exercise.difficulty} level exercise, `;
                    
                    if (exercise.instructions && exercise.instructions.length > 0) {
                        aiResponse += 'here are the key steps:\n\n';
                        aiResponse += exercise.instructions.slice(0, 3).map(instruction => `• ${instruction}`).join('\n');
                    } else {
                        aiResponse += 'focus on the learning objectives and try to apply the concepts step by step.';
                    }
                } else {
                    aiResponse += `I'm ready to help with any questions about this ${exercise.difficulty} level exercise. You can ask me about the requirements, get coding help, or request hints!`;
                }
            } else {
                aiResponse = 'I can help you with that! Can you share your code so I can provide specific feedback?';
            }
            
            addMessage(aiResponse, 'assistant');
        }, 1000);
    }
}

// Expose to global scope immediately
window.sendMessage = sendMessage;

// Terminal Functions
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

function executeTerminalCommand(command) {
    const terminalOutput = document.getElementById('terminalOutput');
    if (!terminalOutput) return;
    
    // Log command execution for security monitoring
    if (isLabSandboxed) {
        logCommandExecution(command);
    }
    
    const promptLine = `student@lab:${currentDirectory.replace(sandboxRoot, '~')}$ ${command}\n`;
    
    terminalOutput.textContent += promptLine;
    
    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    // Security check: validate command is allowed
    if (isLabSandboxed && !isCommandAllowed(cmd)) {
        const output = `Permission denied: Command '${cmd}' is not allowed in this sandboxed environment.\nType 'help' to see available commands.\n`;
        terminalOutput.textContent += output;
        addPrompt();
        scrollToBottom();
        return;
    }
    
    let output = '';
    
    switch (cmd) {
        case 'help':
            output = 'Available commands:\n' +
                   'ls [path]          - List directory contents\n' +
                   'cd <path>          - Change directory\n' +
                   'pwd                - Print working directory\n' +
                   'cat <file>         - Display file contents\n' +
                   'echo <text>        - Display text\n' +
                   'mkdir <dir>        - Create directory\n' +
                   'touch <file>       - Create empty file\n' +
                   'clear              - Clear terminal\n' +
                   'whoami             - Display current user\n' +
                   'date               - Display current date\n' +
                   'help               - Show this help\n';
            break;
        
        case 'ls':
            output = simulateLS(args[0] || currentDirectory);
            break;
        
        case 'pwd':
            output = currentDirectory + '\n';
            break;
        
        case 'cd':
            output = simulateCD(args[0] || sandboxRoot);
            break;
        
        case 'cat':
            output = simulateCAT(args[0]);
            break;
        
        case 'echo':
            output = args.join(' ') + '\n';
            break;
        
        case 'whoami':
            output = 'student\n';
            break;
        
        case 'date':
            output = new Date().toString() + '\n';
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
            output = `bash: ${cmd}: command not found\n`;
            break;
    }
    
    terminalOutput.textContent += output;
    terminalOutput.textContent += `student@lab:${currentDirectory.replace('/home/student', '~')}$ `;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function simulateLS(path) {
    // Simplified file listing
    if (path === '.' || path === currentDirectory || !path) {
        return 'readme.txt  examples/\n';
    } else if (path === 'examples') {
        return 'hello.sh  test.py  sample.js\n';
    } else {
        return `ls: cannot access '${path}': No such file or directory\n`;
    }
}

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
        return accessCheck.message + '\n';
    }
    
    // Check if directory exists in our simulated file system
    if (targetPath === sandboxRoot || 
        targetPath === sandboxRoot + '/examples' ||
        (fileSystem[targetPath] && typeof fileSystem[targetPath] === 'object')) {
        currentDirectory = targetPath;
        return '';
    } else {
        return `bash: cd: ${path}: No such file or directory\n`;
    }
}

function simulateCAT(filename) {
    if (!filename) {
        return 'cat: missing file operand\n';
    }
    
    if (filename === 'readme.txt' && currentDirectory === '/home/student') {
        return 'Welcome to the lab environment!\nThis is a simulated file system.\n';
    } else if (filename === 'hello.sh' && currentDirectory.includes('examples')) {
        return '#!/bin/bash\necho "Hello from the lab!"\n';
    } else {
        return `cat: ${filename}: No such file or directory\n`;
    }
}

function simulateMKDIR(dirname) {
    if (!dirname) {
        return 'mkdir: missing operand\n';
    }
    return `Directory '${dirname}' created (simulated)\n`;
}

function simulateTOUCH(filename) {
    if (!filename) {
        return 'touch: missing file operand\n';
    }
    return `File '${filename}' created (simulated)\n`;
}

// Security and sandboxing functions
function isCommandAllowed(cmd) {
    if (!isLabSandboxed) return true;
    return allowedCommands.includes(cmd);
}

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

function resolvePath(path) {
    if (!path) return currentDirectory;
    
    if (path.startsWith('/')) {
        return path; // Absolute path
    } else {
        // Relative path - resolve relative to current directory
        return currentDirectory + '/' + path;
    }
}

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
    
    console.log('Command logged:', logEntry);
}

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

// Progress tracking functions
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
    
    console.log(`Exercise ${exerciseId} completed!`);
}

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
            console.log('Progress loaded from server');
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

function loadProgressFromLocalStorage() {
    const progressKey = `labProgress_${studentId}_${courseId}`;
    const savedProgress = localStorage.getItem(progressKey);
    
    if (savedProgress) {
        try {
            const progressData = JSON.parse(savedProgress);
            exerciseProgress = progressData.exerciseProgress || {};
            totalLabTime = progressData.totalLabTime || 0;
            console.log('Progress loaded from localStorage');
        } catch (error) {
            console.error('Error parsing saved progress:', error);
        }
    }
}

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
            console.log('Progress saved to server');
        } else {
            console.warn('Failed to save progress to server, using localStorage fallback');
            saveProgressToLocalStorage();
        }
    } catch (error) {
        console.error('Error saving progress to server:', error);
        saveProgressToLocalStorage();
    }
}

function calculateTotalLabTime() {
    if (!labStartTime) return totalLabTime;
    
    const currentTime = new Date();
    const sessionTime = Math.floor((currentTime - labStartTime) / 1000); // in seconds
    return totalLabTime + sessionTime;
}

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
        const codeLines = code.split('\n').filter(line => line.trim().length > 0);
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

function updateProgressDisplay() {
    const summary = getProgressSummary();
    
    // Update any progress indicators in the UI
    const progressElements = document.querySelectorAll('.progress-indicator');
    progressElements.forEach(element => {
        element.textContent = `${summary.completedExercises}/${summary.totalExercises} exercises completed (${summary.progressPercentage}%)`;
    });
    
    // Log progress for debugging
    console.log('Progress updated:', summary);
}

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

function focusTerminalInput() {
    const terminalInput = document.getElementById('terminalInput');
    if (terminalInput) {
        terminalInput.focus();
    }
}

// Expose to global scope immediately
window.focusTerminalInput = focusTerminalInput;

function updatePrompt() {
    const promptSpan = document.querySelector('.terminal-prompt');
    if (promptSpan) {
        promptSpan.textContent = `student@lab:${currentDirectory.replace('/home/student', '~')}$`;
    }
}

function scrollToBottom() {
    const terminalWindow = document.getElementById('terminalWindow');
    if (terminalWindow) {
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }
}

// Auto-focus terminal on load
function initializeTerminal() {
    setTimeout(() => {
        focusTerminalInput();
    }, 100);
}

// Ensure functions are globally available
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

// Test function to force exercise display
window.forceDisplayExercises = function() {
    console.log('Force display exercises called');
    console.log('Current exercises:', exercises);
    displayExercises();
};

// Test function to force exercise panel visibility
window.forceShowExercisePanel = function() {
    console.log('Force show exercise panel called');
    const exercisePanel = document.getElementById('exercisePanel');
    console.log('Exercise panel found:', !!exercisePanel);
    if (exercisePanel) {
        exercisePanel.classList.remove('panel-hidden');
        panelStates.exercises = true;
        console.log('Exercise panel made visible');
        updateLayout();
    }
};

// Initialize after DOM is loaded
function initializeLabAfterDOM() {
    console.log('initializeLabAfterDOM called');
    
    // First, ensure all panels are properly initialized
    panelStates = {
        exercises: true,
        editor: true,
        terminal: true,
        assistant: true
    };
    
    console.log('Panel states initialized:', panelStates);
    
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

// Initialize after load function
window.initializeAfterLoad = function() {
    console.log('initializeAfterLoad called');
    console.log('togglePanel available:', typeof window.togglePanel);
    console.log('DOM ready state:', document.readyState);
    
    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOMContentLoaded event fired');
            initializeLabAfterDOM();
        });
    } else {
        initializeLabAfterDOM();
    }
};

window.initializeLabAfterDOM = initializeLabAfterDOM;
