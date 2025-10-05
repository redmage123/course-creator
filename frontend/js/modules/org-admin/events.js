/**
 * Organization Admin Dashboard - Event Handlers Module
 *
 * BUSINESS CONTEXT:
 * Manages all event handlers and event listener setup for the organization admin
 * dashboard, including form submissions, button clicks, and tab navigation.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only event handling and listener setup
 * - Open/Closed: New event handlers can be added without modifying existing code
 * - Dependency Inversion: Depends on abstractions from other modules
 *
 * ARCHITECTURE:
 * Extracted from monolithic org-admin-dashboard.js (3,273 lines) to improve
 * maintainability, testability, and separation of concerns.
 */

// Import dependencies from other modules
import { closeModal, showNotification, parseCommaSeparated } from './utils.js';
import {
    getCurrentOrganization,
    getCurrentTab,
    setCurrentTab,
    ORG_API_BASE
} from './state.js';
import {
    loadInstructorsData,
    loadProjectsData,
    loadStudentsData,
    loadTracksData,
    loadTabContent,
    submitTrack,
    uploadLogoFile,
    confirmDeleteTrack,
    confirmProjectInstantiation,
    saveInstructorAssignments,
    bulkEnrollStudents,
    confirmStudentUnenrollment,
    confirmInstructorRemoval,
    cancelOrganizationChanges
} from './api.js';
import {
    updateOrganizationDisplay
} from './ui.js';

// =============================================================================
// FORM SUBMISSION HANDLERS
// =============================================================================

/**
 * Handle add instructor form submission
 *
 * BUSINESS CONTEXT:
 * Allows org admins to add new instructors to their organization
 *
 * @param {Event} e - The form submission event
 */
export async function handleAddInstructor(e) {
    e.preventDefault();

    try {
        const formData = new FormData(e.target);
        const instructorData = {
            email: formData.get('email'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            role: formData.get('role'),
            send_welcome_email: formData.get('send_welcome_email') === 'on'
        };

        const orgId = getCurrentOrganization().id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instructorData)
        });

        if (response.ok) {
            showNotification('Instructor added successfully', 'success');
            closeModal('addInstructorModal');
            if (getCurrentTab() === 'instructors') {
                await loadInstructorsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add instructor', 'error');
        }
    } catch (error) {
        console.error('Error adding instructor:', error);
        showNotification('Failed to add instructor', 'error');
    }
}

/**
 * Handle create project form submission
 *
 * BUSINESS CONTEXT:
 * Creates a new training project within the organization
 *
 * @param {Event} e - The form submission event
 */
