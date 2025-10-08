# Complete Platform Workflow Specification

## Overview

This document specifies the complete end-to-end workflow for the Course Creator Platform, covering the entire organizational learning lifecycle from project creation to personalized AI-assisted learning.

## Test File Location

`/home/bbrelin/course-creator/tests/e2e/critical_user_journeys/test_complete_platform_workflow.py`

## Workflow Summary

**Total Steps:** 16 comprehensive integration tests
**Roles Tested:** Organization Admin, Instructor, Student
**Status:** Test framework complete, awaiting full UI implementation

## Detailed Workflow Steps

### Phase 1: Project & Track Setup (Org Admin)

#### Step 1: Create Project with 2 Tracks
- **Actor:** Organization Admin
- **Action:** Create new project "Platform E2E Project"
- **Sub-actions:**
  - Create "Application Development Track" (intermediate difficulty)
  - Create "Business Analysis Track" (beginner difficulty)
- **Verification:** Both tracks visible in projects section
- **Test:** `test_step_01_org_admin_creates_project_with_tracks`

#### Step 2: Create 2 Instructors
- **Actor:** Organization Admin
- **Action:** Create instructor accounts
- **Instructors:**
  - App Dev Instructor (for Application Development Track)
  - BA Instructor (for Business Analysis Track)
- **Verification:** Both instructors appear in instructors list
- **Test:** `test_step_02_org_admin_creates_instructors`

#### Step 3: Assign Instructors to Tracks
- **Actor:** Organization Admin
- **Action:** Link instructors to their respective tracks
- **Assignments:**
  - App Dev Instructor → Application Development Track
  - BA Instructor → Business Analysis Track
- **Verification:** Assignments visible in tracks management
- **Test:** `test_step_03_org_admin_assigns_instructors_to_tracks`

#### Step 4: Create 4 Courses (2 per Track)
- **Actor:** Organization Admin
- **Action:** Create sequential courses for each track
- **App Dev Track Courses:**
  1. Python Fundamentals (Sequence 1, Beginner)
  2. Advanced Python & Frameworks (Sequence 2, Intermediate)
- **BA Track Courses:**
  1. Requirements Gathering Basics (Sequence 1, Beginner)
  2. Advanced BA Techniques (Sequence 2, Intermediate)
- **Verification:** All 4 courses visible in track listings
- **Test:** `test_step_04_org_admin_creates_courses_for_tracks`

### Phase 2: Course Visibility & Navigation

#### Step 5: Org Admin Course Visibility
- **Actor:** Organization Admin
- **Action:** View all courses across all tracks
- **Expected:** Can see all 4 courses from both tracks
- **Verification:** All courses clickable for details
- **Test:** `test_step_05_course_visibility_org_admin`

#### Step 6: Instructor Course Visibility
- **Actor:** Instructors (both App Dev and BA)
- **Action:** View assigned track courses
- **Expected:**
  - App Dev Instructor sees only App Dev track courses
  - BA Instructor sees only BA track courses
- **Verification:** RBAC enforced per instructor
- **Test:** `test_step_06_course_visibility_instructor`

### Phase 3: AI-Powered Content Generation

#### Step 7: AI Generates Course Materials
- **Actor:** Instructor
- **Action:** Trigger AI content generation for course
- **AI Generates:**
  - Presentation slides
  - Course notes/handouts
  - Relevant videos (found and uploaded from YouTube, etc.)
  - Quizzes with multiple question types
- **Verification:** All materials appear in course content
- **Test:** `test_step_07_ai_generates_course_materials`

### Phase 4: RBAC Content Management

#### Step 8: Org Admin Material Management
- **Actor:** Organization Admin
- **Action:** Manage course materials
- **Permissions:**
  - ✅ CREATE new materials
  - ✅ UPDATE existing materials
  - ✅ DELETE materials
- **Verification:** All CRUD operations successful
- **Test:** `test_step_08_org_admin_can_manage_course_materials`

#### Step 9: Instructor Material Management
- **Actor:** Instructor
- **Action:** Manage own course materials
- **Permissions:**
  - ✅ CREATE new materials for assigned courses
  - ✅ UPDATE existing materials for assigned courses
  - ✅ DELETE materials for assigned courses
- **Verification:** All CRUD operations successful
- **Test:** `test_step_09_instructor_can_manage_course_materials`

### Phase 5: Analytics & Reporting

#### Step 10: Org Admin Analytics Access
- **Actor:** Organization Admin
- **Action:** View analytics for all students
- **Access Level:** ALL students across all tracks
- **Features:**
  - Filter by track
  - Filter by course
  - View progress metrics
  - View completion rates
- **Verification:** Can see data for all enrolled students
- **Test:** `test_step_10_org_admin_analytics_all_students`

#### Step 11: Instructor Analytics Access
- **Actor:** Instructor
- **Action:** View analytics for enrolled students
- **Access Level:** Only students in instructor's courses
- **Features:**
  - Filter by course
  - View progress metrics
  - View quiz scores
  - View lab completion
- **Verification:** Can see data for own students only
- **Test:** `test_step_11_instructor_analytics_all_students`

#### Step 12: Student Analytics Access
- **Actor:** Student
- **Action:** View own progress and analytics
- **Access Level:** OWN data only
- **Features:**
  - View own progress
  - View own quiz scores
  - View own lab completion
  - Cannot see other students' data
- **Verification:** RBAC enforces data isolation
- **Test:** `test_step_12_student_analytics_own_data_only`

### Phase 6: Personalized AI Assistants

#### Step 13: Personalized AI Assistant per Student
- **Actor:** Each Student
- **Feature:** Every student has unique AI assistant
- **Personalization:**
  - Learns from student's interaction history
  - Adapts to student's learning pace
  - Provides personalized recommendations
  - Maintains conversation context
