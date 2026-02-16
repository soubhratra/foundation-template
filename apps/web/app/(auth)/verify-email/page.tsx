"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

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
import type { EmailVerificationInput } from "@repo/validation";
import { emailVerificationSchema } from "@repo/validation";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const defaultKey = useMemo(() => searchParams?.get("key") ?? "", [searchParams]);
  const form = useForm<EmailVerificationInput>({
    resolver: zodResolver(emailVerificationSchema),
    defaultValues: { key: defaultKey },
  });
  const [status, setStatus] = useState<AuthFormStatus | null>(null);

  const handleSubmit = async (values: EmailVerificationInput) => {
    setStatus(null);
    try {
      await postJson("/api/v1/auth/account/confirm-email/", values);
      toast.success("Email verified. You can sign in now.");
      setStatus({
        variant: "success",
        title: "Email verified",
        description: "Return to the login page to access your dashboard.",
      });
      form.reset(values);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to verify this key.";
      toast.error(message);
      setStatus({
        variant: "error",
        title: "Verification failed",
        description: message,
      });
    }
  };

  return (
    <AuthCard
      eyebrow="Verify email"
      title="Confirm your account"
      description="Paste the verification key from your email to continue."
      footer={
        <AuthLinks
          items={[
            { prefix: "Ready to continue?", label: "Return to login", href: "/" },
            { prefix: "Need to resend?", label: "Request new email", href: "/signup" },
          ]}
        />
      }
    >
      <AuthForm
        form={form}
        submitLabel="Verify email"
        isSubmitting={form.formState.isSubmitting}
        onSubmit={handleSubmit}
        status={status}
        footer={
          status?.variant === "success" ? (
            <Link href="/" className="font-medium text-primary hover:underline">
              Continue to login
            </Link>
          ) : undefined
        }
      >
        <FormField
          control={form.control}
          name="key"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Verification key</FormLabel>
              <FormControl>
                <Input
                  placeholder="paste-your-key"
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
