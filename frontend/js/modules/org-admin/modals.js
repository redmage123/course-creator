/**
 * Organization Admin Dashboard - Modal Management Module
 *
 * BUSINESS CONTEXT:
 * Manages all modal dialogs for the organization admin dashboard including
 * project creation, instructor assignment, student enrollment/unenrollment,
 * track management, analytics display, and instructor removal modals.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only modal display and management functions
 * - Open/Closed: New modals can be added without modifying existing code
 * - Dependency Inversion: Depends on abstractions (state, API, UI modules)
 *
 * ARCHITECTURE:
 * Extracted from monolithic org-admin-dashboard.js (3,273 lines) to improve
 * maintainability, testability, and separation of concerns.
 */
// Import dependencies from other modules
import { closeModal, showNotification } from './utils.js';
import {
    getCurrentOrganization,
    getCurrentProjectStep,
    setCurrentProjectStep,
    getSelectedTrackTemplates,
    setSelectedTrackTemplates,
    getRagSuggestionsCache,
    setRagSuggestionsCache,
    getSelectedProjectForAction,
    setSelectedProjectForAction,
    getInstructorAssignments,
    setInstructorAssignments,
    getSelectedStudents,
    setSelectedStudents,
    getAvailableInstructors,
    setAvailableInstructors,
    getCurrentAnalyticsProject,
    setCurrentAnalyticsProject,
    getSelectedStudentsForUnenrollment,
    setSelectedStudentsForUnenrollment,
    getSelectedInstructorsForRemoval,
    setSelectedInstructorsForRemoval,
    ORG_API_BASE
} from './state.js';
import {
    loadProjectsForTrackForm,
    loadAvailableInstructors,
    loadProjectTracksForAssignment,
    loadProjectModulesForAssignment,
    loadAvailableStudents,
    loadProjectTracksForEnrollment,
    loadProjectAnalytics,
    loadEnrolledStudentsForProject,
    loadAssignedInstructorsForProject,
    loadReplacementInstructorOptions
} from './api.js';
import {
    displayTrackAssignments,
    displayModuleAssignments,
    displayAvailableStudents,
    displayAnalyticsSummary,
    displayEnrolledStudents,
    displayAssignedInstructors,
    escapeHtml,
    capitalizeFirst
} from './ui.js';

// Module-level state for loaded templates
let loadedTrackTemplates = [];

// =============================================================================
// BASIC MODAL FUNCTIONS
// =============================================================================

/**
 * Show create project modal
 *
 * BUSINESS CONTEXT:
 * Initiates the multi-step project creation workflow with RAG integration
 */
export function showCreateProjectModal() {
    const modal = document.getElementById('createProjectModal');
    const modalContent = modal.querySelector('.draggable-modal');

    // Reset position
    if (modalContent) {
        modalContent.style.transform = 'translate(0px, 0px)';
    }

    modal.style.display = 'block';
}

/**
 * Show add instructor modal
 */
export function showAddInstructorModal() {
    document.getElementById('addInstructorModal').style.display = 'block';
}

/**
 * Show add student modal
 */
export function showAddStudentModal() {
    document.getElementById('addStudentModal').style.display = 'block';
}

// =============================================================================
// TRACK MANAGEMENT MODALS
// =============================================================================

/**
 * Show create track modal
 *
 * BUSINESS CONTEXT:
 * Allows organization admins to create new learning tracks
 */
export async function showCreateTrackModal() {
    const modal = document.getElementById('trackModal');
    const form = document.getElementById('trackForm');
    const title = document.getElementById('trackModalTitle');
    const submitBtn = document.getElementById('trackSubmitBtn');

    if (!modal || !form) return;

    // Reset form
    form.reset();
    document.getElementById('trackId').value = '';

    // Set modal title and button
    title.textContent = 'Create New Track';
    submitBtn.textContent = 'Create Track';

    // Load projects for the dropdown
    await loadProjectsForTrackForm();

    // Show modal
    modal.style.display = 'block';
}

