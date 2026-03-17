"""
Demo Video Recording Tests

BUSINESS PURPOSE:
Generate high-quality demo videos showing platform workflows.
Uses continuous frame capture for smooth, realistic videos.

TECHNICAL APPROACH:
Extends E2E tests with continuous video recording enabled.
Captures frames every 0.1 seconds for smooth 10 FPS videos.

USAGE:
    RECORD_VIDEO=true VIDEO_FPS=10 pytest tests/e2e/demo_recordings/test_demo_videos.py -v
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.selenium_base import BasePage, BaseTest


class DemoRecordingTest(BaseTest):
    """
    Base class for demo recording tests.
    Automatically enables continuous frame capture for smooth videos.
    """

    def setup_method(self, method):
        """Setup with continuous recording enabled"""
        super().setup_method(method)

        # Initialize wait object
        from selenium.webdriver.support.ui import WebDriverWait
        self.wait = WebDriverWait(self.driver, 30)

        # Start continuous frame capture for smooth video
        if self.video_recorder:
            self.start_continuous_recording(interval=0.1)  # 10 FPS
            print(f"🎥 Recording demo video: {self.test_name}")

    def teardown_method(self, method):
        """Teardown with recording stopped"""
        # Stop continuous recording
        if hasattr(self, 'frame_capturer') and self.frame_capturer:
            self.stop_continuous_recording()

        super().teardown_method(method)

    def slow_action(self, action_func, description="", delay=1.5):
        """
        Perform action slowly for demo purposes

        Args:
            action_func: Function to execute
            description: Description for logging
            delay: Seconds to wait after action
        """
        if description:
            print(f"  → {description}")

        action_func()
        time.sleep(delay)


class TestIntroAndOutroDemos(DemoRecordingTest):
    """Demo videos for introduction and summary"""

    def test_introduction_homepage(self):
        """
        Demo: Platform introduction and homepage overview

        Duration: ~15 seconds
        Shows: Homepage, platform overview, navigation preview
        """
        print("\n📹 Recording: Introduction & Homepage")

        # Navigate to homepage
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}"),
            "Load homepage",
            4
        )

        # Scroll to show features
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View features section",
            3
        )

        # Scroll to show more
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View more features",
            3
        )

        # Return to top
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "Return to top",
            2
        )

        print("✅ Recording complete")

    def test_summary_and_cta(self):
        """
        Demo: Summary and call-to-action

        Duration: ~15 seconds
        Shows: Platform overview, workflow summary, CTA buttons
        """
        print("\n📹 Recording: Summary & CTA")

        # Navigate to homepage
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}"),
            "Load homepage",
            3
        )

        # Scroll to CTA section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
            "View CTA section",
            4
        )

        # Hover over CTA buttons (if present)
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button.cta, .cta-button, a[href*='trial']"),
                "Highlight CTA",
                3
            )
        except:
            time.sleep(3)

        # Return to overview
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View overview",
            2
        )

        print("✅ Recording complete")


class TestStudentJourneyDemos(DemoRecordingTest):
    """Demo videos for student learning journey"""

    def test_student_login_and_dashboard(self):
        """
        Demo: Student login and dashboard overview

        Duration: ~20 seconds
        Shows: Login form, authentication, dashboard load
        """
        print("\n📹 Recording: Student Login & Dashboard")

        # Navigate to login
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/login"),
            "Navigate to login page",
            2
        )

        # Fill login form slowly
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            ).send_keys("demo.student@example.com"),
            "Enter email",
            1.5
        )

        self.slow_action(
            lambda: self.driver.find_element(By.ID, "password").send_keys("DemoPass123!"),
            "Enter password",
            1.5
        )

        # Submit login
        self.slow_action(
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click(),
            "Click login",
            3
        )

        # Wait for dashboard to load
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .dashboard"))
            ),
            "Dashboard loaded",
            3
        )

        # Scroll through dashboard
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "Scroll dashboard",
            2
        )

        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "Scroll more",
            2
        )

        print("✅ Recording complete")

    def test_student_course_browsing(self):
        """
        Demo: Browsing course catalog

        Duration: ~15 seconds
        Shows: Course discovery, filtering, course details
        """
        print("\n📹 Recording: Course Browsing")

        # Login first
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.student@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to courses
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/courses"),
            "Navigate to courses",
            3
        )

        # Scroll through courses
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 500);"),
            "Browse courses",
            3
        )

        # Click on a course (if exists)
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".course-card, a[href*='course']").click(),
                "View course details",
                5
            )
        except:
            time.sleep(5)

        print("✅ Recording complete")

    def test_taking_quiz(self):
        """
        Demo: Student taking quiz and viewing results

        Duration: ~45 seconds
        Shows: Quiz interface, timer, question types, instant grading
        """
        print("\n📹 Recording: Taking Quiz")

        # Login first
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.student@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to quiz page
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/html/quiz.html"),
            "Navigate to quiz",
            3
        )

        # View quiz interface
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 300);"),
            "View quiz questions",
            4
        )

        # Look for quiz start button
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[class*='start'], button[id*='start']").click(),
                "Start quiz",
                4
            )
        except:
            time.sleep(4)

        # View question
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View question",
            4
        )

        # Simulate answering (scroll to answers)
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 600);"),
            "View answer options",
            4
        )

        # View quiz controls
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View quiz controls",
            4
        )

        # Return to top
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "View quiz results",
            3
        )

        print("✅ Recording complete")

    def test_student_progress_analytics(self):
        """
        Demo: Student viewing personal progress dashboard

        Duration: ~30 seconds
        Shows: Progress tracking, quiz scores, achievements, charts
        """
        print("\n📹 Recording: Student Progress")

        # Login first
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.student@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to progress page
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/html/student-progress.html"),
            "Navigate to progress",
            3
        )

        # View progress metrics
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View progress metrics",
            4
        )

        # View charts
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View progress charts",
            4
        )

        # View achievements
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1200);"),
            "View achievements",
            4
        )

        # Return to overview
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "Return to overview",
            2
        )

        print("✅ Recording complete")


class TestInstructorJourneyDemos(DemoRecordingTest):
    """Demo videos for instructor workflows"""

    def test_instructor_dashboard(self):
        """
        Demo: Instructor dashboard and course management

        Duration: ~20 seconds
        Shows: Instructor login, dashboard, course list
        """
        print("\n📹 Recording: Instructor Dashboard")

        # Navigate to login
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/login"),
            "Navigate to login",
            2
        )

        # Login as instructor
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            ).send_keys("demo.instructor@example.com"),
            "Enter instructor email",
            1.5
        )

        self.slow_action(
            lambda: self.driver.find_element(By.ID, "password").send_keys("DemoPass123!"),
            "Enter password",
            1.5
        )

        self.slow_action(
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click(),
            "Login",
            3
        )

        # Dashboard loaded
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .dashboard"))
            ),
            "Dashboard loaded",
            3
        )

        # Scroll dashboard
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 600);"),
            "View courses",
            3
        )

        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1200);"),
            "Scroll more",
            2
        )

        print("✅ Recording complete")

    def test_adding_course_content(self):
        """
        Demo: Adding content and materials to a course

        Duration: ~45 seconds
        Shows: Content editor, lessons, exercises, resources
        """
        print("\n📹 Recording: Adding Course Content")

        # Login as instructor
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.instructor@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to instructor dashboard
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/instructor-dashboard-modular"),
            "Navigate to dashboard",
            3
        )

        # Scroll to courses section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View courses section",
            3
        )

        # Look for course or content management
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "a[href*='course'], button[class*='course']").click(),
                "Open course",
                4
            )
        except:
            time.sleep(4)

        # Show content editor interface
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 600);"),
            "View content editor",
            4
        )

        # Scroll to show modules/lessons
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1000);"),
            "View modules",
            4
        )

        # Scroll to exercises section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1400);"),
            "View exercises",
            4
        )

        # Return to top
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "Return to overview",
            3
        )

        print("✅ Recording complete")

    def test_enrolling_students(self):
        """
        Demo: Enrolling students in a course

        Duration: ~45 seconds
        Shows: Student enrollment, bulk CSV import, section management
        """
        print("\n📹 Recording: Enrolling Students")

        # Login as instructor
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.instructor@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to course management
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/instructor-dashboard-modular"),
            "Navigate to dashboard",
            3
        )

        # Scroll to student management section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 500);"),
            "View student management",
            4
        )

        # Look for student enrollment button
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[class*='student'], button[class*='enroll'], a[href*='student']").click(),
                "Open student enrollment",
                4
            )
        except:
            time.sleep(4)

        # View enrollment interface
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View enrollment form",
            4
        )

        # Scroll to show student list
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View enrolled students",
            4
        )

        # Show bulk actions
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1200);"),
            "View bulk actions",
            3
        )

        print("✅ Recording complete")

    def test_instructor_analytics(self):
        """
        Demo: Instructor viewing class analytics

        Duration: ~45 seconds
        Shows: Class metrics, student performance, engagement heatmap
        """
        print("\n📹 Recording: Instructor Analytics")

        # Login as instructor
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.instructor@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to analytics
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/instructor-dashboard-modular"),
            "Navigate to dashboard",
            3
        )

        # Look for analytics tab/section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 600);"),
            "View analytics section",
            4
        )

        # Try to find and click analytics button
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[class*='analytic'], a[href*='analytic'], [data-tab*='analytic']").click(),
                "Open analytics",
                4
            )
        except:
            time.sleep(4)

        # View class metrics
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View class metrics",
            4
        )

        # View student performance
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View student performance",
            4
        )

        # View engagement data
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 1200);"),
            "View engagement data",
            4
        )

        # Return to overview
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "Return to overview",
            3
        )

        print("✅ Recording complete")


class TestOrgAdminJourneyDemos(DemoRecordingTest):
    """Demo videos for organization admin workflows"""

    def test_org_admin_dashboard(self):
        """
        Demo: Organization admin dashboard

        Duration: ~20 seconds
        Shows: Org admin login, dashboard, organization overview
        """
        print("\n📹 Recording: Org Admin Dashboard")

        # Navigate to login
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/login"),
            "Navigate to login",
            2
        )

        # Login as org admin
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            ).send_keys("demo.orgadmin@example.com"),
            "Enter org admin email",
            1.5
        )

        self.slow_action(
            lambda: self.driver.find_element(By.ID, "password").send_keys("DemoPass123!"),
            "Enter password",
            1.5
        )

        self.slow_action(
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click(),
            "Login",
            3
        )

        # Dashboard loaded
        self.slow_action(
            lambda: self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .dashboard"))
            ),
            "Dashboard loaded",
            4
        )

        # Navigate organization features
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 500);"),
            "View organization details",
            3
        )

        print("✅ Recording complete")

    def test_projects_and_tracks(self):
        """
        Demo: Creating projects and tracks within organization

        Duration: ~30 seconds
        Shows: Project creation, track creation, organizational hierarchy
        """
        print("\n📹 Recording: Projects & Tracks")

        # Login as org admin first
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.orgadmin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to organization dashboard
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/organization-admin-dashboard"),
            "Navigate to organization management",
            3
        )

        # Scroll to projects section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View projects section",
            3
        )

        # Look for project creation button
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[class*='create'], a[href*='project']").click(),
                "Click create project",
                4
            )
        except:
            time.sleep(4)

        # Scroll to show tracks section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View tracks section",
            4
        )

        # Scroll back to top
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            "Return to overview",
            3
        )

        print("✅ Recording complete")

    def test_adding_instructors(self):
        """
        Demo: Adding instructors to organization

        Duration: ~30 seconds
        Shows: Instructor invitation, role assignment, member management
        """
        print("\n📹 Recording: Adding Instructors")

        # Login as org admin
        self.driver.get(f"{self.config.base_url}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys("demo.orgadmin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("DemoPass123!")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)

        # Navigate to members management
        self.slow_action(
            lambda: self.driver.get(f"{self.config.base_url}/organization-admin-dashboard"),
            "Navigate to dashboard",
            3
        )

        # Scroll to members section
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 600);"),
            "View members section",
            3
        )

        # Look for add member/instructor button
        try:
            self.slow_action(
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[class*='add'], button[class*='invite'], a[href*='member']").click(),
                "Click add instructor",
                4
            )
        except:
            time.sleep(4)

        # View member management interface
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 400);"),
            "View member management",
            4
        )

        # Scroll to show member list
        self.slow_action(
            lambda: self.driver.execute_script("window.scrollTo(0, 800);"),
            "View member list",
            3
        )

        print("✅ Recording complete")
