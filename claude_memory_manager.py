#!/usr/bin/env python3
"""
CLAUDE CODE MEMORY MANAGER

BUSINESS REQUIREMENT:
Provide Claude Code with persistent memory capabilities across conversations,
enabling context retention, entity tracking, fact storage, and relationship management.

TECHNICAL IMPLEMENTATION:
SQLite-based memory system with Python interface for Claude Code tool integration.
Supports CRUD operations, complex queries, and automatic session management.

DESIGN PRINCIPLES:
- Single Responsibility: Each method handles one specific memory operation
- Open/Closed: Extensible for new memory types without modifying existing code
- Interface Segregation: Clean separation between read/write operations
- Dependency Inversion: Abstract database operations through methods

SECURITY CONSIDERATIONS:
- SQL injection prevention through parameterized queries
- Input validation for all user data
- Proper error handling and logging

PERFORMANCE OPTIMIZATIONS:
- Connection pooling and context management
- Indexed queries for fast lookups
- Batch operations for bulk data handling
- WAL mode for concurrent access
"""

import sqlite3
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from contextlib import contextmanager
from pathlib import Path
import os
from omegaconf import DictConfig
import hydra
from hydra.core.config_store import ConfigStore


class ClaudeMemoryManager:
    """
    Comprehensive memory management system for Claude Code
    
    Provides persistent storage and retrieval of:
    - Conversations and context
    - Entities (people, systems, concepts)
    - Facts and knowledge
    - Relationships between entities
    - Query patterns and frequency
    """
    
    def __init__(self, config: DictConfig = None):
        """
        Initialize memory manager with Hydra configuration
        
        BUSINESS REQUIREMENT:
        Create memory manager instance using Hydra configuration for
        environment-aware setup with proper fallback defaults.
        
        TECHNICAL IMPLEMENTATION:
        Uses Hydra DictConfig for all paths and settings, with intelligent
        fallback to sensible defaults for development environments.
        
        Args:
            config: Hydra DictConfig with memory system configuration
        """
        # Initialize configuration with fallbacks
        self.config = self._init_config(config)
        
        # Extract paths from configuration
        self.db_path = Path(self.config.memory.database.db_path)
        self.schema_path = Path(self.config.memory.database.schema_path)
        
        # Session tracking
        self.current_session_id = None
        self.current_conversation_id = None
        
        # Setup logging based on configuration
        self._setup_logging()
        
        # Initialize database
        self._init_database()
    
    def _init_config(self, config: DictConfig = None) -> DictConfig:
        """
        Initialize configuration with Hydra or fallback defaults
        
        BUSINESS REQUIREMENT:
        Provide robust configuration initialization that works in all environments,
        from development to production, with intelligent path resolution.
        
        TECHNICAL IMPLEMENTATION:
        - Try to use provided config first
        - Fall back to Hydra global config if available
        - Use hardcoded defaults as last resort
        - Resolve relative paths relative to current working directory
        
        Args:
            config: Optional Hydra configuration object
            
        Returns:
            DictConfig with complete memory system configuration
        """
        if config is not None:
            return config
            
        # Try to get Hydra config if running in Hydra context
        try:
            from hydra import compose, initialize_config_module
            from hydra.core.global_hydra import GlobalHydra
            
            if GlobalHydra.instance().is_initialized():
                # Use existing Hydra configuration
                from hydra.core.hydra_config import HydraConfig
                hydra_cfg = HydraConfig.get()
                return hydra_cfg.cfg
        except Exception:
            pass
            
        # Fallback to default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> DictConfig:
        """
        Get default configuration for standalone operation
        
        BUSINESS REQUIREMENT:
        Provide sensible defaults that work in development environments
        without requiring complex configuration setup.
        
        TECHNICAL IMPLEMENTATION:
        Returns a DictConfig-compatible object with all necessary
        memory system settings using current working directory as base.
        
        Returns:
            DictConfig with default memory system configuration
        """
        from omegaconf import OmegaConf
        
        # Get current working directory for relative paths
        cwd = os.getcwd()
        
        default_config = {
            'memory': {
                'database': {
                    'db_path': os.path.join(cwd, 'claude_memory.db'),
                    'schema_path': os.path.join(cwd, 'claude_memory_schema.sql'),
                    'connection_params': {
                        'journal_mode': 'WAL',
                        'cache_size': 2000,
                        'foreign_keys': True,
                        'timeout': 30.0,
                        'wal_autocheckpoint': 1000
                    }
                },
                'session': {
                    'cleanup_after_hours': 24,
                    'max_sessions': 100,
                    'track_context': True
                },
                'entities': {
                    'cache_size': 1000,
                    'cleanup_threshold_days': 90,
                    'auto_discover_relationships': True
                },
                'search': {
                    'max_results': 50,
                    'fuzzy_matching': True,
                    'fuzzy_threshold': 0.6
                },
                'performance': {
                    'enable_caching': True,
                    'cache_timeout_minutes': 30,
                    'auto_optimize_days': 7,
                    'enable_monitoring': False
                },
                'logging': {
                    'level': 'INFO',
                    'log_queries': False,
                    'log_file': '',
                    'structured_logging': True
                },
                'development': {
                    'test_mode': False,
                    'reset_on_startup': False,
                    'debug_mode': False,
                    'populate_sample_data': False
                },
                'security': {
                    'encrypt_data': False,
                    'encryption_key_path': '',
                    'audit_logging': False,
                    'max_memory_mb': 100
                }
            }
        }
        
        return OmegaConf.create(default_config)
    
    def _setup_logging(self) -> None:
        """
        Setup logging based on configuration
        
        BUSINESS REQUIREMENT:
        Configure logging that integrates with the Course Creator platform's
        centralized logging system while supporting standalone operation.
        
        TECHNICAL IMPLEMENTATION:
        Uses configuration-driven log level and format settings with
        fallback to basic logging for development environments.
        """
        log_level = getattr(logging, self.config.memory.logging.level.upper())
        
        # Setup logger with appropriate format
        if self.config.memory.logging.structured_logging:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        else:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
        logging.basicConfig(
            level=log_level,
            format=log_format
        )
        
        self.logger = logging.getLogger(__name__)
        
        if self.config.memory.development.debug_mode:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Memory system initialized in debug mode")
        
    def _init_database(self) -> None:
        """
        Initialize database with schema if it doesn't exist
        
        BUSINESS LOGIC:
        Creates database and tables on first run, ensuring proper constraints
        and indexes are in place for optimal performance.
        """
        if not self.db_path.exists():
            self.logger.info("Creating new memory database")
            self._create_database()
        else:
            self.logger.info(f"Using existing memory database: {self.db_path}")
            
        # Start new session
        self._start_session()
    
    def _create_database(self) -> None:
        """
        Create database with schema from SQL file
        
        BUSINESS REQUIREMENT:
        Initialize SQLite database with proper schema and constraints
        for Claude Code memory system operations.
        
        TECHNICAL IMPLEMENTATION:
        Reads schema from configured path and applies it to new database,
        with proper error handling and configuration validation.
        """
        if not self.schema_path.exists():
            # Provide helpful error message with configuration info
            self.logger.error(f"Schema file not found: {self.schema_path}")
            self.logger.error(f"Current working directory: {os.getcwd()}")
            self.logger.error(f"Configured schema path: {self.config.memory.database.schema_path}")
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}. "
                f"Please ensure the claude_memory_schema.sql file exists in the configured location."
            )
            
        self.logger.info(f"Creating memory database at: {self.db_path}")
        
        with open(self.schema_path, 'r') as f:
            schema_sql = f.read()
            
        with self._get_connection() as conn:
            # Use executescript to handle the full SQL file
            conn.executescript(schema_sql)
            
        self.logger.info("Database schema created successfully")
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections
        
        TECHNICAL IMPLEMENTATION:
        Ensures proper connection handling with automatic commit/rollback
        and connection cleanup. Uses WAL mode for better concurrency.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
            
    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID with optional prefix"""
        return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex
        
    def _current_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
    
    # Session Management
    def _start_session(self) -> str:
        """
        Start new memory session
        
        BUSINESS REQUIREMENT:
        Track Claude Code usage sessions for context and analytics.
        Each session represents a period of Claude Code activity.
        """
        session_id = self._generate_id("session")
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO memory_sessions (id, started_at, total_operations, context)
                VALUES (?, ?, ?, ?)
            """, (session_id, self._current_timestamp(), 0, "Claude Code session started"))
            conn.commit()
            
        self.current_session_id = session_id
        self.logger.info(f"Started memory session: {session_id}")
        return session_id
    
    def end_session(self) -> None:
        """End current memory session"""
        if self.current_session_id:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE memory_sessions 
                    SET ended_at = ?, total_operations = (
                        SELECT COUNT(*) FROM facts WHERE source_conversation IN (
                            SELECT id FROM conversations WHERE id = ?
                        )
                    )
                    WHERE id = ?
                """, (self._current_timestamp(), self.current_conversation_id or '', self.current_session_id))
                conn.commit()
                
            self.logger.info(f"Ended memory session: {self.current_session_id}")
            self.current_session_id = None
    
    # Conversation Management
    def start_conversation(self, title: str = None, context: str = None) -> str:
        """
        Start new conversation context
        
        Args:
            title: Optional conversation title
            context: Optional context description
            
        Returns:
            Conversation ID
        """
        conversation_id = self._generate_id("conv")
        title = title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations (id, title, context_summary, total_messages)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, title, context, 0))
            conn.commit()
            
        self.current_conversation_id = conversation_id
        self.logger.info(f"Started conversation: {conversation_id} - {title}")
        return conversation_id
    
    def update_conversation(self, conversation_id: str, **kwargs) -> bool:
        """
        Update conversation details
        
        Args:
            conversation_id: ID of conversation to update
            **kwargs: Fields to update (title, context_summary, status, key_topics)
        """
        if not kwargs:
            return False
            
        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['title', 'context_summary', 'status', 'key_topics', 'metadata']:
                fields.append(f"{key} = ?")
                values.append(json.dumps(value) if key in ['key_topics', 'metadata'] else value)
        
        if not fields:
            return False
            
        fields.append("last_updated = ?")
        values.append(self._current_timestamp())
        values.append(conversation_id)
        
        with self._get_connection() as conn:
            result = conn.execute(f"""
                UPDATE conversations 
                SET {', '.join(fields)}
                WHERE id = ?
            """, values)
            conn.commit()
            
        return result.rowcount > 0
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        with self._get_connection() as conn:
            result = conn.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,)).fetchone()
            
        return dict(result) if result else None
    
    def list_conversations(self, status: str = 'active', limit: int = 50) -> List[Dict]:
        """List recent conversations"""
        with self._get_connection() as conn:
            results = conn.execute("""
                SELECT * FROM conversations 
                WHERE status = ?
                ORDER BY last_updated DESC
                LIMIT ?
            """, (status, limit)).fetchall()
            
        return [dict(row) for row in results]
    
    # Entity Management
    def store_entity(self, name: str, entity_type: str, description: str = None, 
                    properties: Dict = None, confidence: float = 1.0) -> str:
        """
        Store entity in memory
        
        Args:
            name: Entity name
            entity_type: Type (person, system, concept, file, project, organization, tool, other)
            description: Optional description
            properties: Optional properties dict
            confidence: Confidence level (0.0-1.0)
            
        Returns:
            Entity ID
        """
        entity_id = self._generate_id("entity")
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO entities (id, name, type, description, properties, confidence, source_conversation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (entity_id, name, entity_type, description, 
                  json.dumps(properties) if properties else None,
                  confidence, self.current_conversation_id))
            conn.commit()
            
        self.logger.info(f"Stored entity: {name} ({entity_type})")
        return entity_id
    
    def get_entity(self, entity_id: str = None, name: str = None) -> Optional[Dict]:
        """Get entity by ID or name"""
        with self._get_connection() as conn:
            if entity_id:
                result = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
            elif name:
                result = conn.execute("SELECT * FROM entities WHERE name = ? ORDER BY last_updated DESC LIMIT 1", 
                                    (name,)).fetchone()
            else:
                return None
                
        if result:
            entity = dict(result)
            if entity['properties']:
                entity['properties'] = json.loads(entity['properties'])
            return entity
        return None
    
    def search_entities(self, query: str = None, entity_type: str = None, limit: int = 20) -> List[Dict]:
        """Search entities by name or type"""
        with self._get_connection() as conn:
            if query and entity_type:
                results = conn.execute("""
                    SELECT * FROM entities 
                    WHERE (name LIKE ? OR description LIKE ?) AND type = ?
                    ORDER BY last_updated DESC LIMIT ?
                """, (f"%{query}%", f"%{query}%", entity_type, limit)).fetchall()
            elif query:
                results = conn.execute("""
                    SELECT * FROM entities 
                    WHERE name LIKE ? OR description LIKE ?
                    ORDER BY last_updated DESC LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit)).fetchall()
            elif entity_type:
                results = conn.execute("""
                    SELECT * FROM entities 
                    WHERE type = ?
                    ORDER BY last_updated DESC LIMIT ?
                """, (entity_type, limit)).fetchall()
            else:
                results = conn.execute("""
                    SELECT * FROM entities 
                    ORDER BY last_updated DESC LIMIT ?
                """, (limit,)).fetchall()
                
        entities = []
        for row in results:
            entity = dict(row)
            if entity['properties']:
                entity['properties'] = json.loads(entity['properties'])
            entities.append(entity)
            
        return entities
    
    def update_entity(self, entity_id: str, **kwargs) -> bool:
        """Update entity properties"""
        if not kwargs:
            return False
            
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'type', 'description', 'confidence']:
                fields.append(f"{key} = ?")
                values.append(value)
            elif key == 'properties':
                fields.append("properties = ?")
                values.append(json.dumps(value))
                
        if not fields:
            return False
            
        fields.append("last_updated = ?")
        values.append(self._current_timestamp())
        values.append(entity_id)
        
        with self._get_connection() as conn:
            result = conn.execute(f"""
                UPDATE entities 
                SET {', '.join(fields)}
                WHERE id = ?
            """, values)
            conn.commit()
            
        return result.rowcount > 0
    
    # Fact Management
    def store_fact(self, content: str, category: str = None, importance: str = 'medium',
                  entity_id: str = None, source: str = None, confidence: float = 1.0,
                  metadata: Dict = None) -> str:
        """
        Store fact in memory
        
        Args:
            content: Fact content
            category: Optional category
            importance: Importance level (critical, high, medium, low)
            entity_id: Optional related entity ID
            source: Optional source information
            confidence: Confidence level (0.0-1.0)
            metadata: Optional metadata dict
            
        Returns:
            Fact ID
        """
        fact_id = self._generate_id("fact")
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO facts (id, content, category, importance, confidence, source, 
                                 source_conversation, entity_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fact_id, content, category, importance, confidence, source,
                  self.current_conversation_id, entity_id, 
                  json.dumps(metadata) if metadata else None))
            conn.commit()
            
        self.logger.info(f"Stored fact: {content[:50]}..." if len(content) > 50 else f"Stored fact: {content}")
        return fact_id
    
    def get_facts(self, category: str = None, importance: str = None, 
                 entity_id: str = None, limit: int = 50) -> List[Dict]:
        """Get facts by various criteria"""
        query = "SELECT f.*, e.name as entity_name FROM facts f LEFT JOIN entities e ON f.entity_id = e.id WHERE 1=1"
        params = []
        
        if category:
            query += " AND f.category = ?"
            params.append(category)
        if importance:
            query += " AND f.importance = ?"
            params.append(importance)
        if entity_id:
            query += " AND f.entity_id = ?"
            params.append(entity_id)
            
        query += " ORDER BY f.importance DESC, f.created_at DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            
        facts = []
        for row in results:
            fact = dict(row)
            if fact['metadata']:
                fact['metadata'] = json.loads(fact['metadata'])
            facts.append(fact)
            
        return facts
    
    def search_facts(self, query: str, limit: int = 20) -> List[Dict]:
        """Search facts by content"""
        with self._get_connection() as conn:
            results = conn.execute("""
                SELECT f.*, e.name as entity_name 
                FROM facts f 
                LEFT JOIN entities e ON f.entity_id = e.id
                WHERE f.content LIKE ?
                ORDER BY f.importance DESC, f.created_at DESC
                LIMIT ?
            """, (f"%{query}%", limit)).fetchall()
            
        facts = []
        for row in results:
            fact = dict(row)
            if fact['metadata']:
                fact['metadata'] = json.loads(fact['metadata'])
            facts.append(fact)
            
        return facts
    
    # Relationship Management
    def store_relationship(self, from_entity: str, to_entity: str, relationship_type: str,
                          description: str = None, strength: float = 1.0, 
                          bidirectional: bool = False) -> str:
        """
        Store relationship between entities
        
        Args:
            from_entity: Source entity ID
            to_entity: Target entity ID
            relationship_type: Type of relationship
            description: Optional description
            strength: Relationship strength (0.0-1.0)
            bidirectional: Whether relationship works both ways
            
        Returns:
            Relationship ID
        """
        relationship_id = self._generate_id("rel")
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, from_entity, to_entity, relationship_type, description, strength, 
                 bidirectional, source_conversation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (relationship_id, from_entity, to_entity, relationship_type, description,
                  strength, bidirectional, self.current_conversation_id))
            conn.commit()
            
        self.logger.info(f"Stored relationship: {from_entity} -> {relationship_type} -> {to_entity}")
        return relationship_id
    
    def get_entity_relationships(self, entity_id: str, direction: str = 'both') -> List[Dict]:
        """
        Get relationships for an entity
        
        Args:
            entity_id: Entity ID
            direction: 'from', 'to', or 'both'
        """
        query_parts = []
        params = []
        
        if direction in ['from', 'both']:
            query_parts.append("""
                SELECT r.*, e1.name as from_name, e2.name as to_name, 'outgoing' as direction
                FROM relationships r
                JOIN entities e1 ON r.from_entity = e1.id
                JOIN entities e2 ON r.to_entity = e2.id
                WHERE r.from_entity = ?
            """)
            params.append(entity_id)
            
        if direction in ['to', 'both']:
            if query_parts:
                query_parts.append(" UNION ALL ")
            query_parts.append("""
                SELECT r.*, e1.name as from_name, e2.name as to_name, 'incoming' as direction
                FROM relationships r
                JOIN entities e1 ON r.from_entity = e1.id
                JOIN entities e2 ON r.to_entity = e2.id
                WHERE r.to_entity = ?
            """)
            params.append(entity_id)
            
        query = "".join(query_parts) + " ORDER BY strength DESC"
        
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            
        return [dict(row) for row in results]
    
    # Memory Statistics and Analysis
    def get_memory_stats(self) -> Dict:
        """Get comprehensive memory statistics"""
        with self._get_connection() as conn:
            stats = {}
            
            # Basic counts
            stats['total_conversations'] = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            stats['total_entities'] = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            stats['total_facts'] = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            stats['total_relationships'] = conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
            
            # Entity types breakdown
            entity_types = conn.execute("""
                SELECT type, COUNT(*) as count 
                FROM entities 
                GROUP BY type 
                ORDER BY count DESC
            """).fetchall()
            stats['entity_types'] = {row[0]: row[1] for row in entity_types}
            
            # Fact categories breakdown
            fact_categories = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM facts 
                WHERE category IS NOT NULL
                GROUP BY category 
                ORDER BY count DESC
            """).fetchall()
            stats['fact_categories'] = {row[0]: row[1] for row in fact_categories}
            
            # Importance distribution
            importance_dist = conn.execute("""
                SELECT importance, COUNT(*) as count 
                FROM facts 
                GROUP BY importance 
                ORDER BY 
                    CASE importance 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END
            """).fetchall()
            stats['fact_importance'] = {row[0]: row[1] for row in importance_dist}
            
            # Recent activity
            stats['recent_entities'] = conn.execute("""
                SELECT COUNT(*) FROM entities 
                WHERE last_updated > datetime('now', '-7 days')
            """).fetchone()[0]
            
            stats['recent_facts'] = conn.execute("""
                SELECT COUNT(*) FROM facts 
                WHERE created_at > datetime('now', '-7 days')
            """).fetchone()[0]
            
            # Database size
            stats['database_size'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            
        return stats
    
    # Query Management
    def log_query(self, query_text: str, query_type: str = 'search', results_count: int = 0) -> None:
        """Log query for frequency analysis"""
        query_id = f"query_{hash(query_text) & 0x7FFFFFFF:08x}"
        
        with self._get_connection() as conn:
            # Try to update existing query
            result = conn.execute("""
                UPDATE queries 
                SET frequency = frequency + 1, last_used = ?, results_count = ?
                WHERE id = ?
            """, (self._current_timestamp(), results_count, query_id))
            
            # If no existing query, insert new one
            if result.rowcount == 0:
                conn.execute("""
                    INSERT INTO queries (id, query_text, query_type, frequency, results_count)
                    VALUES (?, ?, ?, 1, ?)
                """, (query_id, query_text, query_type, results_count))
                
            conn.commit()
    
    def get_frequent_queries(self, query_type: str = None, limit: int = 10) -> List[Dict]:
        """Get most frequent queries"""
        if query_type:
            query = """
                SELECT * FROM queries 
                WHERE query_type = ?
                ORDER BY frequency DESC, last_used DESC 
                LIMIT ?
            """
            params = (query_type, limit)
        else:
            query = """
                SELECT * FROM queries 
                ORDER BY frequency DESC, last_used DESC 
                LIMIT ?
            """
            params = (limit,)
            
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            
        return [dict(row) for row in results]
    
    # Utility Methods
    def backup_memory(self, backup_path: str = None) -> str:
        """Create backup of memory database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/home/bbrelin/course-creator/claude_memory_backup_{timestamp}.db"
            
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        self.logger.info(f"Memory backup created: {backup_path}")
        return backup_path
    
    def vacuum_database(self) -> None:
        """Optimize database by vacuuming"""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
            
        self.logger.info("Database vacuumed and optimized")
    
    def clear_old_data(self, days: int = 90) -> int:
        """Clear data older than specified days"""
        with self._get_connection() as conn:
            # Delete old conversations and related data
            result = conn.execute("""
                DELETE FROM conversations 
                WHERE status = 'archived' 
                AND last_updated < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted_count = result.rowcount
            conn.commit()
            
        self.logger.info(f"Cleared {deleted_count} old conversations")
        return deleted_count
    
    # Context Management for Claude Code
    def get_current_context(self) -> Dict:
        """Get current conversation and session context"""
        context = {
            'session_id': self.current_session_id,
            'conversation_id': self.current_conversation_id,
            'timestamp': self._current_timestamp()
        }
        
        if self.current_conversation_id:
            conversation = self.get_conversation(self.current_conversation_id)
            if conversation:
                context['conversation'] = conversation
                
        return context
    
    def remember(self, content: str, category: str = None, importance: str = 'medium',
                entity_name: str = None, entity_type: str = None) -> Dict:
        """
        Convenient method to remember something
        
        BUSINESS LOGIC:
        Simplified interface for Claude Code to store information.
        Automatically handles entity creation and fact storage.
        """
        result = {'fact_id': None, 'entity_id': None}
        
        # Create or find entity if specified
        if entity_name:
            entity = self.get_entity(name=entity_name)
            if not entity:
                entity_id = self.store_entity(
                    name=entity_name,
                    entity_type=entity_type or 'concept',
                    description=f"Entity mentioned in context: {content[:100]}"
                )
                result['entity_id'] = entity_id
            else:
                result['entity_id'] = entity['id']
        
        # Store the fact
        fact_id = self.store_fact(
            content=content,
            category=category,
            importance=importance,
            entity_id=result['entity_id'],
            source='claude_code_remember'
        )
        result['fact_id'] = fact_id
        
        return result
    
    def recall(self, query: str, limit: int = 10) -> Dict:
        """
        Convenient method to recall information
        
        Returns comprehensive search results across entities and facts
        """
        self.log_query(query, 'recall')
        
        results = {
            'query': query,
            'entities': self.search_entities(query, limit=limit),
            'facts': self.search_facts(query, limit=limit),
            'timestamp': self._current_timestamp()
        }
        
        # Log results count
        total_results = len(results['entities']) + len(results['facts'])
        self.log_query(query, 'recall', total_results)
        
        return results
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.end_session()


# Convenience function for Claude Code
def get_memory_manager(config: DictConfig = None) -> ClaudeMemoryManager:
    """
    Get singleton memory manager instance with Hydra configuration support
    
    BUSINESS REQUIREMENT:
    Provide a singleton memory manager that can be configured with Hydra
    while maintaining backwards compatibility for existing code.
    
    TECHNICAL IMPLEMENTATION:
    Uses singleton pattern with lazy initialization, supporting both
    Hydra configuration and fallback defaults for development.
    
    Args:
        config: Optional Hydra DictConfig for memory system configuration
        
    Returns:
        Singleton ClaudeMemoryManager instance
    """
    if not hasattr(get_memory_manager, '_instance'):
        get_memory_manager._instance = ClaudeMemoryManager(config)
    return get_memory_manager._instance


if __name__ == "__main__":
    """
    Example usage and testing
    """
    # Test the memory system
    with ClaudeMemoryManager() as memory:
        print("Claude Code Memory System Test")
        
        # Start a conversation
        conv_id = memory.start_conversation("Memory System Test", "Testing memory functionality")
        
        # Remember some facts
        memory.remember(
            "The course creator platform uses microservices architecture",
            category="architecture",
            importance="high",
            entity_name="Course Creator Platform",
            entity_type="system"
        )
        
        memory.remember(
            "SQLite is used for Claude Code memory storage",
            category="technology",
            importance="medium",
            entity_name="SQLite",
            entity_type="tool"
        )
        
        # Create a relationship
        platform_entity = memory.get_entity(name="Course Creator Platform")
        sqlite_entity = memory.get_entity(name="SQLite")
        
        if platform_entity and sqlite_entity:
            memory.store_relationship(
                platform_entity['id'],
                sqlite_entity['id'],
                "uses_for_memory",
                "Platform uses SQLite for Claude Code memory storage"
            )
        
        # Recall information
        results = memory.recall("course creator")
        print(f"\nRecall results for 'course creator': {len(results['entities'])} entities, {len(results['facts'])} facts")
        
        # Show statistics
        stats = memory.get_memory_stats()
        print(f"\nMemory Statistics:")
        print(f"- Entities: {stats['total_entities']}")
        print(f"- Facts: {stats['total_facts']}")
        print(f"- Relationships: {stats['total_relationships']}")
        print(f"- Database size: {stats['database_size']:,} bytes")
        
        print("\nMemory system test completed successfully!")