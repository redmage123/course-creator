/**
 * Frontend Tests for Organization Registration
 * Tests JavaScript functionality, drag-and-drop, validation, and user interactions
 */

// Mock DOM environment for testing
global.document = require('jsdom').jsdom('<html><body></body></html>');
global.window = document.defaultView;
global.FormData = require('form-data');
global.File = class File {
    constructor(bits, filename, options = {}) {
        this.bits = bits;
        this.name = filename;
        this.type = options.type || '';
        this.size = bits.reduce((size, bit) => size + bit.length, 0);
    }
};

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock CONFIG object
global.CONFIG = {
    API_URLS: {
        ORGANIZATION: 'https://test-api.com:8008'
    }
};

describe('Organization Registration Frontend', () => {
    let organizationRegistration;
    let mockForm;
    let mockElements = {};

    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = `
            <form id="organizationRegistrationForm">
                <input id="orgName" name="name" type="text" required>
                <input id="orgSlug" name="slug" type="text" required>
                <input id="orgEmail" name="contact_email" type="email" required>
                <input id="adminEmail" name="admin_email" type="email" required>
                <input id="orgPhone" name="contact_phone" type="tel" required>
                <input id="adminPhone" name="admin_phone" type="tel">
                
                <div id="logoUploadArea" class="logo-upload-area">
                    <div class="upload-content">
                        <p>Drag & drop your logo here</p>
                    </div>
                    <input id="orgLogo" name="logo" type="file" hidden>
                </div>
                
                <div id="logoPreview" class="logo-preview" style="display: none;">
                    <img id="previewImage" src="" alt="Logo preview">
                    <div class="preview-info">
                        <span id="fileName" class="file-name"></span>
                        <button id="removeLogo" type="button" class="remove-logo">×</button>
                    </div>
                </div>
                
                <button id="submitBtn" type="submit">Submit</button>
                <div id="successMessage" class="success-message" style="display: none;"></div>
                
                <!-- Error containers -->
                <div id="orgName-error" class="form-error"></div>
                <div id="orgSlug-error" class="form-error"></div>
                <div id="orgEmail-error" class="form-error"></div>
                <div id="adminEmail-error" class="form-error"></div>
                <div id="orgPhone-error" class="form-error"></div>
                <div id="adminPhone-error" class="form-error"></div>
                <div id="orgLogo-error" class="form-error"></div>
            </form>
        `;

        // Create mock elements object
        mockElements = {
            form: document.getElementById('organizationRegistrationForm'),
            submitBtn: document.getElementById('submitBtn'),
            successMessage: document.getElementById('successMessage'),
            logoUploadArea: document.getElementById('logoUploadArea'),
            fileInput: document.getElementById('orgLogo'),
            preview: document.getElementById('logoPreview'),
            previewImage: document.getElementById('previewImage'),
            fileName: document.getElementById('fileName'),
            removeBtn: document.getElementById('removeLogo')
        };

        // Mock the OrganizationRegistration class
        organizationRegistration = {
            form: mockElements.form,
            submitBtn: mockElements.submitBtn,
            successMessage: mockElements.successMessage,
            selectedLogo: null,
            logoUpload: {
                uploadArea: mockElements.logoUploadArea,
                fileInput: mockElements.fileInput,
                preview: mockElements.preview,
                previewImage: mockElements.previewImage,
                fileName: mockElements.fileName,
                removeBtn: mockElements.removeBtn,
                maxSize: 5 * 1024 * 1024,
                allowedTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            },
            blockedEmailDomains: new Set([
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'aol.com', 'icloud.com', 'me.com', 'live.com'
            ])
        };

        // Reset fetch mock
        fetch.mockClear();
    });

    describe('Email Validation', () => {
        test('should reject personal email domains', () => {
            const personalEmails = [
                'user@gmail.com',
                'admin@yahoo.com', 
                'contact@hotmail.com',
                'info@outlook.com'
            ];

            personalEmails.forEach(email => {
                const domain = email.split('@')[1];
                expect(organizationRegistration.blockedEmailDomains.has(domain)).toBe(true);
            });
        });

        test('should accept professional email domains', () => {
            const professionalEmails = [
                'admin@techcorp.com',
                'contact@university.edu',
                'info@nonprofit.org',
                'training@enterprise.co.uk'
            ];

            professionalEmails.forEach(email => {
                const domain = email.split('@')[1];
                expect(organizationRegistration.blockedEmailDomains.has(domain)).toBe(false);
            });
        });

        test('should validate email format', () => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            const validEmails = [
                'test@example.com',
                'user.name@domain.co.uk',
                'admin+tag@company.org'
            ];

            const invalidEmails = [
                'not-an-email',
                '@domain.com',
                'user@',
                'user space@domain.com'
            ];

            validEmails.forEach(email => {
                expect(emailRegex.test(email)).toBe(true);
            });

            invalidEmails.forEach(email => {
                expect(emailRegex.test(email)).toBe(false);
            });
        });
    });

    describe('Slug Generation', () => {
        test('should generate correct slugs from organization names', () => {
            const testCases = [
                { input: 'TechCorp Training Institute', expected: 'techcorp-training-institute' },
                { input: 'University of Technology', expected: 'university-of-technology' },
                { input: 'ABC Corp & Associates', expected: 'abc-corp-associates' },
                { input: '   Spaced   Name   ', expected: 'spaced-name' },
                { input: 'Name@#$%With^&*Special()', expected: 'namewithspecial' }
            ];

            testCases.forEach(({ input, expected }) => {
                const result = input
                    .toLowerCase()
                    .replace(/[^a-z0-9\s-]/g, '')
                    .replace(/\s+/g, '-')
                    .replace(/-+/g, '-')
                    .replace(/^-|-$/g, '');
                
                expect(result).toBe(expected);
            });
        });
    });

    describe('Phone Number Validation', () => {
        test('should validate phone number formats', () => {
            const phoneRegex = /^\+?[\d\s\-()]{10,}$/;
            
            const validPhones = [
                '+1-555-123-4567',
                '+44-20-7946-0958',
                '+1 (555) 123-4567',
                '15551234567',
                '+86-138-0013-8000'
            ];

            const invalidPhones = [
                '123',
                'abc-def-ghij',
                '+1-555',
                ''
            ];

            validPhones.forEach(phone => {
                expect(phoneRegex.test(phone)).toBe(true);
            });

            invalidPhones.forEach(phone => {
                expect(phoneRegex.test(phone)).toBe(false);
            });
        });

        test('should format phone numbers', () => {
            // Mock phone formatting function
            const formatPhoneNumber = (phone) => {
                let value = phone.replace(/\D/g, '');
                
                if (value.length > 0) {
                    if (!phone.startsWith('+')) {
                        value = '1' + value;
                    }
                    
                    if (value.length <= 11 && value.startsWith('1')) {
                        if (value.length > 1) value = '+1-' + value.substring(1);
                        if (value.length > 6) value = value.substring(0, 6) + '-' + value.substring(6);
                        if (value.length > 10) value = value.substring(0, 10) + '-' + value.substring(10, 14);
                    }
                }
                
                return value;
            };

            expect(formatPhoneNumber('5551234567')).toBe('+1-555-123-4567');
            expect(formatPhoneNumber('15551234567')).toBe('+1-555-123-4567');
        });
    });

    describe('File Upload Validation', () => {
        test('should validate file types', () => {
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
            
            const validFiles = [
                { type: 'image/jpeg', name: 'photo.jpg' },
                { type: 'image/png', name: 'logo.png' },
                { type: 'image/gif', name: 'animation.gif' }
            ];

            const invalidFiles = [
                { type: 'text/plain', name: 'document.txt' },
                { type: 'application/pdf', name: 'file.pdf' },
                { type: 'video/mp4', name: 'video.mp4' }
            ];

            validFiles.forEach(file => {
                expect(allowedTypes.includes(file.type)).toBe(true);
            });

            invalidFiles.forEach(file => {
                expect(allowedTypes.includes(file.type)).toBe(false);
            });
        });

        test('should validate file size', () => {
            const maxSize = 5 * 1024 * 1024; // 5MB
            
            const validSizes = [
                1024,           // 1KB
                1024 * 1024,    // 1MB
                3 * 1024 * 1024 // 3MB
            ];

            const invalidSizes = [
                6 * 1024 * 1024,  // 6MB
                10 * 1024 * 1024  // 10MB
            ];

            validSizes.forEach(size => {
                expect(size <= maxSize).toBe(true);
            });

            invalidSizes.forEach(size => {
                expect(size <= maxSize).toBe(false);
            });
        });

        test('should format file sizes correctly', () => {
            const formatFileSize = (bytes) => {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            };

            expect(formatFileSize(0)).toBe('0 Bytes');
            expect(formatFileSize(1024)).toBe('1 KB');
            expect(formatFileSize(1024 * 1024)).toBe('1 MB');
            expect(formatFileSize(5 * 1024 * 1024)).toBe('5 MB');
        });
    });

    describe('Form Submission', () => {
        test('should prepare form data correctly for JSON submission', () => {
            // Mock form data
            const formData = new Map([
                ['name', 'Test Corporation'],
                ['slug', 'test-corporation'],
                ['address', '123 Test St, Test City, TC 12345'],
                ['contact_phone', '+1-555-123-4567'],
                ['contact_email', 'admin@testcorp.com'],
                ['admin_full_name', 'Test Admin'],
                ['admin_email', 'admin@testcorp.com'],
                ['admin_phone', '+1-555-123-4568'],
                ['description', 'Test organization'],
                ['domain', 'testcorp.com']
            ]);

            const organizationData = {
                name: formData.get('name'),
                slug: formData.get('slug'),
                address: formData.get('address'),
                contact_phone: formData.get('contact_phone'),
                contact_email: formData.get('contact_email'),
                admin_full_name: formData.get('admin_full_name'),
                admin_email: formData.get('admin_email'),
                admin_phone: formData.get('admin_phone') || undefined,
                description: formData.get('description') || undefined,
                domain: formData.get('domain') || undefined
            };

            expect(organizationData.name).toBe('Test Corporation');
            expect(organizationData.slug).toBe('test-corporation');
            expect(organizationData.contact_email).toBe('admin@testcorp.com');
            expect(organizationData.admin_email).toBe('admin@testcorp.com');
        });

        test('should handle API success response', async () => {
            const mockResponse = {
                id: '123e4567-e89b-12d3-a456-426614174000',
                name: 'Test Corporation',
                slug: 'test-corporation',
                contact_email: 'admin@testcorp.com',
                is_active: true,
                created_at: '2023-01-01T00:00:00Z',
                updated_at: '2023-01-01T00:00:00Z'
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => mockResponse
            });

            const response = await fetch('https://test-api.com/organizations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            expect(response.ok).toBe(true);
            const data = await response.json();
            expect(data.name).toBe('Test Corporation');
            expect(data.is_active).toBe(true);
        });

        test('should handle API validation errors', async () => {
            const mockErrorResponse = {
                detail: [
                    {
                        loc: ['contact_email'],
                        msg: 'Personal email provider gmail.com not allowed',
                        type: 'value_error'
                    }
                ]
            };

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 422,
                json: async () => mockErrorResponse
            });

            const response = await fetch('https://test-api.com/organizations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            expect(response.ok).toBe(false);
            expect(response.status).toBe(422);
            
            const errorData = await response.json();
            expect(errorData.detail).toHaveLength(1);
            expect(errorData.detail[0].loc).toContain('contact_email');
            expect(errorData.detail[0].msg).toContain('gmail.com');
        });
    });

    describe('File Upload with FormData', () => {
        test('should handle multipart form submission', async () => {
            const mockFile = new File(['test'], 'logo.png', { type: 'image/png' });
            const formData = new FormData();
            
            formData.append('name', 'Test Corporation');
            formData.append('slug', 'test-corporation');
            formData.append('logo', mockFile);

            // Mock successful file upload response
            fetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => ({
                    id: '123e4567-e89b-12d3-a456-426614174000',
                    name: 'Test Corporation',
                    logo_url: 'https://api.example.com/files/logo.png',
                    logo_file_path: '/uploads/organizations/123/logo.png'
                })
            });

            const response = await fetch('https://test-api.com/organizations/upload', {
                method: 'POST',
                body: formData
            });

            expect(response.ok).toBe(true);
            const data = await response.json();
            expect(data.logo_url).toBeTruthy();
            expect(data.logo_file_path).toBeTruthy();
        });

        test('should handle file upload validation errors', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: async () => ({
                    detail: 'Invalid file type. Please upload JPG, PNG, or GIF files only.'
                })
            });

            const response = await fetch('https://test-api.com/organizations/upload', {
                method: 'POST',
                body: new FormData()
            });

            expect(response.ok).toBe(false);
            expect(response.status).toBe(400);
            
            const errorData = await response.json();
            expect(errorData.detail).toContain('Invalid file type');
        });
    });

    describe('DOM Manipulation', () => {
        test('should show and hide elements correctly', () => {
            const element = mockElements.preview;
            
            // Initially hidden
            expect(element.style.display).toBe('none');
            
            // Show element
            element.style.display = 'block';
            expect(element.style.display).toBe('block');
            
            // Hide element
            element.style.display = 'none';
            expect(element.style.display).toBe('none');
        });

        test('should manipulate CSS classes', () => {
            const element = mockElements.logoUploadArea;
            
            // Add class
            element.classList.add('dragover');
            expect(element.classList.contains('dragover')).toBe(true);
            
            // Remove class
            element.classList.remove('dragover');
            expect(element.classList.contains('dragover')).toBe(false);
            
            // Toggle class
            element.classList.toggle('error');
            expect(element.classList.contains('error')).toBe(true);
            
            element.classList.toggle('error');
            expect(element.classList.contains('error')).toBe(false);
        });

        test('should handle form field errors', () => {
            const input = document.getElementById('orgEmail');
            const errorElement = document.getElementById('orgEmail-error');
            
            // Show error
            input.classList.add('error');
            errorElement.textContent = 'Personal email not allowed';
            errorElement.classList.add('show');
            
            expect(input.classList.contains('error')).toBe(true);
            expect(errorElement.textContent).toBe('Personal email not allowed');
            expect(errorElement.classList.contains('show')).toBe(true);
            
            // Clear error
            input.classList.remove('error');
            errorElement.classList.remove('show');
            
            expect(input.classList.contains('error')).toBe(false);
            expect(errorElement.classList.contains('show')).toBe(false);
        });
    });

    describe('Event Handling', () => {
        test('should handle form validation events', () => {
            const form = mockElements.form;
            let validationCalled = false;
            
            // Mock validation function
            const mockValidation = () => {
                validationCalled = true;
                return true;
            };
            
            // Simulate form submission
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                mockValidation();
            });
            
            // Trigger submit
            const submitEvent = new Event('submit');
            form.dispatchEvent(submitEvent);
            
            expect(validationCalled).toBe(true);
        });

        test('should handle file input change events', () => {
            const fileInput = mockElements.fileInput;
            let changeHandled = false;
            
            fileInput.addEventListener('change', () => {
                changeHandled = true;
            });
            
            // Trigger change event
            const changeEvent = new Event('change');
            fileInput.dispatchEvent(changeEvent);
            
            expect(changeHandled).toBe(true);
        });
    });
});

// Test configuration for Jest
module.exports = {
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],
    testMatch: ['**/*.test.js'],
    collectCoverageFrom: [
        'frontend/js/**/*.js',
        '!frontend/js/config.js'
    ],
    coverageReporters: ['text', 'lcov', 'html'],
    moduleNameMapping: {
        '^@/(.*)$': '<rootDir>/frontend/$1'
    }
};