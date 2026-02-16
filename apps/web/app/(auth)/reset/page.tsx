"use client";

import Link from "next/link";
import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import {
  AuthCard,
  AuthForm,
  AuthLinks,
  type AuthFormStatus,
} from "@/components/auth";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/sonner";
import { postJson } from "@/lib/request";
import type { PasswordResetInput } from "@repo/validation";
import { passwordResetSchema } from "@repo/validation";

const defaultValues: PasswordResetInput = {
  email: "",
};

export default function ResetPage() {
  const form = useForm<PasswordResetInput>({
    resolver: zodResolver(passwordResetSchema),
    defaultValues,
  });
  const [status, setStatus] = useState<AuthFormStatus | null>(null);

  const handleSubmit = async (values: PasswordResetInput) => {
    setStatus(null);
    try {
      await postJson("/api/v1/auth/password/reset/", values);
      toast.success("Password reset email sent.");
      setStatus({
        variant: "success",
        title: "Check your inbox",
        description: "Follow the link we emailed you to set a new password.",
      });
      form.reset(values);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to start the reset flow.";
      toast.error(message);
      setStatus({
        variant: "error",
        title: "Reset failed",
        description: message,
      });
    }
  };

  return (
    <AuthCard
      eyebrow="Reset access"
      title="Send a reset link"
      description="We will email you a secure link to update your password."
      footer={
        <AuthLinks
          items={[
            { prefix: "Ready to sign in?", label: "Return to login", href: "/" },
            { prefix: "Need an account?", label: "Create one", href: "/signup" },
          ]}
        />
      }
    >
      <AuthForm
        form={form}
        submitLabel="Send reset link"
        isSubmitting={form.formState.isSubmitting}
        onSubmit={handleSubmit}
        status={status}
        footer={
          status?.variant === "success" ? (
            <Link href="/verify-email" className="font-medium text-primary hover:underline">
              Need to verify your email instead?
            </Link>
          ) : undefined
        }
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input
                  type="email"
                  autoComplete="email"
                  disabled={form.formState.isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </AuthForm>
    </AuthCard>
  );
}
