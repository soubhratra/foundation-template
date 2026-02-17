import * as p from "@clack/prompts";
import pc from "picocolors";
import { handleError, logger } from "./utils.js";
import {
  promptProjectName,
  promptFeatures,
  promptOutputDir,
  type SelectedFeatures,
} from "./prompts.js";
import { copyTemplate, getTemplateDir } from "./copy.js";
import { replaceInFiles, getReplacementMap } from "./transform.js";
import { writeEnvFile } from "./secrets.js";
import { removeAIModule, removeMobileApp, removeLandingApp, removeWebApp } from "./remove.js";

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
  try {
    // Welcome message
    p.intro(pc.bgCyan(pc.black(" create-foundation-app ")));

    logger.info("Welcome to Foundation Template CLI");
    logger.info("This tool will scaffold a new full-stack SaaS project");

    // Collect configuration via interactive prompts
    const projectName = await promptProjectName();
    const features = await promptFeatures();
    const outputDir = await promptOutputDir();

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
    s4.stop(pc.green("✓ Features configured"));

    // Success
    p.outro(
      pc.green("✓ Project created successfully!") +
        "\n\n" +
        pc.dim("Next steps:") +
        "\n" +
        pc.dim(`  cd ${config.outputDir}`) +
        "\n" +
        pc.dim("  pnpm install") +
        "\n" +
        pc.dim("  docker compose up -d") +
        "\n" +
        pc.dim("  pnpm dev"),
    );
  } catch (error) {
    handleError(error);
  }
}
