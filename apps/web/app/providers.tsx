"use client";

import React, { Suspense, useEffect, useMemo, useState, type ReactNode } from "react";

import { AuthProvider, createWebTokenStorage } from "@repo/business-logic";

import { Toaster } from "@/components/ui/sonner";
import { useSessionToast } from "@/hooks/use-session-toast";

type DevtoolsComponent = React.ComponentType<{ initialIsOpen?: boolean }>;

function ReactQueryDevtoolsPortal() {
  const [Devtools, setDevtools] = useState<DevtoolsComponent | null>(null);

  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;
    let mounted = true;
    import("@tanstack/react-query-devtools")
      .then((m) => {
        if (mounted) setDevtools(() => m.ReactQueryDevtools as DevtoolsComponent);
      })
      .catch(() => null);
    return () => {
      mounted = false;
    };
  }, []);

  if (!Devtools) return null;
  return <Devtools />;
}

interface AppProvidersProps {
  readonly children: ReactNode;
  readonly baseUrl: string;
  readonly redirectBase?: string;
}

export function AppProviders({ children, baseUrl, redirectBase = "/login" }: AppProvidersProps) {
  const tokenStorage = useMemo(() => createWebTokenStorage(), []);

  return (
    <AuthProvider baseUrl={baseUrl} tokenStorage={tokenStorage}>
      <Suspense fallback={<>{children}</>}>
        <SessionBoundary redirectBase={redirectBase}>{children}</SessionBoundary>
      </Suspense>
      <ReactQueryDevtoolsPortal />
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