/**
 * View track details in modal
 *
 * @param {string} trackId - The track ID to display
 */
export async function viewTrackDetails(trackId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load track details');
        }

        const track = await response.json();

        // Populate details modal
        const content = document.getElementById('trackDetailsContent');
        if (content) {
            content.innerHTML = `
                <div style="display: grid; gap: 1.5rem;">
                    <div>
                        <h3>${escapeHtml(track.name)}</h3>
                        <p>${escapeHtml(track.description || 'No description provided')}</p>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <strong>Project:</strong> ${escapeHtml(track.project_name || 'N/A')}
                        </div>
                        <div>
                            <strong>Status:</strong>
                            <span class="status-badge status-${track.status}">${capitalizeFirst(track.status)}</span>
                        </div>
                        <div>
                            <strong>Difficulty:</strong>
                            <span class="badge badge-${track.difficulty_level}">${capitalizeFirst(track.difficulty_level)}</span>
                        </div>
                        <div>
                            <strong>Duration:</strong> ${track.duration_weeks ? `${track.duration_weeks} weeks` : 'N/A'}
                        </div>
                        <div>
                            <strong>Students:</strong> ${track.enrollment_count || 0}${track.max_students ? ` / ${track.max_students}` : ''}
                        </div>
                        <div>
                            <strong>Instructors:</strong> ${track.instructor_count || 0}
                        </div>
                    </div>

                    ${track.target_audience && track.target_audience.length > 0 ? `
                        <div>
                            <strong>Target Audience:</strong>
                            <ul>
                                ${track.target_audience.map(a => `<li>${escapeHtml(a)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${track.prerequisites && track.prerequisites.length > 0 ? `
                        <div>
                            <strong>Prerequisites:</strong>
                            <ul>
                                ${track.prerequisites.map(p => `<li>${escapeHtml(p)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${track.learning_objectives && track.learning_objectives.length > 0 ? `
                        <div>
                            <strong>Learning Objectives:</strong>
                            <ul>
                                ${track.learning_objectives.map(o => `<li>${escapeHtml(o)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    <div style="font-size: 0.9rem; color: var(--text-muted);">
                        <div>Created: ${new Date(track.created_at).toLocaleString()}</div>
                        <div>Last Updated: ${new Date(track.updated_at).toLocaleString()}</div>
                    </div>
                </div>
            `;
        }

        // Store track ID for edit action
        document.getElementById('trackDetailsModal').dataset.trackId = trackId;

        // Show modal
        document.getElementById('trackDetailsModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading track details:', error);
        showNotification('Failed to load track details', 'error');
    }
}

/**
 * Edit track from details modal
 */
export function editTrackFromDetails() {
    const trackId = document.getElementById('trackDetailsModal').dataset.trackId;
    if (trackId) {
        closeModal('trackDetailsModal');
        editTrack(trackId);
    }
}

/**
 * Edit track
 *
 * @param {string} trackId - The track ID to edit
 */
export async function editTrack(trackId) {
    try {
        // Fetch track details
        const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load track details');
        }

        const track = await response.json();

        // Populate form
        document.getElementById('trackId').value = track.id;
        document.getElementById('trackName').value = track.name;
        document.getElementById('trackDescription').value = track.description || '';
        document.getElementById('trackProject').value = track.project_id;
        document.getElementById('trackDifficulty').value = track.difficulty_level;
        document.getElementById('trackDuration').value = track.duration_weeks || '';
        document.getElementById('trackMaxStudents').value = track.max_students || '';
        document.getElementById('trackAudience').value = (track.target_audience || []).join(', ');
        document.getElementById('trackPrerequisites').value = (track.prerequisites || []).join(', ');
        document.getElementById('trackObjectives').value = (track.learning_objectives || []).join(', ');

        // Update modal title and button
        document.getElementById('trackModalTitle').textContent = 'Edit Track';
        document.getElementById('trackSubmitBtn').textContent = 'Update Track';

        // Load projects
        await loadProjectsForTrackForm();

        // Show modal
        document.getElementById('trackModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading track for edit:', error);
        showNotification('Failed to load track', 'error');
    }
}

/**
 * Show delete track confirmation modal
 *
 * @param {string} trackId - The track ID to delete
 */
export function deleteTrack(trackId) {
    // Store track ID
    document.getElementById('deleteTrackId').value = trackId;

    // Show warning
    const warning = document.getElementById('deleteTrackWarning');
    if (warning) {
        warning.textContent = 'This action cannot be undone. All enrollments will be removed.';
    }

    // Show modal
    document.getElementById('deleteTrackModal').style.display = 'block';
}

// =============================================================================
// PROJECT CREATION STEP NAVIGATION
// =============================================================================

/**
 * Navigate to next project creation step
 */
export function nextProjectStep() {
    const currentStep = getCurrentProjectStep();

    if (currentStep === 1) {
        // Validate step 1 form
        const form = document.getElementById('createProjectForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // Move to step 2 and get RAG suggestions
        showProjectStep(2);
        generateRAGSuggestions();
    } else if (currentStep === 2) {
        // Move to step 3 and load track templates
        showProjectStep(3);
        loadTrackTemplates();
    }
}

/**
 * Navigate to previous project creation step
 */
export function previousProjectStep() {
    const currentStep = getCurrentProjectStep();
    if (currentStep > 1) {
        showProjectStep(currentStep - 1);
    }
}

/**
 * Show specific project creation step
 *
 * @param {number} stepNumber - The step number to display
 */
export function showProjectStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.project-step').forEach(step => {
        step.classList.remove('active');
    });

    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 === stepNumber) {
            step.classList.add('active');
        } else if (index + 1 < stepNumber) {
            step.classList.add('completed');
        }
    });

    // Show current step
    document.getElementById(`projectStep${stepNumber}`).classList.add('active');
    setCurrentProjectStep(stepNumber);
}

