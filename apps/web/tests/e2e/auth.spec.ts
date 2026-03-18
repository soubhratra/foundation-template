// @spec: E2E-01, DOCS-01, DOCS-02
import { test, expect } from "@playwright/test";

import { E2E_USER } from "./fixtures";

const UNIQUE_EMAIL = () => `e2e-signup-${Date.now()}@example.com`;

test.describe("Auth flows", () => {
  test("login with valid credentials redirects to dashboard", async ({ page }) => {
    // @spec: E2E-01
    await page.goto("/");
    await page.fill('input[type="email"]', E2E_USER.email);
    await page.fill('input[type="password"]', E2E_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("/dashboard");
    expect(page.url()).toContain("/dashboard");
  });

  test("login with invalid credentials shows inline error", async ({ page }) => {
    // @spec: E2E-01
    await page.goto("/");
    await page.fill('input[type="email"]', "wrong@example.com");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');
    // Stays on login page and shows error
    await expect(page.locator("text=Unable to sign in")).toBeVisible({ timeout: 5000 });
    expect(page.url()).not.toContain("/dashboard");
  });

  test("logout clears session and returns to login", async ({ page }) => {
    // @spec: E2E-01
    await page.goto("/");
    await page.fill('input[type="email"]', E2E_USER.email);
    await page.fill('input[type="password"]', E2E_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("/dashboard");

    // Open user dropdown and click Sign out
    await page.locator("header").getByRole("button").filter({ hasText: /@/ }).first().click();
    await page.click("text=Sign out");
    // After logout the app redirects to / (possibly with sessionExpired query params)
    await page.waitForURL(/^http:\/\/localhost:\d+\/(?!dashboard)/);
    expect(page.url()).not.toContain("/dashboard");
  });

  test("signup form submission shows email verification message", async ({ page }) => {
    // @spec: E2E-01
    await page.goto("/signup");
    const email = UNIQUE_EMAIL();
    await page.fill('input[name="name"]', "Test User");
    await page.fill('input[type="email"]', email);

    const passwordFields = page.locator('input[type="password"]');
    await passwordFields.nth(0).fill("SecurePassword123!");
    await passwordFields.nth(1).fill("SecurePassword123!");

    await page.click('button[type="submit"]');
    // Dev: ACCOUNT_EMAIL_VERIFICATION="optional" → redirects to dashboard after signup.
    // Prod: ACCOUNT_EMAIL_VERIFICATION="mandatory" → shows "Verify your email" message.
    // Either way, the user should leave the /signup page.
    await page.waitForFunction(() => !location.pathname.startsWith("/signup"), { timeout: 8000 });
  });
});
