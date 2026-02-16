# WebSocket Protocol Specification

**Feature**: 001-browser-agent-platform
**Version**: 1.0.0
**Date**: 2026-02-17

## Overview

This document defines the WebSocket communication protocol between the BrowserMind browser extension (client) and the Python backend (server). The protocol supports bidirectional real-time messaging for command execution, status updates, and queue management.

---

## Connection

### Endpoint
```
ws://localhost:8000/ws
wss://localhost:8000/ws  (production with TLS)
```

### Authentication
- Initial connection includes extension ID in query parameter: `?extension_id={uuid}`
- Server validates extension ID and establishes session
- Connection rejected if invalid or rate-limited

### Connection Lifecycle
```
[Disconnected] → [Connecting] → [Connected] → [Disconnected]
                      ↓              ↓
                  [Failed]      [Reconnecting]
```

### Heartbeat
- Client sends `ping` every 30 seconds
- Server responds with `pong` within 5 seconds
- Connection considered dead if no `pong` received after 3 attempts
- Client initiates reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s)

---

## Message Format

All messages are JSON objects with the following structure:

```typescript
interface WSMessage {
  type: string;           // Message type identifier
  id: string;             // Unique message ID (UUID)
  timestamp: number;      // Unix timestamp in milliseconds
  payload: any;           // Type-specific payload
  correlation_id?: string; // Optional correlation ID for request/response pairing
}
```

### Message Types

#### Client → Server

1. **command** - Execute a natural language command
2. **tool_result** - Return result of tool execution from extension
3. **cancel_command** - Cancel a queued or executing command
4. **list_assistants** - Request list of all assistants
5. **create_assistant** - Create a new assistant
6. **activate_assistant** - Activate an assistant
7. **deactivate_assistant** - Deactivate an assistant
8. **delete_assistant** - Delete an assistant
9. **get_queue_status** - Request current command queue status
10. **archive_session** - Archive a session to prevent auto-deletion
11. **ping** - Heartbeat ping

#### Server → Client

1. **tool_execution** - Request tool execution in browser
2. **status_update** - Update on command execution progress
3. **queue_status** - Current state of command queue
4. **assistant_list** - List of assistants
5. **assistant_created** - Confirmation of assistant creation
6. **assistant_updated** - Notification of assistant state change
7. **error** - Error message
8. **ack** - Acknowledgment of received message
9. **pong** - Heartbeat pong

---

## Message Specifications

### 1. command (Client → Server)

Execute a natural language command with the active assistant.

```typescript
{
  type: "command",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    text: string;              // User command text (1-10,000 chars)
    assistant_id: string;      // Target assistant UUID
    session_id?: string;       // Optional session ID (creates new if omitted)
  }
}
```

**Server Response**: `ack` → `status_update` (multiple) → `tool_execution` (if needed) → `status_update` (completion)

**Validation**:
- text: 1-10,000 characters
- assistant_id: must exist and be active
- session_id: must exist if provided

**Error Codes**:
- `ASSISTANT_NOT_FOUND`: assistant_id doesn't exist
- `ASSISTANT_INACTIVE`: assistant is not active
- `SESSION_NOT_FOUND`: session_id doesn't exist
- `QUEUE_FULL`: Too many queued commands (>10)
- `INVALID_TEXT`: Text validation failed

---

### 2. tool_execution (Server → Client)

Request the extension to execute a tool in the browser.

```typescript
{
  type: "tool_execution",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "command_uuid",
  payload: {
    tool: string;              // Tool name (e.g., "navigate", "click_element")
    params: object;            // Tool-specific parameters (see tool-schemas.json)
    timeout_ms: number;        // Execution timeout (default 30000)
  }
}
```

**Client Response**: `tool_result`

**Validation**:
- tool: must be a valid capability name
- params: must match tool schema
- timeout_ms: 1000-60000

---

### 3. tool_result (Client → Server)

Return the result of a tool execution.

```typescript
{
  type: "tool_result",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "tool_execution_uuid",
  payload: {
    status: "success" | "error" | "timeout";
    result?: any;              // Tool output (if success)
    error?: string;            // Error message (if error)
    execution_time_ms: number; // Actual execution time
  }
}
```

**Server Response**: `ack` → continues command execution

---

### 4. status_update (Server → Client)

Update on command execution progress.

```typescript
{
  type: "status_update",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "command_uuid",
  payload: {
    status: "queued" | "executing" | "completed" | "failed" | "cancelled" | "timeout";
    message: string;           // Human-readable status message
    progress?: number;         // Optional progress percentage (0-100)
    result?: any;              // Final result (if completed)
    error?: string;            // Error details (if failed)
  }
}
```

