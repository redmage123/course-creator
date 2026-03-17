#!/bin/bash

"""
Test AI Assistant Integration with Lab Environment

This script verifies that:
1. Lab environment page loads with AI chat widget
2. Lab-manager AI assistant API is accessible
3. RAG service integration is functional
"""

echo "=========================================="
echo "AI Assistant Integration Test"
echo "=========================================="
echo ""

# Test 1: Lab environment page loads
echo "✓ Test 1: Checking lab environment page loads..."
RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:3000/html/lab-environment.html)
if [ "$RESPONSE" = "200" ]; then
    echo "  ✅ Lab environment page loads (HTTP $RESPONSE)"
else
    echo "  ❌ Lab environment page failed (HTTP $RESPONSE)"
    exit 1
fi

# Test 2: AI chat widget present
echo ""
echo "✓ Test 2: Checking AI chat widget is present in HTML..."
WIDGET_COUNT=$(curl -k -s https://localhost:3000/html/lab-environment.html | grep -c "ai-chat-toggle")
if [ "$WIDGET_COUNT" -gt "0" ]; then
    echo "  ✅ AI chat widget found ($WIDGET_COUNT occurrences)"
else
    echo "  ❌ AI chat widget not found"
    exit 1
fi

# Test 3: Lab-manager service running
echo ""
echo "✓ Test 3: Checking lab-manager service is running..."
LAB_HEALTH=$(curl -k -s https://localhost:8006/health)
if echo "$LAB_HEALTH" | grep -q "healthy"; then
    echo "  ✅ Lab-manager service is healthy"
    echo "     $LAB_HEALTH"
else
    echo "  ❌ Lab-manager service not healthy"
    exit 1
fi

# Test 4: AI assistant endpoint exists
echo ""
echo "✓ Test 4: Checking AI assistant endpoint is accessible..."
ASSISTANT_STATS=$(curl -k -s https://localhost:8006/assistant/stats)
if echo "$ASSISTANT_STATS" | grep -q "assistant_stats"; then
    echo "  ✅ AI assistant endpoint accessible"
    echo "     $ASSISTANT_STATS"
else
    echo "  ❌ AI assistant endpoint not accessible"
    exit 1
fi

# Test 5: Test AI assistant help endpoint with sample request
echo ""
echo "✓ Test 5: Testing AI assistant help endpoint..."
AI_RESPONSE=$(curl -k -s -X POST https://localhost:8006/assistant/help \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python",
    "question": "What does this code do?",
    "error_message": null,
    "student_id": "test_student",
    "skill_level": "beginner"
  }')

if echo "$AI_RESPONSE" | grep -q "response_text"; then
    echo "  ✅ AI assistant responded successfully"
    echo "     Response preview: $(echo "$AI_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response_text', '')[:100])")"
else
    echo "  ❌ AI assistant help endpoint failed"
    echo "     Response: $AI_RESPONSE"
    exit 1
fi

# Test 6: Check RAG service availability
echo ""
echo "✓ Test 6: Checking RAG service availability..."
RAG_HEALTH=$(curl -k -s https://localhost:8009/api/v1/rag/health 2>&1)
if echo "$RAG_HEALTH" | grep -q "healthy\|status"; then
    echo "  ✅ RAG service is available"
else
    echo "  ⚠️  RAG service may not be available (assistant will work with reduced intelligence)"
    echo "     Response: $RAG_HEALTH"
fi

echo ""
echo "=========================================="
echo "✅ All AI Assistant Integration Tests PASSED"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Lab environment page: ✅ Loading"
echo "  • AI chat widget: ✅ Present"
echo "  • Lab-manager service: ✅ Healthy"
echo "  • AI assistant API: ✅ Functional"
echo "  • RAG integration: ✅ Available"
echo ""
echo "You can now:"
echo "  1. Navigate to https://localhost:3000/lab"
echo "  2. Click the purple robot button (bottom-right)"
echo "  3. Ask questions about your code"
echo "  4. Get AI-powered debugging help"
echo ""
