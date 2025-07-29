/**
 * Terminal Emulator Module
 * Single Responsibility: Handle terminal operations and command execution
 */

export class TerminalEmulator {
    constructor(fileSystem, config, outputElement) {
        this.fileSystem = fileSystem;
        this.config = config;
        this.outputElement = outputElement;
        this.history = [];
        this.historyIndex = -1;
        this.environmentVariables = {
            USER: 'student',
            HOME: '/home/student',
            PATH: '/usr/local/bin:/usr/bin:/bin',
            SHELL: '/bin/bash'
        };
    }

    // Execute a command
    async executeCommand(commandLine) {
        const trimmedCommand = commandLine.trim();
        
        if (!trimmedCommand) {
            return '';
        }

        // Add to history
        this.addToHistory(trimmedCommand);

        // Parse command and arguments
        const parts = this.parseCommand(trimmedCommand);
        const command = parts[0];
        const args = parts.slice(1);

        // Check if command is allowed
        if (!this.config.isCommandAllowed(command)) {
            return `bash: ${command}: command not found or not allowed`;
        }

        try {
            return await this.runCommand(command, args);
        } catch (error) {
            return `Error: ${error.message}`;
        }
    }

    parseCommand(commandLine) {
        // Simple command parsing (doesn't handle complex shell features)
        return commandLine.split(/\s+/).filter(part => part.length > 0);
    }

    async runCommand(command, args) {
        switch (command) {
            case 'help':
                return this.helpCommand();
            case 'ls':
                return this.lsCommand(args);
            case 'cd':
                return this.cdCommand(args);
            case 'pwd':
                return this.pwdCommand();
            case 'cat':
                return this.catCommand(args);
            case 'echo':
                return this.echoCommand(args);
            case 'mkdir':
                return this.mkdirCommand(args);
            case 'touch':
                return this.touchCommand(args);
            case 'clear':
                return this.clearCommand();
            case 'whoami':
                return this.whoamiCommand();
            case 'date':
                return this.dateCommand();
            case 'rm':
                return this.rmCommand(args);
            case 'python':
                return this.pythonCommand(args);
            case 'node':
                return this.nodeCommand(args);
            case 'gcc':
                return this.gccCommand(args);
            default:
                return `bash: ${command}: command not found`;
        }
    }

    helpCommand() {
        const commands = this.config.config.security.allowedCommands;
        return `Available commands:\n${commands.join(', ')}\n\nType 'man <command>' for more information about a specific command.`;
    }

    lsCommand(args) {
        const path = args.length > 0 ? args[0] : this.fileSystem.getCurrentDirectory();
        
        try {
            const items = this.fileSystem.listDirectory(path);
            
            if (items.length === 0) {
                return '';
            }
            
            return items.map(item => {
                const prefix = item.type === 'directory' ? 'd' : '-';
                const permissions = item.type === 'directory' ? 'rwxr-xr-x' : 'rw-r--r--';
                const size = item.size.toString().padStart(8);
                const name = item.type === 'directory' ? `\x1b[34m${item.name}\x1b[0m` : item.name;
                return `${prefix}${permissions} 1 student student ${size} ${name}`;
            }).join('\n');
        } catch (error) {
            return `ls: ${error.message}`;
        }
    }

    cdCommand(args) {
        const path = args.length > 0 ? args[0] : this.environmentVariables.HOME;
        
        try {
            this.fileSystem.changeDirectory(path);
            return '';
        } catch (error) {
            return `cd: ${error.message}`;
        }
    }

    pwdCommand() {
        return this.fileSystem.getCurrentDirectory();
    }

    catCommand(args) {
        if (args.length === 0) {
            return 'cat: missing file operand';
        }
        
        try {
            const content = this.fileSystem.readFile(args[0]);
            return content;
        } catch (error) {
            return `cat: ${error.message}`;
        }
    }

    echoCommand(args) {
        return args.join(' ');
    }

    mkdirCommand(args) {
        if (args.length === 0) {
            return 'mkdir: missing operand';
        }
        
        try {
            this.fileSystem.createDirectory(args[0]);
            return '';
        } catch (error) {
            return `mkdir: ${error.message}`;
        }
    }

    touchCommand(args) {
        if (args.length === 0) {
            return 'touch: missing file operand';
        }
        
        try {
            // Create empty file if it doesn't exist
            if (!this.fileSystem.exists(args[0])) {
                this.fileSystem.writeFile(args[0], '');
            }
            return '';
        } catch (error) {
            return `touch: ${error.message}`;
        }
    }

    clearCommand() {
        if (this.outputElement) {
            this.outputElement.innerHTML = '';
        }
        return '';
    }

    whoamiCommand() {
        return this.environmentVariables.USER;
    }

    dateCommand() {
        return new Date().toString();
    }

    rmCommand(args) {
        if (args.length === 0) {
            return 'rm: missing operand';
        }
        
        try {
            this.fileSystem.delete(args[0]);
            return '';
        } catch (error) {
            return `rm: ${error.message}`;
        }
    }

    pythonCommand(args) {
        if (args.length === 0) {
            return 'Python 3.9.0 (simulated)\nType "help", "copyright", "credits" or "license" for more information.\n>>> (Interactive mode not available in this environment)';
        }
        
        // Simulate running Python file
        try {
            const content = this.fileSystem.readFile(args[0]);
            return `Executing Python file: ${args[0]}\n[Simulated execution - Python runtime not available]`;
        } catch (error) {
            return `python: ${error.message}`;
        }
    }

    nodeCommand(args) {
        if (args.length === 0) {
            return 'Welcome to Node.js v16.0.0 (simulated)\nType ".help" for more information.\n> (Interactive mode not available in this environment)';
        }
        
        // Simulate running Node.js file
        try {
            const content = this.fileSystem.readFile(args[0]);
            return `Executing Node.js file: ${args[0]}\n[Simulated execution - Node.js runtime not available]`;
        } catch (error) {
            return `node: ${error.message}`;
        }
    }

    gccCommand(args) {
        if (args.length === 0) {
            return 'gcc: fatal error: no input files';
        }
        
        // Simulate compiling C file
        try {
            const content = this.fileSystem.readFile(args[0]);
            const outputFile = args[0].replace(/\\.c$/, '') || 'a.out';
            return `Compiling ${args[0]}...\n[Simulated compilation - GCC not available]\nOutput would be: ${outputFile}`;
        } catch (error) {
            return `gcc: ${error.message}`;
        }
    }

    addToHistory(command) {
        this.history.push(command);
        this.historyIndex = this.history.length;
    }

    getPreviousCommand() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            return this.history[this.historyIndex];
        }
        return null;
    }

    getNextCommand() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            return this.history[this.historyIndex];
        } else if (this.historyIndex === this.history.length - 1) {
            this.historyIndex++;
            return '';
        }
        return null;
    }

    getPrompt() {
        const user = this.environmentVariables.USER;
        const hostname = 'lab-container';
        const currentDir = this.fileSystem.getCurrentDirectory();
        const shortDir = currentDir === this.environmentVariables.HOME ? '~' : currentDir.split('/').pop();
        
        return `${user}@${hostname}:${shortDir}$ `;
    }

    setEnvironmentVariable(name, value) {
        this.environmentVariables[name] = value;
    }

    getEnvironmentVariable(name) {
        return this.environmentVariables[name];
    }
}