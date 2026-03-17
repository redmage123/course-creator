/**
 * File Explorer Component
 *
 * Tree-view file explorer for lab environment
 * Supports file/folder creation, deletion, renaming
 *
 * @module features/labs/components/FileExplorer
 */

import React from 'react';
import type { LabFile } from '../LabEnvironment';
import styles from './FileExplorer.module.css';

export interface FileExplorerProps {
  files: LabFile[];
  currentFile: LabFile | null;
  onFileSelect: (fileId: string) => void;
  onFileCreate: (name: string) => Promise<void>;
  onFileDelete: (fileId: string) => Promise<void>;
  onFileRename: (fileId: string, newName: string) => Promise<void>;
  onFolderCreate: (name: string) => Promise<void>;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  files,
  currentFile,
  onFileSelect,
  onFileCreate,
  onFileDelete,
  onFileRename,
  onFolderCreate
}) => {
  const [newFileName, setNewFileName] = React.useState('');
  const [isCreatingFile, setIsCreatingFile] = React.useState(false);

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFileName.trim()) return;

    try {
      await onFileCreate(newFileName);
      setNewFileName('');
      setIsCreatingFile(false);
    } catch (error) {
      console.error('Failed to create file:', error);
    }
  };

  return (
    <div className={styles.fileExplorer} id="file-explorer">
      <div className={styles.fileExplorerHeader}>
        <h3>Files</h3>
        <div className={styles.fileActions}>
          <button
            id="new-file-btn"
            className={styles.actionBtn}
            onClick={() => setIsCreatingFile(!isCreatingFile)}
            title="New File"
          >
            📄
          </button>
          <button
            id="new-folder-btn"
            className={styles.actionBtn}
            onClick={() => {/* TODO: Implement */}}
            title="New Folder"
          >
            📁
          </button>
        </div>
      </div>

      {isCreatingFile && (
        <form onSubmit={handleCreateFile} className={styles.newFileForm}>
          <input
            id="new-file-name"
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            placeholder="filename.py"
            className={styles.newFileInput}
            autoFocus
          />
        </form>
      )}

      <div className={styles.fileList}>
        {files.map((file) => (
          <div
            key={file.id}
            className={`${styles.fileItem} ${currentFile?.id === file.id ? styles.active : ''}`}
            onClick={() => onFileSelect(file.id)}
            data-filename={file.name}
          >
            <span className={styles.fileIcon}>
              {getFileIcon(file.language)}
            </span>
            <span className={styles.fileName}>{file.name}</span>
            {file.isModified && <span className={styles.modifiedIndicator}>●</span>}
          </div>
        ))}

        {files.length === 0 && !isCreatingFile && (
          <div className={styles.emptyState}>
            No files yet. Click 📄 to create one.
          </div>
        )}
      </div>
    </div>
  );
};

function getFileIcon(language: string): string {
  const icons: Record<string, string> = {
    python: '🐍',
    javascript: '📜',
    typescript: '💙',
    java: '☕',
    cpp: '⚙️',
    c: '⚙️',
    html: '🌐',
    css: '🎨',
    json: '📋',
  };
  return icons[language] || '📄';
}

export default FileExplorer;
