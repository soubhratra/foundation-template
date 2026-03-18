#!/usr/bin/env bash
set -euo pipefail

# run-all-tests.sh — Run API + E2E tests sequentially and merge failure reports.
# Usage: scripts/run-all-tests.sh [--mode=dev|ci]
#   --mode=dev (default): exits non-zero on failure, prints guidance for the auto-fix loop
#   --mode=ci            : exits non-zero on failure (same exit behavior, no extra messaging)
# Outputs: test-results/FAILURES.md — merged report from both suites

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
RESULTS_DIR="${REPO_ROOT}/test-results"
FAILURES_FILE="${RESULTS_DIR}/FAILURES.md"

MODE="dev"
for arg in "$@"; do
  case "${arg}" in
    --mode=dev) MODE="dev" ;;
    --mode=ci)  MODE="ci"  ;;
    *)
      echo "Unknown argument: ${arg}" >&2
      echo "Usage: $0 [--mode=dev|ci]" >&2
      exit 1
      ;;
  esac
done

mkdir -p "${RESULTS_DIR}"

API_FAILURES="${RESULTS_DIR}/_api_failures.md"
E2E_FAILURES="${RESULTS_DIR}/_e2e_failures.md"
rm -f "${API_FAILURES}" "${E2E_FAILURES}"

API_EXIT=0
E2E_EXIT=0

echo "=========================================="
echo " Running API Tests"
echo "=========================================="
set +e
"${SCRIPTS_DIR}/run-api-tests.sh"
API_EXIT=$?
set -e

# If run-api-tests.sh produced a FAILURES.md, capture it
if [[ -f "${FAILURES_FILE}" ]]; then
  cp "${FAILURES_FILE}" "${API_FAILURES}"
fi

echo ""
echo "=========================================="
echo " Running E2E Tests"
echo "=========================================="
set +e
"${SCRIPTS_DIR}/run-e2e-tests.sh"
E2E_EXIT=$?
set -e

# If run-e2e-tests.sh produced a FAILURES.md, capture it
if [[ -f "${FAILURES_FILE}" ]]; then
  cp "${FAILURES_FILE}" "${E2E_FAILURES}"
fi

# Merge both reports into a single FAILURES.md
if [[ "${API_EXIT}" -ne 0 || "${E2E_EXIT}" -ne 0 ]]; then
  echo ""
  echo "Merging failure reports into ${FAILURES_FILE}…"

  {
    if [[ -f "${API_FAILURES}" ]]; then
      echo "## API Test Failures"
      echo ""
      # Strip the existing "## Failed Tests — <timestamp>" header and reuse the table
      tail -n +2 "${API_FAILURES}"
      echo ""
    else
      echo "## API Test Failures"
      echo ""
      echo "_No API test failures._"
      echo ""
    fi

    if [[ -f "${E2E_FAILURES}" ]]; then
      echo "## E2E Test Failures"
      echo ""
      tail -n +2 "${E2E_FAILURES}"
      echo ""
    else
      echo "## E2E Test Failures"
      echo ""
      echo "_No E2E test failures._"
      echo ""
    fi
  } > "${FAILURES_FILE}"

  # Clean up intermediates
  rm -f "${API_FAILURES}" "${E2E_FAILURES}"

  echo ""
  echo "=========================================="
  echo " Tests FAILED"
  echo "=========================================="

  if [[ "${MODE}" == "dev" ]]; then
    echo ""
    echo "Dev loop: read test-results/FAILURES.md to identify fixes."
    echo "  • Each row shows the failing test, the file:line, assertion, and requirement IDs."
    echo "  • Fix the failures, then re-run: scripts/run-all-tests.sh --mode=dev"
  fi

  exit 1
fi

# All passed — write an empty / success FAILURES.md for consistency
rm -f "${API_FAILURES}" "${E2E_FAILURES}"
echo ""
echo "=========================================="
echo " All tests passed."
echo "=========================================="
exit 0
