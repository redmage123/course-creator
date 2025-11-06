# Sub-Projects (Locations) Feature Design

## Business Context

**Problem**: Large training programs need to run in multiple locations with different schedules. A single "Graduate Training Program" might run simultaneously in Boston, London, and Tokyo, each with different start dates, instructors, and track selections.

**Solution**: Hierarchical project structure with **Main Projects** (templates) and **Sub-Projects** (locations/instances).

## Terminology

- **Main Project**: Template-level project defining the overall program structure
- **Sub-Project / Location / Instance**: Specific execution of the main project in a location with dates
- **Location**: Geographic identifier (country + region + city)
- **Track Override**: Ability to customize track dates/instructors per sub-project

## Use Cases

### Use Case 1: Global Training Program
```
Main Project: "Cloud Architecture Graduate Program"
├── Boston Location (Fall 2025)
│   ├── Location: USA, Massachusetts, Boston
│   ├── Dates: 2025-09-01 to 2025-12-15
│   ├── Tracks: All 4 tracks
│   └── Max: 30 participants
├── London Location (Spring 2026)
│   ├── Location: UK, England, London
│   ├── Dates: 2026-03-01 to 2026-06-15
│   ├── Tracks: 3 of 4 tracks (excluding Advanced Track)
│   └── Max: 25 participants
└── Tokyo Location (Fall 2026)
    ├── Location: Japan, Tokyo, Shibuya
    ├── Dates: 2026-10-01 to 2027-01-15
    ├── Tracks: All 4 tracks + 1 region-specific track
    └── Max: 20 participants
```

### Use Case 2: Staggered Regional Rollout
```
Main Project: "DevOps Engineering Certification"
├── US East Coast (Q1)
├── US West Coast (Q2)
├── Europe (Q3)
└── Asia Pacific (Q4)
```

### Use Case 3: Multiple Cities, Same Country
```
Main Project: "Sales Training Program"
├── New York Office
├── Chicago Office
├── San Francisco Office
└── Los Angeles Office
```

## Data Model

### Main Project (Template)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    objectives TEXT[],
    target_roles VARCHAR(100)[],

    -- Template flag
    is_template BOOLEAN DEFAULT false,
    has_sub_projects BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT projects_org_slug_unique UNIQUE(organization_id, slug)
);
```

### Sub-Project (Location/Instance)
```sql
CREATE TABLE sub_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,

    -- Location
    location_country VARCHAR(100) NOT NULL,
    location_region VARCHAR(100),
    location_city VARCHAR(100),
    location_address TEXT,
    timezone VARCHAR(50),

    -- Scheduling
    start_date DATE,
    end_date DATE,
    duration_weeks INTEGER,

    -- Capacity
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    -- Values: draft, active, completed, cancelled, archived

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT sub_projects_unique UNIQUE(organization_id, parent_project_id, slug)
);

CREATE INDEX idx_sub_projects_parent ON sub_projects(parent_project_id);
CREATE INDEX idx_sub_projects_location ON sub_projects(location_country, location_region, location_city);
CREATE INDEX idx_sub_projects_dates ON sub_projects(start_date, end_date);
CREATE INDEX idx_sub_projects_status ON sub_projects(status);
```

### Track Assignment to Sub-Projects
```sql
CREATE TABLE sub_project_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sub_project_id UUID NOT NULL REFERENCES sub_projects(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,

    -- Schedule overrides (optional)
    start_date DATE,
    end_date DATE,

    -- Assignment
    primary_instructor_id UUID REFERENCES users(id),

    -- Ordering
    sequence_order INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT sub_project_tracks_unique UNIQUE(sub_project_id, track_id)
);

CREATE INDEX idx_sub_project_tracks_sub_project ON sub_project_tracks(sub_project_id);
CREATE INDEX idx_sub_project_tracks_track ON sub_project_tracks(track_id);
```

### Enrollment Changes
```sql
-- Modify enrollments table to support sub-projects
ALTER TABLE enrollments
ADD COLUMN sub_project_id UUID REFERENCES sub_projects(id),
ADD CONSTRAINT enrollments_project_or_sub_project CHECK (
    (project_id IS NOT NULL AND sub_project_id IS NULL) OR
    (project_id IS NULL AND sub_project_id IS NOT NULL)
);

