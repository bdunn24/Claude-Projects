"""Runs the API test specs in content/api/*.json against a live API.

One JSON file per project. Each file names the environment variables that hold
the base URL and the credential, so no URL or secret lives in the repository.
A spec test is data: method, path, body, expectations and values to save for
later tests. tests/api/test_api_specs.py turns every spec test into a pytest
case named by its board ID, so JUnit results load straight onto the board.

    python tools/api_engine.py --validate    # check every spec file (the gate runs this)
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "content" / "api"
VAR_RX = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
ID_RX = re.compile(r"^[A-Z]{2,6}-API-[A-Z]{2,6}-\d{3}$")
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
TYPES = {
    "string": str, "number": (int, float), "integer": int, "boolean": bool,
    "array": list, "object": dict, "null": type(None),
}
CHECKS = {
    "equals", "notEquals", "equalsPath", "approx", "gte", "lte", "type",
    "contains", "oneOf", "matches", "exists",
}
MISSING = object()


class Blocked(Exception):
    """The test cannot run: a setting is missing or an earlier test left no value."""


@dataclass
class Response:
    status: int
    headers: dict = field(default_factory=dict)
    text: str = ""
    ms: float = 0.0

    def json(self):
        try:
            return json.loads(self.text) if self.text else None
        except json.JSONDecodeError:
            return MISSING


# --- Loading ---------------------------------------------------------------

def load_projects(spec_dir: Path = SPEC_DIR) -> list[dict]:
    """Every project spec, skipping files that start with _ (the template)."""
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(spec_dir.glob("*.json"))
        if not p.name.startswith("_")
    ]


def iter_cases(projects):
    for project in projects:
        for suite in project["suites"]:
            for test in suite["tests"]:
                yield project, suite, test


# --- Variables -------------------------------------------------------------

def builtin(name: str, env=os.environ, today: datetime.date | None = None):
    """Built-ins: $uuid, $rand, $today, $daysAgo:N, $daysAhead:N, $env:NAME."""
    today = today or datetime.date.today()
    if name == "$uuid":
        return str(uuid.uuid4())
    if name == "$rand":
        return uuid.uuid4().hex[:8].upper()
    if name == "$today":
        return today.isoformat()
    m = re.fullmatch(r"\$days(Ago|Ahead):(\d+)", name)
    if m:
        delta = datetime.timedelta(days=int(m[2]))
        return (today - delta if m[1] == "Ago" else today + delta).isoformat()
    if name.startswith("$env:"):
        value = env.get(name[5:])
        if value is None:
            raise Blocked(f"environment variable {name[5:]} not set")
        return value
    raise ValueError(f"unknown built-in {name}")


def resolve(name: str, ctx: dict, env=os.environ) -> Any:
    if name.startswith("$"):
        return builtin(name, env)
    if name not in ctx:
        raise Blocked(f"needs '{name}' from an earlier test")
    return ctx[name]


def substitute(value: Any, ctx: dict, env=os.environ) -> Any:
    """Fill {{name}} placeholders. A string that is one placeholder keeps the value's type."""
    if isinstance(value, str):
        whole = VAR_RX.fullmatch(value)
        if whole:
            return resolve(whole[1], ctx, env)
        return VAR_RX.sub(lambda m: str(resolve(m[1], ctx, env)), value)
    if isinstance(value, list):
        return [substitute(v, ctx, env) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, ctx, env) for k, v in value.items()}
    return value


# --- Checks ----------------------------------------------------------------

def get_path(data: Any, path: str) -> Any:
    """Dot path into JSON: 'id', 'errors.0.field', '$.items.2.status'."""
    path = path.removeprefix("$").lstrip(".")
    cur = data
    for part in filter(None, path.split(".")):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return MISSING
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


def _is_type(actual, name: str) -> bool:
    if name in ("number", "integer") and isinstance(actual, bool):
        return False
    return isinstance(actual, TYPES[name])


def check_json(body, rule: dict, ctx: dict) -> str | None:
    """One JSON rule. Returns an error message, or None when it holds."""
    path = rule["path"]
    actual = get_path(body, path)
    if "exists" in rule:
        if (actual is not MISSING) != bool(rule["exists"]):
            return f"{path}: expected {'present' if rule['exists'] else 'absent'}"
        if len(rule) == 2:
            return None
    if actual is MISSING:
        return f"{path}: missing from the response"
    for op, expected in rule.items():
        if op in ("path", "exists"):
            continue
        expected = substitute(expected, ctx)
        try:
            if op == "equals":
                ok = actual == expected
            elif op == "notEquals":
                ok = actual != expected
            elif op == "equalsPath":
                other = get_path(body, expected)
                ok = other is not MISSING and actual == other
            elif op == "approx":
                ok = _is_type(actual, "number") and abs(actual - expected) <= 0.005
            elif op == "gte":
                ok = actual >= expected
            elif op == "lte":
                ok = actual <= expected
            elif op == "type":
                ok = _is_type(actual, expected)
            elif op == "contains":
                ok = expected in actual
            elif op == "oneOf":
                ok = actual in expected
            elif op == "matches":
                ok = isinstance(actual, str) and re.search(expected, actual) is not None
            else:
                return f"{path}: unknown check '{op}'"
        except TypeError:
            ok = False
        if not ok:
            return f"{path}: expected {op} {expected!r}, got {actual!r}"
    return None


