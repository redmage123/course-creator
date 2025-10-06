"""
NLP Preprocessing Service

BUSINESS CONTEXT:
Lightweight NLP preprocessing to reduce LLM costs by 30-40%
and improve response latency for simple queries.

ARCHITECTURE:
- Intent classification (rule-based)
- Entity extraction (regex + metadata)
- Query expansion (RAG embeddings)
- Semantic deduplication (Numba/NumPy optimized)
"""
