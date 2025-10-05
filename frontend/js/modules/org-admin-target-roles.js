/**
 * Organization Admin Dashboard - Target Roles Management Module
 *
 * BUSINESS CONTEXT:
 * Manages the list of available target roles that can be assigned to projects.
 * Roles are stored in the organization's settings in the database and are
 * organization-specific, allowing each organization to customize their role list.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Database-backed persistence via organization settings
 * - API-based CRUD operations
 * - Real-time UI updates
 * - Integration with project creation form
 *
 * @module org-admin-target-roles
 */

import { showNotification, escapeHtml } from './org-admin-utils.js';
import { fetchOrganization, updateOrganization } from './org-admin-api.js';

// Current organization context
let currentOrganizationId = null;
let currentSettings = null;

/**
 * Default target roles
 */
const DEFAULT_ROLES = [
    'Application Developer',
    'Business Analyst',
    'Operations Engineer',
    'Data Scientist',
    'DevOps Engineer',
    'QA Engineer',
    'System Administrator',
    'Technical Architect',
    'Product Manager',
    'Frontend Developer',
    'Backend Developer',
    'Full Stack Developer',
    'Security Engineer',
    'Network Engineer',
    'Database Administrator'
];

/**
 * Initialize module with organization ID
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeTargetRoles(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Target roles initialized for organization:', organizationId);
}

/**
 * Get current target roles from organization settings
 *
 * @returns {Array<string>} Array of role names
 */
export function getTargetRoles() {
    if (currentSettings?.target_roles && Array.isArray(currentSettings.target_roles)) {
        return currentSettings.target_roles;
    }
    return DEFAULT_ROLES;
}

/**
 * Save target roles to database via organization settings
 *
 * @param {Array<string>} roles - Array of role names
 * @returns {Promise<void>}
 */
async function saveTargetRoles(roles) {
    try {
        console.log('💾 Saving target roles to database:', roles);

        // Parse existing settings if it's a JSON string
        let settingsObj = currentSettings || {};
        if (typeof settingsObj === 'string') {
            try {
                settingsObj = JSON.parse(settingsObj);
            } catch (e) {
                settingsObj = {};
            }
        }

        // Update target_roles in settings
        settingsObj.target_roles = roles;

        // Save to database
        await updateOrganization(currentOrganizationId, {
            settings: settingsObj
        });

        // Update local cache
        currentSettings = settingsObj;

        // Update UI
        updateProjectFormRoles();

        console.log('✅ Target roles saved successfully');
    } catch (error) {
        console.error('❌ Error saving target roles:', error);
        throw error;
    }
}

/**
 * Add a new target role
 *
 * @param {string} roleName - Name of role to add
 * @returns {Promise<boolean>} True if added, false if duplicate
 */
export async function addTargetRole(roleName) {
    try {
        const roles = getTargetRoles();

        // Check for duplicates (case-insensitive)
        if (roles.some(r => r.toLowerCase() === roleName.toLowerCase())) {
            showNotification('Role already exists', 'error');
            return false;
        }

        roles.push(roleName);
        roles.sort();
        await saveTargetRoles(roles);
        renderTargetRolesList();
        showNotification('Role added successfully', 'success');
        return true;
    } catch (error) {
        showNotification('Failed to add role', 'error');
        return false;
    }
}

/**
 * Update an existing target role
 *
 * @param {string} oldName - Current name of role
 * @param {string} newName - New name for role
 * @returns {Promise<boolean>} True if updated successfully
 */
export async function updateTargetRole(oldName, newName) {
    try {
        const roles = getTargetRoles();
        const index = roles.indexOf(oldName);

        if (index === -1) {
            showNotification('Role not found', 'error');
            return false;
        }

        // Check if new name already exists (case-insensitive)
        if (roles.some((r, i) => i !== index && r.toLowerCase() === newName.toLowerCase())) {
            showNotification('A role with that name already exists', 'error');
            return false;
        }

        roles[index] = newName;
        roles.sort();
        await saveTargetRoles(roles);
        renderTargetRolesList();
        showNotification('Role updated successfully', 'success');
        return true;
    } catch (error) {
        showNotification('Failed to update role', 'error');
        return false;
    }
}

/**
 * Delete a target role
 *
 * @param {string} roleName - Name of role to delete
 * @returns {Promise<void>}
 */
export async function deleteTargetRole(roleName) {
    try {
        if (!confirm(`Delete role "${roleName}"?`)) {
            return;
        }

        const roles = getTargetRoles();
        const filtered = roles.filter(r => r !== roleName);
        await saveTargetRoles(filtered);
        renderTargetRolesList();
        showNotification('Role deleted successfully', 'success');
    } catch (error) {
        showNotification('Failed to delete role', 'error');
    }
}

/**
 * Reset roles to defaults
 *
 * @returns {Promise<void>}
 */
export async function resetTargetRolesToDefaults() {
    try {
        if (!confirm('Reset target roles to default list? This will delete any custom roles you have added.')) {
            return;
        }

        await saveTargetRoles([...DEFAULT_ROLES]);
        renderTargetRolesList();
        showNotification('Roles reset to defaults', 'success');
    } catch (error) {
        showNotification('Failed to reset roles', 'error');
    }
}

/**
 * Render the target roles list in settings
 */
