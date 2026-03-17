"""
Unit tests for Accessibility Domain Entities

What: Tests for accessibility entities, enums, and domain logic.
Where: Organization Management service domain layer tests.
Why: Ensures:
     1. All accessibility enums have expected values
     2. Entity validation rules are enforced
     3. Business logic methods work correctly
     4. Color contrast calculations are accurate
     5. Factory functions create valid entities

BUSINESS CONTEXT:
These tests verify the foundation of accessibility features including:
- WCAG compliance level tracking
- Color contrast validation per WCAG 2.1 requirements
- User preference management
- Keyboard shortcut configuration
- Audit result tracking
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from organization_management.domain.entities.accessibility import (
    # Enums
    WCAGLevel,
    ColorContrastLevel,
    FontSizePreference,
    MotionPreference,
    ColorSchemePreference,
    FocusIndicatorStyle,
    AuditSeverity,
    AuditCategory,
    KeyboardNavigationType,
    # Entities
    AccessibilityPreference,
    ColorContrastRequirement,
    KeyboardShortcut,
    ScreenReaderAnnouncement,
    AccessibilityAuditResult,
    AccessibilityComplianceReport,
    # Factory functions
    create_default_preferences,
    create_contrast_check,
    create_audit_issue,
)


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestWCAGLevelEnum:
    """Test WCAGLevel enum values."""

    def test_wcag_level_a(self):
        """Test Level A value."""
        assert WCAGLevel.A.value == "A"

    def test_wcag_level_aa(self):
        """Test Level AA value."""
        assert WCAGLevel.AA.value == "AA"

    def test_wcag_level_aaa(self):
        """Test Level AAA value."""
        assert WCAGLevel.AAA.value == "AAA"

    def test_wcag_level_count(self):
        """Test total number of levels."""
        assert len(WCAGLevel) == 3


class TestColorContrastLevelEnum:
    """Test ColorContrastLevel enum values."""

    def test_normal_text_aa(self):
        """Test normal text AA level."""
        assert ColorContrastLevel.NORMAL_TEXT_AA.value == "normal_text_aa"

    def test_large_text_aa(self):
        """Test large text AA level."""
        assert ColorContrastLevel.LARGE_TEXT_AA.value == "large_text_aa"

    def test_normal_text_aaa(self):
        """Test normal text AAA level."""
        assert ColorContrastLevel.NORMAL_TEXT_AAA.value == "normal_text_aaa"

    def test_large_text_aaa(self):
        """Test large text AAA level."""
        assert ColorContrastLevel.LARGE_TEXT_AAA.value == "large_text_aaa"

    def test_ui_component(self):
        """Test UI component level."""
        assert ColorContrastLevel.UI_COMPONENT.value == "ui_component"


class TestFontSizePreferenceEnum:
    """Test FontSizePreference enum values."""

    def test_default_font_size(self):
        """Test default font size."""
        assert FontSizePreference.DEFAULT.value == "default"

    def test_large_font_size(self):
        """Test large font size."""
        assert FontSizePreference.LARGE.value == "large"

    def test_extra_large_font_size(self):
        """Test extra large font size."""
        assert FontSizePreference.EXTRA_LARGE.value == "xlarge"

    def test_huge_font_size(self):
        """Test huge font size."""
        assert FontSizePreference.HUGE.value == "huge"


class TestMotionPreferenceEnum:
    """Test MotionPreference enum values."""

    def test_no_preference(self):
        """Test no preference value."""
        assert MotionPreference.NO_PREFERENCE.value == "no_preference"

    def test_reduce_motion(self):
        """Test reduce motion value."""
        assert MotionPreference.REDUCE.value == "reduce"

    def test_no_motion(self):
        """Test no motion value."""
        assert MotionPreference.NO_MOTION.value == "no_motion"


class TestColorSchemePreferenceEnum:
    """Test ColorSchemePreference enum values."""

    def test_system_scheme(self):
        """Test system scheme value."""
        assert ColorSchemePreference.SYSTEM.value == "system"

    def test_light_scheme(self):
        """Test light scheme value."""
        assert ColorSchemePreference.LIGHT.value == "light"

    def test_dark_scheme(self):
        """Test dark scheme value."""
        assert ColorSchemePreference.DARK.value == "dark"

    def test_high_contrast_scheme(self):
        """Test high contrast scheme value."""
        assert ColorSchemePreference.HIGH_CONTRAST.value == "high_contrast"


class TestFocusIndicatorStyleEnum:
    """Test FocusIndicatorStyle enum values."""

    def test_default_style(self):
        """Test default style value."""
        assert FocusIndicatorStyle.DEFAULT.value == "default"

    def test_enhanced_style(self):
        """Test enhanced style value."""
        assert FocusIndicatorStyle.ENHANCED.value == "enhanced"

    def test_high_visibility_style(self):
        """Test high visibility style value."""
        assert FocusIndicatorStyle.HIGH_VISIBILITY.value == "high_visibility"


class TestAuditSeverityEnum:
    """Test AuditSeverity enum values."""

    def test_critical_severity(self):
        """Test critical severity value."""
        assert AuditSeverity.CRITICAL.value == "critical"

    def test_serious_severity(self):
        """Test serious severity value."""
        assert AuditSeverity.SERIOUS.value == "serious"

    def test_moderate_severity(self):
        """Test moderate severity value."""
        assert AuditSeverity.MODERATE.value == "moderate"

    def test_minor_severity(self):
        """Test minor severity value."""
        assert AuditSeverity.MINOR.value == "minor"


class TestAuditCategoryEnum:
    """Test AuditCategory enum values."""

    def test_perceivable_category(self):
        """Test perceivable category."""
        assert AuditCategory.PERCEIVABLE.value == "perceivable"

    def test_operable_category(self):
        """Test operable category."""
        assert AuditCategory.OPERABLE.value == "operable"

    def test_understandable_category(self):
        """Test understandable category."""
        assert AuditCategory.UNDERSTANDABLE.value == "understandable"

    def test_robust_category(self):
        """Test robust category."""
        assert AuditCategory.ROBUST.value == "robust"


class TestKeyboardNavigationTypeEnum:
    """Test KeyboardNavigationType enum values."""

    def test_tab_navigation(self):
        """Test tab navigation type."""
        assert KeyboardNavigationType.TAB_NAVIGATION.value == "tab"

    def test_arrow_navigation(self):
        """Test arrow navigation type."""
        assert KeyboardNavigationType.ARROW_NAVIGATION.value == "arrow"

    def test_roving_tabindex(self):
        """Test roving tabindex type."""
        assert KeyboardNavigationType.ROVING_TABINDEX.value == "roving"

    def test_focus_trap(self):
        """Test focus trap type."""
        assert KeyboardNavigationType.FOCUS_TRAP.value == "focus_trap"


# =============================================================================
# ACCESSIBILITY PREFERENCE TESTS
# =============================================================================

class TestAccessibilityPreference:
    """Test AccessibilityPreference entity."""

    def test_preference_creation_with_defaults(self):
        """Test creating preference with default values."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4()
        )
        assert pref.font_size == FontSizePreference.DEFAULT
        assert pref.color_scheme == ColorSchemePreference.SYSTEM
        assert pref.motion_preference == MotionPreference.NO_PREFERENCE
        assert pref.keyboard_shortcuts_enabled is True
        assert pref.captions_enabled is True

    def test_preference_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Preference ID is required"):
            AccessibilityPreference(id=None, user_id=uuid4())

    def test_preference_requires_user_id(self):
        """Test that user ID is required."""
        with pytest.raises(ValueError, match="User ID is required"):
            AccessibilityPreference(id=uuid4(), user_id=None)

    def test_timeout_multiplier_minimum(self):
        """Test timeout multiplier minimum validation."""
        with pytest.raises(ValueError, match="must be at least 1.0"):
            AccessibilityPreference(
                id=uuid4(),
                user_id=uuid4(),
                timeout_multiplier=Decimal("0.5")
            )

    def test_timeout_multiplier_maximum(self):
        """Test timeout multiplier maximum validation."""
        with pytest.raises(ValueError, match="cannot exceed 5.0"):
            AccessibilityPreference(
                id=uuid4(),
                user_id=uuid4(),
                timeout_multiplier=Decimal("6.0")
            )

    def test_get_font_size_multiplier_default(self):
        """Test font size multiplier for default."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            font_size=FontSizePreference.DEFAULT
        )
        assert pref.get_font_size_multiplier() == Decimal("1.0")

    def test_get_font_size_multiplier_large(self):
        """Test font size multiplier for large."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            font_size=FontSizePreference.LARGE
        )
        assert pref.get_font_size_multiplier() == Decimal("1.25")

    def test_get_font_size_multiplier_huge(self):
        """Test font size multiplier for huge."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            font_size=FontSizePreference.HUGE
        )
        assert pref.get_font_size_multiplier() == Decimal("2.0")

    def test_get_animation_duration_no_motion(self):
        """Test animation duration for no motion."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            motion_preference=MotionPreference.NO_MOTION
        )
        assert pref.get_animation_duration_multiplier() == Decimal("0")

    def test_get_animation_duration_reduce(self):
        """Test animation duration for reduced motion."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            motion_preference=MotionPreference.REDUCE
        )
        assert pref.get_animation_duration_multiplier() == Decimal("0.3")

    def test_needs_screen_reader_support(self):
        """Test screen reader support detection."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            screen_reader_optimizations=True
        )
        assert pref.needs_screen_reader_support() is True

    def test_to_css_custom_properties(self):
        """Test CSS custom properties generation."""
        pref = AccessibilityPreference(
            id=uuid4(),
            user_id=uuid4(),
            font_size=FontSizePreference.LARGE,
            focus_indicator_style=FocusIndicatorStyle.ENHANCED
        )
        props = pref.to_css_custom_properties()
        assert "--a11y-font-size-multiplier" in props
        assert props["--a11y-focus-ring-width"] == "3px"


