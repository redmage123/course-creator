#!/usr/bin/env python3
"""
Ingest and remember key parts of the codebase into MCP memory

STRATEGY:
1. Cache all critical Python files (main.py, routes.py, endpoints, services)
2. Store architectural facts about each service
3. Remember key entities (models, domain entities)
4. Map relationships between services
5. Store API endpoint information
6. Remember configuration patterns

This focuses on:
- Service entry points and main files
- API endpoints and routes
- Domain entities and models
- Service dependencies
- Key business logic files
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Set

PROJECT_ROOT = Path('/home/bbrelin/course-creator')

# Critical file patterns to cache and remember
CRITICAL_PATTERNS = [
    # Service entry points
    '**/main.py',
    '**/app.py',
    '**/routes.py',

    # API endpoints
    '**/api/**/*_endpoints.py',
    '**/api/**/*_api.py',
    '**/endpoints/**/*.py',

    # Domain entities and models
    '**/domain/entities/**/*.py',
    '**/models/**/*.py',

    # Services (business logic)
    '**/services/**/*_service.py',
    '**/application/services/**/*.py',

    # Data access
    '**/data_access/**/*_dao.py',
    '**/repositories/**/*.py',

    # Dependencies and configuration
    '**/dependencies.py',
    '**/app_dependencies.py',
    '**/__init__.py',
]

# Directories to analyze
SERVICE_DIRS = [
    'services/user-management',
    'services/course-management',
    'services/content-management',
    'services/organization-management',
    'services/lab-manager',
    'services/analytics',
    'services/course-generator',
    'services/rag-service',
    'services/demo-service',
]

def run_memory_command(command: List[str]) -> bool:
    """Run MCP memory server command"""
    cmd = ['python3', '.claude/mcp_memory_server.py'] + command
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def cache_file(file_path: str) -> bool:
    """Cache a file in memory"""
    return run_memory_command(['cache', file_path])

def remember_fact(content: str, category: str, importance: str = 'medium') -> bool:
    """Store a fact in memory"""
    return run_memory_command(['remember', content, category, importance])

def create_entity(name: str, entity_type: str, description: str) -> bool:
    """Create an entity in memory"""
    return run_memory_command(['entity', name, entity_type, description])

def find_files_by_pattern(pattern: str) -> List[Path]:
    """Find files matching a glob pattern"""
    return list(PROJECT_ROOT.glob(pattern))

def analyze_service_structure(service_dir: Path) -> Dict:
    """Analyze a service's structure and extract key information"""
    service_name = service_dir.name

    info = {
        'name': service_name,
        'main_file': None,
        'endpoints': [],
        'models': [],
        'services': [],
        'dependencies': []
    }

    # Find main entry point
    for main_file in ['main.py', 'app.py']:
        if (service_dir / main_file).exists():
            info['main_file'] = main_file
            break

    # Find endpoint files
    if (service_dir / 'api').exists():
        info['endpoints'] = [
            f.name for f in (service_dir / 'api').glob('*_endpoints.py')
        ]

    # Find model files
    if (service_dir / 'models').exists():
        info['models'] = [
            f.name for f in (service_dir / 'models').glob('*.py')
            if f.name != '__init__.py'
        ]
    elif (service_dir / 'domain' / 'entities').exists():
        info['models'] = [
            f.name for f in (service_dir / 'domain' / 'entities').glob('*.py')
            if f.name != '__init__.py'
        ]

    # Find service files
    if (service_dir / 'services').exists():
        info['services'] = [
            f.name for f in (service_dir / 'services').glob('*_service.py')
        ]
    elif (service_dir / 'application' / 'services').exists():
        info['services'] = [
            f.name for f in (service_dir / 'application' / 'services').glob('*_service.py')
        ]

    return info

