import * as p from "@clack/prompts";
import pc from "picocolors";
import { logger } from "./utils.js";
import {
  promptProjectName,
  promptFeatures,
  promptOutputDir,
  type SelectedFeatures,
} from "./prompts.js";
import { copyTemplate, getTemplateDir } from "./copy.js";
import { replaceInFiles, getReplacementMap } from "./transform.js";
import { writeEnvFile } from "./secrets.js";
import {
  removeAIModule,
  removeMobileApp,
  removeLandingApp,
  removeWebApp,
  removeBillingModule,
  removeObservability,
  removeEmailModule,
  removeSocialAuthModule,
} from "./remove.js";
import { runValidation } from "./validation-runner.js";
import { rollbackGeneration } from "./rollback.js";

/**
 * Project configuration collected from user prompts
 */
export interface ProjectConfig {
  projectName: string;
  features: SelectedFeatures;
  outputDir: string;
}

/**
 * Main CLI entry point
 * Orchestrates the interactive project scaffolding flow
 */
export async function main() {
  // Parse CLI flags
  const skipValidation = process.argv.includes("--skip-validation");

  // Parse --without billing / --without-billing flag
  const withoutArgs = process.argv.slice(2);
  const withoutIdx = withoutArgs.indexOf("--without");
  const withoutBillingFlag =
    (withoutIdx !== -1 && withoutArgs[withoutIdx + 1] === "billing") ||
    withoutArgs.includes("--without-billing");

  // Parse --without observability / --without-observability flag
  const withoutObservabilityFlag =
    (withoutIdx !== -1 && withoutArgs[withoutIdx + 1] === "observability") ||
    withoutArgs.includes("--without-observability");

  // Parse --without social-auth / --without-social-auth flag
  const withoutSocialAuthFlag =
    (withoutIdx !== -1 && withoutArgs[withoutIdx + 1] === "social-auth") ||
    withoutArgs.includes("--without-social-auth");

  // Track output directory for rollback
  let outputDir = "";

  try {
    // Welcome message
    p.intro(pc.bgCyan(pc.black(" create-foundation-app ")));

    logger.info("Welcome to Foundation Template CLI");
    logger.info("This tool will scaffold a new full-stack SaaS project");

    // Collect configuration via interactive prompts
    const projectName = await promptProjectName();
    const rawFeatures = await promptFeatures();
    // If --without billing flag was passed, remove billing from selected features
    // If --without observability flag was passed, remove observability from selected features
    const features = rawFeatures
      .filter((f) => !(withoutBillingFlag && f === "billing"))
      .filter((f) => !(withoutObservabilityFlag && f === "observability"))
      .filter((f) => !(withoutSocialAuthFlag && f === "social-auth"));
    outputDir = await promptOutputDir();

    // Build configuration object
    const config: ProjectConfig = {
      projectName,
      features,
      outputDir,
    };

    // Log collected config
    p.log.info(`Project: ${config.projectName}`);
    p.log.info(`Features: ${config.features.join(", ")}`);
    p.log.info(`Output: ${config.outputDir}`);

    // Generate project
    const templateDir = getTemplateDir();

    // Step 1: Copy template files
    const s1 = p.spinner();
    s1.start("Copying template files...");
    await copyTemplate(templateDir, config.outputDir);
    s1.stop(pc.green("✓ Template files copied"));

    // Step 2: Replace placeholders
    const s2 = p.spinner();
    s2.start("Transforming project files...");
    const replacements = getReplacementMap(config.projectName);
    await replaceInFiles(config.outputDir, replacements);
    s2.stop(pc.green("✓ Project files transformed"));

    // Step 3: Generate secrets
    const s3 = p.spinner();
    s3.start("Generating secrets...");
    await writeEnvFile(config.outputDir, config.projectName);
    s3.stop(pc.green("✓ Secrets generated"));

    // Step 4: Remove excluded features
    const s4 = p.spinner();
    s4.start("Removing excluded features...");
    if (!config.features.includes("ai")) {
      await removeAIModule(config.outputDir);
    }
    if (!config.features.includes("mobile")) {
      await removeMobileApp(config.outputDir);
    }
    if (!config.features.includes("landing")) {
      await removeLandingApp(config.outputDir);
    }
    if (!config.features.includes("web")) {
      await removeWebApp(config.outputDir);
    }
    if (!config.features.includes("billing")) {
      await removeBillingModule(config.outputDir);
    }
    if (!config.features.includes("observability")) {
      await removeObservability(config.outputDir);
    }
    if (!config.features.includes("email")) {
      await removeEmailModule(config.outputDir);
    }
    if (!config.features.includes("social-auth")) {
      await removeSocialAuthModule(config.outputDir);
    }
    s4.stop(pc.green("✓ Features configured"));

    // Step 5: Run validation (unless skipped)
    if (!skipValidation) {
      await runValidation(config.outputDir);
    } else {
      p.log.info(pc.yellow("⚠ Skipping validation (--skip-validation flag)"));
    }

    // Success
    p.outro(
      pc.green(`✓ Project "${config.projectName}" created successfully!`) +
        "\n\n" +
        pc.dim("Next steps:") +
        "\n" +
        pc.dim(`  cd ${config.outputDir}`) +
        "\n" +
        pc.dim("  git init  # Initialize fresh repository (no template history)") +
        "\n" +
        pc.dim("  # Before coding UI: run /ux-design-workflow (Design DNA First)") +
        "\n" +
        pc.dim("  # See: openspec/specs/foundation/ux-design.md") +
        "\n" +
        pc.dim(`  ${skipValidation ? "pnpm install" : "# Dependencies already installed"}`) +
        "\n" +
        pc.dim("  docker compose up -d") +
        "\n" +
        pc.dim(`  ${skipValidation ? "pnpm db:migrate" : "pnpm turbo db:migrate"}`) +
        "\n" +
        pc.dim("  pnpm dev") +
        "\n\n" +
        pc.dim("Visit:") +
        "\n" +
        pc.dim("  http://localhost:3000 (web)") +
        "\n" +
        pc.dim("  http://localhost:8000/api/docs (API)"),
    );
  } catch {
    p.log.error(pc.red("Generation failed"));
    if (outputDir) {
      await rollbackGeneration(outputDir);
    }
    p.cancel(pc.red("Project generation failed"));
    process.exit(1);
  }
}
