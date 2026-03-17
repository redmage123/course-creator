# Sub-Projects and Track Management System

**Version:** 1.0
**Date:** 2025-10-15
**Status:** Design Phase

## 🎯 Business Requirements

### Current Architecture Problem
- Tracks are currently attached directly to main projects
- No organizational hierarchy between projects and tracks
- No student-instructor assignment mechanism
- No instructor communication links stored

### New Architecture Requirements
- **Sub-Projects:** OPTIONAL intermediate layer between main projects and tracks
- **Track Assignments:** Students and instructors assigned to tracks
- **Load Balancing:** Opt-in equal distribution (default OFF, org admin controlled)
- **Instructor Profiles:** Zoom, Teams, and Slack links
- **Course Navigation:** Dropdown interface for track modules
- **Reassignment:** Org admins can reassign students between instructors
- **Minimum Instructors:** At least 1 instructor required per project/sub-project
- **Org Admin as Instructor:** Org admins can be assigned as instructors

---

## 🏗️ Architecture Overview

### New Hierarchy Structure

```
Organization
└── Main Project (e.g., "2025 Enterprise Training")
    ├── Sub-Project 1 (e.g., "Q1 Development Track")
    │   ├── Track 1 (e.g., "Application Development")
    │   │   ├── Assigned Instructors (2-3)
    │   │   ├── Assigned Students (50-100)
    │   │   └── Courses
    │   │       └── Modules (Labs, Quizzes, Content)
    │   └── Track 2 (e.g., "DevOps Engineering")
    └── Sub-Project 2 (e.g., "Q1 Data Science Track")
        └── Track 3 (e.g., "Data Analysis")
```

### Key Relationships

```
projects (main_project)
    ↓ (parent_project_id FK - OPTIONAL)
projects (sub_project - OPTIONAL)
    ↓ OR ↓
tracks (can reference project_id OR sub_project_id)
    ↓ (track_id FK)
track_instructors (junction table) - MINIMUM 1 REQUIRED
track_students (junction table)
```

**Note:** Tracks can belong directly to a main project if no sub-projects exist.

---

## 💾 Database Schema Design

### 1. Projects Table (Extended)

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    parent_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,  -- NULLABLE: For optional sub-projects
    is_sub_project BOOLEAN DEFAULT FALSE,  -- Flag for sub-projects

    -- Existing fields
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',

    -- NEW: Auto-balancing flag
    auto_balance_students BOOLEAN DEFAULT FALSE,  -- Opt-in load balancing

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_project_slug UNIQUE(organization_id, slug),
    CONSTRAINT no_recursive_subprojects CHECK (
        parent_project_id IS NULL OR is_sub_project = TRUE
    )
);

-- Index for sub-project queries
CREATE INDEX idx_projects_parent ON projects(parent_project_id) WHERE parent_project_id IS NOT NULL;
```

### 2. Tracks Table (Updated FK - Flexible)

```sql
ALTER TABLE tracks
    -- Keep existing project_id FK for tracks directly under projects
    -- Add optional sub_project_id for tracks under sub-projects
    ADD COLUMN sub_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Constraint: Track must reference EITHER project_id OR sub_project_id (not both)
    ADD CONSTRAINT tracks_must_reference_project_or_subproject CHECK (
        (project_id IS NOT NULL AND sub_project_id IS NULL) OR
        (project_id IS NULL AND sub_project_id IS NOT NULL)
    );

-- Index for sub-project track queries
CREATE INDEX idx_tracks_subproject ON tracks(sub_project_id) WHERE sub_project_id IS NOT NULL;

-- NO MIGRATION NEEDED: Existing tracks keep their project_id references
```

### 3. Track Instructors (NEW)

```sql
CREATE TABLE track_instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Instructor communication links
    zoom_link VARCHAR(500),
    teams_link VARCHAR(500),
    slack_links JSONB DEFAULT '[]',  -- Array of Slack channel/DM links

    -- Assignment metadata
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),  -- Org admin who made assignment

    CONSTRAINT unique_track_instructor UNIQUE(track_id, user_id)
);

