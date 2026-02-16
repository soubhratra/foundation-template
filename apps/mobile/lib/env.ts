/**
 * Environment variable validation for Expo mobile app.
 *
 * Import this module in app/_layout.tsx to validate env vars at startup.
 * Missing required vars will throw a clear error message instead of
 * producing cryptic runtime failures.
 */

interface MobileEnv {
  readonly EXPO_PUBLIC_API_URL: string;
}

function validateEnv(): MobileEnv {
  const required: Partial<MobileEnv> = {
    EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL,
  };

  const missing = Object.entries(required)
    .filter(([, value]) => !value)
    .map(([key]) => key);

  if (missing.length > 0) {
    throw new Error(
      [
        "",
        "=".repeat(60),
        "MISSING REQUIRED ENVIRONMENT VARIABLES",
        "=".repeat(60),
        ...missing.map((key) => `  - ${key}`),
        "",
        "Copy apps/mobile/.env.example to apps/mobile/.env",
        "and fill in the required values.",
        "=".repeat(60),
      ].join("\n"),
    );
  }

  return required as MobileEnv;
}

export const env = validateEnv();
