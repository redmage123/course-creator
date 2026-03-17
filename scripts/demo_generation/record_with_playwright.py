#!/usr/bin/env python3
"""
Demo Recording with Playwright + OBS

This script coordinates Playwright browser automation with OBS screen recording
to generate demo screencasts. It handles:
- Self-signed certificates (HTTPS)
- OBS recording control
- Automated browser interactions
- Video file management

USAGE:
    DISPLAY=:99 python scripts/demo_generation/record_with_playwright.py --slide 1
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Playwright async API
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.demo_generation.demo_recorder import DEMO_SLIDES, DemoSlide

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv('DEMO_BASE_URL', 'https://localhost:3000')
OUTPUT_DIR = Path('frontend-legacy/static/demo/videos')
DISPLAY = os.getenv('DISPLAY', ':99')


class OBSRecorder:
    """
    Controls OBS Studio for screen recording via CLI.

    Since OBS WebSocket may not always be available,
    this uses ffmpeg as a reliable fallback for screen recording.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recording_process = None
        self.current_output: Optional[Path] = None

    def start_recording(self, output_name: str) -> bool:
        """
        Start screen recording using ffmpeg.

        Args:
            output_name: Name for the output video file (without extension)

        Returns:
            True if recording started successfully
        """
        self.current_output = self.output_dir / f"{output_name}.mp4"

        # Use ffmpeg for reliable screen recording
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-f', 'x11grab',
            '-video_size', '1920x1080',
            '-framerate', '30',
            '-i', DISPLAY,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            str(self.current_output)
        ]

        try:
            self.recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, 'DISPLAY': DISPLAY}
            )
            logger.info(f"Started recording: {self.current_output}")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> Optional[Path]:
        """
        Stop the current recording.

        Returns:
            Path to the recorded video file
        """
        if self.recording_process:
            # Send SIGTERM for graceful shutdown
            self.recording_process.terminate()
            try:
                self.recording_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.recording_process.kill()

            self.recording_process = None
            logger.info(f"Stopped recording: {self.current_output}")

            # Verify file was created
            if self.current_output and self.current_output.exists():
                return self.current_output
            return None

        return None


class DemoPlaywright:
    """
    Executes demo workflows using Playwright.

    Handles browser automation for demo recordings including:
    - Self-signed certificate acceptance
    - Page navigation
    - Element interactions
    - Screenshot capture
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self):
        """Start Playwright browser with proper configuration."""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Show browser for recording
            args=[
                '--start-maximized',
                '--ignore-certificate-errors',
                '--disable-web-security',
            ]
        )

        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,  # Accept self-signed certs
        )

        self.page = await self.context.new_page()
        logger.info("Playwright browser started")

    async def stop(self):
        """Stop Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser stopped")

    async def execute_slide(self, slide: DemoSlide) -> Dict[str, Any]:
        """
        Execute all actions for a demo slide.

        Args:
            slide: DemoSlide with actions to execute

        Returns:
            Result dictionary with execution details
        """
        result = {
            "slide_id": slide.id,
            "title": slide.title,
            "actions_executed": 0,
            "errors": [],
            "screenshots": []
        }

        logger.info(f"Executing slide {slide.id}: {slide.title}")

        for action in slide.actions:
            try:
                await self._execute_action(action, result)
                result["actions_executed"] += 1

                # Wait after action
                if action.wait_after > 0:
                    await asyncio.sleep(action.wait_after)

            except Exception as e:
                error_msg = f"Action '{action.action}' failed: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

        return result

    async def _execute_action(self, action, result: Dict):
        """Execute a single demo action."""

        if action.action == "navigate":
            url = action.target if action.target.startswith('http') else f"{BASE_URL}{action.target}"
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='domcontentloaded')

        elif action.action == "click":
            logger.info(f"Clicking: {action.target}")
            await self.page.click(action.target, timeout=10000)

        elif action.action == "type":
            logger.info(f"Typing in: {action.target}")
            await self.page.fill(action.target, action.value)

        elif action.action == "wait":
            if action.target:
                logger.info(f"Waiting for text: {action.target}")
                await self.page.wait_for_selector(f'text={action.target}', timeout=30000)
            else:
                wait_time = float(action.value or 1)
                logger.info(f"Waiting {wait_time}s")
                await asyncio.sleep(wait_time)

        elif action.action == "hover":
            logger.info(f"Hovering: {action.target}")
            try:
                await self.page.hover(action.target, timeout=5000)
            except Exception:
                logger.warning(f"Could not hover on {action.target}, continuing...")

        elif action.action == "snapshot" or action.action == "screenshot":
            screenshot_path = OUTPUT_DIR / f"slide_{result['slide_id']:02d}_snapshot.png"
            await self.page.screenshot(path=str(screenshot_path))
            result["screenshots"].append(str(screenshot_path))
            logger.info(f"Screenshot saved: {screenshot_path}")