-- Indexes for efficient queries
CREATE INDEX idx_track_instructors_track ON track_instructors(track_id);
CREATE INDEX idx_track_instructors_user ON track_instructors(user_id);

-- Business rule: At least 1 instructor required per track
-- (Enforced at application level and via trigger)
CREATE OR REPLACE FUNCTION validate_minimum_instructors()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM track_instructors WHERE track_id = OLD.track_id) < 1 THEN
        RAISE EXCEPTION 'Cannot remove instructor: Track must have at least 1 instructor assigned';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_min_instructors
BEFORE DELETE ON track_instructors
FOR EACH ROW
EXECUTE FUNCTION validate_minimum_instructors();
```

### 4. Track Students (NEW)

```sql
CREATE TABLE track_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Instructor assignment for load balancing
    assigned_instructor_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Assignment metadata
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),  -- Org admin who made assignment
    last_reassigned_at TIMESTAMP,

    CONSTRAINT unique_track_student UNIQUE(track_id, student_id),
    CONSTRAINT valid_instructor_assignment FOREIGN KEY (track_id, assigned_instructor_id)
        REFERENCES track_instructors(track_id, user_id) ON DELETE SET NULL
);

-- Indexes for efficient queries
CREATE INDEX idx_track_students_track ON track_students(track_id);
CREATE INDEX idx_track_students_student ON track_students(student_id);
CREATE INDEX idx_track_students_instructor ON track_students(assigned_instructor_id);
```

### 5. Courses Table (Updated FK)

```sql
ALTER TABLE courses
    ADD COLUMN track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    ADD CONSTRAINT courses_track_fkey
        FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE;

-- Index for track-course queries
CREATE INDEX idx_courses_track ON courses(track_id);
```

---

## 🔄 Project Creation Wizard Updates

### New Wizard Flow

```
Step 1: Project Details
    ├── Project Name
    ├── Description
    └── Target Roles

Step 2: Project Configuration
    ├── Duration
    ├── Objectives
    └── AI Suggestions

Step 3: Sub-Projects Creation (NEW)
    ├── Define Sub-Projects (e.g., Q1, Q2, Q3, Q4)
    ├── Each sub-project gets:
    │   ├── Name (e.g., "Q1 Development Track")
    │   ├── Description
    │   ├── Start/End Dates
    │   └── Associated Target Roles
    └── Auto-generate tracks for each sub-project

Step 4: Track Review & Confirmation
    ├── Review all tracks across all sub-projects
    ├── Create custom tracks for specific sub-projects
    └── Finalize project creation
```

---

## 👥 Student-Instructor Assignment System

### Load Balancing Algorithm

```python
def assign_students_to_instructors(track_id: UUID, student_ids: List[UUID]) -> Dict[UUID, List[UUID]]:
    """
    Distribute students evenly across instructors assigned to a track

    ALGORITHM:
    1. Get all instructors assigned to track
    2. Sort instructors by current student count (ascending)
    3. Round-robin assignment to balance load
    4. Return mapping: {instructor_id: [student_ids]}

    EXAMPLE:
    - 3 instructors assigned to track
    - 10 students to assign
    - Result: Instructor 1 (4), Instructor 2 (3), Instructor 3 (3)
    """
    instructors = get_track_instructors(track_id)
    current_loads = {i.id: get_student_count(i.id, track_id) for i in instructors}

    # Sort by current load (ascending)
    sorted_instructors = sorted(instructors, key=lambda i: current_loads[i.id])

    # Round-robin assignment
    assignments = {i.id: [] for i in instructors}
    for idx, student_id in enumerate(student_ids):
        instructor = sorted_instructors[idx % len(sorted_instructors)]
        assignments[instructor.id].append(student_id)

    return assignments
