#!/usr/bin/env python3
"""
Regenerate ALL demo audio files with consistent Charlotte voice.

Uses ElevenLabs API with natural conversational narration.
All 20 slides use the same voice, model, and settings for consistency.

Voice: Charlotte (UK Female, mid-20s) - warm, professional, conversational
Model: eleven_turbo_v2 (supports SSML for phoneme corrections)
Settings: stability=0.50, similarity=0.75, style=0.15 for natural delivery
"""

import os
import sys
import time
import requests

API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
VOICE_ID = 'XB0fDUnXU5powFXDhCwa'  # Charlotte - UK Female, mid-20s
API_URL = 'https://api.elevenlabs.io/v1/text-to-speech'
OUTPUT_DIR = '/home/bbrelin/course-creator/frontend-react/public/demo/audio'

SLIDES = [
    {
        'num': 1,
        'file': 'slide_01_narration.mp3',
        'text': """Welcome to Course Creator Platform. This is built for people who create training... corporate teams, professional instructors, anyone who's tired of spending weeks building courses from scratch. What if you could do all of that in minutes instead? That's exactly what our AI-powered system delivers. Let me show you how it works."""
    },
    {
        'num': 2,
        'file': 'slide_02_narration.mp3',
        'text': """Getting started is really straightforward. Head to the home page and click Register Organization. You'll see a clean form... just fill in your organization name, website, and a short description of what you do. Add your contact details, business email, address, the basics. Then set up your admin account with a username and password. Hit submit and... that's it. Your organization is live and ready to go. Now let me show you what happens next."""
    },
    {
        'num': 3,
        'file': 'slide_03_narration.mp3',
        'text': """Let's log in as the organization admin we just created. Go to the home page, click Login, and enter the credentials. For this demo, that's sarah at <phoneme alphabet="cmu-arpabet" ph="AE1 K M IY0">Acme</phoneme> Learning dot e-d-u. Type in the password and sign in.

And here we are... the organization admin dashboard. Think of this as your command center. Everything you need to manage your training program lives right here.

See that purple button in the bottom right? That's our AI assistant. You can manage your entire organization just by talking to it in plain English... but we'll get to that in a moment.

First, let's create a project. Projects are how you organize courses and content. Click Create New Project, give it a name and description, and hit Create. Done. You can always come back to edit or delete it later.

Now watch what happens when we switch projects using this dropdown. Select Data Science Foundations and... the dashboard updates instantly. You can see your Tracks, those are learning paths. Your Instructors, showing your teaching team. And Students, total enrollment across the board.

Below the metrics you've got three tabs: Tracks for managing learning paths, Members for your team, and Settings for configuration.

Next up... creating tracks for your project."""
    },
    {
        'num': 4,
        'file': 'slide_04_narration.mp3',
        'text': """Now let's create a learning track. We're already on the Tracks tab from the previous step, so click Create New Track.

Here's the form. Start with the track name... we'll call this one Python Fundamentals. Choose the project, Data Science Foundations. Set the level to Beginner. And add a quick description: Learn Python basics for data science.

Click Create Track and... there you go. Your track is ready. That's all it takes... name it, assign it to a project, set the level, and you're done."""
    },
    {
        'num': 5,
        'file': 'slide_05_narration.mp3',
        'text': """Here's where it gets interesting. Instead of filling out forms, you can just tell our AI assistant what you need.

Click that purple button in the bottom right corner. The chat panel slides open. Now just type what you want in plain English: Create an intermediate track called Machine Learning Basics for the Data Science project.

And watch... the AI understands exactly what you mean. It confirms the details and creates the track right there. No forms. No dropdowns. No hunting through menus. Just a natural conversation.

This works for creating courses, enrolling students, pulling up reports... pretty much anything you'd normally do through the interface."""
    },
    {
        'num': 6,
        'file': 'slide_06_narration.mp3',
        'text': """Your instructors are your greatest asset, so bringing them onboard should be effortless. Add them in seconds, assign them to specific projects or tracks, and they're instantly connected to your Slack or Teams channels for real-time collaboration. Whether they're co-developing courses with colleagues or running their own independent programs, everything integrates with the tools your team already uses."""
    },
    {
        'num': 7,
        'file': 'slide_07_narration.mp3',
        'text': """Here's what instructors see when they log in. They've got powerful AI tools right at their fingertips. Tell the system your learning objectives, target audience, and key topics... and watch it generate a complete course structure. Modules, learning outcomes, even quiz questions, all created in seconds.

You review it, refine it, make it yours. What used to take days of curriculum design now takes minutes. And when you schedule live sessions, automatic Zoom or Teams integration means one click launches your class."""
    },
    {
        'num': 8,
        'file': 'slide_08_narration.mp3',
        'text': """This is where AI really shines for content creation. Need a lesson? Just describe your topic and the AI drafts a complete lesson for you. Add your expertise and real-world examples to make it yours.

Quizzes? The AI generates questions based on your content... multiple choice, coding challenges, scenario-based problems. You spend your time refining and personalizing, not starting from a blank page.

Upload presentations, embed videos, add code exercises with real-time feedback. The AI handles the heavy lifting so you can focus on what matters... the quality of the learning experience."""
    },
    {
        'num': 9,
        'file': 'slide_09_narration.mp3',
        'text': """Your course is ready, so now it's time to bring in your students. And enrollment is incredibly flexible.

Got one student? Just enter their email and they're in. A hundred students? Upload a CSV file and the whole class is enrolled in seconds. No manual data entry at all.

You can organize them however makes sense for your program... by section, skill level, semester, department, whatever works. The system adapts to your workflow, not the other way around.

Because honestly... managing students should be the easy part, not the time-consuming part."""
    },
    {
        'num': 10,
        'file': 'slide_10_narration.mp3',
        'text': """Now let's see what the experience looks like from a student's perspective. They log in and immediately... everything they need is right here. Their courses, their progress, upcoming deadlines, recent achievements. There's no confusion and no searching around. Just a clean, clear path forward and the motivation to keep learning."""
    },
    {
        'num': 11,
        'file': 'slide_11_narration.mp3',
        'text': """Students can browse the catalog, find courses they're interested in, and enroll with a single click. But here's where it gets really exciting for technical training.

When they open a coding lesson, a professional development environment launches right in their browser. VS Code for web development. PyCharm for Python. JupyterLab for data science. Full Linux terminal for system administration.

No installation. No configuration headaches. No waiting for IT to set things up. Developers learn with real professional tools from day one."""
    },
    {
        'num': 12,
        'file': 'slide_12_narration.mp3',
        'text': """Assessment shouldn't feel like a trap... it should be a genuine learning experience.

Our quiz system supports multiple formats. Multiple choice for quick knowledge checks, coding challenges for hands-on skill validation, and short answers for deeper understanding.

But what really makes the difference is instant, detailed feedback. Not just a score... actual explanations that help students understand what they got wrong and why. That's how mistakes turn into real learning."""
    },
    {
        'num': 13,
        'file': 'slide_13_narration.mp3',
        'text': """Progress should be visible and worth celebrating. Every quiz completed, every module mastered, every milestone reached... students see it all unfold in real time.

Completion rates, quiz scores, time invested... it adds up to something meaningful. Proof of growth. And that sense of progress? That's what keeps people coming back."""
    },
    {
        'num': 14,
        'file': 'slide_14_narration.mp3',
        'text': """We go well beyond basic LMS reporting. Our AI-powered analytics don't just show you numbers... they surface actual insights.

Which students are falling behind? The system flags them automatically. What content drives the most engagement? AI spots the patterns across all your courses. Which quiz questions are too easy or too hard? The system analyzes performance trends and recommends adjustments.

You can export reports directly to Slack or Teams so your whole training team stays in the loop. This isn't just analytics... it's intelligent course optimization."""
    },
    {
        'num': 15,
        'file': 'slide_15_learning_analytics_narration.mp3',
        'text': """Students want more than just a progress bar, and this dashboard delivers.

The Learning Analytics Dashboard gives them genuinely useful insights into their own learning. Skill mastery shows up as visual radar charts... you can immediately see your strengths and where you need more work. Learning velocity tells you how quickly you're absorbing new concepts. Session activity patterns help you figure out when you learn best and optimize your study habits.

And for multi-course tracks, you can follow your progress through the entire learning path, not just one course at a time.

It's not about just finishing courses. It's about understanding where you actually stand."""
    },
    {
        'num': 16,
        'file': 'slide_16_instructor_insights_narration.mp3',
        'text': """Now let's look at the Instructor Insights Dashboard... this is where AI really earns its keep.

At a glance, you can see course performance metrics: completion rates, engagement levels, average scores. Student engagement widgets show you who's thriving and who might need some extra support. Content effectiveness charts highlight which lessons are driving the most actual learning.

But the best part? AI-powered teaching recommendations. The system looks at patterns across all your courses and tells you specifically what to improve. Maybe a lesson needs more worked examples. Maybe a quiz is discouraging students because it's too difficult. The AI identifies these issues and suggests concrete changes.

That's the kind of insight that used to take weeks of manual analysis."""
    },
    {
        'num': 17,
        'file': 'slide_17_integrations_narration.mp3',
        'text': """Your organization doesn't work in isolation, and your learning platform shouldn't either.

Click the Integrations tab and you can connect everything your team already uses. Slack for instant notifications when students hit milestones. Google Calendar or Outlook for automatic scheduling. OAuth connections for single sign-on with your existing identity provider. Webhooks to trigger your own custom automation workflows.

And if you're already running another learning management system, LTI integration lets you embed our courses directly into it.

The whole point is seamless connectivity... your training platform working with your tools, not competing with them."""
    },
    {
        'num': 18,
        'file': 'slide_18_accessibility_narration.mp3',
        'text': """Accessibility isn't something we bolted on at the end... it's baked into every part of the platform.

Every user can personalize their experience. Font sizes go from default up to extra large. Color schemes include light, dark, and high contrast options. You can reduce motion for anyone sensitive to animations, choose your preferred focus indicator style, and enable screen reader optimizations.

Keyboard shortcuts are fully configurable to match how you like to work, and skip links are always there for keyboard navigation.

We're committed to WCAG 2.1 double-A compliance across the entire platform. Because if your training isn't accessible to everyone on your team, it isn't really working for your organization."""
    },
    {
        'num': 19,
        'file': 'slide_19_mobile_narration.mp3',
        'text': """Learning doesn't stop when someone leaves their desk, and the platform is built with that in mind.

The entire experience is fully responsive... it adapts to phones and tablets seamlessly. Swipe through course cards, pull down to refresh, all the touch gestures you'd expect.

But here's the real game changer: offline sync. Your team can download courses and learn on the go, even without an internet connection. Progress syncs automatically the moment they're back online.

Train your people anywhere, anytime, on any device. That's not a nice-to-have... for a lot of organizations, that's the feature that makes everything else possible."""
    },
    {
        'num': 20,
        'file': 'slide_20_summary_narration.mp3',
        'text': """So that's Course Creator Platform. Let me recap what we've covered.

AI handles the heavy lifting... course development, content generation, and intelligent analytics that actually help you improve. Deep learning insights for both students and instructors. Seamless integrations with Slack, Teams, Zoom, and your existing systems. Full accessibility support. Mobile-first design with offline learning.

Whether you're building corporate training programs or teaching independently, this platform turns what used to take weeks of manual work into minutes of guided setup.

So... ready to try it yourself? Head to our site, register your organization, and see how it works for your team."""
    },
]


