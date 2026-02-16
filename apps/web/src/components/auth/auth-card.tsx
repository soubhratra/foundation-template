import type { ReactNode } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface AuthCardProps {
  readonly eyebrow?: string;
  readonly title: string;
  readonly description?: string;
  readonly children: ReactNode;
  readonly footer?: ReactNode;
}

export function AuthCard({ eyebrow, title, description, children, footer }: AuthCardProps) {
  return (
    <Card className="border border-border/60 bg-card/80 shadow-2xl backdrop-blur">
      <CardHeader className="space-y-2 text-center">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-primary">
            {eyebrow}
          </p>
        ) : null}
        <CardTitle className="text-2xl font-semibold text-foreground">{title}</CardTitle>
        {description ? (
          <CardDescription className="text-base text-muted-foreground">
            {description}
          </CardDescription>
        ) : null}
      </CardHeader>
      <CardContent>{children}</CardContent>
      {footer ? <CardFooter className="justify-center border-t pt-4 text-sm text-muted-foreground">{footer}</CardFooter> : null}
    </Card>
  );
}