CREATE INDEX idx_enrollments_sub_project ON enrollments(sub_project_id);
```

## API Endpoints

### Sub-Project Management

**List Sub-Projects**
```
GET /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects
Query params: ?location_country=USA&status=active&start_date_from=2025-01-01
Response: Array of sub-project objects
```

**Create Sub-Project**
```
POST /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects
Body: {
    "name": "Boston Location Fall 2025",
    "slug": "boston-fall-2025",
    "description": "Graduate training program for Boston office",
    "location_country": "USA",
    "location_region": "Massachusetts",
    "location_city": "Boston",
    "timezone": "America/New_York",
    "start_date": "2025-09-01",
    "end_date": "2025-12-15",
    "duration_weeks": 16,
    "max_participants": 30,
    "selected_tracks": [
        {"track_id": "uuid1", "sequence_order": 1},
        {"track_id": "uuid2", "sequence_order": 2}
    ]
}
```

**Update Sub-Project**
```
PUT /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}
```

**Delete Sub-Project**
```
DELETE /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}
```

**Get Sub-Project Details**
```
GET /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}
Response: {
    "id": "uuid",
    "name": "Boston Location Fall 2025",
    "location": {...},
    "dates": {...},
    "tracks": [...],
    "participants": {...},
    "instructors": [...]
}
```

**Assign Track to Sub-Project**
```
POST /api/v1/organizations/{org_id}/sub-projects/{sub_project_id}/tracks
Body: {
    "track_id": "uuid",
    "start_date": "2025-09-01",
    "end_date": "2025-10-15",
    "primary_instructor_id": "uuid",
    "sequence_order": 1
}
```

**Compare Sub-Projects**
```
GET /api/v1/organizations/{org_id}/projects/{project_id}/sub-projects/compare?ids=uuid1,uuid2,uuid3
Response: Comparison matrix of participants, tracks, dates, etc.
```

## UI Components

### 1. Project Creation Wizard Enhancement

**Step 1: Project Type Selection** (NEW)
- Radio buttons: "Single Project" vs "Multi-Location Program (with sub-projects)"
- If multi-location: set `is_template = true, has_sub_projects = true`

**Step 2-4**: Existing wizard steps (unchanged)

### 2. Sub-Project Management Tab

**Location**: Org Admin Dashboard → Projects → [Select Project] → "Locations/Locations" tab

**Features**:
- List all sub-projects in a table/card grid
- Filter by location (country dropdown, region dropdown, city search)
- Filter by date range
- Filter by status
- Visual timeline showing all locations
- Map view showing global distribution (optional)

**Columns**:
- Name
- Location (flag icon + city)
- Dates (start - end)
- Status
- Participants (current/max)
- Tracks (count)
- Actions (View, Edit, Delete)

### 3. Create Sub-Project Modal

**Step 1: Basic Info**
- Name (e.g., "Boston Location Fall 2025")
- Slug (auto-generated)
- Description

**Step 2: Location**
- Country (dropdown with flags)
- Region/State (conditional dropdown)
- City (text input with autocomplete)
- Address (optional)
- Timezone (dropdown)

**Step 3: Schedule**
- Start date (date picker)
- End date (date picker)
- Duration (auto-calculated, editable)
- Max participants

**Step 4: Track Selection**
- Checklist of all tracks from parent project
- For each selected track:
  - Override start/end dates (optional)
  - Assign primary instructor (dropdown)
  - Set sequence order (drag to reorder)

**Step 5: Review and Create**
- Summary of all settings
- Preview calendar
- Create button

### 4. Sub-Project Detail View

**Tabs**:
- Overview (stats, location, dates)
- Tracks (list with schedules)
- Participants (enrollment list)
- Instructors (assigned instructors)
- Analytics (completion rates, etc.)
- Settings

### 5. Global Timeline View

Visual timeline showing all sub-projects across time:
```
2025    Q1        Q2        Q3        Q4
        |---------|---------|---------|
        [Boston     =========>        ]
                   [London  =========>]
                            [Tokyo   =====>]
