import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation — useSearchParams returns a stub per test
const mockGet = vi.fn();
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockGet }),
}));

// Mock @/components/auth — render children and footer passthrough
vi.mock("@/components/auth", () => ({
  AuthCard: ({
    children,
    footer,
    description,
  }: {
    children: React.ReactNode;
    footer?: React.ReactNode;
    description?: string;
  }) => (
    <div>
      {description ? <p>{description}</p> : null}
      <div>{children}</div>
      {footer ? <div>{footer}</div> : null}
    </div>
  ),
  AuthLinks: ({
    items,
  }: {
    items: ReadonlyArray<{ href: string; label: string; prefix?: string }>;
  }) => (
    <div>
      {items.map((item) => (
        <a key={item.href} href={item.href}>
          {item.label}
        </a>
      ))}
    </div>
  ),
}));

import OAuthErrorPage from "@/app/(auth)/error/page";

describe("OAuthErrorPage", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("renders human-readable message for cancelled error code", () => {
    mockGet.mockReturnValue("cancelled");
    render(<OAuthErrorPage />);
    expect(screen.getByText(/you cancelled the sign-in/i)).toBeInTheDocument();
  });

  it("renders human-readable message for unknown error code", () => {
    mockGet.mockReturnValue("unknown");
    render(<OAuthErrorPage />);
    expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument();
  });

  it("renders human-readable message for denied error code", () => {
    mockGet.mockReturnValue("denied");
    render(<OAuthErrorPage />);
    expect(screen.getByText(/access was denied/i)).toBeInTheDocument();
  });

  it("renders a link back to the sign-in page with accessible text", () => {
    mockGet.mockReturnValue("unknown");
    render(<OAuthErrorPage />);
    expect(screen.getByRole("link", { name: /back to sign-in/i })).toHaveAttribute("href", "/");
  });

  it("falls back to the unknown message for an unrecognised error code", () => {
    mockGet.mockReturnValue("some_new_code");
    render(<OAuthErrorPage />);
    expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument();
  });
});
