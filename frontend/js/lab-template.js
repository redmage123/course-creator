// Lab environment JavaScript functions (global scope)
let exercises = [];
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
    panelStates[panelName] = !panelStates[panelName];
    updateLayout();
    updateToggleButtons();
}

function updateLayout() {
    const mainLayout = document.querySelector('.main-layout');
    if (!mainLayout) return;
    
    // Reset all layout classes
    mainLayout.className = 'main-layout';
    
    // Get visible panels
    const visiblePanels = Object.keys(panelStates).filter(panel => panelStates[panel]);
    
    // Update panel visibility
    const exercisePanel = document.getElementById('exercisePanel');
    const editorPanel = document.getElementById('editorPanel');
    const terminalPanel = document.getElementById('terminalPanel');
    const assistantPanel = document.getElementById('assistantPanel');
    
    if (exercisePanel) exercisePanel.classList.toggle('panel-hidden', !panelStates.exercises);
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

// Initialize the lab environment
function initializeLab() {
    console.log('Initializing lab environment...');
    
    // Check if this is a sandboxed environment
    const urlParams = new URLSearchParams(window.location.search);
    isLabSandboxed = urlParams.get('sandboxed') === 'true';
    studentId = urlParams.get('studentId');
    sessionId = urlParams.get('sessionId');
    courseId = urlParams.get('courseId');
    
    // Initialize progress tracking
    initializeProgressTracking();
    
    if (isLabSandboxed) {
        console.log('Lab running in sandboxed mode');
        initializeSandbox();
    }
    
    loadExercises();
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

// Load predefined exercises
function loadExercises() {
    console.log('Loading exercises...');
    exercises = [
        {
            id: 1,
            title: "Personal Information System",
            description: "Create a program that collects and displays user information. Practice with variables, input/output, and string manipulation.",
            difficulty: "easy",
            starterCode: "// Create a personal information system\\n// 1. Create variables for name, age, email, and favorite color\\n// 2. Display a formatted profile\\n// 3. Calculate birth year from age\\n\\n// Your code here:",
            solution: "// Personal Information System\\nconst name = 'John Doe';\\nconst age = 25;\\nconst email = 'john.doe@example.com';\\nconst favoriteColor = 'blue';\\n\\n// Calculate birth year\\nconst currentYear = new Date().getFullYear();\\nconst birthYear = currentYear - age;\\n\\n// Display profile\\nconsole.log('=== Personal Profile ===');\\nconsole.log('Name: ' + name);\\nconsole.log('Age: ' + age + ' years old');\\nconsole.log('Email: ' + email);\\nconsole.log('Favorite Color: ' + favoriteColor);\\nconsole.log('Birth Year: ' + birthYear);\\nconsole.log('Profile created on: ' + new Date().toLocaleDateString());"
        },
        {
            id: 2,
            title: "Grade Calculator with File Output",
            description: "Build a grade calculator that processes student scores and generates a report. Practice with arrays, loops, and file I/O concepts.",
            difficulty: "medium",
            starterCode: "// Grade Calculator System\\n// 1. Create an array of student scores\\n// 2. Calculate average, highest, and lowest scores\\n// 3. Assign letter grades\\n// 4. Generate a summary report\\n\\nconst scores = [85, 92, 78, 96, 88, 74, 90, 83, 91, 87];\\n\\n// Your code here:",
            solution: "// Grade Calculator System\\nconst scores = [85, 92, 78, 96, 88, 74, 90, 83, 91, 87];\\nconst studentNames = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack'];\\n\\n// Calculate statistics\\nconst average = scores.reduce((sum, score) => sum + score, 0) / scores.length;\\nconst highest = Math.max(...scores);\\nconst lowest = Math.min(...scores);\\n\\n// Function to get letter grade\\nfunction getLetterGrade(score) {\\n    if (score >= 90) return 'A';\\n    if (score >= 80) return 'B';\\n    if (score >= 70) return 'C';\\n    if (score >= 60) return 'D';\\n    return 'F';\\n}\\n\\n// Generate report\\nconsole.log('=== CLASS GRADE REPORT ===');\\nconsole.log('Class Average: ' + average.toFixed(2));\\nconsole.log('Highest Score: ' + highest);\\nconsole.log('Lowest Score: ' + lowest);\\nconsole.log('\\\\n=== INDIVIDUAL GRADES ===');\\n\\nfor (let i = 0; i < scores.length; i++) {\\n    const letterGrade = getLetterGrade(scores[i]);\\n    console.log(studentNames[i] + ': ' + scores[i] + ' (' + letterGrade + ')');\\n}\\n\\n// Summary statistics\\nconst gradeDistribution = {};\\nscores.forEach(score => {\\n    const grade = getLetterGrade(score);\\n    gradeDistribution[grade] = (gradeDistribution[grade] || 0) + 1;\\n});\\n\\nconsole.log('\\\\n=== GRADE DISTRIBUTION ===');\\nfor (const grade in gradeDistribution) {\\n    console.log(grade + ': ' + gradeDistribution[grade] + ' students');\\n}"
        },
        {
            id: 3,
            title: "Password Strength Checker",
            description: "Build a password validation system that checks password strength and provides feedback. Practice with functions, conditionals, and string methods.",
            difficulty: "medium",
            starterCode: "// Password Strength Checker\\n// 1. Create a function to check password strength\\n// 2. Check for length, uppercase, lowercase, numbers, special chars\\n// 3. Provide specific feedback for improvements\\n// 4. Rate password as Weak, Medium, or Strong\\n\\nfunction checkPasswordStrength(password) {\\n    // Your code here\\n}\\n\\n// Test with different passwords\\nconst testPasswords = ['123', 'password', 'Password123', 'MyStr0ng!Pass'];\\n\\n// Your testing code here:",
            solution: "// Password Strength Checker\\nfunction checkPasswordStrength(password) {\\n    const criteria = {\\n        length: password.length >= 8,\\n        uppercase: /[A-Z]/.test(password),\\n        lowercase: /[a-z]/.test(password),\\n        numbers: /\\\\d/.test(password),\\n        special: /[!@#$%^&*(),.?\\\":{}|<>]/.test(password)\\n    };\\n    \\n    const score = Object.values(criteria).filter(Boolean).length;\\n    \\n    let strength = 'Weak';\\n    if (score >= 4) strength = 'Strong';\\n    else if (score >= 3) strength = 'Medium';\\n    \\n    return {\\n        strength: strength,\\n        score: score,\\n        criteria: criteria,\\n        feedback: generateFeedback(criteria)\\n    };\\n}\\n\\nfunction generateFeedback(criteria) {\\n    const feedback = [];\\n    if (!criteria.length) feedback.push('Use at least 8 characters');\\n    if (!criteria.uppercase) feedback.push('Add uppercase letters');\\n    if (!criteria.lowercase) feedback.push('Add lowercase letters');\\n    if (!criteria.numbers) feedback.push('Add numbers');\\n    if (!criteria.special) feedback.push('Add special characters');\\n    return feedback;\\n}\\n\\n// Test with different passwords\\nconst testPasswords = ['123', 'password', 'Password123', 'MyStr0ng!Pass'];\\n\\ntestPasswords.forEach(password => {\\n    const result = checkPasswordStrength(password);\\n    console.log('\\\\n=== Password: \"' + password + '\" ===');\\n    console.log('Strength: ' + result.strength + ' (' + result.score + '/5)');\\n    if (result.feedback.length > 0) {\\n        console.log('Improvements needed:');\\n        result.feedback.forEach(tip => console.log('- ' + tip));\\n    } else {\\n        console.log('✓ Password meets all criteria!');\\n    }\\n});"
        }
    ];
    
    console.log('Loaded', exercises.length, 'exercises');
    displayExercises();
}

// Display exercises in the sidebar
function displayExercises() {
    console.log('Displaying exercises...');
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
        console.log('Exercise panel made visible');
    }
    
    exerciseList.innerHTML = exercises.map(exercise => `
        <div class="exercise-item" onclick="selectExercise(${exercise.id})">
            <h4>${exercise.title}</h4>
            <p>${exercise.description}</p>
            <span class="exercise-difficulty difficulty-${exercise.difficulty}">${exercise.difficulty.toUpperCase()}</span>
            <div class="exercise-controls">
                <button class="solution-toggle-btn" onclick="event.stopPropagation(); toggleSolution(${exercise.id})" id="solutionBtn${exercise.id}">
                    👁️ Show Solution
                </button>
            </div>
        </div>
    `).join('');
    
    console.log('Exercises displayed in DOM, count:', exercises.length);
    
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
    event.target.closest('.exercise-item').classList.add('active');
    
    // Load exercise code (always start with starter code)
    const editor = document.getElementById('codeEditor');
    if (editor) {
        editor.value = currentExercise.starterCode.replace(/\\n/g, '\n');
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
    
    // Add message to chat
    addMessage(`Great! You've selected "${currentExercise.title}". ${currentExercise.description} Feel free to ask for hints if you need help!`, 'assistant');
}

// Solution toggle functionality
function toggleSolution(exerciseId) {
    const exercise = exercises.find(ex => ex.id === exerciseId);
    if (!exercise) return;
    
    const editor = document.getElementById('codeEditor');
    const button = document.getElementById('solutionBtn' + exerciseId);
    
    if (!editor || !button) return;
    
    if (showingSolution[exerciseId]) {
        // Hide solution - show starter code
        editor.value = exercise.starterCode.replace(/\\n/g, '\n');
        button.textContent = '👁️ Show Solution';
        button.classList.remove('active');
        showingSolution[exerciseId] = false;
        addToTerminal('Switched back to starter code', 'output');
    } else {
        // Show solution
        editor.value = exercise.solution.replace(/\\n/g, '\n');
        button.textContent = '🚫 Hide Solution';
        button.classList.add('active');
        showingSolution[exerciseId] = true;
        addToTerminal('Showing solution code', 'output');
    }
}

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

// Helper function to add styled output to terminal
function addToTerminal(text, type = 'normal') {
    const terminalOutput = document.getElementById('terminalOutput');
    if (!terminalOutput) return;
    
    const div = document.createElement('div');
    if (type === 'output') {
        div.className = 'code-output';
    } else if (type === 'error') {
        div.className = 'code-error';
    }
    div.textContent = text;
    
    terminalOutput.appendChild(div);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
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
        
        // Simulate AI response
        setTimeout(() => {
            addMessage('I can help you with that! Can you share your code so I can provide specific feedback?', 'assistant');
        }, 1000);
    }
}

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
    const terminalOutput = document.getElementById('terminalOutput');
    if (terminalOutput) {
        terminalOutput.innerHTML = '';
        const prompt = isLabSandboxed 
            ? `Terminal cleared.\nSecure Lab Environment - Session: ${sessionId}\n\nstudent@lab:~$ `
            : 'Terminal cleared.\n\nstudent@lab:~$ ';
        terminalOutput.textContent = prompt;
    }
}

