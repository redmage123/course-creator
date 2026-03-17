# AI Assistant Pipeline Architecture

## Overview

This document describes the comprehensive AI assistant pipeline architecture for the Course Creator Platform, implementing an ensemble model approach with frontier model consensus.

**Version**: 1.0.0
**Date**: 2025-10-15
**Status**: Implementation In Progress

---

## Pipeline Flow

```
User Query
    ↓
┌──────────────────────────────────────────────────────────────┐
│ PHASE 1: NLP Preprocessing (NLP Service - Port 8013)        │
│ - Intent classification                                      │
│ - Entity extraction (courses, skills, actions)              │
│ - Query expansion (synonyms, related terms)                 │
│ - Deduplication (remove redundant conversation history)     │
│ - LLM call optimization (skip for simple queries)           │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│ PHASE 2: Parallel Service Calls (Concurrent)                │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Knowledge Graph    │  │ Metadata Service   │            │
│  │ Service (8012)     │  │ (8014)             │            │
│  │                    │  │                    │            │
│  │ • Course recs      │  │ • Fuzzy search     │            │
│  │ • Prerequisites    │  │ • Full-text search │            │
│  │ • Learning paths   │  │ • Content matching │            │
│  └────────────────────┘  └────────────────────┘            │
│                                                              │
│  ┌────────────────────┐                                     │
│  │ RAG Service (8009) │                                     │
│  │                    │                                     │
│  │ • Codebase context │                                     │
│  │ • Documentation    │                                     │
│  │ • Examples         │                                     │
│  └────────────────────┘                                     │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│ PHASE 3: Ensemble Model Generation (Parallel LLM Calls)     │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Model 1: Mistral   │  │ Model 2: LLama     │            │
│  │ (Ollama - 8015)    │  │ (Ollama - 8015)    │            │
│  │                    │  │                    │            │
│  │ • course-creator-  │  │ • llama3.1:8b-     │            │
│  │   assistant        │  │   instruct-q4_K_M  │            │
│  │ • Fine-tuned for   │  │ • General purpose  │            │
│  │   educational      │  │   instruction      │            │
│  │   content          │  │   following        │            │
│  └────────────────────┘  └────────────────────┘            │
│           ↓                        ↓                        │
│     Response A              Response B                      │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│ PHASE 4: Frontier Model Consensus (GPT-4/Claude)            │
│                                                              │
│  Input:                                                      │
│  - Original user query                                       │
│  - Context (NLP, KG, Metadata, RAG)                         │
│  - Response A (Mistral)                                      │
│  - Response B (LLama)                                        │
│                                                              │
│  Consensus Algorithm:                                        │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 1. Accuracy: Which response is most factually    │      │
│  │    correct based on context?                     │      │
│  │                                                   │      │
│  │ 2. Precision: Which response is more specific    │      │
│  │    and directly answers the question?            │      │
│  │                                                   │      │
│  │ 3. Responsiveness: Which response is more        │      │
│  │    helpful and actionable?                       │      │
│  │                                                   │      │
│  │ 4. Context Alignment: Which response better      │      │
│  │    uses the provided context (RAG, KG, metadata)?│      │
│  │                                                   │      │
│  │ 5. Coherence: Which response is better          │      │
│  │    structured and easier to understand?          │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Output: Selected best response OR hybrid response          │
└──────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────┐
│ PHASE 5: Function Execution (If Needed)                     │
│ - RBAC validation                                            │
│ - Platform API calls                                         │
│ - Result formatting                                          │
└──────────────────────────────────────────────────────────────┘
    ↓
  Return to User
```

---

## Current Implementation Status

### ✅ Implemented Components

1. **Phase 1: NLP Preprocessing**
   - Location: `/services/ai-assistant-service/api/websocket.py` lines 220-239
   - Service: `nlp_service.preprocess_query()`
   - Status: **PRODUCTION READY**

