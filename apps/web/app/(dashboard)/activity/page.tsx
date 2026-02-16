import { ActivityTable, type ActivityEntry } from "@/components/dashboard/activity-table";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const filters = [
  { label: "All", active: true },
  { label: "Auth", active: false },
  { label: "Deployments", active: false },
  { label: "Security", active: false },
];

const logEntries: ActivityEntry[] = [
  {
    id: "deploy-247",
    title: "Deploy #247 promoted to staging",
    actor: "CI pipeline",
    meta: "commit 41cdacb",
    status: "success",
    time: "08:42 UTC",
  },
  {
    id: "login-alert",
    title: "Burst login attempts detected",
    actor: "edge shield",
    meta: "blocked 142 requests",
    status: "warning",
    time: "08:12 UTC",
  },
  {
    id: "token-rotation",
    title: "API tokens rotated",
    actor: "security-bot",
    meta: "7 keys refreshed",
    status: "success",
    time: "07:55 UTC",
  },
  {
    id: "session-expired",
    title: "Session invalidation",
    actor: "ops-team",
    meta: "user avery@acme.io",
    status: "success",
    time: "07:20 UTC",
  },
  {
    id: "db-migration",
    title: "Migration 2024.10 applied",
    actor: "release captain",
    meta: "duration 18s",
    status: "success",
    time: "06:44 UTC",
  },
  {
    id: "anomaly-detected",
    title: "Anomaly flagged on signup flow",
    actor: "analytics",
    meta: "conversion dipped 4%",
    status: "warning",
    time: "06:10 UTC",
  },
  {
    id: "audit-log",
    title: "Audit export generated",
    actor: "finance-automation",
    meta: "sent to GRC inbox",
    status: "success",
    time: "05:55 UTC",
  },
  {
    id: "rate-limit",
    title: "Rate limit breach blocked",
    actor: "api-gateway",
    meta: "client 2df8",
    status: "error",
    time: "05:12 UTC",
  },
];

export default function ActivityPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Audit trail</p>
          <h1 className="text-2xl font-semibold text-foreground">Activity log</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            Export CSV
          </Button>
          <Button size="sm">Subscribe to stream</Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Mock controls to demonstrate layout — wiring arrives next plan.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <Button
                key={filter.label}
                variant={filter.active ? "default" : "outline"}
                size="sm"
              >
                {filter.label}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">Last 24h</Badge>
            <Badge variant="outline">Workspace: Production</Badge>
          </div>
          <div className="overflow-x-auto">
            <ActivityTable entries={logEntries} />
          </div>
        </CardContent>
        <CardFooter className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
          <span>Page 1 of 8</span>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm">
              Previous
            </Button>
            <Button variant="ghost" size="sm">
              Next
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
