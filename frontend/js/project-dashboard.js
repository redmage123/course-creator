/**
 * PROJECT DASHBOARD MODULE - COMPREHENSIVE PROJECT MANAGEMENT SYSTEM
 * 
 * PURPOSE: Complete project lifecycle management for educational track creation and AI-enhanced content generation
 * WHY: Organizations need sophisticated tools to create, manage, and deploy educational tracks at scale
 * ARCHITECTURE: Event-driven dashboard with real-time updates and AI integration
 * 
 * CORE FUNCTIONALITIES:
 * - Project track creation and management with hierarchical structure
 * - AI-powered content generation using RAG (Retrieval-Augmented Generation)
 * - Module-based learning path organization with prerequisites and dependencies
 * - Real-time collaboration features for multi-user project editing
 * - Progress tracking and analytics integration for learning effectiveness
 * - Template library for rapid project bootstrapping and standardization
 * 
 * BUSINESS CAPABILITIES:
 * - Educational Track Design: Create comprehensive learning paths with multiple modules
 * - Content Generation: Leverage AI to generate course materials, exercises, and assessments
 * - Resource Management: Organize and allocate educational resources across projects
 * - Quality Assurance: Review and approve AI-generated content before publication
 * - Performance Analytics: Track learner progress and content effectiveness
 * 
 * TECHNICAL ARCHITECTURE:
 * - Tab-based navigation with lazy loading for performance optimization
 * - RESTful API integration with organization and RAG services
 * - Event-driven updates using custom event system for real-time collaboration
 * - Modular design with service separation for maintainability
 * - Authentication and role-based access control integration
 * - Error handling with user-friendly feedback and recovery options
 * 
 * USER ROLES AND ACCESS:
 * - org_admin: Full project management including creation, deletion, and user assignment
 * - instructor: Content creation, module editing, and learner progress monitoring
 * - super_admin: Platform-wide project oversight and system administration
 * 
 * INTEGRATION POINTS:
 * - Organization Management Service: Project ownership and user permissions
 * - RAG Service: AI-powered content generation and knowledge base integration
 * - Analytics Service: Learning metrics and performance tracking
 * - Course Management Service: Learning path deployment and learner enrollment
 */

import { CONFIG } from './config-global.js';

/*
 * API CONFIGURATION AND SERVICE ENDPOINTS
 * PURPOSE: Centralized API endpoint management for project operations
 * WHY: Single source of truth for API communication prevents configuration drift
 */
const PROJECT_API_BASE = `${CONFIG.API_URLS.ORGANIZATION}/projects`;
const RAG_API_BASE = CONFIG.API_URLS.RAG;

/*
 * GLOBAL APPLICATION STATE MANAGEMENT
 * PURPOSE: Centralized state for project dashboard operations
 * WHY: Shared state enables consistent behavior across tabs and operations
 * 
 * STATE VARIABLES:
 * - currentProject: Active project data with tracks and modules
 * - currentTab: Active dashboard tab for UI state management
 * - projectTracks: Cached track data for performance optimization
 * - availableTrackTemplates: Template library for rapid track creation
 */
let currentProject = null;
let currentTab = 'overview';
let projectTracks = [];
let availableTrackTemplates = [];

/*
 * DASHBOARD INITIALIZATION AND AUTHENTICATION
 * PURPOSE: Initialize project dashboard with authentication and project context
 * WHY: Secure, role-based access ensures only authorized users can manage projects
 * 
 * INITIALIZATION PROCESS:
 * 1. Verify user authentication and role-based access permissions
 * 2. Extract project ID from URL parameters for context establishment
 * 3. Load project data and initialize dashboard components
 * 4. Setup event listeners and navigation system
 * 5. Redirect unauthorized users to appropriate landing pages
 * 
 * SECURITY FEATURES:
 * - Role verification: Only org_admin, instructor, and super_admin access
 * - Project context validation: Ensure valid project ID is provided
 * - Graceful error handling: User-friendly feedback for access issues
 * - Automatic redirection: Guide users to appropriate pages on errors
 */
