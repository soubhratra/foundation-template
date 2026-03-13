import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["html", { open: "never" }], ["line"]],
  use: {
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "admin",
      testMatch: "**/admin/**/*.spec.ts",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: process.env.ADMIN_BASE_URL ?? "http://localhost:8000",
      },
    },
    {
      name: "web",
      testMatch: "**/web/**/*.spec.ts",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: process.env.WEB_BASE_URL ?? "http://localhost:3000",
      },
    },
  ],
});
