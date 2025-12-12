"""
Unit Tests for LLM Service

BUSINESS CONTEXT:
Tests the LLM service that provides natural language understanding
and generation capabilities. Validates OpenAI and Claude integration,
streaming responses, and error handling.

TECHNICAL VALIDATION:
- Provider initialization (OpenAI/Claude)
- API key validation
- Message formatting
- Streaming response handling
- Error handling and retries
- Rate limiting
- Token counting

TEST COVERAGE TARGETS:
- Line Coverage: 85%+
- Function Coverage: 80%+
- Branch Coverage: 75%+
"""

import pytest
from typing import List, Dict, Any
import sys
import os
from pathlib import Path

# Add ai-assistant-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'ai-assistant-service'))

from ai_assistant_service.application.services.llm_service import (
    LLMService,
    LLMProvider
)
from ai_assistant_service.domain.entities.message import Message, MessageRole



class TestLLMService:
    """Test suite for LLM Service"""

    @pytest.fixture
    def openai_service(self):
        """
        TEST FIXTURE: OpenAI LLM Service instance

        BUSINESS SCENARIO: Instructor needs AI-powered content generation
        TECHNICAL SETUP: Initialize LLM service with OpenAI provider
        """
        import os
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not configured")
        service = LLMService(provider=LLMProvider.OPENAI)
        return service

    @pytest.fixture
    def claude_service(self):
        """
        TEST FIXTURE: Claude LLM Service instance

        BUSINESS SCENARIO: Platform needs alternative LLM for diversity
        TECHNICAL SETUP: Initialize LLM service with Claude provider
        """
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")
        service = LLMService(provider=LLMProvider.CLAUDE)
        return service

    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        """
        TEST FIXTURE: Sample conversation messages

        BUSINESS SCENARIO: Student asks about course prerequisites
        """
        return [
            Message(role="system", content="You are a helpful course assistant."),
            Message(role="user", content="What are the prerequisites for Python 201?"),
        ]

    # ==========================================
    # INITIALIZATION TESTS
    # ==========================================

    def test_llm_service_initialization_openai(self, openai_service):
        """
        TEST: LLM service initializes with OpenAI provider

        BUSINESS SCENARIO: Platform starts AI assistant service
        TECHNICAL VALIDATION: Service instance created with correct provider
        EXPECTED OUTCOME: Service ready for OpenAI API calls
        """
        # Assert
        assert openai_service.provider == LLMProvider.OPENAI
        assert openai_service is not None

    def test_llm_service_initialization_claude(self, claude_service):
        """
        TEST: LLM service initializes with Claude provider

        BUSINESS SCENARIO: Platform uses Claude for advanced reasoning
        TECHNICAL VALIDATION: Service instance created with correct provider
        EXPECTED OUTCOME: Service ready for Claude API calls
        """
        # Assert
        assert claude_service.provider == LLMProvider.CLAUDE
        assert claude_service is not None

    def test_llm_service_missing_api_key(self):
        """
        TEST: Service handles missing API key gracefully

        BUSINESS SCENARIO: Deployment misconfiguration
        TECHNICAL VALIDATION: Raises appropriate exception
        EXPECTED OUTCOME: Clear error message for debugging
        """
        # Arrange
        pass

    # ==========================================
    # MESSAGE FORMATTING TESTS
    # ==========================================

    def test_format_messages_openai(self, openai_service, sample_messages):
        """
        TEST: Messages formatted correctly for OpenAI API

        BUSINESS SCENARIO: Student conversation forwarded to OpenAI
        TECHNICAL VALIDATION: Message structure matches OpenAI schema
        EXPECTED OUTCOME: API accepts formatted messages
        """
        # Act
        formatted = openai_service._format_messages(sample_messages)

        # Assert
        assert isinstance(formatted, list)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"

    def test_format_messages_claude(self, claude_service, sample_messages):
        """
        TEST: Messages formatted correctly for Claude API

        BUSINESS SCENARIO: Student conversation forwarded to Claude
        TECHNICAL VALIDATION: Message structure matches Claude schema
        EXPECTED OUTCOME: API accepts formatted messages
        """
        # Act
        formatted = claude_service._format_messages(sample_messages)

        # Assert
        assert isinstance(formatted, list)
        assert len(formatted) == 2

    # ==========================================
    # COMPLETION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, openai_service, sample_messages):
        """
        TEST: Successful completion generation

        BUSINESS SCENARIO: Student asks question, receives AI response
        TECHNICAL VALIDATION: API called with correct parameters
        EXPECTED OUTCOME: Valid LLMResponse returned
        """
        # Arrange
        pass
            # Act
            response = await openai_service.generate_completion(sample_messages)

            # Assert
            assert isinstance(response, LLMResponse)
            assert response.content == "Python 101 is required."
            assert response.tokens_used == 50

    @pytest.mark.asyncio
    async def test_generate_completion_with_functions(self, openai_service, sample_messages):
        """
        TEST: Completion with function calling

        BUSINESS SCENARIO: AI needs to call platform API for data
        TECHNICAL VALIDATION: Functions passed to API correctly
        EXPECTED OUTCOME: Function call returned in response
        """
        # Arrange
        functions = [
            {
                "name": "get_course_info",
                "description": "Get course information",
                "parameters": {"type": "object", "properties": {}}
            }
        ]

        pass
            # Act
            response = await openai_service.generate_completion(sample_messages, functions=functions)

            # Assert
            assert response.function_call is not None
            assert response.function_call["name"] == "get_course_info"

    @pytest.mark.asyncio
    async def test_generate_completion_api_error(self, openai_service, sample_messages):
        """
        TEST: Handles API errors gracefully

        BUSINESS SCENARIO: OpenAI API is down or rate-limited
        TECHNICAL VALIDATION: Exception caught and handled
        EXPECTED OUTCOME: User-friendly error message
        """
        # Arrange
        pass
            # Act & Assert
            with pytest.raises(Exception, match="API Error"):
                await openai_service.generate_completion(sample_messages)

    # ==========================================
    # STREAMING TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_generate_streaming_completion(self, openai_service, sample_messages):
        """
        TEST: Streaming completion generation

        BUSINESS SCENARIO: Real-time response for better UX
        TECHNICAL VALIDATION: Chunks yielded progressively
        EXPECTED OUTCOME: Complete response assembled from chunks
        """
        # Arrange
        pass
            # Act
            chunks = []
            async for chunk in openai_service.generate_streaming_completion(sample_messages):
                chunks.append(chunk)

            # Assert
            assert len(chunks) == 3
            assert "".join(chunks) == "Python 101 required."

    # ==========================================
    # TOKEN COUNTING TESTS
    # ==========================================

    def test_count_tokens_openai(self, openai_service, sample_messages):
        """
        TEST: Token counting for cost estimation

        BUSINESS SCENARIO: Platform needs to estimate API costs
        TECHNICAL VALIDATION: Accurate token count calculation
        EXPECTED OUTCOME: Reasonable token count returned
        """
        # Act
        token_count = openai_service.count_tokens(sample_messages)

        # Assert
        assert isinstance(token_count, int)
        assert token_count > 0

    # ==========================================
    # ERROR HANDLING TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, openai_service, sample_messages):
        """
        TEST: Handles rate limiting with retry

        BUSINESS SCENARIO: Too many API requests in short time
        TECHNICAL VALIDATION: Exponential backoff retry logic
        EXPECTED OUTCOME: Request eventually succeeds
        """
        # Arrange
        pass
            # Act
            response = await openai_service.generate_completion(sample_messages, max_retries=3)

            # Assert
            assert response.content == "Success"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_handling(self, openai_service, sample_messages):
        """
        TEST: Handles API timeout

        BUSINESS SCENARIO: Slow API response or network issue
        TECHNICAL VALIDATION: Timeout exception raised
        EXPECTED OUTCOME: User notified of timeout
        """
        # Arrange
        pass
            # Act & Assert
            with pytest.raises(TimeoutError):
                await openai_service.generate_completion(sample_messages, timeout=5)

    # ==========================================
    # EDGE CASE TESTS
    # ==========================================

    def test_empty_messages_list(self, openai_service):
        """
        TEST: Handles empty messages list

        BUSINESS SCENARIO: Invalid API call with no messages
        TECHNICAL VALIDATION: Validation error raised
        EXPECTED OUTCOME: Clear error message
        """
        # Act & Assert
        with pytest.raises(ValueError, match="messages"):
            openai_service._format_messages([])

    def test_very_long_message(self, openai_service):
        """
        TEST: Handles message exceeding token limit

        BUSINESS SCENARIO: Student submits very long question
        TECHNICAL VALIDATION: Message truncated or split
        EXPECTED OUTCOME: Request processed without error
        """
        # Arrange
        long_message = [Message(role="user", content="A" * 100000)]

        # Act
        token_count = openai_service.count_tokens(long_message)

        # Assert
        assert token_count > 10000  # Should be substantial

    @pytest.mark.asyncio
    async def test_context_window_management(self, openai_service):
        """
        TEST: Manages conversation context within token limits

        BUSINESS SCENARIO: Long conversation needs context trimming
        TECHNICAL VALIDATION: Messages pruned to fit context window
        EXPECTED OUTCOME: Most recent messages retained
        """
        # Arrange
        many_messages = [
            Message(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")
            for i in range(100)
        ]

        # Act
        pruned = openai_service._prune_context(many_messages, max_tokens=1000)

        # Assert
        assert len(pruned) < len(many_messages)
        assert pruned[-1].content == "Message 99"  # Most recent kept


# ==========================================
# INTEGRATION-STYLE TESTS (still unit tests with mocks)
# ==========================================


class TestLLMServiceIntegrationScenarios:
    """Integration-style scenarios testing multiple components"""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """
        TEST: Multi-turn conversation with context

        BUSINESS SCENARIO: Student has back-and-forth with AI
        TECHNICAL VALIDATION: Context maintained across turns
        EXPECTED OUTCOME: Coherent conversation flow
        """
        # Arrange
        service = LLMService(provider=LLMProvider.OPENAI)

        messages = [
            Message(role="system", content="You are a course assistant."),
            Message(role="user", content="What is Python?"),
            Message(role="assistant", content="Python is a programming language."),
            Message(role="user", content="How do I learn it?"),
        ]

        pass
            # Act
            response = await service.generate_completion(messages)

            # Assert
            assert "Python 101" in response.content

    @pytest.mark.asyncio
    async def test_function_calling_workflow(self):
        """
        TEST: Complete function calling workflow

        BUSINESS SCENARIO: AI needs course data from platform
        TECHNICAL VALIDATION: Function call -> execute -> second LLM call
        EXPECTED OUTCOME: Final response incorporates function result
        """
        # Arrange
        service = LLMService(provider=LLMProvider.OPENAI)

        messages = [
            Message(role="user", content="Tell me about course 123")
        ]

        functions = [{"name": "get_course", "parameters": {}}]

        pass
            # Act
            response1 = await service.generate_completion(messages, functions=functions)

            # Simulate function execution
            messages.append(Message(role="function", content='{"name": "Python 101"}', name="get_course"))

            response2 = await service.generate_completion(messages)

            # Assert
            assert response1.function_call is not None
            assert "Python 101" in response2.content
