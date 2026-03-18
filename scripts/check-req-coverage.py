#!/usr/bin/env python3
"""check-req-coverage.py — Report which OpenSpec requirement IDs have test coverage.

Sources of requirement IDs:
  - .planning/ROADMAP.md   : phases 13–34 (v1.2–v1.4), scanned for **Requirements**: lines
  - .planning/milestones/v1.3-ROADMAP.md  : v1.3 archived phase details
  - .planning/milestones/v1.4-ROADMAP.md  : v1.4 archived phase details
  - .planning/REQUIREMENTS.md             : v1.5 requirement IDs (AUTO-*, TRACE-*, E2E-*, etc.)

Coverage markers:
  - pytest  : @pytest.mark.req("REQ-ID")  in apps/api/tests/**/*.py
  - Playwright: // @spec: REQ-ID          in apps/web/tests/e2e/**/*.ts

Exit codes:
  0 — all requirements covered (or no requirements found)
  1 — one or more requirements are uncovered
"""

import glob as glob_module
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (all relative to repo root, resolved to absolute)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

ROADMAP_FILE = REPO_ROOT / ".planning" / "ROADMAP.md"
REQUIREMENTS_FILE = REPO_ROOT / ".planning" / "REQUIREMENTS.md"
MILESTONE_ROADMAPS = [
    REPO_ROOT / ".planning" / "milestones" / "v1.2-ROADMAP.md",
    REPO_ROOT / ".planning" / "milestones" / "v1.3-ROADMAP.md",
    REPO_ROOT / ".planning" / "milestones" / "v1.4-ROADMAP.md",
]

API_TESTS_GLOB = str(REPO_ROOT / "apps" / "api" / "tests" / "**" / "*.py")
E2E_TESTS_GLOB = str(REPO_ROOT / "apps" / "web" / "tests" / "e2e" / "**" / "*.ts")

# ---------------------------------------------------------------------------
# Step 1: Collect requirement IDs
# ---------------------------------------------------------------------------
REQ_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
ROADMAP_REQ_LINE_RE = re.compile(r"^\*\*Requirements\*\*:\s*(.+)$", re.MULTILINE)

# Phases 13–34 cover v1.2–v1.4 milestones
COVERED_PHASE_RE = re.compile(r"^###\s+Phase\s+(\d+):", re.MULTILINE)


def collect_req_ids_from_roadmap(path: Path) -> set[str]:
    """Extract all requirement IDs from **Requirements**: lines in a roadmap file."""
    if not path.is_file():
        return set()
    content = path.read_text()
    ids: set[str] = set()
    for m in ROADMAP_REQ_LINE_RE.finditer(content):
        ids.update(REQ_ID_RE.findall(m.group(1)))
    return ids


def collect_req_ids_from_requirements_file(path: Path) -> set[str]:
    """Extract requirement IDs from REQUIREMENTS.md.

    Looks for lines like:
      - [ ] **AUTO-01**: ...
      - [x] **E2E-03**: ...
    """
    if not path.is_file():
        return set()
    content = path.read_text()
    # Match "**REQ-ID**" patterns on list item lines
    ids = set(re.findall(r"\*\*([A-Z][A-Z0-9]+-\d+)\*\*", content))
    return ids


# Collect from ROADMAP.md phases 13–34 only (v1.2–v1.4).
# The main ROADMAP.md has phase 13–18 details inline; v1.3 and v1.4 are archived.
roadmap_ids: set[str] = set()

# From the main ROADMAP.md: only gather from phase blocks 13–34
if ROADMAP_FILE.is_file():
    content = ROADMAP_FILE.read_text()
    # Find all phase headers and their byte offsets
    phase_spans: list[tuple[int, int, int]] = []  # (phase_num, start, end)
    phase_headers = list(re.finditer(r"^###\s+Phase\s+(\d+):", content, re.MULTILINE))
    for i, ph in enumerate(phase_headers):
        phase_num = int(ph.group(1))
        start = ph.start()
        end = (
            phase_headers[i + 1].start() if i + 1 < len(phase_headers) else len(content)
        )
        phase_spans.append((phase_num, start, end))

    for phase_num, start, end in phase_spans:
        if 13 <= phase_num <= 34:
            block = content[start:end]
            for m in ROADMAP_REQ_LINE_RE.finditer(block):
                roadmap_ids.update(REQ_ID_RE.findall(m.group(1)))

