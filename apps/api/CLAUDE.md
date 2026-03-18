# API — Testing Guide

## Running Tests

```bash
# From repo root
scripts/run-api-tests.sh

# Or directly
cd apps/api
python -m pytest
python -m pytest tests/billing/  # specific domain
python -m pytest -k "test_create" # specific pattern
```

## Adding Tests for New Features

### Directory Structure

```
apps/api/tests/
└── <domain>/
    ├── test_models.py
    ├── test_services.py
    ├── test_controllers.py
    └── test_schemas.py
```

### Required Fixtures

Use fixtures from `apps/api/conftest.py`:
- `authenticated_client` — Django test client with active session
- `api_client` — unauthenticated client
- `user` — factory_boy User instance (verified email)
- `organization` — factory_boy Organization instance

### Test Template

```python
import pytest
from django.test import TestCase

@pytest.mark.django_db
@pytest.mark.req("REQ-ID")   # REQUIRED: link to OpenSpec requirement
def test_my_feature_description():
    # Arrange
    ...
    # Act
    response = client.post(...)
    # Assert
    assert response.status_code == 201
```

### Spec Traceability — REQUIRED

Every test function that exercises a specific OpenSpec requirement MUST have `@pytest.mark.req("REQ-ID")`.

- Find the requirement ID in `.planning/REQUIREMENTS.md` or `.planning/ROADMAP.md`
- Use multiple IDs if the test covers several requirements: `@pytest.mark.req("REQ-01", "REQ-02")`
- Run `scripts/check-req-coverage.py` to verify coverage before marking a phase complete

**A phase cannot be marked complete if `check-req-coverage.py` reports uncovered requirements for that phase.**

## Coverage

Minimum threshold: 80% line coverage (enforced in CI).

```bash
cd apps/api
python -m pytest --cov=apps --cov-report=term-missing
```
