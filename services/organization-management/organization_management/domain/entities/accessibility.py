"""
Accessibility Domain Entities

What: Domain entities for accessibility features and WCAG compliance.
Where: Organization Management service domain layer.
Why: Provides:
     1. User accessibility preferences management
     2. WCAG 2.1 AA compliance tracking
     3. Color contrast validation rules
     4. Keyboard navigation configuration
     5. Screen reader optimization settings
     6. Accessibility audit result tracking

BUSINESS CONTEXT:
Accessibility is a critical feature for educational platforms. These entities enable:
- Users with disabilities to customize their experience
- Organizations to track WCAG compliance
- Instructors to create accessible course content
- Platform-wide accessibility auditing and reporting

WCAG 2.1 Compliance Levels:
- Level A: Essential accessibility features
- Level AA: Recommended accessibility features (our target)
- Level AAA: Enhanced accessibility features

Technical Implementation:
- Dataclasses for immutable domain objects
- Enums for controlled vocabulary
- Validation methods for business rules
- Factory methods for common creation patterns
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


# =============================================================================
# ENUMS - Accessibility Configuration
# =============================================================================

class WCAGLevel(Enum):
    """
    WCAG Compliance Levels.

    What: Defines WCAG 2.1 compliance level targets.
    Where: Used in accessibility audits and preference settings.
    Why: Provides standard compliance level vocabulary for accessibility features.
    """
    A = "A"           # Essential accessibility
    AA = "AA"         # Recommended (target)
    AAA = "AAA"       # Enhanced accessibility


class ColorContrastLevel(Enum):
    """
    Color Contrast Ratio Requirements.

    What: Defines minimum contrast ratios for WCAG compliance.
    Where: Used in color contrast validation.
    Why: Ensures text and UI elements meet visibility requirements.

    WCAG Requirements:
    - NORMAL_TEXT_AA: 4.5:1 ratio for text < 18pt (or < 14pt bold)
    - LARGE_TEXT_AA: 3:1 ratio for text >= 18pt (or >= 14pt bold)
    - NORMAL_TEXT_AAA: 7:1 ratio for enhanced contrast
    - LARGE_TEXT_AAA: 4.5:1 ratio for enhanced contrast
    - UI_COMPONENT: 3:1 ratio for graphical objects and UI components
    """
    NORMAL_TEXT_AA = "normal_text_aa"       # 4.5:1
    LARGE_TEXT_AA = "large_text_aa"         # 3:1
    NORMAL_TEXT_AAA = "normal_text_aaa"     # 7:1
    LARGE_TEXT_AAA = "large_text_aaa"       # 4.5:1
    UI_COMPONENT = "ui_component"           # 3:1


class FontSizePreference(Enum):
    """
    Font Size Preference Options.

    What: User-selectable font size preferences.
    Where: Accessibility settings UI and rendering.
    Why: Supports users who need larger text for readability.
    """
    DEFAULT = "default"     # Browser default
    LARGE = "large"         # 125%
    EXTRA_LARGE = "xlarge"  # 150%
    HUGE = "huge"           # 200%


class MotionPreference(Enum):
    """
    Motion and Animation Preferences.

    What: Controls animation and motion settings.
    Where: Accessibility settings and CSS rendering.
    Why: Supports users with vestibular disorders or motion sensitivity.

    Relates to WCAG 2.3.3 (Animation from Interactions).
    """
    NO_PREFERENCE = "no_preference"  # Use system default
    REDUCE = "reduce"                # Minimize non-essential motion
    NO_MOTION = "no_motion"          # Disable all animations


class ColorSchemePreference(Enum):
    """
    Color Scheme Preferences.

    What: User-selectable color scheme options.
    Where: Theme settings and CSS rendering.
    Why: Supports users who need specific color schemes for accessibility.
    """
    SYSTEM = "system"           # Follow system preference
    LIGHT = "light"             # Light background, dark text
    DARK = "dark"               # Dark background, light text
    HIGH_CONTRAST = "high_contrast"  # Maximum contrast


class FocusIndicatorStyle(Enum):
    """
    Focus Indicator Style Options.

    What: Visual style for keyboard focus indicators.
    Where: Accessibility settings and CSS rendering.
    Why: Supports users who need more visible focus indicators.

    Relates to WCAG 2.4.7 (Focus Visible).
    """
    DEFAULT = "default"         # Standard 2px outline
    ENHANCED = "enhanced"       # 3px outline with offset
    HIGH_VISIBILITY = "high_visibility"  # 4px solid with glow effect


class AuditSeverity(Enum):
    """
    Accessibility Audit Issue Severity Levels.

    What: Severity classification for accessibility issues.
    Where: Audit results and compliance reporting.
    Why: Prioritizes accessibility fixes by impact.
    """
    CRITICAL = "critical"   # Blocks access to content
    SERIOUS = "serious"     # Significantly impairs access
    MODERATE = "moderate"   # Causes difficulty
    MINOR = "minor"         # Inconvenience


class AuditCategory(Enum):
    """
    Accessibility Audit Categories.

    What: WCAG principle categories for accessibility issues.
    Where: Audit organization and reporting.
    Why: Groups issues by WCAG principle for systematic remediation.
    """
    PERCEIVABLE = "perceivable"       # Content must be presentable
    OPERABLE = "operable"             # UI must be operable
    UNDERSTANDABLE = "understandable" # Info must be understandable
    ROBUST = "robust"                 # Content must be robust


class KeyboardNavigationType(Enum):
    """
    Types of Keyboard Navigation Patterns.

    What: Standard keyboard navigation patterns for accessibility.
    Where: Component keyboard event handling.
    Why: Ensures consistent keyboard navigation across the platform.
    """
    TAB_NAVIGATION = "tab"          # Tab/Shift+Tab between elements
    ARROW_NAVIGATION = "arrow"      # Arrow keys within composite widgets
    ROVING_TABINDEX = "roving"      # Single tab stop with arrow navigation
    FOCUS_TRAP = "focus_trap"       # Keeps focus within modal/dialog


# =============================================================================
# DOMAIN ENTITIES - Accessibility Preferences
# =============================================================================

@dataclass
class AccessibilityPreference:
    """
    User Accessibility Preferences.

    What: Stores individual user accessibility settings.
    Where: User profile and session management.
    Why: Enables personalized accessibility features including:
         - Font size adjustments
         - Motion reduction
         - Color scheme preferences
         - Focus indicator customization
         - Screen reader optimizations

    Technical Implementation:
    - Stored per user in database
    - Cached in session for performance
    - Applied via CSS custom properties
    - Synced with system preferences if enabled
    """
    id: UUID
    user_id: UUID

    # Visual Preferences
    font_size: FontSizePreference = FontSizePreference.DEFAULT
    color_scheme: ColorSchemePreference = ColorSchemePreference.SYSTEM
    focus_indicator_style: FocusIndicatorStyle = FocusIndicatorStyle.DEFAULT
    high_contrast_mode: bool = False

    # Motion Preferences
    motion_preference: MotionPreference = MotionPreference.NO_PREFERENCE
    reduce_transparency: bool = False

    # Screen Reader Optimizations
    screen_reader_optimizations: bool = False
    announce_page_changes: bool = True
    verbose_announcements: bool = False

    # Keyboard Navigation
    keyboard_shortcuts_enabled: bool = True
    skip_links_always_visible: bool = False
    focus_highlight_enabled: bool = True

    # Audio/Visual Preferences
    auto_play_media: bool = False
    captions_enabled: bool = True
    audio_descriptions_enabled: bool = False

    # Timing Preferences
    extend_timeouts: bool = False
    timeout_multiplier: Decimal = Decimal("1.0")
    disable_auto_refresh: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate preference values on initialization."""
        if not self.id:
            raise ValueError("Preference ID is required")
        if not self.user_id:
            raise ValueError("User ID is required")
        if self.timeout_multiplier < Decimal("1.0"):
            raise ValueError("Timeout multiplier must be at least 1.0")
        if self.timeout_multiplier > Decimal("5.0"):
            raise ValueError("Timeout multiplier cannot exceed 5.0")

    def get_font_size_multiplier(self) -> Decimal:
        """
        Get CSS font size multiplier based on preference.

        What: Converts font size preference to CSS multiplier.
        Where: Applied to root CSS font-size.
        Why: Enables consistent font scaling across the platform.
        """
        multipliers = {
            FontSizePreference.DEFAULT: Decimal("1.0"),
            FontSizePreference.LARGE: Decimal("1.25"),
            FontSizePreference.EXTRA_LARGE: Decimal("1.5"),
            FontSizePreference.HUGE: Decimal("2.0"),
        }
        return multipliers[self.font_size]

    def get_animation_duration_multiplier(self) -> Decimal:
        """
        Get animation duration multiplier based on motion preference.

        What: Converts motion preference to animation speed.
        Where: Applied to CSS transition durations.
        Why: Enables motion reduction for users with vestibular disorders.
        """
        if self.motion_preference == MotionPreference.NO_MOTION:
            return Decimal("0")
        elif self.motion_preference == MotionPreference.REDUCE:
            return Decimal("0.3")
        return Decimal("1.0")

    def needs_screen_reader_support(self) -> bool:
        """Check if screen reader optimizations are needed."""
        return (
            self.screen_reader_optimizations or
            self.verbose_announcements or
            self.announce_page_changes
        )

    def to_css_custom_properties(self) -> Dict[str, str]:
        """
        Convert preferences to CSS custom properties.

        What: Generates CSS custom properties for accessibility settings.
        Where: Applied to document root element.
        Why: Enables CSS-based accessibility customization.
        """
        return {
            "--a11y-font-size-multiplier": str(self.get_font_size_multiplier()),
            "--a11y-animation-multiplier": str(self.get_animation_duration_multiplier()),
            "--a11y-reduce-transparency": "0.5" if self.reduce_transparency else "0",
            "--a11y-focus-ring-width": (
                "4px" if self.focus_indicator_style == FocusIndicatorStyle.HIGH_VISIBILITY
                else "3px" if self.focus_indicator_style == FocusIndicatorStyle.ENHANCED
                else "2px"
            ),
        }


