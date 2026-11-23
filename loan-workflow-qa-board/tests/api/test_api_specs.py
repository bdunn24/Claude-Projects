"""Every test in content/api/*.json, as one pytest case per board ID.

Run one project:   API_PROJECT=SAH pytest tests/api --junitxml=results/api-junit.xml
Run by tag:        pytest tests/api -m smoke
Then load the XML on the board with Load a test run.

Status rule: pass -> Pass, a failed check -> Fail, a missing setting or an
unreachable API -> skip "BLOCKED: <reason>" -> Blocked.
Tests run in file order, so a value one test saves (e.g. caseId) reaches the next.
"""
import os

import pytest

from tools import api_engine as eng

ONLY = os.environ.get("API_PROJECT", "").upper()
PROJECTS = [p for p in eng.load_projects() if not ONLY or p["code"] == ONLY]


def _params():
    for project, suite, test in eng.iter_cases(PROJECTS):
        marks = [getattr(pytest.mark, tag) for tag in test.get("tags", [])]
        yield pytest.param(project, suite, test, id=test["id"], marks=marks)


@pytest.mark.parametrize(("project", "suite", "test"), list(_params()))
def test_api(project, suite, test, api_context):
    ctx = api_context.setdefault(project["code"], {})
    try:
        resp, errors = eng.run_case(project, test, ctx)
    except eng.Blocked as reason:
        pytest.skip(f"BLOCKED: {reason}")
    where = f"{test['method']} {test['path']} -> {resp.status} in {resp.ms:.0f} ms"
    assert not errors, f"{where}: " + "; ".join(errors)
