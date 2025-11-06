"""
WebSocket API - AI Assistant Service

BUSINESS PURPOSE:
Provides real-time WebSocket communication for AI assistant chat.
Enables streaming responses and interactive conversations.

TECHNICAL IMPLEMENTATION:
FastAPI WebSocket endpoint for bidirectional communication. Manages
conversation state, LLM streaming, and action execution.
"""

import json
import logging
from typing import Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from ai_assistant_service.domain.entities.conversation import (
    Conversation,
    UserContext
)
from ai_assistant_service.domain.entities.message import MessageRole
from ai_assistant_service.application.services.llm_service import LLMService
from ai_assistant_service.application.services.rag_service import RAGService
from ai_assistant_service.application.services.function_executor import FunctionExecutor
from ai_assistant_service.application.services.nlp_service import NLPService
from ai_assistant_service.application.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class AIAssistantWebSocketHandler:
    """
    WebSocket handler for AI assistant

    BUSINESS PURPOSE:
    Manages real-time conversation between user and AI assistant.
    Orchestrates LLM, RAG, and function execution for each message.

    TECHNICAL IMPLEMENTATION:
    - Maintains conversation state per WebSocket connection
    - Coordinates LLM, RAG, and function executor services
    - Sends typing indicators and streaming responses
    - Handles errors gracefully with user-friendly messages

    ATTRIBUTES:
        llm_service: LLM service for AI responses
        rag_service: RAG service for codebase context
        function_executor: Function executor for actions
        nlp_service: NLP service for preprocessing and optimization
        kg_service: Knowledge graph service for course recommendations
        conversations: Active conversations by connection ID
    """

    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        function_executor: FunctionExecutor,
        nlp_service: NLPService,
        kg_service: KnowledgeGraphService
    ):
        """Initialize WebSocket handler with services"""
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.function_executor = function_executor
        self.nlp_service = nlp_service
        self.kg_service = kg_service
        self.conversations: Dict[str, Conversation] = {}

        logger.info("AI Assistant WebSocket handler initialized with NLP and Knowledge Graph services")

    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle WebSocket connection

        BUSINESS PURPOSE:
        Manages full lifecycle of WebSocket connection. Accepts connection,
        processes messages, executes actions, and handles disconnection.

        TECHNICAL IMPLEMENTATION:
        1. Accept WebSocket connection
        2. Receive user context and auth token
        3. Create conversation
        4. Process messages in loop
        5. Close gracefully on disconnect

        ARGS:
            websocket: FastAPI WebSocket connection
        """
        await websocket.accept()
        logger.info("WebSocket connection accepted")

        conversation_id = None

        try:
            # Wait for initialization message with user context
            init_message = await websocket.receive_json()

            if init_message.get("type") != "init":
                await websocket.send_json({
                    "type": "error",
                    "content": "First message must be 'init' type with user context"
                })
                await websocket.close()
                return

            # Extract user context
            user_data = init_message.get("user_context", {})
            auth_token = init_message.get("auth_token", "")

            user_context = UserContext(
                user_id=user_data.get("user_id"),
                username=user_data.get("username", "Unknown"),
                role=user_data.get("role", "student"),
                organization_id=user_data.get("organization_id"),
                current_page=user_data.get("current_page")
            )

            # Create conversation
            conversation = Conversation(user_context=user_context)
            conversation_id = conversation.conversation_id
            self.conversations[conversation_id] = conversation

            logger.info(
                f"Conversation started: "
                f"id={conversation_id}, "
                f"user={user_context.username}, "
                f"role={user_context.role}"
            )

            # Send confirmation
            await websocket.send_json({
                "type": "connected",
                "conversation_id": conversation_id
            })

            # Process messages
            while True:
                message_data = await websocket.receive_json()

                if message_data.get("type") == "user_message":
                    await self._process_user_message(
                        websocket,
                        conversation,
                        message_data.get("content", ""),
                        auth_token
                    )
                elif message_data.get("type") == "clear_history":
                    conversation.clear_history()
                    await websocket.send_json({
                        "type": "history_cleared"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {message_data.get('type')}"
                    })

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: conversation_id={conversation_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "content": "An error occurred. Please try again."
                })
            except:
                pass
        finally:
            # Cleanup conversation
            if conversation_id and conversation_id in self.conversations:
                del self.conversations[conversation_id]
                logger.info(f"Conversation cleaned up: {conversation_id}")

    async def _process_user_message(
        self,
        websocket: WebSocket,
        conversation: Conversation,
        user_message: str,
        auth_token: str
    ) -> None:
        """
        Process user message and generate response

        BUSINESS PURPOSE:
        Orchestrates complete message processing flow with intelligent preprocessing:
        1. NLP preprocessing (intent, entities, query expansion, deduplication)
        2. Knowledge graph context (course recommendations, prerequisites)
        3. RAG retrieval with expanded query
        4. LLM response generation (only if needed)
        5. Function execution with RBAC validation

        TECHNICAL IMPLEMENTATION:
        - Shows typing indicator during processing
        - Uses NLP preprocessing to optimize costs and performance
        - Integrates knowledge graph for course-related queries
        - Retrieves RAG context with expanded queries
        - Calls LLM with optimized context and function schemas
        - Executes function calls with RBAC validation
        - Sends structured response to frontend

        ARGS:
            websocket: WebSocket connection
            conversation: Active conversation
            user_message: User's message text
            auth_token: Auth token for API calls
        """
        try:
            # Add user message to conversation
            conversation.add_message(MessageRole.USER, user_message)

            # Send thinking indicator
            await websocket.send_json({
                "type": "thinking"
            })

            # ===== PHASE 1: NLP PREPROCESSING =====
            # Perform intelligent preprocessing for cost optimization and better results
            preprocessing_result = await self.nlp_service.preprocess_query(
                query=user_message,
                conversation_history=conversation.messages[:-1]  # Exclude current message
            )

            intent_result = preprocessing_result["intent"]
            entities = preprocessing_result["entities"]
            expanded_query = preprocessing_result["expanded_query"]
            deduplicated_history = preprocessing_result["deduplicated_history"]
            should_call_llm = preprocessing_result["should_call_llm"]
            metrics = preprocessing_result["metrics"]

            logger.info(
                f"NLP preprocessing complete: "
                f"intent={intent_result.get('intent_type')}, "
                f"entities={len(entities)}, "
                f"tokens_saved={metrics['estimated_token_savings']}"
            )

            # ===== PHASE 2: KNOWLEDGE GRAPH CONTEXT =====
            # Enhance responses with knowledge graph data for course-related queries
            kg_context = ""
            intent_type = intent_result.get("intent_type", "")

            # Check if query is course-related
            if any(keyword in user_message.lower() for keyword in [
                "course", "learn", "skill", "prerequisite", "recommend", "path"
            ]):
                kg_context = await self._get_knowledge_graph_context(
                    user_message=user_message,
                    user_id=conversation.user_context.user_id,
                    intent_type=intent_type,
                    entities=entities
                )

            # ===== PHASE 3: RAG RETRIEVAL =====
            # Use expanded query for better retrieval
            search_query = user_message
            if expanded_query["expanded_keywords"]:
                # Combine original query with top expanded keywords
                keywords = " ".join(expanded_query["expanded_keywords"][:3])
                search_query = f"{user_message} {keywords}"

            rag_results = await self.rag_service.query(
                query=search_query,
                n_results=3
            )

            rag_context = self.rag_service.format_context_for_llm(rag_results)

            # ===== PHASE 4: CHECK IF LLM CALL IS NEEDED =====
            # Simple queries (greetings, basic info) can skip LLM
            if not should_call_llm:
                # Handle simple queries without LLM
                response_text = self._handle_simple_query(
                    intent_type=intent_type,
                    user_message=user_message
                )

                # Add AI response to conversation
                ai_message = conversation.add_message(MessageRole.ASSISTANT, response_text)
                ai_message.add_metadata("llm_called", False)

                # Send response
                await websocket.send_json({
                    "type": "response",
                    "content": response_text,
                    "function_call": None,
                    "action_success": None
                })

                logger.info(
                    f"Simple query handled without LLM: "
                    f"intent={intent_type}"
                )
                return

            # ===== PHASE 5: LLM RESPONSE GENERATION =====
            # Build system prompt with all context
            system_prompt = self._build_system_prompt(
                user_context=conversation.user_context,
                rag_context=rag_context,
                kg_context=kg_context,
                entities=entities
            )

            # Get available functions for user role
            available_functions = FunctionExecutor.get_available_functions()

            # Use deduplicated history for LLM call (cost optimization)
            optimized_messages = deduplicated_history + [conversation.messages[-1]]

            # Generate LLM response
            response_text, function_call = await self.llm_service.generate_response(
                messages=optimized_messages,
                system_prompt=system_prompt,
                available_functions=available_functions
            )

            # ===== PHASE 6: FUNCTION EXECUTION =====
            # Execute function if requested
            action_result = None
            if function_call:
                logger.info(f"Executing function: {function_call.function_name}")

                action_result = await self.function_executor.execute(
                    function_call=function_call,
                    user_context=conversation.user_context,
                    auth_token=auth_token
                )

                # Add function result to response
                if action_result.success:
                    response_text += f"\n\n{action_result.to_user_message()}"
                else:
                    response_text = action_result.to_user_message()

            # Add AI response to conversation
            ai_message = conversation.add_message(MessageRole.ASSISTANT, response_text)

            # Add metadata
            ai_message.add_metadata("llm_called", True)
            ai_message.add_metadata("intent", intent_type)
            ai_message.add_metadata("entities_count", len(entities))
            ai_message.add_metadata("tokens_saved", metrics["estimated_token_savings"])
            if function_call:
                ai_message.add_metadata("function_call", function_call.function_name)
            if action_result:
                ai_message.add_metadata("action_result", action_result.success)

            # Send response to user
            await websocket.send_json({
                "type": "response",
                "content": response_text,
                "function_call": function_call.function_name if function_call else None,
                "action_success": action_result.success if action_result else None
            })

            logger.info(
                f"Response sent: "
                f"conversation_id={conversation.conversation_id}, "
                f"intent={intent_type}, "
                f"function_call={function_call.function_name if function_call else None}, "
                f"tokens_saved={metrics['estimated_token_savings']}"
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await websocket.send_json({
                "type": "error",
                "content": "I encountered an error processing your request. Please try again."
            })

    async def _get_knowledge_graph_context(
        self,
        user_message: str,
        user_id: int,
        intent_type: str,
        entities: List[Dict[str, Any]]
    ) -> str:
        """
        Get knowledge graph context for course-related queries

        BUSINESS PURPOSE:
        Enhances AI responses with course relationships, prerequisites,
        and learning path recommendations from knowledge graph.

        TECHNICAL IMPLEMENTATION:
        Based on intent and entities, queries knowledge graph for:
        - Course recommendations
        - Prerequisites
        - Learning paths
        - Related courses

        ARGS:
            user_message: User's query
            user_id: User ID for personalized recommendations
            intent_type: Classified intent
            entities: Extracted entities

        RETURNS:
            Formatted knowledge graph context string
        """
        try:
            kg_data = []

            # Get course recommendations for skill-based queries
            if any(word in user_message.lower() for word in ["learn", "skill", "path"]):
                # Extract skill from message (simplified - could be enhanced with NER)
                skill_keywords = ["python", "javascript", "java", "data science", "machine learning"]
                for skill in skill_keywords:
                    if skill in user_message.lower():
                        path = await self.kg_service.get_learning_path(
                            user_id=user_id,
                            target_skill=skill.title()
                        )
                        if path and path.get("courses"):
                            kg_data.append(
                                f"**Learning Path for {skill.title()}:**\n"
                                f"- {len(path['courses'])} courses\n"
                                f"- Total duration: {path.get('total_duration', 0)} hours\n"
                                f"- Difficulty: {' → '.join(path.get('difficulty_progression', []))}"
                            )
                        break

            # Get course recommendations based on progress
            if any(word in user_message.lower() for word in ["recommend", "next", "what should"]):
                recommendations = await self.kg_service.recommend_next_course(
                    user_id=user_id,
                    max_recommendations=3
                )
                if recommendations:
                    kg_data.append("**Recommended Courses:**")
                    for rec in recommendations[:3]:
                        kg_data.append(
                            f"- {rec.get('title', 'Unknown')} "
                            f"(relevance: {rec.get('relevance_score', 0):.2f})"
                        )

            # Get prerequisites for specific course
            if "prerequisite" in user_message.lower():
                # Try to extract course ID from entities (simplified)
                for entity in entities:
                    if entity.get("entity_type") == "course_id":
                        course_id = int(entity.get("text", 0))
                        prerequisites = await self.kg_service.get_prerequisites(course_id)
                        if prerequisites:
                            kg_data.append("**Prerequisites:**")
                            for prereq in prerequisites:
                                kg_data.append(f"- {prereq.get('title', 'Unknown')}")

            if kg_data:
                return "\nKNOWLEDGE GRAPH CONTEXT:\n" + "\n".join(kg_data) + "\n"
            else:
                return ""

        except Exception as e:
            logger.error(f"Failed to get knowledge graph context: {e}")
            return ""

    def _handle_simple_query(
        self,
        intent_type: str,
        user_message: str
    ) -> str:
        """
        Handle simple queries without calling LLM

        BUSINESS PURPOSE:
        Reduces LLM API costs by handling common simple queries
        with predefined responses.

        TECHNICAL IMPLEMENTATION:
        Maps intent types to appropriate responses.
        Greetings, basic info, and help queries handled here.

        ARGS:
            intent_type: Classified intent
            user_message: User's message

        RETURNS:
            Response text
        """
        # Simple greeting responses
        if intent_type == "greeting":
            return (
                "Hello! I'm your AI assistant for the Course Creator Platform. "
                "I can help you with:\n"
                "- Creating projects, tracks, and courses\n"
                "- Onboarding instructors\n"
                "- Generating course content\n"
                "- Viewing analytics\n"
                "- Answering questions about the platform\n\n"
                "What would you like to do today?"
            )

        # Help requests
        if intent_type == "help_question":
            return (
                "I'm here to help! Here are some things you can ask me:\n\n"
                "📚 **Creating Content:**\n"
                "- \"Create a beginner Python track in Data Science project\"\n"
                "- \"Generate a course on machine learning\"\n\n"
                "👥 **Managing Users:**\n"
                "- \"Onboard a new instructor\"\n"
                "- \"Add instructor John to my organization\"\n\n"
                "📊 **Analytics:**\n"
                "- \"Show me analytics for my organization\"\n"
                "- \"What are my top courses?\"\n\n"
                "❓ **Questions:**\n"
                "- \"How do I create a project?\"\n"
                "- \"What is a track?\"\n\n"
                "Just type your question or request!"
            )

        # Default fallback (shouldn't reach here often)
        return (
            "I'm not sure I understood that correctly. "
            "Could you rephrase your question or request?"
        )

    def _build_system_prompt(
        self,
        user_context: UserContext,
        rag_context: str,
        kg_context: str = "",
        entities: List[Dict[str, Any]] = None
    ) -> str:
        """
        Build system prompt for LLM

        BUSINESS PURPOSE:
        Creates context-aware system prompt for AI assistant. Includes
        user role, available actions, codebase context from RAG,
        knowledge graph data, and extracted entities.

        TECHNICAL IMPLEMENTATION:
        Formats system prompt with user context, RAG results,
        knowledge graph recommendations, and NLP-extracted entities.
        Defines AI assistant's capabilities and response guidelines.

        ARGS:
            user_context: User identity and role
            rag_context: Formatted RAG search results
            kg_context: Knowledge graph context (course recommendations, paths)
            entities: Extracted entities from NLP preprocessing

        RETURNS:
            Complete system prompt string
        """
        entities_str = ""
        if entities:
            entities_str = "\nEXTRACTED ENTITIES:\n"
            for entity in entities[:5]:  # Limit to top 5
                entities_str += (
                    f"- {entity.get('text')}: "
                    f"{entity.get('entity_type')} "
                    f"(confidence: {entity.get('confidence', 0):.2f})\n"
                )

        return f"""You are an AI assistant for the Course Creator Platform.