@dataclass
class ColorContrastRequirement:
    """
    Color Contrast Validation Requirements.

    What: Defines and validates color contrast ratios.
    Where: Design system and accessibility auditing.
    Why: Ensures WCAG 2.1 color contrast compliance.

    WCAG Color Contrast Requirements:
    - 4.5:1 for normal text (Level AA)
    - 3:1 for large text (Level AA)
    - 7:1 for normal text (Level AAA)
    - 4.5:1 for large text (Level AAA)
    - 3:1 for UI components and graphical objects
    """
    id: UUID
    level: ColorContrastLevel
    foreground_color: str  # Hex color code
    background_color: str  # Hex color code
    calculated_ratio: Decimal = Decimal("0")
    passes: bool = False
    component_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate color codes and calculate contrast ratio."""
        if not self.id:
            raise ValueError("Requirement ID is required")
        if not self._is_valid_hex_color(self.foreground_color):
            raise ValueError(f"Invalid foreground color: {self.foreground_color}")
        if not self._is_valid_hex_color(self.background_color):
            raise ValueError(f"Invalid background color: {self.background_color}")

        # Calculate contrast ratio if not provided
        if self.calculated_ratio == Decimal("0"):
            self.calculated_ratio = self._calculate_contrast_ratio()

        # Validate against requirements
        self.passes = self._validate_contrast()

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

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _get_relative_luminance(self, rgb: tuple) -> Decimal:
        """
        Calculate relative luminance per WCAG 2.1.

        Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
        Where R, G, B are linearized sRGB values.
        """
        def linearize(value: int) -> Decimal:
            v = Decimal(value) / Decimal(255)
            if v <= Decimal("0.03928"):
                return v / Decimal("12.92")
            return ((v + Decimal("0.055")) / Decimal("1.055")) ** Decimal("2.4")

        r, g, b = rgb
        return (
            Decimal("0.2126") * linearize(r) +
            Decimal("0.7152") * linearize(g) +
            Decimal("0.0722") * linearize(b)
        )

    def _calculate_contrast_ratio(self) -> Decimal:
        """
        Calculate contrast ratio between foreground and background.

        Formula: (L1 + 0.05) / (L2 + 0.05)
        Where L1 is the lighter luminance and L2 is the darker.
        """
        fg_rgb = self._hex_to_rgb(self.foreground_color)
        bg_rgb = self._hex_to_rgb(self.background_color)

        fg_lum = self._get_relative_luminance(fg_rgb)
        bg_lum = self._get_relative_luminance(bg_rgb)

        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)

        ratio = (lighter + Decimal("0.05")) / (darker + Decimal("0.05"))
        return ratio.quantize(Decimal("0.01"))

    def _validate_contrast(self) -> bool:
        """Validate contrast ratio against requirement level."""
        requirements = {
            ColorContrastLevel.NORMAL_TEXT_AA: Decimal("4.5"),
            ColorContrastLevel.LARGE_TEXT_AA: Decimal("3.0"),
            ColorContrastLevel.NORMAL_TEXT_AAA: Decimal("7.0"),
            ColorContrastLevel.LARGE_TEXT_AAA: Decimal("4.5"),
            ColorContrastLevel.UI_COMPONENT: Decimal("3.0"),
        }
        required_ratio = requirements[self.level]
        return self.calculated_ratio >= required_ratio

    def get_required_ratio(self) -> Decimal:
        """Get the minimum required ratio for this level."""
        requirements = {
            ColorContrastLevel.NORMAL_TEXT_AA: Decimal("4.5"),
            ColorContrastLevel.LARGE_TEXT_AA: Decimal("3.0"),
            ColorContrastLevel.NORMAL_TEXT_AAA: Decimal("7.0"),
            ColorContrastLevel.LARGE_TEXT_AAA: Decimal("4.5"),
            ColorContrastLevel.UI_COMPONENT: Decimal("3.0"),
        }
        return requirements[self.level]


@dataclass
class KeyboardShortcut:
    """
    Keyboard Shortcut Configuration.

    What: Defines keyboard shortcuts for accessibility navigation.
    Where: Application-wide keyboard event handling.
    Why: Enables efficient keyboard-only navigation.

    WCAG Reference:
    - 2.1.1 Keyboard (Level A)
    - 2.1.4 Character Key Shortcuts (Level A)
    """
    id: UUID
    key: str  # Key code (e.g., "KeyS", "Enter", "Escape")
    modifiers: List[str] = field(default_factory=list)  # ["ctrl", "alt", "shift"]
    action: str = ""  # Action to perform
    description: str = ""  # Human-readable description
    context: str = "global"  # Where shortcut is active
    enabled: bool = True
    is_customizable: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate shortcut configuration."""
        if not self.id:
            raise ValueError("Shortcut ID is required")
        if not self.key:
            raise ValueError("Key is required")
        if not self.action:
            raise ValueError("Action is required")

        # Validate modifiers
        valid_modifiers = {"ctrl", "alt", "shift", "meta"}
        for mod in self.modifiers:
            if mod.lower() not in valid_modifiers:
                raise ValueError(f"Invalid modifier: {mod}")

    def get_shortcut_string(self) -> str:
        """
        Get human-readable shortcut string.

        Returns:
            String like "Ctrl+Shift+S" or "Enter"
        """
        parts = [mod.capitalize() for mod in sorted(self.modifiers)]
        parts.append(self.key)
        return "+".join(parts)

    def matches_event(self, event_key: str, ctrl: bool = False,
                      alt: bool = False, shift: bool = False,
                      meta: bool = False) -> bool:
        """Check if keyboard event matches this shortcut."""
        if event_key != self.key:
            return False

        expected_mods = set(m.lower() for m in self.modifiers)
        actual_mods = set()
        if ctrl:
            actual_mods.add("ctrl")
        if alt:
            actual_mods.add("alt")
        if shift:
            actual_mods.add("shift")
        if meta:
            actual_mods.add("meta")

        return expected_mods == actual_mods


