import { reactNativeConfig } from "@repo/config-eslint/react-native";

/** @type {import("eslint").Linter.Config[]} */
export default [
  ...reactNativeConfig,
  {
    files: ["metro.config.js"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
];