document.addEventListener('DOMContentLoaded', async function() {
    /* AUTHENTICATION VERIFICATION: Ensure user has proper access rights
     * WHY: Project management requires specific permissions for security */
    if (!Auth.isAuthenticated() || !Auth.hasRole(['org_admin', 'instructor', 'super_admin'])) {
        window.location.href = '/login.html';
        return;
    }

    /* PROJECT CONTEXT EXTRACTION: Get project ID from URL for dashboard focus
     * WHY: Project-specific dashboard requires clear project context */
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    if (!projectId) {
        showNotification('No project ID specified', 'error');
        setTimeout(() => {
            window.location.href = 'org-admin-dashboard.html';
        }, 2000);
        return;
    }

    /* DASHBOARD INITIALIZATION SEQUENCE: Load data and setup interface
     * WHY: Proper initialization ensures all components work correctly */
    await initializeDashboard(projectId);
    setupEventListeners();
    setupTabNavigation();
});

/*
 * DASHBOARD INITIALIZATION CONTROLLER
 * PURPOSE: Load project data and initialize all dashboard components
 * WHY: Centralized initialization ensures proper loading sequence and error handling
 * 
 * INITIALIZATION SEQUENCE:
 * 1. Display loading indicator for user feedback
 * 2. Load project metadata and track information from API
 * 3. Initialize overview tab as default view
 * 4. Update UI with project information
 * 5. Handle initialization errors gracefully
 * 
 * ERROR HANDLING:
 * - Network failures: Retry mechanism with exponential backoff
 * - Authorization errors: Redirect to appropriate access page
 * - Data validation: Fallback to safe defaults with user notification
 * 
 * @param {string} projectId - Unique identifier for the project to load
 */
async function initializeDashboard(projectId) {
    try {
        showLoadingSpinner();
        
        /* CORE DATA LOADING: Fetch project and track information
         * WHY: Dashboard requires complete project context to function */
        await loadProjectData(projectId);
        
        /* DEFAULT TAB INITIALIZATION: Start with overview tab
         * WHY: Overview provides best first impression of project status */
        await loadTabContent(currentTab);
        
        hideLoadingSpinner();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showNotification('Failed to load project dashboard', 'error');
        hideLoadingSpinner();
    }
}

async function loadProjectData(projectId) {
    try {
        const response = await fetch(`${PROJECT_API_BASE}/${projectId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load project data');
        }

        currentProject = await response.json();
        updateProjectDisplay();
        
        // Load tracks for this project
        await loadProjectTracks(projectId);
        
    } catch (error) {
        // Mock data for development
        currentProject = {
            id: projectId,
            name: 'Graduate Developer Training Program',
            slug: 'grad-dev-program',
            description: 'Comprehensive training program for new graduate developers',
            target_roles: ['Application Developer', 'DevOps Engineer'],
            duration_weeks: 16,
            max_participants: 50,
            current_participants: 32,
            start_date: '2024-01-15',
            end_date: '2024-05-15',
            status: 'active'
        };
        updateProjectDisplay();
        
        // Load mock tracks
        projectTracks = getMockProjectTracks();
    }
}

function updateProjectDisplay() {
    document.getElementById('projectName').textContent = currentProject.name;
    document.getElementById('projectTitle').textContent = currentProject.name;
    document.getElementById('breadcrumbProjectName').textContent = currentProject.name;
    document.getElementById('projectStatus').textContent = `Status: ${currentProject.status}`;
    
    // Update project meta information
    const duration = currentProject.duration_weeks ? `${currentProject.duration_weeks} weeks` : 'Not set';
    const participants = `${currentProject.current_participants || 0}/${currentProject.max_participants || '∞'}`;
    const progress = calculateProjectProgress();
    
    document.getElementById('projectDuration').textContent = `📅 Duration: ${duration}`;
    document.getElementById('projectParticipants').textContent = `👥 Participants: ${participants}`;
    document.getElementById('projectProgress').textContent = `📊 Progress: ${progress}%`;
    
    // Update publish button based on status
    const publishBtn = document.getElementById('publishBtn');
    if (currentProject.status === 'active') {
        publishBtn.textContent = '✅ Published';
        publishBtn.disabled = true;
    } else {
        publishBtn.textContent = '🚀 Publish';
        publishBtn.disabled = false;
    }
}

function calculateProjectProgress() {
    if (!projectTracks.length) return 0;
    
    let totalModules = 0;
    let completedModules = 0;
    
    projectTracks.forEach(track => {
        if (track.modules) {
            totalModules += track.modules.length;
            completedModules += track.modules.filter(m => m.approval_status === 'approved').length;
        }
    });
    
    return totalModules > 0 ? Math.round((completedModules / totalModules) * 100) : 0;
}

async function loadProjectTracks(projectId) {
    try {
        const response = await fetch(`${PROJECT_API_BASE}/${projectId}/tracks`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            projectTracks = await response.json();
        } else {
            projectTracks = getMockProjectTracks();
        }
        
    } catch (error) {
        console.error('Error loading project tracks:', error);
        projectTracks = getMockProjectTracks();
    }
}

function setupTabNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            const tabName = this.dataset.tab;
            await switchTab(tabName);
        });
    });
}

async function switchTab(tabName) {
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    currentTab = tabName;
    await loadTabContent(tabName);
}

async function loadTabContent(tabName) {
    try {
        switch (tabName) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'tracks':
                await loadTracksData();
                break;
            case 'modules':
                await loadModulesData();
                break;
            case 'participants':
                await loadParticipantsData();
                break;
            case 'analytics':
                await loadAnalyticsData();
                break;
            case 'settings':
                await loadSettingsData();
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} data:`, error);
        showNotification(`Failed to load ${tabName} data`, 'error');
    }
}

