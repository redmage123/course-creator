#!/usr/bin/env python3
"""
Audit all demo slides to check for privacy banner presence

BUSINESS CONTEXT:
Identifies which slides have the privacy modal/banner visible
so they can be regenerated without it for clean demo presentation.
"""

import os
from pathlib import Path
from PIL import Image
import subprocess

VIDEO_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
TEMP_DIR = Path("/tmp/slide_audit")

# Create temp directory
TEMP_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("DEMO SLIDES - PRIVACY BANNER AUDIT")
print("=" * 70)

# Get all slide videos
slides = sorted([f for f in VIDEO_DIR.glob("slide_*.mp4")])

print(f"\nFound {len(slides)} slides to audit\n")

results = []

for slide_video in slides:
    slide_name = slide_video.stem
    print(f"Checking {slide_name}...", end=" ")

    # Extract first frame
    frame_path = TEMP_DIR / f"{slide_name}_frame1.png"

    cmd = [
        'ffmpeg',
        '-i', str(slide_video),
        '-vframes', '1',
        '-f', 'image2',
        '-y',
        str(frame_path)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10
    )

    if result.returncode == 0 and frame_path.exists():
        # Check image for privacy-related content
        # Look for common privacy banner patterns
        try:
            img = Image.open(frame_path)
            width, height = img.size

            # Sample center area where privacy banners typically appear
            # Privacy modals usually appear in center or bottom-center
            center_y = height // 2
            bottom_third_y = int(height * 0.66)

            # Check if image has very bright/white areas in center (typical for modals)
            # This is a heuristic check
            pixels = img.load()

            bright_pixels = 0
            sample_points = [
                (width//2, center_y),
                (width//2, bottom_third_y),
                (width//3, center_y),
                (2*width//3, center_y),
            ]

            for x, y in sample_points:
                try:
                    pixel = pixels[x, y]
                    # Check if pixel is very bright (likely modal background)
                    if isinstance(pixel, tuple) and len(pixel) >= 3:
                        r, g, b = pixel[:3]
                        if r > 200 and g > 200 and b > 200:
                            bright_pixels += 1
                except:
                    pass

            # Manual visual check needed - save frame for review
            has_banner = "NEEDS_REVIEW"
            status = "⚠️  Review needed"

            if bright_pixels >= 3:
                has_banner = "LIKELY"
                status = "⚠️  Likely has privacy banner"
            else:
                has_banner = "UNLIKELY"
                status = "✓ Probably clean"

            results.append({
                'slide': slide_name,
                'status': has_banner,
                'frame': str(frame_path),
                'size': f"{slide_video.stat().st_size / 1024:.0f}KB"
            })

            print(status)

        except Exception as e:
            print(f"❌ Error analyzing: {e}")
            results.append({
                'slide': slide_name,
                'status': 'ERROR',
                'frame': str(frame_path),
                'size': f"{slide_video.stat().st_size / 1024:.0f}KB"
            })
    else:
        print("❌ Failed to extract frame")
        results.append({
            'slide': slide_name,
            'status': 'NO_FRAME',
            'frame': 'N/A',
            'size': f"{slide_video.stat().st_size / 1024:.0f}KB"
        })

# Print summary
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)

likely_needs_fix = []
needs_review = []

for r in results:
    status_icon = {
        'LIKELY': '❌',
        'UNLIKELY': '✓',
        'NEEDS_REVIEW': '⚠️',
        'ERROR': '❌',
        'NO_FRAME': '❌'
    }.get(r['status'], '?')

    print(f"{status_icon} {r['slide']:30s} - {r['status']:15s} - {r['size']:10s}")

    if r['status'] == 'LIKELY':
        likely_needs_fix.append(r['slide'])
    elif r['status'] in ['NEEDS_REVIEW', 'ERROR', 'NO_FRAME']:
        needs_review.append(r['slide'])

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if likely_needs_fix:
    print(f"\n⚠️  {len(likely_needs_fix)} slides LIKELY have privacy banner:")
    for slide in likely_needs_fix:
        print(f"   - {slide}")

if needs_review:
    print(f"\n⚠️  {len(needs_review)} slides need manual review:")
    for slide in needs_review:
        print(f"   - {slide}")

print(f"\n📁 First frames saved to: {TEMP_DIR}")
print("   Review these images manually to confirm which slides need regeneration")

print("\n" + "=" * 70)
