#!/bin/bash
# Regenerate Demo Audio with Enthusiastic Voice Settings
#
# Usage:
#   1. Set your API key: export ELEVENLABS_API_KEY="your_key_here"
#   2. Run this script: ./regenerate_audio.sh
#
# Or run in one line:
#   ELEVENLABS_API_KEY="your_key_here" ./regenerate_audio.sh

echo "========================================================================"
echo "🎤 REGENERATING DEMO AUDIO WITH ENTHUSIASTIC VOICE SETTINGS"
echo "========================================================================"
echo ""

# Check if API key is set
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "❌ ERROR: ELEVENLABS_API_KEY environment variable is not set"
    echo ""
    echo "Please set your API key first:"
    echo "  export ELEVENLABS_API_KEY=\"your_key_here\""
    echo ""
    echo "Or run with:"
    echo "  ELEVENLABS_API_KEY=\"your_key_here\" ./regenerate_audio.sh"
    echo ""
    echo "Get your API key from: https://elevenlabs.io/app/settings/api-keys"
    echo ""
    exit 1
fi

echo "✓ API key found"
echo ""

# Run the audio generation script
echo "Running audio generation script..."
echo ""

cd /home/bbrelin/course-creator
python3 scripts/generate_demo_audio_elevenlabs.py

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ AUDIO GENERATION COMPLETE!"
    echo "========================================================================"
    echo ""
    echo "New audio files generated with enthusiastic voice settings:"
    echo "  - Style: 0.90 (very high expressiveness)"
    echo "  - Stability: 0.30 (natural variation)"
    echo "  - Voice: Charlotte (UK Female, mid-20s)"
    echo ""
    echo "🔄 Restarting frontend to load new audio..."
    docker-compose restart frontend
    echo ""
    echo "✅ Done! Test the demo player at: https://localhost:3000/demo-player.html"
    echo ""
else
    echo ""
    echo "❌ Audio generation failed. Check the errors above."
    echo ""
    exit 1
fi
