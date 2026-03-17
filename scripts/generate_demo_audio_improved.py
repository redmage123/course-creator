#!/usr/bin/env python3
"""
Improved ElevenLabs Audio Generation - Natural Voice Quality

BUSINESS PURPOSE:
Generates professional, natural-sounding narration for demo videos
using ElevenLabs AI voice synthesis API with optimized settings
for clarity, warmth, and natural delivery without echo or robotic artifacts.

KEY IMPROVEMENTS OVER PREVIOUS VERSION:
1. Uses eleven_multilingual_v2 model for higher quality output
2. Higher stability (0.70) to reduce echo and artifacts
3. Rachel voice (warm, professional American female)
4. Cleaner SSML with more natural pacing
5. Stereo output for better audio quality

USAGE:
    source .cc_env && python3 scripts/generate_demo_audio_improved.py

    # Test single slide first:
    source .cc_env && python3 scripts/generate_demo_audio_improved.py --test

REQUIREMENTS:
    pip install requests
"""

import os
import sys
import json
import requests
from pathlib import Path
import time
import argparse

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'
OUTPUT_DIR = Path('frontend-legacy/static/demo/audio')

# Voice IDs from ElevenLabs library
# Testing multiple voices to find the best natural sound
VOICES = {
    'rachel': '21m00Tcm4TlvDq8ikWAM',      # Female, American, warm and professional
    'sarah': 'EXAVITQu4vr4xnSDxMaL',        # Female, American, soft and friendly
    'elli': 'MF3mGyEYCl7XYWbV9V6O',         # Female, American, clear narrator
    'nicole': 'piTKgcLEGmPE4e6mEKli',       # Female, American, conversational
    'adam': 'pNInz6obpgDQGcFmaJgB',         # Male, American, deep and professional
}

# Model options - higher quality vs speed tradeoff
MODELS = {
    'multilingual_v2': 'eleven_multilingual_v2',  # Highest quality, supports 29 languages
    'turbo_v2_5': 'eleven_turbo_v2_5',            # Good quality, faster
    'turbo_v2': 'eleven_turbo_v2',                # Fast but may have artifacts
}

