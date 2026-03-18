// @spec: E2E-03
import { test, expect } from "@playwright/test";

import { loginViaUI } from "./fixtures";

test.describe("Billing page", () => {
  test.beforeEach(async ({ page }) => {
    await loginViaUI(page);
    await page.goto("/billing");
  });

  test("plan cards are visible on billing page", async ({ page }) => {
    // @spec: E2E-03
    // Billing page renders plan selection cards from billingConfig.plans
    await expect(page.getByRole("heading", { name: "Available Plans" })).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText("Pro", { exact: true }).first()).toBeVisible();
  });

  test("billing page loads without error", async ({ page }) => {
    // @spec: E2E-03
    await expect(page).toHaveURL("/billing");
    // No error boundary triggered
    await expect(page.locator("text=500")).not.toBeVisible();
    await expect(page.locator("text=Something went wrong")).not.toBeVisible();
  });

  test("upgrade CTA or portal button is present", async ({ page }) => {
    // @spec: E2E-03
    // Either an "Upgrade" / "Subscribe" button (no subscription) or "Manage billing" portal button
    await expect(page.getByRole("heading", { name: "Available Plans" })).toBeVisible({
      timeout: 10000,
    });
    const hasUpgrade = await page
      .locator("button, a")
      .filter({
        hasText: /upgrade|subscribe|manage billing|get started/i,
      })
      .count();
    expect(hasUpgrade).toBeGreaterThanOrEqual(1);
  });
});
