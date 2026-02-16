/**
 * Environment variable validation for the Next.js web app.
 *
 * Import this module wherever runtime configuration is needed. Missing
 * variables fail fast with a descriptive error instead of creating subtle
 * runtime bugs.
 */

interface WebEnv {
  readonly NEXT_PUBLIC_API_URL: string;
}

function validateEnv(): WebEnv {
  const required: Partial<WebEnv> = {
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

  return required as WebEnv;
}

export const env = validateEnv();
