"""
Slide Entity - Domain Layer
Single Responsibility: Slide-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .base_content import BaseContent, ContentType


class SlideType(Enum):
    """Slide type enumeration"""
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
    """Slide layout enumeration"""
    TITLE_ONLY = "title_only"
    TITLE_CONTENT = "title_content"
    TITLE_TWO_COLUMN = "title_two_column"
    TITLE_IMAGE = "title_image"
    TITLE_VIDEO = "title_video"
    FULL_IMAGE = "full_image"
    BLANK = "blank"


class SlideContent:
    """Slide content value object"""
    
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
    """Slide animation value object"""
    
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
    Slide domain entity following SOLID principles
    Single Responsibility: Slide-specific business logic
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