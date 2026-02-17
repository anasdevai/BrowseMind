# BrowserMind Deployment Guide

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# LLM Provider Configuration
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
DEFAULT_MODEL=anthropic/claude-3.5-sonnet

# Database Configuration
DATABASE_URL=sqlite:///./browsermind.db
DATABASE_ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY_HERE

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=info

# Security
SECRET_KEY=YOUR_SECRET_KEY_HERE
CORS_ORIGINS=["http://localhost:3000","chrome-extension://*"]

# Features
ENABLE_CLEANUP_JOB=true
SESSION_RETENTION_DAYS=90
```

**Generate Keys:**

```bash
# Encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Initialize Database

```bash
python -c "from app.db.init_db import init_database; init_database()"
```

### 4. Start Server

```bash
python -m app.main
```

Server runs on `http://0.0.0.0:8000`

## 🔑 Getting API Keys

### OpenRouter (Recommended)

1. Visit https://openrouter.ai/
2. Sign up for an account
3. Go to Keys section
4. Create a new API key
5. Copy key (starts with `sk-or-v1-`)

**Benefits:**
- Access to multiple models (Claude, GPT-4, Gemini, Llama)
- Pay-per-use pricing
- No monthly subscription
- Automatic fallback between providers

### OpenAI (Alternative)

1. Visit https://platform.openai.com/
2. Sign up for an account
3. Go to API Keys
4. Create a new key
5. Copy key (starts with `sk-`)

Set in `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-YOUR_KEY_HERE
```

## 🧪 Testing

### Verify Installation

```bash
cd backend
source .venv/Scripts/activate

# Test imports
python -c "
from app.agents.assistant_agent import AssistantAgent
from app.agents.openai_orchestrator import get_orchestrator
from app.tools.base import get_tool_registry
print('[OK] All components loaded')
"

# Test server
python -m app.main
```

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "protocol_version": "1.0.0",
  "connections": {
    "active": 0,
    "max": 100
  }
}
```

## 🌐 Extension Setup

### 1. Install Dependencies

```bash
cd extension
npm install
```

### 2. Configure

Create `.env`:
```env
PLASMO_PUBLIC_BACKEND_WS_URL=ws://localhost:8000/ws
```

### 3. Build

```bash
npm run build
```

### 4. Load in Chrome

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension/build/chrome-mv3-prod`

## 🐳 Docker Deployment

### Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "app.main"]
```

### Build and Run

```bash
docker build -t browsermind-backend .
docker run -p 8000:8000 --env-file .env browsermind-backend
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=openrouter
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DEFAULT_MODEL=anthropic/claude-3.5-sonnet
      - DATABASE_URL=sqlite:///./data/browsermind.db
      - DATABASE_ENCRYPTION_KEY=${DATABASE_ENCRYPTION_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

## 🔒 Production Security

### Environment Variables

Never commit `.env` files. Use:
- Docker secrets
- Kubernetes secrets
- Cloud provider secret managers (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)

### HTTPS

Use reverse proxy (nginx, Caddy) for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name api.browsermind.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Rate Limiting

Configure in `.env`:
```env
WS_RATE_LIMIT=100  # messages per minute
WS_MAX_CONNECTIONS=100
```

## 📊 Monitoring

### Logs

```bash
# View logs
tail -f logs/browsermind.log

# Docker logs
docker logs -f browsermind-backend
```

### Metrics

Access metrics at:
- Health: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`

### Alerts

Set up monitoring for:
- Server uptime
- WebSocket connection count
- Command queue length
- Database size
- API response times

## 🔄 Updates

### Backend

```bash
cd backend
source .venv/Scripts/activate
git pull
pip install -r requirements.txt
python -m app.main
```

### Extension

```bash
cd extension
git pull
npm install
npm run build
# Reload extension in chrome://extensions/
```

## 🆘 Troubleshooting

### "OpenRouter API key not configured"

Set `OPENROUTER_API_KEY` in `.env` file.

### "Database encryption key not configured"

Generate key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:
```env
DATABASE_ENCRYPTION_KEY=your_generated_key_here
```

### WebSocket connection fails

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `.env`
3. Verify extension WebSocket URL matches backend

### Extension not loading

1. Check for build errors: `npm run build`
2. Verify manifest.json is valid
3. Check Chrome console for errors

## 📝 Maintenance

### Database Cleanup

Automatic cleanup runs every 24 hours (configurable):
```env
ENABLE_CLEANUP_JOB=true
SESSION_RETENTION_DAYS=90
```

Manual cleanup:
```bash
python -c "
from app.db.cleanup import cleanup_expired_sessions
import asyncio
asyncio.run(cleanup_expired_sessions())
"
```

### Backup

```bash
# Backup database
cp backend/browsermind.db backend/browsermind.db.backup

# Restore
cp backend/browsermind.db.backup backend/browsermind.db
```

## 🎯 Performance Tuning

### Backend

```env
# Increase concurrent commands
WS_MAX_CONNECTIONS=200

# Adjust timeouts
WS_TIMEOUT=60
```

### Database

For production, consider PostgreSQL:
```env
DATABASE_URL=postgresql://user:pass@localhost/browsermind
```

## 📞 Support

- Issues: https://github.com/browsermind/browsermind/issues
- Documentation: See README.md
- Discord: Community support channel
