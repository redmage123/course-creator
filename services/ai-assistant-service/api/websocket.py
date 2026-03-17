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
from typing import Dict, Any, List, Optional
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

# Import student AI prompts for pedagogically-sound student interactions
try:
    from ai_assistant_service.application.services.student_ai_prompts import (
        StudentInteractionContext,
        StudentSkillLevel,
        STUDENT_SYSTEM_PROMPT,
        get_student_prompt,
        get_emotional_support,
        build_contextual_prompt
    )
    STUDENT_PROMPTS_AVAILABLE = True
except ImportError:
    STUDENT_PROMPTS_AVAILABLE = False

# Import onboarding prompts for first-time user welcome experience
try:
    from ai_assistant_service.application.services.onboarding_prompts import (
        OnboardingPhase,
        UserRole as OnboardingUserRole,
        get_welcome_prompt,
        get_tour_prompt,
        get_help_prompt,
        get_faq_answer,
        search_faq,
        build_onboarding_prompt,
        FAQ_CONTENT,
        CONTEXTUAL_HELP_PROMPTS
    )
    ONBOARDING_PROMPTS_AVAILABLE = True
except ImportError:
    ONBOARDING_PROMPTS_AVAILABLE = False

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

        # Student skill level tracking (could be enhanced with persistent storage)
        self.student_skill_levels: Dict[str, str] = {}

        logger.info(
            f"AI Assistant WebSocket handler initialized. "
            f"Student prompts available: {STUDENT_PROMPTS_AVAILABLE}"
        )

    def _is_student_role(self, user_context: UserContext) -> bool:
        """
        Check if user is a student for pedagogical prompt selection.

        WHAT: Determines if user should receive student-focused prompts.
        WHY: Students need pedagogically-sound, encouraging responses.
        HOW: Checks user role against student roles.

        Args:
            user_context: User's context information

        Returns:
            True if user is a student
        """
        student_roles = {"student", "learner", "trainee"}
        return user_context.role.lower() in student_roles

    def _detect_student_emotion(self, message: str) -> Optional[str]:
        """
        Detect emotional state in student message.

        WHAT: Identifies frustration, confusion, or other emotions.
        WHY: Enables appropriate emotional support in responses.
        HOW: Uses keyword detection (could be enhanced with ML).

        Args:
            message: The user's message

        Returns:
            Detected emotion or None
        """
        message_lower = message.lower()

        emotion_patterns = {
            "frustrated": [
                "frustrated", "frustrating", "stuck", "can't figure",
                "doesn't work", "hate", "annoying", "giving up", "ugh"
            ],
            "confused": [
                "confused", "don't understand", "what does", "unclear",
                "lost", "make sense", "huh", "doesn't make sense"
            ],
            "discouraged": [
                "never get", "too hard", "can't do", "stupid", "dumb",
                "give up", "failing", "hopeless"
            ],
            "anxious": [
                "worried", "nervous", "scared", "stress", "anxious",
                "deadline", "panic", "test", "exam"
            ],
            "excited": [
                "excited", "awesome", "amazing", "great", "love",
                "cool", "finally", "got it"
            ],
            "accomplished": [
                "it works", "solved", "figured out", "success",
                "did it", "passed", "completed"
            ]
        }

        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return emotion

        return None

    def _get_student_interaction_context(
        self,
        user_message: str,
        current_page: Optional[str]
    ) -> StudentInteractionContext:
        """
        Determine the appropriate student interaction context.

        WHAT: Maps user situation to learning context for prompts.
        WHY: Different contexts require different pedagogical approaches.
        HOW: Analyzes message content and current page.

        Args:
            user_message: The user's message
            current_page: Current page/URL the user is on

        Returns:
            Appropriate StudentInteractionContext
        """
        if not STUDENT_PROMPTS_AVAILABLE:
            return None

        message_lower = user_message.lower()
        page_lower = (current_page or "").lower()

        # Check for specific contexts based on message and page
        if "quiz" in page_lower or "quiz" in message_lower or "test" in message_lower:
            return StudentInteractionContext.QUIZ_HELP
        elif "lab" in page_lower or "code" in message_lower or "error" in message_lower:
            return StudentInteractionContext.LAB_PROGRAMMING
        elif "assignment" in message_lower or "homework" in message_lower:
            return StudentInteractionContext.ASSIGNMENT_HELP
        elif "don't understand" in message_lower or "explain" in message_lower:
            return StudentInteractionContext.CONCEPT_CLARIFICATION
        elif "study" in message_lower or "plan" in message_lower:
            return StudentInteractionContext.STUDY_PLANNING
        elif "progress" in message_lower or "how am i doing" in message_lower:
            return StudentInteractionContext.PROGRESS_REVIEW
        elif "course" in page_lower:
            return StudentInteractionContext.COURSE_CONTENT
        else:
            return StudentInteractionContext.GENERAL_LEARNING

    def _get_student_skill_level(
        self,
        user_id: int
    ) -> StudentSkillLevel:
        """
        Get student's skill level for adaptive responses.

        WHAT: Retrieves or estimates student skill level.
        WHY: Enables skill-appropriate language and explanations.
        HOW: Checks cached levels or defaults to intermediate.

        Args:
            user_id: The student's user ID

        Returns:
            StudentSkillLevel enum
        """
        if not STUDENT_PROMPTS_AVAILABLE:
            return None

        # Check cached skill level
        user_id_str = str(user_id)
        if user_id_str in self.student_skill_levels:
            level = self.student_skill_levels[user_id_str]
            return StudentSkillLevel(level)

        # Default to intermediate (could be enhanced with actual progress data)
        return StudentSkillLevel.INTERMEDIATE

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
            # For students, this uses pedagogical prompts with emotional support
            system_prompt = self._build_system_prompt(
                user_context=conversation.user_context,
                rag_context=rag_context,
                kg_context=kg_context,
                entities=entities,
                user_message=user_message  # Pass for emotion detection and context
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
        entities: List[Dict[str, Any]] = None,
        user_message: str = ""
    ) -> str:
        """
        Build system prompt for LLM with role-based prompt selection.

        BUSINESS PURPOSE:
        Creates context-aware system prompt for AI assistant. Uses
        pedagogical student prompts for students, admin prompts for admins.

        TECHNICAL IMPLEMENTATION:
        - Students get pedagogically-sound prompts (Socratic method, scaffolding)
        - Admins get task-focused prompts
        - Includes emotional support context when detected
        - Formats with RAG, KG, and entity context

        PEDAGOGICAL APPROACH (for students):
        - Guides students to discover answers themselves
        - Provides skill-level-appropriate explanations
        - Includes emotional support when frustration detected
        - Never gives away answers directly for quizzes

        ARGS:
            user_context: User identity and role
            rag_context: Formatted RAG search results
            kg_context: Knowledge graph context (course recommendations, paths)
            entities: Extracted entities from NLP preprocessing
            user_message: Current user message for emotion detection

        RETURNS:
            Complete system prompt string
        """
        # Check if user is a student for pedagogical prompts
        is_student = self._is_student_role(user_context)

        if is_student and STUDENT_PROMPTS_AVAILABLE:
            return self._build_student_system_prompt(
                user_context=user_context,
                rag_context=rag_context,
                kg_context=kg_context,
                entities=entities,
                user_message=user_message
            )

        # Build admin/instructor prompt (original behavior)
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
4. **CRITICAL: If information is missing for an action, ASK clarifying questions instead of failing**
5. Respect user's role and permissions
6. Provide step-by-step guidance when needed
7. Include relevant examples from the codebase

