import { useMessages, useInvalidateMessages } from "../hooks/useMessages";
import { useChatStream } from "../hooks/useChatStream";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { CancelButton } from "./CancelButton";

export function ChatWindow({ conversationId }: { conversationId: string }) {
  const { data, isLoading } = useMessages(conversationId);
  const invalidate = useInvalidateMessages();
  const { streamingContent, isStreaming, pendingUserContent, send, cancel } = useChatStream(
    conversationId,
    () => invalidate(conversationId),
  );

  if (isLoading) {
    return <div className="flex-1 p-4 text-sm text-gray-500">Loading conversation...</div>;
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {data?.messages.map((m) => (
          <MessageBubble key={m.id} role={m.role} content={m.content} />
        ))}
        {pendingUserContent !== null && <MessageBubble role="user" content={pendingUserContent} />}
        {isStreaming && <MessageBubble role="assistant" content={streamingContent || "..."} />}
      </div>
      <div className="flex items-center gap-2 px-3">
        {isStreaming && <CancelButton onCancel={cancel} />}
      </div>
      <ChatInput onSend={(content) => void send(content)} disabled={isStreaming} />
    </div>
  );
}
