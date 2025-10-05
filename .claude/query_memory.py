#!/usr/bin/env python3
"""Query and update MCP memory database"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = ".claude/memory.db"

def query_facts(search_term=None, limit=50):
    """Query facts from memory"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if search_term:
        cursor.execute("""
            SELECT id, content, category, importance, created_at
            FROM facts
            WHERE content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f'%{search_term}%', limit))
    else:
        cursor.execute("""
            SELECT id, content, category, importance, created_at
            FROM facts
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    facts = cursor.fetchall()
    conn.close()

    return facts

def add_fact(content, category="general", importance="medium"):
    """Add a new fact to memory"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO facts (content, category, importance, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (content, category, importance, datetime.now(), datetime.now()))

    fact_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return fact_id

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 query_memory.py search <term>")
        print("  python3 query_memory.py add '<fact>' [category] [importance]")
        print("  python3 query_memory.py list [limit]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "search":
        if len(sys.argv) < 3:
            print("Please provide a search term")
            sys.exit(1)

        search_term = sys.argv[2]
        facts = query_facts(search_term)

        print(f"\n{'='*80}")
        print(f"Found {len(facts)} facts matching '{search_term}':")
        print(f"{'='*80}\n")

        for fact in facts:
            print(f"ID: {fact[0]}")
            print(f"Content: {fact[1]}")
            print(f"Category: {fact[2]} | Importance: {fact[3]}")
            print(f"Created: {fact[4]}")
            print("-" * 80)

    elif command == "add":
        if len(sys.argv) < 3:
            print("Please provide fact content")
            sys.exit(1)

        content = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else "general"
        importance = sys.argv[4] if len(sys.argv) > 4 else "medium"

        fact_id = add_fact(content, category, importance)
        print(f"✅ Added fact #{fact_id}")
        print(f"Content: {content}")
        print(f"Category: {category} | Importance: {importance}")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        facts = query_facts(limit=limit)

        print(f"\n{'='*80}")
        print(f"Latest {len(facts)} facts:")
        print(f"{'='*80}\n")

        for fact in facts:
            print(f"ID: {fact[0]}")
            print(f"Content: {fact[1][:100]}...")
            print(f"Category: {fact[2]} | Importance: {fact[3]}")
            print(f"Created: {fact[4]}")
            print("-" * 80)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