INTERACTIVE INFORMATION GATHERING:
When a user requests an action but doesn't provide all required information, you MUST:
- DO NOT attempt to execute functions with missing parameters
- DO ask friendly, specific questions to gather missing information
- DO gather information conversationally, one or two questions at a time
- DO remember context from earlier in the conversation
- DO offer helpful suggestions or examples when asking questions

Examples of required information for common actions:
- **Create project**: project name (required), description (optional)
- **Create track**: project, track name, difficulty level (beginner/intermediate/advanced)
- **Create course**: track, course title
- **Onboard instructor**: name, email address
- **Delete project/track/course**: explicit confirmation before destructive actions

EXAMPLE INTERACTIONS:

User: "Create a project"
Assistant: I'd be happy to create a project for you! What would you like to name this project?
User: "Python Training"
Assistant: Great name! Would you like to add a description for the Python Training project? (optional - you can skip this)
User: "It's for new developers"
Assistant: [Calls create_project function]
         ✅ Created "Python Training" project with description "It's for new developers"
         Would you like to add any learning tracks to this project?

User: "Add a track"
Assistant: I'll help you create a learning track! What would you like to name it, and what difficulty level should it be (beginner, intermediate, or advanced)?
User: "Python Basics, beginner"
Assistant: Which project should the "Python Basics" track belong to?
User: "Python Training"
Assistant: [Calls create_track function]
         ✅ Created "Python Basics" track (Beginner level) in Python Training project.

