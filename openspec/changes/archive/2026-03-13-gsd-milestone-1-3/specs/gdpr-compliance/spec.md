## Implementation Decisions

### Why `UserDeletionService` orchestrator (not direct `user.delete()`)

`user.delete()` via Django's ORM cascade deletes the database record and any `on_delete=CASCADE` foreign keys, but it does not know about external systems. Without an orchestrator:

- The Stripe subscription remains active (continued charges)
- The Stripe customer record persists (leaks PII to Stripe)
- The PostHog person record persists (leaks behavioural data)

All three violate GDPR Article 17 (right to erasure). `UserDeletionService.execute()` runs the four-step cascade — cancel subscription → delete Stripe customer → delete PostHog person → `user.delete()` — with per-step exception catching so that an external service failure does not prevent the Django record from being deleted.

**Key invariant:** `user.delete()` is always called last and always executes, regardless of whether earlier steps raised exceptions.

### Why async Celery task (not synchronous deletion in the HTTP handler)

Stripe and PostHog API calls can take hundreds of milliseconds or fail transiently. Performing them synchronously in `DELETE /api/v1/account/` would block the HTTP worker and risk timeouts on the client side. The handler immediately returns `202 Accepted` and enqueues `delete_user_account.delay(user_id)`. The user is signed out from the client's perspective before the cascade completes.

### Why `transaction.on_commit()` is NOT used for deletion (unlike email)

Email tasks must not fire if the triggering transaction rolls back. Account deletion is the opposite: we want the cascade to proceed even if the handler's transaction had some issue. The Celery task is enqueued directly (not in `on_commit()`) because the primary concern is external service cleanup, not database consistency.

### Why cookie consent gates PostHog init (not just PostHog event capture)

`posthog.init()` itself can set cookies and begin session replay. Initialising PostHog before consent is granted violates GDPR/ePrivacy Directive requirements in EU jurisdictions. `providers.tsx` conditionally calls `posthog.init()` only after the user accepts the cookie consent banner. The banner state is stored in `localStorage` so it persists across page loads.

**Alternative rejected:** Initialising PostHog but setting `opt_out_capturing_by_default: true` — this is a valid GDPR approach but requires careful configuration of every PostHog capture point. Conditional init is simpler and more bulletproof.

### Why the alias-import pattern for Celery task patchability

`tasks.py` uses:

```python
from apps.billing.adapters import get_adapter as PaymentAdapter
from apps.observability.adapters import get_observability_adapter as ObservabilityAdapter
```

This allows tests to patch at `apps.accounts.tasks.PaymentAdapter` (the local name in the task module's namespace), which is the correct patching target for `unittest.mock.patch`. Patching at the original import path would not intercept calls already bound in the task module.
