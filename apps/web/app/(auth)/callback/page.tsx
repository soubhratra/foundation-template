"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@repo/business-logic";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const { refetch } = useAuth();

  useEffect(() => {
    void refetch().then((result) => {
      if (result.data?.id) {
        router.replace("/dashboard");
      } else {
        router.replace("/auth/error?error=unknown");
      }
    });
  }, [refetch, router]);

  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm text-muted-foreground">Completing sign-in...</p>
    </div>
  );
}
