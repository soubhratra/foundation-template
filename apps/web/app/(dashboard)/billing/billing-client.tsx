"use client";

import { useState } from "react";

import { toast } from "sonner";

import { billingConfig, type BillingActionType, type SubscriptionState } from "billing.config";
import type { ActionResponse } from "@/actions/profile-actions";
import type { SubscriptionDetailOut, InvoiceOut, ProrationPreviewOut } from "@/lib/api/server";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BillingClientProps {
  subscription: SubscriptionDetailOut | undefined;
  invoices: InvoiceOut[];
  changePlanAction: (planId: string, billingPeriod: string) => Promise<ActionResponse>;
  cancelSubscriptionAction: () => Promise<ActionResponse>;
  reactivateSubscriptionAction: () => Promise<ActionResponse>;
  createPortalSessionAction: () => Promise<ActionResponse & { portal_url?: string }>;
  previewProrationAction: (
    planId: string,
    billingPeriod: string,
  ) => Promise<ActionResponse & { preview?: ProrationPreviewOut }>;
  createCheckoutSessionAction: (
    planId: string,
    billingPeriod: string,
  ) => Promise<ActionResponse & { checkout_url?: string }>;
}

type SheetMode = "proration" | "cancel" | null;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function formatUnixDate(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function formatIsoDate(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function deriveSubscriptionState(
  subscription: SubscriptionDetailOut | undefined,
): SubscriptionState {
  if (!subscription) return "no_subscription";
  if (subscription.status === "canceled") return "canceled";
  if (subscription.cancel_at_period_end) return "cancel_at_period_end";
  return subscription.status as SubscriptionState;
}

function getPlanName(planId: string | null | undefined): string {
  if (!planId) return "No plan";
  const plan = billingConfig.plans.find((p) => p.id === planId);
  return plan?.name ?? planId;
}

// ---------------------------------------------------------------------------
// PDF download
// ---------------------------------------------------------------------------

async function downloadInvoicePdf(invoiceId: string): Promise<void> {
  const apiBase = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

  // Enqueue PDF generation
  const enqueueRes = await fetch(`${apiBase}/api/v1/billing/invoices/${invoiceId}/pdf`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": getCsrfToken() },
  });
  if (!enqueueRes.ok) throw new Error("Failed to start PDF generation");
  const { task_id } = (await enqueueRes.json()) as { task_id: string };

  // Poll until complete (max 30s)
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    const statusRes = await fetch(`${apiBase}/api/v1/billing/invoices/pdf-status/${task_id}`, {
      credentials: "include",
    });
    if (!statusRes.ok) throw new Error("Failed to poll PDF status");
    const data = (await statusRes.json()) as { status: string; pdf_base64?: string };
    if (data.status === "success" && data.pdf_base64) {
      const bytes = Uint8Array.from(atob(data.pdf_base64), (c) => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    if (data.status === "failure") throw new Error("PDF generation failed");
  }
  throw new Error("PDF generation timed out");
}

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function BillingClient({
  subscription,
  invoices,
  changePlanAction,
  cancelSubscriptionAction,
  reactivateSubscriptionAction,
  createPortalSessionAction,
  previewProrationAction,
  createCheckoutSessionAction,
}: BillingClientProps) {
  const [sheetMode, setSheetMode] = useState<SheetMode>(null);
  const [selectedPlan, setSelectedPlan] = useState<{ id: string; period: string } | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState<string | null>(null);
  const [prorationPreview, setProrationPreview] = useState<ProrationPreviewOut | null>(null);
  const [isPending, setIsPending] = useState(false);

  const subscriptionState = deriveSubscriptionState(subscription);
  const allowedActions: BillingActionType[] = billingConfig.actions[subscriptionState] ?? [];

  // -------------------------------------------------------------------------
  // Action handlers
  // -------------------------------------------------------------------------

  async function handlePlanSelect(planId: string, period: string) {
    setIsPending(true);
    const result = await previewProrationAction(planId, period);
    setIsPending(false);
    if (result.status === "error") {
      toast.error(result.message || "Unable to preview plan change.");
      return;
    }
    if (result.preview) {
      setProrationPreview(result.preview);
      setSelectedPlan({ id: planId, period });
      setSheetMode("proration");
    }
  }

  async function handleConfirmPlanChange() {
    if (!selectedPlan) return;
    setIsPending(true);
    const result = await changePlanAction(selectedPlan.id, selectedPlan.period);
    setIsPending(false);
    if (result.status === "success") {
      toast.success("Plan updated.");
      setSheetMode(null);
      setSelectedPlan(null);
      setProrationPreview(null);
    } else {
      toast.error(result.message || "Unable to change plan.");
    }
  }

  async function handleCancelConfirm() {
    setIsPending(true);
    const result = await cancelSubscriptionAction();
    setIsPending(false);
    if (result.status === "success") {
      toast.success("Subscription cancelled.");
      setSheetMode(null);
    } else {
      toast.error(result.message || "Unable to cancel subscription.");
    }
  }

  async function handleReactivate() {
    setIsPending(true);
    const result = await reactivateSubscriptionAction();
    setIsPending(false);
    if (result.status === "success") {
      toast.success("Subscription reactivated.");
    } else {
      toast.error(result.message || "Unable to reactivate subscription.");
    }
  }

  async function handlePortal() {
    setIsPending(true);
    const result = await createPortalSessionAction();
    setIsPending(false);
    if (result.status === "success" && result.portal_url) {
      window.location.href = result.portal_url;
    } else {
      toast.error(result.message || "Unable to open billing portal.");
    }
  }

  async function handleSubscribe(planId: string, period: string) {
    setIsPending(true);
    const result = await createCheckoutSessionAction(planId, period);
    setIsPending(false);
    if (result.status === "success" && result.checkout_url) {
      window.location.href = result.checkout_url;
    } else {
      toast.error(result.message || "Unable to start checkout.");
    }
  }

  // -------------------------------------------------------------------------
  // Sections
  // -------------------------------------------------------------------------

  const planOverviewSection = billingConfig.sections.find((s) => s.id === "plan_overview");
  const planSelectionSection = billingConfig.sections.find((s) => s.id === "plan_selection");
  const paymentHistorySection = billingConfig.sections.find((s) => s.id === "payment_history");

  return (
    <div className="flex flex-col gap-8">
      {/* ------------------------------------------------------------------ */}
      {/* Plan overview                                                        */}
      {/* ------------------------------------------------------------------ */}
      {planOverviewSection?.visible && (
        <section>
          <h2 className="mb-4 text-xl font-semibold">{planOverviewSection.heading}</h2>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-4">
                <CardTitle>
                  {subscription ? getPlanName(subscription.plan_id) : "Free plan"}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {subscription?.status && (
                    <Badge variant={subscription.status === "active" ? "default" : "secondary"}>
                      {subscription.status}
                    </Badge>
                  )}
                  {subscription?.cancel_at_period_end && (
                    <Badge variant="outline">
                      Cancels {formatIsoDate(subscription.current_period_end)}
                    </Badge>
                  )}
                </div>
              </div>
              {subscription?.billing_period && (
                <CardDescription className="capitalize">
                  {subscription.billing_period} billing
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              {subscription?.current_period_end && !subscription.cancel_at_period_end && (
                <p className="text-sm text-muted-foreground">
                  Renews {formatIsoDate(subscription.current_period_end)}
                </p>
              )}
              {!subscription && (
                <p className="text-sm text-muted-foreground">
                  No active subscription. Upgrade to a paid plan below.
                </p>
              )}
              {/* Action buttons for current plan overview */}
              {allowedActions.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {allowedActions.includes("reactivate") && (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleReactivate}
                      disabled={isPending}
                    >
                      {billingConfig.copy.reactivateButton}
                    </Button>
                  )}
                  {allowedActions.includes("cancel") && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSheetMode("cancel")}
                      disabled={isPending}
                    >
                      Cancel subscription
                    </Button>
                  )}
                  {allowedActions.includes("portal") && (
                    <Button variant="outline" size="sm" onClick={handlePortal} disabled={isPending}>
                      {billingConfig.copy.portalButton}
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Plan selection                                                       */}
      {/* ------------------------------------------------------------------ */}
      {planSelectionSection?.visible && (
        <section>
          <h2 className="mb-4 text-xl font-semibold">{planSelectionSection.heading}</h2>
          <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2">
            {billingConfig.plans.map((plan) => {
              const isCurrent =
                plan.id === subscription?.plan_id || (!subscription && plan.id === "free"); // free-tier fallback
              const canUpgrade = allowedActions.includes("upgrade");
              const canDowngrade = allowedActions.includes("downgrade");
              const canSubscribe = allowedActions.includes("subscribe");
              const showButton = !isCurrent && (canUpgrade || canDowngrade || canSubscribe);
              const billingPeriod = subscription?.billing_period ?? "monthly";

              return (
                <Card key={plan.id} className={isCurrent ? "border-primary" : undefined}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle>{plan.name}</CardTitle>
                      {plan.badge && (
                        <Badge variant="secondary" className="shrink-0">
                          {plan.badge}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="mb-4 space-y-1">
                      {plan.features.map((feature) => (
                        <li key={feature} className="text-sm text-muted-foreground">
                          {feature}
                        </li>
                      ))}
                    </ul>
                    {isCurrent ? (
                      <Button variant="outline" size="sm" disabled>
                        Current plan
                      </Button>
                    ) : showButton ? (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() =>
                          canSubscribe
                            ? handleSubscribe(plan.id, billingPeriod)
                            : handlePlanSelect(plan.id, billingPeriod)
                        }
                        disabled={isPending}
                      >
                        {canSubscribe ? `Subscribe to ${plan.name}` : `Select ${plan.name}`}
                      </Button>
                    ) : null}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Payment history                                                      */}
      {/* ------------------------------------------------------------------ */}
      {paymentHistorySection?.visible && (
        <section>
          <h2 className="mb-4 text-xl font-semibold">{paymentHistorySection.heading}</h2>
          <Card>
            <CardContent className="p-0">
              {invoices.length === 0 ? (
                <p className="p-6 text-sm text-muted-foreground">
                  {billingConfig.copy.emptyInvoices}
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Invoice</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.invoice_id}>
                        <TableCell className="text-sm">{formatUnixDate(invoice.created)}</TableCell>
                        <TableCell className="text-sm">{formatCents(invoice.amount)}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {invoice.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invoice.invoice_url ? (
                            <a
                              href={invoice.invoice_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm underline hover:no-underline"
                            >
                              Download
                            </a>
                          ) : (
                            <button
                              className="text-sm underline hover:no-underline disabled:opacity-50 disabled:cursor-not-allowed"
                              disabled={downloadingPdf === invoice.invoice_id}
                              onClick={async () => {
                                setDownloadingPdf(invoice.invoice_id);
                                try {
                                  await downloadInvoicePdf(invoice.invoice_id);
                                } catch {
                                  toast.error("Failed to download PDF. Please try again.");
                                } finally {
                                  setDownloadingPdf(null);
                                }
                              }}
                            >
                              {downloadingPdf === invoice.invoice_id
                                ? "Generating…"
                                : "Download PDF"}
                            </button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Proration sheet                                                      */}
      {/* ------------------------------------------------------------------ */}
      <Sheet open={sheetMode === "proration"} onOpenChange={(open) => !open && setSheetMode(null)}>
        <SheetContent side="bottom" className="mx-auto max-w-md">
          <SheetHeader>
            <SheetTitle>{billingConfig.copy.prorationModalTitle}</SheetTitle>
          </SheetHeader>
          {prorationPreview && (
            <div className="my-4 space-y-2">
              <p className="text-sm">
                <span className="font-medium">Charged today:</span>{" "}
                {formatCents(prorationPreview.amount_due_now)}
              </p>
              <p className="text-sm">
                <span className="font-medium">Next renewal:</span>{" "}
                {formatCents(prorationPreview.next_invoice_total)} on{" "}
                {formatUnixDate(prorationPreview.proration_date)}
              </p>
            </div>
          )}
          <SheetFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setSheetMode(null)} disabled={isPending}>
              Cancel
            </Button>
            <Button onClick={handleConfirmPlanChange} disabled={isPending}>
              Confirm change
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* ------------------------------------------------------------------ */}
      {/* Cancel sheet                                                         */}
      {/* ------------------------------------------------------------------ */}
      <Sheet open={sheetMode === "cancel"} onOpenChange={(open) => !open && setSheetMode(null)}>
        <SheetContent side="bottom" className="mx-auto max-w-md">
          <SheetHeader>
            <SheetTitle>{billingConfig.copy.cancelModalTitle}</SheetTitle>
          </SheetHeader>
          <p className="my-4 text-sm text-muted-foreground">
            {billingConfig.copy.cancelModalBody(formatIsoDate(subscription?.current_period_end))}
          </p>
          <SheetFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setSheetMode(null)} disabled={isPending}>
              {billingConfig.copy.cancelKeepButton}
            </Button>
            <Button variant="destructive" onClick={handleCancelConfirm} disabled={isPending}>
              {billingConfig.copy.cancelConfirmButton}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
