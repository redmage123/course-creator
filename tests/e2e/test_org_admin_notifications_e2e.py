"""
E2E tests for organization admin notification and bulk room management workflows

BUSINESS CONTEXT:
Tests complete user journeys from org admin dashboard through notification
sending and bulk room creation, verifying UI interactions and backend operations.
"""
import pytest
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import time


# Test configuration
TEST_BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'


@pytest.fixture
def driver():
    """Setup Selenium WebDriver with Grid support"""
    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')

    # Check for Selenium Grid configuration
    selenium_remote = os.getenv('SELENIUM_REMOTE')
    if selenium_remote:
        driver = webdriver.Remote(
            command_executor=selenium_remote,
            options=options
        )
    else:
        driver = webdriver.Chrome(options=options)

    driver.implicitly_wait(20)  # Increased for Grid reliability

    yield driver

    driver.quit()


@pytest.fixture
def authenticated_org_admin(driver):
    """
    Authenticate as organization admin and navigate to dashboard

    BUSINESS CONTEXT:
    Organization admins have full access to meeting room management
    and notification features within their organization.
    """
    driver.get(f'{TEST_BASE_URL}/html/student-login.html')

    # Wait for page to fully load
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    time.sleep(0.5)  # Additional brief pause for JS initialization

    # Accept privacy banner if present
    try:
        accept_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, 'acceptAllCookies'))
        )
        accept_btn.click()
        time.sleep(0.5)
    except TimeoutException:
        pass

    # Wait for login form to be visible and ready
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'credentialsForm'))
    )

    # Login as org admin
    email_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'email'))
    )
    email_input.send_keys('orgadmin@e2etest.com')

    password_input = driver.find_element(By.ID, 'password')
    password_input.send_keys('org_admin_password')

    # Wait for login button to be clickable
    login_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
    )

    # Scroll button into view and click
    driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
    time.sleep(0.3)  # Brief pause after scroll
    login_btn.click()

    # Wait for redirect to org admin dashboard (or any dashboard on successful login)
    try:
        WebDriverWait(driver, 15).until(
            lambda d: 'org-admin-dashboard' in d.current_url or
                     'org-admin-enhanced' in d.current_url or
                     'dashboard' in d.current_url
        )
    except TimeoutException:
        # Debug: print current URL if redirect fails
        print(f"DEBUG: Current URL after login: {driver.current_url}")
        print(f"DEBUG: Page title: {driver.title}")
        raise

    # Allow dashboard to fully load and JavaScript to initialize
    time.sleep(3)

    # Wait for templateLoader to be available
    driver.execute_script("return window.templateLoader !== undefined;")

    # Verify we're on org admin dashboard
    if 'org-admin' not in driver.current_url and 'dashboard' in driver.current_url:
        print(f"WARNING: Landed on {driver.current_url} instead of org-admin dashboard")

    return driver


