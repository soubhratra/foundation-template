import { ArrowUpRight, CircleCheck, ShieldCheck } from "lucide-react";

import type { components } from "@repo/api-client/gen/v1";

import { ActivityTable, type ActivityEntry } from "@/components/dashboard/activity-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getServerApi, type CurrentUser } from "@/lib/api/server";

type HealthSnapshot = components["schemas"]["HealthOut"];

const FALLBACK_ACTIVITY: ActivityEntry[] = [
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

export default async function DashboardPage() {
  const api = await getServerApi();
  const [user, health] = await Promise.all([
    api
      .getCurrentUser()
      .catch(() => undefined),
    api.client
      .GET("/api/v1/health")
      .then((result) => result.data)
      .catch(() => undefined),
  ]);

  const kpis = buildKpis(user, health);
  const activityEntries = buildActivityEntries(user);
  const environmentStatuses = buildEnvironmentStatuses(health);

  return (
    <div className="space-y-8">
      {!user ? (
        <Alert variant="destructive">
          <AlertTitle>Unable to read session data</AlertTitle>
          <AlertDescription>
            We could not fetch the current profile from Django. Check that you are signed in and the API is reachable.
          </AlertDescription>
        </Alert>
      ) : null}
      <Card className="border-0 bg-[radial-gradient(circle_at_top,_rgba(37,99,235,0.25),_transparent)] bg-background">
        <CardHeader className="gap-2">
          <CardDescription className="text-xs uppercase text-muted-foreground">
            Live mission control
          </CardDescription>
          <CardTitle className="text-3xl font-semibold text-foreground">
            {user ? `Welcome back, ${user.full_name ?? user.email}` : "Connect your account"}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {user
              ? `Session synced from /api/v1/users/me. User #${user.id} is ready to manage the fleet.`
              : "Sign in to hydrate this dashboard with live session data."}
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
              <CardDescription>Snapshot straight from the health endpoint</CardDescription>
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

function buildKpis(user?: CurrentUser, health?: HealthSnapshot | undefined) {
  return [
    {
      label: "Session",
      value: user ? `User #${user.id}` : "Not authenticated",
      delta: user ? `Email ${user.email}` : "Sign in to load data",
    },
    {
      label: "Display name",
      value: user?.full_name ?? "Add your name",
      delta: user?.full_name ? "Synced from Django" : "Edit profile to personalize",
    },
    {
      label: "API health",
      value: health?.status ?? "Unknown",
      delta: health?.database ? `Database ${health.database}` : "Awaiting heartbeat",
    },
    {
      label: "Last sync",
      value: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      delta: user ? "Fetched via getServerApi" : "Retry after login",
    },
  ];
}

function buildActivityEntries(user?: CurrentUser): ActivityEntry[] {
  if (!user) {
    return FALLBACK_ACTIVITY;
  }
  return [
    {
      id: `profile-${user.id}`,
      title: `${user.full_name ?? user.email} session synced`,
      actor: user.email,
      meta: "GET /api/v1/users/me",
      status: "success",
      time: "Just now",
    },
    ...FALLBACK_ACTIVITY.slice(0, 4),
  ];
}

function buildEnvironmentStatuses(health?: HealthSnapshot | undefined) {
  if (!health) {
    return [
      { name: "Production", status: "Unknown", variant: "warning" as const },
      { name: "Staging", status: "Unknown", variant: "warning" as const },
      { name: "Preview", status: "Unknown", variant: "warning" as const },
    ];
  }

  return [
    { name: "Production", status: health.status, variant: "success" as const },
    { name: "Database", status: health.database, variant: "success" as const },
    { name: "Preview", status: "Queue clear", variant: "success" as const },
  ];
}
