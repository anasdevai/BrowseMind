# BrowserMind - User Installation Guide

**Control your browser with AI in 3 simple steps!**

---

## What You Need

- **Google Chrome** browser
- **Python 3.11+** ([Download here](https://www.python.org/downloads/))
- **OpenRouter API Key** - Free! ([Get it here](https://openrouter.ai/))

---

## 🚀 Installation (3 Simple Steps)

### Step 1: Download & Extract

1. **Download the ZIP file:**
   - Go to https://github.com/anasdevai/BrowseMind
   - Click the green **"Code"** button
   - Click **"Download ZIP"**

2. **Extract the ZIP:**
   - Right-click the downloaded file
   - Select "Extract All..."
   - Choose a location (like Desktop or Documents)
   - Click "Extract"

---

### Step 2: Set Your API Key & Start Backend

1. **Open the backend folder:**
   - Navigate to the extracted BrowseMind folder
   - Open the `backend` folder
   - Find the file named `.env`

2. **Add your OpenRouter API key:**
   - Right-click `.env` and open with Notepad (Windows) or TextEdit (Mac)
   - Find this line:
     ```
     OPENROUTER_API_KEY=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
     ```
   - Replace the key with YOUR OpenRouter API key
   - Save and close the file

3. **Start the backend server:**
   
   **Windows:**
   - Double-click `start.bat` in the backend folder
   - A black window will open showing "BrowserMind backend ready"
   - Keep this window open while using BrowserMind

   **Mac/Linux:**
   - Open Terminal
   - Navigate to the backend folder:
     ```bash
     cd /path/to/BrowseMind/backend
     ```
   - Run:
     ```bash
     chmod +x start.sh
     ./start.sh
     ```
   - Keep Terminal open while using BrowserMind

---

### Step 3: Install Chrome Extension

1. **Open Chrome Extensions page:**
   - Open Google Chrome
   - Type `chrome://extensions/` in the address bar
   - Press Enter

2. **Enable Developer Mode:**
   - Look at the top-right corner
   - Toggle ON the "Developer mode" switch

3. **Load BrowserMind extension:**
   - Click the **"Load unpacked"** button (top-left)
   - Navigate to your BrowseMind folder
   - Go to: `extension` → `build` → `chrome-mv3-prod`
   - Click **"Select Folder"**

4. **Pin the extension (recommended):**
   - Click the puzzle icon 🧩 in Chrome toolbar
   - Find "BrowserMind"
   - Click the pin 📌 icon next to it

**✅ Installation Complete!**

---

## 🎯 How to Use BrowserMind

### Opening the Side Chat

1. Click the **BrowserMind icon** in your Chrome toolbar
2. A sidebar will open on the right side of your browser
3. You'll see a chat interface - this is where you control your browser!

---

### Giving Instructions

Simply type what you want the browser to do in natural language. BrowserMind will perform actions on your **current tab**.

#### Example Commands:

**Navigate to websites:**
```
Go to youtube.com
Open github.com
Navigate to amazon.com
```

**Click elements:**
```
Click the sign in button
Click the first search result
Click on the menu icon
```

**Type text:**
```
Type "AI news" in the search box
Fill the email field with test@example.com
Enter "hello world" in the text area
```

**Extract information:**
```
Get all links on this page
Extract the article text
Show me all product prices
What's the main heading?
```

**Scroll and navigate:**
```
Scroll down
Scroll to the bottom
Go back
Refresh the page
```

**Complex tasks:**
```
Search for "machine learning" on Google and open the first result
Find all email addresses on this page
Take a screenshot of this section
Extract all the data from the table
```

---

### Real-World Usage Example

Let's say you want to research AI news:

1. **Open BrowserMind sidebar** (click the icon)

2. **Type in chat:**
   ```
   Go to news.google.com
   ```
   ✅ BrowserMind navigates to Google News

3. **Type in chat:**
   ```
   Search for "artificial intelligence"
   ```
   ✅ BrowserMind types in search box and searches

4. **Type in chat:**
   ```
   Extract the titles of the first 5 articles
   ```
   ✅ BrowserMind extracts and shows you the titles

5. **Type in chat:**
   ```
   Click on the first article
   ```
   ✅ BrowserMind opens the article

6. **Type in chat:**
   ```
   Summarize this article
   ```
   ✅ BrowserMind reads and summarizes the content

---

## 🤖 Creating Sub-Agents

Sub-agents are specialized AI assistants you create for specific tasks. They work alongside the main agent.

### How to Create a Sub-Agent

In the BrowserMind chat, use the `/sub_agents create` command:

```
/sub_agents create name="DataExtractor" role="Extract product information from shopping sites" tools=["extract_text", "extract_links", "extract_tables"] permissions=["read_dom"]
```

### Sub-Agent Examples

**1. Research Assistant:**
```
/sub_agents create name="ResearchBot" role="Gather and summarize information from multiple sources" tools=["navigate", "extract_text", "extract_links"] permissions=["read_dom", "navigate"]
```

**Use it:**
```
ResearchBot, find information about climate change from 3 different sources
```

---

**2. Shopping Helper:**
```
/sub_agents create name="ShoppingBot" role="Compare prices and extract product details" tools=["extract_text", "extract_tables", "screenshot"] permissions=["read_dom"]
```

**Use it:**
```
ShoppingBot, compare prices of wireless headphones on this page
```

---

**3. Form Filler:**
```
/sub_agents create name="FormBot" role="Fill out web forms automatically" tools=["type_text", "click_element"] permissions=["interact"]
```

**Use it:**
```
FormBot, fill out this contact form with my details
```

---

**4. Data Scraper:**
```
/sub_agents create name="ScraperBot" role="Extract structured data from web pages" tools=["extract_text", "extract_links", "extract_tables", "get_dom"] permissions=["read_dom"]
```

**Use it:**
```
ScraperBot, extract all job listings from this page into a table
```

---

### Sub-Agent Command Format

```
/sub_agents create name="[AgentName]" role="[What it does]" tools=["tool1", "tool2"] permissions=["permission1"]
```

**Available Tools:**
- `navigate` - Go to URLs
- `click_element` - Click buttons/links
- `type_text` - Type into fields
- `scroll` - Scroll the page
- `screenshot` - Take screenshots
- `extract_text` - Get text content
- `extract_links` - Get all links
- `extract_tables` - Get table data
- `get_dom` - Get page structure
- `highlight_element` - Highlight elements

**Available Permissions:**
- `read_dom` - Read page content
- `navigate` - Navigate to URLs
- `interact` - Click and type
- `extract` - Extract data

---

## 💡 Tips for Best Results

1. **Be specific:** "Click the blue submit button" is better than "click button"
2. **One task at a time:** Let each command complete before the next
3. **Describe what you see:** "The search box at the top" helps the AI find it
4. **Use sub-agents for repetitive tasks:** Create specialized agents for tasks you do often

---

## 🔧 Troubleshooting

### Extension Not Working?

**Check if backend is running:**
- Look for the black window (Windows) or Terminal (Mac/Linux)
- It should say "BrowserMind backend ready on 0.0.0.0:8000"
- If closed, run `start.bat` (Windows) or `./start.sh` (Mac/Linux) again

**Reload the extension:**
1. Go to `chrome://extensions/`
2. Find BrowserMind
3. Click the refresh icon 🔄

**Check connection:**
- Open BrowserMind sidebar
- Look for "Connected" status at the bottom
- If "Disconnected", restart the backend

---

### Commands Not Working?

**Make sure:**
- The backend server is running
- You're on the tab you want to control
- The page has finished loading
- Your command is clear and specific

**Try:**
- Refresh the webpage
- Close and reopen the sidebar
- Restart the backend server

---

### API Key Issues?

**"Invalid API key" error:**
1. Go to https://openrouter.ai/
2. Sign up/login
3. Get your API key
4. Open `backend/.env` file
5. Replace the key after `OPENROUTER_API_KEY=`
6. Save the file
7. Restart the backend (close and run `start.bat` again)

---

## 🎓 Advanced Usage Examples

### Automated Research Workflow

```
1. Go to scholar.google.com
2. Search for "quantum computing 2024"
3. Extract titles and authors of first 10 papers
4. Open the first paper
5. Summarize the abstract
```

### E-commerce Price Comparison

```
1. Go to amazon.com
2. Search for "laptop"
3. Extract all product names and prices
4. Show me the 5 cheapest options
```

### Social Media Monitoring

```
1. Go to twitter.com
2. Search for #AI
3. Extract the top 10 tweets
4. Summarize the main topics
```

### Job Application Helper

```
Create sub-agent:
/sub_agents create name="JobBot" role="Help with job applications" tools=["navigate", "extract_text", "type_text", "click_element"] permissions=["read_dom", "navigate", "interact"]

Then use:
JobBot, go to linkedin.com/jobs and find software engineer positions in San Francisco
```

---

## ❓ FAQ

**Q: Do I need to keep the backend window open?**
A: Yes! The black window (or Terminal) must stay open while using BrowserMind.

**Q: Can I use it on multiple tabs?**
A: Yes! BrowserMind works on whichever tab is currently active.

**Q: Is my browsing data safe?**
A: Yes! Everything runs locally on your computer. Only your commands are sent to OpenRouter for AI processing.

**Q: How much does OpenRouter cost?**
A: Very cheap! Usually less than $1/month for normal use. They often have free tiers too.

**Q: Can I close the sidebar?**
A: Yes! Click the X or click outside. Click the BrowserMind icon to open it again.

**Q: Do sub-agents save between sessions?**
A: Yes! Once created, sub-agents are saved in the database.

---

## 🎉 You're Ready!

Start with a simple command:

```
Go to github.com and show me trending repositories
```

Then try creating your first sub-agent for a task you do often!

**Enjoy your AI-powered browser! 🚀**

---

## 📞 Need Help?

- **Issues:** https://github.com/anasdevai/BrowseMind/issues
- **Discussions:** https://github.com/anasdevai/BrowseMind/discussions

Share your cool sub-agents and workflows with the community!
