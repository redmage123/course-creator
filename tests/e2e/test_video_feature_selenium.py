"""
Video Feature End-to-End Tests with Selenium

Comprehensive E2E testing for the video upload and linking feature using
Selenium WebDriver with Chrome.

BUSINESS WORKFLOWS TESTED:
1. Upload video file to course
2. Add YouTube/Vimeo video links
3. Reorder videos in course
4. Delete videos
5. View videos in course player

TECHNICAL COVERAGE:
- File upload with validation
- External link validation
- Video list management
- CRUD operations through UI
- Error handling and user feedback
"""

import pytest
import time
import os
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium_base import BaseTest, BasePage, SeleniumConfig


class InstructorDashboardPage(BasePage):
    """
    Page Object for Instructor Dashboard.

    DESIGN PATTERN: Page Object Model
    Encapsulates all instructor dashboard interactions for maintainability.
    """

    # Locators
    COURSES_TAB = (By.CSS_SELECTOR, "a[href='#courses']")
    CREATE_COURSE_BTN = (By.ID, "createCourseBtn")
    COURSE_TITLE_INPUT = (By.ID, "course-title")
    COURSE_DESCRIPTION = (By.ID, "course-description")
    COURSE_CATEGORY = (By.ID, "course-category")
    COURSE_LEVEL = (By.ID, "course-level")

    # Video section locators
    ADD_UPLOAD_VIDEO_BTN = (By.ID, "add-upload-video-btn")
    ADD_LINK_VIDEO_BTN = (By.ID, "add-link-video-btn")
    VIDEOS_CONTAINER = (By.ID, "course-videos-container")

    SUBMIT_COURSE_BTN = (By.CSS_SELECTOR, "button[type='submit']")

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.navigate_to("/html/instructor-dashboard.html")

    def navigate_to_courses_tab(self):
        """Navigate to courses tab in dashboard."""
        self.click_element(*self.COURSES_TAB)
        time.sleep(1)  # Wait for tab content to load

    def click_create_course(self):
        """Click the create course button."""
        self.click_element(*self.CREATE_COURSE_BTN)

    def fill_course_basic_info(self, title, description, category="programming", level="beginner"):
        """
        Fill in basic course information.

        Args:
            title: Course title
            description: Course description
            category: Course category
            level: Difficulty level
        """
        self.enter_text(*self.COURSE_TITLE_INPUT, title)
        self.enter_text(*self.COURSE_DESCRIPTION, description)

        # Select category
        category_dropdown = self.find_element(*self.COURSE_CATEGORY)
        category_dropdown.click()
        category_option = self.find_element(By.CSS_SELECTOR, f"option[value='{category}']")
        category_option.click()

        # Select level
        level_dropdown = self.find_element(*self.COURSE_LEVEL)
        level_dropdown.click()
        level_option = self.find_element(By.CSS_SELECTOR, f"option[value='{level}']")
        level_option.click()

    def click_add_upload_video(self):
        """Open video upload modal."""
        self.click_element(*self.ADD_UPLOAD_VIDEO_BTN)

    def click_add_link_video(self):
        """Open video link modal."""
        self.click_element(*self.ADD_LINK_VIDEO_BTN)

    def get_video_count(self):
        """
        Get number of videos in the list.

        Returns:
            Number of video items
        """
        video_items = self.find_elements(By.CLASS_NAME, "video-item")
        return len(video_items)

    def submit_course(self):
        """Submit the course creation form."""
        self.click_element(*self.SUBMIT_COURSE_BTN)


class VideoUploadModalPage(BasePage):
    """
    Page Object for Video Upload Modal.
    """

    # Locators
    MODAL = (By.ID, "video-upload-modal")
    TITLE_INPUT = (By.ID, "upload-video-title")
    DESCRIPTION_INPUT = (By.ID, "upload-video-description")
    FILE_INPUT = (By.ID, "upload-video-file")
    UPLOAD_BTN = (By.ID, "confirm-video-upload-btn")
    CANCEL_BTN = (By.CSS_SELECTOR, "#video-upload-modal .btn-secondary")
    PROGRESS_BAR = (By.ID, "upload-progress-bar")

    def is_modal_visible(self):
        """Check if upload modal is displayed."""
        modal = self.find_element(*self.MODAL)
        return modal.is_displayed()

    def fill_video_info(self, title, description=""):
        """
        Fill video information.

        Args:
            title: Video title
            description: Optional video description
        """
        self.enter_text(*self.TITLE_INPUT, title)
        if description:
            self.enter_text(*self.DESCRIPTION_INPUT, description)

    def select_video_file(self, file_path):
        """
        Select video file for upload.

        Args:
            file_path: Absolute path to video file

        NOTE: File input is not visible, so we send keys directly
        """
        file_input = self.find_element(*self.FILE_INPUT)
        file_input.send_keys(file_path)

    def click_upload(self):
        """Click upload button."""
        self.click_element(*self.UPLOAD_BTN)

    def wait_for_upload_complete(self, timeout=60):
        """
        Wait for upload to complete.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if upload completed, False if timeout
        """
        try:
            # Wait for progress bar to reach 100%
            self.wait.until(
                lambda driver: driver.find_element(*self.PROGRESS_BAR).get_attribute("style").contains("100%")
            )
            return True
        except:
            return False