/**
 * Show custom track form (placeholder)
 */
export function showCustomTrackForm() {
    showNotification('Custom track creation will open in a new modal - coming soon!', 'info');
    // TODO: Implement custom track creation modal
}

// =============================================================================
// INSTRUCTOR ASSIGNMENT MODAL
// =============================================================================

/**
 * Show instructor assignment modal for a project
 *
 * @param {string} projectId - The project ID
 */
export async function showInstructorAssignmentModal(projectId) {
    setSelectedProjectForAction(projectId);

    try {
        // Load available instructors
        await loadAvailableInstructors();

        // Load project tracks and modules
        const tracks = await loadProjectTracksForAssignment(projectId);
        const modules = await loadProjectModulesForAssignment(projectId);

        // Display assignment interface
        displayTrackAssignments(tracks);
        displayModuleAssignments(modules);

        document.getElementById('instructorAssignmentModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading instructor assignment data:', error);
        showNotification('Failed to load instructor assignment interface', 'error');
    }
}

/**
 * Switch assignment tab (tracks/modules)
 *
 * @param {string} tabName - The tab name to switch to
 */
export function switchAssignmentTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.assignment-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.assignment-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    document.getElementById(tabName + 'AssignmentTab').classList.add('active');

    // Activate selected tab button
    event.target.classList.add('active');
}

// =============================================================================
// STUDENT ENROLLMENT MODAL
// =============================================================================

/**
 * Show student enrollment modal for a project
 *
 * @param {string} projectId - The project ID
 */
export async function showStudentEnrollmentModal(projectId) {
    setSelectedProjectForAction(projectId);
    setSelectedStudents([]);

    try {
        // Load available students and project tracks
        await loadAvailableStudents();
        await loadProjectTracksForEnrollment(projectId);

        document.getElementById('studentEnrollmentModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading student enrollment data:', error);
        showNotification('Failed to load student enrollment interface', 'error');
    }
}

