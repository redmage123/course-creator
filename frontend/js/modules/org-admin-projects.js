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
    fetchMembers,
    addInstructor,
    addStudent,
    removeMember
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
    showNotification
} from './org-admin-utils.js';

// Current organization context
let currentOrganizationId = null;
let currentProjectId = null;

/**
 * Initialize projects management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeProjectsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Projects management initialized for organization:', organizationId);
}

/**
 * Load and display projects data
 *
 * BUSINESS LOGIC:
 * Fetches all projects for the organization and displays them in a table
 * Supports filtering by status and search term
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

        // Update UI
        renderProjectsTable(projects);
        updateProjectsStats(projects);

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
                <span class="status-badge status-${project.status || 'draft'}">
                    ${capitalizeFirst(project.status || 'draft')}
                </span>
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
export function showCreateProjectModal() {
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

    // Reset wizard to step 1
    form.reset();
    showProjectStep(1);

    // Open modal
    openModal('createProjectModal');
}

/**
 * Navigate to next project wizard step
 *
 * BUSINESS LOGIC:
 * Validates current step before advancing
 * Step 1 → 2: Validates basic info and triggers AI suggestions
 * Step 2 → 3: Validates configuration
 */
export function nextProjectStep() {
    const currentStepElem = document.querySelector('.project-step.active');
    const currentStep = currentStepElem ? parseInt(currentStepElem.id.replace('projectStep', '')) : 1;

    console.log('📄 Current step:', currentStep);

    // Validate current step
    if (currentStep === 1) {
        const name = document.getElementById('projectName')?.value;
        const slug = document.getElementById('projectSlug')?.value;
        const description = document.getElementById('projectDescription')?.value;

        if (!name || !slug || !description) {
            showNotification('Please fill in all required fields (Name, Slug, and Description)', 'error');
            return;
        }

        // Moving to step 2 - generate AI suggestions
        showProjectStep(2);
        generateAISuggestions();
    } else if (currentStep === 2) {
        // Moving to step 3
        showProjectStep(3);
    }
}

/**
 * Navigate to previous project wizard step
 */
export function previousProjectStep() {
    const currentStep = parseInt(document.querySelector('.wizard-step.active')?.dataset.step || '1');
    const prevStep = currentStep - 1;

    if (prevStep >= 1) {
        showProjectStep(prevStep);
    }
}

/**
 * Show specific project wizard step
 *
 * @param {number} stepNumber - Step number (1, 2, or 3)
 */
function showProjectStep(stepNumber) {
    console.log(`📄 Showing project step ${stepNumber}`);

    // Hide all steps
    document.querySelectorAll('.project-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    const targetStep = document.getElementById(`projectStep${stepNumber}`);
    if (targetStep) {
        targetStep.classList.add('active');
        console.log(`✅ Step ${stepNumber} activated`);
    } else {
        console.error(`❌ projectStep${stepNumber} not found`);
    }

    // Update step indicators
    document.querySelectorAll('.step').forEach((indicator, index) => {
        indicator.classList.remove('active', 'completed');
        if (index + 1 === stepNumber) {
            indicator.classList.add('active');
        } else if (index + 1 < stepNumber) {
            indicator.classList.add('completed');
        }
    });
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
        showNotification('Project created successfully', 'success');
        closeModal('projectWizardModal');
        loadProjectsData();

    } catch (error) {
        console.error('Error creating project:', error);
    }
}

/**
 * View project details
 *
 * @param {string} projectId - UUID of project
 */
export function viewProject(projectId) {
    // Implementation will show project details modal
    console.log('View project:', projectId);
    showNotification('Project details feature coming soon', 'info');
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
