import type { Metadata } from "next";
import "@/app/env";
import "./globals.css";

export const metadata: Metadata = {
  title: "Foundation Template",
  description: "Full-stack SaaS starter kit",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
