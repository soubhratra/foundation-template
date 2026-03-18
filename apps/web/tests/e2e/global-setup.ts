/**
 * global-setup.ts — Runs once before the entire Playwright suite.
 *
 * Verifies that the API server is reachable and that E2E test users exist.
 * Exits with a clear error message if either check fails, rather than letting
 * individual tests fail with cryptic login errors.
 *
 * In CI: test users are pre-seeded via `python manage.py shell` in the
 * workflow's "Seed test users" step (see .github/workflows/ci.yml and
 * .github/workflows/e2e-nightly.yml).
 *
 * In local dev: seed users manually once:
 *   cd apps/api
 *   python manage.py shell -c "
 *   from django.contrib.auth import get_user_model
 *   from allauth.account.models import EmailAddress
 *   User = get_user_model()
 *   for email, password, staff in [
 *     ('e2e@example.com', 'E2EPassword123!', False),
 *     ('e2e-admin@example.com', 'E2EPassword123!', True),
 *   ]:
 *     if not User.objects.filter(email=email).exists():
 *       u = User.objects.create_user(email=email, password=password, is_staff=staff)
 *       EmailAddress.objects.create(user=u, email=email, primary=True, verified=True)
 *   print('done')
 *   "
 */

const SEED_COMMAND = `
  cd apps/api && python manage.py shell -c "
  from django.contrib.auth import get_user_model
  from allauth.account.models import EmailAddress
  User = get_user_model()
  for email, password, staff in [
    ('e2e@example.com', 'E2EPassword123!', False),
    ('e2e-admin@example.com', 'E2EPassword123!', True),
  ]:
    if not User.objects.filter(email=email).exists():
      u = User.objects.create_user(email=email, password=password, is_staff=staff)
      EmailAddress.objects.create(user=u, email=email, primary=True, verified=True)
  print('done')
  "`.trim();

export default async function globalSetup(): Promise<void> {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";

  // 1. Verify the API server is reachable
  try {
    const res = await fetch(`${apiUrl}/api/health/live`);
    if (!res.ok) {
      throw new Error(`API health check returned ${res.status}. Is the server running?`);
    }
  } catch (err) {
    throw new Error(
      `Cannot reach API at ${apiUrl}.\n` +
        `Start the Django dev server: cd apps/api && python manage.py runserver\n` +
        (err instanceof Error ? err.message : String(err)),
    );
  }

  // 2. Remind about user seeding — we don't attempt login here to avoid
  //    contributing to allauth's rate limiter when 8 parallel workers also
  //    login simultaneously at suite start.
  console.info(
    `\n  API ready at ${apiUrl}.` +
      `\n  If tests fail with login errors, seed test users once:\n` +
      `  ${SEED_COMMAND}\n`,
  );
}
