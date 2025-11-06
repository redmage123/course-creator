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
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
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

    /**
     * INITIALIZE EVENT LISTENERS COMPONENT
     * PURPOSE: Initialize event listeners component
     * WHY: Proper initialization ensures component reliability and correct state
     */
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
            
            // Show generated ID preview
            this.updateSlugPreview(slug);
        });

        // Phone number formatting
        const phoneInputs = ['orgPhone', 'adminPhone'];
        phoneInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', (e) => this.formatPhoneNumber(e));
            }
        });
        
        // Initialize enhanced country dropdowns with keyboard navigation
        this.initializeCountryDropdowns();
        
        // Initialize password functionality
        this.initializePasswordFields();
        
        // Set default country codes to US (not Canada)
        const orgCountrySelect = document.getElementById('orgPhoneCountry');
        const adminCountrySelect = document.getElementById('adminPhoneCountry');
        if (orgCountrySelect) {
            // Select United States specifically, not just +1 (which would select Canada first)
            const usOption = orgCountrySelect.querySelector('option[data-country="US"]');
            if (usOption) {
                orgCountrySelect.value = usOption.value;
                console.log('Set organization country to US:', usOption.value);
            } else {
                console.warn('US option not found in organization country dropdown');
            }
        }
        if (adminCountrySelect) {
            // Select United States specifically, not just +1 (which would select Canada first)
            const usOption = adminCountrySelect.querySelector('option[data-country="US"]');
            if (usOption) {
                adminCountrySelect.value = usOption.value;
                console.log('Set admin country to US:', usOption.value);
            } else {
                console.warn('US option not found in admin country dropdown');
            }
        }
    }

    /**
     * INITIALIZE COUNTRY DROPDOWNS COMPONENT
     * PURPOSE: Initialize country dropdowns component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    initializeCountryDropdowns() {
        /**
         * Initialize enhanced country dropdowns with keyboard navigation
         * 
         * PURPOSE: Provide accessible keyboard navigation for country selection
         * WHY: Improves user experience and accessibility for users who prefer keyboard navigation
         * FEATURES: 
         * - Type to search country names
         * - Arrow key navigation
         * - Enter to select
         * - Escape to close suggestions
         */
        const countrySelects = ['orgPhoneCountry', 'adminPhoneCountry'];
        
        countrySelects.forEach(selectId => {
            const selectElement = document.getElementById(selectId);
            if (selectElement) {
                console.log(`✅ Enhancing country select: ${selectId}`);
                this.enhanceCountrySelect(selectElement);
                console.log(`✅ Country select enhanced with keyboard navigation: ${selectId}`);
            } else {
                console.warn(`❌ Country select element not found: ${selectId}`);
            }
        });
    }

    /**
     * EXECUTE ENHANCECOUNTRYSELECT OPERATION
     * PURPOSE: Execute enhanceCountrySelect operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} selectElement - Selectelement parameter
     */
    enhanceCountrySelect(selectElement) {
        /**
         * Enhance a country select element with keyboard navigation and search
         * 
         * PURPOSE: Convert standard select to searchable dropdown with keyboard support
         * WHY: Standard selects have limited keyboard navigation for long lists
         */
        // Store original options
        const originalOptions = Array.from(selectElement.options).slice(1); // Skip "Select Country"
        
        // Add keyboard search functionality
        let searchString = '';
        let searchTimeout;
        
        selectElement.addEventListener('keydown', (e) => {
            console.log(`Country select keydown: ${e.key}`);
            // Handle different key presses
            switch(e.key) {
                case 'ArrowDown':
                case 'ArrowUp':
                    // Let browser handle arrow navigation
                    break;
                    
                case 'Enter':
                    // Prevent form submission when selecting country
                    e.preventDefault();
                    break;
                    
                case 'Escape':
                    // Clear search and close dropdown
                    selectElement._searchString = '';
                    this.hideCountrySearchFeedback(selectElement);
                    selectElement.blur();
                    break;
                    
                default:
                    // Handle typing for search
                    if (e.key.length === 1 && /[a-zA-Z\s]/.test(e.key)) {
                        e.preventDefault(); // Prevent default select behavior
                        this.handleCountrySearch(e.key, selectElement, originalOptions);
                    }
            }
        });

        // Add visual feedback for keyboard navigation
        selectElement.addEventListener('focus', () => {
            selectElement.classList.add('keyboard-focused');
        });

        selectElement.addEventListener('blur', () => {
            selectElement.classList.remove('keyboard-focused');
        });

        // Store search state
        selectElement._searchString = '';
        selectElement._originalOptions = originalOptions;
    }

    /**
     * HANDLE COUNTRY SEARCH EVENT
     * PURPOSE: Handle country search event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {*} key - Key parameter
     * @param {*} selectElement - Selectelement parameter
     * @param {*} originalOptions - Originaloptions parameter
     */
    handleCountrySearch(key, selectElement, originalOptions) {
        /**
         * Handle typing in country dropdown for type-ahead functionality
         * 
         * PURPOSE: Jump to first country that starts with typed letters (standard dropdown behavior)
         * WHY: Provides intuitive navigation - typing 'U' jumps to first U country (Uganda, Ukraine, etc.)
         */
        // Clear previous search timeout
        if (selectElement._searchTimeout) {
            clearTimeout(selectElement._searchTimeout);
        }

        // Add to search string
        selectElement._searchString = (selectElement._searchString || '') + key.toLowerCase();

        // Find countries that START WITH the typed letters (not contains)
        const matchingOptions = originalOptions.filter(option => {
            // Extract country name from text like "🇺🇸 United States (+1)"
            const countryText = option.textContent.toLowerCase();
            // Get just the country name part (after the flag emoji and space)
            const countryName = countryText.substring(countryText.indexOf(' ') + 1);
            
            // Check if country name starts with search string
            return countryName.startsWith(selectElement._searchString);
        });

        // Select first match if any
        if (matchingOptions.length > 0) {
            const firstMatch = matchingOptions[0];
            selectElement.value = firstMatch.value;
            
            // Highlight the selected option visually
            this.highlightSelectedCountry(selectElement);
            
            // Show search feedback with "starts with" indicator
            this.showCountrySearchFeedback(selectElement, selectElement._searchString, matchingOptions.length, 'starts_with');
        } else {
            // No matches found - show feedback
            this.showCountrySearchFeedback(selectElement, selectElement._searchString, 0, 'no_match');
        }

        // Clear search string after delay
        selectElement._searchTimeout = setTimeout(() => {
            selectElement._searchString = '';
            this.hideCountrySearchFeedback(selectElement);
        }, 1500);
    }

    /**
     * EXECUTE HIGHLIGHTSELECTEDCOUNTRY OPERATION
     * PURPOSE: Execute highlightSelectedCountry operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} selectElement - Selectelement parameter
     */
    highlightSelectedCountry(selectElement) {
        /**
         * Visual feedback when country is selected via keyboard
         */
        selectElement.style.backgroundColor = '#e6f3ff';
        setTimeout(() => {
            selectElement.style.backgroundColor = '';
        }, 200);
    }

    /**
     * DISPLAY COUNTRY SEARCH FEEDBACK INTERFACE
     * PURPOSE: Display country search feedback interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} selectElement - Selectelement parameter
     * @param {*} searchString - Searchstring parameter
     * @param {*} matchCount - Matchcount parameter
     * @param {*} searchType - Searchtype parameter
     */
    showCountrySearchFeedback(selectElement, searchString, matchCount, searchType = 'starts_with') {
        /**
         * Show search feedback to user with enhanced messaging
         */
        // Find or create feedback element
        let feedbackElement = selectElement.parentNode.querySelector('.country-search-feedback');
        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.className = 'country-search-feedback';
            feedbackElement.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                background: #333;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1000;
                white-space: nowrap;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            `;
            selectElement.parentNode.style.position = 'relative';
            selectElement.parentNode.appendChild(feedbackElement);
        }
        
        // Set message based on search results
        let message, backgroundColor;
        if (searchType === 'no_match') {
            message = `No countries start with "${searchString}"`;
            backgroundColor = '#d73502'; // Red for no matches
        } else if (matchCount === 1) {
            message = `Found: "${searchString}" (1 match)`;
            backgroundColor = '#28a745'; // Green for single match
        } else {
            message = `Type ahead: "${searchString}" (${matchCount} countries)`;
            backgroundColor = '#007bff'; // Blue for multiple matches
        }
        
        feedbackElement.textContent = message;
        feedbackElement.style.backgroundColor = backgroundColor;
        feedbackElement.style.display = 'block';
    }

    /**
     * HIDE COUNTRY SEARCH FEEDBACK INTERFACE
     * PURPOSE: Hide country search feedback interface
     * WHY: Improves UX by managing interface visibility and state
     *
     * @param {*} selectElement - Selectelement parameter
     */
    hideCountrySearchFeedback(selectElement) {
        /**
         * Hide search feedback
         */
        const feedbackElement = selectElement.parentNode.querySelector('.country-search-feedback');
        if (feedbackElement) {
            feedbackElement.style.display = 'none';
        }
    }

    /**
     * INITIALIZE PASSWORD FIELDS COMPONENT
     * PURPOSE: Initialize password fields component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    initializePasswordFields() {
        /**
         * Initialize password functionality including strength checking and toggle visibility
         * 
         * PURPOSE: Provide secure password input with user feedback
         * WHY: Help users create strong passwords and improve UX with visibility toggle
         */
        const passwordField = document.getElementById('adminPassword');
        const confirmField = document.getElementById('adminPasswordConfirm');
        
        if (passwordField) {
            // Add strength checking
            passwordField.addEventListener('input', (e) => {
                this.checkPasswordStrength(e.target.value);
                this.validatePasswordMatch();
            });
        }
        
        if (confirmField) {
            // Add confirmation checking
            confirmField.addEventListener('input', () => {
                this.validatePasswordMatch();
            });
        }
    }

    /**
     * EXECUTE CHECKPASSWORDSTRENGTH OPERATION
     * PURPOSE: Execute checkPasswordStrength operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} password - Password parameter
     */
    checkPasswordStrength(password) {
        /**
         * Check and display password strength
         */
        const strengthElement = document.getElementById('adminPassword-strength');
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

    /**
     * EXECUTE CALCULATEPASSWORDSTRENGTH OPERATION
     * PURPOSE: Execute calculatePasswordStrength operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} password - Password parameter
     *
     * @returns {number} Calculated value
     */
    calculatePasswordStrength(password) {
        /**
         * Calculate password strength score and provide feedback matching backend requirements
         */
        let score = 0;
        const feedback = [];
        
        if (password.length < 8) {
            feedback.push('Must be at least 8 characters');
            return { score: 0, feedback };
        }
        
        score += 1;
        
        // Check for different character types - all required by backend
        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        
        // All character types must be present for backend validation
        if (!hasUpper) feedback.push('Must contain uppercase letter');
        if (!hasLower) feedback.push('Must contain lowercase letter'); 
        if (!hasNumbers) feedback.push('Must contain digit');
        if (!hasSpecial) feedback.push('Must contain special character');
        
        // Score based on meeting all requirements
        if (hasLower && hasUpper && hasNumbers && hasSpecial) {
            score = 3; // Strong - meets all requirements
        } else if ([hasLower, hasUpper, hasNumbers, hasSpecial].filter(Boolean).length >= 3) {
            score = 2; // Medium - missing one requirement
        } else {
            score = 1; // Weak - missing multiple requirements
        }
        
        if (password.length >= 12) {
            score = Math.min(score + 1, 3);
            if (feedback.length === 0) {
                feedback.push('Excellent! Consider using 12+ characters for extra security');
            }
        }
        
        return { score, feedback };
    }

    /**
     * VALIDATE PASSWORD MATCH INPUT
     * PURPOSE: Validate password match input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    validatePasswordMatch() {
        /**
         * Validate that passwords match
         */
        const password = document.getElementById('adminPassword');
        const confirm = document.getElementById('adminPasswordConfirm');
        const errorElement = document.getElementById('adminPasswordConfirm-error');
        
        if (!password || !confirm || !errorElement) return;
        
        if (confirm.value === '') {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
            return;
        }
        
        if (password.value !== confirm.value) {
            errorElement.textContent = 'Passwords do not match';
            errorElement.classList.add('show');
            return false;
        } else {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
            return true;
        }
    }

    /**
     * INITIALIZE REAL TIME VALIDATION COMPONENT
     * PURPOSE: Initialize real time validation component
     * WHY: Proper initialization ensures component reliability and correct state
     */
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

    /**
     * INITIALIZE LOGO UPLOAD COMPONENT
     * PURPOSE: Initialize logo upload component
     * WHY: Proper initialization ensures component reliability and correct state
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * HANDLE FILE UPLOAD EVENT
     * PURPOSE: Handle file upload event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {*} file - File parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * REMOVE LOGO FROM SYSTEM
     * PURPOSE: Remove logo from system
     * WHY: Manages resource cleanup and data consistency
     */
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

    /**
     * FORMAT FILE SIZE FOR DISPLAY
     * PURPOSE: Format file size for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} bytes - Bytes parameter
     *
     * @returns {string} Formatted string
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * EXECUTE GENERATESLUG OPERATION
     * PURPOSE: Execute generateSlug operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} name - Name value
     *
     * @returns {string|Object} Generated content
     */
    generateSlug(name) {
        return name
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
            .replace(/\s+/g, '-') // Replace spaces with hyphens
            .replace(/-+/g, '-') // Replace multiple hyphens with single
            .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
    }

    /**
     * UPDATE SLUG PREVIEW STATE
     * PURPOSE: Update slug preview state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} slug - Slug parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updateSlugPreview(slug) {
        const preview = document.getElementById('slug-preview');
        const previewText = document.getElementById('slug-preview-text');
        
        if (slug && slug.length >= 2) {
            previewText.textContent = slug;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }

    /**
     * FORMAT PHONE NUMBER FOR DISPLAY
     * PURPOSE: Format phone number for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {Event} event - Event object
     *
     * @returns {string} Formatted string
     */
    formatPhoneNumber(event) {
        // Only keep digits, hyphens, spaces, and parentheses
        let value = event.target.value.replace(/[^\d\-\(\)\s]/g, '');
        
        // Get the country code from the corresponding select
        const inputId = event.target.id;
        const countrySelectId = inputId.replace('Phone', 'PhoneCountry');
        const countrySelect = document.getElementById(countrySelectId);
        const countryCode = countrySelect ? countrySelect.value : '+1';
        
        // Remove any formatting and get digits only
        const digitsOnly = value.replace(/\D/g, '');
        
        // Format based on country code
        if (countryCode === '+1') {
            // US/Canada formatting
            if (digitsOnly.length === 10) {
                // Format as XXX-XXX-XXXX
                const formatted = digitsOnly.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
                event.target.value = formatted;
            } else if (digitsOnly.length === 7) {
                // Format as XXX-XXXX for 7-digit numbers
                const formatted = digitsOnly.replace(/(\d{3})(\d{4})/, '$1-$2');
                event.target.value = formatted;
            } else {
                // Don't format if not the right length
                event.target.value = value;
            }
        } else {
            // For other countries, just clean the input but don't auto-format
            // Different countries have different formats
            event.target.value = value;
        }
    }

    /**
     * VALIDATE PROFESSIONAL EMAIL INPUT
     * PURPOSE: Validate professional email input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @param {*} input - Input parameter
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    validateProfessionalEmail(input) {
        const email = input.value.trim().toLowerCase();
        const errorElement = document.getElementById(`${input.id}-error`);
        
        // Debug logging
        console.log(`🔍 Validating email: ${email} (field: ${input.id})`);
        
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
        console.log(`📧 Email domain: ${domain}, blocked domains:`, this.blockedEmailDomains);
        
        if (this.blockedEmailDomains.has(domain)) {
            console.log(`❌ Domain ${domain} is blocked`);
            this.showFieldError(input, errorElement, 
                `Personal email provider ${domain} not allowed. Please use a professional business email address.`);
            return false;
        }

        // Success
        console.log(`✅ Email ${email} validated successfully`);
        this.showFieldSuccess(input, errorElement, 'Professional email address verified');
        return true;
    }

    /**
     * VALIDATE FIELD INPUT
     * PURPOSE: Validate field input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @param {*} input - Input parameter
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

        if (input.maxLength && input.maxLength > 0 && value.length > input.maxLength) {
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
                    message = 'Please enter a valid URL (e.g., https://example.com or example.com)';
                } else if (input.id === 'adminUsername') {
                    message = 'Administrator ID can only contain letters, numbers, underscores, and hyphens';
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

        // URL validation
        if (input.type === 'url') {
            // Allow URLs with or without protocol
            const urlWithProtocol = /^https?:\/\/[^\s$.?#].[^\s]*$/i.test(value);
            const urlWithoutProtocol = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}(\/[^\s]*)?$/i.test(value);
            
            // Also check for common invalid patterns
            const startsWithProtocolOnly = /^https?:\/\/\s*$/i.test(value);
            const hasSpaces = /\s/.test(value.trim());
            
            if (startsWithProtocolOnly) {
                this.showFieldError(input, errorElement, 'Please enter a complete URL after the protocol');
                return false;
            }
            
            if (hasSpaces) {
                this.showFieldError(input, errorElement, 'URL cannot contain spaces');
                return false;
            }
            
            if (!urlWithProtocol && !urlWithoutProtocol) {
                this.showFieldError(input, errorElement, 'Please enter a valid URL (e.g., https://example.com or example.com)');
                return false;
            }
        }

        // Success
        this.clearFieldError(input, errorElement);
        return true;
    }

    /**
     * RETRIEVE FIELD LABEL INFORMATION
     * PURPOSE: Retrieve field label information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} input - Input parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getFieldLabel(input) {
        const label = input.closest('.form-group')?.querySelector('.form-label');
        return label ? label.textContent.replace(' *', '') : 'Field';
    }

    /**
     * DISPLAY FIELD ERROR INTERFACE
     * PURPOSE: Display field error interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} input - Input parameter
     * @param {*} errorElement - Errorelement parameter
     * @param {*} message - Message parameter
     */
    showFieldError(input, errorElement, message) {
        input.classList.remove('success');
        input.classList.add('error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    /**
     * DISPLAY FIELD SUCCESS INTERFACE
     * PURPOSE: Display field success interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} input - Input parameter
     * @param {*} errorElement - Errorelement parameter
     * @param {*} message - Message parameter
     */
    showFieldSuccess(input, errorElement, message = '') {
        input.classList.remove('error');
        input.classList.add('success');
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    /**
     * EXECUTE CLEARFIELDERROR OPERATION
     * PURPOSE: Execute clearFieldError operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} input - Input parameter
     * @param {*} errorElement - Errorelement parameter
     */
    clearFieldError(input, errorElement) {
        input.classList.remove('error');
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    /**
     * VALIDATE FORM INPUT
     * PURPOSE: Validate form input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    validateForm() {
        let isValid = true;
        const inputs = this.form.querySelectorAll('input[required], input[pattern], input[type="email"]');
        
        console.log(`🔍 Validating ${inputs.length} form fields`);
        
        inputs.forEach(input => {
            const fieldValid = input.type === 'email' ? 
                this.validateProfessionalEmail(input) : 
                this.validateField(input);
            
            if (!fieldValid) {
                console.log(`❌ Field validation failed: ${input.id} (${input.name}) - value: "${input.value}"`);
                isValid = false;
            } else {
                console.log(`✅ Field validation passed: ${input.id}`);
            }
        });

        // Additional password validation
        const passwordValid = this.validatePasswords();
        if (!passwordValid) {
            console.log(`❌ Password validation failed`);
            isValid = false;
        } else {
            console.log(`✅ Password validation passed`);
        }

        console.log(`📋 Overall form validation: ${isValid ? 'PASSED' : 'FAILED'}`);
        return isValid;
    }

    /**
     * VALIDATE PASSWORDS INPUT
     * PURPOSE: Validate passwords input
     * WHY: Ensures data integrity and prevents invalid states
     *
     * @returns {boolean} True if validation passes, false otherwise
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    validatePasswords() {
        /**
         * Comprehensive password validation for admin user
         */
        const passwordField = document.getElementById('adminPassword');
        const confirmField = document.getElementById('adminPasswordConfirm');
        
        if (!passwordField || !confirmField) return false;
        
        const password = passwordField.value;
        const confirm = confirmField.value;
        
        // Check password strength - must meet backend requirements
        const strength = this.calculatePasswordStrength(password);
        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        
        if (password.length < 8) {
            this.showFieldError('adminPassword', 'Password must be at least 8 characters long');
            return false;
        }
        
        if (!hasUpper) {
            this.showFieldError('adminPassword', 'Password must contain at least one uppercase letter');
            return false;
        }
        
        if (!hasLower) {
            this.showFieldError('adminPassword', 'Password must contain at least one lowercase letter');
            return false;
        }
        
        if (!hasNumbers) {
            this.showFieldError('adminPassword', 'Password must contain at least one digit');
            return false;
        }
        
        if (!hasSpecial) {
            this.showFieldError('adminPassword', 'Password must contain at least one special character');
            return false;
        }
        
        // Check passwords match
        if (password !== confirm) {
            this.showFieldError('adminPasswordConfirm', 'Passwords do not match');
            return false;
        }
        
        // Clear any existing errors
        this.clearFieldError('adminPassword');
        this.clearFieldError('adminPasswordConfirm');
        
        return true;
    }

    /**
     * DISPLAY FIELD ERROR INTERFACE
     * PURPOSE: Display field error interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} fieldId - Fieldid parameter
     * @param {*} message - Message parameter
     */
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

    /**
     * EXECUTE CLEARFIELDERROR OPERATION
     * PURPOSE: Execute clearFieldError operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} fieldId - Fieldid parameter
     */
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

    /**
     * HANDLE SUBMIT EVENT
     * PURPOSE: Handle submit event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {Event} event - Event object
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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
            
            // Combine country codes with phone numbers
            const orgCountryCode = document.getElementById('orgPhoneCountry').value;
            const orgPhoneNumber = document.getElementById('orgPhone').value;
            const adminCountryCode = document.getElementById('adminPhoneCountry').value;
            const adminPhoneNumber = document.getElementById('adminPhone').value;
            
            // Set complete phone numbers
            if (orgCountryCode && orgPhoneNumber) {
                formData.set('contact_phone', `${orgCountryCode}${orgPhoneNumber.replace(/\D/g, '')}`);
            }
            if (adminCountryCode && adminPhoneNumber) {
                formData.set('admin_phone', `${adminCountryCode}${adminPhoneNumber.replace(/\D/g, '')}`);
            }
            
            // Normalize domain (remove protocol, keep just domain name for API)
            const domain = formData.get('domain');
            if (domain) {
                // Extract just the domain name without protocol
                const domainOnly = domain.replace(/^https?:\/\//, '').split('/')[0];
                formData.set('domain', domainOnly);
            }
            
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
                    contact_phone: formData.get('contact_phone'),
                    contact_email: formData.get('contact_email'),
                    // Subdivided address fields
                    street_address: formData.get('street_address') || undefined,
                    city: formData.get('city') || undefined,
                    state_province: formData.get('state_province') || undefined,
                    postal_code: formData.get('postal_code') || undefined,
                    country: formData.get('country') || 'US',
                    // Legacy address field (optional)
                    address: formData.get('address') || undefined,
                    admin_full_name: formData.get('admin_full_name'),
                    admin_username: formData.get('admin_username'),
                    admin_email: formData.get('admin_email'),
                    admin_phone: formData.get('admin_phone') || undefined,
                    admin_role: primaryRole,
                    admin_roles: uniqueRoles,
                    admin_password: formData.get('admin_password'),
                    description: formData.get('description') || undefined,
                    domain: formData.get('domain') || undefined
                };
                
                // Submit to API
                response = await this.submitOrganization(organizationData);
            }

            if (response.success) {
                console.log('🎉 Registration successful!', response.data);
                console.log('🔍 About to call showSuccess...');
                this.showSuccess(response.data);
                console.log('✅ showSuccess called, form should be hidden and success message shown');
                return; // Prevent any further execution
            } else {
                console.log('❌ Registration failed:', response.error);
                throw new Error(response.error || 'Registration failed');
            }

        } catch (error) {
            console.error('Registration error:', error);
            console.log('Error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            this.showGeneralError(error.message || 'Registration failed. Please try again.');
        } finally {
            this.setSubmitLoading(false);
        }
    }

    /**
     * EXECUTE SUBMITORGANIZATION OPERATION
     * PURPOSE: Execute submitOrganization operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {Object} data - Data object
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async submitOrganization(data) {
        try {
            // Use CONFIG system for proper protocol and URL handling
            const orgApiUrl = window.CONFIG?.API_URLS.ORGANIZATION;
            console.log('Making API request to:', `${orgApiUrl}/api/v1/organizations`);
            console.log('window.CONFIG?.PROTOCOL:', window.CONFIG?.PROTOCOL);
            console.log('window.CONFIG?.HOST:', window.CONFIG?.HOST);
            console.log('Full organization API URL:', orgApiUrl);
            const response = await fetch(`${orgApiUrl}/api/v1/organizations`, {
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

    /**
     * EXECUTE SUBMITORGANIZATIONWITHFILE OPERATION
     * PURPOSE: Execute submitOrganizationWithFile operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} formData - Formdata parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async submitOrganizationWithFile(formData) {
        try {
            // Use current hostname for API calls instead of hardcoded localhost
            const currentHost = window.location.hostname;
            const orgApiUrl = `https://${currentHost}:8008`;
            console.log('Making multipart API request to:', `${orgApiUrl}/api/v1/organizations/upload`);
            const response = await fetch(`${orgApiUrl}/api/v1/organizations/upload`, {
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

    /**
     * HANDLE VALIDATION ERRORS EVENT
     * PURPOSE: Handle validation errors event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {*} errors - Errors parameter
     */
    handleValidationErrors(errors) {
        errors.forEach(error => {
            const fieldPath = error.loc ? error.loc.join('.') : '';
            const fieldName = error.loc ? error.loc[error.loc.length - 1] : '';
            
            // Map backend field names to frontend input IDs
            const fieldMapping = {
                'name': 'orgName',
                'slug': 'orgSlug',
                'street_address': 'orgStreetAddress',
                'city': 'orgCity',
                'state_province': 'orgStateProvince',
                'postal_code': 'orgPostalCode',
                'country': 'orgCountry',
                'contact_phone': 'orgPhone',
                'contact_email': 'orgEmail',
                'admin_full_name': 'adminName',
                'admin_username': 'adminUsername',
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

    /**
     * SET SUBMIT LOADING VALUE
     * PURPOSE: Set submit loading value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {*} loading - Loading parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    setSubmitLoading(loading) {
        this.submitBtn.disabled = loading;
        this.submitBtn.classList.toggle('loading', loading);
    }

    /**
     * DISPLAY SUCCESS INTERFACE
     * PURPOSE: Display success interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {Object} data - Data object
     */
    showSuccess(data) {
        console.log('🎉 Showing success message with data:', data);
        
        // Debug: Check if elements exist
        console.log('🔍 Form element:', this.form);
        console.log('🔍 Success message element:', this.successMessage);
        
        // Hide the form completely
        if (this.form) {
            this.form.style.display = 'none';
            console.log('✅ Form hidden');
        } else {
            console.error('❌ Form element not found!');
        }
        
        // Show the success message
        if (this.successMessage) {
            this.successMessage.classList.add('show');
            console.log('✅ Success message show class added');
        } else {
            console.error('❌ Success message element not found!');
        }
        
        // Update success message with organization and admin details
        const messageElement = this.successMessage.querySelector('.success-content');
        if (messageElement) {
            const orgName = data.name || 'Your organization';
            const adminEmail = document.getElementById('adminEmail').value;
            
            messageElement.innerHTML = `
                <h2><i class="fas fa-check-circle" style="color: #10b981; margin-right: 0.5rem;"></i>Registration Successful!</h2>
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                    <p style="font-size: 1.1rem; margin-bottom: 1rem;"><strong>${orgName}</strong> has been successfully registered with the Course Creator Platform!</p>
                    
                    <div class="admin-info" style="margin-bottom: 1.5rem;">
                        <h3><i class="fas fa-user-shield" style="margin-right: 0.5rem;"></i>Administrator Account Created</h3>
                        <p>✅ Administrator account created for: <strong>${adminEmail}</strong></p>
                        <p>✅ Password configured successfully - you can now log in!</p>
                    </div>
                    
                    <div class="next-steps">
                        <h3><i class="fas fa-rocket" style="margin-right: 0.5rem;"></i>Next Steps:</h3>
                        <ul style="text-align: left; margin: 1rem 0;">
                            <li>✅ Log in with your administrator credentials</li>
                            <li>🏢 Complete your organization profile setup</li>
                            <li>📚 Begin creating courses and managing users</li>
                            <li>⚙️ Access password change options in your profile settings</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; border-radius: 4px;">
                        <p style="margin: 0;"><strong>🎯 Quick Tip:</strong> You can now access the platform using your administrator credentials to start building your educational content.</p>
                    </div>
                </div>
            `;
        } else {
            console.warn('Success message element not found, using fallback');
            // Fallback if the element structure is different
            this.successMessage.innerHTML = `
                <div class="success-content">
                    <h2><i class="fas fa-check-circle" style="color: #10b981; margin-right: 0.5rem;"></i>Registration Successful!</h2>
                    <p>Your organization registration has been completed successfully!</p>
                    <p>You can now log in with your administrator credentials.</p>
                </div>
            `;
        }
        
        // Scroll to top to show success message (single scroll operation to avoid forced reflow)
        setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 200);
        
        console.log('Success message displayed successfully');
    }

    /**
     * DISPLAY GENERAL ERROR INTERFACE
     * PURPOSE: Display general error interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} message - Message parameter
     */
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

// Initialize when DOM is loaded and CONFIG is available
document.addEventListener('DOMContentLoaded', () => {
    // Wait for CONFIG to be available
    /**
     * INITIALIZE REGISTRATION COMPONENT
     * PURPOSE: Initialize registration component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    const initializeRegistration = () => {
        if (typeof CONFIG !== 'undefined' || typeof window.CONFIG !== 'undefined') {
            new OrganizationRegistration();
        } else {
            // Retry after a short delay if CONFIG isn't ready yet
            setTimeout(initializeRegistration, 50);
        }
    };
    initializeRegistration();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrganizationRegistration;
}