"""
Pytest configuration for dashboard tests with visual regression support

BUSINESS PURPOSE:
- Provides pytest fixtures for visual regression testing
- Handles --update-baselines command-line flag
- Configures visual regression behavior across all dashboard tests

USAGE:
    pytest tests/e2e/dashboards/ --update-baselines  # Update all baselines
    pytest tests/e2e/dashboards/                     # Normal test run with visual comparison
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def pytest_addoption(parser):
    """
    Add custom pytest command-line options

    WHY THIS IS NEEDED:
    Allows developers to update visual regression baselines via command line
    without modifying test code or configuration files.
    """
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Update visual regression baseline images instead of comparing"
    )
    parser.addoption(
        "--visual-threshold",
        action="store",
        default=None,
        type=float,
        help="Override default visual regression threshold (0.0-1.0)"
    )


@pytest.fixture(scope="session")
def update_baselines(request):
    """
    Session-scoped fixture for baseline update mode

    BUSINESS RULE:
    When --update-baselines flag is set, all visual regression tests
    will save new baselines instead of comparing to existing ones.
    """
    return request.config.getoption("--update-baselines")


@pytest.fixture(scope="session")
def visual_threshold(request):
    """
    Session-scoped fixture for custom visual threshold

    ALLOWS:
    Temporary threshold adjustments for specific test runs
    without changing code: pytest --visual-threshold=0.05
    """
    custom_threshold = request.config.getoption("--visual-threshold")
    if custom_threshold is not None:
        return custom_threshold
    return 0.02  # Default 2%


@pytest.fixture
def visual_regression_path():
    """
    Fixture providing path to visual regression directory

    WHY FIXTURE:
    Centralizes path management. Tests don't need to know
    the directory structure for visual regression files.
    """
    return Path(__file__).parent / "visual_regression"


def pytest_configure(config):
    """
    Configure pytest session

    BUSINESS PURPOSE:
    - Adds custom markers for visual regression tests
    - Sets up environment variables
    - Validates configuration
    """
    config.addinivalue_line(
        "markers",
        "visual: mark test as using visual regression testing"
    )

    # Set environment variable for VisualRegressionConfig
    if config.getoption("--update-baselines"):
        os.environ["UPDATE_BASELINES"] = "true"


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on configuration

    BUSINESS PURPOSE:
    Automatically skip visual regression tests in CI if needed,
    or run only visual tests when requested.
    """
    skip_visual = pytest.mark.skip(reason="Visual regression disabled in this environment")

    # Check if visual regression should be skipped
    disable_visual = os.environ.get("DISABLE_VISUAL_REGRESSION", "false").lower() == "true"

    if disable_visual:
        for item in items:
            if "visual" in item.keywords:
                item.add_marker(skip_visual)
