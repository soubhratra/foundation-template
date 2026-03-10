import fse from "fs-extra";
const { remove, pathExists } = fse;
import { logger } from "./utils.js";

/**
 * Rollback project generation on error
 *
 * Deletes the output directory to clean up partial generation.
 * Errors during cleanup are logged but not thrown (already in error state).
 *
 * @param outputDir - Generated project directory to delete
 */
export async function rollbackGeneration(outputDir: string): Promise<void> {
  try {
    logger.info("Rolling back generation...");

    // Check if directory exists before attempting removal
    const exists = await pathExists(outputDir);
    if (!exists) {
      logger.info("  ✓ Output directory doesn't exist (nothing to clean up)");
      return;
    }

    // Remove the entire output directory
    await remove(outputDir);
    logger.info(`  ✓ Removed ${outputDir}`);
    logger.info(
      "Cleanup complete. You may need to manually delete the directory if removal failed.",
    );
  } catch (error) {
    // Don't throw - we're already in an error state
    // Just log the cleanup failure
    logger.warning(
      `Failed to clean up ${outputDir}: ${error}. You may need to delete it manually.`,
    );
  }
}
