import { readFile, writeFile } from "fs/promises";
import { globby } from "globby";

/**
 * Convert kebab-case to Title Case
 *
 * @param kebab - Kebab-case string (e.g., "my-saas-app")
 * @returns Title Case string (e.g., "My Saas App")
 */
export function toTitleCase(kebab: string): string {
  return kebab
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Escape special regex characters in a string
 *
 * @param str - String to escape
 * @returns Escaped string safe for use in RegExp
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Build replacement map for project name transformation
 *
 * @param projectName - User's project name in kebab-case
 * @returns Record of placeholder -> replacement mappings
 */
export function getReplacementMap(projectName: string): Record<string, string> {
  return {
    // Root package name in package.json
    "foundation-template": projectName,

    // API package name in pyproject.toml
    "foundation-api": `${projectName}-api`,

    // Workspace package scope (e.g., @repo/ -> @my-app/)
    "@repo/": `@${projectName}/`,

    // Display name in README and marketing content
    "Foundation Template": toTitleCase(projectName),
  };
}

/**
 * Replace placeholders in all text files
 *
 * Transforms template-specific names to user's project name across:
 * - Package manifests (package.json, pyproject.toml)
 * - Source code (TypeScript, Python)
 * - Documentation (Markdown)
 * - Configuration (YAML)
 *
 * @param outputDir - Directory containing the copied template files
 * @param replacements - Map of placeholder -> replacement strings
 */
export async function replaceInFiles(
  outputDir: string,
  replacements: Record<string, string>,
): Promise<void> {
  // Find all text files that need transformation
  const files = await globby(
    [
      "**/package.json",
      "**/tsconfig.json",
      "**/pyproject.toml",
      "**/*.json", // Expo app.json, etc.
      "**/*.md",
      "**/*.ts",
      "**/*.tsx",
      "**/*.py",
      "**/*.yml",
      "**/*.yaml",
      "**/*.js",
      "**/Dockerfile",
      "**/Dockerfile.*",
      "**/.env.example",
    ],
    {
      cwd: outputDir,
      absolute: true,
      dot: true, // Include dotfiles and dot-directories (e.g., .github/)
      ignore: ["**/node_modules/**", "**/dist/**", "**/.venv/**"],
    },
  );

  // Apply replacements to each file
  for (const file of files) {
    let content = await readFile(file, "utf-8");

    // Apply all replacements using regex for global replacement
    for (const [placeholder, replacement] of Object.entries(replacements)) {
      const regex = new RegExp(escapeRegex(placeholder), "g");
      content = content.replace(regex, replacement);
    }

    await writeFile(file, content, "utf-8");
  }
}

/**
 * Strip all marker-fenced blocks from a string.
 *
 * Removes every region bounded by:
 *   <optional whitespace># MARKER_START<optional trailing text><newline>
 *   ...content...
 *   <optional whitespace># MARKER_END<optional trailing text><newline>
 *
 * Uses non-greedy matching so multiple blocks in one file are each stripped
 * independently. After stripping, collapses 3+ consecutive blank lines to 2.
 *
 * @param content - File content string
 * @param markerName - Marker prefix (e.g. "B2B" matches # B2B_START / # B2B_END)
 * @returns Stripped content
 */
export function stripMarkerBlocks(content: string, markerName: string): string {
  const regex = new RegExp(
    `[ \\t]*# ${markerName}_START[^\\n]*\\n[\\s\\S]*?[ \\t]*# ${markerName}_END[^\\n]*\\n`,
    "g",
  );
  let stripped = content.replace(regex, "");
  if (stripped !== content) {
    stripped = stripped.replace(/\n{3,}/g, "\n\n");
  }
  return stripped;
}
