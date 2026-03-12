import * as p from "@clack/prompts";
import { validateProjectName, validateOutputDir } from "./validate.js";

/**
 * Selected features configuration
 */
export type SelectedFeatures = Array<
  "web" | "mobile" | "landing" | "ai" | "billing" | "observability" | "email"
>;

/**
 * Prompts for project name with npm package validation
 * Re-prompts on invalid input instead of exiting
 *
 * @returns The validated project name
 */
export async function promptProjectName(): Promise<string> {
  while (true) {
    const name = await p.text({
      message: "What is your project name?",
      placeholder: "my-saas-app",
      validate: (value) => {
        if (!value) {
          return "Project name is required";
        }

        const validation = validateProjectName(value);
        if (!validation.valid) {
          return validation.errors.join(", ");
        }
      },
    });

    // Handle cancellation (Ctrl+C)
    if (p.isCancel(name)) {
      p.cancel("Operation cancelled");
      process.exit(0);
    }

    // If we got here, validation passed
    return name as string;
  }
}

/**
 * Prompts for feature selection with multi-select
 * All platforms are checked by default
 *
 * @returns Array of selected features
 */
export async function promptFeatures(): Promise<SelectedFeatures> {
  const features = await p.multiselect({
    message: "Select platforms to include:",
    options: [
      {
        value: "web",
        label: "Web Application (Next.js)",
      },
      {
        value: "mobile",
        label: "Mobile Application (Expo)",
      },
      {
        value: "landing",
        label: "Landing Page (Static Next.js)",
      },
      {
        value: "ai",
        label: "AI Module (LangGraph + PGVector)",
      },
      {
        value: "billing",
        label: "Billing Module (Stripe payments + invoice PDFs)",
      },
      {
        value: "observability",
        label: "Observability (PostHog analytics + error tracking)",
      },
      {
        value: "email",
        label: "Transactional Email",
        hint: "Async email via Resend (anymail) with console fallback in dev",
      },
    ],
    initialValues: ["web", "mobile", "landing", "ai", "billing", "observability", "email"],
    required: true,
  });

  // Handle cancellation (Ctrl+C)
  if (p.isCancel(features)) {
    p.cancel("Operation cancelled");
    process.exit(0);
  }

  return features as SelectedFeatures;
}

/**
 * Prompts for output directory path with validation
 * Validates that directory doesn't exist or is empty
 *
 * @returns The validated output directory path
 */
export async function promptOutputDir(): Promise<string> {
  while (true) {
    const dirPath = await p.text({
      message: "Where should the project be created?",
      placeholder: "./my-saas-app",
      validate: (value) => {
        if (!value) {
          return "Output directory is required";
        }

        const validation = validateOutputDir(value);
        if (!validation.valid) {
          return validation.error;
        }
      },
    });

    // Handle cancellation (Ctrl+C)
    if (p.isCancel(dirPath)) {
      p.cancel("Operation cancelled");
      process.exit(0);
    }

    // If we got here, validation passed
    return dirPath as string;
  }
}
