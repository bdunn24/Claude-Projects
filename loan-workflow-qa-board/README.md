# Loan Workflow QA Board

One page that shows a loan's nine workflow stages and their test cases as
Pass, Fail, Blocked or Not run, and updates from a Selenium JUnit XML run.

**State (2026-11-23):** board v4. The left navigation folds by section and searches every test, suite and stage. An API tests view shows the API specs in `content/api/`, builds new API tests from any example, and loads API JUnit results. The first project, SAH/SHA grants, holds 33 sample API tests on placeholder endpoints. Selenium tests are a skeleton with placeholder locators.

## Use
```bash
python tools/build_page.py                                  # build the board from content/
pytest tests/selenium --junitxml=results/junit.xml          # run Selenium (needs LOAN_APP_URL)
./check.sh                                                  # the gate
```

### API tests
```powershell
$env:SAH_API_BASE_URL = "https://<host>/<base path>"     # the API under test
$env:SAH_API_BEARER   = "<credential>"                    # from your vault, not a file
$env:API_PROJECT = "SAH"; python -m pytest tests/api --junitxml=results/api-junit.xml
python -m pytest tests/api -m smoke                        # by tag
python tools/api_engine.py --validate                      # check the specs
python -m pytest tests/unit                                # the runner's offline tests
```
One JSON file per project in `content/api/`. Copy `content/api/_template.json` to start a new project. Load `results/api-junit.xml` on the API tests view. A missing setting or an unreachable API shows as Blocked.
Open `app/loan-workflow.html`, then load `results/junit.xml` with **Load a test run**.

## Setup
```bash
pip install -r requirements.txt
git config core.hooksPath .githooks   # run from the repository root
```
