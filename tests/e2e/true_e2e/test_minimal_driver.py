"""Minimal test using true_e2e_driver fixture."""
import pytest

@pytest.mark.true_e2e
def test_driver_works(true_e2e_driver, selenium_config):
    """Test that driver works."""
    true_e2e_driver.get(selenium_config.base_url)
    assert "Course Creator" in true_e2e_driver.title
