import type { Metadata } from "next";
import type { ReactNode } from "react";

import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { ThemeToggle } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
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
    <SidebarProvider>
      <DashboardSidebar />
      <SidebarInset>
        <div className="flex min-h-screen flex-col bg-background">
          <header className="flex h-16 items-center justify-between border-b bg-background/80 px-6 backdrop-blur">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <SidebarTrigger />
              <span>Monitored in real-time</span>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Button size="sm">Deploy changes</Button>
            </div>
          </header>
          <main className="flex-1 p-6">
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
              {children}
            </div>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
