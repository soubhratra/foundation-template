import { baseConfig } from "@repo/config-eslint";

/**
 * Root ESLint config for monorepo
 * Each package/app has its own eslint.config.js that extends this
 */
export default [
  ...baseConfig,
  {
    ignores: [
      "**/dist/**",
      "**/.next/**",
      "**/.expo/**",
      "**/node_modules/**",
      "**/.turbo/**",
      "**/build/**",
      "**/.venv/**",
    ],
  },
];
