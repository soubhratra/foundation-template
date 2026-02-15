import tseslint from "typescript-eslint";

export const baseConfig = tseslint.config(
  ...tseslint.configs.recommended,
  {
    ignores: [
      "**/dist/**",
      "**/.next/**",
      "**/.expo/**",
      "**/node_modules/**",
      "**/.turbo/**",
    ],
  },
);
