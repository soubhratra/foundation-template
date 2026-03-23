#!/bin/bash
# critique.sh — Headless critique loop for any deliverable
# Usage: ./scripts/critique.sh <deliverable-file> <eval-json-file>
# Run from bizops/ directory

set -e

DELIVERABLE=$1
EVAL_FILE=$2

if [ -z "$DELIVERABLE" ] || [ -z "$EVAL_FILE" ]; then
  echo "Usage: ./scripts/critique.sh <deliverable-file> <eval-json-file>"
  exit 1
fi

echo "🔍 Critiquing: $DELIVERABLE"
echo "📋 Against: $EVAL_FILE"
echo "---"

claude -p \
  --system-prompt "You are a deliverable critic. Score against assertions only. No praise. No hedging. For each assertion, output TRUE or FALSE with a one-line justification. Then answer the meta-assertion YES or NO." \
  "Review this deliverable against these assertions:

DELIVERABLE:
$(cat $DELIVERABLE)

ASSERTIONS:
$(cat $EVAL_FILE)

Output format: JSON array with {assertion_id, result: true/false, justification} for each assertion, plus {meta_assertion_result: true/false, meta_justification}."
