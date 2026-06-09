"use client";

import { useRef, useState } from "react";
import { Bot, Mic, MicOff, Send, User } from "lucide-react";
import { AssistantDataCard } from "@/components/assistant/assistant-data-card";
import { ConfirmActionCard } from "@/components/assistant/confirm-action-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useChatMutation, useConfirmMutation } from "@/features/assistant/hooks";
import type { ChatMessage, PendingAction } from "@/features/assistant/types";
import {
  ASSISTANT_CANCEL_WORDS,
  ASSISTANT_CHANNEL,
  ASSISTANT_CONFIRM_WORDS,
} from "@/lib/constants";
import { cn } from "@/lib/utils";

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your KuberAIQ assistant. Ask me to create invoices, check overdue payments, or summarize your dashboard.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [listening, setListening] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const chatMutation = useChatMutation();
  const confirmMutation = useConfirmMutation();

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const appendAssistantMessage = (response: {
    message: string;
    intent?: string;
    data?: Record<string, unknown> | null;
    suggested_actions?: { label: string; value: string }[];
    requires_confirmation?: boolean;
    pending_action?: PendingAction | null;
  }) => {
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: response.message,
        timestamp: new Date(),
        intent: response.intent,
        data: response.data ?? null,
        suggestedActions: response.suggested_actions,
        requiresConfirmation: response.requires_confirmation,
        pendingAction: response.pending_action ?? null,
      },
    ]);
    setPendingAction(response.requires_confirmation ? response.pending_action ?? null : null);
    setTimeout(scrollToBottom, 100);
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || chatMutation.isPending || confirmMutation.isPending) return;

    const trimmed = text.trim();
    const normalized = trimmed.toLowerCase();

    if (pendingAction && sessionId) {
      if (ASSISTANT_CONFIRM_WORDS.has(normalized) || normalized === "confirm") {
        await handleConfirm();
        return;
      }
      if (ASSISTANT_CANCEL_WORDS.has(normalized) || normalized === "cancel") {
        handleCancel();
        return;
      }
    }

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await chatMutation.mutateAsync({
        message: trimmed,
        session_id: sessionId,
        channel: ASSISTANT_CHANNEL,
        pending_action:
          pendingAction && ASSISTANT_CONFIRM_WORDS.has(normalized) ? pendingAction : undefined,
      });

      setSessionId(response.session_id);
      appendAssistantMessage(response);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Something went wrong. Please try again.",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleConfirm = async () => {
    if (!sessionId || !pendingAction) return;
    try {
      const response = await confirmMutation.mutateAsync({
        session_id: sessionId,
        pending_action: pendingAction,
      });
      appendAssistantMessage(response);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Could not complete that action.",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleCancel = () => {
    setPendingAction(null);
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "Okay, I cancelled that action.",
        timestamp: new Date(),
      },
    ]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const isBusy = chatMutation.isPending || confirmMutation.isPending;

  const startVoiceInput = () => {
    type SpeechRecognitionCtor = new () => {
      lang: string;
      interimResults: boolean;
      maxAlternatives: number;
      onresult: ((event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void) | null;
      onerror: (() => void) | null;
      onend: (() => void) | null;
      start: () => void;
    };
    const win = window as unknown as {
      SpeechRecognition?: SpeechRecognitionCtor;
      webkitSpeechRecognition?: SpeechRecognitionCtor;
    };
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Voice input is not supported in this browser.",
          timestamp: new Date(),
        },
      ]);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    setListening(true);
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setInput(transcript);
      setListening(false);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognition.start();
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">AI Assistant</h2>
        <p className="text-muted-foreground">
          Natural language commands for invoices, collections, and reports
        </p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardHeader className="border-b py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">KuberAIQ Copilot</CardTitle>
              <CardDescription>Powered by LangGraph agents</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden p-0">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-3",
                  msg.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={cn(
                    "max-w-[80%] rounded-lg px-4 py-2 text-sm",
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted",
                  )}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.role === "assistant" && msg.intent && msg.data && (
                    <AssistantDataCard intent={msg.intent} data={msg.data} />
                  )}
                  {msg.role === "assistant" &&
                    i === messages.length - 1 &&
                    pendingAction &&
                    msg.requiresConfirmation && (
                    <ConfirmActionCard
                      pendingAction={pendingAction}
                      onConfirm={handleConfirm}
                      onCancel={handleCancel}
                      loading={confirmMutation.isPending}
                    />
                  )}
                  {msg.suggestedActions && msg.suggestedActions.length > 0 && !msg.requiresConfirmation && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {msg.suggestedActions.map((action) => (
                        <Button
                          key={action.value}
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => sendMessage(action.value)}
                          disabled={isBusy}
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
            {isBusy && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-lg bg-muted px-4 py-2 text-sm text-muted-foreground">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSubmit} className="border-t p-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="e.g. Show overdue invoices for ABC Traders"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(input);
                  }
                }}
                rows={2}
                className="min-h-[60px] resize-none"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-[60px] w-[60px] shrink-0"
                disabled={isBusy}
                onClick={startVoiceInput}
                aria-label={listening ? "Stop listening" : "Voice input"}
              >
                {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
              <Button
                type="submit"
                size="icon"
                className="h-[60px] w-[60px] shrink-0"
                disabled={!input.trim() || isBusy}
              >
                <Send className="h-4 w-4" />
                <span className="sr-only">Send</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
