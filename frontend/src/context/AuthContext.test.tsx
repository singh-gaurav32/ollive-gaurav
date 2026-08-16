import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthContext";
import * as authApi from "../api/auth";
import { ApiError } from "../api/client";

vi.mock("../api/auth");

function Probe() {
  const { user, loading, login, logout } = useAuth();
  if (loading) return <div>loading</div>;
  return (
    <div>
      <div data-testid="user">{user ? user.username : "none"}</div>
      <button onClick={() => login("alice")}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("starts with no user when the initial /auth/me check returns 401", async () => {
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("none"));
  });

  it("loads the current user when already logged in", async () => {
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      id: "1",
      username: "alice",
      created_at: "now",
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("alice"));
  });

  it("login sets the user", async () => {
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new ApiError(401, "Not authenticated"));
    vi.mocked(authApi.login).mockResolvedValue({ id: "1", username: "alice", created_at: "now" });
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("none"));

    await user.click(screen.getByText("login"));

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("alice"));
  });

  it("logout clears the user", async () => {
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      id: "1",
      username: "alice",
      created_at: "now",
    });
    vi.mocked(authApi.logout).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("alice"));

    await user.click(screen.getByText("logout"));

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("none"));
  });
});
