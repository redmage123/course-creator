#!/usr/bin/env python3
"""
Generate Demo Slides 2-10 with Playwright + FFmpeg
(Slide 1 already completed)
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, '/home/bbrelin/course-creator')

from scripts.generate_demo_with_obs import (
    slide_02_getting_started,
    slide_03_create_organization,
    slide_04_projects_tracks,
    slide_05_assign_instructors,
    slide_06_create_course_ai,
    slide_07_enroll_employees,
    slide_08_student_experience,
    slide_09_ai_assistant,
    slide_10_summary,
    BASE_URL,
    RESOLUTION,
    VIDEOS_DIR
)
from playwright.async_api import async_playwright

class FFmpegRecorder:
    """Simple FFmpeg-based recorder"""

    def __init__(self):
        self.process = None

    def start_recording(self, output_file):
        """Start FFmpeg recording"""
        cmd = [
            'ffmpeg', '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', '30',
            '-i', ':99',
            '-vcodec', 'libx264',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            '-y', str(output_file)
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  🎥 Recording started: {os.path.basename(output_file)}")
        return True

    def stop_recording(self):
        """Stop FFmpeg recording"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print(f"  ⏹️  Recording stopped")
            return True
        return False

async def main():
    print("="*70)
    print("🎬 GENERATING DEMO SLIDES 2-10")
    print("  Using Playwright + FFmpeg")
    print("  H.264 encoding, 1920x1080, 30fps")
    print("="*70)
    print()

    # Load slide definitions
    import json
    with open('/home/bbrelin/course-creator/scripts/demo_narration_scripts.json', 'r') as f:
        data = json.load(f)

    slides = [
        (2, "Getting Started", slide_02_getting_started, data['slides'][1]['duration']),
        (3, "Create Organization", slide_03_create_organization, data['slides'][2]['duration']),
        (4, "Projects & Tracks", slide_04_projects_tracks, data['slides'][3]['duration']),
        (5, "Assign Instructors", slide_05_assign_instructors, data['slides'][4]['duration']),
        (6, "Create Course with AI", slide_06_create_course_ai, data['slides'][5]['duration']),
        (7, "Enroll Employees", slide_07_enroll_employees, data['slides'][6]['duration']),
        (8, "Student Experience", slide_08_student_experience, data['slides'][7]['duration']),
        (9, "AI Assistant", slide_09_ai_assistant, data['slides'][8]['duration']),
        (10, "Summary", slide_10_summary, data['slides'][9]['duration']),
    ]

    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                '--window-position=0,0',
                f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}'
            ]
        )

        context = await browser.new_context(
            viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
            ignore_https_errors=True
        )

        page = await context.new_page()

        for slide_num, slide_title, slide_func, duration in slides:
            print(f"\n🎥 Slide {slide_num}/10: {slide_title}")
            print(f"   Duration: {duration}s")

            output_file = VIDEOS_DIR / f"slide_{str(slide_num).zfill(2)}_{slide_title.lower().replace(' ', '_').replace('&', 'and')}.mp4"

            # For FFmpeg, we need to modify the slide functions to not use recorder parameter
            # Let's create a simple wrapper
            class DummyRecorder:
                def start_recording(self, filename):
                    pass
                def stop_recording(self):
                    pass

            dummy = DummyRecorder()

            # Start FFmpeg recording
            recorder.start_recording(output_file)

            # Wait a moment for recording to start
            await asyncio.sleep(1)

            try:
                # Execute slide workflow
                await slide_func(page, dummy, duration)
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

            # Stop recording
            recorder.stop_recording()

            # Verify file was created
            await asyncio.sleep(2)
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"  ✅ Created: {output_file.name} ({size_mb:.2f} MB)")
            else:
                print(f"  ❌ Failed: {output_file.name}")

            # Small pause between slides
            if slide_num < 10:
                await asyncio.sleep(2)

        await context.close()
        await browser.close()

    print("\n" + "="*70)
    print("✅ SLIDES 2-10 GENERATED")
    print("="*70)
    print(f"\nVideos saved to: {VIDEOS_DIR}")
    print("\nAll 10 slides complete!")
    print("View demo at: https://localhost:3000/html/demo-player.html")

if __name__ == "__main__":
    asyncio.run(main())
