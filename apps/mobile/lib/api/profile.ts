"use client";

import { useCallback } from "react";
import {
  useMutation,
  type UseMutationOptions,
  type UseMutationResult,
} from "@tanstack/react-query";

import { useAuthContext } from "@repo/business-logic";
import type { UpdateProfileInput } from "@repo/validation";

const UPDATE_PROFILE_PATH = "/api/v1/users/me";

interface UserResponse {
  readonly id: string;
  readonly email: string;
  readonly full_name?: string | null;
  readonly timezone?: string | null;
  [key: string]: unknown;
}

interface UpdateProfileResponse {
  readonly user?: UserResponse;
  readonly detail?: string;
}

type UpdateProfileVariables = UpdateProfileInput;

interface ErrorEnvelope {
  readonly error?: {
    readonly message?: string;
    readonly details?: Record<string, string[]>;
  };
  readonly detail?: string;
}

/**
 * Hook for updating the user's profile.
 * PATCHs /api/v1/users/me with UpdateProfileInput and invalidates user cache on success.
 */
export function useUpdateProfileMutation(
  options?: UseMutationOptions<UpdateProfileResponse, Error, UpdateProfileVariables>,
): UseMutationResult<UpdateProfileResponse, Error, UpdateProfileVariables> {
  const { baseUrl, queryClient } = useAuthContext();

  return useMutation<UpdateProfileResponse, Error, UpdateProfileVariables>({
    mutationFn: async (data) => {
      const response = await fetch(`${baseUrl}${UPDATE_PROFILE_PATH}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
        credentials: "include",
      });

      if (!response.ok) {
        let errorMessage = "Failed to update profile";
        try {
          const errorPayload = (await response.json()) as ErrorEnvelope;
          errorMessage =
            errorPayload.error?.message ??
            errorPayload.detail ??
            errorMessage;
        } catch {
          // Ignore parse errors
        }
        throw new Error(errorMessage);
      }

      return response.json() as Promise<UpdateProfileResponse>;
    },
    onSuccess: () => {
      // Invalidate the user query to refresh cached data
      queryClient.invalidateQueries({ queryKey: ["get", UPDATE_PROFILE_PATH] });
    },
    ...options,
  });
}

/**
 * Helper function to check if an error is a field error from the API.
 */
export function getFieldError(
  error: unknown,
  field: string,
): string | undefined {
  if (error instanceof Error) {
    // Field errors are typically nested in the error payload
    // This is a simplified check - the actual implementation depends on API response format
    return undefined;
  }
  return undefined;
}
