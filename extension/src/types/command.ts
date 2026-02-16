/**
 * Command and execution type definitions.
 */

export interface Command {
  id: string;
  assistant_id: string;
  session_id: string;
  text: string;
  status: CommandStatus;
  queued_at: string;
  started_at?: string;
  completed_at?: string;
  result?: any;
  error?: string;
}

export enum CommandStatus {
  QUEUED = "queued",
  EXECUTING = "executing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  TIMEOUT = "timeout",
}

export interface Session {
  id: string;
  assistant_id: string;
  created_at: string;
  last_active_at: string;
  archived: boolean;
  expires_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}
