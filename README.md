# Claude Projects

Brit Dunn's projects built with the value engineering method. One folder per
application; each carries its own record and its own gate (`check.sh`).

| Project | What it is | State |
|---|---|---|
| [loan-workflow-qa-board](loan-workflow-qa-board/) | Loan workflow stages with Pass, Fail and Blocked test cases, fed by Selenium JUnit XML | v2, sample data |

## Setup after cloning
```bash
git config core.hooksPath .githooks
```
The pre-commit hook runs every project's `check.sh`; a red gate stops the commit.
