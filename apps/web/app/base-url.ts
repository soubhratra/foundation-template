export function buildApiBaseUrl(value: string): string {
  return value.replace(/\/$/, "");
}
