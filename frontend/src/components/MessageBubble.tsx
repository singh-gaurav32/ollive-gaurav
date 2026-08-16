import type { MessageRole } from "../types";

export function MessageBubble({ role, content }: { role: MessageRole; content: string }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-lg rounded-lg px-4 py-2 text-sm ${
          isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
