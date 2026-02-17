# BrowserMind - Quick Start Guide

**Get started in 3 minutes!**

---

## Step 1: Download ZIP File

1. Go to: **https://github.com/anasdevai/BrowseMind**
2. Click green **"Code"** button
3. Click **"Download ZIP"**
4. Extract the ZIP file to your Desktop

---

## Step 2: Set API Key & Start Backend

### Get Your Free API Key:
1. Go to: **https://openrouter.ai/**
2. Sign up (free)
3. Copy your API key (starts with `sk-or-v1-...`)

### Add API Key:
1. Open the `BrowseMind` folder
2. Go to `backend` folder
3. Open `.env` file with Notepad
4. Find line: `OPENROUTER_API_KEY=...`
5. Replace with YOUR key
6. Save and close

### Start Backend:
- **Windows:** Double-click `start.bat` in backend folder
- **Mac/Linux:** Open Terminal, run `./start.sh` in backend folder
- Keep the window open!

---

## Step 3: Install Extension in Chrome

1. Open Chrome
2. Go to: `chrome://extensions/`
3. Turn ON "Developer mode" (top-right)
4. Click "Load unpacked"
5. Select: `BrowseMind/extension/build/chrome-mv3-prod`
6. Done! Click the BrowserMind icon 🧩

---

## How to Use

### Open Side Chat:
Click the **BrowserMind icon** in Chrome toolbar → Sidebar opens

### Give Commands:
Type what you want in the chat:

```
Go to youtube.com
```
```
Click the search button
```
```
Extract all links from this page
```

The agent performs actions on your **current tab**!

---

## Create Sub-Agents

Type in chat:
```
/sub_agents create name="ShoppingBot" role="Compare prices" tools=["extract_text", "extract_tables"] permissions=["read_dom"]
```

Then use it:
```
ShoppingBot, find the cheapest laptop on this page
```

---

## Examples

### Research Assistant:
```
/sub_agents create name="ResearchBot" role="Gather information from multiple sources" tools=["navigate", "extract_text", "extract_links"] permissions=["read_dom", "navigate"]
```

### Data Scraper:
```
/sub_agents create name="ScraperBot" role="Extract structured data" tools=["extract_text", "extract_tables", "get_dom"] permissions=["read_dom"]
```

### Form Filler:
```
/sub_agents create name="FormBot" role="Fill web forms" tools=["type_text", "click_element"] permissions=["interact"]
```

---

## Troubleshooting

**Extension not working?**
- Make sure backend window is still open
- Restart backend: close window, run `start.bat` again

**Commands not working?**
- Check if "Connected" shows in sidebar
- Refresh the webpage
- Reload extension at `chrome://extensions/`

**API key error?**
- Check `.env` file has correct key
- Restart backend after changing key

---

## That's It!

Start with:
```
Go to github.com and show me trending repositories
```

**Enjoy! 🚀**