**Client Response**: None (notification only)

---

### 5. queue_status (Server → Client)

Current state of the command queue for an assistant.

```typescript
{
  type: "queue_status",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    assistant_id: string;
    queued: Array<{
      command_id: string;
      text: string;
      queued_at: number;
      timeout_at: number;
    }>;
    in_progress: {
      command_id: string;
      text: string;
      started_at: number;
      progress?: number;
    } | null;
  }
}
```

**Client Response**: None (notification only)

---

### 6. list_assistants (Client → Server)

Request list of all assistants.

```typescript
{
  type: "list_assistants",
  id: "uuid",
  timestamp: 1234567890,
  payload: {}
}
```

**Server Response**: `assistant_list`

---

### 7. assistant_list (Server → Client)

List of all assistants with their current state.

```typescript
{
  type: "assistant_list",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "list_assistants_uuid",
  payload: {
    assistants: Array<{
      id: string;
      name: string;
      status: "active" | "inactive";
      capabilities: string[];    // Array of capability names
      created_at: number;
      last_active_at?: number;
    }>;
    total_count: number;
    max_allowed: number;         // 20 for MVP
  }
}
```

---

### 8. create_assistant (Client → Server)

Create a new assistant with specified capabilities.

```typescript
{
  type: "create_assistant",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    name: string;                // 1-100 chars, unique
    instructions: string;        // 10-10,000 chars
    capabilities: string[];      // Array of capability names (max 10)
    model?: string;              // Optional model override
  }
}
```

**Server Response**: `assistant_created` or `error`

**Validation**:
- name: 1-100 chars, alphanumeric + spaces/hyphens, unique
- instructions: 10-10,000 chars
- capabilities: 1-10 valid capability names
- Total assistants < 20

**Error Codes**:
- `NAME_TAKEN`: Assistant name already exists
- `INVALID_NAME`: Name validation failed
- `INVALID_INSTRUCTIONS`: Instructions validation failed
- `INVALID_CAPABILITIES`: Unknown or too many capabilities
- `MAX_ASSISTANTS_REACHED`: Already have 20 assistants

---

### 9. assistant_created (Server → Client)

Confirmation of assistant creation.

```typescript
{
  type: "assistant_created",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "create_assistant_uuid",
  payload: {
    assistant: {
      id: string;
      name: string;
      status: "inactive";
      capabilities: string[];
      created_at: number;
    }
  }
}
```

---

### 10. activate_assistant (Client → Server)

Activate an assistant to handle commands.

```typescript
{
  type: "activate_assistant",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    assistant_id: string;
  }
}
```

**Server Response**: `assistant_updated` or `error`

**Side Effects**:
- Deactivates currently active assistant (if any)
- Activates specified assistant
- Broadcasts `assistant_updated` for both assistants

---

### 11. deactivate_assistant (Client → Server)

Deactivate an assistant.

```typescript
{
  type: "deactivate_assistant",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    assistant_id: string;
  }
}
```

**Server Response**: `assistant_updated` or `error`

---

### 12. delete_assistant (Client → Server)

Permanently delete an assistant and all its sessions.

```typescript
{
  type: "delete_assistant",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    assistant_id: string;
    confirm: boolean;            // Must be true
  }
}
```

**Server Response**: `assistant_updated` (status: deleted) or `error`

**Side Effects**:
- Soft deletes assistant (status = 'deleted')
- Cascades to all sessions
- Cannot be undone

**Error Codes**:
- `ASSISTANT_NOT_FOUND`: assistant_id doesn't exist
- `CONFIRMATION_REQUIRED`: confirm must be true

---

### 13. cancel_command (Client → Server)

Cancel a queued or executing command.

```typescript
{
  type: "cancel_command",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    command_id: string;
  }
}
```

**Server Response**: `status_update` (status: cancelled) or `error`

**Behavior**:
- If queued: Remove from queue immediately
- If executing: Send cancellation signal, wait up to 5s for graceful stop
- If completed/failed: No-op, return current status

---

### 14. archive_session (Client → Server)

Archive a session to prevent auto-deletion after 90 days.

```typescript
{
  type: "archive_session",
  id: "uuid",
  timestamp: 1234567890,
  payload: {
    session_id: string;
    archived: boolean;           // true to archive, false to unarchive
  }
}
```

**Server Response**: `ack` or `error`

**Side Effects**:
- Sets session.archived flag
- Archived sessions never expire
- Unarchiving resets expires_at to 90 days from now

