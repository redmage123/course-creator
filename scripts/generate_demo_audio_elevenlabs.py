#!/usr/bin/env python3
"""
ElevenLabs Audio Generation for Demo Videos

BUSINESS PURPOSE:
Generates professional, natural-sounding narration for demo videos
using ElevenLabs AI voice synthesis API.

TECHNICAL APPROACH:
Uses ElevenLabs REST API to convert narration text to high-quality
audio files. Supports multiple voices and quality settings.

API DOCUMENTATION:
https://elevenlabs.io/docs/api-reference/text-to-speech

USAGE:
    python3 scripts/generate_demo_audio_elevenlabs.py

REQUIREMENTS:
    pip install requests

SETUP:
    1. Sign up at https://elevenlabs.io (free tier available)
    2. Get API key from https://elevenlabs.io/app/settings/api-keys
    3. Set environment variable: export ELEVENLABS_API_KEY="your_key_here"
    OR
    4. Create .env file with: ELEVENLABS_API_KEY=your_key_here
"""

import os
import sys
import json
import requests
from pathlib import Path
import time

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'
OUTPUT_DIR = Path('frontend/static/demo/audio')
AUDIO_FORMAT = 'mp3_44100_128'  # High quality MP3

# Voice IDs (from ElevenLabs library)
# You can get these from: https://api.elevenlabs.io/v1/voices
VOICES = {
    'rachel': '21m00Tcm4TlvDq8ikWAM',      # Female, American, warm
    'domi': 'AZnzlk1XvdvUeBnXmlld',        # Female, American, strong
    'bella': 'EXAVITQu4vr4xnSDxMaL',       # Female, American, soft
    'charlotte': 'XB0fDUnXU5powFXDhCwa',   # Female, UK, young (mid-20s), expressive ⭐
    'alice': 'Xb7hH8MSUJpSbSDYk0k2',       # Female, UK, clear, conversational
    'antoni': 'ErXwobaYiN019PkySvjV',      # Male, American, well-rounded
    'elli': 'MF3mGyEYCl7XYWbV9V6O',        # Female, American, conversational
    'josh': 'TxGEqnHWrfWFTfGW9XjX',        # Male, American, deep
    'arnold': 'VR6AewLTigWG4xSOukaG',      # Male, American, crisp
    'adam': 'pNInz6obpgDQGcFmaJgB',        # Male, American, deep
    'sam': 'yoZ06aMxZJJ28mfd3POQ',         # Male, American, dynamic
}

