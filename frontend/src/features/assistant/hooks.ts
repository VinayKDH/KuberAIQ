import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "./api";
import type { ChatRequest } from "./types";

export function useChatMutation() {
  return useMutation({
    mutationFn: (payload: ChatRequest) => sendChatMessage(payload),
  });
}