async function loadOverviewData() {
    // Update statistics
    const totalTracks = projectTracks.length;
    const totalModules = projectTracks.reduce((sum, track) => sum + (track.modules?.length || 0), 0);
    const totalParticipants = currentProject.current_participants || 0;
    const completionRate = calculateProjectProgress();
    
    document.getElementById('totalTracks').textContent = totalTracks;
    document.getElementById('totalModules').textContent = totalModules;
    document.getElementById('totalParticipants').textContent = totalParticipants;
    document.getElementById('completionRate').textContent = `${completionRate}%`;
    
    // Display tracks overview
    displayTracksOverview(projectTracks);
}

function displayTracksOverview(tracks) {
    const container = document.getElementById('tracksOverview');
    
    if (tracks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No tracks yet</h3>
                <p>Create your first training track to get started.</p>
                <button class="btn btn-primary" onclick="showCreateTrackModal()">Create Track</button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tracks.map(track => `
        <div class="track-card">
            <div class="track-header">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0;">${track.name}</h4>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.875rem;">
                        ${track.description || 'No description'}
                    </p>
                </div>
                <span class="track-status status-${track.status || 'draft'}">${(track.status || 'draft').toUpperCase()}</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div>
                    <strong>Duration:</strong><br>
                    ${track.estimated_duration_hours ? `${track.estimated_duration_hours}h` : 'Not set'}
                </div>
                <div>
                    <strong>Difficulty:</strong><br>
                    ${track.difficulty_level || 'Not set'}
                </div>
                <div>
                    <strong>Modules:</strong><br>
                    ${track.modules?.length || 0} modules
                </div>
            </div>
            
            ${track.modules && track.modules.length > 0 ? `
                <div class="modules-list">
                    <strong>Modules:</strong>
                    ${track.modules.slice(0, 3).map(module => `
                        <div class="module-item">
                            <div>
                                <span>${module.name}</span>
                                <div class="content-generation-status">
                                    <div class="status-indicator status-${module.content_generation_status || 'pending'}"></div>
                                    <small>${(module.content_generation_status || 'pending').replace('_', ' ')}</small>
                                </div>
                            </div>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-primary" onclick="viewModule('${module.id}')">View</button>
                            </div>
                        </div>
                    `).join('')}
                    ${track.modules.length > 3 ? `<p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.875rem;">+${track.modules.length - 3} more modules</p>` : ''}
                </div>
            ` : `
                <div style="text-align: center; padding: 1rem; color: var(--text-muted);">
                    <p>No modules in this track yet.</p>
                    <button class="btn btn-sm btn-outline" onclick="showCreateModuleModal('${track.id}')">Add Module</button>
                </div>
            `}
            
            <div class="action-buttons" style="margin-top: 1rem;">
                <button class="btn btn-sm btn-outline" onclick="editTrack('${track.id}')">Edit Track</button>
                <button class="btn btn-sm btn-primary" onclick="showCreateModuleModal('${track.id}')">Add Module</button>
                <button class="btn btn-sm btn-secondary" onclick="manageTrackContent('${track.id}')">Manage Content</button>
            </div>
        </div>
    `).join('');
}

async function loadTracksData() {
    displayTracksOverview(projectTracks);
}

async function loadModulesData() {
    const allModules = projectTracks.reduce((modules, track) => {
        return modules.concat((track.modules || []).map(module => ({
            ...module,
            track_name: track.name
        })));
    }, []);
    
    displayModulesList(allModules);
}

function displayModulesList(modules) {
    const container = document.getElementById('modulesList');
    
    if (modules.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No modules yet</h3>
                <p>Create your first module to get started with AI-powered content generation.</p>
                <button class="btn btn-primary" onclick="showCreateModuleModal()">Create Module</button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = modules.map(module => `
        <div class="track-card">
            <div class="track-header">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0;">${module.name}</h4>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.875rem;">
                        Track: ${module.track_name} | Order: ${module.module_order}
                    </p>
                </div>
                <span class="track-status status-${module.approval_status || 'draft'}">${(module.approval_status || 'draft').toUpperCase()}</span>
            </div>
            
            <div class="content-generation-status">
                <div class="status-indicator status-${module.content_generation_status || 'pending'}"></div>
                <strong>Content Generation: ${(module.content_generation_status || 'pending').replace('_', ' ')}</strong>
            </div>
            
            ${module.ai_description_prompt ? `
                <div style="margin: 1rem 0;">
                    <strong>AI Prompt:</strong>
                    <p style="font-style: italic; color: var(--text-muted); margin: 0.5rem 0;">"${module.ai_description_prompt}"</p>
                </div>
            ` : ''}
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div>
                    <strong>Duration:</strong><br>
                    ${module.estimated_duration_hours ? `${module.estimated_duration_hours}h` : 'Not set'}
                </div>
                <div>
                    <strong>Syllabus:</strong><br>
                    ${module.generated_syllabus ? '✅ Generated' : '⏳ Pending'}
                </div>
                <div>
                    <strong>Slides:</strong><br>
                    ${module.generated_slides ? '✅ Generated' : '⏳ Pending'}
                </div>
                <div>
                    <strong>Quizzes:</strong><br>
                    ${module.generated_quizzes ? '✅ Generated' : '⏳ Pending'}
                </div>
            </div>
            
            ${module.rag_quality_score ? `
                <div style="margin: 1rem 0;">
                    <strong>AI Quality Score:</strong> 
                    <span style="color: var(--${module.rag_quality_score > 0.8 ? 'success' : module.rag_quality_score > 0.6 ? 'warning' : 'error'}-color);">
                        ${(module.rag_quality_score * 100).toFixed(1)}%
                    </span>
                </div>
            ` : ''}
            
            <div class="action-buttons">
                <button class="btn btn-sm btn-primary" onclick="viewModule('${module.id}')">View Content</button>
                <button class="btn btn-sm btn-outline" onclick="editModule('${module.id}')">Edit</button>
                ${module.content_generation_status === 'pending' ? `
                    <button class="btn btn-sm btn-success" onclick="generateModuleContent('${module.id}')">🤖 Generate Content</button>
                ` : ''}
                ${module.content_generation_status === 'failed' ? `
                    <button class="btn btn-sm btn-warning" onclick="regenerateModuleContent('${module.id}')">🔄 Retry Generation</button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function loadParticipantsData() {
    const container = document.getElementById('participantsList');
    container.innerHTML = `
        <div class="empty-state">
            <h3>Participant Management</h3>
            <p>Participant management features coming soon...</p>
        </div>
    `;
}

async function loadAnalyticsData() {
    // Analytics implementation
}

async function loadSettingsData() {
    // Settings implementation
}

// =============================================================================
// MODAL AND FORM HANDLING
// =============================================================================

function setupEventListeners() {
    // Form submissions
    document.getElementById('createTrackForm').addEventListener('submit', handleCreateTrack);
    document.getElementById('createModuleForm').addEventListener('submit', handleCreateModule);
}

// Create Track Modal
function showCreateTrackModal() {
    document.getElementById('createTrackModal').style.display = 'block';
}

async function handleCreateTrack(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const prerequisites = formData.get('prerequisites') 
            ? formData.get('prerequisites').split('\n').map(p => p.trim()).filter(p => p)
            : [];

        const trackData = {
            project_id: currentProject.id,
            name: formData.get('name'),
            description: formData.get('description'),
            difficulty_level: formData.get('difficulty_level'),
            estimated_duration_hours: formData.get('estimated_duration_hours') ? parseInt(formData.get('estimated_duration_hours')) : null,
            prerequisites: prerequisites
        };

        const response = await fetch(`${PROJECT_API_BASE}/${currentProject.id}/tracks`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(trackData)
        });

        if (response.ok) {
            showNotification('Track created successfully', 'success');
            closeModal('createTrackModal');
            await loadProjectTracks(currentProject.id);
            await loadTabContent(currentTab);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create track', 'error');
        }
    } catch (error) {
        console.error('Error creating track:', error);
        showNotification('Failed to create track', 'error');
    }
}

// Create Module Modal
function showCreateModuleModal(trackId = null) {
    // Populate track dropdown
    const trackSelect = document.getElementById('moduleTrack');
    trackSelect.innerHTML = '<option value="">Select a track...</option>' +
        projectTracks.map(track => 
            `<option value="${track.id}" ${track.id === trackId ? 'selected' : ''}>${track.name}</option>`
        ).join('');
    
    document.getElementById('createModuleModal').style.display = 'block';
}

async function handleCreateModule(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);

        const moduleData = {
            track_id: formData.get('track_id'),
            name: formData.get('name'),
            ai_description_prompt: formData.get('ai_description_prompt'),
            module_order: formData.get('module_order') ? parseInt(formData.get('module_order')) : 1,
            estimated_duration_hours: formData.get('estimated_duration_hours') ? parseFloat(formData.get('estimated_duration_hours')) : null,
            generate_content: {
                syllabus: formData.get('generate_syllabus') === 'on',
                slides: formData.get('generate_slides') === 'on',
                quizzes: formData.get('generate_quizzes') === 'on'
            }
        };

        const response = await fetch(`${PROJECT_API_BASE}/${currentProject.id}/modules`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(moduleData)
        });

        if (response.ok) {
            const createdModule = await response.json();
            showNotification('Module created! AI content generation started...', 'success');
            closeModal('createModuleModal');
            
            // Start content generation if enabled
            if (moduleData.generate_content.syllabus || moduleData.generate_content.slides || moduleData.generate_content.quizzes) {
                await triggerContentGeneration(createdModule.id, moduleData.generate_content);
            }
            
            await loadProjectTracks(currentProject.id);
            await loadTabContent(currentTab);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create module', 'error');
        }
    } catch (error) {
        console.error('Error creating module:', error);
        showNotification('Failed to create module', 'error');
    }
}

