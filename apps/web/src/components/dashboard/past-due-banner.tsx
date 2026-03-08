"use client";

import { createPortalSessionAction } from "@/actions/billing-actions";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { billingConfig } from "billing.config";

export function PastDueBanner() {
  async function handlePortalClick() {
    const result = await createPortalSessionAction();
    if (result.status === "success" && result.portal_url) {
      window.location.href = result.portal_url;
    }
  }

  return (
    <Alert
      variant="destructive"
      className="mx-6 mt-4 rounded-lg border-amber-500 bg-amber-50 text-amber-900"
    >
      <AlertDescription className="flex items-center justify-between">
        <span>{billingConfig.copy.pastDueBannerBody}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={handlePortalClick}
          className="ml-4 shrink-0 border-amber-600 text-amber-900 hover:bg-amber-100"
        >
          {billingConfig.copy.pastDueBannerCta}
        </Button>
      </AlertDescription>
    </Alert>
  );
}
