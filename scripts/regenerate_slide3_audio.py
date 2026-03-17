#!/usr/bin/env python3
"""
Regenerate Slide 3 Audio - Corrected Narration
"""

import os
import sys
import requests
from pathlib import Path

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'
OUTPUT_PATH = Path('frontend/static/demo/audio/slide_03_narration.mp3')

# Charlotte voice ID (UK Female, mid-20s, expressive)
VOICE_ID = 'XB0fDUnXU5powFXDhCwa'

# CORRECTED narration - ends with "create learning tracks" not "add instructors"
NARRATION_TEXT = """Let's log in as the organization admin we just created. First, navigate to the home page and click the Login button in the header. Now, enter the email address: sarah at acmelearning dot edu. Then enter the password. Click the login button to sign in. Notice the user icon in the header changes to show you're logged in. You're now redirected to your organization admin dashboard. From here, you can manage everything. Let's create a new project. Click Create New Project, enter the project name and description, then click Create. Your project is ready! You can edit or delete projects anytime. Now, let's change which project we're viewing. Click the Current Project dropdown and select Data Science Foundations. Notice how the metrics update instantly. The Tracks metric shows how many learning paths are in this project. The Instructors metric shows your teaching team. And Students shows total enrollment. Click on Tracks to see all learning paths. Click on Members to manage your team. Click Settings to configure the project. Next, we'll show you how to create learning tracks for your organization."""

def main():
    if not ELEVENLABS_API_KEY:
        print("❌ ERROR: ELEVENLABS_API_KEY not set")
        print("export ELEVENLABS_API_KEY='your_key_here'")
        sys.exit(1)

    print("=" * 70)
    print("🎤 Regenerating Slide 3 Audio - Corrected Narration")
    print("=" * 70)
    print()
    print("📝 Narration ending: ...create learning tracks for your organization.")
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
