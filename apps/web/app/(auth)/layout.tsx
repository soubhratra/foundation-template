import type { ReactNode } from "react";

import { AuthShellClient, MarketingHero } from "@/components/auth";

interface AuthLayoutProps {
  readonly children: ReactNode;
}

export const metadata = {
  title: "Foundation Template — Access Portal",
  description: "Authenticate to unlock the dashboard experience.",
};

// Disable static optimization for auth pages (check session state dynamically)
export const dynamic = "force-dynamic";

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <AuthShellClient>
      <div className="min-h-screen bg-gradient-to-b from-background via-background/70 to-background px-6 py-12">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_minmax(320px,420px)]">
          <MarketingHero />
          <div className="relative flex w-full items-center justify-center px-2 py-8 sm:px-6">
            <div className="w-full max-w-md">{children}</div>
          </div>
        </div>
      </div>
    </AuthShellClient>
  );
}
