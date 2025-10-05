# Course Creator Platform - Documentation Index

**Last Updated**: 2025-10-05

## 📚 Quick Start

- **[README.md](README.md)** - Platform overview and getting started
- **[RUNBOOK.md](RUNBOOK.md)** - Operational procedures and troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design

## 🤖 AI Assistant Documentation

- **[CLAUDE.md](CLAUDE.md)** - Main documentation for Claude Code AI assistant
  - [Critical Requirements](claude.md/01-critical-requirements.md)
  - [Documentation Standards](claude.md/02-documentation-standards.md)
  - [Memory System](claude.md/03-memory-system.md)
  - [Version History](claude.md/04-version-history.md)
  - [Architecture Overview](claude.md/05-architecture.md)
  - [Key Systems](claude.md/06-key-systems.md)
  - [Development Commands](claude.md/07-development-commands.md)
  - [Testing Strategy](claude.md/08-testing-strategy.md)
  - [Quality Assurance](claude.md/09-quality-assurance.md)
  - [Troubleshooting](claude.md/10-troubleshooting.md)

## 🧪 Testing Documentation

Located in `docs/testing/`:

- **[TEST_INTEGRATION_SUMMARY.md](docs/testing/TEST_INTEGRATION_SUMMARY.md)** - Complete test integration status (96.7% success)
- **[HOW_TO_RUN_TESTS.md](docs/testing/HOW_TO_RUN_TESTS.md)** - Guide to running test suites
- **[TESTING_GUIDE.md](docs/testing/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[INSTRUCTOR_DASHBOARD_TEST_SUMMARY.md](docs/testing/INSTRUCTOR_DASHBOARD_TEST_SUMMARY.md)** - Dashboard test results

### Test Statistics

- **Tests Integrated**: 1,450 tests (96.7% of all test files)
- **Test Categories**: Unit, Integration, E2E, Performance, Security
- **Test Markers**: See pytest.ini for complete list

## 🚀 Deployment Documentation

Located in `docs/deployment/`:

- **[DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)** - Main deployment guide
- **[SIMPLE_DEPLOYMENT_GUIDE.md](docs/deployment/SIMPLE_DEPLOYMENT_GUIDE.md)** - Quick deployment steps
- **[PRODUCTION_DEPLOYMENT_README.md](docs/deployment/PRODUCTION_DEPLOYMENT_README.md)** - Production checklist
- **[DEPLOY_SCRIPT_FIXES.md](docs/deployment/DEPLOY_SCRIPT_FIXES.md)** - Deployment script fixes

## ✨ Feature Documentation

Located in `docs/features/`:

### Fuzzy Search System
- **[FUZZY_LOGIC_DEPLOYMENT_SUCCESS.md](docs/features/FUZZY_LOGIC_DEPLOYMENT_SUCCESS.md)** - Complete fuzzy search implementation
- **[FUZZY_LOGIC_IMPLEMENTATION_COMPLETE.md](docs/features/FUZZY_LOGIC_IMPLEMENTATION_COMPLETE.md)** - Implementation details
- **[SELENIUM_FUZZY_SEARCH_SUCCESS.md](docs/features/SELENIUM_FUZZY_SEARCH_SUCCESS.md)** - E2E test success

### Knowledge Graph
- **[KNOWLEDGE_GRAPH_COMPLETE.md](docs/features/KNOWLEDGE_GRAPH_COMPLETE.md)** - Knowledge graph implementation
- **[KNOWLEDGE_GRAPH_COMPLETE_SUMMARY.md](docs/features/KNOWLEDGE_GRAPH_COMPLETE_SUMMARY.md)** - Implementation summary

### Other Features
- **[COURSE_VIDEO_FEATURE.md](docs/features/COURSE_VIDEO_FEATURE.md)** - Video upload and linking
- **[ACCESSIBILITY_IMPLEMENTATION_SUMMARY.md](docs/features/ACCESSIBILITY_IMPLEMENTATION_SUMMARY.md)** - Accessibility features
- **[RAG_ENHANCEMENTS_IMPLEMENTATION.md](docs/features/RAG_ENHANCEMENTS_IMPLEMENTATION.md)** - RAG system enhancements
- **[OWASP_SECURITY_ASSESSMENT_SUMMARY.md](docs/features/OWASP_SECURITY_ASSESSMENT_SUMMARY.md)** - Security assessment

## 📖 Additional Documentation

Located in `docs/`:

- **[api.md](docs/api.md)** - API documentation
- **[architecture.md](docs/architecture.md)** - Detailed architecture
- **[deployment.md](docs/deployment.md)** - Deployment procedures
- **[RUNBOOK.md](docs/RUNBOOK.md)** - Operations runbook
- **[USER-GUIDE.md](docs/USER-GUIDE.md)** - User documentation
- **[FEEDBACK_SYSTEM_GUIDE.md](docs/FEEDBACK_SYSTEM_GUIDE.md)** - Feedback system
- **[QUIZ_MANAGEMENT_GUIDE.md](docs/QUIZ_MANAGEMENT_GUIDE.md)** - Quiz management
- **[EMAIL_CONFIGURATION.md](docs/EMAIL_CONFIGURATION.md)** - Email setup
- **[WEBHOOK_SETUP.md](docs/WEBHOOK_SETUP.md)** - Webhook configuration

## 📦 Archived Documentation

Located in `docs/archive/`:

Historical documentation preserved for reference:
- Fuzzy logic implementation progress docs
- Knowledge graph development docs
- Metadata service TDD progress
- Refactoring summaries
- Validation reports

## 🔍 Quick Reference

### Running Tests
```bash
# All tests
pytest

# By category
pytest -m unit
pytest -m integration
pytest -m e2e

# Specific test file
pytest tests/unit/analytics/test_analytics_dao.py
```

### Starting Services
```bash
./scripts/app-control.sh start
./scripts/app-control.sh status
```

### Deployment
```bash
./scripts/deploy.sh
```

---

## 📝 Documentation Standards

All documentation follows these standards:
1. Clear, concise titles
2. Table of contents for longer docs
3. Code examples where applicable
4. Business context and technical rationale
5. Last updated dates

For contributing to documentation, see [Documentation Standards](claude.md/02-documentation-standards.md).
