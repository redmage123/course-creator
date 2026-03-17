/**
 * useFileSystem Hook
 *
 * Manages lab file system operations
 * - File CRUD operations (create, read, update, delete)
 * - File navigation and selection
 * - File modification tracking
 * - Auto-save functionality
 *
 * @module features/labs/hooks/useFileSystem
 */

import { useState, useEffect, useCallback } from 'react';
import type { LabFile } from '../LabEnvironment';

interface UseFileSystemResult {
  files: LabFile[];
  currentFile: LabFile | null;
  createFile: (name: string, content?: string) => Promise<LabFile>;
  openFile: (fileId: string) => Promise<void>;
  saveFile: (fileId: string, content: string) => Promise<void>;
  deleteFile: (fileId: string) => Promise<void>;
  renameFile: (fileId: string, newName: string) => Promise<void>;
  createFolder: (name: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const useFileSystem = (
  sessionId: string | undefined
): UseFileSystemResult => {
  const [files, setFiles] = useState<LabFile[]>([]);
  const [currentFile, setCurrentFile] = useState<LabFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load files when session is active
  useEffect(() => {
    if (!sessionId) {
      setFiles([]);
      setCurrentFile(null);
      return;
    }

    const loadFiles = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files`,
          {
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load files');
        }

        const data = await response.json();
        setFiles(data.files || []);

        // Auto-select first file if none selected
        if (data.files && data.files.length > 0 && !currentFile) {
          setCurrentFile(data.files[0]);
        }
      } catch (err) {
        console.error('Failed to load files:', err);
        setError('Failed to load file system');
      } finally {
        setIsLoading(false);
      }
    };

    loadFiles();
  }, [sessionId]);

  // Detect file language from extension
  const detectLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'javascript',
      'tsx': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'h': 'c',
      'hpp': 'cpp',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'xml': 'xml',
      'md': 'markdown',
      'txt': 'plaintext'
    };
    return languageMap[ext || ''] || 'plaintext';
  };

  // Create new file
  const createFile = useCallback(async (
    name: string,
    content: string = ''
  ): Promise<LabFile> => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name,
            content,
            language: detectLanguage(name)
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create file');
      }

      const data = await response.json();
      const newFile: LabFile = {
        ...data.file,
        lastModified: new Date(data.file.lastModified)
      };

      setFiles(prev => [...prev, newFile]);
      setCurrentFile(newFile);

      return newFile;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create file';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Open file
  const openFile = useCallback(async (fileId: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files/${fileId}`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to open file');
      }

      const data = await response.json();
      const file: LabFile = {
        ...data.file,
        lastModified: new Date(data.file.lastModified)
      };

      setCurrentFile(file);

      // Update file in list if content changed
      setFiles(prev => prev.map(f => f.id === file.id ? file : f));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to open file';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Save file
  const saveFile = useCallback(async (fileId: string, content: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files/${fileId}`,
        {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save file');
      }

      const data = await response.json();
      const updatedFile: LabFile = {
        ...data.file,
        lastModified: new Date(data.file.lastModified)
      };

      // Update file in list
      setFiles(prev => prev.map(f => f.id === fileId ? updatedFile : f));

      // Update current file if it's the one being saved
      if (currentFile?.id === fileId) {
        setCurrentFile(updatedFile);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save file';
      setError(message);
      throw err;
    }
  }, [sessionId, currentFile]);

  // Delete file
  const deleteFile = useCallback(async (fileId: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files/${fileId}`,
        {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete file');
      }

      // Remove file from list
      setFiles(prev => prev.filter(f => f.id !== fileId));

      // Clear current file if it was deleted
      if (currentFile?.id === fileId) {
        setCurrentFile(files.length > 1 ? files[0] : null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete file';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, currentFile, files]);

  // Rename file
  const renameFile = useCallback(async (fileId: string, newName: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files/${fileId}/rename`,
        {
          method: 'PATCH',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: newName })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to rename file');
      }

      const data = await response.json();
      const updatedFile: LabFile = {
        ...data.file,
        lastModified: new Date(data.file.lastModified),
        language: detectLanguage(newName)
      };

      // Update file in list
      setFiles(prev => prev.map(f => f.id === fileId ? updatedFile : f));

      // Update current file if it's the one being renamed
      if (currentFile?.id === fileId) {
        setCurrentFile(updatedFile);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to rename file';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, currentFile]);

  // Create folder
  const createFolder = useCallback(async (name: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/folders`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create folder');
      }

      // Reload files to include new folder structure
      const filesResponse = await fetch(
        `https://176.9.99.103:8005/api/v1/labs/${sessionId}/files`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (filesResponse.ok) {
        const data = await filesResponse.json();
        setFiles(data.files || []);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create folder';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  return {
    files,
    currentFile,
    createFile,
    openFile,
    saveFile,
    deleteFile,
    renameFile,
    createFolder,
    isLoading,
    error
  };
};

export default useFileSystem;
