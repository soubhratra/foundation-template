"use client";

import React, { Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import posthog from "posthog-js";
import { PostHogProvider, usePostHog } from "posthog-js/react";
import { usePathname } from "next/navigation";

import { AuthProvider, createWebTokenStorage } from "@repo/business-logic";

import { Toaster } from "@/components/ui/sonner";
import { useSessionToast } from "@/hooks/use-session-toast";

function PostHogPageView() {
  const pathname = usePathname();
  const ph = usePostHog();
  const prevPathnameRef = useRef<string | null>(null);

  useEffect(() => {
    if (pathname && prevPathnameRef.current !== pathname) {
      prevPathnameRef.current = pathname;
      ph.capture("$pageview", { $current_url: window.location.href });
    }
  }, [pathname, ph]);

  return null;
}

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
    <PostHogProvider client={posthog}>
      <PostHogPageView />
      <AuthProvider baseUrl={baseUrl} tokenStorage={tokenStorage}>
        <Suspense fallback={<>{children}</>}>
          <SessionBoundary redirectBase={redirectBase}>{children}</SessionBoundary>
        </Suspense>
        <ReactQueryDevtoolsPortal />
      </AuthProvider>
    </PostHogProvider>
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