```

### Reassignment Rules

1. **Org Admin Only:** Only organization admins can reassign students
2. **Audit Trail:** Log all reassignments with timestamp and admin ID
3. **Notification:** Notify both old and new instructors
4. **Load Check:** Warn if reassignment creates imbalance (>20% difference)

---

## 🎨 UI Components

### 1. Track Detail View

```
┌─────────────────────────────────────────────────────────────┐
│ Track: Application Development (Sub-Project: Q1 Training)   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Instructors (3)                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 👨‍🏫 John Doe (25 students)                                │ │
│ │    🎥 Zoom: https://zoom.us/j/123456                     │ │
│ │    💬 Slack: #dev-track-q1                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ Students (75) [Assign Students] [View All]                   │
│                                                               │
│ Course Modules ▼                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Module 1: Introduction to Python                         │ │
│ │    📚 Content | 🧪 Labs | 📝 Quizzes                     │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Module 2: Data Structures                                │ │
│ │    📚 Content | 🧪 Labs | 📝 Quizzes                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Student Assignment Interface

```
┌─────────────────────────────────────────────────────────────┐
│ Assign Students to Track: Application Development           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Available Students (150)           Assigned Students (75)    │
│ ┌─────────────────────────┐      ┌──────────────────────┐  │
│ │ [x] Alice Johnson       │      │ Bob Smith            │  │
│ │ [x] Carol Williams      │      │   └─ Instructor: John │  │
│ │ [ ] David Brown         │      │ Emma Davis           │  │
│ │ [ ] Frank Miller        │      │   └─ Instructor: Jane │  │
│ └─────────────────────────┘      └──────────────────────┘  │
│                                                               │
│ [Assign Selected (Auto-Balance)] [Assign to Specific]        │
└─────────────────────────────────────────────────────────────┘
```

### 3. Student Reassignment (Drag & Drop)

```
┌─────────────────────────────────────────────────────────────┐
│ Reassign Students Between Instructors                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Instructor: John Doe (28 students) ⚠️ Above avg              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Drag] Alice Johnson                                     │ │
│ │ [Drag] Bob Smith                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ Instructor: Jane Smith (22 students) ✓ Balanced              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Drop Zone]                                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ [Save Reassignments] [Cancel]                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 API Endpoints

### Sub-Projects

```
POST   /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects
GET    /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects
GET    /api/v1/organizations/{org_id}/sub-projects/{sub_project_id}
PUT    /api/v1/organizations/{org_id}/sub-projects/{sub_project_id}
DELETE /api/v1/organizations/{org_id}/sub-projects/{sub_project_id}
```

### Track Assignments

```
POST   /api/v1/organizations/{org_id}/tracks/{track_id}/instructors
DELETE /api/v1/organizations/{org_id}/tracks/{track_id}/instructors/{instructor_id}
PUT    /api/v1/organizations/{org_id}/tracks/{track_id}/instructors/{instructor_id}