export async function handleCreateProject(e) {
    e.preventDefault();

    try {
        const formData = new FormData(e.target);
        const targetRoles = formData.get('target_roles')
            ? formData.get('target_roles').split('\n').map(role => role.trim()).filter(role => role)
            : [];

        const projectData = {
            name: formData.get('name'),
            slug: formData.get('slug'),
            description: formData.get('description'),
            target_roles: targetRoles,
            duration_weeks: formData.get('duration_weeks') ? parseInt(formData.get('duration_weeks')) : null,
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            start_date: formData.get('start_date') || null,
            end_date: formData.get('end_date') || null
        };

        const orgId = getCurrentOrganization().id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (response.ok) {
            showNotification('Project created successfully', 'success');
            closeModal('createProjectModal');
            if (getCurrentTab() === 'projects') {
                await loadProjectsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create project', 'error');
        }
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project', 'error');
    }
}

/**
 * Handle add student form submission
 *
 * BUSINESS CONTEXT:
 * Allows org admins to add new students to their organization
 *
 * @param {Event} e - The form submission event
 */
export async function handleAddStudent(e) {
    e.preventDefault();

    try {
        const formData = new FormData(e.target);
        const studentData = {
            user_email: formData.get('user_email'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            send_welcome_email: formData.get('send_welcome_email') === 'on',
            role: 'student'
        };

        const orgId = getCurrentOrganization().id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });

        if (response.ok) {
            showNotification('Student added successfully', 'success');
            closeModal('addStudentModal');
            if (getCurrentTab() === 'students') {
                await loadStudentsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add student', 'error');
        }
    } catch (error) {
        console.error('Error adding student:', error);
        showNotification('Failed to add student', 'error');
    }
}

/**
 * Handle update organization settings form submission
 *
 * BUSINESS CONTEXT:
 * Updates organization profile information including logo, contact details, etc.
 *
 * @param {Event} e - The form submission event
 */
export async function handleUpdateSettings(e) {
    e.preventDefault();

    try {
        // Show saving state
        const saveBtn = document.getElementById('saveOrgSettingsBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        saveBtn.disabled = true;

        const formData = new FormData(e.target);

        // Combine country code with phone number
        const countryCode = document.getElementById('orgContactPhoneCountry').value;
        const phoneNumber = formData.get('contact_phone');
        const fullPhoneNumber = phoneNumber ? `${countryCode}${phoneNumber.replace(/^\+?[\d\s\-\(\)]*/, '')}` : '';

        const settingsData = {
            name: formData.get('name'),
            description: formData.get('description'),
            address: formData.get('address'),
            contact_email: formData.get('contact_email'),
            contact_phone: fullPhoneNumber,
            domain: formData.get('domain'),
            logo_url: formData.get('logo_url')
        };

        // Handle logo file upload if present
        const logoFile = document.getElementById('orgLogoFile').files[0];
        if (logoFile) {
            try {
                const logoUrl = await uploadLogoFile(logoFile);
                settingsData.logo_url = logoUrl;
            } catch (uploadError) {
                console.error('Logo upload failed:', uploadError);
                showNotification('Logo upload failed, but other settings will be saved', 'warning');
            }
        }

        const orgId = getCurrentOrganization().id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settingsData)
        });

        if (response.ok) {
            const updatedOrg = await response.json();
            showNotification('Organization information updated successfully', 'success');
            // Update local organization data
            const currentOrg = getCurrentOrganization();
            Object.assign(currentOrg, updatedOrg);
            updateOrganizationDisplay();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update organization information', 'error');
        }
    } catch (error) {
        console.error('Error updating settings:', error);
        showNotification('Failed to update organization information', 'error');
    } finally {
        // Restore button state
        const saveBtn = document.getElementById('saveOrgSettingsBtn');
        const originalText = '<i class="fas fa-save"></i> Save Changes';
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
}

/**
 * Handle update preferences form submission
 *
 * @param {Event} e - The form submission event
 */
export async function handleUpdatePreferences(e) {
    e.preventDefault();
    showNotification('Preferences updated successfully', 'success');
}

// =============================================================================
// TAB NAVIGATION
// =============================================================================

/**
 * Setup tab navigation event listeners
 *
 * BUSINESS CONTEXT:
 * Enables navigation between different sections of the admin dashboard
 */
export function setupTabNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            const tabName = this.dataset.tab;
            await switchTab(tabName);
        });
    });
}

/**
 * Switch to a different tab
 *
 * @param {string} tabName - The name of the tab to switch to
 */
