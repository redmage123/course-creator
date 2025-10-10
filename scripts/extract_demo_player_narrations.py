#!/usr/bin/env python3
"""
Extract narration scripts from demo-player.html JavaScript
"""

import json
import re

# Read demo-player.html
with open('/home/bbrelin/course-creator/frontend/html/demo-player.html', 'r') as f:
    content = f.read()

# Extract the slides array (lines 628-720)
# Find the this.slides = [ ... ]; block
slides_match = re.search(r'this\.slides\s*=\s*\[(.*?)\];', content, re.DOTALL)

if not slides_match:
    print("Could not find slides array!")
    exit(1)

slides_text = slides_match.group(1)

# Parse slide objects
slide_pattern = r'\{[^}]*id:\s*(\d+),[^}]*title:\s*"([^"]+)",[^}]*video:\s*"([^"]+)",[^}]*duration:\s*(\d+),[^}]*narration:\s*"((?:[^"\\]|\\.)*)"\s*\}'

slides = []
for match in re.finditer(slide_pattern, slides_text, re.DOTALL):
    slide_id = int(match.group(1))
    title = match.group(2)
    video = match.group(3)
    duration = int(match.group(4))
    narration = match.group(5).replace('\\"', '"').replace('\\n', '\n')

    slides.append({
        "id": slide_id,
        "title": title,
        "video": video,
        "duration": duration,
        "narration": narration
    })

# Save to JSON file
output = {
    "slides": slides
}

with open('/home/bbrelin/course-creator/scripts/demo_player_narrations.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Extracted {len(slides)} slide narrations")
print("📄 Saved to: scripts/demo_player_narrations.json")

# Print summary
for slide in slides:
    print(f"\nSlide {slide['id']}: {slide['title']}")
    print(f"  Video: {slide['video']}")
    print(f"  Duration: {slide['duration']}s")
    print(f"  Narration length: {len(slide['narration'])} chars")
