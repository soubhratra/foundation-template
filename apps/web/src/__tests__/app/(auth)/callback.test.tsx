import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation
const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  useSearchParams: () => ({ get: vi.fn() }),
}));

// Mock @repo/business-logic
const mockRefetch = vi.fn();
vi.mock("@repo/business-logic", () => ({
  useAuth: () => ({ refetch: mockRefetch }),
}));

import OAuthCallbackPage from "../../../app/(auth)/callback/page";

describe("OAuthCallbackPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state on mount", () => {
    mockRefetch.mockResolvedValue({ data: undefined });
    render(<OAuthCallbackPage />);
    expect(screen.getByText(/completing sign-in/i)).toBeInTheDocument();
  });

  it("calls refetch on mount", async () => {
    mockRefetch.mockResolvedValue({ data: undefined });
    render(<OAuthCallbackPage />);
    await waitFor(() => expect(mockRefetch).toHaveBeenCalledTimes(1));
  });

  it("redirects to /dashboard when refetch resolves with a user", async () => {
    mockRefetch.mockResolvedValue({ data: { id: "user-1", email: "test@example.com" } });
    render(<OAuthCallbackPage />);
    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/dashboard"));
  });

  it("redirects to /auth/error?error=unknown when refetch resolves with no user", async () => {
    mockRefetch.mockResolvedValue({ data: undefined });
    render(<OAuthCallbackPage />);
    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/auth/error?error=unknown"));
  });
});
