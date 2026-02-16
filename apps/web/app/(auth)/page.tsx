"use client";

import Link from "next/link";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { toast } from "@/components/ui/sonner";
import { useAuth } from "@repo/business-logic";
import type { LoginInput } from "@repo/validation";
import { loginSchema } from "@repo/validation";

const defaultValues: LoginInput = {
  email: "",
  password: "",
  remember: false,
};

export default function AuthPage() {
  const { login } = useAuth();
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues,
  });

  const onSubmit = async (values: LoginInput) => {
    try {
      await login.mutateAsync(values);
      toast.success("Login successful");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to login");
    }
  };

  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" autoComplete="email" {...field} />
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
                <Link href="#" className="text-xs font-medium text-primary">
                  Forgot?
                </Link>
              </div>
              <FormControl>
                <Input type="password" autoComplete="current-password" {...field} />
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
                />
              </FormControl>
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Access dashboard"}
        </Button>
        {login.error ? (
          <p className="text-center text-sm text-destructive">
            {login.error.message}
          </p>
        ) : null}
      </form>
    </Form>
  );
}
