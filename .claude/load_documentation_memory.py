#!/usr/bin/env python3
"""
Load all documentation into MCP memory system

This script reads all .md documentation files and stores key information
in the MCP memory system for Claude Code to recall.
"""
import os
import sys
import subprocess
from pathlib import Path

# Key documentation files to remember (prioritized)
PRIORITY_DOCS = [
    # Claude-specific documentation
    'CLAUDE.md',
    'claude.md/01-critical-requirements.md',
    'claude.md/02-documentation-standards.md',
    'claude.md/03-memory-system.md',
    'claude.md/04-version-history.md',
    'claude.md/05-architecture.md',
    'claude.md/06-key-systems.md',
    'claude.md/07-development-commands.md',
    'claude.md/08-testing-strategy.md',
    'claude.md/09-quality-assurance.md',
    'claude.md/10-troubleshooting.md',

    # Recent fixes and test documentation
    'AUDIT_LOG_FIXES.md',
    'TEST_FAILURE_ANALYSIS.md',
    'TESTING_GUIDE.md',
    'TEST_REFACTORING_COMPLETE_SUMMARY.md',

    # Architecture and deployment
    'README.md',
    'docs/architecture.md',
    'docs/RUNBOOK.md',
    'DEPLOYMENT.md',
]

def remember_fact(content, category, importance="medium"):
    """Store a fact in memory"""
    cmd = [
        'python3',
        '.claude/mcp_memory_server.py',
        'remember',
        content,
        category,
        importance
    ]
    subprocess.run(cmd, cwd='/home/bbrelin/course-creator', capture_output=True)

def cache_file(file_path):
    """Cache a file in memory"""
    cmd = [
        'python3',
        '.claude/mcp_memory_server.py',
        'cache',
        file_path
    ]
    result = subprocess.run(cmd, cwd='/home/bbrelin/course-creator', capture_output=True, text=True)
    return result.returncode == 0

def extract_key_facts(file_path, content):
    """Extract key facts from documentation content"""
    facts = []

    # Determine category based on file path
    if 'claude.md' in file_path:
        category = 'claude_documentation'
        importance = 'critical'
    elif 'AUDIT_LOG' in file_path:
        category = 'audit_log'
        importance = 'high'
    elif 'TEST' in file_path or 'test' in file_path.lower():
        category = 'testing'
        importance = 'high'
    elif 'architecture' in file_path.lower() or 'ARCHITECTURE' in file_path:
        category = 'architecture'
        importance = 'high'
    elif 'deployment' in file_path.lower() or 'DEPLOYMENT' in file_path:
        category = 'deployment'
        importance = 'medium'
    else:
        category = 'documentation'
        importance = 'medium'

    # Extract headings as facts
    lines = content.split('\n')
    current_section = None

    for line in lines:
        # H1 headings
        if line.startswith('# '):
            current_section = line[2:].strip()
            facts.append({
                'content': f"{file_path}: {current_section}",
                'category': category,
                'importance': importance
            })

        # H2 headings with context
        elif line.startswith('## ') and current_section:
            subsection = line[3:].strip()
            facts.append({
                'content': f"{file_path} > {current_section} > {subsection}",
                'category': category,
                'importance': importance
            })

        # Critical markers
        elif 'CRITICAL' in line or 'IMPORTANT' in line or '🚨' in line:
            clean_line = line.strip().replace('**', '').replace('*', '')
            if len(clean_line) > 10 and len(clean_line) < 200:
                facts.append({
                    'content': f"{file_path}: {clean_line}",
                    'category': category,
                    'importance': 'critical'
                })

    return facts

def main():
    project_root = Path('/home/bbrelin/course-creator')

    print("🧠 Loading documentation into MCP memory...")
    print()

    cached_files = 0
    stored_facts = 0

    for doc_file in PRIORITY_DOCS:
        file_path = project_root / doc_file

        if not file_path.exists():
            print(f"⚠️  Skipping {doc_file} (not found)")
            continue

        print(f"📖 Processing {doc_file}...")

        # Cache the entire file
        if cache_file(doc_file):
            cached_files += 1
            print(f"   ✅ Cached file")

        # Extract and store key facts
        try:
            content = file_path.read_text()
            facts = extract_key_facts(doc_file, content)

            for fact in facts[:10]:  # Limit to top 10 facts per file
                remember_fact(fact['content'], fact['category'], fact['importance'])
                stored_facts += 1

            print(f"   ✅ Stored {len(facts[:10])} key facts")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print()
    print("=" * 60)
    print(f"✅ Complete!")
    print(f"   Cached files: {cached_files}")
    print(f"   Stored facts: {stored_facts}")
    print("=" * 60)

    # Show final stats
    print()
    subprocess.run(['python3', '.claude/mcp_memory_server.py', 'stats'],
                   cwd='/home/bbrelin/course-creator')

if __name__ == '__main__':
    main()
