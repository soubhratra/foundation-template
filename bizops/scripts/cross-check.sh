#!/bin/bash
# cross-check.sh — Cross-document consistency checker
# Usage: ./scripts/cross-check.sh <phase-number>
# Run from bizops/ directory

set -e

PHASE=$1
BIZOPS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$PHASE" ]; then
  echo "Usage: ./scripts/cross-check.sh <phase-number>"
  exit 1
fi

if [ "$PHASE" == "1" ]; then
  DOCS=""
  for f in competitor-matrix.md market-sizing.md tech-feasibility.md validation-report.md; do
    filepath="$BIZOPS_DIR/phase-1/$f"
    if [ -f "$filepath" ]; then
      DOCS="$DOCS\n\n--- $f ---\n$(cat $filepath)"
    fi
  done
  claude -p \
    --system-prompt "You are a startup due-diligence analyst. Find CONTRADICTIONS between these deliverables. Output: list each contradiction with severity (critical/warning/minor). If none, state internally consistent." \
    "Review these Phase 1 deliverables for contradictions:$DOCS"

elif [ "$PHASE" == "3" ]; then
  DOCS=""
  for f in phase-3/prd.md phase-3/gtm-plan.md docs/architecture.md; do
    filepath="$BIZOPS_DIR/$f"
    if [ -f "$filepath" ]; then
      DOCS="$DOCS\n\n--- $(basename $f) ---\n$(cat $filepath)"
    fi
  done
  claude -p \
    --system-prompt "You are a startup CTO. Find contradictions, scope mismatches, or gaps BETWEEN these documents." \
    "Review these Phase 3 deliverables:$DOCS"

else
  echo "Cross-check not defined for Phase $PHASE"
  exit 1
fi