# =============================================================================
# COLOR CONTRAST REQUIREMENT TESTS
# =============================================================================

class TestColorContrastRequirement:
    """Test ColorContrastRequirement entity and contrast calculations."""

    def test_contrast_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Requirement ID is required"):
            ColorContrastRequirement(
                id=None,
                level=ColorContrastLevel.NORMAL_TEXT_AA,
                foreground_color="#000000",
                background_color="#FFFFFF"
            )

    def test_contrast_requires_valid_foreground(self):
        """Test foreground color validation."""
        with pytest.raises(ValueError, match="Invalid foreground color"):
            ColorContrastRequirement(
                id=uuid4(),
                level=ColorContrastLevel.NORMAL_TEXT_AA,
                foreground_color="invalid",
                background_color="#FFFFFF"
            )

    def test_contrast_requires_valid_background(self):
        """Test background color validation."""
        with pytest.raises(ValueError, match="Invalid background color"):
            ColorContrastRequirement(
                id=uuid4(),
                level=ColorContrastLevel.NORMAL_TEXT_AA,
                foreground_color="#000000",
                background_color="invalid"
            )

    def test_black_on_white_contrast(self):
        """Test maximum contrast ratio (black on white)."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#000000",
            background_color="#FFFFFF"
        )
        assert contrast.calculated_ratio == Decimal("21.00")
        assert contrast.passes is True

    def test_white_on_white_contrast(self):
        """Test minimum contrast ratio (white on white)."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#FFFFFF",
            background_color="#FFFFFF"
        )
        assert contrast.calculated_ratio == Decimal("1.00")
        assert contrast.passes is False

    def test_contrast_passes_aa_normal_text(self):
        """Test contrast passing AA for normal text (4.5:1)."""
        # Dark gray on white - ratio ~8:1
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#595959",
            background_color="#FFFFFF"
        )
        assert contrast.passes is True
        assert contrast.calculated_ratio >= Decimal("4.5")

    def test_contrast_fails_aa_normal_text(self):
        """Test contrast failing AA for normal text."""
        # Light gray on white - ratio ~3:1
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#949494",
            background_color="#FFFFFF"
        )
        assert contrast.passes is False
        assert contrast.calculated_ratio < Decimal("4.5")

    def test_contrast_passes_aa_large_text(self):
        """Test contrast passing AA for large text (3:1)."""
        # Medium gray on white - ratio ~3.5:1
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.LARGE_TEXT_AA,
            foreground_color="#757575",
            background_color="#FFFFFF"
        )
        assert contrast.passes is True
        assert contrast.calculated_ratio >= Decimal("3.0")

    def test_contrast_passes_aaa_normal_text(self):
        """Test contrast passing AAA for normal text (7:1)."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AAA,
            foreground_color="#000000",
            background_color="#FFFFFF"
        )
        assert contrast.passes is True
        assert contrast.calculated_ratio >= Decimal("7.0")

    def test_get_required_ratio(self):
        """Test getting required ratio for level."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#000000",
            background_color="#FFFFFF"
        )
        assert contrast.get_required_ratio() == Decimal("4.5")

    def test_short_hex_color(self):
        """Test 3-digit hex color support."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="#000",
            background_color="#FFF"
        )
        assert contrast.calculated_ratio == Decimal("21.00")

    def test_color_with_hash(self):
        """Test colors with and without hash."""
        contrast = ColorContrastRequirement(
            id=uuid4(),
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            foreground_color="000000",
            background_color="FFFFFF"
        )
        assert contrast.calculated_ratio == Decimal("21.00")


# =============================================================================
# KEYBOARD SHORTCUT TESTS
# =============================================================================

class TestKeyboardShortcut:
    """Test KeyboardShortcut entity."""

    def test_shortcut_creation(self):
        """Test basic shortcut creation."""
        shortcut = KeyboardShortcut(
            id=uuid4(),
            key="KeyS",
            modifiers=["ctrl"],
            action="save"
        )
        assert shortcut.key == "KeyS"
        assert shortcut.action == "save"
        assert shortcut.enabled is True

    def test_shortcut_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Shortcut ID is required"):
            KeyboardShortcut(id=None, key="KeyS", action="save")

    def test_shortcut_requires_key(self):
        """Test that key is required."""
        with pytest.raises(ValueError, match="Key is required"):
            KeyboardShortcut(id=uuid4(), key="", action="save")

    def test_shortcut_requires_action(self):
        """Test that action is required."""
        with pytest.raises(ValueError, match="Action is required"):
            KeyboardShortcut(id=uuid4(), key="KeyS", action="")

    def test_shortcut_validates_modifiers(self):
        """Test modifier validation."""
        with pytest.raises(ValueError, match="Invalid modifier"):
            KeyboardShortcut(
                id=uuid4(),
                key="KeyS",
                modifiers=["invalid"],
                action="save"
            )

    def test_get_shortcut_string(self):
        """Test shortcut string generation."""
        shortcut = KeyboardShortcut(
            id=uuid4(),
            key="KeyS",
            modifiers=["ctrl", "shift"],
            action="save"
        )
        assert shortcut.get_shortcut_string() == "Ctrl+Shift+KeyS"

    def test_get_shortcut_string_no_modifiers(self):
        """Test shortcut string without modifiers."""
        shortcut = KeyboardShortcut(
            id=uuid4(),
            key="Escape",
            modifiers=[],
            action="close"
        )
        assert shortcut.get_shortcut_string() == "Escape"

    def test_matches_event_with_modifiers(self):
        """Test event matching with modifiers."""
        shortcut = KeyboardShortcut(
            id=uuid4(),
            key="KeyS",
            modifiers=["ctrl"],
            action="save"
        )
        assert shortcut.matches_event("KeyS", ctrl=True) is True
        assert shortcut.matches_event("KeyS", ctrl=False) is False
        assert shortcut.matches_event("KeyS", ctrl=True, alt=True) is False

    def test_matches_event_without_modifiers(self):
        """Test event matching without modifiers."""
        shortcut = KeyboardShortcut(
            id=uuid4(),
            key="Escape",
            modifiers=[],
            action="close"
        )
        assert shortcut.matches_event("Escape") is True
        assert shortcut.matches_event("Escape", ctrl=True) is False


# =============================================================================
# SCREEN READER ANNOUNCEMENT TESTS
# =============================================================================

class TestScreenReaderAnnouncement:
    """Test ScreenReaderAnnouncement entity."""

    def test_announcement_creation(self):
        """Test basic announcement creation."""
        announcement = ScreenReaderAnnouncement(
            id=uuid4(),
            message="Form submitted successfully"
        )
        assert announcement.message == "Form submitted successfully"
        assert announcement.politeness == "polite"
        assert announcement.atomic is True

    def test_announcement_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Announcement ID is required"):
            ScreenReaderAnnouncement(id=None, message="Test")

    def test_announcement_requires_message(self):
        """Test that message is required."""
        with pytest.raises(ValueError, match="Message is required"):
            ScreenReaderAnnouncement(id=uuid4(), message="")

    def test_announcement_validates_politeness(self):
        """Test politeness level validation."""
        with pytest.raises(ValueError, match="Invalid politeness"):
            ScreenReaderAnnouncement(
                id=uuid4(),
                message="Test",
                politeness="invalid"
            )

    def test_announcement_validates_delay(self):
        """Test delay validation."""
        with pytest.raises(ValueError, match="Delay cannot be negative"):
            ScreenReaderAnnouncement(
                id=uuid4(),
                message="Test",
                delay_ms=-100
            )

    def test_assertive_announcement(self):
        """Test assertive announcement."""
        announcement = ScreenReaderAnnouncement(
            id=uuid4(),
            message="Error occurred",
            politeness="assertive"
        )
        assert announcement.politeness == "assertive"


# =============================================================================
# ACCESSIBILITY AUDIT RESULT TESTS
# =============================================================================

class TestAccessibilityAuditResult:
    """Test AccessibilityAuditResult entity."""

    def test_audit_result_creation(self):
        """Test basic audit result creation."""
        result = AccessibilityAuditResult(
            id=uuid4(),
            page_url="/dashboard",
            rule_id="color-contrast",
            issue_description="Low contrast text"
        )
        assert result.page_url == "/dashboard"
        assert result.rule_id == "color-contrast"
        assert result.is_fixed is False

    def test_audit_result_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Audit result ID is required"):
            AccessibilityAuditResult(
                id=None,
                page_url="/test",
                rule_id="test",
                issue_description="Test"
            )

    def test_audit_result_requires_page_url(self):
        """Test that page URL is required."""
        with pytest.raises(ValueError, match="Page URL is required"):
            AccessibilityAuditResult(
                id=uuid4(),
                page_url="",
                rule_id="test",
                issue_description="Test"
            )

    def test_audit_result_requires_rule_id(self):
        """Test that rule ID is required."""
        with pytest.raises(ValueError, match="Rule ID is required"):
            AccessibilityAuditResult(
                id=uuid4(),
                page_url="/test",
                rule_id="",
                issue_description="Test"
            )

    def test_audit_result_requires_description(self):
        """Test that description is required."""
        with pytest.raises(ValueError, match="Issue description is required"):
            AccessibilityAuditResult(
                id=uuid4(),
                page_url="/test",
                rule_id="test",
                issue_description=""
            )

    def test_mark_fixed(self):
        """Test marking issue as fixed."""
        result = AccessibilityAuditResult(
            id=uuid4(),
            page_url="/test",
            rule_id="color-contrast",
            issue_description="Test issue"
        )
        fixer_id = uuid4()
        result.mark_fixed(fixer_id)

        assert result.is_fixed is True
        assert result.fixed_by == fixer_id
        assert result.fixed_at is not None

    def test_get_wcag_criteria(self):
        """Test WCAG criteria lookup."""
        result = AccessibilityAuditResult(
            id=uuid4(),
            page_url="/test",
            rule_id="color-contrast",
            issue_description="Test"
        )
        assert result.get_wcag_criteria() == "1.4.3"

    def test_get_wcag_criteria_unknown(self):
        """Test WCAG criteria for unknown rule."""
        result = AccessibilityAuditResult(
            id=uuid4(),
            page_url="/test",
            rule_id="unknown-rule",
            issue_description="Test"
        )
        assert result.get_wcag_criteria() == "Unknown"


# =============================================================================
# ACCESSIBILITY COMPLIANCE REPORT TESTS
# =============================================================================

class TestAccessibilityComplianceReport:
    """Test AccessibilityComplianceReport entity."""

    def test_report_creation(self):
        """Test basic report creation."""
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=uuid4()
        )
        assert report.wcag_level == WCAGLevel.AA
        assert report.pages_audited == 0
        assert report.total_issues == 0

    def test_report_requires_id(self):
        """Test that ID is required."""
        with pytest.raises(ValueError, match="Report ID is required"):
            AccessibilityComplianceReport(id=None, organization_id=uuid4())

    def test_report_requires_organization_id(self):
        """Test that organization ID is required."""
        with pytest.raises(ValueError, match="Organization ID is required"):
            AccessibilityComplianceReport(id=uuid4(), organization_id=None)

    def test_calculate_compliance_score_no_pages(self):
        """Test compliance score with no pages audited."""
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=uuid4(),
            pages_audited=0
        )
        assert report.calculate_compliance_score() == Decimal("100")

    def test_calculate_compliance_score_no_issues(self):
        """Test compliance score with no issues."""
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=uuid4(),
            pages_audited=10
        )
        assert report.calculate_compliance_score() == Decimal("100.0")

    def test_calculate_compliance_score_with_issues(self):
        """Test compliance score with issues."""
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=uuid4(),
            pages_audited=10,
            critical_issues=2,
            serious_issues=3,
            moderate_issues=5,
            minor_issues=10
        )
        score = report.calculate_compliance_score()
        assert score < Decimal("100")
        assert score >= Decimal("0")

    def test_get_summary(self):
        """Test report summary generation."""
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=uuid4(),
            pages_audited=10,
            total_issues=20,
            critical_issues=2,
            issues_fixed=5,
            compliance_score=Decimal("75.5")
        )
        summary = report.get_summary()

        assert "pages_audited" in summary
        assert summary["pages_audited"] == 10
        assert summary["total_issues"] == 20
        assert summary["issues_by_severity"]["critical"] == 2
        assert summary["issues_fixed"] == 5


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Test factory functions for creating entities."""

    def test_create_default_preferences(self):
        """Test creating default preferences."""
        user_id = uuid4()
        prefs = create_default_preferences(user_id)

        assert prefs.user_id == user_id
        assert prefs.font_size == FontSizePreference.DEFAULT
        assert prefs.keyboard_shortcuts_enabled is True
        assert prefs.captions_enabled is True

    def test_create_contrast_check(self):
        """Test creating contrast check."""
        check = create_contrast_check(
            foreground="#000000",
            background="#FFFFFF",
            level=ColorContrastLevel.NORMAL_TEXT_AA,
            component_name="Button"
        )

        assert check.foreground_color == "#000000"
        assert check.background_color == "#FFFFFF"
        assert check.component_name == "Button"
        assert check.passes is True

    def test_create_audit_issue(self):
        """Test creating audit issue."""
        issue = create_audit_issue(
            page_url="/dashboard",
            rule_id="color-contrast",
            description="Low contrast text",
            severity=AuditSeverity.SERIOUS,
            element=".header-text"
        )

        assert issue.page_url == "/dashboard"
        assert issue.rule_id == "color-contrast"
        assert issue.severity == AuditSeverity.SERIOUS
        assert issue.affected_element == ".header-text"


