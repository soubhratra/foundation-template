"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo } from "react";
import { Bell, ChevronRight } from "lucide-react";

import { useAuth } from "@repo/business-logic";

import { ThemeToggle } from "@/components/dashboard/theme-toggle";
import { MobileNavSheet, dashboardNavItems } from "@/components/dashboard/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarTrigger } from "@/components/ui/sidebar";

export function DashboardHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const activeItem = useMemo(() => {
    return dashboardNavItems.find((item) => matchesPath(pathname, item.href));
  }, [pathname]);

  const displayName = user?.full_name ?? "Operations Lead";
  const email = user?.email ?? "operator@example.com";

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/80 px-4 backdrop-blur lg:px-6">
      <div className="flex flex-1 items-center gap-3">
        <SidebarTrigger className="hidden lg:inline-flex" />
        <MobileNavSheet />
        <div className="space-y-0.5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
            <span>Workspace</span>
            <ChevronRight className="h-3 w-3" />
            <span>{activeItem?.title ?? "Dashboard"}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {activeItem?.description ?? "Monitor the heartbeat of your foundation."}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 rounded-full border"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-1 top-1 inline-flex h-2 w-2 rounded-full bg-primary" />
        </Button>
        <ThemeToggle />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-10 gap-2 rounded-full border px-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src={buildAvatarUrl(email)} alt={displayName} />
                <AvatarFallback>{getInitials(displayName)}</AvatarFallback>
              </Avatar>
              <div className="hidden flex-col text-left text-xs leading-tight lg:flex">
                <span className="font-medium text-foreground">{displayName}</span>
                <span className="text-muted-foreground">{email}</span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="text-xs font-normal text-muted-foreground">Signed in as</div>
              <div className="text-sm font-medium text-foreground">{email}</div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile">View profile</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings">Workspace settings</Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onSelect={(event) => {
                event.preventDefault();
                logout.mutate(undefined, { onSettled: () => router.replace("/") });
              }}
            >
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

function matchesPath(pathname: string | null, href: string): boolean {
  if (!pathname) {
    return false;
  }
  if (pathname === href) {
    return true;
  }
  return pathname.startsWith(`${href}/`);
}

function buildAvatarUrl(identifier: string) {
  return `https://avatar.vercel.sh/${encodeURIComponent(identifier)}`;
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
