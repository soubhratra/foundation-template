# Error Handling

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

Error handling in the Foundation Template follows a unified strategy across the full stack: Django Ninja Extra backend, Next.js web frontend, and Expo mobile app. Every error that surfaces to a user or a log is routed through a standardized format, with clear rules for when to display errors to users, when to log silently, and how to structure error payloads so that all three clients can parse them identically.

---

## Specifications

### 1. Backend Error Handling (Django Ninja Extra)

#### 1.1 Standardized Error Response Format

All API error responses use a single JSON envelope:

```json
{
  "error": {
    "code": "AUTH_001",
    "message": "Authentication credentials were not provided.",
    "details": {}
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.code` | `string` | Yes | Machine-readable error code from the taxonomy (see section 4.1) |
| `error.message` | `string` | Yes | Human-readable message safe to display to end users |
| `error.details` | `object` | No | Additional context; for validation errors, contains field-level errors |

#### 1.2 Validation Error Format (Pydantic Field Errors)

When Pydantic schema validation fails on request input, the response includes field-level errors in `details`:

```json
{
  "error": {
    "code": "VALIDATION_001",
    "message": "Validation failed.",
    "details": {
      "field_errors": {
        "email": ["Enter a valid email address."],
        "password": ["This field is required."]
      }
    }
  }
}
```

- Each key in `field_errors` is the field name from the Pydantic schema.
- Each value is an array of error message strings for that field.
- Non-field validation errors (e.g., cross-field validation) use the key `__all__`.

#### 1.3 Django Ninja Extra Exception Handlers

Custom exception handlers are registered on the NinjaExtraAPI instance to intercept Django and Pydantic exceptions and convert them to the standardized format:

```python
# apps/api/config/api.py
from ninja_extra import NinjaExtraAPI
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError as PydanticValidationError

api = NinjaExtraAPI(title="Foundation API", version="1.0.0")

@api.exception_handler(PydanticValidationError)
def pydantic_validation_error_handler(request, exc):
    field_errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        field_errors.setdefault(field, []).append(error["msg"])
    return api.create_response(request, {
        "error": {
            "code": "VALIDATION_001",
            "message": "Validation failed.",
            "details": {"field_errors": field_errors}
        }
    }, status=400)

@api.exception_handler(DjangoValidationError)
def django_validation_error_handler(request, exc):
    return api.create_response(request, {
        "error": {
            "code": "VALIDATION_002",
            "message": str(exc.message),
            "details": {}
        }
    }, status=400)

@api.exception_handler(Exception)
def unhandled_exception_handler(request, exc):
    import logging
    logger = logging.getLogger("foundation.unhandled")
    logger.exception("Unhandled exception", exc_info=exc)
    return api.create_response(request, {
        "error": {
            "code": "SERVER_001",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
    }, status=500)
```

#### 1.4 HTTP Status Code Usage

| Status Code | When Used | Error Code Prefix |
|-------------|-----------|-------------------|
| 400 | Request validation failures (Pydantic/Zod), malformed input | `VALIDATION_*` |
| 401 | Missing or invalid authentication credentials | `AUTH_*` |
| 403 | Authenticated but lacks permission for the requested resource | `AUTH_*` |
| 404 | Resource not found | `RESOURCE_*` |
| 409 | Conflict (e.g., duplicate email on signup) | `CONFLICT_*` |
| 422 | Semantic validation failure (input is syntactically valid but logically wrong) | `VALIDATION_*` |
| 429 | Rate limit exceeded | `RATE_*` |
| 500 | Unhandled server error | `SERVER_*` |

#### 1.5 Unhandled Exception Catching

- All unhandled exceptions return HTTP 500 with the generic message `"An unexpected error occurred. Please try again later."`.
- The actual exception, traceback, and request metadata are logged at the `ERROR` level via Django's logging framework.
- In `DEBUG=True` mode, `details` may include a truncated traceback for developer convenience. In production (`DEBUG=False`), `details` is always an empty object.

#### 1.6 Django Logging Configuration

```python
# config/settings/base.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "foundation": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "foundation.unhandled": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
```

---

### 2. Frontend Error Handling (Next.js)

#### 2.1 Error Boundary Components (`error.tsx`)

Each route group has an `error.tsx` boundary component that catches rendering errors:

```tsx
// app/(dashboard)/error.tsx
"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p>An unexpected error occurred. Please try again.</p>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```

- The root `app/error.tsx` catches any unhandled error across the app.
- Route-group-specific `error.tsx` files provide contextual recovery actions.
- `app/global-error.tsx` handles errors in the root layout itself.

#### 2.2 API Error Parsing

A shared utility function parses the standardized error response format:

```typescript
// lib/api-error.ts
export interface ApiError {
  code: string;
  message: string;
  details: {
    field_errors?: Record<string, string[]>;
  };
}

export function parseApiError(response: unknown): ApiError {
  if (
    typeof response === "object" &&
    response !== null &&
    "error" in response
  ) {
    return (response as { error: ApiError }).error;
  }
  return {
    code: "UNKNOWN_001",
    message: "An unexpected error occurred.",
    details: {},
  };
}
```