async def record_slide(slide_id: int) -> Dict[str, Any]:
    """
    Record a single demo slide.

    Args:
        slide_id: ID of the slide to record

    Returns:
        Recording result with file paths and status
    """
    # Find slide
    slide = None
    for s in DEMO_SLIDES:
        if s.id == slide_id:
            slide = s
            break

    if not slide:
        return {"error": f"Slide {slide_id} not found"}

    output_name = f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_').replace('-', '_')}"

    # Initialize components
    recorder = OBSRecorder(OUTPUT_DIR)
    playwright = DemoPlaywright()

    result = {
        "slide_id": slide.id,
        "title": slide.title,
        "output_file": None,
        "status": "failed"
    }

    try:
        # Start browser
        await playwright.start()

        # Start recording
        recorder.start_recording(output_name)

        # Wait for recording to initialize
        await asyncio.sleep(1)

        # Execute slide actions
        execution_result = await playwright.execute_slide(slide)
        result.update(execution_result)

        # Wait a moment after actions complete
        await asyncio.sleep(2)

        # Stop recording
        output_file = recorder.stop_recording()
        if output_file:
            result["output_file"] = str(output_file)
            result["status"] = "success"

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Recording failed: {e}")
        recorder.stop_recording()

    finally:
        await playwright.stop()

    return result


async def record_all_slides(slide_range: str = "all") -> List[Dict[str, Any]]:
    """
    Record multiple demo slides.

    Args:
        slide_range: "all", single ID "1", range "1-5", or list "1,3,5"

    Returns:
        List of recording results
    """
    # Parse slide range
    if slide_range == "all":
        slides = DEMO_SLIDES
    elif "-" in slide_range:
        start, end = map(int, slide_range.split("-"))
        slides = [s for s in DEMO_SLIDES if start <= s.id <= end]
    elif "," in slide_range:
        ids = [int(x) for x in slide_range.split(",")]
        slides = [s for s in DEMO_SLIDES if s.id in ids]
    else:
        slides = [s for s in DEMO_SLIDES if s.id == int(slide_range)]

    results = []

    for slide in slides:
        logger.info(f"\n{'='*60}")
        logger.info(f"Recording slide {slide.id}: {slide.title}")
        logger.info(f"{'='*60}\n")

        result = await record_slide(slide.id)
        results.append(result)

        # Brief pause between slides
        await asyncio.sleep(2)

    return results


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Record demo slides with Playwright + ffmpeg")
    parser.add_argument("--slide", "-s", default="1", help="Slide(s) to record")
    parser.add_argument("--list", "-l", action="store_true", help="List slides")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Demo Slides:")
        for slide in DEMO_SLIDES:
            print(f"  {slide.id:2d}. {slide.title} ({slide.duration_seconds}s)")
        return

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Record slides
    results = await record_all_slides(args.slide)

    # Summary
    print("\n" + "="*60)
    print("RECORDING COMPLETE")
    print("="*60)

    success_count = sum(1 for r in results if r.get("status") == "success")
    print(f"Successful: {success_count}/{len(results)}")

    for r in results:
        status = "✅" if r.get("status") == "success" else "❌"
        print(f"  {status} Slide {r['slide_id']}: {r.get('output_file', 'FAILED')}")

    # Save results
    results_file = OUTPUT_DIR / "recording_results.json"
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