2. **Phase 2: Parallel Services (Partial)**
   - Knowledge Graph: ✅ Implemented (lines 241-255)
   - RAG Service: ✅ Implemented (lines 257-270)
   - Metadata Fuzzy Search: ❌ **NOT INTEGRATED**

3. **Hybrid LLM Router**
   - Location: `/services/ai-assistant-service/ai_assistant_service/application/services/hybrid_llm_router.py`
   - Status: Routes to EITHER local OR cloud (not ensemble)
   - Issue: Does not call both models concurrently

### ❌ Missing Components

1. **Metadata Service Integration**
   - Need to add parallel call to `metadata_service.search_fuzzy()`
   - Extract course/content metadata context
   - Add to system prompt

2. **Ensemble Model Service**
   - Call BOTH Mistral AND LLama models concurrently
   - Collect both responses
   - Pass to consensus mechanism

3. **Frontier Model Consensus**
   - Analyze both ensemble responses
   - Select best response based on quality criteria
   - Return consensus to user

---

## Implementation Plan

### Step 1: Create Metadata Service Integration

**File**: `/services/ai-assistant-service/ai_assistant_service/application/services/metadata_service.py`

```python
class MetadataService:
    """Integration with Metadata Service for fuzzy search"""

    async def fuzzy_search(
        self,
        query: str,
        entity_types: List[str] = ["course", "content"],
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for courses and content

        Handles typos and partial matches using trigram similarity
        """
        # Call metadata service API
        response = await self.client.get(
            f"{self.base_url}/api/v1/metadata/fuzzy-search",
            params={
                "query": query,
                "entity_types": entity_types,
                "similarity_threshold": similarity_threshold
            }
        )
        return response.json()
```

### Step 2: Create Ensemble Model Service

**File**: `/services/ai-assistant-service/ai_assistant_service/application/services/ensemble_model_service.py`

```python
class EnsembleModelService:
    """
    Ensemble model service that calls multiple LLMs concurrently
    """

    async def generate_ensemble_responses(
        self,
        user_message: str,
        system_prompt: str,
        rag_context: str = "",
        kg_context: str = "",
        metadata_context: str = ""
    ) -> Dict[str, Any]:
        """
        Call Mistral and LLama models in parallel

        Returns:
            {
                "mistral_response": "...",
                "llama_response": "...",
                "mistral_model": "course-creator-assistant",
                "llama_model": "llama3.1:8b-instruct-q4_K_M",
                "generation_time_ms": 1234
            }
        """
        # Build prompt with context
        full_prompt = f"{system_prompt}\n\nContext:\n{rag_context}\n{kg_context}\n{metadata_context}\n\nUser: {user_message}"

        # Call both models concurrently
        mistral_task = self.local_llm_service.generate_response(
            prompt=full_prompt,
            model="course-creator-assistant",
            max_tokens=500
        )

        llama_task = self.local_llm_service.generate_response(
            prompt=full_prompt,
            model="llama3.1:8b-instruct-q4_K_M",
            max_tokens=500
        )

        # Wait for both
        mistral_response, llama_response = await asyncio.gather(
            mistral_task,
            llama_task
        )

        return {
            "mistral_response": mistral_response,
            "llama_response": llama_response,
            "mistral_model": "course-creator-assistant",
            "llama_model": "llama3.1:8b-instruct-q4_K_M"
        }
```

### Step 3: Create Frontier Model Consensus

**File**: `/services/ai-assistant-service/ai_assistant_service/application/services/consensus_service.py`

