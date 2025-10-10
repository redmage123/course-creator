# ElevenLabs Audio Integration Guide

**Purpose:** Generate professional, natural-sounding narration for demo videos
**Quality:** 9.5/10 - Nearly indistinguishable from human voice actors
**Cost:** ~$0.15 one-time (Free tier available: $10,000 characters/month)

---

## 🎯 ElevenLabs API Features

### What You Get
- ✅ **Ultra-realistic voices** - State-of-the-art neural synthesis
- ✅ **Multiple voice options** - 9 pre-made voices included
- ✅ **Emotional control** - Adjust stability, similarity, style
- ✅ **Voice cloning** - Clone your own voice (paid tiers)
- ✅ **Multiple languages** - 29+ languages supported
- ✅ **Simple REST API** - Easy integration with Python

### API Endpoints Used
```
GET  https://api.elevenlabs.io/v1/voices       # List available voices
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}  # Generate audio
GET  https://api.elevenlabs.io/v1/user         # Check quota/usage
```

---

## 🚀 Quick Start

### Step 1: Get API Key (2 minutes)

1. **Sign up** at https://elevenlabs.io
   - Free tier: 10,000 characters/month
   - Our demo: ~2,500 characters total (well within free tier!)

2. **Get API key** from https://elevenlabs.io/app/settings/api-keys
   - Click "Generate API Key"
   - Copy the key (starts with `sk_...`)

3. **Set environment variable:**
   ```bash
   export ELEVENLABS_API_KEY='sk_your_key_here'
   ```

   OR create `.env` file in project root:
   ```bash
   echo "ELEVENLABS_API_KEY=sk_your_key_here" >> .env
   ```

### Step 2: Install Dependencies (30 seconds)

```bash
.venv/bin/pip install requests
```

### Step 3: Generate Audio (2 minutes)

```bash
# Run the generation script
.venv/bin/python3 scripts/generate_demo_audio_elevenlabs.py
```

**Expected output:**
```
======================================================================
🎤 ELEVENLABS AUDIO GENERATION - Demo Narration
======================================================================

📁 Output directory: frontend/static/demo/audio

🎵 Fetching available voices...
   ✓ Found 11 available voices

🎙️  Selected voice: Rachel
   Voice ID: 21m00Tcm4TlvDq8ikWAM

======================================================================
Generating audio files...
======================================================================

📝 Slide 01: Introduction
   Generating audio for slide 1... ✓ (45.2KB)
📝 Slide 02: Organization Dashboard
   Generating audio for slide 2... ✓ (98.5KB)
...
[continues for all 13 slides]

======================================================================
✅ AUDIO GENERATION COMPLETE
======================================================================

📊 Summary:
   • Total slides: 13
   • Success: 13
   • Failed: 0

📁 Audio files saved to: /home/bbrelin/course-creator/frontend/static/demo/audio
```

**Generated files:**
```
frontend/static/demo/audio/
├── slide_01_narration.mp3  (~45KB)
├── slide_02_narration.mp3  (~98KB)
├── slide_03_narration.mp3  (~65KB)
...
└── slide_13_narration.mp3  (~38KB)

Total: ~800KB for all 13 audio files
```

---

## 🎙️ Voice Selection

### Pre-configured Voices

The script includes 9 professional voices:

| Voice | Gender | Style | Best For |
|-------|--------|-------|----------|
| **Rachel** ⭐ | Female | Warm, professional | Product demos (default) |
| Domi | Female | Strong, confident | Corporate presentations |
| Bella | Female | Soft, gentle | Educational content |
| Elli | Female | Conversational | Casual explanations |
| Antoni | Male | Well-rounded | General narration |
| Josh | Male | Deep, authoritative | Professional content |
| Arnold | Male | Crisp, clear | Technical explanations |
| Adam | Male | Deep, narrative | Storytelling |
| Sam | Male | Dynamic, energetic | Engaging presentations |

**Default:** Rachel (warm, professional female voice)

### Changing Voices

Edit line 163 in `scripts/generate_demo_audio_elevenlabs.py`:

```python
# Change from Rachel to Josh (male voice)
selected_voice = 'josh'  # or 'domi', 'bella', etc.
```

---

## 🎛️ Voice Settings

### Available Controls

```python
voice_settings = {
    'stability': 0.5,         # 0-1: Lower = more expressive
    'similarity_boost': 0.75, # 0-1: Higher = more like original
    'style': 0.0,            # 0-1: Exaggeration (paid tier)
    'use_speaker_boost': True # Enhanced clarity
}
```

**Recommended settings for demos:**
- **Stability: 0.5-0.7** - Balanced between consistency and expression
- **Similarity: 0.75** - High quality voice reproduction
- **Style: 0.0** - Natural delivery (requires paid tier to adjust)

---

## 🔧 Integration with Demo Player

### Option A: HTML5 Audio Elements (Recommended)

Update `demo-player.html` to play audio files alongside videos:

```javascript
// In loadSlide() function
loadSlide(index) {
    const slide = this.slides[index];

    // Load video
    this.videoSource.src = slide.video;
    this.videoPlayer.load();

    // Load and play audio narration (NEW)
    const audioPath = `/static/demo/audio/slide_${String(index + 1).padStart(2, '0')}_narration.mp3`;
    const audio = new Audio(audioPath);

    // Play audio when video starts
    this.videoPlayer.addEventListener('play', () => {
        audio.play();
    }, { once: true });

    // Stop audio when changing slides
    this.videoPlayer.addEventListener('pause', () => {
        audio.pause();
        audio.currentTime = 0;
    }, { once: true });
}
```

