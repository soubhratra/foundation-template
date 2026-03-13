import { test as base, type Page } from "@playwright/test";

export type AdminFixtures = {
  adminPage: Page; // logged-in admin session
};

/** Navigate and dismiss Unfold's search overlay before interacting.
 *
 * Unfold renders a full-screen search overlay via Alpine.js x-show. In headless
 * Chromium the overlay can be rendered as display:flex (visible) before Alpine
 * initialises the x-show binding. We force it hidden via inline style so it
 * never intercepts pointer events during tests.
 */
export async function gotoAdmin(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  // Unfold has multiple Alpine.js full-screen overlays (search command, filter panel)
  // that render as display:flex before Alpine initialises their x-show bindings
  // in headless Chromium. Hide them all so they don't intercept pointer events.
  await page.evaluate(() => {
    const overlaySelectors = ['[x-data="searchCommand()"]', "#changelist-filter"];
    for (const selector of overlaySelectors) {
      const el = document.querySelector(selector) as HTMLElement | null;
      if (el) {
        el.style.setProperty("display", "none", "important");
        el.style.setProperty("pointer-events", "none", "important");
      }
    }
  });
}

export const test = base.extend<AdminFixtures>({
  adminPage: async ({ page }, use) => {
    const email = process.env.ADMIN_EMAIL ?? "staff@dev.local";
    const password = process.env.ADMIN_PASSWORD ?? "admin123";

    await page.goto("/admin/login/?next=/admin/");
    await page.fill('input[name="username"]', email);
    await page.fill('input[name="password"]', password);
    await page.click('[type="submit"]');
    // Wait for redirect away from login page; may land on /accounts/profile/ if
    // LOGIN_REDIRECT_URL is set — navigate explicitly to /admin/ in that case.
    await page.waitForLoadState("networkidle");
    if (!page.url().includes("/admin/")) {
      await page.goto("/admin/");
    }
    await page.waitForURL(/\/admin\//);
    // Dismiss Unfold's search overlay which opens on initial load
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    await use(page);
  },
});

export { expect } from "@playwright/test";
