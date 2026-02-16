# Data Model: BrowserMind Platform

**Feature**: 001-browser-agent-platform
**Date**: 2026-02-17
**Phase**: 1 - Design and Contracts

## Overview

This document defines the core data entities, their relationships, validation rules, and state transitions for the BrowserMind platform. All entities support the constitutional requirements for isolation, traceability, and persistence.

---

## Entity Relationship Diagram

```
┌─────────────┐
│   User      │ (implicit - browser extension user)
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐
│  Assistant  │◄──────┐
└──────┬──────┘       │
       │ 1:N          │ N:1
       │              │
┌──────▼──────┐       │
│   Session   │       │
└──────┬──────┘       │
       │ 1:N          │
       │              │
┌──────▼──────┐       │
│   Message   │       │
└─────────────┘       │
                      │
┌─────────────┐       │
│ Capability  │───────┘
└──────┬──────┘
       │ N:M (through AssistantCapability)
       │
┌──────▼──────┐
│    Tool     │
└──────┬──────┘
       │ 1:N
       │
┌──────▼──────┐
│ ToolLog     │
└─────────────┘

┌─────────────┐
│  Command    │ (in-memory queue)
└─────────────┘
```

---

## Core Entities

### 1. Assistant

**Description**: A specialized AI helper with specific capabilities, instructions, and isolated memory. Persists across sessions and browser restarts.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| name | String(100) | NOT NULL, UNIQUE per user | User-defined assistant name |
| instructions | Text | NOT NULL | System prompt defining assistant behavior |
| model | String(50) | NOT NULL, DEFAULT 'gpt-4-turbo' | OpenAI model identifier |
| status | Enum | NOT NULL, DEFAULT 'inactive' | 'active', 'inactive', 'deleted' |
| created_at | DateTime | NOT NULL | Creation timestamp |
| updated_at | DateTime | NOT NULL | Last modification timestamp |
| last_active_at | DateTime | NULLABLE | Last activation timestamp |
| metadata | JSON | NULLABLE | Additional configuration (max 10KB) |

**Relationships:**
- Has many Sessions (1:N)
- Has many Capabilities through AssistantCapability (N:M)
- Has many ToolLogs (1:N)

**Validation Rules:**
- Name must be 1-100 characters, alphanumeric + spaces/hyphens
- Maximum 20 assistants per user (enforced at application level)
- Instructions must be 10-10,000 characters
- Status transitions: inactive ↔ active, any → deleted (terminal)

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE INDEX (name) -- per user context
- INDEX (status, last_active_at) -- for listing active assistants

---

### 2. Session

**Description**: A continuous interaction period between user and assistant, containing conversation history and context. Persists across browser restarts.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| assistant_id | UUID | FOREIGN KEY, NOT NULL | Associated assistant |
| created_at | DateTime | NOT NULL | Session start timestamp |
| last_active_at | DateTime | NOT NULL | Last message timestamp |
| archived | Boolean | NOT NULL, DEFAULT false | User-archived flag |
| expires_at | DateTime | NOT NULL | Auto-deletion date (90 days from creation) |
| metadata | JSON | NULLABLE | Session-specific context (max 50KB) |

**Relationships:**
- Belongs to one Assistant (N:1)
- Has many Messages (1:N)

**Validation Rules:**
- expires_at = created_at + 90 days (unless archived)
- Archived sessions never expire
- last_active_at must be >= created_at
- Auto-delete when expires_at < current_time AND archived = false

**Indexes:**
- PRIMARY KEY (id)
- INDEX (assistant_id, last_active_at DESC) -- for session listing
- INDEX (expires_at) -- for cleanup job
- INDEX (archived, expires_at) -- for retention policy

**State Transitions:**
```
[Created] → [Active] → [Expired] → [Deleted]
              ↓
          [Archived] (terminal, never expires)
```

---

### 3. Message

