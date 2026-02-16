import type { Metadata } from "next";

import { ThemeProvider } from "@/components/theme-provider";
import { env } from "@/config/env";
import { cn } from "@/lib/utils";
import "./globals.css";

import { buildApiBaseUrl } from "./base-url";
import { AppProviders } from "./providers";

export const metadata: Metadata = {
  title: "Foundation Template",
  description: "Full-stack SaaS starter kit",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const apiBaseUrl = buildApiBaseUrl(env.NEXT_PUBLIC_API_URL);

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn("min-h-screen bg-background font-sans antialiased")}>
        <ThemeProvider>
          <AppProviders baseUrl={apiBaseUrl}>{children}</AppProviders>
        </ThemeProvider>
      </body>
    </html>
  );
}
