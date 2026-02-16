# Research: BrowserMind Technical Decisions

**Feature**: 001-browser-agent-platform
**Date**: 2026-02-17
**Phase**: 0 - Research and Technology Selection

## Overview

This document captures the research findings, technical decisions, and rationale for the BrowserMind platform architecture. All decisions align with constitutional principles and feature requirements.

---

## Backend Technology Stack

### Decision: Python 3.11+ with FastAPI

**Rationale:**
- **Async Support**: FastAPI built on Starlette provides native async/await support, critical for WebSocket connections and concurrent agent execution (FR-014: 5 concurrent agents)
- **Performance**: FastAPI is one of the fastest Python frameworks, meeting <2s command execution requirement (SC-005)
- **OpenAI SDK Integration**: Python has first-class support for OpenAI Agents SDK, which is a constitutional constraint (Execution Constraints)
- **Type Safety**: Pydantic models provide runtime validation for tool schemas (FR-003: validate commands for safety)
- **WebSocket Support**: Native WebSocket support via Starlette for real-time bidirectional communication

**Alternatives Considered:**
- **Node.js + Express**: Rejected due to less mature OpenAI Agents SDK support and weaker type safety
- **Go**: Rejected due to limited OpenAI SDK support and steeper learning curve for AI/ML ecosystem
- **Django**: Rejected due to heavier framework overhead and less optimized async support

**Best Practices:**
- Use `uv` for package management (10-100x faster than pip)
- Use dependency injection for testability
- Implement structured logging with correlation IDs
- Use Pydantic for all data validation
- Implement circuit breakers for external API calls
- Use connection pooling for database access

**Package Management:**
- **Recommended**: `uv` - Modern, fast Python package installer and resolver
  - Installation: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Usage: `uv venv` to create venv, `uv pip install -r requirements.txt` to install
  - Benefits: 10-100x faster than pip, better dependency resolution, disk space efficient
- **Alternative**: Standard `pip` - Works but slower for large dependency trees

---

## Agent Orchestration

### Decision: OpenAI Agents SDK

**Rationale:**
- **Constitutional Requirement**: Explicitly mandated in Execution Constraints
- **Built-in Tool Calling**: Native function calling support aligns with tool permission system (FR-006)
- **Streaming Support**: Enables real-time status updates (FR-018)
- **Thread Management**: Built-in conversation threading supports persistent memory (FR-011, FR-013)
- **Model Flexibility**: OpenAI Router Provider allows model selection per agent

**Alternatives Considered:**
- **LangChain**: Rejected due to higher abstraction overhead and less direct control over tool execution
- **Custom Implementation**: Rejected due to development time and maintenance burden

**Best Practices:**
- Implement retry logic with exponential backoff for API calls
- Use streaming responses for better UX
- Implement token usage tracking for cost management
- Cache agent configurations to reduce API calls
- Implement graceful degradation when API unavailable (FR-022)

---

## Browser Extension Framework

### Decision: Plasmo + React + TypeScript

**Rationale:**
- **Manifest V3 Support**: Plasmo provides first-class Manifest V3 support, required for Chrome extensions
- **Developer Experience**: Hot reload, TypeScript support, and modern build tooling
- **React Ecosystem**: Access to shadcn/ui components for consistent UI (requirement from spec)
- **Type Safety**: TypeScript prevents runtime errors in extension code
- **Modular Architecture**: Supports separation of background, content, and sidepanel scripts

**Alternatives Considered:**
- **Vanilla JavaScript**: Rejected due to lack of type safety and modern tooling
- **Vue.js**: Rejected due to smaller ecosystem for browser extensions
- **WXT**: Rejected due to less mature framework compared to Plasmo

**Best Practices:**
- Use message passing between scripts (background ↔ content ↔ sidepanel)
- Implement CSP-compliant code (no eval, inline scripts)
- Use storage.local for extension state persistence
- Implement error boundaries for React components
- Use Web Workers for heavy computations

---

## Data Storage

### Decision: SQLite with SQLAlchemy ORM

**Rationale:**
- **Constitutional Requirement**: "SQLite minimum" specified in Operational Constraints
- **Zero Configuration**: No separate database server required, simplifies deployment
- **ACID Compliance**: Ensures data integrity for agent configurations and conversation history
- **File-Based**: Easy backup and migration (FR-007: persist across restarts)
- **Performance**: Sufficient for MVP scale (20 assistants, 90-day retention)

