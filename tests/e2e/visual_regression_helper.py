"""
Visual Regression Testing Helper

BUSINESS PURPOSE:
Provides reusable visual regression testing capabilities for E2E tests.
Captures screenshots, compares them to baselines, and generates diff images
to detect unintended UI changes.

USAGE:
    from visual_regression_helper import VisualRegressionHelper

    # In your test class:
    def setup_method(self):
        self.visual = VisualRegressionHelper(
            self.driver,
            test_name="my_dashboard",
            threshold=0.01  # 1% difference tolerance
        )

    # In your tests:
    def test_ui_element(self):
        self.visual.capture_and_compare("element_name", element_selector="#myElement")
        # Or full page:
        self.visual.capture_and_compare("full_page")

WHY THIS APPROACH:
- Centralizes visual regression logic for reuse across all test suites
- Provides consistent baseline management and comparison methodology
- Automatically generates diff images highlighting visual changes
- Configurable tolerance levels for minor rendering variations
- Supports both full-page and element-specific screenshots

INTEGRATION WITH TDD:
- Run with --update-baselines flag to create/update baseline images
- Tests fail when visual changes exceed threshold
- Diff images help identify unintended layout breaks

@module visual_regression_helper
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageChops, ImageDraw, ImageFont
import numpy as np
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logger = logging.getLogger(__name__)


class VisualRegressionHelper:
    """
    Helper class for visual regression testing

    BUSINESS RULES:
    - Baseline images are the "golden" reference screenshots
    - Test images are captured during test execution
    - Diff images highlight pixel-level differences
    - Tests pass if difference percentage < threshold

    FILE ORGANIZATION:
    tests/e2e/dashboards/visual_regression/
        baselines/{test_name}/
            {screenshot_name}.png
        results/{test_name}/
            {screenshot_name}.png
        diffs/{test_name}/
            {screenshot_name}_diff.png
    """

    def __init__(
        self,
        driver,
        test_name: str,
        threshold: float = 0.02,  # 2% default tolerance
        base_path: Optional[Path] = None,
        update_baselines: bool = False
    ):
        """
        Initialize visual regression helper

        PARAMETERS:
        - driver: Selenium WebDriver instance
        - test_name: Name of test suite (used for directory organization)
        - threshold: Maximum allowed difference percentage (0.0-1.0)
        - base_path: Root directory for visual regression files
        - update_baselines: If True, saves new baselines instead of comparing

        WHY THRESHOLD:
        Minor rendering differences (antialiasing, font rendering) are acceptable.
        2% threshold catches real layout issues while ignoring trivial pixel variations.
        """
        self.driver = driver
        self.test_name = test_name
        self.threshold = threshold
        self.update_baselines = update_baselines

        # Set up directory structure
        if base_path is None:
            base_path = Path(__file__).parent / "dashboards" / "visual_regression"

        self.base_path = Path(base_path)
        self.baselines_dir = self.base_path / "baselines" / test_name
        self.results_dir = self.base_path / "results" / test_name
        self.diffs_dir = self.base_path / "diffs" / test_name

        # Create directories
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Visual regression helper initialized for '{test_name}'")
        logger.info(f"Threshold: {threshold * 100}%")
        logger.info(f"Update baselines mode: {update_baselines}")

    def capture_screenshot(
        self,
        name: str,
        element_selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        wait_timeout: int = 10
    ) -> Path:
        """
        Capture a screenshot

        BUSINESS PURPOSE:
        Takes a screenshot of either full page or specific element.
        Optionally waits for element to be visible before capturing.

        PARAMETERS:
        - name: Screenshot identifier (becomes filename)
        - element_selector: CSS selector for element-specific screenshot
        - wait_for_selector: Wait for this element before capturing
        - wait_timeout: Maximum seconds to wait for element

        RETURNS:
        Path to saved screenshot file

        WHY WAIT BEFORE CAPTURE:
        Ensures animations complete and lazy-loaded content appears.
        Prevents capturing transitional states that aren't representative.
        """
        # Wait for element if specified
        if wait_for_selector:
            try:
                WebDriverWait(self.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
                time.sleep(0.5)  # Additional stabilization time
            except TimeoutException:
                logger.warning(f"Element '{wait_for_selector}' not found within {wait_timeout}s")

        # Determine output path
        output_path = self.results_dir / f"{name}.png"

        # Capture screenshot
        if element_selector:
            # Element-specific screenshot
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                element.screenshot(str(output_path))
                logger.info(f"Captured element screenshot: {name} ({element_selector})")
            except NoSuchElementException:
                logger.error(f"Element not found for screenshot: {element_selector}")
                # Fall back to full page
                self.driver.save_screenshot(str(output_path))
        else:
            # Full page screenshot
            self.driver.save_screenshot(str(output_path))
            logger.info(f"Captured full page screenshot: {name}")

        return output_path

    def compare_images(
        self,
        baseline_path: Path,
        result_path: Path,
        diff_path: Path
    ) -> Tuple[float, bool]:
        """
        Compare two images and generate diff

        BUSINESS PURPOSE:
        Performs pixel-by-pixel comparison of baseline vs current screenshot.
        Generates visual diff highlighting changed regions.

        ALGORITHM:
        1. Load both images and ensure same dimensions
        2. Calculate pixel-level difference using PIL ImageChops
        3. Compute percentage of changed pixels
        4. Generate diff image with red highlights on changes
        5. Return (difference_percentage, passes_threshold)

        RETURNS:
        (difference_percentage, passes_threshold)
        - difference_percentage: 0.0-1.0 representing % of pixels changed
        - passes_threshold: True if difference < threshold

        WHY PIXEL-LEVEL COMPARISON:
        Catches subtle layout shifts, rendering bugs, CSS issues that
        functional tests might miss. Visual bugs matter to users.
        """
        # Load images
        baseline = Image.open(baseline_path).convert('RGB')
        result = Image.open(result_path).convert('RGB')

        # Ensure same dimensions
        if baseline.size != result.size:
            logger.warning(f"Image size mismatch: baseline={baseline.size}, result={result.size}")
            # Resize result to match baseline
            result = result.resize(baseline.size, Image.LANCZOS)

        # Calculate difference
        diff = ImageChops.difference(baseline, result)

        # Convert to numpy for analysis
        diff_array = np.array(diff)

        # Count changed pixels (any channel > 0)
        changed_pixels = np.any(diff_array > 30, axis=2)  # 30 = threshold for "significant" change
        total_pixels = diff_array.shape[0] * diff_array.shape[1]
        difference_percentage = np.sum(changed_pixels) / total_pixels

        # Generate visual diff image
        # Convert diff to grayscale, then colorize red for changes
        diff_gray = diff.convert('L')
        diff_colored = Image.new('RGB', baseline.size)

        for x in range(baseline.width):
            for y in range(baseline.height):
                base_pixel = baseline.getpixel((x, y))
                diff_pixel = diff_gray.getpixel((x, y))

                if diff_pixel > 30:  # Significant change
                    # Highlight in red
                    diff_colored.putpixel((x, y), (255, 0, 0))
                else:
                    # Show baseline
                    diff_colored.putpixel((x, y), base_pixel)

        # Add text annotation
        draw = ImageDraw.Draw(diff_colored)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()

        text = f"Diff: {difference_percentage * 100:.2f}% | Threshold: {self.threshold * 100:.2f}%"
        status = "PASS" if difference_percentage < self.threshold else "FAIL"
        color = (0, 255, 0) if difference_percentage < self.threshold else (255, 0, 0)

        draw.text((10, 10), text, fill=color, font=font)
        draw.text((10, 30), f"Status: {status}", fill=color, font=font)

        # Save diff image
        diff_colored.save(diff_path)

        passes = difference_percentage < self.threshold
        logger.info(f"Visual comparison: {difference_percentage * 100:.2f}% difference ({status})")

        return difference_percentage, passes

    def capture_and_compare(
        self,
        name: str,
        element_selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        custom_threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Main method: Capture screenshot and compare to baseline

        BUSINESS PURPOSE:
        One-line method to add visual regression testing to any test.
        Handles all workflow: capture, compare, update baselines, assertions.

        WORKFLOW:
        1. Capture current screenshot
        2. If update_baselines mode: Copy to baselines and return
        3. If baseline exists: Compare and return result
        4. If no baseline: Create one and warn

        PARAMETERS:
        - name: Screenshot identifier
        - element_selector: Optional CSS selector for element screenshot
        - wait_for_selector: Wait for element before capture
        - custom_threshold: Override default threshold for this comparison

        RETURNS:
        (passed, difference_percentage)

        USAGE IN TESTS:
        assert self.visual.capture_and_compare("dashboard_loaded")[0], \
            "Visual regression detected in dashboard"
        """
        threshold = custom_threshold if custom_threshold is not None else self.threshold

        # Capture current screenshot
        result_path = self.capture_screenshot(
            name,
            element_selector=element_selector,
            wait_for_selector=wait_for_selector
        )

        baseline_path = self.baselines_dir / f"{name}.png"
        diff_path = self.diffs_dir / f"{name}_diff.png"

        # Update baselines mode
        if self.update_baselines:
            import shutil
            shutil.copy(result_path, baseline_path)
            logger.info(f"Baseline updated: {name}")
            return True, 0.0

        # Check if baseline exists
        if not baseline_path.exists():
            # First run - create baseline
            import shutil
            shutil.copy(result_path, baseline_path)
            logger.warning(f"No baseline found for '{name}'. Created baseline from current screenshot.")
            return True, 0.0

        # Compare to baseline
        difference_percentage, passes = self.compare_images(
            baseline_path,
            result_path,
            diff_path
        )

        if not passes:
            logger.error(
                f"Visual regression detected in '{name}': "
                f"{difference_percentage * 100:.2f}% > {threshold * 100:.2f}%"
            )
            logger.error(f"Diff image saved to: {diff_path}")

        return passes, difference_percentage

    def assert_visual_match(
        self,
        name: str,
        element_selector: Optional[str] = None,
        message: Optional[str] = None
    ):
        """
        Assert-style method for visual regression

        BUSINESS PURPOSE:
        Provides assertion-style API for visual testing.
        Automatically raises AssertionError if visual regression detected.

        USAGE:
        self.visual.assert_visual_match("modal_open", element_selector="#myModal")

        WHY ASSERT STYLE:
        Matches pytest assertion patterns. Test fails immediately on visual regression.
        Clear failure messages with diff image path.
        """
        passed, diff = self.capture_and_compare(name, element_selector=element_selector)

        if not passed:
            error_msg = message or (
                f"Visual regression detected in '{name}': "
                f"{diff * 100:.2f}% difference exceeds {self.threshold * 100:.2f}% threshold. "
                f"Check diff image: {self.diffs_dir / f'{name}_diff.png'}"
            )
            raise AssertionError(error_msg)

    def cleanup_old_results(self, days: int = 7):
        """
        Clean up old test results and diffs

        BUSINESS PURPOSE:
        Prevents visual regression directory from growing indefinitely.
        Keeps recent results for debugging while cleaning old data.

        WHY 7 DAYS DEFAULT:
        Allows time for CI/CD review and debugging while preventing bloat.
        Baselines are never auto-cleaned (they're the source of truth).
        """
        import time
        cutoff_time = time.time() - (days * 86400)

        for directory in [self.results_dir, self.diffs_dir]:
            for file_path in directory.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Cleaned old file: {file_path}")


