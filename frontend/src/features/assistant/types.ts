export interface SuggestedAction {
  label: string;
  value: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  intent?: string;
  data?: Record<string, unknown> | null;
  suggestedActions?: SuggestedAction[];
  requiresConfirmation?: boolean;
  pendingAction?: PendingAction | null;
}

export interface PendingAction {
  type: string;
  preview: Record<string, unknown>;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  channel: string;
  pending_action?: PendingAction | null;
}

export interface ConfirmRequest {
  session_id: string;
  pending_action: PendingAction;
}

export interface ChatResponse {
  session_id: string;
  intent: string;
  message: string;
  requires_confirmation: boolean;
  pending_action?: PendingAction | null;
  data?: Record<string, unknown> | null;
  suggested_actions?: SuggestedAction[];
}
