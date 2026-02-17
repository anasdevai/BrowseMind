# BrowserMind Troubleshooting Guide

## Common Issues and Solutions

### Backend Issues

#### "OpenRouter API key not configured"

**Problem:** Backend fails to start with error about missing API key.

**Solution:**
1. Create `.env` file in `backend/` directory
2. Add your API key:
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

**Get API key:**
- OpenRouter: https://openrouter.ai/
- OpenAI: https://platform.openai.com/

---

#### "Database encryption key not configured"

**Problem:** Backend fails with validation error about encryption key.

**Solution:**
Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:
```env
DATABASE_ENCRYPTION_KEY=YOUR_GENERATED_KEY_HERE
```

---

#### "Port 8000 already in use"

**Problem:** Backend fails to start because port is occupied.

**Solution:**
1. Find process using port:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

2. Kill process or change port in `.env`:
```env
PORT=8001
```

---

#### Backend starts but WebSocket connection fails

**Problem:** Extension can't connect to backend.

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify CORS settings in `.env`:
```env
CORS_ORIGINS=["http://localhost:3000","chrome-extension://*"]
```
3. Check firewall isn't blocking port 8000
4. Verify WebSocket URL in extension `.env`:
```env
PLASMO_PUBLIC_BACKEND_WS_URL=ws://localhost:8000/ws
```

---

### Extension Issues

#### Extension won't build - "Cannot find module @parcel/watcher"

**Problem:** npm install fails with native module errors.

**Solution:**
Install Visual Studio Build Tools:
1. Download from: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++"
3. Run: `npm install` again

**Alternative:**
Use WSL (Windows Subsystem for Linux) for building.

---

#### Extension loads but shows "Disconnected"

**Problem:** Extension can't connect to backend.

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check extension console for errors (F12 in sidepanel)
3. Verify WebSocket URL matches backend:
   - Extension: `ws://localhost:8000/ws`
   - Backend: Running on port 8000
4. Check browser console for CORS errors

---

#### "Failed to load extension" in Chrome

**Problem:** Chrome rejects extension during load.

**Solution:**
1. Verify build completed: Check `extension/build/chrome-mv3-prod` exists
2. Check manifest.json is valid
3. Enable Developer Mode in chrome://extensions/
4. Try "Load unpacked" again
5. Check Chrome console for specific errors

---

### Database Issues

#### "Database is locked"

**Problem:** SQLite database locked error.

**Solution:**
1. Close all connections to database
2. Restart backend server
3. If persists, delete `browsermind.db-wal` and `browsermind.db-shm` files
4. Restart backend

---

#### "No such table: assistants"

**Problem:** Database not initialized.

**Solution:**
```bash
cd backend
source .venv/Scripts/activate
python -c "from app.db.init_db import init_database; init_database()"
```

---

### OpenAI Assistants API Issues

#### "Rate limit exceeded"

**Problem:** Too many API requests.

**Solution:**
1. Wait 60 seconds before retrying
2. Reduce concurrent commands in queue
3. Check OpenRouter/OpenAI dashboard for limits
4. Consider upgrading API plan

---

#### "Model not found" or "Invalid model"

**Problem:** Specified model doesn't exist or isn't available.

**Solution:**
1. Check model name in `.env`:
```env
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

2. Verify model is available on OpenRouter:
   - Visit https://openrouter.ai/models
   - Check model ID matches exactly

3. Try fallback model:
```env
DEFAULT_MODEL=openai/gpt-4-turbo-preview
```

---

#### "Insufficient credits" or "Payment required"

**Problem:** OpenRouter/OpenAI account has no credits.

**Solution:**
1. Add credits to OpenRouter account
2. Or add payment method to OpenAI account
3. Check account dashboard for billing status

---

### Tool Execution Issues

#### "Tool execution failed: Element not found"

**Problem:** DOM selector can't find element.

**Solution:**
1. Verify page is fully loaded
2. Use more specific CSS selector
3. Try text-based selection instead
4. Check element exists in page (F12 → Elements)
5. Wait for dynamic content to load

---

#### "Permission denied" for tool

**Problem:** Assistant doesn't have capability.

**Solution:**
1. Check assistant capabilities:
   - Open AssistantList in extension
   - Verify capability is granted
2. Grant capability:
   - Edit assistant
   - Add required capability (max 10)
3. Activate assistant after changes

---

#### "Command timeout after 30 seconds"

**Problem:** Command takes too long to execute.

**Solution:**
1. Break command into smaller steps
2. Check network connectivity
3. Verify page isn't stuck loading
4. Increase timeout in backend (not recommended):
```python
# backend/app/websocket/queue.py
timeout_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(seconds=60))
```

---

### Performance Issues

#### Backend using too much memory

**Problem:** Memory usage grows over time.

**Solution:**
1. Check number of active assistants (max 20)
2. Archive old sessions
3. Restart backend periodically
4. Enable cleanup job in `.env`:
```env
ENABLE_CLEANUP_JOB=true
SESSION_RETENTION_DAYS=90
```

---

#### Slow response times

**Problem:** Commands take long to execute.

**Solution:**
1. Check OpenRouter/OpenAI API latency
2. Reduce concurrent commands (default: 5)
3. Use faster model:
```env
DEFAULT_MODEL=openai/gpt-3.5-turbo
```
4. Check database size (vacuum if large)

---

### Security Issues

#### "Rate limit exceeded" message

**Problem:** Too many WebSocket messages.

**Solution:**
This is normal rate limiting (100 msg/min). Wait 60 seconds.

To adjust (not recommended for production):
```env
WS_RATE_LIMIT=200
```

---

#### CORS errors in browser console

**Problem:** Cross-origin request blocked.

**Solution:**
Add extension origin to CORS in `.env`:
```env
CORS_ORIGINS=["http://localhost:3000","chrome-extension://*"]
```

Restart backend after changes.

---

## Debugging Tips

### Enable Debug Logging

Backend:
```env
LOG_LEVEL=debug
```

Extension:
- Open sidepanel
- Press F12 for DevTools
- Check Console tab

### Check WebSocket Messages

Extension DevTools → Network tab → WS → Messages

### Verify Database State

```bash
cd backend
sqlite3 browsermind.db
.tables
SELECT * FROM assistants;
.quit
```

### Test API Directly

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## Getting Help

1. **Check logs:**
   - Backend: Console output
   - Extension: Chrome DevTools console

2. **Verify configuration:**
   - Backend `.env` file
   - Extension `.env` file

3. **Test components:**
   - Backend health: `curl http://localhost:8000/health`
   - WebSocket: Check extension connection status

4. **Report issues:**
   - GitHub: https://github.com/browsermind/browsermind/issues
   - Include: Error messages, logs, configuration (redact API keys)

---

## Quick Fixes

### Reset Everything

```bash
# Stop backend
# Delete database
rm backend/browsermind.db*

# Reinitialize
cd backend
source .venv/Scripts/activate
python -c "from app.db.init_db import init_database; init_database()"

# Restart
./start.sh
```

### Clear Extension Data

1. chrome://extensions/
2. Find BrowserMind
3. Click "Remove"
4. Reload extension

### Regenerate Keys

```bash
# New encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# New secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env` with new keys and restart.
