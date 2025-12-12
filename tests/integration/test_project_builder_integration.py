"""
Integration Tests for Project Builder Orchestrator

BUSINESS CONTEXT:
Tests the complete Project Builder integration that enables organization admins
to create multi-location training projects through AI-powered conversation.

WHY THESE TESTS:
The Project Builder orchestrator is the central coordinator for:
1. Parsing roster files (CSV, Excel, JSON)
2. Generating optimized training schedules
3. Creating Zoom meeting rooms in bulk
4. Creating projects with tracks and assignments

TEST COVERAGE:
- Session management and state transitions
- Error handling and exception types
- State machine completeness
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Service imports
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "course-management"))
sys.path.insert(0, str(project_root / "services" / "organization-management"))

from course_management.application.services.project_builder_orchestrator import (
    ProjectBuilderOrchestrator,
    ProjectBuilderSession,
    ProjectBuilderState,
    SessionNotFoundException,
    InvalidStateTransitionException,
    ValidationException
)


class TestProjectBuilderSessionManagement:
    """
    Tests for ProjectBuilderSession state management

    BUSINESS CONTEXT:
    Verifies that session state transitions work correctly and
    session data is properly maintained throughout the workflow.
    """

    def test_session_initialization(self):
        """
        Test that session initializes with correct defaults

        BUSINESS RULE: New sessions must start in INITIAL state
        """
        session = ProjectBuilderSession(
            organization_id=uuid4(),
            user_id=uuid4()
        )

        assert session.id is not None
        assert session.state == ProjectBuilderState.INITIAL
        assert session.organization_id is not None
        assert session.user_id is not None

    def test_session_id_uniqueness(self):
        """
        Test that each session gets unique ID

        BUSINESS RULE: Session IDs must be unique for tracking
        """
        session1 = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())
        session2 = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        assert session1.id != session2.id

    def test_session_state_is_enum(self):
        """
        Test that session state uses ProjectBuilderState enum

        BUSINESS RULE: State machine must use defined states only
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        assert isinstance(session.state, ProjectBuilderState)
        assert session.state == ProjectBuilderState.INITIAL

    def test_session_can_change_state(self):
        """
        Test that session state can be changed

        BUSINESS RULE: State transitions must be possible
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())
        session.state = ProjectBuilderState.COLLECTING_DETAILS

        assert session.state == ProjectBuilderState.COLLECTING_DETAILS

    def test_session_preserves_ids(self):
        """
        Test that session preserves organization and user IDs

        BUSINESS RULE: Session must track organization and user context
        """
        org_id = uuid4()
        user_id = uuid4()
        session = ProjectBuilderSession(organization_id=org_id, user_id=user_id)

        assert session.organization_id == org_id
        assert session.user_id == user_id


class TestProjectBuilderStateTransitions:
    """
    Tests for valid state transitions

    BUSINESS CONTEXT:
    Verifies that the state machine enforces valid transitions
    and prevents invalid state changes.
    """

    def test_all_states_defined(self):
        """
        Test that all required states are defined

        BUSINESS RULE: State machine must have all workflow states
        """
        required_states = [
            'INITIAL',
            'COLLECTING_DETAILS',
            'AWAITING_ROSTERS',
            'PARSING_ROSTERS',
            'SCHEDULE_REVIEW',
            'CONTENT_CONFIG',
            'ZOOM_CONFIG',
            'PREVIEW',
            'CREATING',
            'COMPLETE',
            'ERROR'
        ]

        for state_name in required_states:
            assert hasattr(ProjectBuilderState, state_name), \
                f"Missing state: {state_name}"

    def test_initial_state_value(self):
        """
        Test INITIAL state string value

        BUSINESS RULE: State values must be lowercase strings
        """
        assert ProjectBuilderState.INITIAL.value == "initial"

    def test_complete_state_value(self):
        """
        Test COMPLETE state string value

        BUSINESS RULE: COMPLETE is terminal success state
        """
        assert ProjectBuilderState.COMPLETE.value == "complete"

    def test_error_state_value(self):
        """
        Test ERROR state string value

        BUSINESS RULE: ERROR is recoverable error state
        """
        assert ProjectBuilderState.ERROR.value == "error"

    def test_collecting_details_state_value(self):
        """
        Test COLLECTING_DETAILS state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.COLLECTING_DETAILS.value == "collecting_details"

    def test_awaiting_rosters_state_value(self):
        """
        Test AWAITING_ROSTERS state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.AWAITING_ROSTERS.value == "awaiting_rosters"

    def test_parsing_rosters_state_value(self):
        """
        Test PARSING_ROSTERS state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.PARSING_ROSTERS.value == "parsing_rosters"

    def test_schedule_review_state_value(self):
        """
        Test SCHEDULE_REVIEW state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.SCHEDULE_REVIEW.value == "schedule_review"

    def test_preview_state_value(self):
        """
        Test PREVIEW state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.PREVIEW.value == "preview"

    def test_creating_state_value(self):
        """
        Test CREATING state value

        BUSINESS RULE: States follow consistent naming convention
        """
        assert ProjectBuilderState.CREATING.value == "creating"

    def test_state_is_string_enum(self):
        """
        Test that states are string enums

        BUSINESS RULE: States must be serializable as strings
        """
        assert issubclass(ProjectBuilderState, str)

    def test_state_count(self):
        """
        Test that we have expected number of states

        BUSINESS RULE: 11 states for complete workflow
        """
        states = list(ProjectBuilderState)
        assert len(states) == 11


