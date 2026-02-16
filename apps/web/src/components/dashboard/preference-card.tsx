import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface PreferenceCardProps {
  readonly title: string;
  readonly description: string;
  readonly children: ReactNode;
  readonly actionLabel?: string;
  readonly onAction?: () => void;
  readonly footer?: ReactNode;
}

export function PreferenceCard({
  title,
  description,
  children,
  actionLabel,
  onAction,
  footer,
}: PreferenceCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">{children}</CardContent>
      {(actionLabel || footer) && (
        <CardFooter className="flex items-center justify-between">
          {footer ?? <span />}
          {actionLabel ? (
            <Button size="sm" variant="outline" onClick={onAction}>
              {actionLabel}
            </Button>
          ) : null}
        </CardFooter>
      )}
    </Card>
  );
}