@dataclass
class ScreenReaderAnnouncement:
    """
    Screen Reader Announcement Configuration.

    What: Configures announcements for assistive technology.
    Where: Dynamic content updates and user actions.
    Why: Ensures screen reader users are informed of changes.

    WCAG Reference:
    - 4.1.3 Status Messages (Level AA)
    """
    id: UUID
    message: str
    politeness: str = "polite"  # "polite", "assertive", "off"
    atomic: bool = True  # Announce entire region
    relevant: str = "additions text"  # What changes to announce
    live_region_id: Optional[str] = None
    delay_ms: int = 0  # Delay before announcement
    clear_after_ms: Optional[int] = None  # Clear message after delay
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate announcement configuration."""
        if not self.id:
            raise ValueError("Announcement ID is required")
        if not self.message:
            raise ValueError("Message is required")
        if self.politeness not in ["polite", "assertive", "off"]:
            raise ValueError(f"Invalid politeness level: {self.politeness}")
        if self.delay_ms < 0:
            raise ValueError("Delay cannot be negative")


@dataclass
class AccessibilityAuditResult:
    """
    Accessibility Audit Result.

    What: Stores results from accessibility audits.
    Where: Compliance tracking and remediation planning.
    Why: Enables systematic tracking of accessibility issues and fixes.

    Technical Implementation:
    - Generated by axe-core or similar tools
    - Stored for historical tracking
    - Used for compliance reporting
    """
    id: UUID
    page_url: str
    wcag_level: WCAGLevel = WCAGLevel.AA
    category: AuditCategory = AuditCategory.PERCEIVABLE
    severity: AuditSeverity = AuditSeverity.MODERATE
    rule_id: str = ""  # e.g., "color-contrast"
    issue_description: str = ""
    affected_element: Optional[str] = None  # CSS selector
    html_snippet: Optional[str] = None
    recommended_fix: Optional[str] = None
    is_fixed: bool = False
    fixed_at: Optional[datetime] = None
    fixed_by: Optional[UUID] = None
    audit_tool: str = "manual"  # "axe-core", "manual", "lighthouse"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate audit result."""
        if not self.id:
            raise ValueError("Audit result ID is required")
        if not self.page_url:
            raise ValueError("Page URL is required")
        if not self.rule_id:
            raise ValueError("Rule ID is required")
        if not self.issue_description:
            raise ValueError("Issue description is required")

    def mark_fixed(self, fixed_by: UUID) -> None:
        """Mark this issue as fixed."""
        self.is_fixed = True
        self.fixed_at = datetime.now()
        self.fixed_by = fixed_by

    def get_wcag_criteria(self) -> str:
        """
        Get WCAG success criteria reference.

        Common mappings from rule_id to WCAG criteria.
        """
        criteria_map = {
            "color-contrast": "1.4.3",
            "image-alt": "1.1.1",
            "label": "1.3.1",
            "link-name": "2.4.4",
            "button-name": "4.1.2",
            "heading-order": "1.3.1",
            "landmark-one-main": "1.3.1",
            "region": "1.3.1",
            "skip-link": "2.4.1",
            "focus-visible": "2.4.7",
            "keyboard": "2.1.1",
        }
        return criteria_map.get(self.rule_id, "Unknown")


