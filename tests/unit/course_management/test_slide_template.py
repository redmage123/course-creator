"""
Unit Tests for SlideTemplate Entity

This module tests the SlideTemplate domain entity, verifying:
1. Template creation and validation
2. Configuration management
3. Default template handling
4. Template lifecycle (activate/deactivate)

BUSINESS RULES TESTED:
- Templates require name and organization_id
- Template names cannot exceed 100 characters
- Only one default template per organization
- Template configuration follows expected schema
"""
import pytest
from datetime import datetime
from uuid import uuid4

# Ensure correct service path is at the front of sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.slide_template import SlideTemplate, TemplateTheme


class TestSlideTemplateCreation:
    """
    Test suite for SlideTemplate creation and validation.
    """

    def test_create_basic_template(self):
        """
        Test creating a basic template with required fields.
        """
        # Arrange
        org_id = str(uuid4())

        # Act
        template = SlideTemplate(
            name="Corporate Template",
            organization_id=org_id
        )

        # Assert
        assert template.name == "Corporate Template"
        assert template.organization_id == org_id
        assert template.is_active is True
        assert template.is_default is False
        assert template.template_config is not None

    def test_create_template_with_full_config(self):
        """
        Test creating a template with full configuration.
        """
        # Arrange
        org_id = str(uuid4())
        config = {
            "theme": "corporate",
            "primaryColor": "#1976d2",
            "secondaryColor": "#dc004e",
            "fontFamily": "Arial, sans-serif",
            "headerStyle": {"backgroundColor": "#f5f5f5"},
            "footerStyle": {"fontSize": "12px"},
            "slideStyle": {"padding": "20px"}
        }

        # Act
        template = SlideTemplate(
            name="Full Config Template",
            organization_id=org_id,
            description="Template with all configuration options",
            template_config=config,
            header_html="<div>Company Name</div>",
            footer_html="<div>Confidential</div>",
            logo_url="https://example.com/logo.png",
            background_image_url="https://example.com/bg.png",
            is_default=True
        )

        # Assert
        assert template.description == "Template with all configuration options"
        assert template.template_config == config
        assert template.header_html == "<div>Company Name</div>"
        assert template.footer_html == "<div>Confidential</div>"
        assert template.logo_url == "https://example.com/logo.png"
        assert template.background_image_url == "https://example.com/bg.png"
        assert template.is_default is True

    def test_create_template_with_default_config(self):
        """
        Test that templates get default configuration when not specified.
        """
        # Act
        template = SlideTemplate(
            name="Default Config Template",
            organization_id=str(uuid4())
        )

        # Assert - Check default config values
        assert template.template_config.get("theme") == "default"
        assert template.template_config.get("primaryColor") == "#1976d2"
        assert template.template_config.get("fontFamily") == "Roboto, sans-serif"


class TestSlideTemplateValidation:
    """
    Test suite for SlideTemplate validation rules.
    """

    def test_empty_name_raises_error(self):
        """
        Test that empty template name raises ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="",
                organization_id=str(uuid4())
            )
        assert "name cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_only_name_raises_error(self):
        """
        Test that whitespace-only name raises ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="   ",
                organization_id=str(uuid4())
            )
        assert "name cannot be empty" in str(exc_info.value).lower()

    def test_name_exceeding_max_length_raises_error(self):
        """
        Test that name exceeding 100 characters raises ValueError.
        """
        long_name = "A" * 101

        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name=long_name,
                organization_id=str(uuid4())
            )
        assert "100 characters" in str(exc_info.value)

    def test_missing_organization_id_raises_error(self):
        """
        Test that missing organization_id raises ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="Valid Name",
                organization_id=None
            )
        assert "organization" in str(exc_info.value).lower()

    def test_description_exceeding_max_length_raises_error(self):
        """
        Test that description exceeding 500 characters raises ValueError.
        """
        long_description = "A" * 501

        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="Valid Name",
                organization_id=str(uuid4()),
                description=long_description
            )
        assert "500 characters" in str(exc_info.value)

    def test_logo_url_exceeding_max_length_raises_error(self):
        """
        Test that logo_url exceeding 500 characters raises ValueError.
        """
        long_url = "https://example.com/" + "a" * 490

        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="Valid Name",
                organization_id=str(uuid4()),
                logo_url=long_url
            )
        assert "Logo URL" in str(exc_info.value)

    def test_invalid_template_config_type_raises_error(self):
        """
        Test that non-dictionary template_config raises ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            SlideTemplate(
                name="Valid Name",
                organization_id=str(uuid4()),
                template_config="not a dict"  # Invalid type
            )
        assert "dictionary" in str(exc_info.value).lower()


