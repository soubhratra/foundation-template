import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@repo/ui"],
  webpack: (config) => {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      "react-native$": "react-native-web",
    };
    const extensions = config.resolve.extensions ?? [".tsx", ".ts", ".js"];
    config.resolve.extensions = Array.from(
      new Set([...extensions, ".web.tsx", ".web.ts", ".web.js"]),
    );
    return config;
  },
};

export default nextConfig;