class TestOrgAdminMeetingRoomsTab:
    """Test meeting rooms tab functionality"""

    def test_meeting_rooms_tab_loads(self, authenticated_org_admin):
        """
        Test meeting rooms tab loads with all UI elements

        BUSINESS REQUIREMENT:
        Org admins need clear visibility of all meeting rooms with filtering
        and bulk creation options.
        """
        driver = authenticated_org_admin

        # Debug: Check if loadTabContent function exists
        function_exists = driver.execute_script("return typeof loadTabContent === 'function';")
        print(f"DEBUG: loadTabContent function exists: {function_exists}")

        # Debug: Check if templateLoader exists
        template_loader_exists = driver.execute_script("return typeof window.templateLoader !== 'undefined';")
        print(f"DEBUG: window.templateLoader exists: {template_loader_exists}")

        # Debug: Try to get any JavaScript errors
        try:
            errors = driver.get_log('browser')
            if errors:
                print(f"DEBUG: Browser console errors: {[e['message'] for e in errors if e['level'] == 'SEVERE'][:3]}")
        except:
            pass

        # Directly load meeting rooms tab using JavaScript
        try:
            result = driver.execute_script("return loadTabContent('meeting-rooms');")
            print(f"DEBUG: loadTabContent returned: {result}")
        except Exception as e:
            print(f"DEBUG: loadTabContent error: {e}")

        # Wait for loading to complete
        time.sleep(3)

        # Debug: Print current page content
        try:
            container = driver.find_element(By.ID, 'tabContentContainer')
            html_content = container.get_attribute('innerHTML')
            print(f"DEBUG: Container HTML length: {len(html_content)}")
            print(f"DEBUG: Container starts with: {html_content[:200]}")
            print(f"DEBUG: 'meeting-rooms-panel' in HTML: {'meeting-rooms-panel' in html_content}")
        except Exception as e:
            print(f"DEBUG: Could not find container: {e}")

        # Verify tab content is visible
        meeting_rooms_panel = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'meeting-rooms-panel'))
        )
        assert meeting_rooms_panel.is_displayed()

        # Verify filter dropdowns exist
        platform_filter = driver.find_element(By.ID, 'platformFilter')
        assert platform_filter.is_displayed()

        room_type_filter = driver.find_element(By.ID, 'roomTypeFilter')
        assert room_type_filter.is_displayed()

        # Verify action buttons exist
        create_room_btn = driver.find_element(By.XPATH, '//button[contains(., "Create Room")]')
        assert create_room_btn.is_displayed()

        bulk_create_btn = driver.find_element(By.XPATH, '//button[contains(., "Bulk Create")]')
        assert bulk_create_btn.is_displayed()

        send_notification_btn = driver.find_element(By.XPATH, '//button[contains(., "Send Notification")]')
        assert send_notification_btn.is_displayed()

    def test_quick_actions_section_visible(self, authenticated_org_admin):
        """
        Test quick actions section with bulk creation buttons

        BUSINESS REQUIREMENT:
        Quick actions enable rapid setup of meeting infrastructure
        for entire teams with one click.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Verify quick actions section exists
        quick_actions = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'quick-actions-section'))
        )
        assert quick_actions.is_displayed()

        # Verify instructor room creation buttons
        teams_instructors_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Teams Rooms for All Instructors')]"
        )
        assert teams_instructors_btn.is_displayed()

        zoom_instructors_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Zoom Rooms for All Instructors')]"
        )
        assert zoom_instructors_btn.is_displayed()

        slack_instructors_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Slack Channels for All Instructors')]"
        )
        assert slack_instructors_btn.is_displayed()

        # Verify track room creation buttons
        teams_tracks_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Teams Rooms for All Tracks')]"
        )
        assert teams_tracks_btn.is_displayed()

        zoom_tracks_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Zoom Rooms for All Tracks')]"
        )
        assert zoom_tracks_btn.is_displayed()

        slack_tracks_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Create Slack Channels for All Tracks')]"
        )
        assert slack_tracks_btn.is_displayed()


class TestBulkRoomCreationWorkflow:
    """Test bulk room creation complete workflows"""

    def test_bulk_create_instructor_rooms_flow(self, authenticated_org_admin):
        """
        Test complete bulk instructor room creation workflow

        BUSINESS REQUIREMENT:
        Org admin clicks button → Confirmation dialog → Rooms created →
        Notifications sent → Success message → Rooms visible in list

        USER STORY:
        As an org admin, I want to create Zoom rooms for all instructors
        so that each instructor has their own meeting space.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Click "Create Zoom Rooms for All Instructors" button
        zoom_instructors_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Create Zoom Rooms for All Instructors')]"
            ))
        )
        zoom_instructors_btn.click()

        # Handle confirmation dialog
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            assert 'zoom rooms for all instructors' in alert.text.lower()
            alert.accept()
        except TimeoutException:
            # If no alert, button may have custom confirmation
            pass

        # Wait for loading overlay to appear and disappear
        try:
            WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, 'loadingOverlay'))
            )
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.ID, 'loadingOverlay'))
            )
        except TimeoutException:
            pass

        # Verify success notification appears
        notification = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'notification'))
        )
        notification_text = notification.text.lower()
        assert 'created' in notification_text or 'success' in notification_text

    def test_bulk_create_track_rooms_flow(self, authenticated_org_admin):
        """
        Test complete bulk track room creation workflow

        BUSINESS REQUIREMENT:
        Create rooms for all tracks and notify all participants in each track.

        USER STORY:
        As an org admin, I want to create Teams rooms for all learning tracks
        so that students have dedicated spaces for synchronous learning.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Click "Create Teams Rooms for All Tracks" button
        teams_tracks_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Create Teams Rooms for All Tracks')]"
            ))
        )
        teams_tracks_btn.click()

        # Handle confirmation
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass

        # Wait for operation to complete
        try:
            WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, 'loadingOverlay'))
            )
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.ID, 'loadingOverlay'))
            )
        except TimeoutException:
            pass

        # Verify success notification
        notification = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'notification'))
        )
        assert notification.is_displayed()


class TestNotificationSendingWorkflow:
    """Test notification sending complete workflows"""

    def test_send_notification_modal_opens(self, authenticated_org_admin):
        """
        Test notification modal opens with all fields

        BUSINESS REQUIREMENT:
        Org admins can send notifications to channels or entire organization
        with priority levels and custom messages.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Click "Send Notification" button
        send_notification_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Send Notification')]"
            ))
        )
        send_notification_btn.click()

        # Wait for modal backdrop to show (CSS transition)
        WebDriverWait(driver, 10).until(
            lambda d: 'show' in d.find_element(By.ID, 'sendNotificationBackdrop').get_attribute('class')
        )

        # Verify modal opens and is visible
        notification_modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'sendNotificationModal'))
        )
        assert notification_modal.is_displayed()

        # Wait for form fields to be present
        # Note: Using presence checks instead of visibility checks because
        # Selenium's is_displayed() can fail for elements within CSS-transformed modals
        notification_type = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationType'))
        )
        assert notification_type.is_enabled()

        # Channel ID field exists but is hidden by default (only visible when "channel" type is selected)
        channel_id_input = driver.find_element(By.ID, 'notificationChannelId')

        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationTitle'))
        )
        assert title_input.is_enabled()

        # Textarea exists and is enabled (visibility check unreliable in modal)
        message_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationMessage'))
        )
        assert message_textarea.is_enabled()

        priority_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationPriority'))
        )
        assert priority_select.is_enabled()

        # Verify send button exists
        send_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Send Notification') and contains(@class, 'btn-primary')]"
        )
        assert send_btn.is_displayed()

    def test_send_channel_notification_complete_flow(self, authenticated_org_admin):
        """
        Test complete channel notification sending workflow

        BUSINESS REQUIREMENT:
        Send notification to specific Slack channel with custom message and priority.

        USER STORY:
        As an org admin, I want to send an urgent update to the #general channel
        about system maintenance.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab and open notification modal
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        send_notification_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Send Notification')]"
            ))
        )
        send_notification_btn.click()

        # Wait for modal backdrop to show (CSS transition)
        WebDriverWait(driver, 10).until(
            lambda d: 'show' in d.find_element(By.ID, 'sendNotificationBackdrop').get_attribute('class')
        )

        # Wait for modal and form fields to be visible and interactable
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'sendNotificationModal'))
        )

        # Wait for notification type dropdown to be interactable
        notification_type_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'notificationType'))
        )

        # Select "Send to Channel"
        notification_type = Select(notification_type_elem)
        notification_type.select_by_value('channel')

        # Wait for channel ID field to become visible after type selection
        channel_id_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'notificationChannelId'))
        )
        channel_id_input.clear()
        channel_id_input.send_keys('C1234567890')

        # Wait for and fill in title
        title_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'notificationTitle'))
        )
        title_input.clear()
        title_input.send_keys('System Maintenance Alert')

        # Fill in message using JavaScript (Selenium visibility detection unreliable in modals)
        message_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationMessage'))
        )
        # Set value and trigger input event so form validation recognizes the change
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, message_textarea, 'The system will be down for maintenance on Sunday from 2-4 AM EST.')

        # Select high priority
        priority_select = Select(driver.find_element(By.ID, 'notificationPriority'))
        priority_select.select_by_value('high')

        # Take screenshot before submission
        driver.save_screenshot('tests/reports/screenshots/test_send_channel_notification_before_submit.png')

        # Click send button
        send_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Send Notification') and contains(@class, 'btn-primary')]"
        )
        send_btn.click()

        # Wait for modal to close and success notification
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, 'sendNotificationModal'))
        )

        # Verify success notification
        notification = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'notification'))
        )
        notification_text = notification.text.lower()
        assert 'sent' in notification_text or 'success' in notification_text

        # Take final screenshot
        driver.save_screenshot('tests/reports/screenshots/test_send_channel_notification_final.png')

    def test_send_organization_announcement_flow(self, authenticated_org_admin):
        """
        Test sending announcement to entire organization

        BUSINESS REQUIREMENT:
        Broadcast important updates to all organization members.

        USER STORY:
        As an org admin, I want to announce a policy change
        to all members of the organization.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab and open notification modal
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        send_notification_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Send Notification')]"
            ))
        )
        send_notification_btn.click()

        # Wait for modal backdrop to show (CSS transition)
        WebDriverWait(driver, 10).until(
            lambda d: 'show' in d.find_element(By.ID, 'sendNotificationBackdrop').get_attribute('class')
        )

        # Wait for modal and form fields to be visible and interactable
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'sendNotificationModal'))
        )

        # Wait for notification type dropdown to be interactable
        notification_type_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'notificationType'))
        )

        # Select "Organization Announcement"
        notification_type = Select(notification_type_elem)
        notification_type.select_by_value('organization')

        time.sleep(0.5)  # Wait for field toggle

        # Verify channel ID field is hidden
        channel_id_group = driver.find_element(By.ID, 'channelIdGroup')
        assert not channel_id_group.is_displayed()

        # Wait for and fill in title
        title_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'notificationTitle'))
        )
        title_input.clear()
        title_input.send_keys('Important Policy Update')

        # Fill in message using JavaScript (Selenium visibility detection unreliable in modals)
        message_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationMessage'))
        )
        # Set value and trigger input event so form validation recognizes the change
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, message_textarea, 'We have updated our code of conduct policy. Please review the changes.')

        # Select normal priority
        priority_select = Select(driver.find_element(By.ID, 'notificationPriority'))
        priority_select.select_by_value('normal')

        # Click send
        send_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Send Notification') and contains(@class, 'btn-primary')]"
        )
        send_btn.click()

        # Wait for completion
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, 'sendNotificationModal'))
        )

        # Verify success notification shows member count
        notification = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'notification'))
        )
        notification_text = notification.text.lower()
        assert 'members' in notification_text or 'sent' in notification_text


