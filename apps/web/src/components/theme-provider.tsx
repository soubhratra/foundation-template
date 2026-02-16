"use client";

import {
  ThemeProvider as NextThemesProvider,
  type ThemeProviderProps,
} from "next-themes";

type ProviderProps = ThemeProviderProps;

function ThemeProvider({ children, ...props }: ProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}

export { ThemeProvider };
export { ThemeToggle } from "@/components/dashboard/theme-toggle";
export { Toaster } from "@/components/ui/sonner";
