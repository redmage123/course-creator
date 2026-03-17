# Quiz Management System Guide

**Version**: 2.2.0  
**Last Updated**: 2025-07-28

## Overview

The Course Creator platform includes a comprehensive quiz management system that enables instructors to publish and unpublish quizzes on a per-course-instance basis, with complete student access control and integrated analytics.

## Key Features

### 🎯 Course Instance-Specific Publishing
- Publish/unpublish quizzes for individual course instances
- Separate control for different sessions of the same course
- Real-time status updates and analytics

### 📊 Instructor Dashboard Integration
- Modal-based interface with tabbed navigation
- Bulk operations (publish/unpublish all quizzes)
- Individual quiz controls with configuration options
- Live analytics display showing student attempts and scores

### 🔒 Student Access Control
- Only enrolled students can access quizzes
- Students see only published quizzes for their course instance
- Automatic enrollment-based access validation
- Configurable attempt limits and time restrictions

### 📈 Analytics Integration
- All quiz attempts stored with course instance tracking
- Complete integration with analytics service
- Real-time performance metrics and participation data
- Detailed attempt history and scoring information

## How It Works

### For Instructors

1. **Access Quiz Management**
   - Navigate to instructor dashboard
   - Click "Quiz Management" for any course
   - Modal opens with course instance tabs

2. **Publish/Unpublish Quizzes**
   - Select course instance tab
   - View all quizzes with publication status
   - Use individual publish/unpublish buttons
   - Or use bulk operations for all quizzes

3. **View Analytics**
   - See real-time attempt counts
   - Monitor average scores
   - Track unique student participation
   - Access detailed performance metrics

### For Students

1. **Quiz Discovery**
   - Log in via unique enrollment URL
   - Navigate to course dashboard
   - Published quizzes appear in quiz section
   - **Note**: Browser refresh required to see newly published quizzes

2. **Taking Quizzes**
   - Click "Take Quiz" on available quizzes
   - Interactive interface with timer and progress
   - Immediate scoring and feedback
   - Attempt tracking and remaining attempts display

3. **Progress Tracking**
   - View quiz completion status
   - See scores and pass/fail results
   - Access attempt history
   - Monitor overall course progress

## Technical Implementation

### Database Schema
```sql
-- Core tables for quiz management
quiz_publications        -- Course instance-specific publication control
quiz_attempts           -- Student attempts with course_instance_id for analytics
student_course_enrollments -- Enrollment-based access control
course_instances        -- Session-specific course management
```

### API Endpoints
```http
# Quiz Publication Management
GET  /course-instances/{instance_id}/quiz-publications
POST /quizzes/publish
PUT  /quiz-publications/{publication_id}

# Student Quiz Access  
GET  /course-instances/{instance_id}/published-quizzes
POST /quiz-attempts
GET  /quiz-attempts/student/{student_id}
```

### Frontend Components
- Modal-based interface with responsive design
- JavaScript modules with error handling
- Real-time status updates and notifications
- Professional CSS styling with animations

## Configuration

### Hydra Configuration
The system uses Hydra configuration management for email notifications and service settings:

```yaml
# services/course-management/conf/config.yaml
email:
  from_address: ${oc.env:EMAIL_FROM_ADDRESS,"noreply@courseplatform.com"}
  smtp:
    server: ${oc.env:SMTP_SERVER,"localhost"}
    port: ${oc.env:SMTP_PORT,587}
    use_tls: ${oc.env:SMTP_USE_TLS,true}
```

## Testing

### Comprehensive Test Suite
- **API Testing**: Endpoint validation and response testing
- **Database Testing**: Schema validation and workflow testing
- **Frontend Testing**: JavaScript functionality and UI component testing
- **Integration Testing**: Complete system workflow validation
- **System Validation**: 12-component comprehensive validation

### Running Tests
```bash
# Quiz management tests
python tests/quiz-management/test_quiz_api_functionality.py
python tests/quiz-management/test_frontend_quiz_management.py
python tests/validation/final_quiz_management_validation.py

# Interactive browser testing
open tests/quiz-management/test_quiz_management_frontend.html
```

## Best Practices

### For Instructors
1. **Course Instance Management**
   - Create separate course instances for different sessions
   - Use descriptive instance names and dates
   - Configure quiz settings per instance as needed

2. **Quiz Publishing Strategy**
   - Test quizzes in unpublished state first
   - Use bulk operations for consistent publishing
   - Monitor student analytics regularly

3. **Student Communication**
   - Inform students about quiz availability
   - Set clear expectations for attempt limits
   - Provide feedback on quiz performance

### For Students
1. **Quiz Preparation**
   - Check course dashboard regularly for new quizzes
   - Refresh browser to see newly published content
   - Review course materials before attempting quizzes

2. **Quiz Taking**
   - Manage time effectively with timer display
   - Save progress frequently if supported
   - Use remaining attempts strategically

## Troubleshooting

### Common Issues

1. **Quiz Not Appearing for Students**
   - Verify quiz is published for correct course instance
   - Check student enrollment status
   - Ensure student refreshes browser page

2. **Analytics Not Updating**
   - Confirm quiz attempts are being stored with course_instance_id
   - Check analytics service connection
   - Verify database migration 011 has been applied

3. **Publication Status Issues**
   - Check course instance ID matching
   - Verify instructor permissions
   - Ensure database consistency

### Support Commands
```bash
# Check service health
curl http://localhost:8004/health

# Validate database schema  
python -c "import asyncpg; # ... check quiz_attempts.course_instance_id"

# Run system validation
python tests/validation/final_quiz_management_validation.py
```

## Migration Notes

### Database Migration Required
The quiz management system requires database migration `011_update_quiz_attempts_table.sql`:

```sql
ALTER TABLE quiz_attempts ADD COLUMN course_instance_id UUID;
ALTER TABLE quiz_attempts 
ADD CONSTRAINT fk_quiz_attempts_course_instance 
FOREIGN KEY (course_instance_id) REFERENCES course_instances(id) ON DELETE CASCADE;
```

### Configuration Updates
- Email service updated to use Hydra configuration
- Database connection updated to use port 5433
- Test files reorganized into proper directory structure

## Future Enhancements

### Planned Features
- Real-time quiz updates without browser refresh
- Advanced quiz question types (drag-and-drop, code completion)
- Proctoring integration for secure quiz taking
- Detailed performance analytics with learning insights
- Quiz templates and question banks

### Integration Opportunities
- LTI integration for external learning management systems
- Mobile app support for quiz taking
- Advanced analytics with machine learning insights
- Collaboration features for group quizzes