def generate_audio(slide):
    """Generate audio for a single slide via ElevenLabs API."""
    url = f'{API_URL}/{VOICE_ID}'
    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': API_KEY
    }

    # Wrap in <speak> tags for SSML support (needed for phoneme in slide 3)
    text = f'<speak>{slide["text"]}</speak>'

    data = {
        'text': text,
        'model_id': 'eleven_turbo_v2',
        'voice_settings': {
            'stability': 0.50,
            'similarity_boost': 0.75,
            'style': 0.15,
            'use_speaker_boost': True
        }
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    output_path = os.path.join(OUTPUT_DIR, slide['file'])
    with open(output_path, 'wb') as f:
        f.write(response.content)

    size_kb = len(response.content) / 1024
    return size_kb


def main():
    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set")
        print("Set it with: export ELEVENLABS_API_KEY=your_key_here")
        sys.exit(1)

    print(f"Regenerating all {len(SLIDES)} demo audio files with Charlotte voice...")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Voice settings: stability=0.50, similarity=0.75, style=0.15")
    print()

    for slide in SLIDES:
        num = slide['num']
        fname = slide['file']
        print(f"  Slide {num:02d}: {fname}...", end=' ', flush=True)
        try:
            size = generate_audio(slide)
            print(f"OK ({size:.0f}KB)")
        except requests.exceptions.HTTPError as e:
            print(f"FAILED: {e}")
            if e.response is not None:
                print(f"           Response: {e.response.text[:200]}")
        except Exception as e:
            print(f"FAILED: {e}")

        # Rate limit protection
        time.sleep(1.0)

    print()
    print("Done! All audio regenerated with Charlotte voice.")
    print("Next steps: check durations with ffprobe and update DemoPlayer.tsx")


if __name__ == '__main__':
    main()
