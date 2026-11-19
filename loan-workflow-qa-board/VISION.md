# Vision

**As of 2026-11-18.** Draft by Claude from Brit Dunn's words in the session. Brit owns this page: rewrite it in your own words, and log each change in docs/methodology.md.

## The user
A QA automation engineer who runs Selenium suites against a loan origination workflow and needs one view of where each loan stage stands.

## The one flow
1. Open the board and see every stage of a loan, from application to funding.
2. See each stage's test cases marked Pass, Fail, Blocked or Not run.
3. Load the results of a Selenium run (JUnit XML) and watch the board update.
4. Open a red or amber stage, read which test failed or what blocks it, and decide the next step.

## What done looks like
- One page shows the whole workflow and its test status at a glance.
- Each test case on the board carries the ID of its Selenium test, so a run maps onto the board with no manual typing.
- A person can still mark a case by hand when automation does not cover it.
- The board uses sample data only. No borrower data, loan numbers or client systems.

## Set aside for now
- A live connection to a CI server.
- Shared results across viewers.
- Real loan systems or real loan data.
