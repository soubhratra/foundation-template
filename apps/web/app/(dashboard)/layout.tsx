import type { Metadata } from "next";
import type { ReactNode } from "react";

import { DashboardHeader } from "@/components/dashboard/header";
import { DashboardShellClient } from "@/components/dashboard/dashboard-shell-client";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { PastDueBanner } from "@/components/dashboard/past-due-banner";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { getServerApi } from "@/lib/api/server";

interface DashboardLayoutProps {
  readonly children: ReactNode;
}

export const metadata: Metadata = {
  title: "Foundation Template — Dashboard",
  description: "Unified control center for your SaaS foundation.",
};

// Disable static optimization for dashboard (uses client-side auth state)
export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: DashboardLayoutProps) {
  let isPastDue = false;
  try {
    const api = await getServerApi();
    const status = await api.getBillingStatus();
    isPastDue = status?.status === "past_due";
  } catch {
    // Never block layout render on billing failure
  }

  return (
    <DashboardShellClient>
      <SidebarProvider>
        <DashboardSidebar />
        <SidebarInset>
          <div className="flex min-h-screen flex-col bg-background">
            <DashboardHeader />
            {isPastDue && <PastDueBanner />}
            <main className="flex-1 p-6">
              <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">{children}</div>
            </main>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </DashboardShellClient>
  );
}
