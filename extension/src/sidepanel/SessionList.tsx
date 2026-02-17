/**
 * Session List Component
 * Displays session history with timestamps and archive functionality
 */

import React, { useEffect, useState } from "react";
import { useBrowserMindStore } from "~/lib/store";
import { Button } from "~/components/ui/button";
import { Card } from "~/components/ui/card";
import { Archive, MessageSquare } from "lucide-react";

interface Session {
  id: string;
  assistant_id: string;
  message_count: number;
  last_message_at: string;
  created_at: string;
  archived_at?: string;
}

export function SessionList() {
  const { currentSession, connectionStatus } = useBrowserMindStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      // Send list_sessions message
      await chrome.runtime.sendMessage({
        type: "send_command",
        payload: {
          type: "list_sessions",
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          payload: {
            limit: 50,
            offset: 0,
            include_archived: false,
          },
        },
      });
    } catch (error) {
      console.error("Error loading sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchSession = async (sessionId: string) => {
    // Load session and switch to it
    const store = useBrowserMindStore.getState();

    // Find session in list
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      store.setCurrentSession({
        id: session.id,
        assistant_id: session.assistant_id,
        created_at: session.created_at,
      });

      // Clear current messages and load session history
      store.clearMessages();

      // Request session messages from backend
      await chrome.runtime.sendMessage({
        type: "send_command",
        payload: {
          type: "get_session_messages",
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          payload: {
            session_id: sessionId,
          },
        },
      });
    }
  };

  const handleArchiveSession = async (sessionId: string) => {
    if (!confirm("Archive this session?")) {
      return;
    }

    try {
      await chrome.runtime.sendMessage({
        type: "send_command",
        payload: {
          type: "archive_session",
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          payload: {
            session_id: sessionId,
          },
        },
      });

      // Reload sessions
      loadSessions();
    } catch (error) {
      console.error("Error archiving session:", error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return <div className="text-center py-4">Loading sessions...</div>;
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No sessions yet. Start a conversation to create one.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sessions.map((session) => (
        <Card
          key={session.id}
          className={`p-3 cursor-pointer hover:bg-accent ${
            currentSession?.id === session.id ? "border-primary" : ""
          }`}
          onClick={() => handleSwitchSession(session.id)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <MessageSquare className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {session.message_count} messages
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                {formatDate(session.last_message_at || session.created_at)}
              </div>
            </div>

            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                handleArchiveSession(session.id);
              }}
              disabled={connectionStatus !== "connected"}
              title="Archive"
            >
              <Archive className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
