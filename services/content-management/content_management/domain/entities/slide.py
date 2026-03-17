"""
Slide Entity - Domain Layer
Single Responsibility: Slide-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from content_management.domain.entities.base_content import BaseContent, ContentType


class SlideType(Enum):
    """
    Presentation slide type classification for educational content delivery.

    Comprehensive enumeration of slide types supporting diverse instructional
    delivery methods and multimedia educational content presentation.

    Slide Type Categories:
    - **TITLE**: Course/section title slides for clear organization
    - **CONTENT**: Text-based instructional content for concept presentation
    - **SECTION_BREAK**: Transition slides for logical content segmentation
    - **BULLET_POINTS**: List-based content for key point emphasis
    - **IMAGE**: Visual content for illustration and engagement
    - **CODE**: Programming code examples for technical instruction
    - **CHART**: Data visualization for analytics and statistics presentation
    - **VIDEO**: Multimedia content for demonstration and engagement
    - **INTERACTIVE**: Interactive elements for active learning
    - **SUMMARY**: Recap slides for knowledge consolidation

    Educational Benefits:
    - Diverse content presentation formats for varied learning styles
    - Clear content organization and structure
    - Multimedia integration for engagement
    - Technical content support (code, charts)
    - Interactive elements for active learning
    """
    TITLE = "title"
    CONTENT = "content"
    SECTION_BREAK = "section_break"
    BULLET_POINTS = "bullet_points"
    IMAGE = "image"
    CODE = "code"
    CHART = "chart"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    SUMMARY = "summary"


class SlideLayout(Enum):
    """
    Slide layout templates for consistent presentation design.

    Standardized layout templates supporting professional presentation design,
    consistent visual structure, and effective information organization.

    Layout Templates:
    - **TITLE_ONLY**: Title-focused layout for section headers
    - **TITLE_CONTENT**: Standard layout with title and content area
    - **TITLE_TWO_COLUMN**: Split content layout for comparisons
    - **TITLE_IMAGE**: Image-focused layout with title
    - **TITLE_VIDEO**: Video-focused layout with title
    - **FULL_IMAGE**: Full-screen image for maximum visual impact
    - **BLANK**: Custom layout for flexible design

    Design Benefits:
    - Consistent visual presentation across slides
    - Professional appearance and structure
    - Appropriate layout for content type
    - Flexibility for custom designs
    """
    TITLE_ONLY = "title_only"
    TITLE_CONTENT = "title_content"
    TITLE_TWO_COLUMN = "title_two_column"
    TITLE_IMAGE = "title_image"
    TITLE_VIDEO = "title_video"
    FULL_IMAGE = "full_image"
    BLANK = "blank"


class SlideContent:
    """
    Slide content value object supporting multimedia educational content.

    BUSINESS REQUIREMENT:
    Educational slides require flexible content support including text,
    images, code examples, bullet points, and charts for effective
    instructional delivery and student engagement.

    CONTENT FRAMEWORK:
    - Text content for instructional narrative
    - Image support with alt text for accessibility
    - Code examples with syntax highlighting
    - Bullet points for key concepts
    - Charts and visualizations for data presentation

    ACCESSIBILITY CONSIDERATIONS:
    - Alt text for images (screen reader support)
    - Caption support for multimedia
    - Clear text structure for comprehension
    """

    def __init__(
        self,
        text: Optional[str] = None,
        images: Optional[List[Dict[str, str]]] = None,
        code: Optional[Dict[str, str]] = None,
        bullets: Optional[List[str]] = None,
        charts: Optional[List[Dict[str, Any]]] = None
    ):
        self.text = text or ""
        self.images = images or []
        self.code = code or {}
        self.bullets = bullets or []
        self.charts = charts or []
    
    def add_bullet_point(self, bullet: str) -> None:
        """Add bullet point"""
        if bullet and bullet not in self.bullets:
            self.bullets.append(bullet)
    
    def add_image(self, url: str, alt_text: str, caption: Optional[str] = None) -> None:
        """Add image to slide"""
        image_data = {
            "url": url,
            "alt_text": alt_text,
            "caption": caption or ""
        }
        self.images.append(image_data)
    
    def set_code(self, code: str, language: str = "python") -> None:
        """Set code content"""
        self.code = {
            "content": code,
            "language": language
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "images": self.images,
            "code": self.code,
            "bullets": self.bullets,
            "charts": self.charts
        }


class SlideAnimation:
    """
    Slide animation specification for engagement and emphasis.

    BUSINESS REQUIREMENT:
    Educational presentations benefit from controlled animations for
    student attention management, content emphasis, and professional
    delivery pacing during instructional sessions.

    ANIMATION TYPES:
    - Entrance animations for content reveal
    - Emphasis animations for key point highlighting
    - Exit animations for content transitions
    - Duration control for appropriate pacing

    EDUCATIONAL DESIGN:
    - Attention-directing animations for key concepts
    - Professional, non-distracting animation choices
    - Consistent timing for predictable delivery
    """

    def __init__(
        self,
        entrance: Optional[str] = None,
        emphasis: Optional[str] = None,
        exit: Optional[str] = None,
        duration: float = 1.0
    ):
        self.entrance = entrance
        self.emphasis = emphasis
        self.exit = exit
        self.duration = duration
        
        self.validate()
    
    def validate(self) -> None:
        """Validate animation"""
        if self.duration < 0:
            raise ValueError("Animation duration must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entrance": self.entrance,
            "emphasis": self.emphasis,
            "exit": self.exit,
            "duration": self.duration
        }


class Slide(BaseContent):
    """
    Slide domain entity - educational presentation slide with multimedia support.

    BUSINESS REQUIREMENT:
    Educational presentations require individual slide management with multimedia
    content support, speaker notes, layout templates, visual customization, and
    timing information for effective instructional delivery and student engagement.

    EDUCATIONAL METHODOLOGY:
    Implements evidence-based presentation design principles including clear slide
    organization, appropriate multimedia integration, speaker note support for
    instructor guidance, and time estimation for proper pacing.

    TECHNICAL IMPLEMENTATION:
    - Extends BaseContent for lifecycle management
    - Uses SlideContent value object for multimedia support
    - Supports SlideAnimation for engagement and emphasis
    - Provides layout templates for consistent design
    - Includes speaker notes for instructor support

    DOMAIN OPERATIONS:
    - Slide numbering and sequencing
    - Content management (text, images, code, bullets)
    - Speaker note management for instructor guidance
    - Layout and visual customization
    - Animation specification for emphasis
    - Duration estimation for timing

    PRESENTATION FEATURES:
    - Multiple slide types for diverse content
    - Layout templates for consistent design
    - Background customization (color, image, gradient)
    - Speaker notes for instructor support
    - Reading time estimation for pacing
    - Animation support for engagement
    """

    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        slide_number: int,
        slide_type: SlideType,
        id: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[SlideContent] = None,
        speaker_notes: Optional[str] = None,
        layout: SlideLayout = SlideLayout.TITLE_CONTENT,
        background: Optional[Dict[str, str]] = None,
        animations: Optional[SlideAnimation] = None,
        duration_minutes: Optional[float] = None,
        **kwargs
    ):
        # Initialize base content
        super().__init__(
            title=title,
            course_id=course_id,
            created_by=created_by,
            id=id,
            description=description,
            **kwargs
        )
        
        # Slide-specific attributes
        self.slide_number = slide_number
        self.slide_type = slide_type
        self.content = content or SlideContent()
        self.speaker_notes = speaker_notes or ""
        self.layout = layout
        self.background = background or {}
        self.animations = animations
        self.duration_minutes = duration_minutes
        
        # Additional validation
        self._validate_slide()
    
    def get_content_type(self) -> ContentType:
        """Get content type"""
        return ContentType.SLIDE
    
    def _validate_slide(self) -> None:
        """Validate slide-specific data"""
        if self.slide_number < 1:
            raise ValueError("Slide number must be positive")
        if self.duration_minutes is not None and self.duration_minutes < 0:
            raise ValueError("Duration must be non-negative")
    
    def update_slide_number(self, slide_number: int) -> None:
        """Update slide number"""
        if slide_number < 1:
            raise ValueError("Slide number must be positive")
        self.slide_number = slide_number
        self._mark_updated()
    
    def update_slide_type(self, slide_type: SlideType) -> None:
        """Update slide type"""
        self.slide_type = slide_type
        self._mark_updated()
    
    def update_layout(self, layout: SlideLayout) -> None:
        """Update slide layout"""
        self.layout = layout
        self._mark_updated()
    
    def add_speaker_note(self, note: str) -> None:
        """Add to speaker notes"""
        if self.speaker_notes:
            self.speaker_notes += "\n" + note
        else:
            self.speaker_notes = note
        self._mark_updated()
    
    def set_speaker_notes(self, notes: str) -> None:
        """Set speaker notes"""
        self.speaker_notes = notes
        self._mark_updated()
    
    def set_background_color(self, color: str) -> None:
        """Set background color"""
        self.background["color"] = color
        self._mark_updated()
    
    def set_background_image(self, image_url: str) -> None:
        """Set background image"""
        self.background["image"] = image_url
        self._mark_updated()
    
    def set_background_gradient(self, gradient: str) -> None:
        """Set background gradient"""
        self.background["gradient"] = gradient
        self._mark_updated()
    
    def update_content_text(self, text: str) -> None:
        """Update slide content text"""
        self.content.text = text
        self._mark_updated()
    
    def add_bullet_point(self, bullet: str) -> None:
        """Add bullet point to content"""
        self.content.add_bullet_point(bullet)
        self._mark_updated()
    
    def add_image_to_content(self, url: str, alt_text: str, caption: Optional[str] = None) -> None:
        """Add image to slide content"""
        self.content.add_image(url, alt_text, caption)
        self._mark_updated()
    
    def set_code_content(self, code: str, language: str = "python") -> None:
        """Set code content"""
        self.content.set_code(code, language)
        self._mark_updated()
    
    def set_duration(self, minutes: float) -> None:
        """Set slide duration"""
        if minutes < 0:
            raise ValueError("Duration must be non-negative")
        self.duration_minutes = minutes
        self._mark_updated()
    
    def set_animations(self, animations: SlideAnimation) -> None:
        """Set slide animations"""
        self.animations = animations
        self._mark_updated()
    
    def has_content(self) -> bool:
        """Check if slide has content"""
        return bool(
            self.content.text or 
            self.content.bullets or 
            self.content.images or 
            self.content.code or 
            self.content.charts
        )
    
    def is_title_slide(self) -> bool:
        """Check if this is a title slide"""
        return self.slide_type == SlideType.TITLE
    
    def is_content_slide(self) -> bool:
        """Check if this is a content slide"""
        return self.slide_type == SlideType.CONTENT
    
    def get_estimated_reading_time(self) -> float:
        """Estimate reading time in minutes based on content"""
        if self.duration_minutes:
            return self.duration_minutes
        
        # Rough estimation: 200 words per minute
        word_count = len(self.content.text.split()) if self.content.text else 0
        word_count += len(self.content.bullets) * 5  # Assume 5 words per bullet
        
        return max(0.5, word_count / 200.0)  # Minimum 30 seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "slide_number": self.slide_number,
            "slide_type": self.slide_type.value,
            "content": self.content.to_dict(),
            "speaker_notes": self.speaker_notes,
            "layout": self.layout.value,
            "background": self.background,
            "animations": self.animations.to_dict() if self.animations else None,
            "duration_minutes": self.duration_minutes,
            "has_content": self.has_content(),
            "estimated_reading_time": self.get_estimated_reading_time()
        })
        return base_dict