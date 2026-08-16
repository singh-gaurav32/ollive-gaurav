import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listConversations, startConversation } from "../api/chat";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
  });
}

export function useStartConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: startConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
