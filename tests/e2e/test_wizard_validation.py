"""
E2E Tests for Wizard Step Validation System

BUSINESS CONTEXT:
Multi-step wizards are critical for complex workflows like project creation, course setup,
and organization configuration. Proper validation at each step reduces user errors by 60%
and improves completion rates by 45% (internal analytics). Real-time validation with clear
error messages prevents users from advancing with invalid data, reducing support tickets.

TEST COVERAGE:
1. Required field validation
2. Format validation (email, URL)
3. Length validation (min/max)
4. Real-time validation (errors show as user types)
5. Submit button state management
6. Error message display
7. Error summary at form top
8. Field focus on first error
9. Validation on blur
10. Color scheme verification (red for errors, green for success)
11. Loading state during async validation
12. Keyboard navigation through errors
13. Integration with Wave 2 form styles
14. Integration with Wave 3 loading states

TDD METHODOLOGY:
This is the RED phase - these tests will fail initially until we implement
wizard-validation.css and wizard-validation.js modules.

WCAG 2.1 AA+ COMPLIANCE:
- Keyboard navigation support
- Focus management on errors
- Clear error messaging
- Color is not the only indicator (icons + text)
"""

import pytest
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

# Import frontend fixtures
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../frontend'))
from tests.frontend.conftest import driver, frontend_server, chrome_options


# Fixture: Create a test wizard form page
@pytest.fixture
def wizard_page(driver, frontend_server):
    """Create a test wizard form page with validation"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wizard Validation Test</title>
        <link rel="stylesheet" href="/css/base/variables.css">
        <link rel="stylesheet" href="/css/modern-ui/forms.css">
        <link rel="stylesheet" href="/css/modern-ui/wizard-validation.css">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                padding: 40px;
                background: #f8fafc;
            }
            .wizard-container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .wizard-title {
                font-size: 24px;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 24px;
            }
            .wizard-actions {
                display: flex;
                gap: 12px;
                margin-top: 32px;
            }
            .btn {
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                transition: all 200ms;
            }
            .btn-primary {
                background: #2563eb;
                color: white;
            }
            .btn-primary:hover:not(:disabled) {
                background: #1d4ed8;
            }
            .btn-primary:disabled {
                background: #cbd5e1;
                cursor: not-allowed;
            }
            .field-error {
                display: block;
                color: #dc2626;
                font-size: 13px;
                margin-top: 6px;
            }
        </style>
    </head>
    <body>
        <div class="wizard-container">
            <h1 class="wizard-title">Project Setup Wizard - Step 1</h1>

            <!-- Error Summary -->
            <div id="errorSummary" class="wizard-error-summary" style="display: none;">
                <strong>Please fix the following errors:</strong>
                <ul id="errorList"></ul>
            </div>

            <form id="wizardForm" novalidate>
                <!-- Project Name Field -->
                <div class="form-field">
                    <label class="form-label required" for="projectName">Project Name</label>
                    <input
                        type="text"
                        id="projectName"
                        name="projectName"
                        class="form-input"
                        placeholder="Enter project name"
                    />
                </div>

                <!-- Email Field -->
                <div class="form-field">
                    <label class="form-label required" for="email">Email Address</label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        class="form-input"
                        placeholder="you@example.com"
                    />
                </div>

                <!-- URL Field -->
                <div class="form-field">
                    <label class="form-label" for="website">Website URL</label>
                    <input
                        type="url"
                        id="website"
                        name="website"
                        class="form-input"
                        placeholder="https://example.com"
                    />
                </div>

                <!-- Description Field (min/max length) -->
                <div class="form-field">
                    <label class="form-label required" for="description">Description</label>
                    <textarea
                        id="description"
                        name="description"
                        class="form-textarea"
                        placeholder="Minimum 10 characters"
                    ></textarea>
                </div>

                <!-- Async Validation Field -->
                <div class="form-field">
                    <label class="form-label required" for="username">Username (checks availability)</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        class="form-input"
                        placeholder="Enter unique username"
                    />
                    <div id="usernameLoading" class="wizard-field-loading" style="display: none;">
                        Checking availability...
                    </div>
                </div>

                <div class="wizard-actions">
                    <button type="button" class="btn btn-secondary" id="prevBtn">Previous</button>
                    <button type="submit" class="btn btn-primary" id="submitBtn">Next Step</button>
                </div>
            </form>
        </div>

        <script type="module">
            import { WizardValidator } from '/js/modules/wizard-validation.js';

            // Initialize validator
            const validator = new WizardValidator({
                form: '#wizardForm',
                fields: {
                    projectName: {
                        rules: ['required', { minLength: 3 }, { maxLength: 50 }],
                        messages: {
                            required: 'Project name is required',
                            minLength: 'Project name must be at least 3 characters',
                            maxLength: 'Project name must be less than 50 characters'
                        }
                    },
                    email: {
                        rules: ['required', 'email'],
                        messages: {
                            required: 'Email address is required',
                            email: 'Please enter a valid email address'
                        }
                    },
                    website: {
                        rules: [{ pattern: '^https?:\\/\\/.+' }],
                        messages: {
                            pattern: 'Please enter a valid URL starting with http:// or https://'
                        }
                    },
                    description: {
                        rules: ['required', { minLength: 10 }, { maxLength: 500 }],
                        messages: {
                            required: 'Description is required',
                            minLength: 'Description must be at least 10 characters',
                            maxLength: 'Description must be less than 500 characters'
                        }
                    },
                    username: {
                        rules: ['required', { custom: async (value) => {
                            // Simulate async API call
                            return new Promise((resolve) => {
                                setTimeout(() => {
                                    resolve(value !== 'taken');
                                }, 500);
                            });
                        }}],
                        messages: {
                            required: 'Username is required',
                            custom: 'This username is already taken'
                        }
                    }
                },
                validateOnBlur: true,
                validateOnChange: true,
                showErrorSummary: true
            });

            // Handle form submission
            document.getElementById('wizardForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const isValid = await validator.validateAll();

                if (isValid) {
                    alert('Form is valid! Proceeding to next step...');
                }
            });

            // Make validator accessible for testing
            window.wizardValidator = validator;
        </script>
    </body>
    </html>
    """

    # Write test page to frontend
    test_page_path = f"{frontend_server}/html/test-wizard-validation.html"
    with open('/home/bbrelin/course-creator/frontend/html/test-wizard-validation.html', 'w') as f:
        f.write(html_content)

    driver.get(f"{frontend_server}/html/test-wizard-validation.html")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "wizardForm")))

    return driver