# From archived milestone roadmaps (v1.2–v1.4)
for path in MILESTONE_ROADMAPS:
    roadmap_ids.update(collect_req_ids_from_roadmap(path))

# From REQUIREMENTS.md (v1.5 requirements: AUTO-*, TRACE-*, E2E-*, CI-*, DOCS-*)
requirements_ids = collect_req_ids_from_requirements_file(REQUIREMENTS_FILE)

all_req_ids = roadmap_ids | requirements_ids

# ---------------------------------------------------------------------------
# Step 2: Scan test files for markers
# ---------------------------------------------------------------------------

# pytest: @pytest.mark.req("REQ-ID") or @pytest.mark.req("REQ-ID", "REQ-ID2", ...)
PYTEST_MARKER_RE = re.compile(r"@pytest\.mark\.req\(([^)]+)\)")
# Playwright: // @spec: REQ-ID
PLAYWRIGHT_SPEC_RE = re.compile(r"//\s*@spec:\s*([A-Z][A-Z0-9]+-\d+)")

# Map: req_id -> list of file paths where it was found
coverage: dict[str, list[str]] = defaultdict(list)


def scan_pytest_tests() -> None:
    files = glob_module.glob(API_TESTS_GLOB, recursive=True)
    for fpath in files:
        try:
            content = Path(fpath).read_text()
        except OSError:
            continue
        for m in PYTEST_MARKER_RE.finditer(content):
            # Extract all quoted IDs from the marker arguments
            for req_id in re.findall(r'["\']([A-Z][A-Z0-9]+-\d+)["\']', m.group(1)):
                rel = os.path.relpath(fpath, REPO_ROOT)
                if rel not in coverage[req_id]:
                    coverage[req_id].append(rel)


def scan_e2e_tests() -> None:
    files = glob_module.glob(E2E_TESTS_GLOB, recursive=True)
    for fpath in files:
        try:
            content = Path(fpath).read_text()
        except OSError:
            continue
        for m in PLAYWRIGHT_SPEC_RE.finditer(content):
            req_id = m.group(1).strip()
            rel = os.path.relpath(fpath, REPO_ROOT)
            if rel not in coverage[req_id]:
                coverage[req_id].append(rel)


scan_pytest_tests()
scan_e2e_tests()

# ---------------------------------------------------------------------------
# Step 3: Build report
# ---------------------------------------------------------------------------

covered_count = 0
uncovered_count = 0
rows: list[tuple[str, str, str]] = []

for req_id in sorted(all_req_ids):
    found_in = coverage.get(req_id, [])
    if found_in:
        status = "covered"
        found_str = found_in[0]  # show first file
        covered_count += 1
    else:
        status = "uncovered"
        found_str = ""
        uncovered_count += 1
    rows.append((req_id, status, found_str))

# ---------------------------------------------------------------------------
# Step 4: Print formatted table
# ---------------------------------------------------------------------------
COL_REQ = max(len("REQ-ID"), max((len(r[0]) for r in rows), default=6))
COL_STATUS = max(len("Status"), max((len(r[1]) for r in rows), default=8))
COL_FOUND = max(len("Found In"), max((len(r[2]) for r in rows), default=10))

sep_line = f"{'-' * COL_REQ}-+-{'-' * COL_STATUS}-+-{'-' * COL_FOUND}"

print()
print("Requirement Coverage Report")
print("===========================")
print(f"{'REQ-ID':<{COL_REQ}} | {'Status':<{COL_STATUS}} | {'Found In':<{COL_FOUND}}")
print(sep_line)

for req_id, status, found_str in rows:
    icon = "\u2705" if status == "covered" else "\u274c"
    print(f"{req_id:<{COL_REQ}} | {icon} {status:<{COL_STATUS - 2}} | {found_str}")

print()
print(f"Total requirements : {len(all_req_ids)}")
print(f"  Covered          : {covered_count}")
print(f"  Uncovered        : {uncovered_count}")
print()

if uncovered_count > 0:
    print(f"ERROR: {uncovered_count} requirement(s) have no test coverage.")
    sys.exit(1)
else:
    print("All requirements have test coverage.")
    sys.exit(0)