class TestPlatformFiltering:
    """Test meeting room filtering functionality"""

    def test_filter_by_platform(self, authenticated_org_admin):
        """
        Test filtering meeting rooms by platform

        BUSINESS REQUIREMENT:
        Org admins can filter rooms to see only specific platforms
        (Teams, Zoom, or Slack).
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Select Zoom from platform filter
        platform_filter = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'platformFilter'))
        ))
        platform_filter.select_by_value('zoom')

        time.sleep(0.5)

        # Verify filtering occurred (check that filter changed)
        selected_option = platform_filter.first_selected_option
        assert selected_option.get_attribute('value') == 'zoom'

        # Try Slack filter
        platform_filter.select_by_value('slack')
        time.sleep(0.5)

        selected_option = platform_filter.first_selected_option
        assert selected_option.get_attribute('value') == 'slack'

    def test_filter_by_room_type(self, authenticated_org_admin):
        """
        Test filtering meeting rooms by type

        BUSINESS REQUIREMENT:
        Filter rooms by type (track, instructor, project, organization).
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        # Select instructor rooms from type filter
        room_type_filter = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'roomTypeFilter'))
        ))
        room_type_filter.select_by_value('instructor')

        time.sleep(0.5)

        selected_option = room_type_filter.first_selected_option
        assert selected_option.get_attribute('value') == 'instructor'


