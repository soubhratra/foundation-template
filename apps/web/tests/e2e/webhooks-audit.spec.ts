// @spec: E2E-09, E2E-10
import { test, expect } from "@playwright/test";

import { apiLogin, getCsrfToken, API_URL } from "./fixtures";

test.describe("Webhooks and audit log", () => {
  let orgSlug: string;

  test.beforeAll(async ({ request }) => {
    // Create a dedicated org for this test suite
    await apiLogin(request);
    const csrf = await getCsrfToken(request);
    const slug = `e2e-hooks-${Date.now()}`;
    const res = await request.post(`${API_URL}/api/v1/org/`, {
      data: { name: `Webhooks Test ${Date.now()}`, slug },
      headers: { "X-CSRFToken": csrf },
    });
    expect(res.status()).toBe(201);
    orgSlug = slug;
  });

  test.afterAll(async ({ request }) => {
    if (!orgSlug) return;
    await apiLogin(request);
    const csrf = await getCsrfToken(request);
    await request.delete(`${API_URL}/api/v1/org/${orgSlug}/`, {
      headers: { "X-CSRFToken": csrf },
    });
  });

  test("register endpoint appears in webhook list", async ({ request }) => {
    // @spec: E2E-09
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const createRes = await request.post(`${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints`, {
      data: { url: `https://example.com/webhook-${Date.now()}`, event_types: ["*"] },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    const created = (await createRes.json()) as { id: string; url: string; secret: string };
    expect(typeof created.id).toBe("string");
    // Secret is shown once on creation
    expect(typeof created.secret).toBe("string");

    // Appears in list
    const listRes = await request.get(`${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints`);
    expect(listRes.status()).toBe(200);
    const listBody = (await listRes.json()) as Array<{ id: string }>;
    expect(listBody.some((ep) => ep.id === created.id)).toBe(true);

    // Cleanup
    await request.delete(`${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints/${created.id}`, {
      headers: { "X-CSRFToken": await getCsrfToken(request) },
    });
  });

  test("delete endpoint removes it from list", async ({ request }) => {
    // @spec: E2E-09
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const createRes = await request.post(`${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints`, {
      data: { url: `https://example.com/to-delete-${Date.now()}`, event_types: ["*"] },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    const created = (await createRes.json()) as { id: string };

    const deleteRes = await request.delete(
      `${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints/${created.id}`,
      { headers: { "X-CSRFToken": await getCsrfToken(request) } },
    );
    expect(deleteRes.status()).toBe(204);

    const listRes = await request.get(`${API_URL}/api/v1/org/${orgSlug}/webhooks/endpoints`);
    const listBody = (await listRes.json()) as Array<{ id: string }>;
    expect(listBody.some((ep) => ep.id === created.id)).toBe(false);
  });

  test("admin sees audit log entries with actor and action", async ({ request }) => {
    // @spec: E2E-10
    // The test user is org owner (admin) — audit log access is granted
    await apiLogin(request);

    const res = await request.get(`${API_URL}/api/v1/org/${orgSlug}/audit-log`);
    expect(res.status()).toBe(200);

    const body = (await res.json()) as {
      items: Array<{ id: number; action: string; actor_email: string | null }>;
    };
    expect(Array.isArray(body.items)).toBe(true);

    if (body.items.length > 0) {
      const entry = body.items[0]!;
      expect(typeof entry.id).toBe("number");
      expect(typeof entry.action).toBe("string");
      // actor_email may be null if user was deleted; just verify the field exists
      expect("actor_email" in entry).toBe(true);
    }
  });
});
