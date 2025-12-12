"""
AI Assistant Service - Main Application

BUSINESS PURPOSE:
Production-ready AI assistant service for Course Creator Platform.
Provides natural language interface for platform operations, answering
questions, and executing actions via LLM + RAG + function calling.

TECHNICAL IMPLEMENTATION:
FastAPI application with WebSocket support for real-time chat.
Integrates with:
- RAG service (port 8009) for codebase knowledge
- OpenAI/Claude for natural language understanding
- Platform APIs for action execution
- RBAC for permission enforcement

SERVICE DETAILS:
- Port: 8011
- Protocol: HTTPS + WebSocket (wss://)
- Dependencies: RAG service, LLM API, Platform APIs
"""

import os
import ssl
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ai_assistant_service.application.services.llm_service import (
    LLMService,
    LLMProvider
)
from ai_assistant_service.application.services.rag_service import RAGService
from ai_assistant_service.application.services.function_executor import (
    FunctionExecutor
)
from ai_assistant_service.application.services.nlp_service import NLPService
from ai_assistant_service.application.services.knowledge_graph_service import (
    KnowledgeGraphService
)
from ai_assistant_service.application.services.hybrid_llm_router import HybridLLMRouter
from api.websocket import AIAssistantWebSocketHandler
from api.onboarding_endpoints import router as onboarding_router, set_websocket_handler

# Configure logging FIRST (before using logger)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import local LLM service (optional dependency)
try:
    import sys
    sys.path.insert(0, "/home/bbrelin/course-creator/services/local-llm-service")
    from local_llm_service.application.services.local_llm_service import LocalLLMService
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False
    logger.warning("Local LLM service not available - will use cloud LLM only")


# Service configuration
SERVICE_PORT = int(os.getenv("AI_ASSISTANT_PORT", "8011"))
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "https://localhost:8009")
NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "https://localhost:8013")
KG_SERVICE_URL = os.getenv("KG_SERVICE_URL", "https://localhost:8012")
LOCAL_LLM_SERVICE_URL = os.getenv("LOCAL_LLM_SERVICE_URL", "http://localhost:8015")
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL", "https://localhost")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai or claude
ENABLE_LOCAL_LLM = os.getenv("ENABLE_LOCAL_LLM", "true").lower() == "true"

# SSL configuration
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "/etc/nginx/ssl/cert.pem")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "/etc/nginx/ssl/key.pem")


