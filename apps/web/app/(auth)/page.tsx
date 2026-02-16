"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
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
import { Switch } from "@/components/ui/switch";
import { toast } from "@/components/ui/sonner";
import { useRedirectTarget } from "@/hooks/use-redirect-target";
import { useAuth } from "@repo/business-logic";
import type { LoginInput } from "@repo/validation";
import { loginSchema } from "@repo/validation";

const defaultValues: LoginInput = {
  email: "",
  password: "",
  remember: false,
};

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { target } = useRedirectTarget();
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues,
  });
  const [status, setStatus] = useState<AuthFormStatus | null>(null);
  const [showVerificationHint, setShowVerificationHint] = useState(false);

  const handleSubmit = async (values: LoginInput) => {
    setStatus(null);
    setShowVerificationHint(false);
    try {
      await login.mutateAsync(values);
      toast.success("Signed in successfully");
      setStatus({
        variant: "success",
        title: "Signed in",
        description: "Redirecting you to your workspace…",
      });
      router.replace(target);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to sign in right now.";
      setStatus({
        variant: "error",
        title: "Unable to sign in",
        description: message,
      });
      if (message.toLowerCase().includes("verify")) {
        setShowVerificationHint(true);
      }
      toast.error(message);
    }
  };

  return (
    <AuthCard
      eyebrow="Access portal"
      title="Ready when you are"
      description="Enter your credentials to unlock the control center."
      footer={
        <AuthLinks
          items={[
            { prefix: "Need an account?", label: "Create one", href: "/signup" },
            { prefix: "Can't access your account?", label: "Reset password", href: "/reset" },
          ]}
        />
      }
    >
      <AuthForm
        form={form}
        submitLabel="Access dashboard"
        isSubmitting={login.isPending}
        onSubmit={handleSubmit}
        status={status}
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" autoComplete="email" disabled={login.isPending} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <div className="flex items-center justify-between">
                <FormLabel>Password</FormLabel>
                <Link href="/reset" className="text-xs font-medium text-primary">
                  Forgot?
                </Link>
              </div>
              <FormControl>
                <Input
                  type="password"
                  autoComplete="current-password"
                  disabled={login.isPending}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="remember"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border px-3 py-2">
              <div>
                <FormLabel className="text-sm">Stay signed in</FormLabel>
                <p className="text-xs text-muted-foreground">
                  Store credentials securely on this device.
                </p>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  aria-label="Remember me"
                  disabled={login.isPending}
                />
              </FormControl>
            </FormItem>
          )}
        />
        {showVerificationHint ? <VerificationHint /> : null}
      </AuthForm>
    </AuthCard>
  );
}

function VerificationHint() {
  return (
    <div className="rounded-lg border border-dashed px-4 py-3 text-sm text-muted-foreground">
      <p className="font-semibold text-foreground">Account pending verification</p>
      <p>
        Check your inbox for the verification email or
        <Link href="/verify-email" className="ml-1 font-medium text-primary hover:underline">
          enter your verification key
        </Link>
        .
      </p>
    </div>
  );
}
