/**
 * Bulk Enrollment JavaScript
 *
 * Handles file upload, validation, and enrollment for bulk student operations.
 */

// Configuration
const CONFIG = {
    API_BASE_URL: 'https://localhost:8001',
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    SUPPORTED_EXTENSIONS: ['.csv', '.xlsx', '.xls', '.ods'],
    SUPPORTED_MIME_TYPES: [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.oasis.opendocument.spreadsheet'
    ]
};

// State
let selectedFile = null;
let enrollmentType = 'course';
let selectedId = null;

// DOM Elements
const elements = {
    // Upload area
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    browseButton: document.getElementById('browseButton'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),
    uploadButton: document.getElementById('uploadButton'),

    // Enrollment type
    enrollmentTypeRadios: document.querySelectorAll('input[name="enrollmentType"]'),
    courseSelection: document.getElementById('courseSelection'),
    trackSelection: document.getElementById('trackSelection'),
    courseSelect: document.getElementById('courseSelect'),
    trackSelect: document.getElementById('trackSelect'),

    // Progress
    progressPanel: document.getElementById('progressPanel'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),

    // Results
    resultsPanel: document.getElementById('resultsPanel'),
    successCount: document.getElementById('successCount'),
    failedCount: document.getElementById('failedCount'),
    totalCount: document.getElementById('totalCount'),
    processingTime: document.getElementById('processingTime'),
    createdCount: document.getElementById('createdCount'),
    skippedCount: document.getElementById('skippedCount'),
    errorsCount: document.getElementById('errorsCount'),
    validRecords: document.getElementById('validRecords'),
    invalidRecords: document.getElementById('invalidRecords'),
    validationRate: document.getElementById('validationRate'),

    // Buttons
    downloadTemplate: document.getElementById('downloadTemplate'),
    closeResults: document.getElementById('closeResults'),
    enrollMore: document.getElementById('enrollMore'),
    downloadReport: document.getElementById('downloadReport'),

    // Alert
    errorAlert: document.getElementById('errorAlert'),
    errorMessage: document.getElementById('errorMessage'),
    closeError: document.getElementById('closeError')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadCourses();
    loadTracks();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Upload area events
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // File input
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.removeFile.addEventListener('click', removeFile);
    elements.uploadButton.addEventListener('click', uploadFile);

    // Enrollment type
    elements.enrollmentTypeRadios.forEach(radio => {
        radio.addEventListener('change', handleEnrollmentTypeChange);
    });

    // Course/track selection
    elements.courseSelect.addEventListener('change', handleCourseSelect);
    elements.trackSelect.addEventListener('change', handleTrackSelect);

    // Template download
    elements.downloadTemplate.addEventListener('click', downloadTemplate);

    // Results actions
    elements.closeResults.addEventListener('click', closeResults);
    elements.enrollMore.addEventListener('click', resetForm);
    elements.downloadReport.addEventListener('click', downloadReport);

    // Alert
    elements.closeError.addEventListener('click', closeError);

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
}

/**
 * Load available courses
 */
async function loadCourses() {
    try {
        const token = getAuthToken();
        const response = await fetch(`${CONFIG.API_BASE_URL}/courses?instructor_id=${getCurrentUserId()}&published_only=false`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load courses');

        const courses = await response.json();
        populateCourseSelect(courses);
    } catch (error) {
        console.error('Error loading courses:', error);
        showError('Failed to load courses. Please refresh the page.');
    }
}

/**
 * Load available tracks
 */
async function loadTracks() {
    try {
        const token = getAuthToken();
        const response = await fetch(`${CONFIG.API_BASE_URL}/tracks`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load tracks');

        const tracks = await response.json();
        populateTrackSelect(tracks);
    } catch (error) {
        console.error('Error loading tracks:', error);
        // Track loading is optional, so don't show error
    }
}

/**
 * Populate course select dropdown
 */
function populateCourseSelect(courses) {
    elements.courseSelect.innerHTML = '<option value="">-- Select a course --</option>';
    courses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.id;
        option.textContent = course.title;
        elements.courseSelect.appendChild(option);
    });
}

