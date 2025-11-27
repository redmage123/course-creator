#!/usr/bin/env python3
"""
Generate Demo Audio with ElevenLabs

BUSINESS REQUIREMENT:
Generate expressive, enthusiastic audio narrations for demo screencasts
using ElevenLabs Text-to-Speech API with SSML support.

VOICE SETTINGS (Optimized for Enthusiastic Delivery):
- stability: 0.30 (more emotional variation)
- similarity_boost: 0.85 (natural voice quality)
- style: 0.55 (more expressive delivery)
- use_speaker_boost: True (enhanced clarity)

SSML SUPPORT:
ElevenLabs supports <break time="Xs"/> tags (max 3s) with the
eleven_turbo_v2 or eleven_multilingual_v2 models.

USAGE:
    export ELEVENLABS_API_KEY='your_key_here'
    python scripts/demo_generation/generate_audio.py --all
    python scripts/demo_generation/generate_audio.py --slide 1
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.demo_generation.narrations import get_narration, get_all_narrations, SlideNarration

# ElevenLabs
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
OUTPUT_DIR = Path('frontend-legacy/static/demo/audio')

# ElevenLabs API settings
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# Voice IDs (popular expressive voices)
VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel - clear, professional
    "josh": "TxGEqnHWrfWFTfGW9XjX",     # Josh - energetic, dynamic
    "bella": "EXAVITQu4vr4xnSDxMaL",    # Bella - warm, engaging
    "adam": "pNInz6obpgDQGcFmaJgB",     # Adam - confident, authoritative
    "arnold": "VR6AewLTigWG4xSOukaG",   # Arnold - enthusiastic
    "sam": "yoZ06aMxZJJ28mfd3POQ",      # Sam - friendly, upbeat
}

# Default voice for demo
DEFAULT_VOICE = "josh"  # Energetic and dynamic

# Voice settings for enthusiastic delivery
VOICE_SETTINGS = {
    "stability": 0.30,           # Lower = more emotional variation
    "similarity_boost": 0.85,    # High for natural quality
    "style": 0.55,               # Higher = more expressive
    "use_speaker_boost": True    # Enhanced clarity
}


class ElevenLabsClient:
    """
    Client for ElevenLabs Text-to-Speech API.

    Generates expressive audio with SSML support for natural speech patterns.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ELEVENLABS_API_URL
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

    def generate_speech(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        use_ssml: bool = True,
        model_id: str = "eleven_turbo_v2"
    ) -> bool:
        """
        Generate speech audio from text.

        Args:
            text: Text or SSML to convert to speech
            voice_id: ElevenLabs voice ID
            output_path: Path to save the audio file
            use_ssml: Whether the text contains SSML markup
            model_id: ElevenLabs model to use (eleven_turbo_v2 supports SSML)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/text-to-speech/{voice_id}"

        # Clean SSML for API
        if use_ssml:
            # Remove outer <speak> tags if present (ElevenLabs handles them)
            clean_text = text.strip()
            if clean_text.startswith("<speak>"):
                clean_text = clean_text[7:]
            if clean_text.endswith("</speak>"):
                clean_text = clean_text[:-8]
            clean_text = clean_text.strip()
        else:
            clean_text = text

        payload = {
            "text": clean_text,
            "model_id": model_id,
            "voice_settings": VOICE_SETTINGS
        }

        try:
            logger.info(f"Generating audio for: {output_path.name}")

            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=60
            )

            if response.status_code == 200:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(response.content)
                logger.info(f"Audio saved: {output_path}")
                return True
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            return False

    def get_voices(self) -> Dict[str, Any]:
        """Get available voices from ElevenLabs."""
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return {}


def generate_slide_audio(
    narration: SlideNarration,
    client: ElevenLabsClient,
    voice_id: str,
    output_dir: Path
) -> Optional[Path]:
    """
    Generate audio for a single slide narration.

    Args:
        narration: SlideNarration object with SSML text
        client: ElevenLabs client
        voice_id: Voice ID to use
        output_dir: Directory to save audio files

    Returns:
        Path to generated audio file, or None if failed
    """
    output_path = output_dir / f"slide_{narration.slide_id:02d}_narration.mp3"

    success = client.generate_speech(
        text=narration.ssml_text,
        voice_id=voice_id,
        output_path=output_path,
        use_ssml=True
    )

    if success:
        return output_path
    return None


def generate_all_audio(voice_name: str = DEFAULT_VOICE) -> Dict[str, Any]:
    """
    Generate audio for all slide narrations.

    Args:
        voice_name: Name of the voice to use

    Returns:
        Dictionary with generation results
    """
    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY environment variable not set")
        return {"error": "API key not set"}

    voice_id = VOICES.get(voice_name, VOICES[DEFAULT_VOICE])
    client = ElevenLabsClient(ELEVENLABS_API_KEY)

    results = {
        "voice": voice_name,
        "voice_id": voice_id,
        "voice_settings": VOICE_SETTINGS,
        "slides": []
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    narrations = get_all_narrations()

    for narration in narrations:
        logger.info(f"\n{'='*50}")
        logger.info(f"Generating audio for Slide {narration.slide_id}: {narration.title}")
        logger.info(f"{'='*50}")

        output_path = generate_slide_audio(
            narration=narration,
            client=client,
            voice_id=voice_id,
            output_dir=OUTPUT_DIR
        )

        slide_result = {
            "slide_id": narration.slide_id,
            "title": narration.title,
            "duration_seconds": narration.duration_seconds,
            "audio_file": str(output_path) if output_path else None,
            "status": "success" if output_path else "failed"
        }
        results["slides"].append(slide_result)

        # Rate limiting - wait between API calls
        time.sleep(1)

    # Save results
    results_path = OUTPUT_DIR / "generation_results.json"
    results_path.write_text(json.dumps(results, indent=2))
    logger.info(f"\nResults saved to: {results_path}")

    # Summary
    success_count = sum(1 for s in results["slides"] if s["status"] == "success")
    logger.info(f"\nGeneration complete: {success_count}/{len(results['slides'])} successful")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate demo narration audio with ElevenLabs")
    parser.add_argument("--slide", "-s", type=int, help="Generate audio for specific slide")
    parser.add_argument("--all", "-a", action="store_true", help="Generate audio for all slides")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE,
                       choices=list(VOICES.keys()),
                       help=f"Voice to use (default: {DEFAULT_VOICE})")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--preview", "-p", action="store_true",
                       help="Preview narration text without generating")

    args = parser.parse_args()

    if args.list_voices:
        print("\nAvailable voices:")
        for name, vid in VOICES.items():
            marker = " (default)" if name == DEFAULT_VOICE else ""
            print(f"  {name}: {vid}{marker}")

        if ELEVENLABS_API_KEY:
            print("\nFetching voices from ElevenLabs API...")
            client = ElevenLabsClient(ELEVENLABS_API_KEY)
            voices = client.get_voices()
            if voices.get("voices"):
                print("\nAll available voices:")
                for voice in voices["voices"]:
                    print(f"  {voice['name']}: {voice['voice_id']}")
        return

    if args.preview:
        if args.slide:
            narration = get_narration(args.slide)
            if narration:
                print(f"\n{'='*60}")
                print(f"Slide {narration.slide_id}: {narration.title}")
                print(f"Duration: {narration.duration_seconds}s")
                print(f"{'='*60}")
                print("\nSSML Text:")
                print(narration.ssml_text)
                print("\nPlain Text:")
                print(narration.plain_text)
            else:
                print(f"Slide {args.slide} not found")
        else:
            for narration in get_all_narrations():
                print(f"\n{'='*60}")
                print(f"Slide {narration.slide_id}: {narration.title} ({narration.duration_seconds}s)")
                print(f"{'='*60}")
                print(narration.plain_text[:200] + "..." if len(narration.plain_text) > 200 else narration.plain_text)
        return

    if not ELEVENLABS_API_KEY:
        print("\nError: ELEVENLABS_API_KEY environment variable not set")
        print("Set it with: export ELEVENLABS_API_KEY='your_key_here'")
        return

    if args.slide:
        narration = get_narration(args.slide)
        if not narration:
            print(f"Slide {args.slide} not found")
            return

        voice_id = VOICES.get(args.voice, VOICES[DEFAULT_VOICE])
        client = ElevenLabsClient(ELEVENLABS_API_KEY)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = generate_slide_audio(narration, client, voice_id, OUTPUT_DIR)

        if output_path:
            print(f"\nAudio generated: {output_path}")
        else:
            print("\nAudio generation failed")

    elif args.all:
        generate_all_audio(args.voice)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
