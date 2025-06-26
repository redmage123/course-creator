#!/usr/bin/env python3
"""
Comprehensive fix for software engineer agent import issues
"""

import re

def fix_agent():
    agent_file = "tools/code-generation/software_engineer_agent.py"
    
    with open(agent_file, 'r') as f:
        content = f.read()
    
    print("🔧 Applying fixes to software engineer agent...")
    
    # 1. Fix shared imports in generated code
    content = re.sub(
        r'from shared\.database',
        r'from ...shared.database',
        content
    )
    
    content = re.sub(
        r'from shared\.middleware',
        r'from ...shared.middleware',
        content
    )
    
    content = re.sub(
        r'from shared\.config',
        r'from ...shared.config',
        content
    )
    
    # 2. Fix config manager method calls
    content = re.sub(
        r'config_manager\.get_config\(',
        r'config_manager.get(',
        content
    )
    
    # 3. Fix middleware imports in templates
    content = re.sub(
        r'from fastapi\.middleware\.',
        r'from starlette.middleware.',
        content
    )
    
    # 4. Fix the specific main app generation template
    # Look for the main_content template and fix it
    if "from fastapi.middleware.cors import CORSMiddleware" in content:
        print("✅ Found CORS import to fix")
        # This is correct, but let's make sure other middleware imports are right
    
    # 5. Fix database model imports
    old_pattern = r'from shared\.database\.base import BaseModel'
    new_pattern = r'from ...shared.database.base import BaseModel'
    content = re.sub(old_pattern, new_pattern, content)
    
    # 6. Fix any remaining shared imports
    content = re.sub(
        r'(\s+)from shared\.(\w+)',
        r'\1from ...shared.\2',
        content
    )
    
    with open(agent_file, 'w') as f:
        f.write(content)
    
    print("✅ Applied comprehensive fixes to agent")

if __name__ == "__main__":
    fix_agent()
