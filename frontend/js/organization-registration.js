/**
 * Organization Registration Frontend Handler
 * 
 * PURPOSE: Handles professional organization registration with complete validation
 * FEATURES:
 * - Real-time professional email validation
 * - Phone number formatting and validation
 * - Address and contact information validation
 * - API integration with backend organization service
 * - Professional business requirements enforcement
 */

class OrganizationRegistration {
    constructor() {
        this.form = document.getElementById('organizationRegistrationForm');
        this.submitBtn = document.getElementById('submitBtn');
        this.successMessage = document.getElementById('successMessage');
        
        // Professional email domains that are blocked
        this.blockedEmailDomains = new Set([
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'me.com', 'live.com',
            'yahoo.co.uk', 'googlemail.com', 'hotmail.co.uk'
        ]);

        this.initializeEventListeners();
        this.initializeRealTimeValidation();
        this.initializeLogoUpload();
    }

    initializeEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Auto-generate slug from organization name
        const nameInput = document.getElementById('orgName');
        const slugInput = document.getElementById('orgSlug');
        
        nameInput.addEventListener('input', (e) => {
            const name = e.target.value;
            const slug = this.generateSlug(name);
            slugInput.value = slug;
            this.validateField(slugInput);
        });

        // Phone number formatting
        const phoneInputs = ['orgPhone', 'adminPhone'];
        phoneInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', (e) => this.formatPhoneNumber(e));
            }
        });
    }

    initializeRealTimeValidation() {
        // Add real-time validation to all form inputs
        const inputs = this.form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', (e) => this.validateField(e.target));
            input.addEventListener('input', (e) => {
                if (e.target.classList.contains('error')) {
                    this.validateField(e.target);
                }
            });
        });

        // Special handling for email inputs
        const emailInputs = ['orgEmail', 'adminEmail'];
        emailInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', (e) => this.validateProfessionalEmail(e.target));
                input.addEventListener('blur', (e) => this.validateProfessionalEmail(e.target));
            }
        });
    }

    initializeLogoUpload() {
        const uploadArea = document.getElementById('logoUploadArea');
        const fileInput = document.getElementById('orgLogo');
        const preview = document.getElementById('logoPreview');
        const previewImage = document.getElementById('previewImage');
        const fileName = document.getElementById('fileName');
        const removeBtn = document.getElementById('removeLogo');

        // File size limit (5MB)
        const MAX_FILE_SIZE = 5 * 1024 * 1024;
        
        // Allowed file types
        const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];

        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Drag and drop events
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        // Remove logo
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeLogo();
        });

        // Store references for later use
        this.logoUpload = {
            uploadArea,
            fileInput,
            preview,
            previewImage,
            fileName,
            removeBtn,
            maxSize: MAX_FILE_SIZE,
            allowedTypes: ALLOWED_TYPES
        };
    }

    handleFileUpload(file) {
        const { uploadArea, preview, previewImage, fileName } = this.logoUpload;
        const errorElement = document.getElementById('orgLogo-error');

        // Reset previous states
        uploadArea.classList.remove('error', 'upload-invalid-type', 'upload-too-large');
        this.clearFieldError(uploadArea, errorElement);

        // Validate file type
        if (!this.logoUpload.allowedTypes.includes(file.type)) {
            uploadArea.classList.add('upload-invalid-type');
            this.showFieldError(uploadArea, errorElement, 
                'Invalid file type. Please upload JPG, PNG, or GIF files only.');
            return;
        }

        // Validate file size
        if (file.size > this.logoUpload.maxSize) {
            uploadArea.classList.add('upload-too-large');
            this.showFieldError(uploadArea, errorElement, 
                `File too large. Maximum size is ${this.formatFileSize(this.logoUpload.maxSize)}.`);
            return;
        }

        // Show processing state
        uploadArea.classList.add('upload-processing');

        // Read and preview file
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                previewImage.src = e.target.result;
                fileName.textContent = file.name;
                
                // Hide upload area, show preview
                uploadArea.style.display = 'none';
                preview.style.display = 'block';
                
                // Add success state
                uploadArea.classList.remove('upload-processing');
                uploadArea.classList.add('upload-success');
                
                // Store file for form submission
                this.selectedLogo = file;
                
            } catch (error) {
                console.error('Error processing file:', error);
                this.showFieldError(uploadArea, errorElement, 'Error processing file. Please try again.');
                uploadArea.classList.remove('upload-processing');
            }
        };

        reader.onerror = () => {
            this.showFieldError(uploadArea, errorElement, 'Error reading file. Please try again.');
            uploadArea.classList.remove('upload-processing');
        };

        reader.readAsDataURL(file);
    }

    removeLogo() {
        const { uploadArea, preview, fileInput } = this.logoUpload;
        const errorElement = document.getElementById('orgLogo-error');

        // Reset file input
        fileInput.value = '';
        
        // Hide preview, show upload area
        preview.style.display = 'none';
        uploadArea.style.display = 'flex';
        
        // Reset states
        uploadArea.classList.remove('upload-success', 'error', 'upload-invalid-type', 'upload-too-large');
        this.clearFieldError(uploadArea, errorElement);
        
        // Clear stored file
        this.selectedLogo = null;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    generateSlug(name) {
        return name
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
            .replace(/\s+/g, '-') // Replace spaces with hyphens
            .replace(/-+/g, '-') // Replace multiple hyphens with single
            .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
    }

    formatPhoneNumber(event) {
        let value = event.target.value.replace(/\D/g, ''); // Remove non-digits
        
        if (value.length > 0) {
            // Add + prefix if not present
            if (!event.target.value.startsWith('+')) {
                value = '1' + value; // Assume US if no country code
            }
            
            // Format as +1-XXX-XXX-XXXX for US numbers
            if (value.length <= 11 && value.startsWith('1')) {
                if (value.length > 1) value = '+1-' + value.substring(1);
                if (value.length > 6) value = value.substring(0, 6) + '-' + value.substring(6);
                if (value.length > 10) value = value.substring(0, 10) + '-' + value.substring(10, 14);
            }
        }
        
        event.target.value = value;
    }

    validateProfessionalEmail(input) {
        const email = input.value.trim().toLowerCase();
        const errorElement = document.getElementById(`${input.id}-error`);
        
        if (!email) {
            if (input.required) {
                this.showFieldError(input, errorElement, 'Email address is required');
                return false;
            }
            this.clearFieldError(input, errorElement);
            return true;
        }

        // Basic email format validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showFieldError(input, errorElement, 'Please enter a valid email address');
            return false;
        }

        // Professional email validation
        const domain = email.split('@')[1];
        if (this.blockedEmailDomains.has(domain)) {
            this.showFieldError(input, errorElement, 
                `Personal email provider ${domain} not allowed. Please use a professional business email address.`);
            return false;
        }

        // Success
        this.showFieldSuccess(input, errorElement, 'Professional email address verified');
        return true;
    }

    validateField(input) {
        const errorElement = document.getElementById(`${input.id}-error`);
        const value = input.value.trim();

        // Required field validation
        if (input.required && !value) {
            this.showFieldError(input, errorElement, `${this.getFieldLabel(input)} is required`);
            return false;
        }

        // Skip other validations if empty and not required
        if (!value && !input.required) {
            this.clearFieldError(input, errorElement);
            return true;
        }

        // Length validations
        if (input.minLength && value.length < input.minLength) {
            this.showFieldError(input, errorElement, 
                `${this.getFieldLabel(input)} must be at least ${input.minLength} characters`);
            return false;
        }

        if (input.maxLength && value.length > input.maxLength) {
            this.showFieldError(input, errorElement, 
                `${this.getFieldLabel(input)} must not exceed ${input.maxLength} characters`);
            return false;
        }

        // Pattern validation
        if (input.pattern) {
            const regex = new RegExp(input.pattern);
            if (!regex.test(value)) {
                let message = `${this.getFieldLabel(input)} format is invalid`;
                
                // Custom messages for specific patterns
                if (input.id === 'orgSlug') {
                    message = 'Organization ID can only contain lowercase letters, numbers, and hyphens';
                } else if (input.id === 'orgDomain') {
                    message = 'Please enter a valid domain (e.g., example.com)';
                }
                
                this.showFieldError(input, errorElement, message);
                return false;
            }
        }

        // Phone validation
        if (input.type === 'tel') {
            const phoneRegex = /^\+?[\d\s\-()]{10,}$/;
            if (!phoneRegex.test(value)) {
                this.showFieldError(input, errorElement, 'Please enter a valid phone number');
                return false;
            }
        }

        // Success
        this.clearFieldError(input, errorElement);
        return true;
    }

    getFieldLabel(input) {
        const label = input.closest('.form-group')?.querySelector('.form-label');
        return label ? label.textContent.replace(' *', '') : 'Field';
    }

    showFieldError(input, errorElement, message) {
        input.classList.remove('success');
        input.classList.add('error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    showFieldSuccess(input, errorElement, message = '') {
        input.classList.remove('error');
        input.classList.add('success');
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    clearFieldError(input, errorElement) {
        input.classList.remove('error');
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    validateForm() {
        let isValid = true;
        const inputs = this.form.querySelectorAll('input[required], input[pattern], input[type="email"]');
        
        inputs.forEach(input => {
            const fieldValid = input.type === 'email' ? 
                this.validateProfessionalEmail(input) : 
                this.validateField(input);
            
            if (!fieldValid) {
                isValid = false;
            }
        });

        return isValid;
    }

    async handleSubmit(event) {
        event.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            this.showGeneralError('Please correct the errors above before submitting.');
            return;
        }

        // Show loading state
        this.setSubmitLoading(true);

        try {
            // Collect form data
            const formData = new FormData(this.form);
            
            let response;
            
            // Collect role information
            const primaryRole = formData.get('admin_role');
            const additionalRoles = formData.getAll('additional_roles');
            
            // Validate primary role is selected
            if (!primaryRole) {
                this.showFieldError(
                    document.getElementById('adminRole'),
                    document.getElementById('adminRole-error'),
                    'Please select your primary role in the organization'
                );
                this.setSubmitLoading(false);
                return;
            }
            
            // Combine roles (primary + additional, removing duplicates)
            const allRoles = [primaryRole, ...additionalRoles];
            const uniqueRoles = [...new Set(allRoles)];
            
            // If logo is selected, use FormData for multipart upload
            if (this.selectedLogo) {
                formData.set('logo', this.selectedLogo);
                formData.set('admin_roles', JSON.stringify(uniqueRoles));
                // Submit multipart form data
                response = await this.submitOrganizationWithFile(formData);
            } else {
                // Submit JSON data without file
                const organizationData = {
                    name: formData.get('name'),
                    slug: formData.get('slug'),
                    address: formData.get('address'),
                    contact_phone: formData.get('contact_phone'),
                    contact_email: formData.get('contact_email'),
                    admin_full_name: formData.get('admin_full_name'),
                    admin_email: formData.get('admin_email'),
                    admin_phone: formData.get('admin_phone') || undefined,
                    admin_role: primaryRole,
                    admin_roles: uniqueRoles,
                    description: formData.get('description') || undefined,
                    domain: formData.get('domain') || undefined
                };
                
                // Submit to API
                response = await this.submitOrganization(organizationData);
            }

            if (response.success) {
                this.showSuccess(response.data);
            } else {
                throw new Error(response.error || 'Registration failed');
            }

        } catch (error) {
            console.error('Registration error:', error);
            this.showGeneralError(error.message || 'Registration failed. Please try again.');
        } finally {
            this.setSubmitLoading(false);
        }
    }

    async submitOrganization(data) {
        try {
            const response = await fetch(`${CONFIG.API_URLS.ORGANIZATION}/api/v1/organizations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                // Handle validation errors from backend
                if (response.status === 400 && result.detail) {
                    if (Array.isArray(result.detail)) {
                        // Pydantic validation errors
                        this.handleValidationErrors(result.detail);
                        return { success: false, error: 'Validation errors occurred' };
                    } else {
                        return { success: false, error: result.detail };
                    }
                }
                throw new Error(result.detail || `HTTP error! status: ${response.status}`);
            }

            return { success: true, data: result };

        } catch (error) {
            console.error('API call failed:', error);
            return { success: false, error: error.message };
        }
    }

    async submitOrganizationWithFile(formData) {
        try {
            const response = await fetch(`${CONFIG.API_URLS.ORGANIZATION}/api/v1/organizations/upload`, {
                method: 'POST',
                body: formData // No Content-Type header - browser sets it with boundary for multipart
            });

            const result = await response.json();

            if (!response.ok) {
                // Handle validation errors from backend
                if (response.status === 400 && result.detail) {
                    if (Array.isArray(result.detail)) {
                        // Pydantic validation errors
                        this.handleValidationErrors(result.detail);
                        return { success: false, error: 'Validation errors occurred' };
                    } else {
                        return { success: false, error: result.detail };
                    }
                }
                throw new Error(result.detail || `HTTP error! status: ${response.status}`);
            }

            return { success: true, data: result };

        } catch (error) {
            console.error('API call with file failed:', error);
            return { success: false, error: error.message };
        }
    }

    handleValidationErrors(errors) {
        errors.forEach(error => {
            const fieldPath = error.loc ? error.loc.join('.') : '';
            const fieldName = error.loc ? error.loc[error.loc.length - 1] : '';
            
            // Map backend field names to frontend input IDs
            const fieldMapping = {
                'name': 'orgName',
                'slug': 'orgSlug',
                'address': 'orgAddress',
                'contact_phone': 'orgPhone',
                'contact_email': 'orgEmail',
                'admin_full_name': 'adminName',
                'admin_email': 'adminEmail',
                'admin_phone': 'adminPhone',
                'description': 'orgDescription',
                'domain': 'orgDomain'
            };

            const inputId = fieldMapping[fieldName];
            if (inputId) {
                const input = document.getElementById(inputId);
                const errorElement = document.getElementById(`${inputId}-error`);
                if (input && errorElement) {
                    this.showFieldError(input, errorElement, error.msg || 'Invalid value');
                }
            }
        });
    }

    setSubmitLoading(loading) {
        this.submitBtn.disabled = loading;
        this.submitBtn.classList.toggle('loading', loading);
    }

    showSuccess(data) {
        this.form.style.display = 'none';
        this.successMessage.classList.add('show');
        
        // Scroll to success message
        this.successMessage.scrollIntoView({ behavior: 'smooth' });
    }

    showGeneralError(message) {
        // Create or update general error message
        let errorDiv = document.getElementById('general-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'general-error';
            errorDiv.className = 'form-error show';
            errorDiv.style.marginBottom = '1rem';
            this.submitBtn.parentNode.insertBefore(errorDiv, this.submitBtn);
        }
        
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        
        // Scroll to error
        errorDiv.scrollIntoView({ behavior: 'smooth' });
        
        // Hide error after 10 seconds
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 10000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new OrganizationRegistration();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrganizationRegistration;
}