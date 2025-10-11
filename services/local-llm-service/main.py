"""
Local LLM Service - Main Entry Point

Production-ready local LLM service using Ollama for cost-effective AI inference.

This service provides:
- Local Llama 3.1 8B inference (10x faster for simple queries)
- Response caching (reduce redundant computation)
- RAG context summarization (reduce token usage)
- Conversation compression (optimize context windows)
- Function parameter extraction (structured outputs)
- Performance metrics and cost tracking

Quick Start:
    1. Install Ollama: https://ollama.ai/
    2. Pull Llama 3.1 8B: ollama pull llama3.1:8b-instruct-q4_K_M
    3. Start service: python main.py
    4. Test: curl http://localhost:8015/health

Environment Variables:
    LOCAL_LLM_PORT - Port to run on (default: 8015)
    OLLAMA_HOST - Ollama server URL (default: http://localhost:11434)
    MODEL_NAME - Model to use (default: llama3.1:8b-instruct-q4_K_M)
    ENABLE_CACHE - Enable response caching (default: true)
    CACHE_TTL - Cache TTL in seconds (default: 3600)
"""

import os
import sys
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Add service to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_llm_service.application.services.local_llm_service import LocalLLMService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration from environment variables
LOCAL_LLM_PORT = int(os.getenv("LOCAL_LLM_PORT", 8015))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b-instruct-q4_K_M")
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))


# FastAPI application
app = FastAPI(
    title="Local LLM Service",
    description="Cost-effective local LLM inference using Ollama",
    version="1.0.0"
)


# Global service instance
local_llm_service: Optional[LocalLLMService] = None


# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = "You are a helpful AI assistant."
    max_tokens: int = 500
    temperature: float = 0.7


class GenerateResponse(BaseModel):
    response: str
    latency_ms: float
    cached: bool


class SummarizeRequest(BaseModel):
    context: str
    max_summary_tokens: int = 100


class CompressRequest(BaseModel):
    messages: List[Dict[str, str]]
    target_tokens: int = 200


class FunctionCallRequest(BaseModel):
    user_message: str
    function_schema: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """
    Initialize the Local LLM Service on startup.
    """
    global local_llm_service

    logger.info("=" * 60)
    logger.info("Starting Local LLM Service")
    logger.info("=" * 60)

    try:
        # Initialize service
        local_llm_service = LocalLLMService(
            base_url=OLLAMA_HOST,
            model_name=MODEL_NAME,
            enable_cache=ENABLE_CACHE,
            cache_ttl=CACHE_TTL
        )

        # Health check
        is_healthy = await local_llm_service.health_check()

        if is_healthy:
            logger.info("✓ Local LLM Service initialized successfully")
            logger.info(f"✓ Model: {MODEL_NAME}")
            logger.info(f"✓ Ollama: {OLLAMA_HOST}")
            logger.info(f"✓ Cache: {'Enabled' if ENABLE_CACHE else 'Disabled'}")
            logger.info(f"✓ Port: {LOCAL_LLM_PORT}")
        else:
            logger.warning(
                "⚠ Ollama service not available. "
                "Service will run in degraded mode."
            )

    except Exception as e:
        logger.error(f"✗ Failed to initialize Local LLM Service: {str(e)}")
        logger.warning("Service will run in degraded mode")

    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    if local_llm_service:
        await local_llm_service.close()
        logger.info("Local LLM Service shut down gracefully")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service health status and model availability.
    """
    if not local_llm_service:
        return JSONResponse(
            status_code=503,
            content={
                "service": "local-llm",
                "status": "unhealthy",
                "error": "Service not initialized"
            }
        )

    is_healthy = await local_llm_service.health_check()

    if is_healthy:
        return {
            "service": "local-llm",
            "status": "healthy",
            "model": MODEL_NAME,
            "ollama_host": OLLAMA_HOST,
            "cache_enabled": ENABLE_CACHE
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "service": "local-llm",
                "status": "unhealthy",
                "error": "Ollama service not available"
            }
        )


@app.get("/models")
async def list_models():
    """
    List available Ollama models.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    models = await local_llm_service.list_models()

    return {
        "models": models,
        "current_model": MODEL_NAME
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate a response for a simple prompt.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    import time
    start_time = time.time()

    # Check cache first
    cache_stats_before = local_llm_service.get_cache_stats()

    response_text = await local_llm_service.generate_response(
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    latency_ms = (time.time() - start_time) * 1000

    # Check if cache was hit
    cache_stats_after = local_llm_service.get_cache_stats()
    cached = (
        cache_stats_after.get("hits", 0) > cache_stats_before.get("hits", 0)
    )

    if response_text is None:
        raise HTTPException(status_code=500, detail="Failed to generate response")

    return GenerateResponse(
        response=response_text,
        latency_ms=latency_ms,
        cached=cached
    )


@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    """
    Summarize RAG context to reduce tokens.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    summary = await local_llm_service.summarize_rag_context(
        context=request.context,
        max_summary_tokens=request.max_summary_tokens
    )

    if summary is None:
        raise HTTPException(status_code=500, detail="Failed to summarize context")

    return {
        "summary": summary,
        "original_length": len(request.context),
        "summary_length": len(summary),
        "compression_ratio": len(summary) / len(request.context)
    }


@app.post("/compress")
async def compress(request: CompressRequest):
    """
    Compress conversation history.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    compressed = await local_llm_service.compress_conversation(
        messages=request.messages,
        target_tokens=request.target_tokens
    )

    if compressed is None:
        raise HTTPException(status_code=500, detail="Failed to compress conversation")

    original_length = sum(len(m["content"]) for m in request.messages)

    return {
        "compressed": compressed,
        "original_length": original_length,
        "compressed_length": len(compressed),
        "compression_ratio": len(compressed) / original_length
    }


@app.post("/extract-parameters")
async def extract_parameters(request: FunctionCallRequest):
    """
    Extract function parameters from user message.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        parameters = await local_llm_service.extract_function_parameters(
            user_message=request.user_message,
            function_schema=request.function_schema
        )

        return {
            "function_name": request.function_schema["name"],
            "parameters": parameters
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract parameters: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """
    Get service performance metrics and cost savings.
    """
    if not local_llm_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    metrics = local_llm_service.get_metrics()

    return metrics


@app.get("/stats")
async def get_stats():
    """
    Get service statistics (alias for /metrics).
    """
    return await get_metrics()


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Local LLM Service on port {LOCAL_LLM_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=LOCAL_LLM_PORT,
        log_level="info"
    )
