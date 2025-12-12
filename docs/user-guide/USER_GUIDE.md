# Course Creator Platform - User Guide

**Version:** 3.3.1
**Last Updated:** December 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Platform Overview](#platform-overview)
3. [Getting Started](#getting-started)
4. [User Roles & Permissions](#user-roles--permissions)
5. [Student Guide](#student-guide)
6. [Instructor Guide](#instructor-guide)
7. [Organization Admin Guide](#organization-admin-guide)
8. [Site Admin Guide](#site-admin-guide)
9. [AI Assistant Features](#ai-assistant-features)
10. [Lab Environments](#lab-environments)
11. [Technical Reference](#technical-reference)
12. [Troubleshooting](#troubleshooting)
13. [Glossary](#glossary)

---

## Introduction

Welcome to the Course Creator Platform - a comprehensive learning management system designed for corporate training and educational institutions. This platform enables organizations to create, deliver, and track professional development courses with AI-powered assistance.

### Key Features

- **AI-Powered Content Generation**: Create courses, quizzes, and labs with AI assistance
- **Interactive Lab Environments**: Hands-on coding practice with real-time feedback
- **Multi-Tenant Architecture**: Secure organization isolation and management
- **RAG-Enhanced AI Assistant**: Context-aware help and tutoring
- **Comprehensive Analytics**: Track learning progress and engagement
- **Integration Ready**: Connect with Zoom, Slack, and enterprise systems

---

## Platform Overview

### System Architecture

The platform is built on a modern microservices architecture, ensuring scalability, reliability, and maintainability.

![Platform Architecture](images/platform-architecture.svg)

#### Key Components

| Component | Description | Port |
|-----------|-------------|------|
| **User Management** | Authentication, authorization, RBAC | 8000 |
| **Organization Management** | Multi-tenant org management | 8001 |
| **Course Management** | Course CRUD, enrollment | 8002 |
| **Content Management** | Media, documents, resources | 8003 |
| **Course Generator** | AI content generation | 8004 |
| **Lab Manager** | Docker container orchestration | 8005 |
| **Analytics** | Learning analytics & reporting | 8006 |
| **Metadata Service** | Search, tags, categorization | 8007 |
| **RAG Service** | Vector search & retrieval | 8009 |
| **AI Assistant** | Conversational AI interface | 8011 |

### Data Flow

Understanding how data flows through the platform helps in troubleshooting and optimization.

![Data Flow](images/data-flow.svg)

---

## Getting Started

### System Requirements

**For End Users:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection
- Screen resolution: 1280x720 or higher

**For Lab Environments:**
- WebSocket support in browser
- JavaScript enabled

### First-Time Login

1. Navigate to the platform URL provided by your organization
2. Click "Login" or "Register" if creating a new account
3. Enter your credentials
4. Complete the AI Assistant welcome tour (recommended)

### Navigation Overview

The platform uses a role-based dashboard system:

```
┌─────────────────────────────────────────┐
│  [Logo]    Navigation Bar    [Profile]  │
├─────────────────────────────────────────┤
│           │                             │
│  Sidebar  │    Main Content Area        │
│   Menu    │                             │
│           │                             │
│           │                             │
├─────────────────────────────────────────┤
│  AI Assistant Button (Bottom Right)     │
└─────────────────────────────────────────┘
```

---

## User Roles & Permissions

The platform supports five user roles with hierarchical permissions:

### Role Hierarchy

```
Site Admin (Platform-wide access)
    │
    └── Organization Admin (Organization-level access)
            │
            ├── Instructor (Course management)
            │
            └── Student (Learning activities)
                    │
                    └── Guest (Limited public access)
```

### Permission Matrix

| Feature | Site Admin | Org Admin | Instructor | Student | Guest |
|---------|:----------:|:---------:|:----------:|:-------:|:-----:|
| View Public Courses | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enroll in Courses | ✅ | ✅ | ✅ | ✅ | ❌ |
| Create Courses | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage Students | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage Instructors | ✅ | ✅ | ❌ | ❌ | ❌ |
| Organization Settings | ✅ | ✅ | ❌ | ❌ | ❌ |
| Platform Settings | ✅ | ❌ | ❌ | ❌ | ❌ |
| System Monitoring | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Student Guide

### Student Workflow Overview

![Student Workflow](images/student-workflow.svg)

### Dashboard Features

Your student dashboard provides quick access to:

- **Enrolled Courses**: Current courses with progress indicators
- **Upcoming Deadlines**: Assignments, quizzes, and milestones
- **Recent Activity**: Continue where you left off
- **Certificates**: View and download earned certificates
- **Progress Overview**: Visual progress tracking

### Taking Courses

#### Viewing Course Content

1. Navigate to **My Courses** from the dashboard
2. Click on a course to open it
3. Progress through modules sequentially or use the outline
4. Mark lessons as complete when finished

#### Interactive Learning Features

**Video Lessons:**
- Playback speed controls
- Caption support
- Bookmarking key moments
- Progress auto-save

**Reading Materials:**
- Downloadable resources
- Highlighted key concepts
- Searchable content

### Lab Environments

Labs provide hands-on practice in isolated coding environments.

#### Starting a Lab

1. Navigate to the lab section within a course
2. Click "Start Lab Environment"
3. Wait for container initialization (10-30 seconds)
4. Write and run code in the integrated editor

#### Lab Features

- **Monaco Editor**: VS Code-like editing experience
- **Real-time Execution**: Run code and see output instantly
- **AI Assistance**: Get help from the AI assistant
- **Test Validation**: Automatic grading of solutions
- **Save Progress**: Work is auto-saved

#### Best Practices for Labs

- Read the instructions completely before starting
- Use the AI assistant for hints, not answers
- Test your code frequently
- Submit before the deadline

### Quizzes & Assessments

#### Quiz Types

| Type | Description | Feedback |
|------|-------------|----------|
| Practice Quiz | Unlimited attempts, no grade impact | Immediate |
| Graded Quiz | Limited attempts, affects grade | After submission |
| Timed Quiz | Time limit, single attempt | After deadline |

#### Taking a Quiz

1. Click "Start Quiz" from the course
2. Answer all questions
3. Review before submitting
4. View results and feedback

### Earning Certificates

Certificates are awarded upon course completion meeting these criteria:

- All required modules completed
- Minimum quiz score achieved (typically 70%)
- All required labs submitted

#### Downloading Certificates

1. Go to **Certificates** from dashboard
2. Click the certificate to preview
3. Click "Download PDF" or "Share"

---

## Instructor Guide

### Instructor Workflow Overview

![Instructor Workflow](images/instructor-workflow.svg)

### Dashboard Overview

The instructor dashboard provides:

- **My Courses**: Courses you teach
- **Student Activity**: Recent enrollments and submissions
- **Analytics**: Engagement metrics
- **Quick Actions**: Create course, view students

### Creating Courses

#### Method 1: AI-Assisted Creation

1. Click **Create Course** → **Use AI Generator**
2. Enter course topic and objectives
3. Select target audience and duration
4. Click "Generate Outline"
5. Review and edit the generated outline
6. Click "Generate Content" for each section
7. Review, edit, and publish

#### Method 2: Manual Creation

1. Click **Create Course** → **Start from Scratch**
2. Fill in course details:
   - Title and description
   - Category and tags
   - Learning objectives
   - Prerequisites
3. Add modules and lessons
4. Upload or create content
5. Configure assessments
6. Preview and publish

### Content Generation with AI

The AI content generator can create:

- **Course Outlines**: Structured curriculum
- **Lesson Content**: Text, slides, summaries
- **Quiz Questions**: Multiple choice, true/false, coding
- **Lab Exercises**: Code templates and test cases

#### Using the Content Generator

```
1. Navigate to: Instructor → Content Generator
2. Select content type
3. Provide context and requirements
4. Generate and review
5. Edit as needed
6. Add to course
```

### Managing Students

#### Enrolling Students

**Individual Enrollment:**
1. Go to course → Students tab
2. Click "Enroll Student"
3. Search by name or email
4. Click "Enroll"

**Bulk Enrollment:**
1. Go to course → Students → Bulk Enroll
2. Download the template CSV
3. Fill in student information
4. Upload the completed CSV
5. Review and confirm

#### Tracking Progress

The student progress view shows:

- Completion percentage
- Quiz scores
- Lab submissions
- Time spent
- Last activity

### Creating Labs

#### Lab Environment Setup

1. Navigate to course → Labs → Create Lab
2. Configure environment:
   - Programming language
   - Required packages
   - Memory/CPU limits
3. Create starter code template
4. Define test cases
5. Set grading criteria
6. Preview and publish

### Analytics & Reporting

Access detailed analytics:

- **Engagement**: Time on platform, video completion
- **Performance**: Quiz scores, lab grades
- **Trends**: Progress over time
- **Comparisons**: Cohort analysis

#### Generating Reports

1. Go to Analytics → Reports
2. Select report type
3. Choose date range
4. Select students/courses
5. Export as PDF or CSV

---

## Organization Admin Guide

### Organization Admin Workflow

![Organization Admin Workflow](images/org-admin-workflow.svg)

### Organization Setup

#### Initial Configuration

1. **Organization Profile**
   - Name and description
   - Logo and branding
   - Contact information

2. **Compliance Settings**
   - Data retention policies
   - Privacy preferences
   - GDPR/CCPA compliance

3. **Integration Setup**
   - SSO configuration
   - Zoom integration
   - Slack notifications

### Member Management

#### Inviting Members

1. Go to **Members** → **Invite**
2. Enter email address(es)
3. Select role (Student, Instructor)
4. Send invitation

#### Bulk Import

1. Download member template
2. Fill in member details
3. Upload CSV file
4. Review and confirm

#### Role Assignment

```
Available Roles:
├── Instructor
│   ├── Can create courses
│   ├── Can manage students
│   └── Can view analytics
│
└── Student
    ├── Can enroll in courses
    ├── Can complete assessments
    └── Can earn certificates
```

### Training Tracks

Training tracks group related courses into learning paths.

#### Creating a Track

1. Go to **Tracks** → **Create Track**
2. Enter track details:
   - Name and description
   - Target audience
   - Duration estimate
3. Add courses:
   - Select from organization courses
   - Set sequence order
   - Define prerequisites
4. Publish track

### Projects & Cohorts

Projects organize training for specific groups.

#### Creating a Project

1. **Define Project**
   - Name and objectives
   - Start and end dates
   - Success criteria

2. **Create Cohorts**
   - Group students
   - Assign instructors
   - Set schedules

3. **Assign Content**
   - Select tracks or courses
   - Set deadlines
   - Configure completion requirements

### Integrations

#### Zoom Integration

1. Go to **Settings** → **Integrations** → **Zoom**
2. Click "Connect Zoom Account"
3. Authorize access
4. Configure room defaults

**Features:**
- Auto-create meeting rooms
- Sync participant lists
- Record sessions

#### Slack Integration

1. Go to **Settings** → **Integrations** → **Slack**
2. Click "Add to Slack"
3. Select workspace
4. Choose notification channels

**Notification Types:**
- Course enrollments
- Completion milestones
- Deadline reminders
- Announcements

### Organization Analytics

Key metrics available:

| Metric | Description |
|--------|-------------|
| Active Users | Users logged in (7/30 day) |
| Course Completions | Total completions |
| Engagement Rate | Active learning time |
| Compliance Rate | Mandatory training completion |

---

## Site Admin Guide

### Site Admin Workflow

![Site Admin Workflow](images/site-admin-workflow.svg)

### Platform Overview Dashboard

The site admin dashboard provides:

- **System Health**: All services status
- **Platform Metrics**: Users, orgs, courses
- **Critical Alerts**: Issues requiring attention
- **Quick Actions**: Common admin tasks

### Organization Management

#### Creating Organizations

1. Go to **Organizations** → **Create**
2. Enter organization details
3. Set resource limits
4. Assign initial admin
5. Activate organization

#### Managing Organizations

| Action | Description |
|--------|-------------|
| Edit | Modify settings |
| Suspend | Temporarily disable |
| Activate | Re-enable suspended org |
| Delete | Permanent removal |

### Global User Management

#### User Search

Search across all organizations by:
- Username or email
- Organization
- Role
- Status

#### User Actions

- View profile and activity
- Reset password
- Change role
- Transfer between orgs
- Disable/enable account

### System Configuration

#### Platform Settings

```yaml
General:
  - Platform name
  - Contact email
  - Support URL

Features:
  - Registration enabled
  - Guest access
  - AI features
  - Lab environments

Limits:
  - Max organizations
  - Users per org
  - Storage per org
  - Concurrent labs
```

#### Security Settings

- Password policies
- Session timeouts
- 2FA requirements
- API rate limits

### System Monitoring

#### Service Status

Monitor all microservices:
- Health status
- Response times
- Error rates
- Resource usage

#### Log Management

Access logs for:
- Application events
- Security events
- Error tracking
- Audit trail

### Demo Management

#### Creating Demo Data

1. Go to **Demo** → **Create Demo**
2. Select template (Small, Medium, Large)
3. Configure options
4. Generate data

#### Demo Reset

Reset demo environment to initial state:
1. Go to **Demo** → **Reset**
2. Confirm reset
3. Wait for completion

---

## AI Assistant Features

### Overview

The AI Assistant is available platform-wide to help with:

- **Navigation Help**: Finding features and pages
- **Learning Assistance**: Explaining concepts
- **Technical Support**: Troubleshooting issues
- **Content Creation**: Generating course materials

### Accessing the AI Assistant

Click the AI bubble icon in the bottom-right corner of any page.

### Conversation Features

#### Natural Language Queries

Ask questions naturally:
- "How do I create a new course?"
- "What are my upcoming deadlines?"
- "Explain Python list comprehensions"

#### Context Awareness

The assistant knows:
- Your current page
- Your role and permissions
- Your enrolled courses
- Platform features

### Role-Specific Assistance

| Role | AI Capabilities |
|------|-----------------|
| Student | Study help, quiz prep, lab hints |
| Instructor | Content ideas, grading help, analytics |
| Org Admin | Setup guidance, reporting, integrations |
| Site Admin | System monitoring, troubleshooting |

### RAG-Enhanced Responses

The assistant uses Retrieval-Augmented Generation (RAG) to provide:
- Course-specific answers
- Platform documentation
- Best practices
- Troubleshooting guides

---

## Lab Environments

### Architecture

Lab environments use Docker containers for isolation:

```
┌──────────────────────────────────────┐
│          User's Browser              │
│  ┌────────────────────────────────┐  │
│  │      Monaco Editor (IDE)       │  │
│  │  ┌─────────────────────────┐   │  │
│  │  │    Code Editor Pane     │   │  │
│  │  ├─────────────────────────┤   │  │
│  │  │    Output Console       │   │  │
│  │  └─────────────────────────┘   │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
                    │
                    │ WebSocket
                    ▼
┌──────────────────────────────────────┐
│         Lab Manager Service          │
│  ┌────────────────────────────────┐  │
│  │   Container Orchestration      │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│     Docker Container (per user)      │
│  ┌─────────┐  ┌─────────┐           │
│  │  Python │  │  Node   │  ...      │
│  └─────────┘  └─────────┘           │
└──────────────────────────────────────┘
```

### Supported Languages

| Language | Version | Features |
|----------|---------|----------|
| Python | 3.11 | Full standard library |
| JavaScript | Node 18 | npm packages |
| Java | 17 | JDK + common libs |
| Go | 1.21 | Standard library |
| Rust | 1.70 | Cargo support |

### Lab Best Practices

**For Students:**
1. Save work frequently (auto-save enabled)
2. Test incrementally
3. Read error messages carefully
4. Use AI assistant for hints

**For Instructors:**
1. Provide clear instructions
2. Include starter code
3. Create comprehensive tests
4. Set appropriate time limits

---

## Technical Reference

### API Overview

The platform exposes RESTful APIs for all services:

```
Base URL: https://your-domain.com/api/v1

Authentication:
  Header: Authorization: Bearer <token>

Common Endpoints:
  GET  /users/me          - Current user
  GET  /courses           - List courses
  POST /courses           - Create course
  GET  /courses/{id}      - Get course
  PUT  /courses/{id}      - Update course
```

### WebSocket Connections

Real-time features use WebSocket:

```javascript
// AI Assistant
ws://domain/ws/ai-assistant

// Lab Environment
ws://domain/ws/lab/{labId}
```

### Database Schema

Key entities:

```
users
  ├── id (UUID)
  ├── username
  ├── email
  ├── role
  └── organization_id

courses
  ├── id (UUID)
  ├── title
  ├── description
  ├── instructor_id
  └── organization_id

enrollments
  ├── user_id
  ├── course_id
  ├── progress
  └── status
```

---

## Troubleshooting

### Common Issues

#### Login Problems

| Issue | Solution |
|-------|----------|
| Forgot password | Use "Forgot Password" link |
| Account locked | Contact organization admin |
| SSO not working | Check with IT department |

#### Course Access Issues

| Issue | Solution |
|-------|----------|
| Can't see course | Verify enrollment |
| Content not loading | Clear browser cache |
| Progress not saving | Check internet connection |

#### Lab Environment Issues

| Issue | Solution |
|-------|----------|
| Lab won't start | Refresh page, try again |
| Code not running | Check syntax errors |
| Timeout errors | Optimize code efficiency |
| Lost work | Check auto-save history |

### Getting Help

1. **AI Assistant**: Click the AI bubble for instant help
2. **FAQ**: Check the Help section
3. **Support**: Contact your organization admin
4. **Technical Support**: support@coursecreator.com

---

## Glossary

| Term | Definition |
|------|------------|
| **Cohort** | Group of students taking a course together |
| **Course** | Collection of learning modules |
| **Enrollment** | Student registration in a course |
| **Lab** | Interactive coding environment |
| **Module** | Section within a course |
| **Organization** | Company or institution using the platform |
| **RAG** | Retrieval-Augmented Generation (AI technique) |
| **Track** | Sequence of related courses |
| **RBAC** | Role-Based Access Control |

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Open search |
| `Escape` | Close modal/AI Assistant |
| `?` | Show help |
| `N` | Next lesson (in course) |
| `P` | Previous lesson (in course) |

### Browser Compatibility

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

---

*For the latest documentation and updates, visit the platform help center or contact your administrator.*
