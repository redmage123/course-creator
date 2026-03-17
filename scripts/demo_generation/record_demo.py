#!/usr/bin/env python3
"""
Complete Demo Recording Script

ORCHESTRATES:
1. OBS/ffmpeg screen recording
2. Playwright browser automation
3. Audio narration playback
4. Final video/audio merging

WORKFLOW:
1. Start screen recording (ffmpeg)
2. Play narration audio
3. Execute Playwright actions in sync with narration
4. Stop recording
5. Merge audio with video using ffmpeg

USAGE:
    DISPLAY=:99 python scripts/demo_generation/record_demo.py --slide 1
    DISPLAY=:99 python scripts/demo_generation/record_demo.py --all
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

# Playwright
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.demo_generation.demo_recorder import DEMO_SLIDES, DemoSlide
from scripts.demo_generation.narrations import get_narration, get_all_narrations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv('DEMO_BASE_URL', 'https://localhost:3000')
DISPLAY = os.getenv('DISPLAY', ':99')
OUTPUT_DIR = Path('frontend-legacy/static/demo/videos')
AUDIO_DIR = Path('frontend-legacy/static/demo/audio')


class ScreenRecorder:
    """Records screen using ffmpeg."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process: Optional[subprocess.Popen] = None
        self.current_output: Optional[Path] = None

    def start(self, output_name: str, resolution: str = "1920x1080") -> bool:
        """Start screen recording."""
        self.current_output = self.output_dir / f"{output_name}_video.mp4"

        cmd = [
            'ffmpeg', '-y',
            '-f', 'x11grab',
            '-video_size', resolution,
            '-framerate', '30',
            '-i', DISPLAY,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '18',
            '-pix_fmt', 'yuv420p',
            str(self.current_output)
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, 'DISPLAY': DISPLAY}
            )
            logger.info(f"Recording started: {self.current_output}")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop(self) -> Optional[Path]:
        """Stop recording and return output path."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

            if self.current_output and self.current_output.exists():
                logger.info(f"Recording stopped: {self.current_output}")
                return self.current_output
        return None


class AudioPlayer:
    """Plays audio files."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def play(self, audio_path: Path) -> bool:
        """Start playing audio file."""
        if not audio_path.exists():
            logger.warning(f"Audio file not found: {audio_path}")
            return False

        # Use ffplay for audio playback
        cmd = [
            'ffplay', '-nodisp', '-autoexit',
            str(audio_path)
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Playing audio: {audio_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False

    def stop(self):
        """Stop audio playback."""
        if self.process:
            self.process.terminate()
            self.process = None


def merge_audio_video(video_path: Path, audio_path: Path, output_path: Path) -> bool:
    """
    Merge audio and video files using ffmpeg.

    Creates final video with synced audio narration.
    """
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False

    if not audio_path.exists():
        logger.warning(f"Audio file not found: {audio_path}, using video only")
        # Just copy video if no audio
        video_path.rename(output_path)
        return True

    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',  # End when shortest input ends
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0:
            logger.info(f"Merged video saved: {output_path}")
            # Clean up temporary video file
            video_path.unlink()
            return True
        else:
            logger.error(f"Merge failed: {result.stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"Failed to merge: {e}")
        return False


class DemoRecorder:
    """
    Orchestrates complete demo recording with Playwright automation.
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screen_recorder = ScreenRecorder(OUTPUT_DIR)
        self.audio_player = AudioPlayer()

    async def start_browser(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                '--start-maximized',
                '--ignore-certificate-errors',
                '--disable-web-security',
                '--window-size=1920,1080',
            ]
        )

        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
        )

        self.page = await self.context.new_page()
        logger.info("Browser started")

    async def stop_browser(self):
        """Stop Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser stopped")

    async def execute_action(self, action) -> bool:
        """Execute a single demo action."""
        try:
            if action.action == "navigate":
                url = action.target if action.target.startswith('http') else f"{BASE_URL}{action.target}"
                logger.info(f"Navigating: {url}")
                await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

            elif action.action == "click":
                logger.info(f"Clicking: {action.target}")
                await self.page.click(action.target, timeout=10000)

            elif action.action == "type":
                logger.info(f"Typing: {action.value[:20]}...")
                # Type slowly for demo effect
                await self.page.fill(action.target, "")
                for char in action.value:
                    await self.page.type(action.target, char, delay=50)

            elif action.action == "wait":
                if action.target:
                    logger.info(f"Waiting for: {action.target}")
                    await self.page.wait_for_selector(f'text={action.target}', timeout=30000)
                else:
                    wait_time = float(action.value or 1)
                    logger.info(f"Waiting: {wait_time}s")
                    await asyncio.sleep(wait_time)

            elif action.action == "hover":
                logger.info(f"Hovering: {action.target}")
                try:
                    await self.page.hover(action.target, timeout=5000)
                except:
                    logger.warning(f"Hover failed on {action.target}, continuing...")

            elif action.action == "snapshot" or action.action == "screenshot":
                pass  # Skip screenshots during recording

            # Wait after action
            if action.wait_after > 0:
                await asyncio.sleep(action.wait_after)

            return True

        except Exception as e:
            logger.error(f"Action failed: {action.action} - {e}")
            return False

    async def record_slide(self, slide: DemoSlide) -> Dict[str, Any]:
        """
        Record a complete slide with audio sync.

        Returns recording result dictionary.
        """
        slide_name = f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_').replace('-', '_')}"
        audio_path = AUDIO_DIR / f"slide_{slide.id:02d}_narration.mp3"
        final_output = OUTPUT_DIR / f"{slide_name}.mp4"

        result = {
            "slide_id": slide.id,
            "title": slide.title,
            "output_file": str(final_output),
            "status": "failed"
        }

        logger.info(f"\n{'='*60}")
        logger.info(f"Recording Slide {slide.id}: {slide.title}")
        logger.info(f"Duration: {slide.duration_seconds}s")
        logger.info(f"{'='*60}\n")

        try:
            # Start screen recording
            self.screen_recorder.start(slide_name)

            # Small delay for recording to initialize
            await asyncio.sleep(0.5)

            # Start audio playback (async)
            if audio_path.exists():
                self.audio_player.play(audio_path)

            # Execute slide actions
            for action in slide.actions:
                await self.execute_action(action)

            # Ensure minimum duration
            # (in case actions complete before narration)
            await asyncio.sleep(2)

            # Stop recording
            video_path = self.screen_recorder.stop()

            # Stop audio
            self.audio_player.stop()

            # Merge audio and video
            if video_path:
                if merge_audio_video(video_path, audio_path, final_output):
                    result["status"] = "success"
                    result["output_file"] = str(final_output)
                else:
                    # Fallback: just use video
                    if video_path.exists():
                        video_path.rename(final_output)
                        result["status"] = "success_no_audio"

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            result["error"] = str(e)
            self.screen_recorder.stop()
            self.audio_player.stop()

        return result

    async def record_all(self, slide_range: str = "all") -> List[Dict[str, Any]]:
        """Record multiple slides."""
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

        if not slides:
            logger.error(f"No slides found for: {slide_range}")
            return []

        results = []

        # Start browser once
        await self.start_browser()

        try:
            for slide in slides:
                result = await self.record_slide(slide)
                results.append(result)

                # Brief pause between slides
                await asyncio.sleep(2)

        finally:
            await self.stop_browser()

        return results


async def main():
    parser = argparse.ArgumentParser(description="Record demo screencasts")
    parser.add_argument("--slide", "-s", default="1", help="Slide(s) to record")
    parser.add_argument("--list", "-l", action="store_true", help="List slides")
    parser.add_argument("--check", action="store_true", help="Check prerequisites")

    args = parser.parse_args()

    if args.list:
        print("\nDemo Slides:")
        for slide in DEMO_SLIDES:
            audio = AUDIO_DIR / f"slide_{slide.id:02d}_narration.mp3"
            audio_status = "✅" if audio.exists() else "❌"
            print(f"  {slide.id:2d}. {slide.title} ({slide.duration_seconds}s) - Audio: {audio_status}")
        return

    if args.check:
        print("\nChecking prerequisites...")

        # Check ffmpeg
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True)
        print(f"  ffmpeg: {'✅' if result.returncode == 0 else '❌'}")

        # Check ffplay
        result = subprocess.run(['which', 'ffplay'], capture_output=True)
        print(f"  ffplay: {'✅' if result.returncode == 0 else '❌'}")

        # Check display
        print(f"  DISPLAY: {DISPLAY}")

        # Check audio files
        audio_count = len(list(AUDIO_DIR.glob("*.mp3")))
        print(f"  Audio files: {audio_count}/10")

        # Check Playwright
        try:
            import playwright
            print(f"  Playwright: ✅")
        except:
            print(f"  Playwright: ❌")

        return

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Record slides
    recorder = DemoRecorder()
    results = await recorder.record_all(args.slide)

    # Summary
    print("\n" + "="*60)
    print("RECORDING COMPLETE")
    print("="*60)

    success = sum(1 for r in results if r.get("status", "").startswith("success"))
    print(f"Successful: {success}/{len(results)}")

    for r in results:
        status = "✅" if r.get("status", "").startswith("success") else "❌"
        print(f"  {status} Slide {r['slide_id']}: {r.get('output_file', 'FAILED')}")

    # Save results
    results_path = OUTPUT_DIR / "recording_results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults: {results_path}")


if __name__ == "__main__":
    import argparse
    asyncio.run(main())