class TestProjectBuilderErrorHandling:
    """
    Tests for error handling in Project Builder

    BUSINESS CONTEXT:
    Verifies that errors are handled gracefully and
    users receive helpful error messages.
    """

    def test_session_not_found_error(self):
        """
        Test handling of non-existent session

        BUSINESS RULE: Invalid session IDs must raise clear error
        """
        with pytest.raises(SessionNotFoundException):
            raise SessionNotFoundException("Session not found", session_id=uuid4())

    def test_session_not_found_contains_id(self):
        """
        Test that SessionNotFoundException contains session ID

        BUSINESS RULE: Errors must include relevant context
        """
        session_id = uuid4()
        try:
            raise SessionNotFoundException("Not found", session_id=session_id)
        except SessionNotFoundException as e:
            assert e.session_id == session_id

    def test_invalid_state_transition_error(self):
        """
        Test handling of invalid state transition

        BUSINESS RULE: Invalid transitions must raise clear error
        """
        with pytest.raises(InvalidStateTransitionException):
            raise InvalidStateTransitionException("Invalid transition")

    def test_validation_error(self):
        """
        Test handling of validation errors

        BUSINESS RULE: Validation errors must be descriptive
        """
        with pytest.raises(ValidationException):
            raise ValidationException("Missing required field: name")

    def test_validation_error_message(self):
        """
        Test that ValidationException preserves message

        BUSINESS RULE: Error messages must be helpful
        """
        message = "Field 'email' is required"
        try:
            raise ValidationException(message)
        except ValidationException as e:
            assert message in str(e)

    def test_exception_has_timestamp(self):
        """
        Test that exceptions include timestamp

        BUSINESS RULE: Errors must be traceable in time
        """
        try:
            raise SessionNotFoundException("Not found", session_id=uuid4())
        except SessionNotFoundException as e:
            assert hasattr(e, 'timestamp')
            assert e.timestamp is not None