function focusTerminalInput() {
    const terminalInput = document.getElementById('terminalInput');
    if (terminalInput) {
        terminalInput.focus();
    }
}

// Auto-focus terminal on load
function initializeTerminal() {
    setTimeout(() => {
        focusTerminalInput();
    }, 100);
}

// Lab environment HTML template
function generateLabHtml(course, courseId) {
    return `<!DOCTYPE html>
<html>
<head>
    <title>AI Lab Environment - ${course.title}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0; 
            background: #1e1e1e; 
            color: #ffffff; 
            overflow: hidden; 
        }
        
        .lab-container { 
            height: 100vh; 
            display: grid; 
            grid-template-rows: auto auto 1fr; 
        }
        
        .lab-header { 
            background: #2d2d30; 
            padding: 15px 20px; 
            border-bottom: 1px solid #3e3e42; 
        }
        
        .lab-header h1 { 
            color: #ffffff; 
            margin: 0; 
            font-size: 1.5em; 
        }
        
        .lab-header p { 
            color: #cccccc; 
            margin: 5px 0 0 0; 
        }
        
        /* Panel Controls */
        .panel-controls {
            background: #252526;
            padding: 8px 15px;
            border-bottom: 1px solid #3e3e42;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .toggle-btn {
            background: #007acc;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8em;
        }
        
        .toggle-btn:hover { background: #005a9e; }
        .toggle-btn.inactive { background: #555; }
        
        /* Main Layout - Dynamic Grid */
        .main-layout { 
            display: grid;
            height: 100%;
            gap: 2px;
            background: #3e3e42;
        }
        
        /* Exercise Panel */
        .exercise-panel { 
            background: #252526; 
            padding: 15px; 
            overflow-y: auto; 
            min-width: 250px;
        }
        
        .panel-header { 
            font-weight: 600; 
            margin-bottom: 15px; 
            color: #ffffff; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            font-size: 1.1em; 
        }
        
        .exercise-list { 
            display: flex; 
            flex-direction: column; 
            gap: 10px; 
        }
        
        .exercise-item { 
            background: #2d2d30; 
            padding: 12px; 
            border-radius: 6px; 
            border: 1px solid #3e3e42; 
            cursor: pointer; 
            transition: all 0.2s; 
        }
        
        .exercise-item:hover { 
            background: #3d3d40; 
            border-color: #007acc; 
        }
        
        .exercise-item.active { 
            background: #1e4f72; 
            border-color: #007acc; 
        }
        
        .exercise-item h4 { 
            margin: 0 0 8px 0; 
            color: #ffffff; 
            font-size: 0.9em; 
        }
        
        .exercise-item p { 
            margin: 0; 
            color: #cccccc; 
            font-size: 0.8em; 
            line-height: 1.4; 
        }
        
        .exercise-difficulty { 
            display: inline-block; 
            padding: 2px 8px; 
            border-radius: 10px; 
            font-size: 0.7em; 
            margin-top: 5px; 
        }
        
        .difficulty-easy { background: #1a4d1a; color: #ccffcc; }
        .difficulty-medium { background: #4d3d1a; color: #ffffcc; }
        .difficulty-hard { background: #4d1a1a; color: #ffcccc; }
        
        .exercise-controls {
            margin-top: 10px;
            display: flex;
            gap: 5px;
        }
        
        .solution-toggle-btn {
            background: #6f42c1;
            color: white;
            border: none;
            padding: 5px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.7em;
            transition: background 0.2s;
        }
        
        .solution-toggle-btn:hover {
            background: #5a2d91;
        }
        
        .solution-toggle-btn.active {
            background: #dc3545;
        }
        
        .request-lab-btn { 
            background: #6f42c1; 
            color: white; 
            border: none; 
            padding: 10px 15px; 
            border-radius: 6px; 
            cursor: pointer; 
            width: 100%; 
            margin-top: 15px; 
            font-size: 0.9em; 
        }
        
        .request-lab-btn:hover { background: #5a2d91; }
        
        /* Code Editor Panel */
        .editor-panel { 
            background: #1e1e1e; 
            display: flex; 
            flex-direction: column; 
        }
        
        .code-toolbar { 
            background: #2d2d30; 
            padding: 8px 15px; 
            border-bottom: 1px solid #3e3e42; 
            display: flex; 
            gap: 8px; 
            align-items: center; 
            flex-shrink: 0; 
        }
        
        .code-toolbar select,
        .code-toolbar button { 
            padding: 6px 12px; 
            background: #007acc; 
            color: white; 
            border: none; 
            border-radius: 3px; 
            cursor: pointer; 
            font-size: 0.85em; 
        }
        
        .code-toolbar select {
            background: #1e1e1e;
            border: 1px solid #3e3e42;
        }
        
        .code-toolbar button:hover { background: #005a9e; }
        .code-toolbar button.analyze { background: #6f42c1; }
        .code-toolbar button.analyze:hover { background: #5a2d91; }
        
        .code-editor { 
            flex: 1; 
            display: flex; 
            flex-direction: column; 
        }
        
        .code-textarea { 
            flex: 1; 
            width: 100%; 
            background: #1e1e1e; 
            color: #d4d4d4; 
            border: none; 
            padding: 15px; 
            font-family: 'Courier New', monospace; 
            font-size: 14px; 
            resize: none; 
            outline: none; 
            overflow-y: auto;
            line-height: 1.4;
        }
        
        
        /* Terminal Panel */
        .terminal-panel { 
            background: #0c0c0c; 
            display: flex; 
            flex-direction: column; 
            border-top: 2px solid #3e3e42; 
        }
        
        .terminal-header { 
            background: #1e1e1e; 
            padding: 8px 15px; 
            border-bottom: 1px solid #3e3e42; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            flex-shrink: 0;
        }
        
        .terminal-header h4 { 
            margin: 0; 
            color: #ffffff; 
            font-size: 0.9em; 
            display: flex; 
            align-items: center; 
            gap: 6px; 
        }
        
        .terminal-output { 
            flex: 1; 
            padding: 10px; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            color: #00ff00; 
            background: #000000; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            min-height: 200px;
            cursor: text;
        }
        
        .terminal-output:focus-within {
            outline: 2px solid #007acc;
            outline-offset: -2px;
        }
        
        .code-output { 
            color: #ccffcc; 
            background: #1a2a1a; 
            padding: 8px; 
            margin: 4px 0; 
            border-left: 3px solid #00ff00; 
            border-radius: 3px; 
        }
        
        .code-error { 
            color: #ffcccc; 
            background: #2a1a1a; 
            padding: 8px; 
            margin: 4px 0; 
            border-left: 3px solid #ff0000; 
            border-radius: 3px; 
        }
        
        .terminal-input-container { 
            display: flex; 
            align-items: center; 
            padding: 8px 10px; 
            background: #1a1a1a; 
            border-top: 1px solid #3e3e42; 
            flex-shrink: 0;
        }
        
        .terminal-prompt { 
            color: #00ff00; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            margin-right: 8px; 
        }
        
        .terminal-input { 
            flex: 1; 
            background: transparent; 
            border: none; 
            color: #00ff00; 
            font-family: 'Courier New', monospace; 
            font-size: 13px; 
            outline: none; 
        }
        
        .terminal-clear-btn { 
            background: #444; 
            color: white; 
            border: none; 
            padding: 4px 8px; 
            border-radius: 3px; 
            cursor: pointer; 
            font-size: 0.8em; 
            margin-left: 8px; 
        }
        
        .terminal-clear-btn:hover { background: #555; }
        
        /* AI Assistant Panel */
        .assistant-panel { 
            background: #252526; 
            display: flex; 
            flex-direction: column; 
        }
        
        .chat-container { 
            flex: 1; 
            overflow-y: auto; 
            padding: 15px; 
            background: #1e1e1e; 
            margin: 15px; 
            border-radius: 6px; 
            border: 1px solid #3e3e42; 
            min-height: 0; 
        }
        
        .message { 
            margin: 10px 0; 
            padding: 12px; 
            border-radius: 6px; 
            max-width: 90%; 
        }
        
        .assistant-message { 
            background: #0e4f88; 
            border-left: 3px solid #007acc; 
        }
        
        .user-message { 
            background: #1a4d1a; 
            border-left: 3px solid #00aa00; 
            margin-left: auto; 
            text-align: right; 
        }
        
        .system-message { 
            background: #4d3d1a; 
            border-left: 3px solid #ffaa00; 
        }
        
        .input-container { 
            display: flex; 
            gap: 8px; 
            padding: 15px; 
            border-top: 1px solid #3e3e42; 
            flex-shrink: 0;
        }
        
        .input-container input { 
            flex: 1; 
            padding: 10px 12px; 
            border: 1px solid #3e3e42; 
            border-radius: 4px; 
            background: #1e1e1e; 
            color: #ffffff; 
        }
        
        .input-container button { 
            padding: 10px 15px; 
            background: #007acc; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
        }
        
        .input-container button:hover { background: #005a9e; }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1e1e1e; }
        ::-webkit-scrollbar-thumb { background: #3e3e42; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #4e4e52; }
        
        /* Hidden panels */
        .panel-hidden { display: none !important; }
        
        /* Layout configurations */
        .layout-exercises-only { grid-template-columns: 1fr; }
        .layout-exercises-editor { grid-template-columns: 300px 1fr; }
        .layout-exercises-terminal { grid-template-columns: 300px 1fr; }
        .layout-exercises-assistant { grid-template-columns: 300px 1fr; }
        .layout-exercises-editor-assistant { grid-template-columns: 300px 1fr 1fr; }
        .layout-exercises-editor-terminal { grid-template-columns: 300px 1fr; grid-template-rows: 1fr 300px; }
        .layout-exercises-assistant-terminal { grid-template-columns: 300px 1fr; grid-template-rows: 1fr 300px; }
        .layout-all-panels { grid-template-columns: 300px 1fr 1fr; grid-template-rows: 1fr 300px; }
    </style>
</head>
<body>
    <div class="lab-container">
        <div class="lab-header">
            <h1>🧪 AI Lab Environment - ${course.title}</h1>
            <p>Interactive Learning Lab with Customizable Panels</p>
        </div>
        
        <!-- Panel Controls -->
        <div class="panel-controls">
            <span style="color: #cccccc; margin-right: 10px;">Toggle Panels:</span>
            <button class="toggle-btn" id="toggleExercises" onclick="togglePanel('exercises')">📚 Exercises</button>
            <button class="toggle-btn" id="toggleEditor" onclick="togglePanel('editor')">💻 Code Editor</button>
            <button class="toggle-btn" id="toggleTerminal" onclick="togglePanel('terminal')">🖥️ Terminal</button>
            <button class="toggle-btn" id="toggleAssistant" onclick="togglePanel('assistant')">🤖 AI Assistant</button>
        </div>
        
        <div class="main-layout layout-all-panels" id="mainLayout">
            <!-- Exercise Selection Panel -->
            <div class="exercise-panel" id="exercisePanel">
                <div class="panel-header">
                    <span>🎯</span> Exercises
                </div>
                <div class="exercise-list" id="exerciseList">
                    <!-- Exercises will be loaded here -->
                </div>
                <button class="request-lab-btn" onclick="requestCustomLab()">
                    💡 Request Custom Lab
                </button>
            </div>
            
            <!-- Code Editor Panel -->
            <div class="editor-panel" id="editorPanel">
                <div class="code-toolbar">
                    <select id="languageSelect" onchange="changeLanguage()">
                        <option value="javascript">JavaScript</option>
                        <option value="python">Python</option>
                        <option value="shell">Shell/Bash</option>
                        <option value="html">HTML</option>
                        <option value="css">CSS</option>
                    </select>
                    <button onclick="runCode()">▶ Run Code</button>
                    <button onclick="analyzeCode()" class="analyze">🔍 Analyze</button>
                    <button onclick="getHint()">💡 Hint</button>
                    <button onclick="clearEditor()">🗑️ Clear</button>
                </div>
                <div class="code-editor">
                    <textarea class="code-textarea" id="codeEditor" placeholder="// Select an exercise to start coding...
// Or write your own code here!"></textarea>
                </div>
            </div>
            
            <!-- AI Assistant Panel -->
            <div class="assistant-panel" id="assistantPanel">
                <div class="panel-header" style="padding: 15px 15px 0 15px;">
                    <span>🤖</span> AI Assistant
                </div>
                <div class="chat-container" id="chatContainer">
                    <div class="message assistant-message">
                        <strong>🤖 AI Assistant:</strong> Hello! I'm here to help you with your learning journey for <strong>${course.title}</strong>. Select an exercise, ask questions, or request custom labs!
                    </div>
                </div>
                <div class="input-container">
                    <input type="text" id="userInput" placeholder="Ask for help, request custom labs, or get explanations..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <!-- Terminal Panel -->
            <div class="terminal-panel" id="terminalPanel">
                <div class="terminal-header">
                    <h4><span>💻</span> Terminal & Output</h4>
                    <button class="terminal-clear-btn" onclick="clearTerminal()">Clear</button>
                </div>
                <div class="terminal-output" id="terminalOutput" onclick="focusTerminalInput()">Welcome to the Lab Terminal!
This terminal shows both command output and code execution results.
Type commands below to interact with the shell environment.
For help, type 'help' and press Enter.

student@lab:~$ </div>
                <div class="terminal-input-container">
                    <span class="terminal-prompt">student@lab:~$</span>
                    <input type="text" class="terminal-input" id="terminalInput" onkeypress="handleTerminalInput(event)" placeholder="Type your command here..." autocomplete="off">
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentExercise = null;
        let exercises = [];
        let currentLanguage = 'javascript';
        let terminalHistory = [];
        let historyIndex = -1;
        let currentDirectory = '/home/student';
        let panelStates = {
            exercises: true,
            editor: true,
            terminal: true,
            assistant: true
        };
        let fileSystem = {
            '/home/student': {
                'readme.txt': 'Welcome to the lab environment!\\nThis is a simulated file system for learning.\\n\\nAvailable directories:\\n- examples/ (sample scripts)\\n\\nTry: ls, cd examples, cat readme.txt',
                'examples': {
                    'hello.sh': '#!/bin/bash\\necho "Hello, World!"\\necho "This is a bash script example"',
                    'test.py': 'print("Hello from Python!")\\nprint("This is a Python script example")',
                    'sample.js': 'console.log("Hello from JavaScript!");\\nconsole.log("This is a JS example");'
                }
            }
        };
        
        // Initialize the lab environment
        function initializeLab() {
            console.log('Initializing lab environment...');
            loadExercises();
            updateLayout();
            addMessage('Welcome! Toggle panels using the controls above, select exercises, or ask me anything!', 'system');
            console.log('Lab initialization complete');
        }
        
        // Panel management
        function togglePanel(panelName) {
            panelStates[panelName] = !panelStates[panelName];
            updateLayout();
            updateToggleButtons();
        }
        
        function updateToggleButtons() {
            Object.keys(panelStates).forEach(panel => {
                const btn = document.getElementById('toggle' + panel.charAt(0).toUpperCase() + panel.slice(1));
                if (btn) {
                    btn.classList.toggle('inactive', !panelStates[panel]);
                }
            });
        }
        
        function updateLayout() {
            const mainLayout = document.getElementById('mainLayout');
            const exercisePanel = document.getElementById('exercisePanel');
            const editorPanel = document.getElementById('editorPanel');
            const terminalPanel = document.getElementById('terminalPanel');
            const assistantPanel = document.getElementById('assistantPanel');
            
            // Hide/show panels
            exercisePanel.classList.toggle('panel-hidden', !panelStates.exercises);
            editorPanel.classList.toggle('panel-hidden', !panelStates.editor);
            terminalPanel.classList.toggle('panel-hidden', !panelStates.terminal);
            assistantPanel.classList.toggle('panel-hidden', !panelStates.assistant);
            
            // Remove all layout classes
            mainLayout.className = 'main-layout';
            
            // Determine which panels are visible
            const visiblePanels = Object.keys(panelStates).filter(panel => panelStates[panel]);
            
            // Apply appropriate layout class
            if (visiblePanels.length === 1) {
                mainLayout.classList.add('layout-exercises-only');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('editor') && visiblePanels.includes('assistant') && visiblePanels.includes('terminal')) {
                mainLayout.classList.add('layout-all-panels');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('editor') && visiblePanels.includes('assistant')) {
                mainLayout.classList.add('layout-exercises-editor-assistant');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('editor') && visiblePanels.includes('terminal')) {
                mainLayout.classList.add('layout-exercises-editor-terminal');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('assistant') && visiblePanels.includes('terminal')) {
                mainLayout.classList.add('layout-exercises-assistant-terminal');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('editor')) {
                mainLayout.classList.add('layout-exercises-editor');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('terminal')) {
                mainLayout.classList.add('layout-exercises-terminal');
            } else if (visiblePanels.includes('exercises') && visiblePanels.includes('assistant')) {
                mainLayout.classList.add('layout-exercises-assistant');
            } else {
                mainLayout.classList.add('layout-exercises-only');
            }
        }
        
        // Load predefined exercises
        function loadExercises() {
            console.log('Loading exercises...');
            exercises = [
                {
                    id: 1,
                    title: "Personal Information System",
                    description: "Create a program that collects and displays user information. Practice with variables, input/output, and string manipulation.",
                    difficulty: "easy",
                    starterCode: "// Create a personal information system\\n// 1. Create variables for name, age, email, and favorite color\\n// 2. Display a formatted profile\\n// 3. Calculate birth year from age\\n\\n// Your code here:",
                    solution: "// Personal Information System\\nconst name = 'John Doe';\\nconst age = 25;\\nconst email = 'john.doe@example.com';\\nconst favoriteColor = 'blue';\\n\\n// Calculate birth year\\nconst currentYear = new Date().getFullYear();\\nconst birthYear = currentYear - age;\\n\\n// Display profile\\nconsole.log('=== Personal Profile ===');\\nconsole.log('Name: ' + name);\\nconsole.log('Age: ' + age + ' years old');\\nconsole.log('Email: ' + email);\\nconsole.log('Favorite Color: ' + favoriteColor);\\nconsole.log('Birth Year: ' + birthYear);\\nconsole.log('Profile created on: ' + new Date().toLocaleDateString());"
                },
                {
                    id: 2,
                    title: "Grade Calculator with File Output",
                    description: "Build a grade calculator that processes student scores and generates a report. Practice with arrays, loops, and file I/O concepts.",
                    difficulty: "medium",
                    starterCode: "// Grade Calculator System\\n// 1. Create an array of student scores\\n// 2. Calculate average, highest, and lowest scores\\n// 3. Assign letter grades\\n// 4. Generate a summary report\\n\\nconst scores = [85, 92, 78, 96, 88, 74, 90, 83, 91, 87];\\n\\n// Your code here:",
                    solution: "// Grade Calculator System\\nconst scores = [85, 92, 78, 96, 88, 74, 90, 83, 91, 87];\\nconst studentNames = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack'];\\n\\n// Calculate statistics\\nconst average = scores.reduce((sum, score) => sum + score, 0) / scores.length;\\nconst highest = Math.max(...scores);\\nconst lowest = Math.min(...scores);\\n\\n// Function to get letter grade\\nfunction getLetterGrade(score) {\\n    if (score >= 90) return 'A';\\n    if (score >= 80) return 'B';\\n    if (score >= 70) return 'C';\\n    if (score >= 60) return 'D';\\n    return 'F';\\n}\\n\\n// Generate report\\nconsole.log('=== CLASS GRADE REPORT ===');\\nconsole.log('Class Average: ' + average.toFixed(2));\\nconsole.log('Highest Score: ' + highest);\\nconsole.log('Lowest Score: ' + lowest);\\nconsole.log('\\\\n=== INDIVIDUAL GRADES ===');\\n\\nfor (let i = 0; i < scores.length; i++) {\\n    const letterGrade = getLetterGrade(scores[i]);\\n    console.log(studentNames[i] + ': ' + scores[i] + ' (' + letterGrade + ')');\\n}\\n\\n// Summary statistics\\nconst gradeDistribution = {};\\nscores.forEach(score => {\\n    const grade = getLetterGrade(score);\\n    gradeDistribution[grade] = (gradeDistribution[grade] || 0) + 1;\\n});\\n\\nconsole.log('\\\\n=== GRADE DISTRIBUTION ===');\\nfor (const grade in gradeDistribution) {\\n    console.log(grade + ': ' + gradeDistribution[grade] + ' students');\\n}"
                },
                {
                    id: 3,
                    title: "Password Strength Checker",
                    description: "Build a password validation system that checks password strength and provides feedback. Practice with functions, conditionals, and string methods.",
                    difficulty: "medium",
                    starterCode: "// Password Strength Checker\\n// 1. Create a function to check password strength\\n// 2. Check for length, uppercase, lowercase, numbers, special chars\\n// 3. Provide specific feedback for improvements\\n// 4. Rate password as Weak, Medium, or Strong\\n\\nfunction checkPasswordStrength(password) {\\n    // Your code here\\n}\\n\\n// Test with different passwords\\nconst testPasswords = ['123', 'password', 'Password123', 'MyStr0ng!Pass'];\\n\\n// Your testing code here:",
                    solution: "// Password Strength Checker\\nfunction checkPasswordStrength(password) {\\n    const criteria = {\\n        length: password.length >= 8,\\n        uppercase: /[A-Z]/.test(password),\\n        lowercase: /[a-z]/.test(password),\\n        numbers: /\\\\d/.test(password),\\n        special: /[!@#$%^&*(),.?\\\":{}|<>]/.test(password)\\n    };\\n    \\n    const score = Object.values(criteria).filter(Boolean).length;\\n    \\n    let strength = 'Weak';\\n    if (score >= 4) strength = 'Strong';\\n    else if (score >= 3) strength = 'Medium';\\n    \\n    return {\\n        strength: strength,\\n        score: score,\\n        criteria: criteria,\\n        feedback: generateFeedback(criteria)\\n    };\\n}\\n\\nfunction generateFeedback(criteria) {\\n    const feedback = [];\\n    if (!criteria.length) feedback.push('Use at least 8 characters');\\n    if (!criteria.uppercase) feedback.push('Add uppercase letters');\\n    if (!criteria.lowercase) feedback.push('Add lowercase letters');\\n    if (!criteria.numbers) feedback.push('Add numbers');\\n    if (!criteria.special) feedback.push('Add special characters');\\n    return feedback;\\n}\\n\\n// Test with different passwords\\nconst testPasswords = ['123', 'password', 'Password123', 'MyStr0ng!Pass'];\\n\\ntestPasswords.forEach(password => {\\n    const result = checkPasswordStrength(password);\\n    console.log('\\\\n=== Password: \"' + password + '\" ===');\\n    console.log('Strength: ' + result.strength + ' (' + result.score + '/5)');\\n    if (result.feedback.length > 0) {\\n        console.log('Improvements needed:');\\n        result.feedback.forEach(tip => console.log('- ' + tip));\\n    } else {\\n        console.log('✓ Password meets all criteria!');\\n    }\\n});"
                },
                {
                    id: 4,
                    title: "Loops & Arrays",
                    description: "Use loops to iterate through arrays and process data.",
                    difficulty: "medium",
                    starterCode: "// Create an array of numbers and find the sum\\nlet numbers = [1, 2, 3, 4, 5];\\nlet sum = 0;\\n\\n// Use a loop to calculate the sum\\n\\nconsole.log('Sum:', sum);",
                    solution: "let numbers = [1, 2, 3, 4, 5];\\nlet sum = 0;\\n\\nfor (let i = 0; i < numbers.length; i++) {\\n    sum += numbers[i];\\n}\\n\\nconsole.log('Sum:', sum);"
                },
                {
                    id: 5,
                    title: "Object Manipulation",
                    description: "Work with JavaScript objects and their properties.",
                    difficulty: "hard",
                    starterCode: "// Create a person object with methods\\nlet person = {\\n    name: 'Alice',\\n    age: 30,\\n    // Add a greet method here\\n};\\n\\n// Test the object\\nconsole.log(person.greet());",
                    solution: "let person = {\\n    name: 'Alice',\\n    age: 30,\\n    greet: function() {\\n        return 'Hello, I\\'m ' + this.name + ' and I\\'m ' + this.age + ' years old.';\\n    }\\n};\\n\\nconsole.log(person.greet());"
                },
                {
                    id: 6,
                    title: "Terminal Basics",
                    description: "Learn basic terminal commands using the shell below.",
                    difficulty: "easy",
                    starterCode: "# Try these commands in the terminal below:\\n# ls - list files\\n# pwd - print working directory\\n# cd examples - change to examples directory\\n# cat readme.txt - display file contents\\n# help - show all available commands",
                    solution: "# These are terminal commands, use the shell below!"
                },
                {
                    id: 7,
                    title: "File System Navigation",
                    description: "Practice navigating directories and managing files.",
                    difficulty: "medium",
                    starterCode: "# Exercise: Navigate the file system\\n# 1. List the current directory contents\\n# 2. Change to the examples directory\\n# 3. List the files in examples\\n# 4. Display the contents of hello.sh\\n# 5. Go back to the home directory",
                    solution: "# Use these commands in terminal:\\n# ls\\n# cd examples\\n# ls\\n# cat hello.sh\\n# cd .."
                },
                {
                    id: 8,
                    title: "Creating Files and Directories",
                    description: "Learn to create and organize files using terminal commands.",
                    difficulty: "medium", 
                    starterCode: "# Exercise: Create and organize files\\n# 1. Create a new directory called 'myproject'\\n# 2. Change into that directory\\n# 3. Create a file called 'notes.txt'\\n# 4. Use echo to add some text to it\\n# 5. List the directory contents",
                    solution: "# Use these commands in terminal:\\n# mkdir myproject\\n# cd myproject\\n# touch notes.txt\\n# echo 'My first note' > notes.txt\\n# ls"
                },
                {
                    id: 9,
                    title: "Python File I/O System",
                    description: "Build a file management system using Python. Practice file reading, writing, and data processing.",
                    difficulty: "medium",
                    starterCode: "# Python File I/O System\\n# 1. Create a function to write student data to a file\\n# 2. Read and display the data from the file\\n# 3. Add search functionality\\n# 4. Handle file errors gracefully\\n\\n# Student data\\nstudents = [\\n    {'name': 'Alice', 'age': 20, 'grade': 'A'},\\n    {'name': 'Bob', 'age': 21, 'grade': 'B'},\\n    {'name': 'Charlie', 'age': 19, 'grade': 'A'}\\n]\\n\\n# Your code here:",
                    solution: "# Python File I/O System\\nimport json\\n\\nstudents = [\\n    {'name': 'Alice', 'age': 20, 'grade': 'A'},\\n    {'name': 'Bob', 'age': 21, 'grade': 'B'},\\n    {'name': 'Charlie', 'age': 19, 'grade': 'A'}\\n]\\n\\ndef save_students_to_file(student_list, filename='students.json'):\\n    '''Save student data to a JSON file'''\\n    try:\\n        with open(filename, 'w') as file:\\n            json.dump(student_list, file, indent=2)\\n        print(f'Successfully saved {len(student_list)} students to {filename}')\\n    except Exception as e:\\n        print(f'Error saving to file: {e}')\\n\\ndef load_students_from_file(filename='students.json'):\\n    '''Load student data from a JSON file'''\\n    try:\\n        with open(filename, 'r') as file:\\n            data = json.load(file)\\n        print(f'Successfully loaded {len(data)} students from {filename}')\\n        return data\\n    except FileNotFoundError:\\n        print(f'File {filename} not found')\\n        return []\\n    except Exception as e:\\n        print(f'Error loading from file: {e}')\\n        return []\\n\\ndef display_students(student_list):\\n    '''Display all students in a formatted way'''\\n    if not student_list:\\n        print('No students to display')\\n        return\\n    \\n    print('\\\\n=== STUDENT RECORDS ===')\\n    for i, student in enumerate(student_list, 1):\\n        print(f'{i}. {student[\"name\"]} - Age: {student[\"age\"]}, Grade: {student[\"grade\"]}')\\n\\ndef search_student(student_list, name):\\n    '''Search for a student by name'''\\n    for student in student_list:\\n        if student['name'].lower() == name.lower():\\n            return student\\n    return None\\n\\n# Main program\\nprint('=== Python File I/O System ===')\\n\\n# Save students to file\\nsave_students_to_file(students)\\n\\n# Load students from file\\nloaded_students = load_students_from_file()\\n\\n# Display all students\\ndisplay_students(loaded_students)\\n\\n# Search for a specific student\\nsearch_name = 'Alice'\\nfound_student = search_student(loaded_students, search_name)\\nif found_student:\\n    print(f'\\\\nFound student: {found_student[\"name\"]} - Age: {found_student[\"age\"]}, Grade: {found_student[\"grade\"]}')\\nelse:\\n    print(f'\\\\nStudent \"{search_name}\" not found')\\n\\n# Add a new student\\nnew_student = {'name': 'Diana', 'age': 22, 'grade': 'B+'}\\nloaded_students.append(new_student)\\nprint(f'\\\\nAdded new student: {new_student[\"name\"]}')\\n\\n# Save updated list\\nsave_students_to_file(loaded_students)\\n\\nprint('\\\\n=== System Demo Complete ===')"
                },
                {
                    id: 10,
                    title: "Python Data Analysis Tool",
                    description: "Create a data analysis tool that processes CSV-like data. Practice with file I/O, data structures, and calculations.",
                    difficulty: "hard",
                    starterCode: "# Python Data Analysis Tool\\n# 1. Create sample sales data\\n# 2. Save data to a text file\\n# 3. Read and analyze the data\\n# 4. Generate reports and statistics\\n\\n# Sample sales data\\nsales_data = [\\n    'Date,Product,Quantity,Price',\\n    '2024-01-15,Laptop,2,999.99',\\n    '2024-01-16,Mouse,5,29.99',\\n    '2024-01-17,Keyboard,3,79.99',\\n    '2024-01-18,Monitor,1,299.99',\\n    '2024-01-19,Laptop,1,999.99'\\n]\\n\\n# Your code here:",
                    solution: "# Python Data Analysis Tool\\nimport csv\\nfrom datetime import datetime\\n\\nsales_data = [\\n    'Date,Product,Quantity,Price',\\n    '2024-01-15,Laptop,2,999.99',\\n    '2024-01-16,Mouse,5,29.99',\\n    '2024-01-17,Keyboard,3,79.99',\\n    '2024-01-18,Monitor,1,299.99',\\n    '2024-01-19,Laptop,1,999.99'\\n]\\n\\ndef save_sales_data(data, filename='sales_data.csv'):\\n    '''Save sales data to a CSV file'''\\n    try:\\n        with open(filename, 'w', newline='') as file:\\n            for line in data:\\n                file.write(line + '\\\\n')\\n        print('Sales data saved to', filename)\\n    except Exception as e:\\n        print('Error saving data:', e)\\n\\ndef load_and_analyze_sales(filename='sales_data.csv'):\\n    '''Load and analyze sales data from CSV file'''\\n    try:\\n        with open(filename, 'r') as file:\\n            reader = csv.DictReader(file)\\n            sales_records = list(reader)\\n        \\n        if not sales_records:\\n            print('No sales data found')\\n            return\\n        \\n        print('=== SALES DATA ANALYSIS ===')\\n        print('Total Records:', len(sales_records))\\n        \\n        # Calculate total revenue\\n        total_revenue = 0\\n        product_sales = {}\\n        \\n        for record in sales_records:\\n            quantity = int(record['Quantity'])\\n            price = float(record['Price'])\\n            revenue = quantity * price\\n            total_revenue += revenue\\n            \\n            product = record['Product']\\n            if product in product_sales:\\n                product_sales[product]['quantity'] += quantity\\n                product_sales[product]['revenue'] += revenue\\n            else:\\n                product_sales[product] = {'quantity': quantity, 'revenue': revenue}\\n        \\n        print('Total Revenue: $' + str(round(total_revenue, 2)))\\n        print('\\\\n=== PRODUCT BREAKDOWN ===')\\n        \\n        for product, data in product_sales.items():\\n            print(product + ':', data['quantity'], 'units, $' + str(round(data['revenue'], 2)) + ' revenue')\\n        \\n        # Find best-selling product\\n        best_product = max(product_sales.keys(), key=lambda x: product_sales[x]['quantity'])\\n        print('\\\\nBest-selling product:', best_product, '(' + str(product_sales[best_product]['quantity']) + ' units)')\\n        \\n        return sales_records\\n    \\n    except FileNotFoundError:\\n        print('File', filename, 'not found')\\n    except Exception as e:\\n        print('Error analyzing data:', e)\\n\\ndef generate_daily_report(sales_records):\\n    '''Generate a daily sales report'''\\n    if not sales_records:\\n        return\\n    \\n    daily_sales = {}\\n    \\n    for record in sales_records:\\n        date = record['Date']\\n        quantity = int(record['Quantity'])\\n        price = float(record['Price'])\\n        revenue = quantity * price\\n        \\n        if date in daily_sales:\\n            daily_sales[date] += revenue\\n        else:\\n            daily_sales[date] = revenue\\n    \\n    print('\\\\n=== DAILY SALES REPORT ===')\\n    for date, revenue in sorted(daily_sales.items()):\\n        print(date + ': $' + str(round(revenue, 2)))\\n\\n# Main program\\nprint('=== Python Data Analysis Tool ===')\\n\\n# Save sample data\\nsave_sales_data(sales_data)\\n\\n# Load and analyze data\\nsales_records = load_and_analyze_sales()\\n\\n# Generate daily report\\nif sales_records:\\n    generate_daily_report(sales_records)\\n\\nprint('\\\\n=== Analysis Complete ===')"
                }
            ];
            
            console.log('Loaded', exercises.length, 'exercises');
            displayExercises();
        }
        
        // Display exercises in the sidebar
        function displayExercises() {
            console.log('Displaying exercises...');
            const exerciseList = document.getElementById('exerciseList');
            if (!exerciseList) {
                console.error('Exercise list element not found!');
                return;
            }
            exerciseList.innerHTML = exercises.map(exercise => \`
                <div class="exercise-item" onclick="selectExercise(\${exercise.id})">
                    <h4>\${exercise.title}</h4>
                    <p>\${exercise.description}</p>
                    <span class="exercise-difficulty difficulty-\${exercise.difficulty}">\${exercise.difficulty.toUpperCase()}</span>
                    <div class="exercise-controls">
                        <button class="solution-toggle-btn" onclick="event.stopPropagation(); toggleSolution(\${exercise.id})" id="solutionBtn\${exercise.id}">
                            👁️ Show Solution
                        </button>
                    </div>
                </div>
            \`).join('');
            console.log('Exercises displayed in DOM');
        }
        
        // Solution toggle functionality
        let showingSolution = {};
        
        function toggleSolution(exerciseId) {
            const exercise = exercises.find(ex => ex.id === exerciseId);
            if (!exercise) return;
            
            const editor = document.getElementById('codeEditor');
            const button = document.getElementById('solutionBtn' + exerciseId);
            
            if (!editor || !button) return;
            
            if (showingSolution[exerciseId]) {
                // Hide solution - show starter code
                editor.value = exercise.starterCode;
                button.textContent = '👁️ Show Solution';
                button.classList.remove('active');
                showingSolution[exerciseId] = false;
                addToTerminal('Switched back to starter code', 'output');
            } else {
                // Show solution
                editor.value = exercise.solution;
                button.textContent = '🚫 Hide Solution';
                button.classList.add('active');
                showingSolution[exerciseId] = true;
                addToTerminal('Showing solution code', 'output');
            }
        }
        
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
                        editor.value = currentExercise.solution;
                    } else {
                        editor.value = currentExercise.starterCode;
                    }
                } else {
                    // Default starter code for each language
                    if (currentLanguage === 'python') {
                        editor.value = '# Python code\\nprint("Hello, World!")';
                    } else if (currentLanguage === 'shell') {
                        editor.value = '#!/bin/bash\\n# Bash script\\necho "Hello, World!"';
                    } else if (currentLanguage === 'html') {
                        editor.value = '<!DOCTYPE html>\\n<html>\\n<head>\\n    <title>My Page</title>\\n</head>\\n<body>\\n    <h1>Hello, World!</h1>\\n</body>\\n</html>';
                    } else if (currentLanguage === 'css') {
                        editor.value = '/* CSS Styles */\\nbody {\\n    font-family: Arial, sans-serif;\\n    background-color: #f0f0f0;\\n}\\n\\nh1 {\\n    color: #333;\\n}';
                    } else {
                        editor.value = '// JavaScript code\\nconsole.log("Hello, World!");';
                    }
                }
            }
            
            addMessage(\`Switched to \${currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1)}. Ready to code!\`, 'assistant');
        }
        
        // Select an exercise
        function selectExercise(exerciseId) {
            currentExercise = exercises.find(ex => ex.id === exerciseId);
            if (currentExercise) {
                // Update UI
                document.querySelectorAll('.exercise-item').forEach(item => item.classList.remove('active'));
                event.target.closest('.exercise-item').classList.add('active');
                
                // Load exercise code (always start with starter code)
                const editor = document.getElementById('codeEditor');
                if (editor) {
                    editor.value = currentExercise.starterCode;
                    // Reset solution toggle state
                    showingSolution[exerciseId] = false;
                    const button = document.getElementById('solutionBtn' + exerciseId);
                    if (button) {
                        button.textContent = '👁️ Show Solution';
                        button.classList.remove('active');
                    }
                }
                
                // Update terminal with exercise info
                addToTerminal(\`Exercise loaded: \${currentExercise.title}\\nRun your code to see the output.\`, 'output');
                
                // Add message to chat
                addMessage(\`Great! You've selected "\${currentExercise.title}". \${currentExercise.description} Feel free to ask for hints if you need help!\`, 'assistant');
            }
        }
        
        // Request custom lab
        function requestCustomLab() {
            const topic = prompt('What topic would you like to practice? (e.g., "async/await", "DOM manipulation", "algorithms")');
            if (topic) {
                addMessage(\`I'd like to practice: \${topic}\`, 'user');
                generateCustomLab(topic);
            }
        }
        
        // Generate custom lab (simulated)
        function generateCustomLab(topic) {
            setTimeout(() => {
                const customLab = {
                    id: Date.now(),
                    title: \`Custom Lab: \${topic}\`,
                    description: \`Practice exercise focused on \${topic}\`,
                    difficulty: "medium",
                    starterCode: \`// Custom lab for: \${topic}\\n// TODO: Implement your solution here\\n\\nconsole.log('Starting \${topic} practice...');\`,
                    solution: "// Custom solution would be generated here"
                };
                
                exercises.push(customLab);
                displayExercises();
                selectExercise(customLab.id);
                
                addMessage(\`I've created a custom lab for "\${topic}"! Check the exercise panel on the left. This is a starter template - let me know if you'd like specific challenges or examples for this topic.\`, 'assistant');
            }, 1000);
        }
        
        // Helper function to add styled output to terminal
        function addToTerminal(text, type = 'normal') {
            const terminalOutput = document.getElementById('terminalOutput');
            if (!terminalOutput) return;
            
            const div = document.createElement('div');
            if (type === 'output') {
                div.className = 'code-output';
            } else if (type === 'error') {
                div.className = 'code-error';
            }
            div.textContent = text;
            
            terminalOutput.appendChild(div);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
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
                        addToTerminal(logs.join('\\n'), 'output');
                    } else {
                        addToTerminal('Code executed successfully (no console output)', 'output');
                    }
                } else {
                    // For other languages, show simulation message
                    addToTerminal(\`\${currentLanguage.charAt(0).toUpperCase() + currentLanguage.slice(1)} code simulation:\`, 'output');
                    addToTerminal(code, 'output');
                    addToTerminal('(Note: Actual execution requires server-side processing)', 'output');
                }
                
                // Add success message to chat
                addMessage('Great! Your code ran successfully. Check the terminal for the output!', 'assistant');
                
            } catch (error) {
                addToTerminal('Error: ' + error.message, 'error');
                
                // Add error help to chat
                addMessage(\`I see there's an error: "\${error.message}". Would you like me to help you fix it?\`, 'assistant');
            }
        }
        
        // Code analysis
        function analyzeCode() {
            const editor = document.getElementById('codeEditor');
            if (!editor) {
                addMessage('Code editor not available. Enable it using the panel controls above.', 'assistant');
                return;
            }
            
            const code = editor.value;
            if (!code.trim()) {
                addMessage('Please write some code first, then I can analyze it for you!', 'assistant');
                return;
            }
            
            addMessage('Let me analyze your code...', 'assistant');
            
            setTimeout(() => {
                // Simple code analysis
                let analysis = 'Code Analysis:\\n';
                
                if (code.includes('console.log')) {
                    analysis += '✅ Good use of console.log for output\\n';
                }
                if (code.includes('function')) {
                    analysis += '✅ Using functions - great for code organization\\n';
                }
                if (code.includes('let ') || code.includes('const ')) {
                    analysis += '✅ Using modern variable declarations\\n';
                }
                if (code.includes('//')) {
                    analysis += '✅ Code comments found - good documentation practice\\n';
                }
                
                analysis += '\\nSuggestions: Consider adding error handling and more descriptive variable names.';
                
                addMessage(analysis, 'assistant');
            }, 1000);
        }
        
        // Get hint
        function getHint() {
            if (!currentExercise) {
                addMessage('Select an exercise first, then I can give you specific hints!', 'assistant');
                return;
            }
            
            const hints = {
                1: "Try using console.log() with the text in quotes!",
                2: "Remember: strings use quotes, numbers don't, and booleans are true/false",
                3: "Functions should 'return' a value. Use the return keyword!",
                4: "Use a for loop: for(let i = 0; i < array.length; i++) { ... }",
                5: "Object methods are functions inside objects. Use 'this' to refer to the object's properties.",
                6: "Use the terminal below to practice these commands!",
                7: "Navigate step by step using the terminal commands shown in the code editor.",
                8: "Create directories with mkdir and files with touch. Use echo to add content."
            };
            
            const hint = hints[currentExercise.id] || "Break down the problem into smaller steps and tackle each one at a time!";
            addMessage(\`💡 Hint: \${hint}\`, 'assistant');
        }
        
        // Clear editor
        function clearEditor() {
            const editor = document.getElementById('codeEditor');
            if (!editor) {
                addMessage('Code editor not available. Enable it using the panel controls above.', 'assistant');
                return;
            }
            
            if (currentExercise) {
                editor.value = currentExercise.starterCode;
            } else {
                if (currentLanguage === 'python') {
                    editor.value = '# Write your Python code here...\\nprint("Hello, World!")';
                } else if (currentLanguage === 'shell') {
                    editor.value = '#!/bin/bash\\n# Write your bash script here...\\necho "Hello, World!"';
                } else {
                    editor.value = '// Write your JavaScript code here...\\nconsole.log("Hello, World!");';
                }
            }
            addToTerminal('Code cleared. Ready to start fresh!', 'output');
        }
        
        // Chat functionality
        function addMessage(message, type) {
            const chatContainer = document.getElementById('chatContainer');
            if (!chatContainer) return;
            
            const messageDiv = document.createElement('div');
            
            let className, prefix;
            switch(type) {
                case 'user':
                    className = 'user-message';
                    prefix = '👤 You:';
                    break;
                case 'assistant':
                    className = 'assistant-message';
                    prefix = '🤖 AI Assistant:';
                    break;
                case 'system':
                    className = 'system-message';
                    prefix = '⚙️ System:';
                    break;
                default:
                    className = 'assistant-message';
                    prefix = '🤖 AI Assistant:';
            }
            
            messageDiv.className = \`message \${className}\`;
            messageDiv.innerHTML = \`<strong>\${prefix}</strong> \${message}\`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            if (!input) return;
            
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            // Simulate AI response
            setTimeout(() => {
                let response = "I understand you're asking about that. ";
                
                if (message.toLowerCase().includes('help')) {
                    response = "I'm here to help! You can ask me about coding concepts, request hints for exercises, or ask me to create custom labs on specific topics.";
                } else if (message.toLowerCase().includes('hint')) {
                    getHint();
                    return;
                } else if (message.toLowerCase().includes('lab') || message.toLowerCase().includes('exercise')) {
                    response = "I can create custom labs for you! Just tell me what topic you want to practice, like 'arrays', 'functions', 'DOM manipulation', etc.";
                } else if (message.toLowerCase().includes('error')) {
                    response = "I see you're having trouble with errors. Make sure to check your syntax, variable names, and that all brackets/parentheses are closed properly.";
                } else if (message.toLowerCase().includes('panel')) {
                    response = "You can toggle panels using the buttons at the top! Hide panels you don't need and show only what's relevant for your current learning goals.";
                } else {
                    response = "That's an interesting question! Can you be more specific about what you'd like help with? I can assist with coding concepts, debugging, or creating practice exercises.";
                }
                
                addMessage(response, 'assistant');
            }, 800);
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
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
            
            const promptLine = \`student@lab:\${currentDirectory.replace('/home/student', '~')}\$ \${command}\\n\`;
            
            terminalOutput.textContent += promptLine;
            
            const parts = command.split(' ');
            const cmd = parts[0];
            const args = parts.slice(1);
            
            let output = '';
            
            switch (cmd) {
                case 'help':
                    output = 'Available commands:\\n' +
                           'ls [path]          - List directory contents\\n' +
                           'cd <path>          - Change directory\\n' +
                           'pwd                - Print working directory\\n' +
                           'cat <file>         - Display file contents\\n' +
                           'echo <text>        - Display text\\n' +
                           'mkdir <dir>        - Create directory\\n' +
                           'touch <file>       - Create empty file\\n' +
                           'clear              - Clear terminal\\n' +
                           'whoami             - Display current user\\n' +
                           'date               - Display current date\\n' +
                           'help               - Show this help message\\n';
                    break;
                
                case 'ls':
                    output = simulateLS(args[0] || currentDirectory);
                    break;
                
                case 'pwd':
                    output = currentDirectory + '\\n';
                    break;
                
                case 'cd':
                    output = simulateCD(args[0] || '/home/student');
                    break;
                
                case 'cat':
                    output = simulateCAT(args[0]);
                    break;
                
                case 'echo':
                    output = args.join(' ') + '\\n';
                    break;
                
                case 'whoami':
                    output = 'student\\n';
                    break;
                
                case 'date':
                    output = new Date().toString() + '\\n';
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
                    output = \`bash: \${cmd}: command not found\\n\`;
                    break;
            }
            
            terminalOutput.textContent += output;
            terminalOutput.textContent += \`student@lab:\${currentDirectory.replace('/home/student', '~')}\$ \`;
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
        
        function simulateLS(path) {
            const targetPath = path || currentDirectory;
            const dirContent = getDirectoryContent(targetPath);
            
            if (dirContent === null) {
                return \`ls: cannot access '\${path}': No such file or directory\\n\`;
            }
            
            const items = Object.keys(dirContent);
            if (items.length === 0) {
                return '';
            }
            
            return items.join('  ') + '\\n';
        }
        
        function simulateCD(path) {
            if (path === '..') {
                const parts = currentDirectory.split('/');
                if (parts.length > 2) {
                    parts.pop();
                    currentDirectory = parts.join('/');
                }
                return '';
            }
            
            if (path.startsWith('/')) {
                if (getDirectoryContent(path) !== null) {
                    currentDirectory = path;
                    return '';
                } else {
                    return \`cd: no such file or directory: \${path}\\n\`;
                }
            } else {
                const newPath = currentDirectory + '/' + path;
                if (getDirectoryContent(newPath) !== null) {
                    currentDirectory = newPath;
                    return '';
                } else {
                    return \`cd: no such file or directory: \${path}\\n\`;
                }
            }
        }
        
        function simulateCAT(filename) {
            if (!filename) {
                return 'cat: missing file operand\\n';
            }
            
            const dirContent = getDirectoryContent(currentDirectory);
            
            if (dirContent && dirContent[filename] && typeof dirContent[filename] === 'string') {
                return dirContent[filename] + '\\n';
            } else {
                return \`cat: \${filename}: No such file or directory\\n\`;
            }
        }
        
        function simulateMKDIR(dirname) {
            if (!dirname) {
                return 'mkdir: missing operand\\n';
            }
            
            const dirContent = getDirectoryContent(currentDirectory);
            if (dirContent && !dirContent[dirname]) {
                dirContent[dirname] = {};
                return '';
            } else {
                return \`mkdir: cannot create directory '\${dirname}': File exists\\n\`;
            }
        }
        
        function simulateTOUCH(filename) {
            if (!filename) {
                return 'touch: missing file operand\\n';
            }
            
            const dirContent = getDirectoryContent(currentDirectory);
            if (dirContent && !dirContent[filename]) {
                dirContent[filename] = '';
                return '';
            }
            return '';
        }
        
        function getDirectoryContent(path) {
            const parts = path.split('/').filter(p => p);
            let current = fileSystem;
            
            for (const part of parts) {
                if (current[part] && typeof current[part] === 'object') {
                    current = current[part];
                } else {
                    return null;
                }
            }
            
            return current;
        }
        
        function clearTerminal() {
            const terminalOutput = document.getElementById('terminalOutput');
            if (terminalOutput) {
                terminalOutput.innerHTML = '';
                terminalOutput.textContent = 'Terminal cleared.\\n\\nstudent@lab:~\$ ';
            }
        }
        
        function focusTerminalInput() {
            const terminalInput = document.getElementById('terminalInput');
            if (terminalInput) {
                terminalInput.focus();
            }
        }
        
        // Auto-focus terminal on load
        function initializeTerminal() {
            setTimeout(() => {
                focusTerminalInput();
            }, 100);
        }
        
        // Initialize everything when the page loads
        window.onload = function() {
            initializeLab();
            updateToggleButtons();
            initializeTerminal();
        };
    </script>
</body>
</html>`;
}

// Make the function available globally
window.generateLabHtml = generateLabHtml;
console.log('Lab template loaded, generateLabHtml function available:', typeof window.generateLabHtml);