def check_response(resp: Response, expect: dict, ctx: dict) -> list[str]:
    errors = []
    want = expect.get("status")
    if want is not None:
        allowed = want if isinstance(want, list) else [want]
        if resp.status not in allowed:
            errors.append(f"status: expected {want}, got {resp.status}")
    if "maxMs" in expect and resp.ms > expect["maxMs"]:
        errors.append(f"time: expected under {expect['maxMs']} ms, took {resp.ms:.0f} ms")
    for name, part in expect.get("headers", {}).items():
        got = resp.headers.get(name.lower(), "")
        if str(part).lower() not in got.lower():
            errors.append(f"header {name}: expected to contain {part!r}, got {got!r}")
    for text in expect.get("bodyContains", []):
        if substitute(text, ctx) not in resp.text:
            errors.append(f"body: expected to contain {text!r}")
    for rx in expect.get("bodyNotMatches", []):
        if re.search(rx, resp.text):
            errors.append(f"body: matched forbidden pattern {rx!r}")
    rules = expect.get("json", [])
    if rules:
        body = resp.json()
        if body is MISSING:
            errors.append("body: expected JSON")
        else:
            errors += [e for e in (check_json(body, r, ctx) for r in rules) if e]
    return errors


# --- Running ---------------------------------------------------------------

def send(method: str, url: str, headers: dict, body, timeout: float) -> Response:
    """The default transport: the standard library, no extra packages."""
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, raw, hdrs = r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        status, raw, hdrs = e.code, e.read(), e.headers
    except (urllib.error.URLError, TimeoutError) as e:
        raise Blocked(f"cannot reach the API: {getattr(e, 'reason', e)}") from e
    ms = (time.perf_counter() - start) * 1000
    return Response(status, {k.lower(): v for k, v in hdrs.items()}, raw.decode("utf-8", "replace"), ms)


def auth_headers(project: dict, test: dict, env) -> dict:
    auth = test.get("auth", project.get("auth", "none"))
    if auth == "none" or auth.get("type") == "none":
        return {}
    credential = env.get(auth["env"])
    if not credential:
        raise Blocked(f"{auth['env']} not set")
    if auth["type"] == "bearer":
        return {"Authorization": f"Bearer {credential}"}
    if auth["type"] == "header":
        return {auth["name"]: credential}
    raise ValueError(f"unknown auth type {auth['type']}")


def run_case(project: dict, test: dict, ctx: dict, transport=send, env=os.environ):
    """Run one spec test. Saves values into ctx for later tests. Returns (response, errors)."""
    base = env.get(project["baseUrlEnv"])
    if not base:
        raise Blocked(f"{project['baseUrlEnv']} not set")
    values = {**project.get("variables", {}), **ctx}
    headers = {**project.get("defaultHeaders", {}), **test.get("headers", {})}
    headers = {**substitute(headers, values, env), **auth_headers(project, test, env)}
    url = base.rstrip("/") + substitute(test["path"], values, env)
    if test.get("query"):
        url += "?" + urllib.parse.urlencode(substitute(test["query"], values, env))
    body = substitute(test["body"], values, env) if "body" in test else None
    resp = transport(test["method"].upper(), url, headers, body, project.get("timeoutSeconds", 30))
    errors = check_response(resp, test.get("expect", {}), values)
    data = resp.json()
    for name, path in test.get("save", {}).items():
        value = get_path(data, path) if data is not MISSING else MISSING
        if value is not MISSING:
            ctx[name] = value
    return resp, errors


# --- Validation (the gate) -------------------------------------------------

def validate_project(project: dict, source: str = "spec") -> list[str]:
    errs = []
    for key in ("project", "code", "baseUrlEnv", "suites"):
        if key not in project:
            errs.append(f"{source}: missing '{key}'")
    if errs:
        return errs
    code = project["code"]
    seen = set()
    saved = set(project.get("variables", {}))
    for suite in project["suites"]:
        for key in ("id", "name", "tests"):
            if key not in suite:
                errs.append(f"{source}: suite missing '{key}'")
        for t in suite.get("tests", []):
            tid = t.get("id", "(no id)")
            where = f"{source}: {tid}"
            if not ID_RX.match(tid):
                errs.append(f"{where}: ID must look like {code}-API-{suite.get('id', 'SUITE')}-001")
            elif not tid.startswith(f"{code}-API-{suite.get('id')}-"):
                errs.append(f"{where}: ID must start {code}-API-{suite.get('id')}-")
            if tid in seen:
                errs.append(f"{where}: duplicate ID")
            seen.add(tid)
            for key in ("title", "method", "path", "expect"):
                if key not in t:
                    errs.append(f"{where}: missing '{key}'")
            if t.get("method", "").upper() not in METHODS:
                errs.append(f"{where}: unknown method {t.get('method')!r}")
            if not str(t.get("path", "/")).startswith("/"):
                errs.append(f"{where}: path must start with /")
            if "status" not in t.get("expect", {}):
                errs.append(f"{where}: expect needs a status")
            for rule in t.get("expect", {}).get("json", []):
                if "path" not in rule:
                    errs.append(f"{where}: a json check needs a path")
                bad = set(rule) - CHECKS - {"path"}
                if bad:
                    errs.append(f"{where}: unknown json check {sorted(bad)}")
            text = json.dumps({k: t.get(k) for k in ("path", "body", "query", "headers")})
            for name in VAR_RX.findall(text):
                if not name.startswith("$") and name not in saved:
                    errs.append(f"{where}: uses {{{{{name}}}}} before any test saves it")
            saved.update(t.get("save", {}))
    return errs


def main(argv: list[str]) -> int:
    if "--validate" not in argv:
        print(__doc__)
        return 0
    errs, n = [], 0
    files = sorted(SPEC_DIR.glob("*.json"))
    for p in files:
        try:
            project = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errs.append(f"{p.name}: not valid JSON ({e})")
            continue
        errs += validate_project(project, p.name)
        n += sum(len(s.get("tests", [])) for s in project.get("suites", []))
    for e in errs:
        print("NO    " + e)
    if not errs:
        print(f"ok    API specs: {len(files)} files, {n} tests valid")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
