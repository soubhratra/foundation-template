import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, accessSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { removeSocialAuthModule } from "../src/remove.js";

describe("removeSocialAuthModule", () => {
  let tmpDir: string;

  beforeEach(() => {
    // Create temp dir mirroring the project structure
    tmpDir = mkdtempSync(join(tmpdir(), "social-auth-removal-test-"));
    mkdirSync(join(tmpDir, "apps/api/config/settings"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/api"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/web/src/components/auth"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/web/app/(auth)"), { recursive: true });
    mkdirSync(join(tmpDir, "apps/mobile/app/(auth)"), { recursive: true });

    // Write fixture base.py with SOCIAL AUTH MODULE block and sentinel-commented lines
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      "INSTALLED_APPS = [\n" +
        '    "allauth.socialaccount",\n' +
        '    "_social_installed",  # SOCIAL AUTH MODULE\n' +
        "]\n" +
        "# ---------------------------------------------------------------------------\n" +
        "# SOCIAL AUTH MODULE\n" +
        "# ---------------------------------------------------------------------------\n" +
        'GOOGLE_CLIENT_ID: str = env("GOOGLE_CLIENT_ID", default="")\n' +
        "SOCIALACCOUNT_PROVIDERS: dict = {}\n" +
        "# ---------------------------------------------------------------------------\n" +
        "# END SOCIAL AUTH MODULE\n" +
        "# ---------------------------------------------------------------------------\n",
    );

    // Write fixture .env.example with social auth vars
    writeFileSync(
      join(tmpDir, "apps/api/.env.example"),
      "DATABASE_URL=postgres://...\n" +
        "# Social Auth (Google)\n" +
        "GOOGLE_CLIENT_ID=\n" +
        "GOOGLE_CLIENT_SECRET=\n" +
        "# Social Auth (GitHub)\n" +
        "GITHUB_CLIENT_ID=\n" +
        "GITHUB_CLIENT_SECRET=\n" +
        "# Social Auth (Apple Sign In)\n" +
        "APPLE_CLIENT_ID=\n" +
        "APPLE_TEAM_ID=\n" +
        "APPLE_KEY_ID=\n" +
        "APPLE_PRIVATE_KEY=\n",
    );

    // Write fixture web login page with social buttons import
    writeFileSync(
      join(tmpDir, "apps/web/app/(auth)/page.tsx"),
      'import { SocialButtons } from "@/components/auth/social-buttons";\n' +
        "export default function LoginPage() {\n" +
        "  return <SocialButtons />;\n" +
        "}\n",
    );

    // Write fixture social-buttons component
    writeFileSync(
      join(tmpDir, "apps/web/src/components/auth/social-buttons.tsx"),
      "export function SocialButtons() { return null; }\n",
    );

    // Write fixture mobile sign-in screen with Apple button
    writeFileSync(
      join(tmpDir, "apps/mobile/app/(auth)/sign-in.tsx"),
      "import * as AppleAuthentication from 'expo-apple-authentication';\n" +
        "export default function SignIn() {\n" +
        "  return (\n" +
        "    <AppleAuthentication.AppleAuthenticationButton />\n" +
        "  );\n" +
        "}\n",
    );
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("removes allauth.socialaccount from INSTALLED_APPS in base.py (unconditional)", async () => {
    // Write a fixture that has the line WITHOUT any sentinel comment
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      'INSTALLED_APPS = [\n    "allauth.account",\n    "allauth.socialaccount",\n]\n',
    );
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("allauth.socialaccount");
  });

  it("removes allauth.socialaccount from INSTALLED_APPS in base.py (with sentinel comment)", async () => {
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      'INSTALLED_APPS = [\n    "allauth.socialaccount",  # SOCIAL AUTH MODULE\n]\n',
    );
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("allauth.socialaccount");
  });

  it("removes SOCIAL AUTH MODULE fenced block from base.py", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("SOCIAL AUTH MODULE");
    expect(content).not.toContain("SOCIALACCOUNT_PROVIDERS");
  });

  it("removes SOCIAL AUTH MODULE sentinel-commented lines from INSTALLED_APPS", async () => {
    writeFileSync(
      join(tmpDir, "apps/api/config/settings/base.py"),
      "INSTALLED_APPS = [\n" +
        '    "django.contrib.auth",\n' +
        '    "_social_installed: list[str] = []",  # SOCIAL AUTH MODULE\n' +
        "]\n",
    );
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/config/settings/base.py"), "utf8");
    expect(content).not.toContain("SOCIAL AUTH MODULE");
  });

  it("removes GOOGLE_CLIENT_ID from .env.example", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/.env.example"), "utf8");
    expect(content).not.toContain("GOOGLE_CLIENT_ID");
    expect(content).toContain("DATABASE_URL"); // other lines preserved
  });

  it("removes GITHUB_CLIENT_ID from .env.example", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/.env.example"), "utf8");
    expect(content).not.toContain("GITHUB_CLIENT_ID");
  });

  it("removes APPLE env vars from .env.example", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/api/.env.example"), "utf8");
    expect(content).not.toContain("APPLE_CLIENT_ID");
    expect(content).not.toContain("APPLE_TEAM_ID");
    expect(content).not.toContain("APPLE_KEY_ID");
    expect(content).not.toContain("APPLE_PRIVATE_KEY");
  });

  it("handles missing .env.example without throwing", async () => {
    rmSync(join(tmpDir, "apps/api/.env.example"));
    await expect(removeSocialAuthModule(tmpDir)).resolves.toBeUndefined();
  });

  it("removes social buttons import from web login page", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/web/app/(auth)/page.tsx"), "utf8");
    expect(content).not.toContain("SocialButtons");
  });

  it("removes Apple Sign In button from mobile sign-in", async () => {
    await removeSocialAuthModule(tmpDir);
    const content = readFileSync(join(tmpDir, "apps/mobile/app/(auth)/sign-in.tsx"), "utf8");
    expect(content).not.toContain("AppleAuthentication.AppleAuthenticationButton");
  });

  it("deletes social-buttons.tsx component file", async () => {
    await removeSocialAuthModule(tmpDir);
    expect(() =>
      accessSync(join(tmpDir, "apps/web/src/components/auth/social-buttons.tsx")),
    ).toThrow();
  });
});
