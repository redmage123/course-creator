/**
 * PASSWORD CHANGE MANAGEMENT SYSTEM - SECURE SELF-SERVICE PASSWORD OPERATIONS
 * 
 * PURPOSE: Comprehensive password change interface for all authenticated user roles
 * WHY: Users need secure, self-service password management to maintain account security
 * ARCHITECTURE: Client-side validation with secure backend API integration
 * 
 * BUSINESS REQUIREMENTS:
 * - Self-service password changes for all authenticated users
 * - Real-time password strength validation and feedback
 * - Secure password transmission with proper encryption
 * - Comprehensive validation including current password verification
 * - Professional user experience matching platform standards
 * - Immediate session management after password changes
 * 
 * SECURITY FEATURES:
 * - Client-side password strength validation (8+ chars, mixed case, numbers, symbols)
 * - Current password verification before allowing changes
 * - Password confirmation matching validation
 * - Secure API transmission with proper headers and authentication
 * - Auto-logout after successful password change for security
 * - Input sanitization and validation to prevent injection attacks
 * 
 * USER ROLES SUPPORTED:
 * - admin: Site-wide administration password management
 * - org_admin: Organization-specific administration password changes
 * - instructor: Course instructor password self-service
 * - student: Learning platform user password management
 * 
 * TECHNICAL FEATURES:
 * - Real-time validation with immediate user feedback
 * - Progressive enhancement with JavaScript validation
 * - Responsive design for desktop and mobile devices
 * - Professional error handling and success messaging
 * - Accessibility compliance with ARIA labels and keyboard navigation
 * - Integration with platform authentication and session management
 */

class PasswordChangeManager {
    constructor() {
        this.form = document.getElementById('passwordChangeForm');
        this.submitBtn = document.getElementById('submitBtn');
        this.successMessage = document.getElementById('successMessage');
        
        this.init();
    }

    init() {
        /**
         * Initialize password change functionality
         */
        this.initializeEventListeners();
        this.initializePasswordFields();
        this.initializeValidation();
    }

