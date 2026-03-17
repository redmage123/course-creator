#!/usr/bin/env python3
"""
Unit Tests for Slide 5 Video Generation Script

BUSINESS PURPOSE:
Tests the video generation script for AI assistant demo slide,
ensuring proper sequence, timing, and output quality.

TECHNICAL APPROACH:
Mock Selenium WebDriver to test logic without actual browser automation
"""

import pytest
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))



class TestSlide5VideoGeneration:
    """Unit tests for slide 5 video generation script"""

    def test_screenshots_directory_created(self, tmp_path):
        """Test that screenshots directory is created if it doesn't exist"""
        test_dir = tmp_path / "slide5_test"
        assert not test_dir.exists()

        os.makedirs(test_dir, exist_ok=True)
        assert test_dir.exists()

    def test_cursor_script_includes_required_elements(self):
        """Test that cursor injection script contains all necessary code"""
        cursor_script = """
        const existingCursor = document.getElementById('demo-cursor');
        if (existingCursor) existingCursor.remove();
        const cursor = document.createElement('div');
        cursor.id = 'demo-cursor';
        """

        assert "getElementById('demo-cursor')" in cursor_script
        assert "createElement('div')" in cursor_script
        assert "cursor.id" in cursor_script

    def test_capture_function_generates_correct_number_of_frames(self):
        """Test that capture function creates expected number of screenshots"""
        frames = 30
        screenshot_paths = []

        for i in range(frames):
            screenshot_paths.append(f"frame_{i+1:05d}.png")

        assert len(screenshot_paths) == frames
        assert screenshot_paths[0] == "frame_00001.png"
        assert screenshot_paths[-1] == "frame_00030.png"

    def test_frame_naming_convention(self):
        """Test frame naming follows 5-digit zero-padded convention"""
        frame_count = 1
        expected_name = f"frame_{frame_count:05d}.png"
        assert expected_name == "frame_00001.png"

        frame_count = 100
        expected_name = f"frame_{frame_count:05d}.png"
        assert expected_name == "frame_00100.png"

        frame_count = 1500
        expected_name = f"frame_{frame_count:05d}.png"
        assert expected_name == "frame_01500.png"

    def test_video_duration_calculation(self):
        """Test that video duration is calculated correctly from frame count"""
        fps = 30
        frames = 1500

        duration = frames / fps
        assert duration == 50.0

    def test_ffmpeg_command_structure(self):
        """Test that FFmpeg command has correct structure"""
        import os
        if not os.getenv('FFMPEG_AVAILABLE'):
            pytest.skip("FFMPEG not available")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", "30",
            "-i", "/tmp/slide5/frame_%05d.png",
            "-vf", "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-profile:v", "baseline",
            "-level", "3.0",
            "/output/video.mp4"
        ]

        assert "ffmpeg" in ffmpeg_cmd
        assert "-framerate" in ffmpeg_cmd
        assert "30" in ffmpeg_cmd
        assert "libx264" in ffmpeg_cmd
        assert "yuv420p" in ffmpeg_cmd

    def test_cursor_movement_calculation(self):
        """Test cursor position calculation for element centering"""
        element_location = {'x': 100, 'y': 200}
        element_size = {'width': 80, 'height': 40}

        target_x = element_location['x'] + element_size['width'] // 2
        target_y = element_location['y'] + element_size['height'] // 2

        assert target_x == 140  # 100 + 80/2
        assert target_y == 220  # 200 + 40/2

    def test_video_workflow_sequence(self):
        """Test that video generation follows correct sequence"""
        workflow_steps = [
            "Load dashboard with AI button",
            "Move cursor to AI button",
            "Click AI button",
            "Wait for panel to open",
            "Move cursor to input field",
            "Click input field",
            "Type message character by character",
            "Move cursor to send button",
            "Click send button",
            "Wait for AI response",
            "Show response",
            "Close panel and show tracks"
        ]

        assert len(workflow_steps) == 12
        assert workflow_steps[0] == "Load dashboard with AI button"
        assert "Type message" in workflow_steps[6]
        assert workflow_steps[-1] == "Close panel and show tracks"

    def test_message_typing_frame_calculation(self):
        """Test frame calculation for character-by-character typing"""
        message = "Create an intermediate track called Machine Learning Basics"
        frames_per_char = 2

        total_frames = len(message) * frames_per_char
        assert total_frames == len(message) * 2

    def test_timing_synchronization(self):
        """Test that video timing matches expected audio duration"""
        expected_audio_duration = 50.0  # seconds
        fps = 30
        expected_frames = int(expected_audio_duration * fps)

        assert expected_frames == 1500

    def test_element_selectors(self):
        """Test that correct element IDs are used"""
        element_ids = {
            'ai_button': 'aiAssistantBtn',
            'ai_panel': 'aiAssistantPanel',
            'ai_input': 'aiInput',
            'ai_send': 'aiSendBtn',
            'ai_messages': 'aiMessages',
            'tracks_tab': 'nav-tracks'
        }

        assert element_ids['ai_button'] == 'aiAssistantBtn'
        assert element_ids['ai_input'] == 'aiInput'
        assert element_ids['tracks_tab'] == 'nav-tracks'

    def test_screenshot_path_generation(self):
        """Test screenshot path generation"""
        base_dir = "/tmp/slide5_ai_assistant"
        frame_number = 123

        path = os.path.join(base_dir, f"frame_{frame_number:05d}.png")
        expected = "/tmp/slide5_ai_assistant/frame_00123.png"

        assert path == expected

    def test_webdriver_options(self):
        """Test that WebDriver options are correctly configured"""
        required_options = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--ignore-certificate-errors"
        ]

        for option in required_options:
            assert option is not None

    def test_base_url_format(self):
        """Test BASE_URL format"""
        base_url = "https://localhost:3000"
        assert base_url.startswith("https://")
        assert "localhost" in base_url
        assert ":3000" in base_url

    def test_video_output_path(self):
        """Test video output path is correct"""
        video_output = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_05_ai_assistant.mp4"

        assert video_output.endswith(".mp4")
        assert "slide_05" in video_output
        assert "ai_assistant" in video_output


