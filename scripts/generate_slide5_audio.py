#!/usr/bin/env python3
"""
Generate Slide 5 Audio - Course Generation with AI
"""

import os
import sys
import requests
from pathlib import Path

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'
OUTPUT_PATH = Path('frontend/static/demo/audio/slide_05_narration.mp3')

# Charlotte voice ID (UK Female, mid-20s, expressive)
VOICE_ID = 'XB0fDUnXU5powFXDhCwa'

# Narration for course generation demo
NARRATION_TEXT = """Now let's explore one of the platform's most powerful features: AI-powered course generation. Click on the Courses tab in the sidebar. Here, organization admins can create entire courses using artificial intelligence. Click the Generate Course with AI button to open the course creation form. Enter a course title, like Machine Learning Fundamentals. Add a detailed description explaining what students will learn. Select the course category from the dropdown, such as Data Science. Choose the difficulty level that matches your audience. In this case, we'll select Intermediate. Now click the Generate button, and watch as our AI assistant creates a complete course structure with modules, lessons, and learning objectives. The AI analyzes your requirements and generates a comprehensive curriculum tailored to your specifications. This saves instructors countless hours of course planning and ensures high-quality educational content."""

def main():
    if not ELEVENLABS_API_KEY:
        print("❌ ERROR: ELEVENLABS_API_KEY not set")
        print("export ELEVENLABS_API_KEY='your_key_here'")
        sys.exit(1)

    print("=" * 70)
    print("🎤 Generating Slide 5 Audio - Course Generation")
    print("=" * 70)
    print()
    print("📝 Narration: AI-powered course generation demo")
    print()

    url = f'{ELEVENLABS_API_URL}/text-to-speech/{VOICE_ID}'

    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY
    }

    data = {
        'text': NARRATION_TEXT,
        'model_id': 'eleven_turbo_v2',
        'voice_settings': {
            'stability': 0.40,
            'similarity_boost': 0.85,
            'style': 0.25,
            'use_speaker_boost': True
        }
    }

    try:
        print("🎙️  Generating audio with ElevenLabs...", flush=True)
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # Save audio file
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'wb') as f:
            f.write(response.content)

        size_kb = OUTPUT_PATH.stat().st_size / 1024
        print(f"✅ Audio generated successfully!")
        print(f"   File: {OUTPUT_PATH}")
        print(f"   Size: {size_kb:.1f}KB")
        print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("   Check your API key is valid")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
