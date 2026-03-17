#!/usr/bin/env bash
"""
Batch Demo Video Generator

Generates all demo videos by running E2E tests with video recording enabled.
Videos are automatically renamed to match the demo slide structure.

USAGE:
    ./scripts/generate_demo_videos_batch.sh
"""

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
VIDEO_DIR="frontend/static/demo/videos"
VIDEO_FPS=10
PYTEST_ARGS="-v --tb=line -x"

# Ensure video directory exists
mkdir -p "$VIDEO_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Demo Video Generation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Kill existing Chrome processes
echo -e "${YELLOW}Cleaning up Chrome processes...${NC}"
pkill -f chrome || true
sleep 2

# Clean old videos
echo -e "${BLUE}Cleaning old demo videos...${NC}"
rm -f "$VIDEO_DIR"/test_*.mp4
echo ""

# Run all demo tests
echo -e "${GREEN}🎥 Recording all 13 demo videos...${NC}"
export HEADLESS=true
export RECORD_VIDEO=true
export VIDEO_DIR="$VIDEO_DIR"
export VIDEO_FPS=$VIDEO_FPS

pytest tests/e2e/demo_recordings/test_demo_videos.py $PYTEST_ARGS

echo ""
echo -e "${GREEN}✅ All videos recorded!${NC}"
echo ""

# Rename videos to slide format
echo -e "${BLUE}Renaming videos to slide format...${NC}"

cd "$VIDEO_DIR"

# Find most recent videos and rename
cp $(ls -t test_introduction_homepage_*.mp4 | head -1) slide_01_introduction.mp4 2>/dev/null || true
cp $(ls -t test_org_admin_dashboard_*.mp4 | head -1) slide_02_org_admin.mp4 2>/dev/null || true
cp $(ls -t test_projects_and_tracks_*.mp4 | head -1) slide_03_projects_tracks.mp4 2>/dev/null || true
cp $(ls -t test_adding_instructors_*.mp4 | head -1) slide_04_add_instructors.mp4 2>/dev/null || true
cp $(ls -t test_instructor_dashboard_*.mp4 | head -1) slide_05_instructor_dashboard.mp4 2>/dev/null || true
cp $(ls -t test_adding_course_content_*.mp4 | head -1) slide_06_course_content.mp4 2>/dev/null || true
cp $(ls -t test_enrolling_students_*.mp4 | head -1) slide_07_enroll_students.mp4 2>/dev/null || true
cp $(ls -t test_student_login_and_dashboard_*.mp4 | head -1) slide_08_student_dashboard.mp4 2>/dev/null || true
cp $(ls -t test_student_course_browsing_*.mp4 | head -1) slide_09_course_browsing.mp4 2>/dev/null || true
cp $(ls -t test_taking_quiz_*.mp4 | head -1) slide_10_taking_quiz.mp4 2>/dev/null || true
cp $(ls -t test_student_progress_analytics_*.mp4 | head -1) slide_11_student_progress.mp4 2>/dev/null || true
cp $(ls -t test_instructor_analytics_*.mp4 | head -1) slide_12_instructor_analytics.mp4 2>/dev/null || true
cp $(ls -t test_summary_and_cta_*.mp4 | head -1) slide_13_summary_cta.mp4 2>/dev/null || true

# Clean up test videos
rm -f test_*.mp4

cd - > /dev/null

echo -e "${GREEN}✅ Videos renamed to slide format${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Demo Video Generation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Videos generated:"
ls -lh "$VIDEO_DIR"/slide_*.mp4 | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
echo -e "Total videos: $(ls -1 "$VIDEO_DIR"/slide_*.mp4 2>/dev/null | wc -l)"
echo -e "Output directory: $VIDEO_DIR"
echo ""
echo -e "${BLUE}Demo Player: ${NC}frontend/html/demo-player.html"