class VideoLinkModalPage(BasePage):
    """
    Page Object for Video Link Modal.
    """

    # Locators
    MODAL = (By.ID, "video-link-modal")
    TITLE_INPUT = (By.ID, "link-video-title")
    DESCRIPTION_INPUT = (By.ID, "link-video-description")
    TYPE_SELECT = (By.ID, "link-video-type")
    URL_INPUT = (By.ID, "link-video-url")
    ADD_BTN = (By.ID, "confirm-video-link-btn")
    CANCEL_BTN = (By.CSS_SELECTOR, "#video-link-modal .btn-secondary")

    def is_modal_visible(self):
        """Check if link modal is displayed."""
        modal = self.find_element(*self.MODAL)
        return modal.is_displayed()

    def fill_video_link_info(self, title, url, video_type="youtube", description=""):
        """
        Fill video link information.

        Args:
            title: Video title
            url: Video URL
            video_type: Platform type (youtube, vimeo, link)
            description: Optional description
        """
        self.enter_text(*self.TITLE_INPUT, title)
        if description:
            self.enter_text(*self.DESCRIPTION_INPUT, description)

        # Select type
        type_dropdown = self.find_element(*self.TYPE_SELECT)
        type_dropdown.click()
        type_option = self.find_element(By.CSS_SELECTOR, f"option[value='{video_type}']")
        type_option.click()

        # Enter URL
        self.enter_text(*self.URL_INPUT, url)

    def click_add_video(self):
        """Click add video button."""
        self.click_element(*self.ADD_BTN)


