"""
Demo Screencast Recorder - Playwright MCP + OBS Integration

BUSINESS REQUIREMENT:
Generate professional demo screencasts by combining Playwright browser automation
with OBS Studio screen recording. Each slide demonstrates a specific platform feature.

TECHNICAL IMPLEMENTATION:
- Uses Playwright MCP server for browser automation (navigation, clicks, typing)
- Uses OBS WebSocket API for recording control (start/stop/pause)
- Generates MP4 videos for each demo slide
- Supports audio narration sync with ElevenLabs

USAGE:
    python scripts/demo_generation/demo_recorder.py --slide 1
    python scripts/demo_generation/demo_recorder.py --all
    python scripts/demo_generation/demo_recorder.py --slide 1-5
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# OBS WebSocket control
try:
    from obswebsocket import obsws, requests as obs_requests
    HAS_OBS_WEBSOCKET = True
except ImportError:
    HAS_OBS_WEBSOCKET = False
    print("Warning: obs-websocket-py not available, using CLI fallback")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv('DEMO_BASE_URL', 'https://localhost:3000')
OBS_HOST = os.getenv('OBS_HOST', 'localhost')
OBS_PORT = int(os.getenv('OBS_PORT', '4455'))
OBS_PASSWORD = os.getenv('OBS_PASSWORD', '')
OUTPUT_DIR = Path(os.getenv('DEMO_OUTPUT_DIR', 'frontend-legacy/static/demo/videos'))


@dataclass
class DemoAction:
    """
    Represents a single action in a demo workflow.

    SUPPORTED ACTIONS:
    - navigate: Go to URL
    - click: Click element by selector
    - type: Type text into element
    - wait: Wait for time or element
    - screenshot: Take screenshot
    - scroll: Scroll page
    - hover: Hover over element
    """
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    wait_after: float = 0.5
    description: str = ""


@dataclass
class DemoSlide:
    """
    Represents a demo slide with its workflow.

    Each slide corresponds to one video file demonstrating
    a specific platform feature or user journey.
    """
    id: int
    title: str
    description: str
    duration_seconds: int
    actions: List[DemoAction] = field(default_factory=list)
    narration_file: Optional[str] = None


class OBSController:
    """
    Controls OBS Studio for screen recording.

    FEATURES:
    - Start/stop recording via WebSocket
    - Scene switching
    - Fallback to CLI if WebSocket unavailable
    """

    def __init__(self):
        self.ws = None
        self.connected = False

    async def connect(self) -> bool:
        """Connect to OBS WebSocket server."""
        if not HAS_OBS_WEBSOCKET:
            logger.warning("OBS WebSocket not available, using CLI mode")
            return False

        try:
            self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            self.ws.connect()
            self.connected = True
            logger.info(f"Connected to OBS WebSocket at {OBS_HOST}:{OBS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS WebSocket: {e}")
            return False

    async def disconnect(self):
        """Disconnect from OBS WebSocket."""
        if self.ws and self.connected:
            self.ws.disconnect()
            self.connected = False
            logger.info("Disconnected from OBS WebSocket")

    async def start_recording(self, output_path: Optional[str] = None) -> bool:
        """Start OBS recording."""
        try:
            if self.connected and self.ws:
                # Set output path if specified
                if output_path:
                    self.ws.call(obs_requests.SetRecordDirectory(
                        recordDirectory=str(Path(output_path).parent)
                    ))
                self.ws.call(obs_requests.StartRecord())
                logger.info("OBS recording started via WebSocket")
            else:
                # CLI fallback
                os.system('obs --startrecording &')
                logger.info("OBS recording started via CLI")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    async def stop_recording(self) -> Optional[str]:
        """Stop OBS recording and return output file path."""
        try:
            if self.connected and self.ws:
                response = self.ws.call(obs_requests.StopRecord())
                output_path = getattr(response, 'outputPath', None)
                logger.info(f"OBS recording stopped, output: {output_path}")
                return output_path
            else:
                # CLI - send stop signal
                os.system('pkill -SIGINT obs')
                logger.info("OBS recording stopped via CLI")
                return None
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return None

    async def set_scene(self, scene_name: str) -> bool:
        """Switch OBS scene."""
        if not self.connected or not self.ws:
            return False
        try:
            self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
            logger.info(f"Switched to scene: {scene_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch scene: {e}")
            return False


class PlaywrightDemoRunner:
    """
    Runs demo workflows using Playwright MCP server.

    DESIGN:
    This class generates Playwright MCP commands that can be executed
    via the MCP server. It does NOT directly control Playwright but
    creates the command sequence for the MCP tools.

    The actual execution happens via the MCP server integration.
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.current_page_url = None

    def generate_mcp_commands(self, slide: DemoSlide) -> List[Dict[str, Any]]:
        """
        Generate MCP command sequence for a demo slide.

        Returns list of MCP tool calls to execute.
        """
        commands = []

        for action in slide.actions:
            cmd = self._action_to_mcp_command(action)
            if cmd:
                commands.append(cmd)

        return commands

    def _action_to_mcp_command(self, action: DemoAction) -> Optional[Dict[str, Any]]:
        """Convert DemoAction to MCP tool call."""

        if action.action == "navigate":
            url = action.target if action.target.startswith('http') else f"{self.base_url}{action.target}"
            return {
                "tool": "mcp__playwright__browser_navigate",
                "params": {"url": url}
            }

        elif action.action == "click":
            return {
                "tool": "mcp__playwright__browser_click",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                }
            }

        elif action.action == "type":
            return {
                "tool": "mcp__playwright__browser_type",
                "params": {
                    "element": action.description or "input field",
                    "ref": action.target,
                    "text": action.value,
                    "slowly": True  # Type slowly for demo effect
                }
            }

        elif action.action == "wait":
            if action.target:
                return {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"text": action.target}
                }
            else:
                return {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"time": float(action.value or 1)}
                }

        elif action.action == "screenshot":
            return {
                "tool": "mcp__playwright__browser_take_screenshot",
                "params": {
                    "filename": action.value or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                }
            }

        elif action.action == "hover":
            return {
                "tool": "mcp__playwright__browser_hover",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                }
            }

        elif action.action == "snapshot":
            return {
                "tool": "mcp__playwright__browser_snapshot",
                "params": {}
            }

        elif action.action == "fill_form":
            # Parse fields from value (JSON)
            try:
                fields = json.loads(action.value)
                return {
                    "tool": "mcp__playwright__browser_fill_form",
                    "params": {"fields": fields}
                }
            except:
                return None

        return None


