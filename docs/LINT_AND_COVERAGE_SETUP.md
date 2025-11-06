# Linting and Test Coverage Infrastructure

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Status**: Production Ready

---

## 📋 Overview

This document describes the comprehensive linting and test coverage infrastructure for the Course Creator Platform. The system ensures code quality, consistency, and comprehensive test coverage across all Python microservices and React frontend.

### Key Features

- **Automated Code Quality**: Pre-commit hooks catch issues before they enter the codebase
- **Comprehensive Coverage**: Combined Python and React coverage reports with 70% minimum threshold
- **CI/CD Integration**: Automated testing and coverage reporting in GitHub Actions
- **Visual Dashboards**: HTML reports with service-level breakdown and trend analysis
- **Multiple Output Formats**: HTML, JSON, XML, and terminal reports for flexibility

---

## 🎯 Goals

1. **Maintain Code Quality**: Consistent formatting, linting, and type checking
2. **Track Test Coverage**: Visibility into tested vs. untested code paths
3. **Prevent Regressions**: Automated checks before commits and in CI/CD
4. **Identify Gaps**: Easy identification of areas needing more tests
5. **Trend Analysis**: Track coverage improvements over time

---

## 📁 Files Created

### Configuration Files

1. **`setup.cfg`** - Python linting and testing configuration
   - Flake8 (PEP 8 compliance)
   - MyPy (type checking)
   - Coverage (test coverage tracking)
   - isort (import organization)
   - pytest (test execution)

2. **`.pre-commit-config.yaml`** - Pre-commit hooks
   - Automated code quality checks before commits
   - Formatting (Black, isort)
   - Linting (Flake8, MyPy)
   - Security (Bandit, Safety)
   - File checks (YAML, JSON, trailing whitespace)

3. **`frontend-react/eslint.config.js`** - React ESLint configuration (enhanced)
   - TypeScript strict mode
   - React best practices
   - Security rules (no eval, XSS prevention)
   - Accessibility considerations
   - Import organization

### Scripts

4. **`scripts/generate_coverage_report.sh`** - Coverage report generator
   - Runs Python and React tests with coverage
   - Generates HTML, JSON, and XML reports
   - Enforces coverage thresholds
   - Provides terminal summary

5. **`scripts/combine_coverage.py`** - Combined coverage dashboard
   - Parses Python and React coverage data
   - Generates unified HTML dashboard
   - Calculates overall platform coverage
   - Tracks coverage trends over time

### CI/CD Workflows

6. **`.github/workflows/test-and-coverage.yml`** - Enhanced CI/CD workflow
   - Parallel test execution
   - Coverage reporting to Codecov
   - Security scanning
   - Artifact preservation
   - PR comments with coverage details

---

## 🚀 Quick Start

### 1. Initial Setup

#### Install Pre-commit Hooks

```bash
# Install pre-commit tool
pip install pre-commit

# Install hooks to .git/hooks/
pre-commit install

# (Optional) Run on all files to verify setup
pre-commit run --all-files
```

#### Install Python Dependencies

```bash
# Install all linting and testing tools
pip install -r requirements.txt

# Or install specific tools
pip install black isort flake8 mypy pytest pytest-cov bandit safety
```

#### Install React Dependencies

```bash
cd frontend-react
npm install --legacy-peer-deps
```

### 2. Running Linters

#### Python Linting

```bash
# Format code with Black
black services/ --line-length=120

# Sort imports with isort
isort services/ --profile=black --line-length=120

# Run Flake8 linting
flake8 services/ --config=setup.cfg

# Run MyPy type checking
mypy services/ --config-file=setup.cfg

# Run all linters at once
black services/ && isort services/ && flake8 services/ && mypy services/
```

#### React Linting

```bash
cd frontend-react

# Run ESLint
npm run lint

# Auto-fix linting issues
npm run lint:fix

# Run Prettier formatting check
npm run format:check

# Auto-fix formatting
npm run format

# Run type checking
npm run type-check
```

### 3. Running Tests with Coverage

#### Quick Command (All Tests)

```bash
# Generate all coverage reports (Python + React + Combined)
./scripts/generate_coverage_report.sh
```

#### Python Only

```bash
# Python tests with coverage
pytest --cov=services --cov-report=html:coverage/python --cov-report=term-missing

# Or use the script
./scripts/generate_coverage_report.sh --python
```

#### React Only

```bash
# React tests with coverage
cd frontend-react
npm run test:coverage

# Or use the script
./scripts/generate_coverage_report.sh --react
```

#### Combined Report Only

```bash
# Generate combined dashboard (requires existing coverage data)
./scripts/generate_coverage_report.sh --combined
```

### 4. Viewing Coverage Reports

#### Open in Browser

```bash
# Python coverage
open coverage/python/index.html

# React coverage
open coverage/react/index.html

# Combined dashboard
open coverage/index.html
```

