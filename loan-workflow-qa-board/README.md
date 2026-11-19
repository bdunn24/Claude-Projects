# Loan Workflow QA Board

One page that shows a loan's nine workflow stages and their test cases as
Pass, Fail, Blocked or Not run, and updates from a Selenium JUnit XML run.

**State (2026-11-19):** in bdunn24/Claude-Projects; board v2 in the PhoenixTeam house style, on sample data. Selenium tests are a skeleton with placeholder locators.

## Use
```bash
python tools/build_page.py                                  # build the board from content/
pytest tests/selenium --junitxml=results/junit.xml          # run Selenium (needs LOAN_APP_URL)
./check.sh                                                  # the gate
```
Open `app/loan-workflow.html`, then load `results/junit.xml` with **Load a test run**.

## Setup
```bash
pip install -r requirements.txt
git config core.hooksPath .githooks   # run from the repository root
```
