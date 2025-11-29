"""
Accessibility Service

What: Business logic service for accessibility features and WCAG compliance.
Where: Organization Management service application layer.
Why: Provides:
     1. User accessibility preference management
     2. Color contrast validation and auditing
     3. Screen reader announcement orchestration
     4. Keyboard shortcut configuration
     5. WCAG compliance reporting
     6. Accessibility audit tracking

BUSINESS CONTEXT:
The AccessibilityService enables:
- Personalized accessibility settings for all users
- Automated WCAG 2.1 AA compliance checking
- Systematic tracking and remediation of accessibility issues
- Organization-wide accessibility reporting

Technical Implementation:
- Follows Single Responsibility Principle with focused methods
- Implements Dependency Inversion through DAO abstraction
- Provides comprehensive error handling with custom exceptions
- Supports async operations for high-performance operations
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from organization_management.domain.entities.accessibility import (
    AccessibilityPreference,
    AccessibilityAuditResult,
    AccessibilityComplianceReport,
    ColorContrastRequirement,
    KeyboardShortcut,
    ScreenReaderAnnouncement,
    WCAGLevel,
    ColorContrastLevel,
    FontSizePreference,
    MotionPreference,
    ColorSchemePreference,
    FocusIndicatorStyle,
    AuditSeverity,
    AuditCategory,
    create_default_preferences,
    create_contrast_check,
    create_audit_issue,
)
from organization_management.exceptions import (
    ValidationException,
    DatabaseException
)


class AccessibilityService:
    """
    Service for managing accessibility features.

    What: Coordinates business logic for accessibility preferences and auditing.
    Where: Organization Management service application layer.
    Why: Provides:
         1. Unified API for all accessibility operations
         2. Business rule validation and enforcement
         3. WCAG compliance validation
         4. Accessibility reporting and analytics

    Technical Implementation:
    - Uses DAO for all database operations
    - Implements comprehensive validation before database writes
    - Provides clear error messages for validation failures
    - Supports multi-tenant isolation through user/organization IDs
    """

    # Default keyboard shortcuts for the platform
    DEFAULT_SHORTCUTS = [
        {"key": "KeyS", "modifiers": ["alt"], "action": "skip_to_main",
         "description": "Skip to main content"},
        {"key": "KeyN", "modifiers": ["alt"], "action": "skip_to_nav",
         "description": "Skip to navigation"},
        {"key": "KeyH", "modifiers": ["alt"], "action": "open_help",
         "description": "Open keyboard shortcuts help"},
        {"key": "KeyD", "modifiers": ["alt"], "action": "go_to_dashboard",
         "description": "Go to dashboard"},
        {"key": "KeyC", "modifiers": ["alt"], "action": "go_to_courses",
         "description": "Go to courses"},
        {"key": "Escape", "modifiers": [], "action": "close_modal",
         "description": "Close current modal or dialog"},
    ]

    def __init__(self, dao: Optional[Any] = None):
        """
        Initialize the Accessibility Service.

        What: Constructor for AccessibilityService.
        Where: Called during service initialization.
        Why: Injects DAO dependency for database operations.

        Args:
            dao: Optional DAO instance for database operations
        """
        self.dao = dao
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # ACCESSIBILITY PREFERENCES MANAGEMENT
    # ================================================================

    async def get_user_preferences(
        self,
        user_id: UUID
    ) -> AccessibilityPreference:
        """
        Get accessibility preferences for a user.

        What: Retrieves user's accessibility settings.
        Where: Called on page load and settings access.
        Why: Enables personalized accessibility experience.

        Args:
            user_id: UUID of the user

        Returns:
            AccessibilityPreference for the user
        """
        self.logger.info(f"Getting accessibility preferences for user {user_id}")

        if self.dao:
            preferences = await self.dao.get_accessibility_preference(user_id)
            if preferences:
                return preferences

        # Return default preferences if none exist
        return create_default_preferences(user_id)

    async def update_user_preferences(
        self,
        user_id: UUID,
        font_size: Optional[FontSizePreference] = None,
        color_scheme: Optional[ColorSchemePreference] = None,
        motion_preference: Optional[MotionPreference] = None,
        focus_indicator_style: Optional[FocusIndicatorStyle] = None,
        high_contrast_mode: Optional[bool] = None,
        reduce_transparency: Optional[bool] = None,
        screen_reader_optimizations: Optional[bool] = None,
        announce_page_changes: Optional[bool] = None,
        verbose_announcements: Optional[bool] = None,
        keyboard_shortcuts_enabled: Optional[bool] = None,
        skip_links_always_visible: Optional[bool] = None,
        focus_highlight_enabled: Optional[bool] = None,
        auto_play_media: Optional[bool] = None,
        captions_enabled: Optional[bool] = None,
        audio_descriptions_enabled: Optional[bool] = None,
        extend_timeouts: Optional[bool] = None,
        timeout_multiplier: Optional[Decimal] = None,
        disable_auto_refresh: Optional[bool] = None,
    ) -> AccessibilityPreference:
        """
        Update accessibility preferences for a user.

        What: Updates user's accessibility settings.
        Where: Called from accessibility settings UI.
        Why: Enables users to customize their accessibility experience.

        Args:
            user_id: UUID of the user
            font_size: Font size preference
            color_scheme: Color scheme preference
            motion_preference: Motion/animation preference
            focus_indicator_style: Focus indicator style
            high_contrast_mode: Enable high contrast
            reduce_transparency: Reduce transparency effects
            screen_reader_optimizations: Enable screen reader optimizations
            announce_page_changes: Announce navigation changes
            verbose_announcements: Use verbose screen reader announcements
            keyboard_shortcuts_enabled: Enable keyboard shortcuts
            skip_links_always_visible: Always show skip links
            focus_highlight_enabled: Enable focus highlights
            auto_play_media: Auto-play media content
            captions_enabled: Enable captions for video
            audio_descriptions_enabled: Enable audio descriptions
            extend_timeouts: Extend session timeouts
            timeout_multiplier: Timeout extension multiplier
            disable_auto_refresh: Disable automatic page refresh

        Returns:
            Updated AccessibilityPreference

        Raises:
            ValidationException: If timeout_multiplier is invalid
        """
        self.logger.info(f"Updating accessibility preferences for user {user_id}")

        # Validate timeout multiplier
        if timeout_multiplier is not None:
            if timeout_multiplier < Decimal("1.0"):
                raise ValidationException(
                    message="Timeout multiplier must be at least 1.0",
                    field_errors={"timeout_multiplier": "Value must be >= 1.0"}
                )
            if timeout_multiplier > Decimal("5.0"):
                raise ValidationException(
                    message="Timeout multiplier cannot exceed 5.0",
                    field_errors={"timeout_multiplier": "Value must be <= 5.0"}
                )

        # Get current preferences or create defaults
        current = await self.get_user_preferences(user_id)

        # Build update dictionary with only changed values
        updates = {}
        if font_size is not None:
            updates["font_size"] = font_size
        if color_scheme is not None:
            updates["color_scheme"] = color_scheme
        if motion_preference is not None:
            updates["motion_preference"] = motion_preference
        if focus_indicator_style is not None:
            updates["focus_indicator_style"] = focus_indicator_style
        if high_contrast_mode is not None:
            updates["high_contrast_mode"] = high_contrast_mode
        if reduce_transparency is not None:
            updates["reduce_transparency"] = reduce_transparency
        if screen_reader_optimizations is not None:
            updates["screen_reader_optimizations"] = screen_reader_optimizations
        if announce_page_changes is not None:
            updates["announce_page_changes"] = announce_page_changes
        if verbose_announcements is not None:
            updates["verbose_announcements"] = verbose_announcements
        if keyboard_shortcuts_enabled is not None:
            updates["keyboard_shortcuts_enabled"] = keyboard_shortcuts_enabled
        if skip_links_always_visible is not None:
            updates["skip_links_always_visible"] = skip_links_always_visible
        if focus_highlight_enabled is not None:
            updates["focus_highlight_enabled"] = focus_highlight_enabled
        if auto_play_media is not None:
            updates["auto_play_media"] = auto_play_media
        if captions_enabled is not None:
            updates["captions_enabled"] = captions_enabled
        if audio_descriptions_enabled is not None:
            updates["audio_descriptions_enabled"] = audio_descriptions_enabled
        if extend_timeouts is not None:
            updates["extend_timeouts"] = extend_timeouts
        if timeout_multiplier is not None:
            updates["timeout_multiplier"] = timeout_multiplier
        if disable_auto_refresh is not None:
            updates["disable_auto_refresh"] = disable_auto_refresh

        updates["updated_at"] = datetime.now()

        if self.dao:
            return await self.dao.update_accessibility_preference(current.id, updates)

        # In-memory update for testing
        for key, value in updates.items():
            if hasattr(current, key):
                object.__setattr__(current, key, value)
        return current

    async def reset_user_preferences(
        self,
        user_id: UUID
    ) -> AccessibilityPreference:
        """
        Reset accessibility preferences to defaults.

        What: Resets all preferences to platform defaults.
        Where: Called from settings UI reset button.
        Why: Allows users to easily return to default settings.

        Args:
            user_id: UUID of the user

        Returns:
            Default AccessibilityPreference
        """
        self.logger.info(f"Resetting accessibility preferences for user {user_id}")

        default_prefs = create_default_preferences(user_id)

        if self.dao:
            return await self.dao.update_accessibility_preference(
                user_id,
                {
                    "font_size": default_prefs.font_size,
                    "color_scheme": default_prefs.color_scheme,
                    "motion_preference": default_prefs.motion_preference,
                    "focus_indicator_style": default_prefs.focus_indicator_style,
                    "high_contrast_mode": default_prefs.high_contrast_mode,
                    "reduce_transparency": default_prefs.reduce_transparency,
                    "screen_reader_optimizations": default_prefs.screen_reader_optimizations,
                    "announce_page_changes": default_prefs.announce_page_changes,
                    "verbose_announcements": default_prefs.verbose_announcements,
                    "keyboard_shortcuts_enabled": default_prefs.keyboard_shortcuts_enabled,
                    "skip_links_always_visible": default_prefs.skip_links_always_visible,
                    "focus_highlight_enabled": default_prefs.focus_highlight_enabled,
                    "auto_play_media": default_prefs.auto_play_media,
                    "captions_enabled": default_prefs.captions_enabled,
                    "audio_descriptions_enabled": default_prefs.audio_descriptions_enabled,
                    "extend_timeouts": default_prefs.extend_timeouts,
                    "timeout_multiplier": default_prefs.timeout_multiplier,
                    "disable_auto_refresh": default_prefs.disable_auto_refresh,
                    "updated_at": datetime.now(),
                }
            )

        return default_prefs

    # ================================================================
    # COLOR CONTRAST VALIDATION
    # ================================================================

    def validate_color_contrast(
        self,
        foreground: str,
        background: str,
        level: ColorContrastLevel = ColorContrastLevel.NORMAL_TEXT_AA,
        component_name: Optional[str] = None
    ) -> ColorContrastRequirement:
        """
        Validate color contrast ratio.

        What: Checks if two colors meet WCAG contrast requirements.
        Where: Design system validation and accessibility auditing.
        Why: Ensures text and UI elements are readable.

        Args:
            foreground: Foreground hex color (e.g., "#000000")
            background: Background hex color (e.g., "#FFFFFF")
            level: WCAG contrast level requirement
            component_name: Optional component being validated

        Returns:
            ColorContrastRequirement with validation result

        Raises:
            ValidationException: If colors are invalid
        """
        self.logger.debug(
            f"Validating contrast: {foreground} on {background} for {level.value}"
        )

        # Validate color format
        if not self._is_valid_hex_color(foreground):
            raise ValidationException(
                message="Invalid foreground color format",
                field_errors={"foreground": "Must be valid hex color (e.g., #000000)"}
            )

        if not self._is_valid_hex_color(background):
            raise ValidationException(
                message="Invalid background color format",
                field_errors={"background": "Must be valid hex color (e.g., #FFFFFF)"}
            )

        return create_contrast_check(
            foreground=foreground,
            background=background,
            level=level,
            component_name=component_name
        )

    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color code format."""
        if not color:
            return False
        color = color.lstrip('#')
        if len(color) not in [3, 6]:
            return False
        try:
            int(color, 16)
            return True
        except ValueError:
            return False

    def batch_validate_contrast(
        self,
        color_pairs: List[Dict[str, str]],
        level: ColorContrastLevel = ColorContrastLevel.NORMAL_TEXT_AA
    ) -> List[ColorContrastRequirement]:
        """
        Validate multiple color pairs at once.

        What: Batch validation of color contrast ratios.
        Where: Design system auditing.
        Why: Efficiently check multiple color combinations.

        Args:
            color_pairs: List of {"foreground": "#...", "background": "#...",
                                  "component": "optional"}
            level: WCAG contrast level requirement

        Returns:
            List of ColorContrastRequirement results
        """
        results = []
        for pair in color_pairs:
            try:
                result = self.validate_color_contrast(
                    foreground=pair["foreground"],
                    background=pair["background"],
                    level=level,
                    component_name=pair.get("component")
                )
                results.append(result)
            except ValidationException as e:
                self.logger.warning(f"Invalid color pair: {pair}, error: {e.message}")
        return results

    def get_contrast_suggestions(
        self,
        foreground: str,
        background: str,
        level: ColorContrastLevel = ColorContrastLevel.NORMAL_TEXT_AA
    ) -> Dict[str, Any]:
        """
        Get suggestions for improving color contrast.

        What: Provides recommendations for meeting contrast requirements.
        Where: Design system and accessibility settings.
        Why: Helps designers create accessible color combinations.

        Args:
            foreground: Current foreground color
            background: Current background color
            level: Target WCAG level

        Returns:
            Dictionary with current ratio, required ratio, and suggestions
        """
        check = self.validate_color_contrast(foreground, background, level)

        return {
            "current_ratio": str(check.calculated_ratio),
            "required_ratio": str(check.get_required_ratio()),
            "passes": check.passes,
            "gap": str(check.get_required_ratio() - check.calculated_ratio)
                   if not check.passes else "0",
            "suggestions": self._generate_contrast_suggestions(
                foreground, background, check
            ) if not check.passes else [],
        }

    def _generate_contrast_suggestions(
        self,
        foreground: str,
        background: str,
        check: ColorContrastRequirement
    ) -> List[str]:
        """Generate suggestions for improving contrast."""
        suggestions = []

        if not check.passes:
            suggestions.append(
                f"Increase contrast by {check.get_required_ratio() - check.calculated_ratio:.1f} "
                f"to meet {check.level.value} requirements"
            )

            # Suggest darkening foreground or lightening background
            fg_rgb = check._hex_to_rgb(foreground)
            bg_rgb = check._hex_to_rgb(background)

            if sum(fg_rgb) > sum(bg_rgb):
                # Light text on dark background
                suggestions.append("Consider using a lighter text color")
                suggestions.append("Or use a darker background color")
            else:
                # Dark text on light background
                suggestions.append("Consider using a darker text color")
                suggestions.append("Or use a lighter background color")

        return suggestions

    # ================================================================
    # KEYBOARD SHORTCUTS MANAGEMENT
    # ================================================================

    async def get_keyboard_shortcuts(
        self,
        user_id: Optional[UUID] = None,
        context: str = "global"
    ) -> List[KeyboardShortcut]:
        """
        Get keyboard shortcuts.

        What: Retrieves available keyboard shortcuts.
        Where: Keyboard navigation and help dialogs.
        Why: Enables users to see and use keyboard navigation.

        Args:
            user_id: Optional user ID for customized shortcuts
            context: Shortcut context (global, modal, form, etc.)

        Returns:
            List of KeyboardShortcut
        """
        # Start with default shortcuts
        shortcuts = []
        for shortcut_def in self.DEFAULT_SHORTCUTS:
            shortcuts.append(KeyboardShortcut(
                id=uuid4(),
                key=shortcut_def["key"],
                modifiers=shortcut_def["modifiers"],
                action=shortcut_def["action"],
                description=shortcut_def["description"],
                context="global",
                enabled=True,
                is_customizable=True,
            ))

        # Get user customizations if DAO available and user_id provided
        if self.dao and user_id:
            custom_shortcuts = await self.dao.get_user_keyboard_shortcuts(user_id)
            if custom_shortcuts:
                # Merge user customizations with defaults
                shortcut_map = {s.action: s for s in shortcuts}
                for custom in custom_shortcuts:
                    if custom.action in shortcut_map:
                        shortcut_map[custom.action] = custom
                    else:
                        shortcuts.append(custom)
                shortcuts = list(shortcut_map.values())

        # Filter by context
        if context != "all":
            shortcuts = [s for s in shortcuts if s.context == context or s.context == "global"]

        return shortcuts

    async def update_keyboard_shortcut(
        self,
        user_id: UUID,
        action: str,
        key: str,
        modifiers: List[str]
    ) -> KeyboardShortcut:
        """
        Update a keyboard shortcut for a user.

        What: Customizes a keyboard shortcut.
        Where: Accessibility settings UI.
        Why: Allows users to customize keyboard navigation.

        Args:
            user_id: UUID of the user
            action: Action to customize
            key: New key code
            modifiers: New modifier keys

        Returns:
            Updated KeyboardShortcut

        Raises:
            ValidationException: If shortcut conflicts with existing ones
        """
        self.logger.info(f"Updating keyboard shortcut for action '{action}'")

        # Validate key
        if not key:
            raise ValidationException(
                message="Key is required",
                field_errors={"key": "Cannot be empty"}
            )

        # Check for conflicts
        existing = await self.get_keyboard_shortcuts(user_id)
        for shortcut in existing:
            if shortcut.action != action:
                if (shortcut.key == key and
                    set(shortcut.modifiers) == set(modifiers)):
                    raise ValidationException(
                        message="Keyboard shortcut conflict",
                        field_errors={"key": f"Already assigned to '{shortcut.action}'"}
                    )

        shortcut = KeyboardShortcut(
            id=uuid4(),
            key=key,
            modifiers=modifiers,
            action=action,
            description=f"Custom shortcut for {action}",
            context="global",
            enabled=True,
            is_customizable=True,
        )

        if self.dao:
            return await self.dao.save_user_keyboard_shortcut(user_id, shortcut)

        return shortcut

    # ================================================================
    # SCREEN READER ANNOUNCEMENTS
    # ================================================================

    def create_announcement(
        self,
        message: str,
        politeness: str = "polite",
        atomic: bool = True,
        delay_ms: int = 0
    ) -> ScreenReaderAnnouncement:
        """
        Create a screen reader announcement.

        What: Creates an announcement for assistive technology.
        Where: Dynamic content updates and user actions.
        Why: Ensures screen reader users are informed of changes.

        Args:
            message: Message to announce
            politeness: "polite" or "assertive"
            atomic: Whether to announce entire region
            delay_ms: Delay before announcement

        Returns:
            ScreenReaderAnnouncement
        """
        if not message:
            raise ValidationException(
                message="Announcement message is required",
                field_errors={"message": "Cannot be empty"}
            )

        if politeness not in ["polite", "assertive", "off"]:
            raise ValidationException(
                message="Invalid politeness level",
                field_errors={"politeness": "Must be 'polite', 'assertive', or 'off'"}
            )

        return ScreenReaderAnnouncement(
            id=uuid4(),
            message=message,
            politeness=politeness,
            atomic=atomic,
            delay_ms=delay_ms,
        )

    def get_announcement_for_action(self, action: str, **context) -> ScreenReaderAnnouncement:
        """
        Get appropriate announcement for common actions.

        What: Creates standardized announcements for common actions.
        Where: Form submissions, navigation, state changes.
        Why: Provides consistent screen reader experience.

        Args:
            action: Action type (e.g., "form_submitted", "page_loaded")
            **context: Additional context for the announcement

        Returns:
            ScreenReaderAnnouncement
        """
        templates = {
            "form_submitted": "Form submitted successfully",
            "form_error": f"Form has {context.get('error_count', 1)} error(s). Please review.",
            "page_loaded": f"Page loaded: {context.get('page_title', 'New page')}",
            "loading_started": "Loading content, please wait",
            "loading_complete": "Content loaded",
            "item_selected": f"{context.get('item_name', 'Item')} selected",
            "item_deleted": f"{context.get('item_name', 'Item')} deleted",
            "modal_opened": f"Dialog opened: {context.get('modal_title', 'Dialog')}",
            "modal_closed": "Dialog closed",
            "notification": context.get("message", "New notification"),
        }

        message = templates.get(action, f"Action: {action}")
        politeness = "assertive" if action in ["form_error", "notification"] else "polite"

        return self.create_announcement(message, politeness)

    # ================================================================
    # ACCESSIBILITY AUDITING
    # ================================================================

    async def create_audit_result(
        self,
        page_url: str,
        rule_id: str,
        description: str,
        severity: AuditSeverity = AuditSeverity.MODERATE,
        category: AuditCategory = AuditCategory.PERCEIVABLE,
        element: Optional[str] = None,
        html_snippet: Optional[str] = None,
        recommended_fix: Optional[str] = None,
        audit_tool: str = "manual"
    ) -> AccessibilityAuditResult:
        """
        Create an accessibility audit result.

        What: Records an accessibility issue found during audit.
        Where: Automated and manual accessibility auditing.
        Why: Tracks issues for remediation.

        Args:
            page_url: URL of the audited page
            rule_id: WCAG rule ID (e.g., "color-contrast")
            description: Description of the issue
            severity: Issue severity
            category: WCAG principle category
            element: CSS selector of affected element
            html_snippet: HTML code of affected element
            recommended_fix: Suggested fix
            audit_tool: Tool used for audit

        Returns:
            AccessibilityAuditResult

        Raises:
            ValidationException: If required fields are missing
        """
        self.logger.info(f"Creating audit result for {page_url}: {rule_id}")

        if not page_url:
            raise ValidationException(
                message="Page URL is required",
                field_errors={"page_url": "Cannot be empty"}
            )

        if not rule_id:
            raise ValidationException(
                message="Rule ID is required",
                field_errors={"rule_id": "Cannot be empty"}
            )

        if not description:
            raise ValidationException(
                message="Issue description is required",
                field_errors={"description": "Cannot be empty"}
            )

        result = create_audit_issue(
            page_url=page_url,
            rule_id=rule_id,
            description=description,
            severity=severity,
            category=category,
            element=element,
            fix=recommended_fix,
        )

        if html_snippet:
            result.html_snippet = html_snippet
        result.audit_tool = audit_tool

        if self.dao:
            return await self.dao.create_audit_result(result)

        return result

    async def mark_issue_fixed(
        self,
        audit_id: UUID,
        fixed_by: UUID
    ) -> AccessibilityAuditResult:
        """
        Mark an accessibility issue as fixed.

        What: Updates audit result to fixed status.
        Where: Remediation tracking.
        Why: Tracks accessibility improvement progress.

        Args:
            audit_id: UUID of the audit result
            fixed_by: UUID of the user who fixed the issue

        Returns:
            Updated AccessibilityAuditResult
        """
        self.logger.info(f"Marking audit issue {audit_id} as fixed")

        if self.dao:
            result = await self.dao.get_audit_result(audit_id)
            if not result:
                raise ValidationException(
                    message="Audit result not found",
                    field_errors={"audit_id": str(audit_id)}
                )

            result.mark_fixed(fixed_by)
            return await self.dao.update_audit_result(audit_id, {
                "is_fixed": True,
                "fixed_at": result.fixed_at,
                "fixed_by": fixed_by,
            })

        # For testing without DAO
        result = AccessibilityAuditResult(
            id=audit_id,
            page_url="/test",
            rule_id="test",
            issue_description="Test issue",
        )
        result.mark_fixed(fixed_by)
        return result

    async def get_page_audit_results(
        self,
        page_url: str,
        include_fixed: bool = False
    ) -> List[AccessibilityAuditResult]:
        """
        Get audit results for a specific page.

        What: Retrieves accessibility issues for a page.
        Where: Page-level accessibility reporting.
        Why: Shows current accessibility status of a page.

        Args:
            page_url: URL of the page
            include_fixed: Whether to include fixed issues

        Returns:
            List of AccessibilityAuditResult
        """
        if self.dao:
            results = await self.dao.get_audit_results_by_page(page_url)
            if not include_fixed:
                results = [r for r in results if not r.is_fixed]
            return results
        return []

    # ================================================================
    # COMPLIANCE REPORTING
    # ================================================================

    async def generate_compliance_report(
        self,
        organization_id: UUID,
        wcag_level: WCAGLevel = WCAGLevel.AA,
        generated_by: Optional[UUID] = None
    ) -> AccessibilityComplianceReport:
        """
        Generate an accessibility compliance report.

        What: Creates organization-wide compliance summary.
        Where: Accessibility dashboards and executive reporting.
        Why: Provides overview of accessibility status.

        Args:
            organization_id: UUID of the organization
            wcag_level: Target WCAG level
            generated_by: UUID of the user generating report

        Returns:
            AccessibilityComplianceReport
        """
        self.logger.info(f"Generating compliance report for org {organization_id}")

        report = AccessibilityComplianceReport(
            id=uuid4(),
            organization_id=organization_id,
            wcag_level=wcag_level,
            generated_by=generated_by,
        )

        if self.dao:
            # Get all audit results for organization
            results = await self.dao.get_audit_results_by_organization(organization_id)

            pages_audited = set()
            for result in results:
                pages_audited.add(result.page_url)
                report.audit_results.append(result.id)

                if not result.is_fixed:
                    report.total_issues += 1
                    if result.severity == AuditSeverity.CRITICAL:
                        report.critical_issues += 1
                    elif result.severity == AuditSeverity.SERIOUS:
                        report.serious_issues += 1
                    elif result.severity == AuditSeverity.MODERATE:
                        report.moderate_issues += 1
                    else:
                        report.minor_issues += 1
                else:
                    report.issues_fixed += 1

            report.pages_audited = len(pages_audited)
            report.compliance_score = report.calculate_compliance_score()

            await self.dao.save_compliance_report(report)

        return report

    async def get_compliance_history(
        self,
        organization_id: UUID,
        limit: int = 10
    ) -> List[AccessibilityComplianceReport]:
        """
        Get compliance report history.

        What: Retrieves past compliance reports.
        Where: Trend analysis and progress tracking.
        Why: Shows accessibility improvement over time.

        Args:
            organization_id: UUID of the organization
            limit: Maximum reports to return

        Returns:
            List of AccessibilityComplianceReport ordered by date
        """
        if self.dao:
            return await self.dao.get_compliance_reports(organization_id, limit)
        return []

    def get_wcag_criteria_info(self, rule_id: str) -> Dict[str, Any]:
        """
        Get WCAG criteria information for a rule.

        What: Provides WCAG reference information.
        Where: Audit details and educational content.
        Why: Helps users understand accessibility requirements.

        Args:
            rule_id: Accessibility rule ID

        Returns:
            Dictionary with WCAG criteria details
        """
        criteria_info = {
            "color-contrast": {
                "criteria": "1.4.3",
                "level": "AA",
                "title": "Contrast (Minimum)",
                "description": "Text and images of text have a contrast ratio of at least 4.5:1",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
            },
            "image-alt": {
                "criteria": "1.1.1",
                "level": "A",
                "title": "Non-text Content",
                "description": "All non-text content has text alternatives",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html",
            },
            "label": {
                "criteria": "1.3.1",
                "level": "A",
                "title": "Info and Relationships",
                "description": "Information and relationships are programmatically determined",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
            },
            "link-name": {
                "criteria": "2.4.4",
                "level": "A",
                "title": "Link Purpose (In Context)",
                "description": "Purpose of each link can be determined from link text",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html",
            },
            "button-name": {
                "criteria": "4.1.2",
                "level": "A",
                "title": "Name, Role, Value",
                "description": "All UI components have accessible names",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html",
            },
            "keyboard": {
                "criteria": "2.1.1",
                "level": "A",
                "title": "Keyboard",
                "description": "All functionality is operable via keyboard",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html",
            },
            "focus-visible": {
                "criteria": "2.4.7",
                "level": "AA",
                "title": "Focus Visible",
                "description": "Keyboard focus indicator is visible",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html",
            },
            "skip-link": {
                "criteria": "2.4.1",
                "level": "A",
                "title": "Bypass Blocks",
                "description": "Mechanism to skip repeated content",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
            },
            "heading-order": {
                "criteria": "1.3.1",
                "level": "A",
                "title": "Info and Relationships (Headings)",
                "description": "Headings are used in proper order",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
            },
        }

        return criteria_info.get(rule_id, {
            "criteria": "Unknown",
            "level": "Unknown",
            "title": "Unknown Rule",
            "description": f"No information available for rule: {rule_id}",
            "url": "https://www.w3.org/WAI/WCAG21/",
        })
