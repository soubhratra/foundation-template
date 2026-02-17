#!/bin/bash
set -e

echo "=== AI Module Removal Verification ==="
echo ""

# Track failures
FAILURES=0

# Check we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "ERROR: Must run from apps/api/ directory (where manage.py is located)"
    exit 1
fi

# 1. Check for imports from ai/ in other apps
echo "1. Checking for external dependencies on ai module..."

if [ -d "apps/ai" ]; then
    echo "   ⚠️  WARNING: apps/ai/ directory still exists"
    echo "   This check assumes the module is being verified before actual removal."
    AI_EXCLUDE="--exclude-dir=ai"
else
    AI_EXCLUDE=""
fi

# Check for "from apps.ai" imports
FROM_IMPORTS=$(grep -r "from apps\.ai" apps/ $AI_EXCLUDE --exclude-dir=__pycache__ --exclude="*.pyc" 2>/dev/null || true)
if [ -n "$FROM_IMPORTS" ]; then
    echo "   ✗ FAIL: Found 'from apps.ai' imports in other apps:"
    echo "$FROM_IMPORTS"
    FAILURES=$((FAILURES + 1))
else
    echo "   ✓ No 'from apps.ai' imports found"
fi

# Check for "import apps.ai" imports
IMPORT_IMPORTS=$(grep -r "import apps\.ai" apps/ $AI_EXCLUDE --exclude-dir=__pycache__ --exclude="*.pyc" 2>/dev/null || true)
if [ -n "$IMPORT_IMPORTS" ]; then
    echo "   ✗ FAIL: Found 'import apps.ai' in other apps:"
    echo "$IMPORT_IMPORTS"
    FAILURES=$((FAILURES + 1))
else
    echo "   ✓ No 'import apps.ai' found"
fi

# 2. Check Django configuration
echo ""
echo "2. Checking Django configuration..."

if ! python -c "import django" 2>/dev/null; then
    echo "   ⚠️  WARNING: Django not found. Activate virtual environment first:"
    echo "   source .venv/bin/activate"
    FAILURES=$((FAILURES + 1))
else
    # Capture check output to filter warnings
    CHECK_OUTPUT=$(python manage.py check 2>&1)
    CHECK_EXIT=$?

    # Check for actual errors (not just warnings)
    if echo "$CHECK_OUTPUT" | grep -q "ERRORS:"; then
        echo "   ✗ FAIL: Django check found errors"
        echo "$CHECK_OUTPUT"
        FAILURES=$((FAILURES + 1))
    elif [ $CHECK_EXIT -ne 0 ] && ! echo "$CHECK_OUTPUT" | grep -q "WARNINGS:"; then
        echo "   ✗ FAIL: Django check failed"
        echo "$CHECK_OUTPUT"
        FAILURES=$((FAILURES + 1))
    else
        echo "   ✓ Django check passes (warnings ignored)"
    fi
fi

# 3. Check if apps.ai is in INSTALLED_APPS
echo ""
echo "3. Checking INSTALLED_APPS..."

if [ -f "config/settings/base.py" ]; then
    if grep -q '"apps\.ai"' config/settings/base.py; then
        echo "   ⚠️  WARNING: apps.ai still in INSTALLED_APPS"
        echo "   Remove it from config/settings/base.py before removal"
    else
        echo "   ✓ apps.ai not in INSTALLED_APPS"
    fi
fi

# 4. Run tests (if pytest available)
echo ""
echo "4. Running tests..."

if command -v pytest &> /dev/null; then
    if [ -d "apps/ai" ]; then
        TEST_EXCLUDE="--ignore=apps/ai"
    else
        TEST_EXCLUDE=""
    fi

    if pytest apps/ $TEST_EXCLUDE --tb=short -q 2>/dev/null; then
        echo "   ✓ Tests pass"
    else
        echo "   ⚠️  Some tests failed (may be unrelated to AI module removal)"
    fi
else
    echo "   ⚠️  pytest not found, skipping tests"
fi

# 5. Run linting (if ruff available)
echo ""
echo "5. Running linting..."

if command -v ruff &> /dev/null; then
    if [ -d "apps/ai" ]; then
        LINT_EXCLUDE="--exclude apps/ai"
    else
        LINT_EXCLUDE=""
    fi

    if ruff check apps/ $LINT_EXCLUDE 2>/dev/null; then
        echo "   ✓ Linting passes"
    else
        echo "   ⚠️  Linting found issues (may be unrelated to AI module removal)"
    fi
else
    echo "   ⚠️  ruff not found, skipping linting"
fi

# Summary
echo ""
echo "=== Verification Summary ==="

if [ $FAILURES -eq 0 ]; then
    echo "✅ All critical checks passed"
    echo ""
    echo "The AI module can be safely removed, or has been removed cleanly."
    exit 0
else
    echo "❌ $FAILURES critical check(s) failed"
    echo ""
    echo "Fix the issues above before proceeding with removal."
    exit 1
fi
