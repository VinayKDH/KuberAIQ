import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { ChatRequest, ChatResponse } from "./types";

export function sendChatMessage(payload: ChatRequest) {
  return apiClient<ChatResponse>(API_PATHS.AI_CHAT, {
    method: "POST",
    body: payload,
  });
}
