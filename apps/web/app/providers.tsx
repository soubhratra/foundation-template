"use client";

import { useMemo, type ReactNode } from "react";

import { AuthProvider, createWebTokenStorage } from "@repo/business-logic";

interface AppProvidersProps {
  readonly children: ReactNode;
  readonly baseUrl: string;
}

export function AppProviders({ children, baseUrl }: AppProvidersProps) {
  const tokenStorage = useMemo(() => createWebTokenStorage(), []);

  return (
    <AuthProvider
      baseUrl={baseUrl}
      tokenStorage={tokenStorage}
      enableDevtools={process.env.NODE_ENV !== "production"}
    >
      {children}
    </AuthProvider>
  );
}
