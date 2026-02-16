"use client";

import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { PreferenceCard } from "@/components/dashboard/preference-card";
import { PreferenceToggle } from "@/components/dashboard/preference-toggle";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/sonner";

const passwordSchema = z
  .object({
    currentPassword: z.string().min(8, "Enter your current password"),
    newPassword: z.string().min(12, "Use at least 12 characters"),
    confirmPassword: z.string().min(12),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;

const tokens = [
  { name: "CI deployments", scope: "production", lastUsed: "2h ago", status: "Active" },
  { name: "QA automation", scope: "staging", lastUsed: "Yesterday", status: "Active" },
  { name: "Legacy CLI", scope: "preview", lastUsed: "30d ago", status: "Expired" },
];

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    incidents: true,
    maintenance: true,
    compliance: false,
  });

  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    void values;
    await new Promise((resolve) => setTimeout(resolve, 300));
    toast.success("Security settings updated", {
      description: "Password change queued — placeholder until backend wiring.",
    });
    form.reset();
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>Mock accordion wiring stands in for future API integration.</CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible defaultValue="password">
            <AccordionItem value="password">
              <AccordionTrigger>Change password</AccordionTrigger>
              <AccordionContent>
                <Form {...form}>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <FormField
                      control={form.control}
                      name="currentPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Current password</FormLabel>
                          <FormControl>
                            <Input type="password" autoComplete="current-password" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="newPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>New password</FormLabel>
                          <FormControl>
                            <Input type="password" autoComplete="new-password" {...field} />
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
                            <Input type="password" autoComplete="new-password" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <Button type="submit" disabled={form.formState.isSubmitting}>
                      {form.formState.isSubmitting ? "Saving" : "Save password"}
                    </Button>
                  </form>
                </Form>
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="sessions">
              <AccordionTrigger>Active sessions</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3 text-sm">
                  <SessionRow device="Chrome on macOS" location="San Francisco" status="Current" />
                  <SessionRow device="Safari on iOS" location="Oakland" status="30 mins ago" />
                  <SessionRow device="Firefox on Windows" location="Remote" status="Revoke" />
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <PreferenceCard
          title="Notification policies"
          description="Fine-tune which events trigger alerts."
          actionLabel="Save"
          onAction={() =>
            toast.success("Preferences captured", {
              description: "Stored locally until persistence is wired.",
            })
          }
        >
          <PreferenceToggle
            label="Incident alerts"
            description="Page/SMS when production incidents fire"
            checked={notifications.incidents}
            onCheckedChange={(value) => setNotifications((prev) => ({ ...prev, incidents: value }))}
          />
          <PreferenceToggle
            label="Maintenance windows"
            description="Email reminders 24h before scheduled downtime"
            checked={notifications.maintenance}
            onCheckedChange={(value) => setNotifications((prev) => ({ ...prev, maintenance: value }))}
          />
          <PreferenceToggle
            label="Compliance exports"
            description="Monthly SOC2 and audit packages"
            checked={notifications.compliance}
            onCheckedChange={(value) => setNotifications((prev) => ({ ...prev, compliance: value }))}
          />
        </PreferenceCard>
        <PreferenceCard
          title="API tokens"
          description="Placeholder list showing how tokens will appear."
          actionLabel="Generate token"
          onAction={() => toast.message("Token mint queued", { description: "Stub action" })}
        >
          <div className="space-y-3">
            {tokens.map((token) => (
              <div key={token.name} className="flex items-center justify-between rounded-lg border px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{token.name}</p>
                  <p className="text-xs text-muted-foreground">
                    Scope: {token.scope} • Last used {token.lastUsed}
                  </p>
                </div>
                <Badge variant="outline" className={token.status === "Active" ? "text-emerald-600" : "text-amber-600"}>
                  {token.status}
                </Badge>
              </div>
            ))}
          </div>
        </PreferenceCard>
      </div>
    </div>
  );
}

function SessionRow({ device, location, status }: { device: string; location: string; status: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2">
      <div>
        <p className="text-sm font-medium text-foreground">{device}</p>
        <p className="text-xs text-muted-foreground">{location}</p>
      </div>
      <Badge variant="outline">{status}</Badge>
    </div>
  );
}
