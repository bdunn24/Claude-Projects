"""Builds app/loan-workflow.html from the template and content/loan-workflow.json.
The JSON is the one source; never edit the built page by hand."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root / "content/loan-workflow.json").read_text(encoding="utf-8"))
blob = json.dumps(data, ensure_ascii=False).replace("</", "<" + chr(92) + "/")
tpl = (root / "app/loan-workflow.template.html").read_text(encoding="utf-8")
assert "__WORKFLOW_JSON__" in tpl, "template placeholder missing"
(root / "app/loan-workflow.html").write_text(tpl.replace("__WORKFLOW_JSON__", blob), encoding="utf-8")
n = sum(len(s["tests"]) for s in data["stages"])
print(f"built app/loan-workflow.html: {len(data['stages'])} stages, {n} test cases, as of {data['asOf']}")
