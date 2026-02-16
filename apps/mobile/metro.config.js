const path = require("node:path");
const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const workspaceRoot = path.resolve(__dirname, "..", "..");

const config = getDefaultConfig(projectRoot);

config.watchFolders = Array.from(
  new Set([...(config.watchFolders ?? []), path.resolve(workspaceRoot, "packages")]),
);

config.resolver = config.resolver ?? {};
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(workspaceRoot, "node_modules"),
];
config.resolver.extraNodeModules = {
  ...(config.resolver.extraNodeModules ?? {}),
  "@repo/ui": path.resolve(workspaceRoot, "packages", "ui"),
};
config.resolver.disableHierarchicalLookup = true;
config.resolver.unstable_enablePackageExports = true;

module.exports = config;
