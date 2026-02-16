import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  target: "es2022",
  sourcemap: true,
  clean: true,
  dts: true,
  treeshake: true,
  splitting: false,
  minify: false,
  external: ["react", "react-native", "@tanstack/react-query"],
});
