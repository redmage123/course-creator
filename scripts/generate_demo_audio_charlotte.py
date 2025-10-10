#!/usr/bin/env python3
"""
Generate Demo Audio Narrations with ElevenLabs Charlotte Voice
"""

import json
import os
import requests
from pathlib import Path
import time

# Load API key from .cc_env
API_KEY = None
with open('/home/bbrelin/course-creator/.cc_env', 'r') as f:
    for line in f:
        if line.startswith('ELEVENLABS_API_KEY='):
            API_KEY = line.strip().split('=')[1]
            break

if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not found in .cc_env")

# Charlotte voice ID (you may need to verify this)
CHARLOTTE_VOICE_ID = "XB0fDUnXU5powFXDhCwa"  # Charlotte voice

AUDIO_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def generate_audio(text, output_file, voice_id=CHARLOTTE_VOICE_ID):
    """
    Generate audio using ElevenLabs API
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

    print(f"  🎙️  Generating audio: {output_file.name}")

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"  ✅ Saved: {output_file.name}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    print("="*70)
    print("🎙️  GENERATING DEMO AUDIO - Charlotte Voice")
    print("="*70)
    print()

    # Load narration scripts
    with open('/home/bbrelin/course-creator/scripts/demo_narration_scripts.json', 'r') as f:
        data = json.load(f)

    slides = data['slides']

    for slide in slides:
        slide_num = str(slide['id']).zfill(2)
        output_file = AUDIO_DIR / f"slide_{slide_num}_narration.mp3"

        print(f"\n📝 Slide {slide['id']}: {slide['title']}")
        print(f"   Duration: ~{slide['duration']}s")
        print(f"   Script: {slide['script'][:100]}...")

        success = generate_audio(slide['script'], output_file)

        if success:
            # Check file size
            file_size = output_file.stat().st_size / 1024  # KB
            print(f"   Size: {file_size:.1f} KB")

        # Rate limiting - don't hammer the API
        if slide['id'] < len(slides):
            print("   ⏳ Waiting 2s...")
            time.sleep(2)

    print("\n" + "="*70)
    print("✅ ALL AUDIO FILES GENERATED")
    print("="*70)
    print(f"\nAudio files saved to: {AUDIO_DIR}")
    print("\nNext steps:")
    print("  1. Review audio files for quality")
    print("  2. Run Playwright demo generation script")
    print("  3. Test individual slides")

if __name__ == "__main__":
    main()