# =============================================================================
# INTEGRATION SCENARIO TESTS
# =============================================================================

class TestAccessibilityScenarios:
    """Test complete accessibility workflow scenarios."""

    def test_user_preference_workflow(self):
        """Test complete user preference workflow."""
        user_id = uuid4()

        # Create default preferences
        prefs = create_default_preferences(user_id)
        assert prefs.font_size == FontSizePreference.DEFAULT

        # Simulate preference update
        prefs.font_size = FontSizePreference.LARGE
        prefs.motion_preference = MotionPreference.REDUCE
        prefs.high_contrast_mode = True

        # Verify CSS properties reflect changes
        css = prefs.to_css_custom_properties()
        assert css["--a11y-font-size-multiplier"] == "1.25"
        assert css["--a11y-animation-multiplier"] == "0.3"

    def test_contrast_audit_workflow(self):
        """Test contrast checking workflow."""
        # Check multiple color combinations
        color_pairs = [
            ("#000000", "#FFFFFF"),  # Pass
            ("#FFFFFF", "#FFFFFF"),  # Fail
            ("#595959", "#FFFFFF"),  # Pass
        ]

        results = []
        for fg, bg in color_pairs:
            check = create_contrast_check(fg, bg)
            results.append(check)

        passing = [r for r in results if r.passes]
        failing = [r for r in results if not r.passes]

        assert len(passing) == 2
        assert len(failing) == 1

    def test_accessibility_audit_workflow(self):
        """Test complete accessibility audit workflow."""
        org_id = uuid4()
        auditor_id = uuid4()

        # Create audit results
        issues = [
            create_audit_issue(
                page_url="/dashboard",
                rule_id="color-contrast",
                description="Low contrast text",
                severity=AuditSeverity.SERIOUS
            ),
            create_audit_issue(
                page_url="/login",
                rule_id="label",
                description="Missing form label",
                severity=AuditSeverity.MODERATE
            ),
        ]

        # Create compliance report
        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=org_id,
            pages_audited=2,
            total_issues=2,
            serious_issues=1,
            moderate_issues=1,
            generated_by=auditor_id
        )

        # Calculate compliance
        report.compliance_score = report.calculate_compliance_score()
        assert report.compliance_score < Decimal("100")

        # Mark issue as fixed
        issues[0].mark_fixed(auditor_id)
        assert issues[0].is_fixed is True

    def test_keyboard_shortcut_workflow(self):
        """Test keyboard shortcut configuration workflow."""
        # Create default shortcuts
        shortcuts = [
            KeyboardShortcut(
                id=uuid4(),
                key="KeyS",
                modifiers=["alt"],
                action="skip_to_main",
                description="Skip to main content"
            ),
            KeyboardShortcut(
                id=uuid4(),
                key="Escape",
                modifiers=[],
                action="close_modal",
                description="Close dialog"
            ),
        ]

        # Test event matching
        assert shortcuts[0].matches_event("KeyS", alt=True) is True
        assert shortcuts[1].matches_event("Escape") is True

        # Verify shortcut strings
        assert shortcuts[0].get_shortcut_string() == "Alt+KeyS"
        assert shortcuts[1].get_shortcut_string() == "Escape"
