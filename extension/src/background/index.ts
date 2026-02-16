/**
 * Background service worker (Manifest V3).
 * Manages WebSocket connection, message routing, and state synchronization.
 */
import { WebSocketClient } from "./websocket-client";
import { useBrowserMindStore } from "~/lib/store";
import { ConnectionStatus } from "~/types/websocket";
import type { WSMessage } from "~/types/websocket";

// Get backend URL from environment
const BACKEND_WS_URL =
  process.env.PLASMO_PUBLIC_BACKEND_WS_URL || "ws://localhost:8000/ws";

// Global WebSocket client instance
let wsClient: WebSocketClient | null = null;

/**
 * Initialize WebSocket connection on service worker startup.
 */
async function initializeWebSocket(): Promise<void> {
  console.log("Initializing WebSocket connection...");

  // Create WebSocket client
  wsClient = new WebSocketClient(BACKEND_WS_URL);

  // Register message handler
  wsClient.onMessage(handleWebSocketMessage);

  // Connect to backend
  await wsClient.connect();

  // Update connection status in store
  const store = useBrowserMindStore.getState();
  store.setConnectionStatus(ConnectionStatus.CONNECTING);
}

/**
 * Handle incoming WebSocket messages.
 */
async function handleWebSocketMessage(message: WSMessage): Promise<void> {
  console.log("Received WebSocket message:", message.type);

  const store = useBrowserMindStore.getState();

  switch (message.type) {
    case "connected":
      // Connection established
      store.setConnectionStatus(ConnectionStatus.CONNECTED);
      store.setConnectionId(message.id);
      store.setProtocolVersion(message.payload.version);
      console.log("WebSocket connected:", message.id);
      break;

    case "status_update":
      // Command status update
      if (message.correlation_id) {
        store.updateCommand(message.correlation_id, {
          status: message.payload.status,
        });
      }
      break;

    case "response":
      // Assistant response message
      if (message.payload.content) {
        const responseMessage = {
          id: message.id,
          session_id: store.currentSession?.id || "",
          role: "assistant" as const,
          content: message.payload.content,
          timestamp: message.timestamp,
          created_at: new Date().toISOString(),
        };
        store.addMessage(responseMessage);
      }
      break;

    case "response_chunk":
      // Streaming response chunk
      // For now, we'll accumulate chunks and add complete message
      // In a full implementation, we'd handle streaming UI updates
      if (message.payload.done && message.payload.content) {
        const responseMessage = {
          id: message.id,
          session_id: store.currentSession?.id || "",
          role: "assistant" as const,
          content: message.payload.content,
          timestamp: message.timestamp,
          created_at: new Date().toISOString(),
        };
        store.addMessage(responseMessage);
      }
      break;

    case "tool_execution":
      // Forward tool execution request to content script
      await forwardToolExecutionToContent(message);
      break;

    case "assistant_list":
      // Update assistants in store
      store.setAssistants(message.payload.assistants || []);
      break;

    case "assistant_created":
      // Add new assistant to store
      store.addAssistant(message.payload.assistant);
      break;

    case "assistant_updated":
      // Update assistant in store
      const { id, ...updates } = message.payload;
      store.updateAssistant(id, updates);
      break;

    case "queue_status":
      // Update queue status
      store.setQueueStatus(
        message.payload.queued || 0,
        message.payload.executing || 0
      );
      break;

    case "error":
      // Log error
      console.error("WebSocket error:", message.payload);
      break;

    case "ack":
    case "pong":
      // Acknowledgment messages - no action needed
      break;

    default:
      console.warn("Unknown message type:", message.type);
  }
}

/**
 * Forward tool execution request to active tab's content script.
 */
async function forwardToolExecutionToContent(message: WSMessage): Promise<void> {
  try {
    // Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab?.id) {
      throw new Error("No active tab found");
    }

    const messageId = crypto.randomUUID();

    // Send message to content script with proper format
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: "execute_tool",
      tool: message.payload.tool,
      params: message.payload.params,
      messageId: messageId,
    });

    // Send tool result back to backend
    if (wsClient && response) {
      wsClient.send({
        type: "tool_result",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        correlation_id: message.correlation_id,
        payload: {
          tool: message.payload.tool,
          success: response.success,
          result: response.result,
          error: response.error,
        },
      });
    }
  } catch (error) {
    console.error("Error forwarding tool execution:", error);

    // Send error result to backend
    if (wsClient) {
      wsClient.send({
        type: "tool_result",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        correlation_id: message.correlation_id,
        payload: {
          tool: message.payload.tool,
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        },
      });
    }
  }
}

/**
 * Handle tab refresh - restore session context and reconnect WebSocket.
 * Implements T037a: Tab refresh session recovery.
 */
async function handleTabRefresh(): Promise<void> {
  console.log("Handling tab refresh - restoring session...");

  const store = useBrowserMindStore.getState();

  // Check if we have an active session
  if (store.currentSession) {
    console.log("Active session found:", store.currentSession.id);

    // Reconnect WebSocket if disconnected
    if (
      !wsClient ||
      wsClient.getStatus() === ConnectionStatus.DISCONNECTED
    ) {
      await initializeWebSocket();
    }

    // Session context is preserved in Zustand store (persisted to chrome.storage)
    console.log("Session context restored");
  } else {
    console.log("No active session to restore");
  }
}

/**
 * Listen for messages from content scripts and sidepanel.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("Background received message:", message.type);

  // Handle async responses
  (async () => {
    try {
      switch (message.type) {
        case "send_command":
          // Forward command to backend
          if (wsClient) {
            wsClient.send({
              type: "command",
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              payload: message.payload,
            });
            sendResponse({ success: true });
          } else {
            sendResponse({ success: false, error: "WebSocket not connected" });
          }
          break;

        case "get_connection_status":
          sendResponse({
            status: wsClient?.getStatus() || ConnectionStatus.DISCONNECTED,
            connectionId: wsClient?.getConnectionId(),
          });
          break;

        case "tool_result":
          // Forward tool result to backend
          if (wsClient) {
            wsClient.send({
              type: "tool_result",
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              correlation_id: message.correlation_id,
              payload: message.payload,
            });
            sendResponse({ success: true });
          }
          break;

        default:
          sendResponse({ success: false, error: "Unknown message type" });
      }
    } catch (error) {
      console.error("Error handling message:", error);
      sendResponse({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      });
    }
  })();

  // Return true to indicate async response
  return true;
});

/**
 * Handle service worker installation.
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log("Service worker installed:", details.reason);

  // Initialize WebSocket on install
  await initializeWebSocket();
});

/**
 * Handle service worker startup.
 */
chrome.runtime.onStartup.addListener(async () => {
  console.log("Service worker starting up...");

  // Handle tab refresh recovery
  await handleTabRefresh();

  // Initialize WebSocket if not already connected
  if (!wsClient || wsClient.getStatus() === ConnectionStatus.DISCONNECTED) {
    await initializeWebSocket();
  }
});

/**
 * Keep service worker alive with periodic heartbeat.
 */
setInterval(() => {
  console.debug("Service worker heartbeat");
}, 20000); // Every 20 seconds

// Initialize on script load
initializeWebSocket().catch((error) => {
  console.error("Failed to initialize WebSocket:", error);
});

console.log("BrowserMind background service worker loaded");