POST   /api/v1/organizations/{org_id}/tracks/{track_id}/students
DELETE /api/v1/organizations/{org_id}/tracks/{track_id}/students/{student_id}
PUT    /api/v1/organizations/{org_id}/tracks/{track_id}/students/{student_id}/reassign
GET    /api/v1/organizations/{org_id}/tracks/{track_id}/students?instructor_id={id}
```

### Instructor Load Balancing

```
POST   /api/v1/organizations/{org_id}/tracks/{track_id}/balance-students
GET    /api/v1/organizations/{org_id}/tracks/{track_id}/instructor-loads
```

---

## 🔐 RBAC Permissions

### New Permissions

```python
TRACK_ASSIGN_INSTRUCTORS = "track.assign_instructors"
TRACK_ASSIGN_STUDENTS = "track.assign_students"
TRACK_REASSIGN_STUDENTS = "track.reassign_students"
SUBPROJECT_CREATE = "subproject.create"
SUBPROJECT_MANAGE = "subproject.manage"
```

### Permission Matrix

| Role          | Create Sub-Projects | Assign Instructors | Assign Students | Reassign Students |
|---------------|---------------------|-------------------|-----------------|-------------------|
| Site Admin    | ✅                  | ✅                | ✅              | ✅                |
| Org Admin     | ✅                  | ✅                | ✅              | ✅                |
| Instructor    | ❌                  | ❌                | ❌              | ❌                |
| Student       | ❌                  | ❌                | ❌              | ❌                |

---

## 📊 Implementation Phases

### Phase 1: Database Foundation (Week 1)
- [ ] Design and review database schema
- [ ] Write migration script
- [ ] Create data models (SQLAlchemy)
- [ ] Write unit tests for models

### Phase 2: Backend APIs (Week 2)
- [ ] Implement sub-project CRUD endpoints
- [ ] Implement track assignment endpoints
- [ ] Implement load balancing algorithm
- [ ] Write integration tests

### Phase 3: Project Wizard (Week 3)
- [ ] Add sub-project creation step
- [ ] Update track creation flow
- [ ] Integrate with backend APIs
- [ ] Write E2E tests

### Phase 4: Track Management UI (Week 4)
- [ ] Build track detail view
- [ ] Build student assignment interface
- [ ] Build instructor profile editor
- [ ] Build drag-and-drop reassignment
- [ ] Write E2E tests

### Phase 5: Course Module Navigation (Week 5)
- [ ] Build dropdown module interface
- [ ] Integrate with course content
- [ ] Add lab/quiz navigation
- [ ] Write E2E tests

---

## ✅ Acceptance Criteria

1. **Sub-Projects**
   - [ ] Main projects can have 1-N sub-projects
   - [ ] Sub-projects have own name, description, dates
   - [ ] Sub-projects can be created in wizard

2. **Track Assignment**
   - [ ] Instructors can be assigned to tracks with Zoom/Teams/Slack links
   - [ ] Students can be assigned to tracks
   - [ ] Students auto-assigned to instructors using load balancing

3. **Reassignment**
   - [ ] Org admins can drag-and-drop students between instructors
   - [ ] System warns if load imbalance >20%
   - [ ] Audit trail records all reassignments

4. **Course Navigation**
   - [ ] Track detail shows expandable course module list
   - [ ] Clicking module shows content/labs/quizzes
   - [ ] Instructor list displays with communication links

---

## 🚧 Migration Strategy

### Existing Data Migration

**NO MIGRATION REQUIRED** for existing projects and tracks!

```sql
-- Existing tracks continue to reference project_id
-- Only new tracks under sub-projects will use sub_project_id

-- Add new columns without breaking existing data
ALTER TABLE projects ADD COLUMN parent_project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE projects ADD COLUMN is_sub_project BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN auto_balance_students BOOLEAN DEFAULT FALSE;
ALTER TABLE tracks ADD COLUMN sub_project_id UUID REFERENCES projects(id) ON DELETE CASCADE;

-- Add constraint (works with existing data since project_id is NOT NULL)
ALTER TABLE tracks ADD CONSTRAINT tracks_must_reference_project_or_subproject CHECK (
    (project_id IS NOT NULL AND sub_project_id IS NULL) OR
    (project_id IS NULL AND sub_project_id IS NOT NULL)
);
```

**Backward Compatibility:** All existing functionality continues to work unchanged.

---

## 📈 Success Metrics

1. **Load Balancing Effectiveness**
   - Target: <10% variance in student count per instructor
   - Measure: Standard deviation of student loads

2. **Reassignment Frequency**
   - Target: <5% of students reassigned per month
   - Measure: Reassignment audit log

3. **User Adoption**
   - Target: >80% of org admins use sub-projects
   - Measure: Sub-project creation rate

---

## 🔮 Future Enhancements

1. **Auto-Balancing:** Automatically rebalance when instructors added/removed
2. **Instructor Preferences:** Allow instructors to specify max student count
3. **Student Preferences:** Allow students to request specific instructors
4. **Analytics Dashboard:** Show load distribution charts
5. **Calendar Integration:** Sync Zoom/Teams meetings with calendar

---

**Document Status:** Ready for Implementation
**Next Step:** Database schema review and approval
