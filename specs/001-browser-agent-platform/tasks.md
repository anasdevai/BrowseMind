# Implementation Tasks: BrowserMind - Autonomous Browser Intelligence Platform

**Feature**: 001-browser-agent-platform | **Date**: 2026-02-17 | **Branch**: `001-browser-agent-platform`

**Input**: Implementation plan from `plan.md`, specification from `spec.md`, data model from `data-model.md`, contracts from `contracts/`

---

## Summary

This document breaks down the BrowserMind platform implementation into executable tasks organized by user story. Each phase represents a complete, independently testable increment.

**Total Tasks**: 140
**User Stories**: 4 (P1-P4)
**Parallel Opportunities**: 42 tasks marked [P]
**MVP Scope**: Phase 3 (User Story 1 - Natural Language Browser Control)

---

## Implementation Strategy

**Approach**: Incremental delivery by user story priority
- **Phase 1**: Setup - Project initialization and tooling
- **Phase 2**: Foundational - Blocking prerequisites for all user stories
- **Phase 3**: User Story 1 (P1) - Natural Language Browser Control (MVP)
- **Phase 4**: User Story 2 (P2) - Create and Manage Specialized Assistants
- **Phase 5**: User Story 3 (P3) - Persistent Memory Across Sessions
- **Phase 6**: User Story 4 (P4) - Multi-Agent Task Coordination
- **Final Phase**: Polish & Cross-Cutting Concerns

**MVP Definition**: Phase 3 completion enables basic browser control via natural language commands.

---

## Phase 1: Setup (Project Initialization)

**Goal**: Establish project structure, dependencies, and development environment

**Independent Test Criteria**:
- [ ] Backend server starts without errors
- [ ] Extension builds successfully
- [ ] Database initializes with correct schema
- [ ] All dependencies install without conflicts

### Tasks

- [x] T001 Create backend directory structure per plan.md (app/agents, app/tools, app/db, app/websocket, tests/)
- [x] T002 Create extension directory structure per plan.md (src/background, src/content, src/sidepanel, src/components, src/lib, src/types)
- [x] T003 [P] Initialize backend Python project with pyproject.toml and requirements.txt
- [x] T004 [P] Initialize extension with package.json and Plasmo configuration
- [x] T005 [P] Create backend/.env.example with all required environment variables
- [x] T006 [P] Create extension/.env.example with backend URL configuration
- [x] T007 [P] Set up backend virtual environment using uv (uv venv)
- [x] T008 [P] Install backend dependencies (FastAPI, OpenAI SDK, SQLAlchemy, cryptography, structlog)
- [X] T009 [P] Install extension dependencies (Plasmo, React, TailwindCSS, shadcn/ui, Zustand)
- [x] T010 [P] Configure TailwindCSS for extension in tailwind.config.js
- [x] T011 [P] Configure TypeScript for extension in tsconfig.json (strict mode)
- [x] T012 [P] Set up pytest configuration in backend/pytest.ini
- [x] T013 [P] Set up Vitest configuration in extension/vitest.config.ts
- [x] T014 [P] Create extension/public/manifest.json for Manifest V3
- [x] T015 [P] Create backend/app/config.py for environment variable loading
- [x] T016 Create backend/README.md with basic setup instructions using uv (initial version for Phase 1 development)
- [x] T017 Create extension/README.md with build and load instructions (initial version for Phase 1 development)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement core infrastructure required by all user stories

**Independent Test Criteria**:
- [ ] Database schema matches data-model.md specification
- [ ] WebSocket connection establishes successfully
- [ ] Encryption/decryption works for sensitive fields
- [ ] Tool registry loads predefined capabilities

### Tasks

#### Database Layer

- [x] T018 Create backend/app/db/models.py with SQLAlchemy base and all 6 entities (Assistant, Session, Message, Capability, AssistantCapability, ToolLog)
- [x] T019 Implement AES-256 encryption utilities in backend/app/db/encryption.py using cryptography.fernet
- [x] T020 Create database session management in backend/app/db/session.py with connection pooling
- [x] T021 Create database initialization script in backend/app/db/init_db.py (creates tables, seeds 10 capabilities: navigate, click_element, type_text, extract_text, extract_links, extract_tables, scroll, screenshot, get_dom, highlight_element)
- [x] T022 Add SQLite WAL mode configuration in backend/app/db/session.py
- [x] T023 Implement 90-day retention cleanup job infrastructure in backend/app/db/cleanup.py (scheduled job framework, database cleanup utilities)

