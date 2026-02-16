"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, LayoutDashboard, Menu, Settings, UserRound } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";

export interface DashboardNavItem {
  readonly title: string;
  readonly href: string;
  readonly description: string;
  readonly icon: LucideIcon;
  readonly badge?: string;
}

export const dashboardNavItems: DashboardNavItem[] = [
  {
    title: "Dashboard",
    href: "/dashboard",
    description: "System health and KPI rollups",
    icon: LayoutDashboard,
  },
  {
    title: "Profile",
    href: "/profile",
    description: "Account details and identity",
    icon: UserRound,
  },
  {
    title: "Settings",
    href: "/settings",
    description: "Security, notifications, tokens",
    icon: Settings,
  },
  {
    title: "Activity",
    href: "/activity",
    description: "Audit log & deployments",
    icon: Activity,
    badge: "Live",
  },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="gap-1 border-b border-sidebar-border pb-4">
        <p className="text-xs uppercase tracking-widest text-muted-foreground">
          Foundation
        </p>
        <h2 className="text-lg font-semibold text-foreground">Control Center</h2>
        <p className="text-xs text-muted-foreground">
          Monitor your SaaS backbone in real time.
        </p>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {dashboardNavItems.map((item) => {
                const isActive = matchesPath(pathname, item.href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={isActive} tooltip={item.title}>
                      <Link href={item.href} className="flex min-w-0 flex-col gap-0">
                        <div className="flex items-center gap-2">
                          <item.icon className="h-4 w-4" />
                          <span className="font-medium">{item.title}</span>
                        </div>
                        <span className="text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
                          {item.description}
                        </span>
                      </Link>
                    </SidebarMenuButton>
                    {item.badge ? (
                      <SidebarMenuBadge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-300">
                        {item.badge}
                      </SidebarMenuBadge>
                    ) : null}
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarSeparator />
      <SidebarFooter className="gap-3 border-t border-sidebar-border pt-4">
        <div className="w-full rounded-xl border border-dashed bg-sidebar-accent/20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Workspace status
          </p>
          <div className="mt-2 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Launch window</p>
              <p className="text-xs text-muted-foreground">All systems nominal</p>
            </div>
            <Badge variant="outline" className="border-emerald-400 text-emerald-600 dark:text-emerald-300">
              Healthy
            </Badge>
          </div>
        </div>
        <Button variant="outline" className="w-full" asChild>
          <Link href="/settings">Workspace settings</Link>
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}

export function MobileNavSheet() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10 rounded-full border lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[320px] p-0">
        <SheetHeader className="border-b px-6 py-4 text-left">
          <SheetTitle>Foundation workspace</SheetTitle>
          <SheetDescription>Navigate between control surfaces.</SheetDescription>
        </SheetHeader>
        <div className="space-y-1 px-4 py-4">
          {dashboardNavItems.map((item) => {
            const isActive = matchesPath(pathname, item.href);
            return (
              <Button
                key={item.href}
                variant={isActive ? "default" : "ghost"}
                className="h-auto w-full justify-start px-4 py-3"
                asChild
              >
                <Link
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="flex w-full items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="h-4 w-4" />
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-medium">{item.title}</span>
                      <span className="text-xs text-muted-foreground">{item.description}</span>
                    </div>
                  </div>
                  {item.badge ? (
                    <Badge variant="outline" className="text-xs">
                      {item.badge}
                    </Badge>
                  ) : null}
                </Link>
              </Button>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
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
