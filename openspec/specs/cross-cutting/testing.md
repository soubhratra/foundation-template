# Testing

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses a layered testing strategy across three platforms: pytest for the Django backend, vitest for the Next.js frontend and shared TypeScript packages, and detox for Expo mobile end-to-end tests. Each layer has distinct tooling but shares common principles: tests are isolated, deterministic, and fast. CI runs all test suites in parallel across three jobs.

---

## Specifications

### 1. Backend Testing (pytest)

#### 1.1 Test Naming Convention

All test functions follow the pattern: `test_<what>_<when>_<expected>`

```python
# Good
def test_create_user_with_valid_data_returns_201():
def test_login_with_wrong_password_returns_401():
def test_get_user_when_unauthenticated_returns_401():

# Bad
def test_user():
def test_create():
def test_it_works():
```

#### 1.2 conftest.py Patterns

The root `conftest.py` provides shared fixtures. App-specific `conftest.py` files add domain-specific fixtures.

```python
# apps/api/conftest.py (root-level for Django project)
import pytest
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    """Unauthenticated Django test client."""
    return Client()

@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    def create_user(**kwargs):
        defaults = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
        }
        defaults.update(kwargs)
        password = defaults.pop("password")
        user = User.objects.create_user(password=password, **defaults)
        return user
    return create_user

@pytest.fixture
def authenticated_client(api_client, user_factory):
    """Django test client with an authenticated session."""
    user = user_factory()
    api_client.force_login(user)
    return api_client

@pytest.fixture
def auth_token(user_factory):
    """JWT access token for mobile-style auth testing."""
    user = user_factory()
    # Generate token via the auth service
    from apps.accounts.services import AuthService
    tokens = AuthService().create_tokens(user)
    return tokens["access"]
```

#### 1.3 Test Database Configuration

```python
# config/settings/test.py (or in conftest.py via django_settings)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_foundation",
        "USER": "foundation",
        "PASSWORD": "foundation",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

- Tests use a real Postgres database with PGVector extension enabled.
- `pytest-django` handles test database creation and teardown.
- Each test runs in a transaction that is rolled back after the test (default `pytest-django` behavior).
- PGVector extension is enabled via a migration, so `CREATE EXTENSION vector` runs automatically during test database creation.

#### 1.4 API Endpoint Tests (Django Test Client)

```python
# apps/api/apps/accounts/tests/test_controllers.py
import pytest
from django.test import Client

@pytest.mark.django_db
class TestUserController:
    def test_get_current_user_when_authenticated_returns_user_data(
        self, authenticated_client
    ):
        response = authenticated_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    def test_get_current_user_when_unauthenticated_returns_401(
        self, api_client
    ):
        response = api_client.get("/api/v1/users/me")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTH_001"

    def test_signup_with_duplicate_email_returns_409(
        self, api_client, user_factory
    ):
        user_factory(email="taken@example.com")
        response = api_client.post(
            "/api/v1/auth/signup",
            data={"email": "taken@example.com", "password": "validpass123"},
            content_type="application/json",
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CONFLICT_001"
```

#### 1.5 Service Layer Unit Tests

Service tests do not use HTTP; they call the service class directly:

```python
# apps/api/apps/accounts/tests/test_services.py
import pytest
from apps.accounts.services import UserService

@pytest.mark.django_db
class TestUserService:
    def test_get_user_with_valid_id_returns_user(self, user_factory):
        user = user_factory()
        service = UserService()
        result = service.get_user(user.id)
        assert result.email == user.email

    def test_get_user_with_invalid_id_raises_not_found(self):
        service = UserService()
        with pytest.raises(User.DoesNotExist):
            service.get_user(99999)
```

#### 1.6 Model Tests

```python
# apps/api/apps/accounts/tests/test_models.py
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email_succeeds(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")

    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="testpass123")
```

#### 1.7 Factory Pattern

The template uses manual fixture factories (functions in `conftest.py`) rather than `factory_boy`. This avoids an additional dependency and keeps the factory logic transparent. Projects may adopt `factory_boy` if model complexity warrants it.

#### 1.8 Coverage Configuration

```ini
# pyproject.toml or pytest.ini
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["tests.py", "test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=apps --cov-report=term-missing --cov-report=html --cov-fail-under=80"
```

- Minimum coverage threshold: 80%.
- Coverage measures the `apps/` directory (Django apps), not third-party or configuration code.
- `--cov-report=html` generates an HTML report for local review.

---

### 2. Frontend Testing (vitest)

#### 2.1 Test File Co-location

Test files are co-located with the components they test:

```
components/
  UserProfile.tsx
  UserProfile.test.tsx
  LoginForm.tsx
  LoginForm.test.tsx
hooks/
  useAuth.ts
  useAuth.test.ts
```

#### 2.2 Component Testing with Testing Library

```tsx
// components/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LoginForm } from "./LoginForm";
import { describe, it, expect, vi } from "vitest";

describe("LoginForm", () => {
  it("displays validation errors for empty fields", async () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it("calls onSubmit with form data when valid", async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password123",
      });
    });
  });
});
```

#### 2.3 Hook Testing with renderHook

```tsx
// hooks/useAuth.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { useAuth } from "./useAuth";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

