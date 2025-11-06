"""
Function Executor - Application Layer

BUSINESS PURPOSE:
Executes platform actions requested by AI assistant. Validates RBAC
permissions and calls appropriate platform APIs. Provides safe action
execution with comprehensive error handling.

TECHNICAL IMPLEMENTATION:
Maps function names to API endpoints. Performs RBAC checks before
execution. Handles API errors gracefully with user-friendly messages.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List

from ai_assistant_service.domain.entities.conversation import UserContext
from ai_assistant_service.domain.entities.intent import (
    FunctionCall,
    ActionResult,
    FunctionSchema,
    FunctionParameter,
    IntentType
)

logger = logging.getLogger(__name__)


class FunctionExecutor:
    """
    Function executor for platform actions

    BUSINESS PURPOSE:
    Bridges AI assistant and platform APIs. Executes user-requested
    actions after validating permissions. Core component enabling
    AI to perform actual platform operations.

    TECHNICAL IMPLEMENTATION:
    - HTTP client for platform API calls
    - RBAC validation before execution
    - Error handling and user-friendly messaging
    - Action result tracking

    ATTRIBUTES:
        api_base_url: Platform API base URL
        auth_token: Authentication token for API calls
        timeout: API request timeout
    """

    # Define available functions with schemas
    AVAILABLE_FUNCTIONS: List[FunctionSchema] = [
        FunctionSchema(
            name="create_project",
            description="Create a new project in an organization",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="integer",
                    description="Organization ID where project will be created",
                    required=True
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Project name",
                    required=True
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Project description",
                    required=False
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="create_track",
            description="Create a learning track within a project",
            parameters=[
                FunctionParameter(
                    name="project_id",
                    type="integer",
                    description="Project ID where track will be created",
                    required=True
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Track name",
                    required=True
                ),
                FunctionParameter(
                    name="level",
                    type="string",
                    description="Track difficulty level",
                    required=True,
                    enum=["beginner", "intermediate", "advanced"]
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Track description",
                    required=False
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="onboard_instructor",
            description="Onboard new instructor to organization",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="integer",
                    description="Organization ID",
                    required=True
                ),
                FunctionParameter(
                    name="email",
                    type="string",
                    description="Instructor email address",
                    required=True
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Instructor full name",
                    required=True
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="create_course",
            description="Create new course in a track",
            parameters=[
                FunctionParameter(
                    name="track_id",
                    type="integer",
                    description="Track ID where course will be created",
                    required=True
                ),
                FunctionParameter(
                    name="title",
                    type="string",
                    description="Course title",
                    required=True
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Course description",
                    required=False
                )
            ],
            rbac_required=["instructor", "organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="get_analytics",
            description="Get analytics data for courses or organization",
            parameters=[
                FunctionParameter(
                    name="analytics_type",
                    type="string",
                    description="Type of analytics to retrieve",
                    required=True,
                    enum=["course", "student", "organization"]
                ),
                FunctionParameter(
                    name="entity_id",
                    type="integer",
                    description="ID of entity to get analytics for",
                    required=True
                )
            ],
            rbac_required=["instructor", "organization_admin", "site_admin"]
        )
    ]

    def __init__(
        self,
        api_base_url: str = "https://localhost",
        timeout: float = 30.0
    ):
        """
        Initialize function executor

        BUSINESS PURPOSE:
        Configures API connection for platform action execution.
        Sets up HTTP client with SSL settings for local development.

        TECHNICAL IMPLEMENTATION:
        Creates httpx async client with timeout and SSL verification
        disabled for localhost development.

        ARGS:
            api_base_url: Platform API base URL
            timeout: API request timeout seconds
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.timeout = timeout

        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=timeout,
            verify=False  # Disable SSL verification for localhost
        )

        logger.info(f"Function Executor initialized: api_base_url={api_base_url}")

    async def execute(
        self,
        function_call: FunctionCall,
        user_context: UserContext,
        auth_token: str
    ) -> ActionResult:
        """
        Execute function call with RBAC validation

        BUSINESS PURPOSE:
        Safely executes platform action requested by AI. Validates user
        has required permissions before calling API. Returns structured
        result for AI response generation.

        TECHNICAL IMPLEMENTATION:
        1. Find function schema
        2. Validate RBAC permissions
        3. Call appropriate API endpoint
        4. Parse response and create ActionResult
        5. Handle errors gracefully

        ARGS:
            function_call: Function to execute with arguments
            user_context: User identity and role
            auth_token: Authentication token for API calls

        RETURNS:
            ActionResult with success status and data/error

        EXAMPLE:
            result = await executor.execute(
                FunctionCall(
                    function_name="create_project",
                    arguments={"organization_id": 1, "name": "ML Project"}
                ),
                user_context,
                auth_token
            )
        """
        # Find function schema
        schema = self._find_function_schema(function_call.function_name)
        if not schema:
            return ActionResult(
                success=False,
                function_name=function_call.function_name,
                error_message=f"Unknown function: {function_call.function_name}"
            )

        # Validate RBAC
        if not self._check_rbac(user_context.role, schema.rbac_required):
            return ActionResult(
                success=False,
                function_name=function_call.function_name,
                error_message=f"Insufficient permissions. Required roles: {schema.rbac_required}",
                rbac_denied=True
            )

        # Validate arguments
        if not function_call.validate_arguments(schema):
            return ActionResult(
                success=False,
                function_name=function_call.function_name,
                error_message="Missing required parameters"
            )

        # Execute function
        try:
            if function_call.function_name == "create_project":
                return await self._create_project(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "create_track":
                return await self._create_track(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "onboard_instructor":
                return await self._onboard_instructor(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "create_course":
                return await self._create_course(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "get_analytics":
                return await self._get_analytics(
                    function_call.arguments,
                    auth_token
                )
            else:
                return ActionResult(
                    success=False,
                    function_name=function_call.function_name,
                    error_message=f"Function not implemented: {function_call.function_name}"
                )

        except Exception as e:
            logger.error(f"Function execution failed: {function_call.function_name} - {e}")
            return ActionResult(
                success=False,
                function_name=function_call.function_name,
                error_message=str(e)
            )

    def _find_function_schema(self, function_name: str) -> Optional[FunctionSchema]:
        """Find function schema by name"""
        for schema in self.AVAILABLE_FUNCTIONS:
            if schema.name == function_name:
                return schema
        return None

    def _check_rbac(self, user_role: str, required_roles: List[str]) -> bool:
        """
        Check if user role has permission

        BUSINESS PURPOSE:
        Enforces role-based access control before executing actions.
        Prevents unauthorized operations.

        TECHNICAL IMPLEMENTATION:
        Normalizes role names and checks if user role is in required list.

        ARGS:
            user_role: User's role
            required_roles: Roles allowed to execute function

        RETURNS:
            True if user has permission, False otherwise
        """
        # Normalize role name
        normalized_user_role = user_role.lower().replace('_', '').replace('-', '')

        for required_role in required_roles:
            normalized_required = required_role.lower().replace('_', '').replace('-', '')
            if normalized_user_role == normalized_required:
                return True

        return False

    async def _create_project(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """Execute create_project API call"""
        try:
            url = f"{self.api_base_url}:8008/api/v1/projects"

            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "name": arguments["name"],
                "organization_id": arguments["organization_id"],
                "description": arguments.get("description", "")
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="create_project",
                result_data=result_data
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="create_project",
                error_message=f"API call failed: {e}"
            )

    async def _create_track(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """Execute create_track API call"""
        try:
            url = f"{self.api_base_url}:8008/api/v1/projects/{arguments['project_id']}/tracks"

            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "name": arguments["name"],
                "level": arguments["level"],
                "description": arguments.get("description", "")
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="create_track",
                result_data=result_data
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="create_track",
                error_message=f"API call failed: {e}"
            )

    async def _onboard_instructor(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """Execute onboard_instructor API call"""
        try:
            url = f"{self.api_base_url}:8000/api/v1/users/register"

            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "email": arguments["email"],
                "name": arguments["name"],
                "role": "instructor",
                "organization_id": arguments["organization_id"]
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="onboard_instructor",
                result_data=result_data
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="onboard_instructor",
                error_message=f"API call failed: {e}"
            )

    async def _create_course(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """Execute create_course API call"""
        try:
            url = f"{self.api_base_url}:8004/api/v1/courses"

            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "title": arguments["title"],
                "track_id": arguments["track_id"],
                "description": arguments.get("description", "")
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="create_course",
                result_data=result_data
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="create_course",
                error_message=f"API call failed: {e}"
            )

    async def _get_analytics(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """Execute get_analytics API call"""
        try:
            analytics_type = arguments["analytics_type"]
            entity_id = arguments["entity_id"]

            url = f"{self.api_base_url}:8007/api/v1/analytics/{analytics_type}/{entity_id}"

            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="get_analytics",
                result_data=result_data
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="get_analytics",
                error_message=f"API call failed: {e}"
            )

    @classmethod
    def get_available_functions(cls) -> List[FunctionSchema]:
        """
        Get list of available functions

        BUSINESS PURPOSE:
        Provides function schemas to LLM for function calling.
        Defines what actions AI assistant can perform.

        RETURNS:
            List of all available function schemas
        """
        return cls.AVAILABLE_FUNCTIONS

    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("Function Executor closed")
