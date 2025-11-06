"""
Video Features E2E Test Suite

BUSINESS CONTEXT:
Comprehensive end-to-end tests for video playback, progress tracking,
upload processing, transcription, and captions. These tests validate
the complete video learning experience from instructor upload through
student viewing and analytics.

TEST CATEGORIES:
1. Video Playback & Tracking (test_video_playback_tracking.py)
   - Playback controls, quality selection, speed adjustment
   - Progress tracking and resume functionality
   - Watch time analytics

2. Video Upload & Processing (test_video_upload_processing.py)
   - Upload workflows with progress tracking
   - Transcoding pipeline (multiple resolutions)
   - Error handling and validation

3. Transcription & Captions (test_video_transcription_captions.py)
   - Auto-generated transcripts (Whisper API)
   - Caption synchronization and styling
   - Accessibility features

COVERAGE TARGET: 30 tests across 3 files (~2,600 lines)
"""

__all__ = [
    'test_video_playback_tracking',
    'test_video_upload_processing',
    'test_video_transcription_captions',
]
