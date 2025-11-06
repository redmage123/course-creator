/**
 * File System Module
 * Single Responsibility: Handle virtual file system operations
 */
export class VirtualFileSystem {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {*} sandboxRoot - Sandboxroot parameter
     */
    constructor(sandboxRoot = '/home/student') {
        this.sandboxRoot = sandboxRoot;
        this.currentDirectory = sandboxRoot;
        this.fileSystem = this.initializeFileSystem();
    }

    /**
     * INITIALIZE FILE SYSTEM COMPONENT
     * PURPOSE: Initialize file system component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    initializeFileSystem() {
        return {
            '/home/student': {
                'readme.txt': 'Welcome to the lab environment!
This is a simulated file system.',
                'examples': {
                    'hello.sh': '#!/bin/bash
echo "Hello from the lab!"',
                    'test.py': 'print("Python in the lab!")',
                    'hello.c': '#include <stdio.h>
int main() {
    printf("C programming in the lab!\
");
    return 0;
}'
                },
                'workspace': {
                    '.gitkeep': ''
                }
            }
        };
    }

    // Normalize path to absolute path within sandbox
    /**
     * EXECUTE NORMALIZEPATH OPERATION
     * PURPOSE: Execute normalizePath operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    normalizePath(path) {
        if (!path.startsWith('/')) {
            // Relative path - resolve from current directory
            path = this.joinPaths(this.currentDirectory, path);
        }
        
        // Resolve . and .. components
        const parts = path.split('/').filter(part => part !== '');
        const resolved = [];
        
        for (const part of parts) {
            if (part === '.') {
                continue;
            } else if (part === '..') {
                if (resolved.length > 0) {
                    resolved.pop();
                }
            } else {
                resolved.push(part);
            }
        }
        
        const normalizedPath = '/' + resolved.join('/');
        
        // Ensure path is within sandbox
        if (!normalizedPath.startsWith(this.sandboxRoot)) {
            throw new Error('Access denied: Path outside sandbox');
        }
        
        return normalizedPath;
    }

    /**
     * EXECUTE JOINPATHS OPERATION
     * PURPOSE: Execute joinPaths operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} ...paths - ...paths parameter
     */
    joinPaths(...paths) {
        return paths.join('/').replace(/\/+/g, '/');
    }

    // Get file or directory at path
    /**
     * RETRIEVE ITEM INFORMATION
     * PURPOSE: Retrieve item information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} path - Path parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getItem(path) {
        const normalizedPath = this.normalizePath(path);
        const parts = normalizedPath.split('/').filter(part => part !== '');
        
        let current = this.fileSystem;
        for (const part of parts) {
            if (current && typeof current === 'object' && part in current) {
                current = current[part];
            } else {
                return null;
            }
        }
        
        return current;
    }

    // Check if path exists
    /**
     * EXECUTE EXISTS OPERATION
     * PURPOSE: Execute exists operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    exists(path) {
        try {
            return this.getItem(path) !== null;
        } catch (e) {
            return false;
        }
    }

    // Check if path is a directory
    /**
     * EXECUTE ISDIRECTORY OPERATION
     * PURPOSE: Execute isDirectory operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isDirectory(path) {
        const item = this.getItem(path);
        return item !== null && typeof item === 'object' && typeof item !== 'string';
    }

    // Check if path is a file
    /**
     * EXECUTE ISFILE OPERATION
     * PURPOSE: Execute isFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isFile(path) {
        const item = this.getItem(path);
        return typeof item === 'string';
    }

    // List directory contents
    /**
     * EXECUTE LISTDIRECTORY OPERATION
     * PURPOSE: Execute listDirectory operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    listDirectory(path = null) {
        const targetPath = path || this.currentDirectory;
        const item = this.getItem(targetPath);
        
        if (!this.isDirectory(targetPath)) {
            throw new Error(`${targetPath}: Not a directory`);
        }
        
        return Object.keys(item).map(name => ({
            name,
            type: typeof item[name] === 'string' ? 'file' : 'directory',
            size: typeof item[name] === 'string' ? item[name].length : 0
        }));
    }

    // Read file content
    /**
     * EXECUTE READFILE OPERATION
     * PURPOSE: Execute readFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    readFile(path) {
        const item = this.getItem(path);
        
        if (item === null) {
            throw new Error(`${path}: No such file or directory`);
        }
        
        if (!this.isFile(path)) {
            throw new Error(`${path}: Is a directory`);
        }
        
        return item;
    }

    // Write file content
    /**
     * EXECUTE WRITEFILE OPERATION
     * PURPOSE: Execute writeFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     * @param {*} content - Content parameter
     */
    writeFile(path, content) {
        try {
            const normalizedPath = this.normalizePath(path);
            const parts = normalizedPath.split('/').filter(part => part !== '');
            const fileName = parts.pop();
            
            // Navigate to parent directory
            let current = this.fileSystem;
            for (const part of parts) {
                if (!(part in current)) {
                    current[part] = {};
                }
                current = current[part];
            }
            
            // Write file
            current[fileName] = content;
            return true;
        } catch (e) {
            throw new Error(`Cannot write file: ${e.message}`);
        }
    }

