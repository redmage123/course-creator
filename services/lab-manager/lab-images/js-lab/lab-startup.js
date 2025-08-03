#!/usr/bin/env node
/**
 * JavaScript Lab Startup Script
 * Configures and starts the lab environment based on session parameters
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const express = require('express');

function setupLabEnvironment() {
    console.log('Setting up JavaScript lab environment...');
    
    // Get lab configuration from environment
    const sessionId = process.env.LAB_SESSION_ID || 'default';
    const userId = process.env.USER_ID || 'student';
    const courseId = process.env.COURSE_ID || 'default-course';
    const labConfig = JSON.parse(process.env.LAB_CONFIG || '{}');
    
    console.log(`Session: ${sessionId}, User: ${userId}, Course: ${courseId}`);
    
    const workspace = '/home/labuser/workspace';
    
    // Create session info file
    const sessionInfo = {
        session_id: sessionId,
        user_id: userId,
        course_id: courseId,
        lab_type: 'javascript',
        config: labConfig
    };
    
    fs.writeFileSync(
        path.join(workspace, 'session_info.json'),
        JSON.stringify(sessionInfo, null, 2)
    );
    
    // Install additional packages if specified
    if (labConfig.packages && labConfig.packages.length > 0) {
        console.log(`Installing additional packages: ${labConfig.packages.join(', ')}`);
        exec(`cd ${workspace} && npm install ${labConfig.packages.join(' ')}`, (error) => {
            if (error) console.error('Package installation error:', error);
        });
    }
    
    // Create starter files if specified
    if (labConfig.starter_files) {
        Object.entries(labConfig.starter_files).forEach(([filename, content]) => {
            const filePath = path.join(workspace, 'assignments', filename);
            fs.mkdirSync(path.dirname(filePath), { recursive: true });
            fs.writeFileSync(filePath, content);
            console.log(`Created starter file: ${filename}`);
        });
    }
    
    // Create welcome HTML file
    const welcomeHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>JavaScript Lab Environment</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; }
        .info { 
            background: #ecf0f1; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0;
        }
        .highlight { color: #e74c3c; font-weight: bold; }
        pre { 
            background: #2c3e50; 
            color: #ecf0f1; 
            padding: 15px; 
            border-radius: 5px;
            overflow-x: auto;
        }
        .feature {
            margin: 10px 0;
            padding: 10px;
            background: #eef7ff;
            border-left: 4px solid #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 JavaScript Lab Environment</h1>
        
        <div class="info">
            <strong>Session ID:</strong> ${sessionId}<br>
            <strong>Course:</strong> ${courseId}<br>
            <strong>Lab Type:</strong> JavaScript/Node.js Programming
        </div>
        
        <h2>📁 Workspace Structure</h2>
        <pre>
workspace/
├── assignments/    # Your lab assignments
├── solutions/      # Example solutions (when available)
├── projects/       # Your project files
├── static/         # Static web files (HTML, CSS, images)
└── package.json    # Node.js dependencies
        </pre>
        
        <h2>🛠 Available Features</h2>
        <div class="feature">
            <strong>Node.js Runtime:</strong> Execute JavaScript server-side code
        </div>
        <div class="feature">
            <strong>Express.js:</strong> Build web applications and APIs
        </div>
        <div class="feature">
            <strong>Development Tools:</strong> ESLint, Prettier, Jest for testing
        </div>
        <div class="feature">
            <strong>Package Manager:</strong> NPM for installing additional libraries
        </div>
        <div class="feature">
            <strong>Live Reload:</strong> Nodemon for automatic server restarts
        </div>
        
        <h2>🚀 Quick Start</h2>
        <p>Open your terminal and try these commands:</p>
        <pre>
# Run JavaScript files
node filename.js

# Start development server with auto-reload
npm run dev

# Run tests
npm test

# Install additional packages
npm install package-name
        </pre>
        
        <h2>📝 Sample Code</h2>
        <p>Try this simple Express.js server:</p>
        <pre>
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello from your JavaScript lab!');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
        </pre>
        
        <p class="highlight">Happy coding! 💻</p>
    </div>
    
    <script>
        // Add some interactivity
        console.log('JavaScript Lab Environment loaded!');
        console.log('Session ID: ${sessionId}');
        console.log('User ID: ${userId}');
        
        // Simple terminal simulator
        function createTerminal() {
            const terminal = document.createElement('div');
            terminal.innerHTML = \`
                <h3>Interactive Terminal</h3>
                <div style="background: #000; color: #0f0; padding: 10px; font-family: monospace;">
                    <div>lab@${sessionId}:~/workspace$ <span id="cursor">_</span></div>
                </div>
            \`;
            document.body.appendChild(terminal);
            
            // Blinking cursor
            setInterval(() => {
                const cursor = document.getElementById('cursor');
                if (cursor) cursor.style.opacity = cursor.style.opacity === '0' ? '1' : '0';
            }, 500);
        }
        
        // Add terminal when page loads
        window.addEventListener('load', createTerminal);
    </script>
</body>
</html>`;
    
    fs.writeFileSync(path.join(workspace, 'index.html'), welcomeHtml);
    
    // Create a sample index.js file
    const sampleIndexJs = `
const express = require('express');
const path = require('path');
const app = express();

// Serve static files
app.use(express.static('.'));

// API endpoint
app.get('/api/info', (req, res) => {
    res.json({
        message: 'JavaScript Lab Environment',
        session: '${sessionId}',
        user: '${userId}',
        course: '${courseId}',
        timestamp: new Date().toISOString()
    });
});

// Serve the welcome page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log(\`🚀 JavaScript Lab running on port \${PORT}\`);
    console.log(\`📝 Session: ${sessionId}\`);
    console.log(\`👤 User: ${userId}\`);
    console.log(\`📚 Course: ${courseId}\`);
});
`;
    
    fs.writeFileSync(path.join(workspace, 'index.js'), sampleIndexJs);
    
    console.log('Lab environment setup complete!');
}

function startLabServer() {
    console.log('Starting JavaScript lab server...');
    
    // Change to workspace directory and start the server
    process.chdir('/home/labuser/workspace');
    
    // Start the Express server
    const server = spawn('node', ['index.js'], {
        stdio: 'inherit',
        cwd: '/home/labuser/workspace'
    });
    
    server.on('error', (error) => {
        console.error('Failed to start lab server:', error);
    });
    
    server.on('exit', (code) => {
        console.log(\`Lab server exited with code: \${code}\`);
    });
}

// Main execution
if (require.main === module) {
    setupLabEnvironment();
    startLabServer();
}

module.exports = { setupLabEnvironment, startLabServer };