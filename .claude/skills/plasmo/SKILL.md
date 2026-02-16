---
name: plasmo
description: Build browser extensions with Plasmo framework. Use when creating Chrome/Firefox extensions, browser plugins, content scripts, or when user mentions Plasmo, browser extension, popup, content script, background service worker, or extension development.
---

# Plasmo Framework Skill

When building browser extensions with Plasmo, follow these patterns:

## 1. Project Structure

```
extension/
├── assets/
│   ├── icon.png
│   └── logo.svg
├── src/
│   ├── background/
│   │   └── messages/
│   │       └── ping.ts
│   ├── components/
│   │   └── Button.tsx
│   ├── contents/
│   │   ├── overlay.tsx
│   │   └── sidebar.tsx
│   ├── tabs/
│   │   └── settings.tsx
│   ├── popup.tsx
│   └── options.tsx
├── package.json
├── tsconfig.json
└── .env
```

## 2. Popup Component (popup.tsx)

```typescript
import { useState, useEffect } from "react"
import "./style.css"

function IndexPopup() {
  const [data, setData] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Load data when popup opens
    chrome.storage.local.get(["userData"], (result) => {
      setData(result.userData || "")
    })
  }, [])

  const handleClick = async () => {
    setIsLoading(true)
    
    // Send message to background script
    const response = await chrome.runtime.sendMessage({
      type: "FETCH_DATA"
    })
    
    setData(response.data)
    setIsLoading(false)
  }

  return (
    <div className="popup-container">
      <h2>My Extension</h2>
      <p>{data || "No data yet"}</p>
      <button onClick={handleClick} disabled={isLoading}>
        {isLoading ? "Loading..." : "Fetch Data"}
      </button>
    </div>
  )
}

export default IndexPopup

// Metadata
export const config = {
  matches: ["<all_urls>"]
}
```

## 3. Background Service Worker (background/index.ts)

```typescript
import type { PlasmoMessaging } from "@plasmohq/messaging"

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("Extension installed!")
    // Set default values
    chrome.storage.local.set({ 
      enabled: true,
      theme: "light" 
    })
  }
})

// Listen for messages from content scripts/popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "FETCH_DATA") {
    fetch("https://api.example.com/data")
      .then(response => response.json())
      .then(data => {
        sendResponse({ success: true, data })
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message })
      })
    
    return true // Keep message channel open for async response
  }
})

// Context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "saveSelection",
    title: "Save Selection",
    contexts: ["selection"]
  })
})

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "saveSelection") {
    const selectedText = info.selectionText
    chrome.storage.local.set({ savedText: selectedText })
  }
})

// Alarm/Timer
chrome.alarms.create("dataSync", { periodInMinutes: 30 })

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "dataSync") {
    console.log("Syncing data...")
    // Perform background sync
  }
})
```

## 4. Content Script (contents/overlay.tsx)

