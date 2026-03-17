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


class FakeHTTPClient:
    """Test double for HTTP client - uses real implementation patterns"""
    def __init__(self):
        self.responses = {}
        self.call_history = []

    def set_response(self, method, url, response):
        """Configure response for specific method/URL"""
        key = f"{method.upper()}:{url}"
        self.responses[key] = response

    async def get(self, url, **kwargs):
        self.call_history.append(('GET', url, kwargs))
        key = f"GET:{url}"
        if key in self.responses:
            return self.responses[key]
        return FakeHTTPResponse(200, {})

    async def post(self, url, **kwargs):
        self.call_history.append(('POST', url, kwargs))
        key = f"POST:{url}"
        if key in self.responses:
            return self.responses[key]
        return FakeHTTPResponse(201, {})

    async def put(self, url, **kwargs):
        self.call_history.append(('PUT', url, kwargs))
        key = f"PUT:{url}"
        if key in self.responses:
            return self.responses[key]
        return FakeHTTPResponse(200, {})

    async def delete(self, url, **kwargs):
        self.call_history.append(('DELETE', url, kwargs))
        key = f"DELETE:{url}"
        if key in self.responses:
            return self.responses[key]
        return FakeHTTPResponse(204)

    async def aclose(self):
        self.call_history.append(('CLOSE', None, {}))


class FakeHTTPResponse:
    """Test double for HTTP response"""
    def __init__(self, status_code, json_data=None, text_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text_data or ""

    def json(self):
        return self._json_data


class TestFunctionExecutor:
    """Test suite for Function Executor"""

    @pytest.fixture
    def function_executor(self):
        """
        TEST FIXTURE: Function Executor instance

        BUSINESS SCENARIO: AI assistant needs to call platform APIs
        TECHNICAL SETUP: Initialize executor with fake HTTP client
        """
        executor = FunctionExecutor(api_base_url="https://localhost")
        executor.client = FakeHTTPClient()
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

        response = FakeHTTPResponse(
            status_code=200,
            json_data={
                "id": "123",
                "name": "Python 101",
                "instructor": "John Doe"
            }
        )
        function_executor.client.set_response('GET', 'https://localhost/api/v1/courses/123', response)

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

        response = FakeHTTPResponse(status_code=404, text_data="Course not found")
        function_executor.client.set_response('GET', 'https://localhost/api/v1/courses/999', response)

        # Act
        result = await function_executor.execute_function("get_course_info", params)

        # Assert
        assert result.success is False
        assert "404" in result.error_message or "not found" in result.error_message.lower()

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

        response = FakeHTTPResponse(200, {"id": "123", "name": "Python 101"})
        function_executor.client.set_response('GET', 'https://localhost/api/v1/courses/123', response)

        # Act
        result = await function_executor.execute_function("get_course_info", params, auth_token=auth_token)

        # Assert
        assert result.success is True
        # Verify auth token was passed
        assert len(function_executor.client.call_history) > 0
        call = function_executor.client.call_history[0]
        assert "headers" in call[2]
        assert "Authorization" in call[2]["headers"]

    @pytest.mark.asyncio
    async def test_close_client(self, function_executor):
        """
        TEST: HTTP client closed properly

        BUSINESS SCENARIO: Service shutdown
        TECHNICAL VALIDATION: Async client cleanup
        EXPECTED OUTCOME: No resource leaks
        """
        # Act
        await function_executor.close()

        # Assert
        assert ('CLOSE', None, {}) in function_executor.client.call_history
