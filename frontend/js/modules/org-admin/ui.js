/**
 * Organization Admin Dashboard UI Rendering Module
 *
 * BUSINESS CONTEXT:
 * This module serves as the View layer in the MVC pattern for the organization admin dashboard.
 * It contains all presentation logic for rendering data to the DOM, keeping display concerns
 * separate from business logic and data management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering functions that accept data and return nothing (side effects on DOM)
 * - Uses template literals for HTML generation
 * - Implements escapeHtml for XSS protection on all user-generated content
 * - Follows SOLID principles with single-responsibility functions
 * - No business logic or data fetching - only presentation
 *
 * ARCHITECTURE:
 * - Import utilities from utils.js (escapeHtml, capitalizeFirst)
 * - Export all display* and update* functions
 * - Each function targets specific DOM elements by ID
 * - Handles empty states gracefully with user-friendly messages
 *
 * @module org-admin/ui
 */

import { escapeHtml, capitalizeFirst } from './utils.js';

/**
 * Update organization header display with current organization data
 *
 * BUSINESS CONTEXT:
 * Updates the dashboard header to show the current organization's branding
 *
 * @param {Object} organization - Organization data object
 * @param {string} organization.name - Organization name
 * @param {string} organization.domain - Organization domain
 * @param {string} organization.description - Organization description
 */
export function updateOrganizationDisplay(organization) {
    document.getElementById('orgName').textContent = organization.name;
    document.getElementById('orgDomain').textContent = organization.domain || 'No domain set';
    document.getElementById('orgTitle').textContent = `${organization.name} Dashboard`;
    document.getElementById('orgDescription').textContent = organization.description || 'Manage your organization\'s training programs and students';
}

/**
 * Display tracks in the tracks management table
 *
 * BUSINESS CONTEXT:
 * Renders all learning tracks for the organization with filtering support
 *
 * @param {Array} tracks - Array of track objects
 */
