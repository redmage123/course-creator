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

    # Define available functions with schemas and interactive clarification support
    AVAILABLE_FUNCTIONS: List[FunctionSchema] = [
        FunctionSchema(
            name="create_project",
            description="Create a new project in an organization. Ask clarifying questions if the user hasn't provided all required information.",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="integer",
                    description="Organization ID where project will be created",
                    required=True,
                    clarification_prompt="Which organization should this project belong to? I can look up your available organizations if needed."
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Project name",
                    required=True,
                    clarification_prompt="What would you like to name this project? A clear, descriptive name helps with organization."
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Project description",
                    required=False,
                    clarification_prompt="Would you like to add a description for this project? (optional)"
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Create a project'\nAssistant: 'I'd be happy to create a project for you! First, what would you like to name the project?'",
                "User: 'I need a new project for training'\nAssistant: 'Great! What name would you like for this training project? Also, would you like to add a description to help others understand its purpose?'"
            ]
        ),
        FunctionSchema(
            name="create_track",
            description="Create a learning track within a project. A track represents a skill path with multiple courses. Ask clarifying questions if information is missing.",
            parameters=[
                FunctionParameter(
                    name="project_id",
                    type="integer",
                    description="Project ID where track will be created",
                    required=True,
                    clarification_prompt="Which project should this track be added to? I can show you a list of your existing projects."
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Track name",
                    required=True,
                    clarification_prompt="What would you like to name this learning track? For example: 'Python Fundamentals', 'Cloud Architecture', etc."
                ),
                FunctionParameter(
                    name="level",
                    type="string",
                    description="Track difficulty level",
                    required=True,
                    enum=["beginner", "intermediate", "advanced"],
                    clarification_prompt="What difficulty level should this track be? Choose from: beginner, intermediate, or advanced."
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Track description",
                    required=False,
                    clarification_prompt="Would you like to add a description explaining what this track covers? (optional)"
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Add a track'\nAssistant: 'I'll help you create a learning track! What would you like to name it, and what difficulty level should it be (beginner, intermediate, or advanced)?'",
                "User: 'Create a Python track'\nAssistant: 'Great choice! What difficulty level should the Python track be - beginner, intermediate, or advanced? And which project should I add it to?'"
            ]
        ),
        FunctionSchema(
            name="onboard_instructor",
            description="Onboard a new instructor to the organization. The instructor will receive an invitation email. Ask for all required information interactively.",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="integer",
                    description="Organization ID",
                    required=True,
                    clarification_prompt="Which organization should this instructor be added to?"
                ),
                FunctionParameter(
                    name="email",
                    type="string",
                    description="Instructor email address",
                    required=True,
                    clarification_prompt="What is the instructor's email address? They'll receive an invitation at this address."
                ),
                FunctionParameter(
                    name="name",
                    type="string",
                    description="Instructor full name",
                    required=True,
                    clarification_prompt="What is the instructor's full name?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Add an instructor'\nAssistant: 'I'll help you onboard a new instructor! What is their full name and email address?'",
                "User: 'Onboard John'\nAssistant: 'I'll set up John as an instructor. What is John's email address so I can send the invitation?'"
            ]
        ),
        FunctionSchema(
            name="create_course",
            description="Create a new course in a learning track. Courses contain lessons, quizzes, and labs. Ask clarifying questions if track or title is not specified.",
            parameters=[
                FunctionParameter(
                    name="track_id",
                    type="integer",
                    description="Track ID where course will be created",
                    required=True,
                    clarification_prompt="Which learning track should this course be added to?"
                ),
                FunctionParameter(
                    name="title",
                    type="string",
                    description="Course title",
                    required=True,
                    clarification_prompt="What title would you like for this course? A clear, descriptive title helps students understand the course content."
                ),
                FunctionParameter(
                    name="description",
                    type="string",
                    description="Course description",
                    required=False,
                    clarification_prompt="Would you like to add a description for this course? (optional but recommended)"
                )
            ],
            rbac_required=["instructor", "organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Create a course'\nAssistant: 'I'll help you create a course! What would you like to title it, and which learning track should it belong to?'",
                "User: 'Add a course on data analysis'\nAssistant: 'A data analysis course sounds great! What specific title would you like, and which track should I add it to?'"
            ]
        ),
        FunctionSchema(
            name="get_analytics",
            description="Get analytics data for courses, students, or organization-wide metrics. Ask which type of analytics the user needs.",
            parameters=[
                FunctionParameter(
                    name="analytics_type",
                    type="string",
                    description="Type of analytics to retrieve",
                    required=True,
                    enum=["course", "student", "organization"],
                    clarification_prompt="What type of analytics would you like to see? I can show:\n- **course**: Performance and completion data for a specific course\n- **student**: Individual student progress and achievements\n- **organization**: Overall organization metrics and trends"
                ),
                FunctionParameter(
                    name="entity_id",
                    type="integer",
                    description="ID of entity to get analytics for",
                    required=True,
                    clarification_prompt="Which specific course, student, or organization would you like analytics for? I can help you find the right ID."
                )
            ],
            rbac_required=["instructor", "organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Show me analytics'\nAssistant: 'I can show you various analytics! Would you like to see course performance, student progress, or organization-wide metrics?'",
                "User: 'How are my courses doing?'\nAssistant: 'I can pull up course analytics for you! Which course would you like to see metrics for?'"
            ]
        ),
        # ============================================================
        # DELETE FUNCTIONS - Org admins can delete projects, tracks, courses, subprojects
        # ============================================================
        FunctionSchema(
            name="delete_project",
            description="Delete a project and all its associated tracks, sub-projects, and enrollments. This is a DESTRUCTIVE operation. Always confirm with the user before executing.",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="string",
                    description="Organization ID (UUID) that owns the project",
                    required=True,
                    clarification_prompt="Which organization does this project belong to?"
                ),
                FunctionParameter(
                    name="project_id",
                    type="string",
                    description="Project ID (UUID) to delete",
                    required=True,
                    clarification_prompt="Which project would you like to delete? Please specify the project name or ID."
                ),
                FunctionParameter(
                    name="force",
                    type="boolean",
                    description="Force delete even if there are active enrollments (default: false)",
                    required=False,
                    clarification_prompt="This project has active student enrollments. Do you want to force delete it anyway? This will unenroll all students."
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Delete a project'\nAssistant: 'I can help you delete a project. Which project would you like to remove? Please note this will also delete all associated tracks, sub-projects, and enrollments.'",
                "User: 'Remove the old training project'\nAssistant: 'Before I delete \"Old Training Project\", I want to confirm - this will permanently remove all tracks, courses, and student enrollments associated with it. Are you sure you want to proceed?'"
            ]
        ),
        FunctionSchema(
            name="delete_track",
            description="Delete a learning track. Always confirm the track name with the user before deleting.",
            parameters=[
                FunctionParameter(
                    name="track_id",
                    type="string",
                    description="Track ID (UUID) to delete",
                    required=True,
                    clarification_prompt="Which track would you like to delete? Please specify the track name or ID."
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Delete a track'\nAssistant: 'Which learning track would you like to delete? Please tell me the track name.'",
                "User: 'Remove the Python beginner track'\nAssistant: 'I'll delete the Python Beginner track. Just to confirm, this will also remove any course assignments. Do you want to proceed?'"
            ]
        ),
        FunctionSchema(
            name="delete_course",
            description="Delete a course. Always confirm with the user and warn about enrolled students.",
            parameters=[
                FunctionParameter(
                    name="course_id",
                    type="string",
                    description="Course ID (UUID) to delete",
                    required=True,
                    clarification_prompt="Which course would you like to delete? Please specify the course title or ID."
                )
            ],
            rbac_required=["instructor", "organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Delete a course'\nAssistant: 'Which course would you like to delete? Please tell me the course title.'",
                "User: 'Remove Introduction to Python'\nAssistant: 'Before deleting \"Introduction to Python\", note that any enrolled students will lose access. Are you sure you want to proceed?'"
            ]
        ),
        FunctionSchema(
            name="delete_subproject",
            description="Delete a sub-project/location from a project. Confirm the location name with the user.",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="string",
                    description="Organization ID (UUID)",
                    required=True,
                    clarification_prompt="Which organization does this sub-project belong to?"
                ),
                FunctionParameter(
                    name="project_id",
                    type="string",
                    description="Parent project ID (UUID)",
                    required=True,
                    clarification_prompt="Which project contains the sub-project you want to delete?"
                ),
                FunctionParameter(
                    name="sub_project_id",
                    type="string",
                    description="Sub-project ID (UUID) to delete",
                    required=True,
                    clarification_prompt="Which sub-project/location would you like to delete? Please specify its name."
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Delete a location'\nAssistant: 'Which location/sub-project would you like to delete, and from which project?'",
                "User: 'Remove the Seattle location'\nAssistant: 'I'll remove the Seattle location. This will also delete track assignments for this location. Which project is this location part of?'"
            ]
        ),
        # ============================================================
        # PROJECT BUILDER FUNCTIONS - Bulk creation via AI conversation
        # ============================================================
        FunctionSchema(
            name="start_project_builder",
            description="Start a new AI-assisted project builder session for creating complete training programs. This begins an interactive conversation to gather all project details.",
            parameters=[
                FunctionParameter(
                    name="organization_id",
                    type="string",
                    description="Organization ID (UUID) where the project will be created",
                    required=True,
                    clarification_prompt="Which organization would you like to create this training program for?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'I want to set up a training program'\nAssistant: 'I can help you create a complete training program! Let me start the project builder. What organization is this for, and what type of training are you planning?'",
                "User: 'Build a new project'\nAssistant: 'Great! I'll start the interactive project builder. This will help you define locations, tracks, instructors, and students step by step. What's the main focus of this training project?'"
            ]
        ),
        FunctionSchema(
            name="submit_project_builder_message",
            description="Continue the project builder conversation by providing additional information about the training program.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="I need the session ID to continue. Do you have an active project builder session?"
                ),
                FunctionParameter(
                    name="message",
                    type="string",
                    description="Natural language message describing project requirements",
                    required=True,
                    clarification_prompt="What additional information would you like to provide for the project?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="upload_project_roster",
            description="Upload an instructor or student roster file for bulk enrollment. Ask about roster format if not specified.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="Which project builder session should I add this roster to?"
                ),
                FunctionParameter(
                    name="roster_type",
                    type="string",
                    description="Type of roster being uploaded",
                    required=True,
                    enum=["instructor", "student"],
                    clarification_prompt="Is this a roster of instructors or students?"
                ),
                FunctionParameter(
                    name="filename",
                    type="string",
                    description="Original filename (used for format detection)",
                    required=True,
                    clarification_prompt="What is the filename of the roster you're uploading? (Supported formats: CSV, Excel .xlsx, JSON)"
                ),
                FunctionParameter(
                    name="file_content_base64",
                    type="string",
                    description="Base64-encoded file content",
                    required=True,
                    clarification_prompt="Please provide the roster file for upload."
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Upload a roster'\nAssistant: 'I can help you upload a roster! Is this a list of instructors or students? And what format is the file in (CSV, Excel, or JSON)?'",
                "User: 'I have a student list'\nAssistant: 'Great! Please upload your student roster file. I support CSV, Excel (.xlsx), and JSON formats. What file would you like to upload?'"
            ]
        ),
        FunctionSchema(
            name="generate_project_schedule",
            description="Generate a schedule proposal for the training project based on the information collected so far.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="Which project builder session should I generate a schedule for?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
        ),
        FunctionSchema(
            name="preview_project_creation",
            description="Preview what will be created before actually creating it. Always offer this option before executing creation.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="Which project builder session would you like to preview?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Show me what will be created'\nAssistant: 'I'll generate a preview of everything that will be created including projects, tracks, courses, and enrollments.'",
                "User: 'Ready to create'\nAssistant: 'Before we create everything, let me show you a preview of what will be created. You can review and confirm.'"
            ]
        ),
        FunctionSchema(
            name="execute_project_creation",
            description="Execute the actual creation of all project components. Always show preview first and require explicit confirmation.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="Which project builder session should I execute?"
                ),
                FunctionParameter(
                    name="confirm",
                    type="boolean",
                    description="Confirmation flag - must be true to execute",
                    required=True,
                    clarification_prompt="Please confirm you want to create all these items. Type 'yes' or 'confirm' to proceed."
                )
            ],
            rbac_required=["organization_admin", "site_admin"],
            interaction_examples=[
                "User: 'Create everything'\nAssistant: 'Before I create everything, let me show you a final preview. [shows preview] Do you confirm you want to create all these items?'",
                "User: 'Yes, create it'\nAssistant: 'Creating your training program now... ✅ Created project, ✅ Created 3 tracks, ✅ Enrolled 25 students. Your training program is ready!'"
            ]
        ),
        FunctionSchema(
            name="get_project_builder_status",
            description="Get the current status and what information has been collected for a project builder session.",
            parameters=[
                FunctionParameter(
                    name="session_id",
                    type="string",
                    description="Project builder session ID (UUID)",
                    required=True,
                    clarification_prompt="Which project builder session would you like the status for?"
                )
            ],
            rbac_required=["organization_admin", "site_admin"]
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
            # Delete Functions
            elif function_call.function_name == "delete_project":
                return await self._delete_project(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "delete_track":
                return await self._delete_track(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "delete_course":
                return await self._delete_course(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "delete_subproject":
                return await self._delete_subproject(
                    function_call.arguments,
                    auth_token
                )
            # Project Builder Functions
            elif function_call.function_name == "start_project_builder":
                return await self._start_project_builder(
                    function_call.arguments,
                    auth_token,
                    user_context
                )
            elif function_call.function_name == "submit_project_builder_message":
                return await self._submit_project_builder_message(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "upload_project_roster":
                return await self._upload_project_roster(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "generate_project_schedule":
                return await self._generate_project_schedule(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "preview_project_creation":
                return await self._preview_project_creation(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "execute_project_creation":
                return await self._execute_project_creation(
                    function_call.arguments,
                    auth_token
                )
            elif function_call.function_name == "get_project_builder_status":
                return await self._get_project_builder_status(
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

    # =========================================================================
    # DELETE API METHODS
    # =========================================================================

    async def _delete_project(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Execute delete_project API call.

        BUSINESS PURPOSE:
        Allows AI assistant to delete projects on behalf of organization admins.
        Cascades to delete all tracks, sub-projects, and enrollments.

        TECHNICAL IMPLEMENTATION:
        Calls organization-management service DELETE endpoint.
        Handles force parameter for active enrollment override.
        """
        try:
            org_id = arguments["organization_id"]
            project_id = arguments["project_id"]
            force = arguments.get("force", False)

            force_param = "?force=true" if force else ""
            url = f"{self.api_base_url}:8008/organizations/{org_id}/projects/{project_id}{force_param}"

            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.delete(url, headers=headers)

            if response.status_code == 409:
                # Active enrollments conflict
                error_data = response.json()
                return ActionResult(
                    success=False,
                    function_name="delete_project",
                    error_message=f"Cannot delete project: {error_data.get('detail', {}).get('error', 'Active enrollments exist')}. Use force=true to override.",
                    result_data=error_data
                )

            response.raise_for_status()
            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="delete_project",
                result_data=result_data,
                user_message=f"Project deleted successfully. Removed {result_data.get('deleted_tracks', 0)} tracks and {result_data.get('deleted_subprojects', 0)} sub-projects."
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="delete_project",
                error_message=f"Failed to delete project: {e}"
            )

    async def _delete_track(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Execute delete_track API call.

        BUSINESS PURPOSE:
        Allows AI assistant to delete learning tracks.
        Validates no active enrollments before deletion.

        TECHNICAL IMPLEMENTATION:
        Calls organization-management service track DELETE endpoint.
        """
        try:
            track_id = arguments["track_id"]
            url = f"{self.api_base_url}:8008/api/v1/tracks/{track_id}"

            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="delete_track",
                result_data=result_data,
                user_message="Track deleted successfully."
            )

        except httpx.HTTPError as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
            return ActionResult(
                success=False,
                function_name="delete_track",
                error_message=f"Failed to delete track: {error_detail or e}"
            )

    async def _delete_course(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Execute delete_course API call.

        BUSINESS PURPOSE:
        Allows AI assistant to delete courses. Organization admins
        can delete any course in their org, instructors only their own.

        TECHNICAL IMPLEMENTATION:
        Calls course-management service DELETE endpoint.
        Role-based permission check happens in the service.
        """
        try:
            course_id = arguments["course_id"]
            url = f"{self.api_base_url}:8004/courses/{course_id}"

            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="delete_course",
                result_data=result_data,
                user_message="Course deleted successfully."
            )

        except httpx.HTTPError as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
            return ActionResult(
                success=False,
                function_name="delete_course",
                error_message=f"Failed to delete course: {error_detail or e}"
            )

    async def _delete_subproject(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Execute delete_subproject API call.

        BUSINESS PURPOSE:
        Allows AI assistant to delete sub-projects/locations from a project.
        This also removes any track assignments for the location.

        TECHNICAL IMPLEMENTATION:
        Calls course-management service sub-project DELETE endpoint.
        """
        try:
            org_id = arguments["organization_id"]
            project_id = arguments["project_id"]
            sub_project_id = arguments["sub_project_id"]

            url = f"{self.api_base_url}:8004/api/v1/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}"

            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()

            # 204 No Content response
            if response.status_code == 204:
                return ActionResult(
                    success=True,
                    function_name="delete_subproject",
                    result_data={"message": "Sub-project deleted"},
                    user_message="Sub-project deleted successfully."
                )

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="delete_subproject",
                result_data=result_data,
                user_message="Sub-project deleted successfully."
            )

        except httpx.HTTPError as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
            return ActionResult(
                success=False,
                function_name="delete_subproject",
                error_message=f"Failed to delete sub-project: {error_detail or e}"
            )

    # =========================================================================
    # PROJECT BUILDER API METHODS
    # =========================================================================

    async def _start_project_builder(
        self,
        arguments: Dict[str, Any],
        auth_token: str,
        user_context: UserContext
    ) -> ActionResult:
        """
        Start a new project builder session.

        BUSINESS PURPOSE:
        Initiates AI-assisted bulk project creation workflow. Creates session
        that tracks conversation state, collected specifications, and progress.

        TECHNICAL IMPLEMENTATION:
        Calls course-management service to create orchestrator session.
        Returns session ID for subsequent interactions.
        """
        try:
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions"
            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "organization_id": arguments["organization_id"],
                "user_id": str(user_context.user_id)
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="start_project_builder",
                result_data=result_data,
                user_message=f"Project builder session started. Session ID: {result_data.get('session_id')}. Tell me about the training program you want to create."
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="start_project_builder",
                error_message=f"Failed to start project builder: {e}"
            )

    async def _submit_project_builder_message(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Submit message to project builder session.

        BUSINESS PURPOSE:
        Processes natural language input to build project specification.
        Extracts project details, locations, tracks, and requirements.

        TECHNICAL IMPLEMENTATION:
        Sends message to orchestrator which uses NLP to classify intent
        and extract entities, updating the project specification.
        """
        try:
            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}/messages"
            headers = {"Authorization": f"Bearer {auth_token}"}

            payload = {
                "message": arguments["message"]
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            return ActionResult(
                success=True,
                function_name="submit_project_builder_message",
                result_data=result_data,
                user_message=result_data.get("response_message", "Message processed.")
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="submit_project_builder_message",
                error_message=f"Failed to process message: {e}"
            )

    async def _upload_project_roster(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Upload and process roster file.

        BUSINESS PURPOSE:
        Enables bulk import of instructor/student data from spreadsheets.
        Parses file and adds entries to project specification.

        TECHNICAL IMPLEMENTATION:
        Decodes base64 file content and sends to roster parser.
        Validates entries and reports any parsing errors.
        """
        import base64

        try:
            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}/rosters"
            headers = {"Authorization": f"Bearer {auth_token}"}

            # Decode base64 file content
            file_content = base64.b64decode(arguments["file_content_base64"])

            payload = {
                "roster_type": arguments["roster_type"],
                "filename": arguments["filename"],
                "file_content": arguments["file_content_base64"]  # Send as base64
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            # Build user-friendly message
            msg_parts = []
            if result_data.get("instructors_added", 0) > 0:
                msg_parts.append(f"{result_data['instructors_added']} instructors added")
            if result_data.get("students_added", 0) > 0:
                msg_parts.append(f"{result_data['students_added']} students added")
            if result_data.get("records_failed", 0) > 0:
                msg_parts.append(f"{result_data['records_failed']} records had errors")

            user_msg = "Roster processed: " + ", ".join(msg_parts) if msg_parts else "Roster processed."

            return ActionResult(
                success=True,
                function_name="upload_project_roster",
                result_data=result_data,
                user_message=user_msg
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="upload_project_roster",
                error_message=f"Failed to process roster: {e}"
            )

    async def _generate_project_schedule(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Generate schedule proposal.

        BUSINESS PURPOSE:
        Creates optimized schedule based on project specification.
        Considers instructor availability, room capacity, and conflicts.

        TECHNICAL IMPLEMENTATION:
        Calls schedule generator service with current spec.
        Returns proposal with any detected conflicts.
        """
        try:
            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}/schedule"
            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.post(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            # Build status message
            conflicts = result_data.get("conflicts", [])
            if conflicts:
                user_msg = f"Schedule generated with {len(conflicts)} conflicts. Review and adjust before proceeding."
            else:
                user_msg = "Schedule generated successfully with no conflicts. Ready to proceed."

            return ActionResult(
                success=True,
                function_name="generate_project_schedule",
                result_data=result_data,
                user_message=user_msg
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="generate_project_schedule",
                error_message=f"Failed to generate schedule: {e}"
            )

    async def _preview_project_creation(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Preview what will be created (dry run).

        BUSINESS PURPOSE:
        Shows user exactly what will be created before execution.
        Allows review and confirmation of project structure.

        TECHNICAL IMPLEMENTATION:
        Calls bulk creator in dry-run mode to simulate creation.
        Returns summary of all entities that would be created.
        """
        try:
            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}/preview"
            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            # Build summary message
            summary = result_data.get("summary", {})
            msg_parts = []
            if summary.get("projects", 0) > 0:
                msg_parts.append(f"{summary['projects']} projects")
            if summary.get("tracks", 0) > 0:
                msg_parts.append(f"{summary['tracks']} tracks")
            if summary.get("courses", 0) > 0:
                msg_parts.append(f"{summary['courses']} courses")
            if summary.get("instructors", 0) > 0:
                msg_parts.append(f"{summary['instructors']} instructor assignments")
            if summary.get("students", 0) > 0:
                msg_parts.append(f"{summary['students']} student enrollments")

            user_msg = "Will create: " + ", ".join(msg_parts) if msg_parts else "Preview generated."

            return ActionResult(
                success=True,
                function_name="preview_project_creation",
                result_data=result_data,
                user_message=user_msg
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="preview_project_creation",
                error_message=f"Failed to generate preview: {e}"
            )

    async def _execute_project_creation(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Execute actual project creation.

        BUSINESS PURPOSE:
        Creates all project components in the database.
        Includes projects, tracks, courses, users, and enrollments.

        TECHNICAL IMPLEMENTATION:
        Calls bulk creator service with confirmed spec.
        Handles transactional creation with rollback on failure.
        """
        try:
            if not arguments.get("confirm"):
                return ActionResult(
                    success=False,
                    function_name="execute_project_creation",
                    error_message="Creation requires confirmation. Set confirm=true to proceed."
                )

            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}/execute"
            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.post(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            if result_data.get("success"):
                user_msg = "Project created successfully! All components have been set up."
            else:
                errors = result_data.get("errors", [])
                user_msg = f"Creation completed with {len(errors)} errors. Review the results."

            return ActionResult(
                success=result_data.get("success", False),
                function_name="execute_project_creation",
                result_data=result_data,
                user_message=user_msg
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="execute_project_creation",
                error_message=f"Project creation failed: {e}"
            )

    async def _get_project_builder_status(
        self,
        arguments: Dict[str, Any],
        auth_token: str
    ) -> ActionResult:
        """
        Get project builder session status.

        BUSINESS PURPOSE:
        Retrieves current state and progress of project builder session.
        Shows collected specifications and any pending actions.

        TECHNICAL IMPLEMENTATION:
        Fetches session state from orchestrator.
        Returns specification summary and current workflow state.
        """
        try:
            session_id = arguments["session_id"]
            url = f"{self.api_base_url}:8004/api/v1/project-builder/sessions/{session_id}"
            headers = {"Authorization": f"Bearer {auth_token}"}

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            result_data = response.json()

            # Build status message
            state = result_data.get("state", "unknown")
            spec = result_data.get("spec", {})

            status_parts = [f"State: {state}"]
            if spec.get("name"):
                status_parts.append(f"Project: {spec['name']}")
            if spec.get("locations"):
                status_parts.append(f"Locations: {len(spec['locations'])}")
            if spec.get("instructors"):
                status_parts.append(f"Instructors: {len(spec['instructors'])}")
            if spec.get("students"):
                status_parts.append(f"Students: {len(spec['students'])}")

            user_msg = " | ".join(status_parts)

            return ActionResult(
                success=True,
                function_name="get_project_builder_status",
                result_data=result_data,
                user_message=user_msg
            )

        except httpx.HTTPError as e:
            return ActionResult(
                success=False,
                function_name="get_project_builder_status",
                error_message=f"Failed to get status: {e}"
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
