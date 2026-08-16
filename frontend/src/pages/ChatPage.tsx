import { useParams } from "react-router-dom";
import { ConversationList } from "../components/ConversationList";
import { ChatWindow } from "../components/ChatWindow";

export function ChatPage() {
  const { conversationId } = useParams();

  return (
    <div className="flex h-[calc(100vh-53px)]">
      <ConversationList />
      {conversationId ? (
        <ChatWindow key={conversationId} conversationId={conversationId} />
      ) : (
        <div className="flex flex-1 items-center justify-center text-sm text-gray-500">
          Select or start a conversation
        </div>
      )}
    </div>
  );
}
