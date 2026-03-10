import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { removeBillingModule } from "../src/remove.js";

describe("removeBillingModule", () => {
  let tmpDir: string;

  beforeEach(() => {
    // Create temp dir mirroring the project structure
    tmpDir = mkdtempSync(join(tmpdir(), "billing-removal-test-"));
    mkdirSync(join(tmpDir, "apps/api/apps/billing"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/api/config/settings"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/api/config"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/web/app/(dashboard)/billing"), {
      recursive: true,
    });

    // Write fixture files with billing markers
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      'INSTALLED_APPS = [\n    "apps.billing", # BILLING MODULE\n]\n' +
        "# ---------------------------------------------------------------------------\n" +
        "# BILLING MODULE\n" +
        "# ---------------------------------------------------------------------------\n" +
        'BILLING_ADAPTER: str = "apps.billing.adapters.StripeAdapter"\n' +
        "# ---------------------------------------------------------------------------\n" +
        "# END BILLING MODULE\n" +
        "# ---------------------------------------------------------------------------\n",
    );
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/development.py"),
      'DEBUG = True\nBILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"\n',
    );
    writeFileSync(
      join(tmpDir, "apps/api/config/urls.py"),
      "from apps.billing import webhooks as billing_views\n" +
        "urlpatterns = [\n" +
        "    # BILLING_START\n" +
        '    path("billing/webhook/", billing_views.stripe_webhook),\n' +
        "    # BILLING_END\n" +
        "]\n",
    );
    writeFileSync(join(tmpDir, "apps/web/billing.config.ts"), "export const billingConfig = {};");
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("removes apps/api/apps/billing/ directory", async () => {
    await removeBillingModule(tmpDir);
    expect(() => readFileSync(join(tmpDir, "apps/api/apps/billing/placeholder"))).toThrow();
  });

  it('removes "apps.billing" from INSTALLED_APPS in base.py', async () => {
    await removeBillingModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("apps.billing");
  });

  it("removes BILLING MODULE settings block from base.py", async () => {
    await removeBillingModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("BILLING MODULE");
    expect(content).not.toContain("BILLING_ADAPTER");
  });

  it("removes BILLING_ADAPTER line from development.py", async () => {
    await removeBillingModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/development.py"), "utf8");
    expect(content).not.toContain("BILLING_ADAPTER");
    expect(content).toContain("DEBUG = True"); // other lines preserved
  });

  it("removes BILLING_START/BILLING_END block and billing import from urls.py", async () => {
    await removeBillingModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/urls.py"), "utf8");
    expect(content).not.toContain("BILLING_START");
    expect(content).not.toContain("from apps.billing");
  });

  it("removes apps/web/app/(dashboard)/billing/ directory", async () => {
    await removeBillingModule(tmpDir);
    const { existsSync } = await import("node:fs");
    expect(existsSync(join(tmpDir, "apps/web/app/(dashboard)/billing"))).toBe(false);
  });

  it("removes apps/web/billing.config.ts", async () => {
    await removeBillingModule(tmpDir);
    const { existsSync } = await import("node:fs");
    expect(existsSync(join(tmpDir, "apps/web/billing.config.ts"))).toBe(false);
  });
});
