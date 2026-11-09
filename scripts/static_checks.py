#!/usr/bin/env python3
"""Static gate checks for PayPilot AI ACCESS.

Run from the repo root:  python scripts/static_checks.py
Exit code 0 = every check passed. Exit code 1 = at least one FAIL.
Uses only the standard library. Does not call any network service.
Do not edit this script to make a failing check pass; fix the code instead.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "tests/fixtures"}
TEXT_EXT = {".py", ".js", ".html", ".css", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".example"}

results = []  # (status, name, detail)


def add(status, name, detail=""):
    results.append((status, name, detail))


def files(exts=None, under=None):
    base = ROOT / under if under else ROOT
    if not base.exists():
        return
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(rel == d or rel.startswith(d + "/") or ("/" + d + "/") in ("/" + rel) for d in SKIP_DIRS):
            continue
        if p.name == ".env":
            yield p
            continue
        if exts is None or p.suffix in exts or p.name.endswith(".example"):
            yield p


def lines(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def scan(name, pattern, paths, flags=0, allow=None, status="FAIL"):
    rx = re.compile(pattern, flags)
    hits = []
    for p in paths:
        for i, line in enumerate(lines(p), 1):
            if rx.search(line) and not (allow and re.search(allow, line)):
                hits.append(f"{p.relative_to(ROOT).as_posix()}:{i}: {line.strip()[:110]}")
    if hits:
        add(status, name, "\n      ".join(hits[:15]))
    else:
        add("PASS", name)


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return out.returncode, out.stdout
    except Exception:
        return 1, ""


# 1. Required files
required = ["README.md", "LICENSE", ".gitignore", ".env.example", "requirements.txt", "render.yaml",
            "AGENTS.md", "SPEC.md", "docs/PROGRESS.md"]
missing = [f for f in required if not (ROOT / f).exists()]
add("FAIL" if missing else "PASS", "required files exist", ", ".join(missing))

# 2. .gitignore covers secrets and local DB
gi = (ROOT / ".gitignore").read_text(errors="ignore") if (ROOT / ".gitignore").exists() else ""
gi_missing = [t for t in (".env", "*.db") if t not in gi]
add("FAIL" if gi_missing else "PASS", ".gitignore covers .env and *.db", ", ".join(gi_missing))

# 3. .env is not tracked by git (only when a git repo exists)
if (ROOT / ".git").exists():
    code, out = git("ls-files")
    tracked = [t for t in out.splitlines() if t == ".env" or t.endswith("/.env") or t.endswith(".db")]
    add("FAIL" if tracked else "PASS", ".env and *.db not tracked by git", ", ".join(tracked))
else:
    add("WARN", ".env not tracked by git", "no git repo found; run git init")

# 4. Secret-looking strings in working tree
secret_rx = (r"AIza[0-9A-Za-z_\-]{30,}|ch3_live_[A-Za-z0-9]{8,}|ch3_[A-Za-z0-9]{20,}|"
             r"(client_secret|api[_-]?key|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{24,}['\"]|"
             r"E[A-Za-z0-9_\-]{70,}")
scan("no secret-looking strings in tracked-style files (local .env is checked separately)", secret_rx, (f for f in files(TEXT_EXT) if f.name != ".env"), allow=r"your[_-]|placeholder|example|changeme|xxxx")

# 5. Secret-looking strings in git history (added lines)
if (ROOT / ".git").exists():
    code, out = git("log", "-p", "--all", "--no-color")
    bad = []
    rx = re.compile(secret_rx)
    for line in out.splitlines():
        if line.startswith("+") and not line.startswith("+++") and rx.search(line):
            if not re.search(r"your[_-]|placeholder|example|changeme|xxxx", line, re.I):
                bad.append(line[:110])
    add("FAIL" if bad else "PASS", "no secret-looking strings in git history", "\n      ".join(bad[:10]))

# 6. Unsafe DOM writes in the frontend
fe = list(files({".js", ".html"}, "static"))
scan("no innerHTML / insertAdjacentHTML / document.write in static/", r"innerHTML|insertAdjacentHTML|document\.write\(", fe, allow=r"safe-static")

# 7. No hard-coded Gemini model names or latest aliases in app code
scan("no hard-coded Gemini model IDs in app/", r"['\"]gemini-[\w.\-]+['\"]", files({".py"}, "app"))

# 8. No production PayPal endpoint literal; no disabled TLS verification
scan("no production PayPal host literal", r"api-m\.paypal\.com|api\.paypal\.com", files({".py", ".js", ".html", ".yaml", ".yml"}), allow=r"sandbox")
scan("no disabled TLS verification", r"verify\s*=\s*False", files({".py"}))

# 9. Client must not send money fields to order/capture endpoints (heuristic)
scan("frontend does not send price/amount/total in order or capture calls",
     r"(api/orders|/capture)[^\n]{0,200}(price|amount|total)\s*:", fe, status="WARN")

# 10. Keys must not be printed or logged
scan("no printing or logging of key variables", r"(print|logging\.\w+|logger\.\w+)\([^)]*(api_key|secret|client_secret|token)", files({".py"}, "app"), flags=re.I, allow=r"debug_id")

# 11. Seeded sample data must not be wired into the live path (heuristic)
scan("seeded catalogue not imported outside tests or offline flag", r"from\s+(app\.)?catalog\s+import|import\s+(app\.)?catalog", files({".py"}, "app"), allow=r"OFFLINE_TESTS", status="WARN")

# 12. Dependency allow-list (anything else needs a line in docs/DECISIONS.md)
allowed = {"fastapi", "uvicorn", "httpx", "pydantic", "pydantic-settings", "google-genai", "pytest", "respx",
           "python-dotenv", "starlette", "pydantic-core", "annotated-types", "anyio", "h11", "httpcore", "certifi",
           "idna", "sniffio", "typing-extensions", "click", "iniconfig", "packaging", "pluggy", "google-auth",
           "requests", "urllib3", "charset-normalizer", "tenacity", "websockets", "pyasn1", "pyasn1-modules",
           "rsa", "cachetools", "annotated-doc", "typing-inspection", "distro", "pytest-cov", "coverage",
           "python-multipart", "jinja2", "markupsafe", "ruff", "httptools", "uvloop", "watchfiles", "pyyaml"}
req = ROOT / "requirements.txt"
decisions = (ROOT / "docs/DECISIONS.md").read_text(errors="ignore").lower() if (ROOT / "docs/DECISIONS.md").exists() else ""
extra = []
if req.exists():
    for line in lines(req):
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[=<>!~\[; ]", line)[0].lower().replace("_", "-")
        if name and name not in allowed and name not in decisions:
            extra.append(name)
add("FAIL" if extra else "PASS", "dependencies are allowed or justified in docs/DECISIONS.md", ", ".join(extra))
banned = [n for n in extra if re.search(r"langchain|autogen|pinecone|redis|psycopg|sqlalchemy|react|next", n)]
if banned:
    add("FAIL", "banned dependencies present", ", ".join(banned))

# 13. README has required sections
readme = (ROOT / "README.md").read_text(errors="ignore").lower() if (ROOT / "README.md").exists() else ""
need = ["limitations", "live", "mock", "tools", "license"]
miss = [n for n in need if n not in readme]
if "what changed" not in readme and "development timeline" not in readme:
    miss.append("development timeline (or 'what changed')")
add("FAIL" if miss else "PASS", "README has required sections", ", ".join(miss))

# 14. Sandbox honesty text present in the frontend
fe_text = " ".join(" ".join(lines(p)) for p in fe).lower()
add("PASS" if "sandbox" in fe_text else "FAIL", "frontend shows Sandbox wording")

# 15. Evidence files exist for the Definition of Done
for f in ("docs/FINAL_VERIFICATION.md", "docs/LIVE_TEST_REPORT.md", "docs/ACCESSIBILITY_TEST.md"):
    add("PASS" if (ROOT / f).exists() else "WARN", f"evidence file {f} exists")

# Report
width = max(len(n) for _, n, _ in results)
fails = warns = 0
for status, name, detail in results:
    print(f"[{status:4}] {name.ljust(width)}" + (f"\n      {detail}" if detail and status != "PASS" else ""))
    fails += status == "FAIL"
    warns += status == "WARN"
print(f"\n{len(results)} checks: {len(results) - fails - warns} pass, {warns} warn, {fails} fail")
sys.exit(1 if fails else 0)
