const path = require("node:path");
const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const workspaceRoot = path.resolve(__dirname, "..", "..");

const config = getDefaultConfig(projectRoot);

const sharedPackages = ["ui", "business-logic", "validation"];

// Watch individual shared package directories so Metro reloads when UI/business logic changes.
config.watchFolders = Array.from(
  new Set([
    ...(config.watchFolders ?? []),
    ...sharedPackages.map((pkg) => path.resolve(workspaceRoot, "packages", pkg)),
  ]),
);

config.resolver = config.resolver ?? {};
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(workspaceRoot, "node_modules"),
];
// Explicitly alias workspace packages to avoid pnpm symlink resolution issues.
config.resolver.extraNodeModules = {
  ...(config.resolver.extraNodeModules ?? {}),
  "@repo/ui": path.resolve(workspaceRoot, "packages", "ui"),
  "@repo/business-logic": path.resolve(workspaceRoot, "packages", "business-logic"),
  "@repo/validation": path.resolve(workspaceRoot, "packages", "validation"),
};
config.resolver.disableHierarchicalLookup = true;
config.resolver.unstable_enablePackageExports = true;

module.exports = config;
