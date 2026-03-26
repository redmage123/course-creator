#!/usr/bin/env python3
"""
Extract and remember all API routes from the codebase
"""
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path('/home/bbrelin/course-creator')

def remember_fact(content: str, category: str, importance: str = 'medium'):
    """Store a fact in memory"""
    cmd = ['python3', '.claude/mcp_memory_server.py', 'remember', content, category, importance]
    subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True)

def extract_routes_from_file(file_path: Path):
    """Extract API routes from a Python file"""
    try:
        content = file_path.read_text()

        # Find router definitions
        routes = re.findall(
            r'@router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',
            content,
            re.IGNORECASE
        )

        # Find app routes
        app_routes = re.findall(
            r'@app\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',
            content,
            re.IGNORECASE
        )

        return routes + app_routes
    except:
        return []

def main():
    print("🔍 Extracting API routes from codebase...")
    print()

    # Find all Python files that might contain routes
    api_files = list(PROJECT_ROOT.glob('services/**/api/**/*.py'))
    api_files += list(PROJECT_ROOT.glob('services/**/routes.py'))
    api_files += list(PROJECT_ROOT.glob('services/**/main.py'))
    api_files += list(PROJECT_ROOT.glob('services/**/app.py'))

    service_routes = {}

    for file_path in api_files:
        routes = extract_routes_from_file(file_path)

        if routes:
            # Determine service name
            parts = file_path.parts
            service_idx = parts.index('services') + 1 if 'services' in parts else None
            service_name = parts[service_idx] if service_idx else 'unknown'

            if service_name not in service_routes:
                service_routes[service_name] = []

            service_routes[service_name].extend(routes)

    # Store routes in memory
    total_routes = 0
    for service, routes in sorted(service_routes.items()):
        # Deduplicate
        unique_routes = list(set(routes))
        unique_routes.sort()

        total_routes += len(unique_routes)

        print(f"📦 {service}: {len(unique_routes)} routes")

        # Store in chunks (max 10 routes per fact for readability)
        for i in range(0, len(unique_routes), 10):
            chunk = unique_routes[i:i+10]
            routes_str = ', '.join([f"{method.upper()} {path}" for method, path in chunk])
            fact = f"{service} API routes: {routes_str}"
            remember_fact(fact, 'api_routes', 'high')

        # Store route count
        remember_fact(
            f"{service} has {len(unique_routes)} API endpoints",
            'architecture',
            'medium'
        )

    print()
    print(f"✅ Stored {total_routes} API routes from {len(service_routes)} services")

if __name__ == '__main__':
    main()
