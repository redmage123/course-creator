#!/usr/bin/env python3
"""
Run Demo Recording - Orchestrates Playwright MCP + OBS for screencast generation

USAGE:
    # Record all slides
    python scripts/demo_generation/run_demo_recording.py --all

    # Record specific slide
    python scripts/demo_generation/run_demo_recording.py --slide 1

    # Record range of slides
    python scripts/demo_generation/run_demo_recording.py --slide 1-5

REQUIREMENTS:
    - OBS Studio with WebSocket server enabled (port 4455)
    - Playwright MCP server running
    - Platform running at https://localhost:3000

WORKFLOW:
    1. Starts OBS recording
    2. Executes Playwright MCP commands for browser automation
    3. Stops OBS recording after slide duration
    4. Saves video to output directory
"""

import os
import sys
import json
import time
import subprocess
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.demo_generation.demo_recorder import (
    DemoRecorder,
    DemoSlide,
    DEMO_SLIDES,
    OBSController
)

# OBS WebSocket
try:
    from obswebsocket import obsws, requests as obs_requests
    HAS_OBS_WEBSOCKET = True
except ImportError:
    HAS_OBS_WEBSOCKET = False

# Configuration
OBS_HOST = os.getenv('OBS_HOST', 'localhost')
OBS_PORT = int(os.getenv('OBS_PORT', '4455'))
OBS_PASSWORD = os.getenv('OBS_PASSWORD', '')
BASE_URL = os.getenv('DEMO_BASE_URL', 'https://localhost:3000')
OUTPUT_DIR = Path('frontend-legacy/static/demo/videos')
DISPLAY = os.getenv('DISPLAY', ':99')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OBSRecordingSession:
    """
    Manages OBS recording sessions for demo videos.

    Handles:
    - Starting/stopping recording
    - Setting output file names
    - Scene management
    """

    def __init__(self):
        self.ws = None
        self.connected = False
        self.recording = False
        self.output_dir = OUTPUT_DIR

    def connect(self) -> bool:
        """Connect to OBS WebSocket server."""
        if not HAS_OBS_WEBSOCKET:
            logger.warning("obs-websocket-py not installed. Install with: pip install obs-websocket-py")
            return False

        try:
            self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            self.ws.connect()
            self.connected = True
            logger.info(f"Connected to OBS WebSocket at {OBS_HOST}:{OBS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            logger.info("Make sure OBS is running with WebSocket server enabled")
            return False

    def disconnect(self):
        """Disconnect from OBS."""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
            except:
                pass
            self.connected = False

    def set_output_filename(self, filename: str):
        """Set the output filename for recording."""
        if not self.connected:
            return False
        try:
            # Set recording directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # OBS uses its own naming, we'll rename after
            self.current_target_file = filename
            return True
        except Exception as e:
            logger.error(f"Failed to set output filename: {e}")
            return False

    def start_recording(self) -> bool:
        """Start OBS recording."""
        if not self.connected:
            return self._start_recording_cli()

        try:
            self.ws.call(obs_requests.StartRecord())
            self.recording = True
            logger.info("OBS recording started")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> Optional[str]:
        """Stop OBS recording and return output path."""
        if not self.connected:
            return self._stop_recording_cli()

        try:
            response = self.ws.call(obs_requests.StopRecord())
            self.recording = False
            output_path = getattr(response, 'outputPath', None)
            logger.info(f"OBS recording stopped: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return None

    def _start_recording_cli(self) -> bool:
        """Fallback: Start OBS recording via CLI."""
        try:
            # Check if OBS is running
            result = subprocess.run(['pgrep', '-x', 'obs'], capture_output=True)
            if result.returncode != 0:
                # Start OBS with recording
                logger.info("Starting OBS with recording...")
                subprocess.Popen(
                    ['obs', '--startrecording', '--minimize-to-tray'],
                    env={**os.environ, 'DISPLAY': DISPLAY},
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(3)  # Wait for OBS to start
            self.recording = True
            return True
        except Exception as e:
            logger.error(f"CLI recording start failed: {e}")
            return False

    def _stop_recording_cli(self) -> Optional[str]:
        """Fallback: Stop OBS recording via CLI."""
        try:
            # Send stop recording hotkey via xdotool
            subprocess.run(
                ['xdotool', 'key', 'ctrl+alt+r'],
                env={**os.environ, 'DISPLAY': DISPLAY}
            )
            self.recording = False
            return None
        except Exception as e:
            logger.error(f"CLI recording stop failed: {e}")
            return None


def generate_playwright_script(slide: DemoSlide, output_file: Path) -> str:
    """
    Generate a Playwright script for a demo slide.

    This creates a standalone Playwright script that can be executed
    to perform the browser automation for a specific slide.
    """
    script_lines = [
        "// Auto-generated Playwright script for demo recording",
        f"// Slide {slide.id}: {slide.title}",
        f"// Generated: {datetime.now().isoformat()}",
        "",
        "const {{ chromium }} = require('playwright');",
        "",
        "(async () => {{",
        "  const browser = await chromium.launch({{ headless: false }});",
        "  const context = await browser.newContext({{",
        "    ignoreHTTPSErrors: true,",
        "    viewport: {{ width: 1920, height: 1080 }}",
        "  }});",
        "  const page = await context.newPage();",
        "",
    ]

    for action in slide.actions:
        if action.action == "navigate":
            url = action.target if action.target.startswith('http') else f"{BASE_URL}{action.target}"
            script_lines.append(f"  // {action.description}")
            script_lines.append(f"  await page.goto('{url}');")

        elif action.action == "click":
            script_lines.append(f"  // {action.description}")
            script_lines.append(f"  await page.click('{action.target}');")

        elif action.action == "type":
            script_lines.append(f"  // {action.description}")
            script_lines.append(f"  await page.fill('{action.target}', '{action.value}');")

        elif action.action == "wait":
            if action.target:
                script_lines.append(f"  // Wait for: {action.target}")
                script_lines.append(f"  await page.waitForSelector(':text(\"{action.target}\")');")
            else:
                script_lines.append(f"  // Wait {action.value} seconds")
                script_lines.append(f"  await page.waitForTimeout({float(action.value or 1) * 1000});")

        elif action.action == "hover":
            script_lines.append(f"  // {action.description}")
            script_lines.append(f"  await page.hover('{action.target}');")

        elif action.action == "snapshot":
            script_lines.append(f"  // {action.description}")
            script_lines.append(f"  await page.screenshot({{ path: 'snapshot_{slide.id}.png' }});")

        # Add wait after action
        if action.wait_after > 0:
            script_lines.append(f"  await page.waitForTimeout({int(action.wait_after * 1000)});")
        script_lines.append("")

    script_lines.extend([
        "  await browser.close();",
        "}})();",
    ])

    return "\n".join(script_lines)


def create_mcp_command_sequence(slide: DemoSlide) -> List[Dict[str, Any]]:
    """
    Create sequence of MCP commands for Playwright MCP server.

    Returns a list of commands that can be executed via the MCP server.
    """
    commands = []

    for action in slide.actions:
        cmd = None

        if action.action == "navigate":
            url = action.target if action.target.startswith('http') else f"{BASE_URL}{action.target}"
            cmd = {
                "tool": "mcp__playwright__browser_navigate",
                "params": {"url": url},
                "description": action.description
            }

        elif action.action == "click":
            cmd = {
                "tool": "mcp__playwright__browser_click",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                },
                "description": action.description
            }

        elif action.action == "type":
            cmd = {
                "tool": "mcp__playwright__browser_type",
                "params": {
                    "element": action.description or "input field",
                    "ref": action.target,
                    "text": action.value,
                    "slowly": True
                },
                "description": action.description
            }

        elif action.action == "wait":
            if action.target:
                cmd = {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"text": action.target},
                    "description": f"Wait for: {action.target}"
                }
            else:
                cmd = {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"time": float(action.value or 1)},
                    "description": f"Wait {action.value}s"
                }

        elif action.action == "hover":
            cmd = {
                "tool": "mcp__playwright__browser_hover",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                },
                "description": action.description
            }

        elif action.action == "snapshot":
            cmd = {
                "tool": "mcp__playwright__browser_snapshot",
                "params": {},
                "description": action.description
            }

        elif action.action == "screenshot":
            cmd = {
                "tool": "mcp__playwright__browser_take_screenshot",
                "params": {
                    "filename": action.value or f"slide_{slide.id}_screenshot.png"
                },
                "description": action.description
            }

        if cmd:
            cmd["wait_after"] = action.wait_after
            commands.append(cmd)

    return commands


