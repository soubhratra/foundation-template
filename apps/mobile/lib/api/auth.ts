import {
  useMutation,
  type UseMutationOptions,
  type UseMutationResult,
} from "@tanstack/react-query";

import { useAuthContext, type AuthContextValue } from "@repo/business-logic";
import type { PasswordResetInput, SignupInput } from "@repo/validation";

interface AuthMutationResponse {
  readonly detail?: string;
  readonly message?: string;
}

type CreateAccountVariables = SignupInput;
type PasswordResetVariables = PasswordResetInput;

type GenericClient = {
  POST: (
    path: string,
    init: {
      readonly body?: unknown;
    },
  ) => Promise<{ data?: unknown; error?: unknown }>;
};

export function useCreateAccountMutation(
  options?: UseMutationOptions<AuthMutationResponse, Error, CreateAccountVariables>,
): UseMutationResult<AuthMutationResponse, Error, CreateAccountVariables> {
  const auth = useAuthContext();
  return useMutation<AuthMutationResponse, Error, CreateAccountVariables>({
    mutationFn: async (values) => {
      return mutateAuthEndpoint(auth, "/api/v1/auth/account/", values, {
        fallbackMessage: "Unable to create your account right now.",
      });
    },
    ...options,
  });
}

export function usePasswordResetMutation(
  options?: UseMutationOptions<AuthMutationResponse, Error, PasswordResetVariables>,
): UseMutationResult<AuthMutationResponse, Error, PasswordResetVariables> {
  const auth = useAuthContext();
  return useMutation<AuthMutationResponse, Error, PasswordResetVariables>({
    mutationFn: async (values) => {
      return mutateAuthEndpoint(auth, "/api/v1/auth/password/reset/", values, {
        fallbackMessage: "Unable to start the password reset flow.",
      });
    },
    ...options,
  });
}

interface MutationOptions {
  readonly fallbackMessage: string;
}

async function mutateAuthEndpoint<TBody>(
  auth: AuthContextValue,
  path: string,
  body: TBody,
  options: MutationOptions,
): Promise<AuthMutationResponse> {
  const client = auth.client as GenericClient;
  try {
    const result = await client.POST(path, { body });
    if (result.error) {
      throw new Error(extractErrorMessage(result.error, options.fallbackMessage));
    }
    return (result.data ?? {}) as AuthMutationResponse;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error(options.fallbackMessage);
  }
}

interface ErrorEnvelope {
  readonly error?: {
    readonly message?: string;
  };
  readonly detail?: string;
  readonly message?: string;
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object") {
    const envelope = payload as ErrorEnvelope;
    return envelope.error?.message ?? envelope.detail ?? envelope.message ?? fallback;
  }
  return fallback;
}
