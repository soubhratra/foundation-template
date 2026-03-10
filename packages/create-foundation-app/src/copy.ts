import fse from "fs-extra";
const fs = fse;
import * as path from "path";
import { fileURLToPath } from "url";
import ignore, { Ignore } from "ignore";

/**
 * Copy template files to output directory with exclusions
 *
 * Excludes build artifacts, version control, and template-specific directories
 * to ensure generated project starts clean.
 *
 * @param templateDir - Root directory of the template (this monorepo)
 * @param outputDir - Target directory for the new project
 * @throws Error if output directory exists and is not empty
 * @throws Error if file copy operation fails
 */
export async function copyTemplate(templateDir: string, outputDir: string): Promise<void> {
  // Build exclusion list using ignore package
  const ig: Ignore = ignore.default();

  // Build artifacts and temporary files
  ig.add("node_modules");
  ig.add(".next");
  ig.add("__pycache__");
  ig.add("*.pyc");
  ig.add(".venv");
  ig.add("venv");
  ig.add("dist");
  ig.add("build");
  ig.add(".turbo");
  ig.add("coverage");
  ig.add(".pytest_cache");
  ig.add(".mypy_cache");
  ig.add(".ruff_cache");
  ig.add(".npm-cache"); // npm cache directory
  ig.add(".coverage"); // Python coverage data
  ig.add(".aider.tags.cache.v4"); // Aider cache directory

  // Environment and secrets (template uses .env.example)
  ig.add(".env");
  ig.add(".env.local");

  // Version control
  ig.add(".git");

  // Template-specific directories
  ig.add(".planning"); // Template planning context
  ig.add("packages/create-foundation-app"); // Don't copy CLI into generated project

  // Verify output directory is safe
  if (await fs.pathExists(outputDir)) {
    const files = await fs.readdir(outputDir);
    if (files.length > 0) {
      throw new Error(
        `Output directory "${outputDir}" is not empty. ` +
          "Please choose an empty or non-existent directory.",
      );
    }
  }

  // Copy files with filter function
  try {
    await fs.copy(templateDir, outputDir, {
      filter: (src) => {
        const relativePath = path.relative(templateDir, src);

        // Always copy root directory itself
        if (relativePath === "") {
          return true;
        }

        // Check against ignore rules
        return !ig.ignores(relativePath);
      },
    });
  } catch (error) {
    // Wrap error with context about which operation failed
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to copy template files: ${message}`);
  }
}

/**
 * Get the template directory (root of this monorepo)
 *
 * @returns Absolute path to template root
 */
export function getTemplateDir(): string {
  // From packages/create-foundation-app/dist/copy.js (after build), go up 3 levels
  // Use import.meta.url to get current file location in ESM
  const currentFile = fileURLToPath(import.meta.url);
  const currentDir = path.dirname(currentFile);
  return path.resolve(currentDir, "../../..");
}
