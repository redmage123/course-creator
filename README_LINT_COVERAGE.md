# Linting & Coverage Infrastructure - Quick Links

## 🎯 What is This?

Comprehensive linting and test coverage infrastructure for the Course Creator Platform, ensuring code quality and comprehensive testing across all Python microservices and React frontend.

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[Full Documentation](docs/LINT_AND_COVERAGE_SETUP.md)** | Complete setup guide, configuration details, troubleshooting | Developers (first time) |
| **[Quick Reference](QUICK_REFERENCE_LINT_COVERAGE.md)** | Common commands and daily usage | Developers (daily use) |
| **[Implementation Summary](LINT_COVERAGE_IMPLEMENTATION_SUMMARY.md)** | File listing, features, verification steps | DevOps, Team Leads |

## 🚀 Quick Start

```bash
# 1. Install pre-commit hooks
pip install pre-commit && pre-commit install

# 2. Install dependencies
pip install -r requirements.txt
cd frontend-react && npm install --legacy-peer-deps

# 3. Generate coverage reports
./scripts/generate_coverage_report.sh

# 4. View combined dashboard
open coverage/index.html
```

## 🛠️ Key Tools

### Python
- **Flake8**: PEP 8 linting
- **Black**: Auto-formatting (120 chars)
- **isort**: Import sorting
- **MyPy**: Type checking
- **pytest**: Testing with coverage
- **Bandit**: Security scanning

### React
- **ESLint**: Comprehensive linting
- **TypeScript**: Type checking
- **Vitest**: Unit testing
- **Prettier**: Code formatting

### Automation
- **Pre-commit Hooks**: Run before commits
- **GitHub Actions**: CI/CD with coverage
- **Codecov**: Cloud coverage tracking

## 📊 Coverage Thresholds

- 🟢 **Excellent**: ≥90%
- 🟡 **Acceptable**: 70-89%
- 🔴 **Needs Improvement**: <70%

**Current Minimum**: 70%

## 🔗 Related Documentation

- [Testing Strategy](claude.md/08-testing-strategy.md)
- [Quality Assurance](claude.md/09-quality-assurance.md)
- [E2E Test Plan](tests/COMPREHENSIVE_E2E_TEST_PLAN.md)

## 📞 Support

For questions or issues, see [Full Documentation](docs/LINT_AND_COVERAGE_SETUP.md) or contact the development team.

---

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: 2025-11-05
