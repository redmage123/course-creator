# AI-Assisted Workflow Templates

## Overview

This directory contains JSON templates for creating complete organization structures using the platform's AI assistant. The templates define organizations, training programs, tracks, courses, instructors, and students in a declarative format.

## Business Context

Setting up a realistic multi-location graduate program manually would take hours and be error-prone. These templates allow you to:

- Define complex organization structures in JSON
- Let the AI assistant intelligently create all entities
- Ensure referential integrity and correct relationships
- Create realistic test data with proper geographic distribution
- Demonstrate the platform's AI capabilities

## Template Files

### 1. organization_template.json
Defines the organization and admin user account.

**Creates:**
- 1 organization (Global Tech Institute)
- 1 organization admin user

### 2. training_programs_template.json
Defines multi-location training programs with sub-projects.

**Creates:**
- 1 main program (Software Engineering Graduate Program 2025)
- 5 geographic locations (NYC, SF, Chicago, Austin, Seattle)
- 4 sub-project tracks (Foundations, Full Stack, Advanced, Capstone)

**Duration:** 18 months (January 2025 - July 2026)

### 3. tracks_template.json
Defines learning tracks with detailed objectives and prerequisites.

**Creates:**
- 4 learning tracks:
  - Foundations Track (12 weeks, beginner)
  - Full Stack Development Track (16 weeks, intermediate)
  - Advanced Specialization Track (14 weeks, advanced)
  - Capstone Projects Track (12 weeks, advanced)

**Total:** Each track includes target audience, prerequisites, learning objectives, and skills taught.

### 4. courses_template.json
Defines individual courses within each track.

**Creates:**
- 12 total courses across all tracks:
  - Foundations: 3 courses (Python, Data Structures, Algorithms)
  - Full Stack: 3 courses (React, Node.js, Deployment)
  - Advanced: 3 courses (Microservices, AWS, DevOps)
  - Capstone: 2 courses (Project Development, Interview Prep)

### 5. instructors_template.json
Defines instructor accounts with location and track assignments.

**Creates:**
- 10 instructors across 5 cities
- Track assignments with date ranges (instructors can switch tracks)
- Expertise and biography for each instructor

**Key Features:**
- Instructors assigned to primary locations
- Track assignments respect program timeline
- Instructors can teach in multiple tracks over time

### 6. students_template.json
Defines student accounts with city assignments and track enrollments.

**Creates:**
- 15 students across 5 cities (3 students per city)
- Each student enrolled in all 4 tracks
- Diverse backgrounds (career changers, graduates, self-taught)

**Distribution:**
- New York City: 3 students
- San Francisco: 3 students
- Chicago: 3 students
- Austin: 3 students
- Seattle: 3 students

### 7. master_workflow_template.json
Orchestrates the entire workflow with execution order and dependencies.

**Defines:**
- 7-step workflow with dependencies
- Success criteria for each step
- AI assistant instructions
- Expected outcomes and verification checks

## How to Use

### Option 1: Run AI-Assisted Workflow (Recommended)

```bash
# Run the automated workflow
python tests/e2e/ai_assisted_workflow.py
```

This script:
1. Creates organization and admin account
2. Logs in as admin
3. Uploads all templates to AI assistant
4. AI assistant creates all entities automatically
5. Verifies everything was created correctly

**Duration:** ~5-10 minutes (depending on AI processing time)

### Option 2: Manual Template Processing

1. **Create Organization:**
   ```bash
   # Use organization_template.json to create org via UI
   ```

2. **Upload Templates to AI Assistant:**
   ```
   - Login as organization admin
   - Navigate to AI Assistant
   - Upload templates in order defined in master_workflow_template.json
   ```

3. **Monitor Progress:**
   ```
   - AI assistant will report progress as it creates entities
   - Verify entities via UI or API
   ```

## Expected Outcomes

After successful execution, your platform will have:

- **1 Organization:** Global Tech Institute
- **26 Users:** 1 admin, 10 instructors, 15 students
- **1 Training Program:** Software Engineering Graduate Program 2025
- **5 Locations:** NYC, SF, Chicago, Austin, Seattle
- **4 Tracks:** Foundations, Full Stack, Advanced, Capstone
- **12 Courses:** Distributed across tracks
- **~20 Instructor Assignments:** Instructors assigned to tracks with schedules
- **60 Student Enrollments:** 15 students × 4 tracks

## Template Customization

### Adding More Students

Edit `students_template.json`:

