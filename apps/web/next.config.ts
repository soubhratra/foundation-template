import path from "node:path";

import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";

// In development the web app (localhost:3000) calls the Django API on a different
// port (localhost:8000). Production runs both behind the same origin/reverse proxy,
// so 'self' is sufficient there. We read NEXT_PUBLIC_API_URL so the CSP always
// matches whatever API URL is configured in .env.local.
const devApiUrl = isDev ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") : null;

// Security headers applied to all Next.js routes.
// CSP here is a STATIC policy (no nonces) — Next.js App Router generates
// inline hydration scripts that require 'unsafe-inline' when nonces are not
// injected via Next.js middleware. Django's CSP uses nonces (via django-csp);
// these are separate origins. No conflict.
//
// isDev adds 'unsafe-eval' for Next.js hot-module reload in development.
// HSTS is intentionally omitted — CDN/reverse proxy handles HTTPS upgrade in prod.
const connectSrc = [
  "'self'",
  "https://eu.i.posthog.com",
  "https://us.i.posthog.com",
  "https://hooks.stripe.com",
  ...(devApiUrl ? [devApiUrl] : []),
].join(" ");

const cspDirectives = [
  "default-src 'self'",
  isDev
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com"
    : "script-src 'self' 'unsafe-inline' https://js.stripe.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  `connect-src ${connectSrc}`,
  "frame-src https://js.stripe.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployments
  output: "standalone",

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: cspDirectives },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
    ];
  },

  // React Native-flavored packages ship untranspiled code, so let Next.js compile them.
  transpilePackages: ["@repo/ui", "@repo/business-logic", "@repo/validation"],
  webpack: (config) => {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      // Map react-native imports to react-native-web so shared primitives render in the browser.
      "react-native$": "react-native-web",
      "@repo/validation": path.resolve(__dirname, "../../packages/validation"),
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
