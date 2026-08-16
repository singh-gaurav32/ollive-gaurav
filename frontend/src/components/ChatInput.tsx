import { useState, type FormEvent } from "react";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (content: string) => void;
  disabled: boolean;
}) {
  const [content, setContent] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || disabled) return; // no empty/whitespace-only sends
    onSend(trimmed);
    setContent("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-200 p-3">
      <input
        value={content}
        onChange={(e) => setContent(e.target.value)}
        disabled={disabled}
        placeholder="Type a message..."
        className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={disabled || !content.trim()}
        className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300"
      >
        Send
      </button>
    </form>
  );
}
