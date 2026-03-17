#!/usr/bin/env python3
"""
Seed Demo Tour Guide Knowledge to RAG Service

BUSINESS PURPOSE:
Populate the RAG service with demo tour guide knowledge base to enable
AI-powered Q&A for demo viewers.

TECHNICAL APPROACH:
Read the demo_tour_guide_knowledge.md file and send it to the RAG service
via the add-document endpoint.
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read the knowledge base
with open('/home/bbrelin/course-creator/docs/demo_tour_guide_knowledge.md', 'r') as f:
    knowledge_content = f.read()

# Split into sections
sections = knowledge_content.split('## ')

print("=" * 70)
print("🤖 SEEDING DEMO TOUR GUIDE KNOWLEDGE TO RAG SERVICE")
print("=" * 70)
print()

success_count = 0
failed_count = 0

for section in sections[1:]:  # Skip first empty split
    lines = section.strip().split('\n')
    title = lines[0]
    content = '\n'.join(lines[1:])

    if not content.strip():
        continue

    print(f"📝 Adding section: {title[:50]}...")

    try:
        response = requests.post(
            'https://localhost:8009/api/v1/rag/add-document',
            json={
                'content': content,
                'domain': 'demo_tour_guide',
                'source': 'knowledge_base',
                'metadata': {
                    'section': title,
                    'file': 'demo_tour_guide_knowledge.md',
                    'type': 'documentation'
                }
            },
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            print(f"   ✓ Added successfully")
            success_count += 1
        else:
            print(f"   ✗ Failed: {response.status_code} - {response.text[:100]}")
            failed_count += 1

    except Exception as e:
        print(f"   ✗ Error: {e}")
        failed_count += 1

print()
print("=" * 70)
print("✅ SEEDING COMPLETE")
print("=" * 70)
print()
print(f"📊 Summary:")
print(f"   • Total sections: {len(sections) - 1}")
print(f"   • Success: {success_count}")
print(f"   • Failed: {failed_count}")
print()
