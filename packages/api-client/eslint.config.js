import { baseConfig } from "@repo/config-eslint";

export default [
  ...baseConfig,
  {
    files: ["src/**/*.{ts,tsx}", "tsup.config.ts"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
      },
    },
  },
];
