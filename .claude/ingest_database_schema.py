#!/usr/bin/env python3
"""
Extract and remember database schema
"""
import subprocess

def remember_fact(content: str, category: str, importance: str = 'medium'):
    """Store a fact in memory"""
    cmd = ['python3', '.claude/mcp_memory_server.py', 'remember', content, category, importance]
    subprocess.run(cmd, cwd='/home/bbrelin/course-creator', capture_output=True)

def get_tables():
    """Get all tables from database"""
    cmd = [
        'docker', 'exec', 'b7132871f4ed_course-creator-postgres-1',
        'psql', '-U', 'postgres', '-d', 'course_creator',
        '-t', '-c',
        "SELECT tablename FROM pg_tables WHERE schemaname = 'course_creator' ORDER BY tablename;"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    tables = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    return tables

def main():
    print("🗄️  Extracting database schema...")

    tables = get_tables()

    print(f"Found {len(tables)} tables")

    # Store table list
    for table in tables:
        remember_fact(f"Database table: course_creator.{table}", "database", "medium")
        print(f"  ✅ {table}")

    # Store summary facts
    remember_fact(
        f"PostgreSQL database has {len(tables)} tables in course_creator schema",
        "database",
        "high"
    )

    # Group tables by domain
    domains = {
        'users': ['users', 'user_sessions'],
        'courses': ['courses', 'course_outlines', 'course_instances', 'course_sections', 'course_feedback'],
        'content': ['slides', 'content_storage'],
        'labs': ['lab_sessions', 'lab_environments'],
        'analytics': ['student_analytics', 'performance_metrics'],
        'organizations': ['organizations', 'organization_memberships'],
        'tracks': ['tracks', 'track_enrollments'],
        'projects': ['projects', 'project_enrollments'],
    }

    for domain, domain_tables in domains.items():
        matching = [t for t in tables if any(dt in t for dt in domain_tables)]
        if matching:
            fact = f"{domain.capitalize()} domain tables: {', '.join(matching)}"
            remember_fact(fact, "database", "medium")

    print(f"\n✅ Stored {len(tables)} database tables")

if __name__ == '__main__':
    main()
