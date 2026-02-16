/**
 * Sidepanel entry point.
 * Main UI for interacting with BrowserMind assistants.
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { Chat } from "./Chat";
import { StatusIndicator } from "./StatusIndicator";
import { useBrowserMindStore } from "../lib/store";
import "../styles/globals.css";

function SidePanel() {
  const { connectionStatus, currentAssistant } = useBrowserMindStore();

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">BrowserMind</h1>
          {currentAssistant && (
            <p className="text-sm text-muted-foreground">
              {currentAssistant.name}
            </p>
          )}
        </div>
        <StatusIndicator status={connectionStatus} />
      </div>

      {/* Chat Interface */}
      <div className="flex-1 overflow-hidden">
        <Chat />
      </div>
    </div>
  );
}

// Mount the app
const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(<SidePanel />);
}