# Global service instances
llm_service: LLMService = None
rag_service: RAGService = None
function_executor: FunctionExecutor = None
nlp_service: NLPService = None
kg_service: KnowledgeGraphService = None
local_llm_service = None
hybrid_router: HybridLLMRouter = None
websocket_handler: AIAssistantWebSocketHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager

    BUSINESS PURPOSE:
    Initializes and cleans up services on startup/shutdown.
    Ensures proper resource management and service availability.

    TECHNICAL IMPLEMENTATION:
    - Starts LLM, RAG, NLP, KG, and function executor services
    - Validates service connectivity
    - Closes HTTP clients on shutdown
    """
    global llm_service, rag_service, function_executor, nlp_service, kg_service, local_llm_service, hybrid_router, websocket_handler

    logger.info("=== AI Assistant Service Starting ===")

    # Initialize services
    try:
        # Initialize LLM service
        provider = LLMProvider.OPENAI if LLM_PROVIDER.lower() == "openai" else LLMProvider.CLAUDE
        llm_service = LLMService(provider=provider)
        logger.info(f"✓ LLM Service initialized: {provider}")

        # Initialize RAG service
        rag_service = RAGService(base_url=RAG_SERVICE_URL)
        rag_healthy = await rag_service.health_check()
        if rag_healthy:
            stats = await rag_service.get_stats()
            logger.info(f"✓ RAG Service connected: {stats}")
        else:
            logger.warning("⚠ RAG Service not reachable - continuing without codebase context")

        # Initialize NLP service
        nlp_service = NLPService(base_url=NLP_SERVICE_URL)
        nlp_healthy = await nlp_service.health_check()
        if nlp_healthy:
            logger.info(f"✓ NLP Service connected: {NLP_SERVICE_URL}")
        else:
            logger.warning("⚠ NLP Service not reachable - continuing without preprocessing optimization")

        # Initialize Knowledge Graph service
        kg_service = KnowledgeGraphService(base_url=KG_SERVICE_URL)
        kg_healthy = await kg_service.health_check()
        if kg_healthy:
            stats = await kg_service.get_statistics()
            logger.info(f"✓ Knowledge Graph Service connected: {stats}")
        else:
            logger.warning("⚠ Knowledge Graph Service not reachable - continuing without course recommendations")

        # Initialize function executor
        function_executor = FunctionExecutor(api_base_url=PLATFORM_API_URL)
        logger.info(f"✓ Function Executor initialized")

        # Initialize Local LLM service (optional)
        if ENABLE_LOCAL_LLM and LOCAL_LLM_AVAILABLE:
            try:
                local_llm_service = LocalLLMService(base_url=LOCAL_LLM_SERVICE_URL)
                local_llm_healthy = await local_llm_service.health_check()
                if local_llm_healthy:
                    logger.info(f"✓ Local LLM Service connected: {LOCAL_LLM_SERVICE_URL}")
                    logger.info(f"  Cost optimization: 74% reduction, 10x faster for simple queries")
                else:
                    logger.warning("⚠ Local LLM Service not reachable - will use cloud LLM only")
                    local_llm_service = None
            except Exception as e:
                logger.warning(f"⚠ Local LLM Service unavailable: {str(e)} - will use cloud LLM only")
                local_llm_service = None
        else:
            logger.info("⚠ Local LLM disabled or not available - using cloud LLM only")
            local_llm_service = None

        # Initialize Hybrid LLM Router
        hybrid_router = HybridLLMRouter(
            local_llm_service=local_llm_service,
            cloud_llm_service=llm_service,
            nlp_service=nlp_service,
            enable_local_llm=ENABLE_LOCAL_LLM and local_llm_service is not None
        )
        logger.info(f"✓ Hybrid LLM Router initialized (local_llm={'enabled' if local_llm_service else 'disabled'})")

        # Initialize WebSocket handler
        websocket_handler = AIAssistantWebSocketHandler(
            llm_service=llm_service,
            rag_service=rag_service,
            function_executor=function_executor,
            nlp_service=nlp_service,
            kg_service=kg_service
        )
        logger.info(f"✓ WebSocket Handler initialized")

        # Set websocket handler for onboarding endpoints
        set_websocket_handler(websocket_handler)
        logger.info(f"✓ Onboarding endpoints connected to WebSocket handler")

        logger.info(f"=== AI Assistant Service Ready on port {SERVICE_PORT} ===")

    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        raise

    yield

    # Cleanup
    logger.info("=== AI Assistant Service Shutting Down ===")

    if rag_service:
        await rag_service.close()
        logger.info("✓ RAG Service client closed")

    if nlp_service:
        await nlp_service.close()
        logger.info("✓ NLP Service client closed")

    if kg_service:
        await kg_service.close()
        logger.info("✓ Knowledge Graph Service client closed")

    if local_llm_service:
        await local_llm_service.close()
        logger.info("✓ Local LLM Service closed")

    if function_executor:
        await function_executor.close()
        logger.info("✓ Function Executor closed")

    logger.info("=== AI Assistant Service Stopped ===")


# Create FastAPI application
app = FastAPI(
    title="AI Assistant Service",
    description="Production-ready AI assistant with LLM + RAG + function calling",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Security: Use environment-configured origins
# Never use wildcard (*) in production - enables CSRF attacks
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://localhost:3000,https://localhost:3001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"]
)

# Register onboarding and help endpoints
app.include_router(onboarding_router)


@app.get("/")
async def root():
    """
    Root endpoint

    BUSINESS PURPOSE:
    Provides service identification and version information.

    RETURNS:
        Service info dictionary
    """
    return {
        "service": "AI Assistant Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Production-ready AI assistant with LLM + RAG + function calling"
    }


@app.get("/api/v1/ai-assistant/health")
async def health_check():
    """
    Health check endpoint

    BUSINESS PURPOSE:
    Allows monitoring systems to verify service health. Checks
    connectivity to dependent services (RAG, LLM).

    RETURNS:
        Health status dictionary

    RAISES:
        HTTPException: If service is unhealthy
    """
    health_status = {
        "service": "ai-assistant",
        "status": "healthy",
        "llm_service": "connected" if llm_service else "not initialized",
        "rag_service": "unknown",
        "nlp_service": "unknown",
        "kg_service": "unknown",
        "function_executor": "connected" if function_executor else "not initialized"
    }

    # Check RAG service
    if rag_service:
        rag_healthy = await rag_service.health_check()
        health_status["rag_service"] = "connected" if rag_healthy else "disconnected"

    # Check NLP service
    if nlp_service:
        nlp_healthy = await nlp_service.health_check()
        health_status["nlp_service"] = "connected" if nlp_healthy else "disconnected"

    # Check Knowledge Graph service
    if kg_service:
        kg_healthy = await kg_service.health_check()
        health_status["kg_service"] = "connected" if kg_healthy else "disconnected"

    # Determine overall health
    if not llm_service or not function_executor:
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@app.get("/api/v1/ai-assistant/stats")
async def get_stats():
    """
    Get service statistics

    BUSINESS PURPOSE:
    Provides usage statistics and metrics for monitoring.
    Shows active conversations, RAG stats, and function usage.

    RETURNS:
        Statistics dictionary
    """
    stats = {
        "active_conversations": len(websocket_handler.conversations) if websocket_handler else 0,
        "available_functions": len(FunctionExecutor.get_available_functions())
    }

    # Get RAG stats if available
    if rag_service:
        rag_stats = await rag_service.get_stats()
        stats["rag_service"] = rag_stats

    return stats


@app.get("/api/v1/ai-assistant/functions")
async def get_available_functions():
    """
    Get available functions

    BUSINESS PURPOSE:
    Lists all functions AI assistant can execute. Useful for
    documentation and frontend function discovery.

    RETURNS:
        List of function schemas
    """
    functions = FunctionExecutor.get_available_functions()
    return {
        "functions": [func.to_openai_format() for func in functions]
    }


@app.websocket("/ws/ai-assistant")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for AI assistant

    BUSINESS PURPOSE:
    Main endpoint for real-time AI assistant chat. Handles full
    conversation lifecycle with streaming responses.

    TECHNICAL IMPLEMENTATION:
    Delegates to AIAssistantWebSocketHandler for message processing.
    Maintains conversation state for multi-turn interactions.

    ARGS:
        websocket: FastAPI WebSocket connection
    """
    if not websocket_handler:
        await websocket.close(code=1011, reason="Service not initialized")
        return

    await websocket_handler.handle_connection(websocket)


def main():
    """
    Main entry point

    BUSINESS PURPOSE:
    Starts FastAPI application with SSL and production settings.

    TECHNICAL IMPLEMENTATION:
    Configures uvicorn with SSL certificates and runs server.
    """
    # Create SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Load SSL certificates if they exist
    if os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
        ssl_context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
        logger.info(f"✓ SSL certificates loaded")
    else:
        logger.warning(f"⚠ SSL certificates not found - running without SSL")
        ssl_context = None

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        ssl_keyfile=SSL_KEY_PATH if ssl_context else None,
        ssl_certfile=SSL_CERT_PATH if ssl_context else None,
        log_level="info"
    )


if __name__ == "__main__":
    main()