# Narrations with cleaner SSML - removed excessive breaks that can cause artifacts
NATURAL_NARRATIONS = [
    {
        'slide': 1,
        'title': 'Introduction',
        'text': '''Welcome to the Course Creator Platform.

Built specifically for corporate training teams and professional instructors who need to create courses fast.

Our AI-powered system transforms what used to take weeks into just minutes.

In the next slide, we'll show you how to get started.'''
    },
    {
        'slide': 2,
        'title': 'Getting Started - Register Your Organization',
        'text': '''To get started, simply click Register Organization on the home page.

Now, let's fill in the details.

Enter your organization name, website, and a brief description.

Add your contact information, including business email and address.

Finally, set up your administrator account with credentials.

Click submit, and there you go! Your organization is successfully registered.

Next, we'll show you how to create projects.'''
    },
    {
        'slide': 3,
        'title': 'Organization Admin Dashboard',
        'text': '''Let's log in as the organization admin we just created.

First, navigate to the home page and click the Login button in the header.

Now, enter the email address: sarah at acmelearning dot edu. Then enter the password.

Click the login button to sign in.

Notice the user icon in the header changes to show you're logged in. You're now redirected to your organization admin dashboard!

From here, you can manage everything.

Notice the purple AI assistant button in the bottom right corner. You can use it to manage your organization through natural language instead of filling out forms.

Let's create a new project. Click Create New Project, enter the project name and description, then click Create. Your project is ready! You can edit or delete projects anytime.

Now, let's change which project we're viewing. Click the Current Project dropdown and select Data Science Foundations. Notice how the metrics update instantly!

The Tracks metric shows how many learning paths are in this project. The Instructors metric shows your teaching team. And Students shows total enrollment.

Click on Tracks to see all learning paths. Click on Members to manage your team. Click Settings to configure the project.

Next, we'll show you how to create tracks for your project.'''
    },
    {
        'slide': 4,
        'title': 'Creating Tracks',
        'text': '''Now let's create a learning track!

We're already viewing the Tracks tab from the previous slide. Click the Create New Track button. This opens the track creation form.

First, enter the track name: Python Fundamentals.

Next, select the project. Choose Data Science Foundations from the dropdown.

Then select the level. We'll make this a Beginner track.

Now add a description: Learn Python basics for data science.

Click Create Track, and there you go! Your track is created.

Tracks let you organize courses into structured learning paths at different skill levels. Students can follow these tracks from beginner to advanced.

Next, we'll show you the AI assistant in action!'''
    },
    {
        'slide': 5,
        'title': 'AI Assistant - Natural Language Management',
        'text': '''Instead of filling out forms, you can simply tell our AI assistant what you need.

Watch how easy it is!

Click the purple AI assistant button in the bottom right corner. The chat panel slides up.

Now, just describe what you want in plain English. Type: Create an intermediate track called Machine Learning Basics for the Data Science project.

The AI understands your request instantly! It confirms the details and creates the track for you.

No forms to fill out. No dropdowns to navigate. Just natural conversation.

The AI assistant can help you create projects, manage tracks, onboard instructors, and generate course content.

It's like having an expert teammate available twenty-four seven!

Next, we'll show you how to add instructors to your organization.'''
    },
    {
        'slide': 6,
        'title': 'Adding Instructors',
        'text': '''Your instructors are your greatest asset.

Bring them onboard in seconds, assign them to specific projects or tracks, and they're instantly connected to your Slack or Teams channels for seamless collaboration.

Whether it's co-developing courses with colleagues or running independent programs, everything integrates with the tools your team already uses.'''
    },
    {
        'slide': 7,
        'title': 'Instructor Dashboard',
        'text': '''Instructors have powerful AI tools at their fingertips!

Tell the system your learning objectives, your target audience, and your key topics.

Then watch as artificial intelligence generates a complete course structure, suggested modules, learning outcomes, even quiz questions!

You review, refine, and approve.

What used to take days of curriculum design now takes minutes.

And when you schedule live sessions? Automatic Zoom or Teams integration means one click launches your class!'''
    },
    {
        'slide': 8,
        'title': 'Course Content',
        'text': '''AI accelerates content creation!

Need lesson content? Describe your topic and the AI generates a complete lesson draft. You just add your expertise and real-world examples.

Creating quizzes? AI suggests questions based on your content: multiple choice, code challenges, scenario-based problems.

You spend your time refining and personalizing, not starting from scratch.

Upload presentations, embed videos, add code exercises with real-time feedback.

The AI accelerates creation. You ensure quality.'''
    },
    {
        'slide': 9,
        'title': 'Enroll Students',
        'text': '''Your course is ready! Now it's time to welcome your students.

One student? Easy. One hundred students? Even easier!

Upload a CSV file and enroll an entire class in seconds.

Organize by section, group by skill level, track by semester.

However you teach, we adapt.

Because managing students should be effortless, not exhausting.'''
    },
    {
        'slide': 10,
        'title': 'Student Dashboard',
        'text': '''Now let's see what your students experience.

They log in and immediately, everything they need is right there.

Their courses, their progress, upcoming deadlines, recent achievements.

No confusion. No hunting for information.

Just a clear path forward and the motivation to keep going.'''
    },
    {
        'slide': 11,
        'title': 'Course Browsing',
        'text': '''Students browse the catalog, discover courses, and enroll with one click.

The game changer for technical training?

When they hit a coding lesson, professional development environments open right in their browser!

VS Code for web development. PyCharm for Python. JupyterLab for data science. Full Linux terminal for system administration.

No installation. No configuration. No IT headaches!

This is why corporate training teams choose us! Their developers learn with real professional tools, no setup time wasted.'''
    },
    {
        'slide': 12,
        'title': 'Taking Quizzes',
        'text': '''Assessment shouldn't feel like a gotcha moment. It should be a learning opportunity!

Our quiz system delivers multiple question formats: multiple choice for quick checks, coding challenges for hands-on validation, short answer for deeper understanding.

But here's what matters most: instant feedback!

Not just a score, but detailed explanations that turn mistakes into mastery.

Because real learning happens when students understand why.'''
    },
    {
        'slide': 13,
        'title': 'Student Progress',
        'text': '''Progress should be visible and celebrated!

Every quiz completed. Every module mastered. Every achievement unlocked.

Students see their journey unfold in real time.

Completion rates, quiz scores, time invested. It all adds up to something powerful: proof of growth!

And that's what keeps them coming back.'''
    },
    {
        'slide': 14,
        'title': 'Instructor Analytics',
        'text': '''We go beyond basic LMS reporting!

Our AI-powered analytics don't just show you data. They surface insights!

Which students are at risk of falling behind? AI flags them automatically.

What content drives the most engagement? AI identifies patterns across all your courses.

Which quiz questions are too easy or too hard? AI analyzes performance trends and suggests adjustments.

Export reports to Slack or Teams so your entire training team stays informed.

This isn't just analytics. It's intelligent course optimization!'''
    },
    {
        'slide': 15,
        'title': 'Summary & Next Steps',
        'text': '''So that's Course Creator Platform!

AI handles course development, content generation, and intelligent analytics.

Your team works inside Slack, Teams, and Zoom, and everything integrates seamlessly.

Whether you're building corporate training programs or teaching as an independent instructor, we turn weeks of work into minutes of guided setup.

Ready to see it in action?

Visit our site to get started!'''
    }
]


