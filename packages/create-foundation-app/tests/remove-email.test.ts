import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { removeEmailModule } from "../src/remove.js";

describe("removeEmailModule", () => {
  let tmpDir: string;

  beforeEach(() => {
    // Create temp dir mirroring the project structure
    tmpDir = mkdtempSync(join(tmpdir(), "email-removal-test-"));
    mkdirSync(join(tmpDir, "apps/api/apps/notifications"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/api/config/settings"), { recursive: true });

    // Write fixture base.py with email sentinel comments and EMAIL MODULE block
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      "INSTALLED_APPS = [\n" +
        '    "anymail",  # EMAIL MODULE — remove this line to exclude email\n' +
        '    "apps.notifications",  # EMAIL MODULE — remove this line to exclude email\n' +
        "]\n" +
        "# ---------------------------------------------------------------------------\n" +
        "# EMAIL MODULE\n" +
        "# ---------------------------------------------------------------------------\n" +
        'RESEND_API_KEY: str = env("RESEND_API_KEY", default="")\n' +
        'EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"\n' +
        "# ---------------------------------------------------------------------------\n" +
        "# END EMAIL MODULE\n" +
        "# ---------------------------------------------------------------------------\n",
    );

    // Write fixture .env.example with email vars
    writeFileSync(
      join(tmpDir, "apps/api/.env.example"),
      "DATABASE_URL=postgres://...\n" +
        "# Email (Transactional)\n" +
        "RESEND_API_KEY=\n" +
        "DEFAULT_FROM_EMAIL=noreply@example.com\n",
    );

    // Create a minimal stub notifications app
    writeFileSync(join(tmpDir, "apps/api/apps/notifications/__init__.py"), "");
    writeFileSync(
      join(tmpDir, "apps/api/apps/notifications/apps.py"),
      "from django.apps import AppConfig\n\n\n" +
        "class NotificationsConfig(AppConfig):\n" +
        "    default_auto_field = 'django.db.models.BigAutoField'\n" +
        "    name = 'apps.notifications'\n",
    );
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("removes apps/api/apps/notifications/ directory", async () => {
    await removeEmailModule(tmpDir);
    const { existsSync } = await import("node:fs");
    expect(existsSync(join(tmpDir, "apps/api/apps/notifications"))).toBe(false);
  });

  it('removes "anymail" from INSTALLED_APPS in base.py', async () => {
    await removeEmailModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("anymail");
  });

  it('removes "apps.notifications" from INSTALLED_APPS in base.py', async () => {
    await removeEmailModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("apps.notifications");
  });

  it("removes EMAIL MODULE settings block from base.py", async () => {
    await removeEmailModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("EMAIL MODULE");
    expect(content).not.toContain("RESEND_API_KEY");
  });

  it("removes RESEND_API_KEY and DEFAULT_FROM_EMAIL from .env.example", async () => {
    await removeEmailModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/.env.example"), "utf8");
    expect(content).not.toContain("RESEND_API_KEY");
    expect(content).not.toContain("DEFAULT_FROM_EMAIL");
    expect(content).toContain("DATABASE_URL"); // other lines preserved
  });

  it("handles missing notifications directory gracefully (ENOENT)", async () => {
    // Remove it before the test so removeEmailModule gets ENOENT
    rmSync(join(tmpDir, "apps/api/apps/notifications"), { recursive: true });
    // Should not throw
    await expect(removeEmailModule(tmpDir)).resolves.toBeUndefined();
  });

  it("handles missing .env.example gracefully (ENOENT)", async () => {
    rmSync(join(tmpDir, "apps/api/.env.example"));
    // Should not throw
    await expect(removeEmailModule(tmpDir)).resolves.toBeUndefined();
  });
});
