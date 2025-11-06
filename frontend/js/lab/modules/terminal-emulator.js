/**
 * Terminal Emulator Module
 * Single Responsibility: Handle terminal operations and command execution
 */
export class TerminalEmulator {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {*} fileSystem - Filesystem parameter
     * @param {Object} config - Configuration options
     * @param {*} outputElement - Outputelement parameter
     */
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
    /**
     * EXECUTE EXECUTECOMMAND OPERATION
     * PURPOSE: Execute executeCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} commandLine - Commandline parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE PARSECOMMAND OPERATION
     * PURPOSE: Execute parseCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} commandLine - Commandline parameter
     *
     * @returns {*} Operation result
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    parseCommand(commandLine) {
        // Simple command parsing (doesn't handle complex shell features)
        return commandLine.split(/\s+/).filter(part => part.length > 0);
    }

    /**
     * EXECUTE RUNCOMMAND OPERATION
     * PURPOSE: Execute runCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} command - Command parameter
     * @param {*} args - Args parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE HELPCOMMAND OPERATION
     * PURPOSE: Execute helpCommand operation
     * WHY: Implements required business logic for system functionality
     */
    helpCommand() {
        const commands = this.config.config.security.allowedCommands;
        return `Available commands:
${commands.join(', ')}

Type 'man <command>' for more information about a specific command.`;
    }

    /**
     * EXECUTE LSCOMMAND OPERATION
     * PURPOSE: Execute lsCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
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
            }).join('
');
        } catch (error) {
            return `ls: ${error.message}`;
        }
    }

    /**
     * EXECUTE CDCOMMAND OPERATION
     * PURPOSE: Execute cdCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
    cdCommand(args) {
        const path = args.length > 0 ? args[0] : this.environmentVariables.HOME;
        
        try {
            this.fileSystem.changeDirectory(path);
            return '';
        } catch (error) {
            return `cd: ${error.message}`;
        }
    }

    /**
     * EXECUTE PWDCOMMAND OPERATION
     * PURPOSE: Execute pwdCommand operation
     * WHY: Implements required business logic for system functionality
     */
    pwdCommand() {
        return this.fileSystem.getCurrentDirectory();
    }

    /**
     * EXECUTE CATCOMMAND OPERATION
     * PURPOSE: Execute catCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
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

    /**
     * EXECUTE ECHOCOMMAND OPERATION
     * PURPOSE: Execute echoCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
    echoCommand(args) {
        return args.join(' ');
    }

    /**
     * EXECUTE MKDIRCOMMAND OPERATION
     * PURPOSE: Execute mkdirCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
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

    /**
     * EXECUTE TOUCHCOMMAND OPERATION
     * PURPOSE: Execute touchCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
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

    /**
     * EXECUTE CLEARCOMMAND OPERATION
     * PURPOSE: Execute clearCommand operation
     * WHY: Implements required business logic for system functionality
     */
    clearCommand() {
        if (this.outputElement) {
            this.outputElement.innerHTML = '';
        }
        return '';
    }

    /**
     * EXECUTE WHOAMICOMMAND OPERATION
     * PURPOSE: Execute whoamiCommand operation
     * WHY: Implements required business logic for system functionality
     */
    whoamiCommand() {
        return this.environmentVariables.USER;
    }

    /**
     * EXECUTE DATECOMMAND OPERATION
     * PURPOSE: Execute dateCommand operation
     * WHY: Implements required business logic for system functionality
     */
    dateCommand() {
        return new Date().toString();
    }

    /**
     * EXECUTE RMCOMMAND OPERATION
     * PURPOSE: Execute rmCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
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

    /**
     * EXECUTE PYTHONCOMMAND OPERATION
     * PURPOSE: Execute pythonCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
    pythonCommand(args) {
        if (args.length === 0) {
            return 'Python 3.9.0 (simulated)
Type "help", "copyright", "credits" or "license" for more information.
>>> (Interactive mode not available in this environment)';
        }
        
        // Simulate running Python file
        try {
            const content = this.fileSystem.readFile(args[0]);
            return `Executing Python file: ${args[0]}
[Simulated execution - Python runtime not available]`;
        } catch (error) {
            return `python: ${error.message}`;
        }
    }

    /**
     * EXECUTE NODECOMMAND OPERATION
     * PURPOSE: Execute nodeCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
    nodeCommand(args) {
        if (args.length === 0) {
            return 'Welcome to Node.js v16.0.0 (simulated)
Type ".help" for more information.
> (Interactive mode not available in this environment)';
        }
        
        // Simulate running Node.js file
        try {
            const content = this.fileSystem.readFile(args[0]);
            return `Executing Node.js file: ${args[0]}
[Simulated execution - Node.js runtime not available]`;
        } catch (error) {
            return `node: ${error.message}`;
        }
    }

    /**
     * EXECUTE GCCCOMMAND OPERATION
     * PURPOSE: Execute gccCommand operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} args - Args parameter
     */
    gccCommand(args) {
        if (args.length === 0) {
            return 'gcc: fatal error: no input files';
        }
        
        // Simulate compiling C file
        try {
            const content = this.fileSystem.readFile(args[0]);
            const outputFile = args[0].replace(/\\.c$/, '') || 'a.out';
            return `Compiling ${args[0]}...
[Simulated compilation - GCC not available]
Output would be: ${outputFile}`;
        } catch (error) {
            return `gcc: ${error.message}`;
        }
    }

    /**
     * EXECUTE ADDTOHISTORY OPERATION
     * PURPOSE: Execute addToHistory operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} command - Command parameter
     */
    addToHistory(command) {
        this.history.push(command);
        this.historyIndex = this.history.length;
    }

    /**
     * RETRIEVE PREVIOUS COMMAND INFORMATION
     * PURPOSE: Retrieve previous command information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getPreviousCommand() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            return this.history[this.historyIndex];
        }
        return null;
    }

    /**
     * RETRIEVE NEXT COMMAND INFORMATION
     * PURPOSE: Retrieve next command information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
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

    /**
     * RETRIEVE PROMPT INFORMATION
     * PURPOSE: Retrieve prompt information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getPrompt() {
        const user = this.environmentVariables.USER;
        const hostname = 'lab-container';
        const currentDir = this.fileSystem.getCurrentDirectory();
        const shortDir = currentDir === this.environmentVariables.HOME ? '~' : currentDir.split('/').pop();
        
        return `${user}@${hostname}:${shortDir}$ `;
    }

    /**
     * SET ENVIRONMENT VARIABLE VALUE
     * PURPOSE: Set environment variable value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {*} name - Name value
     * @param {*} value - Value to set or process
     */
    setEnvironmentVariable(name, value) {
        this.environmentVariables[name] = value;
    }

    /**
     * RETRIEVE ENVIRONMENT VARIABLE INFORMATION
     * PURPOSE: Retrieve environment variable information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} name - Name value
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getEnvironmentVariable(name) {
        return this.environmentVariables[name];
    }
}