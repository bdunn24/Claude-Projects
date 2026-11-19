"""Selenium tests for the loan workflow, mapped to the QA board by ID.

Naming rule: every test name starts test_<BOARD ID with underscores>_, e.g.
test_LW_CRD_002_dti_recalculates maps to LW-CRD-002 on the board.
Status rule: pass -> Pass, assertion or error -> Fail,
pytest.skip("BLOCKED: <reason>") -> Blocked.

Run:  pytest tests/selenium --junitxml=results/junit.xml
Then load results/junit.xml on the board.

The locators below are placeholders. Replace them with your application's.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

WAIT = 10


def wait_for(driver, locator):
    return WebDriverWait(driver, WAIT).until(EC.visibility_of_element_located(locator))


# --- Application intake --------------------------------------------------

def test_LW_APP_001_submit_complete_application(driver, base_url):
    driver.get(f"{base_url}/application/new")
    wait_for(driver, (By.ID, "first-name")).send_keys("Sample")
    driver.find_element(By.ID, "last-name").send_keys("Borrower")
    driver.find_element(By.ID, "loan-amount").send_keys("250000")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    assert "Application received" in wait_for(driver, (By.CSS_SELECTOR, ".toast")).text


def test_LW_APP_002_required_field_errors(driver, base_url):
    driver.get(f"{base_url}/application/new")
    wait_for(driver, (By.CSS_SELECTOR, "button[type=submit]")).click()
    errors = driver.find_elements(By.CSS_SELECTOR, ".field-error")
    assert len(errors) >= 3, f"expected required-field errors, got {len(errors)}"


# --- Credit and income ---------------------------------------------------

def test_LW_CRD_002_dti_recalculates(driver, base_url):
    driver.get(f"{base_url}/loans/sample/income")
    income = wait_for(driver, (By.ID, "monthly-income"))
    income.clear()
    income.send_keys("10000")
    driver.find_element(By.ID, "recalculate").click()
    dti = wait_for(driver, (By.ID, "dti-value")).text
    assert dti == "36.0%", f"Expected DTI 36.0%, page shows {dti} after income edit"


# --- Appraisal: an example of a Blocked case ----------------------------

def test_LW_APR_001_order_appraisal(driver, base_url):
    pytest.skip("BLOCKED: appraisal vendor sandbox unavailable")


# Add the remaining board IDs the same way: one test per ID in
# content/loan-workflow.json, using the "selenium" name listed there.
