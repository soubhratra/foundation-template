"use client";

import type { ReactNode } from "react";

import { useAuth } from "@repo/business-logic";

import { AuthSkeleton } from "@/components/skeletons/auth-skeleton";

interface AuthShellClientProps {
  readonly children: ReactNode;
}

export function AuthShellClient({ children }: AuthShellClientProps) {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <AuthSkeleton />;
  }

  return <>{children}</>;
}
