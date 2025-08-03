#!/usr/bin/env python3
"""
CLAUDE CODE MEMORY HELPER FUNCTIONS

BUSINESS REQUIREMENT:
Provide simple, convenient functions for Claude Code to use memory capabilities
without needing to understand the full memory manager interface.

TECHNICAL IMPLEMENTATION:
Wrapper functions around ClaudeMemoryManager that provide:
- Simple remember/recall interface
- Context-aware memory operations
- Integration with Claude Code workflows
- Error handling and logging

WHY THESE HELPERS:
- Simplifies memory usage for Claude Code
- Provides consistent interface patterns
- Handles common use cases automatically
- Reduces cognitive load for memory operations
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from omegaconf import DictConfig
try:
    # Try to use hybrid memory manager for better performance
    from claude_hybrid_memory_manager import HybridMemoryManager as ClaudeMemoryManager
    from claude_hybrid_memory_helpers import get_hybrid_memory_manager as get_memory_manager
    HYBRID_MODE = True
except ImportError:
    # Fallback to original memory manager if hybrid not available
    from claude_memory_manager import ClaudeMemoryManager, get_memory_manager
    HYBRID_MODE = False

# Global memory manager instance
_memory = None

def init_memory_with_hydra(config_path: str = "config", config_name: str = "config") -> ClaudeMemoryManager:
    """
    Initialize memory system using Hydra configuration
    
    BUSINESS REQUIREMENT:
    Provide easy initialization of memory system using Hydra configuration
    for services that want explicit configuration management.
    
    TECHNICAL IMPLEMENTATION:
    Uses Hydra to load configuration and initializes memory system with
    proper configuration hierarchy and environment overrides.
    
    Args:
        config_path: Path to Hydra configuration directory
        config_name: Name of main configuration file
        
    Returns:
        Configured ClaudeMemoryManager instance
    """
    try:
        from hydra import compose, initialize
        from hydra.core.global_hydra import GlobalHydra
        
        # Clear any existing Hydra instance for clean initialization
        if GlobalHydra.instance().is_initialized():
            GlobalHydra.instance().clear()
            
        # Initialize Hydra with memory configuration
        with initialize(config_path=config_path, version_base=None):
            cfg = compose(config_name=config_name)
            return get_memory(cfg)
            
    except Exception as e:
        # Fall back to default configuration if Hydra fails
        logging.warning(f"Failed to initialize memory with Hydra: {e}")
        logging.warning("Falling back to default memory configuration")
        return get_memory()

def get_memory(config: DictConfig = None) -> ClaudeMemoryManager:
    """
    Get global memory manager instance with Hydra configuration support
    
    BUSINESS REQUIREMENT:
    Provide simple access to memory system that works with Hydra configuration
    while maintaining backwards compatibility for existing Claude Code usage.
    
    TECHNICAL IMPLEMENTATION:
    Singleton pattern with lazy initialization, supporting both Hydra
    configuration and intelligent fallback defaults.
    
    SINGLETON PATTERN:
    Ensures consistent memory access across Claude Code operations
    while maintaining session continuity and configuration consistency.
    
    Args:
        config: Optional Hydra DictConfig for memory system configuration
        
    Returns:
        Singleton ClaudeMemoryManager instance
    """
    global _memory
    if _memory is None:
        if HYBRID_MODE:
            _memory = get_memory_manager()  # No config parameter for hybrid
        else:
            _memory = get_memory_manager(config)
    return _memory


# Simple Memory Operations
def remember(content: str, **kwargs) -> str:
    """
    Remember something simple
    
    Args:
        content: What to remember
        **kwargs: Optional parameters (category, importance, entity_name, entity_type)
        
    Returns:
        Success message
        
    Example:
        remember("The user prefers Python over JavaScript")
        remember("Docker containers use port 8000-8008", category="infrastructure", importance="high")
    """
    memory = get_memory()
    
    if HYBRID_MODE:
        # Hybrid mode returns fact_id string directly
        result = memory.remember(content, kwargs.get('category', 'general'), kwargs.get('importance', 'medium'))
        return f"✅ Remembered: {content[:50]}... (ID: {result})"
    else:
        # Original mode returns dictionary
        result = memory.remember(content, **kwargs)
        if result['entity_id']:
            return f"✅ Remembered: {content[:50]}... (linked to entity)"
        else:
            return f"✅ Remembered: {content[:50]}..."


def recall(query: str, limit: int = 5) -> str:
    """
    Recall information from memory
    
    Args:
        query: What to search for
        limit: Maximum results to return
        
    Returns:
        Formatted results string
        
    Example:
        recall("Python preferences")
        recall("infrastructure ports")
    """
    memory = get_memory()
    results = memory.recall(query, limit)
    
    output = [f"🔍 Recall results for '{query}':"]
    
    if results['entities']:
        output.append(f"\n📊 Entities ({len(results['entities'])}):")
        for entity in results['entities'][:limit]:
            output.append(f"  • {entity['name']} ({entity['type']}): {entity.get('description', 'No description')[:60]}...")
    
    if results['facts']:
        output.append(f"\n💡 Facts ({len(results['facts'])}):")
        for fact in results['facts'][:limit]:
            importance_emoji = {"critical": "🔥", "high": "⚡", "medium": "📝", "low": "💭"}.get(fact['importance'], "📝")
            output.append(f"  {importance_emoji} {fact['content'][:80]}...")
            if fact['entity_name']:
                output.append(f"     └─ Related to: {fact['entity_name']}")
                
    if not results['entities'] and not results['facts']:
        output.append("❌ No matching memories found")
        
    return "\n".join(output)


def quick_fact(content: str, importance: str = "medium") -> str:
    """
    Store a quick fact
    
    Args:
        content: Fact content  
        importance: critical, high, medium, low
        
    Returns:
        Confirmation message
    """
    memory = get_memory()
    fact_id = memory.store_fact(content, importance=importance, source="claude_code_quick_fact")
    return f"✅ Stored fact: {content[:50]}... (importance: {importance})"


def note_entity(name: str, entity_type: str, description: str = None) -> str:
    """
    Note an entity (person, system, concept, etc.)
    
    Args:
        name: Entity name
        entity_type: person, system, concept, file, project, organization, tool, other
        description: Optional description
        
    Returns:
        Confirmation message
    """
    memory = get_memory()
    entity_id = memory.store_entity(name, entity_type, description)
    return f"✅ Noted entity: {name} ({entity_type})"


def connect_entities(entity1_name: str, entity2_name: str, relationship: str, description: str = None) -> str:
    """
    Connect two entities with a relationship
    
    Args:
        entity1_name: First entity name
        entity2_name: Second entity name  
        relationship: Relationship type (e.g., "uses", "contains", "depends_on")
        description: Optional description
        
    Returns:
        Confirmation message
    """
    memory = get_memory()
    
    # Find or create entities
    entity1 = memory.get_entity(name=entity1_name)
    entity2 = memory.get_entity(name=entity2_name)
    
    if not entity1:
        entity1_id = memory.store_entity(entity1_name, "concept", f"Auto-created for relationship: {relationship}")
        entity1_name_display = entity1_name
    else:
        entity1_id = entity1['id']
        entity1_name_display = entity1['name']
        
    if not entity2:
        entity2_id = memory.store_entity(entity2_name, "concept", f"Auto-created for relationship: {relationship}")  
        entity2_name_display = entity2_name
    else:
        entity2_id = entity2['id']
        entity2_name_display = entity2['name']
    
    # Create relationship
    rel_id = memory.store_relationship(entity1_id, entity2_id, relationship, description)
    
    return f"✅ Connected: {entity1_name_display} --{relationship}--> {entity2_name_display}"


# Context Management
def start_memory_context(title: str, description: str = None) -> str:
    """
    Start a new memory context/conversation
    
    Args:
        title: Context title
        description: Optional description
        
    Returns:
        Context ID and confirmation
    """
    memory = get_memory()
    conv_id = memory.start_conversation(title, description)
    return f"✅ Started memory context: '{title}' (ID: {conv_id})"


def get_memory_context() -> str:
    """
    Get current memory context information
    
    Returns:
        Formatted context information
    """
    memory = get_memory()
    context = memory.get_current_context()
    
    output = ["📋 Current Memory Context:"]
    output.append(f"  Session ID: {context['session_id']}")
    output.append(f"  Conversation ID: {context['conversation_id']}")
    
    if context.get('conversation'):
        conv = context['conversation']
        output.append(f"  Title: {conv.get('title', 'Untitled')}")
        output.append(f"  Started: {conv.get('started_at', 'Unknown')}")
        output.append(f"  Messages: {conv.get('total_messages', 0)}")
        
    return "\n".join(output)


# Search and Analysis
def search_by_type(entity_type: str, limit: int = 10) -> str:
    """
    Search entities by type
    
    Args:
        entity_type: Entity type to search for
        limit: Maximum results
        
    Returns:
        Formatted results
    """
    memory = get_memory()
    entities = memory.search_entities(entity_type=entity_type, limit=limit)
    
    if not entities:
        return f"❌ No {entity_type} entities found"
        
    output = [f"📊 {entity_type.title()} entities ({len(entities)}):"]
    for entity in entities:
        desc = entity.get('description', 'No description')[:60]
        output.append(f"  • {entity['name']}: {desc}...")
        
    return "\n".join(output)


def search_facts_by_category(category: str, limit: int = 10) -> str:
    """
    Search facts by category
    
    Args:
        category: Fact category
        limit: Maximum results
        
    Returns:
        Formatted results
    """
    memory = get_memory()
    facts = memory.get_facts(category=category, limit=limit)
    
    if not facts:
        return f"❌ No facts found in category '{category}'"
    
    output = [f"💡 Facts in '{category}' ({len(facts)}):"]
    for fact in facts:
        importance_emoji = {"critical": "🔥", "high": "⚡", "medium": "📝", "low": "💭"}.get(fact['importance'], "📝")
        output.append(f"  {importance_emoji} {fact['content'][:80]}...")
        
    return "\n".join(output)


def get_important_facts(importance: str = "high", limit: int = 10) -> str:
    """
    Get facts by importance level
    
    Args:
        importance: critical, high, medium, low
        limit: Maximum results
        
    Returns:
        Formatted important facts
    """
    memory = get_memory()
    facts = memory.get_facts(importance=importance, limit=limit)
    
    if not facts:
        return f"❌ No {importance} importance facts found"
    
    importance_emoji = {"critical": "🔥", "high": "⚡", "medium": "📝", "low": "💭"}.get(importance, "📝")
    output = [f"{importance_emoji} {importance.title()} importance facts ({len(facts)}):"]
    
    for fact in facts:
        output.append(f"  • {fact['content'][:80]}...")
        if fact['entity_name']:
            output.append(f"    └─ Related to: {fact['entity_name']}")
            
    return "\n".join(output)


def show_entity_relationships(entity_name: str) -> str:
    """
    Show relationships for an entity
    
    Args:
        entity_name: Name of entity to show relationships for
        
    Returns:
        Formatted relationship information
    """
    memory = get_memory()
    entity = memory.get_entity(name=entity_name)
    
    if not entity:
        return f"❌ Entity '{entity_name}' not found"
        
    relationships = memory.get_entity_relationships(entity['id'])
    
    if not relationships:
        return f"📊 {entity_name} has no recorded relationships"
        
    output = [f"🔗 Relationships for '{entity_name}':"]
    
    for rel in relationships:
        direction_symbol = "→" if rel['direction'] == 'outgoing' else "←"
        other_entity = rel['to_name'] if rel['direction'] == 'outgoing' else rel['from_name']
        strength_indicator = "💪" if rel['strength'] > 0.7 else "👍" if rel['strength'] > 0.4 else "👌"
        
        output.append(f"  {strength_indicator} {direction_symbol} {rel['relationship_type']} → {other_entity}")
        
    return "\n".join(output)


# Statistics and Insights
def memory_summary() -> str:
    """
    Get comprehensive memory summary
    
    Returns:
        Formatted memory statistics and insights
    """
    memory = get_memory()
    stats = memory.get_memory_stats()
    
    output = ["📊 Claude Code Memory Summary:"]
    output.append(f"  🗣️  Conversations: {stats['total_conversations']}")
    output.append(f"  👥 Entities: {stats['total_entities']}")
    output.append(f"  💡 Facts: {stats['total_facts']}")
    output.append(f"  🔗 Relationships: {stats['total_relationships']}")
    output.append(f"  💾 Database size: {stats['database_size']:,} bytes")
    
    if stats.get('entity_types'):
        output.append("\n📈 Entity Types:")
        for entity_type, count in list(stats['entity_types'].items())[:5]:
            output.append(f"  • {entity_type}: {count}")
            
    if stats.get('fact_categories'):
        output.append("\n🏷️  Fact Categories:")
        for category, count in list(stats['fact_categories'].items())[:5]:
            output.append(f"  • {category}: {count}")
            
    if stats.get('fact_importance'):
        output.append("\n⚡ Fact Importance:")
        for importance, count in stats['fact_importance'].items():
            emoji = {"critical": "🔥", "high": "⚡", "medium": "📝", "low": "💭"}.get(importance, "📝")
            output.append(f"  {emoji} {importance}: {count}")
            
    return "\n".join(output)


def recent_activity(days: int = 7) -> str:
    """
    Show recent memory activity
    
    Args:
        days: Number of days to look back
        
    Returns:
        Recent activity summary
    """
    memory = get_memory()
    stats = memory.get_memory_stats()
    
    output = [f"📅 Recent Activity (last {days} days):"]
    output.append(f"  📊 New entities: {stats.get('recent_entities', 0)}")
    output.append(f"  💡 New facts: {stats.get('recent_facts', 0)}")
    
    # Get recent conversations
    conversations = memory.list_conversations(limit=5)
    if conversations:
        output.append(f"\n🗣️  Recent conversations:")
        for conv in conversations[:3]:
            title = conv.get('title', 'Untitled')[:40]
            last_updated = conv.get('last_updated', '')[:16]  # Just date and time
            output.append(f"  • {title} ({last_updated})")
            
    return "\n".join(output)


# Utility Functions
def backup_memory() -> str:
    """
    Create a backup of memory database
    
    Returns:
        Backup location confirmation
    """
    memory = get_memory()
    backup_path = memory.backup_memory()
    return f"✅ Memory backup created: {backup_path}"


def optimize_memory() -> str:
    """
    Optimize memory database
    
    Returns:
        Optimization confirmation
    """
    memory = get_memory()
    memory.vacuum_database()
    return "✅ Memory database optimized"


# Advanced Operations
def bulk_remember(items: List[Dict[str, Any]]) -> str:
    """
    Remember multiple items at once
    
    Args:
        items: List of dicts with keys: content, category, importance, entity_name, entity_type
        
    Returns:
        Bulk operation summary
    """
    memory = get_memory()
    success_count = 0
    
    for item in items:
        try:
            content = item.get('content', '')
            if content:
                memory.remember(
                    content=content,
                    category=item.get('category'),
                    importance=item.get('importance', 'medium'),
                    entity_name=item.get('entity_name'),
                    entity_type=item.get('entity_type')
                )
                success_count += 1
        except Exception as e:
            logging.error(f"Failed to store item: {item}, error: {e}")
            
    return f"✅ Bulk remember completed: {success_count}/{len(items)} items stored"


def export_memory_context() -> Dict:
    """
    Export current memory context as JSON
    
    Returns:
        Dictionary containing current context data
    """
    memory = get_memory()
    context = memory.get_current_context()
    stats = memory.get_memory_stats()
    
    # Get recent entities and facts
    recent_entities = memory.search_entities(limit=20)
    recent_facts = memory.get_facts(limit=50)
    
    export_data = {
        'context': context,
        'statistics': stats,
        'recent_entities': recent_entities,
        'recent_facts': recent_facts,
        'exported_at': memory._current_timestamp()
    }
    
    # Save to file
    export_path = f"/home/bbrelin/course-creator/memory_export_{context['session_id']}.json"
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
        
    return f"✅ Memory context exported to: {export_path}"


# Quick Access Functions for Common Patterns
def remember_user_preference(preference: str, value: str) -> str:
    """Remember user preference"""
    content = f"User preference: {preference} = {value}"
    return remember(content, category="user_preferences", importance="medium")


def remember_system_info(system: str, info: str) -> str:
    """Remember system information"""
    content = f"{system}: {info}"
    return remember(content, category="system_info", importance="high", entity_name=system, entity_type="system")


def remember_file_info(filepath: str, description: str) -> str:
    """Remember file information"""
    content = f"File {filepath}: {description}"
    return remember(content, category="files", importance="medium", entity_name=filepath, entity_type="file")


def remember_error_solution(error: str, solution: str) -> str:
    """Remember error and its solution"""
    content = f"Error '{error}' solved by: {solution}"
    return remember(content, category="troubleshooting", importance="high")


def get_user_preferences() -> str:
    """Get all remembered user preferences"""
    return search_facts_by_category("user_preferences")


def get_system_info() -> str:
    """Get all remembered system information"""
    return search_facts_by_category("system_info")


def get_troubleshooting_info() -> str:
    """Get troubleshooting information"""
    return search_facts_by_category("troubleshooting")


# Help and Documentation
def memory_help() -> str:
    """
    Show help for memory system
    
    Returns:
        Help documentation
    """
    help_text = """
