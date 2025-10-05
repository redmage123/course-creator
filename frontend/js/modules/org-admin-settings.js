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

    // Set up form submit handlers
    setupFormHandlers();
}

/**
 * Setup form event handlers
 *
 * TECHNICAL IMPLEMENTATION:
 * Attaches submit handlers to all settings forms
 */
function setupFormHandlers() {
    console.log('📋 Setting up settings form handlers');

    // Main settings form
    const settingsForm = document.getElementById('orgSettingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveOrganizationProfile);
        console.log('✅ Settings form submit handler attached');
    } else {
        console.warn('⚠️ Settings form not found (will try again when tab loads)');
    }

    // Preferences form (if separate)
    const preferencesForm = document.getElementById('orgPreferencesForm');
    if (preferencesForm) {
        preferencesForm.addEventListener('submit', savePreferences);
        console.log('✅ Preferences form submit handler attached');
    }

    // Logo upload input
    const logoInput = document.getElementById('settingsOrgLogoFile');
    if (logoInput) {
        logoInput.addEventListener('change', uploadLogo);
        console.log('✅ Logo upload handler attached');
    }
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
        console.log('📋 Loading settings data for org:', currentOrganizationId);
        currentOrganizationData = await fetchOrganization(currentOrganizationId);
        console.log('✅ Organization data fetched:', currentOrganizationData);

        // Re-attach form handlers (in case tab was just loaded)
        setupFormHandlers();

        // Populate settings forms
        populateOrganizationProfileForm(currentOrganizationData);
        populateContactInformationForm(currentOrganizationData);
        populateBrandingSettings(currentOrganizationData);
        populatePreferences(currentOrganizationData);

        // Initialize target roles management
        if (window.OrgAdmin?.TargetRoles?.init) {
            await window.OrgAdmin.TargetRoles.init(currentOrganizationId, currentOrganizationData);
        }

        console.log('✅ Settings forms populated');

    } catch (error) {
        console.error('❌ Error loading settings:', error);
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
    console.log('📝 Populating organization profile form');

    // Try both naming conventions (settingsOrgName and orgNameSetting)
    const nameInput = document.getElementById('settingsOrgName') || document.getElementById('orgNameSetting');
    if (nameInput) {
        nameInput.value = org.name || '';
        console.log('✅ Set organization name:', org.name);
    } else {
        console.warn('⚠️ Name input not found (tried settingsOrgName and orgNameSetting)');
    }

    // Organization slug
    const slugInput = document.getElementById('settingsOrgSlug') || document.getElementById('orgSlugSetting');
    if (slugInput) {
        slugInput.value = org.slug || '';
        slugInput.disabled = true; // Slug cannot be changed after creation
        console.log('✅ Set organization slug:', org.slug);
    } else {
        console.warn('⚠️ Slug input not found');
    }

    // Description
    const descInput = document.getElementById('settingsOrgDescription') || document.getElementById('orgDescriptionSetting');
    if (descInput) {
        descInput.value = org.description || '';
        console.log('✅ Set description');
    } else {
        console.warn('⚠️ Description input not found');
    }

    // Domain - ensure it has protocol for URL validation
    const domainInput = document.getElementById('settingsOrgDomain') || document.getElementById('orgDomainSetting');
    if (domainInput) {
        let domainValue = org.domain || '';
        // Add https:// if domain exists but doesn't have protocol
        if (domainValue && !domainValue.startsWith('http://') && !domainValue.startsWith('https://')) {
            domainValue = 'https://' + domainValue;
        }
        domainInput.value = domainValue;
        console.log('✅ Set domain:', domainValue);
    } else {
        console.warn('⚠️ Domain input not found');
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
    console.log('📞 Populating contact information form');

    // Address - try both formats
    const addressInput = document.getElementById('settingsOrgAddress') ||
                        document.getElementById('orgStreetAddressSetting');
    if (addressInput) {
        addressInput.value = org.street_address || org.address || '';
        console.log('✅ Set address');
    } else {
        console.warn('⚠️ Address input not found');
    }

    // Phone - try both formats
    const phoneInput = document.getElementById('settingsOrgPhone') ||
                      document.getElementById('orgContactPhoneSetting');
    if (phoneInput) {
        phoneInput.value = org.contact_phone || '';
        console.log('✅ Set phone:', org.contact_phone);
    } else {
        console.warn('⚠️ Phone input not found');
    }

    // Email - try both formats
    const emailInput = document.getElementById('settingsOrgEmail') ||
                      document.getElementById('orgContactEmailSetting');
    if (emailInput) {
        emailInput.value = org.contact_email || '';
        console.log('✅ Set email:', org.contact_email);
    } else {
        console.warn('⚠️ Email input not found');
    }

    // Additional address fields
    const cityInput = document.getElementById('orgCitySetting');
    if (cityInput) {
        cityInput.value = org.city || '';
        console.log('✅ Set city:', org.city);
    }

    const stateInput = document.getElementById('orgStateProvinceSetting');
    if (stateInput) {
        stateInput.value = org.state_province || '';
        console.log('✅ Set state:', org.state_province);
    }

    const postalInput = document.getElementById('orgPostalCodeSetting');
    if (postalInput) {
        postalInput.value = org.postal_code || '';
        console.log('✅ Set postal code:', org.postal_code);
    }

    const countryInput = document.getElementById('orgCountrySetting');
    if (countryInput) {
        countryInput.value = org.country || 'US';
        console.log('✅ Set country:', org.country);
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

    console.log('💾 Saving organization profile...');

    try {
        // Get values from form fields (try both naming conventions)
        const nameField = document.getElementById('settingsOrgName') || document.getElementById('orgNameSetting');
        const descField = document.getElementById('settingsOrgDescription') || document.getElementById('orgDescriptionSetting');
        const domainField = document.getElementById('settingsOrgDomain') || document.getElementById('orgDomainSetting');
        const streetField = document.getElementById('orgStreetAddressSetting');
        const cityField = document.getElementById('orgCitySetting');
        const stateField = document.getElementById('orgStateProvinceSetting');
        const postalField = document.getElementById('orgPostalCodeSetting');
        const countryField = document.getElementById('orgCountrySetting');
        const phoneField = document.getElementById('settingsOrgPhone') || document.getElementById('orgContactPhoneSetting');
        const emailField = document.getElementById('settingsOrgEmail') || document.getElementById('orgContactEmailSetting');

        // Strip protocol from domain for API (backend expects just domain name)
        let domainValue = domainField?.value || null;
        if (domainValue) {
            domainValue = domainValue.replace(/^https?:\/\//, '');
        }

        const updateData = {
            name: nameField?.value,
            description: descField?.value || null,
            domain: domainValue,
            street_address: streetField?.value || null,
            city: cityField?.value || null,
            state_province: stateField?.value || null,
            postal_code: postalField?.value || null,
            country: countryField?.value || null,
            contact_phone: phoneField?.value || null,
            contact_email: emailField?.value || null
        };

        console.log('📤 Sending update data:', updateData);

        await updateOrganization(currentOrganizationId, updateData);
        showNotification('Organization profile updated successfully', 'success');

        console.log('✅ Organization profile saved');

        // Reload settings to reflect changes
        await loadSettingsData();

    } catch (error) {
        console.error('❌ Error saving organization profile:', error);
        showNotification(`Failed to save: ${error.message}`, 'error');
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
