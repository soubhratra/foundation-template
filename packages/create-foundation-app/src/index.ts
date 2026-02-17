import * as p from "@clack/prompts";
import pc from "picocolors";
import { handleError, logger } from "./utils.js";

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

    // Placeholder for prompts (Wave 2 will add prompt calls)
    // const projectName = await promptProjectName();
    // const features = await promptFeatures();
    // const outputDir = await promptOutputDir();

    // Log collected config
    p.log.info("Configuration collected (placeholder)");

    // Next steps
    p.outro(pc.green("Setup complete! Next: implement template generation"));
  } catch (error) {
    handleError(error);
  }
}
