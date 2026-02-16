# BrowserMind Extension

Browser extension for BrowserMind - Autonomous Browser Intelligence Platform.

## Tech Stack

- **Framework**: Plasmo
- **UI**: React 18 + TypeScript 5.x
- **Styling**: TailwindCSS + shadcn/ui
- **State**: Zustand
- **Testing**: Vitest + Testing Library

## Prerequisites

- Node.js 18+ or Bun
- Backend service running (see `backend/README.md`)

## Quick Start

### 1. Install dependencies

```bash
cd extension
npm install
# or
pnpm install
# or
bun install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if backend URL is different from default
```

### 3. Run development build

```bash
npm run dev
```

### 4. Load extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/build/chrome-mv3-dev` directory

The extension will auto-reload on code changes.

## Project Structure

```
extension/
├── src/
│   ├── background/      # Service worker (Manifest V3)
│   ├── content/         # Content scripts for DOM control
│   ├── sidepanel/       # Side panel UI
│   ├── components/      # Reusable React components
│   ├── lib/             # Utilities and state management
│   └── types/           # TypeScript type definitions
├── public/              # Static assets and manifest
├── tests/               # Test suite
└── package.json         # Dependencies and scripts
```

## Development

### Running tests

```bash
npm test
```

### Running tests with UI

```bash
npm run test:ui
```

### Building for production

```bash
npm run build
```

The production build will be in `build/chrome-mv3-prod/`

### Packaging for distribution

```bash
npm run package
```

This creates a `.zip` file ready for Chrome Web Store submission.

## Features

- **Natural Language Control**: Control browser with conversational commands
- **Specialized Assistants**: Create custom assistants with specific capabilities
- **Persistent Memory**: Conversations persist across browser sessions
- **Real-time Status**: See command execution progress in real-time
- **Secure**: All sensitive data encrypted, permissions enforced

## Architecture

The extension communicates with the backend via WebSocket:

1. **Background Service Worker**: Manages WebSocket connection, message routing
2. **Content Scripts**: Execute DOM operations (click, type, extract)
3. **Side Panel**: User interface for chat and assistant management
4. **Zustand Store**: Centralized state management

See `specs/001-browser-agent-platform/contracts/websocket-protocol.md` for protocol details.

## Troubleshooting

### Extension not loading
- Ensure you're loading the correct directory (`build/chrome-mv3-dev`)
- Check Chrome DevTools console for errors
- Try removing and re-adding the extension

### WebSocket connection fails
- Verify backend is running at `http://localhost:8000`
- Check `.env` file has correct `PLASMO_PUBLIC_BACKEND_WS_URL`
- Look for CORS errors in browser console

### Hot reload not working
- Restart `npm run dev`
- Reload extension manually in `chrome://extensions/`