/**
 * Populate track select dropdown
 */
function populateTrackSelect(tracks) {
    elements.trackSelect.innerHTML = '<option value="">-- Select a track --</option>';
    tracks.forEach(track => {
        const option = document.createElement('option');
        option.value = track.id;
        option.textContent = track.name;
        elements.trackSelect.appendChild(option);
    });
}

/**
 * Handle enrollment type change
 */
function handleEnrollmentTypeChange(event) {
    enrollmentType = event.target.value;

    if (enrollmentType === 'course') {
        elements.courseSelection.style.display = 'block';
        elements.trackSelection.style.display = 'none';
        selectedId = elements.courseSelect.value;
    } else {
        elements.courseSelection.style.display = 'none';
        elements.trackSelection.style.display = 'block';
        selectedId = elements.trackSelect.value;
    }

    updateUploadButtonState();
}

/**
 * Handle course selection
 */
function handleCourseSelect(event) {
    selectedId = event.target.value;
    updateUploadButtonState();
}

/**
 * Handle track selection
 */
function handleTrackSelect(event) {
    selectedId = event.target.value;
    updateUploadButtonState();
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
    event.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

/**
 * Handle file drop event
 */
function handleDrop(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

/**
 * Handle file selection
 */
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

/**
 * Handle file validation and display
 */
function handleFile(file) {
    // Validate file size
    if (file.size > CONFIG.MAX_FILE_SIZE) {
        showError(`File is too large. Maximum size is ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB`);
        return;
    }

    // Validate file type
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!CONFIG.SUPPORTED_EXTENSIONS.includes(extension)) {
        showError(`Unsupported file type. Supported formats: ${CONFIG.SUPPORTED_EXTENSIONS.join(', ')}`);
        return;
    }

    // Store file
    selectedFile = file;

    // Display file info
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.uploadArea.style.display = 'none';
    elements.fileInfo.style.display = 'flex';

    updateUploadButtonState();
}

/**
 * Remove selected file
 */
function removeFile() {
    selectedFile = null;
    elements.fileInput.value = '';
    elements.uploadArea.style.display = 'block';
    elements.fileInfo.style.display = 'none';
    updateUploadButtonState();
}

/**
 * Update upload button state
 */
function updateUploadButtonState() {
    elements.uploadButton.disabled = !selectedFile || !selectedId;
}

/**
 * Upload file and process enrollment
 */
async function uploadFile() {
    if (!selectedFile || !selectedId) return;

    // Show progress
    showProgress('Uploading file...', 10);

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Get auth token
        const token = getAuthToken();

        // Determine endpoint
        const endpoint = enrollmentType === 'course'
            ? `/courses/${selectedId}/bulk-enroll`
            : `/tracks/${selectedId}/bulk-enroll`;

        // Update progress
        showProgress('Processing enrollment...', 30);

        // Make API call
        const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        // Update progress
        showProgress('Finalizing...', 80);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Enrollment failed');
        }

        const result = await response.json();

        // Update progress
        showProgress('Complete!', 100);

        // Show results
        setTimeout(() => {
            hideProgress();
            showResults(result);
        }, 500);

    } catch (error) {
        console.error('Upload error:', error);
        hideProgress();
        showError(error.message || 'Failed to upload file. Please try again.');
    }
}

/**
 * Show progress panel
 */
