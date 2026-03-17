"""
Application Layer - AI Assistant Service

BUSINESS PURPOSE:
Application services orchestrating domain logic and infrastructure.
Coordinates between LLM, RAG, and platform APIs to fulfill user requests.

TECHNICAL IMPLEMENTATION:
- LLMService: Manages LLM API calls and response parsing
- RAGService: Retrieves relevant context from codebase
- FunctionExecutor: Executes platform actions with RBAC
- ConversationManager: Manages conversation lifecycle
"""
