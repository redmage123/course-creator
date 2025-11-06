"""
Pytest configuration for metadata and search tests

BUSINESS PURPOSE:
- Provides database connection for tag verification
- Sets up metadata test environment
- Manages test data cleanup
- Provides common fixtures for search testing
"""

import pytest
import os
import psycopg2
import json
from datetime import datetime


@pytest.fixture(scope="session")
def db_connection():
    """
    Provides PostgreSQL database connection for metadata verification
    
    BUSINESS REQUIREMENT:
    Tests must verify course tags (JSONB column), search_analytics table,
    and tag hierarchy relationships.
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5433')),
        database=os.getenv('DB_NAME', 'course_creator'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres_password')
    )
    yield conn
    conn.close()


@pytest.fixture
def cleanup_test_tags(db_connection):
    """
    Cleanup test tags after each test
    
    BUSINESS REQUIREMENT:
    Prevents test data pollution affecting production or other tests.
    """
    yield
    
    # Cleanup courses with test tags
    cursor = db_connection.cursor()
    cursor.execute("""
        UPDATE courses 
        SET tags = '{}'::jsonb
        WHERE title LIKE '%Test Course%'
    """)
    db_connection.commit()
    cursor.close()


@pytest.fixture
def test_instructor_credentials():
    """
    Provides test instructor credentials for tag management
    
    BUSINESS REQUIREMENT:
    Tag management is restricted to instructors and admins.
    """
    return {
        'email': 'instructor@example.com',
        'password': 'InstructorPass123!',
        'instructor_id': 'test_instructor_001',
        'organization_id': 'test_org_001'
    }


@pytest.fixture
def test_admin_credentials():
    """
    Provides test admin credentials for tag analytics
    
    BUSINESS REQUIREMENT:
    Tag analytics dashboard requires admin privileges.
    """
    return {
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'admin_id': 'test_admin_001',
        'organization_id': 'test_org_001'
    }


@pytest.fixture
def sample_tags():
    """
    Provides sample tag sets for testing
    
    BUSINESS REQUIREMENT:
    Common tag categories for course metadata.
    """
    return {
        'skills': [
            'Python', 'Java', 'JavaScript', 'SQL', 'Docker',
            'Kubernetes', 'AWS', 'Machine Learning', 'Data Analysis'
        ],
        'topics': [
            'Programming', 'DevOps', 'Cloud Computing', 'Data Science',
            'Web Development', 'Mobile Development', 'AI', 'Security'
        ],
        'difficulty': [
            'Beginner', 'Intermediate', 'Advanced', 'Expert'
        ]
    }


@pytest.fixture
def tag_hierarchy_structure():
    """
    Provides sample tag hierarchy for testing
    
    BUSINESS REQUIREMENT:
    Tags can have parent-child relationships for organization.
    """
    return {
        'Programming': {
            'children': ['Python', 'Java', 'JavaScript', 'Go']
        },
        'Data Science': {
            'children': ['Machine Learning', 'Data Analysis', 'Statistics']
        },
        'Cloud Computing': {
            'children': ['AWS', 'Azure', 'GCP', 'Kubernetes', 'Docker']
        }
    }


@pytest.fixture
def search_analytics_helper(db_connection):
    """
    Helper to create search analytics data for testing
    
    BUSINESS REQUIREMENT:
    Tag effectiveness measured via search analytics (CTR).
    """
    def create_search_analytics(tag_value, searches, clicks):
        """
        Create search analytics records for tag
        
        Args:
            tag_value: Tag to create analytics for
            searches: Number of searches
            clicks: Number of clicks (must be <= searches)
        """
        cursor = db_connection.cursor()
        for i in range(searches):
            clicked = i < clicks  # First N are clicked
            cursor.execute("""
                INSERT INTO search_analytics 
                (search_query, tags_used, clicked, search_timestamp)
                VALUES (%s, %s, %s, NOW())
            """, (
                f"search for {tag_value}",
                json.dumps([tag_value]),
                clicked
            ))
        db_connection.commit()
        cursor.close()
    
    return create_search_analytics