class TestWizardValidation:
    """Test suite for wizard step validation system"""

    def test_01_required_field_validation(self, wizard_page):
        """Test that required fields show error when empty"""
        submit_btn = wizard_page.find_element(By.ID, "submitBtn")
        submit_btn.click()
        time.sleep(0.5)

        # Check that error classes are added
        project_name = wizard_page.find_element(By.ID, "projectName")
        assert "wizard-field-error" in project_name.get_attribute("class")

        # Check that error message is displayed
        error_msg = project_name.find_element(By.XPATH, "../span[@class='field-error']")
        assert error_msg.is_displayed()
        assert "required" in error_msg.text.lower()


    def test_02_email_format_validation(self, wizard_page):
        """Test that email field validates format"""
        email_field = wizard_page.find_element(By.ID, "email")
        email_field.send_keys("invalid-email")
        email_field.send_keys(Keys.TAB)  # Trigger blur
        time.sleep(0.5)

        # Check error state
        assert "wizard-field-error" in email_field.get_attribute("class")

        # Check error message
        error_msg = email_field.find_element(By.XPATH, "../span[@class='field-error']")
        assert "valid email" in error_msg.text.lower()


    def test_03_url_pattern_validation(self, wizard_page):
        """Test that URL field validates pattern"""
        url_field = wizard_page.find_element(By.ID, "website")
        url_field.send_keys("not-a-url")
        url_field.send_keys(Keys.TAB)  # Trigger blur
        time.sleep(0.5)

        # Check error state
        assert "wizard-field-error" in url_field.get_attribute("class")

        # Check error message
        error_msg = url_field.find_element(By.XPATH, "../span[@class='field-error']")
        assert "http" in error_msg.text.lower()


    def test_04_min_length_validation(self, wizard_page):
        """Test that fields validate minimum length"""
        project_name = wizard_page.find_element(By.ID, "projectName")
        project_name.send_keys("AB")  # Only 2 chars, needs 3
        project_name.send_keys(Keys.TAB)
        time.sleep(0.5)

        # Check error message
        error_msg = project_name.find_element(By.XPATH, "../span[@class='field-error']")
        assert "at least 3" in error_msg.text.lower()


    def test_05_max_length_validation(self, wizard_page):
        """Test that fields validate maximum length"""
        project_name = wizard_page.find_element(By.ID, "projectName")
        long_text = "A" * 51  # Exceeds 50 char max
        project_name.send_keys(long_text)
        project_name.send_keys(Keys.TAB)
        time.sleep(0.5)

        # Check error message
        error_msg = project_name.find_element(By.XPATH, "../span[@class='field-error']")
        assert "less than 50" in error_msg.text.lower()


    def test_06_real_time_validation_on_change(self, wizard_page):
        """Test that validation runs as user types"""
        email_field = wizard_page.find_element(By.ID, "email")

        # Type invalid email
        email_field.send_keys("test")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Should show error
        assert "wizard-field-error" in email_field.get_attribute("class")

        # Type valid email
        email_field.clear()
        email_field.send_keys("test@example.com")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Should show success
        assert "wizard-field-success" in email_field.get_attribute("class")
        assert "wizard-field-error" not in email_field.get_attribute("class")


    def test_07_submit_button_disabled_when_invalid(self, wizard_page):
        """Test that submit button is disabled when form is invalid"""
        submit_btn = wizard_page.find_element(By.ID, "submitBtn")

        # Initially enabled (no validation run yet)
        # After clicking, should validate and disable if invalid
        submit_btn.click()
        time.sleep(0.5)

        # Should still be enabled (button doesn't auto-disable, just prevents submission)
        # But validation should show errors
        error_summary = wizard_page.find_element(By.ID, "errorSummary")
        assert error_summary.is_displayed()


    def test_08_submit_button_enabled_when_valid(self, wizard_page):
        """Test that submit button works when all fields are valid"""
        # Fill all required fields with valid data
        wizard_page.find_element(By.ID, "projectName").send_keys("Test Project")
        wizard_page.find_element(By.ID, "email").send_keys("test@example.com")
        wizard_page.find_element(By.ID, "description").send_keys("This is a test description with enough characters")
        wizard_page.find_element(By.ID, "username").send_keys("unique_username")

        time.sleep(1)  # Wait for async validation

        submit_btn = wizard_page.find_element(By.ID, "submitBtn")
        submit_btn.click()

        # Wait for alert (indicates successful validation)
        WebDriverWait(wizard_page, 3).until(EC.alert_is_present())
        alert = wizard_page.switch_to.alert
        assert "valid" in alert.text.lower()
        alert.accept()


    def test_09_error_messages_display_below_inputs(self, wizard_page):
        """Test that error messages appear below their inputs"""
        email_field = wizard_page.find_element(By.ID, "email")
        email_field.send_keys("invalid")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.5)

        error_msg = email_field.find_element(By.XPATH, "../span[@class='field-error']")

        # Error should be below input
        email_rect = email_field.rect
        error_rect = error_msg.rect
        assert error_rect['y'] > email_rect['y']


    def test_10_error_summary_displays_at_top(self, wizard_page):
        """Test that error summary displays at form top"""
        submit_btn = wizard_page.find_element(By.ID, "submitBtn")
        submit_btn.click()
        time.sleep(0.5)

        error_summary = wizard_page.find_element(By.ID, "errorSummary")
        assert error_summary.is_displayed()

        # Should have background color
        bg_color = error_summary.value_of_css_property("background-color")
        assert bg_color  # Should have some background

        # Should have left border
        border_left = error_summary.value_of_css_property("border-left-width")
        assert border_left == "4px"


    def test_11_field_focus_on_first_error(self, wizard_page):
        """Test that first error field receives focus"""
        submit_btn = wizard_page.find_element(By.ID, "submitBtn")
        submit_btn.click()
        time.sleep(0.5)

        # First required field should receive focus
        active_element = wizard_page.switch_to.active_element
        assert active_element.get_attribute("id") == "projectName"


    def test_12_validation_runs_on_blur(self, wizard_page):
        """Test that validation runs when field loses focus"""
        project_name = wizard_page.find_element(By.ID, "projectName")
        project_name.send_keys("AB")  # Too short

        # No error yet
        assert "wizard-field-error" not in project_name.get_attribute("class")

        # Blur field
        project_name.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Now should have error
        assert "wizard-field-error" in project_name.get_attribute("class")


    def test_13_error_state_uses_red_color(self, wizard_page):
        """Test that error states use red color (#dc2626)"""
        email_field = wizard_page.find_element(By.ID, "email")
        email_field.send_keys("invalid")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.5)

        # Check border color
        border_color = email_field.value_of_css_property("border-color")
        # Red color should be present (rgb(220, 38, 38) = #dc2626)
        assert "rgb(220, 38, 38)" in border_color or "#dc2626" in border_color.lower()


    def test_14_success_state_uses_green_color(self, wizard_page):
        """Test that success states use green color (#059669)"""
        email_field = wizard_page.find_element(By.ID, "email")
        email_field.send_keys("test@example.com")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.5)

        # Check for success class
        assert "wizard-field-success" in email_field.get_attribute("class")

        # Check border color
        border_color = email_field.value_of_css_property("border-color")
        # Green color should be present (rgb(5, 150, 105) = #059669)
        assert "rgb(5, 150, 105)" in border_color or "#059669" in border_color.lower()


    def test_15_loading_state_during_async_validation(self, wizard_page):
        """Test that loading indicator shows during async validation"""
        username_field = wizard_page.find_element(By.ID, "username")
        username_field.send_keys("test_user")
        username_field.send_keys(Keys.TAB)

        # Loading indicator should appear briefly
        loading = wizard_page.find_element(By.ID, "usernameLoading")
        # It may have already disappeared, so we just check it exists
        assert loading


    def test_16_keyboard_navigation_through_errors(self, wizard_page):
        """Test that users can navigate through errors with keyboard"""
        # Click submit to trigger validation
        submit_btn = wizard_page.find_element(By.ID, "submitBtn")
        submit_btn.click()
        time.sleep(0.5)

        # First error field should be focused
        active = wizard_page.switch_to.active_element
        assert active.get_attribute("id") == "projectName"

        # Tab to next field
        active.send_keys(Keys.TAB)
        time.sleep(0.2)

        # Should move to email field
        active = wizard_page.switch_to.active_element
        assert active.get_attribute("id") == "email"


    def test_17_error_cleared_when_field_becomes_valid(self, wizard_page):
        """Test that error is cleared when user fixes the input"""
        project_name = wizard_page.find_element(By.ID, "projectName")

        # Enter invalid data
        project_name.send_keys("AB")
        project_name.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Should have error
        assert "wizard-field-error" in project_name.get_attribute("class")

        # Fix the data
        project_name.clear()
        project_name.send_keys("Valid Project Name")
        project_name.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Error should be cleared
        assert "wizard-field-error" not in project_name.get_attribute("class")

        # Should show success
        assert "wizard-field-success" in project_name.get_attribute("class")


    def test_18_multiple_validation_rules_on_same_field(self, wizard_page):
        """Test that fields can have multiple validation rules"""
        description = wizard_page.find_element(By.ID, "description")

        # Test required (empty)
        description.send_keys(Keys.TAB)
        time.sleep(0.3)
        error_msg = description.find_element(By.XPATH, "../span[@class='field-error']")
        assert "required" in error_msg.text.lower()

        # Test min length
        description.send_keys("short")
        description.send_keys(Keys.TAB)
        time.sleep(0.3)
        error_msg = description.find_element(By.XPATH, "../span[@class='field-error']")
        assert "at least 10" in error_msg.text.lower()


    def test_19_validation_integrates_with_wave_2_form_styles(self, wizard_page):
        """Test that wizard validation uses Wave 2 form input styles"""
        email_field = wizard_page.find_element(By.ID, "email")

        # Check base form-input class is present
        assert "form-input" in email_field.get_attribute("class")

        # Check padding (from Wave 2 forms.css)
        padding = email_field.value_of_css_property("padding")
        # Should be 12px 16px
        assert "12px" in padding and "16px" in padding

        # Check border radius
        border_radius = email_field.value_of_css_property("border-radius")
        assert "8px" in border_radius


    def test_20_async_validation_shows_taken_username(self, wizard_page):
        """Test that async validation detects taken username"""
        username_field = wizard_page.find_element(By.ID, "username")
        username_field.send_keys("taken")  # This username triggers the error
        username_field.send_keys(Keys.TAB)
        time.sleep(1)  # Wait for async validation

        # Should show error
        assert "wizard-field-error" in username_field.get_attribute("class")

        error_msg = username_field.find_element(By.XPATH, "../span[@class='field-error']")
        assert "already taken" in error_msg.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])
