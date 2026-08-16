import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "./LoginPage";
import { AuthProvider } from "../context/AuthContext";
import * as authApi from "../api/auth";
import { ApiError } from "../api/client";

vi.mock("../api/auth");

describe("LoginPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new ApiError(401, "Not authenticated"));
  });

  it("lists the demo users and logs in on click", async () => {
    vi.mocked(authApi.listDemoUsers).mockResolvedValue([
      { id: "1", username: "alice", created_at: "now" },
      { id: "2", username: "bob", created_at: "now" },
    ]);
    vi.mocked(authApi.login).mockResolvedValue({ id: "1", username: "alice", created_at: "now" });
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId("login-alice")).toBeInTheDocument());
    expect(screen.getByTestId("login-bob")).toBeInTheDocument();

    await user.click(screen.getByTestId("login-alice"));

    await waitFor(() => expect(authApi.login).toHaveBeenCalledWith("alice"));
  });
});
