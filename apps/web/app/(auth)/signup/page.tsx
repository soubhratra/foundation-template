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
import { Switch } from "@/components/ui/switch";
import { toast } from "@/components/ui/sonner";
import { postJson } from "@/lib/request";
import type { SignupInput } from "@repo/validation";
import { signupSchema } from "@repo/validation";

const defaultValues: SignupInput = {
  name: "",
  email: "",
  password: "",
  confirmPassword: "",
  marketingOptIn: true,
};

export default function SignupPage() {
  const form = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues,
  });
  const [status, setStatus] = useState<AuthFormStatus | null>(null);

  const handleSubmit = async (values: SignupInput) => {
    setStatus(null);
    try {
      await postJson("/api/v1/auth/account/", values);
      toast.success("Check your inbox to verify your account.");
      setStatus({
        variant: "success",
        title: "Verify your email",
        description: "We sent instructions to your inbox. Enter your key once it arrives.",
      });
      form.reset({ ...defaultValues, email: values.email });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to create your account right now.";
      toast.error(message);
      setStatus({
        variant: "error",
        title: "Signup failed",
        description: message,
      });
    }
  };

  return (
    <AuthCard
      eyebrow="Create account"
      title="Start in minutes"
      description="Provision your control center credentials."
      footer={
        <AuthLinks
          items={[
            { prefix: "Already onboard?", label: "Sign in", href: "/" },
            { prefix: "Need help?", label: "Reset password", href: "/reset" },
          ]}
        />
      }
    >
      <AuthForm
        form={form}
        submitLabel="Create account"
        isSubmitting={form.formState.isSubmitting}
        onSubmit={handleSubmit}
        status={status}
        footer={
          status?.variant === "success" ? (
            <Link href="/verify-email" className="font-medium text-primary hover:underline">
              Enter verification key
            </Link>
          ) : undefined
        }
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full name</FormLabel>
              <FormControl>
                <Input placeholder="Ada Lovelace" disabled={form.formState.isSubmitting} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" autoComplete="email" disabled={form.formState.isSubmitting} {...field} />
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
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="new-password" disabled={form.formState.isSubmitting} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="confirmPassword"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm password</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="new-password" disabled={form.formState.isSubmitting} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="marketingOptIn"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border px-3 py-2">
              <div>
                <FormLabel className="text-sm">Product updates</FormLabel>
                <p className="text-xs text-muted-foreground">
                  Receive onboarding tips and release highlights.
                </p>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  aria-label="Marketing opt-in"
                  disabled={form.formState.isSubmitting}
                />
              </FormControl>
            </FormItem>
          )}
        />
      </AuthForm>
    </AuthCard>
  );
}