# Demo narration scripts - REVISED PROFESSIONAL VERSION (2025-10-09)
# Based on professional presenter analysis with pause timing and emphasis
NARRATIONS = [
    {
        'slide': 1,
        'title': 'Introduction',
        'text': 'Welcome to Course Creator Platform, built specifically for corporate training teams and professional instructors who need to create courses fast. Our AI-powered system transforms what used to take weeks into just minutes. In the next nine minutes, you\'ll see how artificial intelligence handles the heavy lifting while you focus on your expertise.'
    },
    {
        'slide': 2,
        'title': 'Organization Dashboard',
        'text': 'Every great learning program starts with a solid foundation. Watch as we create an organization. We\'ll enter the name, website, and a brief description. Then add contact details, like the business email and address. Finally, we\'ll set up the admin account with username, email, and password. In under a minute, you\'ve created a complete organizational structure, ready to host unlimited courses and manage hundreds of users. That\'s effortless setup.'
    },
    {
        'slide': 3,
        'title': 'Projects & Tracks',
        'text': 'Now, let\'s talk about structure. Projects let you organize related courses, think Web Development Bootcamp or Data Science Foundations. Tracks? They\'re your secret weapon for personalization. Create customized learning paths for beginners, intermediates, or advanced students, all within the same program. One platform, infinite possibilities.'
    },
    {
        'slide': 4,
        'title': 'Adding Instructors',
        'text': 'Your instructors are your greatest asset. Bring them onboard in seconds, assign them to specific projects or tracks, and they\'re instantly connected to your Slack or Teams channels for seamless collaboration. Whether it\'s co-developing courses with colleagues or running independent programs, everything integrates with the tools your team already uses.'
    },
    {
        'slide': 5,
        'title': 'Instructor Dashboard',
        'text': 'Here\'s where the AI magic happens. Tell our system your learning objectives, your target audience, and your key topics. Then watch as artificial intelligence generates a complete course structure, suggested modules, learning outcomes, even quiz questions. You review, refine, and approve. What used to take days of curriculum design now takes minutes. And when you schedule live sessions? Automatic Zoom or Teams integration means one click launches your class.'
    },
    {
        'slide': 6,
        'title': 'Course Content',
        'text': 'Here\'s where AI really shines. Need lesson content? Describe your topic and the AI generates a complete lesson draft, you just add your expertise and real-world examples. Creating quizzes? AI suggests questions based on your content, multiple choice, code challenges, scenario-based problems. You spend your time refining and personalizing, not starting from scratch. Upload presentations, embed videos, add code exercises with real-time feedback. The AI accelerates creation, you ensure quality.'
    },
    {
        'slide': 7,
        'title': 'Enroll Students',
        'text': 'Your course is ready, now it\'s time to welcome your students. One student? Easy. One hundred students? Even easier. Upload a CSV file and enroll an entire cohort in seconds. Organize by section, group by skill level, track by semester. However you teach, we adapt. Because managing students should be effortless, not exhausting.'
    },
    {
        'slide': 8,
        'title': 'Student Dashboard',
        'text': 'Now let\'s see what your students experience. They log in and immediately, everything they need is right there. Their courses, their progress, upcoming deadlines, recent achievements. No confusion, no hunting for information. Just a clear path forward and the motivation to keep going.'
    },
    {
        'slide': 9,
        'title': 'Course Browsing',
        'text': 'Here\'s where things get really exciting. Students browse the catalog, discover courses, and enroll with one click. But here\'s the game changer for technical training. When they hit a coding lesson? Professional development environments open right in their browser. VSCode for web development, PyCharm for Python, JupyterLab for data science, full Linux terminal for system administration. No installation, no configuration, no IT headaches. This is why corporate training teams choose us, their developers learn with real professional tools, no setup time wasted.'
    },
    {
        'slide': 10,
        'title': 'Taking Quizzes',
        'text': 'Assessment shouldn\'t feel like a gotcha moment, it should be a learning opportunity. Our quiz system delivers multiple question formats, multiple choice for quick checks, coding challenges for hands-on validation, short answer for deeper understanding. But here\'s what matters most, instant feedback. Not just a score, but detailed explanations that turn mistakes into mastery. Because real learning happens when students understand why.'
    },
    {
        'slide': 11,
        'title': 'Student Progress',
        'text': 'Progress should be visible and celebrated. Every quiz completed, every module mastered, every achievement unlocked. Students see their journey unfold in real time. Completion rates, quiz scores, time invested, it all adds up to something powerful, proof of growth. And that\'s what keeps them coming back.'
    },
    {
        'slide': 12,
        'title': 'Instructor Analytics',
        'text': 'Here\'s where we go beyond basic LMS reporting. Our AI-powered analytics don\'t just show you data, they surface insights. Which students are at risk of falling behind? AI flags them automatically. What content drives the most engagement? AI identifies patterns across all your courses. Which quiz questions are too easy or too hard? AI analyzes performance trends and suggests adjustments. Export reports to Slack or Teams so your entire training team stays informed. This isn\'t just analytics, it\'s intelligent course optimization.'
    },
    {
        'slide': 13,
        'title': 'Summary & Next Steps',
        'text': 'So that\'s Course Creator Platform. AI handles course development, content generation, and intelligent analytics. Your team works inside Slack, Teams, and Zoom, and everything integrates seamlessly. Whether you\'re building corporate training programs or teaching as an independent instructor, we turn weeks of work into minutes of guided setup. Ready to see it in action? Visit our site to get started.'
    }
]


def check_api_key():
    """
    Verify API key is configured
    """
    if not ELEVENLABS_API_KEY:
        print("❌ ERROR: ELEVENLABS_API_KEY not set")
        print()
        print("Please set your API key:")
        print("  1. Sign up at https://elevenlabs.io")
        print("  2. Get API key from https://elevenlabs.io/app/settings/api-keys")
        print("  3. Set environment variable:")
        print()
        print("     export ELEVENLABS_API_KEY='your_key_here'")
        print()
        print("  OR create .env file with:")
        print()
        print("     ELEVENLABS_API_KEY=your_key_here")
        print()
        sys.exit(1)