function showProgress(text, percentage) {
    elements.progressPanel.style.display = 'block';
    elements.progressText.textContent = text;
    elements.progressFill.style.width = `${percentage}%`;

    // Scroll to progress
    elements.progressPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Hide progress panel
 */
function hideProgress() {
    elements.progressPanel.style.display = 'none';
}

/**
 * Show results panel
 */
function showResults(result) {
    // Update summary cards
    elements.successCount.textContent = result.successful_enrollments;
    elements.failedCount.textContent = result.failed_enrollments;
    elements.totalCount.textContent = result.total_students;
    elements.processingTime.textContent = `${Math.round(result.processing_time_ms)}ms`;

    // Update counts
    elements.createdCount.textContent = result.created_accounts.length;
    elements.skippedCount.textContent = result.skipped_accounts.length;
    elements.errorsCount.textContent = result.errors.length;

    // Update validation summary
    if (result.metadata.validation_summary) {
        const vs = result.metadata.validation_summary;
        elements.validRecords.textContent = vs.valid_count;
        elements.invalidRecords.textContent = vs.invalid_count;
        elements.validationRate.textContent = `${vs.validation_rate.toFixed(1)}%`;
    }

    // Populate tables
    populateCreatedTable(result.created_accounts);
    populateSkippedTable(result.skipped_accounts);
    populateErrorsTable(result.errors);

    // Show results panel
    elements.resultsPanel.style.display = 'block';
    elements.resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Store results for download
    window.enrollmentResults = result;
}

/**
 * Populate created accounts table
 */
function populateCreatedTable(accounts) {
    const tbody = document.querySelector('#createdTable tbody');
    tbody.innerHTML = '';

    if (accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary);">No new accounts created</td></tr>';
        return;
    }

    accounts.forEach(account => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${account.email}</td>
            <td>${account.first_name || ''} ${account.last_name || ''}</td>
            <td>${account.id}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Populate skipped accounts table
 */
function populateSkippedTable(accounts) {
    const tbody = document.querySelector('#skippedTable tbody');
    tbody.innerHTML = '';

    if (accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: var(--text-secondary);">No accounts skipped</td></tr>';
        return;
    }

    accounts.forEach(account => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${account.email}</td>
            <td>${account.reason}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Populate errors table
 */
function populateErrorsTable(errors) {
    const tbody = document.querySelector('#errorsTable tbody');
    tbody.innerHTML = '';

    if (errors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: var(--text-secondary);">No errors</td></tr>';
        return;
    }

    errors.forEach(error => {
        const row = document.createElement('tr');
        const errorDetails = error.errors
            ? Object.entries(error.errors).map(([field, msg]) => `${field}: ${msg}`).join(', ')
            : error.error || 'Unknown error';

        row.innerHTML = `
            <td>${error.student.email}</td>
            <td>${errorDetails}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Switch between result tabs
 */
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

/**
 * Close results panel
 */
function closeResults() {
    elements.resultsPanel.style.display = 'none';
}

/**
 * Reset form for new enrollment
 */
function resetForm() {
    removeFile();
    closeResults();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Download enrollment report as CSV
 */
function downloadReport() {
    if (!window.enrollmentResults) return;

    const result = window.enrollmentResults;
    let csv = 'Status,Email,Name,Details\n';

    // Add created accounts
    result.created_accounts.forEach(account => {
        csv += `Created,${account.email},"${account.first_name || ''} ${account.last_name || ''}",${account.id}\n`;
    });

    // Add skipped accounts
    result.skipped_accounts.forEach(account => {
        csv += `Skipped,${account.email},,${account.reason}\n`;
    });

    // Add errors
    result.errors.forEach(error => {
        const errorDetails = error.errors
            ? Object.entries(error.errors).map(([field, msg]) => `${field}: ${msg}`).join('; ')
            : error.error || 'Unknown error';
        csv += `Error,${error.student.email},,${errorDetails}\n`;
    });

    // Download file
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `enrollment-report-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Download CSV template
 */
function downloadTemplate() {
    const template = 'first_name,last_name,email,role\nJohn,Doe,john.doe@example.com,student\nJane,Smith,jane.smith@example.com,student\n';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'student-enrollment-template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Show error message
 */
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorAlert.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(closeError, 5000);
}

/**
 * Close error alert
 */
function closeError() {
    elements.errorAlert.style.display = 'none';
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Get authentication token
 * (Mock implementation - replace with actual auth logic)
 */
function getAuthToken() {
    // TODO: Implement actual token retrieval
    return localStorage.getItem('auth_token') || 'mock-token';
}

/**
 * Get current user ID
 * (Mock implementation - replace with actual auth logic)
 */
function getCurrentUserId() {
    // TODO: Implement actual user ID retrieval
    return localStorage.getItem('user_id') || 'instructor-123';
}
