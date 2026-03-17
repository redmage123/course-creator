"""
Demo Narration Scripts with SSML Markup

BUSINESS REQUIREMENT:
Provide expressive, enthusiastic narrations for demo screencasts using
Speech Synthesis Markup Language (SSML) for natural speech patterns.

SSML FEATURES USED:
- <break time="Xs"/> - Strategic pauses for emphasis (max 3s for ElevenLabs)
- Punctuation for natural rhythm (!, ?, ...)
- Short sentences for impact
- Questions for engagement

VOICE SETTINGS (ElevenLabs - Optimized for Expressiveness):
- stability: 0.30 (lower = more emotional variation)
- similarity_boost: 0.85 (natural voice quality)
- style: 0.50 (higher = more expressive delivery)
- use_speaker_boost: True (enhanced clarity)
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NarrationSegment:
    """A segment of narration with timing info."""
    text: str
    start_time: float  # When to start this segment (seconds)
    duration: float    # How long this segment takes


@dataclass
class SlideNarration:
    """Complete narration for a demo slide."""
    slide_id: int
    title: str
    ssml_text: str
    plain_text: str
    duration_seconds: float
    segments: List[NarrationSegment]


# Slide 1: Platform Introduction (15s)
SLIDE_01_NARRATION = SlideNarration(
    slide_id=1,
    title="Platform Introduction",
    duration_seconds=15,
    ssml_text="""
<speak>
Welcome to the Course Creator Platform! <break time="0.5s"/>

This is where training transformation begins. <break time="0.3s"/>

With AI-powered content generation, <break time="0.2s"/>
interactive coding labs, <break time="0.2s"/>
and real-time analytics... <break time="0.4s"/>

You can create world-class training programs in minutes, not months! <break time="0.5s"/>

Ready to see what's possible? <break time="0.3s"/>
Let's dive in!
</speak>
""",
    plain_text="Welcome to the Course Creator Platform! This is where training transformation begins. With AI-powered content generation, interactive coding labs, and real-time analytics, you can create world-class training programs in minutes, not months! Ready to see what's possible? Let's dive in!",
    segments=[
        NarrationSegment("Welcome to the Course Creator Platform!", 0, 2.5),
        NarrationSegment("This is where training transformation begins.", 3, 2),
        NarrationSegment("With AI-powered content generation, interactive coding labs, and real-time analytics...", 5.5, 4),
        NarrationSegment("You can create world-class training programs in minutes, not months!", 10, 3),
        NarrationSegment("Ready to see what's possible? Let's dive in!", 13.5, 1.5),
    ]
)

# Slide 2: Organization Registration (25s)
SLIDE_02_NARRATION = SlideNarration(
    slide_id=2,
    title="Organization Registration",
    duration_seconds=25,
    ssml_text="""
<speak>
Getting started is incredibly easy! <break time="0.4s"/>

Just head to the organization registration page... <break time="0.5s"/>

Enter your organization name... <break time="0.3s"/>
That's Acme Training Corp! <break time="0.4s"/>

Add your admin email and name... <break time="0.3s"/>

Choose a secure password... <break time="0.5s"/>

And that's it! <break time="0.3s"/>

In just seconds, you've created your organization's training hub! <break time="0.5s"/>

No complex setup. <break time="0.2s"/>
No IT department needed. <break time="0.3s"/>
Just start creating amazing courses!
</speak>
""",
    plain_text="Getting started is incredibly easy! Just head to the organization registration page. Enter your organization name - that's Acme Training Corp! Add your admin email and name. Choose a secure password. And that's it! In just seconds, you've created your organization's training hub! No complex setup. No IT department needed. Just start creating amazing courses!",
    segments=[
        NarrationSegment("Getting started is incredibly easy!", 0, 2),
        NarrationSegment("Just head to the organization registration page...", 2.5, 2.5),
        NarrationSegment("Enter your organization name - that's Acme Training Corp!", 5.5, 3),
        NarrationSegment("Add your admin email and name...", 9, 2),
        NarrationSegment("Choose a secure password...", 11.5, 2),
        NarrationSegment("And that's it!", 14, 1.5),
        NarrationSegment("In just seconds, you've created your organization's training hub!", 16, 3),
        NarrationSegment("No complex setup. No IT department needed. Just start creating amazing courses!", 20, 5),
    ]
)

# Slide 3: Organization Admin Dashboard (30s)
SLIDE_03_NARRATION = SlideNarration(
    slide_id=3,
    title="Organization Admin Dashboard",
    duration_seconds=30,
    ssml_text="""
