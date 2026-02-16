import type { Metadata } from "next";
import { env } from "@/app/env";
import "./globals.css";

import { AppProviders } from "./providers";

export const metadata: Metadata = {
  title: "Foundation Template",
  description: "Full-stack SaaS starter kit",
};

const API_BASE_PATH = "/api/v1";

function buildApiBaseUrl(value: string): string {
  return `${value.replace(/\/$/, "")}${API_BASE_PATH}`;
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const apiBaseUrl = buildApiBaseUrl(env.NEXT_PUBLIC_API_URL);

  return (
    <html lang="en">
      <body>
        <AppProviders baseUrl={apiBaseUrl}>{children}</AppProviders>
      </body>
    </html>
  );
}
