# Demo Setup Instructions - OBS + Playwright

This guide explains how to generate the demo videos using OBS Studio and Playwright.

## ✅ Completed Steps

1. **Demo Flow Designed** - 10 slides covering the complete platform journey
2. **Audio Generated** - All 10 narrations created with ElevenLabs Charlotte voice
3. **Scripts Created** - Playwright + OBS integration ready

## 🎯 Setup OBS Studio

### Step 1: Start OBS Studio

```bash
# Start OBS in the background
DISPLAY=:99 obs &
```

**Or manually launch OBS from your desktop environment**

### Step 2: Enable WebSocket Server

1. In OBS, go to **Tools → WebSocket Server Settings**
2. Check **Enable WebSocket server**
3. Set Port: `4455`
4. **Uncheck** "Enable Authentication" (or set password to blank)
5. Click **Apply** and **OK**

### Step 3: Configure Recording Settings

#### Output Settings
1. Go to **Settings → Output**
2. Output Mode: **Simple**
3. Recording Format: **MP4**
4. Recording Quality: **High Quality**
5. Encoder: **Software (x264)**

#### Video Settings
1. Go to **Settings → Video**
2. Base (Canvas) Resolution: **1920x1080**
3. Output (Scaled) Resolution: **1920x1080**
4. FPS: **30**

#### Recording Path
1. In **Settings → Output → Recording**
2. Set Recording Path to: `/home/bbrelin/course-creator/frontend/static/demo/videos`

### Step 4: Add Browser Source

1. In the **Sources** panel, click **+**
2. Select **Browser**
3. Name it "Demo Browser"
4. Settings:
   - URL: `https://localhost:3000`
   - Width: `1920`
   - Height: `1080`
   - FPS: `30`
   - Check: **Shutdown source when not visible**
   - Check: **Refresh browser when scene becomes active**
5. Click **OK**

### Step 5: Test WebSocket Connection

```bash
python3 -c "
from obswebsocket import obsws, requests
try:
    ws = obsws('localhost', 4455, '')
    ws.connect()
    version = ws.call(requests.GetVersion())
    print(f'✅ Connected to OBS {version.getObsVersion()}')
    ws.disconnect()
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('Make sure OBS is running with WebSocket enabled')
"
```

## 🎬 Generate Demo Videos

### Test Single Slide First

Create a test script to verify everything works:

```bash
cat > /tmp/test_slide1.py << 'EOF'
import asyncio
from scripts.generate_demo_with_obs import *

async def test():
    recorder = OBSRecorder()
    recorder.connect()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = await context.new_page()

        # Test slide 1
        await slide_01_introduction(page, recorder, 25)

        await context.close()
        await browser.close()

    recorder.disconnect()
    print("✅ Test complete! Check frontend/static/demo/videos/slide_01_introduction.mp4")

asyncio.run(test())
EOF

python3 /tmp/test_slide1.py
```

### Generate All Slides

Once the test works:

```bash
cd /home/bbrelin/course-creator
python3 scripts/generate_demo_with_obs.py
```

This will generate all 10 slides sequentially.

## 🎵 Audio Files

All audio narrations are ready:
- `frontend/static/demo/audio/slide_01_narration.mp3` through `slide_10_narration.mp3`
- Generated with ElevenLabs Charlotte voice
- Matched to script durations

## 📋 Slide Overview

| # | Title | Duration | Description |
|---|-------|----------|-------------|
| 1 | Introduction | 25s | Platform overview and value proposition |
| 2 | Getting Started | 20s | How to register organization |
| 3 | Create Organization | 45s | Fill registration form |
| 4 | Projects & Tracks | 40s | Training track management |
| 5 | Assign Instructors | 35s | Add instructors to tracks |
| 6 | Create Course with AI | 60s | AI-assisted course creation |
| 7 | Enroll Employees | 40s | Bulk employee enrollment |
| 8 | Student Experience | 45s | Student dashboard and learning |
| 9 | AI Assistant | 50s | AI chatbot and contact capture |
| 10 | Summary | 30s | Wrap-up and CTA |

## 🐛 Troubleshooting

### OBS WebSocket Won't Connect
- Verify OBS is running
- Check WebSocket settings in OBS (Tools → WebSocket Server Settings)
- Ensure port 4455 is not blocked
- Try restarting OBS

### Browser Not Showing in Recording
- Check that Browser source is added to the scene
- Verify URL is `https://localhost:3000`
- Make sure frontend container is running: `docker ps | grep frontend`

### Mouse Cursor Not Visible
- The script includes custom cursor CSS
- OBS should capture the system cursor automatically
- Check OBS settings: **Settings → Video → Show cursor in recording**

### Recording File Not Found
- Check OBS recording path matches: `/home/bbrelin/course-creator/frontend/static/demo/videos`
- Verify you have write permissions to that directory

## 📚 Next Steps

After generating videos:

1. **Review Videos** - Check each slide for quality
2. **Update Demo Player** - Ensure demo-player.html references all 10 slides
3. **Test Audio Sync** - Verify audio and video are synchronized
4. **Add Transitions** - Enhance demo player with fade transitions
5. **Deploy** - Restart frontend container to serve new videos

## 🎨 Customization

To modify slides:
- **Edit narration**: Update `scripts/demo_narration_scripts.json`
- **Change workflows**: Edit slide functions in `scripts/generate_demo_with_obs.py`
- **Regenerate audio**: Run `python3 scripts/generate_demo_audio_charlotte.py`
- **Regenerate videos**: Run `python3 scripts/generate_demo_with_obs.py`
