#!/usr/bin/env python3
"""
MCP + OBS Demo Recording Coordinator

This script generates the exact sequence of MCP tool calls needed to record
demo screencasts. It outputs commands that can be executed via Claude Code's
Playwright MCP server while OBS records the screen.

WORKFLOW:
1. Start OBS recording via WebSocket or CLI
2. Execute Playwright MCP commands (browser_navigate, browser_click, etc.)
3. Stop OBS recording
4. Save video file

The MCP commands are designed to work with the mcp__playwright__* tools
available in Claude Code.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.demo_generation.demo_recorder import DEMO_SLIDES, DemoSlide, DemoAction

BASE_URL = os.getenv('DEMO_BASE_URL', 'https://localhost:3000')
OUTPUT_DIR = Path('frontend-legacy/static/demo/videos')


def generate_mcp_sequence(slide: DemoSlide) -> List[Dict[str, Any]]:
    """
    Generate MCP tool call sequence for a slide.

    Returns a list of dictionaries representing MCP tool calls
    that can be executed via Claude Code's Playwright MCP server.
    """
    commands = []

    for action in slide.actions:
        cmd = None

        if action.action == "navigate":
            url = action.target if action.target.startswith('http') else f"{BASE_URL}{action.target}"
            cmd = {
                "tool": "mcp__playwright__browser_navigate",
                "params": {"url": url},
                "description": action.description or f"Navigate to {url}"
            }

        elif action.action == "click":
            cmd = {
                "tool": "mcp__playwright__browser_click",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                },
                "description": action.description or f"Click {action.target}"
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
                "description": action.description or f"Type into {action.target}"
            }

        elif action.action == "wait":
            if action.target:
                cmd = {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"text": action.target},
                    "description": f"Wait for text: {action.target}"
                }
            else:
                cmd = {
                    "tool": "mcp__playwright__browser_wait_for",
                    "params": {"time": float(action.value or 1)},
                    "description": f"Wait {action.value} seconds"
                }

        elif action.action == "hover":
            cmd = {
                "tool": "mcp__playwright__browser_hover",
                "params": {
                    "element": action.description or action.target,
                    "ref": action.target
                },
                "description": action.description or f"Hover over {action.target}"
            }

        elif action.action == "snapshot":
            cmd = {
                "tool": "mcp__playwright__browser_snapshot",
                "params": {},
                "description": action.description or "Capture accessibility snapshot"
            }

        elif action.action == "screenshot":
            cmd = {
                "tool": "mcp__playwright__browser_take_screenshot",
                "params": {
                    "filename": action.value or f"slide_{slide.id:02d}_screenshot.png"
                },
                "description": action.description or "Take screenshot"
            }

        elif action.action == "fill_form":
            try:
                fields = json.loads(action.value)
                cmd = {
                    "tool": "mcp__playwright__browser_fill_form",
                    "params": {"fields": fields},
                    "description": action.description or "Fill form fields"
                }
            except:
                pass

        if cmd:
            cmd["wait_after_seconds"] = action.wait_after
            commands.append(cmd)

    return commands


def print_slide_recording_instructions(slide: DemoSlide):
    """Print step-by-step instructions for recording a slide."""
    output_file = OUTPUT_DIR / f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_')}.mp4"

    print(f"""
{'='*70}
RECORDING INSTRUCTIONS FOR SLIDE {slide.id}: {slide.title}
{'='*70}

DESCRIPTION: {slide.description}
DURATION: {slide.duration_seconds} seconds
OUTPUT FILE: {output_file}
NARRATION: {slide.narration_file or 'None'}

STEP 1: START OBS RECORDING
--------------------------
Start OBS Studio and begin recording. Ensure your scene captures
the browser window at 1920x1080 resolution.

OBS WebSocket command (if enabled):
  obs-websocket-py: ws.call(requests.StartRecord())

OBS CLI (alternative):
  DISPLAY=:99 obs --startrecording &

STEP 2: EXECUTE MCP COMMANDS
---------------------------
Execute these Playwright MCP tool calls in sequence:
""")

    commands = generate_mcp_sequence(slide)

    for i, cmd in enumerate(commands, 1):
        print(f"""
{i}. {cmd['description']}
   Tool: {cmd['tool']}
   Params: {json.dumps(cmd['params'], indent=6)}
   Wait after: {cmd.get('wait_after_seconds', 0.5)}s
""")

    print(f"""
STEP 3: STOP OBS RECORDING
-------------------------
Stop the OBS recording. The video will be saved automatically.

OBS WebSocket: ws.call(requests.StopRecord())
OBS CLI: pkill -SIGINT obs

STEP 4: RENAME OUTPUT FILE
-------------------------
Rename the OBS output file to: {output_file.name}

{'='*70}
""")


def generate_full_recording_script():
    """Generate complete recording script for all slides."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_commands = {}

    for slide in DEMO_SLIDES:
        all_commands[f"slide_{slide.id:02d}"] = {
            "title": slide.title,
            "description": slide.description,
            "duration_seconds": slide.duration_seconds,
            "narration_file": slide.narration_file,
            "output_file": str(OUTPUT_DIR / f"slide_{slide.id:02d}_{slide.title.lower().replace(' ', '_')}.mp4"),
            "mcp_commands": generate_mcp_sequence(slide)
        }

    # Save to JSON
    output_path = OUTPUT_DIR / "mcp_recording_commands.json"
    output_path.write_text(json.dumps(all_commands, indent=2))

    print(f"""
MCP Recording Commands Generated
================================
Total slides: {len(DEMO_SLIDES)}
Output file: {output_path}

To record a slide:
1. Start OBS with screen capture
2. Execute the MCP commands from the JSON file
3. Stop OBS recording
4. Rename output to match expected filename

Quick reference for MCP tools:
- mcp__playwright__browser_navigate: Go to URL
- mcp__playwright__browser_click: Click element
- mcp__playwright__browser_type: Type text
- mcp__playwright__browser_hover: Hover element
- mcp__playwright__browser_wait_for: Wait for text/time
- mcp__playwright__browser_snapshot: Accessibility snapshot
- mcp__playwright__browser_take_screenshot: Screenshot
""")

    return all_commands


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate MCP + OBS recording commands")
    parser.add_argument("--slide", "-s", type=int, help="Show instructions for specific slide")
    parser.add_argument("--all", "-a", action="store_true", help="Generate all commands to JSON")
    parser.add_argument("--list", "-l", action="store_true", help="List all slides")

    args = parser.parse_args()

    if args.list:
        print("\nDemo Slides:")
        for slide in DEMO_SLIDES:
            print(f"  {slide.id:2d}. {slide.title} ({slide.duration_seconds}s)")
        return

    if args.slide:
        for slide in DEMO_SLIDES:
            if slide.id == args.slide:
                print_slide_recording_instructions(slide)
                return
        print(f"Slide {args.slide} not found")
        return

    if args.all:
        generate_full_recording_script()
        return

    # Default: show usage
    parser.print_help()
    print("\n\nExample usage:")
    print("  python mcp_obs_coordinator.py --list          # List all slides")
    print("  python mcp_obs_coordinator.py --slide 1       # Instructions for slide 1")
    print("  python mcp_obs_coordinator.py --all           # Generate all commands to JSON")


if __name__ == "__main__":
    main()
