interface ErrorEnvelope {
  readonly error?: {
    readonly message?: string;
  };
  readonly detail?: string;
}

export async function postJson<TResponse>(
  path: string,
  body: unknown,
  init: RequestInit = {},
): Promise<TResponse> {
  const headers = buildHeaders(init.headers);
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  const response = await fetch(path, {
    method: "POST",
    credentials: "include",
    ...init,
    headers,
    body: JSON.stringify(body ?? {}),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return {} as TResponse;
  }

  const text = await response.text();
  if (!text) {
    return {} as TResponse;
  }
  return JSON.parse(text) as TResponse;
}

function buildHeaders(input?: HeadersInit): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (!input) {
    return headers;
  }

  if (input instanceof Headers) {
    input.forEach((value, key) => {
      headers[key] = value;
    });
    return headers;
  }

  if (Array.isArray(input)) {
    for (const [key, value] of input) {
      headers[key] = value;
    }
    return headers;
  }

  return { ...headers, ...(input as Record<string, string>) };
}

function getCsrfToken(): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookies = document.cookie?.split(";") ?? [];
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith("csrftoken=")) {
      return trimmed.substring("csrftoken=".length);
    }
  }
  return null;
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ErrorEnvelope;
    return payload.error?.message ?? payload.detail ?? response.statusText;
  } catch {
    return response.statusText || `Request failed with status ${response.status}`;
  }
}
