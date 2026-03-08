"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyApiClient = any;

import { getServerApi, type ProrationPreviewOut } from "@/lib/api/server";
import type { ActionResponse } from "@/actions/profile-actions";

function handleActionError(error: unknown, fallback: string): ActionResponse {
  const message = error instanceof Error && error.message ? error.message : fallback;
  return { status: "error", message };
}

export async function changePlanAction(
  planId: string,
  billingPeriod: string,
): Promise<ActionResponse> {
  try {
    const api = await getServerApi();
    // TODO: use generated types after `turbo run generate:types`
    const client: AnyApiClient = api.client;
    await client.POST("/api/v1/billing/subscription/change", {
      body: { plan_id: planId, billing_period: billingPeriod },
    });
    revalidatePath("/billing");
    return { status: "success", message: "Plan updated." };
  } catch (error) {
    return handleActionError(error, "Unable to change plan.");
  }
}

export async function cancelSubscriptionAction(): Promise<ActionResponse> {
  try {
    const api = await getServerApi();
    // TODO: use generated types after `turbo run generate:types`
    const client: AnyApiClient = api.client;
    await client.POST("/api/v1/billing/subscription/cancel", {});
    revalidatePath("/billing");
    return { status: "success", message: "Subscription cancelled." };
  } catch (error) {
    return handleActionError(error, "Unable to cancel subscription.");
  }
}

export async function reactivateSubscriptionAction(): Promise<ActionResponse> {
  try {
    const api = await getServerApi();
    // TODO: use generated types after `turbo run generate:types`
    const client: AnyApiClient = api.client;
    await client.POST("/api/v1/billing/subscription/reactivate", {});
    revalidatePath("/billing");
    return { status: "success", message: "Subscription reactivated." };
  } catch (error) {
    return handleActionError(error, "Unable to reactivate subscription.");
  }
}

export async function createPortalSessionAction(): Promise<
  ActionResponse & { portal_url?: string }
> {
  try {
    const api = await getServerApi();
    // TODO: use generated types after `turbo run generate:types`
    const client: AnyApiClient = api.client;
    const result = await client.POST("/api/v1/billing/portal-session", {});
    const data = result as { data?: { portal_url?: string } };
    return { status: "success", message: "", portal_url: data.data?.portal_url };
  } catch (error) {
    return handleActionError(error, "Unable to open billing portal.");
  }
}

export async function previewProrationAction(
  planId: string,
  billingPeriod: string,
): Promise<ActionResponse & { preview?: ProrationPreviewOut }> {
  try {
    const api = await getServerApi();
    const preview = await api.previewBillingProration(planId, billingPeriod);
    // No revalidatePath — proration preview is a read operation, does not mutate state
    return { status: "success", message: "", preview };
  } catch (error) {
    return handleActionError(error, "Unable to preview plan change.");
  }
}

export async function createCheckoutSessionAction(
  planId: string,
  billingPeriod: string,
): Promise<ActionResponse & { checkout_url?: string }> {
  try {
    const api = await getServerApi();
    // TODO: use generated types after `turbo run generate:types`
    const client: AnyApiClient = api.client;
    const headersList = await headers();
    const host = headersList.get("host") ?? "localhost:3000";
    const protocol = host.startsWith("localhost") ? "http" : "https";
    const origin = `${protocol}://${host}`;
    const result = await client.POST("/api/v1/billing/subscription/subscribe", {
      body: {
        plan_id: planId,
        billing_period: billingPeriod,
        success_url: `${origin}/billing/return?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${origin}/billing`,
      },
    });
    const data = result as { data?: { checkout_url?: string } };
    // No revalidatePath — checkout session creation does not mutate local state.
    // Subscription state updates via webhook after payment completes.
    return { status: "success", message: "", checkout_url: data.data?.checkout_url };
  } catch (error) {
    return handleActionError(error, "Unable to start checkout.");
  }
}
