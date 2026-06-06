export interface SuggestedAction {
  label: string;
  value: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  suggestedActions?: SuggestedAction[];
  requiresConfirmation?: boolean;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  channel: string;
}

export interface ChatResponse {
  session_id: string;
  intent: string;
  message: string;
  requires_confirmation: boolean;
  pending_action?: unknown;
  data?: unknown;
  suggested_actions?: SuggestedAction[];
}
