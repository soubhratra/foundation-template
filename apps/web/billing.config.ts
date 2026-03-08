/**
 * billing.config.ts
 *
 * Single developer-facing customization surface for the billing module.
 * Components import from this file directly — no React Context needed.
 *
 * Usage:
 *   import { billingConfig } from '@/billing.config'
 *   (or from root: import { billingConfig } from 'billing.config')
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BillingPlanDisplay {
  /** Internal plan ID — must match BILLING_PLANS keys in Django settings */
  id: string;
  /** Display name shown in plan cards */
  name: string;
  /** Feature list for plan card bullet points */
  features: string[];
  /** Optional badge label shown on the plan card (e.g. "Most Popular") */
  badge?: string;
}

/**
 * All subscription states the billing page must handle.
 * Maps 1:1 to SubscriptionStatus values from the Django billing model.
 */
export type SubscriptionState =
  | "active"
  | "trialing"
  | "past_due"
  | "canceled"
  | "cancel_at_period_end"
  | "no_subscription";

/**
 * Action buttons that can be shown on the billing page.
 * Which actions appear depends on the current SubscriptionState (see BillingConfig.actions).
 */
export type BillingActionType = "upgrade" | "downgrade" | "cancel" | "reactivate" | "portal";

export interface BillingSection {
  /** Section identifier used in component logic to look up config */
  id: "plan_overview" | "plan_selection" | "payment_history";
  /** Whether this section renders at all — set visible: false to hide a section */
  visible: boolean;
  /** Heading text rendered above the section */
  heading: string;
}

export interface BillingConfig {
  /** Ordered list of sections to render on the /billing page */
  sections: BillingSection[];
  /** Plans to display in the plan selection section */
  plans: BillingPlanDisplay[];
  /**
   * Maps each subscription state to the list of action buttons to show.
   * The order of actions in each array controls the button render order.
   */
  actions: Record<SubscriptionState, BillingActionType[]>;
  /** All user-visible copy strings for the billing UI */
  copy: {
    /** Title for the cancel subscription confirmation modal */
    cancelModalTitle: string;
    /**
     * Body copy for the cancel confirmation modal.
     * Receives the period-end date string (formatted by caller) as an argument.
     */
    cancelModalBody: (periodEnd: string) => string;
    /** Label for the destructive "confirm cancel" button */
    cancelConfirmButton: string;
    /** Label for the "keep subscription" (dismiss) button */
    cancelKeepButton: string;
    /** Title for the proration preview modal shown before plan change */
    prorationModalTitle: string;
    /** Label for the reactivate subscription button */
    reactivateButton: string;
    /** Label for the Stripe Customer Portal redirect button */
    portalButton: string;
    /** Body copy for the past-due alert banner shown in the dashboard layout */
    pastDueBannerBody: string;
    /** CTA label for the past-due banner's action button */
    pastDueBannerCta: string;
    /** Empty state message for the invoice table when no invoices exist */
    emptyInvoices: string;
  };
}

// ---------------------------------------------------------------------------
// Default config
// ---------------------------------------------------------------------------

export const billingConfig: BillingConfig = {
  sections: [
    {
      id: "plan_overview",
      visible: true,
      heading: "Current Plan",
    },
    {
      id: "plan_selection",
      visible: true,
      heading: "Available Plans",
    },
    {
      id: "payment_history",
      visible: true,
      heading: "Payment History",
    },
  ],

  plans: [
    {
      id: "free",
      name: "Free",
      features: ["Up to 3 projects", "Community support"],
    },
    {
      id: "pro",
      name: "Pro",
      features: ["Unlimited projects", "Priority support", "API access"],
      badge: "Most Popular",
    },
    {
      id: "enterprise",
      name: "Enterprise",
      features: ["Everything in Pro", "Dedicated support", "Custom contracts", "SLA"],
    },
  ],

  actions: {
    active: ["upgrade", "downgrade", "cancel", "portal"],
    trialing: ["upgrade", "cancel", "portal"],
    past_due: ["portal"],
    canceled: [],
    cancel_at_period_end: ["reactivate", "portal"],
    no_subscription: [],
  },

  copy: {
    cancelModalTitle: "Cancel subscription?",
    cancelModalBody: (periodEnd) =>
      `Your plan cancels on ${periodEnd}. You keep full access until then.`,
    cancelConfirmButton: "Cancel subscription",
    cancelKeepButton: "Keep subscription",
    prorationModalTitle: "Confirm plan change",
    reactivateButton: "Reactivate",
    portalButton: "Update payment method",
    pastDueBannerBody: "Your payment failed. Update your payment method to continue access.",
    pastDueBannerCta: "Update payment method",
    emptyInvoices: "No invoices yet.",
  },
};
