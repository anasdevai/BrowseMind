# BrowserMind Backend

Backend service for BrowserMind - Autonomous Browser Intelligence Platform.

## Tech Stack

- **Python**: 3.11+
- **Framework**: FastAPI
- **AI**: OpenAI Agents SDK
- **Database**: SQLite with SQLAlchemy
- **WebSocket**: Native WebSocket support
- **Encryption**: AES-256 (cryptography.fernet)

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

## Quick Start

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Set up virtual environment

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key and encryption key
```

### 5. Initialize database

```bash
python -m app.db.init_db
```

### 6. Run development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

## Project Structure

```
backend/
├── app/
│   ├── agents/          # Agent orchestration and registry
│   ├── tools/           # Browser control tools
│   ├── db/              # Database models and utilities
│   ├── websocket/       # WebSocket handlers and queue
│   ├── config.py        # Configuration management
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Project configuration
```

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
black app tests
ruff check app tests
```

### Type checking

```bash
mypy app
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## WebSocket Endpoint

Connect to: `ws://localhost:8000/ws`

See `specs/001-browser-agent-platform/contracts/websocket-protocol.md` for protocol details.
