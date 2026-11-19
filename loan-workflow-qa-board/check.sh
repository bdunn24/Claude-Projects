#!/usr/bin/env sh
# The gate. Run before every commit. It refuses (exit 1); it does not warn.
# Rows follow the value engineering standard (textbook Part 9; see assets/SOURCES.md).
cd "$(dirname "$0")" || exit 1
fail=0
no() { echo "NO    $1"; fail=1; }
ok() { echo "ok    $1"; }

# 1. The record exists
for f in README.md VISION.md CLAUDE.md assets/SOURCES.md docs/facts.md docs/methodology.md docs/standard.md \
         docs/banned-words.txt tasks/lessons.md tasks/todo.md; do
  [ -f "$f" ] || no "missing $f"
done
for d in assets history content; do [ -d "$d" ] || no "missing $d/"; done
for s in .claude/skills/*/; do
  [ -d "$s" ] && [ ! -f "${s}SKILL.md" ] && no "missing ${s}SKILL.md"
done

# 2. The scripts parse
for s in $(find . -name '*.sh' -not -path './.git/*'); do
  sh -n "$s" 2>/dev/null || no "$s does not parse"
done

# 3. The vision is written and dated
if grep -qx 'TODO' VISION.md 2>/dev/null; then no "VISION.md not written yet"
elif ! grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2}' VISION.md; then no "VISION.md has no date"
else ok "vision written and dated"; fi

# 4. The plan has a NEXT block; the method log is dated
grep -q '^## NEXT' tasks/todo.md 2>/dev/null && ok "NEXT block" || no "tasks/todo.md has no '## NEXT' block"
grep -qE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/methodology.md 2>/dev/null \
  && ok "method log dated" || no "docs/methodology.md has no dated entry"

# 5. Words, confidentiality: see the Python block
python - <<'PY' || fail=1
import os, re, sys
fail = False
def no(m):
    global fail; fail = True; print("NO    " + m)

# Outward words: content/, README, VISION, facts
words = ["README.md", "VISION.md", "docs/facts.md"]
for root, _, files in os.walk("content"):
    words += [os.path.join(root, f) for f in files if f.endswith((".md", ".json", ".html"))]
words = [p for p in words if os.path.isfile(p)]

banned = [l.strip().lower() for l in open("docs/banned-words.txt", encoding="utf-8")
          if l.strip() and not l.startswith("#")]
absolutes = re.compile(r"\b(always|never|guarantee[ds]?|ensures?|warrant(y|ies|s|ed)?|certainly|"
                       r"impossible|completely|fully|zero risk)\b|100%", re.I)
passive = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ly\s+)?\w+(ed|en)\b", re.I)

sentences = passives = 0
for p in words:
    for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        if line.lstrip().startswith("<!--"): continue
        low = line.lower()
        for w in banned:
            if re.search(r"\b" + re.escape(w) + r"\b", low): no(f"{p}:{n} banned word '{w}'")
        if absolutes.search(line) and "absolute-ok" not in line:
            no(f"{p}:{n} absolute '{absolutes.search(line).group(0)}' (mark <!-- absolute-ok: why --> if meant)")
        for s in re.split(r"[.!?]\s", line):
            if len(s.split()) >= 4:
                sentences += 1
                passives += bool(passive.search(s))
if sentences:
    pct = 100 * passives / sentences
    (no if pct >= 2 else lambda m: print("ok    " + m))(f"passive voice {pct:.1f}% of {sentences} sentences (limit 2%)")

# Confidential data (org policy): everything but assets/ and .git
pats = {
    "SSN-like number": r"\b\d{3}-\d{2}-\d{4}\b",
    "email address": r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
    "IPv4 address": r"\b(?!127\.0\.0\.1\b)(?!0\.0\.0\.0\b)\d{1,3}(\.\d{1,3}){3}\b",
    "AWS key": r"\bAKIA[0-9A-Z]{16}\b",
    "API key": r"\b(sk|pk|rk)-[A-Za-z0-9_-]{20,}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "password assignment": r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{4,}",
}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "assets", "node_modules", ".venv")]
    for f in files:
        p = os.path.join(root, f)
        if f == "check.sh" or os.path.getsize(p) > 2_000_000: continue
        try: text = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError): continue
        for name, rx in pats.items():
            m = re.search(rx, text)
            if m:
                n = text.count("\n", 0, m.start()) + 1
                no(f"{p}:{n} possible {name}; remove it (no client-confidential data)")
if not fail: print("ok    words and confidentiality")
sys.exit(1 if fail else 0)
PY

# 6. The count of turns
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "info  turns: $(git rev-list --count HEAD -- . 2>/dev/null || echo 0) commits touching this project"
else echo "info  no git repository yet; turns not counted"; fi

[ $fail -eq 0 ] && echo "GATE  pass" || echo "GATE  refused"
exit $fail
