// @spec: E2E-08
import { test, expect } from "@playwright/test";

import { apiLogin, getCsrfToken, API_URL } from "./fixtures";

test.describe("API key lifecycle", () => {
  test("create key returns raw key value once", async ({ request }) => {
    // @spec: E2E-08
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const createRes = await request.post(`${API_URL}/api/v1/me/api-keys/`, {
      data: { name: `E2E Key ${Date.now()}`, scopes: ["read"] },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);

    const body = (await createRes.json()) as { key: string; id: string; prefix: string };
    // Raw key is returned only on creation
    expect(typeof body.key).toBe("string");
    expect(body.key.length).toBeGreaterThan(0);
    expect(typeof body.id).toBe("string");

    // Cleanup
    await request.delete(`${API_URL}/api/v1/me/api-keys/${body.id}/`, {
      headers: { "X-CSRFToken": await getCsrfToken(request) },
    });
  });

  test("key is masked (prefix only) in list after creation", async ({ request }) => {
    // @spec: E2E-08
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const createRes = await request.post(`${API_URL}/api/v1/me/api-keys/`, {
      data: { name: `E2E List Key ${Date.now()}`, scopes: ["read"] },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    const created = (await createRes.json()) as { id: string };

    // List endpoint returns masked keys (prefix, no raw key)
    const listRes = await request.get(`${API_URL}/api/v1/me/api-keys/`);
    expect(listRes.status()).toBe(200);
    const listResp = (await listRes.json()) as
      | { results: Array<Record<string, unknown>> }
      | Array<Record<string, unknown>>;
    const listBody = Array.isArray(listResp) ? listResp : listResp.results;
    const found = listBody.find((k) => k["id"] === created.id);
    expect(found).toBeDefined();
    expect(found!["key"]).toBeUndefined();
    expect(typeof found!["prefix"]).toBe("string");

    // Cleanup
    await request.delete(`${API_URL}/api/v1/me/api-keys/${created.id}/`, {
      headers: { "X-CSRFToken": await getCsrfToken(request) },
    });
  });

  test("delete removes key from list", async ({ request }) => {
    // @spec: E2E-08
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const createRes = await request.post(`${API_URL}/api/v1/me/api-keys/`, {
      data: { name: `E2E Delete Key ${Date.now()}`, scopes: ["read"] },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    const created = (await createRes.json()) as { id: string };

    const deleteRes = await request.delete(`${API_URL}/api/v1/me/api-keys/${created.id}/`, {
      headers: { "X-CSRFToken": await getCsrfToken(request) },
    });
    expect(deleteRes.status()).toBe(204);

    const listRes = await request.get(`${API_URL}/api/v1/me/api-keys/`);
    const listResp = (await listRes.json()) as
      | { results: Array<Record<string, unknown>> }
      | Array<Record<string, unknown>>;
    const listBody = Array.isArray(listResp) ? listResp : listResp.results;
    const found = listBody.find((k) => k["id"] === created.id);
    // Delete is a soft-delete: key is deactivated, not removed from list
    expect(!found || found["is_active"] === false).toBe(true);
  });
});
