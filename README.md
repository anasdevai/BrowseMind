# BrowserMind - Autonomous Browser Intelligence Platform

A production-ready browser automation platform powered by OpenAI Assistants API with multi-provider LLM support (OpenRouter/OpenAI).

## 🚀 Features

- **OpenAI Assistants API Integration**: Production-ready agent system using OpenAI's official Agent SDK
- **Multi-Provider LLM Support**: OpenRouter for access to Claude, GPT-4, and other models
- **Multi-Agent Orchestration**: Coordinate multiple specialized assistants
- **Real-time WebSocket Communication**: Bidirectional streaming with protocol v1.0.0
- **Browser Control Tools**: 10 capabilities (navigate, click, type, extract, scroll, screenshot, etc.)
- **Persistent Memory**: 90-day session retention with automatic cleanup
- **Command Queue**: Concurrent execution with timeout management (max 5 concurrent)
- **Rate Limiting**: Token bucket algorithm (100 messages/min)
- **Security**: AES-256 encryption, CORS protection, capability-based permissions
- **Production-Ready**: Health checks, monitoring, graceful shutdown

## 📋 Quick Start

### Backend Setup

1. **Activate environment:**
```bash
cd backend
source .venv/Scripts/activate  # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Start server:**
```bash
python -m app.main
```

### Extension Setup

1. **Install and build:**
```bash
cd extension
npm install
npm run build
```

2. **Load in Chrome:**
- Open `chrome://extensions/`
- Enable "Developer mode"
- Click "Load unpacked"
- Select `extension/build/chrome-mv3-prod`

## 🔧 Configuration

### OpenRouter (Recommended)

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

Get your API key from https://openrouter.ai/

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

## 🏗️ Architecture

- **Backend**: FastAPI + OpenAI Assistants API + SQLite
- **Extension**: Plasmo + React + TypeScript + Zustand
- **Communication**: WebSocket Protocol v1.0.0

## 📝 License

MIT License
