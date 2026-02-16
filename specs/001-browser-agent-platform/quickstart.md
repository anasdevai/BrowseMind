# Quickstart Guide: BrowserMind Development

**Feature**: 001-browser-agent-platform
**Date**: 2026-02-17
**Audience**: Developers setting up local development environment

## Overview

This guide walks you through setting up a local development environment for BrowserMind, running the system, and executing your first browser automation command.

**Time to Complete**: ~30 minutes

---

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **uv** (recommended) or **pip** - Python package manager
- **Node.js 18+** - Extension build tooling
- **pnpm** (or npm) - Package manager
- **Chrome/Edge/Brave** - Chromium-based browser
- **Git** - Version control

**Install uv** (recommended for faster package management):
```bash
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip:
pip install uv
```

### Required Accounts

- **OpenAI API Key** - For agent orchestration (get from https://platform.openai.com/api-keys)

### System Requirements

- **OS**: Windows 10+, macOS 12+, or Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space

---

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/browsemind.git
cd browsemind
git checkout 001-browser-agent-platform
```

---

## Step 2: Backend Setup

### 2.1 Create Virtual Environment

**Using uv (recommended - faster)**:
```bash
cd backend
uv venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows
```

**Using standard venv**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 2.2 Install Dependencies

**Using uv (recommended)**:
```bash
uv pip install -r requirements.txt
```

**Using pip**:
```bash
pip install -r requirements.txt
```

**Expected output**: ~50 packages installed including FastAPI, OpenAI SDK, SQLAlchemy

**Note**: `uv` is significantly faster than pip (10-100x) and is recommended for development. Install with: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2.3 Configure Environment

Create `.env` file in `backend/` directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Database Configuration
DATABASE_URL=sqlite:///./browsemind.db

# Server Configuration
HOST=localhost
PORT=8000
LOG_LEVEL=INFO

# Security
ENCRYPTION_KEY=generate-with-python-cryptography-fernet-generate-key
SECRET_KEY=generate-random-secret-key-here

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL=30
WS_TIMEOUT=300
```

**Generate encryption key**:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2.4 Initialize Database

```bash
python -m app.db.init_db
```

**Expected output**:
```
Creating database schema...
✓ Created tables: assistants, sessions, messages, capabilities, assistant_capabilities, tool_logs
✓ Seeded 10 predefined capabilities
Database initialized successfully at: ./browsemind.db
```

### 2.5 Verify Backend Setup

```bash
python -m pytest tests/unit -v
```

**Expected**: All unit tests pass (if tests exist)

---

## Step 3: Extension Setup

### 3.1 Install Dependencies

```bash
cd ../extension
pnpm install
# or: npm install
```

**Expected output**: ~200 packages installed including React, Plasmo, TailwindCSS

### 3.2 Configure Extension

Create `.env` file in `extension/` directory:

```env
# Backend Configuration
PLASMO_PUBLIC_BACKEND_URL=ws://localhost:8000/ws
PLASMO_PUBLIC_BACKEND_HTTP=http://localhost:8000

# Development
NODE_ENV=development
```

### 3.3 Build Extension

```bash
pnpm dev
# or: npm run dev
```

**Expected output**:
```
✓ Built extension in development mode
✓ Output: build/chrome-mv3-dev
✓ Watching for changes...
```

### 3.4 Load Extension in Browser

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select `extension/build/chrome-mv3-dev` directory
5. Extension icon should appear in toolbar

**Verify**: Extension icon visible, no errors in console

---

## Step 4: Start Backend Server

```bash
cd ../backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     WebSocket endpoint available at ws://localhost:8000/ws
```

**Verify**: Navigate to http://localhost:8000/docs - should see FastAPI Swagger UI

---

## Step 5: First Command Execution

### 5.1 Open Extension

1. Click BrowserMind icon in Chrome toolbar
2. Sidebar should open on the right side
3. Connection status should show "Connected" (green indicator)

**Troubleshooting**: If "Disconnected", check backend is running and `.env` URLs are correct

### 5.2 Create Your First Assistant

In the extension sidebar:

1. Click "Create Assistant" button
2. Fill in the form:
   - **Name**: "Web Navigator"
   - **Instructions**: "You are a helpful assistant that navigates websites and extracts information."
   - **Capabilities**: Select "navigate", "extract_text", "extract_links"
3. Click "Create"

**Expected**: Assistant appears in list with "Inactive" status

### 5.3 Activate Assistant

1. Click on "Web Navigator" in the assistant list
2. Click "Activate" button
3. Status should change to "Active" (green)

### 5.4 Execute First Command

In the chat input at the bottom:

```
Navigate to https://example.com and extract the main heading
```

**Expected behavior**:
1. Command appears in chat as user message
2. Status indicator shows "Executing..."
3. Browser navigates to example.com
4. Assistant responds with extracted heading: "Example Domain"
5. Status returns to "Ready"

**Execution time**: Should complete in <5 seconds

---

## Step 6: Verify Core Features

### 6.1 Test Command Queueing

Execute two commands rapidly:

```
Navigate to https://github.com
```

```
Extract all links from the page
```

**Expected**:
- First command executes immediately
- Second command shows "Queued" status
- Both complete successfully in sequence

### 6.2 Test Persistence

1. Close browser completely
2. Reopen browser
3. Open BrowserMind extension

**Expected**: "Web Navigator" assistant still exists and is active

### 6.3 Test Multiple Assistants

Create a second assistant:
- **Name**: "Data Extractor"
- **Instructions**: "You extract structured data from web pages."
- **Capabilities**: "extract_text", "extract_tables", "extract_links"

**Expected**: Both assistants visible in list, can switch between them

---

## Development Workflow

### Backend Development

**Run with auto-reload**:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Run tests**:
```bash
pytest tests/ -v --cov=app
```

**Check types**:
```bash
mypy app/
```

**Format code**:
```bash
black app/ tests/
isort app/ tests/
```

### Extension Development

**Development mode** (auto-reload):
```bash
cd extension
pnpm dev
```

**Run tests**:
```bash
pnpm test
```

**Type check**:
```bash
pnpm type-check
```

**Lint**:
```bash
pnpm lint
```

**Build for production**:
```bash
pnpm build
```

---

## Common Issues & Solutions

### Issue: Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Activate virtual environment and reinstall dependencies
```bash
# If using uv:
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt

# If using standard venv:
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### Issue: Extension shows "Disconnected"

**Possible causes**:
1. Backend not running → Start backend server
2. Wrong WebSocket URL → Check `extension/.env` has correct `PLASMO_PUBLIC_BACKEND_URL`
3. Port conflict → Change port in both backend and extension config

**Debug**: Check browser console (F12) for WebSocket errors

---

### Issue: "OpenAI API Error"

**Error**: `AuthenticationError: Invalid API key`

**Solution**:
1. Verify API key in `backend/.env`
2. Check key has credits at https://platform.openai.com/usage
3. Ensure no extra spaces or quotes around key

---

### Issue: Commands timeout

**Error**: Status shows "Timeout" after 30 seconds

**Possible causes**:
1. OpenAI API slow/unavailable → Check https://status.openai.com
2. Complex command → Simplify or break into steps
3. Network issues → Check internet connection

**Solution**: Commands are queued and will retry when service recovers

---

### Issue: Extension not loading

**Error**: "Manifest version 3 required"

**Solution**: Ensure using Chrome 88+ or Edge 88+. Manifest V3 not supported in older versions.

---

### Issue: Database locked

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
1. Close all backend instances
2. Delete `browsemind.db-wal` and `browsemind.db-shm` files
3. Restart backend

---

## Project Structure Reference

```
browsemind/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent orchestration
│   │   ├── tools/           # Browser control tools
│   │   ├── db/              # Database models
│   │   ├── websocket/       # WebSocket handlers
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Backend tests
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Configuration (create this)
├── extension/
│   ├── src/
│   │   ├── background/      # Service worker
│   │   ├── content/         # Content scripts
│   │   ├── sidepanel/       # Sidebar UI
│   │   └── components/      # React components
│   ├── package.json         # Node dependencies
│   └── .env                 # Configuration (create this)
└── specs/
    └── 001-browser-agent-platform/
        ├── spec.md          # Feature specification
        ├── plan.md          # Implementation plan
        ├── research.md      # Technical decisions
        ├── data-model.md    # Database schema
        ├── quickstart.md    # This file
        └── contracts/       # API contracts
```

---

## Next Steps

### Learn More

- **Architecture**: Read `specs/001-browser-agent-platform/plan.md`
- **Data Model**: Read `specs/001-browser-agent-platform/data-model.md`
- **API Contracts**: Read `specs/001-browser-agent-platform/contracts/`
- **Constitution**: Read `.specify/memory/constitution.md`

### Extend the System

- **Add New Tool**: See `backend/app/tools/browser_tools.py` for examples
- **Customize UI**: Modify `extension/src/sidepanel/` components
- **Add Tests**: Follow patterns in `backend/tests/` and `extension/tests/`

### Deploy

- **Production Build**: `pnpm build` in extension directory
- **Package Extension**: Zip `build/chrome-mv3-prod` directory
- **Backend Deployment**: Use Docker or systemd service

---

## Getting Help

### Documentation

- **Feature Spec**: `specs/001-browser-agent-platform/spec.md`
- **Technical Decisions**: `specs/001-browser-agent-platform/research.md`
- **WebSocket Protocol**: `specs/001-browser-agent-platform/contracts/websocket-protocol.md`

### Debugging

**Backend logs**: Check console output or `logs/` directory

**Extension logs**:
- Background script: `chrome://extensions/` → BrowserMind → "Inspect views: service worker"
- Content script: F12 on any webpage → Console tab
- Sidebar: Right-click sidebar → "Inspect"

**Database inspection**:
```bash
sqlite3 backend/browsemind.db
.tables
.schema assistants
SELECT * FROM assistants;
```

---

## Success Checklist

- [ ] Backend starts without errors
- [ ] Extension loads in Chrome
- [ ] Extension shows "Connected" status
- [ ] Can create assistant
- [ ] Can activate assistant
- [ ] Can execute "Navigate to https://example.com" command
- [ ] Browser navigates successfully
- [ ] Assistant responds with confirmation
- [ ] Assistant persists after browser restart

**If all checked**: You're ready to develop! 🎉

---

## Performance Benchmarks

Expected performance on development machine:

| Metric | Target | Typical |
|--------|--------|---------|
| Backend cold start | <2s | ~1s |
| Extension load | <2s | ~0.5s |
| WebSocket connection | <1s | ~0.2s |
| Simple command (navigate) | <2s | ~1.5s |
| Complex command (extract) | <5s | ~3s |
| Database query | <100ms | ~10ms |
| Memory usage (5 agents) | <500MB | ~300MB |

**Note**: First command may be slower due to OpenAI API cold start (~5-10s)

---

This quickstart guide gets you from zero to a working BrowserMind development environment in ~30 minutes. For production deployment, see deployment documentation (Phase 2).