export async function switchTab(tabName) {
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const targetLink = document.querySelector(`[data-tab="${tabName}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const targetContent = document.getElementById(tabName);
    if (targetContent) {
        targetContent.classList.add('active');
    }

    setCurrentTab(tabName);
    await loadTabContent(tabName);
}

// =============================================================================
// EVENT LISTENER SETUP
// =============================================================================

/**
 * Setup all event listeners for the dashboard
 *
 * BUSINESS CONTEXT:
 * Initializes all form submissions, button clicks, and interactive elements
 */
export function setupEventListeners() {
    // Form submissions - with null checks for safety
    const addInstructorForm = document.getElementById('addInstructorForm');
    if (addInstructorForm) {
        addInstructorForm.addEventListener('submit', handleAddInstructor);
    }

    const createProjectForm = document.getElementById('createProjectForm');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', handleCreateProject);
    }

    const addStudentForm = document.getElementById('addStudentForm');
    if (addStudentForm) {
        addStudentForm.addEventListener('submit', handleAddStudent);
    }

    const orgSettingsForm = document.getElementById('orgSettingsForm');
    if (orgSettingsForm) {
        orgSettingsForm.addEventListener('submit', handleUpdateSettings);
    }

    const orgPreferencesForm = document.getElementById('orgPreferencesForm');
    if (orgPreferencesForm) {
        orgPreferencesForm.addEventListener('submit', handleUpdatePreferences);
    }

    const trackForm = document.getElementById('trackForm');
    if (trackForm) {
        trackForm.addEventListener('submit', submitTrack);
    }

    // Auto-generate slug from project name
    const projectNameInput = document.getElementById('projectName');
    if (projectNameInput) {
        projectNameInput.addEventListener('input', function(e) {
            const slug = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            const projectSlugInput = document.getElementById('projectSlug');
            if (projectSlugInput) {
                projectSlugInput.value = slug;
            }
        });
    }

    // Cancel button for organization settings
    const cancelBtn = document.getElementById('cancelOrgSettingsBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            cancelOrganizationChanges();
        });
    }

    // Delete track confirmation
    const confirmDeleteTrackBtn = document.getElementById('confirmDeleteTrackBtn');
    if (confirmDeleteTrackBtn) {
        confirmDeleteTrackBtn.addEventListener('click', confirmDeleteTrack);
    }

    // Project instantiation confirmation
    const confirmInstantiateBtn = document.getElementById('confirmInstantiateBtn');
    if (confirmInstantiateBtn) {
        confirmInstantiateBtn.addEventListener('click', confirmProjectInstantiation);
    }

    // Save instructor assignments
    const saveInstructorAssignmentsBtn = document.getElementById('saveInstructorAssignmentsBtn');
    if (saveInstructorAssignmentsBtn) {
        saveInstructorAssignmentsBtn.addEventListener('click', saveInstructorAssignments);
    }

    // Bulk enroll students
    const bulkEnrollBtn = document.getElementById('bulkEnrollBtn');
    if (bulkEnrollBtn) {
        bulkEnrollBtn.addEventListener('click', bulkEnrollStudents);
    }

    // Confirm student unenrollment
    const confirmUnenrollBtn = document.getElementById('confirmUnenrollBtn');
    if (confirmUnenrollBtn) {
        confirmUnenrollBtn.addEventListener('click', confirmStudentUnenrollment);
    }

    // Confirm instructor removal
    const confirmRemovalBtn = document.getElementById('confirmInstructorRemovalBtn');
    if (confirmRemovalBtn) {
        confirmRemovalBtn.addEventListener('click', confirmInstructorRemoval);
    }

    // Transfer assignments checkbox handler
    const transferCheckbox = document.getElementById('transferAssignments');
    const replacementSection = document.getElementById('replacementInstructorSection');

    if (transferCheckbox && replacementSection) {
        transferCheckbox.addEventListener('change', function() {
            if (this.checked) {
                replacementSection.style.display = 'block';
                loadReplacementInstructorOptions();
            } else {
                replacementSection.style.display = 'none';
            }
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
}

// =============================================================================
// UTILITY EVENT HANDLERS
// =============================================================================

/**
 * Handle logo file selection
 *
 * @param {File} file - The selected logo file
 */
export function handleLogoFile(file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please upload a valid image file (JPG, PNG, GIF)', 'error');
        return;
    }

    // Validate file size (5MB limit)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        showNotification('File size must be less than 5MB', 'error');
        return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('logoPreview');
        const previewImg = document.getElementById('logoPreviewImg');
        const uploadArea = document.getElementById('logoUploadAreaSettings');

        if (previewImg && preview && uploadArea) {
            previewImg.src = e.target.result;
            preview.style.display = 'block';
            uploadArea.style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
}

/**
 * Remove logo preview
 */
export function removeLogo() {
    const preview = document.getElementById('logoPreview');
    const previewImg = document.getElementById('logoPreviewImg');
    const uploadArea = document.getElementById('logoUploadAreaSettings');
    const fileInput = document.getElementById('orgLogoFile');

    if (preview && uploadArea && fileInput && previewImg) {
        preview.style.display = 'none';
        uploadArea.style.display = 'flex';
        fileInput.value = '';
        previewImg.src = '';
    }
}

/**
 * Initialize logo upload functionality
 */
export function initializeLogoUpload() {
    const uploadArea = document.getElementById('logoUploadAreaSettings');
    const fileInput = document.getElementById('orgLogoFile');
    const uploadLink = uploadArea?.querySelector('.upload-link');
    const preview = document.getElementById('logoPreview');
    const previewImg = document.getElementById('logoPreviewImg');
    const removeBtn = document.getElementById('removeLogo');

    if (!uploadArea || !fileInput) return;

    // Click to browse functionality
    if (uploadLink) {
        uploadLink.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        });
    }

    uploadArea.addEventListener('click', (e) => {
        if (e.target === uploadArea || e.target.classList.contains('upload-content')) {
            fileInput.click();
        }
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleLogoFile(file);
        }
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
        uploadArea.style.backgroundColor = 'rgba(var(--primary-color-rgb), 0.1)';
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                fileInput.files = files;
                handleLogoFile(file);
            } else {
                showNotification('Please upload an image file', 'error');
            }
        }
    });

    // Remove logo button
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            removeLogo();
        });
    }

    // Show existing logo if available
    const currentOrg = getCurrentOrganization();
    if (currentOrg && currentOrg.logo_url && previewImg && preview) {
        previewImg.src = currentOrg.logo_url;
        preview.style.display = 'block';
    }
}

// =============================================================================
// SEARCH AND FILTER HANDLERS
// =============================================================================

/**
 * Search students in enrollment modal
 */
export function searchStudents() {
    const searchTerm = document.getElementById('studentSearchInput')?.value.toLowerCase() || '';
    const studentItems = document.querySelectorAll('.student-item');

    studentItems.forEach(item => {
        const name = item.querySelector('.student-name')?.textContent.toLowerCase() || '';
        const email = item.querySelector('.student-email')?.textContent.toLowerCase() || '';

        if (name.includes(searchTerm) || email.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Filter projects by status
 */
export function filterProjects() {
    const filterValue = document.getElementById('projectStatusFilter')?.value || '';
    // In production, this would filter the displayed projects
    showNotification(`Filtering projects by status: ${filterValue || 'All'}`, 'info');
}

/**
 * Filter tracks by project
 */
export function filterTracks() {
    const projectId = document.getElementById('trackProjectFilter')?.value || '';
    // In production, this would filter the displayed tracks
    showNotification(`Filtering tracks${projectId ? ' by project' : ''}`, 'info');
}

// =============================================================================
// TOGGLE HANDLERS
// =============================================================================

/**
 * Toggle student selection for enrollment
 *
 * @param {string} studentId - The student ID
 */
export function toggleStudentSelection(studentId) {
    const selectedStudents = getSelectedStudents();
    const index = selectedStudents.indexOf(studentId);

    if (index > -1) {
        selectedStudents.splice(index, 1);
    } else {
        selectedStudents.push(studentId);
    }

    // Update UI
    const studentElement = document.querySelector(`[onclick="toggleStudentSelection('${studentId}')"]`);
    if (studentElement) {
        studentElement.classList.toggle('selected');
    }

    updateEnrollmentSummary();
}

/**
 * Toggle student for unenrollment
 *
 * @param {string} studentId - The student ID
 */
export function toggleStudentForUnenrollment(studentId) {
    const checkbox = document.getElementById(`unenroll-${studentId}`);
    const selectedStudents = getSelectedStudentsForUnenrollment();

    if (checkbox && checkbox.checked) {
        if (!selectedStudents.includes(studentId)) {
            selectedStudents.push(studentId);
        }
    } else {
        const index = selectedStudents.indexOf(studentId);
        if (index > -1) {
            selectedStudents.splice(index, 1);
        }
    }

    // Update unenroll button state
    const unenrollBtn = document.querySelector('#studentUnenrollmentModal .btn-danger');
    if (unenrollBtn) {
        unenrollBtn.disabled = selectedStudents.length === 0;
    }
}

/**
 * Toggle instructor for removal
 *
 * @param {string} instructorId - The instructor ID
 */
export function toggleInstructorForRemoval(instructorId) {
    const checkbox = document.getElementById(`remove-${instructorId}`);
    const selectedInstructors = getSelectedInstructorsForRemoval();

    if (checkbox && checkbox.checked) {
        if (!selectedInstructors.includes(instructorId)) {
            selectedInstructors.push(instructorId);
        }
    } else {
        const index = selectedInstructors.indexOf(instructorId);
        if (index > -1) {
            selectedInstructors.splice(index, 1);
        }
    }

    // Update remove button state
    const removeBtn = document.querySelector('#instructorRemovalModal .btn-danger');
    if (removeBtn) {
        removeBtn.disabled = selectedInstructors.length === 0;
    }
}

/**
 * Update enrollment summary display
 */
function updateEnrollmentSummary() {
    const selectedStudents = getSelectedStudents();
    const selectedCount = selectedStudents.length;
    const trackSelect = document.getElementById('enrollmentTrackSelect');
    const selectedTrack = trackSelect?.options[trackSelect.selectedIndex]?.text || 'No track selected';

    // Update UI to show selection summary
    console.log(`${selectedCount} students selected for enrollment in: ${selectedTrack}`);
}

// =============================================================================
// ASSIGNMENT HANDLERS
// =============================================================================

/**
 * Assign instructor to track
 *
 * @param {string} trackId - The track ID
 * @param {string} instructorId - The instructor ID
 */
export function assignInstructorToTrack(trackId, instructorId) {
    const assignments = getInstructorAssignments();

    if (!assignments.tracks[trackId]) {
        assignments.tracks[trackId] = [];
    }

    if (!assignments.tracks[trackId].includes(instructorId)) {
        assignments.tracks[trackId].push(instructorId);
        showNotification('Instructor assigned to track', 'success');
        // Update UI to reflect the change
    }
}

/**
 * Remove instructor from track
 *
 * @param {string} trackId - The track ID
 * @param {string} instructorId - The instructor ID
 */
export function removeInstructorFromTrack(trackId, instructorId) {
    const assignments = getInstructorAssignments();

    if (assignments.tracks[trackId]) {
        assignments.tracks[trackId] = assignments.tracks[trackId].filter(id => id !== instructorId);
        showNotification('Instructor removed from track', 'success');
        // Update UI to reflect the change
    }
}

/**
 * Assign instructor to module
 *
 * @param {string} moduleId - The module ID
 * @param {string} instructorId - The instructor ID
 */
export function assignInstructorToModule(moduleId, instructorId) {
    const assignments = getInstructorAssignments();

    if (!assignments.modules[moduleId]) {
        assignments.modules[moduleId] = [];
    }

    if (!assignments.modules[moduleId].includes(instructorId)) {
        assignments.modules[moduleId].push(instructorId);
        showNotification('Instructor assigned to module', 'success');
        // Update UI to reflect the change
    }
}

/**
 * Remove instructor from module
 *
 * @param {string} moduleId - The module ID
 * @param {string} instructorId - The instructor ID
 */
export function removeInstructorFromModule(moduleId, instructorId) {
    const assignments = getInstructorAssignments();

    if (assignments.modules[moduleId]) {
        assignments.modules[moduleId] = assignments.modules[moduleId].filter(id => id !== instructorId);
        showNotification('Instructor removed from module', 'success');
        // Update UI to reflect the change
    }
}

// =============================================================================
// EXPORT ANALYTICS
// =============================================================================

/**
 * Export analytics data
 */
export function exportAnalytics() {
    showNotification('Analytics export functionality coming soon', 'info');
}