#### WebSocket Infrastructure

- [x] T024 Create WebSocket connection manager in backend/app/websocket/manager.py (handles connections, heartbeat)
- [x] T025 Implement WebSocket message handler in backend/app/websocket/handler.py (routes 17 message types)
- [x] T026 Create command queue with 30s timeout in backend/app/websocket/queue.py
- [x] T027 Implement rate limiting (100 messages/min) in backend/app/websocket/rate_limiter.py
- [x] T028 Add WebSocket error handling and protocol versioning in backend/app/websocket/protocol.py

#### Extension Core

- [x] T029 Create background service worker in extension/src/background/index.ts
- [x] T030 Implement WebSocket client in extension/src/background/websocket-client.ts (auto-reconnect, heartbeat)
- [x] T031 Create Zustand store in extension/src/lib/store.ts (agents, commands, connection status)
- [x] T032 Define TypeScript types in extension/src/types/agent.ts, command.ts, websocket.ts
- [x] T033 Create message passing utilities between background/content/sidepanel in extension/src/lib/messaging.ts

#### FastAPI Application

- [x] T034 Create FastAPI app in backend/app/main.py with CORS, WebSocket endpoint, startup/shutdown events
- [x] T035 Implement structured logging with structlog in backend/app/logging_config.py
- [x] T036 Add health check endpoint GET /health in backend/app/main.py
- [x] T037 Configure OpenAPI documentation in backend/app/main.py
- [x] T037a Implement tab refresh session recovery in extension/src/background/index.ts (restore session context, reconnect WebSocket)

