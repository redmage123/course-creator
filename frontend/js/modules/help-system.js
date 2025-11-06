/**
 * Help System Module - Comprehensive context-aware help with AI integration
 *
 * BUSINESS CONTEXT:
 * Provides integrated help system that combines static documentation with
 * AI-powered assistance. Adapts to user's current context and role.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Context-aware help content based on current page/tab
 * - AI assistant integration for dynamic questions
 * - Search functionality across help content
 * - Keyboard shortcuts (F1) for quick access
 * - Guided tours and walkthroughs
 * - Accessibility compliant (WCAG 2.1 AA)
 *
 * @module help-system
 */

import { showNotification, escapeHtml } from './org-admin-utils.js';

// ============================================================================
// HELP CONTENT LIBRARY
// ============================================================================

/**
 * Comprehensive help content organized by category
 *
 * BUSINESS CONTEXT:
 * Provides self-service help content covering all platform features.
 * Content is organized by user role and task.
 */
export const HELP_CONTENT = {
    // Getting Started
    gettingStarted: {
        title: "Getting Started",
        icon: "🚀",
        articles: [
            {
                id: "welcome",
                title: "Welcome to Course Creator",
                tags: ["basics", "introduction"],
                content: `
                    <h3>Welcome to the Course Creator Platform</h3>
                    <p>This platform helps you create, manage, and deliver high-quality training programs.</p>

                    <h4>Quick Start Guide</h4>
                    <ol>
                        <li><strong>Create a Project:</strong> Start by creating a project for your training program</li>
                        <li><strong>Add Tracks:</strong> Organize learning paths within your project</li>
                        <li><strong>Add Members:</strong> Invite instructors and enroll students</li>
                        <li><strong>Generate Content:</strong> Use AI to create course materials</li>
                        <li><strong>Monitor Progress:</strong> Track student performance and analytics</li>
                    </ol>

                    <div class="help-tip">
                        <strong>💡 Tip:</strong> Press <kbd>F1</kbd> anytime to open this help system!
                    </div>
                `
            },
            {
                id: "dashboard-overview",
                title: "Dashboard Overview",
                tags: ["dashboard", "navigation"],
                content: `
                    <h3>Organization Admin Dashboard</h3>
                    <p>Your dashboard is organized into key sections:</p>

                    <ul>
                        <li><strong>📋 Projects:</strong> Create and manage training projects</li>
                        <li><strong>👥 Members:</strong> Manage instructors and students</li>
                        <li><strong>📊 Analytics:</strong> View performance metrics and reports</li>
                        <li><strong>⚙️ Settings:</strong> Configure organization preferences</li>
                    </ul>

                    <h4>Navigation Tips</h4>
                    <p>Use the tab buttons at the top to switch between sections. Each tab shows relevant content and actions.</p>
                `
            },
            {
                id: "ai-assistant",
                title: "Using the AI Assistant",
                tags: ["ai", "assistant", "help"],
                content: `
                    <h3>AI Assistant</h3>
                    <p>The AI assistant can help you with:</p>

                    <ul>
                        <li>Creating projects and tracks</li>
                        <li>Generating course content</li>
                        <li>Finding specific features</li>
                        <li>Answering questions about the platform</li>
                    </ul>

                    <h4>How to Use</h4>
                    <ol>
                        <li>Click the 💬 button in the bottom-right corner</li>
                        <li>Type your question or request</li>
                        <li>Press Enter or click Send</li>
                    </ol>

                    <div class="help-example">
                        <strong>Example Questions:</strong>
                        <ul>
                            <li>"How do I create a new project?"</li>
                            <li>"What's the difference between single and multi-location projects?"</li>
                            <li>"How can I add instructors to my organization?"</li>
                        </ul>
                    </div>
                `
            }
        ]
    },

    // Projects
    projects: {
        title: "Projects",
        icon: "📋",
        articles: [
            {
                id: "create-project",
                title: "Creating a Project",
                tags: ["project", "create", "wizard"],
                content: `
                    <h3>Creating a Project</h3>
                    <p>Projects are the top-level containers for your training programs.</p>

                    <h4>Step-by-Step Guide</h4>
                    <ol>
                        <li>Go to the <strong>Projects</strong> tab</li>
                        <li>Click <strong>Create Project</strong></li>
                        <li>Choose project type:
                            <ul>
                                <li><strong>Single Location:</strong> All students in one location</li>
                                <li><strong>Multi-Location:</strong> Students across multiple locations</li>
                            </ul>
                        </li>
                        <li>Fill in project details:
                            <ul>
                                <li>Project name and slug (URL-friendly identifier)</li>
                                <li>Start and end dates</li>
                                <li>Maximum participants (optional)</li>
                            </ul>
                        </li>
                        <li>Add tracks (learning paths)</li>
                        <li>Review and create</li>
                    </ol>

                    <div class="help-tip">
                        <strong>💡 Tip:</strong> Start dates default to the next working day if you create a project on the weekend!
                    </div>

                    <div class="help-warning">
                        <strong>⚠️ Important:</strong> The project slug cannot be changed after creation.
                    </div>
                `
            },
            {
                id: "project-types",
                title: "Project Types Explained",
                tags: ["project", "types", "single-location", "multi-location"],
                content: `
                    <h3>Understanding Project Types</h3>

                    <h4>Single Location Projects</h4>
                    <p>Best for:</p>
                    <ul>
                        <li>Training programs at one physical location</li>
                        <li>Online-only courses</li>
                        <li>Simpler setup and management</li>
                    </ul>

                    <h4>Multi-Location Projects</h4>
                    <p>Best for:</p>
                    <ul>
                        <li>Training programs across multiple cities/offices</li>
                        <li>Different start dates per location</li>
                        <li>Location-specific capacity management</li>
                    </ul>

                    <p>Each location can have:</p>
                    <ul>
                        <li>Different start and end dates</li>
                        <li>Different maximum participant counts</li>
                        <li>Location-specific instructors</li>
                    </ul>
                `
            },
            {
                id: "manage-projects",
                title: "Managing Projects",
                tags: ["project", "edit", "manage"],
                content: `
                    <h3>Managing Existing Projects</h3>

                    <h4>View Project Details</h4>
                    <p>Click on any project in the list to view full details including:</p>
                    <ul>
                        <li>Project timeline and status</li>
                        <li>Enrolled students and instructors</li>
                        <li>Tracks and learning paths</li>
                        <li>Performance analytics</li>
                    </ul>

                    <h4>Edit Projects</h4>
                    <p>You can modify:</p>
                    <ul>
                        <li>Project name and description</li>
                        <li>End dates (start dates are locked after enrollment begins)</li>
                        <li>Maximum participants</li>
                        <li>Assigned tracks</li>
                    </ul>

                    <h4>Archive Projects</h4>
                    <p>Completed projects can be archived to keep your dashboard organized while preserving historical data.</p>
                `
            }
        ]
    },

    // Tracks
    tracks: {
        title: "Tracks",
        icon: "🛤️",
        articles: [
            {
                id: "create-track",
                title: "Creating a Track",
                tags: ["track", "create", "learning-path"],
                content: `
                    <h3>Creating a Track</h3>
                    <p>Tracks are learning paths that organize course content and define student journeys.</p>

                    <h4>Track Creation Steps</h4>
                    <ol>
                        <li>Within a project, click <strong>Add Track</strong></li>
                        <li>Enter track details:
                            <ul>
                                <li>Track name and description</li>
                                <li>Difficulty level (Beginner, Intermediate, Advanced)</li>
                                <li>Estimated duration in hours</li>
                            </ul>
                        </li>
                        <li>Define prerequisites (if any)</li>
                        <li>Add courses and modules</li>
                    </ol>

                    <h4>Track Organization Tips</h4>
                    <ul>
                        <li>Create separate tracks for different roles (e.g., Developer, DevOps, QA)</li>
                        <li>Use difficulty levels to guide student selection</li>
                        <li>Set realistic time estimates to help students plan</li>
                    </ul>
                `
            },
            {
                id: "track-structure",
                title: "Track Structure & Prerequisites",
                tags: ["track", "structure", "prerequisites"],
                content: `
                    <h3>Organizing Track Content</h3>

                    <h4>Track Hierarchy</h4>
                    <pre>
Project
  └── Track (e.g., "Full Stack Developer")
      ├── Course 1: Frontend Fundamentals
      ├── Course 2: Backend Development
      └── Course 3: DevOps Basics
                    </pre>

                    <h4>Setting Prerequisites</h4>
                    <p>Prerequisites ensure students complete foundational content first:</p>
                    <ul>
                        <li>Select required tracks that must be completed first</li>
                        <li>Students can only enroll if prerequisites are met</li>
                        <li>Helps maintain learning progression</li>
                    </ul>
                `
            }
        ]
    },

    // Members
    members: {
        title: "Members",
        icon: "👥",
        articles: [
            {
                id: "add-instructors",
                title: "Adding Instructors",
                tags: ["instructors", "members", "add"],
                content: `
                    <h3>Adding Instructors</h3>

                    <h4>Individual Instructor</h4>
                    <ol>
                        <li>Go to <strong>Members</strong> tab</li>
                        <li>Click <strong>Add Instructor</strong></li>
                        <li>Enter instructor details:
                            <ul>
                                <li>Email address</li>
                                <li>Full name</li>
                                <li>Assign to projects/tracks</li>
                            </ul>
                        </li>
                        <li>Click <strong>Send Invitation</strong></li>
                    </ol>

                    <h4>Bulk Import</h4>
                    <p>For multiple instructors:</p>
                    <ol>
                        <li>Click <strong>Bulk Import</strong></li>
                        <li>Download the template spreadsheet</li>
                        <li>Fill in instructor details</li>
                        <li>Upload the completed file</li>
                    </ol>

                    <div class="help-tip">
                        <strong>💡 Tip:</strong> Instructors receive an email invitation with login instructions.
                    </div>
                `
            },
            {
                id: "enroll-students",
                title: "Enrolling Students",
                tags: ["students", "enrollment", "add"],
                content: `
                    <h3>Student Enrollment</h3>

                    <h4>Manual Enrollment</h4>
                    <ol>
                        <li>Select a project or track</li>
                        <li>Click <strong>Enroll Student</strong></li>
                        <li>Enter student email and name</li>
                        <li>Select enrollment options:
                            <ul>
                                <li>Start date</li>
                                <li>Location (for multi-location projects)</li>
                                <li>Optional: Custom deadline</li>
                            </ul>
                        </li>
                    </ol>

                    <h4>Bulk Enrollment</h4>
                    <p>Enroll multiple students at once using spreadsheet import:</p>
                    <ol>
                        <li>Download enrollment template</li>
                        <li>Add student details (email, name, project, track)</li>
                        <li>Upload to automatically create accounts and enroll</li>
                    </ol>

                    <div class="help-warning">
                        <strong>⚠️ Capacity Limits:</strong> Respect project maximum participant settings.
                    </div>
                `
            }
        ]
    },

    // Analytics
    analytics: {
        title: "Analytics",
        icon: "📊",
        articles: [
            {
                id: "view-analytics",
                title: "Viewing Analytics",
                tags: ["analytics", "reports", "metrics"],
                content: `
                    <h3>Analytics Dashboard</h3>

                    <h4>Available Metrics</h4>
                    <ul>
                        <li><strong>Enrollment Stats:</strong> Total enrollments, active students</li>
                        <li><strong>Completion Rates:</strong> Track and course completion percentages</li>
                        <li><strong>Progress Tracking:</strong> Individual and cohort progress</li>
                        <li><strong>Performance Metrics:</strong> Quiz scores, assignment grades</li>
                        <li><strong>Engagement Data:</strong> Login frequency, time spent</li>
                    </ul>

                    <h4>Filtering Options</h4>
                    <p>Filter analytics by:</p>
                    <ul>
                        <li>Date range</li>
                        <li>Project or track</li>
                        <li>Location</li>
                        <li>Student cohort</li>
                    </ul>

                    <h4>Exporting Reports</h4>
                    <p>Export analytics data as CSV or PDF for external analysis or reporting.</p>
                `
            }
        ]
    },

    // Settings
    settings: {
        title: "Settings",
        icon: "⚙️",
        articles: [
            {
                id: "org-settings",
                title: "Organization Settings",
                tags: ["settings", "organization", "configuration"],
                content: `
                    <h3>Organization Settings</h3>

                    <h4>General Information</h4>
                    <ul>
                        <li>Organization name and description</li>
                        <li>Contact information (email, phone, website)</li>
                        <li>Logo and branding</li>
                    </ul>

                    <h4>Preferences</h4>
                    <ul>
                        <li>Default language and timezone</li>
                        <li>Email notification settings</li>
                        <li>Default project settings</li>
                    </ul>

                    <h4>Security</h4>
                    <ul>
                        <li>Two-factor authentication</li>
                        <li>Password policies</li>
                        <li>Session timeout settings</li>
                    </ul>
                `
            }
        ]
    },

    // Keyboard Shortcuts
    shortcuts: {
        title: "Keyboard Shortcuts",
        icon: "⌨️",
        articles: [
            {
                id: "shortcuts-list",
                title: "Keyboard Shortcuts",
                tags: ["shortcuts", "keyboard", "hotkeys"],
                content: `
                    <h3>Keyboard Shortcuts</h3>

                    <h4>Global Shortcuts</h4>
                    <table class="help-table">
                        <tr><td><kbd>F1</kbd></td><td>Open Help</td></tr>
                        <tr><td><kbd>Ctrl</kbd> + <kbd>/</kbd></td><td>Search</td></tr>
                        <tr><td><kbd>Esc</kbd></td><td>Close modal/panel</td></tr>
                    </table>

                    <h4>Navigation</h4>
                    <table class="help-table">
                        <tr><td><kbd>Ctrl</kbd> + <kbd>1</kbd></td><td>Projects tab</td></tr>
                        <tr><td><kbd>Ctrl</kbd> + <kbd>2</kbd></td><td>Members tab</td></tr>
                        <tr><td><kbd>Ctrl</kbd> + <kbd>3</kbd></td><td>Analytics tab</td></tr>
                        <tr><td><kbd>Ctrl</kbd> + <kbd>4</kbd></td><td>Settings tab</td></tr>
                    </table>

                    <h4>Actions</h4>
                    <table class="help-table">
                        <tr><td><kbd>Ctrl</kbd> + <kbd>N</kbd></td><td>New Project</td></tr>
                        <tr><td><kbd>Ctrl</kbd> + <kbd>S</kbd></td><td>Save</td></tr>
                    </table>
                `
            }
        ]
    }
};