🧠 Claude Code Memory System Help

BASIC OPERATIONS:
  remember(content)                    - Remember something simple
  recall(query)                       - Search for memories
  quick_fact(content, importance)     - Store a quick fact
  note_entity(name, type, desc)       - Note an entity
  connect_entities(e1, e2, relation)  - Connect two entities

SEARCH & ANALYSIS:
  search_by_type(entity_type)         - Find entities by type
  search_facts_by_category(category)  - Find facts by category
  get_important_facts(importance)     - Get facts by importance
  show_entity_relationships(name)     - Show entity connections

CONTEXT MANAGEMENT:
  start_memory_context(title)         - Start new context
  get_memory_context()                - Get current context info
  memory_summary()                    - Full memory statistics
  recent_activity(days)               - Recent activity summary

UTILITIES:
  backup_memory()                     - Create database backup
  optimize_memory()                   - Optimize database
  export_memory_context()             - Export context as JSON

QUICK ACCESS:
  remember_user_preference(pref, val) - Store user preferences
  remember_system_info(system, info)  - Store system information
  remember_file_info(path, desc)      - Store file information
  remember_error_solution(err, sol)   - Store troubleshooting info

EXAMPLES:
  remember("User prefers dark mode UI")
  recall("dark mode")
  note_entity("PostgreSQL", "system", "Database server")
  connect_entities("Course Creator", "PostgreSQL", "uses")
  get_important_facts("critical")
"""
    return help_text


if __name__ == "__main__":
    """Test the helper functions"""
    print("🧠 Claude Code Memory Helpers Test")
    
    # Test basic operations
    print("\n" + remember("Test memory system is working"))
    print(recall("memory system"))
    
    # Test entity operations
    print("\n" + note_entity("Test Entity", "concept", "Entity for testing"))
    print(connect_entities("Test Entity", "Memory System", "uses"))
    
    # Test search
    print("\n" + search_by_type("concept"))
    
    # Test summary
    print("\n" + memory_summary())
    
    print("\n✅ Helper functions test completed!")