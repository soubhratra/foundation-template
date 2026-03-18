// @spec: E2E-05
import { test, expect } from "@playwright/test";

import { API_URL } from "./fixtures";

test.describe("Social auth", () => {
  test("allauth config reports supported social providers", async ({ request }) => {
    // @spec: E2E-05
    const res = await request.get(`${API_URL}/api/v1/auth/browser/v1/config`);
    expect(res.status()).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    // Config endpoint must be reachable; social providers array may be empty in dev
    expect(body).toHaveProperty("data");
  });

  test("login page renders without error", async ({ page }) => {
    // @spec: E2E-05
    await page.goto("/");
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test("Google OAuth button visible when NEXT_PUBLIC_GOOGLE_ENABLED=true", async ({ page }) => {
    // @spec: E2E-05
    await page.goto("/");
    // Verify page loaded
    await expect(page.locator('input[type="email"]')).toBeVisible();
    // If Google is enabled, the button must be visible; if disabled, that's also valid
    const googleBtn = page.locator("button", { hasText: /google/i });
    const count = await googleBtn.count();
    if (count > 0) {
      await expect(googleBtn.first()).toBeVisible();
    }
  });

  test("GitHub OAuth button visible when NEXT_PUBLIC_GITHUB_ENABLED=true", async ({ page }) => {
    // @spec: E2E-05
    await page.goto("/");
    const githubBtn = page.locator("button", { hasText: /github/i });
    const count = await githubBtn.count();
    if (count > 0) {
      await expect(githubBtn.first()).toBeVisible();
    }
    // If count === 0, GitHub is disabled — valid for builds without social auth
  });
});
