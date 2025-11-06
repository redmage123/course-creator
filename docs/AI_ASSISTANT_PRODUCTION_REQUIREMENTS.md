# AI Assistant - Production Implementation Requirements

## Current State vs. Production Ready

### Current Implementation (Demo Only)
- ✅ Pattern matching for keywords
- ✅ Simulated conversations
- ✅ UI/UX demonstration
- ❌ No real AI/LLM
- ❌ No actual action execution
- ❌ No codebase understanding

### Production Requirements

## 1. RAG System (Retrieval Augmented Generation)

### Components Needed

#### A. Vector Database
Store codebase embeddings for semantic search:

```python
# Example using Pinecone, Weaviate, or Chroma
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Index the codebase
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=codebase_docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
```

#### B. Codebase Documentation
The AI needs indexed information about:

1. **API Endpoints**
   ```
   - POST /api/v1/projects - Create new project
   - POST /api/v1/tracks - Create learning track
   - POST /api/v1/instructors - Onboard instructor
   ```

2. **Data Models**
   ```python
   class Project:
       name: str
       description: str
       organization_id: int
   ```

3. **Business Rules**
   ```
   - Projects must have unique names within an organization
   - Tracks must belong to a project
   - Instructors need email verification
   ```

4. **Workflow Documentation**
   ```
   To create a track:
   1. User must be org admin
   2. Project must exist
   3. Track name must be unique within project
   4. Level must be: beginner/intermediate/advanced
   ```

### What Gets Indexed

```
services/
├── user-management/          → API docs, data models
├── course-management/        → Course creation workflows
├── organization-management/  → Org/project/track APIs
├── content-management/       → Content generation
└── analytics/                → Metrics APIs

frontend/
├── js/                       → UI component documentation
└── html/                     → Page structure

docs/
├── API_DOCUMENTATION.md      → All API endpoints
├── WORKFLOWS.md              → Business processes
└── RBAC_DOCUMENTATION.md     → Permission requirements
```

## 2. LLM Backend Integration

### Option A: OpenAI GPT-4
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_user_request(user_input, context):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        functions=AVAILABLE_FUNCTIONS,
        function_call="auto"
    )
    return response
```

### Option B: Anthropic Claude
```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def process_user_request(user_input, context):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=AVAILABLE_TOOLS,
        messages=[
            {"role": "user", "content": user_input}
        ]
    )
    return message
```

### Option C: Self-Hosted (Llama 3, Mistral)
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-70B")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-70B")
```

## 3. Backend API Service

### Architecture
```
frontend/static/js/ai-assistant.js (UI)
    ↓ WebSocket or HTTP
services/ai-assistant-service/ (NEW)
    ↓
RAG System (Vector DB + LLM)
    ↓
Platform APIs (execute actions)
```

### Service Structure
```
services/ai-assistant-service/
├── ai_assistant/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── conversation.py
│   │   │   └── intent.py
│   │   └── services/
│   │       ├── intent_classifier.py
│   │       └── action_executor.py
│   ├── application/
│   │   └── services/
│   │       ├── rag_service.py
│   │       └── llm_service.py
│   └── infrastructure/
│       ├── repositories/
│       │   └── conversation_repository.py
│       └── external/
│           ├── openai_client.py
│           └── vector_store.py
├── api/
│   └── endpoints.py
├── rag/
│   ├── indexer.py          # Index codebase
│   ├── retriever.py        # Retrieve relevant context
│   └── embeddings.py       # Generate embeddings
└── main.py
```

## 4. Function Calling / Tool Use

### Define Available Actions
```python
AVAILABLE_FUNCTIONS = [
    {
        "name": "create_project",
        "description": "Create a new project in an organization",
        "parameters": {
            "type": "object",
            "properties": {
                "organization_id": {"type": "integer"},
                "name": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["organization_id", "name"]
        }
    },
    {
        "name": "create_track",
        "description": "Create a learning track within a project",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
                "name": {"type": "string"},
                "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "description": {"type": "string"}
            },
            "required": ["project_id", "name", "level"]
        }
    },
    # ... more functions
]
```