**Description**: A single message in a conversation, from either user or assistant. Includes full content and metadata for context reconstruction.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| session_id | UUID | FOREIGN KEY, NOT NULL | Associated session |
| role | Enum | NOT NULL | 'user', 'assistant', 'system' |
| content | Text | NOT NULL | Message text content |
| timestamp | DateTime | NOT NULL | Message creation time |
| token_count | Integer | NULLABLE | Token usage for this message |
| metadata | JSON | NULLABLE | Tool calls, attachments, etc. (max 10KB) |

**Relationships:**
- Belongs to one Session (N:1)

**Validation Rules:**
- content must be 1-100,000 characters
- timestamp must be >= session.created_at
- role must be one of: 'user', 'assistant', 'system'
- Messages are immutable after creation (no updates)

**Indexes:**
- PRIMARY KEY (id)
- INDEX (session_id, timestamp ASC) -- for conversation retrieval
- INDEX (timestamp) -- for cleanup and analytics

---

### 4. Capability

**Description**: A specific action an assistant can perform (e.g., navigate, click, extract_text). Defines the tool permission system.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| name | String(50) | NOT NULL, UNIQUE | Capability identifier (e.g., 'navigate') |
| display_name | String(100) | NOT NULL | Human-readable name |
| description | Text | NOT NULL | Capability description for UI |
| category | Enum | NOT NULL | 'navigation', 'interaction', 'extraction', 'utility' |
| risk_level | Enum | NOT NULL | 'low', 'medium', 'high' |
| schema | JSON | NOT NULL | Tool parameter schema (JSON Schema format) |
| enabled | Boolean | NOT NULL, DEFAULT true | Global enable/disable flag |

**Relationships:**
- Has many Assistants through AssistantCapability (N:M)
- Has many ToolLogs (1:N)

**Validation Rules:**
- name must match pattern: ^[a-z][a-z0-9_]*$
- schema must be valid JSON Schema
- Predefined capabilities cannot be deleted, only disabled

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE INDEX (name)
- INDEX (category, enabled) -- for capability listing

**Predefined Capabilities:**
```json
[
  { "name": "navigate", "category": "navigation", "risk_level": "low" },
  { "name": "click_element", "category": "interaction", "risk_level": "medium" },
  { "name": "type_text", "category": "interaction", "risk_level": "medium" },
  { "name": "extract_text", "category": "extraction", "risk_level": "low" },
  { "name": "extract_links", "category": "extraction", "risk_level": "low" },
  { "name": "extract_tables", "category": "extraction", "risk_level": "low" },
  { "name": "scroll", "category": "navigation", "risk_level": "low" },
  { "name": "screenshot", "category": "utility", "risk_level": "low" },
  { "name": "get_dom", "category": "extraction", "risk_level": "low" },
  { "name": "highlight_element", "category": "utility", "risk_level": "low" }
]
```

---

### 5. AssistantCapability (Join Table)

**Description**: Maps assistants to their allowed capabilities, enforcing the permission system.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| assistant_id | UUID | FOREIGN KEY, NOT NULL | Associated assistant |
| capability_id | UUID | FOREIGN KEY, NOT NULL | Associated capability |
| granted_at | DateTime | NOT NULL | When capability was granted |

**Relationships:**
- Belongs to one Assistant (N:1)
- Belongs to one Capability (N:1)

**Validation Rules:**
- Maximum 10 capabilities per assistant (FR-010)
- Composite primary key (assistant_id, capability_id)
- Cannot grant capability to deleted assistant

**Indexes:**
- PRIMARY KEY (assistant_id, capability_id)
- INDEX (capability_id) -- for reverse lookup

---

### 6. ToolLog

**Description**: Audit log of all tool executions, including inputs, outputs, timestamps, and agent identifiers. Supports debugging and compliance.

