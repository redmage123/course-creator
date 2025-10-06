# NLP Preprocessing Service - Quick Reference

**Service URL:** `https://localhost:8013`
**Status:** Production Ready ✅

---

## Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "nlp-preprocessing",
  "version": "1.0.0"
}
```

---

### 2. Preprocess Query
```bash
POST /api/v1/preprocess
Content-Type: application/json

{
  "query": "Find beginner courses about machine learning",
  "conversation_history": null,  // Optional
  "enable_deduplication": false,  // Optional, default: true
  "deduplication_threshold": 0.95  // Optional, default: 0.95
}
```

**Response:**
```json
{
  "intent": {
    "intent_type": "course_lookup",
    "confidence": 0.8,
    "keywords": ["courses about"],
    "should_call_llm": false,
    "metadata": {...}
  },
  "entities": [
    {
      "text": "beginner",
      "entity_type": "difficulty",
      "confidence": 0.9,
      "span": [5, 13],
      "metadata": {...}
    },
    {
      "text": "machine learning",
      "entity_type": "topic",
      "confidence": 0.7,
      "span": [28, 44],
      "metadata": {...}
    }
  ],
  "expanded_query": {
    "original": "Find beginner courses about machine learning",
    "expansions": ["find beginner courses about ml"],
    "combined": "(Find beginner courses about machine learning) OR (find beginner courses about ml)",
    "expansion_terms": {"machine learning": ["ml"]}
  },
  "should_call_llm": false,
  "direct_response": {
    "type": "course_lookup",
    "routing": "metadata-service",
    "search_criteria": {...}
  },
  "processing_time_ms": 0.402,
  "metadata": {...},
  "original_history_length": 0,
  "deduplicated_history_length": null
}
```

---

### 3. Service Statistics
```bash
GET /api/v1/stats
```

**Response:**
```json
{
  "service": "nlp-preprocessing",
  "components": {
    "intent_classifier": "active",
    "entity_extractor": "active",
    "query_expander": "active",
    "similarity_algorithms": "active"
  },
  "capabilities": {
    "intent_types": 9,
    "entity_types": 6,
    "synonyms": 40,
    "performance_target_ms": 20
  }
}
```

---

## Intent Types (9)

| Intent Type | Description | LLM Required | Example Query |
|-------------|-------------|--------------|---------------|
| `greeting` | User greeting | ❌ No | "Hello", "Hi there" |
| `course_lookup` | Find courses | ❌ No | "Find beginner courses about ML" |
| `skill_lookup` | Find by skill | ❌ No | "Courses teaching Python" |
| `prerequisite_check` | Check prerequisites | ❌ No | "What do I need for Advanced Python?" |
| `learning_path` | Get learning path | ❌ No | "How do I learn data science?" |
| `feedback` | User feedback | ❌ No | "This course is great!" |
| `concept_explanation` | Explain concept | ✅ Yes | "Explain gradient descent" |
| `question` | General question | ✅ Yes | "What is backpropagation?" |
| `command` | System command | ✅ Yes | "Reset my progress" |
| `clarification` | Clarification | ✅ Yes | "Can you explain that again?" |
| `unknown` | Unknown intent | ✅ Yes | Ambiguous queries |

---

## Entity Types (6)

| Entity Type | Description | Example Extractions |
|-------------|-------------|---------------------|
| `course` | Course names | "Python Advanced", "Machine Learning 101" |
| `topic` | Subject topics | "machine learning", "data science" |
| `skill` | Skills/technologies | "Python", "JavaScript", "Docker" |
| `concept` | Technical concepts | "gradient descent", "neural networks" |
| `difficulty` | Difficulty level | "beginner", "intermediate", "advanced" |
| `duration` | Time duration | "2 weeks", "3 months", "10 hours" |

---

## Query Expansion (40+ Terms)

### Acronyms
- ML → machine learning
- AI → artificial intelligence
- DL → deep learning
- NLP → natural language processing
- CNN → convolutional neural network
- RNN → recurrent neural network
- API → application programming interface
- REST → representational state transfer
- SQL → structured query language
- NoSQL → not only sql
- And 30+ more...

### Synonyms
- python → python programming, python language
- javascript → js, ecmascript
- data science → data analysis, data analytics
- docker → containerization
- kubernetes → k8s, container orchestration

---

## Usage Examples

### Example 1: Greeting (Bypass LLM)
```bash
curl -k -X POST https://localhost:8013/api/v1/preprocess \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello"}'
```

**Result:**
- Intent: `greeting`
- Should call LLM: `false`
- Direct response: Canned greeting with suggestions
- Cost savings: 100%

---

### Example 2: Course Lookup (Bypass LLM)
```bash
curl -k -X POST https://localhost:8013/api/v1/preprocess \
  -H "Content-Type: application/json" \
  -d '{"query": "Find beginner ML courses"}'