User: "Onboard John"
Assistant: I'll set up John as an instructor. What is John's email address so I can send the invitation?
User: "john@example.com"
Assistant: [Calls onboard_instructor function]
         ✅ Sent instructor invitation to John at john@example.com

User: "Delete the old project"
Assistant: Before I delete "Old Project", I want to confirm - this will permanently remove all tracks, courses, and student enrollments associated with it. Are you sure you want to proceed?
User: "Yes"
Assistant: [Calls delete_project function]
         ✅ Deleted "Old Project" and all associated content.

IMPORTANT REMINDERS:
- Always confirm before executing destructive actions (delete, remove)
- If you're unsure which entity the user is referring to, ask for clarification
- When the user provides partial information, acknowledge what you have and ask for what's missing
- Be conversational and helpful, not robotic or demanding
- Respect RBAC permissions - inform users if they lack permission for an action
"""

    def _build_student_system_prompt(
        self,
        user_context: UserContext,
        rag_context: str,
        kg_context: str = "",
        entities: List[Dict[str, Any]] = None,
        user_message: str = ""
    ) -> str:
        """
        Build pedagogically-sound system prompt for student interactions.

        BUSINESS PURPOSE:
        Creates student-focused AI assistant prompt that applies
        educational best practices for learning support.

        PEDAGOGICAL PRINCIPLES:
        - Socratic method: Guide students to discover answers
        - Scaffolding: Break complex topics into manageable steps
        - Growth mindset: Encourage persistence and learning from mistakes
        - Active learning: Promote hands-on practice
        - Emotional support: Address frustration and confusion

        TECHNICAL IMPLEMENTATION:
        Uses student AI prompts module for context-aware, skill-level
        appropriate responses with emotional support integration.

        ARGS:
            user_context: User identity and role
            rag_context: Formatted RAG search results
            kg_context: Knowledge graph context
            entities: Extracted entities from NLP preprocessing
            user_message: Current message for context detection

        RETURNS:
            Complete student-focused system prompt string
        """
        # Get student interaction context based on message and page
        interaction_context = self._get_student_interaction_context(
            user_message=user_message,
            current_page=user_context.current_page
        )

        # Get student skill level
        skill_level = self._get_student_skill_level(user_context.user_id)

        # Detect emotional state
        detected_emotion = self._detect_student_emotion(user_message)

        # Build base student prompt
        prompt_config = build_contextual_prompt(
            context=interaction_context,
            skill_level=skill_level,
            student_name=user_context.username,
            topic=None  # Could be extracted from entities
        )

        base_prompt = prompt_config["system_prompt"]

        # Add emotional support context if emotion detected
        emotional_context = ""
        if detected_emotion:
            support = get_emotional_support(detected_emotion)
            emotional_context = f"""

EMOTIONAL STATE DETECTED: {detected_emotion}
- Recognition: {support['recognition']}
- Validation: {support['validation']}
- Support suggestions: {', '.join(support['support'][:2])}

RESPONSE GUIDANCE:
Begin your response by acknowledging the student's emotional state
before addressing their question. Use supportive, encouraging language."""

        # Build entities context
        entities_str = ""
        if entities:
            entities_str = "\nIDENTIFIED TOPICS:\n"
            for entity in entities[:5]:
                entities_str += f"- {entity.get('text')}: {entity.get('entity_type')}\n"

        # Combine all context
        return f"""{base_prompt}

STUDENT CONTEXT:
- Name: {user_context.username}
- User ID: {user_context.user_id}
- Current Page: {user_context.current_page or 'Unknown'}
- Detected Context: {interaction_context.value if interaction_context else 'general'}
- Skill Level: {skill_level.value if skill_level else 'intermediate'}
{emotional_context}

{rag_context}
{kg_context}
{entities_str}

RESPONSE GUIDELINES FOR STUDENTS:
1. Be encouraging and supportive - celebrate effort and progress
2. Use the Socratic method - guide them to discover answers
3. For quizzes: NEVER give direct answers, only hints and guidance
4. For coding: Explain the "why" behind solutions
5. Adapt language complexity to their skill level
6. If they seem frustrated, acknowledge their feelings first
7. Break complex topics into smaller, manageable steps
8. Encourage them to try and make mistakes - that's how we learn!