#### Terminal Output

```bash
# View Python coverage summary
pytest --cov=services --cov-report=term-missing

# View React coverage summary
cd frontend-react
npm run test:coverage
```

---

## 📊 Coverage Reports Explained

### Combined Coverage Dashboard

The main dashboard (`coverage/index.html`) provides:

1. **Overall Platform Coverage**: Weighted average across Python and React
2. **Component Breakdown**: Separate metrics for backend and frontend
3. **Visual Progress Bars**: Color-coded coverage percentages
4. **Service-Level Details**: Coverage by microservice
5. **Recommendations**: Actionable items for improvement

### Coverage Metrics

- **Lines**: Percentage of code lines executed during tests
- **Statements**: Percentage of executable statements covered
- **Branches**: Percentage of decision branches (if/else) tested
- **Functions**: Percentage of functions/methods covered

### Coverage Thresholds

| Threshold | Range | Status | Action |
|-----------|-------|--------|--------|
| **High** | ≥90% | 🟢 Excellent | Maintain current coverage |
| **Medium** | 70-89% | 🟡 Acceptable | Improve coverage gradually |
| **Low** | <70% | 🔴 Needs Improvement | Add tests immediately |

---

## 🔧 Configuration Details

### Python Configuration (`setup.cfg`)

#### Flake8

```ini
[flake8]
max-line-length = 120
ignore = E203, W503, E501  # Black compatibility
max-complexity = 15
exclude = .venv, venv, migrations, __pycache__
```

#### MyPy

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Gradually enable
ignore_missing_imports = True
```

#### Coverage

```ini
[coverage:run]
source = services
branch = True
omit = */tests/*, */migrations/*, */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
fail_under = 70
```

#### pytest

```ini
[tool:pytest]
testpaths = tests
addopts =
    -v
    --cov=services
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow-running tests
```

### React Configuration (`eslint.config.js`)

Key rules enforced:

- **TypeScript**: Strict mode, no explicit `any`, consistent type imports
- **React**: Hooks rules, refresh fast refresh
- **Security**: No eval, no script URLs
- **Code Quality**: Prefer const, no var, template literals
- **Best Practices**: Eqeqeq, curly braces, default parameters

### Pre-commit Hooks

Hooks run automatically on `git commit`:

1. **File Checks**: Large files, merge conflicts, syntax validation
2. **Python Formatting**: Black (line length 120)
3. **Import Sorting**: isort (Black profile)
4. **Linting**: Flake8 with plugins
5. **Type Checking**: MyPy
6. **Security**: Bandit, Safety
7. **YAML/Markdown**: Linting and validation
8. **Shell Scripts**: ShellCheck
9. **Docker**: Hadolint

---

## 🤖 CI/CD Integration

### GitHub Actions Workflow

The `test-and-coverage.yml` workflow runs on:
- Push to `main`, `master`, `develop` branches
- Pull requests to these branches
- Manual trigger via workflow_dispatch

### Workflow Jobs

1. **python-tests** (30 min timeout)
   - Runs linters (Black, isort, Flake8, MyPy)
   - Executes unit and integration tests
   - Generates coverage reports
   - Uploads to Codecov
   - Comments on PR with coverage details

2. **react-tests** (20 min timeout)
   - Runs ESLint, type checking, format checking
   - Executes Vitest tests with coverage
   - Uploads to Codecov
   - Preserves artifacts

3. **combined-coverage**
   - Downloads Python and React coverage
   - Generates combined dashboard
   - Creates GitHub Step Summary
   - Uploads combined report artifact

4. **security-scan** (10 min timeout)
   - Runs Bandit (Python security)
   - Runs Safety (dependency vulnerabilities)
   - Uploads security reports

5. **build-summary**
   - Aggregates all job results
   - Creates final status report
   - Posts to GitHub Step Summary

### Artifacts Preserved

- Python coverage reports (30 days)
- React coverage reports (30 days)
- Combined coverage dashboard (90 days)
- Security scan reports (30 days)

---

## 📈 Coverage Trend Tracking

### Historical Data

Coverage trends are tracked in `coverage/coverage-trends.json`:

```json
[
  {
    "timestamp": "2025-11-05T10:30:00",
    "python_coverage": 75.5,
    "react_coverage": 68.2,
    "overall_coverage": 72.8
  }
]
```

### Viewing Trends

1. Check `coverage-trends.json` for historical data
2. Last 30 runs are preserved
3. Use for:
   - Tracking improvements over time
   - Identifying coverage regressions
   - Setting team goals

---

## 🎯 Best Practices

### Writing Tests

1. **Follow TDD**: Write tests before implementing features (Red-Green-Refactor)
2. **Aim for 90%+**: High coverage reduces bugs and maintenance costs
3. **Test Edge Cases**: Don't just test happy paths
4. **Keep Tests Fast**: Unit tests should run in milliseconds
5. **Isolate Tests**: Each test should be independent

### Running Tests Locally

1. **Before Committing**: Always run tests locally
2. **Use Pre-commit**: Let hooks catch issues automatically
3. **Review Coverage**: Check which lines aren't covered
4. **Fix Immediately**: Don't let coverage drop below threshold

### CI/CD Workflow

1. **Monitor Pipeline**: Check GitHub Actions after every push
2. **Fix Failures Fast**: Don't let pipeline stay red
3. **Review Coverage**: Check Codecov reports on PRs
4. **Update Thresholds**: Gradually increase minimum coverage

---

## 🐛 Troubleshooting

### Pre-commit Hooks Failing

**Problem**: Hooks fail on commit
**Solution**:
```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Fix issues and try again
git add .
git commit -m "Your message"

