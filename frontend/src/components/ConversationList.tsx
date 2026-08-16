import { Link, useNavigate, useParams } from "react-router-dom";
import { useConversations, useStartConversation } from "../hooks/useConversations";

export function ConversationList() {
  const { data: conversations, isLoading } = useConversations();
  const startConversation = useStartConversation();
  const { conversationId: activeId } = useParams();
  const navigate = useNavigate();

  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
      <button
        onClick={() =>
          startConversation.mutate(undefined, {
            onSuccess: (conversation) => navigate(`/chat/${conversation.id}`),
          })
        }
        className="m-3 rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        + New conversation
      </button>
      <div className="flex-1 overflow-y-auto">
        {isLoading && <p className="px-3 text-sm text-gray-500">Loading...</p>}
        {conversations?.map((c) => (
          <Link
            key={c.id}
            to={`/chat/${c.id}`}
            data-testid={`conversation-${c.id}`}
            className={`block truncate px-3 py-2 text-sm ${
              c.id === activeId ? "bg-blue-100 text-blue-900" : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            {c.state === "cancelled" && <span className="mr-1 text-xs text-gray-400">(cancelled)</span>}
            {c.id.slice(0, 8)}
          </Link>
        ))}
      </div>
    </div>
  );
}