- **Verification:** Different students have different AI assistants
- **Test:** `test_step_13_personalized_ai_assistant_per_student`

#### Step 14: On-Demand Lab Generation
- **Actor:** Student (via AI assistant)
- **Action:** Request lab exercise creation
- **AI Capabilities:**
  - Generate lab based on current course topic
  - Create appropriate difficulty level
  - Provide step-by-step instructions
  - Generate validation criteria
- **Verification:** Lab generated and appropriate for context
- **Test:** `test_step_14_ai_assistant_generates_labs_on_demand`

#### Step 15: On-Demand Quiz Generation
- **Actor:** Student (via AI assistant)
- **Action:** Request quiz creation
- **AI Capabilities:**
  - Generate quiz based on studied material
  - Create multiple question types
  - Adjust difficulty to student level
  - Provide immediate feedback
- **Verification:** Quiz generated and contextually relevant
- **Test:** `test_step_15_ai_assistant_generates_quizzes_on_demand`

### Phase 7: Complete Integration Validation

#### Step 16: End-to-End Workflow Integration
- **Purpose:** Validate entire platform workflow
- **Verifies:**
  - ✅ Projects and tracks created successfully
  - ✅ Instructors assigned correctly
  - ✅ Courses created in proper sequence
  - ✅ AI materials generated
  - ✅ Students enrolled
  - ✅ Analytics accessible per RBAC rules
  - ✅ AI assistants functional
- **Test:** `test_step_16_complete_workflow_integration`

## Test Data Structure

```python
WORKFLOW_DATA = {
    "project": {
        "name": "Platform E2E Project [timestamp]",
        "description": "Complete platform workflow test project"
    },
    "tracks": [
        {
            "name": "Application Development Track",
            "difficulty": "intermediate",
            "description": "Full-stack application development"
        },
        {
            "name": "Business Analysis Track",
            "difficulty": "beginner",
            "description": "Business analysis and requirements gathering"
        }
    ],
    "instructors": [
        {
            "name": "App Dev Instructor",
            "email": "appdev.instructor.[timestamp]@test.com",
            "track": "Application Development Track"
        },
        {
            "name": "BA Instructor",
            "email": "ba.instructor.[timestamp]@test.com",
            "track": "Business Analysis Track"
        }
    ],
    "courses": {
        "app_dev": [
            {
                "title": "Python Fundamentals",
                "description": "Introduction to Python programming",
                "difficulty": "beginner",
                "sequence": 1
            },
            {
                "title": "Advanced Python & Frameworks",
                "description": "Django, Flask, and FastAPI",
                "difficulty": "intermediate",
                "sequence": 2
            }
        ],
        "business_analysis": [
            {
                "title": "Requirements Gathering Basics",
                "description": "Elicitation techniques and documentation",
                "difficulty": "beginner",
                "sequence": 1
            },
            {
                "title": "Advanced BA Techniques",
                "description": "Process modeling and stakeholder management",
                "difficulty": "intermediate",
                "sequence": 2
            }
        ]
    },
    "students": [
        {
            "name": "App Dev Student",
            "email": "appdev.student.[timestamp]@test.com",
            "track": "Application Development Track"
        },
        {
            "name": "BA Student",
            "email": "ba.student.[timestamp]@test.com",
            "track": "Business Analysis Track"
        }
    ]
}
```

## Running the Tests

### Run All Workflow Tests
```bash
export HEADLESS=true
export TEST_BASE_URL=https://localhost:3000
pytest tests/e2e/critical_user_journeys/test_complete_platform_workflow.py -v --tb=short -m e2e
```

### Run Individual Step
```bash
pytest tests/e2e/critical_user_journeys/test_complete_platform_workflow.py::TestCompletePlatformWorkflow::test_step_01_org_admin_creates_project_with_tracks -v
```

## Current Status

### Implemented
- ✅ Test framework structure complete (16 tests)
- ✅ Authentication patterns implemented
- ✅ Role-based test setup methods
- ✅ RBAC verification logic
- ✅ Session management
- ✅ Test data generation

### Pending Implementation
- ⏳ Projects/Tracks UI in org admin dashboard
- ⏳ Instructor assignment UI
- ⏳ Course sequence management
- ⏳ AI content generation triggers
- ⏳ Granular RBAC for course materials
- ⏳ Comprehensive analytics dashboards
- ⏳ Personalized AI assistant UI
- ⏳ On-demand lab generation
- ⏳ On-demand quiz generation

## Integration with Existing Tests

This workflow test builds upon and integrates with:
- **Organization Admin Tests** (41/41 passing)
- **Instructor Tests** (36/36 passing)
- **Student Tests** (if implemented)
- **Guest Tests** (if implemented)

## Success Criteria

All 16 tests passing indicates:
1. Complete project/track management
2. Full RBAC enforcement
3. AI content generation functional
4. Analytics properly scoped per role
5. Personalized AI assistants working
6. On-demand content generation operational
7. End-to-end platform workflow validated

## Next Steps for Development

1. Implement projects/tracks management UI in org admin dashboard
2. Add instructor assignment functionality
3. Build course sequencing system
4. Integrate AI content generation
5. Implement granular material permissions
6. Create comprehensive analytics views
7. Build personalized AI assistant interface
8. Add on-demand content generation features

## Documentation Links

- Org Admin Tests: `tests/e2e/critical_user_journeys/test_org_admin_complete_journey.py`
- Instructor Tests: `tests/e2e/critical_user_journeys/test_instructor_complete_journey.py`
- CLAUDE.md: `CLAUDE.md`
- Test Plan: `tests/COMPREHENSIVE_E2E_TEST_PLAN.md`