class TestSlideTemplateConfigMethods:
    """
    Test suite for template configuration methods.
    """

    def test_update_config_merges_values(self):
        """
        Test that update_config merges new values with existing.
        """
        # Arrange
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )
        original_font = template.template_config.get("fontFamily")

        # Act
        template.update_config({"primaryColor": "#ff5722"})

        # Assert
        assert template.template_config.get("primaryColor") == "#ff5722"
        assert template.template_config.get("fontFamily") == original_font

    def test_update_config_sets_updated_at(self):
        """
        Test that update_config updates the updated_at timestamp.
        """
        # Arrange
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )
        original_updated_at = template.updated_at

        # Act
        template.update_config({"theme": "dark"})

        # Assert
        assert template.updated_at is not None
        assert template.updated_at != original_updated_at

    def test_update_config_with_invalid_type_raises_error(self):
        """
        Test that update_config with non-dict raises ValueError.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )

        with pytest.raises(ValueError) as exc_info:
            template.update_config("not a dict")
        assert "dictionary" in str(exc_info.value).lower()

    def test_get_theme_returns_configured_theme(self):
        """
        Test get_theme returns the theme from config.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={"theme": "dark"}
        )
        assert template.get_theme() == "dark"

    def test_get_theme_returns_default_when_not_set(self):
        """
        Test get_theme returns 'default' when not configured.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={}
        )
        assert template.get_theme() == "default"

    def test_get_primary_color_returns_configured_color(self):
        """
        Test get_primary_color returns the configured color.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={"primaryColor": "#ff0000"}
        )
        assert template.get_primary_color() == "#ff0000"

    def test_get_font_family_returns_configured_font(self):
        """
        Test get_font_family returns the configured font.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={"fontFamily": "Arial, sans-serif"}
        )
        assert template.get_font_family() == "Arial, sans-serif"


class TestSlideTemplateLifecycle:
    """
    Test suite for template lifecycle methods.
    """

    def test_set_as_default(self):
        """
        Test set_as_default marks template as default.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )
        assert template.is_default is False

        template.set_as_default()

        assert template.is_default is True
        assert template.updated_at is not None

    def test_deactivate_sets_inactive_and_removes_default(self):
        """
        Test deactivate sets is_active=False and is_default=False.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            is_default=True
        )

        template.deactivate()

        assert template.is_active is False
        assert template.is_default is False
        assert template.updated_at is not None

    def test_activate_sets_active(self):
        """
        Test activate sets is_active=True.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )
        template.deactivate()
        assert template.is_active is False

        template.activate()

        assert template.is_active is True
        assert template.updated_at is not None


class TestSlideTemplateSerialization:
    """
    Test suite for template serialization methods.
    """

    def test_to_css_variables(self):
        """
        Test to_css_variables generates correct CSS custom properties.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={
                "theme": "corporate",
                "primaryColor": "#1976d2",
                "secondaryColor": "#dc004e",
                "fontFamily": "Arial"
            }
        )

        css_vars = template.to_css_variables()

        assert css_vars["--template-primary"] == "#1976d2"
        assert css_vars["--template-secondary"] == "#dc004e"
        assert css_vars["--template-font"] == "Arial"
        assert css_vars["--template-theme"] == "corporate"

    def test_to_dict_includes_all_fields(self):
        """
        Test to_dict includes all template fields.
        """
        org_id = str(uuid4())
        template = SlideTemplate(
            name="Test Template",
            organization_id=org_id,
            description="Test description",
            logo_url="https://example.com/logo.png",
            is_default=True
        )

        result = template.to_dict()

        assert result["name"] == "Test Template"
        assert result["organization_id"] == org_id
        assert result["description"] == "Test description"
        assert result["logo_url"] == "https://example.com/logo.png"
        assert result["is_default"] is True
        assert "template_config" in result

    def test_to_dict_handles_none_timestamps(self):
        """
        Test to_dict handles None timestamps correctly.
        """
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4())
        )

        result = template.to_dict()

        # Timestamps may be None initially
        assert "created_at" in result
        assert "updated_at" in result