async def record_slide_with_mcp(slide: DemoSlide, obs: OBSRecordingSession) -> Dict[str, Any]:
    """
    Record a slide using Playwright MCP commands and OBS.

    This function generates the MCP command sequence and coordinates
    with OBS for recording.
    """
    output_file = OUTPUT_DIR / f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_').replace('-', '_')}.mp4"

    logger.info(f"\n{'='*60}")
    logger.info(f"Recording Slide {slide.id}: {slide.title}")
    logger.info(f"Duration: {slide.duration_seconds}s")
    logger.info(f"Output: {output_file}")
    logger.info(f"{'='*60}\n")

    # Generate MCP commands
    mcp_commands = create_mcp_command_sequence(slide)

    result = {
        "slide_id": slide.id,
        "title": slide.title,
        "output_file": str(output_file),
        "mcp_commands": mcp_commands,
        "duration_seconds": slide.duration_seconds,
        "narration_file": slide.narration_file,
        "status": "ready",
        "recorded_at": datetime.now().isoformat()
    }

    # Print MCP commands for manual execution or automation
    print(f"\n--- MCP Commands for Slide {slide.id} ---")
    for i, cmd in enumerate(mcp_commands, 1):
        print(f"\n{i}. {cmd.get('description', cmd['tool'])}")
        print(f"   Tool: {cmd['tool']}")
        print(f"   Params: {json.dumps(cmd['params'], indent=2)}")
        if cmd.get('wait_after', 0) > 0:
            print(f"   Wait after: {cmd['wait_after']}s")
    print(f"\n--- End of Slide {slide.id} ---\n")

    return result


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Record demo screencasts with Playwright MCP + OBS")
    parser.add_argument("--slide", "-s", default="all", help="Slide(s) to record: 'all', '1', '1-5', '1,3,5'")
    parser.add_argument("--list", "-l", action="store_true", help="List all slides")
    parser.add_argument("--output", "-o", type=Path, default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--json", action="store_true", help="Output commands as JSON file")
    parser.add_argument("--script", action="store_true", help="Generate Playwright scripts")

    args = parser.parse_args()

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    if args.list:
        print("\n" + "="*60)
        print("DEMO SLIDES")
        print("="*60)
        for slide in DEMO_SLIDES:
            print(f"\n  Slide {slide.id}: {slide.title}")
            print(f"  {'-'*50}")
            print(f"  Description: {slide.description}")
            print(f"  Duration: {slide.duration_seconds}s")
            print(f"  Actions: {len(slide.actions)}")
            if slide.narration_file:
                print(f"  Narration: {slide.narration_file}")
        print("\n" + "="*60 + "\n")
        return

    # Get slides to record
    recorder = DemoRecorder()
    slides = recorder.get_slides(args.slide)

    if not slides:
        print(f"No slides found for: {args.slide}")
        return

    # Initialize OBS
    obs = OBSRecordingSession()
    obs.output_dir = args.output

    # Connect to OBS (optional - will use CLI fallback if not available)
    obs.connect()

    all_results = []

    try:
        for slide in slides:
            result = await record_slide_with_mcp(slide, obs)
            all_results.append(result)

            if args.script:
                # Generate Playwright script
                script_path = args.output / f"slide_{slide.id:02d}_playwright.js"
                script = generate_playwright_script(slide, script_path)
                script_path.write_text(script)
                logger.info(f"Playwright script saved: {script_path}")

    finally:
        obs.disconnect()

    # Save results
    if args.json:
        json_path = args.output / "demo_recording_commands.json"
        json_path.write_text(json.dumps(all_results, indent=2))
        print(f"\nMCP commands saved to: {json_path}")

    # Summary
    print("\n" + "="*60)
    print("RECORDING PREPARATION COMPLETE")
    print("="*60)
    print(f"Slides prepared: {len(all_results)}")
    print(f"Output directory: {args.output}")
    print("\nTo record with OBS + Playwright MCP:")
    print("1. Start OBS with screen capture")
    print("2. Use the MCP commands above with Playwright MCP server")
    print("3. OBS will record the browser automation")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
