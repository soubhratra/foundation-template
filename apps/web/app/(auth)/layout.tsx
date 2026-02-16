import type { ReactNode } from "react";

import { MarketingHero } from "@/components/auth/marketing-hero";

interface AuthLayoutProps {
  readonly children: ReactNode;
}

export const metadata = {
  title: "Foundation Template — Access Portal",
  description: "Authenticate to unlock the dashboard experience.",
};

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background/70 to-background px-6 py-12">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_minmax(320px,400px)]">
        <MarketingHero />
        <div className="relative flex w-full items-center justify-center">
          <div className="w-full max-w-md rounded-3xl border border-border/60 bg-card/80 p-8 shadow-2xl backdrop-blur">
            <div className="mb-8 space-y-1 text-center">
              <p className="text-sm font-medium uppercase tracking-[0.3em] text-primary">
                Sign in
              </p>
              <h2 className="text-2xl font-semibold text-foreground">
                Ready when you are
              </h2>
              <p className="text-sm text-muted-foreground">
                Enter your template credentials to access the control center.
              </p>
            </div>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