**Note on TLS (FR-027)**: TLS encryption for WebSocket connections is handled by the WebSocket library configuration (wss:// protocol) and does not require a separate implementation task. Production deployment must use wss:// URLs.

---

## Phase 3: User Story 1 (P1) - Natural Language Browser Control

**User Story**: As a user, I want to control my browser using natural language commands so that I can automate repetitive tasks without writing code.

**Goal**: Enable basic browser control via natural language (navigate, click, type, extract)

**Independent Test Criteria**:
- [ ] User can send "Navigate to https://example.com" and browser navigates
- [ ] User can send "Click the login button" and element is clicked
- [ ] User can send "Type 'hello' in search box" and text is entered
- [ ] User can send "Extract the page title" and receives text response
- [ ] Commands execute in <2 seconds for local operations
- [ ] Extension shows real-time status updates during execution

### Tasks

#### Browser Control Tools

- [X] T038 [P] [US1] Create tool base class in backend/app/tools/base.py (Tool interface, registry, validation)
- [X] T039 [P] [US1] Implement navigate tool in backend/app/tools/browser_tools.py (url, wait_until, timeout)
- [X] T040 [P] [US1] Implement click_element tool in backend/app/tools/browser_tools.py (selector, text, index)
- [X] T041 [P] [US1] Implement type_text tool in backend/app/tools/browser_tools.py (selector, text, clear_first, press_enter)
- [X] T042 [P] [US1] Implement extract_text tool in backend/app/tools/extraction_tools.py (selector, all, trim)
- [X] T043 [P] [US1] Implement extract_links tool in backend/app/tools/extraction_tools.py (selector, filter options)
- [X] T044 [P] [US1] Implement scroll tool in backend/app/tools/browser_tools.py (direction, amount, smooth)
- [X] T045 [P] [US1] Implement screenshot tool in backend/app/tools/browser_tools.py (selector, full_page, format)

#### Content Script (DOM Control)

- [X] T046 [US1] Create content script entry point in extension/src/content/index.tsx
- [X] T047 [US1] Implement DOM controller in extension/src/content/dom-controller.ts (navigate, click, type, scroll)
- [X] T048 [US1] Implement element selector in extension/src/content/element-selector.ts (CSS selector, text matching)
- [X] T049 [US1] Implement text extraction in extension/src/content/dom-controller.ts (extract_text, extract_links)
- [X] T050 [US1] Add screenshot capture in extension/src/content/dom-controller.ts using chrome.tabs.captureVisibleTab

#### Agent Orchestration

- [X] T051 [US1] Create base agent class in backend/app/agents/base_agent.py (OpenAI SDK integration, tool calling)
- [X] T052 [US1] Implement main orchestrator agent in backend/app/agents/main_agent.py (command parsing, tool execution)
- [X] T053 [US1] Add tool permission validator in backend/app/tools/permission_validator.py (checks AssistantCapability)
- [X] T054 [US1] Implement streaming response handler in backend/app/agents/base_agent.py

#### Extension UI (Sidebar)

- [X] T055 [US1] Create sidepanel entry point in extension/src/sidepanel/index.tsx
- [X] T056 [US1] Implement Chat component in extension/src/sidepanel/Chat.tsx (message list, input, send)
- [X] T057 [US1] Implement StatusIndicator component in extension/src/sidepanel/StatusIndicator.tsx (connection, execution status)
- [X] T058 [US1] Add shadcn/ui components (Button, Input, Card, Badge) to extension/src/components/ui/
- [X] T059 [US1] Implement message rendering with markdown support in extension/src/sidepanel/MessageList.tsx

#### Integration

- [X] T060 [US1] Connect WebSocket handler to agent orchestrator in backend/app/websocket/handler.py (command message → agent execution)
- [X] T061 [US1] Connect background script to content script for tool execution in extension/src/background/index.ts
- [X] T062 [US1] Implement status_update message flow (backend → extension → UI) in extension/src/lib/store.ts
- [X] T063 [US1] Add error handling and user-friendly error messages in extension/src/sidepanel/Chat.tsx

---

## Phase 4: User Story 2 (P2) - Create and Manage Specialized Assistants

**User Story**: As a user, I want to create specialized assistants with specific capabilities so that I can have focused tools for different tasks.

**Goal**: Enable assistant lifecycle management (create, configure, activate, delete)

**Independent Test Criteria**:
- [ ] User can create assistant with name, instructions, and selected capabilities
- [ ] User can activate/deactivate assistants
- [ ] User can delete assistants
- [ ] User can view list of all assistants with status
- [ ] Maximum 20 assistants enforced
- [ ] Maximum 10 capabilities per assistant enforced
- [ ] Only active assistant receives commands

### Tasks

#### Assistant Management Backend

- [X] T064 [P] [US2] Implement create_assistant handler in backend/app/websocket/handler.py (validates max 20 assistants)
- [X] T065 [P] [US2] Implement activate_assistant handler in backend/app/websocket/handler.py (deactivates others)
- [X] T066 [P] [US2] Implement deactivate_assistant handler in backend/app/websocket/handler.py
- [X] T067 [P] [US2] Implement delete_assistant handler in backend/app/websocket/handler.py (cascade delete sessions)
- [X] T068 [P] [US2] Implement list_assistants handler in backend/app/websocket/handler.py
- [X] T069 [US2] Add assistant capability validation in backend/app/tools/permission_validator.py (max 10 tools)
- [X] T070 [US2] Create assistant registry in backend/app/agents/registry.py (dynamic loading, metadata)

#### Assistant Management UI

- [X] T071 [US2] Create AssistantList component in extension/src/sidepanel/AssistantList.tsx (list, status badges)
- [X] T072 [US2] Create CreateAssistantForm component in extension/src/sidepanel/CreateAssistantForm.tsx (name, instructions, capabilities)
- [X] T073 [US2] Implement capability selector in extension/src/sidepanel/CapabilitySelector.tsx (checkboxes, max 10 validation)
- [X] T074 [US2] Add assistant actions (activate, deactivate, delete) in extension/src/sidepanel/AssistantList.tsx
- [X] T075 [US2] Update Zustand store with assistant management actions in extension/src/lib/store.ts

#### Integration

- [X] T076 [US2] Connect create_assistant form to WebSocket in extension/src/sidepanel/CreateAssistantForm.tsx
- [X] T077 [US2] Implement assistant list sync on connection in extension/src/background/websocket-client.ts
- [X] T078 [US2] Add active assistant indicator in extension/src/sidepanel/Chat.tsx header

---

## Phase 5: User Story 3 (P3) - Persistent Memory Across Sessions

**User Story**: As a user, I want my assistants to remember previous conversations so that I can continue tasks across browser sessions.

**Goal**: Enable conversation persistence and retrieval across sessions

**Independent Test Criteria**:
- [ ] Conversation history persists after browser restart
- [ ] User can view previous conversations
- [ ] Sessions auto-archive after 90 days
- [ ] User can manually archive sessions
- [ ] Encrypted fields (instructions, messages) decrypt correctly
- [ ] Session list shows last active timestamp

### Tasks

#### Session Management Backend

- [X] T079 [P] [US3] Implement session creation on first command in backend/app/websocket/handler.py
- [X] T080 [P] [US3] Implement message persistence in backend/app/websocket/handler.py (encrypt content)
- [X] T081 [P] [US3] Implement session retrieval in backend/app/websocket/handler.py (decrypt messages)
- [X] T082 [P] [US3] Implement archive_session handler in backend/app/websocket/handler.py
- [X] T083 [US3] Add 90-day expiration check logic in backend/app/db/cleanup.py (queries expired sessions, marks for deletion, integrates with T023 cleanup job)
- [X] T084 [US3] Implement session list with pagination in backend/app/websocket/handler.py

#### Session Management UI

- [X] T085 [US3] Create SessionList component in extension/src/sidepanel/SessionList.tsx (list, timestamps, archive button)
- [X] T086 [US3] Implement session switching in extension/src/sidepanel/SessionList.tsx (loads conversation history)
- [X] T087 [US3] Add "New Session" button in extension/src/sidepanel/Chat.tsx
- [X] T088 [US3] Update Zustand store with session management in extension/src/lib/store.ts

#### Integration

- [X] T089 [US3] Load active session on extension startup in extension/src/background/index.ts
- [X] T090 [US3] Sync conversation history to UI on session switch in extension/src/lib/store.ts
- [X] T091 [US3] Implement optimistic UI updates for messages in extension/src/sidepanel/Chat.tsx

---

## Phase 6: User Story 4 (P4) - Multi-Agent Task Coordination

**User Story**: As a user, I want to run multiple commands concurrently so that I can multitask efficiently.

**Goal**: Enable command queueing and concurrent execution (5 agents minimum)

**Independent Test Criteria**:
- [ ] User can queue multiple commands while one is executing
- [ ] Queue status shows all pending commands
- [ ] User can cancel queued commands
- [ ] System handles 5 concurrent agents without degradation
- [ ] Memory usage stays <500MB with 5 active agents
- [ ] Commands timeout after 30 seconds with clear error message

### Tasks

#### Concurrent Execution Backend

- [X] T092 [P] [US4] Implement concurrent command execution in backend/app/websocket/queue.py (asyncio, max 5)
- [X] T093 [P] [US4] Add command cancellation in backend/app/websocket/queue.py
- [X] T094 [P] [US4] Implement queue_status message in backend/app/websocket/handler.py (queued, in_progress)
- [X] T095 [US4] Add resource monitoring in backend/app/agents/base_agent.py (memory, execution time)
- [X] T096 [US4] Implement graceful degradation when queue full in backend/app/websocket/queue.py

#### Queue Management UI

- [X] T097 [US4] Create CommandQueue component in extension/src/sidepanel/CommandQueue.tsx (list, status, cancel button)
- [X] T098 [US4] Add queue status indicator in extension/src/sidepanel/StatusIndicator.tsx (X queued, Y executing)
- [X] T099 [US4] Implement command cancellation in extension/src/sidepanel/CommandQueue.tsx
- [X] T100 [US4] Update Zustand store with queue management in extension/src/lib/store.ts

#### Integration

- [X] T101 [US4] Connect queue_status updates to UI in extension/src/lib/store.ts
- [X] T102 [US4] Add visual feedback for queued vs executing commands in extension/src/sidepanel/Chat.tsx

---

## Final Phase: Polish & Cross-Cutting Concerns

**Goal**: Production readiness, testing, documentation, and deployment

**Independent Test Criteria**:
- [ ] All unit tests pass with >80% coverage
- [ ] E2E tests cover critical user journeys
- [ ] Extension loads without errors in Chrome
- [ ] Backend starts and serves requests
- [ ] Documentation is complete and accurate

### Tasks

#### Testing

- [X] T103 [P] Write unit tests for database models in backend/tests/unit/test_models.py
- [X] T104 [P] Write unit tests for encryption utilities in backend/tests/unit/test_encryption.py
- [X] T105 [P] Write unit tests for tool implementations in backend/tests/unit/test_tools.py
- [X] T106 [P] Write unit tests for permission validator in backend/tests/unit/test_permissions.py
- [X] T107 [P] Write unit tests for agent orchestration in backend/tests/unit/test_agents.py
- [X] T108 [P] Write integration tests for WebSocket protocol in backend/tests/integration/test_websocket.py
- [X] T109 [P] Write integration tests for agent lifecycle in backend/tests/integration/test_agent_lifecycle.py
- [X] T110 [P] Write integration tests for session persistence in backend/tests/integration/test_persistence.py
- [X] T111 [P] Write unit tests for DOM controller in extension/tests/unit/dom-controller.test.ts
- [X] T112 [P] Write unit tests for element selector in extension/tests/unit/element-selector.test.ts
- [X] T113 Write E2E test for basic navigation in extension/tests/e2e/browser-control.spec.ts using Playwright
- [X] T114 Write E2E test for assistant creation in extension/tests/e2e/assistant-management.spec.ts
- [X] T115 Write E2E test for session persistence in extension/tests/e2e/session-persistence.spec.ts
- [X] T115a Write integration test for memory isolation between assistants in backend/tests/integration/test_memory_isolation.py (verify assistant A cannot access assistant B's session data)

#### Security & Performance

- [X] T116 [P] Implement input sanitization for all user inputs in backend/app/tools/sanitizer.py
- [X] T117 [P] Add CSP headers in extension manifest.json
- [X] T118 [P] Implement SQL injection prevention (parameterized queries) in backend/app/db/models.py
- [X] T119 [P] Add XSS prevention (DOMPurify) in extension/src/sidepanel/MessageList.tsx
- [X] T120 [P] Implement rate limiting per connection in backend/app/websocket/rate_limiter.py
- [X] T121 Optimize database queries with indexes in backend/app/db/models.py
- [X] T122 Implement connection pooling in backend/app/db/session.py
- [X] T123 Add performance monitoring in backend/app/logging_config.py (execution time, memory)
- [X] T123a Implement command success rate tracking in backend/app/websocket/handler.py (track success/failure per command type, expose metrics endpoint)

#### Observability

- [X] T124 [P] Implement structured logging for all tool executions in backend/app/tools/base.py
- [X] T125 [P] Add correlation IDs for request tracing in backend/app/websocket/handler.py
- [X] T126 [P] Implement log rotation in backend/app/logging_config.py
- [X] T127 Create separate log files (agents.log, tools.log, websocket.log, errors.log) in backend/app/logging_config.py

#### Documentation

- [X] T128 [P] Update backend/README.md with complete setup instructions using uv
- [X] T129 [P] Update extension/README.md with build and installation instructions
- [X] T130 [P] Create API documentation using FastAPI OpenAPI in backend/app/main.py
- [X] T131 [P] Document WebSocket protocol in backend/README.md
- [X] T132 [P] Create troubleshooting guide in specs/001-browser-agent-platform/troubleshooting.md
- [X] T133 Create deployment guide in specs/001-browser-agent-platform/deployment.md

#### Build & Deployment

- [X] T134 [P] Create production build script for extension in extension/package.json
- [X] T135 [P] Create Docker configuration for backend in backend/Dockerfile
- [X] T136 [P] Create docker-compose.yml for local development
- [X] T137 Create GitHub Actions workflow for CI/CD in .github/workflows/ci.yml

---

## Dependencies

### User Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Final Phase
```

**Blocking Dependencies**:
- Phase 2 blocks all user story phases (foundational infrastructure required)
- Phase 3 (US1) blocks Phase 4 (US2) - assistant management requires working browser control
- Phase 4 (US2) blocks Phase 5 (US3) - session persistence requires assistant management
- Phase 5 (US3) blocks Phase 6 (US4) - concurrent execution requires session management

**Independent User Stories**: None - each builds on previous

---

## Parallel Execution Opportunities

### Phase 1 (Setup)
**Parallel Group 1**: T003, T004, T005, T006 (project initialization files)
**Parallel Group 2**: T007, T008, T009 (dependency installation)
**Parallel Group 3**: T010, T011, T012, T013, T014, T015 (configuration files)

### Phase 2 (Foundational)
**Parallel Group 1**: T029, T030, T031, T032, T033 (extension core - independent of backend)

### Phase 3 (User Story 1)
**Parallel Group 1**: T038, T039, T040, T041, T042, T043, T044, T045 (all browser control tools - independent implementations)

### Phase 4 (User Story 2)
**Parallel Group 1**: T064, T065, T066, T067, T068 (all assistant management handlers - independent endpoints)

### Phase 5 (User Story 3)
**Parallel Group 1**: T079, T080, T081, T082 (all session management handlers - independent endpoints)

### Phase 6 (User Story 4)
**Parallel Group 1**: T092, T093, T094 (queue management features - independent implementations)

### Final Phase (Polish)
**Parallel Group 1**: T103, T104, T105, T106, T107, T109, T110, T111, T112 (all unit tests - independent)
**Parallel Group 2**: T116, T117, T118, T119, T120 (all security features - independent)
**Parallel Group 3**: T124, T125, T126 (all observability features - independent)
**Parallel Group 4**: T128, T129, T130, T131, T132 (all documentation - independent)
**Parallel Group 5**: T134, T135, T136 (all build/deployment - independent)

---

## Task Validation

**Format Compliance**: ✅ All 140 tasks follow checklist format with IDs, [P] markers, [Story] labels, and file paths

**Coverage Check**:
- ✅ User Story 1 (P1): 26 tasks covering browser control, DOM manipulation, agent orchestration, UI
- ✅ User Story 2 (P2): 15 tasks covering assistant lifecycle, capability management, UI
- ✅ User Story 3 (P3): 13 tasks covering session persistence, encryption, archiving, UI
- ✅ User Story 4 (P4): 11 tasks covering concurrent execution, queueing, cancellation, UI
- ✅ Setup: 17 tasks covering project structure, dependencies, configuration
- ✅ Foundational: 20 tasks covering database, WebSocket, extension core, FastAPI, tab refresh recovery
- ✅ Polish: 38 tasks covering testing, security, observability, documentation, deployment, metrics

**Independent Testability**: ✅ Each phase has clear acceptance criteria and can be validated independently

**File Path Specificity**: ✅ All tasks include exact file paths for implementation

---

## Suggested MVP Scope

**Minimum Viable Product**: Phase 3 (User Story 1) completion

**Rationale**:
- Delivers core value proposition: natural language browser control
- Includes foundational infrastructure (database, WebSocket, agent orchestration, tab refresh recovery)
- Enables basic user workflows (navigate, click, type, extract)
- Provides working UI for command input and status display
- ~64 tasks (Setup + Foundational + US1)

**Post-MVP Increments**:
- **Increment 2**: Add Phase 4 (US2) for assistant management
- **Increment 3**: Add Phase 5 (US3) for persistent memory
- **Increment 4**: Add Phase 6 (US4) for concurrent execution
- **Increment 5**: Add Final Phase for production readiness

---

## Notes

- All tasks reference specific files from plan.md project structure
- Tool schemas validated against contracts/tool-schemas.json
- Database schema validated against data-model.md
- WebSocket protocol validated against contracts/websocket-protocol.md
- Security requirements validated against research.md decisions
- Performance targets validated against plan.md constraints (<2s execution for local operations, <500MB memory, 5 concurrent agents)
- TLS encryption (FR-027) handled by WebSocket library configuration (wss:// protocol)
- Tab refresh recovery (FR-017) implemented in T037a
- Terminology standardized: "Assistant" used consistently (runtime instances still use "agent" in code paths like backend/app/agents/)
- T023 creates cleanup job infrastructure, T083 adds session expiration logic
- T016/T017 create initial READMEs for Phase 1, T128/T129 add complete production documentation
- Success rate tracking (SC-001) implemented in T123a
- Memory isolation (FR-012) tested in T115a
- Measurement methodologies defined in spec.md for SC-005, SC-007, SC-009
