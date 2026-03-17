"""
SlideTemplate Domain Entity - Organization-Level Presentation Branding

This module defines the SlideTemplate domain entity, which represents customizable
presentation templates that organizations can apply to their course slides for
consistent branding and professional appearance.

BUSINESS PURPOSE:
Slide templates enable organizations to maintain brand consistency across all
educational content. Templates define visual styling, headers, footers, and
branding elements that are automatically applied to course presentations.

DOMAIN RESPONSIBILITY:
1. Template Configuration Management: Store and validate template settings
2. Branding Elements: Logo, colors, fonts, and styling configuration
3. Header/Footer Content: Organization-specific content for slides
4. Default Template Selection: One default template per organization

BUSINESS RULES:
1. Templates belong to exactly one organization (organization_id required)
2. Template names must be unique within an organization
3. Only one template can be marked as default per organization
4. Templates can be active or inactive for soft-delete functionality
5. Template configuration follows a standardized JSON schema

TEMPLATE CONFIGURATION SCHEMA:
{
    "theme": "default|dark|light|custom",
    "primaryColor": "#hex",
    "secondaryColor": "#hex",
    "fontFamily": "font-name",
    "headerStyle": { CSS properties },
    "footerStyle": { CSS properties },
    "slideStyle": { CSS properties }
}
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TemplateTheme(Enum):
    """
    Predefined template themes for quick styling selection.

    DEFAULT: Clean, professional appearance with neutral colors
    DARK: Dark background with light text for modern look
    LIGHT: Light background with dark text for readability
    CORPORATE: Formal business-appropriate styling
    CUSTOM: User-defined custom styling via template_config
    """
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    CORPORATE = "corporate"
    CUSTOM = "custom"


@dataclass
class SlideTemplate:
    """
    Organization-level slide template for consistent course presentation branding.

    DOMAIN RESPONSIBILITIES:
    1. Template Identity: Name and description for template management
    2. Visual Configuration: Theme, colors, fonts, and styling
    3. Branding Content: Logo, header, and footer HTML content
    4. Lifecycle Management: Active/inactive status and default selection
    5. Audit Trail: Creator, updater, and timestamp tracking

    BUSINESS RULES ENFORCED:
    - Template name is required and cannot be empty
    - Organization ID is required (templates belong to organizations)
    - Template configuration must be valid JSON structure
    - Only one default template per organization (enforced at DB level)

    USAGE PATTERNS:
    1. Organization admin creates template with branding elements
    2. Template is applied to course slides during content generation
    3. Slides inherit template styling for consistent presentation
    4. Multiple templates allow different branding for different contexts

    Example:
        >>> template = SlideTemplate(
        ...     name="Corporate Training",
        ...     organization_id="org-123",
        ...     template_config={
        ...         "theme": "corporate",
        ...         "primaryColor": "#1976d2",
        ...         "fontFamily": "Arial, sans-serif"
        ...     },
        ...     logo_url="https://example.com/logo.png",
        ...     is_default=True
        ... )
    """
    # Required fields
    name: str
    organization_id: str

    # Template configuration
    template_config: Dict[str, Any] = field(default_factory=lambda: {
        "theme": "default",
        "primaryColor": "#1976d2",
        "secondaryColor": "#dc004e",
        "fontFamily": "Roboto, sans-serif",
        "headerStyle": {},
        "footerStyle": {},
        "slideStyle": {}
    })

    # Optional identification
    id: Optional[str] = None
    description: Optional[str] = None

    # Header/footer content
    header_html: Optional[str] = None
    footer_html: Optional[str] = None

    # Branding assets
    logo_url: Optional[str] = None
    background_image_url: Optional[str] = None

    # Status flags
    is_default: bool = False
    is_active: bool = True

    # Audit fields
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """
        Execute post-initialization validation after dataclass creation.

        Validates all business rules immediately upon object creation,
        implementing the fail-fast principle of Domain-Driven Design.
        """
        self.validate()

    def validate(self) -> None:
        """
        Validate all business rules for slide template entity.

        BUSINESS RULES ENFORCED:
        1. Template name is required and non-empty
        2. Template name cannot exceed 100 characters
        3. Organization ID is required
        4. Description cannot exceed 500 characters
        5. Template config must be a valid dictionary

        Raises:
            ValueError: If any business rule is violated
        """
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Template name cannot be empty")

        if len(self.name) > 100:
            raise ValueError("Template name cannot exceed 100 characters")

        if not self.organization_id:
            raise ValueError("Template must belong to an organization")

        if self.description and len(self.description) > 500:
            raise ValueError("Template description cannot exceed 500 characters")

        if not isinstance(self.template_config, dict):
            raise ValueError("Template configuration must be a dictionary")

        # Validate URL formats if provided
        if self.logo_url and len(self.logo_url) > 500:
            raise ValueError("Logo URL cannot exceed 500 characters")

        if self.background_image_url and len(self.background_image_url) > 500:
            raise ValueError("Background image URL cannot exceed 500 characters")

    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update template configuration with partial updates.

        Merges new configuration values with existing configuration,
        allowing selective updates without requiring full config replacement.

        Args:
            config_updates: Dictionary of configuration values to update

        Example:
            >>> template.update_config({"primaryColor": "#ff5722"})
        """
        if not isinstance(config_updates, dict):
            raise ValueError("Configuration updates must be a dictionary")

        self.template_config.update(config_updates)
        self.updated_at = datetime.utcnow()

    def set_as_default(self) -> None:
        """
        Mark this template as the default for its organization.

        Note: The database trigger ensures only one default template
        per organization. Setting this template as default will
        automatically unset any existing default template.
        """
        self.is_default = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Soft-delete template by marking it as inactive.

        Inactive templates are not shown in template selection UI
        but remain in the database for historical reference and
        potential reactivation.
        """
        self.is_active = False
        self.is_default = False  # Cannot be default if inactive
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Reactivate a previously deactivated template.
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def get_theme(self) -> str:
        """
        Get the current theme name from template configuration.

        Returns:
            str: Theme name (default, dark, light, corporate, custom)
        """
        return self.template_config.get("theme", "default")

    def get_primary_color(self) -> str:
        """
        Get the primary color from template configuration.

        Returns:
            str: Primary color hex code
        """
        return self.template_config.get("primaryColor", "#1976d2")

    def get_font_family(self) -> str:
        """
        Get the font family from template configuration.

        Returns:
            str: CSS font-family value
        """
        return self.template_config.get("fontFamily", "Roboto, sans-serif")

    def to_css_variables(self) -> Dict[str, str]:
        """
        Convert template configuration to CSS custom properties.

        Generates a dictionary of CSS variable names and values
        that can be applied to slide elements for consistent styling.

        Returns:
            Dict[str, str]: CSS custom property names and values

        Example:
            >>> template.to_css_variables()
            {
                "--template-primary": "#1976d2",
                "--template-secondary": "#dc004e",
                "--template-font": "Roboto, sans-serif"
            }
        """
        return {
            "--template-primary": self.get_primary_color(),
            "--template-secondary": self.template_config.get("secondaryColor", "#dc004e"),
            "--template-font": self.get_font_family(),
            "--template-theme": self.get_theme()
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary for API serialization.

        Returns:
            Dict[str, Any]: Template data as dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "organization_id": self.organization_id,
            "template_config": self.template_config,
            "header_html": self.header_html,
            "footer_html": self.footer_html,
            "logo_url": self.logo_url,
            "background_image_url": self.background_image_url,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
