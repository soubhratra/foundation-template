/**
 * Environment variable validation for Next.js web app.
 *
 * Import this module in app/layout.tsx to validate env vars at startup.
 * Missing required vars will throw a clear error message instead of
 * producing cryptic runtime failures.
 */

function validateEnv() {
  const required: Record<string, string | undefined> = {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
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
        "Copy apps/web/.env.example to apps/web/.env.local",
        "and fill in the required values.",
        "=".repeat(60),
      ].join("\n"),
    );
  }

  return required as Record<string, string>;
}

export const env = validateEnv();
