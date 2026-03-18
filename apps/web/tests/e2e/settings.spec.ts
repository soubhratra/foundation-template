// @spec: E2E-02
import { test, expect } from "@playwright/test";

import { apiLogin, API_URL } from "./fixtures";

test.describe("GDPR data export", () => {
  test("account export endpoint returns 200 for authenticated user", async ({ request }) => {
    // @spec: E2E-02
    await apiLogin(request);

    const state = await request.storageState();
    const csrfToken = state.cookies.find((c) => c.name === "csrftoken")?.value ?? "";

    const res = await request.get(`${API_URL}/api/v1/account/export`, {
      headers: { "X-CSRFToken": csrfToken },
    });
    expect(res.status()).toBe(200);

    const body = (await res.json()) as Record<string, unknown>;
    expect(body).toHaveProperty("exported_at");
  });

  test('"Download export" button is present on the profile page', async ({ page, request }) => {
    // @spec: E2E-02
    // Use API login to avoid hitting the UI rate limit (5/m)
    await apiLogin(request);
    const state = await request.storageState();
    await page.context().addCookies(state.cookies);

    await page.goto("/profile");
    await expect(page.locator("text=Download export")).toBeVisible({ timeout: 5000 });
  });
});
