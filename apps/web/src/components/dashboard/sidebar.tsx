"use client";

import Link from "next/link";
import {
  BarChart3,
  Database,
  LayoutDashboard,
  Settings2,
  ShieldCheck,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";

const primaryNav = [
  { title: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { title: "Customers", href: "/dashboard/customers", icon: Users },
  { title: "Billing", href: "/dashboard/billing", icon: BarChart3 },
  { title: "Security", href: "/dashboard/security", icon: ShieldCheck },
];

const dataNav = [
  { title: "Warehouse", href: "/dashboard/data", icon: Database },
  { title: "Settings", href: "/dashboard/settings", icon: Settings2 },
];

export function DashboardSidebar() {
  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="gap-1 border-b border-sidebar-border pb-4">
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Foundation</p>
        <h2 className="text-lg font-semibold text-foreground">Control Center</h2>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {primaryNav.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Data plane</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {dataNav.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarSeparator />
      <SidebarFooter className="gap-3 border-t border-sidebar-border pt-4">
        <div className="space-y-1 text-sm">
          <p className="font-medium text-foreground">Acme Inc.</p>
          <p className="text-xs text-muted-foreground">Enterprise workspace</p>
        </div>
        <Button variant="outline" className="w-full">
          Invite teammates
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
