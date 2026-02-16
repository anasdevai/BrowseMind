/**
 * WebSocket message types and protocol definitions.
 */

export interface WSMessage {
  type: string;
  id: string;
  timestamp: number;
  payload: any;
  correlation_id?: string;
}

// Client → Server message types
export type ClientMessageType =
  | "command"
  | "tool_result"
  | "cancel_command"
  | "list_assistants"
  | "create_assistant"
  | "activate_assistant"
  | "deactivate_assistant"
  | "delete_assistant"
  | "get_queue_status"
  | "archive_session"
  | "ping";

// Server → Client message types
export type ServerMessageType =
  | "connected"
  | "tool_execution"
  | "status_update"
  | "queue_status"
  | "assistant_list"
  | "assistant_created"
  | "assistant_updated"
  | "error"
  | "ack"
  | "pong";

// Command message
export interface CommandMessage extends WSMessage {
  type: "command";
  payload: {
    text: string;
    assistant_id: string;
    session_id?: string;
  };
}

// Tool execution message
export interface ToolExecutionMessage extends WSMessage {
  type: "tool_execution";
  payload: {
    tool: string;
    params: Record<string, any>;
    timeout_ms: number;
  };
}

// Tool result message
export interface ToolResultMessage extends WSMessage {
  type: "tool_result";
  payload: {
    success: boolean;
    result?: any;
    error?: string;
  };
}

// Status update message
export interface StatusUpdateMessage extends WSMessage {
  type: "status_update";
  payload: {
    status: "queued" | "executing" | "completed" | "failed";
    message: string;
  };
}

// Error message
export interface ErrorMessage extends WSMessage {
  type: "error";
  payload: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

// Connection status
export enum ConnectionStatus {
  DISCONNECTED = "disconnected",
  CONNECTING = "connecting",
  CONNECTED = "connected",
  RECONNECTING = "reconnecting",
  FAILED = "failed",
}

// Protocol info
export interface ProtocolInfo {
  version: string;
  supported_message_types: string[];
  rate_limit: {
    max_messages: number;
    window_seconds: number;
  };
  timeouts: {
    command_timeout_seconds: number;
    heartbeat_interval_seconds: number;
  };
}