**Attributes:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| assistant_id | UUID | FOREIGN KEY, NOT NULL | Executing assistant |
| capability_id | UUID | FOREIGN KEY, NOT NULL | Executed capability |
| session_id | UUID | FOREIGN KEY, NULLABLE | Associated session (if any) |
| input_params | JSON | NOT NULL | Tool input parameters |
| output_result | JSON | NULLABLE | Tool output (null if error) |
| status | Enum | NOT NULL | 'success', 'error', 'timeout', 'cancelled' |
| error_message | Text | NULLABLE | Error details if status = 'error' |
| execution_time_ms | Integer | NOT NULL | Execution duration in milliseconds |
| timestamp | DateTime | NOT NULL | Execution start time |

**Relationships:**
- Belongs to one Assistant (N:1)
- Belongs to one Capability (N:1)
- Optionally belongs to one Session (N:1)

**Validation Rules:**
- input_params must be valid JSON (max 100KB)
- output_result must be valid JSON (max 1MB)
- execution_time_ms must be >= 0
- error_message required if status = 'error'
- Logs are immutable after creation

**Indexes:**
- PRIMARY KEY (id)
- INDEX (assistant_id, timestamp DESC) -- for assistant activity log
- INDEX (capability_id, timestamp DESC) -- for capability usage analytics
- INDEX (session_id, timestamp ASC) -- for session replay
- INDEX (timestamp) -- for cleanup and analytics
- INDEX (status, timestamp) -- for error monitoring

**Retention Policy:**
- Keep logs for 90 days (same as conversation history)
- Archived sessions keep their logs indefinitely

---

## In-Memory Entities (Not Persisted)

### 7. Command

**Description**: A queued user command waiting for execution. Exists only in memory during runtime.

**Attributes:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique identifier |
| assistant_id | UUID | Target assistant |
| session_id | UUID | Associated session |
| text | String | User command text |
| status | Enum | 'queued', 'executing', 'completed', 'failed', 'cancelled', 'timeout' |
| queued_at | DateTime | When command was queued |
| started_at | DateTime | When execution started (nullable) |
| completed_at | DateTime | When execution finished (nullable) |
| timeout_at | DateTime | When command will timeout (queued_at + 30s) |
| result | Any | Execution result (nullable) |
| error | String | Error message if failed (nullable) |

**Validation Rules:**
- Maximum 10 queued commands per assistant
- Auto-cancel if timeout_at < current_time
- Commands older than 5 minutes are purged

**State Transitions:**
```
[Queued] → [Executing] → [Completed]
                ↓
            [Failed]
                ↓
            [Cancelled]
                ↓
            [Timeout]
```

---

## Encryption Strategy

### Encrypted Fields

Per FR-026 (AES-256 encryption at rest), the following fields are encrypted:

**Assistant Table:**
- `instructions` (contains sensitive system prompts)
- `metadata` (may contain API keys or credentials)

**Session Table:**
- `metadata` (may contain sensitive context)

**Message Table:**
- `content` (conversation history)
- `metadata` (may contain extracted sensitive data)

**Implementation:**
- Use Python `cryptography.fernet` (AES-256-CBC)
- Encryption key stored in environment variable `ENCRYPTION_KEY`
- Key rotation supported via dual-key decryption
- Encrypted fields stored as base64-encoded strings

---

## Data Lifecycle

### Creation
- Assistants: Created via user command, persisted immediately
- Sessions: Created on first message to assistant, persisted immediately
- Messages: Created on each user/assistant interaction, persisted immediately
- ToolLogs: Created after each tool execution, persisted immediately

### Updates
- Assistants: Can update name, instructions, status, capabilities
- Sessions: Only last_active_at and archived flag can be updated
- Messages: Immutable after creation
- ToolLogs: Immutable after creation

### Deletion
- Assistants: Soft delete (status = 'deleted'), cascade to sessions
- Sessions: Hard delete after expiration (unless archived)
- Messages: Cascade delete with session
- ToolLogs: Cascade delete with session (unless archived)

### Retention Policy (FR-013, FR-021)
- Default: 90 days from session creation
- Archived: Indefinite retention
- Cleanup job runs daily at 2 AM local time
- User notified 7 days before auto-deletion

---

## Database Schema (SQLite)

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

