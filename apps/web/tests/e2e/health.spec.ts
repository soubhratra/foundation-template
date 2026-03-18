// @spec: E2E-04, CI-01, CI-02, CI-03
import { test, expect } from "@playwright/test";

import { API_URL } from "./fixtures";

test.describe("Health probes", () => {
  test("GET /api/health/live returns 200", async ({ request }) => {
    // @spec: E2E-04, CI-01, CI-02, CI-03
    const res = await request.get(`${API_URL}/api/health/live`);
    expect(res.status()).toBe(200);
  });

  test("GET /api/health/ready returns 200", async ({ request }) => {
    // @spec: E2E-04, CI-01, CI-02, CI-03
    const res = await request.get(`${API_URL}/api/health/ready`);
    expect(res.status()).toBe(200);
  });

  test("GET /api/health/startup returns 200", async ({ request }) => {
    // @spec: E2E-04, CI-01, CI-02, CI-03
    const res = await request.get(`${API_URL}/api/health/startup`);
    expect(res.status()).toBe(200);
  });
});