def check_api_key():
    """Verify API key is configured"""
    if not ELEVENLABS_API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set")
        print()
        print("Set your API key:")
        print("  source .cc_env")
        print()
        sys.exit(1)


def get_available_voices():
    """Fetch and display available voices from ElevenLabs API"""
    url = f'{ELEVENLABS_API_URL}/voices'
    headers = {'xi-api-key': ELEVENLABS_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        voices = data.get('voices', [])

        print(f"Found {len(voices)} available voices:")
        for v in voices[:10]:  # Show first 10
            print(f"  - {v['name']}: {v['voice_id']} ({v.get('labels', {}).get('accent', 'unknown accent')})")

        return voices
    except Exception as e:
        print(f"Warning: Could not fetch voices: {e}")
        return []


def generate_audio(text, voice_id, output_path, slide_number, model='eleven_multilingual_v2'):
    """
    Generate high-quality audio using ElevenLabs API

    KEY SETTINGS FOR NATURAL SOUND:
    - stability: 0.70 (higher = more consistent, less artifacts/echo)
    - similarity_boost: 0.75 (balanced for natural variation)
    - style: 0.30 (moderate expressiveness, not overdone)
    - use_speaker_boost: True (enhanced clarity)

    ARGS:
        text: Narration text (plain text, no SSML needed with this model)
        voice_id: ElevenLabs voice ID
        output_path: Path to save audio file
        slide_number: Slide number for progress display
        model: Model ID to use

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
        'model_id': model,
        'voice_settings': {
            # OPTIMIZED FOR NATURAL, CLEAR DELIVERY:
            'stability': 0.70,         # Higher = less variation/echo
            'similarity_boost': 0.75,  # Balanced voice quality
            'style': 0.30,             # Moderate expressiveness
            'use_speaker_boost': True  # Enhanced clarity
        }
    }

    try:
        print(f"   Generating audio for slide {slide_number}...", end=' ', flush=True)

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # Save audio file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        # Get file size and estimate duration
        size_kb = output_path.stat().st_size / 1024
        # Rough estimate: 128kbps = 16KB/s
        est_duration = size_kb / 16
        print(f"Done ({size_kb:.1f}KB, ~{est_duration:.0f}s)")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"Failed")
        print(f"      HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"      Response: {e.response.text[:500] if e.response.text else 'No response body'}")
            if e.response.status_code == 401:
                print("      Check your API key is valid")
            elif e.response.status_code == 429:
                print("      Rate limit exceeded - waiting 60 seconds...")
                time.sleep(60)
                return generate_audio(text, voice_id, output_path, slide_number, model)
        return False

    except Exception as e:
        print(f"Failed")
        print(f"      Error: {e}")
        return False


def test_single_slide():
    """Generate audio for slide 1 only to test quality"""
    print("=" * 70)
    print("TESTING IMPROVED AUDIO QUALITY - SLIDE 1 ONLY")
    print("=" * 70)
    print()

    check_api_key()

    # Create test output directory
    test_dir = Path('frontend-legacy/static/demo/audio/test')
    test_dir.mkdir(parents=True, exist_ok=True)

    # Test with Rachel voice (warm, professional)
    voice_id = VOICES['rachel']
    narration = NATURAL_NARRATIONS[0]

    print("Testing with Rachel voice (warm American female)")
    print(f"Model: eleven_multilingual_v2")
    print(f"Settings: stability=0.70, similarity=0.75, style=0.30")
    print()

    output_path = test_dir / "test_slide_01_rachel.mp3"
    success = generate_audio(
        narration['text'],
        voice_id,
        output_path,
        1,
        model='eleven_multilingual_v2'
    )

    if success:
        print()
        print("Test audio generated!")
        print(f"File: {output_path.absolute()}")
        print()
        print("To play the test audio:")
        print(f"   mpg123 {output_path}")
        print()
        print("Compare with current audio:")
        print(f"   mpg123 frontend-legacy/static/demo/audio/slide_01_narration.mp3")
        print()
        print("If quality is better, run without --test to regenerate all slides.")
    else:
        print("Test failed. Check errors above.")

    return success


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate improved demo audio')
    parser.add_argument('--test', action='store_true', help='Test with slide 1 only')
    parser.add_argument('--voice', default='rachel', choices=VOICES.keys(), help='Voice to use')
    parser.add_argument('--model', default='eleven_multilingual_v2', choices=MODELS.values(), help='Model to use')
    args = parser.parse_args()

    if args.test:
        return test_single_slide()

    print("=" * 70)
    print("IMPROVED ELEVENLABS AUDIO GENERATION")
    print("Natural Voice with Higher Quality Settings")
    print("=" * 70)
    print()

    check_api_key()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Voice selection
    voice_id = VOICES[args.voice]
    print(f"Selected voice: {args.voice.title()}")
    print(f"Model: {args.model}")
    print()
    print("Optimized Voice Settings (to reduce echo/artifacts):")
    print("   Stability: 0.70 (higher = more consistent)")
    print("   Similarity: 0.75 (balanced quality)")
    print("   Style: 0.30 (moderate expressiveness)")
    print("   Speaker Boost: Enabled")
    print()

    # Generate audio for all slides
    print("=" * 70)
    print("Generating Audio Files...")
    print("=" * 70)
    print()

    success_count = 0
    failed_count = 0

    for narration in NATURAL_NARRATIONS:
        slide_num = narration['slide']
        title = narration['title']
        text = narration['text']

        print(f"Slide {slide_num:02d}: {title}")

        # Output filename
        filename = f"slide_{slide_num:02d}_narration.mp3"
        output_path = OUTPUT_DIR / filename

        success = generate_audio(text, voice_id, output_path, slide_num, args.model)

        if success:
            success_count += 1
        else:
            failed_count += 1

        # Delay to avoid rate limiting
        time.sleep(1.5)

    # Summary
    print()
    print("=" * 70)
    print("AUDIO GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Summary:")
    print(f"   Total slides: {len(NATURAL_NARRATIONS)}")
    print(f"   Success: {success_count}")
    print(f"   Failed: {failed_count}")
    print()
    print(f"Audio files saved to: {OUTPUT_DIR.absolute()}")
    print()

    if failed_count > 0:
        print("Some files failed to generate. Check errors above.")
        print()

    print("Next Steps:")
    print("   1. Listen to audio files to verify quality improvement")
    print("   2. Re-record videos to match new audio durations")
    print("   3. Update DemoPlayer with synchronized content")
    print()


if __name__ == '__main__':
    main()