```python
class ConsensusService:
    """
    Frontier model (GPT-4/Claude) consensus mechanism
    """

    async def select_best_response(
        self,
        user_query: str,
        context: Dict[str, str],
        ensemble_responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Use frontier model to select best response from ensemble

        Evaluation Criteria:
        1. Accuracy - Factual correctness
        2. Precision - Specificity and directness
        3. Responsiveness - Helpfulness and actionability
        4. Context Alignment - Use of provided context
        5. Coherence - Structure and clarity

        Returns:
            {
                "selected_response": "...",
                "selected_model": "mistral|llama|hybrid",
                "reasoning": "...",
                "confidence": 0.85
            }
        """
        consensus_prompt = f"""
You are an expert AI evaluator. Analyze these two responses to the user's query and select the best one.

USER QUERY:
{user_query}

AVAILABLE CONTEXT:
{json.dumps(context, indent=2)}

RESPONSE A (Mistral - course-creator-assistant):
{ensemble_responses["mistral_response"]}

RESPONSE B (LLama 3.1 8B):
{ensemble_responses["llama_response"]}

EVALUATION CRITERIA:
1. Accuracy: Which response is most factually correct based on the context?
2. Precision: Which response is more specific and directly answers the question?
3. Responsiveness: Which response is more helpful and actionable?
4. Context Alignment: Which response better uses the provided context (RAG, knowledge graph, metadata)?
5. Coherence: Which response is better structured and easier to understand?

Analyze both responses and select the best one. You can also create a hybrid response combining the strengths of both.

Respond in JSON format:
{{
    "selected_model": "mistral|llama|hybrid",
    "selected_response": "the best response or hybrid",
    "reasoning": "explanation of why this response is best",
    "confidence": 0.0-1.0,
    "strengths_a": ["strength1", "strength2"],
    "strengths_b": ["strength1", "strength2"],
    "weaknesses_a": ["weakness1"],
    "weaknesses_b": ["weakness1"]
}}
"""

        # Call frontier model (GPT-4 or Claude)
        response = await self.cloud_llm_service.generate_response(
            messages=[{"role": "user", "content": consensus_prompt}],
            system_prompt="You are an expert AI response evaluator.",
            temperature=0.3  # Lower temperature for consistent evaluation
        )

        # Parse JSON response
        return json.loads(response)
```

### Step 4: Update WebSocket Pipeline

**File**: `/services/ai-assistant-service/api/websocket.py` (modify `_process_user_message`)

```python
async def _process_user_message(self, websocket, conversation, user_message, auth_token):
    """
    Complete pipeline implementation:
    1. NLP preprocessing
    2. Parallel services (KG, Metadata, RAG)
    3. Ensemble model generation (Mistral + LLama)
    4. Frontier model consensus
    5. Function execution
    """

    # PHASE 1: NLP Preprocessing (EXISTING - NO CHANGES)
    preprocessing_result = await self.nlp_service.preprocess_query(...)

    # PHASE 2: Parallel Service Calls (ADD METADATA)
    kg_task = self._get_knowledge_graph_context(...)
    metadata_task = self.metadata_service.fuzzy_search(user_message)
    rag_task = self.rag_service.query(...)

    kg_context, metadata_results, rag_results = await asyncio.gather(
        kg_task, metadata_task, rag_task
    )

    # Format metadata context
    metadata_context = self._format_metadata_context(metadata_results)

    # PHASE 3: Ensemble Model Generation (NEW)
    ensemble_responses = await self.ensemble_service.generate_ensemble_responses(
        user_message=user_message,
        system_prompt=system_prompt,
        rag_context=rag_context,
        kg_context=kg_context,
        metadata_context=metadata_context
    )

    # PHASE 4: Frontier Model Consensus (NEW)
    consensus_result = await self.consensus_service.select_best_response(
        user_query=user_message,
        context={
            "rag": rag_context,
            "knowledge_graph": kg_context,
            "metadata": metadata_context
        },
        ensemble_responses=ensemble_responses
    )

    # Use consensus response
    response_text = consensus_result["selected_response"]

    # PHASE 5: Function Execution (EXISTING - NO CHANGES)
    # ... existing function call logic
```

---

## Benefits of This Architecture

### 1. **Improved Accuracy**
- Ensemble models provide multiple perspectives
- Frontier model selects the most accurate response
- Reduces hallucinations and errors

### 2. **Better Context Utilization**
- Metadata fuzzy search finds relevant courses even with typos
- Knowledge graph provides structured relationships
- RAG provides codebase context
- All combined for comprehensive understanding

