export interface ErrorEnvelope {
  error: {
    code?: string;
    message: string;
    details?: Record<string, unknown>;
  };
  status?: number;
}

export interface ApiErrorInit {
  code: string;
  message: string;
  status?: number;
  details?: Record<string, unknown>;
  cause?: unknown;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status?: number;
  readonly details?: Record<string, unknown>;

  constructor(init: ApiErrorInit) {
    super(init.message, { cause: init.cause });
    this.name = "ApiError";
    this.code = init.code;
    this.status = init.status;
    this.details = init.details;
  }
}

const DEFAULT_ERROR_CODE = "unknown_error";
const DEFAULT_ERROR_MESSAGE = "An unexpected error occurred";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function extractEnvelope(value: unknown): ErrorEnvelope | undefined {
  if (!isRecord(value)) {
    return undefined;
  }

  if (isRecord(value.error) && typeof value.error.message === "string") {
    return {
      error: {
        code: typeof value.error.code === "string" ? value.error.code : undefined,
        message: value.error.message,
        details: isRecord(value.error.details) ? (value.error.details as Record<string, unknown>) : undefined,
      },
      status: typeof value.status === "number"
        ? value.status
        : typeof (value.response as { status?: number } | undefined)?.status === "number"
          ? (value.response as { status: number }).status
          : undefined,
    } satisfies ErrorEnvelope;
  }

  if (typeof value.message === "string") {
    return {
      error: {
        code: typeof value.code === "string" ? value.code : undefined,
        message: value.message,
      },
      status: typeof value.status === "number" ? value.status : undefined,
    } satisfies ErrorEnvelope;
  }

  return undefined;
}

export function normalizeFetchError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  const envelope = extractEnvelope(error);
  if (envelope) {
    return new ApiError({
      code: envelope.error.code ?? DEFAULT_ERROR_CODE,
      message: envelope.error.message ?? DEFAULT_ERROR_MESSAGE,
      status: envelope.status,
      details: envelope.error.details,
      cause: error,
    });
  }

  const fallbackMessage = error instanceof Error ? error.message : DEFAULT_ERROR_MESSAGE;

  return new ApiError({
    code: DEFAULT_ERROR_CODE,
    message: fallbackMessage || DEFAULT_ERROR_MESSAGE,
    cause: error,
  });
}

export function unwrapResult<TData, TError = unknown>(result: { data?: TData; error?: TError }): TData {
  if (result.error) {
    throw normalizeFetchError(result.error);
  }

  if (typeof result.data === "undefined") {
    throw new ApiError({ code: DEFAULT_ERROR_CODE, message: DEFAULT_ERROR_MESSAGE });
  }

  return result.data;
}