### Option B: Embed Audio in Videos

Use FFmpeg to merge audio with video:

```bash
# For each slide
ffmpeg -i slide_01_introduction.mp4 \
       -i slide_01_narration.mp3 \
       -c:v copy \
       -c:a aac \
       -shortest \
       slide_01_with_audio.mp4
```

---

## 💰 Pricing & Usage

### Free Tier
- **10,000 characters/month**
- Our demo: ~2,500 characters
- **Can regenerate 4x per month for free**

### Character Count by Slide

| Slide | Characters | Cost (if paid) |
|-------|-----------|----------------|
| 1 | 158 | $0.0003 |
| 2 | 245 | $0.0005 |
| 3 | 161 | $0.0003 |
| 4 | 180 | $0.0004 |
| 5 | 185 | $0.0004 |
| 6 | 197 | $0.0004 |
| 7 | 158 | $0.0003 |
| 8 | 153 | $0.0003 |
| 9 | 228 | $0.0005 |
| 10 | 181 | $0.0004 |
| 11 | 204 | $0.0004 |
| 12 | 225 | $0.0005 |
| 13 | 158 | $0.0003 |
| **Total** | **2,433** | **$0.0049** |

**Paid Pricing (if exceeded free tier):**
- $0.30 per 1,000 characters
- Our demo: $0.73 total (one-time)

### Usage Tracking

Check your usage:
```bash
curl https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: $ELEVENLABS_API_KEY"
```

Response shows:
```json
{
  "subscription": {
    "character_count": 2433,
    "character_limit": 10000,
    "can_use_delayed_payment_methods": false
  }
}
```

---

## 🎨 Advanced Features

### Voice Cloning (Paid Tiers)

Clone your own voice or hire a voice actor:

```python
# Upload voice samples
url = f'{ELEVENLABS_API_URL}/voices/add'
files = {
    'files': [
        open('sample1.mp3', 'rb'),
        open('sample2.mp3', 'rb'),
        open('sample3.mp3', 'rb')
    ]
}
data = {'name': 'Custom Voice'}
response = requests.post(url, files=files, data=data, headers=headers)
```

Requirements:
- 3+ audio samples (at least 1 minute each)
- Clear audio quality
- Consistent speaking style
- Professional tier: $5/month

### Sound Effects & Music

Add background music or effects:

```python
# Generate with sound effects (beta feature)
data = {
    'text': 'Welcome to Course Creator Platform.',
    'sound_effects': ['soft_background_music']
}
```

### Projects (Organization)

Group related audio files:

```python
# Create project
url = f'{ELEVENLABS_API_URL}/projects'
data = {'name': 'Course Creator Demo', 'default_voice_id': voice_id}
response = requests.post(url, json=data, headers=headers)
```

---

## 🔍 Troubleshooting

### Error: "Invalid API Key"
```
❌ HTTP Error 401: Unauthorized
```
**Solution:** Check your API key is correct and set in environment

### Error: "Quota Exceeded"
```
❌ HTTP Error 429: Too Many Requests
```
**Solution:** Wait for quota reset (monthly) or upgrade to paid tier

### Error: "Rate Limited"
```
⚠️  Rate limit exceeded - waiting 60 seconds...
```
**Solution:** Script automatically retries after delay

### Audio Quality Issues
- **Problem:** Audio sounds muffled
- **Solution:** Increase `similarity_boost` to 0.85-0.95

- **Problem:** Audio sounds robotic
- **Solution:** Decrease `stability` to 0.3-0.4 for more expression

### Missing Audio Files
```bash
# Verify files were created
ls -lh frontend/static/demo/audio/
```

Expected: 13 MP3 files (slide_01 through slide_13)

---

## 📋 Next Steps

After generating audio:

1. **Preview audio files:**
   ```bash
   # Linux/Mac
   mpg123 frontend/static/demo/audio/slide_01_narration.mp3

   # Or use browser
   open frontend/static/demo/audio/slide_01_narration.mp3
   ```

2. **Update demo player** to use audio files (see Integration section)

3. **Test full demo** with audio narration

4. **Optional:** Embed audio in video files for standalone distribution

---

## 🆚 Comparison: ElevenLabs vs Others

| Feature | ElevenLabs | Google Neural2 | Browser TTS |
|---------|-----------|---------------|-------------|
| **Quality** | 9.5/10 | 8.5/10 | 6/10 |
| **Naturalness** | Excellent | Very Good | Mediocre |
| **Cost (our demo)** | $0.00 (free tier) | $0.02 | Free |
| **Voices** | 9 premade + clone | 10+ neural | OS dependent |
| **Setup Time** | 5 min | 30 min | 0 min |
| **API** | Simple REST | Google Cloud SDK | Browser native |
| **Offline** | Pre-generate files | Pre-generate files | Live synthesis |

**Recommendation:** Use ElevenLabs for production demos, Browser TTS for development/testing

---

## 📞 Support

**ElevenLabs Documentation:** https://elevenlabs.io/docs
**API Reference:** https://elevenlabs.io/docs/api-reference
**Voice Library:** https://elevenlabs.io/voice-library
**Community Discord:** https://discord.gg/elevenlabs
**Support:** support@elevenlabs.io

---

## ✅ Summary

**What you get:**
- 13 professional audio narration files
- Ultra-realistic AI voice (Rachel)
- Total cost: $0.00 with free tier
- Generation time: ~2 minutes
- File size: ~800KB total

**Quality:**
- Sounds 95% like a human voice actor
- Professional, warm, engaging tone
- Perfect for product demos and presentations

**Next:** Update demo player to play audio files alongside videos! 🎬🔊