---

### 15. error (Server → Client)

Error message for failed operations.

```typescript
{
  type: "error",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id?: string,       // If in response to a request
  payload: {
    code: string;                // Error code (e.g., "ASSISTANT_NOT_FOUND")
    message: string;             // Human-readable error message
    details?: any;               // Optional additional error details
    retry_after_ms?: number;     // Optional retry delay for rate limiting
  }
}
```

**Common Error Codes**:
- `INVALID_MESSAGE`: Message validation failed
- `AUTHENTICATION_FAILED`: Extension ID invalid
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: OpenAI API unavailable
- `TIMEOUT`: Operation timed out

---

### 16. ack (Server → Client)

Acknowledgment of received message.

```typescript
{
  type: "ack",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: string,        // ID of acknowledged message
  payload: {}
}
```

---

### 17. ping / pong (Heartbeat)

```typescript
// Client → Server
{
  type: "ping",
  id: "uuid",
  timestamp: 1234567890,
  payload: {}
}

// Server → Client
{
  type: "pong",
  id: "uuid",
  timestamp: 1234567890,
  correlation_id: "ping_uuid",
  payload: {}
}
```

---

## Error Handling

### Connection Errors
- **Connection Refused**: Backend not running → Show "Backend Offline" status
- **Authentication Failed**: Invalid extension ID → Show error, disable features
- **Connection Lost**: Network issue → Auto-reconnect with exponential backoff

### Message Errors
- **Invalid JSON**: Log error, ignore message
- **Unknown Message Type**: Send `error` with code `INVALID_MESSAGE`
- **Validation Failed**: Send `error` with code and details
- **Timeout**: Send `status_update` with status `timeout` after 30s

### Service Errors
- **OpenAI API Unavailable**: Queue commands, show "Service Degraded" status (FR-022)
- **Database Error**: Send `error` with code `INTERNAL_ERROR`, retry operation
- **Tool Execution Failed**: Send `status_update` with status `failed` and error details

---

## Rate Limiting

### Per Connection
- Maximum 100 messages per minute
- Maximum 10 concurrent commands per assistant
- Exceeded limits result in `error` with code `RATE_LIMITED` and `retry_after_ms`

### Reconnection
- Maximum 10 reconnection attempts per minute
- Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)

---

## Security

### Transport Security
- TLS 1.3 required for production (wss://)
- Certificate validation enforced
- No fallback to unencrypted (ws://) in production

### Message Validation
- All messages validated against schemas before processing
- Input sanitization for all text fields
- Maximum message size: 10MB
- Reject messages with unknown fields (strict validation)

### Authentication
- Extension ID validated on connection
- Session tokens rotated every 24 hours
- Connections terminated after 1 hour of inactivity

---

## Example Message Flows

### Flow 1: Execute Command

```
Client → Server: command
Server → Client: ack
Server → Client: status_update (status: queued)
Server → Client: queue_status
Server → Client: status_update (status: executing)
Server → Client: tool_execution (navigate)
Client → Server: tool_result (success)
Server → Client: status_update (status: completed)
```

### Flow 2: Create and Activate Assistant

```
Client → Server: create_assistant
Server → Client: assistant_created
Client → Server: activate_assistant
Server → Client: assistant_updated (old assistant: inactive)
Server → Client: assistant_updated (new assistant: active)
```

### Flow 3: Service Unavailable

```
Client → Server: command
Server → Client: ack
Server → Client: status_update (status: queued)
Server → Client: queue_status (command in queue)
[30 seconds pass]
Server → Client: status_update (status: timeout)
Server → Client: error (code: SERVICE_UNAVAILABLE)
```

### Flow 4: Cancel Command

```
Client → Server: command
Server → Client: ack
Server → Client: status_update (status: queued)
Client → Server: cancel_command
Server → Client: status_update (status: cancelled)
Server → Client: queue_status (queue updated)
```

---

## Protocol Versioning

**Current Version**: 1.0.0

**Version Negotiation**:
- Client sends version in connection query parameter: `?version=1.0.0`
- Server responds with supported version in first message
- Incompatible versions result in connection rejection

**Breaking Changes**:
- Increment major version (e.g., 1.0.0 → 2.0.0)
- Maintain backward compatibility for one major version

**Non-Breaking Changes**:
- Increment minor version (e.g., 1.0.0 → 1.1.0)
- Add new optional fields
- Add new message types

---

This protocol specification supports all functional requirements (FR-001 through FR-027) and enables real-time bidirectional communication between the browser extension and backend.
