import { ArrowUpRight, CircleCheck, ShieldCheck } from "lucide-react";

import { ActivityTable, type ActivityEntry } from "@/components/dashboard/activity-table";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const kpis = [
  { label: "Active sessions", value: "1,204", delta: "+6.2% vs last week" },
  { label: "Avg. response", value: "182 ms", delta: "Edge cached" },
  { label: "Deployments", value: "3 today", delta: "Last: 14:12 UTC" },
  { label: "Incidents", value: "0 open", delta: "Last closed 3d ago" },
];

const activityEntries: ActivityEntry[] = [
  {
    id: "deploy-248",
    title: "Deploy #248 promoted to production",
    actor: "CI pipeline",
    meta: "us-east-1",
    status: "success",
    time: "2m ago",
  },
  {
    id: "policy-update",
    title: "Admin policy synced",
    actor: "policy-sync@automation",
    meta: "RBAC refresh",
    status: "success",
    time: "12m ago",
  },
  {
    id: "login-spike",
    title: "Auth traffic spike throttled",
    actor: "Edge shield",
    meta: "3 regions",
    status: "warning",
    time: "29m ago",
  },
  {
    id: "api-token",
    title: "API token rotation queued",
    actor: "security-bot",
    meta: "Found expiring credentials",
    status: "success",
    time: "1h ago",
  },
  {
    id: "activity-ingest",
    title: "Activity stream backlog cleared",
    actor: "worker-pool",
    meta: "2.3M events",
    status: "success",
    time: "2h ago",
  },
];

const environmentStatuses: Array<{
  name: string;
  status: string;
  variant: "success" | "warning";
}> = [
  { name: "Production", status: "Healthy", variant: "success" },
  { name: "Staging", status: "Deploying", variant: "warning" },
  { name: "Preview", status: "Queued", variant: "warning" },
];

const runbookCards = [
  {
    title: "Session integrity",
    description: "Past 24h",
    stat: "99.99%",
  },
  {
    title: "Background workers",
    description: "Queues drained",
    stat: "5/5",
  },
  {
    title: "Security tasks",
    description: "Requiring review",
    stat: "2",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <Card className="border-0 bg-[radial-gradient(circle_at_top,_rgba(37,99,235,0.25),_transparent)] bg-background">
        <CardHeader className="gap-2">
          <CardDescription className="text-xs uppercase text-muted-foreground">
            Live mission control
          </CardDescription>
          <CardTitle className="text-3xl font-semibold text-foreground">
            All systems nominal — ready for launch
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Stay ahead of auth events, deployments, and infrastructure health from a single dashboard. Real data wiring arrives in the next plan.
          </p>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button size="sm" className="gap-2">
            Review alerts
            <ArrowUpRight className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            Download audit log
            <ShieldCheck className="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="border-dashed">
            <CardHeader className="space-y-1">
              <CardDescription>{kpi.label}</CardDescription>
              <CardTitle className="text-2xl">{kpi.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{kpi.delta}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
            <CardDescription>Human-friendly view of mock deployment + security events.</CardDescription>
          </CardHeader>
          <CardContent>
            <ActivityTable entries={activityEntries} dense />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Environment status</CardTitle>
              <CardDescription>Snapshot of each surface</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {environmentStatuses.map((env) => (
                <div key={env.name} className="flex items-center justify-between rounded-lg border px-3 py-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">{env.name}</p>
                    <p className="text-xs text-muted-foreground">Updated moments ago</p>
                  </div>
                  <Badge variant="outline" className={badgeTone(env.variant)}>
                    {env.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Operator checklist</CardTitle>
              <CardDescription>High-level runbook reminders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {runbookCards.map((card) => (
                <div key={card.title} className="flex items-center justify-between rounded-lg border px-3 py-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">{card.title}</p>
                    <p className="text-xs text-muted-foreground">{card.description}</p>
                  </div>
                  <div className="flex items-center gap-1 text-sm font-semibold">
                    <CircleCheck className="h-4 w-4 text-primary" />
                    {card.stat}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function badgeTone(variant: "success" | "warning") {
  if (variant === "success") {
    return "border-emerald-500/40 text-emerald-600 dark:text-emerald-300";
  }
  return "border-amber-500/40 text-amber-600 dark:text-amber-300";
}