<speak>
Now let's log in as an Organization Admin! <break time="0.5s"/>

This is your command center! <break time="0.4s"/>

Look at this beautiful dashboard... <break time="0.3s"/>
Everything you need, right at your fingertips! <break time="0.5s"/>

The Members tab lets you manage your team... <break time="0.3s"/>
Add instructors, invite students, assign roles! <break time="0.5s"/>

And the Projects tab? <break time="0.3s"/>
This is where you organize all your training initiatives! <break time="0.4s"/>

Create projects for different departments... <break time="0.2s"/>
Different skill tracks... <break time="0.2s"/>
Different learning paths! <break time="0.5s"/>

Total control. <break time="0.2s"/>
Total visibility. <break time="0.3s"/>
Total awesome!
</speak>
""",
    plain_text="Now let's log in as an Organization Admin! This is your command center! Look at this beautiful dashboard - everything you need, right at your fingertips! The Members tab lets you manage your team. Add instructors, invite students, assign roles! And the Projects tab? This is where you organize all your training initiatives! Create projects for different departments, different skill tracks, different learning paths! Total control. Total visibility. Total awesome!",
    segments=[
        NarrationSegment("Now let's log in as an Organization Admin!", 0, 2.5),
        NarrationSegment("This is your command center!", 3, 1.5),
        NarrationSegment("Look at this beautiful dashboard - everything you need, right at your fingertips!", 5, 3.5),
        NarrationSegment("The Members tab lets you manage your team. Add instructors, invite students, assign roles!", 9, 4),
        NarrationSegment("And the Projects tab? This is where you organize all your training initiatives!", 14, 4),
        NarrationSegment("Create projects for different departments, different skill tracks, different learning paths!", 19, 4.5),
        NarrationSegment("Total control. Total visibility. Total awesome!", 25, 5),
    ]
)

# Slide 4: Creating Training Tracks (25s)
SLIDE_04_NARRATION = SlideNarration(
    slide_id=4,
    title="Creating Training Tracks",
    duration_seconds=25,
    ssml_text="""
<speak>
Time to create a Training Track! <break time="0.4s"/>

Tracks are how you organize courses into learning journeys! <break time="0.5s"/>

Click on the Tracks tab... <break time="0.3s"/>
Then Create Track! <break time="0.4s"/>

Let's call this one... Python Fundamentals! <break time="0.5s"/>

Add a description... <break time="0.3s"/>
"Learn Python from basics to advanced!" <break time="0.5s"/>

Tracks can contain multiple courses... <break time="0.3s"/>
In a specific order... <break time="0.3s"/>
With prerequisites automatically enforced! <break time="0.5s"/>

Your students get a clear path to mastery! <break time="0.4s"/>
How cool is that?
</speak>
""",
    plain_text="Time to create a Training Track! Tracks are how you organize courses into learning journeys! Click on the Tracks tab, then Create Track! Let's call this one Python Fundamentals! Add a description - Learn Python from basics to advanced! Tracks can contain multiple courses, in a specific order, with prerequisites automatically enforced! Your students get a clear path to mastery! How cool is that?",
    segments=[
        NarrationSegment("Time to create a Training Track!", 0, 2),
        NarrationSegment("Tracks are how you organize courses into learning journeys!", 2.5, 3),
        NarrationSegment("Click on the Tracks tab, then Create Track!", 6, 2.5),
        NarrationSegment("Let's call this one Python Fundamentals!", 9, 2.5),
        NarrationSegment("Add a description - Learn Python from basics to advanced!", 12, 3),
        NarrationSegment("Tracks can contain multiple courses, in a specific order, with prerequisites automatically enforced!", 16, 4),
        NarrationSegment("Your students get a clear path to mastery! How cool is that?", 21, 4),
    ]
)

# Slide 5: Instructor Dashboard (30s)
SLIDE_05_NARRATION = SlideNarration(
    slide_id=5,
    title="Instructor Dashboard",
    duration_seconds=30,
    ssml_text="""
<speak>
Now let's see what instructors get! <break time="0.5s"/>

Logging in as an instructor... <break time="0.4s"/>

Wow! <break time="0.3s"/>
Look at this instructor dashboard! <break time="0.5s"/>

The Courses tab shows all your courses... <break time="0.3s"/>
Published, drafts, everything organized! <break time="0.5s"/>