// =============================================================================
// STUDENT UNENROLLMENT MODAL
// =============================================================================

/**
 * Show student unenrollment modal for a project
 *
 * @param {string} projectId - The project ID
 */
export async function showStudentUnenrollmentModal(projectId) {
    setSelectedProjectForAction(projectId);
    setSelectedStudents([]);

    try {
        // Load enrolled students for this project
        await loadEnrolledStudentsForProject(projectId);

        document.getElementById('studentUnenrollmentModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading student unenrollment data:', error);
        showNotification('Failed to load student unenrollment interface', 'error');
    }
}

// =============================================================================
// INSTRUCTOR REMOVAL MODAL
// =============================================================================

/**
 * Show instructor removal modal for a project
 *
 * @param {string} projectId - The project ID
 */
export async function showInstructorRemovalModal(projectId) {
    setSelectedProjectForAction(projectId);
    setSelectedInstructorsForRemoval([]);

    try {
        // Load assigned instructors for this project
        await loadAssignedInstructorsForProject(projectId);

        document.getElementById('instructorRemovalModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading instructor removal data:', error);
        showNotification('Failed to load instructor removal interface', 'error');
    }
}

// =============================================================================
// ANALYTICS MODAL
// =============================================================================

/**
 * Show project analytics modal
 *
 * @param {string} projectId - The project ID
 */
export async function showProjectAnalytics(projectId) {
    setCurrentAnalyticsProject(projectId);

    try {
        // Load project analytics data
        const analytics = await loadProjectAnalytics(projectId);
        displayAnalyticsSummary(analytics);

        // Load default analytics tab (overview)
        switchAnalyticsTab('overview');

        document.getElementById('projectAnalyticsModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading project analytics:', error);
        showNotification('Failed to load project analytics', 'error');
    }
}

/**
 * Switch analytics tab
 *
 * @param {string} tabName - The tab name to switch to
 */
export function switchAnalyticsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.analytics-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }

    // Load tab content
    loadAnalyticsTabContent(tabName);
}

/**
 * Load analytics tab content
 *
 * @param {string} tabName - The tab name
 */
function loadAnalyticsTabContent(tabName) {
    const container = document.getElementById('analyticsTabContent');

    switch(tabName) {
        case 'overview':
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <h4>Enrollment Trends</h4>
                        <div style="height: 200px; background: var(--hover-color); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            📈 Enrollment Chart Placeholder
                        </div>
                    </div>
                    <div>
                        <h4>Progress Distribution</h4>
                        <div style="height: 200px; background: var(--hover-color); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            📊 Progress Chart Placeholder
                        </div>
                    </div>
                </div>
            `;
            break;
        case 'progress':
            container.innerHTML = `
                <div>
                    <h4>Student Progress Tracking</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        📋 Detailed progress tracking table will be implemented here
                    </div>
                </div>
            `;
            break;
        case 'performance':
            container.innerHTML = `
                <div>
                    <h4>Performance Metrics</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        🎯 Performance analytics and quiz scores will be displayed here
                    </div>
                </div>
            `;
            break;
        case 'engagement':
            container.innerHTML = `
                <div>
                    <h4>Student Engagement</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        👥 Engagement metrics and activity patterns will be shown here
                    </div>
                </div>
            `;
            break;
    }
}

// =============================================================================
// RAG SUGGESTIONS (Part of Project Creation)
// =============================================================================

/**
 * Generate RAG suggestions for project creation
 */
async function generateRAGSuggestions() {
    try {
        const formData = new FormData(document.getElementById('createProjectForm'));
        const projectDescription = formData.get('description');
        const targetRoles = formData.get('target_roles');

        if (!projectDescription.trim()) {
            showNotification('Please provide a project description to get AI suggestions', 'warning');
            return;
        }

        // Show loading indicator
        document.getElementById('ragLoadingIndicator').style.display = 'block';
        document.getElementById('ragSuggestions').style.display = 'none';

        // Query RAG service for project planning assistance
        const ragQuery = `Create training project for: ${projectDescription}. Target roles: ${targetRoles || 'General'}`;

        const response = await fetch(`${window.CONFIG?.API_URLS.RAG}/api/v1/rag/query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: ragQuery,
                domain: 'project_planning',
                n_results: 5,
                metadata_filter: {
                    content_type: 'project_planning',
                    target_roles: targetRoles?.split('\n').map(r => r.trim()).filter(r => r) || []
                }
            })
        });

        if (response.ok) {
            const ragResult = await response.json();
            setRagSuggestionsCache(ragResult);
            displayRAGSuggestions(ragResult, projectDescription, targetRoles);
        } else {
            // Fallback to mock suggestions if RAG service is unavailable
            const mockSuggestions = generateMockRAGSuggestions(projectDescription, targetRoles);
            displayRAGSuggestions(mockSuggestions, projectDescription, targetRoles);
        }
    } catch (error) {
        console.error('Error generating RAG suggestions:', error);
        // Show mock suggestions as fallback
        const mockSuggestions = generateMockRAGSuggestions(
            document.getElementById('projectDescription').value,
            document.getElementById('projectTargetRoles').value
        );
        displayRAGSuggestions(mockSuggestions);
    }
}

