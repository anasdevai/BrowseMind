/**
 * Command Queue Component
 * Displays queued and executing commands with cancel functionality
 */

import React from "react";
import { useBrowserMindStore } from "~/lib/store";
import { Button } from "~/components/ui/button";
import { Card } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { X, Loader2 } from "lucide-react";

export function CommandQueue() {
  const { commands, queuedCount, executingCount, connectionStatus } =
    useBrowserMindStore();

  const handleCancelCommand = async (commandId: string) => {
    try {
      await chrome.runtime.sendMessage({
        type: "send_command",
        payload: {
          type: "cancel_command",
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          payload: {
            command_id: commandId,
          },
        },
      });
    } catch (error) {
      console.error("Error cancelling command:", error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "queued":
        return <Badge variant="secondary">Queued</Badge>;
      case "executing":
        return (
          <Badge variant="default" className="flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Executing
          </Badge>
        );
      case "completed":
        return <Badge variant="outline">Completed</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "cancelled":
        return <Badge variant="outline">Cancelled</Badge>;
      case "timeout":
        return <Badge variant="destructive">Timeout</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const activeCommands = commands.filter(
    (cmd) => cmd.status === "queued" || cmd.status === "executing"
  );

  if (activeCommands.length === 0) {
    return (
      <div className="text-center py-4 text-sm text-muted-foreground">
        No commands in queue
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium">Command Queue</h3>
        <div className="text-xs text-muted-foreground">
          {queuedCount} queued, {executingCount} executing
        </div>
      </div>

      {activeCommands.map((command) => (
        <Card key={command.id} className="p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {getStatusBadge(command.status)}
                <span className="text-xs text-muted-foreground">
                  {command.elapsed_time
                    ? `${Math.floor(command.elapsed_time)}s`
                    : ""}
                </span>
              </div>
              <div className="text-sm truncate">{command.text}</div>
            </div>

            {(command.status === "queued" || command.status === "executing") && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleCancelCommand(command.id)}
                disabled={connectionStatus !== "connected"}
                title="Cancel"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