You can see student progress at a glance... <break time="0.3s"/>
Engagement metrics... <break time="0.2s"/>
Completion rates... <break time="0.3s"/>
All in real-time! <break time="0.5s"/>

But here's where it gets really exciting... <break time="0.4s"/>

The Content Generation tab! <break time="0.3s"/>
This is where AI magic happens!
</speak>
""",
    plain_text="Now let's see what instructors get! Logging in as an instructor... Wow! Look at this instructor dashboard! The Courses tab shows all your courses - published, drafts, everything organized! You can see student progress at a glance, engagement metrics, completion rates, all in real-time! But here's where it gets really exciting - the Content Generation tab! This is where AI magic happens!",
    segments=[
        NarrationSegment("Now let's see what instructors get!", 0, 2),
        NarrationSegment("Logging in as an instructor...", 2.5, 2),
        NarrationSegment("Wow! Look at this instructor dashboard!", 5, 2.5),
        NarrationSegment("The Courses tab shows all your courses - published, drafts, everything organized!", 8, 4),
        NarrationSegment("You can see student progress at a glance, engagement metrics, completion rates, all in real-time!", 13, 5),
        NarrationSegment("But here's where it gets really exciting...", 19, 2.5),
        NarrationSegment("The Content Generation tab! This is where AI magic happens!", 22, 4),
    ]
)

# Slide 6: AI Course Generation (35s)
SLIDE_06_NARRATION = SlideNarration(
    slide_id=6,
    title="AI Course Generation",
    duration_seconds=35,
    ssml_text="""
<speak>
This is the game changer! <break time="0.5s"/>

AI-powered course generation! <break time="0.4s"/>

Just enter a course title... <break time="0.3s"/>
"Introduction to Machine Learning!" <break time="0.5s"/>

Add a brief description... <break time="0.4s"/>

Now watch this... <break time="0.3s"/>
Click Generate Outline! <break time="0.5s"/>

The AI analyzes your topic... <break time="0.3s"/>
Creates a complete course structure... <break time="0.3s"/>
With modules, lessons, and learning objectives! <break time="0.5s"/>

But wait, there's more! <break time="0.4s"/>

It can generate slides... <break time="0.2s"/>
Quiz questions... <break time="0.2s"/>
Even hands-on lab exercises! <break time="0.5s"/>

What used to take weeks... <break time="0.3s"/>
Now takes minutes! <break time="0.4s"/>

This is the future of course creation!
</speak>
""",
    plain_text="This is the game changer! AI-powered course generation! Just enter a course title - Introduction to Machine Learning! Add a brief description. Now watch this - click Generate Outline! The AI analyzes your topic, creates a complete course structure, with modules, lessons, and learning objectives! But wait, there's more! It can generate slides, quiz questions, even hands-on lab exercises! What used to take weeks now takes minutes! This is the future of course creation!",
    segments=[
        NarrationSegment("This is the game changer! AI-powered course generation!", 0, 3),
        NarrationSegment("Just enter a course title - Introduction to Machine Learning!", 3.5, 3),
        NarrationSegment("Add a brief description.", 7, 1.5),
        NarrationSegment("Now watch this - click Generate Outline!", 9, 2.5),
        NarrationSegment("The AI analyzes your topic, creates a complete course structure, with modules, lessons, and learning objectives!", 12, 5),
        NarrationSegment("But wait, there's more! It can generate slides, quiz questions, even hands-on lab exercises!", 18, 5),
        NarrationSegment("What used to take weeks now takes minutes!", 24, 3),
        NarrationSegment("This is the future of course creation!", 28, 3),
    ]
)

# Slide 7: Interactive Lab Environment (40s)
SLIDE_07_NARRATION = SlideNarration(
    slide_id=7,
    title="Interactive Lab Environment",
    duration_seconds=40,
    ssml_text="""
<speak>
Now for something truly amazing! <break time="0.5s"/>

Interactive coding labs! <break time="0.4s"/>

Each student gets their own isolated environment... <break time="0.3s"/>
Running in Docker containers! <break time="0.5s"/>

Look at this! <break time="0.3s"/>
A full code editor... right in the browser! <break time="0.5s"/>

Let's write some code... <break time="0.3s"/>
print... open parenthesis... <break time="0.2s"/>
quote... Hello, World! <break time="0.4s"/>

Click Run! <break time="0.5s"/>

And there it is! <break time="0.3s"/>
The code executes instantly! <break time="0.5s"/>