#### 2.3 Toast Notifications for User-Facing Errors

- Non-field errors (server errors, auth errors, network errors) display as toast notifications.
- Field-level validation errors display inline on the form, not as toasts.
- Toasts auto-dismiss after 5 seconds for non-critical errors. Critical errors (auth failures) persist until dismissed.

#### 2.4 Form Validation Errors (Zod)

Zod validation runs before API submission. Field errors from Zod display inline on the form fields. If the API returns additional validation errors (e.g., "email already taken"), those are merged into the form field errors:

```typescript
// Pattern: Merge API field errors into react-hook-form
const onSubmit = async (data: FormData) => {
  try {
    await apiClient.POST("/api/v1/auth/signup", { body: data });
  } catch (err) {
    const apiError = parseApiError(err);
    if (apiError.details.field_errors) {
      Object.entries(apiError.details.field_errors).forEach(
        ([field, messages]) => {
          form.setError(field as keyof FormData, {
            message: messages[0],
          });
        }
      );
    }
  }
};
```

#### 2.5 Loading and Error States in React Query

```typescript
const { data, error, isLoading, isError } = useQuery({
  queryKey: ["user", "me"],
  queryFn: () => apiClient.GET("/api/v1/users/me"),
  retry: (failureCount, error) => {
    // Do not retry on 401/403 (auth errors)
    if (error.status === 401 || error.status === 403) return false;
    return failureCount < 3;
  },
});
```

- `isLoading`: Render skeleton or spinner.
- `isError`: Render inline error message with retry button.
- 401 errors trigger redirect to login (handled by a global query client `onError` callback).
- 500 errors show a generic error message with retry.

---

### 3. Mobile Error Handling (Expo)

#### 3.1 Error Boundary Component

A top-level error boundary wraps the Expo Router layout:

```tsx
// app/_layout.tsx
import { ErrorBoundary } from "react-error-boundary";

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Something went wrong</Text>
      <Button title="Try again" onPress={resetErrorBoundary} />
    </View>
  );
}

export default function RootLayout() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Slot />
    </ErrorBoundary>
  );
}
```

#### 3.2 API Error Handling

Mobile uses the same `parseApiError` utility from the shared `packages/api-client` or `packages/business-logic`. Error parsing logic is identical to web.

#### 3.3 Network Error Handling (Offline Detection)

```typescript
// lib/network.ts
import NetInfo from "@react-native-community/netinfo";

export function useNetworkStatus() {
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsConnected(state.isConnected ?? true);
    });
    return unsubscribe;
  }, []);

  return { isConnected };
}
```

- When `isConnected` is `false`, API calls are deferred.
- A banner displays at the top of the screen: "You are offline. Some features may be unavailable."
- React Query `networkMode` is set to `"online"` so queries do not fire when offline.

#### 3.4 Token Refresh Error Handling

When a token refresh fails (refresh token expired or revoked), the user is redirected to the login screen:

```typescript
// In the API client interceptor
if (response.status === 401) {
  const refreshResult = await attemptTokenRefresh();
  if (!refreshResult.success) {
    await SecureStore.deleteItemAsync("access_token");
    await SecureStore.deleteItemAsync("refresh_token");
    router.replace("/(auth)/login");
    return;
  }
  // Retry original request with new token
}
```

---

### 4. Cross-Cutting Concerns

#### 4.1 Error Code Taxonomy

| Code | Category | Description |
|------|----------|-------------|
| `AUTH_001` | Authentication | Credentials not provided |
| `AUTH_002` | Authentication | Invalid credentials (wrong email/password) |
| `AUTH_003` | Authentication | Token expired |
| `AUTH_004` | Authentication | Token invalid or malformed |
| `AUTH_005` | Authorization | Insufficient permissions |
| `AUTH_006` | Authentication | Account not verified (email verification pending) |
| `VALIDATION_001` | Validation | Pydantic schema validation failed (field-level errors in details) |
| `VALIDATION_002` | Validation | Django model validation failed |
| `VALIDATION_003` | Validation | Business rule validation failed |
| `RESOURCE_001` | Resource | Resource not found |
| `RESOURCE_002` | Resource | Resource already exists (conflict) |
| `CONFLICT_001` | Conflict | Duplicate entry (e.g., email already registered) |
| `RATE_001` | Rate Limit | Too many requests |
| `SERVER_001` | Server | Unhandled server error |
| `SERVER_002` | Server | External service unavailable (e.g., LLM provider down) |
| `NETWORK_001` | Network | Client is offline (mobile only, client-side code) |

#### 4.2 Logging Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Verbose diagnostic output; disabled in production | Query parameters, full request body |
| `INFO` | Normal operational events worth recording | User signup completed, OpenAPI spec regenerated |
| `WARNING` | Unexpected but recoverable situations | Deprecated endpoint accessed, rate limit approaching |
| `ERROR` | Unhandled exceptions, failed external service calls | 500 error, LLM provider timeout |
| `CRITICAL` | System-level failures requiring immediate attention | Database connection lost, migration failed |

#### 4.3 User-Facing vs Silent Errors