    // Create directory
    /**
     * CREATE NEW DIRECTORY INSTANCE
     * PURPOSE: Create new directory instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} path - Path parameter
     *
     * @returns {Object} Newly created instance
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    createDirectory(path) {
        try {
            const normalizedPath = this.normalizePath(path);
            const parts = normalizedPath.split('/').filter(part => part !== '');
            const dirName = parts.pop();
            
            // Navigate to parent directory
            let current = this.fileSystem;
            for (const part of parts) {
                if (!(part in current)) {
                    current[part] = {};
                }
                current = current[part];
            }
            
            // Create directory
            if (dirName in current) {
                throw new Error('Directory already exists');
            }
            
            current[dirName] = {};
            return true;
        } catch (e) {
            throw new Error(`Cannot create directory: ${e.message}`);
        }
    }

    // Change current directory
    /**
     * EXECUTE CHANGEDIRECTORY OPERATION
     * PURPOSE: Execute changeDirectory operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     */
    changeDirectory(path) {
        const normalizedPath = this.normalizePath(path);
        
        if (!this.exists(normalizedPath)) {
            throw new Error(`${path}: No such file or directory`);
        }
        
        if (!this.isDirectory(normalizedPath)) {
            throw new Error(`${path}: Not a directory`);
        }
        
        this.currentDirectory = normalizedPath;
        return this.currentDirectory;
    }

    // Get current directory
    /**
     * RETRIEVE CURRENT DIRECTORY INFORMATION
     * PURPOSE: Retrieve current directory information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getCurrentDirectory() {
        return this.currentDirectory;
    }

    // Delete file or directory
    /**
     * REMOVE  FROM SYSTEM
     * PURPOSE: Remove  from system
     * WHY: Manages resource cleanup and data consistency
     *
     * @param {*} path - Path parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    delete(path) {
        try {
            const normalizedPath = this.normalizePath(path);
            const parts = normalizedPath.split('/').filter(part => part !== '');
            const itemName = parts.pop();
            
            // Navigate to parent directory
            let current = this.fileSystem;
            for (const part of parts) {
                if (!(part in current)) {
                    throw new Error('Path not found');
                }
                current = current[part];
            }
            
            if (!(itemName in current)) {
                throw new Error('File or directory not found');
            }
            
            delete current[itemName];
            return true;
        } catch (e) {
            throw new Error(`Cannot delete: ${e.message}`);
        }
    }

    // Get file system state for persistence
    /**
     * EXECUTE SERIALIZE OPERATION
     * PURPOSE: Execute serialize operation
     * WHY: Implements required business logic for system functionality
     */
    serialize() {
        return {
            fileSystem: this.fileSystem,
            currentDirectory: this.currentDirectory,
            sandboxRoot: this.sandboxRoot
        };
    }

    // Restore file system state
    /**
     * EXECUTE DESERIALIZE OPERATION
     * PURPOSE: Execute deserialize operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} state - State parameter
     */
    deserialize(state) {
        this.fileSystem = state.fileSystem || this.initializeFileSystem();
        this.currentDirectory = state.currentDirectory || this.sandboxRoot;
        this.sandboxRoot = state.sandboxRoot || '/home/student';
    }
}