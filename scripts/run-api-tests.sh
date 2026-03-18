#!/usr/bin/env bash
set -euo pipefail

# run-api-tests.sh — Run the full pytest suite and produce a structured failure report.
# Usage: scripts/run-api-tests.sh
# Outputs: test-results/FAILURES.md on failure
# Exits: 0 if all tests pass, 1 if any fail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/test-results"
FAILURES_FILE="${RESULTS_DIR}/FAILURES.md"
API_DIR="${REPO_ROOT}/apps/api"
RAW_OUTPUT="${RESULTS_DIR}/_pytest_raw.txt"

# Ensure test-results/ exists
mkdir -p "${RESULTS_DIR}"

# Resolve Python interpreter
PYTHON="${PYTHON:-python3}"
if ! command -v "${PYTHON}" &>/dev/null; then
  PYTHON="python"
fi
if ! command -v "${PYTHON}" &>/dev/null; then
  echo "ERROR: python / python3 not found on PATH." >&2
  exit 1
fi

# Check that pytest is importable
if ! "${PYTHON}" -m pytest --version &>/dev/null 2>&1; then
  echo "ERROR: pytest is not installed or not importable by ${PYTHON}." >&2
  echo "       Run: pip install pytest pytest-django" >&2
  exit 1
fi

echo "Running API tests (pytest)…"

set +e
(cd "${API_DIR}" && "${PYTHON}" -m pytest --tb=short -q --no-header 2>&1) \
  | tee "${RAW_OUTPUT}"
PYTEST_EXIT="${PIPESTATUS[0]}"
set -e

if [[ "${PYTEST_EXIT}" -eq 0 ]]; then
  echo "All API tests passed."
  rm -f "${RAW_OUTPUT}"
  exit 0
fi

echo ""
echo "Some tests failed. Writing ${FAILURES_FILE}…"

# Parse pytest output with an inline Python script (written to a temp file to avoid
# heredoc quoting issues when the script itself contains single/double quotes).
PARSER_SCRIPT="${RESULTS_DIR}/_parse_failures.py"

cat > "${PARSER_SCRIPT}" << 'PYEOF'
import re
import sys
import os
import datetime

results_dir  = os.environ["RESULTS_DIR"]
api_dir      = os.environ["API_DIR"]
raw_file     = os.path.join(results_dir, "_pytest_raw.txt")
failures_file = os.path.join(results_dir, "FAILURES.md")

if not os.path.isfile(raw_file):
    print("ERROR: raw pytest output not found.", file=sys.stderr)
    sys.exit(1)

with open(raw_file) as fh:
    content = fh.read()

# --tb=short produces lines like:
#   tests/foo/test_bar.py:42: AssertionError
#   followed by indented body lines
assertion_block_re = re.compile(
    r"^([\w/.\-]+\.py):(\d+):\s*(\w+)\s*$\n((?:[ \t]+.*\n)*)",
    re.MULTILINE,
)

# Map from relative test path -> (lineno, first assertion body line)
assertion_map: dict[str, tuple[str, str]] = {}
for m in assertion_block_re.finditer(content):
    fpath, lineno, exc, body = m.groups()
    lines = [ln.strip() for ln in body.strip().splitlines() if ln.strip()]
    assertion_map.setdefault(fpath, (lineno, lines[0] if lines else exc))

# Summary lines: FAILED tests/foo/test_bar.py::test_func - AssertionError: msg
failed_re = re.compile(
    r"^FAILED\s+([\w/.\-]+(?:\.py))::([^\s]+)\s*(?:-\s*(.*))?$",
    re.MULTILINE,
)


def get_req_markers(test_file_abs: str, test_name: str) -> str:
    """Return comma-separated @pytest.mark.req() IDs for the failing test function."""
    if not os.path.isfile(test_file_abs):
        return "-"
    with open(test_file_abs) as fh:
        src = fh.read()
    func_base = test_name.split("::")[-1]
    pattern = re.compile(
        r"((?:@pytest\.mark\.req\([^)]+\)\s*\n)+)\s*def\s+" + re.escape(func_base) + r"\b"
    )
    match = pattern.search(src)
    if not match:
        return "-"
    req_ids = re.findall(r'@pytest\.mark\.req\(["\']([^"\']+)["\']\)', match.group(1))
    return ", ".join(req_ids) if req_ids else "-"


def md(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


rows = []
for m in failed_re.finditer(content):
    rel_path, test_id, inline_msg = m.groups()
    inline_msg = (inline_msg or "").strip()

    line_no = ""
    assertion_msg = inline_msg
    for key, (lineno, assertion) in assertion_map.items():
        if rel_path.endswith(key) or key.endswith(rel_path):
            line_no = lineno
            if not assertion_msg:
                assertion_msg = assertion
            break

    file_col = f"{rel_path}:{line_no}" if line_no else rel_path

    # Try to resolve absolute path for marker extraction
    abs_path = os.path.join(api_dir, rel_path)
    if not os.path.isfile(abs_path):
        abs_path = rel_path  # fallback (may not exist)

    reqs = get_req_markers(abs_path, test_id)
    rows.append((md(test_id), md(file_col), md(assertion_msg or "-"), md(reqs), "FAILED"))

timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

with open(failures_file, "w") as fh:
    fh.write(f"## Failed Tests — {timestamp}\n\n")
    fh.write("| Test | File | Assertion | Requirements | Status |\n")
    fh.write("|------|------|-----------|--------------|--------|\n")
    if rows:
        for test, file_col, assertion, reqs, status in rows:
            fh.write(f"| {test} | {file_col} | {assertion} | {reqs} | {status} |\n")
    else:
        fh.write("| (see raw output) | - | pytest exited non-zero | - | FAILED |\n")

print(f"Wrote {len(rows)} failure(s) to {failures_file}")
PYEOF

RESULTS_DIR="${RESULTS_DIR}" API_DIR="${API_DIR}" "${PYTHON}" "${PARSER_SCRIPT}"
rm -f "${PARSER_SCRIPT}"

echo "Read ${FAILURES_FILE} for details."
exit 1
