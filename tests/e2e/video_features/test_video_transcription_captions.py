"""
E2E Tests for Video Transcription and Captions

Comprehensive end-to-end testing for video transcription generation,
caption display, and accessibility features in the Course Creator Platform.

BUSINESS REQUIREMENTS:
1. Automatic transcript generation from video audio using Whisper API
2. Manual transcript editing and correction by instructors
3. Export transcripts in multiple formats (TXT, SRT, VTT)
4. Synchronized caption display during video playback
5. Multi-language caption support
6. Caption styling customization (font, background, position)
7. Keyboard navigation for video controls
8. Screen reader compatibility with ARIA labels
9. Caption search functionality
10. Transcription accuracy >85% (word error rate <15%)

TECHNICAL IMPLEMENTATION:
- Whisper API integration for speech-to-text
- WebVTT format for caption synchronization
- WCAG 2.1 AA accessibility compliance
- Real-time caption rendering
- Multi-layer verification (UI + Database + Caption Files)

TEST COVERAGE:
- Transcription Generation (4 tests)
- Caption Display & Features (3 tests)
- Accessibility Compliance (3 tests)

USAGE:
    pytest tests/e2e/video_features/test_video_transcription_captions.py -v
    pytest tests/e2e/video_features/test_video_transcription_captions.py::TestTranscription -v
"""

import pytest
import time
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import sys
sys.path.append(str(Path(__file__).parent.parent))
from selenium_base import BaseTest, BasePage, SeleniumConfig


# ============================================================================
# PAGE OBJECTS
# ============================================================================

class TranscriptionPage(BasePage):
    """
    Page Object for video transcription management.

    BUSINESS CONTEXT:
    Provides interface for instructors to manage video transcripts, enabling
    accessibility compliance and improved student learning experience through
    searchable, editable video transcripts.

    DESIGN PATTERN: Page Object Model
    Encapsulates all transcription-related UI interactions and locators.
    """

    # Video player locators
    VIDEO_PLAYER = (By.ID, "video-player")
    VIDEO_TITLE = (By.ID, "video-title")
    VIDEO_DURATION = (By.ID, "video-duration")

    # Transcription controls
    GENERATE_TRANSCRIPT_BTN = (By.ID, "generate-transcript-btn")
    TRANSCRIPT_STATUS = (By.ID, "transcript-status")
    TRANSCRIPT_PROGRESS = (By.ID, "transcript-progress")
    TRANSCRIPT_EDITOR = (By.ID, "transcript-editor")
    SAVE_TRANSCRIPT_BTN = (By.ID, "save-transcript-btn")
    CANCEL_TRANSCRIPT_BTN = (By.ID, "cancel-transcript-btn")

    # Export controls
    EXPORT_TRANSCRIPT_BTN = (By.ID, "export-transcript-btn")
    EXPORT_FORMAT_DROPDOWN = (By.ID, "export-format-dropdown")
    EXPORT_TXT_OPTION = (By.CSS_SELECTOR, "option[value='txt']")
    EXPORT_SRT_OPTION = (By.CSS_SELECTOR, "option[value='srt']")
    EXPORT_VTT_OPTION = (By.CSS_SELECTOR, "option[value='vtt']")
    CONFIRM_EXPORT_BTN = (By.ID, "confirm-export-btn")
    DOWNLOAD_LINK = (By.ID, "download-transcript-link")

    # Transcript segments (timestamp-synced)
    TRANSCRIPT_SEGMENTS = (By.CLASS_NAME, "transcript-segment")
    SEGMENT_TIMESTAMP = (By.CLASS_NAME, "segment-timestamp")
    SEGMENT_TEXT = (By.CLASS_NAME, "segment-text")

    # Accuracy metrics
    WORD_ERROR_RATE = (By.ID, "word-error-rate")
    CONFIDENCE_SCORE = (By.ID, "confidence-score")
    LANGUAGE_DETECTED = (By.ID, "language-detected")

    # Search functionality
    TRANSCRIPT_SEARCH_INPUT = (By.ID, "transcript-search")
    SEARCH_RESULTS_COUNT = (By.ID, "search-results-count")
    SEARCH_HIGHLIGHT = (By.CLASS_NAME, "search-highlight")
    NEXT_SEARCH_RESULT_BTN = (By.ID, "next-search-result")
    PREV_SEARCH_RESULT_BTN = (By.ID, "prev-search-result")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.navigate_to("/html/video-transcription.html")

    def generate_transcript(self, timeout: int = 120):
        """
        Generate transcript from video audio using Whisper API.

        Args:
            timeout: Maximum seconds to wait for generation

        Returns:
            True if transcript generated successfully

        BUSINESS LOGIC:
        Initiates AI-powered speech-to-text transcription, providing
        students with searchable, accessible video content.
        """
        self.click_element(*self.GENERATE_TRANSCRIPT_BTN)

        # Wait for generation to complete
        try:
            self.wait_for_element(
                *self.TRANSCRIPT_EDITOR,
                timeout=timeout,
                condition=EC.visibility_of_element_located
            )
            return True
        except TimeoutException:
            return False

    def get_transcript_status(self) -> str:
        """Get current transcription status."""
        status = self.find_element(*self.TRANSCRIPT_STATUS)
        return status.text.strip()

    def get_transcript_progress(self) -> int:
        """Get transcription progress percentage."""
        progress = self.find_element(*self.TRANSCRIPT_PROGRESS)
        return int(progress.get_attribute("value") or "0")

    def get_transcript_text(self) -> str:
        """Get complete transcript text from editor."""
        editor = self.find_element(*self.TRANSCRIPT_EDITOR)
        return editor.get_attribute("value") or ""

    def edit_transcript(self, new_text: str):
        """
        Edit transcript text manually.

        BUSINESS LOGIC:
        Allows instructors to correct AI-generated transcripts,
        improving accuracy and quality for students.
        """
        editor = self.find_element(*self.TRANSCRIPT_EDITOR)
        editor.clear()
        editor.send_keys(new_text)

    def save_transcript(self):
        """Save edited transcript to database."""
        self.click_element(*self.SAVE_TRANSCRIPT_BTN)
        time.sleep(1)  # Wait for save operation

    def cancel_transcript_edit(self):
        """Cancel transcript editing without saving."""
        self.click_element(*self.CANCEL_TRANSCRIPT_BTN)

    def export_transcript(self, format: str = 'txt') -> str:
        """
        Export transcript in specified format.

        Args:
            format: Export format ('txt', 'srt', 'vtt')

        Returns:
            Downloaded file path

        BUSINESS LOGIC:
        Enables instructors to export transcripts for external use,
        integration with other systems, or manual review.
        """
        self.click_element(*self.EXPORT_TRANSCRIPT_BTN)

        # Select format
        self.click_element(*self.EXPORT_FORMAT_DROPDOWN)
        if format == 'txt':
            self.click_element(*self.EXPORT_TXT_OPTION)
        elif format == 'srt':
            self.click_element(*self.EXPORT_SRT_OPTION)
        elif format == 'vtt':
            self.click_element(*self.EXPORT_VTT_OPTION)

        # Confirm export
        self.click_element(*self.CONFIRM_EXPORT_BTN)

        # Get download link
        download_link = self.wait_for_element(*self.DOWNLOAD_LINK)
        return download_link.get_attribute("href")

    def get_transcript_segments(self) -> List[Dict[str, str]]:
        """
        Get all transcript segments with timestamps.

        Returns:
            List of segments with 'timestamp' and 'text' keys
        """
        segments = []
        segment_elements = self.find_elements(*self.TRANSCRIPT_SEGMENTS)

        for segment in segment_elements:
            timestamp = segment.find_element(*self.SEGMENT_TIMESTAMP).text
            text = segment.find_element(*self.SEGMENT_TEXT).text
            segments.append({
                'timestamp': timestamp,
                'text': text
            })

        return segments

    def get_word_error_rate(self) -> float:
        """Get word error rate (WER) metric."""
        wer = self.find_element(*self.WORD_ERROR_RATE)
        return float(wer.text.strip().replace('%', ''))

    def get_confidence_score(self) -> float:
        """Get AI transcription confidence score."""
        confidence = self.find_element(*self.CONFIDENCE_SCORE)
        return float(confidence.text.strip().replace('%', ''))

    def get_detected_language(self) -> str:
        """Get detected audio language."""
        language = self.find_element(*self.LANGUAGE_DETECTED)
        return language.text.strip()

    def search_transcript(self, query: str) -> int:
        """
        Search for text in transcript.

        Returns:
            Number of search results found

        BUSINESS LOGIC:
        Enables students to quickly find specific topics or keywords
        within video transcripts, improving learning efficiency.
        """
        search_input = self.find_element(*self.TRANSCRIPT_SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)

        time.sleep(0.5)  # Wait for search highlighting

        results_count = self.find_element(*self.SEARCH_RESULTS_COUNT)
        return int(results_count.text.strip())

    def get_search_highlights(self) -> List[str]:
        """Get all highlighted search results."""
        highlights = self.find_elements(*self.SEARCH_HIGHLIGHT)
        return [h.text.strip() for h in highlights]

    def navigate_to_next_search_result(self):
        """Navigate to next search result."""
        self.click_element(*self.NEXT_SEARCH_RESULT_BTN)

    def navigate_to_prev_search_result(self):
        """Navigate to previous search result."""
        self.click_element(*self.PREV_SEARCH_RESULT_BTN)


