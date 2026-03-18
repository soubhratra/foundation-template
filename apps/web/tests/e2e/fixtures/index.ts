import type { APIRequestContext, Page } from "@playwright/test";

/** API server URL — separate port from the Next.js web app. */
export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export const E2E_USER = {
  email: process.env.E2E_USER_EMAIL ?? "e2e@example.com",
  password: process.env.E2E_USER_PASSWORD ?? "E2EPassword123!",
};

export const E2E_ADMIN = {
  email: process.env.E2E_ADMIN_EMAIL ?? "e2e-admin@example.com",
  password: process.env.E2E_ADMIN_PASSWORD ?? "E2EPassword123!",
};

/**
 * Log in via the allauth headless browser API.
 * After this call, `request` holds valid session + CSRF cookies.
 */
export async function apiLogin(
  request: APIRequestContext,
  credentials: { email: string; password: string } = E2E_USER,
): Promise<void> {
  // Prime the CSRF cookie
  await request.get(`${API_URL}/api/v1/auth/browser/v1/config`);
  const state = await request.storageState();
  const csrfToken = state.cookies.find((c) => c.name === "csrftoken")?.value ?? "";

  const res = await request.post(`${API_URL}/api/v1/auth/browser/v1/auth/login`, {
    data: { email: credentials.email, password: credentials.password },
    headers: { "X-CSRFToken": csrfToken },
  });

  if (!res.ok()) {
    throw new Error(`apiLogin failed: ${res.status()} — ${await res.text()}`);
  }
}

/**
 * Log in via the login page UI.
 * After this call, `page` is on `/dashboard`.
 */
export async function loginViaUI(
  page: Page,
  credentials: { email: string; password: string } = E2E_USER,
): Promise<void> {
  await page.goto("/");
  await page.fill('input[type="email"]', credentials.email);
  await page.fill('input[type="password"]', credentials.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("/dashboard");
}

/** Return a fresh CSRF token from the active `request` session. */
export async function getCsrfToken(request: APIRequestContext): Promise<string> {
  const state = await request.storageState();
  return state.cookies.find((c) => c.name === "csrftoken")?.value ?? "";
}