# Or bypass hooks temporarily (not recommended)
git commit --no-verify -m "Your message"
```

### Coverage Below Threshold

**Problem**: Tests fail due to low coverage
**Solution**:
```bash
# Generate coverage report to see missing lines
pytest --cov=services --cov-report=html:coverage/python

# Open HTML report
open coverage/python/index.html

# Write tests for uncovered lines
# Re-run tests
pytest --cov=services
```

### MyPy Type Errors

**Problem**: Type checking fails
**Solution**:
```bash
# Run MyPy to see errors
mypy services/

# Add type hints to fix errors
# Or add # type: ignore comments for external libraries

# Gradually enable strict typing
# Edit setup.cfg: disallow_untyped_defs = True
```

### React Linting Errors

**Problem**: ESLint fails on React code
**Solution**:
```bash
cd frontend-react

# Run ESLint to see errors
npm run lint

# Auto-fix many issues
npm run lint:fix

# For remaining errors, fix manually
# Update eslint.config.js to adjust rules if needed
```

### CI/CD Pipeline Failures

**Problem**: GitHub Actions workflow fails
**Solution**:

1. Check workflow logs in GitHub Actions tab
2. Reproduce locally: `./scripts/generate_coverage_report.sh`
3. Fix issues and push again
4. Check artifacts for detailed reports

---

## 📚 Additional Resources

### Documentation

- [Python Testing Strategy](../claude.md/08-testing-strategy.md)
- [Quality Assurance](../claude.md/09-quality-assurance.md)
- [Troubleshooting Guide](../claude.md/10-troubleshooting.md)
- [Comprehensive E2E Test Plan](../tests/COMPREHENSIVE_E2E_TEST_PLAN.md)

### External Resources

- [pytest documentation](https://docs.pytest.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Black formatter](https://black.readthedocs.io/)
- [Flake8 linter](https://flake8.pycqa.org/)
- [MyPy type checker](https://mypy.readthedocs.io/)
- [ESLint rules](https://eslint.org/docs/rules/)
- [Vitest documentation](https://vitest.dev/)
- [Codecov documentation](https://docs.codecov.com/)

### Tools

- **Python**: pytest, pytest-cov, black, isort, flake8, mypy, bandit, safety
- **React**: vitest, eslint, prettier, typescript
- **CI/CD**: GitHub Actions, Codecov
- **Pre-commit**: pre-commit framework

---

## 🔄 Maintenance

### Regular Tasks

#### Daily
- Monitor CI/CD pipeline status
- Review coverage reports on PRs
- Fix failing tests immediately

#### Weekly
- Review coverage trends
- Update pre-commit hooks: `pre-commit autoupdate`
- Check for security vulnerabilities: `safety check`

#### Monthly
- Update Python dependencies: `pip list --outdated`
- Update React dependencies: `npm outdated`
- Review and adjust coverage thresholds
- Clean up old coverage artifacts

---

## 📞 Support

### Getting Help

1. **Check Documentation**: Review this guide and linked resources
2. **Search Issues**: Check GitHub Issues for similar problems
3. **Ask Team**: Contact development team for assistance
4. **Create Issue**: Open new issue with detailed error information

### Reporting Issues

When reporting issues, include:
- Error messages (full stack traces)
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (Python version, Node version, OS)
- Relevant logs and screenshots

---

## 📝 Changelog

### Version 1.0.0 (2025-11-05)

**Initial Release**

- Created `setup.cfg` with Python linting and testing configuration
- Created `.pre-commit-config.yaml` with comprehensive hooks
- Enhanced `frontend-react/eslint.config.js` with strict rules
- Created `scripts/generate_coverage_report.sh` for automated reporting
- Created `scripts/combine_coverage.py` for unified dashboards
- Created `.github/workflows/test-and-coverage.yml` for CI/CD
- Implemented coverage trend tracking
- Set 70% minimum coverage threshold
- Integrated Codecov for cloud coverage tracking

---

**Last Updated**: 2025-11-05
**Maintained By**: Course Creator Platform Development Team
**Version**: 1.0.0
