import { useQuery, useQueryClient } from "@tanstack/react-query";
import { resumeConversation } from "../api/chat";

export function useMessages(conversationId: string | undefined) {
  return useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => resumeConversation(conversationId as string),
    enabled: !!conversationId,
  });
}

export function useInvalidateMessages() {
  const queryClient = useQueryClient();
  return (conversationId: string) => {
    queryClient.invalidateQueries({ queryKey: ["conversation", conversationId] });
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };
}