def get_available_voices():
    """
    Fetch available voices from ElevenLabs API

    RETURNS: List of available voices
    """
    url = f'{ELEVENLABS_API_URL}/voices'
    headers = {'xi-api-key': ELEVENLABS_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data.get('voices', [])

    except Exception as e:
        print(f"⚠️  Warning: Could not fetch voices: {e}")
        return []


def generate_audio(text, voice_id, output_path, slide_number):
    """
    Generate audio using ElevenLabs API

    ARGS:
        text: Narration text to synthesize
        voice_id: ElevenLabs voice ID
        output_path: Path to save audio file
        slide_number: Slide number for progress display

    RETURNS: True if successful, False otherwise
    """
    url = f'{ELEVENLABS_API_URL}/text-to-speech/{voice_id}'

    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY
    }

    data = {
        'text': text,
        'model_id': 'eleven_turbo_v2',  # Latest high-quality model (paid tier)
        'voice_settings': {
            'stability': 0.40,       # 0-1: Lower for natural variation and emotion (per Claude Sonnet recommendations)
            'similarity_boost': 0.85, # 0-1: Higher = premium voice quality
            'style': 0.25,           # 0-1: Subtle expressiveness for natural, human-like delivery (20-30% range)
            'use_speaker_boost': True  # Enhanced clarity and naturalness
        }
    }

    try:
        print(f"   Generating audio for slide {slide_number}...", end=' ', flush=True)

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # Save audio file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        # Get file size for confirmation
        size_kb = output_path.stat().st_size / 1024
        print(f"✓ ({size_kb:.1f}KB)")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"✗")
        print(f"      HTTP Error: {e}")
        if e.response.status_code == 401:
            print("      Check your API key is valid")
        elif e.response.status_code == 429:
            print("      Rate limit exceeded - waiting 60 seconds...")
            time.sleep(60)
            return generate_audio(text, voice_id, output_path, slide_number)
        return False

    except Exception as e:
        print(f"✗")
        print(f"      Error: {e}")
        return False


def main():
    """
    Main execution function
    """
    print("=" * 70)
    print("🎤 ELEVENLABS AUDIO GENERATION - Demo Narration")
    print("=" * 70)
    print()

    # Check API key
    check_api_key()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()

    # Get available voices (optional - for informational purposes)
    print("🎵 Fetching available voices...")
    voices = get_available_voices()
    if voices:
        print(f"   ✓ Found {len(voices)} available voices")
    print()

    # Select voice (Charlotte - UK female, mid-20s, natural and conversational)
    selected_voice = 'charlotte'
    voice_id = VOICES[selected_voice]
    print(f"🎙️  Selected voice: {selected_voice.title()} (UK Female, Mid-20s)")
    print(f"   Voice ID: {voice_id}")
    print(f"   Settings: Stability 0.40, Style 0.25 - Natural, human-like with emotion")
    print(f"   Optimized per Claude Sonnet recommendations for conversational delivery")
    print()

    # Generate audio for all slides
    print("=" * 70)
    print("Generating audio files...")
    print("=" * 70)
    print()

    success_count = 0
    failed_count = 0

    for narration in NARRATIONS:
        slide_num = narration['slide']
        title = narration['title']
        text = narration['text']

        print(f"📝 Slide {slide_num:02d}: {title}")

        # Output filename
        filename = f"slide_{slide_num:02d}_narration.mp3"
        output_path = OUTPUT_DIR / filename

        # Generate audio
        success = generate_audio(text, voice_id, output_path, slide_num)

        if success:
            success_count += 1
        else:
            failed_count += 1

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Summary
    print()
    print("=" * 70)
    print("✅ AUDIO GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"📊 Summary:")
    print(f"   • Total slides: {len(NARRATIONS)}")
    print(f"   • Success: {success_count}")
    print(f"   • Failed: {failed_count}")
    print()
    print(f"📁 Audio files saved to: {OUTPUT_DIR.absolute()}")
    print()

    if failed_count > 0:
        print("⚠️  Some files failed to generate. Check errors above.")
        print()

    # Next steps
    print("📋 Next Steps:")
    print("   1. Review generated audio files")
    print("   2. Update demo player to use audio files")
    print("   3. Test audio playback in browser")
    print()
    print("🔊 To preview audio files:")
    print(f"   mpg123 {OUTPUT_DIR}/slide_01_narration.mp3")
    print()


if __name__ == '__main__':
    main()
