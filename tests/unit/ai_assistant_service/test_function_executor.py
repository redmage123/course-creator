"""
Unit Tests for Function Executor

BUSINESS CONTEXT:
Tests the function executor that allows AI to call platform APIs
for data retrieval and actions. Validates function registration,
parameter validation, execution, and error handling.

TECHNICAL VALIDATION:
- Function registration and discovery
- Parameter validation
- API call execution
- Error handling and retries
- Authorization checks

TEST COVERAGE TARGETS:
- Line Coverage: 85%+
- Function Coverage: 80%+
- Branch Coverage: 75%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
import sys
from pathlib import Path

# Add ai-assistant-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'ai-assistant-service'))

from ai_assistant_service.application.services.function_executor import FunctionExecutor
from ai_assistant_service.domain.entities.intent import (
    FunctionSchema,
    ActionResult,
    FunctionCall,
    IntentType
)


class TestFunctionExecutor:
    """Test suite for Function Executor"""

    @pytest.fixture
    def function_executor(self):
        """
        TEST FIXTURE: Function Executor instance

        BUSINESS SCENARIO: AI assistant needs to call platform APIs
        TECHNICAL SETUP: Initialize executor with mock HTTP client
        """
        with patch('httpx.AsyncClient'):
            executor = FunctionExecutor(api_base_url="https://localhost")
            executor.client = AsyncMock()
            return executor

    @pytest.fixture
    def sample_function_schema(self) -> FunctionSchema:
        """TEST FIXTURE: Sample function schema"""
        return FunctionSchema(
            name="get_course_info",
            description="Get information about a course",
            parameters={
                "type": "object",
                "properties": {
                    "course_id": {"type": "string", "description": "Course ID"}
                },
                "required": ["course_id"]
            },
            api_endpoint="/api/v1/courses/{course_id}",
            http_method="GET"
        )

    # ==========================================
    # INITIALIZATION TESTS
    # ==========================================

    def test_function_executor_initialization(self, function_executor):
        """
        TEST: Function executor initializes correctly

        BUSINESS SCENARIO: Platform starts AI assistant service
        TECHNICAL VALIDATION: Executor instance created
        EXPECTED OUTCOME: Ready to execute functions
        """
        # Assert
        assert function_executor is not None
        assert function_executor.api_base_url == "https://localhost"

    def test_get_available_functions(self, function_executor):
        """
        TEST: Retrieve list of available functions

        BUSINESS SCENARIO: AI needs to know what it can do
        TECHNICAL VALIDATION: Function schemas returned
        EXPECTED OUTCOME: List of executable functions
        """
        # Act
        functions = FunctionExecutor.get_available_functions()

        # Assert
        assert isinstance(functions, list)
        assert len(functions) > 0
        assert all(isinstance(f, FunctionSchema) for f in functions)

    # ==========================================
    # FUNCTION REGISTRATION TESTS
    # ==========================================

    def test_register_function(self, function_executor, sample_function_schema):
        """
        TEST: Register new function

        BUSINESS SCENARIO: Add new platform capability to AI
        TECHNICAL VALIDATION: Function added to registry
        EXPECTED OUTCOME: Function available for execution
        """
        # Act
        function_executor.register_function(sample_function_schema)

        # Assert
        functions = function_executor.get_available_functions()
        assert any(f.name == "get_course_info" for f in functions)

    def test_register_duplicate_function(self, function_executor, sample_function_schema):
        """
        TEST: Prevents duplicate function registration

        BUSINESS SCENARIO: Accidental double registration
        TECHNICAL VALIDATION: Error raised on duplicate
        EXPECTED OUTCOME: Clear error message
        """
        # Arrange
        function_executor.register_function(sample_function_schema)

        # Act & Assert
        with pytest.raises(ValueError, match="already registered"):
            function_executor.register_function(sample_function_schema)

    # ==========================================
    # PARAMETER VALIDATION TESTS
    # ==========================================

    def test_validate_parameters_success(self, function_executor, sample_function_schema):
        """
        TEST: Valid parameters pass validation

        BUSINESS SCENARIO: AI provides correct parameters
        TECHNICAL VALIDATION: Schema validation passes
        EXPECTED OUTCOME: No errors raised
        """
        # Arrange
        params = {"course_id": "123"}

        # Act & Assert (no exception should be raised)
        function_executor._validate_parameters(sample_function_schema, params)

    def test_validate_parameters_missing_required(self, function_executor, sample_function_schema):
        """
        TEST: Missing required parameter detected

        BUSINESS SCENARIO: AI forgets required parameter
        TECHNICAL VALIDATION: Validation error raised
        EXPECTED OUTCOME: Clear error about missing parameter
        """
        # Arrange
        params = {}  # Missing course_id

        # Act & Assert
        with pytest.raises(ValueError, match="required"):
            function_executor._validate_parameters(sample_function_schema, params)

    def test_validate_parameters_wrong_type(self, function_executor, sample_function_schema):
        """
        TEST: Wrong parameter type detected

        BUSINESS SCENARIO: AI provides integer instead of string
        TECHNICAL VALIDATION: Type validation fails
        EXPECTED OUTCOME: Clear error about type mismatch
        """
        # Arrange
        params = {"course_id": 123}  # Should be string

        # Act & Assert
        with pytest.raises(TypeError):
            function_executor._validate_parameters(sample_function_schema, params)

    # ==========================================
    # FUNCTION EXECUTION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_execute_function_success(self, function_executor, sample_function_schema):
        """
        TEST: Successful function execution

        BUSINESS SCENARIO: AI retrieves course information
        TECHNICAL VALIDATION: API called, result returned
        EXPECTED OUTCOME: Course data returned to AI
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "123"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            "id": "123",
            "name": "Python 101",
            "instructor": "John Doe"
        })
        function_executor.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("get_course_info", params)

        # Assert
        assert isinstance(result, ActionResult)
        assert result.success is True
        assert result.result_data["name"] == "Python 101"

    @pytest.mark.asyncio
    async def test_execute_function_not_found(self, function_executor):
        """
        TEST: Execute non-existent function

        BUSINESS SCENARIO: AI tries to call unknown function
        TECHNICAL VALIDATION: Function not found error
        EXPECTED OUTCOME: Clear error message
        """
        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await function_executor.execute_function("unknown_function", {})

    @pytest.mark.asyncio
    async def test_execute_function_api_error(self, function_executor, sample_function_schema):
        """
        TEST: Handles API error during execution

        BUSINESS SCENARIO: Platform API returns error
        TECHNICAL VALIDATION: Error captured and returned
        EXPECTED OUTCOME: Error details in result
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "999"}

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Course not found"
        function_executor.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("get_course_info", params)

        # Assert
        assert result.success is False
        assert "404" in result.error_message or "not found" in result.error_message.lower()

    # ==========================================
    # HTTP METHOD TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_execute_post_function(self, function_executor):
        """
        TEST: Execute POST function

        BUSINESS SCENARIO: AI creates new course
        TECHNICAL VALIDATION: POST request sent
        EXPECTED OUTCOME: Resource created
        """
        # Arrange
        create_schema = FunctionSchema(
            name="create_course",
            description="Create a new course",
            parameters={"type": "object", "properties": {"name": {"type": "string"}}},
            api_endpoint="/api/v1/courses",
            http_method="POST"
        )
        function_executor.register_function(create_schema)
        params = {"name": "New Course"}

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json = Mock(return_value={"id": "456", "name": "New Course"})
        function_executor.client.post = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("create_course", params)

        # Assert
        assert result.success is True
        assert result.data["id"] == "456"

    @pytest.mark.asyncio
    async def test_execute_put_function(self, function_executor):
        """
        TEST: Execute PUT function

        BUSINESS SCENARIO: AI updates course information
        TECHNICAL VALIDATION: PUT request sent
        EXPECTED OUTCOME: Resource updated
        """
        # Arrange
        update_schema = FunctionSchema(
            name="update_course",
            description="Update course",
            parameters={
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "name": {"type": "string"}
                }
            },
            api_endpoint="/api/v1/courses/{course_id}",
            http_method="PUT"
        )
        function_executor.register_function(update_schema)
        params = {"course_id": "123", "name": "Updated Name"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"id": "123", "name": "Updated Name"})
        function_executor.client.put = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("update_course", params)

        # Assert
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_delete_function(self, function_executor):
        """
        TEST: Execute DELETE function

        BUSINESS SCENARIO: AI deletes course
        TECHNICAL VALIDATION: DELETE request sent
        EXPECTED OUTCOME: Resource deleted
        """
        # Arrange
        delete_schema = FunctionSchema(
            name="delete_course",
            description="Delete course",
            parameters={"type": "object", "properties": {"course_id": {"type": "string"}}},
            api_endpoint="/api/v1/courses/{course_id}",
            http_method="DELETE"
        )
        function_executor.register_function(delete_schema)
        params = {"course_id": "123"}

        mock_response = Mock()
        mock_response.status_code = 204
        function_executor.client.delete = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("delete_course", params)

        # Assert
        assert result.success is True

    # ==========================================
    # AUTHORIZATION TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_execute_with_auth_token(self, function_executor, sample_function_schema):
        """
        TEST: Function execution with authentication

        BUSINESS SCENARIO: AI acts on behalf of user
        TECHNICAL VALIDATION: Auth token passed in headers
        EXPECTED OUTCOME: Authorized request succeeds
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "123"}
        auth_token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"id": "123", "name": "Python 101"})
        function_executor.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("get_course_info", params, auth_token=auth_token)

        # Assert
        assert result.success is True
        # Verify auth token was passed
        call_kwargs = function_executor.client.get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_execute_unauthorized(self, function_executor, sample_function_schema):
        """
        TEST: Handles unauthorized access

        BUSINESS SCENARIO: AI tries to access restricted resource
        TECHNICAL VALIDATION: 401/403 error handled
        EXPECTED OUTCOME: Authorization error in result
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "123"}

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        function_executor.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await function_executor.execute_function("get_course_info", params)

        # Assert
        assert result.success is False
        assert "403" in result.error_message or "forbidden" in result.error_message.lower()

    # ==========================================
    # TIMEOUT AND RETRY TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, function_executor, sample_function_schema):
        """
        TEST: Function execution with timeout

        BUSINESS SCENARIO: Slow API response
        TECHNICAL VALIDATION: Timeout exception raised
        EXPECTED OUTCOME: Error result with timeout message
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "123"}

        function_executor.client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        # Act
        result = await function_executor.execute_function("get_course_info", params, timeout=5)

        # Assert
        assert result.success is False
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, function_executor, sample_function_schema):
        """
        TEST: Function execution with retry on failure

        BUSINESS SCENARIO: Transient API error
        TECHNICAL VALIDATION: Retry logic attempts multiple times
        EXPECTED OUTCOME: Eventually succeeds
        """
        # Arrange
        function_executor.register_function(sample_function_schema)
        params = {"course_id": "123"}

        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json = Mock(return_value={"id": "123", "name": "Python 101"})

        function_executor.client.get = AsyncMock(side_effect=[mock_response_fail, mock_response_success])

        # Act
        result = await function_executor.execute_function("get_course_info", params, max_retries=2)

        # Assert
        assert result.success is True
        assert function_executor.client.get.call_count == 2

    # ==========================================
    # OPENAI FORMAT CONVERSION TESTS
    # ==========================================

    def test_function_schema_to_openai_format(self, sample_function_schema):
        """
        TEST: Convert schema to OpenAI function format

        BUSINESS SCENARIO: Pass functions to OpenAI API
        TECHNICAL VALIDATION: Schema converted correctly
        EXPECTED OUTCOME: Valid OpenAI function object
        """
        # Act
        openai_format = sample_function_schema.to_openai_format()

        # Assert
        assert "name" in openai_format
        assert "description" in openai_format
        assert "parameters" in openai_format
        assert openai_format["name"] == "get_course_info"

    # ==========================================
    # CLEANUP TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_close_client(self, function_executor):
        """
        TEST: HTTP client closed properly

        BUSINESS SCENARIO: Service shutdown
        TECHNICAL VALIDATION: Async client cleanup
        EXPECTED OUTCOME: No resource leaks
        """
        # Arrange
        function_executor.client.aclose = AsyncMock()

        # Act
        await function_executor.close()

        # Assert
        function_executor.client.aclose.assert_called_once()


