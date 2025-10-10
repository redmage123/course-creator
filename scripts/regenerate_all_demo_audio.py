#!/usr/bin/env python3
"""
Regenerate ALL demo narration audio files (slides 1-13)
Using ElevenLabs Charlotte voice with correct narration text from demo-player.html
"""

import json
import requests
import os
from pathlib import Path
import time

# ElevenLabs API configuration
API_KEY = os.getenv("ELEVENLABS_API_KEY")
CHARLOTTE_VOICE_ID = "XB0fDUnXU5powFXDhCwa"  # Charlotte - UK Female, mid-20s

AUDIO_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def generate_audio(text, output_file, voice_id=CHARLOTTE_VOICE_ID):
    """
    Generate audio narration using ElevenLabs API
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    print(f"  Generating: {output_file.name}")
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Get file size
        size_kb = output_file.stat().st_size / 1024
        print(f"  ✅ Generated: {output_file.name} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return False

def main():
    if not API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("   Please set it in .cc_env file")
        exit(1)

    print("="*70)
    print("🎙️  REGENERATING ALL DEMO AUDIO NARRATIONS (1-13)")
    print("   Voice: Charlotte (UK Female, professional, enthusiastic)")
    print("   Using correct long narrations from demo-player.html")
    print("="*70)
    print()

    # Load correct narration scripts
    with open('/home/bbrelin/course-creator/scripts/demo_player_narrations_correct.json', 'r') as f:
        data = json.load(f)

    total_slides = len(data['slides'])
    print(f"Found {total_slides} slides to generate\n")

    success_count = 0

    for slide in data['slides']:
        slide_num = slide['id']
        title = slide['title']
        narration = slide['narration']
        duration = slide['duration']

        print(f"Slide {slide_num}/13: {title}")
        print(f"  Expected duration: {duration}s")
        print(f"  Narration length: {len(narration)} characters")

        output_file = AUDIO_DIR / f"slide_{str(slide_num).zfill(2)}_narration.mp3"

        if generate_audio(narration, output_file):
            success_count += 1
            # Small delay to avoid rate limiting
            time.sleep(1)

        print()

    print("="*70)
    print(f"✅ AUDIO GENERATION COMPLETE: {success_count}/{total_slides} slides")
    print("="*70)
    print(f"\nAudio files saved to: {AUDIO_DIR}")
    print("\nNext steps:")
    print("  1. Verify audio durations match or exceed video durations")
    print("  2. Test in demo player: https://localhost:3000/html/demo-player.html")
    print("  3. Check for audio sync with videos")

if __name__ == "__main__":
    main()
