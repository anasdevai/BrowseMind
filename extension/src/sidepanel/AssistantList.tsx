/**
 * Assistant List Component
 * Displays all assistants with status badges and actions
 */

import React from "react";
import { useBrowserMindStore } from "~/lib/store";
import { Button } from "~/components/ui/button";
import { Card } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { Trash2, Power, PowerOff } from "lucide-react";

export function AssistantList() {
  const { assistants, activeAssistantId, connectionStatus } = useBrowserMindStore();

  const handleActivate = async (assistantId: string) => {
    // Send activate_assistant message
    await chrome.runtime.sendMessage({
      type: "send_command",
      payload: {
        type: "activate_assistant",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        payload: {
          assistant_id: assistantId,
        },
      },
    });
  };

  const handleDeactivate = async (assistantId: string) => {
    // Send deactivate_assistant message
    await chrome.runtime.sendMessage({
      type: "send_command",
      payload: {
        type: "deactivate_assistant",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        payload: {
          assistant_id: assistantId,
        },
      },
    });
  };

  const handleDelete = async (assistantId: string) => {
    if (!confirm("Are you sure you want to delete this assistant?")) {
      return;
    }

    // Send delete_assistant message
    await chrome.runtime.sendMessage({
      type: "send_command",
      payload: {
        type: "delete_assistant",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        payload: {
          assistant_id: assistantId,
        },
      },
    });
  };

  if (assistants.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No assistants yet. Create one to get started.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {assistants.map((assistant) => (
        <Card key={assistant.id} className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium">{assistant.name}</h3>
                {assistant.status === "active" && (
                  <Badge variant="default">Active</Badge>
                )}
                {assistant.status === "inactive" && (
                  <Badge variant="secondary">Inactive</Badge>
                )}
              </div>
              {assistant.instructions && (
                <p className="text-sm text-muted-foreground mb-2">
                  {assistant.instructions}
                </p>
              )}
              <div className="text-xs text-muted-foreground">
                {assistant.capability_count || 0} capabilities
              </div>
            </div>

            <div className="flex gap-1">
              {assistant.status === "inactive" ? (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleActivate(assistant.id)}
                  disabled={connectionStatus !== "connected"}
                  title="Activate"
                >
                  <Power className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleDeactivate(assistant.id)}
                  disabled={connectionStatus !== "connected"}
                  title="Deactivate"
                >
                  <PowerOff className="h-4 w-4" />
                </Button>
              )}

              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(assistant.id)}
                disabled={connectionStatus !== "connected"}
                title="Delete"
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