Students can experiment... <break time="0.2s"/>
Make mistakes... <break time="0.2s"/>
Learn by doing! <break time="0.5s"/>

And the AI assistant is right there... <break time="0.3s"/>
Ready to help when they get stuck! <break time="0.5s"/>

This is hands-on learning at its best!
</speak>
""",
    plain_text="Now for something truly amazing! Interactive coding labs! Each student gets their own isolated environment running in Docker containers! Look at this - a full code editor right in the browser! Let's write some code - print, open parenthesis, quote, Hello World! Click Run! And there it is - the code executes instantly! Students can experiment, make mistakes, learn by doing! And the AI assistant is right there, ready to help when they get stuck! This is hands-on learning at its best!",
    segments=[
        NarrationSegment("Now for something truly amazing! Interactive coding labs!", 0, 3),
        NarrationSegment("Each student gets their own isolated environment running in Docker containers!", 3.5, 4),
        NarrationSegment("Look at this - a full code editor right in the browser!", 8, 3),
        NarrationSegment("Let's write some code - print Hello World!", 12, 3),
        NarrationSegment("Click Run!", 16, 1.5),
        NarrationSegment("And there it is - the code executes instantly!", 18, 3),
        NarrationSegment("Students can experiment, make mistakes, learn by doing!", 22, 4),
        NarrationSegment("And the AI assistant is right there, ready to help when they get stuck!", 27, 4),
        NarrationSegment("This is hands-on learning at its best!", 32, 3),
    ]
)

# Slide 8: Student Progress Analytics (30s)
SLIDE_08_NARRATION = SlideNarration(
    slide_id=8,
    title="Student Progress Analytics",
    duration_seconds=30,
    ssml_text="""
<speak>
Data-driven teaching! <break time="0.5s"/>

The analytics dashboard shows everything! <break time="0.4s"/>

Student engagement charts... <break time="0.3s"/>
Completion rates over time... <break time="0.3s"/>
Quiz performance breakdowns! <break time="0.5s"/>

Hover over any chart... <break time="0.3s"/>
Get detailed insights instantly! <break time="0.5s"/>

Now check out the Students view... <break time="0.4s"/>

See every student's progress... <break time="0.3s"/>
Time spent learning... <break time="0.2s"/>
Areas where they're struggling! <break time="0.5s"/>

Instructors can identify at-risk students early... <break time="0.3s"/>
And provide targeted support! <break time="0.5s"/>

Better data. <break time="0.2s"/>
Better teaching. <break time="0.2s"/>
Better outcomes!
</speak>
""",
    plain_text="Data-driven teaching! The analytics dashboard shows everything! Student engagement charts, completion rates over time, quiz performance breakdowns! Hover over any chart - get detailed insights instantly! Now check out the Students view. See every student's progress, time spent learning, areas where they're struggling! Instructors can identify at-risk students early and provide targeted support! Better data. Better teaching. Better outcomes!",
    segments=[
        NarrationSegment("Data-driven teaching!", 0, 1.5),
        NarrationSegment("The analytics dashboard shows everything!", 2, 2),
        NarrationSegment("Student engagement charts, completion rates over time, quiz performance breakdowns!", 4.5, 4),
        NarrationSegment("Hover over any chart - get detailed insights instantly!", 9, 3),
        NarrationSegment("Now check out the Students view.", 13, 2),
        NarrationSegment("See every student's progress, time spent learning, areas where they're struggling!", 15.5, 4),
        NarrationSegment("Instructors can identify at-risk students early and provide targeted support!", 20, 4),
        NarrationSegment("Better data. Better teaching. Better outcomes!", 25, 4),
    ]
)

# Slide 9: Quiz and Assessment (30s)
SLIDE_09_NARRATION = SlideNarration(
    slide_id=9,
    title="Quiz and Assessment",
    duration_seconds=30,
    ssml_text="""
<speak>
Assessment made easy! <break time="0.5s"/>

Let's create a quiz! <break time="0.4s"/>

Enter the quiz title... <break time="0.3s"/>
Python Basics Quiz! <break time="0.5s"/>

Now here's the magic button... <break time="0.3s"/>
Generate Questions with AI! <break time="0.5s"/>

Watch this! <break time="0.4s"/>

The AI creates relevant questions... <break time="0.3s"/>
Multiple choice... <break time="0.2s"/>
True or false... <break time="0.2s"/>
Even coding challenges! <break time="0.5s"/>

Each question is automatically graded... <break time="0.3s"/>
With instant feedback for students! <break time="0.5s"/>

