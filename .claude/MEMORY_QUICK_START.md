# MCP Memory Quick Start Guide

## ✅ What You Have

I've created a **working MCP memory server** for Claude Code that:
- ✅ Stores facts, entities, and relationships persistently
- ✅ Works with SQLite (no external dependencies)
- ✅ Tested and verified working
- ✅ Located at `.claude/mcp_memory_server.py`

**Database**: `.claude/memory.db` (created automatically)

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Find Your Claude Code Config File

**Location by OS:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 2: Add This Configuration

If the file doesn't exist, create it. If it exists, add the `mcpServers` section:

```json
{
  "mcpServers": {
    "course-creator-memory": {
      "command": "python3",
      "args": [
        "/home/bbrelin/course-creator/.claude/mcp_memory_server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/bbrelin/course-creator"
      }
    }
  }
}
```

**Important**: Replace `/home/bbrelin/course-creator` with the actual full path if different.

### Step 3: Restart Claude Code

Completely quit and restart Claude Code (not just close the window).

---

## ✅ Verify It's Working

After restart, ask Claude Code:

```
Remember that the Course Creator Platform uses pytest for all testing
```

Then in a new conversation:

```
What testing framework does this project use?
```

If Claude recalls "pytest", memory is working! 🎉

---

## 📋 Alternative: Use Official MCP Memory

If you prefer the official Anthropic memory server:

```bash
# Install
npm install -g @modelcontextprotocol/server-memory

# Configure claude_desktop_config.json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}

# Restart Claude Code
```

---

## 🧪 Test the Server Directly (CLI)

You can test the memory server from command line:

```bash
cd /home/bbrelin/course-creator

# Remember a fact
python .claude/mcp_memory_server.py remember "Platform uses 13 microservices" infrastructure high

# Recall facts
python .claude/mcp_memory_server.py recall "microservices"

# Create entity
python .claude/mcp_memory_server.py entity "PostgreSQL" "system" "Primary database"

# Cache a file
python .claude/mcp_memory_server.py cache services/user-management/main.py

# Get cached file
python .claude/mcp_memory_server.py get-cache services/user-management/main.py

# View cache stats
python .claude/mcp_memory_server.py cache-stats

# View all stats
python .claude/mcp_memory_server.py stats
```

---

## 🎯 What Claude Code Can Remember

Once configured, Claude Code will be able to:

### Project Information
- "Remember that services directory has 13 microservices"
- "Remember that we use PostgreSQL for persistence"
- "Remember that tests are in the tests/ directory"

### User Preferences
- "Remember that I prefer pytest over unittest"
- "Remember that I like detailed commit messages"

### Architecture Decisions
- "Remember that we use FastAPI for all services"
- "Remember that authentication uses JWT tokens"

### Problem Solutions
- "Remember that container issues are fixed with docker-compose down -v"
- "Remember that import errors need absolute imports, not relative"

### Test Results
- "Remember that all 109 user management tests are passing"
- "Remember that we fixed mock datetime comparison errors"

### File Caching (NEW)
- "Cache the main.py file for faster access"
- "Get the cached version of user.py"
- "Show me cache statistics"
- Files are automatically re-cached if they change on disk
- Cache tracks access counts and last access times

---

## 🔍 Checking If MCP is Active

### Method 1: Look for MCP Tools
After configuring and restarting, MCP tools will be available. They'll have names starting with `mcp__`.

### Method 2: Check Claude Code Logs
- **macOS/Linux**: `~/Library/Logs/Claude/mcp-*.log`
- **Windows**: `%APPDATA%\Claude\logs\`

Look for messages about the memory server starting.

### Method 3: Test Memory Operations
Just ask Claude Code to remember something, then recall it in a new conversation.

---

## ⚠️ Troubleshooting

### "Command not found" or "Permission denied"

```bash
chmod +x /home/bbrelin/course-creator/.claude/mcp_memory_server.py
```

### Python version issues

Make sure you're using `python3` in the config:
```json
"command": "python3"
```

### Config file syntax error

Validate your JSON at https://jsonlint.com/

### Server not starting

Check Claude Code logs for error messages.

---

## 📚 Full Documentation

For complete details, see:
- **Setup Guide**: `.claude/MCP_MEMORY_SETUP.md`
- **Server Code**: `.claude/mcp_memory_server.py`
- **CLAUDE.md Reference**: `claude.md/03-memory-system.md`

---

## 🎉 Benefits of MCP Memory

### For You:
- ✅ Claude Code remembers context between sessions
- ✅ No need to re-explain project structure every time
- ✅ Claude learns from past conversations
- ✅ Better, more consistent code suggestions

### For Development:
- ✅ Faster development (less context repetition)
- ✅ Better architecture understanding over time
- ✅ Accumulated troubleshooting knowledge
- ✅ Personalized to your preferences

---

## Next Steps

1. ✅ **Configure** Claude Code with MCP memory (see Step 1-3 above)
2. ✅ **Restart** Claude Code completely
3. ✅ **Test** with a simple remember/recall operation
4. ✅ **Use** - Start having Claude Code remember important facts

The memory will persist in `.claude/memory.db` and work across all Claude Code sessions!
