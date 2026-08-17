import { useCallback, useEffect, useRef, useState } from "react";
import { cancelConversation, sendMessage } from "../api/chat";

interface UseChatStreamResult {
  streamingContent: string;
  isStreaming: boolean;
  pendingUserContent: string | null;
  send: (content: string) => Promise<void>;
  cancel: () => void;
}

export function useChatStream(
  conversationId: string,
  onComplete: () => void,
): UseChatStreamResult {
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  // Echoes the just-sent content immediately, before the round trip
  // completes - the backend persists the user message before it ever
  // touches the provider, but `data.messages` only reflects that once
  // onComplete's invalidate() refetches, which is after the full stream.
  const [pendingUserContent, setPendingUserContent] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cleanup on unmount mid-stream (Functional Design: "cleanup if the
  // component unmounts mid-stream") - navigating away shouldn't leave a
  // dangling read.
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const send = useCallback(
    async (content: string) => {
      setPendingUserContent(content);
      setStreamingContent("");
      setIsStreaming(true);
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        await sendMessage(conversationId, content, controller.signal, (token) => {
          setStreamingContent((prev) => prev + token);
        });
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          throw err;
        }
      } finally {
        setIsStreaming(false);
        setPendingUserContent(null);
        abortControllerRef.current = null;
        onComplete();
      }
    },
    [conversationId, onComplete],
  );

  // BR6: cancel stops the UI immediately (abort the local read) *and*
  // tells the backend to stop the in-flight provider call - neither
  // waits on the other.
  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    void cancelConversation(conversationId);
  }, [conversationId]);

  return { streamingContent, isStreaming, pendingUserContent, send, cancel };
}
