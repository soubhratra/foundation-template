"use client";

import { type ComponentProps } from "react";

import { Toaster as SonnerToaster, toast } from "sonner";

type ToasterProps = ComponentProps<typeof SonnerToaster>;

function Toaster(props: ToasterProps) {
  return (
    <SonnerToaster
      position="top-center"
      richColors
      theme="system"
      closeButton
      {...props}
    />
  );
}

export { Toaster, toast };