function wrapper({ children }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useAuth", () => {
  it("returns user data when authenticated", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => {
      expect(result.current.user).toBeDefined();
      expect(result.current.isAuthenticated).toBe(true);
    });
  });
});
```

#### 2.4 API Mocking with MSW (Mock Service Worker)

MSW intercepts network requests at the service worker level, providing realistic API mocking without modifying application code:

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/v1/users/me", () => {
    return HttpResponse.json({
      id: 1,
      email: "test@example.com",
      first_name: "Test",
      last_name: "User",
    });
  }),

  http.post("/api/v1/auth/login", async ({ request }) => {
    const body = await request.json();
    if (body.password === "wrong") {
      return HttpResponse.json(
        {
          error: {
            code: "AUTH_002",
            message: "Invalid email or password.",
            details: {},
          },
        },
        { status: 401 }
      );
    }
    return HttpResponse.json({ message: "Login successful." });
  }),
];
```

```typescript
// tests/mocks/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

```typescript
// vitest.setup.ts
import { server } from "./tests/mocks/server";
import { beforeAll, afterEach, afterAll } from "vitest";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

#### 2.5 Snapshot Testing

Snapshot tests are used sparingly -- only for stable, presentational components that rarely change:

- Snapshots are acceptable for: icon components, static layout components, design-system primitives.
- Snapshots are NOT acceptable for: interactive components, components with dynamic data, components under active development.
- When a snapshot test fails, the developer reviews the diff and explicitly accepts or fixes the change.

#### 2.6 Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      thresholds: {
        statements: 80,
        branches: 70,
        functions: 80,
        lines: 80,
      },
    },
  },
});
```

---

### 3. Mobile Testing (detox)

#### 3.1 E2E Test Patterns

Detox tests cover critical user flows, not individual components:

```javascript
// e2e/auth.test.js
describe("Authentication Flow", () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it("should sign up a new user", async () => {
    await element(by.id("signup-link")).tap();
    await element(by.id("email-input")).typeText("new@example.com");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("signup-button")).tap();
    await expect(element(by.id("dashboard-screen"))).toBeVisible();
  });

  it("should log out and log back in", async () => {
    await element(by.id("settings-tab")).tap();
    await element(by.id("logout-button")).tap();
    await expect(element(by.id("login-screen"))).toBeVisible();

    await element(by.id("email-input")).typeText("new@example.com");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();
    await expect(element(by.id("dashboard-screen"))).toBeVisible();
  });
});
```

#### 3.2 Device Configuration

```json
// .detoxrc.js
module.exports = {
  testRunner: {
    args: { config: "e2e/jest.config.js" },
    jest: { setupTimeout: 120000 }
  },
  apps: {
    "ios.debug": {
      type: "ios.app",
      binaryPath: "ios/build/Build/Products/Debug-iphonesimulator/Foundation.app",
      build: "xcodebuild -workspace ios/Foundation.xcworkspace -scheme Foundation -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build"
    },
    "android.debug": {
      type: "android.apk",
      binaryPath: "android/app/build/outputs/apk/debug/app-debug.apk",
      build: "cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug"
    }
  },
  devices: {
    simulator: { type: "ios.simulator", device: { type: "iPhone 15" } },
    emulator: { type: "android.emulator", device: { avdName: "Pixel_7_API_34" } }
  },
  configurations: {
    "ios.sim.debug": { device: "simulator", app: "ios.debug" },
    "android.emu.debug": { device: "emulator", app: "android.debug" }
  }
};
```

#### 3.3 When to Use Detox vs Unit Tests

| Use Detox For | Use Unit Tests (vitest) For |
|---------------|-----------------------------|
| Full auth flow (signup, login, logout) | Individual component rendering |
| Navigation between screens | Hook logic |
| Form submission with API interaction | Validation schema correctness |
| Offline → online transitions | Data transformation utilities |
| Push notification deep links | State management logic |

#### 3.4 CI Considerations

- Detox requires macOS runners (for iOS simulator).
- Detox E2E tests run only on merges to `main`, not on every PR (macOS runners are expensive).
- Android detox tests can run on Linux runners with Android emulator.
- A dedicated CI job handles detox with a 15-minute timeout.

---

### 4. Shared Package Testing

#### 4.1 Each Package Has Its Own Test Suite

Every shared package in `packages/` has its own `vitest.config.ts` and test files:

```
packages/
  api-client/
    src/
      client.ts
      client.test.ts
    vitest.config.ts
  schemas/
    src/
      auth.ts
      auth.test.ts
    vitest.config.ts
  ui-primitives/
    src/
      Button.tsx
      Button.test.tsx
    vitest.config.ts