### Execute Actions
```python
async def execute_function(function_name, arguments, user_context):
    """Execute the requested function with proper auth"""

    # Verify user has permission
    if not await check_permission(user_context, function_name):
        return {"error": "Insufficient permissions"}

    # Execute action
    if function_name == "create_project":
        return await create_project_api(
            organization_id=arguments["organization_id"],
            name=arguments["name"],
            description=arguments.get("description", ""),
            user_id=user_context["user_id"]
        )
    elif function_name == "create_track":
        return await create_track_api(
            project_id=arguments["project_id"],
            name=arguments["name"],
            level=arguments["level"],
            description=arguments.get("description", ""),
            user_id=user_context["user_id"]
        )
    # ... more functions
```

## 5. System Prompt for AI

```python
SYSTEM_PROMPT = """You are an AI assistant for the Course Creator Platform.

CAPABILITIES:
- Create and manage projects, tracks, courses
- Onboard instructors and students
- Generate course content
- Retrieve analytics and reports
- Manage organization settings

CONTEXT AWARENESS:
- Current user: {user_role} in {organization_name}
- Available projects: {project_list}
- Recent activity: {recent_actions}

RESPONSE FORMAT:
1. Understand user intent
2. Check if you have required information
3. If missing info, ask clarifying questions
4. When ready, use function calling to execute actions
5. Confirm success and provide next steps

EXAMPLE INTERACTIONS:

User: "Create a beginner track for Python"
Assistant: I'll create a Python track. Which project should this belong to?
User: "Data Science Foundations"
Assistant: [Calls create_track function]
         ✓ Created "Python Fundamentals" track (Beginner level) in Data Science Foundations project.
         Would you like to add courses to this track?

GUIDELINES:
- Always confirm before destructive actions
- Respect RBAC permissions
- Provide helpful context and next steps
- If uncertain, ask for clarification
- Surface relevant documentation

AVAILABLE FUNCTIONS:
{function_list}
"""
```

## 6. Frontend Integration (WebSocket)

```javascript
class AIAssistant {
    constructor(config) {
        this.ws = new WebSocket('wss://localhost:8011/ws/ai-assistant');
        this.setupWebSocket();
    }

    setupWebSocket() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'thinking') {
                this.showThinkingIndicator();
            } else if (data.type === 'response') {
                this.addMessage(data.content, false);
            } else if (data.type === 'action_executed') {
                this.showActionSuccess(data.action, data.result);
            }
        };
    }

    async sendMessage(message) {
        this.ws.send(JSON.stringify({
            type: 'user_message',
            content: message,
            user_id: this.userId,
            organization_id: this.organizationId,
            context: this.getContext()
        }));
    }

    getContext() {
        return {
            current_page: window.location.pathname,
            selected_project: this.currentProjectId,
            user_role: this.userRole
        };
    }
}
```

## 7. Codebase Indexing Pipeline

```python
# scripts/index_codebase_for_ai.py

import os
from langchain.document_loaders import DirectoryLoader, PythonLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

def index_codebase():
    """Index entire codebase for RAG"""

    # 1. Load all Python files
    python_loader = DirectoryLoader(
        'services/',
        glob='**/*.py',
        loader_cls=PythonLoader
    )
    python_docs = python_loader.load()

    # 2. Load documentation
    md_loader = DirectoryLoader(
        'docs/',
        glob='**/*.md'
    )
    md_docs = md_loader.load()

    # 3. Load API schemas
    # ... load OpenAPI specs, data models, etc.

    # 4. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    all_docs = python_docs + md_docs + api_docs
    chunks = text_splitter.split_documents(all_docs)

    # 5. Create embeddings and store
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory='./ai_assistant_rag_db'
    )

    print(f"✓ Indexed {len(chunks)} chunks from codebase")
    return vectorstore

if __name__ == '__main__':
    index_codebase()
```