```

**Result:**
- Intent: `course_lookup`
- Entities: difficulty="beginner", topic="ML"
- Expanded: "ML" → "machine learning"
- Should call LLM: `false`
- Routes to: metadata-service
- Cost savings: 100%

---

### Example 3: Complex Query (Use LLM)
```bash
curl -k -X POST https://localhost:8013/api/v1/preprocess \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain how neural networks learn"}'
```

**Result:**
- Intent: `concept_explanation`
- Should call LLM: `true`
- Direct response: `null`
- Query sent to LLM with expanded terms

---

## Performance Benchmarks

| Component | Performance | Target | Status |
|-----------|-------------|--------|--------|
| Cosine Similarity | 217.8 ns | <1 μs | ✅ 4.6x faster |
| Entity Extraction | 42.7 μs | <10 ms | ✅ 234x faster |
| Query Expansion | 49.7 μs | <5 ms | ✅ 100x faster |
| Intent Classification | 111.0 μs | <5 ms | ✅ 45x faster |
| **Full Pipeline** | **374.5 μs** | **<20 ms** | **✅ 53x faster** |

---

## Integration Pattern (Frontend)

```javascript
// Step 0: NLP Preprocessing
const nlpResult = await fetch('https://localhost:8013/api/v1/preprocess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: userMessage,
        enable_deduplication: false
    })
}).then(r => r.json());

// Check if we can bypass LLM
if (!nlpResult.should_call_llm && nlpResult.direct_response) {
    // Use direct response (cost savings!)
    return handleDirectResponse(nlpResult);
} else {
    // Continue to LLM with expanded query
    const searchQuery = nlpResult.expanded_query?.combined || userMessage;
    return queryLLM(searchQuery, nlpResult);
}
```

---

## Troubleshooting

### Service Not Responding
```bash
# Check if container is running
docker ps --filter "name=nlp-preprocessing"

# Check logs
docker logs course-creator_nlp-preprocessing_1 --tail 50

# Restart service
docker-compose restart nlp-preprocessing
```

### Health Check Failing
```bash
# Test manually
curl -k https://localhost:8013/health

# Check if SSL certs are mounted
docker exec course-creator_nlp-preprocessing_1 ls -la /app/certs
```

### Slow Performance
```bash
# Check CPU usage
docker stats course-creator_nlp-preprocessing_1

# Verify Numba compilation cache exists
docker exec course-creator_nlp-preprocessing_1 ls -la /root/.numba_cache
```

---

## Testing

### Run Unit Tests (90 tests)
```bash
cd /home/bbrelin/course-creator/services/nlp-preprocessing
PYTHONPATH=$PWD:$PYTHONPATH python -m pytest tests/ -v
```

### Run Integration Tests (5 tests)
```bash
/tmp/run_nlp_tests.sh
```

### Browser Test Page
```
https://localhost:3001/test_nlp_integration.html
```

---

## Configuration

### Environment Variables
- `SERVICE_NAME`: "nlp-preprocessing"
- `LOG_LEVEL`: "INFO"
- `PYTHONPATH`: "/app"

### Docker Volumes
- `/app/certs` → SSL certificates (read-only)
- `/var/log/course-creator` → Service logs

### Ports
- `8013` → NLP preprocessing service (HTTPS)

---

## Cost Savings Calculation

**Assumptions:**
- 1000 queries/day
- 50% require LLM (concept explanations, complex questions)
- 50% bypass LLM (greetings, course lookups, prerequisites)
- Cost per LLM call: $0.001

**Daily Savings:**
- 500 queries × $0.001 = **$0.50/day**

**Annual Savings:**
- $0.50 × 365 = **$182.50/year**

**At Scale (100K queries/day):**
- 50,000 queries × $0.001 = **$50/day**
- $50 × 365 = **$18,250/year**

---

## Support

### Documentation
- Full Test Report: `/tmp/NLP_INTEGRATION_TEST_REPORT.md`
- Integration Status: `/tmp/FINAL_INTEGRATION_STATUS.md`
- This Quick Reference: `/home/bbrelin/course-creator/services/nlp-preprocessing/QUICK_REFERENCE.md`

### Service Logs
```bash
docker logs course-creator_nlp-preprocessing_1 -f
```

### Source Code
- Service: `/home/bbrelin/course-creator/services/nlp-preprocessing/`
- Frontend Integration: `/home/bbrelin/course-creator/frontend/js/modules/ai-assistant.js`

---

**Last Updated:** 2025-10-05
**Version:** 1.0.0
**Status:** Production Ready ✅
