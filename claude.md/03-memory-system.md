# Memory System

## Claude Code Memory System (v2.5 - MANDATORY USAGE)

**CRITICAL**: Claude Code now has access to a comprehensive persistent memory system that MUST be used to maintain context, store important information, and provide continuity across conversations.

## Memory System Overview

The memory system provides Claude Code with:
- **Persistent storage** of facts, entities, and relationships across sessions
- **Context continuity** - remember previous conversations and decisions
- **Knowledge accumulation** - build understanding of the codebase over time
- **Entity tracking** - maintain information about users, systems, files, and concepts
- **Relationship mapping** - understand connections between different components
- **Search capabilities** - quickly recall relevant information from past interactions

## Mandatory Memory Usage Requirements

**WHEN TO USE MEMORY (Required)**:

1. **Every significant interaction** - Store key facts from each conversation
2. **User preferences** - Remember user choices, preferences, and requirements
3. **System discoveries** - Store information learned about the codebase
4. **Problem solutions** - Remember fixes, workarounds, and troubleshooting steps
5. **Entity relationships** - Track connections between users, systems, files, projects
6. **Context preservation** - Maintain conversation context across sessions

## Memory System Location and Files

**Configuration**: `config/memory/claude_memory.yaml` - Hydra-based configuration with environment-aware settings  
**Manager Class**: `shared/memory/claude_memory_manager.py` - Core memory management with Hydra integration  
**Helper Functions**: `shared/memory/claude_memory_helpers.py` - Simplified interface for Claude Code  
**Schema**: `shared/memory/claude_memory_schema.sql` - SQLite database schema  
**Tests**: `shared/memory/tests/test_memory_system.py` - Comprehensive test suite  
**Database Location**: Configurable via Hydra (default: `shared/memory/claude_memory.db`)

## Memory System Usage Patterns

### Simple Memory Operations (Use These Frequently)

```python
# Import helper functions (Hydra configuration automatic)
import sys
sys.path.append('shared/memory')
import claude_memory_helpers as memory

# Remember key information
memory.remember("User prefers dark mode interface", category="user_preferences", importance="medium")
memory.remember("Docker containers use ports 8000-8008", category="infrastructure", importance="high")

# Recall information
results = memory.recall("docker ports")
print(results)

# Remember user-specific information
memory.remember_user_preference("ui_theme", "dark")
memory.remember_system_info("Course Creator Platform", "Uses microservices architecture with 8 services")

# Remember troubleshooting solutions
memory.remember_error_solution("Container startup failure", "Remove old containers and rebuild with --no-cache")
```

### Hydra-Based Memory Initialization (For Services)

```python
# Explicit Hydra initialization for services that need configuration control
import sys
sys.path.append('shared/memory')
import claude_memory_helpers as memory

# Initialize with specific Hydra configuration
memory_manager = memory.init_memory_with_hydra(config_path="config", config_name="config")

# Use memory with custom configuration
memory.remember("Service-specific information", category="service_config", importance="high")

# Access configuration details
config = memory_manager.config
db_path = config.memory.database.db_path
performance_settings = config.memory.performance
```

### Entity and Relationship Management

```python
# Track entities (people, systems, concepts, files)
memory.note_entity("Course Creator Platform", "system", "Educational platform with microservices")
memory.note_entity("PostgreSQL Database", "system", "Primary database for all services")
memory.note_entity("User", "person", "Platform user working on course creation")

# Create relationships
memory.connect_entities("Course Creator Platform", "PostgreSQL Database", "uses", "Platform stores data in PostgreSQL")
memory.connect_entities("User", "Course Creator Platform", "uses", "User develops and maintains the platform")
```

### Context and Conversation Management

```python
# Start memory context for significant work sessions
memory.start_memory_context("Database Migration Project", "Migrating database schema for v2.5")

# Get current context
context_info = memory.get_memory_context()
print(context_info)

# View memory statistics
summary = memory.memory_summary()
print(summary)
```

## Integration with Claude Code Workflows

### Before Starting Work
**ALWAYS** check memory for relevant context:
```python
# Check for related information
results = memory.recall("database migration")
user_prefs = memory.get_user_preferences()
system_info = memory.get_system_info()
```