### 3. **Cost Optimization**
- Local LLMs (Mistral/LLama) are free and fast
- Frontier model only used for consensus (shorter prompts)
- Overall cost reduction compared to all-GPT-4 approach

### 4. **Robustness**
- If one model fails, consensus can still use the other
- Parallel service calls reduce latency
- Graceful degradation if services unavailable

### 5. **Quality Assurance**
- Frontier model provides expert-level evaluation
- Hybrid responses combine strengths of both models
- Confidence scores for monitoring

---

## Performance Metrics

### Expected Latency (Parallel Execution)

- **Phase 1** (NLP): ~100ms
- **Phase 2** (Parallel Services): ~300ms (max of all parallel calls)
- **Phase 3** (Ensemble Models): ~500ms (parallel Mistral + LLama)
- **Phase 4** (Consensus): ~800ms (GPT-4 evaluation)
- **Phase 5** (Function Execution): ~200ms (if needed)

**Total**: ~1.9 seconds for complex queries requiring consensus

### Simple Query Fast Path

For simple queries (greetings, basic info):
- Skip ensemble and consensus
- Direct response: ~100ms

---

## Monitoring and Metrics

### Key Metrics to Track

1. **Response Quality**
   - Consensus confidence scores
   - User satisfaction ratings
   - Response accuracy (manual review)

2. **Model Performance**
   - Mistral vs LLama selection rate
   - Hybrid response frequency
   - Model failure rate

3. **Service Health**
   - NLP service response time
   - Metadata service response time
   - Knowledge graph service response time
   - RAG service response time
   - Ensemble generation time
   - Consensus selection time

4. **Cost Metrics**
   - Token usage per query
   - Cost per query (frontier model calls)
   - Cost savings vs all-GPT-4 approach

---

## Future Enhancements

1. **Adaptive Consensus**
   - Learn from user feedback which model to prefer
   - Adjust consensus criteria based on query type

2. **Model Fine-Tuning**
   - Continue fine-tuning Mistral on platform-specific data
   - A/B test fine-tuned vs base models

3. **Caching**
   - Cache consensus decisions for identical queries
   - Cache ensemble responses for common questions

4. **Multi-Model Ensemble**
   - Add CodeLlama for code-related queries
   - Add domain-specific models

---

## Testing Strategy

### Unit Tests
- Test each service integration independently
- Mock external service calls
- Validate response formats

### Integration Tests
- Test complete pipeline with real services
- Validate parallel execution
- Verify consensus selection logic

### E2E Tests
- Test with real user queries
- Measure latency and quality
- Validate RBAC and function execution

---

## Rollout Plan

### Phase 1: Infrastructure Setup ✅
- ✅ Local LLM service running
- ✅ Ollama models available
- ✅ NLP, KG, RAG services operational

### Phase 2: Service Integration (In Progress)
- ⏳ Create MetadataService integration
- ⏳ Create EnsembleModelService
- ⏳ Create ConsensusService
- ⏳ Update websocket handler

### Phase 3: Testing & Validation
- Unit tests for new services
- Integration tests for pipeline
- E2E tests with real users
- Performance benchmarking

### Phase 4: Production Deployment
- Feature flag for ensemble mode
- Gradual rollout (10% → 50% → 100%)
- Monitor metrics and user feedback
- Iterate based on results

---

## References

- [NLP Preprocessing Service](/services/nlp-preprocessing)
- [Metadata Service](/services/metadata-service)
- [Knowledge Graph Service](/services/knowledge-graph-service)
- [Local LLM Service](/services/local-llm-service)
- [Hybrid LLM Router](/services/ai-assistant-service/ai_assistant_service/application/services/hybrid_llm_router.py)
- [WebSocket Handler](/services/ai-assistant-service/api/websocket.py)

---

**Last Updated**: 2025-10-15
**Author**: AI Assistant Pipeline Team
**Status**: Design Complete, Implementation In Progress
