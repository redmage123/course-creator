/**
 * File System Module
 * Single Responsibility: Handle virtual file system operations
 */

export class VirtualFileSystem {
    constructor(sandboxRoot = '/home/student') {
        this.sandboxRoot = sandboxRoot;
        this.currentDirectory = sandboxRoot;
        this.fileSystem = this.initializeFileSystem();
    }

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

    joinPaths(...paths) {
        return paths.join('/').replace(/\/+/g, '/');
    }

    // Get file or directory at path
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
    exists(path) {
        try {
            return this.getItem(path) !== null;
        } catch (e) {
            return false;
        }
    }

    // Check if path is a directory
    isDirectory(path) {
        const item = this.getItem(path);
        return item !== null && typeof item === 'object' && typeof item !== 'string';
    }

    // Check if path is a file
    isFile(path) {
        const item = this.getItem(path);
        return typeof item === 'string';
    }

    // List directory contents
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
    getCurrentDirectory() {
        return this.currentDirectory;
    }

    // Delete file or directory
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
    serialize() {
        return {
            fileSystem: this.fileSystem,
            currentDirectory: this.currentDirectory,
            sandboxRoot: this.sandboxRoot
        };
    }

    // Restore file system state
    deserialize(state) {
        this.fileSystem = state.fileSystem || this.initializeFileSystem();
        this.currentDirectory = state.currentDirectory || this.sandboxRoot;
        this.sandboxRoot = state.sandboxRoot || '/home/student';
    }
}