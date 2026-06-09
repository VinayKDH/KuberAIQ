import { useMutation } from "@tanstack/react-query";
import { confirmChatAction, sendChatMessage } from "./api";
import type { ChatRequest, ConfirmRequest } from "./types";

export function useChatMutation() {
  return useMutation({
    mutationFn: (payload: ChatRequest) => sendChatMessage(payload),
  });
}

export function useConfirmMutation() {
  return useMutation({
    mutationFn: (payload: ConfirmRequest) => confirmChatAction(payload),
  });
}
