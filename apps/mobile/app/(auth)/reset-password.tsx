import { useMemo, useState } from "react";

import { useLocalSearchParams } from "expo-router";
import { useForm } from "react-hook-form";

import {
  AuthFooter,
  AuthForm,
  AuthFormField,
  AuthFormHint,
  type AuthFormStatus,
} from "@/components/auth";
import {
  createZodFormOptions,
  passwordResetSchema,
  type PasswordResetInput,
} from "@repo/validation";

import { usePasswordResetMutation } from "@/lib/api/auth";

const defaultValues: PasswordResetInput = {
  email: "",
};

export default function ResetPasswordScreen() {
  const params = useLocalSearchParams();
  const [status, setStatus] = useState<AuthFormStatus | null>(null);
  const redirectHint = useMemo(() => resolveRedirect(params.redirect), [params.redirect]);
  const form = useForm<PasswordResetInput>(
    createZodFormOptions(passwordResetSchema, { defaultValues }),
  );
  const mutation = usePasswordResetMutation();

  const handleSubmit = async (values: PasswordResetInput) => {
    setStatus(null);
    try {
      await mutation.mutateAsync(values);
      form.reset(values);
      setStatus({
        variant: "success",
        title: "Check your inbox",
        description: "Follow the link we sent to choose a new password.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to send the reset link.";
      setStatus({
        variant: "error",
        title: "Reset failed",
        description: message,
      });
    }
  };

  return (
    <AuthForm
      form={form}
      submitLabel="Send reset link"
      isSubmitting={mutation.isPending}
      onSubmit={handleSubmit}
      status={status}
      footer={
        <AuthFooter
          links={[
            { prefix: "Ready to sign in?", label: "Return to login", href: "/(auth)/sign-in" },
            { prefix: "Need an account?", label: "Create one", href: "/(auth)/sign-up" },
          ]}
        />
      }
    >
      <AuthFormField
        control={form.control}
        name="email"
        label="Email"
        inputProps={{
          keyboardType: "email-address",
          autoCapitalize: "none",
          autoComplete: "email",
          textContentType: "emailAddress",
          placeholder: "founder@workspace.dev",
        }}
      />
      {redirectHint ? (
        <AuthFormHint
          title="After reset"
          description={`We'll send you back to ${redirectHint}`}
        />
      ) : null}
    </AuthForm>
  );
}

function resolveRedirect(value?: string | string[]): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}