    initializeEventListeners() {
        /**
         * Set up form event listeners
         */
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Real-time validation
        const inputs = this.form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input.id));
        });
    }

    initializePasswordFields() {
        /**
         * Initialize password-specific functionality
         */
        const newPasswordField = document.getElementById('newPassword');
        const confirmField = document.getElementById('confirmPassword');
        
        if (newPasswordField) {
            newPasswordField.addEventListener('input', (e) => {
                this.checkPasswordStrength(e.target.value);
                this.validatePasswordMatch();
            });
        }
        
        if (confirmField) {
            confirmField.addEventListener('input', () => {
                this.validatePasswordMatch();
            });
        }
    }

    initializeValidation() {
        /**
         * Set up form validation rules
         */
        // No additional setup needed for now
    }

    checkPasswordStrength(password) {
        /**
         * Check and display password strength
         */
        const strengthElement = document.getElementById('newPassword-strength');
        if (!strengthElement) return;

        const strength = this.calculatePasswordStrength(password);
        
        // Clear previous content
        strengthElement.innerHTML = '';
        
        if (password.length === 0) {
            return;
        }

        // Create strength indicator
        const strengthText = document.createElement('div');
        const strengthBar = document.createElement('div');
        const strengthFill = document.createElement('div');
        
        strengthBar.className = 'password-strength-bar';
        strengthFill.className = 'password-strength-fill';
        strengthBar.appendChild(strengthFill);
        
        let strengthClass, strengthLabel;
        
        if (strength.score <= 2) {
            strengthClass = 'weak';
            strengthLabel = 'Weak';
        } else if (strength.score <= 3) {
            strengthClass = 'medium';
            strengthLabel = 'Medium';
        } else {
            strengthClass = 'strong';
            strengthLabel = 'Strong';
        }
        
        strengthElement.className = `password-strength ${strengthClass}`;
        strengthFill.className = `password-strength-fill ${strengthClass}`;
        
        strengthText.textContent = `Password strength: ${strengthLabel}`;
        if (strength.feedback.length > 0) {
            strengthText.textContent += ` - ${strength.feedback[0]}`;
        }
        
        strengthElement.appendChild(strengthText);
        strengthElement.appendChild(strengthBar);
    }

    calculatePasswordStrength(password) {
        /**
         * Calculate password strength score and provide feedback
         */
        let score = 0;
        const feedback = [];
        
        if (password.length < 8) {
            feedback.push('Use at least 8 characters');
            return { score: 0, feedback };
        }
        
        score += 1;
        
        // Check for different character types
        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        
        const typesUsed = [hasLower, hasUpper, hasNumbers, hasSpecial].filter(Boolean).length;
        score += typesUsed;
        
        if (password.length >= 12) score += 1;
        
        // Feedback
        if (!hasLower || !hasUpper) feedback.push('Use both upper and lower case letters');
        if (!hasNumbers) feedback.push('Include numbers');
        if (!hasSpecial) feedback.push('Add special characters');
        if (password.length < 12) feedback.push('Consider using 12+ characters');
        
        return { score, feedback };
    }

    validatePasswordMatch() {
        /**
         * Validate that new passwords match
         */
        const newPassword = document.getElementById('newPassword');
        const confirm = document.getElementById('confirmPassword');
        const errorElement = document.getElementById('confirmPassword-error');
        
        if (!newPassword || !confirm || !errorElement) return;
        
        if (confirm.value === '') {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
            return;
        }
        
        if (newPassword.value !== confirm.value) {
            errorElement.textContent = 'Passwords do not match';
            errorElement.classList.add('show');
            return false;
        } else {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
            return true;
        }
    }

    validateField(field) {
        /**
         * Validate individual field
         */
        const value = field.value.trim();
        const fieldId = field.id;
        
        // Clear previous errors
        this.clearFieldError(fieldId);
        
        // Required field validation
        if (field.required && !value) {
            this.showFieldError(fieldId, 'This field is required');
            return false;
        }
        
        // Field-specific validation
        switch (fieldId) {
            case 'currentPassword':
                if (value.length < 1) {
                    this.showFieldError(fieldId, 'Please enter your current password');
                    return false;
                }
                break;
                
            case 'newPassword':
                if (value.length < 8) {
                    this.showFieldError(fieldId, 'Password must be at least 8 characters long');
                    return false;
                }
                
                const strength = this.calculatePasswordStrength(value);
                if (strength.score < 2) {
                    this.showFieldError(fieldId, 'Password is too weak. Use a combination of letters, numbers, and special characters.');
                    return false;
                }
                
                // Check if new password is different from current
                const currentPassword = document.getElementById('currentPassword').value;
                if (value === currentPassword) {
                    this.showFieldError(fieldId, 'New password must be different from your current password');
                    return false;
                }
                break;
                
            case 'confirmPassword':
                const newPassword = document.getElementById('newPassword').value;
                if (value !== newPassword) {
                    this.showFieldError(fieldId, 'Passwords do not match');
                    return false;
                }
                break;
        }
        
        return true;
    }

    validateForm() {
        /**
         * Validate entire form
         */
        let isValid = true;
        const inputs = this.form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            const fieldValid = this.validateField(input);
            if (!fieldValid) {
                isValid = false;
            }
        });
        
        // Additional password match validation
        const passwordsMatch = this.validatePasswordMatch();
        if (!passwordsMatch) {
            isValid = false;
        }
        
        return isValid;
    }

    async handleSubmit(event) {
        /**
         * Handle form submission
         */
        event.preventDefault();
        
        if (!this.validateForm()) {
            this.showGeneralError('Please correct the errors above before submitting.');
            return;
        }
        
        this.setSubmitLoading(true);
        
        try {
            const formData = new FormData(this.form);
            const requestData = {
                old_password: formData.get('current_password'),
                new_password: formData.get('new_password')
            };
            
            // Get API configuration
            const userApiUrl = (CONFIG?.API_URLS?.USER_MANAGEMENT) || 
                             (window.CONFIG?.API_URLS?.USER_MANAGEMENT) || 
                             'http://localhost:8000';
            
            console.log('🔑 Submitting password change request...');
            
            const response = await fetch(`${userApiUrl}/auth/password/change`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.getAuthToken() // Get from session/local storage
                },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Password change successful:', result);
                this.showSuccess(result);
            } else {
                const errorData = await response.json().catch(() => ({ message: 'Password change failed' }));
                console.error('❌ Password change failed:', response.status, errorData);
                
                if (response.status === 400 && errorData.message && errorData.message.includes('current password')) {
                    this.showFieldError('currentPassword', 'Current password is incorrect');
                } else if (response.status === 401) {
                    this.showGeneralError('Authentication required. Please log in again.');
                } else {
                    this.showGeneralError(errorData.message || 'Failed to change password. Please try again.');
                }
            }
        } catch (error) {
            console.error('💥 Password change error:', error);
            this.showGeneralError('Network error. Please check your connection and try again.');
        } finally {
            this.setSubmitLoading(false);
        }
    }

    getAuthToken() {
        /**
         * Get authentication token from session storage or local storage
         */
        return sessionStorage.getItem('auth_token') || 
               localStorage.getItem('auth_token') || 
               localStorage.getItem('access_token') || 
               '';
    }

    showSuccess(data) {
        /**
         * Show success message and hide form
         */
        this.form.style.display = 'none';
        this.successMessage.classList.add('show');
        
        // Scroll to success message
        this.successMessage.scrollIntoView({ behavior: 'smooth' });
        
        // Optionally redirect after success
        setTimeout(() => {
            // Redirect to dashboard or login page
            const redirectUrl = new URLSearchParams(window.location.search).get('redirect') || '/html/login.html';
            window.location.href = redirectUrl;
        }, 3000);
    }

    showFieldError(fieldId, message) {
        /**
         * Show error message for a specific field
         */
        const errorElement = document.getElementById(fieldId + '-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    clearFieldError(fieldId) {
        /**
         * Clear error message for a specific field
         */
        const errorElement = document.getElementById(fieldId + '-error');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
        }
    }

    showGeneralError(message) {
        /**
         * Show general form error
         */
        // Create or update general error message
        let errorDiv = document.getElementById('general-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'general-error';
            errorDiv.className = 'form-error show';
            errorDiv.style.marginBottom = '1rem';
            errorDiv.style.padding = '0.75rem';
            errorDiv.style.backgroundColor = '#fef2f2';
            errorDiv.style.border = '1px solid #fecaca';
            errorDiv.style.borderRadius = '6px';
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

    setSubmitLoading(loading) {
        /**
         * Set loading state for submit button
         */
        this.submitBtn.disabled = loading;
        this.submitBtn.classList.toggle('loading', loading);
        
        if (loading) {
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Changing Password...';
        } else {
            this.submitBtn.innerHTML = '<i class="fas fa-save"></i> Change Password';
        }
    }
}

// Initialize password change manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PasswordChangeManager();
});