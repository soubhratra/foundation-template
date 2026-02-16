"use client";

import { useMemo, useState } from "react";

import { useAuth } from "@repo/business-logic";

import { AccountForm, type AccountFormResult } from "@/components/dashboard/account-form";
import { PreferenceCard } from "@/components/dashboard/preference-card";
import { PreferenceToggle } from "@/components/dashboard/preference-toggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toast } from "@/components/ui/sonner";
import type { CurrentUser } from "@/lib/api/server";
import type { AccountFormValues } from "@/validation/account-form";
import type {
  NotificationChannelPreferences,
  NotificationPreferencesInput,
} from "@/validation/preferences";
import type {
  updateProfileAction as UpdateProfileAction,
  updateNotificationAction as UpdateNotificationAction,
} from "@/actions/profile-actions";

interface ProfileClientProps {
  readonly user?: CurrentUser;
  readonly channelPrefs: NotificationChannelPreferences;
  readonly updateProfileAction: typeof UpdateProfileAction;
  readonly updateNotificationAction: typeof UpdateNotificationAction;
}

export function ProfileClient({
  user,
  channelPrefs,
  updateProfileAction,
  updateNotificationAction,
}: ProfileClientProps) {
  const { refetch } = useAuth();
  const defaultValues = useMemo<AccountFormValues>(() => {
    return {
      fullName: user?.full_name ?? "Operations Lead",
      email: user?.email ?? "operator@example.com",
      jobTitle: "Platform owner",
      timezone: "UTC",
      productUpdates: true,
    } satisfies AccountFormValues;
  }, [user]);

  const [channels, setChannels] = useState(channelPrefs);
  const [isSavingChannels, setIsSavingChannels] = useState(false);

  const handleProfileSubmit = async (values: AccountFormValues): Promise<AccountFormResult> => {
    const response = await updateProfileAction(values);
    if (response.status === "success") {
      toast.success(response.message);
      await refetch();
      return { status: "success", resetValues: values } satisfies AccountFormResult;
    }
    toast.error(response.message);
    return {
      status: "error",
      fieldErrors: response.fieldErrors,
    } satisfies AccountFormResult;
  };

  const handleChannelSave = async () => {
    if (isSavingChannels) {
      return;
    }
    setIsSavingChannels(true);
    const payload: NotificationPreferencesInput = {
      kind: "channels",
      weeklyDigest: channels.weeklyDigest,
      incidentEscalations: channels.incidentEscalations,
      betaAccess: channels.betaAccess,
    } satisfies NotificationChannelPreferences;
    const response = await updateNotificationAction(payload);
    setIsSavingChannels(false);
    if (response.status === "success") {
      toast.success("Notification preferences saved");
    } else {
      toast.error(response.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Account summary</CardTitle>
            <CardDescription>Identity verified and synced with AuthProvider.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarImage src={buildAvatarSrc(defaultValues.email)} alt={defaultValues.fullName} />
                <AvatarFallback>{getInitials(defaultValues.fullName)}</AvatarFallback>
              </Avatar>
              <div className="space-y-0.5">
                <p className="text-sm font-medium text-foreground">{defaultValues.fullName}</p>
                <p className="text-xs text-muted-foreground">{defaultValues.email}</p>
              </div>
              <Badge variant="outline" className="ml-auto border-emerald-400 text-emerald-600 dark:text-emerald-300">
                Verified
              </Badge>
            </div>
            <div className="space-y-2 text-sm">
              <SummaryRow label="Role" value="Administrator" />
              <SummaryRow label="Workspace" value="Foundation template" />
              <SummaryRow label="MFA" value="Enabled" />
            </div>
          </CardContent>
          <CardFooter className="gap-2">
            <Button variant="outline" size="sm">
              Download export
            </Button>
            <Button variant="ghost" size="sm">
              Generate backup codes
            </Button>
          </CardFooter>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Profile details</CardTitle>
            <CardDescription>Server action backed form saves changes immediately.</CardDescription>
          </CardHeader>
          <CardContent>
            <AccountForm defaultValues={defaultValues} onSubmit={handleProfileSubmit} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PreferenceCard
          title="Notification channels"
          description="Decide how we contact you during incidents."
          actionLabel={isSavingChannels ? "Saving..." : "Save prefs"}
          onAction={handleChannelSave}
        >
          <PreferenceToggle
            label="Weekly digest"
            description="Summary of auth health every Monday"
            checked={channels.weeklyDigest}
            onCheckedChange={(value) => setChannels((prev) => ({ ...prev, weeklyDigest: value }))}
          />
          <PreferenceToggle
            label="Incident escalations"
            description="Send SMS/email when P1 incidents fire"
            checked={channels.incidentEscalations}
            onCheckedChange={(value) => setChannels((prev) => ({ ...prev, incidentEscalations: value }))}
          />
          <PreferenceToggle
            label="Beta access"
            description="Opt into testing new dashboard surfaces"
            checked={channels.betaAccess}
            onCheckedChange={(value) => setChannels((prev) => ({ ...prev, betaAccess: value }))}
          />
        </PreferenceCard>
        <PreferenceCard
          title="Session controls"
          description="Future API wiring will hydrate these controls with real data."
        >
          <div className="space-y-3">
            <ControlRow label="Active devices" value="5 sessions" action="View" />
            <ControlRow label="Last password change" value="12 days ago" action="Reset" />
            <ControlRow label="API tokens" value="3 active" action="Manage" />
          </div>
        </PreferenceCard>
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

function ControlRow({
  label,
  value,
  action,
}: {
  label: string;
  value: string;
  action: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm">
      <div>
        <p className="font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">{value}</p>
      </div>
      <Button variant="ghost" size="sm">
        {action}
      </Button>
    </div>
  );
}

function buildAvatarSrc(identifier: string) {
  return `https://avatar.vercel.sh/${encodeURIComponent(identifier)}`;
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