/**
 * Display RAG suggestions
 *
 * @param {Object} ragResult - The RAG result object
 * @param {string} projectDescription - The project description
 * @param {string} targetRoles - The target roles
 */
function displayRAGSuggestions(ragResult, projectDescription, targetRoles) {
    // Hide loading and show suggestions
    document.getElementById('ragLoadingIndicator').style.display = 'none';
    document.getElementById('ragSuggestions').style.display = 'block';

    // Display project insights
    const insightsContainer = document.getElementById('projectInsights');
    insightsContainer.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <strong>Project Analysis:</strong>
            <p>${ragResult.enhanced_context || ragResult.analysis || 'AI analysis of your project description suggests a comprehensive training approach.'}</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="insight-metric">
                <strong>Recommended Duration:</strong><br>
                <span style="color: var(--primary-color);">${ragResult.recommended_duration || '12-16 weeks'}</span>
            </div>
            <div class="insight-metric">
                <strong>Difficulty Level:</strong><br>
                <span style="color: var(--info-color);">${ragResult.difficulty_level || 'Intermediate'}</span>
            </div>
            <div class="insight-metric">
                <strong>Optimal Locations Size:</strong><br>
                <span style="color: var(--success-color);">${ragResult.location_size || '20-30 participants'}</span>
            </div>
        </div>
    `;

    // Display recommended tracks
    const tracksContainer = document.getElementById('recommendedTracks');
    const recommendedTracks = ragResult.recommended_tracks || [
        { name: 'Foundation Track', description: 'Core concepts and fundamentals' },
        { name: 'Practical Application Track', description: 'Hands-on exercises and projects' },
        { name: 'Advanced Topics Track', description: 'Deep dive into specialized areas' }
    ];

    tracksContainer.innerHTML = recommendedTracks.map(track => `
        <div style="background: white; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid var(--info-color);">
            <strong>${track.name}</strong><br>
            <small style="color: var(--text-muted);">${track.description}</small>
        </div>
    `).join('');

    // Display suggested learning objectives
    const objectivesContainer = document.getElementById('suggestedObjectives');
    const objectives = ragResult.learning_objectives || [
        'Understand core principles and concepts',
        'Apply knowledge through practical exercises',
        'Demonstrate proficiency in key skills',
        'Collaborate effectively in team environments',
        'Present and communicate solutions clearly'
    ];

    objectivesContainer.innerHTML = `
        <ul style="margin: 0; padding-left: 1.5rem;">
            ${objectives.map(obj => `<li style="margin-bottom: 0.5rem;">${obj}</li>`).join('')}
        </ul>
    `;
}

/**
 * Generate mock RAG suggestions
 *
 * @param {string} description - The project description
 * @param {string} targetRoles - The target roles
 * @returns {Object} Mock RAG suggestions
 */
function generateMockRAGSuggestions(description, targetRoles) {
    return {
        analysis: `Based on your project description, this appears to be a ${targetRoles ? 'role-specific' : 'general'} training program that would benefit from a structured, multi-track approach.`,
        recommended_duration: '14 weeks',
        difficulty_level: 'Intermediate',
        location_size: '25 participants',
        recommended_tracks: [
            { name: 'Foundation Track', description: 'Essential knowledge and core concepts' },
            { name: 'Hands-On Track', description: 'Practical exercises and real-world applications' },
            { name: 'Capstone Track', description: 'Final project and portfolio development' }
        ],
        learning_objectives: [
            'Master fundamental concepts and principles',
            'Apply knowledge through practical projects',
            'Develop professional skills and competencies',
            'Build a comprehensive portfolio',
            'Demonstrate readiness for advanced roles'
        ]
    };
}

/**
 * Regenerate AI suggestions
 */
export async function regenerateAISuggestions() {
    setRagSuggestionsCache(null);
    await generateRAGSuggestions();
}

/**
 * Load track templates
 */
async function loadTrackTemplates() {
    try {
        const orgId = getCurrentOrganization().id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/track-templates`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            loadedTrackTemplates = await response.json();
        } else {
            loadedTrackTemplates = [];
        }

        displayTrackTemplates(loadedTrackTemplates);
    } catch (error) {
        console.error('Error loading track templates:', error);
        displayTrackTemplates([]);
    }
}

