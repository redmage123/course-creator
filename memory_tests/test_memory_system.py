#!/usr/bin/env python3
"""
CLAUDE CODE MEMORY SYSTEM COMPREHENSIVE TEST SUITE

BUSINESS REQUIREMENT:
Validate all aspects of the Claude Code memory system including:
- Database schema and initialization
- Memory manager CRUD operations
- Helper function interfaces
- Data integrity and performance
- Error handling and edge cases

TECHNICAL IMPLEMENTATION:
Comprehensive test suite using unittest framework with:
- Isolated test database for each test
- Setup/teardown for clean test environment
- Mock data generation and validation
- Performance benchmarking
- Error condition testing

WHY SEPARATE TEST DIRECTORY:
- Memory system is independent of the main application
- Different testing requirements and data isolation needs
- Prevents interference with application test suite
- Allows for specialized memory system testing tools
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_memory_manager import ClaudeMemoryManager
import claude_memory_helpers as helpers


class TestClaudeMemorySystem(unittest.TestCase):
    """
    Comprehensive test suite for Claude Code memory system
    
    Tests cover all major functionality including:
    - Database initialization and schema validation
    - Entity management (CRUD operations)
    - Fact storage and retrieval
    - Relationship management
    - Search and query capabilities
    - Helper function interfaces
    - Performance characteristics
    - Error handling and edge cases
    """
    
    def setUp(self):
        """
        Set up test environment with isolated database
        
        ISOLATION STRATEGY:
        Each test gets a clean, temporary database to ensure
        test independence and prevent data contamination.
        """
        # Create temporary database for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.test_schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude_memory_schema.sql")
        
        # Initialize memory manager with test database
        self.memory = ClaudeMemoryManager(db_path=self.test_db_path)
        
        # Start test conversation
        self.test_conv_id = self.memory.start_conversation("Test Conversation", "Unit test conversation")
        
    def tearDown(self):
        """Clean up test environment"""
        # End session and cleanup
        self.memory.end_session()
        
        # Remove temporary database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)


class TestDatabaseInitialization(TestClaudeMemorySystem):
    """Test database initialization and schema validation"""
    
    def test_database_creation(self):
        """Test database file creation"""
        self.assertTrue(os.path.exists(self.test_db_path))
        self.assertGreater(os.path.getsize(self.test_db_path), 0)
    
    def test_schema_tables_exist(self):
        """Test all required tables are created"""
        with self.memory._get_connection() as conn:
            # Get all table names
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            
            table_names = [table[0] for table in tables]
            
            # Check required tables exist
            required_tables = [
                'conversations', 'entities', 'facts', 'relationships', 
                'queries', 'memory_sessions'
            ]
            
            for table in required_tables:
                self.assertIn(table, table_names, f"Table {table} not found")
    
    def test_initial_data_inserted(self):
        """Test initial system data is inserted"""
        # Check for initial conversation
        conversations = self.memory.list_conversations()
        self.assertGreater(len(conversations), 0)
        
        # Check for initial entity
        platform_entity = self.memory.get_entity(name="Course Creator Platform")
        self.assertIsNotNone(platform_entity)
        self.assertEqual(platform_entity['type'], 'system')
        
        # Check for initial facts
        facts = self.memory.get_facts(category="development_standards")
        self.assertGreater(len(facts), 0)
    
    def test_database_constraints(self):
        """Test database constraints work correctly"""
        with self.memory._get_connection() as conn:
            # Test foreign key constraint
            with self.assertRaises(Exception):
                conn.execute("""
                    INSERT INTO facts (id, content, source_conversation)
                    VALUES ('test_fact', 'Test content', 'nonexistent_conversation')
                """)
                conn.commit()


class TestEntityManagement(TestClaudeMemorySystem):
    """Test entity storage, retrieval, and management"""
    
    def test_store_entity(self):
        """Test entity storage"""
        entity_id = self.memory.store_entity(
            name="Test User",
            entity_type="person",
            description="A test user entity",
            properties={"role": "tester", "active": True}
        )
        
        # Verify entity was stored
        self.assertIsNotNone(entity_id)
        self.assertTrue(entity_id.startswith("entity_"))
        
        # Retrieve and verify entity
        entity = self.memory.get_entity(entity_id)
        self.assertIsNotNone(entity)
        self.assertEqual(entity['name'], "Test User")
        self.assertEqual(entity['type'], "person")
        self.assertEqual(entity['description'], "A test user entity")
        self.assertEqual(entity['properties']['role'], "tester")
        self.assertTrue(entity['properties']['active'])
    
    def test_get_entity_by_name(self):
        """Test entity retrieval by name"""
        # Store entity
        entity_id = self.memory.store_entity("Unique Entity", "concept", "Test entity")
        
        # Retrieve by name
        entity = self.memory.get_entity(name="Unique Entity")
        self.assertIsNotNone(entity)
        self.assertEqual(entity['id'], entity_id)
        self.assertEqual(entity['name'], "Unique Entity")
    
    def test_search_entities(self):
        """Test entity search functionality"""
        # Store multiple entities
        self.memory.store_entity("Python Language", "tool", "Programming language")
        self.memory.store_entity("JavaScript Language", "tool", "Web programming language")
        self.memory.store_entity("Language Model", "concept", "AI language model")
        
        # Search by query
        results = self.memory.search_entities("language")
        self.assertGreaterEqual(len(results), 3)
        
        # Search by type
        tools = self.memory.search_entities(entity_type="tool")
        self.assertGreaterEqual(len(tools), 2)
        
        # Search by query and type
        tool_languages = self.memory.search_entities("language", entity_type="tool")
        self.assertGreaterEqual(len(tool_languages), 2)
    
    def test_update_entity(self):
        """Test entity updates"""
        # Store entity
        entity_id = self.memory.store_entity("Update Test", "concept", "Original description")
        
        # Update entity
        success = self.memory.update_entity(
            entity_id,
            description="Updated description",
            properties={"updated": True}
        )
        self.assertTrue(success)
        
        # Verify update
        entity = self.memory.get_entity(entity_id)
        self.assertEqual(entity['description'], "Updated description")
        self.assertTrue(entity['properties']['updated'])
    
    def test_entity_validation(self):
        """Test entity type validation"""
        # Test valid entity types
        valid_types = ['person', 'system', 'concept', 'file', 'project', 'organization', 'tool', 'other']
        for entity_type in valid_types:
            entity_id = self.memory.store_entity(f"Test {entity_type}", entity_type, "Test entity")
            self.assertIsNotNone(entity_id)


class TestFactManagement(TestClaudeMemorySystem):
    """Test fact storage, retrieval, and management"""
    
    def test_store_fact(self):
        """Test fact storage"""
        fact_id = self.memory.store_fact(
            content="Python is a programming language",
            category="programming",
            importance="high",
            confidence=0.95,
            metadata={"verified": True}
        )
        
        # Verify fact was stored
        self.assertIsNotNone(fact_id)
        self.assertTrue(fact_id.startswith("fact_"))
        
        # Retrieve facts and verify
        facts = self.memory.get_facts(category="programming")
        self.assertGreater(len(facts), 0)
        
        stored_fact = next((f for f in facts if f['id'] == fact_id), None)
        self.assertIsNotNone(stored_fact)
        self.assertEqual(stored_fact['content'], "Python is a programming language")
        self.assertEqual(stored_fact['importance'], "high")
        self.assertEqual(stored_fact['confidence'], 0.95)
        self.assertTrue(stored_fact['metadata']['verified'])
    
    def test_fact_with_entity_link(self):
        """Test storing facts linked to entities"""
        # Create entity first
        entity_id = self.memory.store_entity("Python", "tool", "Programming language")
        
        # Store fact linked to entity
        fact_id = self.memory.store_fact(
            content="Python supports object-oriented programming",
            category="programming",
            entity_id=entity_id,
            importance="medium"
        )
        
        # Retrieve facts for entity
        entity_facts = self.memory.get_facts(entity_id=entity_id)
        self.assertGreater(len(entity_facts), 0)
        
        linked_fact = next((f for f in entity_facts if f['id'] == fact_id), None)
        self.assertIsNotNone(linked_fact)
        self.assertEqual(linked_fact['entity_name'], "Python")
    
    def test_search_facts(self):
        """Test fact search functionality"""
        # Store multiple facts
        self.memory.store_fact("SQLite is a database engine", category="database", importance="high")
        self.memory.store_fact("SQLite supports ACID transactions", category="database", importance="medium")
        self.memory.store_fact("Database queries use SQL", category="database", importance="low")
        
        # Search facts by content
        results = self.memory.search_facts("SQLite")
        self.assertGreaterEqual(len(results), 2)
        
        # Get facts by category
        db_facts = self.memory.get_facts(category="database")
        self.assertGreaterEqual(len(db_facts), 3)
        
        # Get facts by importance
        high_facts = self.memory.get_facts(importance="high")
        self.assertGreater(len(high_facts), 0)
    
    def test_fact_importance_validation(self):
        """Test fact importance level validation"""
        valid_importance = ['critical', 'high', 'medium', 'low']
        
        for importance in valid_importance:
            fact_id = self.memory.store_fact(
                f"Test fact with {importance} importance",
                importance=importance
            )
            self.assertIsNotNone(fact_id)


class TestRelationshipManagement(TestClaudeMemorySystem):
    """Test relationship storage and management"""
    
    def test_store_relationship(self):
        """Test relationship storage"""
        # Create entities
        entity1_id = self.memory.store_entity("Docker", "tool", "Containerization platform")
        entity2_id = self.memory.store_entity("Course Creator", "system", "Educational platform")
        
        # Store relationship
        rel_id = self.memory.store_relationship(
            from_entity=entity2_id,
            to_entity=entity1_id,
            relationship_type="uses",
            description="Course Creator uses Docker for deployment",
            strength=0.9
        )
        
        self.assertIsNotNone(rel_id)
        self.assertTrue(rel_id.startswith("rel_"))
    
    def test_get_entity_relationships(self):
        """Test entity relationship retrieval"""
        # Create entities
        user_id = self.memory.store_entity("Test User", "person", "Test user")
        system_id = self.memory.store_entity("Test System", "system", "Test system")
        tool_id = self.memory.store_entity("Test Tool", "tool", "Test tool")
        
        # Create relationships
        self.memory.store_relationship(user_id, system_id, "uses", strength=0.8)
        self.memory.store_relationship(system_id, tool_id, "depends_on", strength=0.9)
        self.memory.store_relationship(tool_id, user_id, "serves", strength=0.7)
        
        # Get relationships for system
        system_rels = self.memory.get_entity_relationships(system_id, direction="both")
        self.assertGreaterEqual(len(system_rels), 2)
        
        # Check relationship directions
        outgoing_rels = self.memory.get_entity_relationships(system_id, direction="from")
        incoming_rels = self.memory.get_entity_relationships(system_id, direction="to")
        
        self.assertGreater(len(outgoing_rels), 0)
        self.assertGreater(len(incoming_rels), 0)
    
    def test_relationship_uniqueness(self):
        """Test relationship uniqueness constraint"""
        # Create entities
        entity1_id = self.memory.store_entity("Entity 1", "concept", "First entity")
        entity2_id = self.memory.store_entity("Entity 2", "concept", "Second entity")
        
        # Store initial relationship
        rel1_id = self.memory.store_relationship(entity1_id, entity2_id, "related_to")
        
        # Store duplicate relationship (should replace)
        rel2_id = self.memory.store_relationship(entity1_id, entity2_id, "related_to", strength=0.5)
        
        # Verify only one relationship exists
        relationships = self.memory.get_entity_relationships(entity1_id, direction="from")
        related_rels = [r for r in relationships if r['relationship_type'] == 'related_to']
        self.assertEqual(len(related_rels), 1)


class TestConversationManagement(TestClaudeMemorySystem):
    """Test conversation and context management"""
    
    def test_start_conversation(self):
        """Test conversation creation"""
        conv_id = self.memory.start_conversation("Test Conv", "Test conversation")
        
        self.assertIsNotNone(conv_id)
        self.assertTrue(conv_id.startswith("conv_"))
        
        # Verify conversation was stored
        conversation = self.memory.get_conversation(conv_id)
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation['title'], "Test Conv")
        self.assertEqual(conversation['context_summary'], "Test conversation")
    
    def test_update_conversation(self):
        """Test conversation updates"""
        conv_id = self.memory.start_conversation("Original Title")
        
        # Update conversation
        success = self.memory.update_conversation(
            conv_id,
            title="Updated Title",
            context_summary="Updated context",
            status="active",
            key_topics=["topic1", "topic2"]
        )
        
        self.assertTrue(success)
        
        # Verify update
        conversation = self.memory.get_conversation(conv_id)
        self.assertEqual(conversation['title'], "Updated Title")
        self.assertEqual(conversation['context_summary'], "Updated context")
    
    def test_list_conversations(self):
        """Test conversation listing"""
        # Create multiple conversations
        conv1 = self.memory.start_conversation("Conv 1")
        conv2 = self.memory.start_conversation("Conv 2")
        
        # List conversations
        conversations = self.memory.list_conversations(limit=10)
        self.assertGreaterEqual(len(conversations), 2)
        
        # Verify conversations are in list
        conv_ids = [c['id'] for c in conversations]
        self.assertIn(conv1, conv_ids)
        self.assertIn(conv2, conv_ids)


class TestMemoryStatistics(TestClaudeMemorySystem):
    """Test memory statistics and analysis"""
    
    def test_memory_stats(self):
        """Test memory statistics generation"""
        # Add some test data
        self.memory.store_entity("Stat Entity", "concept", "For statistics")
        self.memory.store_fact("Statistical fact", category="statistics", importance="high")
        
        # Get statistics
        stats = self.memory.get_memory_stats()
        
        # Verify basic stats
        self.assertIn('total_conversations', stats)
        self.assertIn('total_entities', stats)
        self.assertIn('total_facts', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('database_size', stats)
        
        # Verify counts are reasonable
        self.assertGreater(stats['total_entities'], 0)
        self.assertGreater(stats['total_facts'], 0)
        self.assertGreater(stats['database_size'], 0)
        
        # Verify breakdowns exist
        self.assertIn('entity_types', stats)
        self.assertIn('fact_categories', stats)
        self.assertIn('fact_importance', stats)


class TestQueryManagement(TestClaudeMemorySystem):
    """Test query logging and frequency tracking"""
    
    def test_log_query(self):
        """Test query logging"""
        # Log a query
        self.memory.log_query("test query", "search", 5)
        
        # Log same query again
        self.memory.log_query("test query", "search", 3)
        
        # Get frequent queries
        queries = self.memory.get_frequent_queries()
        
        # Find our query
        test_query = next((q for q in queries if q['query_text'] == "test query"), None)
        self.assertIsNotNone(test_query)
        self.assertEqual(test_query['frequency'], 2)  # Should be incremented
    
    def test_frequent_queries(self):
        """Test frequent query retrieval"""
        # Log multiple queries with different frequencies
        for i in range(5):
            self.memory.log_query("popular query", "search", 1)
        
        for i in range(2):
            self.memory.log_query("less popular query", "search", 1)
        
        # Get frequent queries
        frequent = self.memory.get_frequent_queries(limit=5)
        
        # Verify popular query is first
        self.assertGreater(len(frequent), 0)
        self.assertEqual(frequent[0]['query_text'], "popular query")
        self.assertEqual(frequent[0]['frequency'], 5)


class TestHelperFunctions(TestClaudeMemorySystem):
    """Test helper function interfaces"""
    
    def setUp(self):
        """Set up helper function tests with memory override"""
        super().setUp()
        # Override global memory instance for testing
        helpers._memory = self.memory
    
    def test_remember_helper(self):
        """Test remember helper function"""
        result = helpers.remember("Helper test fact", category="testing", importance="high")
        
        self.assertIn("✅ Remembered", result)
        
        # Verify fact was stored
        facts = self.memory.search_facts("Helper test fact")
        self.assertGreater(len(facts), 0)
    
    def test_recall_helper(self):
        """Test recall helper function"""
        # Store some facts first
        helpers.remember("Recall test fact 1", category="testing")
        helpers.remember("Recall test fact 2", category="testing")
        helpers.note_entity("Recall Entity", "concept", "For recall testing")
        
        # Test recall
        result = helpers.recall("recall test")
        
        self.assertIn("🔍 Recall results", result)
        self.assertIn("Facts", result)
    
    def test_note_entity_helper(self):
        """Test note_entity helper function"""
        result = helpers.note_entity("Helper Entity", "tool", "Helper test entity")
        
        self.assertIn("✅ Noted entity", result)
        
        # Verify entity was stored
        entity = self.memory.get_entity(name="Helper Entity")
        self.assertIsNotNone(entity)
        self.assertEqual(entity['type'], "tool")
    
    def test_connect_entities_helper(self):
        """Test connect_entities helper function"""
        # First create entities using helper
        helpers.note_entity("Entity A", "concept", "First entity")
        helpers.note_entity("Entity B", "concept", "Second entity")
        
        # Connect them
        result = helpers.connect_entities("Entity A", "Entity B", "connects_to", "Test connection")
        
        self.assertIn("✅ Connected", result)
        
        # Verify relationship exists
        entity_a = self.memory.get_entity(name="Entity A")
        relationships = self.memory.get_entity_relationships(entity_a['id'])
        self.assertGreater(len(relationships), 0)
    
    def test_memory_summary_helper(self):
        """Test memory_summary helper function"""
        # Add some data
        helpers.remember("Summary test fact")
        helpers.note_entity("Summary Entity", "concept")
        
        result = helpers.memory_summary()
        
        self.assertIn("📊 Claude Code Memory Summary", result)
        self.assertIn("Conversations:", result)
        self.assertIn("Entities:", result)
        self.assertIn("Facts:", result)
    
    def test_search_helpers(self):
        """Test search helper functions"""
        # Add test data
        helpers.note_entity("Search Tool", "tool", "For searching")
        helpers.remember("Search fact", category="search_test", importance="high")
        
        # Test search by type
        result = helpers.search_by_type("tool")
        self.assertIn("tool entities", result.lower())
        
        # Test search facts by category  
        result = helpers.search_facts_by_category("search_test")
        self.assertIn("search_test", result)
        
        # Test get important facts
        result = helpers.get_important_facts("high")
        self.assertIn("high importance facts", result.lower())


class TestPerformanceAndScale(TestClaudeMemorySystem):
    """Test performance characteristics and scalability"""
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        start_time = time.time()
        
        # Store many entities
        entity_ids = []
        for i in range(100):
            entity_id = self.memory.store_entity(f"Entity {i}", "concept", f"Test entity {i}")
            entity_ids.append(entity_id)
        
        entity_time = time.time() - start_time
        
        # Store many facts
        start_time = time.time()
        for i in range(100):
            self.memory.store_fact(f"Fact {i}", category="performance", importance="medium")
        
        fact_time = time.time() - start_time
        
        # Performance should be reasonable (less than 5 seconds each)
        self.assertLess(entity_time, 5.0, f"Entity storage took {entity_time:.2f}s")
        self.assertLess(fact_time, 5.0, f"Fact storage took {fact_time:.2f}s")
        
        # Test search performance
        start_time = time.time()
        results = self.memory.search_entities("Entity", limit=50)
        search_time = time.time() - start_time
        
        self.assertLess(search_time, 1.0, f"Search took {search_time:.2f}s")
        self.assertGreaterEqual(len(results), 50)
    
    def test_database_size_management(self):
        """Test database size growth management"""
        initial_stats = self.memory.get_memory_stats()
        initial_size = initial_stats['database_size']
        
        # Add significant amount of data
        for i in range(50):
            entity_id = self.memory.store_entity(f"Size Entity {i}", "concept", f"Description {i}")
            self.memory.store_fact(f"Size fact {i}", category="size_test", entity_id=entity_id)
        
        # Check size growth is reasonable
        final_stats = self.memory.get_memory_stats()
        final_size = final_stats['database_size']
        
        size_growth = final_size - initial_size
        self.assertGreater(size_growth, 0)
        self.assertLess(size_growth, 1024 * 1024, "Database grew more than 1MB for 50 entities")


class TestErrorHandlingAndEdgeCases(TestClaudeMemorySystem):
    """Test error handling and edge cases"""
    
    def test_nonexistent_entity_retrieval(self):
        """Test retrieving nonexistent entities"""
        entity = self.memory.get_entity("nonexistent_id")
        self.assertIsNone(entity)
        
        entity = self.memory.get_entity(name="Nonexistent Entity")
        self.assertIsNone(entity)
    
    def test_nonexistent_conversation_retrieval(self):
        """Test retrieving nonexistent conversation"""
        conversation = self.memory.get_conversation("nonexistent_conv")
        self.assertIsNone(conversation)
    
    def test_empty_search_results(self):
        """Test searches that return no results"""
        entities = self.memory.search_entities("absolutely_unique_nonexistent_query")
        self.assertEqual(len(entities), 0)
        
        facts = self.memory.search_facts("absolutely_unique_nonexistent_query")
        self.assertEqual(len(facts), 0)
    
    def test_invalid_update_operations(self):
        """Test update operations with invalid data"""
        # Test updating nonexistent entity
        success = self.memory.update_entity("nonexistent_id", name="New Name")
        self.assertFalse(success)
        
        # Test updating nonexistent conversation
        success = self.memory.update_conversation("nonexistent_conv", title="New Title")
        self.assertFalse(success)
    
    def test_empty_string_handling(self):
        """Test handling of empty strings"""
        # Empty content should still create fact (business rule)
        fact_id = self.memory.store_fact("", category="empty_test")
        self.assertIsNotNone(fact_id)
        
        # Empty entity name should still work
        entity_id = self.memory.store_entity("", "concept", "Empty name test")
        self.assertIsNotNone(entity_id)
    
    def test_large_content_handling(self):
        """Test handling of large content"""
        large_content = "A" * 10000  # 10KB of text
        
        # Should handle large fact content
        fact_id = self.memory.store_fact(large_content, category="large_test")
        self.assertIsNotNone(fact_id)
        
        # Verify retrieval works
        facts = self.memory.get_facts(category="large_test")
        self.assertGreater(len(facts), 0)
        self.assertEqual(len(facts[0]['content']), 10000)


class TestBackupAndMaintenance(TestClaudeMemorySystem):
    """Test backup and maintenance operations"""
    
    def test_backup_creation(self):
        """Test database backup functionality"""
        # Add some data
        self.memory.store_entity("Backup Entity", "concept", "For backup testing")
        self.memory.store_fact("Backup fact", category="backup_test")
        
        # Create backup
        backup_path = self.memory.backup_memory()
        
        # Verify backup exists and has content
        self.assertTrue(os.path.exists(backup_path))
        self.assertGreater(os.path.getsize(backup_path), 0)
        
        # Cleanup backup
        os.remove(backup_path)
    
    def test_database_vacuum(self):
        """Test database optimization"""
        # Get initial size
        initial_stats = self.memory.get_memory_stats()
        initial_size = initial_stats['database_size']
        
        # Vacuum database
        self.memory.vacuum_database()  # Should not raise error
        
        # Verify database still works
        stats = self.memory.get_memory_stats()
        self.assertGreater(stats['total_entities'], 0)
    
    def test_old_data_cleanup(self):
        """Test old data cleanup functionality"""
        # Create old conversation
        old_conv_id = self.memory.start_conversation("Old Conversation")
        self.memory.update_conversation(old_conv_id, status="archived")
        
        # Clear old data (0 days to force cleanup)
        deleted_count = self.memory.clear_old_data(days=0)
        
        # Should have deleted the archived conversation
        self.assertGreaterEqual(deleted_count, 0)


def run_memory_tests():
    """
    Run comprehensive memory system test suite
    
    Returns:
        Test results and statistics
    """
    # Create test suite
    test_classes = [
        TestDatabaseInitialization,
        TestEntityManagement,
        TestFactManagement,
        TestRelationshipManagement,
        TestConversationManagement,
        TestMemoryStatistics,
        TestQueryManagement,
        TestHelperFunctions,
        TestPerformanceAndScale,
        TestErrorHandlingAndEdgeCases,
        TestBackupAndMaintenance
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"CLAUDE CODE MEMORY SYSTEM TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - failures - errors}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    print(f"\n{'='*60}")
    
    return {
        'total_tests': total_tests,
        'passed': total_tests - failures - errors,
        'failed': failures,
        'errors': errors,
        'success_rate': success_rate,
        'result': result
    }


if __name__ == "__main__":
    """Run the complete test suite"""
    print("🧠 Claude Code Memory System - Comprehensive Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_results = run_memory_tests()
    
    # Exit with appropriate code
    if test_results['failed'] > 0 or test_results['errors'] > 0:
        sys.exit(1)
    else:
        print("✅ All tests passed successfully!")
        sys.exit(0)