```json
{
  "email": "new.student@students.globaltech.edu",
  "first_name": "New",
  "last_name": "Student",
  "city": "New York City",
  "background": "Your background description",
  "enrolled_tracks": ["Foundations Track", "Full Stack Development Track"],
  "start_date": "2025-01-15",
  "graduation_date": "2026-07-15"
}
```

### Adding More Locations

Edit `training_programs_template.json` and add to `locations` array:

```json
{
  "city": "Boston",
  "country": "USA",
  "region": "Northeast",
  "timezone": "America/New_York",
  "start_date": "2025-01-15",
  "end_date": "2026-07-15",
  "max_participants": 40,
  "address": "123 Innovation St, Boston, MA 02101"
}
```

### Changing Instructor Track Assignments

Edit `instructors_template.json` and modify `track_assignments`:

```json
{
  "track": "New Track Name",
  "start_date": "2025-XX-XX",
  "end_date": "2025-XX-XX",
  "courses": ["Course 1", "Course 2"]
}
```

## Verification

### Via UI
1. Login as organization admin
2. Navigate to:
   - Training Programs: Check program and locations created
   - Tracks: Verify 4 tracks exist
   - Members: Verify 10 instructors + 15 students
   - Each track: Check course assignments

### Via API

```bash
# Get training programs
curl -H "Authorization: Bearer $TOKEN" \
  "https://localhost:3000/api/v1/courses?organization_id=$ORG_ID"

# Get tracks
curl -H "Authorization: Bearer $TOKEN" \
  "https://localhost:3000/api/v1/tracks/?organization_id=$ORG_ID"

# Get organization members
curl -H "Authorization: Bearer $TOKEN" \
  "https://localhost:3000/api/v1/organizations/$ORG_ID/members"
```

## Troubleshooting

### Issue: AI Assistant Not Responding

**Cause:** AI assistant service may not be running or authentication failed.

**Solution:**
```bash
# Check AI assistant service
docker ps | grep ai-assistant

# Check browser console for auth errors
# Verify auth token exists in localStorage
```

### Issue: Entities Not Created

**Cause:** API errors, missing dependencies, or referential integrity violations.

**Solution:**
- Check browser console for API errors
- Verify organization was created successfully
- Check service logs: `docker logs course-creator-organization-management-1`

### Issue: Instructor/Student Not Assigned to Tracks

**Cause:** Track IDs not matching, date range conflicts.

**Solution:**
- Verify track names match exactly between templates
- Check date ranges don't overlap incorrectly
- Ensure tracks exist before creating assignments

## Architecture

The template system follows this hierarchy:

```
Organization
├── Training Program
│   ├── Location 1 (New York City)
│   ├── Location 2 (San Francisco)
│   ├── Location 3 (Chicago)
│   ├── Location 4 (Austin)
│   └── Location 5 (Seattle)
├── Tracks
│   ├── Foundations Track
│   │   ├── Course 1: Intro to Python
│   │   ├── Course 2: Data Structures
│   │   └── Course 3: Algorithms
│   ├── Full Stack Development Track
│   │   ├── Course 4: React
│   │   ├── Course 5: Node.js
│   │   └── Course 6: Deployment
│   ├── Advanced Specialization Track
│   │   ├── Course 7: Microservices
│   │   ├── Course 8: AWS
│   │   └── Course 9: DevOps
│   └── Capstone Projects Track
│       ├── Course 10: Project Development
│       └── Course 11: Interview Prep
├── Instructors (10)
│   ├── Assigned to locations (primary city)
│   └── Assigned to tracks (with date ranges)
└── Students (15)
    ├── Assigned to locations (by city)
    └── Enrolled in tracks (all 4 tracks)
```

## Timeline

```
2025-01-15 to 2025-04-08 (12 weeks) - Foundations Track
2025-04-15 to 2025-08-19 (16 weeks) - Full Stack Development Track
2025-08-26 to 2025-12-09 (14 weeks) - Advanced Specialization Track
2026-03-01 to 2026-07-15 (12 weeks) - Capstone Projects Track
```

Total: 18 months (54 weeks of instruction + breaks)

## Future Enhancements

- [ ] Add validation scripts to verify template correctness before upload
- [ ] Support for multiple cohorts with different start dates
- [ ] Template inheritance (define base template, extend for variations)
- [ ] Export existing organization structure as templates
- [ ] Template diff tool to compare versions
- [ ] Rollback capability to undo template-created entities

## Contact

For questions or issues with templates:
- Create issue in GitHub repository
- Contact: admin@globaltech.edu
- Documentation: https://docs.globaltech.edu/templates
