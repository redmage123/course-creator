#!/usr/bin/env python3
import sys
print("STEP 1: Script started", flush=True)

import time
import os
print("STEP 2: Basic imports done", flush=True)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
print("STEP 3: Selenium imports done", flush=True)

print("STEP 4: Setting up Chrome options", flush=True)
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")
print("STEP 5: Chrome options configured", flush=True)

chromedriver_path = "/home/bbrelin/.wdm/drivers/chromedriver/linux64/141.0.7390.76/chromedriver-linux64/chromedriver"
print(f"STEP 6: Using chromedriver: {chromedriver_path}", flush=True)

service = Service(chromedriver_path)
print("STEP 7: Service created", flush=True)

print("STEP 8: About to create Chrome driver...", flush=True)
driver = webdriver.Chrome(service=service, options=options)
print("STEP 9: Driver created!", flush=True)

driver.quit()
print("✅ Test complete!", flush=True)