```typescript
import type { PlasmoCSConfig } from "plasmo"
import { useState, useEffect } from "react"
import { sendToBackground } from "@plasmohq/messaging"

// Configure which sites this content script runs on
export const config: PlasmoCSConfig = {
  matches: ["https://www.example.com/*"],
  all_frames: false
}

// Mount component into page
export const getStyle = () => {
  const style = document.createElement("style")
  style.textContent = `
    .plasmo-overlay {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 999999;
      background: white;
      padding: 16px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
  `
  return style
}

const PlasmoOverlay = () => {
  const [isVisible, setIsVisible] = useState(true)
  const [pageData, setPageData] = useState({
    title: "",
    url: ""
  })

  useEffect(() => {
    setPageData({
      title: document.title,
      url: window.location.href
    })

    // Listen for messages from background
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.type === "TOGGLE_OVERLAY") {
        setIsVisible(request.visible)
        sendResponse({ success: true })
      }
    })
  }, [])

  const handleSave = async () => {
    const response = await sendToBackground({
      name: "save-page",
      body: {
        title: pageData.title,
        url: pageData.url
      }
    })
    
    console.log("Saved:", response)
  }

  if (!isVisible) return null

  return (
    <div className="plasmo-overlay">
      <h3>{pageData.title}</h3>
      <p>{pageData.url}</p>
      <button onClick={handleSave}>Save Page</button>
      <button onClick={() => setIsVisible(false)}>Close</button>
    </div>
  )
}

export default PlasmoOverlay
```

## 5. Messaging Pattern (background/messages/ping.ts)

```typescript
import type { PlasmoMessaging } from "@plasmohq/messaging"

// Message handler in background script
const handler: PlasmoMessaging.MessageHandler = async (req, res) => {
  const { name, body } = req
  
  console.log("Received message:", name, body)
  
  try {
    // Perform some operation
    const result = await performOperation(body)
    
    res.send({
      success: true,
      data: result
    })
  } catch (error) {
    res.send({
      success: false,
      error: error.message
    })
  }
}

export default handler

async function performOperation(data: any) {
  // Your logic here
  return { processed: true, ...data }
}
```

## 6. Storage Management

```typescript
import { Storage } from "@plasmohq/storage"

const storage = new Storage()

// Set value
await storage.set("key", "value")
await storage.set("user", { id: 1, name: "Alice" })

// Get value
const value = await storage.get("key")
const user = await storage.get("user")

// Remove value
await storage.remove("key")

// Watch for changes
storage.watch({
  "user": (change) => {
    console.log("User changed:", change.newValue)
  }
})

// Storage area selection (local, sync, session)
const syncStorage = new Storage({ area: "sync" })
await syncStorage.set("syncedKey", "syncedValue")
```

## 7. Options Page (options.tsx)

```typescript
import { useState, useEffect } from "react"
import { Storage } from "@plasmohq/storage"

function OptionsPage() {
  const [settings, setSettings] = useState({
    enabled: true,
    apiKey: "",
    theme: "light",
    autoSync: false
  })

  const storage = new Storage()

  useEffect(() => {
    // Load settings
    storage.get("settings").then((saved) => {
      if (saved) {
        setSettings(saved)
      }
    })
  }, [])

  const handleSave = async () => {
    await storage.set("settings", settings)
    alert("Settings saved!")
  }

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="options-container">
      <h1>Extension Settings</h1>
      
      <div className="setting-group">
        <label>
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => handleChange("enabled", e.target.checked)}
          />
          Enable Extension
        </label>
      </div>

      <div className="setting-group">
        <label>
          API Key:
          <input
            type="password"
            value={settings.apiKey}
            onChange={(e) => handleChange("apiKey", e.target.value)}
          />
        </label>
      </div>

      <div className="setting-group">
        <label>
          Theme:
          <select
            value={settings.theme}
            onChange={(e) => handleChange("theme", e.target.value)}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="auto">Auto</option>
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label>
          <input
            type="checkbox"
            checked={settings.autoSync}
            onChange={(e) => handleChange("autoSync", e.target.checked)}
          />
          Auto Sync
        </label>
      </div>

      <button onClick={handleSave}>Save Settings</button>
    </div>
  )
}

export default OptionsPage
```

## 8. Tabs API Usage (tabs/settings.tsx)

```typescript
import { useState, useEffect } from "react"

function SettingsTab() {
  const [tabs, setTabs] = useState([])

  useEffect(() => {
    loadTabs()
  }, [])

  const loadTabs = async () => {
    const allTabs = await chrome.tabs.query({})
    setTabs(allTabs)
  }

  const openNewTab = async () => {
    await chrome.tabs.create({
      url: "https://example.com",
      active: true
    })
  }

  const closeTab = async (tabId: number) => {
    await chrome.tabs.remove(tabId)
    loadTabs()
  }

  const executeScript = async (tabId: number) => {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        alert("Hello from extension!")
      }
    })
  }

  return (
    <div>
      <h2>Tab Manager</h2>
      <button onClick={openNewTab}>Open New Tab</button>
      
      <ul>
        {tabs.map((tab) => (
          <li key={tab.id}>
            {tab.title}
            <button onClick={() => executeScript(tab.id)}>
              Run Script
            </button>
            <button onClick={() => closeTab(tab.id)}>
              Close
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default SettingsTab
```

## 9. Web Accessible Resources

```typescript
// contents/widget.tsx
import type { PlasmoCSConfig } from "plasmo"

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  css: ["widget.css"]
}

// Inject custom elements
const Widget = () => {
  const imageUrl = chrome.runtime.getURL("assets/icon.png")
  
  return (
    <div className="extension-widget">
      <img src={imageUrl} alt="Extension icon" />
      <h3>Widget Content</h3>
    </div>
  )
}

export default Widget
```

## 10. API Integration

```typescript
// lib/api.ts
export class ExtensionAPI {
  private baseUrl: string
  private apiKey: string

  constructor() {
    // Load from storage
    this.init()
  }

  private async init() {
    const storage = new Storage()
    this.apiKey = await storage.get("apiKey")
    this.baseUrl = "https://api.example.com"
  }

  async fetchData(endpoint: string) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json"
      }
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  }

  async postData(endpoint: string, data: any) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    return await response.json()
  }
}

// Usage in popup or content script
const api = new ExtensionAPI()
const data = await api.fetchData("/users")
```

## 11. Permissions in package.json

```json
{
  "manifest": {
    "host_permissions": [
      "https://*/*"
    ],
    "permissions": [
      "storage",
      "tabs",
      "activeTab",
      "scripting",
      "alarms",
      "contextMenus"
    ]
  }
}
```

## 12. Environment Variables

```typescript
// .env.local
PLASMO_PUBLIC_API_KEY=your_api_key
PLASMO_PUBLIC_API_URL=https://api.example.com

// Usage in code
const apiKey = process.env.PLASMO_PUBLIC_API_KEY
const apiUrl = process.env.PLASMO_PUBLIC_API_URL
```

## 13. Tailwind CSS Integration

```typescript
// popup.tsx
import "~base.css"

function Popup() {
  return (
    <div className="flex flex-col items-center justify-center p-4 bg-white rounded-lg shadow-lg">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">
        My Extension
      </h1>
      <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        Click Me
      </button>
    </div>
  )
}

export default Popup
```

## 14. Testing

```typescript
// tests/popup.test.tsx
import { render, screen, fireEvent } from "@testing-library/react"
import Popup from "~popup"

// Mock chrome API
global.chrome = {
  storage: {
    local: {
      get: jest.fn(),
      set: jest.fn()
    }
  },
  runtime: {
    sendMessage: jest.fn()
  }
} as any

describe("Popup", () => {
  it("renders correctly", () => {
    render(<Popup />)
    expect(screen.getByText("My Extension")).toBeInTheDocument()
  })

  it("handles button click", async () => {
    render(<Popup />)
    const button = screen.getByText("Fetch Data")
    fireEvent.click(button)
    
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
      type: "FETCH_DATA"
    })
  })
})
```

## 15. Build Configuration

```typescript
// package.json
{
  "name": "my-extension",
  "version": "1.0.0",
  "scripts": {
    "dev": "plasmo dev",
    "build": "plasmo build",
    "build:firefox": "plasmo build --target=firefox-mv2",
    "package": "plasmo build --zip"
  },
  "dependencies": {
    "@plasmohq/messaging": "^0.6.0",
    "@plasmohq/storage": "^1.8.0",
    "plasmo": "^0.84.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/chrome": "^0.0.246",
    "@types/node": "^20.8.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0"
  }
}
```

## Best Practices

1. **Use TypeScript**: Plasmo has excellent TypeScript support
2. **Message Passing**: Use `@plasmohq/messaging` for background communication
3. **Storage API**: Use `@plasmohq/storage` for cross-browser storage
4. **Content Security**: Be mindful of CSP restrictions
5. **Permissions**: Request only necessary permissions
6. **Performance**: Minimize content script impact on page load
7. **Error Handling**: Always handle async operations and API errors
8. **Testing**: Write tests for critical functionality
9. **Icons**: Provide multiple icon sizes (16, 48, 128px)
10. **Documentation**: Document your extension's features

## Common Patterns

### Inject into Specific Elements
```typescript
import type { PlasmoCSConfig, PlasmoGetInlineAnchor } from "plasmo"

export const config: PlasmoCSConfig = {
  matches: ["https://github.com/*"]
}

export const getInlineAnchor: PlasmoGetInlineAnchor = async () => {
  return document.querySelector("#repository-container-header")
}

const GitHubWidget = () => {
  return <div>Custom GitHub Widget</div>
}

export default GitHubWidget
```

### Side Panel
```typescript
// sidepanel.tsx
import { useState } from "react"

function SidePanel() {
  const [content, setContent] = useState("")

  return (
    <div className="side-panel">
      <h2>Side Panel</h2>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Take notes..."
      />
    </div>
  )
}

export default SidePanel
```

### Badge Updates
```typescript
// background.ts
chrome.action.setBadgeText({ text: "5" })
chrome.action.setBadgeBackgroundColor({ color: "#FF0000" })

// Update based on data
async function updateBadge() {
  const count = await getUnreadCount()
  chrome.action.setBadgeText({ 
    text: count > 0 ? count.toString() : "" 
  })
}
```

## Debugging Tips

```typescript
// Log to extension console
console.log("Popup:", data)

// Log from content script (appears in page console)
console.log("Content Script:", window.location.href)

// Debug messages
chrome.runtime.onMessage.addListener((msg) => {
  console.log("Message received:", msg)
})

// Check storage
chrome.storage.local.get(null, (items) => {
  console.log("All storage:", items)
})
```

## Performance Optimization

```typescript
// Lazy load components
import { lazy, Suspense } from "react"

const HeavyComponent = lazy(() => import("./HeavyComponent"))

function Popup() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  )
}

// Debounce expensive operations
function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout
  return (...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// Use in content script
const handleScroll = debounce(() => {
  console.log("Scrolled!")
}, 300)

window.addEventListener("scroll", handleScroll)
```

Remember: Browser extensions should be lightweight, secure, and respectful of user privacy. Always minimize permissions and resource usage!