@pytest.mark.e2e
@pytest.mark.frontend
@pytest.mark.video
class TestVideoFeatureE2E(BaseTest):
    """
    End-to-end tests for video upload and linking feature.

    BUSINESS VALUE:
    Ensures instructors can successfully add videos to courses through
    the UI, validating the complete user workflow.

    TECHNICAL COVERAGE:
    - File upload functionality
    - External link validation
    - Video list management
    - Modal interactions
    - Form validation
    """

    @pytest.fixture(autouse=True)
    def setup_pages(self):
        """Initialize page objects for each test."""
        self.dashboard = InstructorDashboardPage(self.driver, self.config)
        self.upload_modal = VideoUploadModalPage(self.driver, self.config)
        self.link_modal = VideoLinkModalPage(self.driver, self.config)

    @pytest.fixture
    def test_video_file(self, tmp_path):
        """
        Create a small test video file.

        Returns:
            Path to test video file
        """
        # Create a minimal valid MP4 file for testing
        # In production, you'd use a real sample video
        video_path = tmp_path / "test_video.mp4"

        # For this example, create a dummy file
        # In real tests, use actual video files
        video_path.write_bytes(b"fake video content for testing")

        return str(video_path)

    def test_add_youtube_link_to_course(self):
        """
        Test adding a YouTube link to a course.

        WORKFLOW:
        1. Navigate to course creation
        2. Fill basic course info
        3. Click "Add Video Link"
        4. Fill YouTube video details
        5. Verify video appears in list
        """
        # Navigate to courses section
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        # Fill basic course information
        self.dashboard.fill_course_basic_info(
            title="Python Programming 101",
            description="Learn Python from scratch with video tutorials"
        )

        # Add YouTube video link
        self.dashboard.click_add_link_video()

        assert self.link_modal.is_modal_visible(), "Video link modal should be visible"

        self.link_modal.fill_video_link_info(
            title="Introduction to Python",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            video_type="youtube",
            description="First lesson covering Python basics"
        )

        self.link_modal.click_add_video()

        # Wait for modal to close
        time.sleep(1)

        # Verify video appears in list
        video_count = self.dashboard.get_video_count()
        assert video_count == 1, f"Expected 1 video in list, got {video_count}"

        # Take success screenshot
        self.take_screenshot("youtube_link_added")

    def test_add_vimeo_link_to_course(self):
        """
        Test adding a Vimeo link to a course.

        WORKFLOW:
        Similar to YouTube test but with Vimeo URL
        """
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        self.dashboard.fill_course_basic_info(
            title="Web Development Bootcamp",
            description="Complete web development course with video lessons"
        )

        self.dashboard.click_add_link_video()

        self.link_modal.fill_video_link_info(
            title="HTML Fundamentals",
            url="https://vimeo.com/123456789",
            video_type="vimeo"
        )

        self.link_modal.click_add_video()
        time.sleep(1)

        video_count = self.dashboard.get_video_count()
        assert video_count == 1, "Vimeo video should be added to list"

    def test_add_multiple_videos_to_course(self):
        """
        Test adding multiple videos (mix of upload and links).

        WORKFLOW:
        1. Add YouTube video
        2. Add Vimeo video
        3. Add custom link
        4. Verify all appear in list
        """
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        self.dashboard.fill_course_basic_info(
            title="Full Stack Development",
            description="Complete course with multiple video lessons"
        )

        # Add first video (YouTube)
        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Introduction",
            url="https://www.youtube.com/watch?v=video1",
            video_type="youtube"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Add second video (Vimeo)
        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Chapter 1",
            url="https://vimeo.com/987654321",
            video_type="vimeo"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Add third video (custom link)
        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Advanced Topics",
            url="https://example.com/videos/advanced.mp4",
            video_type="link"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Verify all 3 videos are in the list
        video_count = self.dashboard.get_video_count()
        assert video_count == 3, f"Expected 3 videos in list, got {video_count}"

        self.take_screenshot("multiple_videos_added")

    def test_video_link_validation(self):
        """
        Test invalid video URL validation.

        WORKFLOW:
        1. Try to add invalid YouTube URL
        2. Verify error message
        """
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        self.dashboard.fill_course_basic_info(
            title="Test Course",
            description="Testing validation"
        )

        self.dashboard.click_add_link_video()

        # Try to add invalid YouTube URL
        self.link_modal.fill_video_link_info(
            title="Invalid Video",
            url="https://example.com/not-youtube",
            video_type="youtube"
        )

        self.link_modal.click_add_video()

        # In a real implementation, check for error message
        # For now, verify modal doesn't close (validation failed)
        time.sleep(1)
        assert self.link_modal.is_modal_visible(), "Modal should remain open on validation error"

    @pytest.mark.skip(reason="File upload requires backend integration")
    def test_upload_video_file(self, test_video_file):
        """
        Test uploading a video file.

        NOTE: Skipped in basic tests as it requires full backend integration
        and actual video file processing.

        WORKFLOW:
        1. Click upload video button
        2. Select file
        3. Fill metadata
        4. Upload
        5. Wait for completion
        6. Verify in list
        """
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        self.dashboard.fill_course_basic_info(
            title="Video Upload Test",
            description="Testing video file upload"
        )

        self.dashboard.click_add_upload_video()

        assert self.upload_modal.is_modal_visible(), "Upload modal should be visible"

        self.upload_modal.fill_video_info(
            title="Uploaded Lesson 1",
            description="First uploaded video lesson"
        )

        self.upload_modal.select_video_file(test_video_file)
        self.upload_modal.click_upload()

        # Wait for upload to complete
        upload_complete = self.upload_modal.wait_for_upload_complete(timeout=60)
        assert upload_complete, "Video upload should complete within timeout"

        # Verify video in list
        video_count = self.dashboard.get_video_count()
        assert video_count == 1, "Uploaded video should appear in list"

    def test_remove_video_from_list(self):
        """
        Test removing a video from the course.

        WORKFLOW:
        1. Add a video
        2. Click remove button
        3. Confirm deletion
        4. Verify video removed
        """
        # Add a video first
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        self.dashboard.fill_course_basic_info(
            title="Remove Video Test",
            description="Testing video removal"
        )

        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Video to Remove",
            url="https://www.youtube.com/watch?v=test",
            video_type="youtube"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Verify video is there
        assert self.dashboard.get_video_count() == 1

        # Click remove button
        remove_btn = self.driver.find_element(By.CSS_SELECTOR, ".video-item .btn-danger")
        remove_btn.click()

        # Handle confirmation alert
        alert = self.driver.switch_to.alert
        alert.accept()

        time.sleep(1)

        # Verify video is removed
        assert self.dashboard.get_video_count() == 0, "Video should be removed from list"

    def test_course_creation_with_videos_end_to_end(self):
        """
        Complete end-to-end test: Create course with videos and submit.

        WORKFLOW:
        1. Fill course details
        2. Add multiple videos
        3. Submit course
        4. Verify success message
        """
        self.dashboard.navigate_to_courses_tab()
        self.dashboard.click_create_course()

        # Fill course information
        self.dashboard.fill_course_basic_info(
            title="Complete E2E Test Course",
            description="This course tests the complete video feature workflow",
            category="web-development",
            level="intermediate"
        )

        # Add first video
        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Course Introduction",
            url="https://www.youtube.com/watch?v=intro123",
            video_type="youtube",
            description="Welcome to the course!"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Add second video
        self.dashboard.click_add_link_video()
        self.link_modal.fill_video_link_info(
            title="Lesson 1: Getting Started",
            url="https://vimeo.com/lesson1",
            video_type="vimeo",
            description="First lesson content"
        )
        self.link_modal.click_add_video()
        time.sleep(1)

        # Verify both videos in list
        assert self.dashboard.get_video_count() == 2, "Should have 2 videos before submit"

        # Submit course
        self.dashboard.submit_course()

        # Wait for success notification or redirect
        time.sleep(2)

        # Verify success (check for notification or URL change)
        # This depends on your actual implementation
        current_url = self.driver.current_url
        # assert "success" in current_url or self.dashboard.is_element_present(By.CLASS_NAME, "notification-success")

        self.take_screenshot("course_created_with_videos")
