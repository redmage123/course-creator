"""
Intent and Function Call Entities - AI Assistant Domain

BUSINESS PURPOSE:
Represents user intent and function calls for executing platform actions.
Maps natural language requests to specific API operations.

TECHNICAL IMPLEMENTATION:
Domain entities for function calling pattern. Used by LLM to decide
which platform actions to execute based on user request.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class IntentType(str, Enum):
    """
    User intent types

    BUSINESS PURPOSE:
    Categorizes user requests into actionable intents. Used to determine
    which functions are available and what information is needed.

    TECHNICAL IMPLEMENTATION:
    Enumeration of supported intent types. Mapped to function schemas
    for LLM function calling.

    VALUES:
        CREATE_PROJECT: User wants to create new project
        CREATE_TRACK: User wants to create learning track
        CREATE_COURSE: User wants to create course
        ONBOARD_INSTRUCTOR: User wants to add instructor
        GENERATE_CONTENT: User wants AI content generation
        VIEW_ANALYTICS: User wants to see analytics/reports
        MANAGE_STUDENTS: User wants to manage student enrollments
        HELP_QUESTION: User has question about platform
        GENERAL_CONVERSATION: General chat, no specific action
    """
    CREATE_PROJECT = "create_project"
    CREATE_TRACK = "create_track"
    CREATE_COURSE = "create_course"
    ONBOARD_INSTRUCTOR = "onboard_instructor"
    GENERATE_CONTENT = "generate_content"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_STUDENTS = "manage_students"
    HELP_QUESTION = "help_question"
    GENERAL_CONVERSATION = "general_conversation"


@dataclass
class FunctionParameter:
    """
    Function parameter definition

    BUSINESS PURPOSE:
    Defines required and optional parameters for platform actions.
    Used by LLM to extract information from user message.

    TECHNICAL IMPLEMENTATION:
    JSON Schema-compatible parameter definition. Used in OpenAI
    function calling and Claude tool use.

    ATTRIBUTES:
        name: Parameter name
        type: Parameter type (string, integer, boolean, etc.)
        description: Human-readable parameter description
        required: Whether parameter is required
        enum: Optional list of allowed values
    """
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


@dataclass
class FunctionSchema:
    """
    Function schema for LLM function calling

    BUSINESS PURPOSE:
    Defines available platform actions for AI assistant. Tells LLM
    what functions it can call and what parameters are needed.

    TECHNICAL IMPLEMENTATION:
    OpenAI function calling schema format. Used in LLM API calls
    to enable function calling capability.

    ATTRIBUTES:
        name: Function name (matches API endpoint)
        description: What the function does
        parameters: List of function parameters
        rbac_required: Roles required to execute function
    """
    name: str
    description: str
    parameters: List[FunctionParameter]
    rbac_required: List[str] = field(default_factory=list)

    def to_openai_format(self) -> Dict[str, Any]:
        """
        Convert to OpenAI function calling format

        BUSINESS PURPOSE:
        Formats function schema for OpenAI API function calling.
        Required for LLM to understand available actions.

        TECHNICAL IMPLEMENTATION:
        Returns dict matching OpenAI function schema format with
        name, description, and JSON Schema parameters.

        RETURNS:
            OpenAI function schema dictionary
        """
        properties = {}
        required_params = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                param_schema["enum"] = param.enum

            properties[param.name] = param_schema

            if param.required:
                required_params.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_params
            }
        }


@dataclass
class FunctionCall:
    """
    Function call entity

    BUSINESS PURPOSE:
    Represents AI decision to execute platform action. Contains
    function name and extracted parameters from user message.

    TECHNICAL IMPLEMENTATION:
    Created by LLM response parser. Used by FunctionExecutor to
    call actual platform APIs with proper parameters.

    ATTRIBUTES:
        function_name: Name of function to call
        arguments: Extracted parameter values
        intent_type: Detected user intent
        confidence: LLM confidence in function call (0.0-1.0)
    """
    function_name: str
    arguments: Dict[str, Any]
    intent_type: IntentType
    confidence: float = 1.0

    def validate_arguments(self, schema: FunctionSchema) -> bool:
        """
        Validate function arguments against schema

        BUSINESS PURPOSE:
        Ensures LLM extracted all required parameters. Prevents
        errors from calling APIs with missing data.

        TECHNICAL IMPLEMENTATION:
        Checks that all required parameters in schema are present
        in arguments dictionary.

        ARGS:
            schema: Function schema to validate against

        RETURNS:
            True if all required parameters present, False otherwise
        """
        required_params = [p.name for p in schema.parameters if p.required]
        return all(param in self.arguments for param in required_params)


@dataclass
class ActionResult:
    """
    Result of executed function call

    BUSINESS PURPOSE:
    Tracks success/failure of platform actions. Used to generate
    user-facing response and handle errors gracefully.

    TECHNICAL IMPLEMENTATION:
    Returned by FunctionExecutor after API call. Contains success
    status, result data, and error information if applicable.

    ATTRIBUTES:
        success: Whether function executed successfully
        function_name: Function that was called
        result_data: API response data
        error_message: Error message if failed
        rbac_denied: Whether RBAC check failed
    """
    success: bool
    function_name: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    rbac_denied: bool = False

    def to_user_message(self) -> str:
        """
        Convert result to user-facing message

        BUSINESS PURPOSE:
        Generates human-readable response for user. Explains what
        action was taken or why it failed.

        TECHNICAL IMPLEMENTATION:
        Creates natural language message based on success status.
        Includes relevant details from result_data or error_message.

        RETURNS:
            User-friendly result message
        """
        if self.rbac_denied:
            return f"⚠️ You don't have permission to {self.function_name}. Please contact your administrator."

        if not self.success:
            return f"❌ Failed to {self.function_name}: {self.error_message}"

        return f"✅ Successfully completed {self.function_name}"
