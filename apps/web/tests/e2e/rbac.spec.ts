// @spec: E2E-06
import { test, expect } from "@playwright/test";

import { apiLogin, E2E_ADMIN, API_URL } from "./fixtures";

test.describe("RBAC", () => {
  test("unauthenticated request to protected endpoint returns 401 or 403", async ({ request }) => {
    // @spec: E2E-06
    // Django Ninja returns 403 (Forbidden) for unauthenticated requests to permission-guarded
    // endpoints rather than 401 (Unauthorized). Both indicate the request is rejected.
    const res = await request.get(`${API_URL}/api/v1/me/api-keys`);
    expect([401, 403]).toContain(res.status());
  });

  test("regular authenticated user can access their own endpoints", async ({ request }) => {
    // @spec: E2E-06
    await apiLogin(request);
    const res = await request.get(`${API_URL}/api/v1/me/api-keys`);
    expect(res.status()).toBe(200);
  });

  test("regular user cannot access Django admin panel", async ({ page }) => {
    // @spec: E2E-06
    await page.goto("/");
    await page.fill('input[type="email"]', process.env.E2E_USER_EMAIL ?? "e2e@example.com");
    await page.fill('input[type="password"]', process.env.E2E_USER_PASSWORD ?? "E2EPassword123!");
    await page.click('button[type="submit"]');
    await page.waitForURL("/dashboard");

    // Regular user gets redirected to login by the Django admin
    await page.goto(`${API_URL}/admin/`);
    await expect(page).toHaveURL(/\/admin\/login\//);
  });

  test("staff user can access Django admin panel", async ({ page }) => {
    // @spec: E2E-06
    // e2e-admin@example.com is seeded with is_staff=True.
    // Allauth auto-generates username from email prefix: "e2e-admin".
    // Unfold admin uses <button type="submit">, not <input type="submit">.
    await page.goto(`${API_URL}/admin/login/?next=/admin/`);
    await page.fill('input[name="username"]', "e2e-admin");
    await page.fill('input[name="password"]', E2E_ADMIN.password);
    await page.locator('button[type="submit"]').click();
    // Successful login lands on the admin dashboard
    await expect(page).toHaveURL(/\/admin\//);
    await expect(page.locator("h1, #site-name").first()).toBeVisible();
  });
});
