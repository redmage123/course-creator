# Demo Assets Directory

This directory contains video screencasts for the Course Creator Platform interactive demo.

## 📁 Directory Structure

```
demo/
├── videos/                          # Video screencasts (MP4 format)
│   ├── slide_01_introduction.mp4       # 15s - Welcome & overview
│   ├── slide_02_challenge.mp4          # 30s - Traditional course creation problems
│   ├── slide_03_course_generation.mp4  # 60s - AI course generation
│   ├── slide_04_content_generation.mp4 # 60s - RAG content creation
│   ├── slide_05_multi_ide_lab.mp4      # 60s - Multi-IDE lab environment
│   ├── slide_06_ai_lab_assistant.mp4   # 45s - AI assistant integration
│   ├── slide_07_assessment_system.mp4  # 45s - Quiz and assessment system
│   ├── slide_08_progress_tracking.mp4  # 30s - Analytics dashboards
│   ├── slide_09_organization_management.mp4  # 30s - Multi-tenant RBAC
│   ├── slide_10_privacy_compliance.mp4 # 30s - GDPR compliance
│   └── slide_11_call_to_action.mp4     # 15s - Trial signup CTA
│
├── screenshots/                     # (Legacy - replaced by videos)
└── README.md                        # This file
```

## 🎬 Generating Videos

Videos are generated using Selenium + FFmpeg automation:

```bash
# Generate all 11 demo videos
python3 /home/bbrelin/course-creator/scripts/generate_demo_videos.py --all --headless

# Generate specific slide
python3 /home/bbrelin/course-creator/scripts/generate_demo_videos.py --slide 5
```

## 🎮 Viewing the Demo

Open the interactive demo player:
```
https://localhost:3000/html/demo-player.html
```

Features:
- Video playback with AI voice narration
- Interactive timeline navigation
- Keyboard shortcuts (Space = play/pause, arrows = navigate)
- Auto-advance through all 11 slides

## 📖 Documentation

- **Complete Guide:** `/docs/DEMO_SYSTEM_GUIDE.md`
- **Design Spec:** `/docs/INTERACTIVE_DEMO_DESIGN.md`
- **Video Generator:** `/scripts/generate_demo_videos.py`
- **Demo Player:** `/frontend/html/demo-player.html`

## 📊 Demo Stats

- **Total Duration:** 7 minutes (420 seconds)
- **Number of Slides:** 11
- **Video Resolution:** 1920x1080 (Full HD)
- **Format:** MP4 (H.264)
- **AI Voice:** Browser-native TTS (Web Speech API)

## 🚀 Quick Start

1. Install dependencies:
   ```bash
   sudo apt-get install ffmpeg xvfb
   ```

2. Create demo user accounts (see `/docs/DEMO_SYSTEM_GUIDE.md`)

3. Generate videos:
   ```bash
   python3 scripts/generate_demo_videos.py --all --clean --headless
   ```

4. View demo:
   ```
   https://localhost:3000/html/demo-player.html
   ```

---

**Note:** Videos are generated on-demand and not committed to version control due to large file sizes. Generate them locally or on your deployment server.
