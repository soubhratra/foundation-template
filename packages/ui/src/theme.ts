export const theme = {
  colors: {
    background: "#0f172a",
    surface: "#1e293b",
    border: "#334155",
    primary: "#2563eb",
    primaryForeground: "#f8fafc",
    muted: "#94a3b8",
    text: "#e2e8f0",
    textMuted: "#cbd5f5",
    focus: "#7dd3fc",
    danger: "#f87171",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
  },
  radii: {
    sm: 6,
    md: 12,
    lg: 18,
    pill: 999,
  },
  typography: {
    fontFamily: "System",
    titleSize: 20,
    bodySize: 16,
    subtleSize: 14,
    captionSize: 12,
    letterSpacing: 0.2,
  },
  input: {
    height: 48,
  },
} as const;

export type Theme = typeof theme;
