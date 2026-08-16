import { useCallback, useEffect, useRef, useState } from "react";
import { cancelConversation, sendMessage } from "../api/chat";

interface UseChatStreamResult {
  streamingContent: string;
  isStreaming: boolean;
  send: (content: string) => Promise<void>;
  cancel: () => void;
}

export function useChatStream(
  conversationId: string,
  onComplete: () => void,
): UseChatStreamResult {
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
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

  return { streamingContent, isStreaming, send, cancel };
}
