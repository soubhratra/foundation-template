import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  outDir: "dist",
  sourcemap: true,
  clean: true,
  dts: true,
  format: ["esm", "cjs"],
  splitting: false,
  minify: false,
  treeshake: true,
  target: "es2020",
  platform: "neutral",
  tsconfig: "tsconfig.json",
  external: [
    "react",
    "react-native",
    "@tanstack/react-query",
    "@tanstack/react-query-devtools",
    "@repo/api-client",
    "@repo/validation",
  ],
});
