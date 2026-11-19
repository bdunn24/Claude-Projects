# CLAUDE.md

The Loan Workflow QA Board: one page that shows a loan's workflow stages and
their test cases as Pass, Fail, Blocked or Not run, fed by Selenium JUnit XML.
Built with the value engineering method. Rules set by Brit Dunn, 2026-11-19,
unless an entry says otherwise.

## Vocabulary
- **Stage**: one step of the loan workflow, with a code (APP, DSC, CRD, APR, UW, COND, CTC, CLS, FND).
- **Board ID**: `LW-<STAGE>-<NNN>`, one per test case. A Selenium test name starts `test_<board ID with underscores>_`.
- **Status**: Pass, Fail, Blocked, Not run. JUnit `<failure>`/`<error>` maps to Fail, `<skipped>` to Blocked, anything else to Pass.
- **Waits on**: a stage after the first failed or blocked stage.
- **The record**: `docs/methodology.md`, `docs/facts.md`, `tasks/lessons.md`, `tasks/todo.md`, `history/`.

## Method
- `content/loan-workflow.json` is the one source for stages and test cases. Change it, then run `python tools/build_page.py`. Never edit `app/loan-workflow.html` by hand.
- Each published version gets a snapshot in `history/` named `v<N>-<date>.html`.
- Every correction goes in `docs/methodology.md`, newest first: who asked, what was wrong, the rule, what changed. Its rule goes in this file.
- The gate `./check.sh` runs before every commit through the root `.githooks/pre-commit`. It refuses; it does not warn.
- Close every session with the NEXT block in `tasks/todo.md`, lessons, the README state line and a method-log entry. Then push.

## Style
- Visual style comes from `.claude/skills/brand/SKILL.md`.
- Plain words, active voice, short sentences. Dates as YYYY-MM-DD.

## Handling
- Sample data only. No borrower data, loan numbers, client systems or credentials. The gate scans for them.
- The value engineering textbook stays out of this repository (see assets/SOURCES.md).
- Credentials for the app under test come from environment variables, never from files.
