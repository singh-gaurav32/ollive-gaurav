import { apiFetch, apiJson } from "./client";
import type { Conversation, ConversationDetail } from "../types";

export function startConversation(): Promise<Conversation> {
  return apiJson("/conversations", { method: "POST" });
}

export function listConversations(): Promise<Conversation[]> {
  return apiJson("/conversations");
}

export function resumeConversation(conversationId: string): Promise<ConversationDetail> {
  return apiJson(`/conversations/${conversationId}/resume`, { method: "POST" });
}

export function cancelConversation(conversationId: string): Promise<void> {
  return apiJson(`/conversations/${conversationId}/cancel`, { method: "POST" });
}

/**
 * The streaming send-message call. POST with a JSON body rules out the
 * browser's native EventSource (GET-only) - fetch + ReadableStream reads
 * the SSE-framed response body manually instead (Functional Design's
 * decided-directly technical note).
 */
export async function sendMessage(
  conversationId: string,
  content: string,
  signal: AbortSignal,
  onToken: (content: string) => void,
): Promise<void> {
  const response = await apiFetch(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
    signal,
  });

  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const lines = frame.split("\n");
      const eventLine = lines.find((l) => l.startsWith("event:"));
      const dataLine = lines.find((l) => l.startsWith("data:"));
      const eventType = eventLine?.slice("event:".length).trim();
      const data = dataLine?.slice("data:".length).trim();

      if (eventType === "token" && data) {
        const parsed = JSON.parse(data) as { content: string };
        onToken(parsed.content);
      }
      if (eventType === "done") {
        return;
      }
    }
  }
}
