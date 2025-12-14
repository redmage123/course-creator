"""Simple homepage test - no ReactWaitHelpers."""
import pytest
from selenium.webdriver.common.by import By

@pytest.mark.true_e2e
def test_homepage_basic(true_e2e_driver, selenium_config):
    """Test homepage loads."""
    true_e2e_driver.get(selenium_config.base_url)
    import time
    time.sleep(3)  # Simple wait instead of ReactWaitHelpers
    page_text = true_e2e_driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'course' in page_text or 'login' in page_text
