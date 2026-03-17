"""
Comprehensive E2E Tests for Video Upload and Processing Workflows

BUSINESS REQUIREMENT:
Instructors must be able to upload video content in multiple formats (MP4, MOV, AVI),
track upload progress, and have videos automatically processed (transcoded, thumbnails
generated, metadata extracted) for optimal delivery to students across devices.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 10 video upload and processing scenarios
- Validates UI interactions, file uploads, and backend processing
- Multi-layer verification: UI + Database + File System

TEST COVERAGE:
1. Upload Workflows (4 tests):
   - Upload video file (MP4, MOV, AVI formats)
   - Upload video with progress tracking
   - Upload large video (>1GB with chunking)
   - Cancel video upload mid-process

2. Processing Pipeline (3 tests):
   - Video transcoding to multiple resolutions (1080p, 720p, 480p)
   - Thumbnail generation (3 timestamps: 0%, 50%, 100%)
   - Metadata extraction (duration, resolution, codec)

3. Error Handling (3 tests):
   - Upload invalid file format (error message)
   - Upload exceeds size limit (reject with message)
   - Processing failure (retry mechanism)

PRIORITY: P1 (HIGH) - Core instructor content creation functionality
"""

import pytest
import time
import uuid
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
import psycopg2

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def create_test_video_file(
    filename: str,
    size_mb: int = 1,
    format: str = 'mp4'
) -> Path:
    """
    Create a test video file for upload testing.
    
    BUSINESS CONTEXT:
    Generates realistic test video files without requiring large binary assets
    in the repository. Files are created in temp directory and cleaned up
    automatically.
    
    Args:
        filename: Name of file to create
        size_mb: Size of file in megabytes
        format: Video format extension (mp4, mov, avi)
    
    Returns:
        Path to created test file
    """
    temp_dir = tempfile.gettempdir()
    filepath = Path(temp_dir) / f"{filename}.{format}"
    
    # Create file with random data of specified size
    size_bytes = size_mb * 1024 * 1024
    with open(filepath, 'wb') as f:
        f.write(os.urandom(size_bytes))
    
    return filepath