## 8. Retrieval Pipeline

```python
async def get_relevant_context(user_query, vectorstore):
    """Retrieve relevant code/docs for user query"""

    # 1. Semantic search in vector DB
    relevant_docs = vectorstore.similarity_search(
        user_query,
        k=5  # Top 5 most relevant
    )

    # 2. Format context for LLM
    context = "\n\n".join([
        f"RELEVANT CONTEXT {i+1}:\n{doc.page_content}"
        for i, doc in enumerate(relevant_docs)
    ])

    return context
```

## 9. Complete Request Flow

```
1. User types: "Create an intermediate Python track for Data Science project"
   ↓
2. Frontend sends to WebSocket
   ↓
3. AI Assistant Service receives
   ↓
4. RAG Retrieval:
   - Query vector DB for: "create track", "track levels", "track API"
   - Retrieve: API docs, data models, business rules
   ↓
5. LLM Processing:
   - Prompt: System prompt + User query + Retrieved context
   - LLM understands: Need to call create_track function
   - LLM extracts: project="Data Science", name="Python track", level="intermediate"
   ↓
6. Function Calling:
   - Check: Does project "Data Science" exist? → Yes (ID: 42)
   - Check: Does user have permission? → Yes (org admin)
   - Execute: POST /api/v1/tracks with proper params
   ↓
7. Response to User:
   "✓ Created 'Python Intermediate Track' in Data Science Foundations project.
    Track ID: 123. Would you like to add courses to this track?"
```

## 10. Security & Permissions

```python
async def verify_action_permission(user_context, action, resource):
    """Verify user can perform action before executing"""

    # Check RBAC
    if action == "create_track":
        # Must be org admin or project owner
        if user_context["role"] not in ["organization_admin", "site_admin"]:
            return False

    # Check resource ownership
    if resource_type == "project":
        project = await get_project(resource_id)
        if project.organization_id != user_context["organization_id"]:
            return False

    return True
```

## 11. Cost Estimation

### Vector Database
- **Pinecone**: ~$70/month (Starter, 1M vectors)
- **Weaviate**: Self-hosted (free) or ~$25/month (cloud)
- **Chroma**: Self-hosted (free)

### LLM API Costs
- **GPT-4**: ~$0.03/1K tokens input, $0.06/1K tokens output
  - Average conversation: ~2K tokens → $0.12
  - 10K conversations/month → $1,200

- **Claude**: ~$0.015/1K tokens input, $0.075/1K tokens output
  - Average conversation: ~2K tokens → $0.15
  - 10K conversations/month → $1,500

- **Self-hosted Llama 3**: $0 API costs
  - Requires GPU server: ~$500-2000/month

## 12. Implementation Timeline

**Phase 1: Basic RAG (2-3 weeks)**
- Set up vector database
- Index codebase and docs
- Basic LLM integration
- Simple query → response

**Phase 2: Function Calling (2 weeks)**
- Define function schemas
- Implement function execution
- Add permission checks
- Test action execution

**Phase 3: Context Awareness (1-2 weeks)**
- Track conversation history
- Maintain user context
- Multi-turn conversations
- Follow-up questions

**Phase 4: Production Polish (2 weeks)**
- Error handling
- Rate limiting
- Caching
- Monitoring
- Testing

**Total: 7-9 weeks**

## Conclusion

**Current Implementation**: Demo only (pattern matching)
**Production Ready**: Requires RAG system, LLM backend, function calling, and 7-9 weeks development

**Does it need the entire codebase?**
- **For Demo**: No, just hardcoded responses
- **For Production**: Yes, needs indexed codebase + docs + API schemas for RAG

The AI needs comprehensive understanding of:
- API endpoints and parameters
- Data models and relationships
- Business rules and workflows
- Permission requirements
- Current system state
