import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // React Native-flavored packages ship untranspiled code, so let Next.js compile them.
  transpilePackages: ["@repo/ui", "@repo/business-logic"],
  webpack: (config) => {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      // Map react-native imports to react-native-web so shared primitives render in the browser.
      "react-native$": "react-native-web",
    };
    const extensions = config.resolve.extensions ?? [".tsx", ".ts", ".js"];
    config.resolve.extensions = Array.from(
      new Set([
        ...extensions,
        ".web.tsx",
        ".web.ts",
        ".web.js",
        ".native.tsx",
        ".native.ts",
        ".native.js",
      ]),
    );
    return config;
  },
};

export default nextConfig;
