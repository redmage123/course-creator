-- CLAUDE CODE MEMORY SYSTEM DATABASE SCHEMA
--
-- BUSINESS REQUIREMENT:
-- Persistent memory system for Claude Code to store and retrieve contextual information
-- across conversations, maintaining entity relationships, facts, and conversation history.
--
-- TECHNICAL IMPLEMENTATION:
-- SQLite database with normalized tables for entities, facts, conversations, and relationships.
-- Optimized for Claude Code's tool-based access patterns with proper indexing.
--
-- WHY SQLITE:
-- - Zero configuration, single file database perfect for VM deployment
-- - Built-in Python support via sqlite3 module
-- - ACID compliance for data integrity
-- - Fast local I/O without network overhead
-- - Full SQL query capabilities for complex memory operations

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Conversations table - stores conversation sessions and context
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    context_summary TEXT,
    total_messages INTEGER DEFAULT 0,
    key_topics TEXT, -- JSON array of topics
    metadata TEXT -- JSON metadata
);

-- Entities table - stores people, systems, concepts, etc.
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('person', 'system', 'concept', 'file', 'project', 'organization', 'tool', 'other')),
    description TEXT,
    properties TEXT, -- JSON properties
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    source_conversation TEXT,
    FOREIGN KEY (source_conversation) REFERENCES conversations(id)
);

-- Facts table - stores discrete pieces of information
CREATE TABLE facts (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,
    importance TEXT DEFAULT 'medium' CHECK (importance IN ('critical', 'high', 'medium', 'low')),
    confidence REAL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    source TEXT,
    source_conversation TEXT,
    entity_id TEXT, -- Optional link to entity
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON metadata
    FOREIGN KEY (source_conversation) REFERENCES conversations(id),
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- Relationships table - stores connections between entities
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    strength REAL DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_conversation TEXT,
    metadata TEXT, -- JSON metadata
    FOREIGN KEY (from_entity) REFERENCES entities(id),
    FOREIGN KEY (to_entity) REFERENCES entities(id),
    FOREIGN KEY (source_conversation) REFERENCES conversations(id),
    UNIQUE(from_entity, to_entity, relationship_type)
);

-- Queries table - stores frequently used queries and patterns
CREATE TABLE queries (
    id TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_type TEXT DEFAULT 'search' CHECK (query_type IN ('search', 'fact', 'entity', 'relationship', 'context', 'recall')),
    frequency INTEGER DEFAULT 1,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    results_count INTEGER DEFAULT 0,
    metadata TEXT -- JSON metadata
);

-- Memory sessions table - tracks Claude Code usage sessions
CREATE TABLE memory_sessions (
    id TEXT PRIMARY KEY,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    total_operations INTEGER DEFAULT 0,
    conversation_id TEXT,
    context TEXT, -- What was being worked on
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Indexes for performance optimization
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_updated ON entities(last_updated DESC);
CREATE INDEX idx_facts_category ON facts(category);
CREATE INDEX idx_facts_importance ON facts(importance);
CREATE INDEX idx_facts_created ON facts(created_at DESC);
CREATE INDEX idx_facts_entity ON facts(entity_id);
CREATE INDEX idx_relationships_from ON relationships(from_entity);
CREATE INDEX idx_relationships_to ON relationships(to_entity);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_updated ON conversations(last_updated DESC);
CREATE INDEX idx_queries_type ON queries(query_type);
CREATE INDEX idx_queries_frequency ON queries(frequency DESC);

-- Views for common queries
CREATE VIEW recent_entities AS
SELECT e.*, c.title as conversation_title
FROM entities e
LEFT JOIN conversations c ON e.source_conversation = c.id
ORDER BY e.last_updated DESC;

CREATE VIEW important_facts AS
SELECT f.*, e.name as entity_name, c.title as conversation_title
FROM facts f
LEFT JOIN entities e ON f.entity_id = e.id
LEFT JOIN conversations c ON f.source_conversation = c.id
WHERE f.importance IN ('critical', 'high')
ORDER BY f.importance, f.created_at DESC;

CREATE VIEW entity_relationships AS
SELECT 
    r.id,
    e1.name as from_name,
    e1.type as from_type,
    r.relationship_type,
    e2.name as to_name,
    e2.type as to_type,
    r.strength,
    r.created_at
FROM relationships r
JOIN entities e1 ON r.from_entity = e1.id
JOIN entities e2 ON r.to_entity = e2.id
ORDER BY r.strength DESC;

-- Insert initial system metadata
INSERT INTO conversations (id, title, status, context_summary) 
VALUES ('system_init', 'System Initialization', 'active', 'Initial Claude Code memory system setup');

INSERT INTO entities (id, name, type, description, properties, source_conversation)
VALUES (
    'course_creator_platform',
    'Course Creator Platform',
    'system',
    'Educational platform with microservices architecture, RBAC, and lab containers',
    '{"version": "2.4.0", "services": 8, "has_rbac": true, "has_lab_containers": true, "uses_docker": true}',
    'system_init'
);

INSERT INTO facts (id, content, category, importance, source, entity_id, source_conversation)
VALUES 
(
    'absolute_imports_only',
    'All Python imports must be absolute imports only - no relative imports allowed',
    'development_standards',
    'critical',
    'CLAUDE.md',
    'course_creator_platform',
    'system_init'
),
(
    'session_timeouts',
    'Session timeouts configured: 8hr absolute, 2hr inactivity, 5min warning',
    'session_management',
    'high',
    'CLAUDE.md',
    'course_creator_platform',
    'system_init'
),
(
    'comprehensive_documentation',
    'All code must include multiline string documentation explaining what and why',
    'development_standards',
    'critical',
    'CLAUDE.md',
    'course_creator_platform',
    'system_init'
);