EXAMPLE STUDENT INTERACTIONS:

Student: "I don't understand recursion"
Assistant: "Recursion can be tricky at first! 🤔 Think of it like a set of Russian nesting dolls - each doll contains a smaller version of itself until you reach the smallest one. Let's start simple: have you seen a function call itself before?"

Student: "My code has a NameError"
Assistant: "A NameError usually means Python doesn't recognize a variable name. Let's figure this out together! Can you show me the line where the error occurs? Often it's a small typo or trying to use a variable before it's defined. What variable is it complaining about?"

Student: "I'm so frustrated, this doesn't work!"
Assistant: "I hear you - debugging can be really frustrating! 🫂 But here's the thing: every programmer, even the experts, feels this way sometimes. Let's take a breath and work through this step by step. What's the specific behavior you're seeing vs. what you expected?"

Remember: Your goal is to help them LEARN, not just solve the problem. A student who struggles and then succeeds learns more than one who just gets the answer.
"""

    # =========================================================================
    # ONBOARDING AND HELP METHODS
    # =========================================================================

    def _map_role_to_onboarding_role(self, role: str) -> 'OnboardingUserRole':
        """
        Map user role string to OnboardingUserRole enum.

        Args:
            role: User's role as string

        Returns:
            OnboardingUserRole enum value
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return None

        role_lower = role.lower()
        role_mapping = {
            "student": OnboardingUserRole.STUDENT,
            "learner": OnboardingUserRole.STUDENT,
            "trainee": OnboardingUserRole.STUDENT,
            "instructor": OnboardingUserRole.INSTRUCTOR,
            "teacher": OnboardingUserRole.INSTRUCTOR,
            "trainer": OnboardingUserRole.INSTRUCTOR,
            "organization_admin": OnboardingUserRole.ORG_ADMIN,
            "org_admin": OnboardingUserRole.ORG_ADMIN,
            "site_admin": OnboardingUserRole.SITE_ADMIN,
            "admin": OnboardingUserRole.SITE_ADMIN,
            "guest": OnboardingUserRole.GUEST
        }
        return role_mapping.get(role_lower, OnboardingUserRole.GUEST)

    async def generate_welcome_message(
        self,
        user_context: UserContext,
        is_first_login: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a welcome message for a user.

        BUSINESS PURPOSE:
        Creates personalized welcome messages for first-time users,
        including tour highlights and suggested first actions.

        Args:
            user_context: User's context information
            is_first_login: Whether this is the user's first login

        Returns:
            Dict containing welcome_message, tour_highlights, first_actions
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return {
                "welcome_message": f"Welcome to Course Creator Platform, {user_context.username}! I'm your AI assistant, here to help you navigate and succeed. What would you like to do first?",
                "tour_highlights": [],
                "first_actions": ["Explore the dashboard", "Browse courses", "Ask me anything!"],
                "show_tour": is_first_login
            }

        # Map role to onboarding role
        onboarding_role = self._map_role_to_onboarding_role(user_context.role)

        # Get welcome prompt
        welcome_data = get_welcome_prompt(
            role=onboarding_role,
            user_name=user_context.username,
            organization_name=getattr(user_context, 'organization_name', None)
        )

        logger.info(
            f"Generated welcome message for {user_context.username} "
            f"(role: {onboarding_role.value}, first_login: {is_first_login})"
        )

        return {
            "welcome_message": welcome_data["welcome_message"],
            "tour_highlights": welcome_data["tour_highlights"],
            "first_actions": welcome_data["first_actions"],
            "show_tour": is_first_login,
            "role": onboarding_role.value
        }

    async def get_tour_step(
        self,
        user_context: UserContext,
        phase: str
    ) -> Dict[str, Any]:
        """
        Get tour content for a specific phase.

        BUSINESS PURPOSE:
        Provides step-by-step tour guidance for new users.

        Args:
            user_context: User's context information
            phase: Tour phase (tour_start, tour_dashboard, tour_features, tour_complete)

        Returns:
            Dict containing tour prompts and content
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return {"prompts": ["Let me show you around!"]}

        try:
            phase_enum = OnboardingPhase(phase)
        except ValueError:
            phase_enum = OnboardingPhase.TOUR_START

        onboarding_role = self._map_role_to_onboarding_role(user_context.role)
        tour_data = get_tour_prompt(phase_enum, onboarding_role)

        return {
            "phase": phase,
            "prompts": tour_data.get("prompts", []),
            "feature_explanations": tour_data.get("feature_explanations", {}),
            "system_context": tour_data.get("system_context", "")
        }

    async def get_help_response(
        self,
        user_context: UserContext,
        query: str,
        current_page: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get help response including FAQ search and contextual hints.

        BUSINESS PURPOSE:
        Provides intelligent help responses by searching FAQs
        and providing contextual guidance.

        Args:
            user_context: User's context information
            query: User's help query
            current_page: Current page context

        Returns:
            Dict containing help response, FAQ matches, and hints
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return {
                "response": "I'm here to help! What would you like to know?",
                "faq_matches": [],
                "hints": []
            }

        # Search FAQs
        faq_matches = search_faq(query)

        # Get contextual help
        help_info = get_help_prompt(current_page, "general")

        # Build response
        response_parts = []

        if faq_matches:
            # Use the first FAQ match as primary response
            response_parts.append(faq_matches[0]["answer"])
            if len(faq_matches) > 1:
                response_parts.append("\n\nRelated topics:")
                for faq in faq_matches[1:3]:  # Show up to 2 more
                    response_parts.append(f"• {faq['question']}")

        return {
            "response": "\n".join(response_parts) if response_parts else None,
            "faq_matches": faq_matches[:5],  # Limit to 5
            "hints": help_info.get("hints", []),
            "help_topics": help_info.get("help_topics", []),
            "system_prompt": help_info.get("system_prompt", "")
        }

    async def get_faq_list(self) -> List[Dict[str, str]]:
        """
        Get list of all FAQ topics.

        Returns:
            List of FAQ entries with question and topic
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return []

        return [
            {"topic": topic, "question": content["question"]}
            for topic, content in FAQ_CONTENT.items()
        ]

    async def get_faq_answer_by_topic(self, topic: str) -> Optional[Dict[str, str]]:
        """
        Get FAQ answer for a specific topic.

        Args:
            topic: FAQ topic key

        Returns:
            FAQ entry or None
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return None

        return get_faq_answer(topic)

    async def get_contextual_hints(
        self,
        current_page: str
    ) -> Dict[str, Any]:
        """
        Get contextual hints for the current page.

        BUSINESS PURPOSE:
        Provides helpful tips based on where the user is in the platform.

        Args:
            current_page: Current page identifier

        Returns:
            Dict containing hints and help topics
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            return {"hints": [], "help_topics": []}

        page_lower = current_page.lower() if current_page else ""

        # Find matching context
        for context_key, context_data in CONTEXTUAL_HELP_PROMPTS.items():
            if context_key in page_lower:
                return {
                    "hints": context_data.get("hints", []),
                    "help_topics": context_data.get("help_topics", []),
                    "context": context_key
                }

        return {"hints": [], "help_topics": [], "context": None}

    async def process_onboarding_message(
        self,
        websocket: WebSocket,
        user_context: UserContext,
        message: str,
        is_first_login: bool = False
    ) -> str:
        """
        Process a message with onboarding context.

        BUSINESS PURPOSE:
        Handles messages from users who are new to the platform,
        using onboarding prompts for more guided responses.

        Args:
            websocket: WebSocket connection
            user_context: User's context information
            message: User's message
            is_first_login: Whether this is user's first login

        Returns:
            AI response string
        """
        if not ONBOARDING_PROMPTS_AVAILABLE:
            # Fall back to regular processing
            return await self._process_user_message(
                websocket, message, user_context, str(id(websocket))
            )

        onboarding_role = self._map_role_to_onboarding_role(user_context.role)

        # Build onboarding-aware prompt
        onboarding_context = build_onboarding_prompt(
            role=onboarding_role,
            phase=OnboardingPhase.WELCOME if is_first_login else OnboardingPhase.HELP_GENERAL,
            user_name=user_context.username,
            organization_name=getattr(user_context, 'organization_name', None),
            current_page=user_context.current_page
        )

        # Process with enhanced context
        return await self._process_user_message(
            websocket,
            message,
            user_context,
            str(id(websocket)),
            custom_system_prompt=onboarding_context.get("system_prompt")
        )