```

### 6. Map View (Optional Enhancement)

Interactive world map with pins for each sub-project location.

## Business Logic Rules

### Rule 1: Parent Project Must Be Template
- If `has_sub_projects = true`, project cannot have direct enrollments
- All enrollments must go through sub-projects

### Rule 2: Track Inheritance
- Sub-projects can only select tracks from parent project
- Cannot add new tracks (must add to parent first)

### Rule 3: Date Validation
- Sub-project dates must be within reasonable range (e.g., not in past)
- Track override dates must be within sub-project date range

### Rule 4: Capacity Management
- `current_participants` auto-increments on enrollment
- Cannot enroll if `current_participants >= max_participants`

### Rule 5: Location Uniqueness
- Warning if creating duplicate location+date combinations
- Allow but warn user

### Rule 6: Status Transitions
```
draft → active (when start_date reached and enrollments open)
active → completed (when end_date reached)
active → cancelled (manual cancellation)
completed → archived (after retention period)
```

## Migration Strategy

### Phase 1: Schema Migration
1. Create `sub_projects` table
2. Create `sub_project_tracks` table
3. Alter `enrollments` table
4. Add `is_template` and `has_sub_projects` to `projects`

### Phase 2: Backend Implementation
1. DAO layer for sub-projects
2. Service layer with business logic
3. API endpoints
4. Unit tests (80%+ coverage)

### Phase 3: Frontend Implementation
1. Sub-project management tab
2. Create sub-project wizard
3. Location filtering
4. Timeline view

### Phase 4: Data Migration (Backwards Compatibility)
```sql
-- Existing projects become "single projects" (not templates)
UPDATE projects SET is_template = false, has_sub_projects = false WHERE is_template IS NULL;
```

### Phase 5: E2E Testing
1. Create main project with sub-projects enabled
2. Create multiple sub-projects in different locations
3. Enroll students in specific sub-projects
4. Verify isolation between sub-projects
5. Test date overrides for tracks

## Reporting Enhancements

### New Reports:
1. **Sub-Project Comparison Report**
   - Compare enrollment, completion, satisfaction across locations

2. **Global Program Dashboard**
   - Total participants across all locations
   - Most popular locations
   - Track completion rates by region

3. **Location Performance Report**
   - Rank locations by performance metrics
   - Identify best practices from top-performing locations

## Security Considerations

### Access Control:
- Org Admin: Can manage all sub-projects within organization
- Project Owner: Can manage all sub-projects of their projects
- Instructor: Can only view sub-projects they're assigned to
- Student: Can only view their enrolled sub-project

### Multi-Tenancy:
- All queries filtered by `organization_id`
- Sub-projects inherit organization from parent project

## Performance Considerations

### Indexing:
- Index on `parent_project_id` for fast sub-project lookup
- Composite index on `(location_country, location_region, location_city)` for location filtering
- Index on `(start_date, end_date)` for date range queries

### Caching:
- Cache location hierarchies (country → regions → cities)
- Cache timezone lists
- Cache sub-project lists per project (invalidate on create/update/delete)

### Query Optimization:
```sql
-- Efficient query for sub-projects with track counts
SELECT
    sp.*,
    COUNT(DISTINCT spt.track_id) as track_count,
    COUNT(DISTINCT e.student_id) as participant_count
FROM sub_projects sp
LEFT JOIN sub_project_tracks spt ON sp.id = spt.sub_project_id
LEFT JOIN enrollments e ON sp.id = e.sub_project_id
WHERE sp.parent_project_id = $1
GROUP BY sp.id;
```

## Testing Strategy

### Unit Tests:
- [ ] Sub-project CRUD operations
- [ ] Track assignment logic
- [ ] Date validation rules
- [ ] Capacity management
- [ ] Status transitions

### Integration Tests:
- [ ] API endpoint responses
- [ ] Database constraints
- [ ] Foreign key cascades

### E2E Tests:
- [ ] Create main project → create sub-project → enroll student
- [ ] Location filtering UI
- [ ] Timeline view rendering
- [ ] Track override functionality

## Documentation

### User Guide:
- How to create a multi-location program
- How to manage sub-projects
- How to compare locations
- Best practices for global programs

### API Documentation:
- OpenAPI spec for all endpoints
- Example requests/responses
- Error codes

---

**Status**: 📝 Design Phase
**Priority**: 🔴 High
**Estimated Effort**: 3-5 days
**Dependencies**: None
**Version**: 3.4.0
