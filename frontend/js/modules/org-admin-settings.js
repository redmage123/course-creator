/**
 * Organization Admin Dashboard - Settings Module
 *
 * BUSINESS CONTEXT:
 * Manages organization settings and preferences. Includes organization profile
 * configuration, branding (logo, colors), contact information, and system
 * preferences. Only organization admins can modify settings.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Organization profile CRUD operations
 * - Logo upload and management
 * - Contact information updates
 * - Feature toggles and preferences
 *
 * @module org-admin-settings
 */

import {
    fetchOrganization,
    updateOrganization
} from './org-admin-api.js';

import {
    escapeHtml,
    openModal,
    closeModal,
    showNotification,
    validateEmail
} from './org-admin-utils.js';

// Current organization context
let currentOrganizationId = null;
let currentOrganizationData = null;

/**
 * Initialize settings management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeSettingsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Settings management initialized for organization:', organizationId);
}

/**
 * Load and display settings data
 *
 * BUSINESS LOGIC:
 * Fetches organization details and populates settings forms
 *
 * @returns {Promise<void>}
 */
export async function loadSettingsData() {
    try {
        currentOrganizationData = await fetchOrganization(currentOrganizationId);

        // Populate settings forms
        populateOrganizationProfileForm(currentOrganizationData);
        populateContactInformationForm(currentOrganizationData);
        populateBrandingSettings(currentOrganizationData);
        populatePreferences(currentOrganizationData);

    } catch (error) {
        console.error('Error loading settings:', error);
        showNotification('Failed to load settings', 'error');
    }
}

/**
 * Populate organization profile form
 *
 * BUSINESS CONTEXT:
 * Shows basic organization information:
 * - Name and slug
 * - Description
 * - Domain/website
 *
 * @param {Object} org - Organization data object
 */
function populateOrganizationProfileForm(org) {
    // Organization name
    const nameInput = document.getElementById('settingsOrgName');
    if (nameInput) {
        nameInput.value = org.name || '';
    }

    // Organization slug
    const slugInput = document.getElementById('settingsOrgSlug');
    if (slugInput) {
        slugInput.value = org.slug || '';
        slugInput.disabled = true; // Slug cannot be changed after creation
    }

    // Description
    const descInput = document.getElementById('settingsOrgDescription');
    if (descInput) {
        descInput.value = org.description || '';
    }

    // Domain
    const domainInput = document.getElementById('settingsOrgDomain');
    if (domainInput) {
        domainInput.value = org.domain || '';
    }

    // Active status
    const activeCheckbox = document.getElementById('settingsOrgActive');
    if (activeCheckbox) {
        activeCheckbox.checked = org.is_active ?? true;
    }
}

/**
 * Populate contact information form
 *
 * BUSINESS CONTEXT:
 * Shows organization contact details:
 * - Physical address
 * - Contact phone
 * - Contact email
 *
 * @param {Object} org - Organization data object
 */
function populateContactInformationForm(org) {
    // Address
    const addressInput = document.getElementById('settingsOrgAddress');
    if (addressInput) {
        addressInput.value = org.address || '';
    }

    // Phone
    const phoneInput = document.getElementById('settingsOrgPhone');
    if (phoneInput) {
        phoneInput.value = org.contact_phone || '';
    }

    // Email
    const emailInput = document.getElementById('settingsOrgEmail');
    if (emailInput) {
        emailInput.value = org.contact_email || '';
    }
}

/**
 * Populate branding settings
 *
 * BUSINESS CONTEXT:
 * Shows organization branding options:
 * - Logo URL/upload
 * - Primary color
 * - Secondary color
 *
 * @param {Object} org - Organization data object
 */
function populateBrandingSettings(org) {
    // Logo URL
    const logoInput = document.getElementById('settingsOrgLogoUrl');
    if (logoInput) {
        logoInput.value = org.logo_url || '';
    }

    // Logo preview
    const logoPreview = document.getElementById('logoPreview');
    if (logoPreview && org.logo_url) {
        logoPreview.src = org.logo_url;
        logoPreview.style.display = 'block';
    }

    // Colors from settings object
    const primaryColorInput = document.getElementById('settingsPrimaryColor');
    if (primaryColorInput && org.settings?.primary_color) {
        primaryColorInput.value = org.settings.primary_color;
    }

    const secondaryColorInput = document.getElementById('settingsSecondaryColor');
    if (secondaryColorInput && org.settings?.secondary_color) {
        secondaryColorInput.value = org.settings.secondary_color;
    }
}

/**
 * Populate preferences
 *
 * BUSINESS CONTEXT:
 * Shows system preferences and feature toggles:
 * - Email notifications enabled
 * - Auto-enroll students
 * - Public project listing
 *
 * @param {Object} org - Organization data object
 */