export function renderTargetRolesList() {
    const container = document.getElementById('targetRolesList');
    if (!container) return;

    const roles = getTargetRoles();

    if (roles.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No roles defined</p>';
        return;
    }

    container.innerHTML = roles.map(role => {
        const escapedRole = escapeHtml(role);
        return `
        <div class="role-item" data-role="${escapedRole}" style="display: flex; justify-content: space-between; align-items: center;
                    padding: 0.75rem; margin-bottom: 0.5rem; background: var(--card-background);
                    border: 1px solid var(--border-color); border-radius: 4px;">
            <span class="role-name" style="font-weight: 500; flex: 1;">${escapedRole}</span>
            <input type="text" class="role-edit-input" style="display: none; flex: 1; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; margin-right: 0.5rem;">
            <div class="role-actions">
                <button type="button" class="btn-edit" onclick="editTargetRole('${escapedRole}')"
                        style="padding: 0.25rem 0.75rem; font-size: 0.875rem; margin-right: 0.5rem; background: var(--warning-color); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    ✏️ Edit
                </button>
                <button type="button" class="btn-delete" onclick="window.deleteTargetRole('${escapedRole}')"
                        style="padding: 0.25rem 0.75rem; font-size: 0.875rem; background: var(--error-color); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🗑️ Delete
                </button>
            </div>
            <div class="role-edit-actions" style="display: none;">
                <button type="button" class="btn-save" onclick="saveTargetRoleEdit('${escapedRole}')"
                        style="padding: 0.25rem 0.75rem; font-size: 0.875rem; margin-right: 0.5rem; background: var(--success-color); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    💾 Save
                </button>
                <button type="button" class="btn-cancel" onclick="cancelTargetRoleEdit('${escapedRole}')"
                        style="padding: 0.25rem 0.75rem; font-size: 0.875rem; background: var(--secondary-color); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    ❌ Cancel
                </button>
            </div>
        </div>
    `;
    }).join('');
}

/**
 * Enter edit mode for a role
 *
 * @param {string} roleName - Name of role to edit
 */
window.editTargetRole = function(roleName) {
    const roleItem = document.querySelector(`.role-item[data-role="${escapeHtml(roleName)}"]`);
    if (!roleItem) return;

    const nameSpan = roleItem.querySelector('.role-name');
    const editInput = roleItem.querySelector('.role-edit-input');
    const normalActions = roleItem.querySelector('.role-actions');
    const editActions = roleItem.querySelector('.role-edit-actions');

    // Show edit input with current value
    nameSpan.style.display = 'none';
    editInput.style.display = 'block';
    editInput.value = roleName;
    editInput.focus();

    // Switch action buttons
    normalActions.style.display = 'none';
    editActions.style.display = 'block';
};

/**
 * Save role edit
 *
 * @param {string} oldName - Original role name
 */
window.saveTargetRoleEdit = async function(oldName) {
    const roleItem = document.querySelector(`.role-item[data-role="${escapeHtml(oldName)}"]`);
    if (!roleItem) return;

    const editInput = roleItem.querySelector('.role-edit-input');
    const newName = editInput.value.trim();

    if (!newName) {
        showNotification('Role name cannot be empty', 'error');
        return;
    }

    if (await window.OrgAdmin.TargetRoles.update(oldName, newName)) {
        // Success - renderTargetRolesList() is called by updateTargetRole
    }
};

/**
 * Cancel role edit
 *
 * @param {string} roleName - Name of role being edited
 */
window.cancelTargetRoleEdit = function(roleName) {
    renderTargetRolesList();
};

/**
 * Update project form with current roles
 */
function updateProjectFormRoles() {
    const select = document.getElementById('projectTargetRoles');
    if (!select) return;

    const roles = getTargetRoles();
    const selectedValues = Array.from(select.selectedOptions).map(opt => opt.value);

    select.innerHTML = roles.map(role => {
        const isSelected = selectedValues.includes(role) ? 'selected' : '';
        return `<option value="${escapeHtml(role)}" ${isSelected}>${escapeHtml(role)}</option>`;
    }).join('');
}

/**
 * Initialize target roles management
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} organizationData - Organization data from API
 */
export async function initializeTargetRolesManagement(organizationId, organizationData) {
    console.log('📋 Initializing target roles management');

    // Set organization context
    currentOrganizationId = organizationId;

    // Load settings from organization
    if (organizationData?.settings) {
        if (typeof organizationData.settings === 'string') {
            try {
                currentSettings = JSON.parse(organizationData.settings);
            } catch (e) {
                console.error('Error parsing organization settings:', e);
                currentSettings = {};
            }
        } else {
            currentSettings = organizationData.settings;
        }
    } else {
        currentSettings = {};
    }

    // If no target_roles in settings, initialize with defaults
    if (!currentSettings.target_roles || !Array.isArray(currentSettings.target_roles)) {
        console.log('No target_roles found, initializing with defaults');
        currentSettings.target_roles = [...DEFAULT_ROLES];
        // Save defaults to database
        try {
            await saveTargetRoles(currentSettings.target_roles);
        } catch (error) {
            console.error('Failed to save default roles:', error);
        }
    }

    console.log('Current target roles:', currentSettings.target_roles);

    // Render roles list
    renderTargetRolesList();

    // Update project form
    updateProjectFormRoles();

    // Setup add role form handler
    const addForm = document.getElementById('addTargetRoleForm');
    if (addForm) {
        // Remove existing listener if any
        const newForm = addForm.cloneNode(true);
        addForm.parentNode.replaceChild(newForm, addForm);

        newForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('newTargetRole');
            const roleName = input.value.trim();

            if (roleName) {
                if (await addTargetRole(roleName)) {
                    input.value = '';
                }
            }
        });
    }

    console.log('✅ Target roles management initialized');
}
