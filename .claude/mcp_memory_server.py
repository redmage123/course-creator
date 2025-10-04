#!/usr/bin/env python3
"""
Custom MCP Memory Server for Course Creator Platform
Provides persistent memory capabilities for Claude Code with file caching
"""

import asyncio
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP Server implementation
class MCPMemoryServer:
    """Memory server using Model Context Protocol"""

    def __init__(self, db_path: str = ".claude/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize SQLite database with memory schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Facts table - stores key information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                importance TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Entities table - tracks systems, people, files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                entity_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Relationships table - connections between entities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_name TEXT NOT NULL,
                entity2_name TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity1_name) REFERENCES entities(name),
                FOREIGN KEY (entity2_name) REFERENCES entities(name)
            )
        """)

        # Contexts table - conversation contexts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # File cache table - stores file contents with metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                file_size INTEGER,
                last_modified TIMESTAMP,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_content ON facts(content)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_cache_path ON file_cache(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_cache_hash ON file_cache(content_hash)")

        self.conn.commit()

    def remember(self, content: str, category: str = "general", importance: str = "medium") -> int:
        """Store a fact in memory"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO facts (content, category, importance) VALUES (?, ?, ?)",
            (content, category, importance)
        )
        self.conn.commit()
        return cursor.lastrowid

    def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall facts matching the query"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, category, importance, created_at
            FROM facts
            WHERE content LIKE ?
            ORDER BY
                CASE importance
                    WHEN 'critical' THEN 4
                    WHEN 'high' THEN 3
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 1
                END DESC,
                created_at DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "category": row[2],
                "importance": row[3],
                "created_at": row[4]
            })
        return results

    def note_entity(self, name: str, entity_type: str, description: str = "") -> int:
        """Track an entity (person, system, concept, file)"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO entities (name, entity_type, description) VALUES (?, ?, ?)",
                (name, entity_type, description)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Entity already exists, update it
            cursor.execute(
                "UPDATE entities SET entity_type = ?, description = ? WHERE name = ?",
                (entity_type, description, name)
            )
            self.conn.commit()
            return cursor.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()[0]

    def connect_entities(self, entity1: str, entity2: str, relationship: str, description: str = ""):
        """Create a relationship between entities"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO relationships (entity1_name, entity2_name, relationship_type, description)
            VALUES (?, ?, ?, ?)
        """, (entity1, entity2, relationship, description))
        self.conn.commit()
        return cursor.lastrowid

    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get all entities of a specific type"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, entity_type, description FROM entities WHERE entity_type = ?",
            (entity_type,)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "description": row[3]
            })
        return results

    def get_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entity2_name, relationship_type, description
            FROM relationships
            WHERE entity1_name = ?
            UNION
            SELECT entity1_name, relationship_type, description
            FROM relationships
            WHERE entity2_name = ?
        """, (entity_name, entity_name))

        results = []
        for row in cursor.fetchall():
            results.append({
                "related_entity": row[0],
                "relationship": row[1],
                "description": row[2]
            })
        return results

    def start_context(self, name: str, description: str = "") -> int:
        """Start a new conversation context"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO contexts (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def cache_file(self, file_path: str, content: str) -> int:
        """Cache file content in memory with metadata"""
        cursor = self.conn.cursor()

        # Calculate content hash for change detection
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Get file stats if it exists on disk
        file_size = len(content.encode('utf-8'))
        last_modified = None

        try:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                last_modified = datetime.fromtimestamp(stat_info.st_mtime)
        except (OSError, IOError):
            pass

        cursor.execute("""
            INSERT OR REPLACE INTO file_cache
            (file_path, content, content_hash, file_size, last_modified, cached_at, access_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, datetime('now'),
                    COALESCE((SELECT access_count FROM file_cache WHERE file_path = ?), 0),
                    datetime('now'))
        """, (file_path, content, content_hash, file_size, last_modified, file_path))

        self.conn.commit()
        return cursor.lastrowid

    def get_cached_file(self, file_path: str, check_freshness: bool = True) -> Optional[Dict[str, Any]]:
        """Get cached file if it exists and is fresh"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT content, content_hash, file_size, last_modified, cached_at, access_count
            FROM file_cache
            WHERE file_path = ?
        """, (file_path,))

        row = cursor.fetchone()
        if not row:
            return None

        cached_content = row[0]
        cached_hash = row[1]

        # Check if file has changed on disk
        if check_freshness and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                current_hash = hashlib.sha256(current_content.encode('utf-8')).hexdigest()

                if current_hash != cached_hash:
                    # File changed, update cache
                    self.cache_file(file_path, current_content)
                    cached_content = current_content
            except (OSError, IOError, UnicodeDecodeError):
                # Can't read file, return cached version
                pass

        # Update access stats
        cursor.execute("""
            UPDATE file_cache
            SET access_count = access_count + 1, last_accessed = datetime('now')
            WHERE file_path = ?
        """, (file_path,))
        self.conn.commit()

        return {
            "content": cached_content,
            "hash": cached_hash,
            "size": row[2],
            "last_modified": row[3],
            "cached_at": row[4],
            "access_count": row[5] + 1
        }

    def invalidate_cache(self, file_path: str) -> bool:
        """Remove a file from cache"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_old_cache(self, days: int = 7) -> int:
        """Clear cache entries older than specified days"""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM file_cache
            WHERE last_accessed < datetime('now', '-' || ? || ' days')
        """, (days,))
        self.conn.commit()
        return cursor.rowcount

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get file cache statistics"""
        cursor = self.conn.cursor()

        stats = {}
        stats["total_cached_files"] = cursor.execute("SELECT COUNT(*) FROM file_cache").fetchone()[0]

        cursor.execute("SELECT SUM(file_size) FROM file_cache")
        total_size = cursor.fetchone()[0] or 0
        stats["total_cache_size_bytes"] = total_size
        stats["total_cache_size_mb"] = round(total_size / (1024 * 1024), 2)

        cursor.execute("SELECT SUM(access_count) FROM file_cache")
        stats["total_accesses"] = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT file_path, access_count
            FROM file_cache
            ORDER BY access_count DESC
            LIMIT 5
        """)
        stats["most_accessed"] = [{"path": row[0], "accesses": row[1]} for row in cursor.fetchall()]

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        cursor = self.conn.cursor()

        stats = {}
        stats["total_facts"] = cursor.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        stats["total_entities"] = cursor.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        stats["total_relationships"] = cursor.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        stats["total_contexts"] = cursor.execute("SELECT COUNT(*) FROM contexts").fetchone()[0]

        # Category breakdown
        cursor.execute("SELECT category, COUNT(*) FROM facts GROUP BY category")
        stats["facts_by_category"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Entity type breakdown
        cursor.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
        stats["entities_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Add cache stats
        stats["cache"] = self.get_cache_stats()

        return stats

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# MCP Protocol Handler
async def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP protocol requests"""
    memory = MCPMemoryServer()

    method = request.get("method")
    params = request.get("params", {})

    try:
        if method == "remember":
            fact_id = memory.remember(
                params["content"],
                params.get("category", "general"),
                params.get("importance", "medium")
            )
            return {"success": True, "fact_id": fact_id}

        elif method == "recall":
            results = memory.recall(
                params["query"],
                params.get("limit", 10)
            )
            return {"success": True, "results": results}

        elif method == "note_entity":
            entity_id = memory.note_entity(
                params["name"],
                params["entity_type"],
                params.get("description", "")
            )
            return {"success": True, "entity_id": entity_id}

        elif method == "connect_entities":
            rel_id = memory.connect_entities(
                params["entity1"],
                params["entity2"],
                params["relationship"],
                params.get("description", "")
            )
            return {"success": True, "relationship_id": rel_id}

        elif method == "get_entities_by_type":
            entities = memory.get_entities_by_type(params["entity_type"])
            return {"success": True, "entities": entities}

        elif method == "get_relationships":
            relationships = memory.get_relationships(params["entity_name"])
            return {"success": True, "relationships": relationships}

        elif method == "start_context":
            context_id = memory.start_context(
                params["name"],
                params.get("description", "")
            )
            return {"success": True, "context_id": context_id}

        elif method == "get_statistics":
            stats = memory.get_statistics()
            return {"success": True, "statistics": stats}

        elif method == "cache_file":
            file_id = memory.cache_file(
                params["file_path"],
                params["content"]
            )
            return {"success": True, "file_id": file_id}

        elif method == "get_cached_file":
            cached = memory.get_cached_file(
                params["file_path"],
                params.get("check_freshness", True)
            )
            if cached:
                return {"success": True, "cached_file": cached}
            else:
                return {"success": False, "error": "File not in cache"}

        elif method == "invalidate_cache":
            invalidated = memory.invalidate_cache(params["file_path"])
            return {"success": True, "invalidated": invalidated}

        elif method == "clear_old_cache":
            cleared = memory.clear_old_cache(params.get("days", 7))
            return {"success": True, "cleared_count": cleared}

        elif method == "get_cache_stats":
            cache_stats = memory.get_cache_stats()
            return {"success": True, "cache_stats": cache_stats}

        else:
            return {"success": False, "error": f"Unknown method: {method}"}

    finally:
        memory.close()


