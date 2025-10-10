# Demo System Guide - Course Creator Platform

**Version:** 1.0
**Last Updated:** 2025-10-09
**Status:** Ready for Video Generation

---

## 🎯 Overview

The Course Creator Platform demo system provides an automated, engaging 5-7 minute video presentation showcasing key platform features to prospective customers, stakeholders, and investors.

**Key Features:**
- ✅ 11 video segments covering all major features
- ✅ AI voice narration (browser-native TTS)
- ✅ Interactive video player with timeline navigation
- ✅ Automated Selenium video recording system
- ✅ Professional presentation design

---

## 📁 System Architecture

```
course-creator/
├── scripts/
│   ├── generate_demo_videos.py          # Selenium + FFmpeg video recorder
│   └── generate_demo_screenshots.py     # (Legacy - replaced by videos)
│
├── frontend/
│   ├── html/
│   │   └── demo-player.html             # Interactive video player UI
│   └── static/demo/
│       └── videos/                      # Generated video screencasts
│           ├── slide_01_introduction.mp4
│           ├── slide_02_challenge.mp4
│           ├── slide_03_course_generation.mp4
│           └── ... (11 total videos)
│
├── docs/
│   ├── INTERACTIVE_DEMO_DESIGN.md       # Complete design specification
│   └── DEMO_SYSTEM_GUIDE.md             # This file
│
└── services/demo-service/               # Demo API backend (future)
    └── demo_slideshow.py
```

---

## 🎬 Demo Storyboard

**Total Duration:** 7 minutes (420 seconds)

| Slide | Title | Duration | Purpose |
|-------|-------|----------|---------|
| 1 | Introduction | 15s | Welcome message and platform overview |
| 2 | The Challenge | 30s | Traditional course creation pain points |
| 3 | AI Course Generation | 60s | Showcase AI-powered course creation |
| 4 | Content Generation | 60s | RAG-enhanced content creation |
| 5 | Multi-IDE Labs | 60s | Professional coding environments |
| 6 | AI Lab Assistant | 45s | Context-aware AI help system |
| 7 | Assessment System | 45s | Quizzes, grading, analytics |
| 8 | Progress Tracking | 30s | Student and instructor dashboards |
| 9 | Organization Mgmt | 30s | Multi-tenant RBAC |
| 10 | Privacy Compliance | 30s | GDPR/CCPA/PIPEDA compliance |
| 11 | Call to Action | 15s | Trial signup and contact info |

---

## 🚀 Getting Started

### Prerequisites

**Required Software:**
```bash
# Install FFmpeg (for video recording)
sudo apt-get update
sudo apt-get install ffmpeg

# Install Xvfb (for headless recording)
sudo apt-get install xvfb

# Install Python dependencies (already installed via requirements.txt)
pip install selenium webdriver-manager
```

**Verify Installation:**
```bash
# Check FFmpeg
ffmpeg -version

# Check Xvfb
Xvfb -help

# Check Python script
python3 scripts/generate_demo_videos.py --help
```

---

## 📹 Generating Video Screencasts

### Step 1: Ensure Platform is Running

```bash
# Start all services
./scripts/app-control.sh start

# Verify all services are healthy
./scripts/app-control.sh status

# Services should be accessible at https://localhost:3000
```

### Step 2: Create Demo User Accounts

The video generator uses these test credentials:

**Instructor Account:**
- Email: `demo.instructor@example.com`
- Password: `DemoPass123!`

**Student Account:**
- Email: `demo.student@example.com`
- Password: `DemoPass123!`

Create these accounts via the platform or database seeding.

### Step 3: Generate All Videos

```bash
# Generate all 11 video segments (headless mode)
python3 scripts/generate_demo_videos.py --all --headless

# Clean old videos before generating
python3 scripts/generate_demo_videos.py --all --clean --headless
```

**Expected Output:**
```
Checking dependencies...
✓ FFmpeg installed
✓ Xvfb installed (headless mode available)
============================================================
DEMO VIDEO GENERATION - ALL SLIDES
============================================================
✓ Virtual display started: :99
✓ WebDriver initialized (1920x1080)

🎥 Generating Slide 1: Introduction (15s)
  🎥 Recording started: slide_01_introduction.mp4 (15s)
  ✓ Recording saved: slide_01_introduction.mp4
✓ Slide 1 complete

... (slides 2-11)

✓ WebDriver closed
============================================================
✅ COMPLETE: 11 video screencasts generated
⏱️  Total duration: 532.4 seconds
📁 Output directory: /home/bbrelin/course-creator/frontend/static/demo/videos
============================================================
```

### Step 4: Generate Individual Slides (Optional)

```bash
# Generate only Slide 5 (Multi-IDE Labs)
python3 scripts/generate_demo_videos.py --slide 5

# Generate Slide 3 in non-headless mode (visible browser)
python3 scripts/generate_demo_videos.py --slide 3
```

---

## 🎮 Using the Demo Player

### Accessing the Demo

1. **Start the platform:**
   ```bash
   ./scripts/app-control.sh start
   ```

