# AI Assistant Service

Production-ready AI assistant for Course Creator Platform. Provides natural language interface for platform operations using LLM + RAG + NLP + Knowledge Graph + function calling.

**Status:** ✅ **PRODUCTION READY** (Fully Dockerized)

## Quick Start (Docker)

```bash
# 1. Set API keys
echo "LLM_PROVIDER=openai" >> .cc_env
echo "OPENAI_API_KEY=sk-..." >> .cc_env

# 2. Start service
docker-compose up -d ai-assistant-service

# 3. Test health
curl -k https://localhost:8011/api/v1/ai-assistant/health

# 4. Connect WebSocket
# wss://localhost:8011/ws/ai-assistant
```

**Full Docker Documentation:** [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

## Features

### 🤖 Natural Language Understanding
- **OpenAI GPT-4** or **Anthropic Claude 3.5 Sonnet** integration
- Context-aware responses using conversation history
- Intent recognition and entity extraction

### 📚 RAG (Retrieval Augmented Generation)
- Integrates with existing RAG service (port 8009)
- Semantic search over codebase documentation
- Accurate answers about platform features and APIs

### ⚡ Function Calling
- Execute platform actions via natural language
- RBAC permission enforcement
- Available functions:
  - `create_project` - Create new project
  - `create_track` - Create learning track
  - `onboard_instructor` - Onboard instructor
  - `create_course` - Create course
  - `get_analytics` - Retrieve analytics

### 🔒 Security
- RBAC validation before action execution
- Authentication token validation
- SSL/TLS encryption
- Input sanitization

### 🌐 Real-Time Communication
- WebSocket API for streaming responses
- Typing indicators
- Multi-turn conversations
- Conversation history management

## Architecture

```
Frontend (WebSocket Client)
    ↓
AI Assistant Service (port 8011)
    ↓
┌───────────────┬──────────────┬────────────────┐
│               │              │                │
RAG Service   LLM API    Platform APIs
(port 8009)   (OpenAI/   (ports 8000-8008)
              Claude)
```

## Installation

### 1. Install Dependencies

```bash
cd services/ai-assistant-service
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required configuration:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM API key
- `RAG_SERVICE_URL` - RAG service endpoint (default: https://localhost:8009)
- `PLATFORM_API_URL` - Platform API base URL (default: https://localhost)

### 3. Start Service

```bash
python main.py
```

Service will start on port 8011 with HTTPS + WebSocket support.

## Usage

### WebSocket Client Example

```javascript
const ws = new WebSocket('wss://localhost:8011/ws/ai-assistant');

// Initialize connection with user context
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'init',
        user_context: {
            user_id: 123,
            username: 'john_doe',
            role: 'organization_admin',
            organization_id: 1,
            current_page: '/dashboard'
        },
        auth_token: 'your_auth_token_here'
    }));
};

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'connected') {
        console.log('Connected:', data.conversation_id);
    } else if (data.type === 'thinking') {
        console.log('AI is thinking...');
    } else if (data.type === 'response') {
        console.log('AI:', data.content);
        if (data.function_call) {
            console.log('Function executed:', data.function_call);
        }
    }
};

// Send user message
ws.send(JSON.stringify({
    type: 'user_message',
    content: 'Create a beginner track for Python in Data Science project'
}));
```

### HTTP API Endpoints

**Health Check**
```bash
GET /api/v1/ai-assistant/health
```

**Service Statistics**
```bash
GET /api/v1/ai-assistant/stats
```

**Available Functions**
```bash
GET /api/v1/ai-assistant/functions
```

## Development

### Project Structure

```
services/ai-assistant-service/
├── ai_assistant_service/
│   ├── __init__.py
│   ├── domain/                  # Domain entities
│   │   ├── entities/
│   │   │   ├── message.py      # Message entity
│   │   │   ├── conversation.py # Conversation entity
│   │   │   └── intent.py       # Intent & function schemas
│   │   └── services/           # Domain services
│   ├── application/             # Application services
│   │   └── services/
│   │       ├── llm_service.py      # LLM integration
│   │       ├── rag_service.py      # RAG client
│   │       └── function_executor.py # Action execution
│   └── infrastructure/          # Infrastructure layer
│       ├── repositories/        # Data persistence
│       └── external/            # External API clients
├── api/
│   └── websocket.py            # WebSocket handler
├── main.py                     # FastAPI application
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

### Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=ai_assistant_service tests/
```

## Configuration

### LLM Provider Selection

**OpenAI (Default)**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

**Anthropic Claude**
```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```

### RAG Service Configuration

The AI assistant uses the existing RAG service at port 8009. Ensure RAG service is running and indexed with codebase documentation:

```bash
# Check RAG service health
curl https://localhost:8009/api/v1/rag/health

# Get RAG stats
curl https://localhost:8009/api/v1/rag/stats
```

### Function Configuration

Functions are defined in `function_executor.py`. Each function specifies:
- Name and description
- Required parameters
- RBAC roles allowed to execute
- API endpoint to call

## Indexing Codebase in RAG

To enable AI assistant to answer questions about the codebase, index documentation in RAG service:

```python
# Example: Index API documentation
import httpx

async def index_documentation():
    rag_url = "https://localhost:8009/api/v1/rag/add-document"

    # Read API documentation
    with open("docs/API_DOCUMENTATION.md") as f:
        content = f.read()

    # Add to RAG
    response = await httpx.post(rag_url, json={
        "content": content,
        "metadata": {
            "source": "API_DOCUMENTATION.md",
            "category": "api_docs"
        },
        "domain": "demo_tour_guide"
    })
```

See `scripts/index_codebase_for_ai.py` for full indexing pipeline.

## Troubleshooting

### Issue: "RAG Service not reachable"
**Solution**: Ensure RAG service is running on port 8009
```bash
curl https://localhost:8009/api/v1/rag/health
```

### Issue: "OpenAI API key not found"
**Solution**: Set OPENAI_API_KEY in .env file
```bash
export OPENAI_API_KEY=sk-...
```

### Issue: "Function execution failed"
**Solution**: Check platform API services are running
```bash
./scripts/app-control.sh status
```

### Issue: "RBAC denied"
**Solution**: User role doesn't have permission for requested action. Check function RBAC requirements in `function_executor.py`.

## Production Deployment

### Environment Variables

```bash
AI_ASSISTANT_PORT=8011
LLM_PROVIDER=openai
OPENAI_API_KEY=<production_key>
RAG_SERVICE_URL=https://rag-service:8009
PLATFORM_API_URL=https://api.courseplatform.com
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Monitoring

- Health check: `GET /api/v1/ai-assistant/health`
- Metrics: `GET /api/v1/ai-assistant/stats`
- Logs: Standard output with structured logging

## Cost Estimation

### LLM API Costs

**OpenAI GPT-4:**
- Input: ~$0.03/1K tokens
- Output: ~$0.06/1K tokens
- Average conversation: ~2K tokens → $0.12
- 10K conversations/month → $1,200/month

**Anthropic Claude:**
- Input: ~$0.015/1K tokens
- Output: ~$0.075/1K tokens
- Average conversation: ~2K tokens → $0.15
- 10K conversations/month → $1,500/month

### Infrastructure Costs

- RAG service: Included (existing service)
- Vector database: $0 (ChromaDB self-hosted)
- Server: Based on deployment environment

## License

Copyright © 2025 Course Creator Platform