CREATE TABLE assistants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    instructions TEXT NOT NULL,  -- encrypted
    model TEXT NOT NULL DEFAULT 'gpt-4-turbo',
    status TEXT NOT NULL DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'deleted')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_active_at TEXT,
    metadata TEXT,  -- encrypted JSON
    CONSTRAINT name_length CHECK(length(name) BETWEEN 1 AND 100),
    CONSTRAINT instructions_length CHECK(length(instructions) BETWEEN 10 AND 10000)
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    assistant_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL,
    metadata TEXT,  -- encrypted JSON
    FOREIGN KEY (assistant_id) REFERENCES assistants(id) ON DELETE CASCADE,
    CONSTRAINT valid_dates CHECK(last_active_at >= created_at)
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,  -- encrypted
    timestamp TEXT NOT NULL,
    token_count INTEGER,
    metadata TEXT,  -- encrypted JSON
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    CONSTRAINT content_length CHECK(length(content) BETWEEN 1 AND 100000)
);

CREATE TABLE capabilities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('navigation', 'interaction', 'extraction', 'utility')),
    risk_level TEXT NOT NULL CHECK(risk_level IN ('low', 'medium', 'high')),
    schema TEXT NOT NULL,  -- JSON Schema
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE assistant_capabilities (
    assistant_id TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    PRIMARY KEY (assistant_id, capability_id),
    FOREIGN KEY (assistant_id) REFERENCES assistants(id) ON DELETE CASCADE,
    FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE RESTRICT
);

CREATE TABLE tool_logs (
    id TEXT PRIMARY KEY,
    assistant_id TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    session_id TEXT,
    input_params TEXT NOT NULL,  -- JSON
    output_result TEXT,  -- JSON
    status TEXT NOT NULL CHECK(status IN ('success', 'error', 'timeout', 'cancelled')),
    error_message TEXT,
    execution_time_ms INTEGER NOT NULL CHECK(execution_time_ms >= 0),
    timestamp TEXT NOT NULL,
    FOREIGN KEY (assistant_id) REFERENCES assistants(id) ON DELETE CASCADE,
    FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE RESTRICT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_assistants_status_active ON assistants(status, last_active_at DESC);
CREATE INDEX idx_sessions_assistant ON sessions(assistant_id, last_active_at DESC);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_archived_expires ON sessions(archived, expires_at);
CREATE INDEX idx_messages_session ON messages(session_id, timestamp ASC);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_capabilities_category ON capabilities(category, enabled);
CREATE INDEX idx_assistant_capabilities_capability ON assistant_capabilities(capability_id);
CREATE INDEX idx_tool_logs_assistant ON tool_logs(assistant_id, timestamp DESC);
CREATE INDEX idx_tool_logs_capability ON tool_logs(capability_id, timestamp DESC);
CREATE INDEX idx_tool_logs_session ON tool_logs(session_id, timestamp ASC);
CREATE INDEX idx_tool_logs_timestamp ON tool_logs(timestamp);
CREATE INDEX idx_tool_logs_status ON tool_logs(status, timestamp);
```

---

## Data Validation Rules Summary

| Entity | Max Count | Max Size | Retention |
|--------|-----------|----------|-----------|
| Assistants | 20 per user | N/A | Until user deletes |
| Capabilities per Assistant | 10 | N/A | N/A |
| Sessions | Unlimited | N/A | 90 days (unless archived) |
| Messages per Session | Unlimited | 100KB each | Same as session |
| ToolLogs | Unlimited | 1MB output | Same as session |
| Queued Commands | 10 per assistant | N/A | 5 minutes |

---

## Migration Strategy

**Initial Schema**: Version 1.0.0 (this document)

**Future Migrations**:
- Use Alembic for schema versioning
- Backward-compatible changes preferred
- Data migrations tested on copy before production
- Rollback plan required for each migration

**Seed Data**:
- Predefined capabilities (10 tools)
- Default system assistant (optional)

---

This data model supports all functional requirements (FR-001 through FR-027) and aligns with constitutional principles for isolation, traceability, and security.