class VisualRegressionConfig:
    """
    Configuration for visual regression testing

    BUSINESS PURPOSE:
    Centralized configuration for visual regression behavior across test suites.
    Allows environment-specific settings (CI vs local).
    """

    # Default threshold for all tests
    DEFAULT_THRESHOLD = 0.02  # 2%

    # Per-test thresholds (some UI elements need higher tolerance)
    CUSTOM_THRESHOLDS = {
        "animated_elements": 0.05,  # 5% for animations
        "dynamic_charts": 0.10,  # 10% for data visualizations
        "video_thumbnails": 0.15,  # 15% for media content
    }

    # Whether to update baselines (typically set via pytest flag)
    UPDATE_BASELINES = os.environ.get("UPDATE_BASELINES", "false").lower() == "true"

    # Browser-specific settings
    BROWSER_THRESHOLDS = {
        "chrome": 0.02,
        "firefox": 0.03,  # Firefox renders slightly differently
        "safari": 0.04,
    }

    @classmethod
    def get_threshold(cls, test_name: str, browser: str = "chrome") -> float:
        """Get appropriate threshold for test"""
        # Check custom thresholds first
        if test_name in cls.CUSTOM_THRESHOLDS:
            return cls.CUSTOM_THRESHOLDS[test_name]

        # Return browser-specific threshold
        return cls.BROWSER_THRESHOLDS.get(browser, cls.DEFAULT_THRESHOLD)
