const API_BASE_PATH = "/api/v1";

export function buildApiBaseUrl(value: string): string {
  return `${value.replace(/\/$/, "")}${API_BASE_PATH}`;
}