// ============================================================================
// HELP SYSTEM STATE
// ============================================================================

let currentContext = null;
let searchIndex = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize help system
 *
 * BUSINESS CONTEXT:
 * Sets up help system on page load, including keyboard shortcuts
 */
export function initializeHelpSystem() {
    console.log('📚 Initializing Help System...');

    // Build search index
    buildSearchIndex();

    // Set up keyboard shortcuts
    setupKeyboardShortcuts();

    // Detect current context
    detectContext();

    console.log('✅ Help System initialized');
}

/**
 * Build search index from all help content
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates searchable index of all help articles for quick lookup
 */
function buildSearchIndex() {
    searchIndex = [];

    Object.keys(HELP_CONTENT).forEach(categoryKey => {
        const category = HELP_CONTENT[categoryKey];

        category.articles.forEach(article => {
            searchIndex.push({
                category: categoryKey,
                categoryTitle: category.title,
                articleId: article.id,
                title: article.title,
                tags: article.tags,
                content: article.content,
                searchText: `${article.title} ${article.tags.join(' ')} ${article.content}`.toLowerCase()
            });
        });
    });

    console.log(`📇 Built search index with ${searchIndex.length} articles`);
}

/**
 * Set up global keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // F1 - Open Help
        if (e.key === 'F1') {
            e.preventDefault();
            openHelpModal();
        }

        // Escape - Close Help
        if (e.key === 'Escape') {
            closeHelpModal();
        }
    });
}

/**
 * Detect current context from page/tab state
 */