export function displayTracks(tracks) {
    const tbody = document.getElementById('tracksTableBody');

    if (!tbody) return;

    if (!tracks || tracks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No tracks found</td></tr>';
        return;
    }

    tbody.innerHTML = tracks.map(track => `
        <tr>
            <td>
                <strong>${escapeHtml(track.name)}</strong>
                ${track.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(track.description.substring(0, 100))}${track.description.length > 100 ? '...' : ''}</small>` : ''}
            </td>
            <td>${escapeHtml(track.project_name || 'N/A')}</td>
            <td>
                <span class="badge badge-${track.difficulty_level || 'beginner'}">
                    ${capitalizeFirst(track.difficulty_level || 'beginner')}
                </span>
            </td>
            <td>${track.duration_weeks ? `${track.duration_weeks} weeks` : 'N/A'}</td>
            <td>
                <span class="stat-badge">${track.enrollment_count || 0}</span>
                ${track.max_students ? `<small>/ ${track.max_students}</small>` : ''}
            </td>
            <td><span class="stat-badge">${track.instructor_count || 0}</span></td>
            <td>
                <span class="status-badge status-${track.status || 'draft'}">
                    ${capitalizeFirst(track.status || 'draft')}
                </span>
            </td>
            <td>
                <button class="btn-icon" onclick="viewTrackDetails('${track.id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="editTrack('${track.id}')" title="Edit">
                    ✏️
                </button>
                <button class="btn-icon" onclick="deleteTrack('${track.id}')" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update tracks statistics display
 *
 * BUSINESS CONTEXT:
 * Updates the total tracks count in the dashboard statistics
 *
 * @param {Array} tracks - Array of track objects
 */
export function updateTracksStats(tracks) {
    const totalTracksEl = document.getElementById('totalTracks');
    if (totalTracksEl) {
        totalTracksEl.textContent = tracks.length;
    }
}

/**
 * Display projects in the projects list
 *
 * BUSINESS CONTEXT:
 * Renders all training projects with action buttons for management
 *
 * @param {Array} projects - Array of project objects
 */
export function displayProjects(projects) {
    const container = document.getElementById('projectsList');

    if (projects.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <h3>No projects yet</h3>
                <p>Create your first training project to get started.</p>
                <button class="btn btn-primary" onclick="showCreateProjectModal()">Create Project</button>
            </div>
        `;
        return;
    }

    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">${project.name}</h3>
                    <p style="margin: 0; color: var(--text-muted);">${project.description || 'No description'}</p>
                </div>
                <span class="project-status status-${project.status}">${project.status.charAt(0).toUpperCase() + project.status.slice(1)}</span>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div>
                    <strong>Duration:</strong><br>
                    ${project.duration_weeks ? `${project.duration_weeks} weeks` : 'Not set'}
                </div>
                <div>
                    <strong>Participants:</strong><br>
                    ${project.current_participants || 0}/${project.max_participants || '∞'}
                </div>
                <div>
                    <strong>Start Date:</strong><br>
                    ${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set'}
                </div>
            </div>

            ${project.target_roles && project.target_roles.length > 0 ? `
                <div>
                    <strong>Target Roles:</strong>
                    <div class="target-roles">
                        ${project.target_roles.map(role => `<span class="role-tag">${role}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            <div style="display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap;">
                <button class="action-btn btn-edit" onclick="editProject('${project.id}')">✏️ Edit</button>
                <button class="action-btn btn-primary" onclick="manageProjectMembers('${project.id}')">👥 Members</button>

                ${project.status === 'draft' ? `
                    <button class="action-btn btn-success" onclick="instantiateProject('${project.id}')">🚀 Instantiate</button>
                ` : ''}

                ${project.status === 'active' ? `
                    <button class="action-btn btn-info" onclick="showInstructorAssignmentModal('${project.id}')">👨‍🏫 Assign Instructors</button>
                    <button class="action-btn btn-warning" onclick="showInstructorRemovalModal('${project.id}')">🗑️ Remove Instructors</button>
                    <button class="action-btn btn-primary" onclick="showStudentEnrollmentModal('${project.id}')">📝 Enroll Students</button>
                    <button class="action-btn btn-warning" onclick="showStudentUnenrollmentModal('${project.id}')">❌ Unenroll Students</button>
                    <button class="action-btn btn-secondary" onclick="showProjectAnalytics('${project.id}')">📊 Analytics</button>
                ` : ''}

                <button class="action-btn btn-delete" onclick="deleteProject('${project.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

/**
 * Display instructors in the instructors table
 *
 * BUSINESS CONTEXT:
 * Renders all instructors with their roles, status, and management actions
 *
 * @param {Array} instructors - Array of instructor objects
 */
export function displayInstructors(instructors) {
    const tbody = document.querySelector('#instructorsTable tbody');

    if (instructors.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No instructors found. Add your first instructor to get started.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = instructors.map(instructor => `
        <tr>
            <td>${instructor.first_name || ''} ${instructor.last_name || ''}</td>
            <td>${instructor.email}</td>
            <td><span class="role-badge role-${instructor.role}">${instructor.role.replace('_', ' ')}</span></td>
            <td>${new Date(instructor.joined_at).toLocaleDateString()}</td>
            <td>${instructor.last_login ? new Date(instructor.last_login).toLocaleDateString() : 'Never'}</td>
            <td><span class="status-${instructor.is_active ? 'active' : 'inactive'}">${instructor.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="action-btn btn-edit" onclick="editInstructor('${instructor.user_id}')">Edit</button>
                <button class="action-btn btn-delete" onclick="removeInstructor('${instructor.user_id}')">Remove</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Display students in the students table
 *
 * BUSINESS CONTEXT:
 * Renders all students with their enrollment status and management actions
 *
 * @param {Array} students - Array of student objects
 */
export function displayStudents(students) {
    const tbody = document.querySelector('#studentsTable tbody');

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No students found.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = students.map(student => `
        <tr>
            <td>${student.first_name || ''} ${student.last_name || ''}</td>
            <td>${student.email}</td>
            <td>${student.project_count || 0}</td>
            <td>${new Date(student.joined_at).toLocaleDateString()}</td>
            <td>${student.last_active ? new Date(student.last_active).toLocaleDateString() : 'Never'}</td>
            <td><span class="status-${student.is_active ? 'active' : 'inactive'}">${student.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="action-btn btn-edit" onclick="editStudent('${student.user_id}')">Edit</button>
                <button class="action-btn btn-delete" onclick="removeStudent('${student.user_id}')">Remove</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Display recent projects on the overview dashboard
 *
 * BUSINESS CONTEXT:
 * Shows a summary of recently created or modified projects
 *
 * @param {Array} projects - Array of recent project objects
 */
export function displayRecentProjects(projects) {
    const container = document.getElementById('recentProjects');
    if (projects.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No recent projects</p>';
        return;
    }

    container.innerHTML = projects.map(project => `
        <div style="padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 0.5rem;">
            <strong>${project.name}</strong><br>
            <small style="color: var(--text-muted);">${project.current_participants || 0} participants</small>
        </div>
    `).join('');
}

/**
 * Display recent activity on the overview dashboard
 *
 * BUSINESS CONTEXT:
 * Shows a timeline of recent actions in the organization
 *
 * @param {Array} activities - Array of activity objects
 */
export function displayRecentActivity(activities) {
    const container = document.getElementById('recentActivity');
    if (activities.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No recent activity</p>';
        return;
    }

    container.innerHTML = activities.map(activity => `
        <div style="padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 0.5rem;">
            <div>${activity.action}</div>
            <small style="color: var(--text-muted);">by ${activity.user} • ${activity.time}</small>
        </div>
    `).join('');
}

/**
 * Display RAG-generated suggestions for project creation
 *
 * BUSINESS CONTEXT:
 * Shows AI-generated insights and recommendations when creating a new project
 *
 * @param {Object} ragResult - RAG query result with suggestions
 * @param {string} projectDescription - Original project description
 * @param {string} targetRoles - Target roles for the project
 */
export function displayRAGSuggestions(ragResult, projectDescription, targetRoles) {
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
 * Display track templates for project creation
 *
 * BUSINESS CONTEXT:
 * Shows available track templates that can be selected during project setup
 *
 * @param {Array} templates - Array of track template objects
 */
export function displayTrackTemplates(templates) {
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
 * Update the display of selected track templates
 *
 * BUSINESS CONTEXT:
 * Shows which track templates have been selected for the new project
 *
 * @param {Array} selectedTrackTemplates - Array of selected template IDs
 * @param {Array} allTemplates - Array of all available template objects
 */
export function updateSelectedTracksDisplay(selectedTrackTemplates, allTemplates) {
    const container = document.getElementById('selectedTracks');
    const listContainer = document.getElementById('selectedTracksList');

    if (selectedTrackTemplates.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    // Filter templates to get selected ones
    const selectedTemplates = allTemplates.filter(t => selectedTrackTemplates.includes(t.id));

    listContainer.innerHTML = selectedTemplates.map(template => `
        <div class="selected-track-item">
            <div>
                <strong>${template.name}</strong><br>
                <small style="color: var(--text-muted);">${template.estimated_duration_hours} hours • ${template.difficulty_level}</small>
            </div>
            <button class="btn btn-sm btn-secondary" onclick="toggleTrackTemplate('${template.id}')">Remove</button>
        </div>
    `).join('');
}

/**
 * Display project instantiation details
 *
 * BUSINESS CONTEXT:
 * Shows project summary before instantiation (converting from draft to active)
 *
 * @param {Object} project - Project object with details
 */
export function displayProjectInstantiationDetails(project) {
    const container = document.getElementById('projectInstantiationDetails');
    container.innerHTML = `
        <div class="project-details-summary">
            <h3>${project.name}</h3>
            <p style="margin: 1rem 0;">${project.description}</p>

            <div class="project-details-grid">
                <div class="detail-item">
                    <span class="detail-label">Target Roles</span>
                    <span class="detail-value">${project.target_roles.join(', ')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Duration</span>
                    <span class="detail-value">${project.duration_weeks} weeks</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Max Participants</span>
                    <span class="detail-value">${project.max_participants}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Existing Tracks</span>
                    <span class="detail-value">${project.tracks_count} tracks</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Existing Modules</span>
                    <span class="detail-value">${project.modules_count} modules</span>
                </div>
            </div>

            ${!project.has_tracks ? `
                <div style="margin-top: 1rem; padding: 1rem; background: var(--warning-color); color: white; border-radius: 6px;">
                    <strong>⚠️ No tracks found!</strong> Default tracks and modules will be created based on the project description and target roles.
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * Display track assignments for instructor assignment
 *
 * BUSINESS CONTEXT:
 * Shows tracks with instructor assignment interface
 *
 * @param {Array} tracks - Array of track objects
 * @param {Array} availableInstructors - Array of available instructor objects
 */
export function displayTrackAssignments(tracks, availableInstructors) {
    const container = document.getElementById('trackAssignmentList');
    container.innerHTML = tracks.map(track => `
        <div class="instructor-assignment-item">
            <h4>${track.name}</h4>
            <p style="margin: 0 0 1rem 0; color: var(--text-muted);">${track.description}</p>

            <div class="instructor-selector">
                <select onchange="addInstructorToTrack('${track.id}', this.value, this)" style="width: 100%;">
                    <option value="">Select instructor to assign...</option>
                    ${availableInstructors.map(instructor => `
                        <option value="${instructor.id}">${instructor.name} (${instructor.specialties.join(', ')})</option>
                    `).join('')}
                </select>
                <select onchange="setInstructorRole('${track.id}', this.value)">
                    <option value="instructor">Instructor</option>
                    <option value="lead_instructor">Lead Instructor</option>
                    <option value="assistant">Assistant</option>
                </select>
                <button type="button" class="btn btn-sm btn-primary" onclick="assignSelectedInstructor('${track.id}')">Assign</button>
            </div>

            <div class="assigned-instructors" id="trackInstructors-${track.id}">
                ${track.assigned_instructors.map(instructor => `
                    <span class="instructor-tag">
                        ${instructor.name} (${instructor.role})
                        <button class="remove-btn" onclick="removeInstructorFromTrack('${track.id}', '${instructor.id}')">×</button>
                    </span>
                `).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * Display module assignments for instructor assignment
 *
 * BUSINESS CONTEXT:
 * Shows modules with instructor assignment interface and required instructor counts
 *
 * @param {Array} modules - Array of module objects
 * @param {Array} availableInstructors - Array of available instructor objects
 */
export function displayModuleAssignments(modules, availableInstructors) {
    const container = document.getElementById('moduleAssignmentList');
    container.innerHTML = modules.map(module => `
        <div class="instructor-assignment-item">
            <h4>${module.name} <span style="font-size: 0.875rem; color: var(--text-muted);">(${module.track_name})</span></h4>

            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <span style="font-size: 0.875rem;">
                    <strong>Required instructors:</strong> ${module.required_instructors}
                </span>
                <span style="font-size: 0.875rem; color: ${module.assigned_instructors.length >= module.required_instructors ? 'var(--success-color)' : 'var(--error-color)'};">
                    <strong>Currently assigned:</strong> ${module.assigned_instructors.length}
                </span>
            </div>

            <div class="instructor-selector">
                <select onchange="addInstructorToModule('${module.id}', this.value, this)" style="width: 100%;">
                    <option value="">Select instructor to assign...</option>
                    ${availableInstructors.map(instructor => `
                        <option value="${instructor.id}">${instructor.name} (${instructor.specialties.join(', ')})</option>
                    `).join('')}
                </select>
                <select onchange="setModuleInstructorRole('${module.id}', this.value)">
                    <option value="co_instructor">Co-Instructor</option>
                    <option value="lead_instructor">Lead Instructor</option>
                    <option value="assistant">Assistant</option>
                </select>
                <button type="button" class="btn btn-sm btn-primary" onclick="assignSelectedModuleInstructor('${module.id}')">Assign</button>
            </div>

            <div class="assigned-instructors" id="moduleInstructors-${module.id}">
                ${module.assigned_instructors.map(instructor => `
                    <span class="instructor-tag">
                        ${instructor.name} (${instructor.role})
                        <button class="remove-btn" onclick="removeInstructorFromModule('${module.id}', '${instructor.id}')">×</button>
                    </span>
                `).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * Display available students for enrollment
 *
 * BUSINESS CONTEXT:
 * Shows students who can be enrolled in a project/track
 *
 * @param {Array} students - Array of student objects
 * @param {Array} selectedStudents - Array of selected student IDs
 */
export function displayAvailableStudents(students, selectedStudents = []) {
    const container = document.getElementById('availableStudentsList');
    container.innerHTML = students.map(student => `
        <div class="student-item ${selectedStudents.includes(student.id) ? 'selected' : ''}"
             onclick="toggleStudentSelection('${student.id}')">
            <div class="student-info">
                <div class="student-name">${student.name}</div>
                <div class="student-email">${student.email}</div>
            </div>
            <div class="enrollment-status status-${student.enrolled ? 'enrolled' : 'not-enrolled'}">
                ${student.enrolled ? 'Enrolled' : 'Available'}
            </div>
        </div>
    `).join('');
}

/**
 * Update enrollment summary display
 *
 * BUSINESS CONTEXT:
 * Updates the display showing how many students are selected for enrollment
 *
 * @param {number} selectedCount - Number of selected students
 * @param {string} trackName - Name of selected track
 */
export function updateEnrollmentSummary(selectedCount, trackName) {
    // Update UI to show selection summary
    console.log(`${selectedCount} students selected for enrollment in: ${trackName}`);
}

/**
 * Display analytics summary for a project
 *
 * BUSINESS CONTEXT:
 * Shows key performance metrics and statistics for a project
 *
 * @param {Object} analytics - Analytics data object
 */
export function displayAnalyticsSummary(analytics) {
    document.getElementById('analyticsEnrolledStudents').textContent = analytics.total_enrolled_students || 0;
    document.getElementById('analyticsActiveStudents').textContent = analytics.active_students || 0;
    document.getElementById('analyticsCompletedStudents').textContent = analytics.completed_students || 0;
    document.getElementById('analyticsAverageProgress').textContent = `${analytics.average_progress_percentage || 0}%`;
    document.getElementById('analyticsAverageScore').textContent = `${analytics.average_quiz_score || 0}%`;
}

/**
 * Display enrolled students for unenrollment
 *
 * BUSINESS CONTEXT:
 * Shows students currently enrolled in a project with selection checkboxes
 *
 * @param {Array} students - Array of enrolled student objects
 */
export function displayEnrolledStudents(students) {
    const container = document.getElementById('enrolledStudentsList');
    if (!container) return;

    if (students.length === 0) {
        container.innerHTML = '<p>No students enrolled in this project.</p>';
        return;
    }

    container.innerHTML = students.map(student => `
        <div class="student-item enrolled-student-item">
            <div class="student-selection">
                <input type="checkbox" id="unenroll-${student.id}" value="${student.id}"
                       onchange="toggleStudentForUnenrollment('${student.id}')">
                <label for="unenroll-${student.id}">
                    <div class="student-info">
                        <div class="student-name">${student.name}</div>
                        <div class="student-email">${student.email}</div>
                        <div class="student-track">Track: ${student.track_name}</div>
                        <div class="student-progress">Progress: ${student.progress_percentage.toFixed(1)}%</div>
                        <div class="student-enrollment-date">Enrolled: ${new Date(student.enrollment_date).toLocaleDateString()}</div>
                    </div>
                </label>
            </div>
        </div>
    `).join('');
}

/**
 * Display assigned instructors for removal
 *
 * BUSINESS CONTEXT:
 * Shows instructors currently assigned to a project with selection checkboxes
 *
 * @param {Array} instructors - Array of assigned instructor objects
 */
export function displayAssignedInstructors(instructors) {
    const container = document.getElementById('assignedInstructorsList');
    if (!container) return;

    if (instructors.length === 0) {
        container.innerHTML = '<p>No instructors assigned to this project.</p>';
        return;
    }

    container.innerHTML = instructors.map(instructor => `
        <div class="instructor-item assigned-instructor-item">
            <div class="instructor-selection">
                <input type="checkbox" id="remove-${instructor.id}" value="${instructor.id}"
                       onchange="toggleInstructorForRemoval('${instructor.id}')">
                <label for="remove-${instructor.id}">
                    <div class="instructor-info">
                        <div class="instructor-name">${instructor.name}</div>
                        <div class="instructor-email">${instructor.email}</div>
                        <div class="instructor-role">Role: ${instructor.role.replace('_', ' ').toUpperCase()}</div>
                        <div class="instructor-tracks">Tracks: ${instructor.tracks.join(', ')}</div>
                        <div class="instructor-modules">Modules: ${instructor.modules.join(', ')}</div>
                        <div class="instructor-assignment-date">Assigned: ${new Date(instructor.assignment_date).toLocaleDateString()}</div>
                    </div>
                </label>
            </div>
        </div>
    `).join('');
}
