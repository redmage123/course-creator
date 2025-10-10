#!/usr/bin/env python3
"""
Convert slide 1 clean screenshot to 15-second video

BUSINESS CONTEXT:
Creates a smooth, professional video from the clean homepage screenshot
for the first slide of the demo presentation, without cookie consent banner.
"""

import subprocess
import os
from pathlib import Path

# Paths
SCREENSHOT = "/home/bbrelin/course-creator/frontend/static/demo/screenshots/slide_01_clean.png"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_01_introduction.mp4"
DURATION = 15  # seconds

print("=" * 60)
print("SLIDE 1 VIDEO GENERATION")
print("=" * 60)

# Verify screenshot exists
if not os.path.exists(SCREENSHOT):
    print(f"❌ Screenshot not found: {SCREENSHOT}")
    exit(1)

print(f"✓ Screenshot found: {SCREENSHOT}")
file_size = os.path.getsize(SCREENSHOT)
print(f"  Size: {file_size:,} bytes")

# Create video from static image with subtle zoom effect
# This creates a more engaging video than just a static image
print(f"\n🎥 Creating {DURATION}s video with subtle zoom effect...")

cmd = [
    'ffmpeg',
    '-loop', '1',
    '-i', SCREENSHOT,
    '-c:v', 'libx264',
    '-t', str(DURATION),
    '-pix_fmt', 'yuv420p',
    '-vf', f'scale=1920:1080,zoompan=z=\'min(zoom+0.001,1.1)\':d={DURATION*30}:s=1920x1080:fps=30',
    '-preset', 'medium',
    '-crf', '23',
    '-movflags', '+faststart',
    '-y',  # Overwrite existing
    VIDEO_OUTPUT
]

try:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        print("✓ Video created successfully!")

        if os.path.exists(VIDEO_OUTPUT):
            video_size = os.path.getsize(VIDEO_OUTPUT)
            print(f"  Output: {VIDEO_OUTPUT}")
            print(f"  Size: {video_size:,} bytes")
        else:
            print("❌ Video file not found after creation!")
            exit(1)
    else:
        print(f"❌ FFmpeg error (exit code {result.returncode}):")
        print(result.stderr)
        exit(1)

except subprocess.TimeoutExpired:
    print("❌ FFmpeg timed out after 60 seconds")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ COMPLETE: Slide 1 video regenerated without cookie banner")
print(f"📁 Video location: {VIDEO_OUTPUT}")
print("=" * 60)
