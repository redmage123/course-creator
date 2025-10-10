#!/usr/bin/env bash
"""
Demo Video Generator - Using Existing E2E Test Framework

BUSINESS PURPOSE:
Generate demo videos by running existing E2E tests with video recording enabled.
Leverages the existing Selenium test infrastructure for reliability.

USAGE:
    ./scripts/generate_demo_videos_e2e.sh all
    ./scripts/generate_demo_videos_e2e.sh student
    ./scripts/generate_demo_videos_e2e.sh instructor
"""

set -e  # Exit on error

# Configuration
export HEADLESS=false           # Show browser for demo recording
export RECORD_VIDEO=true        # Enable video recording
export VIDEO_DIR="frontend/static/demo/videos"
export VIDEO_FPS=10             # Higher FPS for smoother demo videos
export WINDOW_WIDTH=1920
export WINDOW_HEIGHT=1080
export TEST_BASE_URL="https://localhost:3000"

# Create video output directory
mkdir -p "$VIDEO_DIR"

echo "=================================================="
echo "DEMO VIDEO GENERATION - E2E Test Framework"
echo "=================================================="
echo "Output directory: $VIDEO_DIR"
echo "Recording mode: HEADLESS=$HEADLESS"
echo "Video FPS: $VIDEO_FPS"
echo ""

# Function to run a specific test with video recording
run_demo_test() {
    local test_file="$1"
    local test_name="$2"
    local video_name="$3"

    echo "🎥 Recording: $video_name"
    echo "   Test: $test_file::$test_name"

    # Run the test with video recording
    HEADLESS=$HEADLESS \
    RECORD_VIDEO=true \
    VIDEO_DIR="$VIDEO_DIR" \
    VIDEO_FPS=$VIDEO_FPS \
    pytest "$test_file::$test_name" -v --tb=short

    echo "✓ Video recorded"
    echo ""
}

# Main demo generation logic
case "${1:-all}" in
    "homepage")
        echo "Generating Slide 1: Homepage & Introduction"
        run_demo_test \
            "tests/e2e/test_homepage_login_modal.py" \
            "TestHomepageLoginModal::test_privacy_modal_appears_on_first_visit" \
            "slide_01_introduction"
        ;;

    "student")
        echo "Generating Student Journey Videos"

        # Student registration
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_student_complete_journey.py" \
            "TestStudentRegistrationAndConsent::test_complete_registration_with_all_consents" \
            "slide_student_registration"

        # Student dashboard
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_student_complete_journey.py" \
            "TestStudentLoginAndAuthentication::test_successful_login_redirects_to_dashboard" \
            "slide_student_dashboard"

        # Lab environment
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_student_complete_journey.py" \
            "TestLabEnvironmentWorkflow::test_start_lab_environment" \
            "slide_student_lab"

        # Quiz taking
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_student_complete_journey.py" \
            "TestQuizTakingWorkflow::test_complete_quiz_submission" \
            "slide_student_quiz"

        # Progress tracking
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_student_complete_journey.py" \
            "TestProgressTrackingAndCertificates::test_view_progress_dashboard" \
            "slide_student_progress"
        ;;

    "instructor")
        echo "Generating Instructor Journey Videos"

        # Instructor dashboard
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_instructor_complete_journey.py" \
            "TestInstructorDashboardNavigation::test_instructor_login_redirects_to_dashboard" \
            "slide_instructor_dashboard"

        # Course creation
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_instructor_complete_journey.py" \
            "TestCourseCreationWorkflow::test_create_new_course" \
            "slide_instructor_create_course"

        # Analytics
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_instructor_complete_journey.py" \
            "TestAnalyticsWorkflow::test_view_course_analytics" \
            "slide_instructor_analytics"
        ;;

    "org")
        echo "Generating Organization Admin Journey Videos"

        # Org admin dashboard
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_org_admin_complete_journey.py" \
            "TestOrgAdminDashboardNavigation::test_org_admin_login_redirects_to_dashboard" \
            "slide_org_admin_dashboard"

        # Member management
        run_demo_test \
            "tests/e2e/critical_user_journeys/test_org_admin_complete_journey.py" \
            "TestMemberManagementWorkflow::test_invite_new_member" \
            "slide_org_admin_members"
        ;;

    "all")
        echo "Generating ALL demo videos"
        echo ""

        # Run all demo categories
        $0 homepage
        $0 student
        $0 instructor
        $0 org
        ;;

    *)
        echo "Usage: $0 {homepage|student|instructor|org|all}"
        exit 1
        ;;
esac

echo "=================================================="
echo "✅ Demo video generation complete!"
echo "   Videos saved to: $VIDEO_DIR"
echo "=================================================="
ls -lh "$VIDEO_DIR"