| Scenario | Show to User? | Log Level | User Message |
|----------|---------------|-----------|--------------|
| Form validation failure | Yes (inline on field) | Not logged | Field-specific message from Zod/Pydantic |
| Wrong password on login | Yes (toast or form) | `INFO` | "Invalid email or password." |
| 403 Forbidden | Yes (toast) | `WARNING` | "You don't have permission to perform this action." |
| 404 Not Found | Yes (page or toast) | Not logged | "The requested resource was not found." |
| 500 Server Error | Yes (toast or error page) | `ERROR` | "An unexpected error occurred. Please try again later." |
| Network timeout | Yes (toast) | `WARNING` | "Request timed out. Please check your connection." |
| Token refresh succeeded silently | No | `DEBUG` | N/A |
| Background sync failed | No (unless repeated) | `WARNING` | N/A |
| Database query slow (> 1s) | No | `WARNING` | N/A |

---

### 5. GIVEN/WHEN/THEN Scenarios

#### Scenario: Validation Error on Form Submission

```
GIVEN a user is on the signup form
  AND the email field is empty
  AND the password field contains "123"
WHEN the user clicks "Sign Up"
THEN the Zod schema validates client-side
  AND the email field displays "Email is required."
  AND the password field displays "Password must be at least 8 characters."
  AND no API request is made
  AND no toast notification is shown
```

```
GIVEN a user is on the signup form
  AND all client-side validation passes
WHEN the user clicks "Sign Up"
  AND the API returns 400 with error code CONFLICT_001
  AND details contain field_errors: { "email": ["A user with this email already exists."] }
THEN the email field displays "A user with this email already exists."
  AND the other fields retain their values
  AND no toast notification is shown (error is field-level)
```

#### Scenario: Authentication Failure (401)

```
GIVEN a user is browsing a protected page on the web app
  AND their session cookie has expired
WHEN they trigger an API request (e.g., loading dashboard data)
THEN the API returns 401 with error code AUTH_003
  AND the React Query global error handler detects the 401
  AND the user is redirected to /login
  AND a toast notification shows "Your session has expired. Please log in again."
```

#### Scenario: Server Error (500)

```
GIVEN a user is submitting a form that triggers a backend service call
WHEN the backend encounters an unhandled exception
THEN the exception handler catches it
  AND the full traceback is logged at ERROR level with request metadata
  AND the API returns 500 with error code SERVER_001
  AND message is "An unexpected error occurred. Please try again later."
  AND the details object is empty (no internal information leaked)
  AND the client displays a toast notification with the generic message
  AND the client provides a "Try again" action
```

#### Scenario: Network Offline (Mobile)

```
GIVEN a user is using the mobile app
  AND the device loses network connectivity
WHEN the NetInfo listener detects isConnected=false
THEN a persistent banner appears: "You are offline. Some features may be unavailable."
  AND React Query pauses all pending queries (networkMode: "online")
  AND no API requests are attempted
  AND cached data remains visible
WHEN network connectivity is restored
THEN the banner disappears
  AND React Query resumes paused queries automatically
  AND fresh data replaces cached data
```

#### Scenario: Token Expired During Request (Mobile)

```
GIVEN a mobile user has a valid refresh token
  AND their access token has expired (15-minute lifetime)
WHEN they trigger an API request
THEN the API client interceptor receives a 401 response
  AND the interceptor calls POST /api/v1/auth/token/refresh with the refresh token
  AND the server returns a new access token
  AND the interceptor stores the new access token in expo-secure-store
  AND the interceptor retries the original request with the new token
  AND the user sees no error; the request completes transparently
```

```
GIVEN a mobile user's refresh token has expired (7-day lifetime)
WHEN they trigger an API request
  AND the access token 401 triggers a refresh attempt
  AND the refresh endpoint returns 401 (refresh token also expired)
THEN both tokens are deleted from expo-secure-store
  AND the user is redirected to the login screen
  AND a toast notification shows "Your session has expired. Please log in again."
```

---

## Constraints

- All API error responses MUST use the standardized envelope format. No endpoint may return a bare string, array, or non-envelope object as an error response.
- Error codes MUST follow the taxonomy defined in section 4.1. New codes are added to the taxonomy before use.
- Production error responses (HTTP 500) MUST NOT include stack traces, file paths, or internal implementation details.
- Client-side validation (Zod) MUST run before API submission for all forms. Server-side validation is not a substitute for client-side validation, and vice versa.
- Mobile apps MUST handle offline state gracefully. No unhandled `fetch` rejections from network errors.
- Token refresh MUST be transparent to the user. A successful refresh does not surface any error or notification.
- Django logging MUST NOT log sensitive data (passwords, tokens, full credit card numbers) at any level.

---

## References

- `.planning/research/STACK.md` -- Stack decisions including React Query, react-hook-form, Zod
- `.planning/research/ARCHITECTURE.md` -- Authentication flow (session for web, JWT for mobile), API client interceptor pattern
- `.planning/research/PITFALLS.md` -- Auth misconfiguration pitfalls, CSRF handling
- `.planning/PROJECT.md` -- Project requirements and constraints
