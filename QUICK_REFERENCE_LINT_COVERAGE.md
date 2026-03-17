# Linting & Coverage Quick Reference

**Quick commands for daily development tasks**

---

## 🚀 Quick Start (First Time)

```bash
# Install pre-commit hooks (one time)
pip install pre-commit
pre-commit install

# Install Python tools
pip install -r requirements.txt

# Install React tools
cd frontend-react && npm install --legacy-peer-deps
```

---

## 🎯 Common Commands

### Run All Tests with Coverage

```bash
# Generate everything (Python + React + Combined)
./scripts/generate_coverage_report.sh

# Open combined dashboard
open coverage/index.html
```

### Python Linting

```bash
# Auto-fix formatting and imports
black services/ && isort services/

# Check linting and types
flake8 services/ && mypy services/
```

### React Linting

```bash
cd frontend-react

# Auto-fix everything possible
npm run lint:fix && npm run format

# Check everything
npm run lint && npm run type-check
```

### Pre-commit Hooks

```bash
# Run manually on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

---

## 📊 Coverage Thresholds

- 🟢 **Excellent**: ≥90%
- 🟡 **Acceptable**: 70-89%
- 🔴 **Needs Improvement**: <70%

---

## 📁 Key Files

### Configuration
- `setup.cfg` - Python linting/testing config
- `.pre-commit-config.yaml` - Pre-commit hooks
- `frontend-react/eslint.config.js` - React ESLint rules

### Scripts
- `scripts/generate_coverage_report.sh` - Generate all coverage reports
- `scripts/combine_coverage.py` - Combine Python + React coverage

### Reports
- `coverage/index.html` - Combined dashboard
- `coverage/python/index.html` - Python coverage
- `coverage/react/index.html` - React coverage

### Documentation
- `docs/LINT_AND_COVERAGE_SETUP.md` - Full documentation

---

## 🔧 Troubleshooting

### Pre-commit fails
```bash
# See what's wrong
pre-commit run --all-files

# Bypass temporarily (not recommended)
git commit --no-verify
```

### Coverage too low
```bash
# See uncovered lines
pytest --cov=services --cov-report=html:coverage/python
open coverage/python/index.html
# Write tests for red lines
```

### Type errors
```bash
# See MyPy errors
mypy services/

# Add type hints or ignore
# Add: # type: ignore
```

---

## 📚 More Info

See full documentation: `docs/LINT_AND_COVERAGE_SETUP.md`