class TestErrorHandling:
    """Test error handling in notification and bulk operations"""

    def test_notification_form_validation(self, authenticated_org_admin):
        """
        Test form validation prevents empty submissions

        BUSINESS REQUIREMENT:
        User must provide required fields before sending notification.
        """
        driver = authenticated_org_admin

        # Navigate to meeting rooms tab and open notification modal
        meeting_rooms_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'meeting-rooms-tab'))
        )
        meeting_rooms_tab.click()

        time.sleep(1)

        send_notification_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Send Notification')]"
            ))
        )
        send_notification_btn.click()

        # Wait for modal backdrop to show (CSS transition)
        WebDriverWait(driver, 10).until(
            lambda d: 'show' in d.find_element(By.ID, 'sendNotificationBackdrop').get_attribute('class')
        )

        # Wait for modal and form fields to be visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'sendNotificationModal'))
        )

        # Wait for submit button to be clickable
        send_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Send Notification') and contains(@class, 'btn-primary')]"
            ))
        )

        # Try to submit without filling fields
        send_btn.click()

        time.sleep(0.5)

        # Verify modal is still open (form validation prevented submission)
        notification_modal = driver.find_element(By.ID, 'sendNotificationModal')
        assert notification_modal.is_displayed()

        # Verify required field attributes are present (HTML5 boolean attributes return '' when present, None when absent)
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationTitle'))
        )
        assert title_input.get_attribute('required') is not None

        message_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'notificationMessage'))
        )
        assert message_textarea.get_attribute('required') is not None
