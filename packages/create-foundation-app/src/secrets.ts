import { randomBytes } from "crypto";
import { writeFile } from "fs/promises";
import * as path from "path";

/**
 * Generate a Django SECRET_KEY
 *
 * Creates a 50-character random string using the character set
 * recommended by Django documentation.
 *
 * @returns Random 50-character secret key
 */
export function generateDjangoSecretKey(): string {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)";
  const length = 50;

  const bytes = randomBytes(length);
  let result = "";

  for (let i = 0; i < length; i++) {
    // Use modulo to map random byte to character set
    const byte = bytes[i];
    if (byte !== undefined) {
      result += chars[byte % chars.length];
    }
  }

  return result;
}

/**
 * Generate a database password
 *
 * Creates a 32-character hexadecimal password suitable for
 * PostgreSQL authentication.
 *
 * @returns Random 32-character hex password
 */
export function generateDatabasePassword(): string {
  // 16 bytes = 32 hex characters
  return randomBytes(16).toString("hex");
}

/**
 * Write .env file with generated secrets
 *
 * Creates a .env file in the project root with:
 * - Unique Django SECRET_KEY
 * - Project-specific database credentials
 * - Development environment defaults
 *
 * @param outputDir - Root directory of the generated project
 * @param projectName - Name of the project (used in DATABASE_URL)
 */
export async function writeEnvFile(outputDir: string, projectName: string): Promise<void> {
  const secretKey = generateDjangoSecretKey();
  const dbPassword = generateDatabasePassword();

  const envContent = `# Django
SECRET_KEY=${secretKey}
DEBUG=True
DATABASE_URL=postgres://${projectName}:${dbPassword}@localhost:5432/${projectName}
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000

# Redis (for AI module Celery tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db

# OpenAI (for AI module - optional)
# OPENAI_API_KEY=your-key-here
`;

  const envPath = path.join(outputDir, ".env");
  await writeFile(envPath, envContent, "utf-8");
}
