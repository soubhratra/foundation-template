import { z } from "zod";

export const notificationChannelsSchema = z.object({
  kind: z.literal("channels"),
  weeklyDigest: z.boolean(),
  incidentEscalations: z.boolean(),
  betaAccess: z.boolean(),
});

export const notificationAlertsSchema = z.object({
  kind: z.literal("alerts"),
  incidents: z.boolean(),
  maintenance: z.boolean(),
  compliance: z.boolean(),
});

export const notificationPreferencesSchema = z.union([notificationChannelsSchema, notificationAlertsSchema]);

export type NotificationChannelPreferences = z.infer<typeof notificationChannelsSchema>;
export type NotificationAlertPreferences = z.infer<typeof notificationAlertsSchema>;
export type NotificationPreferencesInput = z.infer<typeof notificationPreferencesSchema>;

export const defaultChannelPreferences: NotificationChannelPreferences = {
  kind: "channels",
  weeklyDigest: true,
  incidentEscalations: true,
  betaAccess: false,
};

export const defaultAlertPreferences: NotificationAlertPreferences = {
  kind: "alerts",
  incidents: true,
  maintenance: true,
  compliance: false,
};

export function parseChannelPreferences(value?: string): NotificationChannelPreferences {
  if (!value) {
    return defaultChannelPreferences;
  }
  try {
    const parsed = JSON.parse(value) as Partial<NotificationChannelPreferences>;
    return notificationChannelsSchema.parse({ ...defaultChannelPreferences, ...parsed });
  } catch {
    return defaultChannelPreferences;
  }
}

export function parseAlertPreferences(value?: string): NotificationAlertPreferences {
  if (!value) {
    return defaultAlertPreferences;
  }
  try {
    const parsed = JSON.parse(value) as Partial<NotificationAlertPreferences>;
    return notificationAlertsSchema.parse({ ...defaultAlertPreferences, ...parsed });
  } catch {
    return defaultAlertPreferences;
  }
}
