# Course Creator Platform - User Guide

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Admin Guide](#admin-guide)  
3. [Instructor Guide](#instructor-guide)
4. [Student Guide](#student-guide)
5. [Interactive Labs](#interactive-labs)
6. [Content Management](#content-management)
7. [Analytics & Reports](#analytics--reports)
8. [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### First Time Login

After platform installation, access the appropriate dashboard:

- **Admin**: http://localhost:3000/admin.html
- **Instructor**: http://localhost:3000/instructor-dashboard.html  
- **Student**: http://localhost:3000/student-dashboard.html

### Account Creation

**Admin accounts** are created during installation with `python create-admin.py`.

**Instructor and Student accounts** are created by administrators through the admin panel.

## 👑 Admin Guide

### Dashboard Overview

The admin dashboard provides:
- User management (create/edit/delete users)
- Platform configuration
- System monitoring and analytics
- Content moderation
- Lab environment management

### Managing Users

#### Creating Users

1. **Navigate to Admin Dashboard**
2. **Click "User Management"**
3. **Click "Add New User"**
4. **Fill in required information**:
   - Username (unique)
   - Email address
   - Password (temporary)
   - Role (Admin/Instructor/Student)
   - Full name
5. **Click "Create User"**

**The user will receive login credentials and can change their password on first login.**

#### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full platform access, user management, system configuration |
| **Instructor** | Create/manage courses, view analytics, manage students |
| **Student** | Access enrolled courses, complete labs, view progress |

#### Bulk User Import

```bash
# CSV format: username,email,role,full_name
# Example: john.doe,john@example.com,student,John Doe

# Import users from CSV
python scripts/import-users.py users.csv
```

### Platform Configuration

#### AI Service Settings

1. **Go to "Platform Settings"**
2. **Configure AI Services**:
   - Anthropic API settings
   - OpenAI API settings (optional)
   - Content generation preferences
   - Rate limiting settings

#### Lab Environment Settings

1. **Go to "Lab Configuration"**
2. **Configure Lab Settings**:
   - Maximum concurrent labs
   - Available programming languages
   - IDE options (VS Code, Vim, Nano)
   - Resource limits (CPU, memory)
   - Session timeout settings

#### Security Settings

1. **Go to "Security Settings"**
2. **Configure Security Options**:
   - Password policies
   - Session timeout
   - Two-factor authentication
   - API rate limiting

### System Monitoring

#### Health Dashboard

Monitor system health through:
- Service status indicators
- Resource usage graphs
- Error logs and alerts
- Performance metrics

#### Analytics Overview

View platform-wide analytics:
- User activity trends
- Course popularity
- Lab usage statistics
- Content generation metrics

## 👨‍🏫 Instructor Guide

### Dashboard Overview

The instructor dashboard includes:
- Course creation and management
- Student enrollment and progress tracking
- Content upload and AI generation
- Lab environment design
- Analytics and reporting

### Creating Courses

#### AI-Powered Course Generation

1. **Click "Create New Course"**
2. **Enter Course Details**:
   - Course name and description
   - Target audience level
   - Learning objectives
3. **Upload Source Materials** (drag & drop):
   - PDF documents
   - PowerPoint presentations
   - Word documents
   - Text files
4. **Configure AI Generation**:
   - Content depth level
   - Number of modules
   - Include exercises/quizzes
   - Lab requirements
5. **Click "Generate Course"**

**The AI will analyze your materials and generate:**
- Course outline and structure
- Learning modules with explanations
- Interactive exercises
- Quiz questions
- Lab assignments
- Assessment rubrics

#### Manual Course Creation

1. **Click "Create New Course"**
2. **Choose "Manual Creation"**
3. **Add Course Structure**:
   - Create modules/chapters
   - Add lessons within modules
   - Include text, images, videos
   - Design assessments
4. **Save Course Draft**

### Content Management

#### Upload Content Types

**Supported Formats:**
- **Documents**: PDF, DOCX, TXT, MD
- **Presentations**: PPTX, PPT
- **Images**: JPG, PNG, GIF, SVG
- **Videos**: MP4, WebM (upload to external service)
- **Code**: Python, JavaScript, Java, C++, etc.

#### Content Processing

When you upload content:
1. **File Analysis**: AI extracts key concepts and structure
2. **Content Generation**: Creates course modules and materials
3. **Exercise Creation**: Generates relevant practice problems
4. **Lab Design**: Creates hands-on coding exercises

#### Export Options

Export your courses in multiple formats:
- **PowerPoint**: Complete slide deck
- **PDF**: Printable course materials
- **SCORM**: LMS-compatible package
- **JSON**: Structured course data
- **ZIP**: Complete course archive

### Managing Students

#### Student Enrollment

1. **Go to Course Management**
2. **Select Your Course**
3. **Click "Manage Students"**
4. **Add Students**:
   - Individual enrollment
   - Bulk enrollment from CSV
   - Self-enrollment codes

#### Progress Tracking

Monitor student progress:
- **Module Completion**: Track progress through course materials
- **Lab Submissions**: View submitted code and solutions
- **Quiz Scores**: Automated grading with detailed results
- **Time Spent**: Engagement metrics and study patterns
- **Difficulty Areas**: Identify concepts students struggle with

#### Communication

Communicate with students:
- **Announcements**: Course-wide notifications
- **Feedback**: Individual feedback on assignments
- **Discussion Forums**: Q&A and collaboration
- **Direct Messages**: Private communication

### Lab Environment Design

#### Creating Interactive Labs

1. **Go to "Lab Designer"**
2. **Choose Lab Type**:
   - **Coding Exercise**: Write and test code
   - **Project-Based**: Multi-file projects
   - **Tutorial**: Step-by-step guided coding
   - **Assessment**: Graded coding challenges

3. **Configure Lab Environment**:
   - Programming language
   - Available IDE options
   - Starter code/templates
   - Test cases and validation
   - Resource limits

4. **Add Instructions**:
   - Clear problem description
   - Expected outcomes
   - Hints and tips
   - Grading criteria

#### Multi-IDE Support

Students can choose their preferred development environment:
- **VS Code**: Full-featured IDE with extensions
- **Vim**: Terminal-based editor for advanced users
- **Nano**: Simple, beginner-friendly editor

Each IDE includes:
- Syntax highlighting
- Code completion
- Debugging tools (where applicable)
- File management
- Terminal access

### Analytics for Instructors

#### Course Analytics

- **Enrollment Trends**: Track student sign-ups over time
- **Completion Rates**: Module and course completion statistics
- **Engagement Metrics**: Time spent, interactions, downloads
- **Performance Data**: Quiz scores, lab submissions, grades

#### Student Analytics

- **Individual Progress**: Detailed student performance
- **Learning Patterns**: Study habits and preferences
- **Difficulty Analysis**: Topics students find challenging
- **Engagement Scores**: Participation and interaction levels

## 👨‍🎓 Student Guide

### Dashboard Overview

The student dashboard shows:
- Enrolled courses and progress
- Upcoming assignments and deadlines
- Recent activity and achievements
- Quick access to lab environments

### Browsing and Enrolling in Courses

#### Finding Courses

1. **Browse Course Catalog**: View all available courses
2. **Search and Filter**: Find courses by topic, difficulty, or instructor
3. **View Course Details**: Read descriptions, prerequisites, and outcomes

#### Enrollment Process

1. **Click "Enroll" on desired course**
2. **Confirm enrollment** (may require instructor approval)
3. **Access course materials** immediately after approval

### Taking Courses

#### Navigation

- **Course Overview**: See all modules and progress
- **Module Content**: Read lessons, watch videos, view materials
- **Progress Tracking**: Monitor completion status
- **Bookmarks**: Save important sections for review

#### Interactive Elements

- **Quizzes**: Test your understanding with instant feedback
- **Discussions**: Participate in course forums
- **Downloads**: Access course materials offline
- **Notes**: Take personal notes within the platform

### Using Lab Environments

#### Starting a Lab

1. **Navigate to Lab Section** in your course
2. **Click "Launch Lab Environment"**
3. **Choose Your IDE** (VS Code, Vim, or Nano)
4. **Wait for environment to load** (30-60 seconds)

#### Working in Labs

**File Management:**
- Create, edit, and delete files
- Upload files from your computer
- Download your work
- Organize files in folders

**Code Execution:**
- Run code directly in the browser
- Use integrated terminal
- View output and errors
- Debug your programs

**Collaboration Features:**
- Share your screen with instructors
- Request help through built-in chat
- Submit assignments directly from the lab

#### Supported Languages and Tools

| Language | Features | Available Tools |
|----------|----------|-----------------|
| **Python** | Full Python 3.x, pip packages | pytest, jupyter, numpy, pandas |
| **JavaScript** | Node.js, npm packages | npm, webpack, jest |
| **Java** | OpenJDK, Maven support | javac, maven, junit |
| **C++** | GCC compiler, debugging | g++, gdb, make |
| **HTML/CSS** | Live preview, validation | Browser preview, validators |
| **SQL** | Database queries, practice DBs | sqlite3, postgresql client |

### Submitting Assignments

#### Lab Assignments

1. **Complete the coding exercise** in the lab environment
2. **Test your solution** using provided test cases
3. **Click "Submit Assignment"**
4. **Add comments or explanations** (optional)
5. **Confirm submission**

**Your code is automatically saved and can be resubmitted before the deadline.**

#### Written Assignments

1. **Download assignment template** (if provided)
2. **Complete assignment** offline
3. **Upload completed file** (PDF, DOCX, etc.)
4. **Add submission comments**
5. **Submit before deadline**

### Progress Tracking

#### Personal Dashboard

Monitor your learning:
- **Course Progress**: Percentage completion for each course
- **Grades**: Quiz scores and assignment grades
- **Achievements**: Badges and milestones earned
- **Study Time**: Time spent in courses and labs
- **Upcoming Deadlines**: Assignment and quiz due dates

#### Performance Analytics

View detailed analytics:
- **Learning Velocity**: How quickly you're progressing
- **Strength Areas**: Topics you excel in
- **Improvement Areas**: Concepts that need more practice
- **Engagement Score**: Your participation level

## 💻 Interactive Labs

### Lab Environment Features

#### Multi-IDE Support

**VS Code (Recommended for beginners):**
- Visual interface with file explorer
- Syntax highlighting and error detection
- Integrated terminal and debugging
- Extension support for enhanced functionality

**Vim (Advanced users):**
- Powerful keyboard-driven editor
- Efficient for experienced developers
- Customizable with plugins
- Lightning-fast text editing

**Nano (Simple and easy):**
- Straightforward text editor
- Minimal learning curve
- Perfect for quick edits
- Clear on-screen help

#### Development Tools

Each lab environment includes:
- **Compilers/Interpreters**: Language-specific execution
- **Package Managers**: Install libraries and dependencies
- **Version Control**: Git for source code management
- **Debugging Tools**: Step-through debugging where supported
- **Testing Frameworks**: Unit testing and validation tools

#### File Operations

- **Upload Files**: Drag and drop or browse to upload
- **Download Files**: Save your work locally
- **File Templates**: Pre-configured starter files
- **Project Structure**: Maintain organized directory layouts

### Lab Types

#### Coding Exercises

**Purpose**: Practice specific programming concepts
**Duration**: 15-60 minutes
**Features**:
- Guided instructions
- Starter code provided
- Automated testing
- Instant feedback

**Example**: "Implement a sorting algorithm in Python"

#### Project-Based Labs

**Purpose**: Build complete applications
**Duration**: 2-8 hours (can be completed over multiple sessions)
**Features**:
- Multi-file projects
- Complex requirements
- Milestone checkpoints
- Peer collaboration

**Example**: "Build a web calculator with HTML, CSS, and JavaScript"

#### Tutorial Labs

**Purpose**: Learn new technologies step-by-step
**Duration**: 30-90 minutes
**Features**:
- Step-by-step instructions
- Progressive difficulty
- Checkpoint validation
- Help hints available

**Example**: "Introduction to React: Building Your First Component"

#### Assessment Labs

**Purpose**: Evaluate learning and skills
**Duration**: 60-180 minutes
**Features**:
- Timed environment
- No external help
- Automated grading
- Detailed feedback after completion

**Example**: "Data Structures Final Exam - Implement Binary Tree Operations"

### Lab Best Practices

#### For Students

1. **Read Instructions Carefully**: Understand requirements before coding
2. **Start Early**: Don't wait until the deadline
3. **Test Frequently**: Run your code often to catch errors early
4. **Use Version Control**: Commit your progress regularly
5. **Ask for Help**: Use built-in help features when stuck
6. **Save Your Work**: Labs auto-save, but download important files

#### Common Issues and Solutions

**Lab Won't Start:**
- Check your internet connection
- Clear browser cache and cookies
- Try a different browser (Chrome/Firefox recommended)
- Contact instructor if problems persist

**Code Won't Run:**
- Check for syntax errors (highlighted in red)
- Verify file names match requirements
- Ensure all required files are present
- Check that you're using the correct programming language

**Lost Work:**
- Labs auto-save every 30 seconds
- Check the "Recent Files" section
- Look in the .backup folder
- Contact support for file recovery

## 📊 Content Management

### Content Upload System

#### Drag-and-Drop Interface

The platform features an intuitive drag-and-drop system:

1. **Access Content Manager**: Go to instructor dashboard
2. **Click "Upload Content"** or drag files directly to the upload area
3. **Supported Formats**: PDF, DOCX, PPTX, TXT, images, code files
4. **Processing**: AI automatically analyzes and processes your content
5. **Review and Edit**: Customize generated course materials

#### Content Processing Pipeline

When you upload content, the system:

1. **File Analysis**: Extracts text, images, and structure
2. **Content Understanding**: AI identifies key concepts and topics
3. **Structure Generation**: Creates logical course progression  
4. **Exercise Creation**: Generates relevant practice problems
5. **Assessment Design**: Creates quizzes and evaluation materials

### AI-Powered Content Generation

#### Smart Course Creation

**Input**: Upload your existing materials (slides, documents, etc.)
**Output**: Complete structured course with:
- Learning objectives
- Module breakdown
- Interactive exercises  
- Assessment questions
- Lab assignments
- Progress tracking

#### Content Enhancement

The AI can enhance your content by:
- **Adding Examples**: Real-world applications and use cases
- **Creating Analogies**: Helping students understand complex concepts
- **Generating Exercises**: Practice problems at appropriate difficulty
- **Building Assessments**: Quiz questions with multiple choice, coding, and essay formats
- **Suggesting Labs**: Hands-on coding exercises that reinforce learning

### Export and Sharing

#### Multiple Export Formats

**PowerPoint (.pptx):**
- Complete slide deck with all course content
- Formatted for classroom presentation
- Includes speaker notes and animations

**PDF Document:**
- Printable course materials
- Student handout format
- Includes exercises and answer keys

**SCORM Package:**
- LMS-compatible format
- Upload to Canvas, Blackboard, Moodle
- Includes tracking and progress data

**JSON Data:**
- Structured course information
- API-compatible format
- Custom integration support

**ZIP Archive:**
- Complete course package
- All files and resources included
- Portable and shareable

#### Sharing Options

- **Direct Links**: Share course URLs with students
- **Embed Codes**: Integrate into existing websites
- **QR Codes**: Easy mobile access
- **Social Media**: Share course previews
- **Email Integration**: Send course invitations

## 📈 Analytics & Reports

### Student Analytics

#### Individual Progress Reports

**Available Metrics:**
- Course completion percentage
- Time spent in each module
- Quiz scores and trends
- Lab assignment submissions
- Engagement and participation levels

**Visual Reports:**
- Progress charts and graphs
- Heat maps of activity
- Performance comparisons
- Learning velocity trends

#### Learning Pattern Analysis

**Study Habits:**
- Preferred study times
- Session duration patterns
- Content consumption preferences
- Break patterns and productivity

**Performance Insights:**
- Strongest subject areas
- Areas needing improvement
- Learning speed analysis
- Retention rate tracking

### Instructor Analytics

#### Course Performance Metrics

**Enrollment and Completion:**
- Student enrollment trends
- Course completion rates
- Drop-off points identification
- Success rate analysis

**Content Effectiveness:**
- Most/least engaging modules
- Time spent per section
- Student feedback scores
- Content difficulty analysis

#### Student Management Data

**Class Overview:**
- Overall class performance
- Individual student progress
- At-risk student identification
- Grade distribution analysis

**Engagement Tracking:**
- Discussion participation
- Lab environment usage
- Assignment submission patterns
- Help-seeking behavior

### Platform Analytics (Admin)

#### System Performance

**Resource Usage:**
- Server resource utilization
- Database performance metrics
- Lab environment capacity
- Storage usage patterns

**User Activity:**
- Daily/weekly active users
- Peak usage times
- Feature utilization rates
- Geographic distribution

#### Content Management Stats

**AI Usage:**
- Course generation requests
- Content processing volume
- AI service performance
- Cost and usage optimization

**Content Library:**
- Total courses created
- Content types uploaded
- Export format popularity
- Sharing and collaboration metrics

### Custom Reports

#### Report Builder

Create custom reports with:
- **Date Range Selection**: Specific time periods
- **User Filtering**: Specific students, instructors, or groups
- **Metric Selection**: Choose relevant data points
- **Visualization Options**: Charts, tables, graphs
- **Export Formats**: PDF, Excel, CSV

#### Automated Reports

Set up automated reports for:
- **Weekly Progress**: Student advancement summaries
- **Monthly Analytics**: Course performance reviews
- **Semester Reports**: Comprehensive academic analysis
- **Alert Reports**: Performance issues and interventions needed

## 🔧 Troubleshooting

### Common Issues

#### Login Problems

**Can't access the platform:**
1. Verify the correct URL (http://localhost:3000)
2. Check if services are running: `./app-control.sh docker-status`
3. Clear browser cache and cookies
4. Try incognito/private browsing mode
5. Contact administrator for account verification

**Password issues:**
1. Use the "Forgot Password" link on login page
2. Contact administrator for password reset
3. Ensure caps lock is off
4. Check for special character requirements

#### Course Access Issues

**Can't see enrolled courses:**
1. Verify enrollment status with instructor
2. Check if course is published and active
3. Refresh the page or clear browser cache
4. Contact instructor for manual enrollment

**Content not loading:**
1. Check internet connection stability
2. Disable browser extensions temporarily
3. Try a different browser (Chrome/Firefox recommended)
4. Report issue to technical support

#### Lab Environment Problems

**Lab won't start:**
1. Check Docker service status: `docker ps`
2. Verify available system resources
3. Close other resource-intensive applications
4. Restart the lab service: `docker-compose restart lab-containers`

**Code execution errors:**
1. Check syntax errors (highlighted in editor)
2. Verify file names and structure
3. Ensure required dependencies are installed
4. Review error messages carefully
5. Use built-in help and documentation

#### Performance Issues

**Slow loading times:**
1. Check internet connection speed
2. Close unnecessary browser tabs
3. Clear browser cache and cookies
4. Restart browser or device
5. Report persistent issues to administrators

**System responsiveness:**
1. Monitor system resources (CPU, memory)
2. Close resource-intensive applications
3. Restart Docker containers if needed
4. Contact technical support for server-side issues

### Getting Help

#### Built-in Help System

- **Help Documentation**: Accessible from any page via the help icon
- **Tooltips and Hints**: Hover over interface elements for guidance
- **Video Tutorials**: Step-by-step video guides for common tasks
- **FAQ Section**: Answers to frequently asked questions

#### Contact Support

**For Students:**
1. Contact your instructor first for course-related issues
2. Use the built-in help system for technical questions
3. Report bugs through the feedback form
4. Check community forums for common solutions

**For Instructors:**
1. Contact system administrators for technical issues
2. Use instructor forums for best practices and tips
3. Access advanced troubleshooting guides in the instructor documentation
4. Request new features through the feedback system

**For Administrators:**
1. Check system logs for error details
2. Review the technical documentation in `docs/`
3. Contact platform developers for critical issues
4. Participate in administrator community forums

#### Emergency Contacts

**Critical System Issues:**
- Platform completely inaccessible
- Data loss or corruption
- Security concerns
- Major performance problems

**Response Times:**
- **Critical Issues**: 2-4 hours
- **Major Issues**: 24 hours
- **Minor Issues**: 48-72 hours
- **Feature Requests**: Next release cycle

### Self-Help Resources

#### Documentation

- **Complete Runbook**: `docs/RUNBOOK.md`
- **Technical Documentation**: `docs/` directory
- **API Documentation**: Available in the platform
- **Video Tutorials**: Embedded help system

#### Community Resources

- **User Forums**: Share experiences and solutions
- **Best Practices Guides**: Community-contributed guides
- **Template Library**: Shared course templates and materials
- **Plugin Directory**: Community-developed extensions

---

## 🎯 Quick Reference

### Key URLs
- **Platform Home**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3000/admin.html
- **Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html
- **Student Dashboard**: http://localhost:3000/student-dashboard.html
- **Interactive Labs**: http://localhost:3000/lab.html

### Support Commands
```bash
# Check system status
./app-control.sh docker-status

# View logs
./app-control.sh docker-logs [service-name]

# Restart services
./app-control.sh docker-restart

# Create admin user
python create-admin.py
```

### Emergency Procedures
1. **Platform Down**: Run `./app-control.sh docker-restart`
2. **Database Issues**: Check logs with `./app-control.sh docker-logs postgres`
3. **Lab Problems**: Restart with `docker-compose restart lab-containers`
4. **Lost Data**: Contact administrator immediately

---

**Need more help?** Check the complete runbook at `docs/RUNBOOK.md` or create an issue in the project repository.