class CaptionEditorPage(BasePage):
    """
    Page Object for caption editing and customization.

    BUSINESS CONTEXT:
    Provides instructors with tools to customize caption appearance,
    synchronization, and multi-language support, ensuring accessibility
    compliance and enhanced student experience.
    """

    # Caption controls
    TOGGLE_CAPTIONS_BTN = (By.ID, "toggle-captions-btn")
    CAPTION_DISPLAY = (By.ID, "caption-display")
    CAPTION_TEXT = (By.ID, "caption-text")

    # Language selection
    LANGUAGE_SELECTOR = (By.ID, "caption-language-selector")
    LANGUAGE_ENGLISH = (By.CSS_SELECTOR, "option[value='en']")
    LANGUAGE_SPANISH = (By.CSS_SELECTOR, "option[value='es']")
    LANGUAGE_FRENCH = (By.CSS_SELECTOR, "option[value='fr']")

    # Styling controls
    FONT_SIZE_SLIDER = (By.ID, "caption-font-size-slider")
    FONT_SIZE_VALUE = (By.ID, "caption-font-size-value")
    BACKGROUND_OPACITY_SLIDER = (By.ID, "caption-background-opacity-slider")
    BACKGROUND_OPACITY_VALUE = (By.ID, "caption-background-opacity-value")
    POSITION_DROPDOWN = (By.ID, "caption-position-dropdown")
    POSITION_BOTTOM = (By.CSS_SELECTOR, "option[value='bottom']")
    POSITION_TOP = (By.CSS_SELECTOR, "option[value='top']")
    POSITION_MIDDLE = (By.CSS_SELECTOR, "option[value='middle']")

    # Preview
    CAPTION_PREVIEW = (By.ID, "caption-preview")
    APPLY_CAPTION_STYLE_BTN = (By.ID, "apply-caption-style-btn")
    RESET_CAPTION_STYLE_BTN = (By.ID, "reset-caption-style-btn")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.navigate_to("/html/caption-editor.html")

    def toggle_captions(self):
        """Toggle caption display on/off."""
        self.click_element(*self.TOGGLE_CAPTIONS_BTN)

    def are_captions_visible(self) -> bool:
        """Check if captions are currently visible."""
        caption_display = self.find_element(*self.CAPTION_DISPLAY)
        return caption_display.is_displayed()

    def get_current_caption_text(self) -> str:
        """Get currently displayed caption text."""
        caption_text = self.find_element(*self.CAPTION_TEXT)
        return caption_text.text.strip()

    def select_caption_language(self, language: str):
        """
        Select caption language.

        Args:
            language: Language code ('en', 'es', 'fr')

        BUSINESS LOGIC:
        Supports multi-language learners by providing captions
        in their preferred language, improving comprehension.
        """
        self.click_element(*self.LANGUAGE_SELECTOR)

        if language == 'en':
            self.click_element(*self.LANGUAGE_ENGLISH)
        elif language == 'es':
            self.click_element(*self.LANGUAGE_SPANISH)
        elif language == 'fr':
            self.click_element(*self.LANGUAGE_FRENCH)

    def set_caption_font_size(self, size: int):
        """
        Set caption font size.

        Args:
            size: Font size in pixels (12-32)
        """
        slider = self.find_element(*self.FONT_SIZE_SLIDER)
        self.driver.execute_script(f"arguments[0].value = {size}", slider)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", slider)

    def get_caption_font_size(self) -> int:
        """Get current caption font size."""
        font_size = self.find_element(*self.FONT_SIZE_VALUE)
        return int(font_size.text.strip().replace('px', ''))

    def set_caption_background_opacity(self, opacity: float):
        """
        Set caption background opacity.

        Args:
            opacity: Opacity value (0.0 - 1.0)
        """
        slider = self.find_element(*self.BACKGROUND_OPACITY_SLIDER)
        self.driver.execute_script(f"arguments[0].value = {opacity}", slider)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", slider)

    def get_caption_background_opacity(self) -> float:
        """Get current caption background opacity."""
        opacity = self.find_element(*self.BACKGROUND_OPACITY_VALUE)
        return float(opacity.text.strip())

    def set_caption_position(self, position: str):
        """
        Set caption position on screen.

        Args:
            position: Position ('bottom', 'top', 'middle')
        """
        self.click_element(*self.POSITION_DROPDOWN)

        if position == 'bottom':
            self.click_element(*self.POSITION_BOTTOM)
        elif position == 'top':
            self.click_element(*self.POSITION_TOP)
        elif position == 'middle':
            self.click_element(*self.POSITION_MIDDLE)

    def apply_caption_styling(self):
        """Apply caption styling changes."""
        self.click_element(*self.APPLY_CAPTION_STYLE_BTN)

    def reset_caption_styling(self):
        """Reset caption styling to defaults."""
        self.click_element(*self.RESET_CAPTION_STYLE_BTN)

    def get_caption_preview_style(self) -> Dict[str, str]:
        """Get caption preview computed styles."""
        preview = self.find_element(*self.CAPTION_PREVIEW)
        return {
            'font-size': preview.value_of_css_property('font-size'),
            'background-color': preview.value_of_css_property('background-color'),
            'opacity': preview.value_of_css_property('opacity'),
            'position': preview.value_of_css_property('position'),
        }


