#!/usr/bin/env python3
"""
Generate Demo Slides for Platform Enhancements 9-13

BUSINESS PURPOSE:
Creates video placeholders and audio narration for the 5 new enhancement
slides showcasing Learning Analytics, Instructor Insights, Integrations,
Accessibility, and Mobile Experience features.

TECHNICAL APPROACH:
1. Uses ffmpeg to create placeholder videos with title cards
2. Uses ElevenLabs API to generate professional narration
3. Outputs files to frontend-react/public/demo/ directories

USAGE:
    python3 scripts/generate_enhancement_demo_slides.py
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'

# Output directories
VIDEO_DIR = Path('/home/bbrelin/course-creator/frontend-react/public/demo/videos')
AUDIO_DIR = Path('/home/bbrelin/course-creator/frontend-react/public/demo/audio')

# Voice configuration (Charlotte - UK female, mid-20s)
VOICE_ID = 'XB0fDUnXU5powFXDhCwa'

# New enhancement slides to generate
ENHANCEMENT_SLIDES = [
    {
        'slide_num': 15,
        'title': 'Learning Analytics Dashboard',
        'video_filename': 'slide_15_learning_analytics.mp4',
        'audio_filename': 'slide_15_learning_analytics_narration.mp3',
        'duration': 32,
        'color': '#2196F3',  # Blue
        'narration': "But students want more than just progress bars! Our Learning Analytics Dashboard gives them deep insights. See skill mastery across different topics with visual radar charts. Track learning velocity to understand how quickly concepts are being absorbed. View session activity patterns to optimize study habits. Monitor learning path progress through multi-course tracks. Students can identify their strengths and areas for improvement. It's not just about completing courses. It's about truly understanding your learning journey!"
    },
    {
        'slide_num': 16,
        'title': 'Instructor Insights Dashboard',
        'video_filename': 'slide_16_instructor_insights.mp4',
        'audio_filename': 'slide_16_instructor_insights_narration.mp3',
        'duration': 35,
        'color': '#9C27B0',  # Purple
        'narration': "Now let's see the Instructor Insights Dashboard! This is where AI truly shines. Course performance metrics show completion rates, engagement levels, and average scores at a glance. Student engagement widgets reveal who's thriving and who needs support. Content effectiveness charts identify which lessons drive the most learning. And the best part? AI-powered teaching recommendations! The system analyzes patterns across all your courses and suggests specific improvements. Maybe a lesson needs more examples. Maybe a quiz is too difficult. The AI tells you exactly what to optimize!"
    },
    {
        'slide_num': 17,
        'title': 'Third-Party Integrations',
        'video_filename': 'slide_17_integrations.mp4',
        'audio_filename': 'slide_17_integrations_narration.mp3',
        'duration': 38,
        'color': '#00BCD4',  # Cyan
        'narration': "Your organization doesn't exist in isolation! Let's set up integrations. Click the Integrations tab. Here you can connect Slack for instant notifications when students complete courses. Link your Google Calendar or Outlook for automatic scheduling. Set up OAuth connections for single sign-on with your existing identity provider. Configure webhooks to trigger your own automation workflows. LTI integration lets you embed our courses directly in your existing LMS. Everything works together seamlessly!"
    },
    {
        'slide_num': 18,
        'title': 'Accessibility Settings',
        'video_filename': 'slide_18_accessibility.mp4',
        'audio_filename': 'slide_18_accessibility_narration.mp3',
        'duration': 30,
        'color': '#4CAF50',  # Green
        'narration': "Accessibility isn't an afterthought. It's built into everything we do! Every user can customize their experience. Adjust font sizes from default to extra large. Switch between light, dark, or high contrast color schemes. Reduce motion for users sensitive to animations. Choose your preferred focus indicator style. Enable screen reader optimizations. Configure keyboard shortcuts to match your workflow. Skip links are always available for keyboard navigation. We're committed to WCAG 2.1 double-A compliance because learning should be accessible to everyone!"
    },
    {
        'slide_num': 19,
        'title': 'Mobile Experience',
        'video_filename': 'slide_19_mobile.mp4',
        'audio_filename': 'slide_19_mobile_narration.mp3',
        'duration': 28,
        'color': '#FF9800',  # Orange
        'narration': "Learning doesn't stop when you leave your desk! Our mobile experience brings the full platform to any device. Responsive design adapts beautifully to phones and tablets. Swipe through course cards with touch gestures. Pull down to refresh for the latest content. And the game changer? Offline sync! Download courses to learn on the go, even without internet. Your progress syncs automatically when you're back online. Train your team anywhere, anytime. That's the power of mobile-first design!"
    }
]


def create_placeholder_video(slide_info):
    """
    Create a placeholder video with title card using ffmpeg

    ARGS:
        slide_info: Dictionary with slide configuration

    RETURNS: True if successful, False otherwise
    """
    output_path = VIDEO_DIR / slide_info['video_filename']
    duration = slide_info['duration']
    title = slide_info['title']
    color = slide_info['color']
    slide_num = slide_info['slide_num']

    # Text to display
    main_text = title
    subtitle = f"Enhancement Feature - Slide {slide_num}"

    print(f"   Creating placeholder video for slide {slide_num}...", end=' ', flush=True)

    try:
        # ffmpeg command to create a video with colored background and text
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c={color.replace("#", "0x")}:size=1920x1080:duration={duration}:rate=30',
            '-vf', (
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"text='{main_text}':"
                f"fontcolor=white:fontsize=72:"
                f"x=(w-text_w)/2:y=(h-text_h)/2-50,"
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"text='{subtitle}':"
                f"fontcolor=white:fontsize=36:"
                f"x=(w-text_w)/2:y=(h-text_h)/2+50,"
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"text='Course Creator Platform':"
                f"fontcolor=white@0.7:fontsize=24:"
                f"x=(w-text_w)/2:y=h-60"
            ),
            '-c:v', 'libx264',
            '-profile:v', 'baseline',
            '-level', '3.1',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✓ ({size_mb:.1f}MB)")
            return True
        else:
            print(f"✗")
            print(f"      Error: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"✗")
        print(f"      Error: {e}")
        return False


def generate_audio(slide_info):
    """
    Generate audio narration using ElevenLabs API

    ARGS:
        slide_info: Dictionary with slide configuration

    RETURNS: True if successful, False otherwise
    """
    if not ELEVENLABS_API_KEY:
        print(f"   ⚠️  Skipping audio (no API key)")
        return False

    output_path = AUDIO_DIR / slide_info['audio_filename']
    text = slide_info['narration']
    slide_num = slide_info['slide_num']

    url = f'{ELEVENLABS_API_URL}/text-to-speech/{VOICE_ID}'

    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': ELEVENLABS_API_KEY
    }

    data = {
        'text': text,
        'model_id': 'eleven_turbo_v2',
        'voice_settings': {
            'stability': 0.40,
            'similarity_boost': 0.85,
            'style': 0.25,
            'use_speaker_boost': True
        }
    }

    try:
        print(f"   Generating audio for slide {slide_num}...", end=' ', flush=True)

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        size_kb = output_path.stat().st_size / 1024
        print(f"✓ ({size_kb:.1f}KB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"✗")
        if e.response.status_code == 401:
            print("      Invalid API key")
        elif e.response.status_code == 429:
            print("      Rate limit - waiting 60s...")
            time.sleep(60)
            return generate_audio(slide_info)
        else:
            print(f"      HTTP Error: {e}")
        return False

    except Exception as e:
        print(f"✗")
        print(f"      Error: {e}")
        return False


def main():
    """Main execution function"""
    print("=" * 70)
    print("🎬 ENHANCEMENT SLIDE GENERATION")
    print("   Generating demo slides for Enhancements 9-13")
    print("=" * 70)
    print()

    # Ensure output directories exist
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📁 Video output: {VIDEO_DIR}")
    print(f"📁 Audio output: {AUDIO_DIR}")
    print()

    # Check for ElevenLabs API key
    if ELEVENLABS_API_KEY:
        print("🎤 ElevenLabs API key: Found")
    else:
        print("⚠️  ElevenLabs API key: Not set (audio will be skipped)")
        print("   Set ELEVENLABS_API_KEY environment variable to generate audio")
    print()

    # Generate slides
    print("=" * 70)
    print("Generating enhancement slides...")
    print("=" * 70)
    print()

    video_success = 0
    video_failed = 0
    audio_success = 0
    audio_failed = 0

    for slide in ENHANCEMENT_SLIDES:
        print(f"📝 Slide {slide['slide_num']}: {slide['title']}")

        # Create video
        if create_placeholder_video(slide):
            video_success += 1
        else:
            video_failed += 1

        # Generate audio
        if generate_audio(slide):
            audio_success += 1
        else:
            audio_failed += 1

        # Delay between API calls
        if ELEVENLABS_API_KEY:
            time.sleep(0.5)

        print()

    # Summary
    print("=" * 70)
    print("✅ GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"📊 Summary:")
    print(f"   • Videos: {video_success} success, {video_failed} failed")
    print(f"   • Audio:  {audio_success} success, {audio_failed} failed")
    print()
    print("📋 Next Steps:")
    print("   1. Review generated placeholder videos")
    print("   2. Replace with actual UI screen recordings")
    print("   3. Test demo player with new slides")
    print()


if __name__ == '__main__':
    main()
