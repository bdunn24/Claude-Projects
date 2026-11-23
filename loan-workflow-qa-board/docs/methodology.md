# Methodology

Method log, newest entry first.

## 2026-11-23: board v4, API automation and a searchable navigation
- Asked by: Brit Dunn, as an automation test engineer, for the SAH/SHA project restart on new infrastructure.
- What: API tests live as data, one JSON file per project in content/api/. tools/api_engine.py runs them with the standard library: variables, saved values between tests, JSON checks, timing, PII patterns. tests/api turns each spec test into a pytest case named by its ID; a missing setting or an unreachable API skips as Blocked. The board gains an API tests view with a builder that starts from any test, and the navigation folds by section and searches everything.
- Source: the SAHSHA Builder reference holds the process, statuses, rules and grant plans, but no API. The 33 SAH/SHA tests check those rules against placeholder endpoints until the new build publishes its API.
- Rule: content/api/<project>.json is the one source for API tests; the gate validates every spec and runs the runner's unit tests.
- Measured: 22 unit tests pass; 33 of 33 API tests pass against a throwaway mock API; a wrong credential fails and a down API blocks; 27 scripted browser checks pass.

## 2026-11-23: board v3, left navigation and loan created tests
- Asked by: Brit Dunn.
- What: a left navigation rail lists two views and the nine stages. The new Loan created tests view drafts test cases for a new loan: stage, next free board ID, title, loan setup, expected result and a Selenium test name built from the ID. Drafts stay in the browser; Copy drafts as JSON groups them by stage for content/loan-workflow.json.
- Rule: content/loan-workflow.json stays the one source. Drafts reach the board only through that file and tools/build_page.py.
- Guard: the draft form refuses text that looks like an SSN, an email or a long account number, per organization policy.
- Also: ruff lint fixes in tools/build_page.py and tests/selenium/conftest.py.

## 2026-11-19: into Claude-Projects on GitHub
- Asked by: Brit Dunn.
- What: the board moved into the private repository bdunn24/Claude-Projects as its own folder, with its record and gate. Brit chose one repository for all projects; each project keeps its own folder, record and check.sh, and the root pre-commit hook runs every gate. The textbook stays out as confidential IP.

## 2026-11-18: board rethemed to the PhoenixTeam house style
- Asked by: Brit Dunn.
- What was wrong: the board used a palette and type of Claude's choosing.
- Root cause: no brand kit; the textbook prints none.
- Rule: brand tokens live in .claude/skills/brand/SKILL.md, measured from the textbook PDF. Orange stays out of status colors.
- What changed: board v2 with a navy masthead, orange rule, Sofia Pro stack with Figtree as stand-in, a footer stamp, equal-height stage cards.

## 2026-11-18: board v1
- Asked by: Brit Dunn, as a QA automation engineer.
- What: VISION.md drafted by Claude from Brit's words, marked for Brit to rewrite. content/loan-workflow.json holds 9 stages and 21 sample test cases; tools/build_page.py builds the page. Results load from JUnit XML.
- Decision: sample data only, per organization policy on loan-level data. Results stay in the viewer's browser.
