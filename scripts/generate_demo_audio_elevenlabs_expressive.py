#!/usr/bin/env python3
"""
ElevenLabs Audio Generation with SSML Expressive Narration

BUSINESS PURPOSE:
Generates professional, emotionally engaging narration for demo videos
using ElevenLabs AI voice synthesis API with SSML markup for dramatic
pauses, natural rhythm, and expressive delivery.

TECHNICAL APPROACH:
- Uses SSML <break> tags for strategic pauses (max 3 seconds each)
- Expressive punctuation guides AI prosody
- Higher 'style' parameter for more emotional delivery
- Natural speech patterns with varied pacing

SSML TAGS SUPPORTED BY ELEVENLABS (eleven_turbo_v2 model):
- <break time="Xs" /> - Pause for X seconds (max 3s)

EXPRESSIVENESS TECHNIQUES USED:
1. Strategic break tags at key emotional moments
2. Exclamation marks for enthusiasm
3. Question patterns for engagement
4. Short punchy sentences for impact
5. Voice settings optimized for expressiveness

API DOCUMENTATION:
https://elevenlabs.io/docs/api-reference/text-to-speech

USAGE:
    python3 scripts/generate_demo_audio_elevenlabs_expressive.py

REQUIREMENTS:
    pip install requests
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
OUTPUT_DIR = Path('frontend-legacy/static/demo/audio')
AUDIO_FORMAT = 'mp3_44100_128'  # High quality MP3

# Voice IDs (from ElevenLabs library)
VOICES = {
    'rachel': '21m00Tcm4TlvDq8ikWAM',      # Female, American, warm
    'domi': 'AZnzlk1XvdvUeBnXmlld',        # Female, American, strong
    'bella': 'EXAVITQu4vr4xnSDxMaL',       # Female, American, soft
    'charlotte': 'XB0fDUnXU5powFXDhCwa',   # Female, UK, young (mid-20s), expressive
    'alice': 'Xb7hH8MSUJpSbSDYk0k2',       # Female, UK, clear, conversational
    'antoni': 'ErXwobaYiN019PkySvjV',      # Male, American, well-rounded
    'josh': 'TxGEqnHWrfWFTfGW9XjX',        # Male, American, deep
}

# ============================================================================
# EXPRESSIVE NARRATIONS WITH SSML MARKUP
# ============================================================================
# Each narration includes:
# - <break time="Xs"/> tags for dramatic pauses
# - Expressive punctuation for natural prosody
# - Short impactful sentences where appropriate
# - Enthusiasm markers (!) at key revelation points
# ============================================================================

EXPRESSIVE_NARRATIONS = [
    {
        'slide': 1,
        'title': 'Introduction',
        'text': '''Welcome to THE Course Creator Platform! <break time="0.5s"/>

Built specifically for corporate training teams <break time="0.3s"/> and professional instructors <break time="0.3s"/> who need to create courses fast.

<break time="0.7s"/>

Our AI-powered system transforms what used to take weeks <break time="0.5s"/> into just minutes.

<break time="0.5s"/>

In the next slide, <break time="0.3s"/> we'll show you how to get started.'''
    },
    {
        'slide': 2,
        'title': 'Getting Started - Register Your Organization',
        'text': '''To get started, <break time="0.3s"/> simply click Register Organization on the home page.

<break time="0.5s"/>

Now, let's fill in the details.

<break time="0.4s"/>

Enter your organization name, <break time="0.2s"/> website, <break time="0.2s"/> and a brief description.

Add your contact information, <break time="0.3s"/> including business email and address.

Finally, <break time="0.3s"/> set up your administrator account with credentials.

<break time="0.5s"/>

Click submit, <break time="0.3s"/> and there you go!

<break time="0.3s"/>

Your organization is successfully registered.

<break time="0.5s"/>

Next, <break time="0.2s"/> we'll show you how to create projects.'''
    },
    {
        'slide': 3,
        'title': 'Organization Admin Dashboard',
        'text': '''Let's log in as the organization admin we just created.

<break time="0.4s"/>

First, <break time="0.2s"/> navigate to the home page and click the Login button in the header.

<break time="0.3s"/>

Now, enter the email address: <break time="0.3s"/> sarah at acmelearning dot <say-as interpret-as="characters">edu</say-as>.

<break time="0.2s"/>

Then enter the password.

<break time="0.3s"/>

Click the login button to sign in.

<break time="0.5s"/>

Notice the user icon in the header changes to show you're logged in.

<break time="0.4s"/>

You're now redirected to your organization admin dashboard!

<break time="0.3s"/>

From here, <break time="0.2s"/> you can manage everything.

<break time="0.7s"/>

Notice the purple AI assistant button in the bottom right corner. <break time="0.4s"/> You can use it to manage your organization through natural language <break time="0.3s"/> instead of filling out forms!

<break time="0.6s"/>

Let's create a new project.

<break time="0.3s"/>

Click Create New Project, <break time="0.2s"/> enter the project name and description, <break time="0.3s"/> then click Create.

<break time="0.4s"/>

Your project is ready!

<break time="0.3s"/>

You can edit or delete projects anytime.

<break time="0.5s"/>

Now, let's change which project we're viewing.

<break time="0.3s"/>

Click the Current Project dropdown and select Data Science Foundations.

<break time="0.4s"/>

Notice how the metrics update instantly!

<break time="0.5s"/>

The Tracks metric shows how many learning paths are in this project.

<break time="0.2s"/>

The Instructors metric shows your teaching team.

<break time="0.2s"/>

And Students shows total enrollment.

<break time="0.5s"/>

Click on Tracks to see all learning paths.

<break time="0.2s"/>

Click on Members to manage your team.

<break time="0.2s"/>

Click Settings to configure the project.

<break time="0.5s"/>

Next, <break time="0.2s"/> we'll show you how to create tracks for your project.'''
    },
    {
        'slide': 4,
        'title': 'Creating Tracks',
        'text': '''Now let's create a learning track!

<break time="0.4s"/>

We're already viewing the Tracks tab from the previous slide.

<break time="0.3s"/>

Click the Create New Track button.

<break time="0.4s"/>

This opens the track creation form.

<break time="0.3s"/>

First, <break time="0.2s"/> enter the track name: <break time="0.3s"/> Python Fundamentals.

<break time="0.3s"/>

Next, <break time="0.2s"/> select the project.

<break time="0.2s"/>

Choose Data Science Foundations from the dropdown.

<break time="0.3s"/>

Then select the level. <break time="0.3s"/> We'll make this a Beginner track.

<break time="0.4s"/>

Now add a description: <break time="0.3s"/> Learn Python basics for data science.

<break time="0.5s"/>

Click Create Track, <break time="0.4s"/> and there you go!

<break time="0.3s"/>

Your track is created.

<break time="0.6s"/>

Tracks let you organize courses into structured learning paths <break time="0.2s"/> at different skill levels.

<break time="0.3s"/>

Students can follow these tracks from beginner <break time="0.2s"/> to advanced.

<break time="0.5s"/>

Next, <break time="0.2s"/> we'll show you the AI assistant in action!'''
    },
    {
        'slide': 5,
        'title': 'AI Assistant - Natural Language Management',
        'text': '''Instead of filling out forms, <break time="0.3s"/> you can simply tell our AI assistant what you need.

<break time="0.5s"/>

Watch how easy it is!

<break time="0.5s"/>

Click the purple AI assistant button in the bottom right corner.

<break time="0.3s"/>

The chat panel slides up.

<break time="0.4s"/>

Now, <break time="0.3s"/> just describe what you want in plain English.

<break time="0.3s"/>

Type: <break time="0.3s"/> Create an intermediate track called Machine Learning Basics for the Data Science project.

<break time="0.6s"/>

The AI understands your request instantly!

<break time="0.4s"/>

It confirms the details <break time="0.2s"/> and creates the track for you.

<break time="0.5s"/>

No forms to fill out. <break time="0.3s"/> No dropdowns to navigate. <break time="0.3s"/> Just natural conversation.

<break time="0.6s"/>

The AI assistant can help you create projects, <break time="0.2s"/> manage tracks, <break time="0.2s"/> onboard instructors, <break time="0.2s"/> and generate course content.

<break time="0.4s"/>

It's like having an expert teammate <break time="0.3s"/> available twenty-four seven!

<break time="0.5s"/>

Next, <break time="0.2s"/> we'll show you how to add instructors to your organization.'''
    },
    {
        'slide': 6,
        'title': 'Adding Instructors',
        'text': '''Your instructors are your greatest asset.

<break time="0.4s"/>

Bring them onboard in seconds, <break time="0.3s"/> assign them to specific projects or tracks, <break time="0.3s"/> and they're instantly connected to your Slack or Teams channels <break time="0.2s"/> for seamless collaboration.

<break time="0.6s"/>

Whether it's co-developing courses with colleagues <break time="0.3s"/> or running independent programs, <break time="0.3s"/> everything integrates with the tools your team already uses.'''
    },
    {
        'slide': 7,
        'title': 'Instructor Dashboard',
        'text': '''Instructors have powerful AI tools at their fingertips!

<break time="0.5s"/>

Tell the system your learning objectives, <break time="0.2s"/> your target audience, <break time="0.2s"/> and your key topics.

<break time="0.5s"/>

Then watch as artificial intelligence generates a complete course structure, <break time="0.3s"/> suggested modules, <break time="0.3s"/> learning outcomes, <break time="0.3s"/> even quiz questions!

<break time="0.6s"/>

You review, <break time="0.2s"/> refine, <break time="0.2s"/> and approve.

<break time="0.5s"/>

What used to take days of curriculum design <break time="0.4s"/> now takes minutes.

<break time="0.5s"/>

And when you schedule live sessions?

<break time="0.4s"/>

Automatic Zoom or Teams integration means <break time="0.3s"/> one click launches your class!'''
    },
    {
        'slide': 8,
        'title': 'Course Content',
        'text': '''AI accelerates content creation!

<break time="0.5s"/>

Need lesson content?

<break time="0.3s"/>

Describe your topic and the AI generates a complete lesson draft. <break time="0.4s"/> You just add your expertise <break time="0.2s"/> and real-world examples.

<break time="0.6s"/>

Creating quizzes?

<break time="0.3s"/>

AI suggests questions based on your content: <break time="0.3s"/> multiple choice, <break time="0.2s"/> code challenges, <break time="0.2s"/> scenario-based problems.

<break time="0.5s"/>

You spend your time refining and personalizing, <break time="0.3s"/> not starting from scratch.

<break time="0.6s"/>

Upload presentations, <break time="0.2s"/> embed videos, <break time="0.2s"/> add code exercises with real-time feedback.

<break time="0.5s"/>

The AI accelerates creation. <break time="0.4s"/> You ensure quality.'''
    },
    {
        'slide': 9,
        'title': 'Enroll Students',
        'text': '''Your course is ready! <break time="0.3s"/> Now it's time to welcome your students.

<break time="0.5s"/>

One student? <break time="0.3s"/> Easy.

<break time="0.3s"/>

One hundred students? <break time="0.4s"/> Even easier!

<break time="0.5s"/>

Upload a CSV file <break time="0.3s"/> and enroll an entire locations in seconds.

<break time="0.4s"/>

Organize by section, <break time="0.2s"/> group by skill level, <break time="0.2s"/> track by semester.

<break time="0.5s"/>

However you teach, <break time="0.3s"/> we adapt.

<break time="0.4s"/>

Because managing students should be effortless, <break time="0.3s"/> not exhausting.'''
    },
    {
        'slide': 10,
        'title': 'Student Dashboard',
        'text': '''Now let's see what your students experience.

<break time="0.5s"/>

They log in <break time="0.3s"/> and immediately, <break time="0.3s"/> everything they need is right there.

<break time="0.4s"/>

Their courses, <break time="0.2s"/> their progress, <break time="0.2s"/> upcoming deadlines, <break time="0.2s"/> recent achievements.

<break time="0.5s"/>

No confusion. <break time="0.3s"/> No hunting for information.

<break time="0.4s"/>

Just a clear path forward <break time="0.3s"/> and the motivation to keep going.'''
    },
    {
        'slide': 11,
        'title': 'Course Browsing',
        'text': '''Students browse the catalog, <break time="0.2s"/> discover courses, <break time="0.2s"/> and enroll with one click.

<break time="0.5s"/>

The game changer for technical training?

<break time="0.5s"/>

When they hit a coding lesson, <break time="0.3s"/> professional development environments open right in their browser!

<break time="0.5s"/>

VSCode for web development. <break time="0.3s"/> PyCharm for Python. <break time="0.3s"/> JupyterLab for data science. <break time="0.3s"/> Full Linux terminal for system administration.

<break time="0.6s"/>

No installation. <break time="0.3s"/> No configuration. <break time="0.3s"/> No IT headaches!

<break time="0.6s"/>

This is why corporate training teams choose us! <break time="0.4s"/> Their developers learn with real professional tools, <break time="0.3s"/> no setup time wasted.'''
    },
    {
        'slide': 12,
        'title': 'Taking Quizzes',
        'text': '''Assessment shouldn't feel like a gotcha moment. <break time="0.4s"/> It should be a learning opportunity!

<break time="0.5s"/>

Our quiz system delivers multiple question formats: <break time="0.3s"/> multiple choice for quick checks, <break time="0.3s"/> coding challenges for hands-on validation, <break time="0.3s"/> short answer for deeper understanding.

<break time="0.6s"/>

But here's what matters most: <break time="0.5s"/> instant feedback!

<break time="0.4s"/>

Not just a score, <break time="0.3s"/> but detailed explanations <break time="0.3s"/> that turn mistakes into mastery.

<break time="0.5s"/>

Because real learning happens <break time="0.3s"/> when students understand why.'''
    },
    {
        'slide': 13,
        'title': 'Student Progress',
        'text': '''Progress should be visible <break time="0.3s"/> and celebrated!

<break time="0.5s"/>

Every quiz completed. <break time="0.3s"/> Every module mastered. <break time="0.3s"/> Every achievement unlocked.

<break time="0.5s"/>

Students see their journey unfold <break time="0.3s"/> in real time.

<break time="0.4s"/>

Completion rates, <break time="0.2s"/> quiz scores, <break time="0.2s"/> time invested. <break time="0.4s"/> It all adds up to something powerful: <break time="0.5s"/> proof of growth!

<break time="0.5s"/>

And that's what keeps them coming back.'''
    },
    {
        'slide': 14,
        'title': 'Instructor Analytics',
        'text': '''We go beyond basic LMS reporting!

<break time="0.5s"/>

Our AI-powered analytics don't just show you data. <break time="0.4s"/> They surface insights!

<break time="0.6s"/>

Which students are at risk of falling behind? <break time="0.3s"/> AI flags them automatically.

<break time="0.4s"/>

What content drives the most engagement? <break time="0.3s"/> AI identifies patterns across all your courses.

<break time="0.4s"/>

Which quiz questions are too easy or too hard? <break time="0.3s"/> AI analyzes performance trends <break time="0.3s"/> and suggests adjustments.

<break time="0.6s"/>

Export reports to Slack or Teams <break time="0.3s"/> so your entire training team stays informed.

<break time="0.5s"/>

This isn't just analytics. <break time="0.4s"/> It's intelligent course optimization!'''
    },
    {
        'slide': 15,
        'title': 'Summary & Next Steps',
        'text': '''So that's Course Creator Platform!

<break time="0.5s"/>

AI handles course development, <break time="0.2s"/> content generation, <break time="0.2s"/> and intelligent analytics.

<break time="0.4s"/>

Your team works inside Slack, <break time="0.2s"/> Teams, <break time="0.2s"/> and Zoom, <break time="0.3s"/> and everything integrates seamlessly.

<break time="0.6s"/>

Whether you're building corporate training programs <break time="0.3s"/> or teaching as an independent instructor, <break time="0.4s"/> we turn weeks of work <break time="0.3s"/> into minutes of guided setup.

<break time="0.7s"/>

Ready to see it in action?

<break time="0.4s"/>

Visit our site to get started!'''
    }
]


def check_api_key():
    """
    Verify API key is configured
    """
    if not ELEVENLABS_API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set")
        print()
        print("Please set your API key:")
        print("  1. Sign up at https://elevenlabs.io")
        print("  2. Get API key from https://elevenlabs.io/app/settings/api-keys")
        print("  3. Set environment variable:")
        print()
        print("     export ELEVENLABS_API_KEY='your_key_here'")
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
        print(f"Warning: Could not fetch voices: {e}")
        return []


def generate_audio_with_ssml(text, voice_id, output_path, slide_number):
    """
    Generate audio using ElevenLabs API with SSML enabled

    SSML SUPPORT:
    - <break time="Xs"/> - Pause for X seconds (max 3s per break)

    VOICE SETTINGS FOR EXPRESSIVENESS:
    - stability: 0.35 (lower = more emotional variation)
    - similarity_boost: 0.80 (voice quality)
    - style: 0.45 (higher = more expressive delivery)
    - use_speaker_boost: True (enhanced clarity)

    ARGS:
        text: Narration text with SSML markup
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

    # Wrap text in <speak> tags for SSML
    ssml_text = f'<speak>{text}</speak>'

    data = {
        'text': ssml_text,
        'model_id': 'eleven_turbo_v2',  # Supports SSML
        'voice_settings': {
            # EXPRESSIVENESS-OPTIMIZED SETTINGS:
            'stability': 0.35,        # Lower = more emotional variation and natural inflection
            'similarity_boost': 0.80, # Slightly lower for more natural variation
            'style': 0.45,            # Higher = more expressive, enthusiastic delivery
            'use_speaker_boost': True # Enhanced clarity and presence
        }
    }

    try:
        print(f"   Generating expressive audio for slide {slide_number}...", end=' ', flush=True)

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # Save audio file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        # Get file size for confirmation
        size_kb = output_path.stat().st_size / 1024
        print(f"Done ({size_kb:.1f}KB)")

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
                return generate_audio_with_ssml(text, voice_id, output_path, slide_number)
        return False

    except Exception as e:
        print(f"Failed")
        print(f"      Error: {e}")
        return False