def ingest_codebase():
    """Main ingestion function"""
    print("🧠 Ingesting Course Creator Platform codebase...")
    print()

    cached_count = 0
    fact_count = 0
    entity_count = 0

    # Step 1: Analyze and remember each service
    print("📦 Step 1: Analyzing microservices...")
    for service_path_str in SERVICE_DIRS:
        service_path = PROJECT_ROOT / service_path_str
        if not service_path.exists():
            print(f"  ⚠️  Skipping {service_path_str} (not found)")
            continue

        print(f"  📁 Analyzing {service_path.name}...")

        info = analyze_service_structure(service_path)

        # Create service entity
        description = f"Microservice: {info['main_file'] or 'N/A'} entry point, " \
                     f"{len(info['endpoints'])} endpoints, " \
                     f"{len(info['models'])} models, " \
                     f"{len(info['services'])} services"

        if create_entity(info['name'], 'service', description):
            entity_count += 1

        # Remember service facts
        if info['main_file']:
            fact = f"{info['name']} service entry point: {info['main_file']}"
            if remember_fact(fact, 'architecture', 'high'):
                fact_count += 1

        if info['endpoints']:
            fact = f"{info['name']} API endpoints: {', '.join(info['endpoints'])}"
            if remember_fact(fact, 'architecture', 'high'):
                fact_count += 1

        if info['models']:
            fact = f"{info['name']} domain models: {', '.join(info['models'][:5])}"  # First 5
            if remember_fact(fact, 'architecture', 'medium'):
                fact_count += 1

        print(f"     ✅ Remembered {info['name']} architecture")

    print()
    print("📄 Step 2: Caching critical files...")

    # Step 2: Cache critical files
    all_files: Set[Path] = set()
    for pattern in CRITICAL_PATTERNS:
        files = find_files_by_pattern(pattern)
        all_files.update(files)

    # Filter to only service files (reduce noise)
    service_files = [
        f for f in all_files
        if any(service in str(f) for service in SERVICE_DIRS)
    ]

    print(f"  Found {len(service_files)} critical files to cache")

    for file_path in sorted(service_files)[:50]:  # Limit to 50 most important
        relative_path = file_path.relative_to(PROJECT_ROOT)

        # Skip very large files
        if file_path.stat().st_size > 100000:  # >100KB
            continue

        if cache_file(str(relative_path)):
            cached_count += 1

            # Extract key information from file
            try:
                content = file_path.read_text()

                # Remember API endpoints
                if 'endpoints.py' in str(file_path) or 'api.py' in str(file_path):
                    import re
                    routes = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
                    if routes:
                        service = str(relative_path).split('/')[1]
                        endpoints_list = [f"{method.upper()} {path}" for method, path in routes[:10]]
                        fact = f"{service} endpoints: {', '.join(endpoints_list)}"
                        if remember_fact(fact, 'api_endpoints', 'high'):
                            fact_count += 1

            except Exception as e:
                pass  # Skip files that can't be read

    print(f"     ✅ Cached {cached_count} files")

    # Step 3: Remember key architectural patterns
    print()
    print("🏗️  Step 3: Remembering architectural patterns...")

    patterns = [
        ("All services use FastAPI framework for HTTP APIs", "architecture", "critical"),
        ("Services communicate via HTTP/HTTPS (no shared database)", "architecture", "critical"),
        ("User-management on port 8000 handles authentication and JWT tokens", "architecture", "critical"),
        ("Organization-management on port 8008 handles RBAC, organizations, audit logs", "architecture", "critical"),
        ("Course-management on port 8001 handles course CRUD operations", "architecture", "high"),
        ("Lab-manager on port 8005 handles Docker container-based lab environments", "architecture", "high"),
        ("All services use PostgreSQL database 'course_creator' with schema 'course_creator'", "architecture", "critical"),
        ("Authentication uses JWT tokens with get_current_user dependency", "authentication", "critical"),
        ("RBAC uses verify_site_admin_permission() for admin endpoints", "authentication", "critical"),
        ("Services follow clean architecture: api/ -> application/services/ -> domain/entities/", "architecture", "high"),
    ]

    for fact, category, importance in patterns:
        if remember_fact(fact, category, importance):
            fact_count += 1

    print(f"     ✅ Remembered {len(patterns)} architectural patterns")

    # Final summary
    print()
    print("=" * 70)
    print("✅ Codebase Ingestion Complete!")
    print(f"   Services analyzed: {len(SERVICE_DIRS)}")
    print(f"   Files cached: {cached_count}")
    print(f"   Facts stored: {fact_count}")
    print(f"   Entities created: {entity_count}")
    print("=" * 70)
    print()

    # Show final stats
    subprocess.run(
        ['python3', '.claude/mcp_memory_server.py', 'stats'],
        cwd=PROJECT_ROOT
    )

if __name__ == '__main__':
    ingest_codebase()