2. **Open demo player:**
   ```
   https://localhost:3000/html/demo-player.html
   ```

### Demo Player Features

**Playback Controls:**
- ▶️ **Play/Pause** - Space bar or Play button
- ⏮️ **Previous Slide** - Left arrow or Previous button
- ⏭️ **Next Slide** - Right arrow or Next button
- **Progress Bar** - Click to seek within current video
- **Timeline** - Click any slide thumbnail to jump directly

**AI Voice Narration:**
- Automatically speaks when video starts
- Pauses with video
- Synchronized with on-screen text overlay
- Uses browser-native high-quality voices (Google preferred)

**Keyboard Shortcuts:**
- `Space` - Play/Pause
- `←` - Previous slide
- `→` - Next slide

---

## 🎙️ AI Voice Narration System

### How It Works

The demo player uses the **Web Speech API** (browser-native TTS) for AI voice narration:

**Voice Selection Priority:**
1. Google UK English Female (highest quality)
2. Google US English Female
3. Google US English
4. Microsoft Zira (Windows)
5. Alex (macOS)
6. Any English voice (fallback)

**Configuration:**
- **Rate:** 0.95 (slightly slower for clarity)
- **Pitch:** 1.0 (natural)
- **Volume:** 1.0 (full)

### Alternative: Pre-Generated Audio Files

For production deployments or offline demos, you can pre-generate audio files using TTS services:

**Option 1: Google Cloud Text-to-Speech**
```python
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

synthesis_input = texttospeech.SynthesisInput(text=narration_text)
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Neural2-F",  # High-quality neural voice
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.95
)

response = client.synthesize_speech(
    input=synthesis_input, voice=voice, audio_config=audio_config
)

with open("slide_01_narration.mp3", "wb") as out:
    out.write(response.audio_content)
```

**Option 2: AWS Polly**
```python
import boto3

polly = boto3.client('polly')

response = polly.synthesize_speech(
    Text=narration_text,
    OutputFormat='mp3',
    VoiceId='Joanna',  # High-quality neural voice
    Engine='neural'
)

with open("slide_01_narration.mp3", "wb") as out:
    out.write(response['AudioStream'].read())
```

Then update the demo player to use `<audio>` elements instead of Web Speech API.

---

## 🔧 Customization

### Updating Narration Scripts

Edit `/frontend/html/demo-player.html` and modify the `loadSlides()` method:

```javascript
this.slides = [
    {
        id: 1,
        title: "Introduction",
        video: "/static/demo/videos/slide_01_introduction.mp4",
        duration: 15,
        narration: "Your custom narration text here..."  // ← Edit this
    },
    // ... other slides
];
```

### Adjusting Video Durations

Edit `/scripts/generate_demo_videos.py` and modify the slide methods:

```python
def generate_slide_01_introduction(self):
    """
    Generate video for Slide 1: Introduction

    Duration: 15 seconds  ← Edit this
    """
    print("\n🎥 Generating Slide 1: Introduction (15s)")

    def workflow():
        self.driver.get(f"{BASE_URL}/")
        time.sleep(3)
        # Add or modify workflow steps

    self.record_workflow("slide_01_introduction.mp4", 15, workflow)  # ← Duration here
```

### Customizing Workflows

Each slide's workflow can be customized by editing the `workflow()` function inside each `generate_slide_XX_()` method:

```python
def workflow():
    self.login_as_student()
    self.driver.get(f"{BASE_URL}/courses")
    time.sleep(5)

    # Add custom interactions
    course_card = self.driver.find_element(By.CLASS_NAME, "course-card")
    course_card.click()
    time.sleep(10)
```

---

## 📊 Quality Assurance

### Video Quality Checklist

Before deploying the demo, verify:

- [ ] All 11 videos generated successfully
- [ ] Videos are 1920x1080 resolution
- [ ] Workflows show intended features clearly
- [ ] No error messages visible in videos
- [ ] Smooth transitions between actions
- [ ] Appropriate timing (not too fast/slow)

### Testing the Complete Demo

```bash
# 1. Generate all videos
python3 scripts/generate_demo_videos.py --all --clean --headless

# 2. Verify all videos exist
ls -lh frontend/static/demo/videos/

# 3. Open demo player
# Navigate to: https://localhost:3000/html/demo-player.html

# 4. Test complete playthrough:
#    - Press Play on Slide 1
#    - Let demo auto-advance through all 11 slides
#    - Verify AI narration speaks on each slide
#    - Total time should be ~7 minutes

# 5. Test navigation:
#    - Click different slides in timeline
#    - Use Previous/Next buttons
#    - Test keyboard shortcuts
```

---

## 🐛 Troubleshooting

### Issue: FFmpeg Not Found

**Error:**
```
❌ FFmpeg not found
   Install: sudo apt-get install ffmpeg
```

**Solution:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Issue: Xvfb Not Running

**Error:**
```
WebDriverException: unknown error: DevToolsActivePort file doesn't exist
```

