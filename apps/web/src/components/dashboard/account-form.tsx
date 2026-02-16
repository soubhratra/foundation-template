"use client";

import { useEffect } from "react";
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

import { accountFormSchema, type AccountFormValues } from "@/validation/account-form";

export interface AccountFormResult {
  status: "success" | "error";
  fieldErrors?: Partial<Record<keyof AccountFormValues, string>>;
  resetValues?: AccountFormValues;
}

interface AccountFormProps {
  readonly defaultValues: AccountFormValues;
  readonly onSubmit?: (values: AccountFormValues) => Promise<AccountFormResult | void>;
}

export function AccountForm({ defaultValues, onSubmit }: AccountFormProps) {
  const form = useForm<AccountFormValues>({
    resolver: zodResolver(accountFormSchema),
    defaultValues,
  });

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    if (!onSubmit) {
      return;
    }
    const result = await onSubmit(values);
    if (!result) {
      return;
    }
    if (result.status === "success") {
      form.reset(result.resetValues ?? values);
      return;
    }
    for (const [field, message] of Object.entries(result.fieldErrors ?? {})) {
      if (message) {
        form.setError(field as keyof AccountFormValues, {
          type: "server",
          message,
        });
      }
    }
  });

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          control={form.control}
          name="fullName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full name</FormLabel>
              <FormControl>
                <Input placeholder="Ada Lovelace" {...field} />
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
                <Input type="email" disabled {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="jobTitle"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role / title</FormLabel>
              <FormControl>
                <Input placeholder="Platform owner" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="timezone"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Timezone</FormLabel>
              <FormControl>
                <Input placeholder="UTC" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="productUpdates"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border px-3 py-2">
              <div>
                <FormLabel className="text-sm">Product updates</FormLabel>
                <p className="text-xs text-muted-foreground">
                  Receive digest emails when new features ship.
                </p>
              </div>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} aria-label="Product updates" />
              </FormControl>
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Saving" : "Save changes"}
        </Button>
      </form>
    </Form>
  );
}
