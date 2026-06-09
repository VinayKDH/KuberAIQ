import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { ChatRequest, ChatResponse, ConfirmRequest } from "./types";

export function sendChatMessage(payload: ChatRequest) {
  return apiClient<ChatResponse>(API_PATHS.AI_CHAT, {
    method: "POST",
    body: payload,
  });
}

export function confirmChatAction(payload: ConfirmRequest) {
  return apiClient<ChatResponse>(API_PATHS.AI_CONFIRM, {
    method: "POST",
    body: payload,
  });
}
