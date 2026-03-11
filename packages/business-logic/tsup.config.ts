import { writeFileSync, readFileSync } from "node:fs";
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
  async onSuccess() {
    // Prepend "use client" to dist files so Next.js App Router treats this
    // package as client-only (required because this package uses React hooks).
    for (const file of ["dist/index.js", "dist/index.cjs"]) {
      const original = readFileSync(file, "utf8");
      writeFileSync(file, `"use client";\n${original}`);
    }
  },
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
