import validateNpmPackageName from "validate-npm-package-name";
import fs from "fs-extra";
import path from "path";

/**
 * Validation result for project names
 */
export interface ProjectNameValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Validation result for output directories
 */
export interface OutputDirValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validates a project name according to npm package name rules
 * Uses strict validation (validForNewPackages)
 *
 * @param name - The project name to validate
 * @returns Validation result with errors if invalid
 */
export function validateProjectName(name: string): ProjectNameValidationResult {
  const result = validateNpmPackageName(name);

  if (result.validForNewPackages) {
    return { valid: true, errors: [] };
  }

  // Collect all errors and warnings into a single array
  const errors: string[] = [];

  if (result.errors) {
    errors.push(...result.errors);
  }

  if (result.warnings) {
    errors.push(...result.warnings);
  }

  return {
    valid: false,
    errors,
  };
}

/**
 * Validates an output directory path
 * Checks if directory exists and whether it's empty
 *
 * @param dirPath - The directory path to validate
 * @returns Validation result with error if directory exists and is not empty
 */
export function validateOutputDir(dirPath: string): OutputDirValidationResult {
  try {
    // Resolve to absolute path
    const absolutePath = path.resolve(dirPath);

    // Check if directory exists
    if (fs.existsSync(absolutePath)) {
      // Check if it's a directory
      const stats = fs.statSync(absolutePath);
      if (!stats.isDirectory()) {
        return {
          valid: false,
          error: "Path exists but is not a directory",
        };
      }

      // Check if directory is empty
      const files = fs.readdirSync(absolutePath);
      if (files.length > 0) {
        return {
          valid: false,
          error: `Directory "${dirPath}" is not empty. Please choose a different path or remove existing files.`,
        };
      }
    }

    // Directory doesn't exist or is empty - valid
    return { valid: true };
  } catch (error) {
    return {
      valid: false,
      error: error instanceof Error ? error.message : "Unknown error validating directory",
    };
  }
}
