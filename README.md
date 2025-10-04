# Course Creator Platform

> **Enterprise-grade learning management system** with AI-powered content generation, isolated lab environments, and comprehensive analytics.

[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen)](https://github.com/yourusername/course-creator)
[![Version](https://img.shields.io/badge/version-3.1.0-blue)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [Platform Status](#platform-status)

---

## Overview

The **Course Creator Platform** is a comprehensive, enterprise-ready learning management system designed for technical education. It combines AI-powered content generation, isolated Docker-based lab environments, and sophisticated analytics to deliver a modern learning experience.

### What Makes It Special

- **🤖 AI-Powered**: Generate complete courses from simple descriptions using Claude AI
- **🔬 Isolated Labs**: Individual Docker containers per student with multi-IDE support
- **📊 Advanced Analytics**: Real-time engagement tracking, proficiency metrics, and predictive insights
- **🏢 Enterprise RBAC**: Multi-tenant organization management with granular permissions
- **🧪 100% Tested**: Comprehensive test coverage with 300+ tests across all services
- **🚀 Production Ready**: Battle-tested with Docker orchestration and CI/CD pipeline

---

## Key Features

### 🎓 For Educators

<details>
<summary><b>AI-Powered Course Creation</b></summary>

- **One-Click Generation**: Create complete courses from a single description
- **Smart Content**: AI generates syllabus, slides, exercises, and quizzes
- **Template Support**: Upload templates for consistent course structure
- **Multi-Format Export**: PowerPoint, PDF, Excel, SCORM, and ZIP

</details>

<details>
<summary><b>Lab Environment Management</b></summary>

- **Individual Containers**: Each student gets isolated Docker environment
- **Multi-IDE Support**: VSCode Server, JupyterLab, IntelliJ IDEA, Terminal
- **Real-Time Monitoring**: Track student lab usage and performance
- **Automatic Lifecycle**: Labs start on login, pause on logout, resume on return
- **Resource Control**: Pause, resume, stop individual or bulk lab sessions

</details>

<details>
<summary><b>Assessment & Analytics</b></summary>

- **Comprehensive Analytics**: Student engagement, proficiency, and progress tracking
- **Predictive Insights**: AI-powered success probability and completion estimates
- **Quiz Management**: Create, publish, and analyze quiz performance
- **Feedback System**: Bi-directional feedback between instructors and students
- **PDF Reports**: Generate detailed performance reports for students and courses

</details>

### 👨‍🎓 For Students

<details>
<summary><b>Interactive Learning Experience</b></summary>

- **Multi-IDE Labs**: Choose VSCode, Jupyter, IntelliJ, or Terminal
- **Seamless Switching**: Change IDEs without losing work
- **Persistent Storage**: All work saved across sessions
- **AI Assistance**: Get help while coding in lab environments
- **Progress Tracking**: Monitor your learning journey with detailed analytics

</details>

<details>
<summary><b>Engagement Tools</b></summary>

- **Interactive Quizzes**: Immediate feedback with detailed explanations
- **Course Feedback**: Rate courses and provide structured feedback
- **Performance Insights**: View your progress compared to class average
- **Personalized Recommendations**: AI-driven learning path suggestions

</details>

### 🏢 For Administrators

<details>
<summary><b>Enterprise Management</b></summary>

- **Multi-Tenant Architecture**: Manage multiple organizations on one platform
- **Advanced RBAC**: Site Admin, Organization Admin, Instructor, Student roles
- **Granular Permissions**: Project-based and track-based access control
- **Teams/Zoom Integration**: Automated meeting room creation and management
- **Comprehensive Audit Logs**: Track all platform activities for compliance

</details>

<details>
<summary><b>Platform Oversight</b></summary>

- **Site Dashboard**: Platform-wide statistics and health monitoring
- **Organization Management**: Create, activate, deactivate organizations
- **User Administration**: Manage users across all organizations
- **Resource Monitoring**: Track platform usage and performance metrics
- **Email Notifications**: Automated notifications for all platform events

</details>

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (20.10+)
- **Git**
- **Anthropic Claude API Key** ([Get one here](https://console.anthropic.com/))

### Installation (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/course-creator.git
cd course-creator

# 2. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start platform
./app-control.sh docker-start

# 4. Create admin user
python create-admin.py
```

### Access Platform

| Interface | URL | Description |
|-----------|-----|-------------|
| **Platform Home** | http://localhost:3000 | Main landing page |
| **Instructor Dashboard** | http://localhost:3000/instructor-dashboard.html | Course creation & management |
| **Student Dashboard** | http://localhost:3000/student-dashboard.html | Learning interface |
| **Org Admin Dashboard** | http://localhost:3000/org-admin-dashboard.html | Organization management |
| **Site Admin Dashboard** | http://localhost:3000/site-admin-dashboard.html | Platform administration |
| **Labs** | http://localhost:3000/lab-multi-ide.html | Multi-IDE lab environment |

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│   │  Instructor  │  │   Student    │  │  Org Admin   │         │
│   │  Dashboard   │  │  Dashboard   │  │  Dashboard   │         │
│   └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│                    (Nginx Reverse Proxy)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Microservices Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     User     │  │   Course     │  │   Content    │          │
│  │  Management  │  │  Generator   │  │  Management  │          │
│  │  (Port 8000) │  │ (Port 8001)  │  │ (Port 8005)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Course     │  │     Lab      │  │  Analytics   │          │
│  │  Management  │  │   Manager    │  │   Service    │          │
│  │ (Port 8004)  │  │ (Port 8006)  │  │ (Port 8007)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │Organization  │  │   Content    │                            │
│  │  Management  │  │   Storage    │                            │
│  │ (Port 8008)  │  │ (Port 8003)  │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │  File        │          │
│  │  Database    │  │    Cache     │  │  Storage     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Lab Container Orchestration Layer                   │
│        (Docker-in-Docker for Student Environments)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Student 1   │  │  Student 2   │  │  Student N   │          │
│  │  Container   │  │  Container   │  │  Container   │          │
│  │  (Multi-IDE) │  │  (Multi-IDE) │  │  (Multi-IDE) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | HTML5, CSS3, JavaScript ES6, Bootstrap 5, xterm.js |
| **Backend** | Python 3.10+, FastAPI, asyncio, Uvicorn |
| **Database** | PostgreSQL 15, asyncpg, Redis |
| **AI** | Anthropic Claude, OpenAI (fallback) |
| **Infrastructure** | Docker, Docker Compose, Nginx |
| **Testing** | pytest, Jest, Selenium, Playwright |
| **CI/CD** | GitHub Actions, pre-commit hooks |

---

## Documentation

### 📚 Core Documentation

| Document | Description |
|----------|-------------|
| **[RUNBOOK.md](RUNBOOK.md)** | Complete operations guide with installation, deployment, and troubleshooting |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Detailed system architecture, design patterns, and data flows |
| **[API Documentation](docs/api.md)** | Complete API reference for all services |
| **[CLAUDE.md](CLAUDE.md)** | Developer guide with coding standards and conventions |
| **[CHANGELOG.md](CHANGELOG.md)** | Version history and release notes |

### 🎯 Quick Reference

| Topic | Document |
|-------|----------|
| Installation & Setup | [RUNBOOK.md § Installation](RUNBOOK.md#installation) |
| Running Tests | [RUNBOOK.md § Testing](RUNBOOK.md#testing) |
| Deployment Guide | [RUNBOOK.md § Deployment](RUNBOOK.md#deployment) |
| Troubleshooting | [RUNBOOK.md § Troubleshooting](RUNBOOK.md#troubleshooting) |
| System Design | [ARCHITECTURE.md § Design](ARCHITECTURE.md#design) |
| API Endpoints | [docs/api.md](docs/api.md) |

---

## Platform Status

### ✅ Version 3.1.0 - Current Release (2025-10-04)

<details>
<summary><b>🔧 Modular Architecture & Code Quality</b></summary>

- **Modular Frontend**: Refactored org admin dashboard into 8 ES6 modules
- **Custom Exceptions**: Comprehensive exception system across all services
- **100% Syntax Validation**: 3,149 files validated with automated checker
- **112+ Tests**: Comprehensive instructor dashboard test suite
- **Code Quality Tools**: `check_syntax.py`, `cleanup_codebase.sh`

</details>

<details>
<summary><b>📋 Enhanced Track Management</b></summary>

- **Full CRUD Operations**: Create, read, update, delete learning tracks
- **Track Analytics**: Enrollment metrics and completion tracking
- **Duplication**: Clone tracks with configuration options
- **Publishing**: Publish/unpublish track workflows
- **Auto-Enrollment**: Automated student enrollment based on criteria

</details>

<details>
<summary><b>🏗️ Project Management</b></summary>

- **Student Enrollment**: Enroll/unenroll students from projects
- **Instructor Management**: Assign/remove instructors from tracks
- **Project Publishing**: Control project visibility and access
- **Track Association**: Link tracks to projects

</details>

<details>
<summary><b>👥 Site Admin Dashboard</b></summary>

- **Platform Statistics**: Real-time metrics across organizations
- **Organization Management**: Activate, deactivate, delete organizations
- **User Administration**: Cross-organization user management
- **Health Monitoring**: System health and resource tracking

</details>

<details>
<summary><b>📊 Advanced Analytics</b></summary>

- **Engagement Scores**: Student engagement level calculations
- **Lab Proficiency**: Code quality and independence metrics
- **Success Prediction**: AI-powered completion probability
- **Risk Assessment**: Identify at-risk students
- **PDF Reports**: Comprehensive student and course reports
- **Performance Comparison**: Student vs. class average analytics

</details>

### 🎯 Previous Versions

<details>
<summary><b>Version 3.0 - Password Management & Enhanced UI</b></summary>

- Self-service password changes with JWT authentication
- Automatic admin account creation during org registration
- Professional email validation (business-only)
- Real-time form validation with error messages

</details>

<details>
<summary><b>Version 2.3 - Enhanced RBAC System</b></summary>

- Multi-tenant organization management
- JWT authentication & authorization
- Teams/Zoom meeting room integration
- Comprehensive audit logging
- 102 RBAC tests with 100% success rate

</details>

<details>
<summary><b>Version 2.2 - Quiz Management System</b></summary>

- Course instance-specific quiz publishing
- Student access control with enrollment validation
- Attempt tracking and progress monitoring

</details>

<details>
<summary><b>Version 2.1 - Bi-Directional Feedback & Multi-IDE</b></summary>

- Complete feedback system (students ↔ instructors)
- Multi-IDE support (VSCode, Jupyter, IntelliJ, Terminal)
- Seamless IDE switching without data loss

</details>

### 📈 Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests | 150+ | ✅ Passing |
| Integration Tests | 80+ | ✅ Passing |
| E2E Tests | 50+ | ✅ Passing |
| Frontend Tests | 40+ | ✅ Passing |
| **Total** | **320+** | **✅ 100%** |

### 🔐 Security & Compliance

- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Input validation & sanitization
- ✅ SQL injection prevention
- ✅ Container isolation & sandboxing
- ✅ Comprehensive audit logging
- ✅ HTTPS enforcement (production)
- ✅ CORS configuration
- ✅ Rate limiting

---

## Getting Help

### 📖 Resources

- **Documentation**: Start with [RUNBOOK.md](RUNBOOK.md)
- **API Reference**: See [docs/api.md](docs/api.md)
- **Troubleshooting**: Check [RUNBOOK.md § Troubleshooting](RUNBOOK.md#troubleshooting)
- **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md)

### 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/course-creator/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/course-creator/discussions)
- **Security Issues**: Email security@yourcompany.com

### 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:

- Code of Conduct
- Development workflow
- Testing requirements
- Pull request process

---

## Quick Commands

```bash
# Start platform
./app-control.sh docker-start

# Check service status
./app-control.sh status

# View logs
./app-control.sh logs <service-name>

# Stop platform
./app-control.sh docker-stop

# Run tests
pytest tests/

# Validate syntax
python check_syntax.py

# Clean codebase
./cleanup_codebase.sh
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Anthropic Claude** - AI-powered content generation
- **FastAPI** - Modern web framework
- **Docker** - Containerization platform
- **PostgreSQL** - Reliable database system

---

<div align="center">

**[⬆ Back to Top](#course-creator-platform)**

Made with ❤️ by the Course Creator Team

</div>
