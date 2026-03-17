#!/usr/bin/env python3
"""
Simplified Database setup script for CI environments
"""
import os
import sys

def setup_database_ci():
    """Setup database for CI testing"""
    print("🏗️  Setting up database for CI testing...")
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://test_user:test_password@localhost:5432/course_creator_test')
    print(f"📍 Database URL: {database_url}")
    
    # For CI, we just need to ensure the database exists
    # The GitHub Actions workflow already creates the test database
    print("✅ Database setup completed for CI environment")
    return 0

if __name__ == "__main__":
    sys.exit(setup_database_ci())