# Simple CLI for testing
if __name__ == "__main__":
    import sys

    memory = MCPMemoryServer()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Remember: python mcp_memory_server.py remember 'fact' [category] [importance]")
        print("  Recall: python mcp_memory_server.py recall 'query'")
        print("  Entity: python mcp_memory_server.py entity 'name' 'type' 'description'")
        print("  Cache: python mcp_memory_server.py cache 'file_path'")
        print("  Get Cache: python mcp_memory_server.py get-cache 'file_path'")
        print("  Cache Stats: python mcp_memory_server.py cache-stats")
        print("  Clear Old: python mcp_memory_server.py clear-cache [days]")
        print("  Stats: python mcp_memory_server.py stats")
        sys.exit(1)

    command = sys.argv[1]

    if command == "remember":
        if len(sys.argv) < 3:
            print("Error: content required")
            sys.exit(1)
        content = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else "general"
        importance = sys.argv[4] if len(sys.argv) > 4 else "medium"
        fact_id = memory.remember(content, category, importance)
        print(f"✅ Stored fact with ID: {fact_id}")

    elif command == "recall":
        if len(sys.argv) < 3:
            print("Error: query required")
            sys.exit(1)
        query = sys.argv[2]
        results = memory.recall(query)
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"  [{result['importance']}] {result['content']}")

    elif command == "entity":
        if len(sys.argv) < 5:
            print("Error: name, type, and description required")
            sys.exit(1)
        name = sys.argv[2]
        entity_type = sys.argv[3]
        description = sys.argv[4]
        entity_id = memory.note_entity(name, entity_type, description)
        print(f"✅ Created/updated entity with ID: {entity_id}")

    elif command == "cache":
        if len(sys.argv) < 3:
            print("Error: file_path required")
            sys.exit(1)
        file_path = sys.argv[2]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_id = memory.cache_file(file_path, content)
            print(f"✅ Cached file with ID: {file_id}")
            print(f"   Size: {len(content.encode('utf-8'))} bytes")
        except Exception as e:
            print(f"❌ Error caching file: {e}")

    elif command == "get-cache":
        if len(sys.argv) < 3:
            print("Error: file_path required")
            sys.exit(1)
        file_path = sys.argv[2]
        cached = memory.get_cached_file(file_path)
        if cached:
            print(f"✅ Found cached file:")
            print(f"   Size: {cached['size']} bytes")
            print(f"   Hash: {cached['hash'][:16]}...")
            print(f"   Cached: {cached['cached_at']}")
            print(f"   Accesses: {cached['access_count']}")
            print(f"\n   Content preview (first 200 chars):")
            print(f"   {cached['content'][:200]}...")
        else:
            print(f"❌ File not in cache: {file_path}")

    elif command == "cache-stats":
        cache_stats = memory.get_cache_stats()
        print("📦 File Cache Statistics:")
        print(f"  Total cached files: {cache_stats['total_cached_files']}")
        print(f"  Total size: {cache_stats['total_cache_size_mb']} MB ({cache_stats['total_cache_size_bytes']} bytes)")
        print(f"  Total accesses: {cache_stats['total_accesses']}")
        if cache_stats['most_accessed']:
            print("\n  Most accessed files:")
            for item in cache_stats['most_accessed']:
                print(f"    {item['path']}: {item['accesses']} accesses")

    elif command == "clear-cache":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cleared = memory.clear_old_cache(days)
        print(f"🗑️  Cleared {cleared} cache entries older than {days} days")

    elif command == "stats":
        stats = memory.get_statistics()
        print("📊 Memory Statistics:")
        print(f"  Total facts: {stats['total_facts']}")
        print(f"  Total entities: {stats['total_entities']}")
        print(f"  Total relationships: {stats['total_relationships']}")
        print(f"  Total contexts: {stats['total_contexts']}")

        if stats['facts_by_category']:
            print("\n  Facts by category:")
            for category, count in stats['facts_by_category'].items():
                print(f"    {category}: {count}")

        if stats['entities_by_type']:
            print("\n  Entities by type:")
            for entity_type, count in stats['entities_by_type'].items():
                print(f"    {entity_type}: {count}")

        # Show cache stats
        cache = stats.get('cache', {})
        if cache.get('total_cached_files', 0) > 0:
            print("\n  File Cache:")
            print(f"    Cached files: {cache['total_cached_files']}")
            print(f"    Cache size: {cache['total_cache_size_mb']} MB")
            print(f"    Total accesses: {cache['total_accesses']}")

    else:
        print(f"Unknown command: {command}")

    memory.close()
