/**
 * Student File Manager Module
 * Handles file downloads and workspace management for students
 */

import { CONFIG } from '../config.js';

export class StudentFileManager {
    constructor() {
        this.labManagerURL = CONFIG.API_URLS.LAB_MANAGER;
        this.currentLabId = null;
        this.fileList = [];
        this.isLoading = false;
    }

    /**
     * Initialize file manager with lab ID
     */
    async initialize(labId) {
        this.currentLabId = labId;
        await this.refreshFileList();
        this.setupEventListeners();
    }

    /**
     * Setup event listeners for file management buttons
     */
    setupEventListeners() {
        // Refresh files button
        const refreshBtn = document.getElementById('refreshFilesBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshFileList());
        }

        // Download workspace button
        const downloadWorkspaceBtn = document.getElementById('downloadWorkspaceBtn');
        if (downloadWorkspaceBtn) {
            downloadWorkspaceBtn.addEventListener('click', () => this.downloadWorkspace());
        }

        // File list container for individual downloads
        const fileListContainer = document.getElementById('studentFileList');
        if (fileListContainer) {
            fileListContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('download-file-btn')) {
                    const filename = e.target.dataset.filename;
                    this.downloadFile(filename);
                }
            });
        }
    }

    /**
     * Refresh the list of files in student workspace
     */
    async refreshFileList() {
        if (!this.currentLabId) {
            console.error('No lab ID available for file refresh');
            return;
        }

        this.setLoading(true);
        
        try {
            const response = await fetch(`${this.labManagerURL}/labs/${this.currentLabId}/files`);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch files: ${response.status}`);
            }

            const data = await response.json();
            this.fileList = data.files || [];
            this.updateFileListUI();
            
            this.showNotification(`Found ${this.fileList.length} files in workspace`, 'success');
            
        } catch (error) {
            console.error('Error refreshing file list:', error);
            this.showNotification('Failed to refresh file list: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Download individual file
     */
    async downloadFile(filename) {
        if (!this.currentLabId || !filename) {
            this.showNotification('Missing lab ID or filename', 'error');
            return;
        }

        this.setLoading(true);
        
        try {
            const response = await fetch(`${this.labManagerURL}/labs/${this.currentLabId}/download/${encodeURIComponent(filename)}`);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            this.showNotification(`Downloaded: ${filename}`, 'success');
            
        } catch (error) {
            console.error('Error downloading file:', error);
            this.showNotification('Failed to download file: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Download entire workspace as ZIP
     */
    async downloadWorkspace() {
        if (!this.currentLabId) {
            this.showNotification('No lab session available', 'error');
            return;
        }

        this.setLoading(true);
        
        try {
            const response = await fetch(`${this.labManagerURL}/labs/${this.currentLabId}/download-workspace`);
            
            if (!response.ok) {
                throw new Error(`Workspace download failed: ${response.status}`);
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `workspace-${this.currentLabId}-${new Date().toISOString().split('T')[0]}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Workspace downloaded successfully!', 'success');
            
        } catch (error) {
            console.error('Error downloading workspace:', error);
            this.showNotification('Failed to download workspace: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Update file list UI
     */
    updateFileListUI() {
        const fileListContainer = document.getElementById('studentFileList');
        if (!fileListContainer) return;

        if (this.fileList.length === 0) {
            fileListContainer.innerHTML = `
                <div class="no-files-message">
                    <i class="fas fa-folder-open"></i>
                    <p>No files found in your workspace</p>
                    <p class="text-muted">Create some files in your lab environment and refresh to see them here</p>
                </div>
            `;
            return;
        }

        const fileListHTML = this.fileList.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <i class="fas fa-file${this.getFileIcon(file.name)}"></i>
                    <div class="file-details">
                        <div class="file-name">${this.escapeHtml(file.name)}</div>
                        <div class="file-metadata">
                            ${this.formatFileSize(file.size)} • Modified: ${this.formatDate(file.modified)}
                        </div>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-primary download-file-btn" 
                        data-filename="${this.escapeHtml(file.name)}"
                        title="Download ${this.escapeHtml(file.name)}">
                    <i class="fas fa-download"></i>
                </button>
            </div>
        `).join('');

        fileListContainer.innerHTML = `
            <div class="file-list-header">
                <h6>Your Files (${this.fileList.length})</h6>
                <button id="refreshFilesBtn" class="btn btn-sm btn-outline-secondary">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
            <div class="file-list-content">
                ${fileListHTML}
            </div>
        `;

        // Re-setup refresh button listener
        const refreshBtn = document.getElementById('refreshFilesBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshFileList());
        }
    }

    /**
     * Get appropriate icon for file type
     */
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'py': '-code',
            'js': '-code', 
            'html': '-code',
            'css': '-code',
            'json': '-code',
            'md': '-alt',
            'txt': '-alt',
            'pdf': '-pdf',
            'zip': '-archive',
            'jpg': '-image',
            'jpeg': '-image',
            'png': '-image',
            'gif': '-image'
        };
        return iconMap[ext] || '';
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Set loading state
     */
    setLoading(loading) {
        this.isLoading = loading;
        
        // Update UI loading indicators
        const loadingElements = document.querySelectorAll('.file-loading');
        loadingElements.forEach(el => {
            el.style.display = loading ? 'block' : 'none';
        });

        // Disable/enable buttons
        const buttons = document.querySelectorAll('#refreshFilesBtn, #downloadWorkspaceBtn, .download-file-btn');
        buttons.forEach(btn => {
            btn.disabled = loading;
            if (loading) {
                btn.classList.add('loading');
            } else {
                btn.classList.remove('loading');
            }
        });
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show file-manager-notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Find or create notification container
        let container = document.getElementById('fileManagerNotifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'fileManagerNotifications';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Get current lab ID from various sources
     */
    static getCurrentLabId() {
        // Try to get from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        let labId = urlParams.get('lab_id');
        
        // Try to get from local storage
        if (!labId) {
            labId = localStorage.getItem('currentLabId');
        }
        
        // Try to get from global variable
        if (!labId && window.currentLabId) {
            labId = window.currentLabId;
        }
        
        return labId;
    }

    /**
     * Initialize file manager if lab ID is available
     */
    static async autoInitialize() {
        const labId = StudentFileManager.getCurrentLabId();
        if (labId) {
            const fileManager = new StudentFileManager();
            await fileManager.initialize(labId);
            return fileManager;
        }
        return null;
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    StudentFileManager.autoInitialize();
});

export default StudentFileManager;