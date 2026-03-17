"""
AI Assistant Service Package

BUSINESS PURPOSE:
Provides production-ready AI assistant with LLM integration, RAG retrieval,
and function calling for platform actions. Replaces demo pattern-matching
implementation with real AI capabilities.

TECHNICAL IMPLEMENTATION:
- LLM integration (OpenAI GPT-4 / Anthropic Claude)
- RAG service integration for codebase understanding
- Function calling for platform actions
- WebSocket API for real-time communication
- RBAC permission checks before action execution

SERVICE DETAILS:
- Port: 8011
- Protocol: HTTPS + WebSocket
- Dependencies: RAG service (port 8009)
"""

__version__ = "1.0.0"