```

#### 4.2 Zod Schema Tests

```typescript
// packages/schemas/src/auth.test.ts
import { describe, it, expect } from "vitest";
import { loginSchema, signupSchema } from "./auth";

describe("loginSchema", () => {
  it("accepts valid login data", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "password123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid email", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "password123",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].path).toEqual(["email"]);
    }
  });

  it("rejects short password", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "123",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].path).toEqual(["password"]);
    }
  });
});
```

#### 4.3 API Client Tests (Mocked Responses)

```typescript
// packages/api-client/src/client.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { createApiClient } from "./client";

const server = setupServer(
  http.get("http://localhost:8000/api/v1/users/me", () => {
    return HttpResponse.json({
      id: 1,
      email: "test@example.com",
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ApiClient", () => {
  it("fetches current user", async () => {
    const client = createApiClient("http://localhost:8000");
    const result = await client.GET("/api/v1/users/me");
    expect(result.data?.email).toBe("test@example.com");
  });
});
```

#### 4.4 UI Primitive Tests

Shared UI primitives are tested for rendering on the web platform (React Native Web):

```tsx
// packages/ui-primitives/src/Button.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "./Button";
import { describe, it, expect, vi } from "vitest";

describe("Button", () => {
  it("renders with label text", () => {
    render(<Button title="Click me" onPress={() => {}} />);
    expect(screen.getByText("Click me")).toBeDefined();
  });

  it("calls onPress when pressed", () => {
    const onPress = vi.fn();
    render(<Button title="Click me" onPress={onPress} />);
    fireEvent.click(screen.getByText("Click me"));
    expect(onPress).toHaveBeenCalledOnce();
  });

  it("does not call onPress when disabled", () => {
    const onPress = vi.fn();
    render(<Button title="Click me" onPress={onPress} disabled />);
    fireEvent.click(screen.getByText("Click me"));
    expect(onPress).not.toHaveBeenCalled();
  });
});
```

---

### 5. CI Integration

#### 5.1 Three Parallel Jobs

```yaml
# .github/workflows/ci.yml
jobs:
  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U test_user"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --directory apps/api
      - run: cd apps/api && uv run ruff check .
      - run: cd apps/api && uv run ruff format --check .
      - run: cd apps/api && uv run mypy .
      - run: cd apps/api && uv run pytest --cov --cov-fail-under=80
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db

  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo lint --filter=web...
      - run: pnpm turbo type-check --filter=web...
      - run: pnpm turbo test --filter=web...
      - run: pnpm turbo build --filter=web

  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo lint --filter=mobile...
      - run: pnpm turbo type-check --filter=mobile...
```

#### 5.2 Type Staleness Gate

A CI step verifies that generated TypeScript types match the current Django OpenAPI spec:

```yaml
  type-staleness:
    runs-on: ubuntu-latest
    needs: [api]
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: uv sync --directory apps/api
      - run: pnpm install --frozen-lockfile
      - run: cd apps/api && uv run python manage.py export_openapi_schema > /tmp/openapi.json
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db
      - run: diff /tmp/openapi.json packages/api-client/openapi.json
        # Fails if committed spec differs from generated spec
```

#### 5.3 Coverage Thresholds

| Platform | Tool | Minimum Coverage |
|----------|------|-----------------|
| Backend (Python) | pytest-cov | 80% line coverage |
| Frontend (TypeScript) | vitest v8 provider | 80% statements, 70% branches |
| Shared packages | vitest v8 provider | 80% statements, 70% branches |
| Mobile (E2E) | Not measured | N/A (E2E tests measure flow completeness, not code coverage) |

#### 5.4 Test Isolation

- No test shares mutable state with another test.
- Backend: Each test runs in a database transaction that is rolled back.
- Frontend: MSW handlers are reset between tests. React Query cache is cleared.
- Each test creates its own data via fixtures or factories.
- Tests do not depend on execution order.
- No global mutable singletons in test setup.

---

### 6. GIVEN/WHEN/THEN Scenarios

#### Scenario: Running Full Test Suite

```
GIVEN the developer has the project cloned and dependencies installed
  AND Docker Compose is running (Postgres available on port 5432)
WHEN the developer runs `pnpm test` from the repository root
THEN Turborepo runs the "test" task for all workspaces in parallel
  AND vitest runs for apps/web, packages/api-client, packages/schemas, packages/ui-primitives
  AND Turborepo also triggers `cd apps/api && uv run pytest` for the Django backend
  AND all tests pass independently without shared state
  AND coverage reports are generated for each workspace
  AND the total execution time is under 3 minutes for the baseline template
```

#### Scenario: Adding a New API Endpoint Test

```
GIVEN a developer has added a new controller endpoint POST /api/v1/items
  AND the endpoint accepts a Pydantic schema ItemCreateIn and returns ItemOut
WHEN the developer creates apps/api/apps/items/tests/test_controllers.py
THEN the test file imports pytest fixtures from conftest.py (api_client, authenticated_client)
  AND the test function is named test_create_item_with_valid_data_returns_201
  AND the test sends a POST request via authenticated_client with valid JSON body
  AND the test asserts response.status_code == 201
  AND the test asserts the response body matches the ItemOut schema structure
  AND a second test function test_create_item_when_unauthenticated_returns_401 verifies auth
  AND running `cd apps/api && uv run pytest apps/items/` passes both tests
```

#### Scenario: Testing a Shared Component on Both Platforms

```
GIVEN a shared Button component exists in packages/ui-primitives/src/Button.tsx
  AND it uses React Native primitives (Pressable, Text)
WHEN the developer runs `pnpm turbo test --filter=ui-primitives`
THEN vitest runs Button.test.tsx using react-native-web to render in jsdom
  AND the test verifies the button renders its label text
  AND the test verifies onPress is called on click
  AND the test verifies disabled state prevents onPress
  AND all assertions pass, confirming web-platform compatibility
  AND mobile-platform compatibility is verified via Expo dev testing (not automated in CI for unit tests)
```

---

## Constraints

- All test files MUST follow the co-location pattern: `component.test.tsx` next to `component.tsx`, `service.test.py` inside the app's `tests/` directory.
- Test names MUST be descriptive using the `test_<what>_<when>_<expected>` pattern (Python) or descriptive `it("description")` blocks (TypeScript).
- No test may depend on another test's side effects. Tests MUST be independently runnable.
- CI MUST fail if coverage drops below the defined thresholds (80% for backend and frontend).
- MSW MUST be used for API mocking in frontend tests. Direct `fetch` mocking (e.g., `vi.mock("fetch")`) is not permitted because it does not exercise the full request pipeline.
- Detox E2E tests run on merge to `main` only, not on every pull request, due to macOS runner cost.
- Snapshot tests MUST NOT be used for interactive or data-driven components. They are permitted only for static presentational components.

---

## References

- `.planning/research/STACK.md` -- Testing tools (pytest, vitest, detox), CI pipeline structure, coverage configuration
- `.planning/research/ARCHITECTURE.md` -- Django app structure (where tests live), CI workflow definition
- `.planning/research/PITFALLS.md` -- CI caching strategies, Turborepo + Python test orchestration
- `.planning/PROJECT.md` -- Testing requirements, code quality gates