**Solution:**
```bash
# Start Xvfb manually
Xvfb :99 -screen 0 1920x1080x24 &

# Or run video generator in non-headless mode
python3 scripts/generate_demo_videos.py --all
```

### Issue: Videos Show Login Errors

**Problem:** Demo user accounts don't exist

**Solution:**
```bash
# Create demo accounts via psql
PGPASSWORD=course_pass psql -h localhost -p 5433 -U course_user -d course_creator

INSERT INTO users (username, email, password_hash, role_name, organization_id)
VALUES
  ('demo.instructor', 'demo.instructor@example.com', '$2b$12$...', 'instructor', 1),
  ('demo.student', 'demo.student@example.com', '$2b$12$...', 'student', 1);
```

### Issue: AI Voice Not Speaking

**Problem:** Browser doesn't support Web Speech API

**Solutions:**
1. Use Chrome/Edge (best support)
2. Enable microphone permissions
3. Check browser console for errors
4. Use pre-generated audio files instead (see Alternative section above)

### Issue: Videos Too Long/Short

**Problem:** Workflow timing doesn't match planned duration

**Solution:**
Adjust `time.sleep()` values in workflow functions to match desired duration:

```python
def workflow():
    self.driver.get(f"{BASE_URL}/")
    time.sleep(5)  # ← Increase/decrease this

    # Add more steps to fill duration
    self.driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(3)
```

---

## 🚀 Production Deployment

### Hosting the Demo

**Option 1: Static Hosting (Recommended)**
- Upload videos to CDN (e.g., AWS S3 + CloudFront)
- Host demo player HTML on static site
- No backend required

**Option 2: Integrated with Platform**
- Serve demo from nginx at `/demo`
- Videos served from `/static/demo/videos/`
- Accessible to all visitors (no login required)

**Nginx Configuration:**
```nginx
# Add to frontend/nginx.conf

location /demo {
    alias /usr/share/nginx/html/html/demo-player.html;
    try_files $uri $uri/ =404;
}

location /static/demo/ {
    alias /usr/share/nginx/html/static/demo/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Performance Optimization

**Video Compression:**
```bash
# Compress videos for web (H.264, smaller file size)
ffmpeg -i slide_01_introduction.mp4 \
       -vcodec libx264 \
       -crf 23 \
       -preset medium \
       -movflags +faststart \
       slide_01_introduction_compressed.mp4
```

**Preloading:**
Add to demo-player.html:
```html
<link rel="preload" href="/static/demo/videos/slide_01_introduction.mp4" as="video">
```

---

## 📈 Analytics & Metrics

### Tracking Demo Engagement

Add analytics to measure:
- **Completion Rate:** % who watch all 11 slides
- **Average Watch Time:** How long viewers watch
- **Drop-off Points:** Where viewers stop watching
- **CTA Click Rate:** % who click "Start Trial"

**Example with Google Analytics:**
```javascript
// Add to demo-player.html

// Track slide views
loadSlide(index) {
    // ... existing code
    gtag('event', 'demo_slide_view', {
        'slide_number': index + 1,
        'slide_title': this.slides[index].title
    });
}

// Track completion
onVideoEnded() {
    if (this.currentSlideIndex === this.slides.length - 1) {
        gtag('event', 'demo_completed', {
            'total_time': this.getTotalWatchTime()
        });
    }
}
```

---

## 📝 Maintenance

### Updating Demo After Feature Changes

When platform features change:

1. **Update narration scripts** in demo-player.html
2. **Regenerate affected videos:**
   ```bash
   python3 scripts/generate_demo_videos.py --slide 5 --clean
   ```
3. **Test the updated slide** in demo player
4. **Deploy updated files** to production

### Version Control

Tag demo versions for tracking:
```bash
git tag -a demo-v1.0 -m "Initial demo release"
git push origin demo-v1.0
```

---

## 🎓 Best Practices

### Video Recording Tips

1. **Clean test data** - Use fresh demo accounts with realistic data
2. **Timing** - Allow sufficient time for animations and page loads
3. **Error handling** - Add try/except blocks for unreliable elements
4. **Consistency** - Use same test data across regenerations
5. **Quality checks** - Review generated videos before deployment

### Narration Writing Guidelines

1. **Be concise** - Match video duration (don't rush or drag)
2. **Focus on benefits** - Explain value, not just features
3. **Professional tone** - Confident, enthusiastic, helpful
4. **Avoid jargon** - Use plain language for broader appeal
5. **Call to action** - End with clear next steps

---

## 📚 Additional Resources

- **Design Document:** `/docs/INTERACTIVE_DEMO_DESIGN.md`
- **Selenium Docs:** https://selenium-python.readthedocs.io/
- **FFmpeg Guide:** https://ffmpeg.org/documentation.html
- **Web Speech API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API

---

## 🤝 Support

For issues or questions:
- **GitHub Issues:** https://github.com/course-creator/platform/issues
- **Email:** support@coursecreator.com
- **Slack:** #demo-system channel

---

**Ready to Generate Your Demo!** 🎬

Follow the steps in "Getting Started" to create your first demo video presentation.