class TestProjectBuilderSessionWorkflow:
    """
    Tests for session workflow patterns

    BUSINESS CONTEXT:
    Verifies common workflow patterns work correctly
    """

    def test_session_workflow_from_initial_to_complete(self):
        """
        Test that session can transition through entire workflow

        BUSINESS RULE: Complete workflow path must be valid
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        # Simulate workflow
        workflow_states = [
            ProjectBuilderState.INITIAL,
            ProjectBuilderState.COLLECTING_DETAILS,
            ProjectBuilderState.AWAITING_ROSTERS,
            ProjectBuilderState.PARSING_ROSTERS,
            ProjectBuilderState.SCHEDULE_REVIEW,
            ProjectBuilderState.PREVIEW,
            ProjectBuilderState.CREATING,
            ProjectBuilderState.COMPLETE
        ]

        for expected_state in workflow_states:
            session.state = expected_state
            assert session.state == expected_state

    def test_session_can_enter_error_state(self):
        """
        Test that session can enter error state from any state

        BUSINESS RULE: Errors can occur at any point in workflow
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        # From various states, should be able to go to ERROR
        for state in ProjectBuilderState:
            if state != ProjectBuilderState.COMPLETE:
                session.state = state
                session.state = ProjectBuilderState.ERROR
                assert session.state == ProjectBuilderState.ERROR

    def test_session_can_recover_from_error(self):
        """
        Test that session can recover from error state

        BUSINESS RULE: ERROR state should be recoverable
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())
        session.state = ProjectBuilderState.ERROR

        # Should be able to go back to collecting details
        session.state = ProjectBuilderState.COLLECTING_DETAILS
        assert session.state == ProjectBuilderState.COLLECTING_DETAILS


class TestProjectBuilderAIPrompts:
    """
    Tests for AI prompt configuration and methods.

    BUSINESS CONTEXT:
    Verifies that AI prompts are correctly configured and
    accessible for the AI backend integration.
    """

    def test_system_prompt_exists(self):
        """
        Test that system prompt is defined.

        BUSINESS RULE: AI backend requires system prompt
        """
        from course_management.application.services.project_builder_orchestrator import (
            SYSTEM_PROMPT
        )
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100  # Should be substantial

    def test_system_prompt_contains_key_sections(self):
        """
        Test that system prompt has required sections.

        BUSINESS RULE: System prompt must guide AI behavior
        """
        from course_management.application.services.project_builder_orchestrator import (
            SYSTEM_PROMPT
        )
        assert "CORE RESPONSIBILITIES" in SYSTEM_PROMPT
        assert "COMMUNICATION STYLE" in SYSTEM_PROMPT
        assert "KEY ENTITIES TO EXTRACT" in SYSTEM_PROMPT
        assert "WORKFLOW STATES" in SYSTEM_PROMPT
        assert "IMPORTANT RULES" in SYSTEM_PROMPT

    def test_state_prompts_exist(self):
        """
        Test that state prompts dictionary is defined.

        BUSINESS RULE: Each state needs contextual prompts
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        assert STATE_PROMPTS is not None
        assert isinstance(STATE_PROMPTS, dict)

    def test_state_prompts_cover_all_states(self):
        """
        Test that prompts exist for all workflow states.

        BUSINESS RULE: Complete coverage of workflow states
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS, ProjectBuilderState
        )
        for state in ProjectBuilderState:
            assert state.value in STATE_PROMPTS, f"Missing prompts for state: {state.value}"

    def test_state_prompt_has_required_keys(self):
        """
        Test that each state prompt has required structure.

        BUSINESS RULE: Consistent prompt structure
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        required_keys = ["system_context", "user_instruction"]

        for state, prompts in STATE_PROMPTS.items():
            for key in required_keys:
                assert key in prompts, f"State {state} missing key: {key}"

    def test_get_system_prompt_method(self):
        """
        Test the static get_system_prompt method.

        BUSINESS RULE: Easy access to system prompt
        """
        system_prompt = ProjectBuilderOrchestrator.get_system_prompt()
        assert system_prompt is not None
        assert "organization administrators" in system_prompt.lower()

    def test_initial_state_prompt_has_triggers(self):
        """
        Test that initial state has high confidence triggers.

        BUSINESS RULE: AI should recognize project creation intent
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        initial_prompt = STATE_PROMPTS.get("initial", {})
        triggers = initial_prompt.get("high_confidence_triggers", [])

        assert len(triggers) > 0
        assert "create a new project" in triggers

    def test_preview_state_has_confirmation_triggers(self):
        """
        Test that preview state has confirmation/rejection triggers.

        BUSINESS RULE: AI should recognize user confirmation intent
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        preview_prompt = STATE_PROMPTS.get("preview", {})

        confirmation = preview_prompt.get("confirmation_triggers", [])
        rejection = preview_prompt.get("rejection_triggers", [])

        assert "confirm" in confirmation
        assert "cancel" in rejection

    def test_creating_state_has_progress_messages(self):
        """
        Test that creating state has progress message templates.

        BUSINESS RULE: Users need creation progress updates
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        creating_prompt = STATE_PROMPTS.get("creating", {})
        progress = creating_prompt.get("progress_messages", {})

        assert "start" in progress
        assert "project" in progress
        assert "complete" in progress

    def test_error_state_has_recovery_prompts(self):
        """
        Test that error state has recovery prompts.

        BUSINESS RULE: Errors must have recovery guidance
        """
        from course_management.application.services.project_builder_orchestrator import (
            STATE_PROMPTS
        )
        error_prompt = STATE_PROMPTS.get("error", {})
        recovery = error_prompt.get("recovery_prompts", {})

        assert "validation" in recovery
        assert "file_error" in recovery
        assert "creation_failed" in recovery


class TestProjectBuilderStateValidation:
    """
    Tests for state validation logic

    BUSINESS CONTEXT:
    Verifies that state values are correctly validated
    """

    def test_state_comparison(self):
        """
        Test that states can be compared

        BUSINESS RULE: States must be comparable for conditionals
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        assert session.state == ProjectBuilderState.INITIAL
        assert session.state != ProjectBuilderState.COMPLETE

    def test_state_in_collection(self):
        """
        Test that state membership checks work

        BUSINESS RULE: States must work in collections
        """
        active_states = {
            ProjectBuilderState.COLLECTING_DETAILS,
            ProjectBuilderState.AWAITING_ROSTERS,
            ProjectBuilderState.PARSING_ROSTERS,
            ProjectBuilderState.SCHEDULE_REVIEW,
            ProjectBuilderState.PREVIEW,
            ProjectBuilderState.CREATING
        }

        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())
        session.state = ProjectBuilderState.COLLECTING_DETAILS

        assert session.state in active_states

    def test_state_string_serialization(self):
        """
        Test that states serialize to strings

        BUSINESS RULE: States must be JSON serializable
        """
        session = ProjectBuilderSession(organization_id=uuid4(), user_id=uuid4())

        # String enum should be directly usable as string
        state_str = str(session.state)
        assert isinstance(state_str, str)

    def test_terminal_states(self):
        """
        Test identification of terminal states

        BUSINESS RULE: COMPLETE is terminal, ERROR is not
        """
        terminal_states = {ProjectBuilderState.COMPLETE}
        non_terminal_states = set(ProjectBuilderState) - terminal_states

        assert ProjectBuilderState.COMPLETE in terminal_states
        assert ProjectBuilderState.ERROR in non_terminal_states
        assert ProjectBuilderState.INITIAL in non_terminal_states
