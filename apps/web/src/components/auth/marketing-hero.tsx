import { ArrowRight, CheckCircle2, Shield, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const highlights = [
  "One command bootstraps API, web, and mobile apps",
  "Pre-wired auth, billing, and observability",
  "Composable UI primitives with first-class dark mode",
];

const metrics = [
  { label: "Templates provisioned", value: "2,417" },
  { label: "Avg. setup", value: "4m 52s" },
];

export function MarketingHero() {
  return (
    <section className="flex w-full flex-col gap-8">
      <div className="space-y-6">
        <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4 text-primary" />
          Ship SaaS surfaces without fighting scaffolding
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-foreground md:text-5xl">
            Launch lightning-fast with a shadcn-powered dashboard, auth shell,
            and ready-to-wire providers.
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            Foundation Template gives your team a production-grade design system
            backed by Next.js 15, Tailwind 4, and next-themes so you can focus on
            flows, not primitives.
          </p>
        </div>
        <div className="flex flex-wrap gap-4">
          <Button size="lg" className="gap-2">
            Launch demo <ArrowRight className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="lg" className="gap-2">
            <Shield className="h-4 w-4" /> Explore security stack
          </Button>
        </div>
      </div>
      <Card className="border-dashed">
        <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Shield className="h-5 w-5 text-primary" /> Enterprise guardrails baked in
            </CardTitle>
            <CardDescription>
              Ready-made auth surfaces, audit logging, and global theming to meet compliance faster.
            </CardDescription>
          </div>
          <div className="flex gap-6">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-left">
                <p className="text-3xl font-semibold text-foreground">{metric.value}</p>
                <p className="text-sm text-muted-foreground">{metric.label}</p>
              </div>
            ))}
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {highlights.map((highlight) => (
            <div key={highlight} className="flex items-start gap-3 rounded-lg border border-dashed p-4">
              <CheckCircle2 className="mt-1 h-5 w-5 text-primary" />
              <p className="text-base text-foreground">{highlight}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </section>
  );
}
