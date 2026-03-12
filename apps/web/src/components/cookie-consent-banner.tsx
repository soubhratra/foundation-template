"use client";

import { useEffect, useRef, useState } from "react";

import posthog from "posthog-js";

import { Button } from "@/components/ui/button";

function initPostHogOnce(initialized: React.MutableRefObject<boolean>) {
  if (initialized.current) return;
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com",
    capture_pageview: false,
    capture_pageleave: true,
    session_recording: { maskAllInputs: true },
    loaded: (ph) => {
      if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) ph.opt_out_capturing();
    },
  });
  initialized.current = true;
}

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);
  const initialized = useRef(false);

  useEffect(() => {
    const consent = localStorage.getItem("analytics_consent");
    if (consent === null) {
      setVisible(true);
    } else if (consent === "granted") {
      initPostHogOnce(initialized);
    } else {
      posthog.opt_out_capturing();
    }
  }, []);

  function handleAccept() {
    localStorage.setItem("analytics_consent", "granted");
    initPostHogOnce(initialized);
    setVisible(false);
  }

  function handleDecline() {
    localStorage.setItem("analytics_consent", "denied");
    posthog.opt_out_capturing();
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background p-4">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          We use analytics to improve the app.{" "}
          <a href="/privacy" className="underline hover:text-foreground">
            Privacy Policy
          </a>
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleDecline}>
            Decline
          </Button>
          <Button size="sm" onClick={handleAccept}>
            Accept Analytics
          </Button>
        </div>
      </div>
    </div>
  );
}