# ==========================================
# INTEGRATION-STYLE TESTS
# ==========================================

class TestFunctionExecutorIntegration:
    """Integration-style scenarios"""

    @pytest.mark.asyncio
    async def test_multi_step_function_workflow(self):
        """
        TEST: Multi-step workflow with multiple function calls

        BUSINESS SCENARIO: AI searches courses, then enrolls student
        TECHNICAL VALIDATION: Sequential function calls
        EXPECTED OUTCOME: Complete workflow succeeds
        """
        # Arrange
        with patch('httpx.AsyncClient'):
            executor = FunctionExecutor(api_base_url="https://localhost")
            executor.client = AsyncMock()

        # Register functions
        search_schema = FunctionSchema(
            name="search_courses",
            description="Search courses",
            parameters={"type": "object", "properties": {}},
            api_endpoint="/api/v1/courses/search",
            http_method="GET"
        )

        enroll_schema = FunctionSchema(
            name="enroll_student",
            description="Enroll student",
            parameters={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "course_id": {"type": "string"}
                }
            },
            api_endpoint="/api/v1/enrollments",
            http_method="POST"
        )

        executor.register_function(search_schema)
        executor.register_function(enroll_schema)

        # Mock responses
        search_response = Mock()
        search_response.status_code = 200
        search_response.json = Mock(return_value={"courses": [{"id": "123", "name": "Python 101"}]})

        enroll_response = Mock()
        enroll_response.status_code = 201
        enroll_response.json = Mock(return_value={"enrollment_id": "789", "status": "enrolled"})

        executor.client.get = AsyncMock(return_value=search_response)
        executor.client.post = AsyncMock(return_value=enroll_response)

        # Act
        search_result = await executor.execute_function("search_courses", {})
        course_id = search_result.data["courses"][0]["id"]

        enroll_result = await executor.execute_function("enroll_student", {
            "student_id": "456",
            "course_id": course_id
        })

        # Assert
        assert search_result.success is True
        assert enroll_result.success is True
        assert enroll_result.data["status"] == "enrolled"
