import * as p from "@clack/prompts";
import pc from "picocolors";
import { handleError, logger } from "./utils.js";
import {
  promptProjectName,
  promptFeatures,
  promptOutputDir,
  type SelectedFeatures,
} from "./prompts.js";

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

    // Next steps
    p.outro(pc.green("Configuration collected! Next: implement template generation (Wave 2)"));
  } catch (error) {
    handleError(error);
  }
}
