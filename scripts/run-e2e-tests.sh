#!/usr/bin/env bash
set -euo pipefail

# run-e2e-tests.sh — Run Playwright E2E tests and produce a structured failure report.
# Usage: BASE_URL=http://localhost:3000 scripts/run-e2e-tests.sh
# Outputs: test-results/FAILURES.md on failure
# Exits: 0 if all tests pass, 1 if any fail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/test-results"
FAILURES_FILE="${RESULTS_DIR}/FAILURES.md"
WEB_DIR="${REPO_ROOT}/apps/web"
BASE_URL="${BASE_URL:-http://localhost:3000}"
PW_JSON="${RESULTS_DIR}/_playwright_results.json"

# Ensure test-results/ exists
mkdir -p "${RESULTS_DIR}"

# Resolve Python interpreter (needed for the parser)
PYTHON="${PYTHON:-python3}"
if ! command -v "${PYTHON}" &>/dev/null; then
  PYTHON="python"
fi
if ! command -v "${PYTHON}" &>/dev/null; then
  echo "ERROR: python / python3 not found on PATH (needed for failure parser)." >&2
  exit 1
fi

# Check that npx is available
if ! command -v npx &>/dev/null; then
  echo "ERROR: npx not found on PATH. Install Node.js / pnpm." >&2
  exit 1
fi

echo "Running E2E tests (Playwright) against ${BASE_URL}…"

set +e
(cd "${WEB_DIR}" && \
  BASE_URL="${BASE_URL}" npx playwright test --reporter=json 2>&1) \
  > "${PW_JSON}"
PW_EXIT="${PIPESTATUS[0]}"
set -e

if [[ "${PW_EXIT}" -eq 0 ]]; then
  echo "All E2E tests passed."
  rm -f "${PW_JSON}"
  TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  {
    printf "## Failed Tests — %s\n\n" "${TIMESTAMP}"
    printf "| Test | File | Assertion | Requirements | Status |\n"
    printf "|------|------|-----------|--------------|--------|\n"
    printf "\n_All E2E tests passed._\n"
  } > "${FAILURES_FILE}"
  exit 0
fi

echo ""
echo "Some E2E tests failed. Writing ${FAILURES_FILE}…"

PARSER_SCRIPT="${RESULTS_DIR}/_parse_e2e_failures.py"

cat > "${PARSER_SCRIPT}" << 'PYEOF'
import json
import re
import sys
import os
import datetime

results_dir   = os.environ["RESULTS_DIR"]
web_dir       = os.environ["WEB_DIR"]
pw_json_path  = os.path.join(results_dir, "_playwright_results.json")
failures_file = os.path.join(results_dir, "FAILURES.md")

if not os.path.isfile(pw_json_path):
    print("ERROR: Playwright JSON output not found.", file=sys.stderr)
    sys.exit(1)

with open(pw_json_path) as fh:
    raw = fh.read().strip()

# Playwright --reporter=json may prefix output with non-JSON lines (e.g. console warnings).
# Find first '{' to locate the JSON payload.
json_start = raw.find("{")
if json_start == -1:
    print("ERROR: No JSON object found in Playwright output.", file=sys.stderr)
    print("Raw output (first 500 chars):", raw[:500], file=sys.stderr)
    sys.exit(1)

data = json.loads(raw[json_start:])


def get_spec_markers(test_file_abs: str) -> str:
    """Return comma-separated // @spec: REQ-ID comments from a test file."""
    if not os.path.isfile(test_file_abs):
        return "-"
    with open(test_file_abs) as fh:
        src = fh.read()
    req_ids = re.findall(r"//\s*@spec:\s*([A-Z0-9\-]+)", src)
    unique_ids = list(dict.fromkeys(req_ids))  # dedupe, preserve order
    return ", ".join(unique_ids) if unique_ids else "-"


def md(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


rows = []

def walk_suites(suites: list) -> None:
    for suite in suites:
        # Recurse into nested suites
        if suite.get("suites"):
            walk_suites(suite["suites"])
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    if result.get("status") not in ("failed", "timedOut"):
                        continue
                    # File path and line
                    file_path = suite.get("file", spec.get("file", ""))
                    line_no   = spec.get("line", "")
                    file_col  = f"{file_path}:{line_no}" if line_no else file_path

                    # Test title
                    title = spec.get("title", test.get("title", "unknown"))

                    # Assertion / error message
                    errors = result.get("errors", [])
                    assertion = ""
                    if errors:
                        msg = errors[0].get("message", "")
                        # Strip ANSI codes
                        assertion = re.sub(r"\x1b\[[0-9;]*m", "", msg).split("\n")[0]

                    # Spec markers
                    abs_path = os.path.join(web_dir, file_path) if file_path else ""
                    reqs = get_spec_markers(abs_path)

                    rows.append((
                        md(title),
                        md(file_col),
                        md(assertion or "-"),
                        md(reqs),
                        "FAILED",
                    ))


walk_suites(data.get("suites", []))

timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

with open(failures_file, "w") as fh:
    fh.write(f"## Failed Tests — {timestamp}\n\n")
    fh.write("| Test | File | Assertion | Requirements | Status |\n")
    fh.write("|------|------|-----------|--------------|--------|\n")
    if rows:
        for test, file_col, assertion, reqs, status in rows:
            fh.write(f"| {test} | {file_col} | {assertion} | {reqs} | {status} |\n")
    else:
        fh.write("| (see raw output) | - | Playwright exited non-zero | - | FAILED |\n")

print(f"Wrote {len(rows)} failure(s) to {failures_file}")
PYEOF

RESULTS_DIR="${RESULTS_DIR}" WEB_DIR="${WEB_DIR}" "${PYTHON}" "${PARSER_SCRIPT}"
rm -f "${PARSER_SCRIPT}"

echo "Read ${FAILURES_FILE} for details."
exit 1
