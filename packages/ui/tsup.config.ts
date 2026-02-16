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
  external: ["react", "react-native", "react-native-web", "react-native-svg"],
});
