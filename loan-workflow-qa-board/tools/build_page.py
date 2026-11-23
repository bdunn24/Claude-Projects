"""Builds app/loan-workflow.html from the template, content/loan-workflow.json
and the API specs in content/api/. The content files are the one source;
never edit the built page by hand."""
import json
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent


def embed(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<" + chr(92) + "/")


data = json.loads((root / "content/loan-workflow.json").read_text(encoding="utf-8"))
api_files = sorted((root / "content/api").glob("*.json"))
api = {
    "projects": [
        json.loads(p.read_text(encoding="utf-8"))
        for p in api_files if not p.name.startswith("_")
    ],
    "template": json.loads((root / "content/api/_template.json").read_text(encoding="utf-8")),
}
tpl = (root / "app/loan-workflow.template.html").read_text(encoding="utf-8")
for mark in ("__WORKFLOW_JSON__", "__API_JSON__"):
    assert mark in tpl, f"template placeholder {mark} missing"
page = tpl.replace("__WORKFLOW_JSON__", embed(data)).replace("__API_JSON__", embed(api))
(root / "app/loan-workflow.html").write_text(page, encoding="utf-8")
n = sum(len(s["tests"]) for s in data["stages"])
n_api = sum(len(s["tests"]) for p in api["projects"] for s in p["suites"])
print(
    f"built app/loan-workflow.html: {len(data['stages'])} stages, "
    f"{n} test cases, {len(api['projects'])} API projects with {n_api} API tests, "
    f"as of {data['asOf']}"
)