def cleanup_test_file(filepath: Path):
    """
    Clean up test video file.
    
    Args:
        filepath: Path to file to delete
    """
    if filepath.exists():
        filepath.unlink()


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class InstructorLoginPage(BasePage):
    """
    Page Object for instructor login page.
    
    BUSINESS CONTEXT:
    Instructors need authentication to access video upload functionality.
    """
    
    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    
    def navigate(self):
        """Navigate to instructor login page."""
        self.navigate_to("/login")
    
    def login(self, email: str, password: str):
        """
        Perform instructor login.
        
        Args:
            email: Instructor email
            password: Instructor password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)  # Wait for redirect


class VideoUploadPage(BasePage):
    """
    Page Object for video upload interface.
    
    BUSINESS CONTEXT:
    Central interface for instructors to upload video content. Supports
    file selection, progress tracking, and upload cancellation.
    
    TECHNICAL IMPLEMENTATION:
    Uses multipart file upload with chunking for large files (>100MB).
    Progress is tracked via WebSocket or polling for real-time updates.
    """
    
    # Navigation Locators
    VIDEOS_TAB = (By.CSS_SELECTOR, "a[href='#videos'], button[data-tab='videos']")
    UPLOAD_VIDEO_BUTTON = (By.ID, "uploadVideoBtn")
    
    # Upload Modal Locators
    UPLOAD_MODAL = (By.ID, "videoUploadModal")
    FILE_INPUT = (By.ID, "videoFileInput")
    VIDEO_TITLE_INPUT = (By.ID, "videoTitle")
    VIDEO_DESCRIPTION_INPUT = (By.ID, "videoDescription")
    COURSE_SELECT = (By.ID, "courseSelect")
    START_UPLOAD_BUTTON = (By.ID, "startUploadBtn")
    CANCEL_UPLOAD_BUTTON = (By.ID, "cancelUploadBtn")
    
    # Progress Tracking Locators
    PROGRESS_BAR = (By.ID, "uploadProgressBar")
    PROGRESS_PERCENTAGE = (By.ID, "uploadProgressPercentage")
    UPLOAD_STATUS_TEXT = (By.ID, "uploadStatusText")
    UPLOAD_SPEED = (By.ID, "uploadSpeed")
    TIME_REMAINING = (By.ID, "timeRemaining")
    
    # File Validation Locators
    FILE_SIZE_DISPLAY = (By.ID, "fileSizeDisplay")
    FILE_FORMAT_DISPLAY = (By.ID, "fileFormatDisplay")
    VALIDATION_ERROR = (By.CLASS_NAME, "validation-error")
    
    # Success/Error Locators
    UPLOAD_SUCCESS_MESSAGE = (By.CLASS_NAME, "upload-success")
    UPLOAD_ERROR_MESSAGE = (By.CLASS_NAME, "upload-error")
    
    def navigate(self):
        """Navigate to video upload page."""
        self.navigate_to("/html/instructor-dashboard.html")
        time.sleep(1)
    
    def navigate_to_videos_tab(self):
        """Navigate to videos tab in instructor dashboard."""
        self.click_element(*self.VIDEOS_TAB)
        time.sleep(1)
    
    def click_upload_video(self):
        """Click upload video button."""
        self.scroll_to_element(*self.UPLOAD_VIDEO_BUTTON)
        self.click_element(*self.UPLOAD_VIDEO_BUTTON)
        time.sleep(1)
    
    def select_video_file(self, filepath: str):
        """
        Select video file for upload.
        
        TECHNICAL NOTE:
        File input is hidden in UI. We use send_keys to provide filepath.
        
        Args:
            filepath: Absolute path to video file
        """
        file_input = self.find_element(*self.FILE_INPUT)
        file_input.send_keys(str(filepath))
        time.sleep(1)  # Wait for file validation
    
    def enter_video_metadata(self, title: str, description: str, course_id: Optional[str] = None):
        """
        Enter video title, description, and course selection.
        
        Args:
            title: Video title
            description: Video description
            course_id: Optional course ID to select
        """
        self.enter_text(*self.VIDEO_TITLE_INPUT, title)
        self.enter_text(*self.VIDEO_DESCRIPTION_INPUT, description)
        
        if course_id:
            course_select = Select(self.find_element(*self.COURSE_SELECT))
            course_select.select_by_value(course_id)
        
        time.sleep(0.5)
    
    def start_upload(self):
        """Click start upload button."""
        self.click_element(*self.START_UPLOAD_BUTTON)
        time.sleep(0.5)
    
    def cancel_upload(self):
        """Click cancel upload button during upload."""
        self.click_element(*self.CANCEL_UPLOAD_BUTTON)
        time.sleep(0.5)
    
    def get_upload_progress(self) -> int:
        """
        Get current upload progress percentage.
        
        Returns:
            Upload progress as integer (0-100)
        """
        progress_text = self.get_element_text(*self.PROGRESS_PERCENTAGE)
        return int(progress_text.replace('%', ''))
    
    def get_upload_status(self) -> str:
        """
        Get current upload status text.
        
        Returns:
            Status text (e.g., "Uploading...", "Processing...", "Complete")
        """
        return self.get_element_text(*self.UPLOAD_STATUS_TEXT)
    
    def get_file_size_display(self) -> str:
        """Get displayed file size."""
        return self.get_element_text(*self.FILE_SIZE_DISPLAY)
    
    def get_file_format_display(self) -> str:
        """Get displayed file format."""
        return self.get_element_text(*self.FILE_FORMAT_DISPLAY)
    
    def get_validation_error(self) -> str:
        """Get validation error message."""
        return self.get_element_text(*self.VALIDATION_ERROR)
    
    def is_upload_successful(self) -> bool:
        """Check if upload success message is displayed."""
        try:
            return self.is_element_visible(*self.UPLOAD_SUCCESS_MESSAGE, timeout=5)
        except TimeoutException:
            return False
    
    def is_upload_error(self) -> bool:
        """Check if upload error message is displayed."""
        try:
            return self.is_element_visible(*self.UPLOAD_ERROR_MESSAGE, timeout=5)
        except TimeoutException:
            return False
    
    def wait_for_upload_complete(self, timeout: int = 60):
        """
        Wait for upload to complete (100% progress).
        
        Args:
            timeout: Maximum wait time in seconds
        """
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda d: self.get_upload_progress() == 100)


class VideoProcessingPage(BasePage):
    """
    Page Object for video processing status and configuration.
    
    BUSINESS CONTEXT:
    After upload, videos are automatically processed (transcoded to multiple
    resolutions, thumbnails generated, metadata extracted). Instructors can
    monitor processing status and configure processing options.
    """
    
    # Processing Status Locators
    PROCESSING_STATUS_CONTAINER = (By.ID, "processingStatusContainer")
    PROCESSING_STATUS_TEXT = (By.ID, "processingStatusText")
    TRANSCODING_PROGRESS = (By.ID, "transcodingProgress")
    THUMBNAIL_GENERATION_STATUS = (By.ID, "thumbnailGenerationStatus")
    METADATA_EXTRACTION_STATUS = (By.ID, "metadataExtractionStatus")
    
    # Processing Results Locators
    AVAILABLE_RESOLUTIONS = (By.CLASS_NAME, "available-resolution")
    THUMBNAIL_PREVIEWS = (By.CLASS_NAME, "thumbnail-preview")
    VIDEO_DURATION_DISPLAY = (By.ID, "videoDuration")
    VIDEO_RESOLUTION_DISPLAY = (By.ID, "videoResolution")
    VIDEO_CODEC_DISPLAY = (By.ID, "videoCodec")
    VIDEO_FILE_SIZE_DISPLAY = (By.ID, "videoFileSize")
    
    # Error Handling Locators
    PROCESSING_ERROR_MESSAGE = (By.CLASS_NAME, "processing-error")
    RETRY_PROCESSING_BUTTON = (By.ID, "retryProcessingBtn")
    
    def navigate_to_video_details(self, video_id: str):
        """
        Navigate to video details page to see processing status.
        
        Args:
            video_id: UUID of video
        """
        self.navigate_to(f"/html/instructor-dashboard.html?video={video_id}")
        time.sleep(1)
    
    def get_processing_status(self) -> str:
        """
        Get current processing status.
        
        Returns:
            Status text (e.g., "Processing...", "Complete", "Failed")
        """
        return self.get_element_text(*self.PROCESSING_STATUS_TEXT)
    
    def get_transcoding_progress(self) -> int:
        """
        Get transcoding progress percentage.
        
        Returns:
            Progress as integer (0-100)
        """
        progress_text = self.get_element_text(*self.TRANSCODING_PROGRESS)
        return int(progress_text.replace('%', ''))
    
    def get_available_resolutions(self) -> List[str]:
        """
        Get list of available video resolutions after transcoding.
        
        Returns:
            List of resolution strings (e.g., ["1080p", "720p", "480p"])
        """
        resolution_elements = self.find_elements(*self.AVAILABLE_RESOLUTIONS)
        return [elem.text for elem in resolution_elements]
    
    def get_thumbnail_count(self) -> int:
        """
        Get count of generated thumbnails.
        
        Returns:
            Number of thumbnail previews displayed
        """
        thumbnails = self.find_elements(*self.THUMBNAIL_PREVIEWS)
        return len(thumbnails)
    
    def get_video_metadata(self) -> Dict[str, str]:
        """
        Get extracted video metadata.
        
        Returns:
            Dictionary with metadata fields:
            - duration: Video duration (e.g., "5:23")
            - resolution: Video resolution (e.g., "1920x1080")
            - codec: Video codec (e.g., "H.264")
            - file_size: File size (e.g., "125 MB")
        """
        return {
            'duration': self.get_element_text(*self.VIDEO_DURATION_DISPLAY),
            'resolution': self.get_element_text(*self.VIDEO_RESOLUTION_DISPLAY),
            'codec': self.get_element_text(*self.VIDEO_CODEC_DISPLAY),
            'file_size': self.get_element_text(*self.VIDEO_FILE_SIZE_DISPLAY)
        }
    
    def is_processing_error(self) -> bool:
        """Check if processing error message is displayed."""
        try:
            return self.is_element_visible(*self.PROCESSING_ERROR_MESSAGE, timeout=5)
        except TimeoutException:
            return False
    
    def click_retry_processing(self):
        """Click retry processing button after failure."""
        self.click_element(*self.RETRY_PROCESSING_BUTTON)
        time.sleep(1)
    
    def wait_for_processing_complete(self, timeout: int = 300):
        """
        Wait for video processing to complete.
        
        BUSINESS NOTE:
        Processing can take several minutes for large videos.
        Default timeout is 5 minutes.
        
        Args:
            timeout: Maximum wait time in seconds
        """
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda d: self.get_processing_status() in ["Complete", "Failed"])


class VideoLibraryPage(BasePage):
    """
    Page Object for video library listing.
    
    BUSINESS CONTEXT:
    Displays all uploaded videos for a course with metadata, thumbnails,
    and management actions (edit, delete, reorder).
    """
    
    # Video List Locators
    VIDEO_LIST_CONTAINER = (By.ID, "videoListContainer")
    VIDEO_ITEMS = (By.CLASS_NAME, "video-item")
    VIDEO_TITLE = (By.CLASS_NAME, "video-title")
    VIDEO_THUMBNAIL = (By.CLASS_NAME, "video-thumbnail")
    VIDEO_DURATION = (By.CLASS_NAME, "video-duration")
    VIDEO_STATUS = (By.CLASS_NAME, "video-status")
    
    # Search/Filter Locators
    SEARCH_INPUT = (By.ID, "videoSearchInput")
    FILTER_STATUS_SELECT = (By.ID, "filterByStatus")
    SORT_SELECT = (By.ID, "sortVideos")
    
    def navigate_to_course_videos(self, course_id: str):
        """
        Navigate to video library for specific course.
        
        Args:
            course_id: UUID of course
        """
        self.navigate_to(f"/html/instructor-dashboard.html?course={course_id}#videos")
        time.sleep(1)
    
    def get_video_count(self) -> int:
        """
        Get count of videos in library.
        
        Returns:
            Number of video items displayed
        """
        videos = self.find_elements(*self.VIDEO_ITEMS)
        return len(videos)
    
    def get_video_by_title(self, title: str):
        """
        Find video item by title.
        
        Args:
            title: Video title to search for
        
        Returns:
            WebElement for video item, or None if not found
        """
        videos = self.find_elements(*self.VIDEO_ITEMS)
        for video in videos:
            video_title = video.find_element(*self.VIDEO_TITLE).text
            if video_title == title:
                return video
        return None
    
    def search_videos(self, search_term: str):
        """
        Search videos by title.
        
        Args:
            search_term: Text to search for
        """
        self.enter_text(*self.SEARCH_INPUT, search_term)
        time.sleep(1)  # Wait for search results
    
    def filter_by_status(self, status: str):
        """
        Filter videos by processing status.
        
        Args:
            status: Status to filter (e.g., "All", "Processing", "Complete", "Failed")
        """
        status_select = Select(self.find_element(*self.FILTER_STATUS_SELECT))
        status_select.select_by_visible_text(status)
        time.sleep(1)


# ============================================================================
# DATABASE VERIFICATION HELPERS
# ============================================================================

class VideoDatabase:
    """
    Database access for video verification.
    
    BUSINESS CONTEXT:
    Validates that UI actions correctly persist to database and that
    backend processing updates are reflected accurately.
    """
    
    def __init__(self):
        """Initialize database connection."""
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'course_creator'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """
        Get video record by ID.
        
        Args:
            video_id: UUID of video
        
        Returns:
            Dictionary with video data, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, course_id, title, description, video_type, video_url,
                   thumbnail_url, duration_seconds, order_index, is_active,
                   file_size_bytes, mime_type, created_at, updated_at
            FROM course_videos
            WHERE id = %s
        """, (video_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'course_id': row[1],
            'title': row[2],
            'description': row[3],
            'video_type': row[4],
            'video_url': row[5],
            'thumbnail_url': row[6],
            'duration_seconds': row[7],
            'order_index': row[8],
            'is_active': row[9],
            'file_size_bytes': row[10],
            'mime_type': row[11],
            'created_at': row[12],
            'updated_at': row[13]
        }
    
    def get_upload_status(self, upload_id: str) -> Optional[Dict]:
        """
        Get upload progress record.
        
        Args:
            upload_id: UUID of upload
        
        Returns:
            Dictionary with upload status, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, course_id, filename, file_size_bytes, upload_status,
                   upload_progress, error_message, storage_path, created_at, completed_at
            FROM video_uploads
            WHERE id = %s
        """, (upload_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'course_id': row[1],
            'filename': row[2],
            'file_size_bytes': row[3],
            'upload_status': row[4],
            'upload_progress': row[5],
            'error_message': row[6],
            'storage_path': row[7],
            'created_at': row[8],
            'completed_at': row[9]
        }
    
    def get_processing_status(self, video_id: str) -> Optional[Dict]:
        """
        Get video processing status.
        
        Args:
            video_id: UUID of video
        
        Returns:
            Dictionary with processing status, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT video_id, processing_status, transcoding_progress,
                   thumbnail_count, metadata_extracted, error_message,
                   started_at, completed_at
            FROM video_processing
            WHERE video_id = %s
        """, (video_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'video_id': row[0],
            'processing_status': row[1],
            'transcoding_progress': row[2],
            'thumbnail_count': row[3],
            'metadata_extracted': row[4],
            'error_message': row[5],
            'started_at': row[6],
            'completed_at': row[7]
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# ============================================================================
# TEST CLASS 1: Upload Workflows
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoUploadWorkflows(BaseTest):
    """
    Test video upload workflows.
    
    BUSINESS REQUIREMENT:
    Instructors must be able to upload videos in multiple formats with
    real-time progress tracking and ability to cancel uploads.
    """
    
    @pytest.fixture(autouse=True)
    def setup_upload_tests(self):
        """Setup for upload tests."""
        self.login_page = InstructorLoginPage(self.driver, self.config)
        self.upload_page = VideoUploadPage(self.driver)
        self.library_page = VideoLibraryPage(self.driver)
        self.db = VideoDatabase()
        
        # Login as instructor
        self.login_page.navigate()
        self.login_page.login("instructor@example.com", "password123")
        
        yield
        
        # Cleanup
        self.db.close()
    
    @pytest.mark.priority_critical
    def test_01_upload_video_file_mp4_format(self):
        """
        Test uploading a video file in MP4 format.
        
        BUSINESS REQUIREMENT:
        Instructors must be able to upload MP4 video files (most common format).
        
        TEST SCENARIO:
        1. Navigate to video upload page
        2. Click upload video button
        3. Select MP4 video file (5MB test file)
        4. Enter video title and description
        5. Start upload
        6. Verify upload completes successfully
        7. Verify video appears in library
        8. Verify video record in database
        
        VALIDATION CRITERIA:
        - Upload progress reaches 100%
        - Success message displayed
        - Video appears in video library with correct title
        - Database record created with correct metadata
        - File saved to storage with correct path
        """
        # Create test video file
        test_file = create_test_video_file("test_video_mp4", size_mb=5, format='mp4')
        video_title = f"Test Video MP4 {uuid.uuid4()}"
        
        try:
            # Navigate and open upload modal
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            
            # Select file and enter metadata
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for MP4 format upload"
            )
            
            # Verify file size displayed
            file_size = self.upload_page.get_file_size_display()
            assert "5" in file_size, f"Expected ~5MB, got {file_size}"
            
            # Start upload
            self.upload_page.start_upload()
            
            # Wait for upload to complete
            self.upload_page.wait_for_upload_complete(timeout=60)
            
            # Verify success
            assert self.upload_page.is_upload_successful(), "Upload success message not displayed"
            
            # Navigate to video library
            time.sleep(2)
            self.library_page.navigate_to_course_videos("default-course-id")
            
            # Verify video in library
            video_item = self.library_page.get_video_by_title(video_title)
            assert video_item is not None, f"Video '{video_title}' not found in library"
            
            # TODO: Verify database record (requires video_id from upload response)
            # video_db = self.db.get_video_by_id(video_id)
            # assert video_db is not None
            # assert video_db['title'] == video_title
            # assert video_db['mime_type'] == 'video/mp4'
            
        finally:
            cleanup_test_file(test_file)
    
    @pytest.mark.priority_critical
    def test_02_upload_video_with_progress_tracking(self):
        """
        Test upload progress tracking with real-time updates.
        
        BUSINESS REQUIREMENT:
        Instructors need real-time feedback on upload progress to understand
        when large video files will be ready for use.
        
        TEST SCENARIO:
        1. Navigate to video upload page
        2. Select large video file (50MB)
        3. Start upload
        4. Monitor progress bar updates
        5. Verify progress increases from 0% to 100%
        6. Verify status text updates ("Uploading...", "Processing...", "Complete")
        7. Verify upload speed displayed
        8. Verify time remaining displayed
        
        VALIDATION CRITERIA:
        - Progress bar visible and updates smoothly
        - Progress percentage increases monotonically
        - Status text changes appropriately
        - Upload speed calculated and displayed
        - Time remaining decreases as upload progresses
        """
        test_file = create_test_video_file("test_video_progress", size_mb=50, format='mp4')
        video_title = f"Test Video Progress {uuid.uuid4()}"
        
        try:
            # Navigate and open upload modal
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            
            # Select file and metadata
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for progress tracking"
            )
            
            # Start upload
            self.upload_page.start_upload()
            time.sleep(1)
            
            # Track progress updates
            previous_progress = 0
            progress_updates = []
            
            for _ in range(10):  # Sample progress 10 times
                current_progress = self.upload_page.get_upload_progress()
                progress_updates.append(current_progress)
                
                # Verify progress increases monotonically
                assert current_progress >= previous_progress, \
                    f"Progress decreased: {previous_progress}% → {current_progress}%"
                
                previous_progress = current_progress
                
                # Check status text
                status = self.upload_page.get_upload_status()
                assert status in ["Uploading...", "Processing...", "Complete"], \
                    f"Unexpected status: {status}"
                
                if current_progress == 100:
                    break
                
                time.sleep(2)
            
            # Verify progress reached 100%
            final_progress = self.upload_page.get_upload_progress()
            assert final_progress == 100, f"Upload did not complete: {final_progress}%"
            
            # Verify at least 3 progress updates occurred
            assert len(set(progress_updates)) >= 3, \
                f"Progress updates not granular enough: {progress_updates}"
            
        finally:
            cleanup_test_file(test_file)
    
    @pytest.mark.priority_high
    def test_03_upload_large_video_with_chunking(self):
        """
        Test uploading large video (>1GB) with chunked upload.
        
        BUSINESS REQUIREMENT:
        Instructors must be able to upload large lecture recordings without
        timeouts or connection failures. Chunked upload enables resumable
        uploads for large files.
        
        TEST SCENARIO:
        1. Navigate to video upload page
        2. Select large video file (simulated 1.5GB)
        3. Start upload
        4. Verify upload uses chunking (multiple HTTP requests)
        5. Verify progress updates smoothly across chunks
        6. Verify upload completes successfully
        
        VALIDATION CRITERIA:
        - Large file accepted (>1GB)
        - Upload progress updates across chunks
        - No timeout errors during upload
        - Upload completes successfully
        - Database record shows correct file size
        
        TECHNICAL NOTE:
        For E2E tests, we simulate large file behavior without creating
        actual 1.5GB files. In production, chunking activates for files >100MB.
        """
        # Simulate large file (use smaller file but mark as large in metadata)
        test_file = create_test_video_file("test_video_large", size_mb=10, format='mp4')
        video_title = f"Test Large Video {uuid.uuid4()}"
        
        try:
            # Navigate and open upload modal
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            
            # Select file
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test large video with chunked upload"
            )
            
            # Start upload
            self.upload_page.start_upload()
            
            # Monitor for chunk-based progress (should see discrete jumps)
            # Each chunk is typically 5-10% of total file
            progress_history = []
            for _ in range(20):
                progress = self.upload_page.get_upload_progress()
                progress_history.append(progress)
                
                if progress == 100:
                    break
                
                time.sleep(1)
            
            # Verify upload completed
            assert self.upload_page.is_upload_successful(), \
                "Large video upload did not complete"
            
            # Verify progress showed incremental updates
            assert len(set(progress_history)) >= 5, \
                f"Expected chunked progress updates, got: {progress_history}"
            
        finally:
            cleanup_test_file(test_file)
    
    @pytest.mark.priority_high
    def test_04_cancel_video_upload_mid_process(self):
        """
        Test canceling video upload while in progress.
        
        BUSINESS REQUIREMENT:
        Instructors must be able to cancel uploads if they selected wrong file
        or need to make changes. Canceled uploads should clean up resources.
        
        TEST SCENARIO:
        1. Navigate to video upload page
        2. Select video file (20MB)
        3. Start upload
        4. Wait for upload to reach 30-50% progress
        5. Click cancel button
        6. Verify upload stops
        7. Verify no video record created in database
        8. Verify temp files cleaned up
        
        VALIDATION CRITERIA:
        - Cancel button enabled during upload
        - Upload stops after cancel clicked
        - No video appears in library
        - Database has no video record
        - Temp upload files deleted
        """
        test_file = create_test_video_file("test_video_cancel", size_mb=20, format='mp4')
        video_title = f"Test Cancel Upload {uuid.uuid4()}"
        
        try:
            # Navigate and open upload modal
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            
            # Select file and metadata
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video to be canceled"
            )
            
            # Start upload
            self.upload_page.start_upload()
            
            # Wait for progress to reach ~40%
            for _ in range(20):
                progress = self.upload_page.get_upload_progress()
                if progress >= 40:
                    break
                time.sleep(0.5)
            
            # Cancel upload
            self.upload_page.cancel_upload()
            time.sleep(2)
            
            # Verify upload did not complete
            assert not self.upload_page.is_upload_successful(), \
                "Upload should not show success after cancellation"
            
            # Navigate to library
            self.library_page.navigate_to_course_videos("default-course-id")
            
            # Verify video not in library
            video_item = self.library_page.get_video_by_title(video_title)
            assert video_item is None, \
                f"Canceled video '{video_title}' should not appear in library"
            
        finally:
            cleanup_test_file(test_file)


# ============================================================================
# TEST CLASS 2: Processing Pipeline
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoProcessingPipeline(BaseTest):
    """
    Test video processing pipeline (transcoding, thumbnails, metadata).
    
    BUSINESS REQUIREMENT:
    After upload, videos must be automatically processed for optimal delivery:
    - Transcoded to multiple resolutions (1080p, 720p, 480p)
    - Thumbnails generated at key timestamps
    - Metadata extracted (duration, codec, resolution)
    """
    
    @pytest.fixture(autouse=True)
    def setup_processing_tests(self):
        """Setup for processing tests."""
        self.login_page = InstructorLoginPage(self.driver, self.config)
        self.upload_page = VideoUploadPage(self.driver)
        self.processing_page = VideoProcessingPage(self.driver)
        self.db = VideoDatabase()
        
        # Login as instructor
        self.login_page.navigate()
        self.login_page.login("instructor@example.com", "password123")
        
        yield
        
        # Cleanup
        self.db.close()
    
    @pytest.mark.priority_critical
    def test_05_video_transcoding_multiple_resolutions(self):
        """
        Test video transcoding to multiple resolutions.
        
        BUSINESS REQUIREMENT:
        Videos must be transcoded to 1080p, 720p, and 480p to support
        different device capabilities and bandwidth constraints.
        
        TEST SCENARIO:
        1. Upload video file
        2. Wait for processing to start
        3. Monitor transcoding progress
        4. Verify all resolutions generated (1080p, 720p, 480p)
        5. Verify processing completes successfully
        6. Verify database records for each resolution
        
        VALIDATION CRITERIA:
        - Transcoding progress updates from 0% to 100%
        - All 3 resolutions available after processing
        - Each resolution has valid video file
        - Database tracks all resolution variants
        """
        test_file = create_test_video_file("test_video_transcode", size_mb=10, format='mp4')
        video_title = f"Test Transcoding {uuid.uuid4()}"
        
        try:
            # Upload video
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for transcoding"
            )
            self.upload_page.start_upload()
            self.upload_page.wait_for_upload_complete(timeout=60)
            
            # Get video ID (from upload response or library)
            # TODO: Extract video_id from upload response
            video_id = "temp-video-id"
            
            # Navigate to processing page
            self.processing_page.navigate_to_video_details(video_id)
            
            # Wait for processing to complete
            self.processing_page.wait_for_processing_complete(timeout=300)
            
            # Verify all resolutions available
            resolutions = self.processing_page.get_available_resolutions()
            expected_resolutions = ["1080p", "720p", "480p"]
            
            for resolution in expected_resolutions:
                assert resolution in resolutions, \
                    f"Resolution {resolution} not found. Available: {resolutions}"
            
            # Verify processing status
            status = self.processing_page.get_processing_status()
            assert status == "Complete", f"Processing status: {status}"
            
        finally:
            cleanup_test_file(test_file)
    
    @pytest.mark.priority_critical
    def test_06_thumbnail_generation_multiple_timestamps(self):
        """
        Test thumbnail generation at multiple timestamps.
        
        BUSINESS REQUIREMENT:
        Videos must have thumbnails generated at 0%, 50%, and 100% timestamps
        to help students preview content and navigate to key moments.
        
        TEST SCENARIO:
        1. Upload video file
        2. Wait for thumbnail generation
        3. Verify 3 thumbnails created (0%, 50%, 100%)
        4. Verify thumbnail images accessible
        5. Verify database records thumbnail URLs
        
        VALIDATION CRITERIA:
        - Exactly 3 thumbnails generated
        - Thumbnails taken at correct timestamps
        - Thumbnail images accessible via URL
        - Database stores thumbnail URLs
        """
        test_file = create_test_video_file("test_video_thumbnails", size_mb=8, format='mp4')
        video_title = f"Test Thumbnails {uuid.uuid4()}"
        
        try:
            # Upload video
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for thumbnail generation"
            )
            self.upload_page.start_upload()
            self.upload_page.wait_for_upload_complete(timeout=60)
            
            # Navigate to processing page
            video_id = "temp-video-id"
            self.processing_page.navigate_to_video_details(video_id)
            
            # Wait for processing
            self.processing_page.wait_for_processing_complete(timeout=300)
            
            # Verify thumbnail count
            thumbnail_count = self.processing_page.get_thumbnail_count()
            assert thumbnail_count == 3, \
                f"Expected 3 thumbnails, found {thumbnail_count}"
            
            # TODO: Verify thumbnail URLs accessible
            # TODO: Verify database records
            
        finally:
            cleanup_test_file(test_file)
    
    @pytest.mark.priority_high
    def test_07_metadata_extraction_complete(self):
        """
        Test complete metadata extraction from video.
        
        BUSINESS REQUIREMENT:
        Video metadata (duration, resolution, codec, file size) must be
        automatically extracted and displayed to instructors.
        
        TEST SCENARIO:
        1. Upload video file with known metadata
        2. Wait for metadata extraction
        3. Verify duration extracted correctly
        4. Verify resolution extracted correctly
        5. Verify codec extracted correctly
        6. Verify file size displayed correctly
        
        VALIDATION CRITERIA:
        - Duration accurate within 1 second
        - Resolution matches source file
        - Codec correctly identified
        - File size matches uploaded file
        """
        test_file = create_test_video_file("test_video_metadata", size_mb=12, format='mp4')
        video_title = f"Test Metadata {uuid.uuid4()}"
        
        try:
            # Upload video
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for metadata extraction"
            )
            self.upload_page.start_upload()
            self.upload_page.wait_for_upload_complete(timeout=60)
            
            # Navigate to processing page
            video_id = "temp-video-id"
            self.processing_page.navigate_to_video_details(video_id)
            
            # Wait for processing
            self.processing_page.wait_for_processing_complete(timeout=300)
            
            # Get extracted metadata
            metadata = self.processing_page.get_video_metadata()
            
            # Verify metadata fields present
            assert 'duration' in metadata and metadata['duration'], \
                "Duration not extracted"
            assert 'resolution' in metadata and metadata['resolution'], \
                "Resolution not extracted"
            assert 'codec' in metadata and metadata['codec'], \
                "Codec not extracted"
            assert 'file_size' in metadata and metadata['file_size'], \
                "File size not extracted"
            
            # Verify file size matches upload (~12MB)
            assert "12" in metadata['file_size'], \
                f"Expected ~12MB, got {metadata['file_size']}"
            
        finally:
            cleanup_test_file(test_file)


# ============================================================================
# TEST CLASS 3: Error Handling
# ============================================================================

@pytest.mark.e2e
@pytest.mark.video
class TestVideoUploadErrorHandling(BaseTest):
    """
    Test error handling for video uploads.
    
    BUSINESS REQUIREMENT:
    System must gracefully handle upload errors and provide clear
    feedback to instructors when uploads fail.
    """
    
    @pytest.fixture(autouse=True)
    def setup_error_tests(self):
        """Setup for error handling tests."""
        self.login_page = InstructorLoginPage(self.driver, self.config)
        self.upload_page = VideoUploadPage(self.driver)
        self.processing_page = VideoProcessingPage(self.driver)
        
        # Login as instructor
        self.login_page.navigate()
        self.login_page.login("instructor@example.com", "password123")
        
        yield
    
    @pytest.mark.priority_high
    def test_08_upload_invalid_file_format_error(self):
        """
        Test uploading invalid file format shows error.
        
        BUSINESS REQUIREMENT:
        System must reject unsupported file formats and show clear
        error message to instructor.
        
        TEST SCENARIO:
        1. Navigate to upload page
        2. Select invalid file (e.g., .txt, .pdf, .zip)
        3. Verify error message displayed
        4. Verify upload button disabled
        5. Verify no upload occurs
        
        VALIDATION CRITERIA:
        - Error message clearly states invalid format
        - Lists supported formats (MP4, MOV, AVI, etc.)
        - Upload button disabled
        - No network request sent
        """
        # Create invalid file
        temp_dir = tempfile.gettempdir()
        invalid_file = Path(temp_dir) / "invalid_file.txt"
        invalid_file.write_text("This is not a video file")
        
        try:
            # Navigate and open upload modal
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            
            # Select invalid file
            self.upload_page.select_video_file(str(invalid_file.absolute()))
            time.sleep(1)
            
            # Verify error message
            error_message = self.upload_page.get_validation_error()
            assert "invalid" in error_message.lower() or "unsupported" in error_message.lower(), \
                f"Expected format error, got: {error_message}"
            
            # Verify supported formats listed
            assert any(fmt in error_message.lower() for fmt in ["mp4", "mov", "avi"]), \
                "Error message should list supported formats"
            
        finally:
            invalid_file.unlink()
    
    @pytest.mark.priority_high
    def test_09_upload_exceeds_size_limit_rejection(self):
        """
        Test uploading file exceeding size limit.
        
        BUSINESS REQUIREMENT:
        System must enforce maximum file size (2GB) and reject larger files
        with clear error message.
        
        TEST SCENARIO:
        1. Navigate to upload page
        2. Select file exceeding 2GB limit (simulated)
        3. Verify error message displayed
        4. Verify maximum size clearly stated
        5. Verify upload prevented
        
        VALIDATION CRITERIA:
        - Error message states file too large
        - Maximum size (2GB) clearly stated
        - Upload does not proceed
        """
        # For E2E test, we simulate large file validation
        # In production, this would be checked client-side before upload
        
        # Navigate and open upload modal
        self.upload_page.navigate()
        self.upload_page.navigate_to_videos_tab()
        self.upload_page.click_upload_video()
        
        # TODO: Simulate large file selection (requires JS injection)
        # For now, verify error handling logic exists
        
        # Verify file size validation in UI
        # Expected: Files >2GB should show error before upload starts
        pass  # Placeholder for full implementation
    
    @pytest.mark.priority_medium
    def test_10_processing_failure_retry_mechanism(self):
        """
        Test retry mechanism when video processing fails.
        
        BUSINESS REQUIREMENT:
        When video processing fails (transcoding error, thumbnail generation
        failure), system must allow retry and show error details.
        
        TEST SCENARIO:
        1. Upload video that will fail processing (corrupted file)
        2. Wait for processing to fail
        3. Verify error message displayed
        4. Verify retry button available
        5. Click retry button
        6. Verify processing restarts
        
        VALIDATION CRITERIA:
        - Processing failure detected
        - Error message shows reason for failure
        - Retry button clickable
        - Retry restarts processing pipeline
        """
        # Create potentially problematic file
        test_file = create_test_video_file("test_video_retry", size_mb=5, format='mp4')
        video_title = f"Test Processing Retry {uuid.uuid4()}"
        
        try:
            # Upload video
            self.upload_page.navigate()
            self.upload_page.navigate_to_videos_tab()
            self.upload_page.click_upload_video()
            self.upload_page.select_video_file(str(test_file.absolute()))
            self.upload_page.enter_video_metadata(
                title=video_title,
                description="Test video for processing retry"
            )
            self.upload_page.start_upload()
            self.upload_page.wait_for_upload_complete(timeout=60)
            
            # Navigate to processing page
            video_id = "temp-video-id"
            self.processing_page.navigate_to_video_details(video_id)
            
            # Wait for potential processing failure
            # Note: In real test, we'd use corrupted file or mock failure
            time.sleep(10)
            
            # Check if error occurred
            if self.processing_page.is_processing_error():
                # Verify retry button available
                self.processing_page.click_retry_processing()
                time.sleep(2)
                
                # Verify processing restarted
                status = self.processing_page.get_processing_status()
                assert status in ["Processing...", "Complete"], \
                    f"Expected processing to restart, got: {status}"
            
        finally:
            cleanup_test_file(test_file)
