#!/usr/bin/env python3
"""
Configure OBS Studio via WebSocket API
"""

from obswebsocket import obsws, requests as obs_requests
import json

OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""

VIDEOS_DIR = "/home/bbrelin/course-creator/frontend/static/demo/videos"

def configure_obs():
    """Configure OBS recording settings"""
    print("🔧 Configuring OBS Studio...")

    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
    ws.connect()

    print("   ✅ Connected to OBS WebSocket")

    # Get current profile
    try:
        # Set video settings
        print("   📹 Setting video resolution to 1920x1080...")
        ws.call(obs_requests.SetVideoSettings(
            baseWidth=1920,
            baseHeight=1080,
            outputWidth=1920,
            outputHeight=1080,
            fpsNumerator=30,
            fpsDenominator=1
        ))
        print("      ✅ Video settings configured")

    except Exception as e:
        print(f"      ⚠️  Video settings error: {e}")

    # Configure recording output
    try:
        print("   💾 Configuring recording output...")

        # Set recording directory
        ws.call(obs_requests.SetRecordDirectory(VIDEOS_DIR))
        print(f"      ✅ Recording path: {VIDEOS_DIR}")

    except Exception as e:
        print(f"      ⚠️  Recording path error: {e}")

    # Get current recording settings
    try:
        print("   📊 Current recording settings:")
        profile = ws.call(obs_requests.GetRecordDirectory())
        print(f"      Recording Directory: {profile.getRecordDirectory()}")

        video = ws.call(obs_requests.GetVideoSettings())
        print(f"      Base Resolution: {video.getBaseWidth()}x{video.getBaseHeight()}")
        print(f"      Output Resolution: {video.getOutputWidth()}x{video.getOutputHeight()}")
        print(f"      FPS: {video.getFpsNumerator()}/{video.getFpsDenominator()}")

    except Exception as e:
        print(f"      ⚠️  Get settings error: {e}")

    # Check scenes
    try:
        scene_list = ws.call(obs_requests.GetSceneList())
        scenes = scene_list.getScenes()
        current = scene_list.getCurrentProgramSceneName()

        print(f"   🎬 Scenes:")
        for scene in scenes:
            marker = "→" if scene['sceneName'] == current else " "
            print(f"      {marker} {scene['sceneName']}")

    except Exception as e:
        print(f"      ⚠️  Scene list error: {e}")

    ws.disconnect()
    print("\n✅ OBS configuration complete!")
    print(f"\nRecording will save to: {VIDEOS_DIR}")
    print("Format: MP4 (default)")
    print("Resolution: 1920x1080")
    print("FPS: 30")

if __name__ == "__main__":
    configure_obs()
