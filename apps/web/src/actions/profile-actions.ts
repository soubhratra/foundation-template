"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import type { ZodError } from "zod";

import type { PasswordChangeInput } from "@repo/validation";
import { passwordChangeSchema } from "@repo/validation";

import { getServerApi } from "@/lib/api/server";
import { accountFormSchema, type AccountFormValues } from "@/validation/account-form";
import {
  notificationPreferencesSchema,
  type NotificationPreferencesInput,
  type NotificationChannelPreferences,
  type NotificationAlertPreferences,
  parseAlertPreferences,
  parseChannelPreferences,
} from "@/validation/preferences";

const CHANNEL_COOKIE = "dashboard:channels";
const ALERT_COOKIE = "dashboard:alerts";

export interface ActionResponse<TField extends string = string> {
  status: "success" | "error";
  message: string;
  fieldErrors?: Partial<Record<TField, string>>;
}

type AccountFields = keyof AccountFormValues & string;
type PasswordFields = keyof PasswordChangeInput & string;
type ChannelFields = keyof NotificationChannelPreferences & string;
type AlertFields = keyof NotificationAlertPreferences & string;

export async function updateProfileAction(values: AccountFormValues): Promise<ActionResponse<AccountFields>> {
  const parsed = accountFormSchema.safeParse(values);
  if (!parsed.success) {
    return {
      status: "error",
      message: "Fix the highlighted fields before saving your profile.",
      fieldErrors: formatFieldErrors<AccountFields>(parsed.error),
    } satisfies ActionResponse<AccountFields>;
  }

  try {
    const api = await getServerApi();
    await api.updateCurrentUser({ full_name: parsed.data.fullName });
    revalidateShell();
    return {
      status: "success",
      message: "Profile saved successfully.",
    } satisfies ActionResponse<AccountFields>;
  } catch (error) {
    return handleActionError<AccountFields>(error, "Unable to update your profile. Please try again.");
  }
}

export async function updateNotificationAction(
  input: NotificationPreferencesInput,
): Promise<ActionResponse<ChannelFields | AlertFields>> {
  const parsed = notificationPreferencesSchema.safeParse(input);
  if (!parsed.success) {
    return {
      status: "error",
      message: "Preferences could not be saved. Fix the toggles and retry.",
      fieldErrors: formatFieldErrors<ChannelFields | AlertFields>(parsed.error as ZodError<Record<string, unknown>>),
    } satisfies ActionResponse<ChannelFields | AlertFields>;
  }

  const store = await cookies();
  const serialized = JSON.stringify(parsed.data);
  const target = parsed.data.kind === "channels" ? CHANNEL_COOKIE : ALERT_COOKIE;
  store.set(target, serialized, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
  });

  revalidatePath("/profile");
  revalidatePath("/settings");

  return {
    status: "success",
    message: "Preferences updated.",
  } satisfies ActionResponse<ChannelFields | AlertFields>;
}

export async function changePasswordAction(values: PasswordChangeInput): Promise<ActionResponse<PasswordFields>> {
  const parsed = passwordChangeSchema.safeParse(values);
  if (!parsed.success) {
    return {
      status: "error",
      message: "Resolve the errors below before changing your password.",
      fieldErrors: formatFieldErrors<PasswordFields>(parsed.error),
    } satisfies ActionResponse<PasswordFields>;
  }

  try {
    const api = await getServerApi();
    await api.requestPasswordChange(parsed.data);
    revalidatePath("/settings");
    return {
      status: "success",
      message: "Password updated successfully.",
    } satisfies ActionResponse<PasswordFields>;
  } catch (error) {
    return handleActionError<PasswordFields>(error, "Unable to change password right now.");
  }
}

export async function readChannelPreferencesFromCookies(): Promise<NotificationChannelPreferences> {
  const store = await cookies();
  const raw = store.get(CHANNEL_COOKIE)?.value;
  return parseChannelPreferences(raw);
}

export async function readAlertPreferencesFromCookies(): Promise<NotificationAlertPreferences> {
  const store = await cookies();
  const raw = store.get(ALERT_COOKIE)?.value;
  return parseAlertPreferences(raw);
}

function revalidateShell() {
  revalidatePath("/dashboard");
  revalidatePath("/profile");
  revalidatePath("/settings");
}

function handleActionError<TField extends string>(error: unknown, fallback: string): ActionResponse<TField> {
  const message = error instanceof Error && error.message ? error.message : fallback;
  return {
    status: "error",
    message,
  } satisfies ActionResponse<TField>;
}

function formatFieldErrors<TField extends string>(error: ZodError<Record<string, unknown>>): Partial<Record<TField, string>> {
  const result: Partial<Record<TField, string>> = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (typeof key === "string" && !result[key as TField]) {
      result[key as TField] = issue.message;
    }
  }
  return result;
}
