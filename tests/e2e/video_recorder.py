"""
Video Recording for Selenium E2E Tests

BUSINESS REQUIREMENT:
Capture video screencasts of test execution for debugging and documentation

TECHNICAL IMPLEMENTATION:
- Uses OpenCV (cv2) to capture frames from Selenium screenshots
- Records at configurable FPS
- Saves as MP4 with H.264 codec
- Minimal performance impact on tests
"""

import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoRecorder:
    """
    Records video of Selenium test execution

    DESIGN PATTERN: Recorder pattern
    Captures frames during test execution and saves as video file

    USAGE:
        recorder = VideoRecorder("test_name", fps=5)
        recorder.start()
        # ... run test ...
        recorder.add_frame(driver.get_screenshot_as_png())
        recorder.stop()
    """

    def __init__(
        self,
        test_name: str,
        output_dir: str = "tests/reports/videos",
        fps: int = 5,
        resolution: tuple = (1920, 1080)
    ):
        """
        Initialize video recorder

        Args:
            test_name: Name of test being recorded
            output_dir: Directory to save videos
            fps: Frames per second (5-10 recommended for tests)
            resolution: Video resolution (width, height)
        """
        self.test_name = test_name
        self.output_dir = output_dir
        self.fps = fps
        self.resolution = resolution

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename = f"{test_name}_{timestamp}.mp4"
        self.filepath = os.path.join(output_dir, self.filename)

        # Video writer (initialized on first frame)
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.frame_count = 0
        self.is_recording = False

    def start(self):
        """Start recording session"""
        self.is_recording = True
        logger.info(f"Started video recording: {self.filename}")

    def add_frame(self, screenshot_data: bytes):
        """
        Add a frame to the video

        Args:
            screenshot_data: PNG screenshot bytes from Selenium
        """
        if not self.is_recording:
            return

        try:
            # Convert PNG bytes to numpy array
            image = Image.open(BytesIO(screenshot_data))

            # Resize to target resolution if needed
            if image.size != self.resolution:
                image = image.resize(self.resolution, Image.Resampling.LANCZOS)

            # Convert to BGR format for OpenCV
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Initialize video writer on first frame
            if self.video_writer is None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(
                    self.filepath,
                    fourcc,
                    self.fps,
                    self.resolution
                )

            # Write frame
            self.video_writer.write(frame)
            self.frame_count += 1

        except Exception as e:
            logger.error(f"Failed to add frame to video: {e}")

    def stop(self) -> str:
        """
        Stop recording and save video

        Returns:
            Path to saved video file
        """
        if not self.is_recording:
            return None

        self.is_recording = False

        if self.video_writer is not None:
            self.video_writer.release()
            logger.info(f"Video saved: {self.filepath} ({self.frame_count} frames)")
        else:
            logger.warning(f"No frames recorded for {self.test_name}")

        return self.filepath

    def capture_frame_from_driver(self, driver):
        """
        Convenience method to capture frame directly from Selenium driver

        Args:
            driver: Selenium WebDriver instance
        """
        try:
            screenshot_png = driver.get_screenshot_as_png()
            self.add_frame(screenshot_png)
        except Exception as e:
            logger.error(f"Failed to capture frame from driver: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False


class FrameCaptureThread:
    """
    Background thread for capturing frames at regular intervals

    USAGE:
        with FrameCaptureThread(driver, recorder, interval=0.2):
            # ... test actions ...
            # Frames captured automatically every 0.2 seconds
    """

    def __init__(self, driver, recorder: VideoRecorder, interval: float = 0.2):
        """
        Initialize frame capture thread

        Args:
            driver: Selenium WebDriver
            recorder: VideoRecorder instance
            interval: Time between captures in seconds
        """
        self.driver = driver
        self.recorder = recorder
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        """Start background frame capture"""
        import threading
        import time

        self.running = True

        def capture_loop():
            while self.running:
                try:
                    self.recorder.capture_frame_from_driver(self.driver)
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Frame capture error: {e}")

        self.thread = threading.Thread(target=capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background frame capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