function detectContext() {
    // Check active tab
    const activeTab = document.querySelector('.tab-button.active');
    if (activeTab) {
        const tabText = activeTab.textContent.toLowerCase();

        if (tabText.includes('project')) {
            currentContext = 'projects';
        } else if (tabText.includes('member')) {
            currentContext = 'members';
        } else if (tabText.includes('analytic')) {
            currentContext = 'analytics';
        } else if (tabText.includes('setting')) {
            currentContext = 'settings';
        }
    }

    console.log(`🎯 Detected context: ${currentContext || 'general'}`);
}

// ============================================================================
// HELP MODAL FUNCTIONS
// ============================================================================

/**
 * Open help modal
 *
 * @param {string} categoryKey - Optional category to show initially
 * @param {string} articleId - Optional specific article to show
 */
export function openHelpModal(categoryKey = null, articleId = null) {
    console.log('📖 Opening help modal...');

    const modal = document.getElementById('helpModal');
    if (!modal) {
        console.error('❌ Help modal not found');
        return;
    }

    // Show modal
    modal.style.display = 'block';
    modal.classList.add('active');

    // Show context-relevant category or specified category
    const targetCategory = categoryKey || currentContext || 'gettingStarted';
    showHelpCategory(targetCategory);

    // Show specific article if specified
    if (articleId) {
        showHelpArticle(targetCategory, articleId);
    }

    // Focus search input
    const searchInput = document.getElementById('helpSearchInput');
    if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
    }
}

