# MCP Memory Setup for Claude Code

## What is MCP Memory?

MCP (Model Context Protocol) memory provides persistent memory capabilities for Claude Code, allowing it to remember facts, entities, relationships, and context across sessions.

---

## Setup Instructions

### Option 1: Official Anthropic Memory Server (Recommended)

**Easiest setup with official support**

1. **Install the MCP memory server**:
   ```bash
   npm install -g @modelcontextprotocol/server-memory
   ```

2. **Configure Claude Code**:

   Find your Claude Code config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

   Add this configuration:
   ```json
   {
     "mcpServers": {
       "memory": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-memory"
         ]
       }
     }
   }
   ```

3. **Restart Claude Code**

4. **Test it**:
   The memory tools should now be available. You can ask Claude Code to:
   - "Remember that this project uses pytest for testing"
   - "What do you remember about testing?"
   - "Create an entity for the Course Creator Platform"

---

### Option 2: SQLite MCP Server (More Control)

**Best for persistent, queryable memory**

1. **Install SQLite MCP server**:
   ```bash
   npm install -g @modelcontextprotocol/server-sqlite
   ```

2. **Configure Claude Code**:
   ```json
   {
     "mcpServers": {
       "sqlite-memory": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-sqlite",
           "--db-path",
           "/home/bbrelin/course-creator/.claude/memory.db"
         ]
       }
     }
   }
   ```

3. **Restart Claude Code**

---

### Option 3: Custom Python Memory Server (Full Control)

**Best for custom functionality specific to this project**

1. **Make the server executable**:
   ```bash
   chmod +x /home/bbrelin/course-creator/.claude/mcp_memory_server.py
   ```

2. **Test the server**:
   ```bash
   cd /home/bbrelin/course-creator
   python .claude/mcp_memory_server.py remember "Testing memory system" testing high
   python .claude/mcp_memory_server.py recall "memory"
   python .claude/mcp_memory_server.py stats
   ```

3. **Configure Claude Code**:
   ```json
   {
     "mcpServers": {
       "course-creator-memory": {
         "command": "python",
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

4. **Restart Claude Code**

---

## Available Memory Operations

Once configured, Claude Code can use these operations:

### Basic Operations
- **Remember facts**: "Remember that the platform uses 9 microservices on ports 8000-8010"
- **Recall information**: "What do you remember about microservices?"
- **Store user preferences**: "Remember that I prefer pytest for testing"

### Entity Management
- **Track entities**: "Create an entity for PostgreSQL Database as a system"
- **Get entities**: "Show me all system entities"
- **Connect entities**: "Connect Course Creator Platform to PostgreSQL Database with relationship 'uses'"

### Context Management
- **Start context**: "Start a new context called 'Database Migration'"
- **Get statistics**: "Show me memory statistics"

---

## Verifying MCP Memory is Working

### Check 1: Look for MCP Tools
After restarting Claude Code, you should see MCP tools available. The tools will have names like:
- `mcp__memory__remember`
- `mcp__memory__recall`
- `mcp__sqlite__query`

### Check 2: Test Memory Operations
Ask Claude Code:
```
Remember that this is the Course Creator Platform with 9 microservices
```

Then in a new conversation:
```
What do you remember about this platform?
```

If memory is working, Claude will recall the information.

### Check 3: Check Server Logs
If using the custom Python server, you can add logging to see if it's being called.

---

## Troubleshooting

### Issue: MCP server not starting

**Check Claude Code logs**:
- **macOS/Linux**: `~/Library/Logs/Claude/`
- **Windows**: `%APPDATA%\Claude\logs\`

Look for MCP server errors.

### Issue: Tools not appearing

1. Verify configuration file syntax (must be valid JSON)
2. Restart Claude Code completely (quit and reopen)
3. Check that the MCP server command is in your PATH

### Issue: Permission denied (Linux/macOS)

```bash
chmod +x /home/bbrelin/course-creator/.claude/mcp_memory_server.py
```

### Issue: Python module not found

Make sure Python 3 is installed and accessible:
```bash
which python3
python3 --version
```

---

## Custom Memory Server Features

The custom Python server (`mcp_memory_server.py`) provides:

### Tables:
- **facts** - Store key information with categories and importance levels
- **entities** - Track systems, people, files, concepts
- **relationships** - Connect entities together
- **contexts** - Manage conversation contexts

### Database Location:
- Default: `.claude/memory.db`
- SQLite database, can be queried with any SQLite tool

### CLI Commands:
```bash
# Remember a fact
python .claude/mcp_memory_server.py remember "Fact content" category importance

# Recall facts
python .claude/mcp_memory_server.py recall "search query"

# Create entity
python .claude/mcp_memory_server.py entity "Entity Name" "type" "description"

# View statistics
python .claude/mcp_memory_server.py stats
```

---

## Memory Best Practices

### For Claude Code to Remember:
1. **Project structure** - Remember key directories and their purposes
2. **Architecture decisions** - Why certain patterns were chosen
3. **Common issues** - Problems and their solutions
4. **User preferences** - Testing frameworks, code style, etc.
5. **Entity relationships** - How services interact

### Categories to Use:
- `infrastructure` - Servers, databases, deployment
- `testing` - Test patterns, frameworks
- `user_preferences` - User choices and preferences
- `architecture` - System design decisions
- `troubleshooting` - Problem solutions
- `database` - Database schema, migrations
- `api` - API endpoints, contracts

### Importance Levels:
- `critical` - Essential information, always recall first
- `high` - Important information
- `medium` - Useful information (default)
- `low` - Nice to have information

---

## Example Memory Usage

```python
# Claude Code will use memory like this:

# Remember project structure
"Remember that services directory contains 9 microservices: user-management,
course-management, course-generator, lab-manager, analytics, organization-management,
content-management, rag-service, demo-service" - category: infrastructure, importance: high

# Remember architecture
"Remember that the platform uses PostgreSQL for persistence and ChromaDB for vector
storage in the RAG service" - category: architecture, importance: high

# Remember user preferences
"Remember that user prefers pytest over unittest for testing"
- category: user_preferences, importance: medium

# Remember troubleshooting
"Remember that container startup failures can be fixed by removing old containers
with docker-compose down -v and rebuilding" - category: troubleshooting, importance: high
```

---

## Next Steps

1. **Choose and configure** one of the three options above
2. **Restart Claude Code**
3. **Test memory** with simple remember/recall operations
4. **Start using** - Claude Code will automatically use memory for continuity

The memory system will help Claude Code maintain context across sessions and provide
better, more consistent assistance for your Course Creator Platform development.
