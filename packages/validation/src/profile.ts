import { z } from "zod";

const MAX_NAME_LENGTH = 255;

export const timezoneSchema = z
  .string({ required_error: "Select a timezone." })
  .trim()
  .regex(
    /^[A-Za-z_+-]+(?:\/[A-Za-z0-9_+.-]+)*$/,
    "Use a valid IANA timezone.",
  )
  .default("UTC");

export const updateProfileSchema = z.object({
  fullName: z
    .string({ required_error: "Full name is required." })
    .trim()
    .min(1, "Full name is required.")
    .max(MAX_NAME_LENGTH, `Full name must be ${MAX_NAME_LENGTH} characters or fewer.`),
  timezone: timezoneSchema,
});

export const notificationPrefsSchema = z.object({
  productEmails: z.boolean().default(true),
  securityAlerts: z.boolean().default(true),
  marketingEmails: z.boolean().default(false),
  smsAlerts: z.boolean().default(false),
});

export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;
export type NotificationPrefsInput = z.infer<typeof notificationPrefsSchema>;