def main():
    """
    Main execution function - generates expressive audio with SSML
    """
    print("=" * 70)
    print("ELEVENLABS EXPRESSIVE AUDIO GENERATION")
    print("With SSML Markup for Natural Pauses and Emphasis")
    print("=" * 70)
    print()

    # Check API key
    check_api_key()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Get available voices (optional - for informational purposes)
    print("Fetching available voices...")
    voices = get_available_voices()
    if voices:
        print(f"   Found {len(voices)} available voices")
    print()

    # Select voice (Charlotte - UK female, mid-20s, natural and expressive)
    selected_voice = 'charlotte'
    voice_id = VOICES[selected_voice]
    print(f"Selected voice: {selected_voice.title()} (UK Female, Mid-20s)")
    print(f"   Voice ID: {voice_id}")
    print()
    print("Expressive Voice Settings:")
    print("   Stability: 0.35 (more emotional variation)")
    print("   Style: 0.45 (more expressive delivery)")
    print("   Speaker Boost: Enabled (enhanced presence)")
    print()
    print("SSML Features Used:")
    print("   - <break time=\"Xs\"/> for dramatic pauses")
    print("   - Punctuation for natural prosody (!, ?)")
    print("   - Short sentences for impact")
    print()

    # Generate audio for all slides
    print("=" * 70)
    print("Generating Expressive Audio Files...")
    print("=" * 70)
    print()

    success_count = 0
    failed_count = 0

    for narration in EXPRESSIVE_NARRATIONS:
        slide_num = narration['slide']
        title = narration['title']
        text = narration['text']

        print(f"Slide {slide_num:02d}: {title}")

        # Output filename
        filename = f"slide_{slide_num:02d}_narration.mp3"
        output_path = OUTPUT_DIR / filename

        # Generate audio with SSML
        success = generate_audio_with_ssml(text, voice_id, output_path, slide_num)

        if success:
            success_count += 1
        else:
            failed_count += 1

        # Delay to avoid rate limiting
        time.sleep(1.0)

    # Summary
    print()
    print("=" * 70)
    print("AUDIO GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Summary:")
    print(f"   Total slides: {len(EXPRESSIVE_NARRATIONS)}")
    print(f"   Success: {success_count}")
    print(f"   Failed: {failed_count}")
    print()
    print(f"Audio files saved to: {OUTPUT_DIR.absolute()}")
    print()

    if failed_count > 0:
        print("Some files failed to generate. Check errors above.")
        print()

    # Next steps
    print("Next Steps:")
    print("   1. Review generated audio files for expressiveness")
    print("   2. Test audio playback in demo player")
    print("   3. Verify audio/video synchronization")
    print()
    print("To preview audio files:")
    print(f"   mpg123 {OUTPUT_DIR}/slide_01_narration.mp3")
    print()


if __name__ == '__main__':
    main()
