#!/usr/bin/env python3
"""
Fix Slide 13 audio - create shorter narration to fit 15s video
"""

import requests
import os
from pathlib import Path

API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_2718a08701a491e97346dfed6b1a203df6f9588124f609f6")
CHARLOTTE_VOICE_ID = "XB0fDUnXU5powFXDhCwa"

AUDIO_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/audio")

# Shorter narration that fits 15 seconds
SHORT_NARRATION = "Course Creator Platform. AI-powered training, from development to analytics. Built for teams using Slack, Teams, and Zoom. Turn weeks into minutes. Ready? Visit our site to get started."

def generate_audio(text, output_file):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{CHARLOTTE_VOICE_ID}"

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

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

output_file = AUDIO_DIR / "slide_13_narration.mp3"
print(f"Generating shorter Slide 13 narration...")
print(f"Text: {SHORT_NARRATION}")
print(f"Length: {len(SHORT_NARRATION)} characters")

if generate_audio(SHORT_NARRATION, output_file):
    import subprocess
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(output_file)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    print(f"✅ Generated! Duration: {duration:.1f}s (target: <15s)")

    if duration > 15:
        print(f"⚠️  Still too long by {duration - 15:.1f}s")
    else:
        print(f"✅ Perfect fit! {15 - duration:.1f}s of margin")
else:
    print("❌ Generation failed")
