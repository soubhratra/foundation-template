import { ArrowUpRight, Cpu, Globe, ShieldCheck } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const cards = [
  {
    title: "Authentication",
    description: "Session + JWT stack online",
    icon: ShieldCheck,
    metric: "99.99% uptime",
  },
  {
    title: "Edge presence",
    description: "Vercel + Cloudflare ready",
    icon: Globe,
    metric: "12 regions",
  },
  {
    title: "Workers",
    description: "Background jobs configured",
    icon: Cpu,
    metric: "5 active queues",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Operations</p>
          <h1 className="text-2xl font-semibold text-foreground">
            Control center overview
          </h1>
        </div>
        <button className="inline-flex items-center gap-2 text-sm font-medium text-primary">
          View runbooks <ArrowUpRight className="h-4 w-4" />
        </button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <Card key={card.title} className="border-dashed">
            <CardHeader className="space-y-1">
              <card.icon className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">{card.title}</CardTitle>
              <CardDescription>{card.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-medium text-foreground">{card.metric}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Recent telemetry</CardTitle>
          <CardDescription>Live data feed placeholder</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