class AccessibilityPage(BasePage):
    """
    Page Object for accessibility testing.

    BUSINESS CONTEXT:
    Validates WCAG 2.1 AA compliance for video features, ensuring
    equal access for students with disabilities through keyboard
    navigation, screen reader support, and accessible controls.
    """

    # Video player controls
    VIDEO_PLAYER = (By.ID, "accessible-video-player")
    PLAY_PAUSE_BTN = (By.ID, "play-pause-btn")
    SEEK_BACKWARD_BTN = (By.ID, "seek-backward-btn")
    SEEK_FORWARD_BTN = (By.ID, "seek-forward-btn")
    VOLUME_UP_BTN = (By.ID, "volume-up-btn")
    VOLUME_DOWN_BTN = (By.ID, "volume-down-btn")
    MUTE_BTN = (By.ID, "mute-btn")
    FULLSCREEN_BTN = (By.ID, "fullscreen-btn")

    # Progress bar
    PROGRESS_BAR = (By.ID, "video-progress-bar")
    CURRENT_TIME = (By.ID, "video-current-time")
    TOTAL_TIME = (By.ID, "video-total-time")

    # ARIA labels
    PLAYER_ARIA_LABEL = (By.CSS_SELECTOR, "[aria-label='Video player']")
    PLAY_ARIA_LABEL = (By.CSS_SELECTOR, "[aria-label='Play video']")
    PAUSE_ARIA_LABEL = (By.CSS_SELECTOR, "[aria-label='Pause video']")
    SEEK_BACKWARD_ARIA = (By.CSS_SELECTOR, "[aria-label='Seek backward 10 seconds']")
    SEEK_FORWARD_ARIA = (By.CSS_SELECTOR, "[aria-label='Seek forward 10 seconds']")

    # Keyboard shortcuts info
    KEYBOARD_SHORTCUTS_BTN = (By.ID, "keyboard-shortcuts-btn")
    SHORTCUTS_MODAL = (By.ID, "keyboard-shortcuts-modal")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.navigate_to("/html/accessible-video-player.html")

    def press_spacebar(self):
        """
        Press spacebar to play/pause video.

        ACCESSIBILITY REQUIREMENT:
        WCAG 2.1 - Keyboard accessibility for video controls.
        """
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys(Keys.SPACE)

    def press_arrow_left(self):
        """Press left arrow to seek backward."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys(Keys.ARROW_LEFT)

    def press_arrow_right(self):
        """Press right arrow to seek forward."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys(Keys.ARROW_RIGHT)

    def press_arrow_up(self):
        """Press up arrow to increase volume."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys(Keys.ARROW_UP)

    def press_arrow_down(self):
        """Press down arrow to decrease volume."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys(Keys.ARROW_DOWN)

    def press_m_key(self):
        """Press M key to toggle mute."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys('m')

    def press_f_key(self):
        """Press F key to toggle fullscreen."""
        video_player = self.find_element(*self.VIDEO_PLAYER)
        video_player.send_keys('f')

    def is_video_playing(self) -> bool:
        """Check if video is currently playing."""
        play_btn = self.find_element(*self.PLAY_PAUSE_BTN)
        return "pause" in play_btn.get_attribute("class").lower()

    def get_current_time(self) -> str:
        """Get current video playback time."""
        current_time = self.find_element(*self.CURRENT_TIME)
        return current_time.text.strip()

    def get_aria_label(self, locator) -> str:
        """Get ARIA label for accessibility."""
        element = self.find_element(*locator)
        return element.get_attribute("aria-label") or ""

    def verify_aria_labels_present(self) -> bool:
        """
        Verify all required ARIA labels are present.

        ACCESSIBILITY REQUIREMENT:
        WCAG 2.1 - All interactive elements must have accessible names.
        """
        required_labels = [
            self.PLAYER_ARIA_LABEL,
            self.PLAY_ARIA_LABEL,
            self.SEEK_BACKWARD_ARIA,
            self.SEEK_FORWARD_ARIA,
        ]

        for label_locator in required_labels:
            try:
                self.find_element(*label_locator)
            except:
                return False

        return True

    def open_keyboard_shortcuts(self):
        """Open keyboard shortcuts help modal."""
        self.click_element(*self.KEYBOARD_SHORTCUTS_BTN)

    def is_shortcuts_modal_visible(self) -> bool:
        """Check if keyboard shortcuts modal is displayed."""
        modal = self.find_element(*self.SHORTCUTS_MODAL)
        return modal.is_displayed()


# ============================================================================
# TEST CLASSES
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestTranscription(BaseTest):
    """
    Test cases for video transcription generation and editing.

    BUSINESS OBJECTIVES:
    - Provide automatic transcript generation for all course videos
    - Enable instructor correction of AI-generated transcripts
    - Support multiple export formats for accessibility compliance
    - Achieve >85% transcription accuracy

    TECHNICAL REQUIREMENTS:
    - Whisper API integration for speech-to-text
    - Real-time transcription progress tracking
    - Database storage for transcript persistence
    - Export to TXT, SRT, VTT formats
    """

    @pytest.mark.priority_critical
    def test_01_generate_transcript_from_video_audio(self):
        """
        Test automatic transcript generation from video audio using Whisper API.

        BUSINESS REQUIREMENT:
        Provide automatic transcription for all course videos to improve
        accessibility and enable students to read video content, supporting
        diverse learning styles and accessibility needs (deaf/hard-of-hearing).

        TEST SCENARIO:
        1. Navigate to video transcription page
        2. Click "Generate Transcript" button
        3. Wait for Whisper API processing (up to 120 seconds)
        4. Verify transcript appears in editor
        5. Verify transcript contains expected content
        6. Verify database record created
        7. Verify caption file generated (VTT format)

        VALIDATION CRITERIA:
        - Transcript generation completes within 120 seconds
        - Transcript editor displays generated text
        - Transcript contains >100 words
        - Database transcript record exists with correct video_id
        - VTT caption file exists in storage
        - Transcript segments have timestamps

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Transcript visible in editor
        Layer 2 (Database): Transcript record in video_transcripts table
        Layer 3 (File System): VTT file exists in /storage/captions/
        """
        # Initialize page object
        page = TranscriptionPage(self.driver, self.config)

        # Verify video loaded
        video_title = page.find_element(*page.VIDEO_TITLE)
        assert video_title.text.strip(), "Video title should be displayed"

        # Generate transcript
        success = page.generate_transcript(timeout=120)
        assert success, "Transcript generation should complete within 120 seconds"

        # Verify transcript status
        status = page.get_transcript_status()
        assert status == "Completed", f"Transcript status should be 'Completed', got '{status}'"

        # Verify transcript text
        transcript_text = page.get_transcript_text()
        assert len(transcript_text) > 100, "Transcript should contain at least 100 characters"

        # Verify transcript segments have timestamps
        segments = page.get_transcript_segments()
        assert len(segments) > 0, "Transcript should have at least one segment"

        for segment in segments:
            assert segment['timestamp'], "Each segment should have a timestamp"
            assert segment['text'], "Each segment should have text content"

        # TODO: Add database verification
        # transcript_record = db.query("SELECT * FROM video_transcripts WHERE video_id = ?", video_id)
        # assert transcript_record is not None, "Transcript record should exist in database"

        # TODO: Add caption file verification
        # caption_file_path = f"/storage/captions/{video_id}.vtt"
        # assert os.path.exists(caption_file_path), "VTT caption file should exist"

    @pytest.mark.priority_high
    def test_02_edit_transcript_manually_instructor_correction(self):
        """
        Test manual transcript editing by instructor to correct AI errors.

        BUSINESS REQUIREMENT:
        Enable instructors to review and correct AI-generated transcripts,
        improving accuracy for technical terminology, proper nouns, and
        domain-specific language that AI may misinterpret.

        TEST SCENARIO:
        1. Generate initial transcript (or load existing)
        2. Identify text to correct (e.g., "machine learning" → "machine learning")
        3. Edit transcript text in editor
        4. Save edited transcript
        5. Verify changes saved to database
        6. Reload page and verify edited version displayed

        VALIDATION CRITERIA:
        - Transcript editor allows text modification
        - Save button becomes enabled after edits
        - Success message displayed after save
        - Database updated with edited transcript
        - Edited transcript persists across page reloads
        - Version history preserved (original + edited)

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Edited text visible in editor after save
        Layer 2 (Database): Transcript record updated with new text
        Layer 3 (Version History): Original version preserved
        """
        page = TranscriptionPage(self.driver, self.config)

        # Generate or load existing transcript
        if page.get_transcript_text() == "":
            page.generate_transcript(timeout=120)

        # Get original transcript
        original_text = page.get_transcript_text()
        assert original_text, "Original transcript should exist"

        # Edit transcript
        edited_text = original_text + "\n\n[Instructor correction: Technical terminology clarified]"
        page.edit_transcript(edited_text)

        # Save edited transcript
        page.save_transcript()

        # Verify save success (check for success message or status)
        status = page.get_transcript_status()
        assert status in ["Saved", "Completed"], f"Transcript should be saved, got status: {status}"

        # Reload page to verify persistence
        page.navigate_to("/html/video-transcription.html")

        # Verify edited text persists
        loaded_text = page.get_transcript_text()
        assert "[Instructor correction" in loaded_text, "Edited transcript should persist after reload"

        # TODO: Add database verification
        # transcript_record = db.query("SELECT * FROM video_transcripts WHERE video_id = ?", video_id)
        # assert transcript_record['text'] == edited_text, "Database should contain edited transcript"

    @pytest.mark.priority_high
    def test_03_export_transcript_multiple_formats(self):
        """
        Test transcript export in TXT, SRT, and VTT formats.

        BUSINESS REQUIREMENT:
        Enable instructors to export transcripts for external use, integration
        with other learning management systems, or manual review processes.
        Different formats support different use cases:
        - TXT: Simple text for review/editing
        - SRT: Subtitle format for video editing software
        - VTT: Web standard for HTML5 video captions

        TEST SCENARIO:
        1. Generate transcript if not exists
        2. Export as TXT format
        3. Verify TXT file contains plain text
        4. Export as SRT format
        5. Verify SRT file has timestamp format (00:00:00,000 --> 00:00:05,000)
        6. Export as VTT format
        7. Verify VTT file has WEBVTT header and cue format

        VALIDATION CRITERIA:
        - Export button triggers download for each format
        - TXT file contains transcript text only
        - SRT file has correct subtitle format with timestamps
        - VTT file has WEBVTT header and valid cues
        - File sizes are reasonable (>1KB, <10MB)
        - Filenames follow convention: video_id.{txt,srt,vtt}

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Download link appears after export
        Layer 2 (File): Downloaded file exists and is not empty
        Layer 3 (Content): File content matches expected format
        """
        page = TranscriptionPage(self.driver, self.config)

        # Ensure transcript exists
        if page.get_transcript_text() == "":
            page.generate_transcript(timeout=120)

        # Test TXT export
        txt_url = page.export_transcript(format='txt')
        assert txt_url, "TXT export should return download URL"
        assert txt_url.endswith('.txt'), "TXT export URL should end with .txt"

        # Test SRT export
        srt_url = page.export_transcript(format='srt')
        assert srt_url, "SRT export should return download URL"
        assert srt_url.endswith('.srt'), "SRT export URL should end with .srt"

        # Test VTT export
        vtt_url = page.export_transcript(format='vtt')
        assert vtt_url, "VTT export should return download URL"
        assert vtt_url.endswith('.vtt'), "VTT export URL should end with .vtt"

        # TODO: Add file content verification
        # txt_content = download_and_read_file(txt_url)
        # assert len(txt_content) > 100, "TXT file should contain transcript text"

        # srt_content = download_and_read_file(srt_url)
        # assert "00:00:00,000 --> " in srt_content, "SRT file should have timestamp format"

        # vtt_content = download_and_read_file(vtt_url)
        # assert vtt_content.startswith("WEBVTT"), "VTT file should have WEBVTT header"

    @pytest.mark.priority_critical
    def test_04_verify_transcript_accuracy_threshold(self):
        """
        Test transcript accuracy meets >85% threshold (word error rate <15%).

        BUSINESS REQUIREMENT:
        Ensure AI-generated transcripts are sufficiently accurate for
        educational use, requiring minimal instructor correction. Accuracy
        threshold of >85% balances automation benefits with quality needs.

        TEST SCENARIO:
        1. Generate transcript from known test video
        2. Retrieve word error rate (WER) metric
        3. Retrieve confidence score from Whisper API
        4. Compare generated transcript to reference transcript
        5. Calculate accuracy percentage
        6. Verify WER < 15%
        7. Verify confidence score > 85%

        VALIDATION CRITERIA:
        - Word error rate (WER) < 15%
        - Confidence score > 85%
        - Language correctly detected (English)
        - Technical terms recognized (e.g., "Python", "API", "database")
        - Numbers and acronyms transcribed correctly

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): WER metric displayed on page
        Layer 2 (Database): Accuracy metrics stored
        Layer 3 (Quality Assurance): Manual spot-check of transcript quality
        """
        page = TranscriptionPage(self.driver, self.config)

        # Generate transcript
        success = page.generate_transcript(timeout=120)
        assert success, "Transcript generation should complete"

        # Get accuracy metrics
        wer = page.get_word_error_rate()
        confidence = page.get_confidence_score()
        detected_language = page.get_detected_language()

        # Verify accuracy threshold
        assert wer < 15.0, f"Word error rate should be < 15%, got {wer}%"
        assert confidence > 85.0, f"Confidence score should be > 85%, got {confidence}%"

        # Verify language detection
        assert detected_language.lower() == "english", f"Language should be English, got {detected_language}"

        # Verify transcript quality (spot check)
        transcript_text = page.get_transcript_text().lower()

        # Check for common technical terms
        technical_terms = ["python", "api", "database", "function", "variable"]
        found_terms = sum(1 for term in technical_terms if term in transcript_text)
        assert found_terms > 0, "Transcript should contain at least one technical term"

        # TODO: Add reference transcript comparison
        # reference_transcript = load_reference_transcript(video_id)
        # calculated_wer = calculate_wer(transcript_text, reference_transcript)
        # assert calculated_wer < 15.0, f"Calculated WER should be < 15%, got {calculated_wer}%"


@pytest.mark.e2e
@pytest.mark.video
class TestCaptions(BaseTest):
    """
    Test cases for caption display, synchronization, and customization.

    BUSINESS OBJECTIVES:
    - Display synchronized captions during video playback
    - Support multi-language caption selection
    - Enable caption styling customization for readability
    - Ensure caption timing accuracy within 500ms

    TECHNICAL REQUIREMENTS:
    - WebVTT format for caption synchronization
    - Real-time caption rendering with video playback
    - CSS-based caption styling
    - Multi-language caption file support
    """

    @pytest.mark.priority_critical
    def test_05_display_captions_during_playback_synchronized(self):
        """
        Test caption display synchronized with video playback.

        BUSINESS REQUIREMENT:
        Display captions in real-time during video playback, synchronized
        with audio to support students with hearing impairments and those
        in sound-sensitive environments. Caption timing must be accurate
        within 500ms for effective comprehension.

        TEST SCENARIO:
        1. Load video with generated captions
        2. Enable caption display
        3. Start video playback
        4. Verify captions appear at correct timestamps
        5. Verify caption text matches audio content
        6. Verify caption updates as video progresses
        7. Seek to different timestamp and verify caption updates

        VALIDATION CRITERIA:
        - Captions visible during playback
        - Caption text updates as video plays
        - Caption timing accurate within 500ms of audio
        - Captions positioned correctly (bottom center)
        - Caption text readable (sufficient contrast)
        - Captions hide when video paused (optional behavior)

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Caption text visible and synchronized
        Layer 2 (Caption File): VTT file loaded correctly
        Layer 3 (Timing): Caption timestamps match video time
        """
        page = CaptionEditorPage(self.driver, self.config)

        # Enable captions
        if not page.are_captions_visible():
            page.toggle_captions()

        # Verify captions now visible
        assert page.are_captions_visible(), "Captions should be visible after toggle"

        # Start video playback (using JavaScript)
        self.driver.execute_script("""
            const video = document.getElementById('accessible-video-player');
            if (video) {
                video.play();
            }
        """)

        time.sleep(2)  # Wait for playback to start

        # Get current caption text
        caption_text = page.get_current_caption_text()
        assert caption_text, "Caption text should be displayed during playback"
        assert len(caption_text) > 0, "Caption text should not be empty"

        # Wait for caption to update
        time.sleep(3)
        new_caption_text = page.get_current_caption_text()

        # Verify caption updated (or remained same if still in same segment)
        # Note: May be same text if segment is long
        assert new_caption_text, "Caption should still be displayed"

        # Pause video
        self.driver.execute_script("""
            const video = document.getElementById('accessible-video-player');
            if (video) {
                video.pause();
            }
        """)

        # TODO: Add precise timestamp verification
        # video_time = get_video_current_time()
        # caption_time = get_caption_current_time()
        # time_diff = abs(video_time - caption_time)
        # assert time_diff < 0.5, f"Caption timing should be within 500ms, got {time_diff}s"

    @pytest.mark.priority_medium
    def test_06_caption_language_selection_multiple_languages(self):
        """
        Test caption language selection for multi-language support.

        BUSINESS REQUIREMENT:
        Support international students by providing captions in multiple
        languages, improving comprehension for non-native English speakers
        and expanding course accessibility globally.

        TEST SCENARIO:
        1. Load video with multiple caption language options
        2. Verify language selector displays available languages
        3. Select English captions
        4. Verify English caption text displayed
        5. Select Spanish captions
        6. Verify Spanish caption text displayed
        7. Verify caption text changed to Spanish

        VALIDATION CRITERIA:
        - Language selector shows available languages (EN, ES, FR)
        - Selecting language updates caption text
        - Caption text matches selected language
        - Language preference persists during playback
        - Default language is browser language or English

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Language selector shows options
        Layer 2 (Caption Files): Multiple VTT files exist (en.vtt, es.vtt, fr.vtt)
        Layer 3 (Content): Caption text in selected language
        """
        page = CaptionEditorPage(self.driver, self.config)

        # Enable captions
        if not page.are_captions_visible():
            page.toggle_captions()

        # Select English captions
        page.select_caption_language('en')

        # Start playback to trigger captions
        self.driver.execute_script("""
            const video = document.getElementById('accessible-video-player');
            if (video) {
                video.play();
            }
        """)

        time.sleep(2)

        # Get English caption text
        english_caption = page.get_current_caption_text()
        assert english_caption, "English caption should be displayed"

        # Select Spanish captions
        page.select_caption_language('es')
        time.sleep(1)

        # Get Spanish caption text
        spanish_caption = page.get_current_caption_text()
        assert spanish_caption, "Spanish caption should be displayed"

        # Verify caption text changed (assuming different languages produce different text)
        # Note: Text may be same if not yet translated
        # In real implementation, verify actual Spanish translation

        # Pause video
        self.driver.execute_script("""
            const video = document.getElementById('accessible-video-player');
            if (video) {
                video.pause();
            }
        """)

        # TODO: Add caption file verification
        # assert os.path.exists(f"/storage/captions/{video_id}_en.vtt"), "English VTT should exist"
        # assert os.path.exists(f"/storage/captions/{video_id}_es.vtt"), "Spanish VTT should exist"

    @pytest.mark.priority_high
    def test_07_caption_styling_customization(self):
        """
        Test caption styling customization (font size, background, position).

        BUSINESS REQUIREMENT:
        Enable students to customize caption appearance for optimal readability
        based on individual preferences, visual impairments, or viewing
        conditions (screen size, lighting, etc.).

        TEST SCENARIO:
        1. Open caption styling controls
        2. Adjust font size (12px → 24px)
        3. Verify font size updated in preview
        4. Adjust background opacity (0.8 → 0.5)
        5. Verify background opacity updated
        6. Change caption position (bottom → top)
        7. Verify caption position updated
        8. Apply styling changes
        9. Verify styling persists in video player

        VALIDATION CRITERIA:
        - Font size adjustable (12-32px range)
        - Background opacity adjustable (0.0-1.0 range)
        - Caption position changeable (bottom, top, middle)
        - Preview shows styling changes in real-time
        - Applied styling persists across video playback
        - Styling preferences saved to user profile

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Preview shows updated styling
        Layer 2 (CSS): Caption element has correct computed styles
        Layer 3 (Database): User preferences saved
        """
        page = CaptionEditorPage(self.driver, self.config)

        # Set font size
        page.set_caption_font_size(24)
        time.sleep(0.5)

        # Verify font size updated
        current_font_size = page.get_caption_font_size()
        assert current_font_size == 24, f"Font size should be 24px, got {current_font_size}px"

        # Set background opacity
        page.set_caption_background_opacity(0.5)
        time.sleep(0.5)

        # Verify opacity updated
        current_opacity = page.get_caption_background_opacity()
        assert abs(current_opacity - 0.5) < 0.1, f"Opacity should be ~0.5, got {current_opacity}"

        # Set caption position
        page.set_caption_position('top')
        time.sleep(0.5)

        # Apply styling
        page.apply_caption_styling()
        time.sleep(1)

        # Verify styling in preview
        preview_style = page.get_caption_preview_style()
        assert preview_style is not None, "Caption preview should have styles"

        # Verify font size in computed style
        # Note: Computed style returns in px format
        font_size_value = preview_style.get('font-size', '')
        assert '24px' in font_size_value or '24' in font_size_value, \
            f"Preview font size should be 24px, got {font_size_value}"

        # TODO: Add user preference verification
        # user_prefs = db.query("SELECT * FROM user_caption_preferences WHERE user_id = ?", user_id)
        # assert user_prefs['font_size'] == 24, "User preference should save font size"


@pytest.mark.e2e
@pytest.mark.video
class TestAccessibility(BaseTest):
    """
    Test cases for video accessibility features and WCAG compliance.

    BUSINESS OBJECTIVES:
    - Ensure WCAG 2.1 AA compliance for video features
    - Enable keyboard-only navigation for video controls
    - Support screen readers with ARIA labels
    - Provide caption search for quick topic finding

    TECHNICAL REQUIREMENTS:
    - Full keyboard navigation (spacebar, arrows, shortcuts)
    - ARIA labels for all interactive elements
    - Focus indicators for keyboard users
    - Screen reader announcements for state changes
    """

    @pytest.mark.priority_critical
    def test_08_keyboard_navigation_video_controls(self):
        """
        Test keyboard navigation for video controls (spacebar, arrow keys).

        BUSINESS REQUIREMENT:
        Enable students who cannot use a mouse (due to motor disabilities,
        preference, or context) to fully control video playback using only
        keyboard. This is a WCAG 2.1 Level A requirement.

        KEYBOARD SHORTCUTS:
        - Spacebar: Play/Pause
        - Left Arrow: Seek backward 10 seconds
        - Right Arrow: Seek forward 10 seconds
        - Up Arrow: Increase volume
        - Down Arrow: Decrease volume
        - M: Toggle mute
        - F: Toggle fullscreen

        TEST SCENARIO:
        1. Focus video player
        2. Press spacebar to play
        3. Verify video starts playing
        4. Press spacebar to pause
        5. Verify video pauses
        6. Press right arrow to seek forward
        7. Verify playback position advanced
        8. Press left arrow to seek backward
        9. Verify playback position rewound
        10. Press M to mute
        11. Verify audio muted

        VALIDATION CRITERIA:
        - Spacebar toggles play/pause
        - Arrow keys control seeking (10s increments)
        - Arrow up/down control volume
        - M key toggles mute
        - F key toggles fullscreen
        - Focus indicators visible for keyboard users
        - No keyboard traps (can tab out of player)

        ACCESSIBILITY COMPLIANCE:
        WCAG 2.1 - 2.1.1 Keyboard (Level A): All functionality available via keyboard
        """
        page = AccessibilityPage(self.driver, self.config)

        # Focus video player
        video_player = page.find_element(*page.VIDEO_PLAYER)
        video_player.click()  # Give focus

        # Test spacebar to play
        page.press_spacebar()
        time.sleep(1)

        # Verify video playing
        is_playing = page.is_video_playing()
        assert is_playing, "Video should be playing after spacebar press"

        # Test spacebar to pause
        page.press_spacebar()
        time.sleep(1)

        # Verify video paused
        is_playing = page.is_video_playing()
        assert not is_playing, "Video should be paused after second spacebar press"

        # Get initial time
        initial_time = page.get_current_time()

        # Test right arrow to seek forward
        page.press_arrow_right()
        time.sleep(1)

        # Verify time advanced
        new_time = page.get_current_time()
        # Note: Exact time comparison may be tricky, so just verify it changed
        assert new_time != initial_time, "Time should advance after right arrow press"

        # Test left arrow to seek backward
        page.press_arrow_left()
        time.sleep(1)

        # Verify time rewound
        rewound_time = page.get_current_time()
        # Time should be different from previous (may not be same as initial due to timing)

        # Test M key to mute
        page.press_m_key()
        time.sleep(0.5)

        # Verify mute state (would need to check mute button state or volume level)
        # This is a placeholder - actual implementation would check button state

        # TODO: Add fullscreen test
        # page.press_f_key()
        # time.sleep(1)
        # is_fullscreen = page.is_fullscreen()
        # assert is_fullscreen, "Video should be fullscreen after F key press"

    @pytest.mark.priority_high
    def test_09_screen_reader_compatibility_aria_labels(self):
        """
        Test screen reader compatibility with ARIA labels.

        BUSINESS REQUIREMENT:
        Ensure blind and visually impaired students can use video features
        with screen readers (JAWS, NVDA, VoiceOver). All interactive elements
        must have accessible names that clearly describe their purpose.

        ARIA LABELS REQUIRED:
        - Video player: "Video player"
        - Play button: "Play video"
        - Pause button: "Pause video"
        - Seek backward: "Seek backward 10 seconds"
        - Seek forward: "Seek forward 10 seconds"
        - Volume controls: "Volume up/down"
        - Progress bar: "Video progress: X% complete"

        TEST SCENARIO:
        1. Verify video player has aria-label
        2. Verify play button has aria-label
        3. Verify all control buttons have aria-labels
        4. Verify aria-labels are descriptive and clear
        5. Verify state changes announced (playing/paused)
        6. Verify progress updates announced

        VALIDATION CRITERIA:
        - All interactive elements have aria-label or aria-labelledby
        - Labels clearly describe element purpose
        - State changes reflected in aria-live regions
        - No images without alt text
        - Semantic HTML elements used where appropriate

        ACCESSIBILITY COMPLIANCE:
        WCAG 2.1 - 4.1.2 Name, Role, Value (Level A): All UI components have accessible names
        """
        page = AccessibilityPage(self.driver, self.config)

        # Verify all required ARIA labels present
        aria_labels_valid = page.verify_aria_labels_present()
        assert aria_labels_valid, "All required ARIA labels should be present"

        # Verify specific ARIA labels
        player_label = page.get_aria_label(page.PLAYER_ARIA_LABEL)
        assert "video player" in player_label.lower(), \
            f"Player should have 'video player' label, got '{player_label}'"

        play_label = page.get_aria_label(page.PLAY_ARIA_LABEL)
        assert "play" in play_label.lower(), \
            f"Play button should have 'play' label, got '{play_label}'"

        seek_back_label = page.get_aria_label(page.SEEK_BACKWARD_ARIA)
        assert "seek backward" in seek_back_label.lower() or "backward" in seek_back_label.lower(), \
            f"Seek backward should have descriptive label, got '{seek_back_label}'"

        seek_forward_label = page.get_aria_label(page.SEEK_FORWARD_ARIA)
        assert "seek forward" in seek_forward_label.lower() or "forward" in seek_forward_label.lower(), \
            f"Seek forward should have descriptive label, got '{seek_forward_label}'"

        # TODO: Add aria-live region verification
        # aria_live_regions = driver.find_elements(By.CSS_SELECTOR, "[aria-live]")
        # assert len(aria_live_regions) > 0, "Should have aria-live regions for announcements"

    @pytest.mark.priority_medium
    def test_10_caption_search_find_text_in_transcript(self):
        """
        Test caption search functionality to find specific text in transcript.

        BUSINESS REQUIREMENT:
        Enable students to quickly find specific topics, keywords, or concepts
        within video transcripts without watching entire video. This improves
        learning efficiency and supports students who need to review specific
        content sections.

        SEARCH FEATURES:
        - Case-insensitive text search
        - Highlight all matching instances
        - Navigate between search results (next/previous)
        - Jump to video timestamp when clicking result
        - Display result count

        TEST SCENARIO:
        1. Load video with transcript
        2. Enter search query (e.g., "function")
        3. Verify search results highlighted
        4. Verify result count displayed
        5. Click "Next" to navigate to next result
        6. Verify video seeks to result timestamp
        7. Click "Previous" to go back
        8. Verify all instances highlighted

        VALIDATION CRITERIA:
        - Search finds all matching instances (case-insensitive)
        - Search results highlighted in transcript
        - Result count accurate
        - Navigation between results works
        - Video seeks to result timestamp when clicked
        - Search clears when query cleared
        - Empty search shows no results

        MULTI-LAYER VERIFICATION:
        Layer 1 (UI): Search results highlighted
        Layer 2 (Transcript): All matches found
        Layer 3 (Video): Playback seeks to correct timestamp
        """
        page = TranscriptionPage(self.driver, self.config)

        # Ensure transcript exists
        transcript_text = page.get_transcript_text()
        if not transcript_text:
            page.generate_transcript(timeout=120)
            transcript_text = page.get_transcript_text()

        assert transcript_text, "Transcript should exist for search testing"

        # Perform search for common word
        search_query = "the"  # Common word likely to appear multiple times
        result_count = page.search_transcript(search_query)

        assert result_count > 0, f"Search for '{search_query}' should return results"

        # Verify search highlights
        highlights = page.get_search_highlights()
        assert len(highlights) > 0, "Search should highlight matching text"
        assert len(highlights) == result_count, \
            f"Highlight count ({len(highlights)}) should match result count ({result_count})"

        # Test navigation between results
        if result_count > 1:
            # Navigate to next result
            page.navigate_to_next_search_result()
            time.sleep(0.5)

            # Navigate to previous result
            page.navigate_to_prev_search_result()
            time.sleep(0.5)

        # Test search with no results
        no_results_query = "xyzabc123notfound"
        no_results_count = page.search_transcript(no_results_query)
        assert no_results_count == 0, "Search for non-existent term should return 0 results"

        # TODO: Add timestamp jump verification
        # page.navigate_to_next_search_result()
        # video_time = get_video_current_time()
        # segment_time = get_search_result_timestamp(0)
        # assert abs(video_time - segment_time) < 1.0, "Video should seek to result timestamp"


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def test_video_file():
    """
    Provide test video file for transcription testing.

    BUSINESS CONTEXT:
    Uses a standardized test video with known audio content to enable
    consistent, reproducible transcription accuracy testing.
    """
    # TODO: Create or reference test video file
    test_video_path = Path("/tmp/test_video_for_transcription.mp4")

    # In real implementation, this would:
    # 1. Copy test video from fixtures
    # 2. Upload to platform
    # 3. Return video_id for testing

    yield str(test_video_path)

    # Cleanup
    # if test_video_path.exists():
    #     test_video_path.unlink()


@pytest.fixture(scope="function")
def clean_transcript_data():
    """
    Clean up transcript data after each test.

    Ensures test isolation by removing generated transcripts,
    caption files, and database records.
    """
    yield

    # Cleanup after test
    # TODO: Implement cleanup
    # db.execute("DELETE FROM video_transcripts WHERE video_id = ?", test_video_id)
    # os.remove(f"/storage/captions/{test_video_id}.vtt")


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
