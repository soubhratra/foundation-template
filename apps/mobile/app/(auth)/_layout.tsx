import { Slot } from "expo-router";

import { AuthShell } from "@/components/auth";

export default function AuthLayout() {
  return (
    <AuthShell
      eyebrow="Secure access"
      title="Welcome to Foundation Mobile"
      description="Authenticate to continue into the workspace."
    >
      <Slot />
    </AuthShell>
  );
}
