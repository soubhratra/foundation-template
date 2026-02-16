"use client";

import type { ReactNode } from "react";

import { useAuth } from "@repo/business-logic";

import { DashboardSkeleton } from "@/components/skeletons/dashboard-skeleton";

interface DashboardShellClientProps {
  readonly children: ReactNode;
}

export function DashboardShellClient({ children }: DashboardShellClientProps) {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return <>{children}</>;
}