/**
 * Display track templates
 *
 * @param {Array} templates - Array of track templates
 */
function displayTrackTemplates(templates) {
    const container = document.getElementById('trackTemplates');

    container.innerHTML = templates.map(template => `
        <div class="track-template-card" onclick="toggleTrackTemplate('${template.id}')" data-track-id="${template.id}">
            <div class="track-category">${template.template_category || 'General'}</div>
            <h4 style="margin: 0.5rem 0;">${template.name}</h4>
            <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0.5rem 0;">${template.description}</p>
            <div class="track-duration">
                ⏱️ ${template.estimated_duration_hours} hours
                ${template.difficulty_level ? `• 📊 ${template.difficulty_level}` : ''}
            </div>
        </div>
    `).join('');
}

/**
 * Toggle track template selection
 *
 * @param {string} templateId - The template ID
 */
export function toggleTrackTemplate(templateId) {
    const card = document.querySelector(`[data-track-id="${templateId}"]`);
    const selectedTemplates = getSelectedTrackTemplates();

    if (card.classList.contains('selected')) {
        card.classList.remove('selected');
        setSelectedTrackTemplates(selectedTemplates.filter(id => id !== templateId));
    } else {
        card.classList.add('selected');
        setSelectedTrackTemplates([...selectedTemplates, templateId]);
    }

    updateSelectedTracksDisplay();
}

/**
 * Update selected tracks display
 */
function updateSelectedTracksDisplay() {
    const container = document.getElementById('selectedTracks');
    const listContainer = document.getElementById('selectedTracksList');
    const selectedTemplates = getSelectedTrackTemplates();

    if (selectedTemplates.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    // Get template details for selected tracks from loaded API data
    const selected = loadedTrackTemplates.filter(t => selectedTemplates.includes(t.id));

    listContainer.innerHTML = selected.map(template => `
        <div class="selected-track-item">
            <div>
                <strong>${template.name}</strong><br>
                <small style="color: var(--text-muted);">${template.estimated_duration_hours} hours • ${template.difficulty_level}</small>
            </div>
            <button class="btn btn-sm btn-secondary" onclick="toggleTrackTemplate('${template.id}')">Remove</button>
        </div>
    `).join('');
}

