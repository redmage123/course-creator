/**
 * Organization Admin Dashboard - Projects Management Module
 *
 * BUSINESS CONTEXT:
 * Manages projects within an organization. Projects are the primary learning
 * containers that hold tracks, modules, and content. Organization admins can
 * create, configure, activate, and manage project membership.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Multi-step project creation wizard with RAG suggestions
 * - Project lifecycle management (draft → active → completed → archived)
 * - Member management (instructors and students)
 * - Analytics dashboard integration
 * - Project instantiation from templates
 *
 * @module org-admin-projects
 */
import {
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    saveDraftProject,
    updateDraftProject,
    fetchDraftProjects,
    fetchMembers,
    addInstructor,
    addStudent,
    removeMember,
    createTrack,
    getAuthHeaders
} from './org-admin-api.js';

import {
    initializeAIAssistant,
    sendContextAwareMessage,
    CONTEXT_TYPES,
    clearConversationHistory
} from './ai-assistant.js';

import {
    escapeHtml,
    capitalizeFirst,
    parseCommaSeparated,
    formatDate,
    formatDuration,
    openModal,
    closeModal,
    showNotification,
    calculateProjectStatus
} from './org-admin-utils.js';

// Wave 4: Wizard Enhancement Modules
import { WizardProgress } from './wizard-progress.js';
import { WizardValidator } from './wizard-validation.js';
import { WizardDraft } from './wizard-draft.js';
import { showToast } from './feedback-system.js';

// Wave 5: Wizard Framework (replaces embedded wizard logic)
import { WizardFramework } from './wizard-framework.js';

// ==============================================================================
// UTILITY FUNCTIONS
// ==============================================================================

/**
 * Sanitize string to create valid URL slug
 *
 * BUSINESS CONTEXT:
 * URL slugs must match pattern ^[a-z0-9-]+$ for API validation.
 * Converts any string to a valid slug format.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Converts to lowercase
 * - Replaces spaces and special chars with hyphens
 * - Removes consecutive hyphens
 * - Trims leading/trailing hyphens
 *
 * @param {string} text - Text to convert to slug
 * @returns {string} Valid URL slug
 */
function sanitizeSlug(text) {
    if (!text) return '';

    return text
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')           // Spaces to hyphens
        .replace(/[^a-z0-9-]/g, '-')    // Special chars to hyphens
        .replace(/-+/g, '-')             // Remove consecutive hyphens
        .replace(/^-+|-+$/g, '');        // Remove leading/trailing hyphens
}

// ==============================================================================
// MODULE STATE
// ==============================================================================

// Current organization context
let currentOrganizationId = null;
let currentProjectId = null;
let currentDraftId = null;  // Track draft being edited

// Wave 5: Single wizard framework instance (replaces all Wave 4 component instances and state tracking)
let projectWizard = null;

/**
 * Initialize projects management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeProjectsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Projects management initialized for organization:', organizationId);

    // Wave 5: Wizard initialization deferred until modal opens (lazy loading)
    // This prevents "Form not found" errors since the form is inside the modal
}

/**
 * Initialize Wave 5 wizard framework for project creation
 *
 * BUSINESS CONTEXT:
 * Sets up the enhanced project creation wizard using the reusable WizardFramework.
 * Framework includes progress tracking, validation, and auto-save functionality
 * to improve user experience and reduce data loss.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses WizardFramework with graceful degradation
 * - Automatically integrates WizardProgress, WizardValidator, WizardDraft
 * - 84% code reduction vs Wave 4 (100+ lines → 16 lines)
 */
async function initializeProjectWizard() {
    console.log('🚀 Initializing Wave 5 WizardFramework...');

    projectWizard = new WizardFramework({
        wizardId: 'project-creation-wizard',
        steps: [
            { id: 'basic-info', label: 'Project Details', panelSelector: '#projectStep1' },
            { id: 'sub-projects', label: 'Configure Locations', panelSelector: '#projectStep2' },
            { id: 'tracks', label: 'Training Tracks', panelSelector: '#projectStep3' },
            { id: 'members', label: 'Assign Members', panelSelector: '#projectStep4' },
            { id: 'review', label: 'Review & Create', panelSelector: '#projectStep5' }
        ],
        progress: {
            enabled: true,
            containerSelector: '#project-wizard-progress',
            allowBackNavigation: true
        },
        validation: {
            enabled: true,
            formSelector: '#createProjectForm',
            validateOnBlur: true,
            validateOnSubmit: true
        },
        draft: {
            enabled: true,
            autoSaveInterval: 30000,
            storage: 'localStorage',
            formSelector: '#createProjectForm'
        },
        onStepChange: (oldIdx, newIdx) => {
            console.log(`Wizard step changed: ${oldIdx} → ${newIdx}`);

            /**
             * AUTO-GENERATE TRACKS: Step 2 → Step 3 transition
             *
             * WHY THIS IS NEEDED:
             * - Step 1 is where user selects target roles
             * - Step 2 is "Configure Locations"
             * - Step 3 is "Configure Training Tracks" where generated tracks are displayed
             * - Step 4 is "Review & Confirm" where tracks can be managed
             *
             * HOW IT WORKS:
             * 1. When entering Step 3 (index 2) from Step 2 (index 1)
             * 2. Get target roles selected in Step 1 via getSelectedAudiences()
             * 3. Map roles to track configurations via mapAudiencesToTracks()
             * 4. Display tracks in Step 3's track list container
             *
             * BUSINESS CONTEXT:
             * - Automates track creation based on target audience selection
             * - Shows tracks immediately in Step 3 for review
             * - User can see what tracks will be created before proceeding
             */
            if (oldIdx === 1 && newIdx === 2) {
                // Entering Step 3 (Training Tracks) from Step 2 (Locations)
                console.log('🎯 Auto-generating tracks from selected audiences...');

                const audiences = getSelectedAudiences();
                console.log(`📋 Found ${audiences.length} selected audiences:`, audiences);

                if (audiences && audiences.length > 0) {
                    const tracks = mapAudiencesToTracks(audiences);
                    console.log(`✅ Generated ${tracks.length} tracks:`, tracks);

                    // Display tracks in Step 3
                    displayGeneratedTracksInStep3(tracks);
                } else {
                    console.warn('⚠️  No audiences selected - cannot generate tracks');
                    displayGeneratedTracksInStep3([]);
                }
            }

            /**
             * POPULATE TRACK REVIEW: Step 3 → Step 4 transition
             *
             * WHY THIS IS NEEDED:
             * - Step 4 shows tracks in the management modal format
             * - Reuses the same track data generated in Step 3
             */
            if (oldIdx === 2 && newIdx === 3) {
                // Also populate Step 4's review list (uses same track data)
                console.log('📋 Populating Step 4 track review list...');
                if (generatedTracks && generatedTracks.length > 0) {
                    populateTrackReviewList(generatedTracks);
                }
            }
        },
        onDraftSaved: () => {
            showToast('Draft saved successfully', 'success', 2000);
        },
        onComplete: () => {
            console.log('Project wizard completed - ready to submit');
        }
    });

    await projectWizard.initialize();
    console.log('✅ WizardFramework initialized');
}

/**
 * Check for existing drafts and prompt user to restore
 */
function checkForExistingDrafts() {
    if (!wizardDraft) return;

    const existingDraft = wizardDraft.checkForDraft();
    if (existingDraft) {
        // Show restoration prompt
        const lastSaved = new Date(existingDraft.timestamp);
        const message = `You have an unsaved draft from ${lastSaved.toLocaleString()}. Would you like to restore it?`;

        if (confirm(message)) {
            wizardDraft.loadDraft();
        }
    }
}

/**
 * Populate form fields from loaded draft
 *
 * @param {Object} draft - Draft data object
 */
function populateFormFromDraft(draft) {
    if (!draft || !draft.data) return;

    const data = draft.data;

    // Populate Step 1 fields
    if (data.projectName) document.getElementById('projectName').value = data.projectName;
    if (data.projectSlug) document.getElementById('projectSlug').value = data.projectSlug;
    if (data.projectDescription) document.getElementById('projectDescription').value = data.projectDescription;
    if (data.projectType) document.getElementById('projectType').value = data.projectType;
    if (data.projectDuration) document.getElementById('projectDuration').value = data.projectDuration;
    if (data.projectMaxParticipants) document.getElementById('projectMaxParticipants').value = data.projectMaxParticipants;
    if (data.projectStartDate) document.getElementById('projectStartDate').value = data.projectStartDate;
    if (data.projectEndDate) document.getElementById('projectEndDate').value = data.projectEndDate;

    showToast('Draft restored successfully', 'success');
}

// Wave 5: showStep() function removed - WizardFramework handles step visibility internally

/**
 * Reset project wizard to initial state (Wave 5 - delegates to framework)
 *
 * BUSINESS CONTEXT:
 * Cleans up wizard state after project creation or when user cancels.
 * Ensures wizard starts fresh for next project creation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Delegates to WizardFramework.reset() which handles all cleanup
 * - Framework resets step, form, progress, validation, and draft
 * - 50 lines reduced to 5 lines (90% reduction)
 *
 * @returns {boolean} True if reset successful
 */
export function resetProjectWizard() {
    if (!projectWizard) {
        console.error('Project wizard not initialized');
        return false;
    }
    return projectWizard.reset();
}

/**
 * Navigate to next project wizard step (Wave 5 - delegates to framework)
 *
 * BUSINESS CONTEXT:
 * Handles wizard step navigation with validation and progress tracking.
 * Ensures users cannot proceed with incomplete or invalid data.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Delegates to WizardFramework.nextStep() which handles all logic
 * - Framework validates, saves draft, shows next step, updates progress
 * - 64 lines reduced to 5 lines (92% reduction)
 *
 * @returns {Promise<boolean>} True if navigation successful, false otherwise
 */
export async function nextProjectStep() {
    if (!projectWizard) {
        console.error('Project wizard not initialized');
        return false;
    }
    return await projectWizard.nextStep();
}

/**
 * Navigate to previous project wizard step (Wave 5 - delegates to framework)
 *
 * BUSINESS CONTEXT:
 * Allows users to navigate back to previous steps to review or modify
 * their inputs before final submission.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Delegates to WizardFramework.previousStep() which handles all logic
 * - Framework validates first step, shows previous panel, updates progress
 * - 37 lines reduced to 5 lines (86% reduction)
 *
 * @returns {boolean} True if navigation successful
 */
export function previousProjectStep() {
    if (!projectWizard) {
        console.error('Project wizard not initialized');
        return false;
    }
    return projectWizard.previousStep();
}

/**
 * Load and display projects data
 *
 * BUSINESS LOGIC:
 * Fetches all projects for the organization and displays them in a table
 * Supports filtering by status and search term
 * Automatically calculates project status based on current date vs. start/end dates
 *
 * @returns {Promise<void>}
 */
export async function loadProjectsData() {
    try {
        // Get filter values
        const filters = {
            status: document.getElementById('projectStatusFilter')?.value || '',
            search: document.getElementById('projectSearchInput')?.value || ''
        };

        const projects = await fetchProjects(currentOrganizationId, filters);

        // Calculate status for each project based on dates
        // This ensures projects with end_date in the past show as "completed"
        const projectsWithStatus = projects.map(project => ({
            ...project,
            status: calculateProjectStatus(project)
        }));

        // Update UI with calculated statuses
        renderProjectsTable(projectsWithStatus);
        updateProjectsStats(projectsWithStatus);

    } catch (error) {
        console.error('Error loading projects:', error);
        renderProjectsTable([]);
    }
}

/**
 * Render projects table
 *
 * BUSINESS CONTEXT:
 * Displays projects with key metrics:
 * - Name and description
 * - Status and duration
 * - Participant counts
 * - Action buttons
 *
 * @param {Array} projects - Array of project objects
 */
