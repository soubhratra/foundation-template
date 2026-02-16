"use client";

import { useMemo, type ReactNode } from "react";

import { AuthProvider, createWebTokenStorage } from "@repo/business-logic";

import { Toaster } from "@/components/ui/sonner";
import { useSessionToast } from "@/hooks/use-session-toast";

interface AppProvidersProps {
  readonly children: ReactNode;
  readonly baseUrl: string;
  readonly redirectBase?: string;
}

export function AppProviders({ children, baseUrl, redirectBase = "/login" }: AppProvidersProps) {
  const tokenStorage = useMemo(() => createWebTokenStorage(), []);

  return (
    <AuthProvider
      baseUrl={baseUrl}
      tokenStorage={tokenStorage}
      enableDevtools={process.env.NODE_ENV !== "production"}
    >
      <SessionBoundary redirectBase={redirectBase}>{children}</SessionBoundary>
    </AuthProvider>
  );
}

interface SessionBoundaryProps {
  readonly children: ReactNode;
  readonly redirectBase: string;
}

function SessionBoundary({ children, redirectBase }: SessionBoundaryProps) {
  useSessionToast({ redirectBase });

  return (
    <>
      {children}
      <Toaster richColors />
    </>
  );
}
