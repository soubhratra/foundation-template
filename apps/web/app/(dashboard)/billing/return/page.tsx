"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function BillingReturnPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (sessionId) {
      const timer = setTimeout(() => router.replace("/billing"), 3000);
      return () => clearTimeout(timer);
    }
  }, [sessionId, router]);

  if (!sessionId) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-muted-foreground">No checkout session found.</p>
        <Link href="/billing" className="text-sm underline">
          Return to billing
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <h1 className="text-2xl font-semibold">Subscription activated</h1>
      <p className="text-muted-foreground">Redirecting to your billing page in a moment...</p>
      <Link href="/billing" className="text-sm underline">
        Go now
      </Link>
    </div>
  );
}