@dataclass
class AccessibilityComplianceReport:
    """
    Accessibility Compliance Report.

    What: Aggregates audit results into compliance report.
    Where: Reporting and executive dashboards.
    Why: Provides overview of accessibility status.
    """
    id: UUID
    organization_id: UUID
    report_date: datetime = field(default_factory=datetime.now)
    wcag_level: WCAGLevel = WCAGLevel.AA
    pages_audited: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    serious_issues: int = 0
    moderate_issues: int = 0
    minor_issues: int = 0
    issues_fixed: int = 0
    compliance_score: Decimal = Decimal("0")
    generated_by: Optional[UUID] = None
    audit_results: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        """Validate report data."""
        if not self.id:
            raise ValueError("Report ID is required")
        if not self.organization_id:
            raise ValueError("Organization ID is required")

    def calculate_compliance_score(self) -> Decimal:
        """
        Calculate compliance score as percentage.

        Formula: ((total - critical*4 - serious*3 - moderate*2 - minor) /
                  max_score) * 100
        """
        if self.pages_audited == 0:
            return Decimal("100")  # No pages = 100% compliant

        # Weight issues by severity
        weighted_issues = (
            self.critical_issues * 4 +
            self.serious_issues * 3 +
            self.moderate_issues * 2 +
            self.minor_issues
        )

        # Maximum theoretical issues (arbitrary scale)
        max_weighted = self.pages_audited * 40

        if weighted_issues >= max_weighted:
            return Decimal("0")

        score = Decimal(100) * (Decimal(1) - Decimal(weighted_issues) / Decimal(max_weighted))
        return score.quantize(Decimal("0.1"))

    def get_summary(self) -> Dict[str, Any]:
        """Get report summary for display."""
        return {
            "report_date": self.report_date.isoformat(),
            "wcag_level": self.wcag_level.value,
            "pages_audited": self.pages_audited,
            "total_issues": self.total_issues,
            "issues_by_severity": {
                "critical": self.critical_issues,
                "serious": self.serious_issues,
                "moderate": self.moderate_issues,
                "minor": self.minor_issues,
            },
            "issues_fixed": self.issues_fixed,
            "compliance_score": str(self.compliance_score),
            "pass_rate": f"{self.compliance_score}%",
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_default_preferences(user_id: UUID) -> AccessibilityPreference:
    """
    Create default accessibility preferences for a new user.

    What: Factory function for creating initial preferences.
    Where: User registration and preference initialization.
    Why: Ensures all users have sensible default settings.
    """
    return AccessibilityPreference(
        id=uuid4(),
        user_id=user_id,
        font_size=FontSizePreference.DEFAULT,
        color_scheme=ColorSchemePreference.SYSTEM,
        motion_preference=MotionPreference.NO_PREFERENCE,
        keyboard_shortcuts_enabled=True,
        captions_enabled=True,
    )


def create_contrast_check(
    foreground: str,
    background: str,
    level: ColorContrastLevel = ColorContrastLevel.NORMAL_TEXT_AA,
    component_name: Optional[str] = None
) -> ColorContrastRequirement:
    """
    Create a color contrast check.

    What: Factory function for contrast validation.
    Where: Design system and component testing.
    Why: Simplifies contrast ratio checking.
    """
    return ColorContrastRequirement(
        id=uuid4(),
        level=level,
        foreground_color=foreground,
        background_color=background,
        component_name=component_name,
    )


def create_audit_issue(
    page_url: str,
    rule_id: str,
    description: str,
    severity: AuditSeverity = AuditSeverity.MODERATE,
    category: AuditCategory = AuditCategory.PERCEIVABLE,
    element: Optional[str] = None,
    fix: Optional[str] = None,
) -> AccessibilityAuditResult:
    """
    Create an accessibility audit issue.

    What: Factory function for audit results.
    Where: Automated and manual accessibility auditing.
    Why: Standardizes audit issue creation.
    """
    return AccessibilityAuditResult(
        id=uuid4(),
        page_url=page_url,
        rule_id=rule_id,
        issue_description=description,
        severity=severity,
        category=category,
        affected_element=element,
        recommended_fix=fix,
    )