No more spending hours writing questions... <break time="0.3s"/>
The AI does the heavy lifting! <break time="0.4s"/>

You just review and publish!
</speak>
""",
    plain_text="Assessment made easy! Let's create a quiz! Enter the quiz title - Python Basics Quiz! Now here's the magic button - Generate Questions with AI! Watch this! The AI creates relevant questions - multiple choice, true or false, even coding challenges! Each question is automatically graded with instant feedback for students! No more spending hours writing questions - the AI does the heavy lifting! You just review and publish!",
    segments=[
        NarrationSegment("Assessment made easy!", 0, 1.5),
        NarrationSegment("Let's create a quiz! Enter the quiz title - Python Basics Quiz!", 2, 3),
        NarrationSegment("Now here's the magic button - Generate Questions with AI!", 5.5, 3),
        NarrationSegment("Watch this!", 9, 1),
        NarrationSegment("The AI creates relevant questions - multiple choice, true or false, even coding challenges!", 10.5, 5),
        NarrationSegment("Each question is automatically graded with instant feedback for students!", 16, 4),
        NarrationSegment("No more spending hours writing questions - the AI does the heavy lifting!", 21, 4),
        NarrationSegment("You just review and publish!", 26, 3),
    ]
)

# Slide 10: Student Learning Experience (35s)
SLIDE_10_NARRATION = SlideNarration(
    slide_id=10,
    title="Student Learning Experience",
    duration_seconds=35,
    ssml_text="""
<speak>
Finally, let's see the student experience! <break time="0.5s"/>

Logging in as a student... <break time="0.4s"/>

This is clean, intuitive, beautiful! <break time="0.5s"/>

The student dashboard shows enrolled courses... <break time="0.3s"/>
Progress bars for each one... <break time="0.3s"/>
And recommended next steps! <break time="0.5s"/>

Click on a course... <break time="0.4s"/>

Look at this learning interface! <break time="0.3s"/>
Video lessons... <break time="0.2s"/>
Interactive content... <break time="0.2s"/>
Clear navigation! <break time="0.5s"/>

Students always know where they are... <break time="0.3s"/>
And what's coming next! <break time="0.5s"/>

This is modern learning... <break time="0.3s"/>
Designed for engagement and success! <break time="0.5s"/>

Welcome to the future of training! <break time="0.3s"/>
Welcome to Course Creator Platform!
</speak>
""",
    plain_text="Finally, let's see the student experience! Logging in as a student... This is clean, intuitive, beautiful! The student dashboard shows enrolled courses, progress bars for each one, and recommended next steps! Click on a course. Look at this learning interface! Video lessons, interactive content, clear navigation! Students always know where they are and what's coming next! This is modern learning designed for engagement and success! Welcome to the future of training! Welcome to Course Creator Platform!",
    segments=[
        NarrationSegment("Finally, let's see the student experience!", 0, 2.5),
        NarrationSegment("Logging in as a student...", 3, 2),
        NarrationSegment("This is clean, intuitive, beautiful!", 5.5, 2.5),
        NarrationSegment("The student dashboard shows enrolled courses, progress bars for each one, and recommended next steps!", 8.5, 5),
        NarrationSegment("Click on a course.", 14, 1.5),
        NarrationSegment("Look at this learning interface! Video lessons, interactive content, clear navigation!", 16, 4),
        NarrationSegment("Students always know where they are and what's coming next!", 21, 3.5),
        NarrationSegment("This is modern learning designed for engagement and success!", 25, 4),
        NarrationSegment("Welcome to the future of training! Welcome to Course Creator Platform!", 30, 5),
    ]
)

# All narrations collection
ALL_NARRATIONS = [
    SLIDE_01_NARRATION,
    SLIDE_02_NARRATION,
    SLIDE_03_NARRATION,
    SLIDE_04_NARRATION,
    SLIDE_05_NARRATION,
    SLIDE_06_NARRATION,
    SLIDE_07_NARRATION,
    SLIDE_08_NARRATION,
    SLIDE_09_NARRATION,
    SLIDE_10_NARRATION,
]


def get_narration(slide_id: int) -> Optional[SlideNarration]:
    """Get narration for a specific slide."""
    for narration in ALL_NARRATIONS:
        if narration.slide_id == slide_id:
            return narration
    return None


def get_all_narrations() -> List[SlideNarration]:
    """Get all narrations."""
    return ALL_NARRATIONS