**Alternatives Considered:**
- **PostgreSQL**: Rejected for MVP due to deployment complexity and overkill for scale
- **MongoDB**: Rejected due to lack of ACID guarantees and schema flexibility not needed
- **In-Memory Only**: Rejected due to persistence requirements (FR-007, FR-013)

**Best Practices:**
- Enable WAL mode for better concurrent read performance
- Implement connection pooling (even for SQLite)
- Use migrations (Alembic) for schema evolution
- Implement automatic vacuum for maintenance
- Encrypt database file at rest (FR-026: AES-256)

**Schema Design:**
```sql
-- Core tables
agents (id, name, instructions, tools, permissions, created_at, status)
sessions (id, agent_id, created_at, last_active, archived)
messages (id, session_id, role, content, timestamp)
tool_logs (id, agent_id, tool_name, input, output, timestamp)
```

---

## Communication Protocol

### Decision: WebSocket with JSON Protocol

**Rationale:**
- **Bidirectional**: Supports real-time updates from backend to extension (FR-018)
- **Low Latency**: Persistent connection reduces overhead vs HTTP polling
- **Streaming**: Enables token-by-token streaming of agent responses
- **Constitutional Alignment**: Communication Standards require WebSocket or authenticated HTTP

**Alternatives Considered:**
- **HTTP Long Polling**: Rejected due to higher latency and resource consumption
- **Server-Sent Events (SSE)**: Rejected due to unidirectional nature (can't send commands from extension)
- **gRPC**: Rejected due to browser compatibility issues

**Protocol Design:**
```typescript
// Message types
type WSMessage =
  | { type: 'command', payload: { text: string, agent_id: string } }
  | { type: 'tool_execution', payload: { tool: string, params: any } }
  | { type: 'status_update', payload: { status: string, progress: number } }
  | { type: 'queue_status', payload: { queued: Command[], in_progress: Command[] } }
  | { type: 'error', payload: { code: string, message: string } }
```

**Best Practices:**
- Implement heartbeat/ping-pong for connection health
- Use message acknowledgments for reliability
- Implement reconnection with exponential backoff
- Validate all messages against schemas
- Implement rate limiting per connection

---

## Security Architecture

### Decision: AES-256 Encryption + TLS + Input Sanitization

**Rationale:**
- **Constitutional Requirement**: Security by Design principle mandates encryption
- **Clarification Requirement**: FR-026 specifies AES-256 at rest, FR-027 specifies TLS in transit
- **Defense in Depth**: Multiple layers of security (encryption, validation, sanitization)

**Implementation:**
- **At Rest**: Use Python `cryptography` library with Fernet (AES-256-CBC)
- **In Transit**: TLS 1.3 for WebSocket connections
- **Input Validation**: Pydantic models + DOMPurify for HTML sanitization
- **Tool Isolation**: Permission checks before every tool execution (FR-016)

**Best Practices:**
- Store encryption keys in environment variables, never in code
- Use PBKDF2 for key derivation if user passwords involved
- Implement CSP headers to prevent XSS
- Sanitize all user inputs before storage or execution
- Use parameterized queries to prevent SQL injection

---

## State Management

### Decision: Zustand for Extension State

**Rationale:**
- **Lightweight**: Minimal bundle size impact (<1KB)
- **TypeScript Support**: First-class TypeScript integration
- **No Boilerplate**: Simpler than Redux for extension use case
- **React Integration**: Hooks-based API aligns with React patterns

**Alternatives Considered:**
- **Redux**: Rejected due to excessive boilerplate for extension scale
- **Context API**: Rejected due to performance issues with frequent updates
- **Jotai/Recoil**: Rejected due to smaller ecosystem and less maturity

**State Structure:**
```typescript
interface AppState {
  agents: Agent[]
  activeAgentId: string | null
  commandQueue: Command[]
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
  currentSession: Session | null
}
```

---

## Testing Strategy

### Decision: pytest (Backend) + Vitest (Extension) + Playwright (E2E)

**Rationale:**
- **pytest**: Industry standard for Python, excellent async support, rich plugin ecosystem
- **Vitest**: Fast, Vite-native, compatible with Jest API, better TypeScript support
- **Playwright**: Cross-browser E2E testing, supports Chrome extensions

**Test Coverage Targets:**
- Unit tests: 80% coverage minimum
- Integration tests: All API endpoints and WebSocket flows
- E2E tests: Critical user journeys (P1 and P2 user stories)

**Best Practices:**
- Use fixtures for test data setup
- Mock external APIs (OpenAI) in unit tests
- Use test databases (in-memory SQLite) for integration tests
- Implement CI/CD pipeline with automated testing
- Use snapshot testing for UI components

---

## Performance Optimization

### Strategies to Meet Performance Requirements

**Command Execution (<2s - SC-005):**
- Cache agent configurations in memory
- Use connection pooling for database
- Implement lazy loading for tool modules
- Optimize DOM queries with efficient selectors

**Memory Usage (<500MB - SC-008):**
- Implement conversation history pagination
- Use streaming responses instead of buffering
- Limit in-memory agent cache size
- Implement garbage collection for inactive sessions

**Concurrent Agents (5 minimum - FR-014):**
- Use asyncio for concurrent execution
- Implement task queues with priority
- Use connection pooling to prevent resource exhaustion
- Monitor and limit per-agent resource usage

---

## Deployment Architecture

### Decision: Local Backend + Browser Extension

**Rationale:**
- **MVP Simplicity**: No cloud infrastructure required for MVP
- **Privacy**: User data stays local (aligns with User Sovereignty principle)
- **Cost**: No hosting costs for MVP
- **Performance**: No network latency for backend communication

**Future Considerations (Phase 2):**
- Cloud deployment option for team collaboration
- Containerization with Docker for easier distribution
- Kubernetes for horizontal scaling

---

## Monitoring and Observability

### Decision: Structured Logging + Local Log Files

**Rationale:**
- **Constitutional Requirement**: Logging and Observability Standards mandate structured, timestamped, queryable logs
- **Debugging**: Essential for troubleshooting agent behavior (FR-015)
- **Audit Trail**: Required for tool execution tracking

**Implementation:**
- Use Python `structlog` for structured logging
- Log format: JSON with timestamp, level, agent_id, tool_name, message
- Log rotation to prevent disk space issues
- Separate log files for agents, tools, websocket, errors

**Best Practices:**
- Include correlation IDs for request tracing
- Log all tool executions with inputs/outputs
- Implement log levels (DEBUG, INFO, WARNING, ERROR)
- Sanitize sensitive data before logging
- Implement log aggregation for production

---

## Error Handling Strategy

### Decision: Graceful Degradation with User Feedback

**Rationale:**
- **Clarification Requirement**: Best-effort availability with graceful degradation (SC-013)
- **User Experience**: Clear error messages (FR-004)
- **Resilience**: System continues operating during partial failures (Principle 8)

**Implementation:**
- Command queueing when AI service unavailable (FR-022)
- 30-second timeout with cancellation (FR-024)
- Retry logic with exponential backoff
- Fallback to cached responses where appropriate
- Clear error messages with suggested actions

---

## Development Workflow

### Recommended Practices

**Version Control:**
- Git with feature branches
- Conventional commits for changelog generation
- PR reviews required for main branch

**Code Quality:**
- Pre-commit hooks (black, isort, mypy for Python; prettier, eslint for TypeScript)
- Type checking enforced (mypy, TypeScript strict mode)
- Linting enforced (ruff for Python, eslint for TypeScript)

**Documentation:**
- Docstrings for all public functions
- OpenAPI/Swagger for API documentation
- README with setup instructions
- Architecture decision records (ADRs) for significant decisions

---

## Summary of Key Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend Framework | FastAPI | Async support, performance, OpenAI SDK integration |
| Agent Orchestration | OpenAI Agents SDK | Constitutional requirement, built-in tool calling |
| Extension Framework | Plasmo + React | Manifest V3 support, modern tooling, React ecosystem |
| Database | SQLite + SQLAlchemy | Constitutional requirement, zero config, ACID compliance |
| Communication | WebSocket + JSON | Real-time bidirectional, low latency, streaming support |
| Encryption | AES-256 + TLS | Security requirements, defense in depth |
| State Management | Zustand | Lightweight, TypeScript support, minimal boilerplate |
| Testing | pytest + Vitest + Playwright | Industry standards, comprehensive coverage |

All decisions align with constitutional principles and meet functional requirements specified in spec.md.
