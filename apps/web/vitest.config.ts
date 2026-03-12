import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/__tests__/setup.ts",
  },
  resolve: {
    alias: [
      // Map @/app/* to ./app/* (Next.js app directory) before the general @/* alias
      { find: /^@\/app(.*)/, replacement: path.resolve(__dirname, "./app") + "$1" },
      { find: "@", replacement: path.resolve(__dirname, "./src") },
    ],
  },
});
