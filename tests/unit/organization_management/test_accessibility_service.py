"""
Unit tests for AccessibilityService

What: Tests for the accessibility service business logic layer.
Where: Organization Management service application layer tests.
Why: Ensures:
     1. Service methods correctly validate inputs
     2. Business logic is properly applied before DAO calls
     3. Error handling produces appropriate exceptions
     4. Color contrast validation is accurate
     5. Accessibility preferences management works correctly

BUSINESS CONTEXT:
The AccessibilityService provides the business logic layer for:
- User accessibility preference management
- Color contrast validation per WCAG 2.1
- Keyboard shortcut configuration
- Screen reader announcement creation
- Accessibility audit tracking and reporting
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from organization_management.application.services.accessibility_service import (
    AccessibilityService
)
from organization_management.domain.entities.accessibility import (
    AccessibilityPreference,
    ColorContrastRequirement,
    KeyboardShortcut,
    ScreenReaderAnnouncement,
    AccessibilityAuditResult,
    AccessibilityComplianceReport,
    WCAGLevel,
    ColorContrastLevel,
    FontSizePreference,
    MotionPreference,
    ColorSchemePreference,
    FocusIndicatorStyle,
    AuditSeverity,
    AuditCategory,
)
from organization_management.exceptions import ValidationException


@pytest.fixture
def mock_dao():
    """Create a mock DAO for testing."""
    dao = AsyncMock()
    return dao


@pytest.fixture
def accessibility_service(mock_dao):
    """Create AccessibilityService with mock DAO."""
    return AccessibilityService(mock_dao)


@pytest.fixture
def accessibility_service_no_dao():
    """Create AccessibilityService without DAO for basic testing."""
    return AccessibilityService()


# =============================================================================
# ACCESSIBILITY PREFERENCES TESTS
# =============================================================================

class TestGetUserPreferences:
    """Test getting user accessibility preferences."""

    @pytest.mark.asyncio
    async def test_get_preferences_from_dao(self, accessibility_service, mock_dao):
        """Test retrieving preferences from DAO."""
        user_id = uuid4()
        expected_prefs = MagicMock(spec=AccessibilityPreference)
        mock_dao.get_accessibility_preference.return_value = expected_prefs

        result = await accessibility_service.get_user_preferences(user_id)

        assert result == expected_prefs
        mock_dao.get_accessibility_preference.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_default_preferences_when_none_exist(
        self, accessibility_service, mock_dao
    ):
        """Test returning default preferences when none exist."""
        user_id = uuid4()
        mock_dao.get_accessibility_preference.return_value = None

        result = await accessibility_service.get_user_preferences(user_id)

        assert result.user_id == user_id
        assert result.font_size == FontSizePreference.DEFAULT

    @pytest.mark.asyncio
    async def test_get_preferences_without_dao(self, accessibility_service_no_dao):
        """Test getting preferences without DAO returns defaults."""
        user_id = uuid4()

        result = await accessibility_service_no_dao.get_user_preferences(user_id)

        assert result.user_id == user_id
        assert result.keyboard_shortcuts_enabled is True


class TestUpdateUserPreferences:
    """Test updating user accessibility preferences."""

    @pytest.mark.asyncio
    async def test_update_font_size(self, accessibility_service, mock_dao):
        """Test updating font size preference."""
        user_id = uuid4()
        existing_prefs = MagicMock()
        existing_prefs.id = uuid4()
        mock_dao.get_accessibility_preference.return_value = existing_prefs
        mock_dao.update_accessibility_preference.return_value = MagicMock()

        await accessibility_service.update_user_preferences(
            user_id=user_id,
            font_size=FontSizePreference.LARGE
        )

        call_args = mock_dao.update_accessibility_preference.call_args[0][1]
        assert call_args["font_size"] == FontSizePreference.LARGE

    @pytest.mark.asyncio
    async def test_update_motion_preference(self, accessibility_service, mock_dao):
        """Test updating motion preference."""
        user_id = uuid4()
        existing_prefs = MagicMock()
        existing_prefs.id = uuid4()
        mock_dao.get_accessibility_preference.return_value = existing_prefs
        mock_dao.update_accessibility_preference.return_value = MagicMock()

        await accessibility_service.update_user_preferences(
            user_id=user_id,
            motion_preference=MotionPreference.REDUCE
        )

        call_args = mock_dao.update_accessibility_preference.call_args[0][1]
        assert call_args["motion_preference"] == MotionPreference.REDUCE

    @pytest.mark.asyncio
    async def test_update_timeout_multiplier_too_low(self, accessibility_service):
        """Test timeout multiplier validation - too low."""
        user_id = uuid4()

        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service.update_user_preferences(
                user_id=user_id,
                timeout_multiplier=Decimal("0.5")
            )

        assert "timeout_multiplier" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_update_timeout_multiplier_too_high(self, accessibility_service):
        """Test timeout multiplier validation - too high."""
        user_id = uuid4()

        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service.update_user_preferences(
                user_id=user_id,
                timeout_multiplier=Decimal("6.0")
            )

        assert "timeout_multiplier" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_update_multiple_preferences(self, accessibility_service, mock_dao):
        """Test updating multiple preferences at once."""
        user_id = uuid4()
        existing_prefs = MagicMock()
        existing_prefs.id = uuid4()
        mock_dao.get_accessibility_preference.return_value = existing_prefs
        mock_dao.update_accessibility_preference.return_value = MagicMock()

        await accessibility_service.update_user_preferences(
            user_id=user_id,
            font_size=FontSizePreference.LARGE,
            high_contrast_mode=True,
            captions_enabled=True
        )

        call_args = mock_dao.update_accessibility_preference.call_args[0][1]
        assert call_args["font_size"] == FontSizePreference.LARGE
        assert call_args["high_contrast_mode"] is True
        assert call_args["captions_enabled"] is True


class TestResetUserPreferences:
    """Test resetting user preferences to defaults."""

    @pytest.mark.asyncio
    async def test_reset_preferences(self, accessibility_service, mock_dao):
        """Test resetting all preferences to defaults."""
        user_id = uuid4()
        mock_dao.update_accessibility_preference.return_value = MagicMock()

        result = await accessibility_service.reset_user_preferences(user_id)

        mock_dao.update_accessibility_preference.assert_called_once()
        call_args = mock_dao.update_accessibility_preference.call_args[0][1]
        assert call_args["font_size"] == FontSizePreference.DEFAULT

    @pytest.mark.asyncio
    async def test_reset_preferences_without_dao(self, accessibility_service_no_dao):
        """Test reset returns default preferences without DAO."""
        user_id = uuid4()

        result = await accessibility_service_no_dao.reset_user_preferences(user_id)

        assert result.font_size == FontSizePreference.DEFAULT
        assert result.color_scheme == ColorSchemePreference.SYSTEM


# =============================================================================
# COLOR CONTRAST VALIDATION TESTS
# =============================================================================

class TestValidateColorContrast:
    """Test color contrast validation."""

    def test_validate_black_on_white(self, accessibility_service_no_dao):
        """Test validating black on white (maximum contrast)."""
        result = accessibility_service_no_dao.validate_color_contrast(
            foreground="#000000",
            background="#FFFFFF"
        )

        assert result.passes is True
        assert result.calculated_ratio == Decimal("21.00")

    def test_validate_white_on_white(self, accessibility_service_no_dao):
        """Test validating white on white (minimum contrast)."""
        result = accessibility_service_no_dao.validate_color_contrast(
            foreground="#FFFFFF",
            background="#FFFFFF"
        )

        assert result.passes is False
        assert result.calculated_ratio == Decimal("1.00")

    def test_validate_invalid_foreground(self, accessibility_service_no_dao):
        """Test validating invalid foreground color."""
        with pytest.raises(ValidationException) as exc_info:
            accessibility_service_no_dao.validate_color_contrast(
                foreground="invalid",
                background="#FFFFFF"
            )

        assert "foreground" in exc_info.value.field_errors

    def test_validate_invalid_background(self, accessibility_service_no_dao):
        """Test validating invalid background color."""
        with pytest.raises(ValidationException) as exc_info:
            accessibility_service_no_dao.validate_color_contrast(
                foreground="#000000",
                background="invalid"
            )

        assert "background" in exc_info.value.field_errors

    def test_validate_large_text_level(self, accessibility_service_no_dao):
        """Test validating with large text level (3:1 ratio)."""
        result = accessibility_service_no_dao.validate_color_contrast(
            foreground="#757575",
            background="#FFFFFF",
            level=ColorContrastLevel.LARGE_TEXT_AA
        )

        assert result.passes is True

    def test_validate_with_component_name(self, accessibility_service_no_dao):
        """Test validating with component name."""
        result = accessibility_service_no_dao.validate_color_contrast(
            foreground="#000000",
            background="#FFFFFF",
            component_name="Button"
        )

        assert result.component_name == "Button"


class TestBatchValidateContrast:
    """Test batch color contrast validation."""

    def test_batch_validate_multiple_pairs(self, accessibility_service_no_dao):
        """Test validating multiple color pairs."""
        color_pairs = [
            {"foreground": "#000000", "background": "#FFFFFF"},
            {"foreground": "#FFFFFF", "background": "#FFFFFF"},
            {"foreground": "#595959", "background": "#FFFFFF"},
        ]

        results = accessibility_service_no_dao.batch_validate_contrast(color_pairs)

        assert len(results) == 3
        assert results[0].passes is True  # Black on white
        assert results[1].passes is False  # White on white
        assert results[2].passes is True  # Dark gray on white

    def test_batch_validate_with_invalid_pairs(self, accessibility_service_no_dao):
        """Test batch validation skips invalid pairs."""
        color_pairs = [
            {"foreground": "#000000", "background": "#FFFFFF"},
            {"foreground": "invalid", "background": "#FFFFFF"},
        ]

        results = accessibility_service_no_dao.batch_validate_contrast(color_pairs)

        assert len(results) == 1  # Only valid pair returned


class TestGetContrastSuggestions:
    """Test contrast improvement suggestions."""

    def test_suggestions_for_passing_contrast(self, accessibility_service_no_dao):
        """Test suggestions when contrast passes."""
        result = accessibility_service_no_dao.get_contrast_suggestions(
            foreground="#000000",
            background="#FFFFFF"
        )

        assert result["passes"] is True
        assert result["gap"] == "0"
        assert len(result["suggestions"]) == 0

    def test_suggestions_for_failing_contrast(self, accessibility_service_no_dao):
        """Test suggestions when contrast fails."""
        result = accessibility_service_no_dao.get_contrast_suggestions(
            foreground="#AAAAAA",
            background="#FFFFFF"
        )

        assert result["passes"] is False
        assert len(result["suggestions"]) > 0


# =============================================================================
# KEYBOARD SHORTCUTS TESTS
# =============================================================================

class TestGetKeyboardShortcuts:
    """Test keyboard shortcut retrieval."""

    @pytest.mark.asyncio
    async def test_get_default_shortcuts(self, accessibility_service_no_dao):
        """Test getting default keyboard shortcuts."""
        shortcuts = await accessibility_service_no_dao.get_keyboard_shortcuts()

        assert len(shortcuts) > 0
        actions = [s.action for s in shortcuts]
        assert "skip_to_main" in actions
        assert "close_modal" in actions

    @pytest.mark.asyncio
    async def test_get_shortcuts_with_user_customization(
        self, accessibility_service, mock_dao
    ):
        """Test getting shortcuts with user customizations."""
        user_id = uuid4()
        custom_shortcut = MagicMock()
        custom_shortcut.action = "custom_action"
        mock_dao.get_user_keyboard_shortcuts.return_value = [custom_shortcut]

        shortcuts = await accessibility_service.get_keyboard_shortcuts(user_id=user_id)

        mock_dao.get_user_keyboard_shortcuts.assert_called_once_with(user_id)


class TestUpdateKeyboardShortcut:
    """Test keyboard shortcut customization."""

    @pytest.mark.asyncio
    async def test_update_shortcut(self, accessibility_service, mock_dao):
        """Test updating a keyboard shortcut."""
        user_id = uuid4()
        mock_dao.get_user_keyboard_shortcuts.return_value = []
        mock_dao.save_user_keyboard_shortcut.return_value = MagicMock()

        result = await accessibility_service.update_keyboard_shortcut(
            user_id=user_id,
            action="save",
            key="KeyS",
            modifiers=["ctrl"]
        )

        mock_dao.save_user_keyboard_shortcut.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_shortcut_empty_key(self, accessibility_service_no_dao):
        """Test updating with empty key raises error."""
        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service_no_dao.update_keyboard_shortcut(
                user_id=uuid4(),
                action="save",
                key="",
                modifiers=[]
            )

        assert "key" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_update_shortcut_conflict(self, accessibility_service_no_dao):
        """Test updating with conflicting shortcut."""
        user_id = uuid4()

        # This will check against default shortcuts
        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service_no_dao.update_keyboard_shortcut(
                user_id=user_id,
                action="new_action",
                key="KeyS",
                modifiers=["alt"]  # Conflicts with skip_to_main
            )

        assert "key" in exc_info.value.field_errors


# =============================================================================
# SCREEN READER ANNOUNCEMENTS TESTS
# =============================================================================

class TestCreateAnnouncement:
    """Test screen reader announcement creation."""

    def test_create_polite_announcement(self, accessibility_service_no_dao):
        """Test creating polite announcement."""
        result = accessibility_service_no_dao.create_announcement(
            message="Content loaded"
        )

        assert result.message == "Content loaded"
        assert result.politeness == "polite"

    def test_create_assertive_announcement(self, accessibility_service_no_dao):
        """Test creating assertive announcement."""
        result = accessibility_service_no_dao.create_announcement(
            message="Error occurred",
            politeness="assertive"
        )

        assert result.politeness == "assertive"

    def test_create_announcement_empty_message(self, accessibility_service_no_dao):
        """Test creating announcement with empty message."""
        with pytest.raises(ValidationException) as exc_info:
            accessibility_service_no_dao.create_announcement(message="")

        assert "message" in exc_info.value.field_errors

    def test_create_announcement_invalid_politeness(self, accessibility_service_no_dao):
        """Test creating announcement with invalid politeness."""
        with pytest.raises(ValidationException) as exc_info:
            accessibility_service_no_dao.create_announcement(
                message="Test",
                politeness="invalid"
            )

        assert "politeness" in exc_info.value.field_errors


class TestGetAnnouncementForAction:
    """Test getting announcements for common actions."""

    def test_form_submitted_announcement(self, accessibility_service_no_dao):
        """Test form submitted announcement."""
        result = accessibility_service_no_dao.get_announcement_for_action(
            "form_submitted"
        )

        assert "submitted" in result.message.lower()
        assert result.politeness == "polite"

    def test_form_error_announcement(self, accessibility_service_no_dao):
        """Test form error announcement (assertive)."""
        result = accessibility_service_no_dao.get_announcement_for_action(
            "form_error",
            error_count=3
        )

        assert "error" in result.message.lower()
        assert result.politeness == "assertive"

    def test_page_loaded_announcement(self, accessibility_service_no_dao):
        """Test page loaded announcement with title."""
        result = accessibility_service_no_dao.get_announcement_for_action(
            "page_loaded",
            page_title="Dashboard"
        )

        assert "Dashboard" in result.message

    def test_modal_opened_announcement(self, accessibility_service_no_dao):
        """Test modal opened announcement."""
        result = accessibility_service_no_dao.get_announcement_for_action(
            "modal_opened",
            modal_title="Settings"
        )

        assert "Settings" in result.message


# =============================================================================
# ACCESSIBILITY AUDITING TESTS
# =============================================================================

class TestCreateAuditResult:
    """Test creating accessibility audit results."""

    @pytest.mark.asyncio
    async def test_create_audit_result(self, accessibility_service, mock_dao):
        """Test creating basic audit result."""
        mock_dao.create_audit_result.return_value = MagicMock()

        result = await accessibility_service.create_audit_result(
            page_url="/dashboard",
            rule_id="color-contrast",
            description="Low contrast text"
        )

        mock_dao.create_audit_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_audit_result_empty_url(self, accessibility_service_no_dao):
        """Test creating audit result with empty URL."""
        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service_no_dao.create_audit_result(
                page_url="",
                rule_id="color-contrast",
                description="Test"
            )

        assert "page_url" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_create_audit_result_empty_rule_id(
        self, accessibility_service_no_dao
    ):
        """Test creating audit result with empty rule ID."""
        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service_no_dao.create_audit_result(
                page_url="/test",
                rule_id="",
                description="Test"
            )

        assert "rule_id" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_create_audit_result_empty_description(
        self, accessibility_service_no_dao
    ):
        """Test creating audit result with empty description."""
        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service_no_dao.create_audit_result(
                page_url="/test",
                rule_id="color-contrast",
                description=""
            )

        assert "description" in exc_info.value.field_errors

    @pytest.mark.asyncio
    async def test_create_audit_result_with_severity(
        self, accessibility_service, mock_dao
    ):
        """Test creating audit result with specific severity."""
        mock_dao.create_audit_result.return_value = MagicMock()

        await accessibility_service.create_audit_result(
            page_url="/dashboard",
            rule_id="color-contrast",
            description="Low contrast",
            severity=AuditSeverity.CRITICAL
        )

        call_args = mock_dao.create_audit_result.call_args[0][0]
        assert call_args.severity == AuditSeverity.CRITICAL


class TestMarkIssueFxed:
    """Test marking accessibility issues as fixed."""

    @pytest.mark.asyncio
    async def test_mark_issue_fixed(self, accessibility_service, mock_dao):
        """Test marking issue as fixed."""
        audit_id = uuid4()
        fixed_by = uuid4()
        result = MagicMock()
        result.is_fixed = False

        mock_dao.get_audit_result.return_value = result
        mock_dao.update_audit_result.return_value = result

        await accessibility_service.mark_issue_fixed(audit_id, fixed_by)

        mock_dao.update_audit_result.assert_called_once()
        call_args = mock_dao.update_audit_result.call_args[0][1]
        assert call_args["is_fixed"] is True
        assert call_args["fixed_by"] == fixed_by

    @pytest.mark.asyncio
    async def test_mark_issue_fixed_not_found(self, accessibility_service, mock_dao):
        """Test marking non-existent issue raises error."""
        audit_id = uuid4()
        mock_dao.get_audit_result.return_value = None

        with pytest.raises(ValidationException) as exc_info:
            await accessibility_service.mark_issue_fixed(audit_id, uuid4())

        assert "audit_id" in exc_info.value.field_errors


class TestGetPageAuditResults:
    """Test retrieving page audit results."""

    @pytest.mark.asyncio
    async def test_get_page_results(self, accessibility_service, mock_dao):
        """Test getting audit results for a page."""
        results = [MagicMock(is_fixed=False), MagicMock(is_fixed=True)]
        mock_dao.get_audit_results_by_page.return_value = results

        page_results = await accessibility_service.get_page_audit_results("/dashboard")

        assert len(page_results) == 1  # Fixed issues filtered out

    @pytest.mark.asyncio
    async def test_get_page_results_include_fixed(
        self, accessibility_service, mock_dao
    ):
        """Test getting audit results including fixed."""
        results = [MagicMock(is_fixed=False), MagicMock(is_fixed=True)]
        mock_dao.get_audit_results_by_page.return_value = results

        page_results = await accessibility_service.get_page_audit_results(
            "/dashboard",
            include_fixed=True
        )

        assert len(page_results) == 2


# =============================================================================
# COMPLIANCE REPORTING TESTS
# =============================================================================

class TestGenerateComplianceReport:
    """Test compliance report generation."""

    @pytest.mark.asyncio
    async def test_generate_report(self, accessibility_service, mock_dao):
        """Test generating compliance report."""
        org_id = uuid4()
        results = [
            MagicMock(
                page_url="/page1",
                is_fixed=False,
                severity=AuditSeverity.CRITICAL,
                id=uuid4()
            ),
            MagicMock(
                page_url="/page2",
                is_fixed=False,
                severity=AuditSeverity.MODERATE,
                id=uuid4()
            ),
            MagicMock(
                page_url="/page1",
                is_fixed=True,
                severity=AuditSeverity.MINOR,
                id=uuid4()
            ),
        ]
        mock_dao.get_audit_results_by_organization.return_value = results
        mock_dao.save_compliance_report.return_value = None

        report = await accessibility_service.generate_compliance_report(org_id)

        assert report.organization_id == org_id
        assert report.pages_audited == 2
        assert report.total_issues == 2
        assert report.critical_issues == 1
        assert report.moderate_issues == 1
        assert report.issues_fixed == 1

    @pytest.mark.asyncio
    async def test_generate_report_without_dao(self, accessibility_service_no_dao):
        """Test generating report without DAO."""
        org_id = uuid4()

        report = await accessibility_service_no_dao.generate_compliance_report(org_id)

        assert report.organization_id == org_id
        assert report.pages_audited == 0


class TestGetComplianceHistory:
    """Test compliance history retrieval."""

    @pytest.mark.asyncio
    async def test_get_history(self, accessibility_service, mock_dao):
        """Test getting compliance report history."""
        org_id = uuid4()
        reports = [MagicMock(), MagicMock()]
        mock_dao.get_compliance_reports.return_value = reports

        result = await accessibility_service.get_compliance_history(org_id)

        assert result == reports
        mock_dao.get_compliance_reports.assert_called_once_with(org_id, 10)


class TestGetWCAGCriteriaInfo:
    """Test WCAG criteria information retrieval."""

    def test_get_color_contrast_info(self, accessibility_service_no_dao):
        """Test getting color contrast criteria info."""
        info = accessibility_service_no_dao.get_wcag_criteria_info("color-contrast")

        assert info["criteria"] == "1.4.3"
        assert info["level"] == "AA"
        assert "Contrast" in info["title"]

    def test_get_keyboard_info(self, accessibility_service_no_dao):
        """Test getting keyboard criteria info."""
        info = accessibility_service_no_dao.get_wcag_criteria_info("keyboard")

        assert info["criteria"] == "2.1.1"
        assert info["level"] == "A"

    def test_get_unknown_rule_info(self, accessibility_service_no_dao):
        """Test getting info for unknown rule."""
        info = accessibility_service_no_dao.get_wcag_criteria_info("unknown-rule")

        assert info["criteria"] == "Unknown"


# =============================================================================
# INTEGRATION SCENARIO TESTS
# =============================================================================

class TestAccessibilityPreferencesScenario:
    """Test complete accessibility preferences workflow."""

    @pytest.mark.asyncio
    async def test_full_preferences_workflow(self, accessibility_service, mock_dao):
        """Test complete preferences workflow."""
        user_id = uuid4()
        pref_id = uuid4()

        # Step 1: Get default preferences (none exist)
        mock_dao.get_accessibility_preference.return_value = None

        prefs = await accessibility_service.get_user_preferences(user_id)
        assert prefs.font_size == FontSizePreference.DEFAULT

        # Step 2: Update preferences
        existing = MagicMock()
        existing.id = pref_id
        mock_dao.get_accessibility_preference.return_value = existing
        updated = MagicMock()
        mock_dao.update_accessibility_preference.return_value = updated

        await accessibility_service.update_user_preferences(
            user_id=user_id,
            font_size=FontSizePreference.LARGE,
            high_contrast_mode=True
        )

        # Step 3: Reset preferences
        await accessibility_service.reset_user_preferences(user_id)

        # Verify reset was called with default values
        reset_call = mock_dao.update_accessibility_preference.call_args_list[-1]
        assert reset_call[0][1]["font_size"] == FontSizePreference.DEFAULT


class TestColorContrastAuditScenario:
    """Test complete color contrast audit workflow."""

    @pytest.mark.asyncio
    async def test_full_contrast_audit_workflow(
        self, accessibility_service, mock_dao
    ):
        """Test complete contrast audit workflow."""
        org_id = uuid4()

        # Step 1: Validate color pairs
        color_pairs = [
            {"foreground": "#000000", "background": "#FFFFFF"},  # Pass
            {"foreground": "#AAAAAA", "background": "#FFFFFF"},  # Fail
        ]

        results = accessibility_service.batch_validate_contrast(color_pairs)
        failing = [r for r in results if not r.passes]

        # Step 2: Create audit results for failing contrasts
        mock_dao.create_audit_result.return_value = MagicMock()

        for fail in failing:
            await accessibility_service.create_audit_result(
                page_url="/dashboard",
                rule_id="color-contrast",
                description=f"Contrast ratio {fail.calculated_ratio} fails AA",
                severity=AuditSeverity.SERIOUS
            )

        assert mock_dao.create_audit_result.call_count == 1

        # Step 3: Generate compliance report
        mock_dao.get_audit_results_by_organization.return_value = []
        mock_dao.save_compliance_report.return_value = None

        report = await accessibility_service.generate_compliance_report(org_id)

        assert report.organization_id == org_id


class TestKeyboardAccessibilityScenario:
    """Test keyboard accessibility workflow."""

    @pytest.mark.asyncio
    async def test_keyboard_navigation_setup(self, accessibility_service_no_dao):
        """Test setting up keyboard navigation."""
        # Step 1: Get default shortcuts
        shortcuts = await accessibility_service_no_dao.get_keyboard_shortcuts()

        # Verify essential shortcuts exist
        actions = [s.action for s in shortcuts]
        assert "skip_to_main" in actions
        assert "close_modal" in actions

        # Step 2: Verify shortcut matching
        skip_shortcut = next(s for s in shortcuts if s.action == "skip_to_main")
        assert skip_shortcut.matches_event("KeyS", alt=True) is True

        # Step 3: Create announcement for navigation
        announcement = accessibility_service_no_dao.get_announcement_for_action(
            "page_loaded",
            page_title="Dashboard"
        )
        assert "Dashboard" in announcement.message