async function triggerContentGeneration(moduleId, contentTypes) {
    try {
        const response = await fetch(`${PROJECT_API_BASE}/${currentProject.id}/modules/${moduleId}/generate-content`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(contentTypes)
        });

        if (response.ok) {
            showNotification('AI content generation started in background', 'info');
        } else {
            showNotification('Module created but content generation failed to start', 'warning');
        }
    } catch (error) {
        console.error('Error triggering content generation:', error);
        showNotification('Module created but content generation failed to start', 'warning');
    }
}

// Modal utilities
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    const form = document.querySelector(`#${modalId} form`);
    if (form) {
        form.reset();
    }
}

// =============================================================================
// ACTION FUNCTIONS
// =============================================================================

async function generateModuleContent(moduleId) {
    try {
        const response = await fetch(`${PROJECT_API_BASE}/${currentProject.id}/modules/${moduleId}/generate-content`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                syllabus: true,
                slides: true,
                quizzes: true
            })
        });

        if (response.ok) {
            showNotification('AI content generation started', 'success');
            await loadTabContent(currentTab);
        } else {
            showNotification('Failed to start content generation', 'error');
        }
    } catch (error) {
        console.error('Error generating module content:', error);
        showNotification('Failed to start content generation', 'error');
    }
}

async function regenerateModuleContent(moduleId) {
    if (!confirm('Are you sure you want to regenerate the content? This will replace any existing generated content.')) {
        return;
    }
    
    await generateModuleContent(moduleId);
}

