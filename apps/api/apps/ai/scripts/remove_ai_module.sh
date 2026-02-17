#!/bin/bash
set -e

echo "=== AI Module Removal Script ==="
echo ""
echo "This script will:"
echo "  1. Remove apps.ai from INSTALLED_APPS"
echo "  2. Run migration to drop ai tables"
echo "  3. Remove ai/ directory"
echo "  4. Run verification checks"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Check we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "ERROR: Must run from apps/api/ directory (where manage.py is located)"
    exit 1
fi

# Step 1: Remove from settings
echo ""
echo "Step 1: Removing apps.ai from INSTALLED_APPS..."

if [ ! -f "config/settings/base.py" ]; then
    echo "ERROR: config/settings/base.py not found"
    exit 1
fi

# Create backup
cp config/settings/base.py config/settings/base.py.bak
echo "✓ Created backup: config/settings/base.py.bak"

# Remove apps.ai line (Mac-compatible sed)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' '/[[:space:]]*"apps\.ai",/d' config/settings/base.py
else
    sed -i '/[[:space:]]*"apps\.ai",/d' config/settings/base.py
fi

echo "✓ Removed apps.ai from INSTALLED_APPS"

# Step 2: Drop database tables
echo ""
echo "Step 2: Dropping AI module database tables..."

# Check if we're in a virtual environment or have Django available
if ! python -c "import django" 2>/dev/null; then
    echo "ERROR: Django not found. Activate virtual environment first:"
    echo "  source .venv/bin/activate"
    exit 1
fi

python manage.py migrate ai zero
echo "✓ Database tables dropped"

# Step 3: Remove directory
echo ""
echo "Step 3: Removing apps/ai/ directory..."
rm -rf apps/ai/
echo "✓ Directory removed"

# Step 4: Verify removal
echo ""
echo "Step 4: Running verification checks..."

# Check Django still works
echo -n "Checking Django configuration... "
if python manage.py check --quiet; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "ERROR: Django check failed after removal"
    exit 1
fi

# Check for dead imports
echo -n "Checking for AI module imports in other apps... "
if grep -r "from apps\.ai" apps/ 2>/dev/null | grep -v "\.pyc" | grep -v "__pycache__"; then
    echo "✗ FAIL"
    echo "ERROR: Found imports from apps.ai in other apps (see above)"
    exit 1
else
    echo "✓ PASS"
fi

if grep -r "import apps\.ai" apps/ 2>/dev/null | grep -v "\.pyc" | grep -v "__pycache__"; then
    echo "✗ FAIL"
    echo "ERROR: Found imports of apps.ai in other apps (see above)"
    exit 1
fi

echo ""
echo "=== Removal Complete ==="
echo ""
echo "✅ AI module successfully removed"
echo ""
echo "Next steps:"
echo "  1. Remove dependencies from pyproject.toml:"
echo "     - pgvector, langgraph, langchain-*, celery, redis, openai, tiktoken"
echo "  2. Run: uv sync"
echo "  3. Restart your Django server"
echo ""
echo "Backup saved: config/settings/base.py.bak"
