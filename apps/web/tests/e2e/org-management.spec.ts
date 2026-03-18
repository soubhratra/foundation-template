// @spec: E2E-07
import { test, expect } from "@playwright/test";

import { apiLogin, getCsrfToken, API_URL } from "./fixtures";

test.describe("Org management", () => {
  /** Slugs of orgs created during this suite — cleaned up in afterAll. */
  const createdSlugs: string[] = [];

  test.beforeAll(async ({ request }) => {
    await apiLogin(request);
  });

  test.afterAll(async ({ request }) => {
    if (createdSlugs.length === 0) return;
    await apiLogin(request);
    const csrf = await getCsrfToken(request);
    for (const slug of createdSlugs) {
      await request
        .delete(`${API_URL}/api/v1/org/${slug}/`, {
          headers: { "X-CSRFToken": csrf },
        })
        .catch(() => {
          // Already deleted inline — ignore
        });
    }
  });

  test("create org appears in org list", async ({ request }) => {
    // @spec: E2E-07
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const uniqueName = `E2E Org ${Date.now()}`;
    const slug = `e2e-org-${Date.now()}`;
    const createRes = await request.post(`${API_URL}/api/v1/org/`, {
      data: { name: uniqueName, slug },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    createdSlugs.push(slug);

    const created = (await createRes.json()) as { slug: string; name: string };
    expect(created.name).toBe(uniqueName);

    // Fetch org to verify it exists
    const getRes = await request.get(`${API_URL}/api/v1/org/${slug}/`);
    expect(getRes.status()).toBe(200);
  });

  test("invite flow creates a pending invitation", async ({ request }) => {
    // @spec: E2E-07
    await apiLogin(request);
    const csrf = await getCsrfToken(request);

    const slug = `e2e-invite-${Date.now()}`;
    const createRes = await request.post(`${API_URL}/api/v1/org/`, {
      data: { name: `Invite Test ${Date.now()}`, slug },
      headers: { "X-CSRFToken": csrf },
    });
    expect(createRes.status()).toBe(201);
    createdSlugs.push(slug);

    // Send an invitation
    const inviteRes = await request.post(`${API_URL}/api/v1/org/${slug}/invitations/`, {
      data: { email: `invited-${Date.now()}@example.com` },
      headers: { "X-CSRFToken": await getCsrfToken(request) },
    });
    expect(inviteRes.status()).toBe(201);

    const invite = (await inviteRes.json()) as { status: string };
    expect(invite.status).toBe("pending");
  });
});
