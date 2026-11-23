"""Shared setup for the API specs. Each project names its base URL and
credential environment variables in content/api/<project>.json."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import api_engine  # noqa: E402


def pytest_configure(config):
    """Register every spec tag as a marker, so `-m smoke` selects smoke tests."""
    tags = set()
    for _, _, test in api_engine.iter_cases(api_engine.load_projects()):
        tags.update(test.get("tags", []))
    for tag in sorted(tags):
        config.addinivalue_line("markers", f"{tag}: API spec tag")


@pytest.fixture(scope="session")
def api_context():
    """Values saved by earlier tests (e.g. caseId), one dict per project."""
    return {}
