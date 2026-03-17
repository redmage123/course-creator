# Demo Feature Module

## Overview

The Demo module provides an interactive slideshow showcasing the Course Creator Platform's capabilities through professionally narrated video walkthroughs. It features:

- **Perfect Audio/Video Synchronization** - Uses a drift correction sync engine
- **ElevenLabs AI Voice** - Natural, expressive narration with SSML markup
- **Auto-Scroll** - Automatic slide advancement with smooth transitions
- **Keyboard Navigation** - Full accessibility support
- **Responsive Design** - Works on desktop and mobile

## Components

### DemoPlayer

Main slideshow component with video player, audio narration, and timeline navigation.

```tsx
import { DemoPlayer } from './features/demo';

<DemoPlayer
  autoPlay={false}
  showSubtitles={true}
  onComplete={() => console.log('Demo finished!')}
/>
```

### DemoPage

Full-page demo experience with CTA section after completion.

## Audio/Video Synchronization

The sync engine monitors drift between audio and video elements, correcting when they diverge beyond 100ms. This ensures narration stays perfectly aligned with visuals.

### How It Works

1. **Initial Sync**: Audio position is set to match video position when playback starts
2. **Drift Detection**: Every 250ms, the engine calculates drift between audio and video
3. **Correction**: If drift exceeds 100ms, audio position is corrected to match video
4. **Seek Handling**: When user seeks, both audio and video are moved to the same position

### Configuration

```typescript
const SYNC_CHECK_INTERVAL_MS = 250; // How often to check drift
const DRIFT_THRESHOLD_MS = 100;      // Max allowed drift before correction
```

## ElevenLabs Audio Generation

### Expressive Narrations with SSML

The narrations use SSML markup for natural speech patterns:

- `<break time="0.5s"/>` - Strategic pauses for emphasis
- Exclamation marks for enthusiasm
- Question patterns for engagement
- Short sentences for impact

### Voice Settings (Optimized for Expressiveness)

```python
'voice_settings': {
    'stability': 0.35,        # Lower = more emotional variation
    'similarity_boost': 0.80, # Natural voice quality
    'style': 0.45,            # Higher = more expressive delivery
    'use_speaker_boost': True # Enhanced clarity
}
```

### Regenerating Audio Files

1. **Set API Key**:
   ```bash
   export ELEVENLABS_API_KEY='your_key_here'
   ```

2. **Run the expressive script**:
   ```bash
   python3 scripts/generate_demo_audio_elevenlabs_expressive.py
   ```

3. **Audio files** are saved to `frontend-legacy/static/demo/audio/`

### SSML Tags Supported

Per [ElevenLabs Documentation](https://elevenlabs.io/docs/best-practices/prompting/controls):

- `<break time="Xs"/>` - Pause for X seconds (max 3s)
- Uses `eleven_turbo_v2` model for SSML support

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Left Arrow | Previous Slide |
| Right Arrow | Next Slide |
| C | Toggle Subtitles |

## Routing

The demo is accessible at `/demo` (public route, no authentication required).

```tsx
// App.tsx
<Route path="/demo" element={<DemoPage />} />
```

## Homepage Integration

A "Watch Demo" button in the hero section links to the demo page:

```tsx
<Link to="/demo" className={styles.ctaButtonDemo}>
  <i className="fas fa-play-circle"></i>
  Watch Demo
</Link>
```

## Video Requirements

Demo videos should be placed in `frontend-legacy/static/demo/videos/` with naming convention:

```
slide_01_introduction.mp4
slide_02_register_organization.mp4
slide_03_org_admin_dashboard.mp4
...
```

## File Structure

```
frontend-react/src/features/demo/
├── index.ts                      # Module exports
├── README.md                     # This file
├── components/
│   └── DemoPlayer/
│       ├── DemoPlayer.tsx        # Main component
│       ├── DemoPlayer.module.css # Styles
│       └── index.ts              # Component export
└── pages/
    ├── DemoPage.tsx              # Full-page experience
    └── DemoPage.module.css       # Page styles

scripts/
└── generate_demo_audio_elevenlabs_expressive.py  # Audio generation
```

## Sources

- [ElevenLabs Controls Documentation](https://elevenlabs.io/docs/best-practices/prompting/controls)
- [ElevenLabs Text to Speech](https://elevenlabs.io/docs/capabilities/text-to-speech)
