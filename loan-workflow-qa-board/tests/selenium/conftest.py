"""Shared Selenium setup. Set LOAN_APP_URL to the loan application under test.
Credentials come from environment variables, never from this file."""
import os

import pytest
from selenium import webdriver


@pytest.fixture
def base_url():
    url = os.environ.get("LOAN_APP_URL")
    if not url:
        pytest.skip("BLOCKED: LOAN_APP_URL not set")
    return url.rstrip("/")


@pytest.fixture
def driver():
    opts = webdriver.ChromeOptions()
    if os.environ.get("HEADLESS", "1") == "1":
        opts.add_argument("--headless=new")
    drv = webdriver.Chrome(options=opts)
    drv.implicitly_wait(0)
    yield drv
    drv.quit()
