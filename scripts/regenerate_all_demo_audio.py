#!/usr/bin/env python3
"""
Regenerate ALL demo audio files with consistent Charlotte voice.

Uses ElevenLabs API with SSML markup for expressive narration.
All 20 slides use the same voice, model, and settings for consistency.
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
        'text': '''Welcome to THE Course Creator Platform! <break time="0.5s"/>
Built specifically for corporate training teams <break time="0.3s"/> and professional instructors <break time="0.3s"/> who need to create courses fast.
<break time="0.7s"/>
Our AI-powered system transforms what used to take weeks <break time="0.5s"/> into just minutes.
<break time="0.5s"/>
In the next slide, <break time="0.3s"/> we'll show you how to get started.'''
    },
    {
        'num': 2,
        'file': 'slide_02_narration.mp3',
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
        'num': 3,
        'file': 'slide_03_narration.mp3',
        'text': '''Let's log in as the organization admin we just created.
<break time="0.4s"/>
First, <break time="0.2s"/> navigate to the home page and click the Login button in the header.
<break time="0.3s"/>
Now, enter the email address: <break time="0.3s"/> sarah at acmelearning dot e-d-u.
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
        'num': 4,
        'file': 'slide_04_narration.mp3',
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
Your track is created.'''
    },
    {
        'num': 5,
        'file': 'slide_05_narration.mp3',
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
No forms to fill out. <break time="0.3s"/> No dropdowns to navigate. <break time="0.3s"/> Just natural conversation.'''
    },
    {
        'num': 6,
        'file': 'slide_06_narration.mp3',
        'text': '''Your instructors are your greatest asset.
<break time="0.4s"/>
Bring them onboard in seconds, <break time="0.3s"/> assign them to specific projects or tracks, <break time="0.3s"/> and they're instantly connected to your Slack or Teams channels <break time="0.2s"/> for seamless collaboration.
<break time="0.6s"/>
Whether it's co-developing courses with colleagues <break time="0.3s"/> or running independent programs, <break time="0.3s"/> everything integrates with the tools your team already uses.'''
    },
    {
        'num': 7,
        'file': 'slide_07_narration.mp3',
        'text': '''Instructors have powerful AI tools at their fingertips!
<break time="0.5s"/>
Tell the system your learning objectives, <break time="0.2s"/> your target audience, <break time="0.2s"/> and your key topics.
<break time="0.5s"/>
Then watch as artificial intelligence generates a complete course structure, <break time="0.3s"/> suggested modules, <break time="0.3s"/> learning outcomes, <break time="0.3s"/> even quiz questions!
<break time="0.6s"/>
You review, <break time="0.2s"/> refine, <break time="0.2s"/> and approve.
<break time="0.5s"/>
What used to take days of curriculum design <break time="0.4s"/> now takes minutes.'''
    },
    {
        'num': 8,
        'file': 'slide_08_narration.mp3',
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
The AI accelerates creation. <break time="0.4s"/> You ensure quality.'''
    },
    {
        'num': 9,
        'file': 'slide_09_narration.mp3',
        'text': '''Your course is ready! <break time="0.3s"/> Now it's time to welcome your students.
<break time="0.5s"/>
One student? <break time="0.3s"/> Easy.
<break time="0.3s"/>
One hundred students? <break time="0.4s"/> Even easier!
<break time="0.5s"/>
Upload a CSV file <break time="0.3s"/> and enroll an entire class in seconds.
<break time="0.4s"/>
However you teach, <break time="0.3s"/> we adapt.'''
    },
    {
        'num': 10,
        'file': 'slide_10_narration.mp3',
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
        'num': 11,
        'file': 'slide_11_narration.mp3',
        'text': '''Students browse the catalog, <break time="0.2s"/> discover courses, <break time="0.2s"/> and enroll with one click.
<break time="0.5s"/>
The game changer for technical training?
<break time="0.5s"/>
When they hit a coding lesson, <break time="0.3s"/> professional development environments open right in their browser!
<break time="0.5s"/>
VS Code for web development. <break time="0.3s"/> PyCharm for Python. <break time="0.3s"/> JupyterLab for data science.
<break time="0.6s"/>
No installation. <break time="0.3s"/> No configuration. <break time="0.3s"/> No IT headaches!
<break time="0.6s"/>
This is why corporate training teams choose us!'''
    },
    {
        'num': 12,
        'file': 'slide_12_narration.mp3',
        'text': '''Assessment shouldn't feel like a gotcha moment. <break time="0.4s"/> It should be a learning opportunity!
<break time="0.5s"/>
Our quiz system delivers multiple question formats: <break time="0.3s"/> multiple choice for quick checks, <break time="0.3s"/> coding challenges for hands-on validation, <break time="0.3s"/> short answer for deeper understanding.
<break time="0.6s"/>
But here's what matters most: <break time="0.5s"/> instant feedback!
<break time="0.4s"/>
Not just a score, <break time="0.3s"/> but detailed explanations <break time="0.3s"/> that turn mistakes into mastery.'''
    },
    {
        'num': 13,
        'file': 'slide_13_narration.mp3',
        'text': '''Progress should be visible <break time="0.3s"/> and celebrated!
<break time="0.5s"/>
Every quiz completed. <break time="0.3s"/> Every module mastered. <break time="0.3s"/> Every achievement unlocked.
<break time="0.5s"/>
Students see their journey unfold <break time="0.3s"/> in real time.
<break time="0.4s"/>
Completion rates, <break time="0.2s"/> quiz scores, <break time="0.2s"/> time invested. <break time="0.4s"/> It all adds up to something powerful: <break time="0.5s"/> proof of growth!'''
    },
    {
        'num': 14,
        'file': 'slide_14_narration.mp3',
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
This isn't just analytics. <break time="0.4s"/> It's intelligent course optimization!'''
    },
    {
        'num': 15,
        'file': 'slide_15_learning_analytics_narration.mp3',
        'text': '''But students want more than just progress bars!
<break time="0.5s"/>
Our Learning Analytics Dashboard gives them deep insights.
<break time="0.4s"/>
See skill mastery across different topics <break time="0.3s"/> with visual radar charts.
<break time="0.3s"/>
Track learning velocity <break time="0.3s"/> to understand how quickly concepts are being absorbed.
<break time="0.4s"/>
View session activity patterns <break time="0.3s"/> to optimize study habits.
<break time="0.5s"/>
It's not just about completing courses. <break time="0.4s"/> It's about truly understanding your learning journey!'''
    },
    {
        'num': 16,
        'file': 'slide_16_instructor_insights_narration.mp3',
        'text': '''Now let's see the Instructor Insights Dashboard!
<break time="0.4s"/>
This is where AI truly shines.
<break time="0.5s"/>
Course performance metrics show completion rates, <break time="0.2s"/> engagement levels, <break time="0.2s"/> and average scores at a glance.
<break time="0.4s"/>
Student engagement widgets reveal who's thriving <break time="0.3s"/> and who needs support.
<break time="0.5s"/>
And the best part? <break time="0.4s"/> AI-powered teaching recommendations!
<break time="0.4s"/>
The system analyzes patterns across all your courses <break time="0.3s"/> and suggests specific improvements.'''
    },
    {
        'num': 17,
        'file': 'slide_17_integrations_narration.mp3',
        'text': '''Your organization doesn't exist in isolation!
<break time="0.4s"/>
Let's set up integrations.
<break time="0.4s"/>
Connect Slack <break time="0.3s"/> for instant notifications when students complete courses.
<break time="0.4s"/>
Link your Google Calendar or Outlook <break time="0.3s"/> for automatic scheduling.
<break time="0.4s"/>
Set up OAuth connections <break time="0.3s"/> for single sign-on with your existing identity provider.
<break time="0.4s"/>
LTI integration lets you embed our courses <break time="0.3s"/> directly in your existing LMS.
<break time="0.5s"/>
Everything works together seamlessly!'''
    },
    {
        'num': 18,
        'file': 'slide_18_accessibility_narration.mp3',
        'text': '''Accessibility isn't an afterthought. <break time="0.4s"/> It's built into everything we do!
<break time="0.5s"/>
Every user can customize their experience.
<break time="0.4s"/>
Adjust font sizes <break time="0.2s"/> from default to extra large.
<break time="0.3s"/>
Switch between light, <break time="0.2s"/> dark, <break time="0.2s"/> or high contrast color schemes.
<break time="0.4s"/>
Enable screen reader optimizations.
<break time="0.3s"/>
Configure keyboard shortcuts <break time="0.3s"/> to match your workflow.
<break time="0.5s"/>
We're committed to WCAG 2.1 double-A compliance <break time="0.3s"/> because learning should be accessible to everyone!'''
    },
    {
        'num': 19,
        'file': 'slide_19_mobile_narration.mp3',
        'text': '''Learning doesn't stop when you leave your desk!
<break time="0.5s"/>
Our mobile experience brings the full platform to any device.
<break time="0.4s"/>
Responsive design adapts beautifully <break time="0.3s"/> to phones and tablets.
<break time="0.5s"/>
And the game changer? <break time="0.4s"/> Offline sync!
<break time="0.4s"/>
Download courses to learn on the go, <break time="0.3s"/> even without internet.
<break time="0.4s"/>
Your progress syncs automatically <break time="0.3s"/> when you're back online.
<break time="0.5s"/>
Train your team anywhere, <break time="0.3s"/> anytime. <break time="0.4s"/> That's the power of mobile-first design!'''
    },
    {
        'num': 20,
        'file': 'slide_20_summary_narration.mp3',
        'text': '''So that's Course Creator Platform! <break time="0.5s"/>
AI handles course development, <break time="0.2s"/> content generation, <break time="0.2s"/> and intelligent analytics.
<break time="0.4s"/>
Deep learning insights for both students and instructors.
<break time="0.5s"/>
Third-party integrations with Slack, <break time="0.2s"/> Teams, <break time="0.2s"/> Zoom, <break time="0.2s"/> and your existing systems.
<break time="0.4s"/>
Full accessibility support <break time="0.2s"/> and mobile-first design.
<break time="0.6s"/>
Whether you're building corporate training programs <break time="0.3s"/> or teaching as an independent instructor, <break time="0.4s"/> we turn weeks of work <break time="0.3s"/> into minutes of guided setup.
<break time="0.7s"/>
Ready to see it in action?
<break time="0.4s"/>
Visit our site to get started!'''
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
    data = {
        'text': f'<speak>{slide["text"]}</speak>',
        'model_id': 'eleven_turbo_v2',
        'voice_settings': {
            'stability': 0.35,
            'similarity_boost': 0.80,
            'style': 0.45,
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
        sys.exit(1)

    print(f"Regenerating all {len(SLIDES)} demo audio files with Charlotte voice...")
    print(f"Output: {OUTPUT_DIR}")
    print()

    for slide in SLIDES:
        num = slide['num']
        fname = slide['file']
        print(f"  Slide {num:02d}: {fname}...", end=' ', flush=True)
        try:
            size = generate_audio(slide)
            print(f"OK ({size:.0f}KB)")
        except Exception as e:
            print(f"FAILED: {e}")

        # Rate limit protection
        time.sleep(1.0)

    print()
    print("Done! All audio regenerated with Charlotte voice.")


if __name__ == '__main__':
    main()
