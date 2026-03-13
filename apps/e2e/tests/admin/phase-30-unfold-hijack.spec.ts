/**
 * Phase 30 — Admin Backoffice browser verification
 *
 * Covers the 5 items that require a live browser and cannot be
 * verified by pytest alone:
 *  1. Unfold theme renders (not default Django admin)
 *  2. Impersonate button appears in user changelist for regular user
 *  3. Impersonation banner persists after hijack
 *  4. Release redirects back to /admin/accounts/user/
 *  5. No Impersonate button in row of staff user
 *
 * Note: HijackUserAdminMixin adds the Impersonate button to the changelist
 * (list view), NOT the change form. Tests target the list view accordingly.
 *
 * Prerequisites (set via env or .env.e2e):
 *   ADMIN_EMAIL        staff superuser email  (default: staff@dev.local)
 *   ADMIN_PASSWORD     staff superuser pass   (default: admin123)
 *   REGULAR_USER_EMAIL non-staff user email   (default: user@dev.local)
 *   STAFF_USER_EMAIL   another staff email    (default: staff2@dev.local)
 */

import { test, expect, gotoAdmin } from "./fixtures";

const regularEmail = process.env.REGULAR_USER_EMAIL ?? "user@dev.local";
const staffEmail2 = process.env.STAFF_USER_EMAIL ?? "staff2@dev.local";

// ─── helpers ──────────────────────────────────────────────────────────────────

/** Find the Impersonate button in the table row for a given user email. */
function impersonateBtnInRow(page: import("@playwright/test").Page, email: string) {
  return page
    .getByRole("row")
    .filter({ hasText: email })
    .getByRole("link", { name: /impersonat/i })
    .or(
      page
        .getByRole("row")
        .filter({ hasText: email })
        .getByRole("button", { name: /impersonat/i }),
    )
    .or(
      // hijack renders a <form> with submit inside the column
      page
        .getByRole("row")
        .filter({ hasText: email })
        .locator('[type="submit"][value*="mpersonat"], form[action*="hijack"] [type="submit"]'),
    );
}

// ─── 1. Unfold theme ──────────────────────────────────────────────────────────

test("unfold theme renders — not default Django admin", async ({ adminPage: page }) => {
  await gotoAdmin(page, "/admin/");

  // django-unfold uses Alpine.js (x-data attributes) throughout its templates.
  // The default Django admin has no Alpine.js at all.
  const alpineElements = await page.locator("[x-data]").count();
  const unfoldScript = await page.locator('script[src*="unfold"], link[href*="unfold"]').count();
  const hasUnfold = alpineElements > 0 || unfoldScript > 0;

  expect(
    hasUnfold,
    `Expected Unfold-themed admin (Alpine.js x-data elements: ${alpineElements}). Default Django admin detected instead.`,
  ).toBeTruthy();
});

// ─── 2. Impersonate button in changelist for regular user ─────────────────────

test("impersonate button visible in changelist for regular user", async ({ adminPage: page }) => {
  await gotoAdmin(page, "/admin/accounts/user/");

  const btn = impersonateBtnInRow(page, regularEmail);
  await expect(btn, `Impersonate button not found in row for ${regularEmail}`).toBeVisible({
    timeout: 10000,
  });
});

// ─── 3. Impersonation banner persists ────────────────────────────────────────

test("impersonation banner persists after hijack", async ({ adminPage: page }) => {
  await gotoAdmin(page, "/admin/accounts/user/");

  await impersonateBtnInRow(page, regularEmail).click();
  await page.waitForLoadState("networkidle");

  // After hijack, django-hijack injects a toolbar/notification into every page
  const banner = page.locator("#hijack-toolbar, .djhj, [data-hijack], .hijack-notification");
  const bannerByText = page.getByText(/you are impersonating/i);
  const hasBanner = (await banner.count()) > 0 || (await bannerByText.count()) > 0;
  expect(hasBanner, "Impersonation banner not found after hijack").toBeTruthy();
});

// ─── 4. Release redirects to user list ───────────────────────────────────────

test("release hijack redirects back to admin user list", async ({ adminPage: page }) => {
  await gotoAdmin(page, "/admin/accounts/user/");

  // Acquire impersonation
  await impersonateBtnInRow(page, regularEmail).click();
  await page.waitForLoadState("networkidle");

  // Release — hijack adds a release link/button somewhere on the page
  const releaseBtn = page
    .getByRole("link", { name: /release/i })
    .or(page.getByRole("button", { name: /release/i }))
    .or(page.locator('a[href*="release"], form[action*="release"] [type="submit"]'));
  await expect(releaseBtn.first()).toBeVisible({ timeout: 10000 });
  await releaseBtn.first().click();

  await page.waitForLoadState("networkidle");
  await expect(page).toHaveURL(/\/admin\/accounts\/user\//);
});

// ─── 5. No impersonate button for staff user ──────────────────────────────────

test("no impersonate button in changelist for staff user", async ({ adminPage: page }) => {
  await gotoAdmin(page, "/admin/accounts/user/");

  const staffRow = page.getByRole("row").filter({ hasText: staffEmail2 });
  if ((await staffRow.count()) === 0) {
    test.skip(true, `Staff user ${staffEmail2} not found — set STAFF_USER_EMAIL env var`);
    return;
  }

  const btn = impersonateBtnInRow(page, staffEmail2);
  await expect(btn).not.toBeVisible({ timeout: 5000 });
});
