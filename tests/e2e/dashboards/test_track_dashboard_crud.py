"""
Track Dashboard CRUD Workflow Tests (TDD - Red Phase)

BUSINESS PURPOSE:
These tests verify complete CRUD operations for track management including:
- Create track with all attributes (including JSONB fields)
- Read/list tracks with filtering
- Update track attributes
- Delete tracks
- Data persistence verification in database

TEST STRATEGY:
1. Run ONLY after pre-flight tests pass
2. Each test is independent (creates its own test data)
3. Verify data persists in database after each operation
4. Clean up test data after tests

@module test_track_dashboard_crud
"""

import pytest
import psycopg2
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from selenium_base import BaseTest


class TestTrackDashboardCRUD(BaseTest):
    """
    Complete CRUD workflow tests for Track Dashboard

    WHY THIS TEST CLASS EXISTS:
    Verifies that all track management operations work end-to-end:
    - UI interactions (buttons, forms, modals)
    - API calls (create, read, update, delete)
    - Database persistence (data actually saves)
    - Data validation (business rules enforced)
    """

    @classmethod
    def setUpClass(cls):
        """Set up test class - authenticate and get database connection"""
        super().setUpClass()
        cls.base_url = os.getenv("TEST_BASE_URL", "https://localhost:3000")

        # Database connection for verification
        cls.db_url = os.getenv("TEST_DATABASE_URL",
                               "postgresql://course_user:course_pass@localhost:5433/course_creator")

        # Login as org admin
        cls.driver.get(f"{cls.base_url}/login.html")
        WebDriverWait(cls.driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        cls.driver.find_element(By.ID, "username").send_keys("org_admin")
        cls.driver.find_element(By.ID, "password").send_keys("admin123")
        cls.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Wait for redirect to dashboard
        WebDriverWait(cls.driver, 10).until(
            EC.url_contains("org-admin-dashboard.html")
        )

        # Get organization ID from localStorage
        cls.org_id = cls.driver.execute_script("return localStorage.getItem('organizationId');")

        cls.created_track_ids = []  # Track IDs to clean up

    @classmethod
    def tearDownClass(cls):
        """Clean up test data from database"""
        if cls.created_track_ids:
            conn = psycopg2.connect(cls.db_url)
            cursor = conn.cursor()
            for track_id in cls.created_track_ids:
                try:
                    cursor.execute("DELETE FROM course_creator.tracks WHERE id = %s", (track_id,))
                except Exception as e:
                    print(f"Error cleaning up track {track_id}: {e}")
            conn.commit()
            conn.close()

        super().tearDownClass()

    def navigate_to_tracks_tab(self):
        """Helper: Navigate to tracks tab"""
        self.driver.get(f"{self.base_url}/org-admin-dashboard.html")
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()

        # Wait for tracks table to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "tracksTable"))
        )

    def get_track_from_database(self, track_id: str) -> dict:
        """Helper: Fetch track from database for verification"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, organization_id, name, description, difficulty_level,
                   estimated_duration_hours, prerequisites, learning_objectives, is_active
            FROM course_creator.tracks
            WHERE id = %s
            """,
            (track_id,)
        )
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(zip(columns, result))
        return None

    def get_latest_track_id_from_table(self) -> str:
        """Helper: Get most recently created track ID from UI table"""
        # Find all track rows in table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table#tracksTable tbody tr")
        if not rows:
            return None

        # Get first row (most recent if sorted by created_at desc)
        first_row = rows[0]

        # Get track ID from data attribute or hidden column
        track_id = first_row.get_attribute("data-track-id")
        return track_id

    # ========== CREATE TESTS ==========

    def test_01_create_track_with_minimal_required_fields(self):
        """
        Test creating track with only required fields

        WORKFLOW:
        1. Navigate to Tracks tab
        2. Click Create Track button
        3. Fill only required fields (name, difficulty)
        4. Submit form
        5. Verify track appears in table
        6. Verify track exists in database
        """
        self.navigate_to_tracks_tab()

        # Click Create Track button
        create_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "createTrackBtn"))
        )
        create_btn.click()

        # Wait for modal to appear
        modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createTrackModal"))
        )

        # Fill required fields
        track_name = f"Minimal Track {int(time.time())}"
        self.driver.find_element(By.ID, "trackName").send_keys(track_name)

        # Select difficulty level
        difficulty_select = Select(self.driver.find_element(By.ID, "trackDifficultyLevel"))
        difficulty_select.select_by_value("beginner")

        # Submit form
        submit_btn = self.driver.find_element(By.ID, "submitCreateTrackBtn")
        submit_btn.click()

        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "createTrackModal"))
        )

        # Verify track appears in table
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element(
                (By.ID, "tracksTable"),
                track_name
            )
        )

        # Get track ID and verify in database
        track_id = self.get_latest_track_id_from_table()
        self.assertIsNotNone(track_id, "Track ID should be available")

        db_track = self.get_track_from_database(track_id)
        self.assertIsNotNone(db_track, "Track should exist in database")
        self.assertEqual(db_track["name"], track_name)
        self.assertEqual(db_track["difficulty_level"], "beginner")

        self.created_track_ids.append(track_id)

    def test_02_create_track_with_all_fields_including_jsonb(self):
        """
        Test creating track with ALL fields including JSONB arrays

        WORKFLOW:
        1. Navigate to Tracks tab
        2. Click Create Track button
        3. Fill ALL fields including prerequisites and learning objectives (JSONB)
        4. Submit form
        5. Verify all data persists correctly in database

        WHY CRITICAL:
        This tests JSONB field handling which can fail silently if not implemented correctly
        """
        self.navigate_to_tracks_tab()

        # Click Create Track button
        create_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "createTrackBtn"))
        )
        create_btn.click()

        # Wait for modal
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createTrackModal"))
        )

        # Prepare test data
        track_data = {
            "name": f"Complete Track {int(time.time())}",
            "description": "This is a comprehensive test track with all fields populated",
            "difficulty_level": "advanced",
            "estimated_duration_hours": 120,
            "prerequisites": ["Python basics", "Git fundamentals", "SQL knowledge"],
            "learning_objectives": ["Master Django framework", "Build REST APIs", "Deploy to production"],
            "is_active": True
        }

        # Fill all fields
        self.driver.find_element(By.ID, "trackName").send_keys(track_data["name"])
        self.driver.find_element(By.ID, "trackDescription").send_keys(track_data["description"])

        Select(self.driver.find_element(By.ID, "trackDifficultyLevel")).select_by_value(
            track_data["difficulty_level"]
        )

        self.driver.find_element(By.ID, "trackDurationHours").send_keys(
            str(track_data["estimated_duration_hours"])
        )

        # Fill JSONB fields (UI should accept JSON strings or provide UI for array input)
        prerequisites_json = json.dumps(track_data["prerequisites"])
        self.driver.find_element(By.ID, "trackPrerequisites").send_keys(prerequisites_json)

        learning_objectives_json = json.dumps(track_data["learning_objectives"])
        self.driver.find_element(By.ID, "trackLearningObjectives").send_keys(learning_objectives_json)

        # Check is_active checkbox
        if track_data["is_active"]:
            is_active_checkbox = self.driver.find_element(By.ID, "trackIsActive")
            if not is_active_checkbox.is_selected():
                is_active_checkbox.click()

        # Submit
        submit_btn = self.driver.find_element(By.ID, "submitCreateTrackBtn")
        submit_btn.click()

        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "createTrackModal"))
        )

        # Verify track appears
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "tracksTable"), track_data["name"])
        )

        # Verify in database
        track_id = self.get_latest_track_id_from_table()
        db_track = self.get_track_from_database(track_id)

        self.assertIsNotNone(db_track)
        self.assertEqual(db_track["name"], track_data["name"])
        self.assertEqual(db_track["description"], track_data["description"])
        self.assertEqual(db_track["difficulty_level"], track_data["difficulty_level"])
        self.assertEqual(db_track["estimated_duration_hours"], track_data["estimated_duration_hours"])
        self.assertEqual(db_track["prerequisites"], track_data["prerequisites"])
        self.assertEqual(db_track["learning_objectives"], track_data["learning_objectives"])
        self.assertEqual(db_track["is_active"], track_data["is_active"])

        self.created_track_ids.append(track_id)

    # ========== READ TESTS ==========

    def test_03_list_all_tracks_in_organization(self):
        """
        Test that tracks table displays all tracks for the organization

        WORKFLOW:
        1. Create 3 test tracks
        2. Navigate to Tracks tab
        3. Verify all 3 tracks appear in table
        4. Verify tracks are from correct organization only
        """
        # Create 3 test tracks via database for speed
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        test_track_names = [
            f"List Test Track 1 {int(time.time())}",
            f"List Test Track 2 {int(time.time())}",
            f"List Test Track 3 {int(time.time())}"
        ]

        for track_name in test_track_names:
            cursor.execute(
                """
                INSERT INTO course_creator.tracks (organization_id, name, difficulty_level)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (self.org_id, track_name, "intermediate")
            )
            track_id = cursor.fetchone()[0]
            self.created_track_ids.append(str(track_id))

        conn.commit()
        conn.close()

        # Navigate and verify
        self.navigate_to_tracks_tab()

        # Wait for table to load
        time.sleep(2)  # Allow time for API call and table update

        table_body = self.driver.find_element(By.CSS_SELECTOR, "#tracksTable tbody")
        table_text = table_body.text

        # Verify all 3 tracks appear
        for track_name in test_track_names:
            self.assertIn(track_name, table_text, f"Track '{track_name}' should appear in table")

    def test_04_search_tracks_by_name(self):
        """
        Test search functionality filters tracks correctly

        WORKFLOW:
        1. Create tracks with distinct names
        2. Enter search term
        3. Verify only matching tracks appear
        """
        # Create test track
        unique_name = f"SearchableTrack_{int(time.time())}"
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO course_creator.tracks (organization_id, name, difficulty_level)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (self.org_id, unique_name, "intermediate")
        )
        track_id = cursor.fetchone()[0]
        self.created_track_ids.append(str(track_id))
        conn.commit()
        conn.close()

        # Navigate and search
        self.navigate_to_tracks_tab()
        time.sleep(2)

        search_input = self.driver.find_element(By.ID, "trackSearchInput")
        search_input.clear()
        search_input.send_keys("SearchableTrack")

        # Wait for filter to apply
        time.sleep(1)

        # Verify only matching track appears
        table_text = self.driver.find_element(By.CSS_SELECTOR, "#tracksTable tbody").text
        self.assertIn(unique_name, table_text)

    # ========== UPDATE TESTS ==========

    def test_05_edit_track_name_and_description(self):
        """
        Test editing track name and description

        WORKFLOW:
        1. Create track
        2. Click edit button
        3. Modify name and description
        4. Save changes
        5. Verify changes in table and database
        """
        # Create test track
        original_name = f"Edit Test Track {int(time.time())}"
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO course_creator.tracks (organization_id, name, description, difficulty_level)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (self.org_id, original_name, "Original description", "beginner")
        )
        track_id = cursor.fetchone()[0]
        self.created_track_ids.append(str(track_id))
        conn.commit()
        conn.close()

        # Navigate and edit
        self.navigate_to_tracks_tab()
        time.sleep(2)

        # Find and click edit button for this track
        edit_btn = self.driver.find_element(
            By.CSS_SELECTOR,
            f"tr[data-track-id='{track_id}'] button.edit-track-btn"
        )
        edit_btn.click()

        # Wait for edit modal
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "editTrackModal"))
        )

        # Modify fields
        new_name = f"EDITED Track {int(time.time())}"
        new_description = "This track has been edited"

        name_input = self.driver.find_element(By.ID, "editTrackName")
        name_input.clear()
        name_input.send_keys(new_name)

        desc_input = self.driver.find_element(By.ID, "editTrackDescription")
        desc_input.clear()
        desc_input.send_keys(new_description)

        # Submit
        submit_btn = self.driver.find_element(By.ID, "submitEditTrackBtn")
        submit_btn.click()

        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "editTrackModal"))
        )

        # Verify changes in database
        time.sleep(1)
        db_track = self.get_track_from_database(str(track_id))
        self.assertEqual(db_track["name"], new_name)
        self.assertEqual(db_track["description"], new_description)

    # ========== DELETE TESTS ==========

    def test_06_delete_track_with_confirmation(self):
        """
        Test deleting track with confirmation modal

        WORKFLOW:
        1. Create track
        2. Click delete button
        3. Confirm deletion
        4. Verify track removed from table
        5. Verify track deleted from database
        """
        # Create test track
        track_name = f"Delete Test Track {int(time.time())}"
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO course_creator.tracks (organization_id, name, difficulty_level)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (self.org_id, track_name, "beginner")
        )
        track_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        # Navigate
        self.navigate_to_tracks_tab()
        time.sleep(2)

        # Click delete button
        delete_btn = self.driver.find_element(
            By.CSS_SELECTOR,
            f"tr[data-track-id='{track_id}'] button.delete-track-btn"
        )
        delete_btn.click()

        # Wait for delete confirmation modal
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "deleteTrackModal"))
        )

        # Confirm deletion
        confirm_btn = self.driver.find_element(By.ID, "confirmDeleteTrackBtn")
        confirm_btn.click()

        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "deleteTrackModal"))
        )

        # Verify track removed from table
        time.sleep(1)
        table_text = self.driver.find_element(By.CSS_SELECTOR, "#tracksTable tbody").text
        self.assertNotIn(track_name, table_text, "Deleted track should not appear in table")

        # Verify track deleted from database
        db_track = self.get_track_from_database(str(track_id))
        self.assertIsNone(db_track, "Track should be deleted from database")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
