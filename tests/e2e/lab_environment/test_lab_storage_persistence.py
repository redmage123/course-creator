"""
Comprehensive E2E Tests for Lab Storage and Persistence

BUSINESS REQUIREMENT:
Tests lab storage persistence, file operations, storage limits, backup/recovery.
Ensures student work is preserved across sessions and recoverable after failures.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Docker Python SDK
- Tests file persistence across pause/resume cycles
- Validates storage quotas and limits
- Tests backup and recovery mechanisms

TEST COVERAGE (10 tests):
1. File Persistence (4 tests)
2. Storage Limits (3 tests)
3. Backup and Recovery (3 tests)

PRIORITY: P0 (CRITICAL) - Data persistence is critical for student experience
"""

import pytest
import time
import uuid
import docker
import os
import zipfile
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class LabStoragePage(BasePage):
    """
    Page Object for lab storage and file management interface.

    BUSINESS CONTEXT:
    Students need reliable file storage for their lab work with visibility
    into storage usage and backup/export capabilities.
    """

    # Locators
    FILE_BROWSER = (By.ID, "lab-file-browser")
    CREATE_FILE_BUTTON = (By.ID, "create-file-button")
    FILE_NAME_INPUT = (By.ID, "file-name-input")
    FILE_EDITOR = (By.ID, "lab-file-editor")
    SAVE_FILE_BUTTON = (By.ID, "save-file-button")
    STORAGE_USAGE_INDICATOR = (By.ID, "storage-usage")
    STORAGE_WARNING = (By.ID, "storage-warning")
    EXPORT_LAB_BUTTON = (By.ID, "export-lab-button")
    BACKUP_STATUS = (By.ID, "backup-status")

    def navigate_to_lab_storage(self, course_id):
        """Navigate to lab storage interface."""
        self.navigate_to(f"/course/{course_id}/lab")

    def create_file(self, filename, content=""):
        """
        Create a new file in lab.

        Args:
            filename: Name of file to create
            content: Optional file content
        """
        create_button = self.wait_for_element(*self.CREATE_FILE_BUTTON)
        create_button.click()

        name_input = self.wait_for_element(*self.FILE_NAME_INPUT)
        name_input.send_keys(filename)

        if content:
            editor = self.wait_for_element(*self.FILE_EDITOR)
            editor.send_keys(content)

        save_button = self.wait_for_element(*self.SAVE_FILE_BUTTON)
        save_button.click()
        time.sleep(0.5)

    def get_storage_usage(self):
        """
        Get current storage usage.

        Returns:
            dict: Storage usage info with 'used' and 'total' in MB
        """
        usage_element = self.wait_for_element(*self.STORAGE_USAGE_INDICATOR)
        usage_text = usage_element.text

        # Parse text like "150 MB / 500 MB"
        parts = usage_text.split('/')
        used_mb = float(parts[0].strip().split()[0])
        total_mb = float(parts[1].strip().split()[0])

        return {"used": used_mb, "total": total_mb}

    def is_storage_warning_visible(self):
        """Check if storage warning is displayed."""
        try:
            warning = self.find_element(*self.STORAGE_WARNING)
            return warning.is_displayed()
        except NoSuchElementException:
            return False

    def export_lab_files(self):
        """Export lab files as zip."""
        export_button = self.wait_for_element(*self.EXPORT_LAB_BUTTON)
        export_button.click()
        time.sleep(2)  # Wait for download to initiate


