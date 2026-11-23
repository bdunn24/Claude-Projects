"""Offline checks of tools/api_engine.py. No network: a fake transport answers.

Run: pytest tests/unit
"""
import datetime
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import api_engine as eng  # noqa: E402

ENV = {"X_BASE": "https://api.example.test/v1", "X_CRED": "sample-credential"}
PROJECT = {
    "project": "Sample", "code": "XYZ", "baseUrlEnv": "X_BASE",
    "auth": {"type": "bearer", "env": "X_CRED"},
    "defaultHeaders": {"Accept": "application/json"},
    "variables": {"program": "SAH"}, "suites": [],
}


class FakeTransport:
    def __init__(self, status=200, body=None, ms=5.0, headers=None):
        self.status, self.body, self.ms, self.headers = status, body, ms, headers or {}
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        text = json.dumps(self.body) if self.body is not None else ""
        return eng.Response(self.status, self.headers, text, self.ms)


def test_substitute_keeps_type_and_fills_strings():
    ctx = {"n": 5, "id": "C-1"}
    assert eng.substitute("{{n}}", ctx) == 5
    assert eng.substitute("/cases/{{id}}/x", ctx) == "/cases/C-1/x"
    assert eng.substitute({"a": ["{{id}}"]}, ctx) == {"a": ["C-1"]}


def test_missing_variable_blocks():
    with pytest.raises(eng.Blocked, match="caseId"):
        eng.substitute("/cases/{{caseId}}", {})


def test_builtins():
    today = datetime.date(2026, 11, 23)
    assert eng.builtin("$daysAgo:75", today=today) == "2026-09-09"
    assert eng.builtin("$daysAhead:7", today=today) == "2026-11-30"
    assert len(eng.builtin("$rand")) == 8
    with pytest.raises(eng.Blocked):
        eng.builtin("$env:NOPE_NOT_SET", env={})


def test_get_path():
    data = {"errors": [{"field": "program"}], "a": {"b": 1}}
    assert eng.get_path(data, "errors.0.field") == "program"
    assert eng.get_path(data, "$.a.b") == 1
    assert eng.get_path(data, "errors.3.field") is eng.MISSING


@pytest.mark.parametrize(("rule", "ok"), [
    ({"path": "amount", "approx": 490.2}, True),
    ({"path": "amount", "approx": 490.3}, False),
    ({"path": "amount", "type": "number"}, True),
    ({"path": "flag", "type": "number"}, False),
    ({"path": "flag", "equals": True}, True),
    ({"path": "max", "equalsPath": "amount"}, True),
    ({"path": "status", "oneOf": ["Active", "Inactive"]}, True),
    ({"path": "status", "matches": "^Act"}, True),
    ({"path": "tags", "contains": "a"}, True),
    ({"path": "nope", "exists": False}, True),
    ({"path": "nope", "exists": True}, False),
    ({"path": "amount", "gte": "text"}, False),
])
def test_check_json(rule, ok):
    body = {"amount": 490.2, "max": 490.2, "flag": True, "status": "Active", "tags": ["a"]}
    assert (eng.check_json(body, rule, {}) is None) == ok


def test_run_case_sends_auth_saves_and_passes():
    fake = FakeTransport(201, {"id": "C-9", "status": "Active", "program": "SAH"})
    test = {
        "id": "XYZ-API-CASE-001", "method": "post", "path": "/cases",
        "body": {"program": "{{program}}"},
        "expect": {"status": 201, "json": [{"path": "program", "equals": "{{program}}"}]},
        "save": {"caseId": "id"},
    }
    ctx = {}
    _, errors = eng.run_case(PROJECT, test, ctx, transport=fake, env=ENV)
    assert errors == []
    assert ctx == {"caseId": "C-9"}
    call = fake.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "https://api.example.test/v1/cases"
    assert call["headers"]["Authorization"] == "Bearer sample-credential"
    assert call["body"] == {"program": "SAH"}


def test_run_case_reports_each_failed_check():
    fake = FakeTransport(500, {"status": "Broken"}, ms=3000)
    test = {"method": "GET", "path": "/health", "auth": "none",
            "expect": {"status": 200, "maxMs": 2000, "json": [{"path": "status", "equals": "ok"}]}}
    _, errors = eng.run_case(PROJECT, test, {}, transport=fake, env=ENV)
    assert len(errors) == 3
    assert "Authorization" not in fake.calls[0]["headers"]


def test_run_case_blocks_without_settings():
    test = {"method": "GET", "path": "/x", "expect": {"status": 200}}
    with pytest.raises(eng.Blocked, match="X_BASE"):
        eng.run_case(PROJECT, test, {}, transport=FakeTransport(), env={})
    with pytest.raises(eng.Blocked, match="X_CRED"):
        eng.run_case(PROJECT, test, {}, transport=FakeTransport(), env={"X_BASE": "http://h"})


def test_query_and_body_not_matches():
    fake = FakeTransport(200, {"text": "Hello, your case number ends 4321"})
    test = {"method": "GET", "path": "/n", "query": {"recipient": "veteran"},
            "expect": {"status": 200, "bodyNotMatches": [r"\b\d{3}-\d{2}-\d{4}\b"]}}
    _, errors = eng.run_case(PROJECT, test, {}, transport=fake, env=ENV)
    assert errors == []
    assert fake.calls[0]["url"].endswith("/n?recipient=veteran")


def test_validator_catches_bad_specs():
    bad = {**PROJECT, "suites": [{"id": "CASE", "name": "Case", "tests": [
        {"id": "XYZ-API-CASE-001", "title": "t", "method": "FETCH", "path": "cases",
         "expect": {}},
        {"id": "XYZ-API-CASE-001", "title": "t", "method": "GET", "path": "/c/{{caseId}}",
         "expect": {"status": 200, "json": [{"path": "a", "bogus": 1}]}},
    ]}]}
    errs = " | ".join(eng.validate_project(bad))
    for part in ("unknown method", "start with /", "needs a status", "duplicate ID",
                 "unknown json check", "before any test saves it"):
        assert part in errs


def test_every_shipped_spec_validates():
    for p in sorted(eng.SPEC_DIR.glob("*.json")):
        assert eng.validate_project(json.loads(p.read_text(encoding="utf-8")), p.name) == []
