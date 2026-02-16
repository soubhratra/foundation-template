"use client";

import type { ReactNode } from "react";
import type { FieldValues, SubmitHandler, UseFormReturn } from "react-hook-form";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";

export type AuthFormStatusVariant = "success" | "error";

export interface AuthFormStatus {
  readonly variant: AuthFormStatusVariant;
  readonly title?: string;
  readonly description?: string;
}

interface AuthFormProps<TFieldValues extends FieldValues> {
  readonly form: UseFormReturn<TFieldValues>;
  readonly onSubmit: SubmitHandler<TFieldValues>;
  readonly children: ReactNode;
  readonly submitLabel: string;
  readonly isSubmitting?: boolean;
  readonly status?: AuthFormStatus | null;
  readonly footer?: ReactNode;
}

export function AuthForm<TFieldValues extends FieldValues>({
  form,
  onSubmit,
  children,
  submitLabel,
  isSubmitting,
  status,
  footer,
}: AuthFormProps<TFieldValues>) {
  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
        {status ? <AuthFormStatusAlert status={status} /> : null}
        <div className="space-y-4">{children}</div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Working…" : submitLabel}
        </Button>
        {footer ? <div className="text-center text-sm text-muted-foreground">{footer}</div> : null}
      </form>
    </Form>
  );
}

interface AuthFormStatusAlertProps {
  readonly status: AuthFormStatus;
}

function AuthFormStatusAlert({ status }: AuthFormStatusAlertProps) {
  const variant = status.variant === "error" ? "destructive" : "default";

  if (!status.title && !status.description) {
    return null;
  }

  return (
    <Alert variant={variant}>
      {status.title ? <AlertTitle>{status.title}</AlertTitle> : null}
      {status.description ? <AlertDescription>{status.description}</AlertDescription> : null}
    </Alert>
  );
}
