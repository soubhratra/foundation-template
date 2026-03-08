import { getServerApi } from "@/lib/api/server";
import {
  changePlanAction,
  cancelSubscriptionAction,
  reactivateSubscriptionAction,
  createPortalSessionAction,
  previewProrationAction,
} from "@/actions/billing-actions";
import { BillingClient } from "./billing-client";

export default async function BillingPage() {
  const api = await getServerApi();
  const [subscription, invoicesData] = await Promise.all([
    api.getBillingSubscription().catch(() => undefined),
    api.listBillingInvoices(10).catch(() => ({ invoices: [], total: 0 })),
  ]);

  return (
    <BillingClient
      subscription={subscription}
      invoices={invoicesData?.invoices ?? []}
      changePlanAction={changePlanAction}
      cancelSubscriptionAction={cancelSubscriptionAction}
      reactivateSubscriptionAction={reactivateSubscriptionAction}
      createPortalSessionAction={createPortalSessionAction}
      previewProrationAction={previewProrationAction}
    />
  );
}
