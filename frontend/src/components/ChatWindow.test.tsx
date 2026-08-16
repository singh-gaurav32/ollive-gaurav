import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatWindow } from "./ChatWindow";
import * as chatApi from "../api/chat";

vi.mock("../api/chat");

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("ChatWindow", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(chatApi.resumeConversation).mockResolvedValue({
      conversation: { id: "c1", user_id: "u1", state: "active", created_at: "now", updated_at: "now" },
      messages: [{ id: "m1", conversation_id: "c1", role: "user", content: "hi", created_at: "now" }],
    });
  });

  it("renders existing message history", async () => {
    renderWithClient(<ChatWindow conversationId="c1" />);

    await waitFor(() => expect(screen.getByText("hi")).toBeInTheDocument());
  });

  it("streams tokens as they arrive and shows the cancel button while streaming", async () => {
    let capturedOnToken: ((content: string) => void) | undefined;
    vi.mocked(chatApi.sendMessage).mockImplementation(async (_id, _content, _signal, onToken) => {
      capturedOnToken = onToken;
      return new Promise(() => {}); // never resolves - simulates an in-flight stream
    });
    const user = userEvent.setup();

    renderWithClient(<ChatWindow conversationId="c1" />);
    await waitFor(() => expect(screen.getByText("hi")).toBeInTheDocument());

    await user.type(screen.getByPlaceholderText("Type a message..."), "hello");
    await user.click(screen.getByText("Send"));

    await waitFor(() => expect(screen.getByTestId("cancel-button")).toBeInTheDocument());

    act(() => capturedOnToken?.("Hi"));
    act(() => capturedOnToken?.(" there"));

    await waitFor(() => expect(screen.getByText("Hi there")).toBeInTheDocument());
  });

  it("cancel calls both the cancel endpoint and stops rendering new tokens", async () => {
    vi.mocked(chatApi.sendMessage).mockImplementation(async () => new Promise(() => {}));
    vi.mocked(chatApi.cancelConversation).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderWithClient(<ChatWindow conversationId="c1" />);
    await waitFor(() => expect(screen.getByText("hi")).toBeInTheDocument());
    await user.type(screen.getByPlaceholderText("Type a message..."), "hello");
    await user.click(screen.getByText("Send"));
    await waitFor(() => expect(screen.getByTestId("cancel-button")).toBeInTheDocument());

    await user.click(screen.getByTestId("cancel-button"));

    expect(chatApi.cancelConversation).toHaveBeenCalledWith("c1");
  });
});
