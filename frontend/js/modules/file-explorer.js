/**
 * File Explorer Widget Module
 *
 * BUSINESS CONTEXT:
 * Provides a file browser interface for admins and instructors to view, select,
 * and manage uploaded course materials. Integrates with drag-and-drop upload
 * functionality and enforces role-based access control for file operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - ES6 class-based architecture
 * - Role-based authorization for file deletion
 * - Integration with drag-and-drop upload module
 * - Metadata tracking for all file operations
 * - Responsive grid/list view modes
 * - File preview capabilities
 * - Batch operations support
 *
 * AUTHORIZATION RULES:
 * - Site Admin: Can delete any file
 * - Org Admin: Can delete files within their organization
 * - Instructor: Can delete only files they uploaded
 * - Student: Read-only access (no deletion)
 *
 * @module file-explorer
 */

import { CONFIG } from '../config.js';

/**
 * File Explorer Widget Class
 *
 * DESIGN PATTERN: Component pattern with event-driven architecture
 * Manages file browsing, selection, and operations with RBAC
 */
export class FileExplorer {
    /**
     * Initialize file explorer
     *
     * @param {HTMLElement} container - Container element for file explorer
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            // API configuration
            apiEndpoint: options.apiEndpoint || `${CONFIG.ENDPOINTS.METADATA_SERVICE}/files`,
            uploadEndpoint: options.uploadEndpoint || `${CONFIG.ENDPOINTS.CONTENT_SERVICE}/upload`,

            // Filter options
            courseId: options.courseId || null,
            organizationId: options.organizationId || null,
            fileTypes: options.fileTypes || [], // e.g., ['syllabus', 'slides', 'video']

            // View options
            viewMode: options.viewMode || 'grid', // 'grid' or 'list'
            sortBy: options.sortBy || 'date', // 'name', 'date', 'size', 'type'
            sortOrder: options.sortOrder || 'desc', // 'asc' or 'desc'

            // Feature flags
            allowUpload: options.allowUpload !== false,
            allowDelete: options.allowDelete !== false,
            allowDownload: options.allowDownload !== false,
            allowPreview: options.allowPreview !== false,
            enableDragDrop: options.enableDragDrop !== false,

            // Selection options
            multiSelect: options.multiSelect || false,

            // Callbacks
            onFileSelect: options.onFileSelect || (() => {}),
            onFileDelete: options.onFileDelete || (() => {}),
            onFileUpload: options.onFileUpload || (() => {}),
            onError: options.onError || ((error) => console.error(error))
        };

        // State management
        this.files = [];
        this.selectedFiles = new Set();
        this.currentUser = this.getCurrentUser();

        // Initialize
        this.render();
        this.attachEventListeners();
        this.loadFiles();
    }

    /**
     * Get current authenticated user
     *
     * BUSINESS LOGIC:
     * Retrieves user context from localStorage for authorization checks
     *
     * @returns {Object} Current user object
     */
    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('currentUser');
            return userStr ? JSON.parse(userStr) : null;
        } catch (error) {
            console.error('Failed to get current user:', error);
            return null;
        }
    }

    /**
     * Check if current user can delete a specific file
     *
     * BUSINESS LOGIC - AUTHORIZATION RULES:
     * 1. Site Admin: Can delete any file
     * 2. Org Admin: Can delete files in their organization
     * 3. Instructor: Can delete only their own uploaded files
     * 4. Student: Cannot delete any files
     *
     * @param {Object} file - File object with metadata
     * @returns {boolean} True if user can delete the file
     */
    canDeleteFile(file) {
        if (!this.currentUser || !this.options.allowDelete) {
            return false;
        }

        const userRole = this.currentUser.role;
        const userId = this.currentUser.id;
        const userOrgId = this.currentUser.organization_id;

        // Site admin can delete anything
        if (userRole === 'site_admin') {
            return true;
        }

        // Org admin can delete files in their organization
        if (userRole === 'org_admin') {
            return file.organization_id === userOrgId;
        }

        // Instructor can delete only their own files
        if (userRole === 'instructor') {
            return file.uploaded_by === userId || file.instructor_id === userId;
        }

        // Students cannot delete
        return false;
    }

    /**
     * Check if current user can upload files
     *
     * @returns {boolean} True if user can upload
     */
    canUploadFiles() {
        if (!this.currentUser || !this.options.allowUpload) {
            return false;
        }

        const userRole = this.currentUser.role;
        return ['site_admin', 'org_admin', 'instructor'].includes(userRole);
    }

    /**
     * Render file explorer UI
     *
     * TECHNICAL IMPLEMENTATION:
     * Creates DOM structure for file explorer with toolbar, file grid/list, and controls
     */
    render() {
        this.container.innerHTML = `
            <div class="file-explorer" data-view-mode="${this.options.viewMode}">
                <!-- Toolbar -->
                <div class="file-explorer-toolbar">
                    <div class="toolbar-left">
                        <button class="btn-icon view-mode-btn" data-view="grid" title="Grid view">
                            <i class="fas fa-th"></i>
                        </button>
                        <button class="btn-icon view-mode-btn" data-view="list" title="List view">
                            <i class="fas fa-list"></i>
                        </button>
                        <div class="toolbar-divider"></div>
                        <select class="sort-select" id="fileSortBy">
                            <option value="date">Sort by Date</option>
                            <option value="name">Sort by Name</option>
                            <option value="size">Sort by Size</option>
                            <option value="type">Sort by Type</option>
                        </select>
                        <button class="btn-icon sort-order-btn" id="sortOrderBtn" title="Sort order">
                            <i class="fas fa-sort-amount-down"></i>
                        </button>
                    </div>
                    <div class="toolbar-right">
                        ${this.canUploadFiles() ? `
                            <button class="btn btn-primary upload-btn" id="uploadFileBtn">
                                <i class="fas fa-upload"></i> Upload Files
                            </button>
                        ` : ''}
                        <button class="btn-icon refresh-btn" id="refreshFilesBtn" title="Refresh">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>

                <!-- File count and selection info -->
                <div class="file-explorer-info">
                    <span class="file-count" id="fileCount">0 files</span>
                    <span class="selection-info" id="selectionInfo" style="display: none;"></span>
                </div>

                <!-- Upload drop zone (shown when dragging) -->
                ${this.options.enableDragDrop && this.canUploadFiles() ? `
                    <div class="file-explorer-drop-zone" id="fileExplorerDropZone" style="display: none;">
                        <div class="drop-zone-content">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <p>Drop files here to upload</p>
                        </div>
                    </div>
                ` : ''}

                <!-- File grid/list container -->
                <div class="file-explorer-content" id="fileExplorerContent">
                    <div class="file-explorer-loading">
                        <div class="loading-spinner"></div>
                        <p>Loading files...</p>
                    </div>
                </div>

                <!-- File actions panel (shown when files selected) -->
                <div class="file-actions-panel" id="fileActionsPanel" style="display: none;">
                    <div class="actions-left">
                        <span class="selected-count" id="selectedCount">0 selected</span>
                    </div>
                    <div class="actions-right">
                        ${this.options.allowDownload ? `
                            <button class="btn btn-secondary" id="downloadSelectedBtn">
                                <i class="fas fa-download"></i> Download
                            </button>
                        ` : ''}
                        ${this.options.allowDelete ? `
                            <button class="btn btn-danger" id="deleteSelectedBtn">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        ` : ''}
                        <button class="btn btn-outline" id="clearSelectionBtn">
                            <i class="fas fa-times"></i> Clear
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add CSS styles
        this.addStyles();
    }

    /**
     * Attach event listeners
     *
     * TECHNICAL IMPLEMENTATION:
     * Sets up event delegation for file operations and UI interactions
     */
    attachEventListeners() {
        const container = this.container;

        // View mode toggle
        container.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const viewMode = e.currentTarget.dataset.view;
                this.setViewMode(viewMode);
            });
        });

        // Sort controls
        const sortSelect = container.querySelector('#fileSortBy');
        if (sortSelect) {
            sortSelect.value = this.options.sortBy;
            sortSelect.addEventListener('change', (e) => {
                this.options.sortBy = e.target.value;
                this.renderFiles();
            });
        }

        const sortOrderBtn = container.querySelector('#sortOrderBtn');
        if (sortOrderBtn) {
            sortOrderBtn.addEventListener('click', () => {
                this.toggleSortOrder();
            });
        }

        // Upload button
        const uploadBtn = container.querySelector('#uploadFileBtn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                this.showUploadDialog();
            });
        }

        // Refresh button
        const refreshBtn = container.querySelector('#refreshFilesBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadFiles();
            });
        }

        // File actions
        const downloadBtn = container.querySelector('#downloadSelectedBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadSelected();
            });
        }

        const deleteBtn = container.querySelector('#deleteSelectedBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteSelected();
            });
        }

        const clearBtn = container.querySelector('#clearSelectionBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSelection();
            });
        }

        // Drag-and-drop support
        if (this.options.enableDragDrop && this.canUploadFiles()) {
            this.setupDragAndDrop();
        }

        // File selection (event delegation)
        const contentArea = container.querySelector('#fileExplorerContent');
        if (contentArea) {
            contentArea.addEventListener('click', (e) => {
                const fileItem = e.target.closest('.file-item');
                if (fileItem) {
                    const fileId = fileItem.dataset.fileId;

                    // Check if delete button was clicked
                    if (e.target.closest('.file-delete-btn')) {
                        e.stopPropagation();
                        this.deleteFile(fileId);
                        return;
                    }

                    // Check if download button was clicked
                    if (e.target.closest('.file-download-btn')) {
                        e.stopPropagation();
                        this.downloadFile(fileId);
                        return;
                    }

                    // Check if preview button was clicked
                    if (e.target.closest('.file-preview-btn')) {
                        e.stopPropagation();
                        this.previewFile(fileId);
                        return;
                    }

                    // Otherwise, select file
                    if (this.options.multiSelect && (e.ctrlKey || e.metaKey)) {
                        this.toggleFileSelection(fileId);
                    } else {
                        this.selectFile(fileId);
                    }
                }
            });
        }
    }

    /**
     * Setup drag-and-drop for file upload
     *
     * TECHNICAL IMPLEMENTATION:
     * Integrates with DragDropUpload module
     */
    async setupDragAndDrop() {
        const contentArea = this.container.querySelector('#fileExplorerContent');
        const dropZone = this.container.querySelector('#fileExplorerDropZone');

        if (!contentArea) return;

        // Show drop zone when dragging files over explorer
        ['dragenter', 'dragover'].forEach(eventName => {
            contentArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();

                if (dropZone) {
                    dropZone.style.display = 'flex';
                }
            });
        });

        if (dropZone) {
            dropZone.addEventListener('dragleave', (e) => {
                if (e.target === dropZone) {
                    dropZone.style.display = 'none';
                }
            });

            dropZone.addEventListener('drop', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.display = 'none';

                const files = Array.from(e.dataTransfer.files);
                await this.uploadFiles(files);
            });
        }
    }

    /**
     * Load files from API
     *
     * BUSINESS LOGIC:
     * Fetches files based on current filters (course, organization, type)
     *
     * @returns {Promise<void>}
     */
    async loadFiles() {
        try {
            const authToken = localStorage.getItem('authToken');

            // Build query parameters
            const params = new URLSearchParams();
            if (this.options.courseId) {
                params.append('course_id', this.options.courseId);
            }
            if (this.options.organizationId) {
                params.append('organization_id', this.options.organizationId);
            }
            if (this.options.fileTypes.length > 0) {
                params.append('file_types', this.options.fileTypes.join(','));
            }

            const response = await fetch(
                `${this.options.apiEndpoint}?${params.toString()}`,
                {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                }
            );

            if (!response.ok) {
                // Handle 404 gracefully - just show empty file list
                if (response.status === 404) {
                    console.warn('Files endpoint not found - showing empty file list');
                    this.files = [];
                    this.renderFiles();
                    return;
                }
                throw new Error('Failed to load files');
            }

            this.files = await response.json();
            this.renderFiles();
        } catch (error) {
            console.error('Error loading files:', error);
            this.options.onError(error);
            // Don't show alert - just render empty list
            this.files = [];
            this.renderFiles();
        }
    }

    /**
     * Render file list/grid
     *
     * TECHNICAL IMPLEMENTATION:
     * Renders files in current view mode with appropriate controls
     */
    renderFiles() {
        const contentArea = this.container.querySelector('#fileExplorerContent');
        const fileCount = this.container.querySelector('#fileCount');

        if (!contentArea) return;

        // Sort files
        const sortedFiles = this.sortFiles(this.files);

        // Update file count
        if (fileCount) {
            fileCount.textContent = `${sortedFiles.length} file${sortedFiles.length !== 1 ? 's' : ''}`;
        }

        if (sortedFiles.length === 0) {
            contentArea.innerHTML = `
                <div class="file-explorer-empty">
                    <i class="fas fa-folder-open"></i>
                    <p>No files found</p>
                    ${this.canUploadFiles() ? '<p class="text-muted">Upload files to get started</p>' : ''}
                </div>
            `;
            return;
        }

        // Render based on view mode
        if (this.options.viewMode === 'grid') {
            this.renderGridView(sortedFiles, contentArea);
        } else {
            this.renderListView(sortedFiles, contentArea);
        }
    }

    /**
     * Render files in grid view
     *
     * @param {Array} files - Array of file objects
     * @param {HTMLElement} container - Container element
     */
    renderGridView(files, container) {
        const fileItems = files.map(file => {
            const isSelected = this.selectedFiles.has(file.id);
            const canDelete = this.canDeleteFile(file);

            return `
                <div class="file-item ${isSelected ? 'selected' : ''}" data-file-id="${file.id}">
                    <div class="file-icon">
                        ${this.getFileIcon(file.file_type)}
                    </div>
                    <div class="file-name" title="${this.escapeHtml(file.filename)}">
                        ${this.escapeHtml(this.truncateFilename(file.filename, 20))}
                    </div>
                    <div class="file-meta">
                        <span class="file-size">${this.formatFileSize(file.file_size_bytes)}</span>
                        <span class="file-date">${this.formatDate(file.created_at)}</span>
                    </div>
                    <div class="file-actions">
                        ${this.options.allowPreview ? `
                            <button class="btn-icon file-preview-btn" title="Preview">
                                <i class="fas fa-eye"></i>
                            </button>
                        ` : ''}
                        ${this.options.allowDownload ? `
                            <button class="btn-icon file-download-btn" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        ` : ''}
                        ${canDelete ? `
                            <button class="btn-icon file-delete-btn" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="file-grid">${fileItems}</div>`;
    }

    /**
     * Render files in list view
     *
     * @param {Array} files - Array of file objects
     * @param {HTMLElement} container - Container element
     */
    renderListView(files, container) {
        const fileItems = files.map(file => {
            const isSelected = this.selectedFiles.has(file.id);
            const canDelete = this.canDeleteFile(file);

            return `
                <div class="file-item ${isSelected ? 'selected' : ''}" data-file-id="${file.id}">
                    <div class="file-info-left">
                        <div class="file-icon">
                            ${this.getFileIcon(file.file_type)}
                        </div>
                        <div class="file-details">
                            <div class="file-name">${this.escapeHtml(file.filename)}</div>
                            <div class="file-meta">
                                <span class="file-type">${file.file_type}</span>
                                <span class="file-separator">•</span>
                                <span class="file-size">${this.formatFileSize(file.file_size_bytes)}</span>
                                <span class="file-separator">•</span>
                                <span class="file-date">${this.formatDate(file.created_at)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="file-actions">
                        ${this.options.allowPreview ? `
                            <button class="btn-icon file-preview-btn" title="Preview">
                                <i class="fas fa-eye"></i>
                            </button>
                        ` : ''}
                        ${this.options.allowDownload ? `
                            <button class="btn-icon file-download-btn" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        ` : ''}
                        ${canDelete ? `
                            <button class="btn-icon file-delete-btn" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="file-list">${fileItems}</div>`;
    }

    /**
     * Sort files based on current sort options
     *
     * @param {Array} files - Array of file objects
     * @returns {Array} Sorted files
     */
    sortFiles(files) {
        const sorted = [...files];
        const order = this.options.sortOrder === 'asc' ? 1 : -1;

        sorted.sort((a, b) => {
            let compareA, compareB;

            switch (this.options.sortBy) {
                case 'name':
                    compareA = a.filename.toLowerCase();
                    compareB = b.filename.toLowerCase();
                    return order * compareA.localeCompare(compareB);

                case 'size':
                    compareA = a.file_size_bytes || 0;
                    compareB = b.file_size_bytes || 0;
                    return order * (compareA - compareB);

                case 'type':
                    compareA = a.file_type || '';
                    compareB = b.file_type || '';
                    return order * compareA.localeCompare(compareB);

                case 'date':
                default:
                    compareA = new Date(a.created_at || 0).getTime();
                    compareB = new Date(b.created_at || 0).getTime();
                    return order * (compareA - compareB);
            }
        });

        return sorted;
    }

    /**
     * Delete a specific file
     *
     * BUSINESS LOGIC - AUTHORIZATION:
     * Checks user permissions before allowing deletion
     * Tracks deletion in metadata service
     *
     * @param {string} fileId - File ID to delete
     * @returns {Promise<void>}
     */
    async deleteFile(fileId) {
        const file = this.files.find(f => f.id === fileId);
        if (!file) return;

        // Authorization check
        if (!this.canDeleteFile(file)) {
            this.showError('You do not have permission to delete this file.');
            return;
        }

        // Confirmation dialog
        if (!confirm(`Are you sure you want to delete "${file.filename}"?`)) {
            return;
        }

        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(
                `${this.options.apiEndpoint}/${fileId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to delete file');
            }

            // Track deletion in metadata
            await this.trackFileDeletion(file);

            // Remove from local state
            this.files = this.files.filter(f => f.id !== fileId);
            this.selectedFiles.delete(fileId);

            // Re-render
            this.renderFiles();
            this.updateSelectionInfo();

            // Callback
            this.options.onFileDelete(file);

            this.showSuccess(`File "${file.filename}" deleted successfully`);
        } catch (error) {
            console.error('Error deleting file:', error);
            this.options.onError(error);
            this.showError('Failed to delete file. Please try again.');
        }
    }

    /**
     * Delete multiple selected files
     *
     * BUSINESS LOGIC - AUTHORIZATION:
     * Only deletes files user has permission to delete
     *
     * @returns {Promise<void>}
     */
    async deleteSelected() {
        const selectedFileIds = Array.from(this.selectedFiles);
        const filesToDelete = this.files.filter(f => selectedFileIds.includes(f.id));

        // Filter by permission
        const deletableFiles = filesToDelete.filter(f => this.canDeleteFile(f));

        if (deletableFiles.length === 0) {
            this.showError('You do not have permission to delete any of the selected files.');
            return;
        }

        const undeletableCount = filesToDelete.length - deletableFiles.length;
        let message = `Are you sure you want to delete ${deletableFiles.length} file(s)?`;

        if (undeletableCount > 0) {
            message += `\n\nNote: ${undeletableCount} file(s) will be skipped due to permissions.`;
        }

        if (!confirm(message)) {
            return;
        }

        // Delete files in parallel
        const deletePromises = deletableFiles.map(file => this.deleteFile(file.id));

        try {
            await Promise.all(deletePromises);
            this.clearSelection();
        } catch (error) {
            console.error('Error deleting files:', error);
            this.showError('Some files failed to delete. Please try again.');
        }
    }

    /**
     * Track file deletion in metadata service
     *
     * @param {Object} file - File object
     * @returns {Promise<void>}
     */
    async trackFileDeletion(file) {
        const authToken = localStorage.getItem('authToken');

        try {
            await fetch(`${CONFIG.ENDPOINTS.METADATA_SERVICE}/metadata`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    entity_id: file.id,
                    entity_type: 'file_deletion',
                    tags: ['file_operation', 'deletion', file.file_type],
                    metadata: {
                        filename: file.filename,
                        file_type: file.file_type,
                        file_size_bytes: file.file_size_bytes,
                        deleted_by: this.currentUser.id,
                        deletion_timestamp: new Date().toISOString(),
                        course_id: file.course_id,
                        organization_id: file.organization_id
                    }
                })
            });
        } catch (error) {
            console.error('Failed to track file deletion:', error);
            // Non-critical error - don't fail the deletion
        }
    }

    /**
     * Download a specific file
     *
     * @param {string} fileId - File ID to download
     */
    async downloadFile(fileId) {
        const file = this.files.find(f => f.id === fileId);
        if (!file) return;

        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(
                `${this.options.apiEndpoint}/${fileId}/download`,
                {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to download file');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // Track download
            await this.trackFileDownload(file);
        } catch (error) {
            console.error('Error downloading file:', error);
            this.showError('Failed to download file. Please try again.');
        }
    }

    /**
     * Download multiple selected files
     */
    async downloadSelected() {
        const selectedFileIds = Array.from(this.selectedFiles);
        const downloadPromises = selectedFileIds.map(id => this.downloadFile(id));

        try {
            await Promise.all(downloadPromises);
        } catch (error) {
            console.error('Error downloading files:', error);
        }
    }

    /**
     * Track file download in metadata service
     *
     * @param {Object} file - File object
     * @returns {Promise<void>}
     */
    async trackFileDownload(file) {
        const authToken = localStorage.getItem('authToken');

        try {
            await fetch(`${CONFIG.ENDPOINTS.METADATA_SERVICE}/metadata`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    entity_id: file.course_id || file.organization_id,
                    entity_type: 'course_material_download',
                    tags: [file.file_type, 'file_download'],
                    metadata: {
                        file_type: file.file_type,
                        filename: file.filename,
                        file_size_bytes: file.file_size_bytes,
                        downloaded_by: this.currentUser.id,
                        download_timestamp: new Date().toISOString()
                    }
                })
            });
        } catch (error) {
            console.error('Failed to track file download:', error);
        }
    }

    /**
     * Preview a file
     *
     * @param {string} fileId - File ID to preview
     */
    async previewFile(fileId) {
        const file = this.files.find(f => f.id === fileId);
        if (!file) return;

        // TODO: Implement file preview modal
        console.log('Preview file:', file);
        this.showInfo(`Preview for ${file.filename} - Feature coming soon!`);
    }

    /**
     * Show upload dialog
     */
    async showUploadDialog() {
        // Dynamically import DragDropUpload module
        try {
            const { DragDropUpload } = await import('./drag-drop-upload.js');

            // Create modal
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3><i class="fas fa-upload"></i> Upload Files</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div id="uploadDropZone"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Setup drag-drop
            const dropZone = modal.querySelector('#uploadDropZone');
            new DragDropUpload(dropZone, {
                uploadEndpoint: this.options.uploadEndpoint,
                onUploadComplete: async (response, file) => {
                    await this.loadFiles();
                    this.options.onFileUpload(response, file);
                }
            });

            // Close button
            modal.querySelector('.modal-close').addEventListener('click', () => {
                modal.remove();
            });

            // Click outside to close
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        } catch (error) {
            console.error('Failed to load upload module:', error);
            this.showError('Failed to open upload dialog.');
        }
    }

    /**
     * Upload files programmatically
     *
     * @param {Array<File>} files - Array of File objects
     */
    async uploadFiles(files) {
        // TODO: Implement bulk upload
        console.log('Upload files:', files);
    }

    /**
     * Select a file
     *
     * @param {string} fileId - File ID
     */
    selectFile(fileId) {
        if (!this.options.multiSelect) {
            this.selectedFiles.clear();
        }
        this.selectedFiles.add(fileId);
        this.updateSelectionUI();

        const file = this.files.find(f => f.id === fileId);
        this.options.onFileSelect(file);
    }

    /**
     * Toggle file selection
     *
     * @param {string} fileId - File ID
     */
    toggleFileSelection(fileId) {
        if (this.selectedFiles.has(fileId)) {
            this.selectedFiles.delete(fileId);
        } else {
            this.selectedFiles.add(fileId);
        }
        this.updateSelectionUI();
    }

    /**
     * Clear all selections
     */
    clearSelection() {
        this.selectedFiles.clear();
        this.updateSelectionUI();
    }

    /**
     * Update selection UI state
     */
    updateSelectionUI() {
        // Update selected class on file items
        this.container.querySelectorAll('.file-item').forEach(item => {
            const fileId = item.dataset.fileId;
            if (this.selectedFiles.has(fileId)) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });

        this.updateSelectionInfo();
    }

    /**
     * Update selection info display
     */
    updateSelectionInfo() {
        const selectionInfo = this.container.querySelector('#selectionInfo');
        const actionsPanel = this.container.querySelector('#fileActionsPanel');
        const selectedCount = this.container.querySelector('#selectedCount');

        if (this.selectedFiles.size > 0) {
            if (selectionInfo) {
                selectionInfo.textContent = `${this.selectedFiles.size} selected`;
                selectionInfo.style.display = 'inline';
            }
            if (actionsPanel) {
                actionsPanel.style.display = 'flex';
            }
            if (selectedCount) {
                selectedCount.textContent = `${this.selectedFiles.size} selected`;
            }
        } else {
            if (selectionInfo) {
                selectionInfo.style.display = 'none';
            }
            if (actionsPanel) {
                actionsPanel.style.display = 'none';
            }
        }
    }

    /**
     * Set view mode (grid or list)
     *
     * @param {string} mode - 'grid' or 'list'
     */
    setViewMode(mode) {
        this.options.viewMode = mode;
        const explorer = this.container.querySelector('.file-explorer');
        if (explorer) {
            explorer.dataset.viewMode = mode;
        }

        // Update button states
        this.container.querySelectorAll('.view-mode-btn').forEach(btn => {
            if (btn.dataset.view === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        this.renderFiles();
    }

    /**
     * Toggle sort order
     */
    toggleSortOrder() {
        this.options.sortOrder = this.options.sortOrder === 'asc' ? 'desc' : 'asc';

        const btn = this.container.querySelector('#sortOrderBtn');
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = this.options.sortOrder === 'asc'
                    ? 'fas fa-sort-amount-up'
                    : 'fas fa-sort-amount-down';
            }
        }

        this.renderFiles();
    }

    /**
     * Get file icon based on type
     *
     * BUSINESS CONTEXT:
     * Provides visual file type indicators for all supported formats
     *
     * Supported file types:
     * - MS Office: Word (.doc, .docx), Excel (.xls, .xlsx), PowerPoint (.ppt, .pptx)
     * - LibreOffice: Writer (.odt), Calc (.ods), Impress (.odp)
     * - Documents: PDF, HTML, XML
     * - Data: JSON
     * - Images: JPG, GIF, PNG, SVG, BMP
     * - Video: MP4, MKV, AVI, MPG/MPEG
     * - Audio: WAV, MP3, OGG
     *
     * @param {string} type - File MIME type or extension
     * @returns {string} HTML for icon
     */
    getFileIcon(type) {
        if (!type) return '<i class="fas fa-file"></i>';

        const typeLower = type.toLowerCase();

        // Images
        if (typeLower.includes('image/jpeg') || typeLower.includes('.jpg') || typeLower.includes('.jpeg'))
            return '<i class="fas fa-file-image" style="color: #4CAF50;"></i>';
        if (typeLower.includes('image/gif') || typeLower.includes('.gif'))
            return '<i class="fas fa-file-image" style="color: #9C27B0;"></i>';
        if (typeLower.includes('image/png') || typeLower.includes('.png'))
            return '<i class="fas fa-file-image" style="color: #2196F3;"></i>';
        if (typeLower.includes('image/svg') || typeLower.includes('.svg'))
            return '<i class="fas fa-file-code" style="color: #FF9800;"></i>';
        if (typeLower.includes('image/bmp') || typeLower.includes('.bmp'))
            return '<i class="fas fa-file-image" style="color: #FF5722;"></i>';
        if (typeLower.startsWith('image/'))
            return '<i class="fas fa-file-image"></i>';

        // PDF
        if (typeLower.includes('pdf') || typeLower.includes('.pdf'))
            return '<i class="fas fa-file-pdf" style="color: #F44336;"></i>';

        // MS Word
        if (typeLower.includes('word') || typeLower.includes('msword') ||
            typeLower.includes('.doc') || typeLower.includes('.docx') ||
            typeLower.includes('wordprocessingml'))
            return '<i class="fas fa-file-word" style="color: #2B579A;"></i>';

        // MS Excel
        if (typeLower.includes('excel') || typeLower.includes('spreadsheet') ||
            typeLower.includes('.xls') || typeLower.includes('.xlsx') ||
            typeLower.includes('spreadsheetml'))
            return '<i class="fas fa-file-excel" style="color: #217346;"></i>';

        // MS PowerPoint
        if (typeLower.includes('powerpoint') || typeLower.includes('presentation') ||
            typeLower.includes('.ppt') || typeLower.includes('.pptx') ||
            typeLower.includes('presentationml'))
            return '<i class="fas fa-file-powerpoint" style="color: #D24726;"></i>';

        // LibreOffice Writer (.odt)
        if (typeLower.includes('.odt') || typeLower.includes('opendocument.text'))
            return '<i class="fas fa-file-word" style="color: #0369A3;"></i>';

        // LibreOffice Calc (.ods)
        if (typeLower.includes('.ods') || typeLower.includes('opendocument.spreadsheet'))
            return '<i class="fas fa-file-excel" style="color: #18A303;"></i>';

        // LibreOffice Impress (.odp)
        if (typeLower.includes('.odp') || typeLower.includes('opendocument.presentation'))
            return '<i class="fas fa-file-powerpoint" style="color: #C8102E;"></i>';

        // HTML
        if (typeLower.includes('html') || typeLower.includes('.html') || typeLower.includes('.htm'))
            return '<i class="fas fa-file-code" style="color: #E34F26;"></i>';

        // XML
        if (typeLower.includes('xml') || typeLower.includes('.xml'))
            return '<i class="fas fa-file-code" style="color: #005FAD;"></i>';

        // JSON
        if (typeLower.includes('json') || typeLower.includes('.json'))
            return '<i class="fas fa-file-code" style="color: #FFA000;"></i>';

        // Video - specific formats
        if (typeLower.includes('video/mp4') || typeLower.includes('.mp4'))
            return '<i class="fas fa-file-video" style="color: #E91E63;"></i>';
        if (typeLower.includes('video/x-matroska') || typeLower.includes('.mkv'))
            return '<i class="fas fa-file-video" style="color: #9C27B0;"></i>';
        if (typeLower.includes('video/x-msvideo') || typeLower.includes('.avi'))
            return '<i class="fas fa-file-video" style="color: #673AB7;"></i>';
        if (typeLower.includes('video/mpeg') || typeLower.includes('.mpg') || typeLower.includes('.mpeg'))
            return '<i class="fas fa-file-video" style="color: #3F51B5;"></i>';
        if (typeLower.startsWith('video/'))
            return '<i class="fas fa-file-video" style="color: #9C27B0;"></i>';

        // Audio - specific formats
        if (typeLower.includes('audio/wav') || typeLower.includes('.wav'))
            return '<i class="fas fa-file-audio" style="color: #00BCD4;"></i>';
        if (typeLower.includes('audio/mpeg') || typeLower.includes('.mp3'))
            return '<i class="fas fa-file-audio" style="color: #009688;"></i>';
        if (typeLower.includes('audio/ogg') || typeLower.includes('.ogg'))
            return '<i class="fas fa-file-audio" style="color: #4CAF50;"></i>';
        if (typeLower.startsWith('audio/'))
            return '<i class="fas fa-file-audio" style="color: #3F51B5;"></i>';

        // Archives
        if (typeLower.includes('zip') || typeLower.includes('compressed') ||
            typeLower.includes('archive') || typeLower.includes('.rar') ||
            typeLower.includes('.7z') || typeLower.includes('.tar') || typeLower.includes('.gz'))
            return '<i class="fas fa-file-archive" style="color: #795548;"></i>';

        // Plain text
        if (typeLower.includes('text') || typeLower.includes('.txt'))
            return '<i class="fas fa-file-alt" style="color: #607D8B;"></i>';

        // Default
        return '<i class="fas fa-file"></i>';
    }

    /**
     * Format file size for display
     *
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted size
     */
    formatFileSize(bytes) {
        if (!bytes) return '0 B';

        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    /**
     * Format date for display
     *
     * @param {string} dateStr - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    /**
     * Truncate filename for display
     *
     * @param {string} filename - Original filename
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated filename
     */
    truncateFilename(filename, maxLength) {
        if (filename.length <= maxLength) {
            return filename;
        }

        const ext = filename.substring(filename.lastIndexOf('.'));
        const name = filename.substring(0, filename.lastIndexOf('.'));
        const truncated = name.substring(0, maxLength - ext.length - 3) + '...';

        return truncated + ext;
    }

    /**
     * Escape HTML to prevent XSS
     *
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Show error notification
     *
     * @param {string} message - Error message
     */
    showError(message) {
        // TODO: Integrate with notification system
        alert(message);
    }

    /**
     * Show success notification
     *
     * @param {string} message - Success message
     */
    showSuccess(message) {
        // TODO: Integrate with notification system
        console.log('Success:', message);
    }

    /**
     * Show info notification
     *
     * @param {string} message - Info message
     */
    showInfo(message) {
        // TODO: Integrate with notification system
        alert(message);
    }

    /**
     * Add CSS styles for file explorer
     *
     * TECHNICAL IMPLEMENTATION:
     * Injects styles dynamically to avoid CSS file dependencies
     */
    addStyles() {
        if (document.getElementById('file-explorer-styles')) {
            return; // Already added
        }

        const style = document.createElement('style');
        style.id = 'file-explorer-styles';
        style.textContent = `
            /* File Explorer Styles */
            .file-explorer {
                background: var(--card-background, #fff);
                border: 1px solid var(--border-color, #ddd);
                border-radius: 8px;
                padding: 1rem;
                min-height: 400px;
            }

            .file-explorer-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                padding-bottom: 0.75rem;
                border-bottom: 1px solid var(--border-color, #ddd);
            }

            .toolbar-left,
            .toolbar-right {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .toolbar-divider {
                width: 1px;
                height: 24px;
                background: var(--border-color, #ddd);
                margin: 0 0.5rem;
            }

            .btn-icon {
                padding: 0.5rem;
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-icon:hover {
                background: var(--hover-color, #f5f5f5);
                border-color: var(--border-color, #ddd);
            }

            .btn-icon.active {
                background: var(--primary-color, #007bff);
                color: white;
            }

            .sort-select {
                padding: 0.5rem;
                border: 1px solid var(--border-color, #ddd);
                border-radius: 4px;
                background: white;
                cursor: pointer;
            }

            .file-explorer-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                font-size: 0.875rem;
                color: var(--text-muted, #666);
            }

            .file-explorer-content {
                min-height: 300px;
                position: relative;
            }

            .file-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 1rem;
            }

            .file-list {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .file-item {
                border: 1px solid var(--border-color, #ddd);
                border-radius: 8px;
                padding: 1rem;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
            }

            .file-item:hover {
                border-color: var(--primary-color, #007bff);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .file-item.selected {
                border-color: var(--primary-color, #007bff);
                background: rgba(0, 123, 255, 0.05);
            }

            /* Grid view styles */
            .file-explorer[data-view-mode="grid"] .file-item {
                text-align: center;
            }

            .file-explorer[data-view-mode="grid"] .file-icon {
                font-size: 3rem;
                color: var(--primary-color, #007bff);
                margin-bottom: 0.5rem;
            }

            .file-explorer[data-view-mode="grid"] .file-name {
                font-weight: 500;
                margin-bottom: 0.5rem;
                word-break: break-word;
            }

            .file-explorer[data-view-mode="grid"] .file-meta {
                font-size: 0.75rem;
                color: var(--text-muted, #666);
            }

            .file-explorer[data-view-mode="grid"] .file-actions {
                display: flex;
                justify-content: center;
                gap: 0.25rem;
                margin-top: 0.5rem;
                opacity: 0;
                transition: opacity 0.2s;
            }

            .file-explorer[data-view-mode="grid"] .file-item:hover .file-actions {
                opacity: 1;
            }

            /* List view styles */
            .file-explorer[data-view-mode="list"] .file-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .file-explorer[data-view-mode="list"] .file-info-left {
                display: flex;
                align-items: center;
                gap: 1rem;
                flex: 1;
            }

            .file-explorer[data-view-mode="list"] .file-icon {
                font-size: 2rem;
                color: var(--primary-color, #007bff);
            }

            .file-explorer[data-view-mode="list"] .file-name {
                font-weight: 500;
                margin-bottom: 0.25rem;
            }

            .file-explorer[data-view-mode="list"] .file-meta {
                font-size: 0.75rem;
                color: var(--text-muted, #666);
            }

            .file-explorer[data-view-mode="list"] .file-separator {
                margin: 0 0.5rem;
            }

            .file-explorer[data-view-mode="list"] .file-actions {
                display: flex;
                gap: 0.25rem;
            }

            .file-actions-panel {
                position: fixed;
                bottom: 2rem;
                left: 50%;
                transform: translateX(-50%);
                background: white;
                border: 1px solid var(--border-color, #ddd);
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 2rem;
                min-width: 400px;
                z-index: 1000;
            }

            .file-explorer-drop-zone {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 123, 255, 0.1);
                border: 3px dashed var(--primary-color, #007bff);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
            }

            .drop-zone-content {
                text-align: center;
                color: var(--primary-color, #007bff);
            }

            .drop-zone-content i {
                font-size: 4rem;
                margin-bottom: 1rem;
            }

            .file-explorer-loading,
            .file-explorer-empty {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 300px;
                color: var(--text-muted, #666);
            }

            .file-explorer-empty i {
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }

            .loading-spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid var(--primary-color, #007bff);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin-bottom: 1rem;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            @media (max-width: 768px) {
                .file-grid {
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                }

                .file-actions-panel {
                    flex-direction: column;
                    min-width: auto;
                    width: 90%;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Export for use in other modules
export default FileExplorer;