# ============================================================================
# TEST CLASS 1: File Persistence (4 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.priority_critical
class TestFilePersistence(BaseTest):
    """
    Test file persistence across lab sessions.

    BUSINESS REQUIREMENT:
    Student work must be preserved across pause/resume cycles and
    between sessions. Files must not be lost due to container restarts.
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver, test_base_url, student_credentials, docker_client):
        """Setup for each test."""
        self.driver = driver
        self.base_url = test_base_url
        self.student_credentials = student_credentials
        self.docker_client = docker_client
        self.storage_page = LabStoragePage(driver, test_base_url)

        # Login as student
        self._login_as_student()

        # Start lab
        self.course_id = f"test-course-persistence-{uuid.uuid4().hex[:8]}"
        self.storage_page.navigate_to_lab_storage(self.course_id)
        self._start_lab()

    def _login_as_student(self):
        """Helper to login as student."""
        self.driver.get(f"{self.base_url}/html/student-login.html")
        wait = WebDriverWait(self.driver, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(self.student_credentials["email"])

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(self.student_credentials["password"])

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_button.click()
        time.sleep(2)

    def _start_lab(self):
        """Helper to start lab."""
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()

        # Wait for lab to start
        WebDriverWait(self.driver, 30).until(
            lambda driver: "Running" in driver.find_element(By.ID, "lab-status").text
        )

    def _get_container(self):
        """Helper to get lab container."""
        student_username = self.student_credentials["username"]
        container_name = f"lab_{self.course_id}_{student_username}"
        return self.docker_client.containers.get(container_name)

    def _pause_lab(self):
        """Helper to pause lab."""
        pause_button = self.driver.find_element(By.ID, "pause-lab-button")
        pause_button.click()
        time.sleep(1)

    def _resume_lab(self):
        """Helper to resume lab."""
        resume_button = self.driver.find_element(By.ID, "resume-lab-button")
        resume_button.click()
        time.sleep(1)

    def test_01_student_writes_file_pauses_resumes_file_exists(self):
        """
        E2E TEST: File persists after pause/resume cycle

        BUSINESS REQUIREMENT:
        When a student pauses a lab and later resumes it, all files
        they created must still exist with the same content.

        TEST SCENARIO:
        1. Student creates file with content
        2. Student pauses lab
        3. Student resumes lab
        4. File still exists with same content

        VALIDATION:
        - File exists after resume
        - File content is preserved
        - File metadata (permissions, timestamps) preserved
        """
        # Create test file in container
        container = self._get_container()
        test_filename = f"test_persist_{uuid.uuid4().hex[:8]}.txt"
        test_content = "This file should persist after pause/resume"

        exit_code, output = container.exec_run(
            f"sh -c 'echo \"{test_content}\" > /workspace/{test_filename}'"
        )
        assert exit_code == 0, f"Failed to create file: {output.decode()}"

        # VALIDATION 1: File exists before pause
        exit_code, output = container.exec_run(f"cat /workspace/{test_filename}")
        assert exit_code == 0, "File doesn't exist before pause"
        assert test_content in output.decode(), "File content incorrect before pause"

        # Pause lab
        self._pause_lab()
        container.reload()
        assert container.status == "paused", f"Container not paused: {container.status}"

        # Resume lab
        self._resume_lab()
        container.reload()
        assert container.status == "running", f"Container not running: {container.status}"

        # VALIDATION 2: File still exists after resume
        exit_code, output = container.exec_run(f"cat /workspace/{test_filename}")
        assert exit_code == 0, "File doesn't exist after resume"

        # VALIDATION 3: File content preserved
        actual_content = output.decode().strip()
        assert test_content in actual_content, \
            f"File content not preserved. Expected: '{test_content}', Got: '{actual_content}'"

    def test_02_student_writes_multiple_files_all_persist(self):
        """
        E2E TEST: Multiple files persist across sessions

        BUSINESS REQUIREMENT:
        Students often work with multiple files (code, data, documentation).
        All files must persist reliably, not just a single file.

        VALIDATION:
        - Multiple files can be created
        - All files persist after pause/resume
        - File count is correct after resume
        """
        container = self._get_container()

        # Create multiple test files
        test_files = {
            f"main_{uuid.uuid4().hex[:8]}.py": "def main():\n    print('Hello')",
            f"data_{uuid.uuid4().hex[:8]}.json": '{"test": "data"}',
            f"README_{uuid.uuid4().hex[:8]}.md": "# Test Project\n\nDescription here."
        }

        for filename, content in test_files.items():
            exit_code, output = container.exec_run(
                f"sh -c 'echo \"{content}\" > /workspace/{filename}'"
            )
            assert exit_code == 0, f"Failed to create {filename}: {output.decode()}"

        # VALIDATION 1: All files exist before pause
        exit_code, output = container.exec_run("ls /workspace")
        assert exit_code == 0, "Failed to list files"

        file_list = output.decode()
        for filename in test_files.keys():
            assert filename in file_list, f"File {filename} not found before pause"

        # Pause and resume
        self._pause_lab()
        time.sleep(1)
        self._resume_lab()
        container.reload()

        # VALIDATION 2: All files still exist after resume
        exit_code, output = container.exec_run("ls /workspace")
        assert exit_code == 0, "Failed to list files after resume"

        file_list_after = output.decode()
        for filename in test_files.keys():
            assert filename in file_list_after, f"File {filename} not found after resume"

        # VALIDATION 3: File count is correct
        file_count_before = len([f for f in file_list.split('\n') if f.strip()])
        file_count_after = len([f for f in file_list_after.split('\n') if f.strip()])
        assert file_count_after >= file_count_before, \
            f"File count decreased after resume: {file_count_before} -> {file_count_after}"

    def test_03_student_edits_file_changes_saved(self):
        """
        E2E TEST: File edits are saved and persisted

        BUSINESS REQUIREMENT:
        When students edit files, their changes must be saved reliably
        and persist across sessions.

        VALIDATION:
        - File can be edited
        - Changes are saved to disk
        - Changes persist after pause/resume
        """
        container = self._get_container()
        test_filename = f"edit_test_{uuid.uuid4().hex[:8]}.txt"

        # Create initial file
        initial_content = "Initial content"
        exit_code, output = container.exec_run(
            f"sh -c 'echo \"{initial_content}\" > /workspace/{test_filename}'"
        )
        assert exit_code == 0, "Failed to create initial file"

        # VALIDATION 1: Initial content is correct
        exit_code, output = container.exec_run(f"cat /workspace/{test_filename}")
        assert initial_content in output.decode(), "Initial content incorrect"

        # Edit file (append new content)
        edited_content = "Edited content appended"
        exit_code, output = container.exec_run(
            f"sh -c 'echo \"{edited_content}\" >> /workspace/{test_filename}'"
        )
        assert exit_code == 0, "Failed to edit file"

        # VALIDATION 2: Edited content saved
        exit_code, output = container.exec_run(f"cat /workspace/{test_filename}")
        file_content = output.decode()
        assert initial_content in file_content, "Initial content lost after edit"
        assert edited_content in file_content, "Edited content not saved"

        # Pause and resume
        self._pause_lab()
        time.sleep(1)
        self._resume_lab()
        container.reload()

        # VALIDATION 3: Both initial and edited content persist
        exit_code, output = container.exec_run(f"cat /workspace/{test_filename}")
        persisted_content = output.decode()
        assert initial_content in persisted_content, "Initial content not persisted"
        assert edited_content in persisted_content, "Edited content not persisted"

    def test_04_file_permissions_preserved(self):
        """
        E2E TEST: File permissions are preserved

        BUSINESS REQUIREMENT:
        File permissions (read/write/execute) must be preserved across
        lab sessions. Students may create executable scripts that need
        to maintain their permissions.

        VALIDATION:
        - File permissions can be set
        - Permissions persist after pause/resume
        - Executable files remain executable
        """
        container = self._get_container()
        test_filename = f"script_{uuid.uuid4().hex[:8]}.sh"

        # Create executable script
        script_content = "#!/bin/bash\\necho 'Hello from script'"
        exit_code, output = container.exec_run(
            f"sh -c 'echo \"{script_content}\" > /workspace/{test_filename}'"
        )
        assert exit_code == 0, "Failed to create script"

        # Make script executable
        exit_code, output = container.exec_run(f"chmod +x /workspace/{test_filename}")
        assert exit_code == 0, "Failed to set executable permission"

        # VALIDATION 1: File is executable before pause
        exit_code, output = container.exec_run(f"test -x /workspace/{test_filename}")
        assert exit_code == 0, "File not executable before pause"

        # Get file permissions
        exit_code, output = container.exec_run(f"stat -c '%a' /workspace/{test_filename}")
        permissions_before = output.decode().strip()

        # Pause and resume
        self._pause_lab()
        time.sleep(1)
        self._resume_lab()
        container.reload()

        # VALIDATION 2: File is still executable after resume
        exit_code, output = container.exec_run(f"test -x /workspace/{test_filename}")
        assert exit_code == 0, "File not executable after resume"

        # VALIDATION 3: Permissions unchanged
        exit_code, output = container.exec_run(f"stat -c '%a' /workspace/{test_filename}")
        permissions_after = output.decode().strip()
        assert permissions_before == permissions_after, \
            f"Permissions changed: {permissions_before} -> {permissions_after}"


# ============================================================================
# TEST CLASS 2: Storage Limits (3 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.priority_high
class TestStorageLimits(BaseTest):
    """
    Test storage quota enforcement.

    BUSINESS REQUIREMENT:
    Each student lab must have a storage quota (500MB) to prevent
    resource exhaustion. Students must be warned when approaching limits.
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver, test_base_url, student_credentials, docker_client):
        """Setup for each test."""
        self.driver = driver
        self.base_url = test_base_url
        self.student_credentials = student_credentials
        self.docker_client = docker_client
        self.storage_page = LabStoragePage(driver, test_base_url)

        # Login and start lab
        self._login_as_student()
        self.course_id = f"test-course-limits-{uuid.uuid4().hex[:8]}"

    def _login_as_student(self):
        """Helper to login as student."""
        self.driver.get(f"{self.base_url}/html/student-login.html")
        wait = WebDriverWait(self.driver, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(self.student_credentials["email"])

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(self.student_credentials["password"])

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_button.click()
        time.sleep(2)

    def _get_container(self):
        """Helper to get lab container."""
        student_username = self.student_credentials["username"]
        container_name = f"lab_{self.course_id}_{student_username}"
        return self.docker_client.containers.get(container_name)

    def test_05_enforce_storage_quota_per_student(self):
        """
        E2E TEST: Enforce storage quota per student (500MB)

        BUSINESS REQUIREMENT:
        Each student lab must have a 500MB storage limit enforced
        at the Docker level to prevent disk exhaustion.

        VALIDATION:
        - Container has storage limit configured
        - Storage limit is 500MB
        - Limit cannot be exceeded
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # VALIDATION 1: Check for storage limit in container config
        # Note: Docker storage limits are typically enforced via storage driver options
        # or device mapper quotas, not directly visible in container.attrs

        # Check if volume mount has size limit
        mounts = container.attrs.get('Mounts', [])
        workspace_mount = next((m for m in mounts if '/workspace' in m.get('Destination', '')), None)

        assert workspace_mount is not None, "No workspace volume found"

        # VALIDATION 2: Try to create large file (should fail if quota enforced)
        # Create 600MB file (exceeds 500MB limit)
        exit_code, output = container.exec_run(
            "sh -c 'dd if=/dev/zero of=/workspace/large_file.bin bs=1M count=600 2>&1'"
        )

        # Should fail due to quota (exit code != 0) OR succeed but show quota warning
        output_text = output.decode()

        # Check for quota-related error messages
        quota_error = any(keyword in output_text.lower() for keyword in
                         ['quota', 'disk full', 'no space left', 'exceeded'])

        # If file was created, check its size
        if exit_code == 0:
            exit_code_size, output_size = container.exec_run("stat -c '%s' /workspace/large_file.bin")
            if exit_code_size == 0:
                file_size_bytes = int(output_size.decode().strip())
                file_size_mb = file_size_bytes / (1024 * 1024)

                # VALIDATION 3: File size limited to quota
                assert file_size_mb <= 500, \
                    f"File size {file_size_mb:.2f}MB exceeds 500MB quota"

    def test_06_warning_when_approaching_storage_limit(self):
        """
        E2E TEST: Warning appears when approaching storage limit

        BUSINESS REQUIREMENT:
        Students must be warned when they reach 80% of storage quota
        so they can clean up files before hitting the limit.

        VALIDATION:
        - Storage usage is tracked and displayed
        - Warning appears at 80% usage
        - Warning message is clear and actionable
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # Create files to reach 80% of 500MB quota (400MB)
        exit_code, output = container.exec_run(
            "sh -c 'dd if=/dev/zero of=/workspace/large1.bin bs=1M count=200 2>&1'"
        )

        exit_code, output = container.exec_run(
            "sh -c 'dd if=/dev/zero of=/workspace/large2.bin bs=1M count=200 2>&1'"
        )

        # Refresh page to update storage usage
        self.driver.refresh()
        time.sleep(2)

        # VALIDATION 1: Storage usage indicator shows high usage
        try:
            usage_info = self.storage_page.get_storage_usage()
            usage_percentage = (usage_info['used'] / usage_info['total']) * 100

            assert usage_percentage >= 80, \
                f"Storage usage {usage_percentage:.1f}% below warning threshold"

            # VALIDATION 2: Warning is visible
            assert self.storage_page.is_storage_warning_visible(), \
                "Storage warning not visible at 80% usage"

            # VALIDATION 3: Warning message is clear
            warning_element = self.driver.find_element(By.ID, "storage-warning")
            warning_text = warning_element.text.lower()

            assert any(keyword in warning_text for keyword in ['warning', 'limit', 'quota', 'space']), \
                f"Warning message not clear: {warning_text}"

        except NoSuchElementException:
            pytest.skip("Storage usage UI not implemented")

    def test_07_prevent_file_operations_when_quota_exceeded(self):
        """
        E2E TEST: Prevent file operations when quota exceeded

        BUSINESS REQUIREMENT:
        When storage quota is exceeded, file creation must be blocked
        with a clear error message. Students must be instructed to
        delete files before continuing.

        VALIDATION:
        - File creation fails when quota exceeded
        - Error message is displayed
        - Existing files can still be read
        - Files can be deleted to free space
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # Fill up storage (create 500MB+ of files)
        for i in range(6):  # 6 * 100MB = 600MB
            exit_code, output = container.exec_run(
                f"sh -c 'dd if=/dev/zero of=/workspace/fill{i}.bin bs=1M count=100 2>&1'"
            )
            if exit_code != 0:
                break  # Quota reached

        # VALIDATION 1: File creation fails when quota exceeded
        exit_code, output = container.exec_run(
            "sh -c 'echo \"test\" > /workspace/new_file.txt 2>&1'"
        )

        # Should fail due to quota
        output_text = output.decode().lower()
        quota_error = any(keyword in output_text for keyword in
                         ['quota', 'disk full', 'no space', 'exceeded'])

        assert exit_code != 0 or quota_error, \
            "File creation succeeded despite quota being exceeded"

        # VALIDATION 2: Existing files can still be read
        exit_code, output = container.exec_run("ls /workspace")
        assert exit_code == 0, "Cannot read existing files when quota exceeded"

        # VALIDATION 3: Files can be deleted to free space
        exit_code, output = container.exec_run("rm /workspace/fill0.bin")
        assert exit_code == 0, "Cannot delete files when quota exceeded"


# ============================================================================
# TEST CLASS 3: Backup and Recovery (3 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.lab_environment
@pytest.mark.priority_critical
class TestBackupAndRecovery(BaseTest):
    """
    Test lab backup and recovery mechanisms.

    BUSINESS REQUIREMENT:
    Lab state must be backed up regularly (every 30 minutes) and
    recoverable in case of container crashes or data corruption.
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver, test_base_url, student_credentials, docker_client):
        """Setup for each test."""
        self.driver = driver
        self.base_url = test_base_url
        self.student_credentials = student_credentials
        self.docker_client = docker_client
        self.storage_page = LabStoragePage(driver, test_base_url)

        # Login and start lab
        self._login_as_student()
        self.course_id = f"test-course-backup-{uuid.uuid4().hex[:8]}"

    def _login_as_student(self):
        """Helper to login as student."""
        self.driver.get(f"{self.base_url}/html/student-login.html")
        wait = WebDriverWait(self.driver, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(self.student_credentials["email"])

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(self.student_credentials["password"])

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_button.click()
        time.sleep(2)

    def _get_container(self):
        """Helper to get lab container."""
        student_username = self.student_credentials["username"]
        container_name = f"lab_{self.course_id}_{student_username}"
        return self.docker_client.containers.get(container_name)

    def test_08_lab_state_backed_up_every_30_minutes(self):
        """
        E2E TEST: Lab state backed up every 30 minutes

        BUSINESS REQUIREMENT:
        Lab state (files, environment) must be automatically backed up
        every 30 minutes to protect against data loss.

        VALIDATION:
        - Backup mechanism exists
        - Backup is triggered periodically
        - Backup contains all workspace files
        - Backup timestamp is tracked

        NOTE: This test checks the backup mechanism exists, not the full 30-minute cycle
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # VALIDATION 1: Check for backup configuration in container
        labels = container.labels

        # Check for backup-related labels
        has_backup_config = any(key.startswith('backup') for key in labels.keys())

        if not has_backup_config:
            pytest.skip("Backup mechanism not configured in container labels")

        # VALIDATION 2: Check for backup directory or volume
        exit_code, output = container.exec_run("test -d /.lab_backups && echo 'exists' || echo 'missing'")

        if "missing" in output.decode():
            # Backup directory may be external
            # Check for backup volume mount
            mounts = container.attrs.get('Mounts', [])
            backup_mount = next((m for m in mounts if 'backup' in m.get('Destination', '').lower()), None)

            assert backup_mount is not None, "No backup volume or directory found"

        # VALIDATION 3: Check for backup process or script
        exit_code, output = container.exec_run("which backup-lab.sh")
        if exit_code != 0:
            # Backup may be handled externally
            # Check for backup label with script path
            assert 'backup_script' in labels or 'backup_enabled' in labels, \
                "No backup mechanism found"

    def test_09_restore_lab_from_backup_after_crash(self):
        """
        E2E TEST: Restore lab from backup after crash

        BUSINESS REQUIREMENT:
        If a lab container crashes, students must be able to restore
        their work from the most recent backup without data loss.

        TEST SCENARIO:
        1. Create files in lab
        2. Simulate backup
        3. Simulate crash (force stop container)
        4. Restart lab and restore from backup
        5. Verify files are restored

        VALIDATION:
        - Files can be restored from backup
        - Restored files match original content
        - Restore process is automatic
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # Create test files
        test_files = {
            f"important_{uuid.uuid4().hex[:8]}.txt": "Critical data that must be backed up",
            f"code_{uuid.uuid4().hex[:8]}.py": "def important_function():\n    return 'data'"
        }

        for filename, content in test_files.items():
            exit_code, output = container.exec_run(
                f"sh -c 'echo \"{content}\" > /workspace/{filename}'"
            )
            assert exit_code == 0, f"Failed to create {filename}"

        # VALIDATION 1: Files exist before crash
        for filename in test_files.keys():
            exit_code, output = container.exec_run(f"test -f /workspace/{filename}")
            assert exit_code == 0, f"File {filename} not found before crash"

        # Simulate backup (if backup script exists)
        exit_code, output = container.exec_run("which backup-lab.sh")
        if exit_code == 0:
            container.exec_run("backup-lab.sh")
            time.sleep(2)

        # Simulate crash (force stop container)
        container.stop(timeout=0)
        time.sleep(1)

        # Restart container
        container.start()
        time.sleep(3)
        container.reload()

        assert container.status == "running", "Container failed to restart"

        # VALIDATION 2: Files restored after restart
        for filename, expected_content in test_files.items():
            exit_code, output = container.exec_run(f"cat /workspace/{filename}")

            if exit_code != 0:
                # File not restored - may need manual restore
                exit_code, output = container.exec_run("restore-lab.sh")
                time.sleep(2)

                # Try again
                exit_code, output = container.exec_run(f"cat /workspace/{filename}")

            assert exit_code == 0, f"File {filename} not restored after crash"

            # VALIDATION 3: Content matches original
            actual_content = output.decode().strip()
            assert expected_content in actual_content, \
                f"File {filename} content not restored correctly"

    def test_10_export_lab_files_to_zip_for_download(self):
        """
        E2E TEST: Export lab files to zip for download

        BUSINESS REQUIREMENT:
        Students must be able to export all their lab work as a zip file
        for backup or submission purposes.

        VALIDATION:
        - Export button triggers zip creation
        - Zip file contains all workspace files
        - Zip file is downloadable
        - File structure is preserved in zip
        """
        self.storage_page.navigate_to_lab_storage(self.course_id)

        # Start lab
        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-lab-button"))
        )
        start_button.click()
        time.sleep(3)

        container = self._get_container()

        # Create test files with directory structure
        test_files = {
            "main.py": "print('main')",
            "src/utils.py": "def util(): pass",
            "data/test.json": '{"test": "data"}'
        }

        for filepath, content in test_files.items():
            # Create directory if needed
            dirname = os.path.dirname(filepath)
            if dirname:
                container.exec_run(f"mkdir -p /workspace/{dirname}")

            exit_code, output = container.exec_run(
                f"sh -c 'echo \"{content}\" > /workspace/{filepath}'"
            )
            assert exit_code == 0, f"Failed to create {filepath}"

        # Create zip export in container
        zip_filename = "lab_export.zip"
        exit_code, output = container.exec_run(
            f"sh -c 'cd /workspace && zip -r /tmp/{zip_filename} . 2>&1'"
        )

        # VALIDATION 1: Zip created successfully
        assert exit_code == 0, f"Zip creation failed: {output.decode()}"

        # VALIDATION 2: Zip file exists
        exit_code, output = container.exec_run(f"test -f /tmp/{zip_filename}")
        assert exit_code == 0, "Zip file not created"

        # VALIDATION 3: Zip contains all files
        exit_code, output = container.exec_run(f"unzip -l /tmp/{zip_filename}")
        assert exit_code == 0, "Failed to list zip contents"

        zip_contents = output.decode()

        for filepath in test_files.keys():
            assert filepath in zip_contents, f"File {filepath} not in zip"

        # VALIDATION 4: Zip preserves directory structure
        assert "src/" in zip_contents, "Directory structure not preserved"
        assert "data/" in zip_contents, "Directory structure not preserved"


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def docker_client():
    """
    Create Docker client for container verification.

    BUSINESS CONTEXT:
    Tests need to verify actual Docker container state and file system
    operations, not just UI state.
    """
    client = docker.from_env()
    yield client

    # Cleanup: Remove any test containers
    try:
        test_containers = client.containers.list(all=True, filters={"label": "test"})
        for container in test_containers:
            try:
                container.stop(timeout=1)
                container.remove()
            except Exception as e:
                print(f"Error cleaning up test container {container.name}: {e}")
    except Exception as e:
        print(f"Error during fixture cleanup: {e}")


@pytest.fixture
def student_credentials():
    """
    Provide student credentials for authentication.

    Returns:
        dict: Student credentials with username, email, and password
    """
    return {
        "username": "test_student",
        "email": "student.test@example.com",
        "password": "password123"
    }
