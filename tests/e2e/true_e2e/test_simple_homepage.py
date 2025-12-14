"""Simple homepage test with ReactWaitHelpers."""
import pytest
import time
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers
from selenium.webdriver.common.by import By


@pytest.mark.true_e2e
@pytest.mark.guest_journey
def test_simple_homepage(true_e2e_driver, selenium_config):
    """Test homepage loads successfully with React wait helpers."""
    true_e2e_driver.get(selenium_config.base_url)
    time.sleep(1)  # Brief wait for initial render

    # Use ReactWaitHelpers to wait for loading to complete
    waits = ReactWaitHelpers(true_e2e_driver)
    waits.wait_for_loading_complete(timeout=10)

    # Verify page content
    page_text = true_e2e_driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'course' in page_text or 'login' in page_text
