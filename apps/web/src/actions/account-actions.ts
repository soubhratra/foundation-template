"use server";

import { cookies } from "next/headers";

import { env } from "@/config/env";

const API_ORIGIN = env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
const CSRF_COOKIE_NAME = "csrftoken";
const DELETE_ACCOUNT_PATH = "/api/v1/account/";

export interface DeleteAccountResult {
  success: boolean;
  error?: string;
}

export async function deleteAccountAction(password: string): Promise<DeleteAccountResult> {
  const store = await cookies();
  const csrfToken = store.get(CSRF_COOKIE_NAME)?.value ?? null;
  const cookieHeader = serializeCookies(store);

  const url = `${API_ORIGIN}${DELETE_ACCOUNT_PATH}`;
  const headers = new Headers({ "Content-Type": "application/json" });
  if (cookieHeader) {
    headers.set("cookie", cookieHeader);
  }
  if (csrfToken) {
    headers.set("X-CSRFToken", csrfToken);
  }

  try {
    const response = await fetch(url, {
      method: "DELETE",
      headers,
      body: JSON.stringify({ password }),
      cache: "no-store",
    });

    if (response.status === 202) {
      return { success: true };
    }

    if (response.status === 400) {
      return { success: false, error: "Incorrect password." };
    }

    if (response.status === 401) {
      return { success: false, error: "Not authenticated. Please sign in again." };
    }

    return { success: false, error: "Something went wrong. Please try again." };
  } catch {
    return { success: false, error: "Something went wrong. Please try again." };
  }
}

type CookieStore = Awaited<ReturnType<typeof cookies>>;

function serializeCookies(store: CookieStore): string | null {
  const serialized = store
    .getAll()
    .map((cookie) => `${cookie.name}=${encodeURIComponent(cookie.value)}`)
    .join("; ");
  return serialized.length > 0 ? serialized : null;
}
