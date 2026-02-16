/**
 * Chat component for sending commands and viewing responses.
 */

import React, { useState, useEffect, useRef } from "react";
import { useBrowserMindStore } from "../lib/store";
import { MessageList } from "./MessageList";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Send, Loader2 } from "lucide-react";

export function Chat() {
  const [input, setInput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    currentSession,
    currentAssistant,
    connectionStatus,
    sendCommand,
  } = useBrowserMindStore();

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isExecuting) return;

    if (!currentAssistant) {
      alert("No assistant selected. Please create or activate an assistant.");
      return;
    }

    if (!currentSession) {
      alert("No active session. Please refresh the page.");
      return;
    }

    if (connectionStatus !== "connected") {
      alert("Not connected to backend. Please check your connection.");
      return;
    }

    try {
      setIsExecuting(true);
      await sendCommand(input, currentAssistant.id, currentSession.id);
      setInput("");
    } catch (error) {
      console.error("Failed to send command:", error);
      alert(`Error: ${error.message || "Failed to send command"}`);
    } finally {
      setIsExecuting(false);
      inputRef.current?.focus();
    }
  };

  const isDisabled =
    !currentAssistant ||
    !currentSession ||
    connectionStatus !== "connected" ||
    isExecuting;

  return (
    <div className="h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isDisabled
                ? "Connect to start chatting..."
                : "Type a command..."
            }
            disabled={isDisabled}
            className="flex-1"
          />
          <Button type="submit" disabled={isDisabled || !input.trim()}>
            {isExecuting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {/* Status message */}
        {!currentAssistant && (
          <p className="text-xs text-muted-foreground mt-2">
            No assistant selected
          </p>
        )}
        {currentAssistant && connectionStatus !== "connected" && (
          <p className="text-xs text-destructive mt-2">
            Disconnected from backend
          </p>
        )}
      </div>
    </div>
  );
}
