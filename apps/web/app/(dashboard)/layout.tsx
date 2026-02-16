import type { Metadata } from "next";
import type { ReactNode } from "react";

import { DashboardHeader } from "@/components/dashboard/header";
import { DashboardShellClient } from "@/components/dashboard/dashboard-shell-client";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";

interface DashboardLayoutProps {
  readonly children: ReactNode;
}

export const metadata: Metadata = {
  title: "Foundation Template — Dashboard",
  description: "Unified control center for your SaaS foundation.",
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <DashboardShellClient>
      <SidebarProvider>
        <DashboardSidebar />
        <SidebarInset>
          <div className="flex min-h-screen flex-col bg-background">
            <DashboardHeader />
            <main className="flex-1 p-6">
              <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
                {children}
              </div>
            </main>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </DashboardShellClient>
  );
}
