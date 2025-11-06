/**
 * Drag and Drop File Upload Module
 *
 * BUSINESS REQUIREMENT:
 * Provide intuitive drag-and-drop interface for file uploads across platform
 *
 * FEATURES:
 * - Visual feedback during drag operations
 * - File type validation
 * - Size limit enforcement
 * - Progress indication
 * - Multiple file support
 */
export class DragDropUpload {
    /**
     * Initialize drag-and-drop upload component
     *
     * @param {HTMLElement} dropZone - Container element for drop zone
     * @param {Object} options - Configuration options
     */
    constructor(dropZone, options = {}) {
        this.dropZone = dropZone;
        this.options = {
            acceptedTypes: options.acceptedTypes || ['*/*'],
            maxSizeMB: options.maxSizeMB || 50,
            multiple: options.multiple || false,
            uploadEndpoint: options.uploadEndpoint || '',
            onUploadStart: options.onUploadStart || (() => {}),
            onUploadProgress: options.onUploadProgress || (() => {}),
            onUploadComplete: options.onUploadComplete || (() => {}),
            onUploadError: options.onUploadError || (() => {})
        };

        this.setupDropZone();
        this.attachEventListeners();
    }

    /**
     * Set up drop zone visual styling and structure
     */
    setupDropZone() {
        this.dropZone.classList.add('drag-drop-zone');
        this.dropZone.innerHTML = `
            <div class="drag-drop-content">
                <i class="fas fa-cloud-upload-alt drag-drop-icon"></i>
                <p class="drag-drop-text">
                    <strong>Drag & Drop files here</strong><br>
                    or <span class="drag-drop-browse">browse</span>
                </p>
                <p class="drag-drop-hint">
                    Supported: ${this.formatAcceptedTypes()}<br>
                    Maximum size: ${this.options.maxSizeMB} MB
                </p>
                <input type="file"
                       class="drag-drop-input"
                       ${this.options.multiple ? 'multiple' : ''}
                       accept="${this.options.acceptedTypes.join(',')}"
                       style="display: none;">
            </div>
            <div class="drag-drop-progress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <p class="progress-text">Uploading...</p>
            </div>
        `;

        this.fileInput = this.dropZone.querySelector('.drag-drop-input');
        this.browseButton = this.dropZone.querySelector('.drag-drop-browse');
        this.progressContainer = this.dropZone.querySelector('.drag-drop-progress');
        this.progressFill = this.dropZone.querySelector('.progress-fill');
        this.progressText = this.dropZone.querySelector('.progress-text');
    }

    /**
     * Attach all event listeners for drag-and-drop functionality
     */
    attachEventListeners() {
        // Prevent default drag behaviors on document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.highlight(), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.unhighlight(), false);
        });

        // Handle dropped files
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);

        // Browse button click
        this.browseButton.addEventListener('click', () => this.fileInput.click());

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFiles(e.target.files);
            }
        });
    }

    /**
     * Prevent default drag behaviors
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Highlight drop zone on drag over
     */
    highlight() {
        this.dropZone.classList.add('drag-over');
    }

    /**
     * Remove highlight from drop zone
     */
    unhighlight() {
        this.dropZone.classList.remove('drag-over');
    }

    /**
     * Handle file drop event
     *
     * @param {DragEvent} e - Drop event
     */
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    /**
     * Process selected/dropped files
     *
     * @param {FileList} files - Files to upload
     */
    async handleFiles(files) {
        const filesArray = Array.from(files);

        // Validate files
        const validFiles = filesArray.filter(file => this.validateFile(file));

        if (validFiles.length === 0) {
            this.options.onUploadError(new Error('No valid files selected'));
            return;
        }

        // Upload files
        for (const file of validFiles) {
            await this.uploadFile(file);
        }
    }

    /**
     * Validate file size and type
     *
     * @param {File} file - File to validate
     * @returns {boolean} - True if valid
     */
    validateFile(file) {
        // Check file size
        const fileSizeMB = file.size / (1024 * 1024);
        if (fileSizeMB > this.options.maxSizeMB) {
            this.options.onUploadError(
                new Error(`File "${file.name}" exceeds ${this.options.maxSizeMB} MB limit`)
            );
            return false;
        }

        // Check file type if specific types are required
        if (this.options.acceptedTypes[0] !== '*/*') {
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            const isAccepted = this.options.acceptedTypes.some(type =>
                type === fileExtension || type === file.type
            );

            if (!isAccepted) {
                this.options.onUploadError(
                    new Error(`File type "${fileExtension}" is not supported`)
                );
                return false;
            }
        }

        return true;
    }

    /**
     * Upload file to server
     *
     * @param {File} file - File to upload
     */
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        this.showProgress();
        this.options.onUploadStart(file);

        try {
            const authToken = localStorage.getItem('authToken');

            const xhr = new XMLHttpRequest();

            // Progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(percentComplete, file.name);
                    this.options.onUploadProgress(percentComplete, file);
                }
            });

            // Upload complete
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    const response = JSON.parse(xhr.responseText);
                    this.hideProgress();
                    this.options.onUploadComplete(response, file);
                    this.resetFileInput();
                } else {
                    throw new Error(`Upload failed with status ${xhr.status}`);
                }
            });

            // Upload error
            xhr.addEventListener('error', () => {
                this.hideProgress();
                this.options.onUploadError(new Error('Upload failed'));
            });

            xhr.open('POST', this.options.uploadEndpoint);
            xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
            xhr.send(formData);

        } catch (error) {
            this.hideProgress();
            this.options.onUploadError(error);
        }
    }

    /**
     * Show upload progress UI
     */
    showProgress() {
        this.dropZone.querySelector('.drag-drop-content').style.display = 'none';
        this.progressContainer.style.display = 'block';
    }

    /**
     * Update progress bar
     *
     * @param {number} percent - Progress percentage
     * @param {string} filename - Filename being uploaded
     */
    updateProgress(percent, filename) {
        this.progressFill.style.width = `${percent}%`;
        this.progressText.textContent = `Uploading ${filename}... ${Math.round(percent)}%`;
    }

    /**
     * Hide upload progress UI
     */
    hideProgress() {
        setTimeout(() => {
            this.progressContainer.style.display = 'none';
            this.dropZone.querySelector('.drag-drop-content').style.display = 'block';
            this.progressFill.style.width = '0%';
        }, 1000);
    }

    /**
     * Reset file input
     */
    resetFileInput() {
        this.fileInput.value = '';
    }

    /**
     * Format accepted file types for display
     *
     * @returns {string} - Human-readable accepted types
     */
    formatAcceptedTypes() {
        if (this.options.acceptedTypes[0] === '*/*') {
            return 'All files';
        }
        return this.options.acceptedTypes.join(', ');
    }

    /**
     * Destroy drag-and-drop instance
     */
    destroy() {
        this.dropZone.innerHTML = '';
        this.dropZone.classList.remove('drag-drop-zone', 'drag-over');
    }
}

export default DragDropUpload;