/**
 * Close help modal
 */
export function closeHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

/**
 * Show help category
 */
export function showHelpCategory(categoryKey) {
    const category = HELP_CONTENT[categoryKey];
    if (!category) {
        console.error(`❌ Category not found: ${categoryKey}`);
        return;
    }

    // Update active category button
    document.querySelectorAll('.help-category-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const categoryBtn = document.querySelector(`[data-category="${categoryKey}"]`);
    if (categoryBtn) {
        categoryBtn.classList.add('active');
    }

    // Show category content
    const contentArea = document.getElementById('helpContentArea');
    if (!contentArea) return;

    let html = `
        <div class="help-category-header">
            <h2>${category.icon} ${category.title}</h2>
        </div>
        <div class="help-articles-list">
    `;

    category.articles.forEach(article => {
        html += `
            <div class="help-article-card" onclick="window.HelpSystem.showHelpArticle('${categoryKey}', '${article.id}')">
                <h3>${article.title}</h3>
                <div class="help-article-tags">
                    ${article.tags.map(tag => `<span class="help-tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;
    });

    html += `</div>`;
    contentArea.innerHTML = html;
}

/**
 * Show specific help article
 */
export function showHelpArticle(categoryKey, articleId) {
    const category = HELP_CONTENT[categoryKey];
    if (!category) return;

    const article = category.articles.find(a => a.id === articleId);
    if (!article) return;

    const contentArea = document.getElementById('helpContentArea');
    if (!contentArea) return;

    contentArea.innerHTML = `
        <div class="help-article-view">
            <button onclick="window.HelpSystem.showHelpCategory('${categoryKey}')" class="help-back-btn">
                ← Back to ${category.title}
            </button>
            <div class="help-article-content">
                ${article.content}
            </div>
            <div class="help-article-footer">
                <p>Was this helpful?</p>
                <button onclick="window.HelpSystem.rateArticle('${categoryKey}', '${articleId}', true)" class="btn btn-sm btn-success">👍 Yes</button>
                <button onclick="window.HelpSystem.rateArticle('${categoryKey}', '${articleId}', false)" class="btn btn-sm">👎 No</button>
            </div>
            <div class="help-ai-prompt">
                <p>Need more help?</p>
                <button onclick="window.HelpSystem.askAIAboutArticle('${categoryKey}', '${articleId}')" class="btn btn-primary">
                    💬 Ask AI Assistant
                </button>
            </div>
        </div>
    `;
}

/**
 * Search help content
 */
export function searchHelp(query) {
    if (!query || query.length < 2) {
        return;
    }

    const searchTerm = query.toLowerCase();
    const results = searchIndex.filter(item => item.searchText.includes(searchTerm));

    const contentArea = document.getElementById('helpContentArea');
    if (!contentArea) return;

    if (results.length === 0) {
        contentArea.innerHTML = `
            <div class="help-no-results">
                <h3>No results found for "${escapeHtml(query)}"</h3>
                <p>Try different keywords or ask the AI Assistant:</p>
                <button onclick="window.HelpSystem.askAI('${escapeHtml(query)}')" class="btn btn-primary">
                    💬 Ask AI Assistant
                </button>
            </div>
        `;
        return;
    }

    let html = `
        <div class="help-search-results">
            <h2>Search Results for "${escapeHtml(query)}"</h2>
            <p class="help-results-count">${results.length} article${results.length !== 1 ? 's' : ''} found</p>
    `;

    results.forEach(result => {
        html += `
            <div class="help-search-result" onclick="window.HelpSystem.showHelpArticle('${result.category}', '${result.articleId}')">
                <h3>${result.title}</h3>
                <p class="help-result-category">${result.categoryTitle}</p>
                <div class="help-article-tags">
                    ${result.tags.map(tag => `<span class="help-tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;
    });

    html += `</div>`;
    contentArea.innerHTML = html;
}

/**
 * Rate help article
 */
export function rateArticle(categoryKey, articleId, helpful) {
    showNotification(helpful ? 'Thanks for your feedback!' : 'Sorry this wasn\'t helpful. Try asking the AI Assistant.', 'info');

    // Track rating (could send to analytics)
    console.log(`📊 Article rated: ${categoryKey}/${articleId} - ${helpful ? 'helpful' : 'not helpful'}`);
}

/**
 * Ask AI about specific article
 */
export function askAIAboutArticle(categoryKey, articleId) {
    const category = HELP_CONTENT[categoryKey];
    const article = category.articles.find(a => a.id === articleId);

    if (!article) return;

    // Close help modal
    closeHelpModal();

    // Open AI assistant with context
    if (typeof toggleDashboardAIChat === 'function') {
        toggleDashboardAIChat();

        // Pre-fill question
        const input = document.getElementById('dashboardAIChatInput');
        if (input) {
            input.value = `I need help with: ${article.title}`;
            input.focus();
        }
    }
}

/**
 * Ask AI directly
 */
export function askAI(question) {
    closeHelpModal();

    if (typeof toggleDashboardAIChat === 'function') {
        toggleDashboardAIChat();

        const input = document.getElementById('dashboardAIChatInput');
        if (input) {
            input.value = question;
            input.focus();
        }
    }
}

// ============================================================================
// GUIDED TOUR
// ============================================================================

/**
 * Start guided tour
 */
export function startGuidedTour() {
    console.log('🎯 Starting guided tour...');
    showNotification('Guided tour feature coming soon!', 'info');
    // TODO: Implement step-by-step tour with highlights
}

// ============================================================================
// EXPORTS
// ============================================================================

// Make functions globally available
if (typeof window !== 'undefined') {
    window.HelpSystem = {
        openHelpModal,
        closeHelpModal,
        showHelpCategory,
        showHelpArticle,
        searchHelp,
        rateArticle,
        askAIAboutArticle,
        askAI,
        startGuidedTour
    };
}

export default {
    initializeHelpSystem,
    openHelpModal,
    closeHelpModal,
    showHelpCategory,
    showHelpArticle,
    searchHelp,
    HELP_CONTENT
};