# Demo Slide Definitions
DEMO_SLIDES: List[DemoSlide] = [
    DemoSlide(
        id=1,
        title="Platform Introduction",
        description="Welcome to Course Creator Platform - Landing page showcase",
        duration_seconds=15,
        narration_file="slide_01_narration.mp3",
        actions=[
            DemoAction("navigate", "/", description="Navigate to homepage"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture homepage layout"),
            DemoAction("hover", "a[href='/demo']", description="Hover Watch Demo button"),
            DemoAction("wait", value="1"),
            DemoAction("hover", "a[href='/login']", description="Hover Sign In button"),
            DemoAction("wait", value="1"),
            DemoAction("hover", "a[href='/register']", description="Hover Create Account button"),
            DemoAction("wait", value="2"),
        ]
    ),
    DemoSlide(
        id=2,
        title="Organization Registration",
        description="Register a new organization on the platform",
        duration_seconds=25,
        narration_file="slide_02_narration.mp3",
        actions=[
            DemoAction("navigate", "/organization/register", description="Go to org registration"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture registration form"),
            DemoAction("type", "#orgName", "Acme Training Corp", description="Enter organization name"),
            DemoAction("wait", value="0.5"),
            DemoAction("type", "#adminEmail", "admin@acmetraining.com", description="Enter admin email"),
            DemoAction("wait", value="0.5"),
            DemoAction("type", "#adminName", "John Smith", description="Enter admin name"),
            DemoAction("wait", value="0.5"),
            DemoAction("type", "#password", "SecurePass123!", description="Enter password"),
            DemoAction("wait", value="1"),
            DemoAction("hover", "button[type='submit']", description="Hover submit button"),
            DemoAction("wait", value="2"),
        ]
    ),
    DemoSlide(
        id=3,
        title="Organization Admin Dashboard",
        description="Explore the Organization Admin dashboard",
        duration_seconds=30,
        narration_file="slide_03_narration.mp3",
        actions=[
            DemoAction("navigate", "/login", description="Go to login"),
            DemoAction("wait", value="1"),
            DemoAction("type", "#email", "org_admin@demo.com", description="Enter org admin email"),
            DemoAction("type", "#password", "demo123", description="Enter password"),
            DemoAction("click", "button[type='submit']", description="Click login"),
            DemoAction("wait", "Dashboard", description="Wait for dashboard"),
            DemoAction("snapshot", description="Capture dashboard"),
            DemoAction("wait", value="2"),
            DemoAction("click", "[data-tab='members']", description="Click Members tab"),
            DemoAction("wait", value="2"),
            DemoAction("click", "[data-tab='projects']", description="Click Projects tab"),
            DemoAction("wait", value="2"),
        ]
    ),
    DemoSlide(
        id=4,
        title="Creating Training Tracks",
        description="Create and organize training tracks",
        duration_seconds=25,
        narration_file="slide_04_narration.mp3",
        actions=[
            DemoAction("click", "[data-tab='tracks']", description="Click Tracks tab"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture tracks view"),
            DemoAction("click", "button.create-track", description="Click Create Track"),
            DemoAction("wait", value="1"),
            DemoAction("type", "#trackName", "Python Fundamentals", description="Enter track name"),
            DemoAction("type", "#trackDescription", "Learn Python from basics to advanced", description="Enter description"),
            DemoAction("wait", value="2"),
        ]
    ),
    DemoSlide(
        id=5,
        title="Instructor Dashboard",
        description="Instructor view for course management",
        duration_seconds=30,
        narration_file="slide_05_narration.mp3",
        actions=[
            DemoAction("navigate", "/login", description="Go to login"),
            DemoAction("wait", value="1"),
            DemoAction("type", "#email", "instructor@demo.com", description="Enter instructor email"),
            DemoAction("type", "#password", "demo123", description="Enter password"),
            DemoAction("click", "button[type='submit']", description="Click login"),
            DemoAction("wait", "Instructor Dashboard", description="Wait for dashboard"),
            DemoAction("snapshot", description="Capture instructor dashboard"),
            DemoAction("wait", value="2"),
            DemoAction("click", "[data-tab='courses']", description="Click Courses tab"),
            DemoAction("wait", value="2"),
        ]
    ),
    DemoSlide(
        id=6,
        title="AI Course Generation",
        description="Generate course content with AI assistance",
        duration_seconds=35,
        narration_file="slide_06_narration.mp3",
        actions=[
            DemoAction("click", "[data-tab='content-generation']", description="Click Content Generation tab"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture AI generation interface"),
            DemoAction("type", "#courseTitle", "Introduction to Machine Learning", description="Enter course title"),
            DemoAction("type", "#courseDescription", "A comprehensive introduction to ML concepts", description="Enter description"),
            DemoAction("wait", value="1"),
            DemoAction("click", "button.generate-outline", description="Click Generate Outline"),
            DemoAction("wait", value="5"),
            DemoAction("snapshot", description="Capture generated outline"),
        ]
    ),
    DemoSlide(
        id=7,
        title="Interactive Lab Environment",
        description="Hands-on coding labs with AI assistance",
        duration_seconds=40,
        narration_file="slide_07_narration.mp3",
        actions=[
            DemoAction("navigate", "/lab/python-basics", description="Open Python lab"),
            DemoAction("wait", value="3"),
            DemoAction("snapshot", description="Capture lab environment"),
            DemoAction("click", ".monaco-editor", description="Click code editor"),
            DemoAction("type", ".monaco-editor", "print('Hello, World!')", description="Type code"),
            DemoAction("wait", value="1"),
            DemoAction("click", "button.run-code", description="Click Run"),
            DemoAction("wait", value="3"),
            DemoAction("snapshot", description="Capture code output"),
        ]
    ),
    DemoSlide(
        id=8,
        title="Student Progress Analytics",
        description="Track student progress and performance",
        duration_seconds=30,
        narration_file="slide_08_narration.mp3",
        actions=[
            DemoAction("navigate", "/instructor/analytics", description="Go to analytics"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture analytics dashboard"),
            DemoAction("hover", ".chart-container", description="Hover over chart"),
            DemoAction("wait", value="2"),
            DemoAction("click", "[data-view='students']", description="Click Students view"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture student list"),
        ]
    ),
    DemoSlide(
        id=9,
        title="Quiz and Assessment",
        description="Create and manage quizzes",
        duration_seconds=30,
        narration_file="slide_09_narration.mp3",
        actions=[
            DemoAction("navigate", "/instructor/quizzes", description="Go to quizzes"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture quiz management"),
            DemoAction("click", "button.create-quiz", description="Click Create Quiz"),
            DemoAction("wait", value="1"),
            DemoAction("type", "#quizTitle", "Python Basics Quiz", description="Enter quiz title"),
            DemoAction("click", "button.ai-generate-questions", description="Generate questions with AI"),
            DemoAction("wait", value="4"),
            DemoAction("snapshot", description="Capture generated questions"),
        ]
    ),
    DemoSlide(
        id=10,
        title="Student Learning Experience",
        description="The student view of course content",
        duration_seconds=35,
        narration_file="slide_10_narration.mp3",
        actions=[
            DemoAction("navigate", "/login", description="Go to login"),
            DemoAction("wait", value="1"),
            DemoAction("type", "#email", "student@demo.com", description="Enter student email"),
            DemoAction("type", "#password", "demo123", description="Enter password"),
            DemoAction("click", "button[type='submit']", description="Click login"),
            DemoAction("wait", "Student Dashboard", description="Wait for dashboard"),
            DemoAction("snapshot", description="Capture student dashboard"),
            DemoAction("click", ".course-card", description="Click a course"),
            DemoAction("wait", value="2"),
            DemoAction("snapshot", description="Capture course content"),
        ]
    ),
]


class DemoRecorder:
    """
    Main orchestrator for demo recording.

    Coordinates Playwright MCP commands with OBS recording
    to produce demo screencast videos.
    """

    def __init__(self):
        self.obs = OBSController()
        self.playwright = PlaywrightDemoRunner()
        self.output_dir = OUTPUT_DIR

    async def setup(self):
        """Initialize recording environment."""
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Connect to OBS
        await self.obs.connect()

        logger.info(f"Demo recorder initialized. Output: {self.output_dir}")

    async def teardown(self):
        """Cleanup after recording."""
        await self.obs.disconnect()

    async def record_slide(self, slide: DemoSlide) -> Dict[str, Any]:
        """
        Record a single demo slide.

        Returns dict with recording results and MCP commands to execute.
        """
        output_file = self.output_dir / f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_')}.mp4"

        logger.info(f"Recording slide {slide.id}: {slide.title}")

        # Generate MCP commands
        mcp_commands = self.playwright.generate_mcp_commands(slide)

        result = {
            "slide_id": slide.id,
            "title": slide.title,
            "output_file": str(output_file),
            "mcp_commands": mcp_commands,
            "duration_seconds": slide.duration_seconds,
            "narration_file": slide.narration_file,
            "status": "ready"
        }

        return result

    async def generate_recording_script(self, slides: List[DemoSlide]) -> str:
        """
        Generate a complete recording script with all MCP commands.

        This script can be executed to perform the full demo recording.
        """
        script_lines = [
            "# Demo Recording Script",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Slides: {len(slides)}",
            "",
            "## Instructions:",
            "1. Start OBS with screen capture source",
            "2. Execute each slide's MCP commands via Playwright MCP server",
            "3. OBS will record each segment",
            "",
        ]

        for slide in slides:
            result = await self.record_slide(slide)

            script_lines.append(f"## Slide {slide.id}: {slide.title}")
            script_lines.append(f"Duration: {slide.duration_seconds}s")
            script_lines.append(f"Output: {result['output_file']}")
            script_lines.append(f"Narration: {slide.narration_file}")
            script_lines.append("")
            script_lines.append("### MCP Commands:")
            script_lines.append("```json")
            script_lines.append(json.dumps(result['mcp_commands'], indent=2))
            script_lines.append("```")
            script_lines.append("")

        return "\n".join(script_lines)

    def get_slide(self, slide_id: int) -> Optional[DemoSlide]:
        """Get slide by ID."""
        for slide in DEMO_SLIDES:
            if slide.id == slide_id:
                return slide
        return None

    def get_slides(self, slide_range: str = "all") -> List[DemoSlide]:
        """
        Get slides by range specification.

        Examples:
            "all" - all slides
            "1" - slide 1 only
            "1-5" - slides 1 through 5
            "1,3,5" - slides 1, 3, and 5
        """
        if slide_range == "all":
            return DEMO_SLIDES

        if "-" in slide_range:
            start, end = map(int, slide_range.split("-"))
            return [s for s in DEMO_SLIDES if start <= s.id <= end]

        if "," in slide_range:
            ids = [int(x) for x in slide_range.split(",")]
            return [s for s in DEMO_SLIDES if s.id in ids]

        # Single slide
        slide_id = int(slide_range)
        slide = self.get_slide(slide_id)
        return [slide] if slide else []


async def main():
    """Main entry point for demo recording."""
    parser = argparse.ArgumentParser(description="Generate demo screencasts with Playwright + OBS")
    parser.add_argument("--slide", "-s", default="all", help="Slide(s) to record: 'all', '1', '1-5', '1,3,5'")
    parser.add_argument("--list", "-l", action="store_true", help="List all available slides")
    parser.add_argument("--script", action="store_true", help="Generate recording script only (no recording)")
    parser.add_argument("--output", "-o", help="Output directory for videos")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Demo Slides:")
        print("-" * 60)
        for slide in DEMO_SLIDES:
            print(f"  {slide.id:2d}. {slide.title}")
            print(f"      {slide.description}")
            print(f"      Duration: {slide.duration_seconds}s")
            print()
        return

    recorder = DemoRecorder()

    if args.output:
        recorder.output_dir = Path(args.output)

    await recorder.setup()

    try:
        slides = recorder.get_slides(args.slide)

        if not slides:
            print(f"No slides found for: {args.slide}")
            return

        if args.script:
            # Generate script only
            script = await recorder.generate_recording_script(slides)
            script_path = recorder.output_dir / "recording_script.md"
            script_path.write_text(script)
            print(f"Recording script saved to: {script_path}")

            # Also output JSON for programmatic use
            json_results = []
            for slide in slides:
                result = await recorder.record_slide(slide)
                json_results.append(result)

            json_path = recorder.output_dir / "recording_commands.json"
            json_path.write_text(json.dumps(json_results, indent=2))
            print(f"MCP commands saved to: {json_path}")
        else:
            print(f"\nRecording {len(slides)} slide(s)...")
            print("Use the MCP commands from the generated script with Playwright MCP server")

            script = await recorder.generate_recording_script(slides)
            print("\n" + script)

    finally:
        await recorder.teardown()


if __name__ == "__main__":
    asyncio.run(main())
