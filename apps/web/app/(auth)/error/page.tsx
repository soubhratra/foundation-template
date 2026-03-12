"use client";

import { useSearchParams } from "next/navigation";

import { AuthCard, AuthLinks } from "@/components/auth";

const ERROR_MESSAGES: Record<string, string> = {
  unknown: "An unexpected error occurred. Please try again.",
  cancelled: "You cancelled the sign-in. Try again when ready.",
  denied: "Access was denied by the provider. Please try again.",
  reauthentication_required: "Re-authentication required. Please sign in again.",
  signup_closed: "Account registration is currently closed.",
  permission_denied: "You do not have permission to sign in.",
};

export default function OAuthErrorPage() {
  const searchParams = useSearchParams();
  const errorCode = searchParams?.get("error") ?? "unknown";
  const message = ERROR_MESSAGES[errorCode] ?? ERROR_MESSAGES.unknown;

  return (
    <AuthCard
      eyebrow="Authentication error"
      title="Sign-in failed"
      description={message}
      footer={
        <AuthLinks
          items={[
            {
              prefix: "Ready to try again?",
              label: "Back to sign-in",
              href: "/",
            },
          ]}
        />
      }
    >
      <p className="text-center text-sm text-muted-foreground">
        Error code: <code className="font-mono">{errorCode}</code>
      </p>
    </AuthCard>
  );
}