USER CONTEXT:
- Name: {user_context.username}
- Role: {user_context.role}
- Organization ID: {user_context.organization_id}
- Current Page: {user_context.current_page or 'Unknown'}

CAPABILITIES:
- Answer questions about the platform
- Create and manage projects, tracks, courses
- Onboard instructors and students
- Generate course content
- Retrieve analytics and reports
- Manage organization settings
- Recommend learning paths and courses
- Check prerequisites and course relationships

{rag_context}
{kg_context}
{entities_str}

RESPONSE GUIDELINES:
1. Be helpful, concise, and accurate
2. Use the codebase context above to inform your answers
3. If you need to execute an action, use function calling
4. If information is missing, ask clarifying questions
5. Respect user's role and permissions
6. Provide step-by-step guidance when needed
7. Include relevant examples from the codebase

EXAMPLE INTERACTIONS:

User: "Create a beginner track for Python"
Assistant: I'll create a Python track. Which project should this belong to?
User: "Data Science Foundations"
Assistant: [Calls create_track function]
         ✓ Created "Python Fundamentals" track (Beginner level) in Data Science Foundations project.
         Would you like to add courses to this track?

User: "How do I create a project?"
Assistant: [Uses codebase context to explain]
         To create a project, you need to:
         1. Navigate to your organization dashboard
         2. Click "Create New Project"
         3. Fill in the project name and description
         4. Click "Create Project"

         As an {user_context.role}, you can create projects in your organization.
         Would you like me to create one for you?

Remember: Always confirm before executing destructive actions, provide context from the codebase when answering questions, and respect RBAC permissions.
"""
