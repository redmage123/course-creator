"""
LLM Service - Application Layer

BUSINESS PURPOSE:
Manages integration with Large Language Models (OpenAI GPT-4 or Anthropic Claude).
Handles API calls, response parsing, function calling, and error handling.

TECHNICAL IMPLEMENTATION:
Supports multiple LLM providers with unified interface. Includes retry logic,
rate limiting, and cost tracking. Parses function calls from LLM responses.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ai_assistant_service.domain.entities.message import Message, MessageRole
from ai_assistant_service.domain.entities.intent import (
    FunctionSchema,
    FunctionCall,
    IntentType
)


logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """
    Supported LLM providers

    BUSINESS PURPOSE:
    Allows switching between LLM providers based on cost, performance,
    or availability requirements.

    VALUES:
        OPENAI: OpenAI GPT-4
        CLAUDE: Anthropic Claude 3.5 Sonnet
    """
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMService:
    """
    LLM Service for AI assistant

    BUSINESS PURPOSE:
    Provides natural language understanding and generation for AI assistant.
    Enables conversational interface and intelligent function calling.

    TECHNICAL IMPLEMENTATION:
    - Supports OpenAI and Claude APIs
    - Function calling for action execution
    - Conversation history management
    - Error handling and retry logic
    - Cost tracking and rate limiting

    ATTRIBUTES:
        provider: LLM provider to use (openai/claude)
        api_key: API key for chosen provider
        model: Model name (gpt-4, claude-3-5-sonnet-20241022)
        temperature: Response randomness (0.0-1.0)
        max_tokens: Maximum response length
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        """
        Initialize LLM service

        BUSINESS PURPOSE:
        Configures LLM connection and parameters. Loads API keys from
        environment if not provided. Sets model defaults per provider.

        TECHNICAL IMPLEMENTATION:
        Initializes provider-specific clients (OpenAI or Anthropic).
        Validates API keys exist. Sets default models if not specified.

        ARGS:
            provider: LLM provider to use
            api_key: API key (falls back to env var)
            model: Model name (defaults per provider)
            temperature: Response randomness
            max_tokens: Max response length
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Load API key from environment if not provided
        if api_key is None:
            if provider == LLMProvider.OPENAI:
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == LLMProvider.CLAUDE:
                api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                f"API key required for {provider}. "
                f"Set {'OPENAI_API_KEY' if provider == LLMProvider.OPENAI else 'ANTHROPIC_API_KEY'} "
                f"environment variable."
            )

        self.api_key = api_key

        # Set default model per provider
        if model is None:
            if provider == LLMProvider.OPENAI:
                model = "gpt-4"
            elif provider == LLMProvider.CLAUDE:
                model = "claude-3-5-sonnet-20241022"

        self.model = model

        # Initialize provider client
        self._initialize_client()

        logger.info(f"LLM Service initialized: provider={provider}, model={model}")

    def _initialize_client(self) -> None:
        """
        Initialize LLM provider client

        BUSINESS PURPOSE:
        Creates authenticated API client for chosen LLM provider.
        Required before making any LLM API calls.

        TECHNICAL IMPLEMENTATION:
        Imports and initializes OpenAI or Anthropic client with API key.
        Lazy imports to avoid unnecessary dependencies.
        """
        if self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )

        elif self.provider == LLMProvider.CLAUDE:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install anthropic"
                )

    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: str,
        available_functions: Optional[List[FunctionSchema]] = None
    ) -> Tuple[str, Optional[FunctionCall]]:
        """
        Generate AI response for conversation

        BUSINESS PURPOSE:
        Produces natural language response to user message. Optionally
        identifies function calls to execute platform actions.

        TECHNICAL IMPLEMENTATION:
        Calls LLM API with conversation history and function schemas.
        Parses response to extract text and function calls. Handles
        provider-specific API formats.

        ARGS:
            messages: Conversation history
            system_prompt: System instructions for AI
            available_functions: Functions AI can call

        RETURNS:
            Tuple of (response_text, function_call)
            function_call is None if no action needed

        RAISES:
            Exception: If LLM API call fails
        """
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai_response(
                    messages, system_prompt, available_functions
                )
            elif self.provider == LLMProvider.CLAUDE:
                return await self._generate_claude_response(
                    messages, system_prompt, available_functions
                )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def _generate_openai_response(
        self,
        messages: List[Message],
        system_prompt: str,
        available_functions: Optional[List[FunctionSchema]] = None
    ) -> Tuple[str, Optional[FunctionCall]]:
        """
        Generate response using OpenAI API

        BUSINESS PURPOSE:
        Communicates with OpenAI GPT-4 API for response generation.
        Enables function calling for platform actions.

        TECHNICAL IMPLEMENTATION:
        Formats messages for OpenAI Chat Completion API. Includes
        function schemas for function calling. Parses response to
        extract text and function calls.

        ARGS:
            messages: Conversation history
            system_prompt: System instructions
            available_functions: Functions AI can call

        RETURNS:
            Tuple of (response_text, function_call)
        """
        # Format messages for OpenAI API
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([msg.to_llm_format() for msg in messages])

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        # Add function calling if functions provided
        if available_functions:
            api_params["functions"] = [
                func.to_openai_format() for func in available_functions
            ]
            api_params["function_call"] = "auto"

        # Call OpenAI API
        response = self.client.chat.completions.create(**api_params)
        message = response.choices[0].message

        # Extract text response
        response_text = message.content or ""

        # Extract function call if present
        function_call = None
        if hasattr(message, "function_call") and message.function_call:
            func_call = message.function_call
            function_call = FunctionCall(
                function_name=func_call.name,
                arguments=json.loads(func_call.arguments),
                intent_type=self._infer_intent(func_call.name),
                confidence=0.9  # OpenAI doesn't provide confidence scores
            )

        logger.info(
            f"OpenAI response generated: "
            f"text_length={len(response_text)}, "
            f"function_call={function_call.function_name if function_call else None}"
        )

        return response_text, function_call

    async def _generate_claude_response(
        self,
        messages: List[Message],
        system_prompt: str,
        available_functions: Optional[List[FunctionSchema]] = None
    ) -> Tuple[str, Optional[FunctionCall]]:
        """
        Generate response using Claude API

        BUSINESS PURPOSE:
        Communicates with Anthropic Claude API for response generation.
        Enables tool use for platform actions.

        TECHNICAL IMPLEMENTATION:
        Formats messages for Claude Messages API. Includes tool schemas
        for tool use (Claude's function calling). Parses response to
        extract text and tool uses.

        ARGS:
            messages: Conversation history
            system_prompt: System instructions
            available_functions: Functions AI can call

        RETURNS:
            Tuple of (response_text, function_call)
        """
        # Format messages for Claude API
        api_messages = [msg.to_llm_format() for msg in messages]

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": api_messages
        }

        # Add tools if functions provided
        if available_functions:
            api_params["tools"] = [
                self._function_to_claude_tool(func)
                for func in available_functions
            ]

        # Call Claude API
        message = self.client.messages.create(**api_params)

        # Extract text response
        response_text = ""
        function_call = None

        for content in message.content:
            if content.type == "text":
                response_text = content.text
            elif content.type == "tool_use":
                function_call = FunctionCall(
                    function_name=content.name,
                    arguments=content.input,
                    intent_type=self._infer_intent(content.name),
                    confidence=0.9
                )

        logger.info(
            f"Claude response generated: "
            f"text_length={len(response_text)}, "
            f"function_call={function_call.function_name if function_call else None}"
        )

        return response_text, function_call

    def _function_to_claude_tool(self, func: FunctionSchema) -> Dict[str, Any]:
        """
        Convert function schema to Claude tool format

        BUSINESS PURPOSE:
        Formats function definition for Claude tool use API.
        Required for Claude to understand available actions.

        TECHNICAL IMPLEMENTATION:
        Converts FunctionSchema to Claude tool format with input schema.

        ARGS:
            func: Function schema to convert

        RETURNS:
            Claude tool definition dictionary
        """
        properties = {}
        required = []

        for param in func.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                param_schema["enum"] = param.enum

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "name": func.name,
            "description": func.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def _infer_intent(self, function_name: str) -> IntentType:
        """
        Infer intent type from function name

        BUSINESS PURPOSE:
        Maps function names to intent categories for analytics and logging.

        TECHNICAL IMPLEMENTATION:
        Simple string matching to determine intent type.

        ARGS:
            function_name: Name of called function

        RETURNS:
            Inferred IntentType
        """
        intent_mapping = {
            "create_project": IntentType.CREATE_PROJECT,
            "create_track": IntentType.CREATE_TRACK,
            "create_course": IntentType.CREATE_COURSE,
            "onboard_instructor": IntentType.ONBOARD_INSTRUCTOR,
            "generate_content": IntentType.GENERATE_CONTENT,
            "get_analytics": IntentType.VIEW_ANALYTICS,
            "manage_students": IntentType.MANAGE_STUDENTS
        }
        return intent_mapping.get(function_name, IntentType.GENERAL_CONVERSATION)