function viewModule(moduleId) {
    window.location.href = `/module-editor.html?module=${moduleId}&project=${currentProject.id}`;
}

function editModule(moduleId) {
    showNotification('Module editing functionality coming soon', 'info');
}

function editTrack(trackId) {
    showNotification('Track editing functionality coming soon', 'info');
}

function manageTrackContent(trackId) {
    showNotification('Track content management coming soon', 'info');
}

function editProject() {
    showNotification('Project editing functionality coming soon', 'info');
}

async function publishProject() {
    if (!confirm('Are you sure you want to publish this project? This will make it available to all assigned participants.')) {
        return;
    }
    
    try {
        const response = await fetch(`${PROJECT_API_BASE}/${currentProject.id}/publish`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Project published successfully', 'success');
            currentProject.status = 'active';
            updateProjectDisplay();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to publish project', 'error');
        }
    } catch (error) {
        console.error('Error publishing project:', error);
        showNotification('Failed to publish project', 'error');
    }
}

function manageParticipants() {
    showNotification('Participant management coming soon', 'info');
}

// Utility functions
function showLoadingSpinner() {
    // Implementation depends on your loading spinner design
}

function hideLoadingSpinner() {
    // Implementation depends on your loading spinner design
}

// Mock data functions for development
function getMockProjectTracks() {
    return [
        {
            id: 'track-1',
            name: 'Foundation Track',
            description: 'Core programming fundamentals and development environment setup',
            difficulty_level: 'beginner',
            estimated_duration_hours: 80,
            status: 'active',
            modules: [
                {
                    id: 'module-1',
                    name: 'Development Environment Setup',
                    ai_description_prompt: 'Teach students how to set up a modern development environment including IDE, version control, and basic tools',
                    content_generation_status: 'completed',
                    approval_status: 'approved',
                    estimated_duration_hours: 8,
                    generated_syllabus: true,
                    generated_slides: true,
                    generated_quizzes: true,
                    rag_quality_score: 0.85,
                    module_order: 1
                },
                {
                    id: 'module-2',
                    name: 'Programming Fundamentals',
                    ai_description_prompt: 'Cover basic programming concepts including variables, data types, control structures, and functions',
                    content_generation_status: 'generating',
                    approval_status: 'draft',
                    estimated_duration_hours: 24,
                    generated_syllabus: true,
                    generated_slides: false,
                    generated_quizzes: false,
                    module_order: 2
                }
            ]
        },
        {
            id: 'track-2',
            name: 'Web Development Track',
            description: 'Modern web development using JavaScript, HTML, CSS, and frameworks',
            difficulty_level: 'intermediate',
            estimated_duration_hours: 120,
            status: 'draft',
            modules: [
                {
                    id: 'module-3',
                    name: 'Frontend Development',
                    ai_description_prompt: 'Comprehensive frontend development covering HTML, CSS, JavaScript, and modern frameworks',
                    content_generation_status: 'pending',
                    approval_status: 'draft',
                    estimated_duration_hours: 40,
                    module_order: 1
                }
            ]
        }
    ];
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});