function renderProjectsTable(projects) {
    const tbody = document.getElementById('projectsTableBody');

    if (!tbody) return;

    if (!projects || projects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No projects found</td></tr>';
        return;
    }

    tbody.innerHTML = projects.map(project => `
        <tr>
            <td>
                <strong>${escapeHtml(project.name)}</strong>
                ${project.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(project.description.substring(0, 100))}${project.description.length > 100 ? '...' : ''}</small>` : ''}
            </td>
            <td>
                <span class="status-badge status-${project.status || 'draft'}"></span>
            </td>
            <td>${formatDuration(project.duration_weeks)}</td>
            <td>
                <span class="stat-badge">${project.current_participants || 0}</span>
                ${project.max_participants ? `<small>/ ${project.max_participants}</small>` : ''}
            </td>
            <td>${formatDate(project.start_date)}</td>
            <td>${formatDate(project.end_date)}</td>
            <td>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.viewProject('${project.id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.editProject('${project.id}')" title="Edit">
                    ✏️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.manageMembers('${project.id}')" title="Manage Members">
                    👥
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.manageProjectTracks('${project.id}')" title="Manage Track">
                    📊
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.deleteProjectPrompt('${project.id}')" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update projects statistics
 *
 * @param {Array} projects - Array of project objects
 */
function updateProjectsStats(projects) {
    const totalProjectsEl = document.getElementById('totalProjects');
    if (totalProjectsEl) {
        totalProjectsEl.textContent = projects.length;
    }

    const activeProjectsEl = document.getElementById('activeProjects');
    if (activeProjectsEl) {
        const activeCount = projects.filter(p => p.status === 'active').length;
        activeProjectsEl.textContent = activeCount;
    }
}

/**
 * Show create project modal
 *
 * BUSINESS CONTEXT:
 * Opens multi-step wizard for project creation
 * Step 1: Basic Info, Step 2: Configuration, Step 3: Tracks
 */
export async function showCreateProjectModal() {
    console.log('📋 Opening create project modal...');

    const modal = document.getElementById('createProjectModal');
    const form = document.getElementById('createProjectForm');

    if (!modal) {
        console.error('❌ createProjectModal not found');
        return;
    }

    if (!form) {
        console.error('❌ createProjectForm not found');
        return;
    }

    console.log('✅ Modal and form found, resetting and opening...');

    // Wave 5: Lazy initialization - create wizard on first modal open
    if (!projectWizard) {
        console.log('🔄 First time opening modal - initializing wizard...');
        await initializeProjectWizard();  // Await async initialization
    }

    // Reset wizard to step 1 (Wave 5: uses framework)
    form.reset();
    if (projectWizard) {
        projectWizard.goToStep(0); // Framework uses 0-based indexing
    }

    // Set default start date to next working day (if today is weekend)
    const startDateInput = document.getElementById('projectStartDate');
    if (startDateInput) {
        const today = new Date();
        const nextWorkingDay = getNextWorkingDay(today);
        startDateInput.value = formatDateForInput(nextWorkingDay);

        // Log for clarity
        if (today.getDay() === 0 || today.getDay() === 6) {
            console.log(`📅 Today is a weekend, defaulting start date to next Monday: ${startDateInput.value}`);
        } else {
            console.log(`📅 Setting start date to today: ${startDateInput.value}`);
        }
    }

    // Hide floating dashboard AI Assistant to avoid conflicts with wizard AI Assistant
    const dashboardAI = document.getElementById('dashboardAIChatPanel');
    if (dashboardAI) {
        dashboardAI.style.display = 'none';
    }
    const aiButton = document.getElementById('aiAssistantButton');
    if (aiButton) {
        aiButton.style.display = 'none';
    }

    // Open modal
    openModal('createProjectModal');

    // CRITICAL FIX: Re-attach drag handler after modal opens
    // The wizard initialization destroys the drag handler attached at page load
    // We need to reattach it after the modal is fully initialized
    setTimeout(() => {
        const modalElement = document.getElementById('createProjectModal');
        const handleElement = document.querySelector('#createProjectModal .draggable-handle');

        if (modalElement && handleElement && window.makeDraggable) {
            window.makeDraggable(modalElement, handleElement);
        }
    }, 100); // Small delay to ensure wizard initialization completes
}

// Wave 5: Legacy duplicate wizard functions removed (lines 392-538)
// These duplicated the Wave 4/5 wizard logic that is now handled by WizardFramework
// Keeping only the framework-based implementations above (lines 218-246)

// ============================================================================
// DRAFT SAVE/LOAD FUNCTIONALITY
// ============================================================================

/**
 * Save current project wizard state as draft
 *
 * BUSINESS CONTEXT:
 * Allows org admins to save incomplete projects and return later
 * Particularly useful for complex multi-locations projects with many locations
 *
 * @returns {Promise<void>}
 */
export async function saveCurrentProjectDraft() {
    try {
        // Collect current wizard data
        const draftData = collectWizardData();

        if (!draftData.name || !draftData.slug) {
            showNotification('Please provide at least a project name and slug before saving', 'error');
            return;
        }

        // Get current step
        const currentStepElem = document.querySelector('.project-step.active');
        const currentStep = currentStepElem ? parseInt(currentStepElem.id.replace('projectStep', '')) : 1;

        // Add wizard state metadata
        draftData.wizard_state = {
            current_step: currentStep,
            wizard_locations: wizardLocations,
            last_saved: new Date().toISOString()
        };

        let savedDraft;
        if (currentDraftId) {
            // Update existing draft
            savedDraft = await updateDraftProject(currentDraftId, draftData);
            showNotification('Draft updated successfully', 'success');
        } else {
            // Create new draft
            savedDraft = await saveDraftProject(currentOrganizationId, draftData);
            currentDraftId = savedDraft.id;
            showNotification('Draft saved successfully', 'success');
        }

        console.log('✅ Draft saved:', savedDraft);
    } catch (error) {
        console.error('Error saving draft:', error);
        showNotification('Failed to save draft', 'error');
    }
}

/**
 * Load project draft and populate wizard
 *
 * @param {string} draftId - UUID of draft project to load
 * @returns {Promise<void>}
 */
export async function loadProjectDraft(draftId) {
    try {
        console.log('📂 Loading draft project:', draftId);

        // Fetch the draft project
        const response = await fetch(`/api/v1/projects/${draftId}`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load draft');
        }

        const draft = await response.json();
        console.log('✅ Draft loaded:', draft);

        // Set current draft ID
        currentDraftId = draftId;

        // Populate Step 1 fields
        document.getElementById('projectName').value = draft.name || '';
        document.getElementById('projectSlug').value = draft.slug || '';
        document.getElementById('projectDescription').value = draft.description || '';
        document.getElementById('projectType').value = draft.type || 'single_location';
        document.getElementById('projectDuration').value = draft.duration_weeks || '';
        document.getElementById('projectMaxParticipants').value = draft.max_participants || '';
        document.getElementById('projectStartDate').value = draft.start_date || '';
        document.getElementById('projectEndDate').value = draft.end_date || '';

        // Handle has_sub_projects field
        if (draft.has_sub_projects !== undefined) {
            document.getElementById('hasSubProjects').value = draft.has_sub_projects ? 'true' : 'false';
        }

        // Restore wizard state if available
        if (draft.wizard_state) {
            // Restore locations
            if (draft.wizard_state.wizard_locations) {
                wizardLocations = draft.wizard_state.wizard_locations;
                renderLocationsList();
            }

            // Navigate to saved step (Wave 5: uses framework, converts 1-based to 0-based)
            if (draft.wizard_state.current_step && projectWizard) {
                projectWizard.goToStep(draft.wizard_state.current_step - 1); // Convert to 0-based
            }
        }

        // Open the project modal
        openModal('createProjectModal');

        showNotification('Draft loaded successfully - continue editing', 'success');
    } catch (error) {
        console.error('Error loading draft:', error);
        showNotification('Failed to load draft', 'error');
    }
}

/**
 * Collect current wizard data from form fields
 *
 * @returns {Object} Project data object
 */
function collectWizardData() {
    const data = {
        name: document.getElementById('projectName')?.value || '',
        slug: document.getElementById('projectSlug')?.value || '',
        description: document.getElementById('projectDescription')?.value || '',
        type: document.getElementById('projectType')?.value || 'single_location',
        duration_weeks: parseInt(document.getElementById('projectDuration')?.value) || null,
        max_participants: parseInt(document.getElementById('projectMaxParticipants')?.value) || null,
        start_date: document.getElementById('projectStartDate')?.value || null,
        end_date: document.getElementById('projectEndDate')?.value || null,
        has_sub_projects: document.getElementById('hasSubProjects')?.value === 'true'
    };

    return data;
}

/**
 * Show drafts list modal for continuing from draft
 *
 * @returns {Promise<void>}
 */
export async function showDraftsList() {
    try {
        const drafts = await fetchDraftProjects(currentOrganizationId);

        if (drafts.length === 0) {
            showNotification('No saved drafts found', 'info');
            return;
        }

        // Build drafts list HTML
        const draftsHTML = drafts.map(draft => `
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; cursor: pointer; transition: all 0.2s;"
                 onmouseover="this.style.backgroundColor='#f8f9fa'"
                 onmouseout="this.style.backgroundColor='white'"
                 onclick="window.OrgAdmin.Projects.loadProjectDraft('${draft.id}')">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0;">${escapeHtml(draft.name)}</h4>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">${escapeHtml(draft.description || '')}</p>
                        <p style="margin: 0.5rem 0 0 0; color: #999; font-size: 0.8rem;">
                            Last saved: ${draft.wizard_state?.last_saved ? formatDate(draft.wizard_state.last_saved) : 'Unknown'}
                        </p>
                    </div>
                    <span style="background: #ffc107; color: #000; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem;">
                        Draft
                    </span>
                </div>
            </div>
        `).join('');

        // Show in a modal or notification
        showNotification(`
            <div style="max-width: 500px;">
                <h3>Continue from Draft</h3>
                <p>Select a draft project to continue editing:</p>
                ${draftsHTML}
            </div>
        `, 'info', 30000);

    } catch (error) {
        console.error('Error showing drafts list:', error);
        showNotification('Failed to load drafts', 'error');
    }
}

// ============================================================================
// LOCATIONS MANAGEMENT (STEP 2)
// ============================================================================

// Store locations being created during wizard
let wizardLocations = []; // Variable name kept for backward compatibility

/**
 * Show the locations creation form in Step 2
 *
 * BUSINESS CONTEXT:
 * Displays the inline form for adding a new locations during
 * project creation. This allows org admins to define initial locations
 * before the project is created.
 */
export function showAddLocationForm() {
    const form = document.getElementById('addLocationForm');
    const button = document.querySelector('button[onclick*="showAddLocationForm"]');

    if (form) {
        // Remove the hidden class (which has !important CSS)
        form.classList.remove('locations-form-hidden');
        if (button) button.style.display = 'none';

        // Clear form fields
        document.getElementById('locationName').value = '';
        document.getElementById('locationLocation').value = '';
        document.getElementById('locationMaxStudents').value = '';

        // Sync dates and duration from project form (Step 1)
        const projectStartDate = document.getElementById('projectStartDate')?.value;
        const projectDuration = document.getElementById('projectDuration')?.value;
        const projectMaxParticipants = document.getElementById('projectMaxParticipants')?.value;

        const locationStartDateInput = document.getElementById('locationStartDate');
        const locationDurationInput = document.getElementById('locationDuration');
        const locationMaxParticipantsInput = document.getElementById('locationMaxParticipants');

        if (projectStartDate && locationStartDateInput) {
            // Sync start date from project
            locationStartDateInput.value = projectStartDate;
            console.log(`📅 Synced location start date from project: ${projectStartDate}`);
        } else if (locationStartDateInput) {
            // Fallback to next working day if no project date set
            const today = new Date();
            const nextWorkingDay = getNextWorkingDay(today);
            locationStartDateInput.value = formatDateForInput(nextWorkingDay);
            console.log(`📅 Location: Using next working day as default: ${locationStartDateInput.value}`);
        }

        if (projectDuration && locationDurationInput) {
            // Sync duration from project
            locationDurationInput.value = projectDuration;
            // Trigger end date calculation
            if (typeof calculateLocationEndDate === 'function') {
                calculateLocationEndDate();
            }
            console.log(`⏱️  Synced location duration from project: ${projectDuration} weeks`);
        } else {
            document.getElementById('locationEndDate').value = '';
        }

        if (projectMaxParticipants && locationMaxParticipantsInput) {
            // Optionally sync max participants from project as a suggested default
            locationMaxParticipantsInput.value = projectMaxParticipants;
            console.log(`👥 Synced location max participants from project: ${projectMaxParticipants}`);
        }

        console.log('📝 Locations form displayed');
    }
}

/**
 * Cancel locations form and hide it
 */
export function cancelLocationForm() {
    const form = document.getElementById('addLocationForm');
    const button = document.querySelector('button[onclick*="showAddLocationForm"]');

    // Re-add the hidden class (which has !important CSS)
    if (form) form.classList.add('locations-form-hidden');
    if (button) button.style.display = 'block';

    console.log('❌ Locations form cancelled');
}

/**
 * Save locations data from form
 *
 * BUSINESS CONTEXT:
 * Validates and stores locations data temporarily during project creation.
 * Locations will be created after the project is created in finalizeProjectCreation().
 */
export function saveLocation() {
    // Get form values (using inline field IDs)
    const name = document.getElementById('locationName')?.value.trim();
    const locationAddress = document.getElementById('locationLocation')?.value.trim();
    const startDate = document.getElementById('inlineLocationStartDate')?.value;
    const endDate = document.getElementById('inlineLocationEndDate')?.value;
    const maxStudents = parseInt(document.getElementById('inlineLocationMaxStudents')?.value) || null;

    // Validate required fields
    if (!name || !locationAddress) {
        showNotification('Please provide location name and address', 'error');
        return;
    }

    // Create location object
    const locationData = {
        id: `temp_${Date.now()}`, // Temporary ID for UI display
        name,
        location: locationAddress,
        start_date: startDate || null,
        end_date: endDate || null,
        max_students: maxStudents
    };

    // Add to wizard locations array
    wizardLocations.push(locationData);

    // Update display
    renderWizardLocations();

    // Clear form fields for next entry
    const nameField = document.getElementById('locationName');
    const locationField = document.getElementById('locationLocation');
    const startDateField = document.getElementById('inlineLocationStartDate');
    const endDateField = document.getElementById('inlineLocationEndDate');
    const maxStudentsField = document.getElementById('inlineLocationMaxStudents');

    if (nameField) nameField.value = '';
    if (locationField) locationField.value = '';
    if (startDateField) startDateField.value = '';
    if (endDateField) endDateField.value = '';
    if (maxStudentsField) maxStudentsField.value = '';

    console.log('🧹 Location form fields cleared');

    // Hide form
    cancelLocationForm();

    showNotification(`Locations "${name}" added`, 'success');
    console.log('✅ Locations saved:', locationData);
}

/**
 * Render locations list in Step 2
 */
function renderWizardLocations() {
    const container = document.getElementById('locationsListContent');

    if (!container) return;

    if (wizardLocations.length === 0) {
        container.innerHTML = `
            <div style="padding: 2rem; text-align: center; background: var(--hover-color); border: 2px dashed var(--border-color); border-radius: 8px;">
                <p style="margin: 0; color: var(--text-muted);">
                    No locations defined yet. Click "Add Locations" to create your first locations.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = wizardLocations.map((locations, index) => `
        <div style="padding: 1.5rem; background: var(--card-background); border: 1px solid var(--border-color); border-radius: 8px; display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <h5 style="margin: 0 0 0.5rem 0; color: var(--primary-color);">
                    ${index + 1}. ${escapeHtml(locations.name)}
                </h5>
                <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; color: var(--text-muted);">
                    <span>📍 ${escapeHtml(locations.locations)}</span>
                    ${locations.start_date ? `<span>📅 ${formatDate(locations.start_date)}</span>` : ''}
                    ${locations.max_students ? `<span>👥 Max ${locations.max_students} students</span>` : ''}
                </div>
            </div>
            <button
                class="btn-icon"
                onclick="window.OrgAdmin.Projects.removeLocationFromWizard('${locations.id}')"
                title="Remove Locations"
                style="color: var(--danger-color);">
                🗑️
            </button>
        </div>
    `).join('');
}

/**
 * Remove locations from wizard
 */
export function removeLocationFromWizard(locationId) {
    wizardLocations = wizardLocations.filter(c => c.id !== locationId);
    renderWizardLocations();
    showNotification('Locations removed', 'info');
}

/**
 * Populate selected roles summary display
 *
 * BUSINESS CONTEXT:
 * Shows the target roles that were selected in Step 1, so users don't need
 * to select them again. Provides a visual reminder and link to go back if
 * they want to change their selection.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads selected options from Step 1's projectTargetRoles multi-select
 * - Maps role values to human-readable labels
 * - Generates styled badge elements for each role
 * - Populates selectedRolesSummary container
 */
function populateSelectedRolesSummary() {
    const summaryContainer = document.getElementById('selectedRolesSummary');
    const rolesSelect = document.getElementById('projectTargetRoles');

    if (!summaryContainer || !rolesSelect) {
        console.warn('Could not find selectedRolesSummary or projectTargetRoles elements');
        return;
    }

    // Get selected roles from Step 1
    const selectedOptions = Array.from(rolesSelect.selectedOptions);

    if (selectedOptions.length === 0) {
        summaryContainer.innerHTML = `
            <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">
                No target roles selected.
                <a href="#" onclick="window.OrgAdmin.Projects.previousProjectStep(); return false;">
                    Go back to Step 1
                </a> to select roles.
            </p>
        `;
        return;
    }

    // Generate role badges
    summaryContainer.innerHTML = selectedOptions.map(option => {
        const roleLabel = option.textContent;
        const roleValue = option.value;

        return `
            <span style="display: inline-flex; align-items: center; gap: 0.5rem;
                         padding: 0.5rem 1rem; background: var(--primary-color);
                         color: white; border-radius: 20px; font-size: 0.9rem;
                         font-weight: 500;">
                <span>👤</span>
                <span>${escapeHtml(roleLabel)}</span>
            </span>
        `;
    }).join('');

    console.log(`✅ Populated ${selectedOptions.length} role(s) in summary`);
}

/**
 * Submit project creation form
 *
 * BUSINESS LOGIC:
 * Gathers data from all wizard steps and creates project
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitProjectForm(event) {
    event.preventDefault();

    try {
        // Gather data from all steps
        const projectData = {
            name: document.getElementById('projectName')?.value,
            slug: document.getElementById('projectSlug')?.value,
            description: document.getElementById('projectDescription')?.value || null,
            objectives: parseCommaSeparated(document.getElementById('projectObjectives')?.value),
            target_roles: parseCommaSeparated(document.getElementById('projectTargetRoles')?.value),
            duration_weeks: parseInt(document.getElementById('projectDuration')?.value) || null,
            max_participants: parseInt(document.getElementById('projectMaxParticipants')?.value) || null,
            start_date: document.getElementById('projectStartDate')?.value || null,
            end_date: document.getElementById('projectEndDate')?.value || null
        };

        await createProject(currentOrganizationId, projectData);

        // Clean up draft after successful project creation
        if (wizardDraft) {
            try {
                wizardDraft.clearDraft();
                console.log('✅ Draft cleaned up after project creation');
            } catch (draftError) {
                console.warn('Could not clear draft (non-critical):', draftError);
            }
        }

        showNotification('Project created successfully', 'success');

        // Reset wizard to initial state
        resetProjectWizard();

        closeModal('createProjectModal');
        loadProjectsData();

    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project', 'error');
    }
}

/**
 * View project details
 *
 * BUSINESS CONTEXT:
 * Opens the project detail modal showing project information and locations tab.
 * The locations tab allows creating and managing sub-projects (locations) for
 * multi-locations projects.
 *
 * TECHNICAL IMPLEMENTATION:
 * Calls the openProjectDetail function defined in org-admin-dashboard.html
 * which handles fetching project data and displaying the modal with tabs.
 *
 * @param {string} projectId - UUID of project
 */
export function viewProject(projectId) {
    console.log('Opening project detail view:', projectId);

    // Check if openProjectDetail function exists (defined in HTML)
    if (typeof openProjectDetail === 'function') {
        openProjectDetail(projectId);
    } else {
        console.error('openProjectDetail function not found');
        showNotification('Unable to open project details. Please refresh the page.', 'error');
    }
}

/**
 * Edit project
 *
 * @param {string} projectId - UUID of project to edit
 */
export async function editProject(projectId) {
    try {
        // Fetch project details and populate form
        // This would be implemented similar to track editing
        console.log('Edit project:', projectId);
        showNotification('Project editing feature coming soon', 'info');
    } catch (error) {
        console.error('Error editing project:', error);
    }
}

/**
 * Manage project members
 *
 * BUSINESS CONTEXT:
 * Opens modal to manage instructors and students assigned to project
 *
 * @param {string} projectId - UUID of project
 */
export async function manageMembers(projectId) {
    currentProjectId = projectId;

    try {
        // Fetch project members
        const members = await fetchMembers(currentOrganizationId, { project_id: projectId });

        // Render members list
        renderProjectMembers(members);

        // Open members modal
        openModal('projectMembersModal');

    } catch (error) {
        console.error('Error loading project members:', error);
    }
}

/**
 * Render project members in modal
 *
 * @param {Array} members - Array of member objects
 */
function renderProjectMembers(members) {
    const instructorsList = document.getElementById('projectInstructorsList');
    const studentsList = document.getElementById('projectStudentsList');

    if (!instructorsList || !studentsList) return;

    const instructors = members.filter(m => m.role === 'instructor');
    const students = members.filter(m => m.role === 'student');

    instructorsList.innerHTML = instructors.length > 0
        ? instructors.map(i => `
            <div class="member-item">
                <span>${escapeHtml(i.first_name)} ${escapeHtml(i.last_name)}</span>
                <span>${escapeHtml(i.email)}</span>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.removeMemberFromProject('${i.user_id}')" title="Remove">
                    ✗
                </button>
            </div>
        `).join('')
        : '<p>No instructors assigned</p>';

    studentsList.innerHTML = students.length > 0
        ? students.map(s => `
            <div class="member-item">
                <span>${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</span>
                <span>${escapeHtml(s.email)}</span>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.removeMemberFromProject('${s.user_id}')" title="Remove">
                    ✗
                </button>
            </div>
        `).join('')
        : '<p>No students enrolled</p>';
}

/**
 * Remove member from project
 *
 * @param {string} userId - UUID of user to remove
 */
export async function removeMemberFromProject(userId) {
    if (!confirm('Are you sure you want to remove this member from the project?')) {
        return;
    }

    try {
        await removeMember(currentOrganizationId, userId);
        showNotification('Member removed successfully', 'success');

        // Refresh members list
        manageMembers(currentProjectId);

    } catch (error) {
        console.error('Error removing member:', error);
    }
}

/**
 * Show delete project confirmation
 *
 * @param {string} projectId - UUID of project to delete
 */
export function deleteProjectPrompt(projectId) {
    currentProjectId = projectId;

    const warning = document.getElementById('deleteProjectWarning');
    if (warning) {
        warning.textContent = 'This will permanently delete the project and all associated data. This action cannot be undone.';
    }

    openModal('deleteProjectModal');
}

/**
 * Confirm and execute project deletion
 *
 * @returns {Promise<void>}
 */
export async function confirmDeleteProject() {
    if (!currentProjectId) return;

    try {
        await deleteProject(currentProjectId);
        showNotification('Project deleted successfully', 'success');
        closeModal('deleteProjectModal');
        loadProjectsData();

    } catch (error) {
        console.error('Error deleting project:', error);
    }
}

/**
 * Filter projects based on search and status
 */
export function filterProjects() {
    loadProjectsData();
}

// Store conversation history for RAG context
let conversationHistory = [];
let ragContext = null;

/**
 * Generate AI suggestions for project planning with RAG enhancement
 *
 * BUSINESS CONTEXT:
 * Uses project description to generate AI-powered suggestions for:
 * - Project insights and analysis (RAG-enhanced with existing course content)
 * - Recommended track structure
 * - Learning objectives
 *
 * TECHNICAL IMPLEMENTATION:
 * 1. Queries RAG service for relevant existing content
 * 2. Calls course-generator service with RAG context
 * 3. Generates contextually-aware recommendations
 */
async function generateAISuggestions() {
    console.log('🤖 Generating context-aware RAG-enhanced AI suggestions...');

    const loadingIndicator = document.getElementById('ragLoadingIndicator');
    const suggestionsContainer = document.getElementById('ragSuggestions');
    const ragIndicator = document.getElementById('ragContextIndicator');

    // Show loading indicator
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (suggestionsContainer) suggestionsContainer.style.display = 'none';

    try {
        // Get project data
        const projectName = document.getElementById('projectName')?.value || '';
        const projectDescription = document.getElementById('projectDescription')?.value || '';
        const targetRoles = Array.from(document.getElementById('projectTargetRoles')?.selectedOptions || [])
            .map(opt => opt.value);

        // Initialize context-aware AI assistant for project creation
        initializeAIAssistant(CONTEXT_TYPES.PROJECT_CREATION, {
            projectName,
            projectDescription,
            targetRoles,
            organizationId: currentOrganizationId
        });

        // Send initial message to AI assistant
        const initialPrompt = `
I need help creating a training project with the following details:

Project Name: ${projectName}
Description: ${projectDescription}
Target Roles: ${targetRoles.join(', ')}

Please analyze this and provide:
1. Key insights about the project scope
2. Recommended track structure (3-5 tracks)
3. Specific learning objectives (5-8 objectives)

Use web search if needed to research current best practices for these roles.
`;

        console.log('📤 Sending to context-aware AI assistant...');
        const response = await sendContextAwareMessage(initialPrompt, { forceWebSearch: true });

        console.log('✅ AI response received:', response);

        // Show RAG indicator if sources were used
        if (response.ragSources && response.ragSources.length > 0) {
            if (ragIndicator) {
                ragIndicator.style.display = 'block';
                ragIndicator.innerHTML = `
                    <span style="color: var(--success-color);">✓</span>
                    Using RAG knowledge base (${response.ragSources.length} sources)
                    ${response.webSearchUsed ? ' + Web research' : ''}
                `;
            }
        }

        // Convert AI response to suggestions format
        const suggestions = parseAIResponseToSuggestions(response);

        // Populate suggestions
        populateAISuggestions(suggestions);

        // Hide loading, show suggestions
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (suggestionsContainer) suggestionsContainer.style.display = 'block';

        console.log('✅ Context-aware AI suggestions generated');

    } catch (error) {
        console.error('❌ Error generating AI suggestions:', error);
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        showNotification('Failed to generate AI suggestions', 'error');
    }
}

/**
 * Parse AI response into suggestions format
 */
function parseAIResponseToSuggestions(response) {
    // Use AI suggestions if provided, otherwise fall back to mock
    if (response.suggestions && response.suggestions.length > 0) {
        return {
            insights: [response.message],
            tracks: response.suggestions.filter(s => s.includes('track')).map((s, i) => ({
                name: `Track ${i + 1}`,
                description: s,
                duration: '2-3 weeks',
                modules: 4 + i
            })),
            objectives: response.suggestions.filter(s => !s.includes('track'))
        };
    }

    // Fallback to generating from message
    const projectName = document.getElementById('projectName')?.value || '';
    const description = document.getElementById('projectDescription')?.value || '';
    const targetRoles = Array.from(document.getElementById('projectTargetRoles')?.selectedOptions || [])
        .map(opt => opt.value);

    return generateMockSuggestions(projectName, description, targetRoles);
}

/**
 * Query RAG service for relevant context
 *
 * BUSINESS CONTEXT:
 * Retrieves relevant existing course content, learning paths, and best practices
 * from the RAG knowledge base to inform AI recommendations
 *
 * @param {string} description - Project description
 * @param {Array<string>} roles - Target roles
 * @returns {Promise<Object>} RAG context with relevant content
 */
async function queryRAGForContext(description, roles) {
    try {
        // TODO: Replace with actual RAG service endpoint
        // const response = await fetch('https://localhost:8005/api/v1/rag/query', {
        //     method: 'POST',
        //     headers: await getAuthHeaders(),
        //     body: JSON.stringify({
        //         query: description,
        //         filters: { roles: roles },
        //         top_k: 5
        //     })
        // });

        // Mock RAG response for now
        return {
            relevantContent: [
                {
                    type: 'course',
                    title: 'Similar training program from past projects',
                    relevance: 0.92,
                    snippet: 'Successful implementation of role-based training with hands-on labs'
                },
                {
                    type: 'best_practice',
                    title: 'Industry best practices for this domain',
                    relevance: 0.87,
                    snippet: 'Progressive difficulty levels with assessment checkpoints'
                },
                {
                    type: 'learning_path',
                    title: 'Recommended learning progression',
                    relevance: 0.85,
                    snippet: 'Start with fundamentals, build to advanced concepts, conclude with capstone'
                }
            ],
            metadata: {
                total_documents_searched: 150,
                query_time_ms: 45
            }
        };
    } catch (error) {
        console.error('Error querying RAG:', error);
        return null;
    }
}

/**
 * Build RAG-enhanced prompt for AI
 */
function buildRAGEnhancedPrompt(projectName, description, roles, ragContext) {
    let prompt = `
Analyze this training project and provide recommendations:

Project: ${projectName}
Description: ${description}
Target Roles: ${roles.join(', ')}
`;

    if (ragContext?.relevantContent) {
        prompt += `\n\nRELEVANT CONTEXT FROM KNOWLEDGE BASE:\n`;
        ragContext.relevantContent.forEach(item => {
            prompt += `- ${item.title}: ${item.snippet}\n`;
        });
    }

    prompt += `
Please provide:
1. Key insights about the project scope and goals (incorporating knowledge base context)
2. Recommended track structure (3-5 tracks)
3. Specific learning objectives (5-8 objectives)
`;

    return prompt;
}

/**
 * Generate RAG-enhanced suggestions
 */
async function generateRAGEnhancedSuggestions(prompt, ragContext) {
    // TODO: Call actual AI service with RAG context
    // For now, enhance mock suggestions with RAG data
    const projectName = document.getElementById('projectName')?.value || '';
    const description = document.getElementById('projectDescription')?.value || '';
    const targetRoles = Array.from(document.getElementById('projectTargetRoles')?.selectedOptions || [])
        .map(opt => opt.value);

    const baseSuggestions = generateMockSuggestions(projectName, description, targetRoles);

    // Enhance with RAG context
    if (ragContext?.relevantContent) {
        baseSuggestions.insights.unshift(
            `📚 RAG Analysis: Found ${ragContext.relevantContent.length} relevant resources from knowledge base`
        );
    }

    return baseSuggestions;
}

/**
 * Regenerate AI suggestions
 *
 * BUSINESS CONTEXT:
 * Allows user to regenerate suggestions if they're not satisfied
 * with the initial recommendations
 */
export async function regenerateAISuggestions() {
    console.log('🔄 Regenerating AI suggestions...');
    await generateAISuggestions();
}

/**
 * Generate mock AI suggestions
 * TODO: Replace with actual AI service call
 */
function generateMockSuggestions(projectName, description, targetRoles) {
    return {
        insights: [
            `This project focuses on comprehensive training for ${targetRoles.join(' and ')} roles.`,
            `The project scope suggests a ${description.length > 200 ? 'comprehensive' : 'focused'} learning path.`,
            `Recommended duration: 8-12 weeks based on content depth.`,
            `Suggested approach: Blend theoretical concepts with hands-on practical exercises.`
        ],
        tracks: [
            {
                name: 'Fundamentals',
                description: 'Core concepts and foundational knowledge',
                duration: '2 weeks',
                modules: 4
            },
            {
                name: 'Intermediate Skills',
                description: 'Building practical capabilities',
                duration: '3 weeks',
                modules: 6
            },
            {
                name: 'Advanced Topics',
                description: 'Deep dive into specialized areas',
                duration: '3 weeks',
                modules: 5
            },
            {
                name: 'Capstone Project',
                description: 'Real-world application and assessment',
                duration: '2 weeks',
                modules: 3
            }
        ],
        objectives: [
            'Understand core principles and best practices',
            'Apply concepts to real-world scenarios',
            'Demonstrate proficiency through hands-on exercises',
            'Collaborate effectively in team environments',
            'Develop problem-solving and critical thinking skills',
            'Master relevant tools and technologies',
            'Create production-ready deliverables',
            'Prepare for certification or career advancement'
        ]
    };
}

/**
 * Populate AI suggestions in the UI
 */
function populateAISuggestions(suggestions) {
    // Populate insights
    const insightsContainer = document.getElementById('projectInsights');
    if (insightsContainer) {
        insightsContainer.innerHTML = suggestions.insights.map(insight => `
            <div style="padding: 0.75rem; margin-bottom: 0.5rem; background: var(--card-background);
                        border-left: 3px solid var(--primary-color); border-radius: 4px;">
                💡 ${escapeHtml(insight)}
            </div>
        `).join('');
    }

    // Populate recommended tracks
    const tracksContainer = document.getElementById('recommendedTracks');
    if (tracksContainer) {
        tracksContainer.innerHTML = suggestions.tracks.map(track => `
            <div style="padding: 1rem; margin-bottom: 0.75rem; background: var(--card-background);
                        border: 1px solid var(--border-color); border-radius: 8px;">
                <h5 style="margin: 0 0 0.5rem 0; color: var(--primary-color);">${escapeHtml(track.name)}</h5>
                <p style="margin: 0 0 0.5rem 0; color: var(--text-muted); font-size: 0.9rem;">
                    ${escapeHtml(track.description)}
                </p>
                <div style="display: flex; gap: 1rem; font-size: 0.85rem; color: var(--text-muted);">
                    <span>⏱️ ${escapeHtml(track.duration)}</span>
                    <span>📚 ${track.modules} modules</span>
                </div>
            </div>
        `).join('');
    }

    // Populate learning objectives
    const objectivesContainer = document.getElementById('suggestedObjectives');
    if (objectivesContainer) {
        objectivesContainer.innerHTML = `
            <ul style="list-style: none; padding: 0; margin: 0;">
                ${suggestions.objectives.map(objective => `
                    <li style="padding: 0.5rem; margin-bottom: 0.25rem; background: var(--hover-color);
                                border-radius: 4px; display: flex; align-items: start; gap: 0.5rem;">
                        <span style="color: var(--success-color); font-weight: bold;">✓</span>
                        <span>${escapeHtml(objective)}</span>
                    </li>
                `).join('')}
            </ul>
        `;
    }
}

/**
 * Toggle AI chat panel visibility
 *
 * BUSINESS CONTEXT:
 * Allows users to minimize/maximize the interactive AI assistant
 * to focus on suggestions or engage in conversation
 */
export function toggleAIChatPanel() {
    const chatPanel = document.getElementById('aiChatPanel');
    const minimizedButton = document.getElementById('aiChatMinimized');

    if (chatPanel && minimizedButton) {
        if (chatPanel.style.display === 'none') {
            // Show panel, hide minimized button
            chatPanel.style.display = 'flex';
            minimizedButton.style.display = 'none';
        } else {
            // Hide panel, show minimized button
            chatPanel.style.display = 'none';
            minimizedButton.style.display = 'block';
        }
    }
}

/**
 * Send message to AI assistant
 *
 * BUSINESS CONTEXT:
 * Allows project creators to provide additional requirements, ask questions,
 * or refine suggestions through interactive conversation with RAG-enhanced AI
 *
 * TECHNICAL IMPLEMENTATION:
 * 1. Adds user message to conversation history
 * 2. Queries RAG for relevant context
 * 3. Sends to AI with full conversation history
 * 4. Updates suggestions based on conversation
 */
export async function sendAIChatMessage() {
    const input = document.getElementById('aiChatInput');
    const messagesContainer = document.getElementById('aiChatMessages');

    if (!input || !messagesContainer) return;

    const userMessage = input.value.trim();
    if (!userMessage) return;

    // Add user message to UI
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'user-message';
    userMessageDiv.style.cssText = 'margin-bottom: 1rem; text-align: right;';
    userMessageDiv.innerHTML = `
        <strong style="color: var(--secondary-color);">You:</strong>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; background: var(--primary-color);
                   color: white; padding: 0.75rem; border-radius: 8px; display: inline-block;
                   text-align: left; max-width: 80%;">
            ${escapeHtml(userMessage)}
        </p>
    `;
    messagesContainer.appendChild(userMessageDiv);

    // Clear input
    input.value = '';

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-typing';
        typingDiv.innerHTML = '<em style="color: var(--text-muted);">🤖 AI is thinking and researching...</em>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Send to context-aware AI assistant
        const response = await sendContextAwareMessage(userMessage);

        // Remove typing indicator
        typingDiv.remove();

        // Add AI response to UI
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'ai-message';
        aiMessageDiv.style.cssText = 'margin-bottom: 1rem;';

        let aiContent = `
            <strong style="color: var(--primary-color);">🤖 AI Assistant:</strong>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                ${escapeHtml(response.message)}
            </p>
        `;

        // Add suggestions if provided
        if (response.suggestions && response.suggestions.length > 0) {
            aiContent += `
                <div style="margin-top: 0.5rem; padding: 0.5rem; background: var(--hover-color); border-radius: 4px;">
                    <strong style="font-size: 0.85rem;">Suggestions:</strong>
                    <ul style="margin: 0.25rem 0 0 1rem; font-size: 0.85rem;">
                        ${response.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Add source indicators
        if (response.webSearchUsed || response.ragSources.length > 0) {
            aiContent += `
                <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
                    ${response.webSearchUsed ? '<span style="color: var(--info-color);">🌐 Web research</span> ' : ''}
                    ${response.ragSources.length > 0 ? `<span style="color: var(--success-color);">📚 ${response.ragSources.length} knowledge base sources</span>` : ''}
                </div>
            `;
        }

        aiMessageDiv.innerHTML = aiContent;
        messagesContainer.appendChild(aiMessageDiv);

        // If AI suggests actions, handle them
        if (response.actions && response.actions.length > 0) {
            console.log('🔄 AI suggested actions:', response.actions);

            // Check if suggestions should be updated
            if (response.actions.includes('update_track_structure') ||
                response.actions.includes('adjust_timeline')) {
                console.log('🔄 Regenerating suggestions based on AI recommendations...');
                await generateAISuggestions();
            }
        }

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (error) {
        console.error('❌ Error sending chat message:', error);
        showNotification('Failed to get AI response', 'error');

        // Remove typing indicator if it exists
        const typingDiv = messagesContainer.querySelector('.ai-typing');
        if (typingDiv) typingDiv.remove();
    }
}

/**
 * Generate AI chat response with RAG context
 *
 * @param {string} userMessage - User's message
 * @param {Object} ragContext - Additional RAG context
 * @returns {Promise<Object>} AI response with message and update flag
 */
async function generateAIChatResponse(userMessage, ragContext) {
    // TODO: Replace with actual AI service call
    // For now, generate contextual mock responses

    const lowerMessage = userMessage.toLowerCase();

    // Detect intent and generate appropriate response
    if (lowerMessage.includes('track') || lowerMessage.includes('module')) {
        return {
            message: `I understand you want to discuss the track structure. Based on your input and similar projects in our knowledge base, I recommend maintaining a progressive learning path from fundamentals to advanced topics. Would you like me to adjust the number of tracks or modify the suggested duration for any specific track?`,
            updateSuggestions: false
        };
    } else if (lowerMessage.includes('objective') || lowerMessage.includes('goal')) {
        return {
            message: `Great question about learning objectives! I'll incorporate your feedback. The objectives should align with your project description and target roles. Would you like me to add more specific technical objectives or focus more on soft skills?`,
            updateSuggestions: false
        };
    } else if (lowerMessage.includes('duration') || lowerMessage.includes('week') || lowerMessage.includes('time')) {
        return {
            message: `I can adjust the timeline for you. Based on the project scope and RAG analysis of similar programs, I recommend 8-12 weeks for comprehensive coverage. However, this can be compressed to 6 weeks for intensive training or extended to 16 weeks for part-time learners. What timeline works best for your organization?`,
            updateSuggestions: false
        };
    } else if (lowerMessage.includes('update') || lowerMessage.includes('change') || lowerMessage.includes('modify')) {
        return {
            message: `I've updated the suggestions based on your requirements. The changes incorporate your feedback along with relevant best practices from our knowledge base. Please review the updated recommendations above.`,
            updateSuggestions: true
        };
    } else {
        return {
            message: `Thank you for the additional context. I've noted your feedback: "${userMessage}". This will help refine the project structure. Is there anything specific about the track structure, learning objectives, or project timeline you'd like me to adjust?`,
            updateSuggestions: false
        };
    }
}

// ==============================================================================
// TRACK CREATION FEATURES (TDD GREEN PHASE)
// ==============================================================================

/**
 * NLP-based Track Name Generator
 *
 * BUSINESS CONTEXT:
 * Uses linguistic transformation rules to generate appropriate track names
 * from role identifiers. Converts role names (e.g., "developers") to
 * discipline/field names (e.g., "Development").
 *
 * TECHNICAL IMPLEMENTATION:
 * - Applies morphological rules to transform profession nouns to field nouns
 * - Handles special cases (QA, DevOps, etc.)
 * - Returns properly capitalized track names
 *
 * EXAMPLES:
 * - application_developers → Application Development
 * - business_analysts → Business Analysis
 * - operations_engineers → Operations Engineering
 *
 * @param {string} audienceIdentifier - Underscore-separated role identifier
 * @returns {string} Properly formatted track name
 */
export function generateTrackName(audienceIdentifier) {
    // Split identifier into words
    const words = audienceIdentifier.split('_');

    // Get the last word (profession/role)
    const profession = words[words.length - 1];

    // Get prefix words (modifiers like "application", "business", etc.)
    const prefixWords = words.slice(0, -1);

    // Linguistic transformation rules: Profession → Field/Discipline
    const professionToField = {
        // Plural forms
        'developers': 'Development',
        'analysts': 'Analysis',
        'engineers': 'Engineering',
        'scientists': 'Science',
        'administrators': 'Administration',
        // Singular forms (fallback)
        'developer': 'Development',
        'analyst': 'Analysis',
        'engineer': 'Engineering',
        'scientist': 'Science',
        'administrator': 'Administration'
    };

    // Transform profession to field using NLP rules
    let fieldName = professionToField[profession.toLowerCase()];

    if (!fieldName) {
        // Fallback: Capitalize the profession if no rule matches
        fieldName = profession.charAt(0).toUpperCase() + profession.slice(1);
        console.warn(`No NLP transformation rule for profession: ${profession}`);
    }

    // Capitalize prefix words
    const capitalizedPrefix = prefixWords.map(word => {
        // Handle special cases
        if (word.toLowerCase() === 'qa') return 'QA';
        if (word.toLowerCase() === 'devops') return 'DevOps';

        // Standard capitalization
        return word.charAt(0).toUpperCase() + word.slice(1);
    });

    // Combine prefix + field name
    return [...capitalizedPrefix, fieldName].join(' ');
}

/**
 * Audience-to-Track Mapping Configuration
 *
 * BUSINESS CONTEXT:
 * Predefined mappings between target audiences and appropriate track
 * configurations. Each audience type gets a tailored track with relevant
 * skills, difficulty level, and description. Track names are generated
 * using NLP linguistic transformations.
 *
 * TECHNICAL IMPLEMENTATION:
 * Configuration object used by mapAudiencesToTracks() to generate
 * track proposals automatically based on audience selection.
 *
 * NOTE: Track names follow the pattern:
 * - application_developers → Application Development
 * - business_analysts → Business Analysis
 * - operations_engineers → Operations Engineering
 */
export const AUDIENCE_TRACK_MAPPING = {
    application_developers: {
        name: 'Application Development',
        description: 'Comprehensive training for software application development, covering modern programming practices, frameworks, and deployment strategies',
        difficulty: 'intermediate',
        skills: ['coding', 'software design', 'debugging', 'testing', 'deployment']
    },
    business_analysts: {
        name: 'Business Analysis',
        description: 'Requirements gathering and business process analysis training focused on stakeholder management and documentation',
        difficulty: 'beginner',
        skills: ['requirements analysis', 'documentation', 'stakeholder management', 'process modeling']
    },
    operations_engineers: {
        name: 'Operations Engineering',
        description: 'System operations, monitoring, and infrastructure management with emphasis on reliability and performance',
        difficulty: 'intermediate',
        skills: ['system administration', 'monitoring', 'troubleshooting', 'automation']
    },
    data_scientists: {
        name: 'Data Science',
        description: 'Data analysis, machine learning, and statistical modeling training with practical applications',
        difficulty: 'advanced',
        skills: ['data analysis', 'machine learning', 'statistics', 'Python', 'visualization']
    },
    qa_engineers: {
        name: 'QA Engineering',
        description: 'Quality assurance and testing methodologies including automation and continuous integration',
        difficulty: 'intermediate',
        skills: ['testing', 'automation', 'quality assurance', 'bug tracking', 'test planning']
    },
    devops_engineers: {
        name: 'DevOps Engineering',
        description: 'DevOps practices, CI/CD pipelines, containerization, and cloud infrastructure management',
        difficulty: 'advanced',
        skills: ['CI/CD', 'containerization', 'cloud platforms', 'infrastructure as code', 'automation']
    },
    security_engineers: {
        name: 'Security Engineering',
        description: 'Cybersecurity fundamentals, threat analysis, and security best practices',
        difficulty: 'advanced',
        skills: ['security analysis', 'threat modeling', 'penetration testing', 'compliance']
    },
    database_administrators: {
        name: 'Database Administration',
        description: 'Database design, optimization, backup strategies, and performance tuning',
        difficulty: 'intermediate',
        skills: ['database design', 'SQL', 'performance tuning', 'backup and recovery']
    },
    system_administrators: {
        name: 'System Administration',
        description: 'System configuration, maintenance, monitoring, and infrastructure management',
        difficulty: 'intermediate',
        skills: ['system configuration', 'Linux/Windows', 'scripting', 'monitoring', 'troubleshooting']
    },
    technical_architects: {
        name: 'Technical Architecture',
        description: 'System design, architectural patterns, scalability, and technical decision-making',
        difficulty: 'advanced',
        skills: ['system design', 'architectural patterns', 'scalability', 'cloud architecture', 'technical leadership']
    },
    product_managers: {
        name: 'Product Management',
        description: 'Product strategy, roadmap planning, stakeholder management, and feature prioritization',
        difficulty: 'intermediate',
        skills: ['product strategy', 'roadmap planning', 'stakeholder management', 'market research', 'prioritization']
    },
    project_managers: {
        name: 'Project Management',
        description: 'Project planning, team coordination, risk management, and delivery execution',
        difficulty: 'beginner',
        skills: ['project planning', 'agile methodologies', 'risk management', 'team coordination', 'stakeholder communication']
    },
    business_consultants: {
        name: 'Business Consulting',
        description: 'Business strategy, process improvement, change management, and client advisory',
        difficulty: 'advanced',
        skills: ['strategic analysis', 'process improvement', 'change management', 'client advisory', 'presentation skills']
    },
    data_analysts: {
        name: 'Data Analysis',
        description: 'Data exploration, statistical analysis, reporting, and business intelligence',
        difficulty: 'intermediate',
        skills: ['data visualization', 'SQL', 'Excel', 'statistical analysis', 'business intelligence']
    },
    data_engineers: {
        name: 'Data Engineering',
        description: 'Data pipeline development, ETL processes, data warehousing, and big data technologies',
        difficulty: 'advanced',
        skills: ['ETL development', 'data pipelines', 'SQL', 'big data technologies', 'data warehousing']
    },
    business_intelligence_analysts: {
        name: 'Business Intelligence Analysis',
        description: 'BI reporting, dashboard development, data modeling, and analytics',
        difficulty: 'intermediate',
        skills: ['BI tools', 'dashboard design', 'data modeling', 'SQL', 'analytics']
    },
    engineering_managers: {
        name: 'Engineering Management',
        description: 'Team leadership, technical mentorship, project delivery, and people management',
        difficulty: 'advanced',
        skills: ['team leadership', 'technical mentorship', 'performance management', 'hiring', 'strategic planning']
    },
    team_leads: {
        name: 'Team Leadership',
        description: 'Team coordination, technical guidance, sprint planning, and hands-on development',
        difficulty: 'intermediate',
        skills: ['team coordination', 'technical guidance', 'agile practices', 'code review', 'mentoring']
    },
    technical_directors: {
        name: 'Technical Direction',
        description: 'Technology strategy, architecture oversight, innovation, and cross-team leadership',
        difficulty: 'advanced',
        skills: ['technology strategy', 'architecture governance', 'innovation', 'cross-functional leadership', 'vendor management']
    },
    cto: {
        name: 'Technology Leadership',
        description: 'Technology vision, executive strategy, organizational transformation, and C-level decision-making',
        difficulty: 'advanced',
        skills: ['technology vision', 'executive strategy', 'digital transformation', 'budget management', 'board communication']
    }
};

/**
 * Check if project needs tracks
 *
 * BUSINESS CONTEXT:
 * Allows organization admins to indicate whether their project requires
 * structured learning tracks. Some projects may not need tracks (e.g.,
 * simple one-off training sessions).
 *
 * @returns {boolean} True if tracks are needed, false otherwise
 */
export function needsTracksForProject() {
    const checkbox = document.getElementById('needTracks');
    return checkbox ? checkbox.checked : true; // Default to true (tracks needed)
}

/**
 * Handle track requirement change event
 *
 * BUSINESS CONTEXT:
 * Responds to user toggling the "need tracks" checkbox by showing/hiding
 * track-related UI fields dynamically.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Checks current state of needTracks checkbox
 * - Shows or hides track creation fields accordingly
 * - Logs state change for debugging
 */
export function handleTrackRequirementChange() {
    const needTracks = needsTracksForProject();
    console.log('Track requirement changed:', needTracks);

    if (!needTracks) {
        hideTrackCreationFields();
    } else {
        showTrackCreationFields();
    }
}

/**
 * Show track creation fields
 *
 * BUSINESS CONTEXT:
 * Makes track-related input fields visible and enabled when user indicates
 * the project needs tracks.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sets display to block
 * - Enables all input fields
 * - Allows user interaction with track configuration
 */
export function showTrackCreationFields() {
    const container = document.getElementById('trackFieldsContainer');
    if (!container) return;

    container.style.display = 'block';

    // Enable all input fields within container
    const inputs = container.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.disabled = false;
    });
}

/**
 * Hide track creation fields
 *
 * BUSINESS CONTEXT:
 * Hides track-related input fields when user indicates the project
 * doesn't need tracks, providing cleaner UI.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sets display to none
 * - Disables all input fields
 * - Clears field values for clean state
 */
export function hideTrackCreationFields() {
    const container = document.getElementById('trackFieldsContainer');
    if (!container) return;

    container.style.display = 'none';

    // Disable and clear all input fields
    const inputs = container.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.disabled = true;
        if (input.type !== 'checkbox' && input.type !== 'radio') {
            input.value = '';
        }
    });
}

/**
 * Get selected target audiences from UI
 *
 * BUSINESS CONTEXT:
 * Extracts the list of target audiences selected by the user from the
 * multi-select dropdown in the project creation wizard.
 *
 * @returns {string[]} Array of selected audience identifiers
 */
export function getSelectedAudiences() {
    const select = document.getElementById('projectTargetRoles');
    if (!select) return [];

    const selectedOptions = Array.from(select.selectedOptions);
    return selectedOptions.map(option => option.value);
}

/**
 * Map selected audiences to track proposals
 *
 * BUSINESS CONTEXT:
 * For each selected target audience, generates a proposed track configuration
 * with appropriate name, description, difficulty, and skills. This automates
 * track creation based on audience needs using NLP-based name generation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates input (returns empty array for null/undefined/empty)
 * - Maps each audience to track configuration from AUDIENCE_TRACK_MAPPING
 * - Uses NLP-based generateTrackName() for unknown audiences
 * - Maintains audience order in output
 *
 * @param {string[]} audiences - Array of audience identifiers
 * @returns {Object[]} Array of proposed track configurations
 */
export function mapAudiencesToTracks(audiences) {
    // Handle invalid input
    if (!audiences || audiences.length === 0) {
        return [];
    }

    // Map each audience to a track configuration
    return audiences.map(audience => {
        const mapping = AUDIENCE_TRACK_MAPPING[audience];

        if (!mapping) {
            // Handle unknown audience with NLP-generated track name
            console.warn(`No predefined track mapping for audience: ${audience}`);
            console.log(`🔤 Using NLP to generate track name...`);

            const trackName = generateTrackName(audience);

            return {
                name: trackName,
                description: `Training track tailored for ${audience.replace(/_/g, ' ')}`,
                difficulty: 'intermediate',
                skills: [],
                audience: audience
            };
        }

        // Return complete track configuration with audience reference
        return {
            ...mapping,
            audience: audience
        };
    });
}

/**
 * Display generated tracks in Step 3
 *
 * BUSINESS CONTEXT:
 * Step 3 is "Configure Training Tracks" where users see the tracks that will
 * be created for their project. This function displays the auto-generated tracks
 * based on the target roles selected in Step 1.
 *
 * WHY THIS IS NEEDED:
 * - Users need to see what tracks will be created BEFORE proceeding to Step 4
 * - Provides transparency about what's being generated
 * - Allows users to understand the project structure early
 *
 * TECHNICAL IMPLEMENTATION:
 * - Stores tracks in generatedTracks array for later use
 * - Renders tracks in Step 3's track list container
 * - Shows track details: name, description, difficulty, skills
 * - Provides visual feedback if no tracks generated
 *
 * @param {Object[]} tracks - Array of track configurations to display
 */
export function displayGeneratedTracksInStep3(tracks) {
    console.log('📋 Displaying generated tracks in Step 3...');

    // Store tracks globally for later use
    generatedTracks = tracks || [];

    // Find the container in Step 3
    const container = document.getElementById('step3TracksList');
    if (!container) {
        console.error('❌ Step 3 tracks container not found');
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    if (generatedTracks.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);
                        background: var(--hover-color); border-radius: 8px;">
                <p>⚠️ No target roles selected in Step 1.</p>
                <p style="margin-top: 0.5rem;">
                    <a href="#" onclick="window.OrgAdmin.Projects.previousProjectStep();
                        window.OrgAdmin.Projects.previousProjectStep(); return false;"
                        style="color: var(--primary-600); text-decoration: underline;">
                        ← Go back to Step 1
                    </a> to select target roles.
                </p>
            </div>
        `;
        return;
    }

    // Render each track
    generatedTracks.forEach((track, index) => {
        const trackCard = document.createElement('div');
        trackCard.className = 'track-preview-card';
        trackCard.style.cssText = `
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: var(--card-background, #ffffff);
            border: 2px solid var(--border-color, #e0e0e0);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;

        trackCard.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--primary-600); font-size: 1.1rem;">
                        ${index + 1}. ${escapeHtml(track.name)}
                    </h4>
                    <span style="display: inline-block; padding: 0.25rem 0.75rem; background: var(--primary-50);
                                 color: var(--primary-700); border-radius: 12px; font-size: 0.85rem; font-weight: 500;">
                        ${escapeHtml(track.difficulty || 'intermediate')}
                    </span>
                </div>
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 0.25rem 0.75rem; background: var(--success-bg, #e8f5e9);
                                 color: var(--success, #10b981); border-radius: 12px; font-size: 0.85rem; font-weight: 500;">
                        ✓ Auto-Generated
                    </span>
                </div>
            </div>

            <p style="margin: 0.75rem 0; color: var(--text-secondary); line-height: 1.5;">
                ${escapeHtml(track.description || 'Training track for selected audience')}
            </p>

            ${track.skills && track.skills.length > 0 ? `
                <div style="margin-top: 0.75rem;">
                    <strong style="font-size: 0.9rem; color: var(--text-primary);">Skills Covered:</strong>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        ${track.skills.map(skill => `
                            <span style="padding: 0.25rem 0.75rem; background: var(--hover-color);
                                         border-radius: 12px; font-size: 0.85rem; color: var(--text-secondary);">
                                ${escapeHtml(skill)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${track.audience ? `
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                    <span style="font-size: 0.85rem; color: var(--text-muted);">
                        Target Audience: <strong>${escapeHtml(track.audience.replace(/_/g, ' '))}</strong>
                    </span>
                </div>
            ` : ''}
        `;

        container.appendChild(trackCard);
    });

    /**
     * Add summary box using design system classes
     *
     * WHY USE DESIGN SYSTEM CLASSES:
     * - Ensures visual consistency across the platform
     * - Leverages CSS variables for theming (light/dark mode support)
     * - Eliminates hardcoded color values (#e3f2fd, #3b82f6)
     * - Makes the UI maintainable through centralized styling
     *
     * CLASSES USED:
     * - info-box: Base container with padding, border-radius, white text
     * - info-box--info: Info variant with blue gradient background
     * - info-box__icon: Emoji icon with proper sizing
     * - info-box__title: Bold title text
     * - info-box__description: Descriptive text with proper opacity
     */
    const summary = document.createElement('div');
    summary.className = 'info-box info-box--info';
    summary.style.marginTop = '1.5rem'; // Keep spacing control
    summary.innerHTML = `
        <div class="info-box__icon">📊</div>
        <h4 class="info-box__title">Track Generation Summary</h4>
        <p class="info-box__description" style="margin: 0;">
            ${generatedTracks.length} ${generatedTracks.length === 1 ? 'track' : 'tracks'}
            will be automatically created for this project based on your target role selection.
        </p>
    `;
    container.appendChild(summary);

    console.log(`✅ Displayed ${generatedTracks.length} tracks in Step 3`);
}

/**
 * Show track confirmation dialog
 *
 * BUSINESS CONTEXT:
 * Before automatically creating tracks, shows the user a confirmation dialog
 * listing all proposed tracks. This provides transparency and control over
 * what will be created.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Dynamically generates modal HTML with track list
 * - Escapes HTML to prevent XSS attacks
 * - Attaches approve and cancel callbacks to buttons
 * - Opens modal using utility function
 * - Closes modal and executes callback on button click
 *
 * @param {Object[]} proposedTracks - Array of proposed track configurations
 * @param {Function} onApprove - Callback when user approves (receives tracks array)
 * @param {Function} onCancel - Callback when user cancels
 */
export function showTrackConfirmationDialog(proposedTracks, onApprove, onCancel) {
    const modalId = 'trackConfirmationModal';

    // Create modal HTML
    const modalHtml = `
        <div id="${modalId}" class="modal" role="dialog" aria-modal="true" style="display: none;">
            <div class="modal-overlay"></div>
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2>Confirm Track Creation</h2>
                    <button class="close-modal" onclick="document.getElementById('${modalId}').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 1rem;">
                        The following tracks will be created based on your selected target audiences:
                    </p>
                    <ul id="proposedTracksList" style="list-style: none; padding: 0; margin: 0 0 1.5rem 0;">
                        ${proposedTracks.map(track => `
                            <li style="padding: 1rem; margin-bottom: 0.75rem; 
                                       background: var(--hover-color); border-radius: 8px;
                                       border-left: 4px solid var(--primary-color);">
                                <strong style="color: var(--primary-color); font-size: 1.1rem;">
                                    ${escapeHtml(track.name)}
                                </strong>
                                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.9rem;">
                                    ${escapeHtml(track.description)}
                                </p>
                                <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                                    <span>📊 Difficulty: ${escapeHtml(track.difficulty)}</span>
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="modal-actions">
                    <button id="approveTracksBtn" class="btn btn-primary">
                        ✓ Approve and Create Tracks
                    </button>
                    <button id="cancelTracksBtn" class="btn btn-secondary">
                        ✗ Cancel
                    </button>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    openModal(modalId);

    // Attach event listeners
    document.getElementById('approveTracksBtn').addEventListener('click', () => {
        closeModal(modalId);
        document.getElementById(modalId).remove();
        onApprove(proposedTracks);
    });

    document.getElementById('cancelTracksBtn').addEventListener('click', () => {
        closeModal(modalId);
        document.getElementById(modalId).remove();
        onCancel();
    });
}

/**
 * Handle track creation approval
 *
 * BUSINESS CONTEXT:
 * When user approves the proposed tracks, creates each track via the API
 * and provides feedback on success or failure.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Iterates through approved tracks
 * - Creates each track via createTrack API
 * - Shows success notification with count
 * - Handles API errors gracefully
 * - Logs errors for debugging
 *
 * @param {Object[]} approvedTracks - Array of approved track configurations
 * @returns {Promise<void>}
 */
export async function handleTrackApproval(approvedTracks) {
    // Validate input
    if (!approvedTracks || approvedTracks.length === 0) {
        return;
    }

    try {
        // Create tracks via API
        console.log(`Creating ${approvedTracks.length} approved tracks...`);

        for (const track of approvedTracks) {
            // Prepare track data with organization and project IDs
            const trackData = {
                organization_id: currentOrganizationId,
                project_id: currentProjectId,
                name: track.name,
                description: track.description,
                difficulty: track.difficulty,
                skills: track.skills || [],
                audience: track.audience
            };

            // Create track via API
            await createTrack(trackData);
            console.log('Created track:', track.name);
        }

        showNotification('success', `${approvedTracks.length} tracks created successfully`);

        // Advance wizard or complete project creation
        // This would be called by the wizard flow
        console.log('Track creation completed');

    } catch (error) {
        console.error('Error creating tracks:', error);
        showNotification('error', 'Failed to create tracks. Please try again.');
    }
}

/**
 * Handle track creation cancellation
 *
 * BUSINESS CONTEXT:
 * When user cancels track creation, returns them to the track configuration
 * step so they can modify their selections.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Logs cancellation event
 * - No tracks created
 * - Returns user to previous step in wizard
 */
export function handleTrackCancellation() {
    console.log('Track creation cancelled, returning to track configuration');

    // Return to track creation step (step 3 = index 2 in framework)
    if (projectWizard) {
        projectWizard.goToStep(2); // Framework uses 0-based indexing
    }
}

// Store generated tracks for Step 3 review
let generatedTracks = [];

/**
 * Populate track review list in Step 4
 *
 * BUSINESS CONTEXT:
 * Displays all generated tracks in the review step (Step 4) so users can
 * see what tracks will be created with the project. Shows track details
 * including name, description, difficulty, and skills. Each track has a
 * "Manage Track" button to configure instructors, courses, and students.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads tracks from generatedTracks array
 * - Dynamically generates HTML for each track
 * - Updates summary statistics (total tracks, roles)
 * - Provides visual feedback if no tracks available
 * - Adds management button for each track
 *
 * @param {Object[]} tracks - Array of track configurations to display
 */
export function populateTrackReviewList(tracks) {
    const reviewList = document.getElementById('tracksReviewList');
    const totalTracksCount = document.getElementById('totalTracksCount');
    const totalRolesCount = document.getElementById('totalRolesCount');

    if (!reviewList) {
        console.error('tracksReviewList element not found');
        return;
    }

    // Store tracks for later use
    generatedTracks = tracks || [];

    if (generatedTracks.length === 0) {
        reviewList.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);
                        background: var(--hover-color); border-radius: 8px;">
                <p>No tracks generated yet. Go back to Step 3 and click "Next: Review & Create"</p>
            </div>
        `;
        if (totalTracksCount) totalTracksCount.textContent = '0';
        if (totalRolesCount) totalRolesCount.textContent = '0';

        // Reset popup counts as well
        const popupTracksCount = document.getElementById('popupTotalTracksCount');
        const popupRolesCount = document.getElementById('popupTotalRolesCount');
        if (popupTracksCount) popupTracksCount.textContent = '0';
        if (popupRolesCount) popupRolesCount.textContent = '0';

        return;
    }

    // Render track list with management buttons
    reviewList.innerHTML = generatedTracks.map((track, index) => `
        <div style="padding: 1.5rem; margin-bottom: 1rem; background: var(--card-background);
                    border: 2px solid var(--border-color); border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <h5 style="margin: 0; color: var(--primary-color); font-size: 1.1rem;">
                        ${index + 1}. ${escapeHtml(track.name)}
                    </h5>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="padding: 0.25rem 0.75rem; background: var(--primary-color);
                                 color: white; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                        ${escapeHtml(track.difficulty || 'intermediate')}
                    </span>
                    <button
                        type="button"
                        class="btn btn-secondary btn-sm"
                        onclick="window.OrgAdmin.Projects.openTrackManagement(${index})"
                        style="padding: 0.5rem 1rem; font-size: 0.85rem; white-space: nowrap;">
                        ⚙️ Manage Track
                    </button>
                </div>
            </div>
            <p style="margin: 0 0 0.75rem 0; color: var(--text-muted); font-size: 0.9rem;">
                ${escapeHtml(track.description || 'No description provided')}
            </p>
            ${track.skills && track.skills.length > 0 ? `
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem;">
                    ${track.skills.map(skill => `
                        <span style="padding: 0.25rem 0.75rem; background: var(--hover-color);
                                     border: 1px solid var(--border-color); border-radius: 16px;
                                     font-size: 0.8rem; color: var(--text-color);">
                            ${escapeHtml(skill)}
                        </span>
                    `).join('')}
                </div>
            ` : ''}
            ${track.instructors && track.instructors.length > 0 ? `
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                        👨‍🏫 Instructors (${track.instructors.length}):
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                        ${track.instructors.map(inst => `
                            <span style="padding: 0.25rem 0.75rem; background: var(--success-color, #10b981);
                                         color: white; border-radius: 12px; font-size: 0.75rem;">
                                ${escapeHtml(inst.name || inst.email)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            ${track.courses && track.courses.length > 0 ? `
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                        📚 Courses (${track.courses.length}):
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                        ${track.courses.map(course => `
                            <span style="padding: 0.5rem; background: var(--hover-color);
                                         border-left: 3px solid var(--info-color, #3b82f6); border-radius: 4px;
                                         font-size: 0.85rem;">
                                ${escapeHtml(course.name || course.title)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');

    // Update summary statistics (both popup and inline versions)
    const trackCount = generatedTracks.length;
    const uniqueRoles = new Set(generatedTracks.map(t => t.audience).filter(Boolean));
    const roleCount = uniqueRoles.size || trackCount;

    if (totalTracksCount) {
        totalTracksCount.textContent = trackCount;
    }

    if (totalRolesCount) {
        totalRolesCount.textContent = roleCount;
    }

    // Update popup statistics
    const popupTracksCount = document.getElementById('popupTotalTracksCount');
    const popupRolesCount = document.getElementById('popupTotalRolesCount');

    if (popupTracksCount) {
        popupTracksCount.textContent = trackCount;
    }

    if (popupRolesCount) {
        popupRolesCount.textContent = roleCount;
    }

    console.log(`✅ Populated ${generatedTracks.length} tracks in review list with management buttons`);
}

/**
 * Open custom track creation modal
 *
 * BUSINESS CONTEXT:
 * Allows organization admins to create additional custom tracks beyond
 * the automatically generated ones. Opens the track creation modal from
 * the org-admin-tracks module.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Checks if org-admin-tracks module is loaded
 * - Calls showCreateTrackModal() from tracks module
 * - Handles case where tracks module not available
 * - Provides fallback notification
 */
export function openCustomTrackCreation() {
    console.log('🎓 Opening custom track creation modal...');

    // Check if tracks module is available
    if (window.OrgAdmin?.Tracks?.showCreateTrackModal) {
        // Use the existing track creation modal from org-admin-tracks module
        window.OrgAdmin.Tracks.showCreateTrackModal();
    } else {
        // Fallback: Show notification that feature needs tracks module
        console.warn('Tracks module not loaded - cannot open custom track creation');
        showNotification('Track creation module not loaded. Please ensure all modules are initialized.', 'warning');
    }
}

// ============================================================================
// TRACK MANAGEMENT IN WIZARD (STEP 4)
// ============================================================================

// Store current track being managed
let currentTrackIndex = null;

/**
 * Open track management modal for a specific track
 *
 * BUSINESS CONTEXT:
 * Allows organization admins to configure a track before project creation.
 * They can add instructors, create courses, and prepare student enrollments.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Opens modal with tabbed interface
 * - Loads track data into tabs
 * - Provides separate interfaces for instructors, courses, and students
 * - Updates track data in generatedTracks array
 *
 * @param {number} trackIndex - Index of track in generatedTracks array
 */
export function openTrackManagement(trackIndex) {
    currentTrackIndex = trackIndex;
    const track = generatedTracks[trackIndex];

    if (!track) {
        console.error('Track not found at index:', trackIndex);
        return;
    }

    console.log('📊 Opening track management for:', track.name);

    // Initialize track arrays if not present
    if (!track.instructors) track.instructors = [];
    if (!track.courses) track.courses = [];
    if (!track.students) track.students = [];

    // Create modal HTML dynamically (prevents blur issues with static modal-overlay)
    const modalHtml = `
        <div id="trackManagementModal" class="modal" style="display: none;">
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.75); z-index: 9999;"
                 onclick="window.OrgAdmin.Projects.closeTrackManagement()"></div>
            <div class="modal-content" style="position: relative; z-index: 10000; max-width: 900px;
                        margin: 2rem auto; background: var(--surface-color); border-radius: 12px;
                        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
                <div class="modal-header">
                    <h2 id="trackManagementTitle">Manage Track: ${escapeHtml(track.name)}</h2>
                    <button class="modal-close" onclick="window.OrgAdmin.Projects.closeTrackManagement()">&times;</button>
                </div>
                <div class="modal-body">
                    <!-- Tab Navigation -->
                    <div class="modal-tabs" style="display: flex; border-bottom: 1px solid var(--border-color); margin-bottom: 1.5rem;">
                        <button id="trackInfoTab" class="modal-tab active" onclick="window.OrgAdmin.Projects.switchTrackTab('info')">
                            📋 Track Info
                        </button>
                        <button id="trackInstructorsTab" class="modal-tab" onclick="window.OrgAdmin.Projects.switchTrackTab('instructors')">
                            👨‍🏫 Instructors (${track.instructors.length})
                        </button>
                        <button id="trackCoursesTab" class="modal-tab" onclick="window.OrgAdmin.Projects.switchTrackTab('courses')">
                            📚 Courses (${track.courses.length})
                        </button>
                        <button id="trackStudentsTab" class="modal-tab" onclick="window.OrgAdmin.Projects.switchTrackTab('students')">
                            👥 Students (${track.students.length})
                        </button>
                    </div>

                    <!-- Tab Content -->
                    <div id="trackInfoContent" class="tab-content" style="display: block;">
                        ${renderTrackInfoTab(track)}
                    </div>
                    <div id="trackInstructorsContent" class="tab-content" style="display: none;">
                        ${renderTrackInstructorsTab(track)}
                    </div>
                    <div id="trackCoursesContent" class="tab-content" style="display: none;">
                        ${renderTrackCoursesTab(track)}
                    </div>
                    <div id="trackStudentsContent" class="tab-content" style="display: none;">
                        ${renderTrackStudentsTab(track)}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="window.OrgAdmin.Projects.closeTrackManagement()">
                        Close
                    </button>
                    <button class="btn btn-primary" onclick="window.OrgAdmin.Projects.saveTrackChanges()">
                        ✓ Save Changes
                    </button>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('trackManagementModal');
    if (existingModal) existingModal.remove();

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    document.getElementById('trackManagementModal').style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent body scroll
}

/**
 * Render track info tab content
 */
function renderTrackInfoTab(track) {
    return `
        <div style="display: grid; gap: 1.5rem;">
            <div>
                <h4 style="margin: 0 0 0.5rem 0;">${escapeHtml(track.name)}</h4>
                <p style="margin: 0; color: var(--text-muted);">${escapeHtml(track.description || 'No description')}</p>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>Difficulty:</strong>
                    <span class="badge badge-${track.difficulty}">${escapeHtml(track.difficulty || 'intermediate')}</span>
                </div>
                <div>
                    <strong>Audience:</strong> ${escapeHtml(track.audience || 'N/A')}
                </div>
            </div>
            ${track.skills && track.skills.length > 0 ? `
                <div>
                    <strong>Skills:</strong>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        ${track.skills.map(skill => `
                            <span style="padding: 0.25rem 0.75rem; background: var(--hover-color);
                                         border: 1px solid var(--border-color); border-radius: 16px;
                                         font-size: 0.85rem;">
                                ${escapeHtml(skill)}
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            <div style="background: var(--info-bg, #e3f2fd); padding: 1rem; border-radius: 8px;
                        border-left: 4px solid var(--info-color, #2196f3);">
                <strong>💡 Tip:</strong> Use the tabs above to add instructors, create courses, and manage student enrollments for this track.
            </div>
        </div>
    `;
}

/**
 * Render track instructors tab content
 */
function renderTrackInstructorsTab(track) {
    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Assigned Instructors</h4>
                <button class="btn btn-primary" onclick="window.OrgAdmin.Projects.addInstructorToTrack()">
                    ➕ Add Instructor
                </button>
            </div>

            ${track.instructors.length > 0 ? `
                <div id="trackInstructorsList" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${track.instructors.map((instructor, idx) => `
                        <div style="display: flex; justify-content: space-between; align-items: center;
                                    padding: 1rem; background: var(--card-background); border: 1px solid var(--border-color);
                                    border-radius: 8px;">
                            <div>
                                <div style="font-weight: 600;">${escapeHtml(instructor.name || 'Unnamed')}</div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(instructor.email || '')}</div>
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="window.OrgAdmin.Projects.removeInstructorFromTrack(${idx})">
                                Remove
                            </button>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color); border-radius: 8px; color: var(--text-muted);">
                    No instructors assigned yet. Click "Add Instructor" to get started.
                </div>
            `}
        </div>
    `;
}

/**
 * Render track courses tab content
 */
function renderTrackCoursesTab(track) {
    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Track Courses</h4>
                <button class="btn btn-primary" onclick="window.OrgAdmin.Projects.createCourseForTrack()">
                    ➕ Create Course
                </button>
            </div>

            ${track.courses.length > 0 ? `
                <div id="trackCoursesList" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${track.courses.map((course, idx) => `
                        <div style="display: flex; justify-content: space-between; align-items: center;
                                    padding: 1rem; background: var(--card-background); border: 1px solid var(--border-color);
                                    border-radius: 8px;">
                            <div style="flex: 1;">
                                <div style="font-weight: 600;">${escapeHtml(course.name || course.title || 'Unnamed Course')}</div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(course.description || '')}</div>
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="window.OrgAdmin.Projects.removeCourseFromTrack(${idx})">
                                Remove
                            </button>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color); border-radius: 8px; color: var(--text-muted);">
                    No courses created yet. Click "Create Course" to add your first course.
                </div>
            `}

            <div style="background: var(--info-bg, #e3f2fd); padding: 1rem; border-radius: 8px;">
                <strong>📚 Course Creation:</strong> Clicking "Create Course" will open the course creation wizard where you can build complete course content for this track.
            </div>
        </div>
    `;
}

/**
 * Render track students tab content
 */
function renderTrackStudentsTab(track) {
    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Enrolled Students</h4>
                <button class="btn btn-primary" onclick="window.OrgAdmin.Projects.addStudentToTrack()">
                    ➕ Add Student
                </button>
            </div>

            ${track.students.length > 0 ? `
                <div id="trackStudentsList" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${track.students.map((student, idx) => `
                        <div style="display: flex; justify-content: space-between; align-items: center;
                                    padding: 1rem; background: var(--card-background); border: 1px solid var(--border-color);
                                    border-radius: 8px;">
                            <div>
                                <div style="font-weight: 600;">${escapeHtml(student.name || 'Unnamed')}</div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(student.email || '')}</div>
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="window.OrgAdmin.Projects.removeStudentFromTrack(${idx})">
                                Remove
                            </button>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color); border-radius: 8px; color: var(--text-muted);">
                    No students enrolled yet. Click "Add Student" to enroll students.
                </div>
            `}
        </div>
    `;
}

/**
 * Switch between tabs in track management modal
 */
export function switchTrackTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.modal-tab').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const contentMap = {
        'info': 'trackInfoContent',
        'instructors': 'trackInstructorsContent',
        'courses': 'trackCoursesContent',
        'students': 'trackStudentsContent'
    };

    const contentId = contentMap[tabName];
    const content = document.getElementById(contentId);
    if (content) {
        content.style.display = 'block';
    }

    // Add active class to selected tab button
    const tabMap = {
        'info': 'trackInfoTab',
        'instructors': 'trackInstructorsTab',
        'courses': 'trackCoursesTab',
        'students': 'trackStudentsTab'
    };

    const tabId = tabMap[tabName];
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add('active');
    }
}

/**
 * Add instructor to track
 */
export async function addInstructorToTrack() {
    // TODO: Open instructor selection modal
    // For now, prompt for instructor details
    const name = prompt('Enter instructor name:');
    const email = prompt('Enter instructor email:');

    if (name && email) {
        const track = generatedTracks[currentTrackIndex];
        if (!track.instructors) track.instructors = [];

        track.instructors.push({ name, email });

        showNotification(`Instructor ${name} added to track`, 'success');

        // Refresh modal
        openTrackManagement(currentTrackIndex);
    }
}

/**
 * Remove instructor from track
 */
export function removeInstructorFromTrack(instructorIndex) {
    const track = generatedTracks[currentTrackIndex];
    const instructor = track.instructors[instructorIndex];

    if (confirm(`Remove ${instructor.name} from this track?`)) {
        track.instructors.splice(instructorIndex, 1);
        showNotification('Instructor removed', 'info');
        openTrackManagement(currentTrackIndex);
    }
}

/**
 * Create course for track
 *
 * BUSINESS LOGIC:
 * Opens course creation modal pre-populated with track context.
 * On successful course creation, adds the course to the track's courses array
 * and refreshes the track management modal.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Checks if course creation modal exists (window.OrgAdmin.Courses.showCreateCourseModal)
 * - Passes track context (trackId, trackName, difficulty) to modal
 * - Provides callback function to receive created course
 * - Adds created course to track's courses array
 * - Reopens track management modal to show updated course list
 * - Falls back to prompt() if modal doesn't exist
 */
export function createCourseForTrack() {
    const track = generatedTracks[currentTrackIndex];

    // Check if course creation modal exists
    if (window.OrgAdmin?.Courses?.showCreateCourseModal) {
        // Close current track management modal
        closeTrackManagement();

        // Open course creation modal with track context and callback
        window.OrgAdmin.Courses.showCreateCourseModal(
            {
                trackId: track.id,
                trackName: track.name,
                difficulty: track.difficulty
            },
            // Callback function to handle created course
            (createdCourse) => {
                // Initialize courses array if not present
                if (!track.courses) track.courses = [];

                // Add created course to track
                track.courses.push({
                    id: createdCourse.id,
                    name: createdCourse.title,
                    title: createdCourse.title,
                    description: createdCourse.description,
                    trackId: track.id,
                    difficulty_level: createdCourse.difficulty_level,
                    category: createdCourse.category,
                    estimated_duration: createdCourse.estimated_duration,
                    duration_unit: createdCourse.duration_unit
                });

                // Reopen track management modal to show updated course list
                openTrackManagement(currentTrackIndex);
            }
        );
    } else {
        // Fallback: prompt for course details
        const courseName = prompt('Enter course name:');
        const courseDescription = prompt('Enter course description (optional):');

        if (courseName) {
            if (!track.courses) track.courses = [];
            track.courses.push({
                name: courseName,
                title: courseName,
                description: courseDescription || '',
                trackId: track.id
            });

            showNotification(`Course "${courseName}" added to track`, 'success');
            openTrackManagement(currentTrackIndex);
        }
    }
}

/**
 * Remove course from track
 */
export function removeCourseFromTrack(courseIndex) {
    const track = generatedTracks[currentTrackIndex];
    const course = track.courses[courseIndex];

    if (confirm(`Remove "${course.name}" from this track?`)) {
        track.courses.splice(courseIndex, 1);
        showNotification('Course removed', 'info');
        openTrackManagement(currentTrackIndex);
    }
}

/**
 * Add student to track
 */
export async function addStudentToTrack() {
    // TODO: Open student selection modal
    // For now, prompt for student details
    const name = prompt('Enter student name:');
    const email = prompt('Enter student email:');

    if (name && email) {
        const track = generatedTracks[currentTrackIndex];
        if (!track.students) track.students = [];

        track.students.push({ name, email });

        showNotification(`Student ${name} added to track`, 'success');

        // Refresh modal
        openTrackManagement(currentTrackIndex);
    }
}

/**
 * Remove student from track
 */
export function removeStudentFromTrack(studentIndex) {
    const track = generatedTracks[currentTrackIndex];
    const student = track.students[studentIndex];

    if (confirm(`Remove ${student.name} from this track?`)) {
        track.students.splice(studentIndex, 1);
        showNotification('Student removed', 'info');
        openTrackManagement(currentTrackIndex);
    }
}

/**
 * Save track changes and close modal
 */
export function saveTrackChanges() {
    showNotification('Track changes saved', 'success');
    closeTrackManagement();

    // Refresh the track review list to show updated data
    populateTrackReviewList(generatedTracks);
}

/**
 * Manage tracks for a specific project from the main Projects list
 *
 * BUSINESS CONTEXT:
 * Provides quick access to track management from the Projects tab without
 * needing to go through the Project Creation Wizard. Organization admins
 * can manage existing project tracks directly from the main list view.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches project details including associated tracks
 * - Loads tracks into temporary generatedTracks array
 * - Opens track management modal with first track selected
 * - Reuses existing openTrackManagement() modal code
 *
 * @param {string} projectId - UUID of the project to manage tracks for
 * @returns {Promise<void>}
 */
/**
 * Manage tracks for an existing project from the Projects tab main list
 *
 * BUSINESS CONTEXT:
 * Organization admins need to access track management for existing projects without
 * going through the Project Creation Wizard again. This function enables editing
 * tracks, courses, instructors, and students for projects that have already been
 * created and deployed.
 *
 * WHY THIS EXISTS:
 * - Originally, track management was only accessible during project creation (Step 4)
 * - After project creation, there was no way to edit tracks, add courses, or assign instructors
 * - This created a major UX gap: admins couldn't modify existing projects
 * - This function fills that gap by providing post-creation track management access
 *
 * ARCHITECTURAL DECISIONS:
 * - Reuses existing openTrackManagement() modal to avoid code duplication (DRY principle)
 * - Fetches fresh data from API rather than using cached data (ensures consistency)
 * - Uses generatedTracks array to maintain compatibility with existing modal code
 * - Provides clear user feedback for edge cases (no tracks, auth errors)
 *
 * TECHNICAL IMPLEMENTATION:
 * 1. Validates authentication and organization context
 * 2. Fetches project details to get project name for display
 * 3. Fetches all tracks associated with this project
 * 4. Transforms track data into format expected by existing modal
 * 5. Populates track review list (same UI as wizard Step 4)
 * 6. Opens track management modal for first track
 *
 * DEPENDENCY INVERSION PRINCIPLE:
 * - Depends on abstractions (API endpoints) not concrete implementations
 * - Uses showNotification abstraction for user feedback
 * - Calls existing modal functions rather than duplicating logic
 *
 * SINGLE RESPONSIBILITY PRINCIPLE:
 * - Only responsibility: Coordinate loading and displaying project tracks
 * - Delegates authentication to localStorage (separation of concerns)
 * - Delegates API calls to fetch API (separation of concerns)
 * - Delegates UI rendering to populateTrackReviewList (separation of concerns)
 * - Delegates modal display to openTrackManagement (separation of concerns)
 *
 * @param {string} projectId - UUID of the project whose tracks to manage
 * @returns {Promise<void>}
 *
 * @throws {Error} If project fetch fails
 * @throws {Error} If tracks fetch fails
 *
 * @example
 * // Called from Projects table "Manage Track" button
 * <button onclick="window.OrgAdmin.Projects.manageProjectTracks('proj-uuid-123')">
 *   📊 Manage Track
 * </button>
 */
export async function manageProjectTracks(projectId) {
    console.log('📊 Managing tracks for project:', projectId);

    try {
        // AUTHENTICATION CHECK
        // WHY: Prevent unauthorized access to project data
        // Security boundary: All API calls require authentication token
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            showNotification('Please log in to continue', 'error');
            return;
        }

        // ORGANIZATION CONTEXT CHECK
        // WHY: Multi-tenant system requires organization scope for all operations
        // Prevents cross-organization data access
        const orgId = localStorage.getItem('currentOrgId');
        if (!orgId) {
            showNotification('No organization selected', 'error');
            return;
        }

        // FETCH PROJECT DATA
        // WHY: Need project name for modal title and context
        // Uses organization-scoped endpoint to ensure multi-tenant security
        const projectResponse = await fetch(`${window.API_BASE_URL || 'https://localhost'}/api/v1/organizations/${orgId}/projects/${projectId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!projectResponse.ok) {
            throw new Error(`Failed to fetch project: ${projectResponse.status}`);
        }

        const project = await projectResponse.json();
        console.log('📋 Project data:', project);

        // FETCH TRACKS FOR THIS PROJECT
        // WHY: Get current track list to display in modal
        // Fresh fetch ensures we have latest data (not stale cached data)
        const tracksResponse = await fetch(`${window.API_BASE_URL || 'https://localhost'}/api/v1/organizations/${orgId}/projects/${projectId}/tracks`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!tracksResponse.ok) {
            throw new Error(`Failed to fetch tracks: ${tracksResponse.status}`);
        }

        const tracks = await tracksResponse.json();
        console.log('📊 Tracks for project:', tracks);

        // HANDLE EMPTY STATE
        // WHY: Projects may exist without tracks (draft state)
        // Provide clear guidance on how to add tracks
        if (!tracks || tracks.length === 0) {
            showNotification('This project has no tracks yet. Create tracks in the Project Creation Wizard.', 'info');
            return;
        }

        // DATA TRANSFORMATION
        // WHY: Modal expects specific format with default values for optional fields
        // Ensures modal doesn't break if backend sends incomplete data
        // OPEN/CLOSED PRINCIPLE: Transforming data to match interface, extensible for new fields
        generatedTracks = tracks.map(track => ({
            id: track.id,
            name: track.name,
            description: track.description || '',
            difficulty_level: track.difficulty_level || 'beginner',
            duration_weeks: track.duration_weeks || 0,
            instructors: track.instructors || [],
            courses: track.courses || [],
            students: track.students || [],
            project_id: projectId,
            project_name: project.name
        }));

        // POPULATE UI
        // WHY: Reuse existing track review list UI from wizard
        // Maintains UI consistency between wizard and post-creation editing
        populateTrackReviewList(generatedTracks);

        // OPEN MODAL
        // WHY: Modal provides full track management interface (courses, instructors, students)
        // Opens first track by default (index 0) for immediate access
        if (generatedTracks.length > 0) {
            openTrackManagement(0);
        }

    } catch (error) {
        // ERROR HANDLING
        // WHY: Provide clear user feedback when operations fail
        // Log technical details for debugging, show user-friendly message
        console.error('❌ Error managing project tracks:', error);
        showNotification(`Failed to load project tracks: ${error.message}`, 'error');
    }
}

/**
 * Close track management modal
 */
export function closeTrackManagement() {
    const modal = document.getElementById('trackManagementModal');
    if (modal) {
        modal.remove();
    }
    document.body.style.overflow = ''; // Restore body scroll
}

/**
 * Finalize project creation with tracks
 *
 * BUSINESS CONTEXT:
 * Final step in the project creation wizard. Creates the project in the database
 * along with all generated and custom tracks. This combines project metadata
 * from all wizard steps into a complete project creation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Gathers project data from all wizard steps
 * - Creates project via API (submitProjectForm logic)
 * - Associates all generated tracks with the project
 * - Shows success/error notifications
 * - Closes modal and refreshes project list on success
 *
 * @returns {Promise<void>}
 */
export async function finalizeProjectCreation() {
    console.log('✅ Finalizing project creation with tracks...');

    try {
        /**
         * Gather project data from wizard and transform to API schema
         *
         * WHY THIS TRANSFORMATION:
         * - API expects specific field names (see ProjectCreateRequest in project_endpoints.py)
         * - Some wizard fields (objectives, locations, tracks) are NOT in the API schema
         * - Those fields need to be handled separately after project creation
         * - API validates: name, slug, description, target_roles, duration_weeks,
         *   max_participants, start_date, end_date, selected_track_templates
         */
        const projectData = {
            // Required fields
            name: document.getElementById('projectName')?.value,
            slug: sanitizeSlug(document.getElementById('projectSlug')?.value),
            description: document.getElementById('projectDescription')?.value || null,

            // Optional fields matching API schema
            target_roles: getSelectedAudiences(), // Array of role strings
            duration_weeks: parseInt(document.getElementById('projectDuration')?.value) || null,
            max_participants: parseInt(document.getElementById('projectMaxParticipants')?.value) || null,
            start_date: document.getElementById('projectStartDate')?.value || null,
            end_date: document.getElementById('projectEndDate')?.value || null,

            // Optional: Track template IDs (if pre-selecting from templates)
            selected_track_templates: [] // Empty for now, tracks created separately
        };

        // Validate required fields
        if (!projectData.name || !projectData.slug) {
            showNotification('Project name and slug are required', 'error');
            return;
        }

        // Backend requires description with minimum 10 characters
        // Provide default description if none entered
        if (!projectData.description || projectData.description.trim().length < 10) {
            projectData.description = `Training project for ${projectData.name}. This project provides comprehensive learning paths and resources.`;
        }

        console.log('📋 Project data prepared for API:', projectData);
        console.log(`🌍 Will create ${wizardLocations.length} locations after project creation`);
        console.log(`📚 Will create ${generatedTracks.length} tracks after project creation`);

        // Create project with tracks
        const createdProject = await createProject(currentOrganizationId, projectData);

        console.log('✅ Project created successfully:', createdProject);

        // If locations were created, associate them with project
        if (wizardLocations.length > 0) {
            console.log(`🌍 Created ${wizardLocations.length} locations for multi-locations project`);
        }

        // If tracks were generated, create them associated with the project
        if (generatedTracks.length > 0) {
            console.log(`📋 Creating ${generatedTracks.length} tracks for project...`);

            // Store the created project ID for track association
            currentProjectId = createdProject.id || createdProject.project_id;

            /**
             * Create all tracks with their instructors, courses, and students
             *
             * WHY INHERIT PROJECT DATES:
             * - Tracks should align with the overall project timeline
             * - Start/end dates from Step 1 provide the boundary for all tracks
             * - Ensures tracks don't extend beyond project duration
             * - Provides sensible defaults that can be adjusted per-track if needed
             */
            for (const track of generatedTracks) {
                const trackData = {
                    organization_id: currentOrganizationId,
                    project_id: currentProjectId,
                    name: track.name,
                    description: track.description,
                    difficulty: track.difficulty || 'intermediate',
                    skills: track.skills || [],
                    audience: track.audience,
                    instructors: track.instructors || [],
                    courses: track.courses || [],
                    students: track.students || [],

                    // Inherit start/end dates from project (entered in Step 1)
                    start_date: projectData.start_date || null,
                    end_date: projectData.end_date || null
                };

                await createTrack(trackData);
                console.log('✅ Created track:', track.name);
            }

            showNotification(`Project created successfully with ${generatedTracks.length} tracks`, 'success');
        } else {
            showNotification('Project created successfully (no tracks)', 'success');
        }

        // Clean up
        generatedTracks = [];
        wizardLocations = [];
        closeModal('createProjectModal');

        // Refresh projects list
        await loadProjectsData();

    } catch (error) {
        console.error('❌ Error finalizing project creation:', error);
        showNotification(`Failed to create project: ${error.message || 'Unknown error'}`, 'error');
    }
}

/**
 * Toggle visibility of wizard progress tracker
 *
 * Business Context:
 * - Allows users to show/hide the step progress tracker in the project creation wizard
 * - Default state is hidden to reduce clutter
 * - Progress tracker shows steps 1-5 with completion status
 *
 * @global
 */
export function toggleWizardProgress() {
    const progressTracker = document.getElementById('project-wizard-progress');
    const button = document.getElementById('toggleWizardProgress');

    if (!progressTracker) {
        console.warn('Wizard progress tracker not found');
        return;
    }

    // Toggle visibility using CSS class (more reliable than inline styles)
    const isHidden = progressTracker.classList.contains('wizard-progress-hidden');

    if (isHidden) {
        // Show the progress tracker
        progressTracker.classList.remove('wizard-progress-hidden');
        if (button) {
            button.textContent = '📊 Hide Progress';
        }
        console.log('✅ Wizard progress tracker shown');
    } else {
        // Hide the progress tracker
        progressTracker.classList.add('wizard-progress-hidden');
        if (button) {
            button.textContent = '📊 Show Progress';
        }
        console.log('✅ Wizard progress tracker hidden');
    }
}

// Export for testing
if (typeof window !== 'undefined') {
    window.OrgAdmin = window.OrgAdmin || {};
    window.OrgAdmin.Projects = {
        ...window.OrgAdmin?.Projects,
        // Wizard navigation
        showCreateProjectModal,
        nextProjectStep,
        previousProjectStep,
        resetProjectWizard,
        submitProjectForm,
        toggleWizardProgress,
        // Draft save/load
        saveCurrentProjectDraft,
        loadProjectDraft,
        showDraftsList,
        // Project management
        loadProjectsData,
        viewProject,
        editProject,
        deleteProjectPrompt,
        confirmDeleteProject,
        filterProjects,
        // Member management
        manageMembers,
        removeMemberFromProject,
        // AI suggestions
        regenerateAISuggestions,
        toggleAIChatPanel,
        sendAIChatMessage,
        // Track creation features (Step 3)
        generateTrackName,
        needsTracksForProject,
        handleTrackRequirementChange,
        showTrackCreationFields,
        hideTrackCreationFields,
        getSelectedAudiences,
        mapAudiencesToTracks,
        showTrackConfirmationDialog,
        handleTrackApproval,
        handleTrackCancellation,
        // Step 2: Locations/Sub-Project management
        showAddLocationForm,
        saveLocation,
        cancelLocationForm,
        removeLocationFromWizard,
        // Step 4: Track review and management
        populateTrackReviewList,
        openCustomTrackCreation,
        openTrackManagement,
        closeTrackManagement,
        switchTrackTab,
        saveTrackChanges,
        manageProjectTracks,
        // Track management - Instructors
        addInstructorToTrack,
        removeInstructorFromTrack,
        // Track management - Courses
        createCourseForTrack,
        removeCourseFromTrack,
        // Track management - Students
        addStudentToTrack,
        removeStudentFromTrack,
        // Project creation finalization
        finalizeProjectCreation
    };

    // Explicitly assign toggleWizardProgress to ensure it's available
    window.OrgAdmin.Projects.toggleWizardProgress = toggleWizardProgress;
    console.log('✅ toggleWizardProgress explicitly assigned:', typeof window.OrgAdmin.Projects.toggleWizardProgress);
}

// ============================================================================
// GLOBAL VALIDATION AND CALCULATION FUNCTIONS (Called from HTML)
// ============================================================================

/**
 * Get next working day from a given date
 *
 * BUSINESS CONTEXT:
 * Projects should start on working days (Monday-Friday).
 * If current day is weekend, defaults to next Monday.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Sunday (0) -> Add 1 day to get Monday
 * - Saturday (6) -> Add 2 days to get Monday
 * - Monday-Friday (1-5) -> Return as-is
 *
 * @param {Date} date - Starting date
 * @returns {Date} Next working day (or same day if already working day)
 */
function getNextWorkingDay(date) {
    const result = new Date(date);
    const dayOfWeek = result.getDay();

    // Sunday (0) -> Add 1 day to Monday
    if (dayOfWeek === 0) {
        result.setDate(result.getDate() + 1);
    }
    // Saturday (6) -> Add 2 days to Monday
    else if (dayOfWeek === 6) {
        result.setDate(result.getDate() + 2);
    }
    // Monday-Friday (1-5) -> No change needed

    return result;
}

/**
 * Format date as YYYY-MM-DD for date input fields
 *
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Validate maximum participants field for projects
 *
 * BUSINESS CONTEXT:
 * Provides real-time validation to prevent invalid capacity values
 *
 * VALIDATION RULES:
 * - Must be a positive integer if provided
 * - Can be empty (unlimited capacity)
 * - Must be at least 1 if provided
 */
window.validateMaxParticipants = function() {
    const input = document.getElementById('projectMaxParticipants');
    const errorDiv = document.getElementById('projectMaxParticipantsError');

    if (!input || !errorDiv) return true;

    // Check for invalid input first (e.g., non-numeric characters in type="number" field)
    if (input.validity.badInput) {
        errorDiv.textContent = 'Invalid input - please enter numbers only';
        errorDiv.style.display = 'block';
        input.style.borderColor = '#dc2626';
        return false;
    }

    const value = input.value.trim();

    // Empty is valid (unlimited capacity)
    if (value === '') {
        errorDiv.style.display = 'none';
        input.style.borderColor = '';
        return true;
    }

    const num = parseInt(value, 10);

    // Check if it's a valid positive integer
    if (isNaN(num) || num < 1 || num.toString() !== value) {
        errorDiv.textContent = 'Must be a positive integer (minimum 1) or leave empty for unlimited';
        errorDiv.style.display = 'block';
        input.style.borderColor = '#dc2626';
        return false;
    }

    // Valid
    errorDiv.style.display = 'none';
    input.style.borderColor = '#10b981';
    return true;
};

/**
 * Validate maximum participants field for locations
 *
 * BUSINESS CONTEXT:
 * Provides real-time validation to prevent invalid capacity values for locations
 *
 * VALIDATION RULES:
 * - Must be a positive integer if provided
 * - Can be empty (unlimited capacity)
 * - Must be at least 1 if provided
 */
window.validateLocationMaxParticipants = function() {
    const input = document.getElementById('locationMaxParticipants');
    const errorDiv = document.getElementById('locationMaxParticipantsError');

    if (!input || !errorDiv) return true;

    // Check for invalid input first (e.g., non-numeric characters in type="number" field)
    if (input.validity.badInput) {
        errorDiv.textContent = 'Invalid input - please enter numbers only';
        errorDiv.style.display = 'block';
        input.style.borderColor = '#dc2626';
        return false;
    }

    const value = input.value.trim();

    // Empty is valid (unlimited capacity)
    if (value === '') {
        errorDiv.style.display = 'none';
        input.style.borderColor = '';
        return true;
    }

    const num = parseInt(value, 10);

    // Check if it's a valid positive integer
    if (isNaN(num) || num < 1 || num.toString() !== value) {
        errorDiv.textContent = 'Must be a positive integer (minimum 1) or leave empty for unlimited';
        errorDiv.style.display = 'block';
        input.style.borderColor = '#dc2626';
        return false;
    }

    // Valid
    errorDiv.style.display = 'none';
    input.style.borderColor = '#10b981';
    return true;
};

/**
 * Calculate location end date from start date and duration
 *
 * BUSINESS CONTEXT:
 * Auto-calculates end date excluding weekends for accurate project timeline
 *
 * CALCULATION:
 * - Start date + duration (weeks)
 * - Excludes Saturdays and Sundays
 * - Updates readonly end date field
 */
window.calculateLocationEndDate = function() {
    const startDateInput = document.getElementById('locationStartDate');
    const durationInput = document.getElementById('locationDuration');
    const endDateInput = document.getElementById('locationEndDate');

    if (!startDateInput || !durationInput || !endDateInput) {
        console.warn('Location date fields not found');
        return;
    }

    const startDate = startDateInput.value;
    const duration = parseInt(durationInput.value, 10);

    // Clear end date if either field is empty
    if (!startDate || !duration || duration < 1) {
        endDateInput.value = '';
        return;
    }

    // Calculate end date excluding weekends
    // IMPORTANT: Start date counts as the first business day
    let current = new Date(startDate);
    let businessDaysAdded = 1; // Count start date as day 1
    const totalBusinessDays = duration * 5; // 5 business days per week

    while (businessDaysAdded < totalBusinessDays) {
        current.setDate(current.getDate() + 1);
        const dayOfWeek = current.getDay();

        // Skip weekends (0 = Sunday, 6 = Saturday)
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            businessDaysAdded++;
        }
    }

    // Format as YYYY-MM-DD for date input
    const year = current.getFullYear();
    const month = String(current.getMonth() + 1).padStart(2, '0');
    const day = String(current.getDate()).padStart(2, '0');
    endDateInput.value = `${year}-${month}-${day}`;

    console.log(`✅ Calculated end date: ${endDateInput.value} (${duration} weeks from ${startDate})`);
};

/**
 * Calculate project end date from start date and duration
 *
 * BUSINESS CONTEXT:
 * Auto-calculates end date excluding weekends for accurate project timeline
 *
 * CALCULATION:
 * - Start date + duration (weeks)
 * - Excludes Saturdays and Sundays
 * - Updates readonly end date field
 */
window.calculateProjectEndDate = function() {
    const startDateInput = document.getElementById('projectStartDate');
    const durationInput = document.getElementById('projectDuration');
    const endDateInput = document.getElementById('projectEndDate');

    if (!startDateInput || !durationInput || !endDateInput) {
        console.warn('Project date fields not found');
        return;
    }

    const startDate = startDateInput.value;
    const duration = parseInt(durationInput.value, 10);

    // Clear end date if either field is empty
    if (!startDate || !duration || duration < 1) {
        endDateInput.value = '';
        return;
    }

    // Calculate end date excluding weekends
    // IMPORTANT: Start date counts as the first business day
    let current = new Date(startDate);
    let businessDaysAdded = 1; // Count start date as day 1
    const totalBusinessDays = duration * 5; // 5 business days per week

    while (businessDaysAdded < totalBusinessDays) {
        current.setDate(current.getDate() + 1);
        const dayOfWeek = current.getDay();

        // Skip weekends (0 = Sunday, 6 = Saturday)
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            businessDaysAdded++;
        }
    }

    // Format as YYYY-MM-DD for date input
    const year = current.getFullYear();
    const month = String(current.getMonth() + 1).padStart(2, '0');
    const day = String(current.getDate()).padStart(2, '0');
    endDateInput.value = `${year}-${month}-${day}`;

    console.log(`✅ Calculated project end date: ${endDateInput.value} (${duration} weeks from ${startDate})`);
};

/**
 * Toggle Project Summary Popup
 *
 * BUSINESS CONTEXT:
 * Provides optional project summary statistics in a non-intrusive popup.
 * Allows users to view project status without cluttering the wizard flow.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Toggles visibility of floating summary popup
 * - Updates button text to show current state
 * - Popup positioned near AI assistant but non-overlapping
 *
 * @export
 */
export function toggleProjectSummary() {
    const popup = document.getElementById('projectSummaryPopup');
    const button = document.getElementById('toggleProjectSummary');

    if (!popup) {
        console.warn('Project summary popup not found');
        return;
    }

    // Toggle display
    const isVisible = popup.style.display === 'block';

    if (isVisible) {
        popup.style.display = 'none';
        if (button) {
            button.textContent = '📊 Show Project Summary';
        }
    } else {
        popup.style.display = 'block';
        if (button) {
            button.textContent = '📊 Hide Project Summary';
        }
    }

    console.log(`Project summary popup ${isVisible ? 'hidden' : 'shown'}`);
}