### During Work
**CONTINUOUSLY** store important findings:
```python
# Store discoveries
memory.remember("Migration script requires manual intervention for user table", 
                category="database", importance="critical")

# Track file relationships
memory.remember_file_info("/path/to/migration.sql", "Contains user table schema updates")
```

### After Completing Tasks
**ALWAYS** summarize and store results:
```python
# Store solutions and outcomes
memory.remember("Database migration completed successfully using manual intervention", 
                category="project_completion", importance="high")

# Update entity information
memory.note_entity("Database Schema", "concept", "Updated to v2.5 with enhanced user management")
```

## Memory System Help and Discovery

```python
# Get help on available functions
help_info = memory.memory_help()
print(help_info)

# View recent activity
recent = memory.recent_activity(days=7)
print(recent)

# Search by categories
db_facts = memory.search_facts_by_category("database")
system_entities = memory.search_by_type("system")
```

## Performance and Maintenance

The memory system is optimized for Claude Code usage:
- **Fast retrieval** - Indexed SQLite database with sub-second queries
- **Automatic cleanup** - Old data automatically archived
- **Backup support** - Regular backups ensure data preservation
- **Scalable design** - Handles thousands of facts and entities efficiently

## Memory System Benefits for Development

1. **Continuity** - Remember context across sessions and conversations
2. **Learning** - Build accumulated knowledge about the codebase
3. **Efficiency** - Avoid re-discovering the same information repeatedly
4. **Relationship Awareness** - Understand connections between system components
5. **Problem Prevention** - Remember past issues and their solutions
6. **User Personalization** - Adapt to user preferences and working patterns

## Memory Usage Examples in Development Context

### Example 1: Remembering User Preferences
```python
# During initial interaction
memory.remember_user_preference("testing_framework", "pytest")
memory.remember_user_preference("code_style", "black_formatting")

# Later in same or different session
user_prefs = memory.get_user_preferences()
# Use stored preferences to adapt behavior
```

### Example 2: System Architecture Knowledge
```python
# Store architecture information
memory.note_entity("User Management Service", "system", "Handles authentication on port 8000")
memory.note_entity("Course Generator Service", "system", "AI content generation on port 8001")
memory.connect_entities("User Management Service", "Course Generator Service", "authenticates_for", 
                       "User service provides auth for course generation")

# Later recall architecture
architecture_info = memory.search_by_type("system")
```

### Example 3: Troubleshooting Knowledge Base
```python
# Store troubleshooting solutions
memory.remember_error_solution("ModuleNotFoundError in Docker", 
                               "Use absolute imports instead of relative imports")
memory.remember_error_solution("Service startup timeout", 
                               "Check health endpoints and dependency order")

# Recall when similar issues arise
troubleshooting = memory.get_troubleshooting_info()
```

## Memory System Configuration (Hydra-Based)

The memory system now uses Hydra configuration for flexible, environment-aware setup:

### Configuration File Structure
```yaml
# config/memory/claude_memory.yaml
memory:
  database:
    db_path: ${oc.env:CLAUDE_MEMORY_DB_PATH,./claude_memory.db}
    schema_path: ${oc.env:CLAUDE_MEMORY_SCHEMA_PATH,./claude_memory_schema.sql}
    connection_params:
      journal_mode: "WAL"
      cache_size: 2000
      foreign_keys: true
  
  session:
    cleanup_after_hours: 24
    max_sessions: 100
    track_context: true
  
  performance:
    enable_caching: true
    cache_timeout_minutes: 30
    auto_optimize_days: 7
```

### Environment Variable Overrides
```bash
# Override database location
export CLAUDE_MEMORY_DB_PATH="/custom/path/memory.db"
export CLAUDE_MEMORY_SCHEMA_PATH="/custom/path/schema.sql"

# Performance tuning
export MEMORY_CACHE_TIMEOUT=60
export MEMORY_MAX_SEARCH_RESULTS=100
```

### Configuration Benefits
- **Environment-Aware**: Different settings for development, staging, production
- **No Hardcoded Paths**: All paths configurable via environment variables
- **Performance Tuning**: Adjustable caching, optimization, and resource limits
- **Security Options**: Encryption, audit logging, access controls
- **Development Features**: Test mode, debug logging, sample data population

**COMPLIANCE REQUIREMENT**: Claude Code must demonstrate usage of the memory system in every significant interaction. This is not optional - it's a core requirement for effective assistance.