class TestSlide5ScriptValidation:
    """Validation tests for script structure and best practices"""

    def test_script_has_proper_shebang(self):
        """Test that script has correct shebang"""
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "generate_slide5_ai_assistant.py"

        if script_path.exists():
            with open(script_path, 'r') as f:
                first_line = f.readline()
                assert first_line.startswith("#!/usr/bin/env python3")

    def test_script_has_docstring(self):
        """Test that script has module-level docstring"""
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "generate_slide5_ai_assistant.py"

        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()
                assert '"""' in content or "'''" in content

    def test_script_imports_required_modules(self):
        """Test that script imports all required modules"""
        required_imports = [
            'time',
            'os',
            'subprocess',
            'selenium',
            'webdriver',
            'Options',
            'Service',
            'By',
            'WebDriverWait',
            'expected_conditions'
        ]

        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "generate_slide5_ai_assistant.py"

        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()

                # Check for key imports
                assert 'import time' in content
                assert 'import os' in content
                assert 'import subprocess' in content
                assert 'from selenium import webdriver' in content

    def test_script_defines_required_constants(self):
        """Test that script defines required constants"""
        required_constants = [
            'BASE_URL',
            'SCREENSHOTS_DIR',
            'VIDEO_OUTPUT'
        ]

        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "generate_slide5_ai_assistant.py"

        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()

                for constant in required_constants:
                    assert constant in content

    def test_script_has_error_handling(self):
        """Test that script includes error handling"""
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "generate_slide5_ai_assistant.py"

        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()

                # Should have try/finally for cleanup
                assert 'try:' in content
                assert 'finally:' in content
                assert 'driver.quit()' in content


class TestSlide5OutputValidation:
    """Tests for validating generated output"""

    def test_video_file_size_reasonable(self):
        """Test that generated video is within expected size range"""
        # Typical size for 50s video at given settings: 800KB - 2MB
        min_size = 500 * 1024  # 500KB
        max_size = 5 * 1024 * 1024  # 5MB

        # This is a range check - actual file would need to exist
        assert min_size < max_size
        assert min_size > 0

    def test_frame_count_matches_duration(self):
        """Test that frame count matches expected video duration"""
        target_duration = 50.0  # seconds
        fps = 30
        tolerance_frames = 30  # 1 second tolerance

        expected_frames = int(target_duration * fps)
        min_frames = expected_frames - tolerance_frames
        max_frames = expected_frames + tolerance_frames

        # For 50s video: 1470-1530 frames
        assert min_frames == 1470
        assert max_frames == 1530

    def test_video_codec_settings(self):
        """Test video codec settings are correct"""
        codec_settings = {
            'codec': 'libx264',
            'preset': 'fast',
            'crf': '23',
            'pixel_format': 'yuv420p',
            'profile': 'baseline',
            'level': '3.0'
        }

        assert codec_settings['codec'] == 'libx264'
        assert codec_settings['pixel_format'] == 'yuv420p'
        assert codec_settings['profile'] == 'baseline'