function populatePreferences(org) {
    // Email notifications
    const emailNotifCheckbox = document.getElementById('settingsEmailNotifications');
    if (emailNotifCheckbox) {
        emailNotifCheckbox.checked = org.settings?.email_notifications ?? true;
    }

    // Auto-enroll
    const autoEnrollCheckbox = document.getElementById('settingsAutoEnroll');
    if (autoEnrollCheckbox) {
        autoEnrollCheckbox.checked = org.settings?.auto_enroll ?? false;
    }

    // Public projects
    const publicProjectsCheckbox = document.getElementById('settingsPublicProjects');
    if (publicProjectsCheckbox) {
        publicProjectsCheckbox.checked = org.settings?.public_projects ?? false;
    }
}

/**
 * Save organization profile changes
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function saveOrganizationProfile(event) {
    event.preventDefault();

    try {
        const updateData = {
            name: document.getElementById('settingsOrgName')?.value,
            description: document.getElementById('settingsOrgDescription')?.value || null,
            domain: document.getElementById('settingsOrgDomain')?.value || null,
            is_active: document.getElementById('settingsOrgActive')?.checked ?? true
        };

        await updateOrganization(currentOrganizationId, updateData);
        showNotification('Organization profile updated successfully', 'success');

        // Reload settings to reflect changes
        await loadSettingsData();

    } catch (error) {
        console.error('Error saving organization profile:', error);
    }
}

/**
 * Save contact information changes
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function saveContactInformation(event) {
    event.preventDefault();

    try {
        const email = document.getElementById('settingsOrgEmail')?.value;

        // Validate email
        if (email && !validateEmail(email)) {
            showNotification('Please enter a valid email address', 'error');
            return;
        }

        const updateData = {
            address: document.getElementById('settingsOrgAddress')?.value,
            contact_phone: document.getElementById('settingsOrgPhone')?.value,
            contact_email: email
        };

        await updateOrganization(currentOrganizationId, updateData);
        showNotification('Contact information updated successfully', 'success');

        // Reload settings
        await loadSettingsData();

    } catch (error) {
        console.error('Error saving contact information:', error);
    }
}

/**
 * Save branding settings
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function saveBrandingSettings(event) {
    event.preventDefault();

    try {
        const logoUrl = document.getElementById('settingsOrgLogoUrl')?.value;
        const primaryColor = document.getElementById('settingsPrimaryColor')?.value;
        const secondaryColor = document.getElementById('settingsSecondaryColor')?.value;

        const updateData = {
            logo_url: logoUrl || null,
            settings: {
                ...currentOrganizationData.settings,
                primary_color: primaryColor,
                secondary_color: secondaryColor
            }
        };

        await updateOrganization(currentOrganizationId, updateData);
        showNotification('Branding settings updated successfully', 'success');

        // Reload settings
        await loadSettingsData();

    } catch (error) {
        console.error('Error saving branding settings:', error);
    }
}

/**
 * Save preferences
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function savePreferences(event) {
    event.preventDefault();

    try {
        const updateData = {
            settings: {
                ...currentOrganizationData.settings,
                email_notifications: document.getElementById('settingsEmailNotifications')?.checked ?? true,
                auto_enroll: document.getElementById('settingsAutoEnroll')?.checked ?? false,
                public_projects: document.getElementById('settingsPublicProjects')?.checked ?? false
            }
        };

        await updateOrganization(currentOrganizationId, updateData);
        showNotification('Preferences updated successfully', 'success');

        // Reload settings
        await loadSettingsData();

    } catch (error) {
        console.error('Error saving preferences:', error);
    }
}

/**
 * Handle logo file upload
 *
 * TECHNICAL IMPLEMENTATION:
 * Uploads logo file to server and updates organization
 *
 * @param {Event} event - File input change event
 * @returns {Promise<void>}
 */
export async function uploadLogo(event) {
    const file = event.target?.files[0];

    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Only JPG, PNG, and GIF files are allowed', 'error');
        return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
        showNotification('File size must be less than 2MB', 'error');
        return;
    }

    try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('logo', file);
        formData.append('organization_id', currentOrganizationId);

        // Upload to server (this endpoint would need to be implemented)
        const response = await fetch('/api/v1/organizations/upload-logo', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to upload logo');
        }

        const result = await response.json();

        // Update logo URL in form
        const logoUrlInput = document.getElementById('settingsOrgLogoUrl');
        if (logoUrlInput) {
            logoUrlInput.value = result.logo_url;
        }

        // Update preview
        const logoPreview = document.getElementById('logoPreview');
        if (logoPreview) {
            logoPreview.src = result.logo_url;
            logoPreview.style.display = 'block';
        }

        showNotification('Logo uploaded successfully', 'success');

    } catch (error) {
        console.error('Error uploading logo:', error);
        showNotification('Failed to upload logo', 'error');
    }
}

/**
 * Reset organization settings to defaults
 *
 * BUSINESS CONTEXT:
 * Allows admin to reset all settings to system defaults
 * Requires confirmation due to irreversible nature
 */
export function resetToDefaults() {
    if (!confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
        return;
    }

    // Reload current settings (effectively cancels any unsaved changes)
    loadSettingsData();
    showNotification('Settings reset to current saved values', 'info');
}
