"""
Integration Tests for Student AI Prompts

BUSINESS CONTEXT:
Tests the integration of student AI prompts across the platform components:
- RAG Lab Assistant integration
- API endpoint integration
- WebSocket handler integration

WHY THESE TESTS:
- Verify prompts are correctly imported and used
- Ensure graceful degradation when prompts unavailable
- Confirm emotional support integration works
- Validate skill-level adaptation functions

TEST COVERAGE:
1. RAG Lab Assistant prompt methods
2. Error explanation integration
3. Emotional support retrieval
4. Encouragement phrase retrieval
5. Context mapping correctness
"""
import pytest
import asyncio
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add service to path
project_root = Path(__file__).parent.parent.parent
# Lab-manager path is added first for rag_lab_assistant imports
lab_manager_path = str(project_root / "services" / "lab-manager")
ai_assistant_path = str(project_root / "services" / "ai-assistant-service")
sys.path.insert(0, lab_manager_path)
sys.path.insert(0, ai_assistant_path)

# Import the endpoint models directly from lab-manager for testing
# We import them here at module level to avoid path conflicts
import importlib.util
_endpoint_spec = importlib.util.spec_from_file_location(
    "rag_assistant_endpoints",
    project_root / "services" / "lab-manager" / "api" / "rag_assistant_endpoints.py"
)
_rag_assistant_endpoints = importlib.util.module_from_spec(_endpoint_spec)
_endpoint_spec.loader.exec_module(_rag_assistant_endpoints)

# Export endpoint models for test access
EmotionalSupportRequest = _rag_assistant_endpoints.EmotionalSupportRequest
EmotionalSupportResponse = _rag_assistant_endpoints.EmotionalSupportResponse
ErrorExplanationRequest = _rag_assistant_endpoints.ErrorExplanationRequest
ErrorExplanationResponse = _rag_assistant_endpoints.ErrorExplanationResponse
EncouragementRequest = _rag_assistant_endpoints.EncouragementRequest
EncouragementResponse = _rag_assistant_endpoints.EncouragementResponse
PromptStatusResponse = _rag_assistant_endpoints.PromptStatusResponse


class TestRAGLabAssistantPromptIntegration:
    """
    Tests for RAG Lab Assistant prompt integration.

    BUSINESS CONTEXT:
    Verifies that the RAG Lab Assistant correctly uses
    student AI prompts for pedagogically-sound responses.
    """

    def test_student_prompts_import_flag(self):
        """Verify STUDENT_PROMPTS_AVAILABLE flag is set."""
        from rag_lab_assistant import STUDENT_PROMPTS_AVAILABLE

        # Should be True if student prompts module exists
        assert isinstance(STUDENT_PROMPTS_AVAILABLE, bool)

    def test_assistance_to_context_mapping_exists(self):
        """Verify assistance type to context mapping is defined."""
        from rag_lab_assistant import RAGLabAssistant

        assert hasattr(RAGLabAssistant, 'ASSISTANCE_TO_CONTEXT_MAP')
        mapping = RAGLabAssistant.ASSISTANCE_TO_CONTEXT_MAP

        # Verify required mappings
        assert "debugging" in mapping
        assert "code_review" in mapping
        assert "concept_explanation" in mapping
        assert "implementation_help" in mapping

    def test_error_explanation_method_exists(self):
        """Verify error explanation method exists on RAGLabAssistant."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        assert hasattr(assistant, 'get_error_explanation_prompt')

    def test_emotional_support_method_exists(self):
        """Verify emotional support method exists on RAGLabAssistant."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        assert hasattr(assistant, 'get_emotional_support_response')

    def test_encouragement_method_exists(self):
        """Verify encouragement method exists on RAGLabAssistant."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        assert hasattr(assistant, 'get_encouragement')


class TestErrorExplanationIntegration:
    """
    Tests for error explanation integration.

    BUSINESS CONTEXT:
    Verifies that error explanations are correctly
    retrieved and formatted for student understanding.
    """

    def test_syntax_error_explanation(self):
        """Verify syntax error produces valid explanation."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_error_explanation_prompt("SyntaxError: invalid syntax")

        assert "explanation" in result
        assert "common_causes" in result
        assert isinstance(result["common_causes"], list)

    def test_name_error_explanation(self):
        """Verify name error produces valid explanation."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_error_explanation_prompt("NameError: name 'x' is not defined")

        assert "explanation" in result
        assert len(result["explanation"]) > 0

    def test_type_error_explanation(self):
        """Verify type error produces valid explanation."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_error_explanation_prompt("TypeError: unsupported operand type")

        assert "explanation" in result
        assert "teaching_moment" in result or "common_causes" in result

    def test_unknown_error_fallback(self):
        """Verify unknown errors get fallback explanation."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_error_explanation_prompt("SomeWeirdError: unknown issue")

        assert "explanation" in result
        assert "common_causes" in result

    def test_error_type_detection(self):
        """Verify error type detection works correctly."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()

        assert assistant._detect_error_type("SyntaxError: invalid syntax") == "syntax_error"
        assert assistant._detect_error_type("NameError: name not defined") == "name_error"
        assert assistant._detect_error_type("TypeError: wrong type") == "type_error"
        assert assistant._detect_error_type("IndexError: out of range") == "index_error"
        assert assistant._detect_error_type("KeyError: missing key") == "key_error"


class TestEmotionalSupportIntegration:
    """
    Tests for emotional support integration.

    BUSINESS CONTEXT:
    Verifies that emotional support is correctly
    retrieved for different student emotional states.
    """

    def test_frustrated_support(self):
        """Verify frustrated emotion produces support."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_emotional_support_response("frustrated")

        assert "recognition" in result
        assert "validation" in result
        assert "support" in result
        assert isinstance(result["support"], list)

    def test_confused_support(self):
        """Verify confused emotion produces support."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_emotional_support_response("confused")

        assert "recognition" in result
        assert len(result["support"]) > 0

    def test_discouraged_support(self):
        """Verify discouraged emotion produces support."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_emotional_support_response("discouraged")

        assert "recognition" in result
        assert "validation" in result

    def test_unknown_emotion_fallback(self):
        """Verify unknown emotions get fallback support."""
        from rag_lab_assistant import RAGLabAssistant

        assistant = RAGLabAssistant()
        result = assistant.get_emotional_support_response("unknown_feeling")

        assert "recognition" in result
        assert "support" in result


class TestEncouragementIntegration:
    """
    Tests for encouragement integration.

    BUSINESS CONTEXT:
    Verifies that encouragement phrases are correctly
    retrieved based on student skill level.
    """

    def test_beginner_encouragement(self):
        """Verify beginner level produces encouragement."""
        from rag_lab_assistant import RAGLabAssistant, SkillLevel

        assistant = RAGLabAssistant()
        result = assistant.get_encouragement(SkillLevel.BEGINNER)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_intermediate_encouragement(self):
        """Verify intermediate level produces encouragement."""
        from rag_lab_assistant import RAGLabAssistant, SkillLevel

        assistant = RAGLabAssistant()
        result = assistant.get_encouragement(SkillLevel.INTERMEDIATE)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_advanced_encouragement(self):
        """Verify advanced level produces encouragement."""
        from rag_lab_assistant import RAGLabAssistant, SkillLevel

        assistant = RAGLabAssistant()
        result = assistant.get_encouragement(SkillLevel.ADVANCED)

        assert isinstance(result, list)
        assert len(result) > 0


class TestPedagogicalPromptIntegration:
    """
    Tests for pedagogical system prompt integration.

    BUSINESS CONTEXT:
    Verifies that pedagogical prompts are correctly
    built for different assistance types and skill levels.
    """

    def test_pedagogical_prompt_generation(self):
        """Verify pedagogical prompt is generated."""
        from rag_lab_assistant import RAGLabAssistant, AssistanceType, SkillLevel

        assistant = RAGLabAssistant()
        prompt = assistant._get_pedagogical_system_prompt(
            assistance_type=AssistanceType.DEBUGGING,
            skill_level=SkillLevel.BEGINNER
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_fallback_prompt_generation(self):
        """Verify fallback prompt works when prompts unavailable."""
        from rag_lab_assistant import RAGLabAssistant, AssistanceType, SkillLevel

        assistant = RAGLabAssistant()
        prompt = assistant._get_fallback_system_prompt(
            assistance_type=AssistanceType.CODE_REVIEW,
            skill_level=SkillLevel.INTERMEDIATE
        )

        assert "programming assistant" in prompt.lower()
        assert "intermediate" in prompt.lower()

    def test_context_mapping(self):
        """Verify assistance type to context mapping."""
        from rag_lab_assistant import RAGLabAssistant, AssistanceType

        assistant = RAGLabAssistant()

        # Test debugging maps to lab_programming
        context = assistant._get_student_interaction_context(AssistanceType.DEBUGGING)
        if context:  # Only if prompts available
            assert context.value == "lab_programming"


class TestAssistanceResponseIntegration:
    """
    Tests for complete assistance response integration.

    BUSINESS CONTEXT:
    Verifies that assistance responses include
    pedagogical elements when prompts are available.
    """

    @pytest.mark.asyncio
    async def test_assistance_response_metadata(self):
        """Verify response metadata includes prompt info."""
        from rag_lab_assistant import (
            RAGLabAssistant,
            AssistanceRequest,
            CodeContext,
            StudentContext,
            AssistanceType,
            SkillLevel
        )
        from datetime import datetime, timezone

        assistant = RAGLabAssistant()

        # Mock RAG service availability
        with patch.object(assistant, 'is_rag_service_available', return_value=False):
            code_context = CodeContext(
                code="print('hello')",
                language="python",
                file_name="test.py"
            )

            student_context = StudentContext(
                student_id="test_student",
                skill_level=SkillLevel.BEGINNER,
                preferred_explanation_style="detailed",
                learning_goals=[],
                recent_topics=[],
                common_mistakes=[],
                successful_patterns=[]
            )

            request = AssistanceRequest(
                assistance_type=AssistanceType.GENERAL_QUESTION,
                code_context=code_context,
                student_context=student_context,
                specific_question="What is a variable?",
                priority_level="medium",
                timestamp=datetime.now(timezone.utc)
            )

            response = await assistant.provide_assistance(request)

            # Verify response has expected fields
            assert hasattr(response, 'response_text')
            assert hasattr(response, 'learning_feedback')
            assert hasattr(response, 'response_metadata')

            # Verify pedagogical info in metadata
            assert 'pedagogical_prompts_used' in response.learning_feedback


@pytest.mark.skip(reason="Needs refactoring to use real services - currently uses MagicMock")
class TestWebSocketStudentPromptIntegration:
    """
    Tests for WebSocket handler student prompt integration.

    BUSINESS CONTEXT:
    Verifies that the WebSocket handler correctly
    uses student prompts for student users.

    TODO: Refactor to use real service instances instead of MagicMock.
    """

    def test_student_role_detection(self):
        """Verify student role detection works."""
        pass

    def test_emotion_detection(self):
        """Verify emotion detection in messages."""
        pass

    def test_interaction_context_detection(self):
        """Verify interaction context detection."""
        pass


class TestAPIEndpointIntegration:
    """
    Tests for API endpoint integration with prompts.

    BUSINESS CONTEXT:
    Verifies that API endpoints correctly expose
    prompt-related functionality.
    """

    def test_emotional_support_endpoint_model(self):
        """Verify emotional support endpoint models exist."""
        # Using module-level imported models to avoid path conflicts

        # Test request model
        request = EmotionalSupportRequest(
            detected_emotion="frustrated",
            student_context={"topic": "recursion"}
        )
        assert request.detected_emotion == "frustrated"

        # Test response model structure
        response = EmotionalSupportResponse(
            recognition="I see you're frustrated",
            validation="That's normal",
            support=["Take a break", "Let's try again"]
        )
        assert len(response.support) == 2

    def test_error_explanation_endpoint_model(self):
        """Verify error explanation endpoint models exist."""
        # Using module-level imported models to avoid path conflicts

        # Test request model
        request = ErrorExplanationRequest(
            error_message="NameError: name 'x' is not defined"
        )
        assert "NameError" in request.error_message

        # Test response model structure
        response = ErrorExplanationResponse(
            explanation="Variable not defined",
            common_causes=["Typo", "Scope issue"],
            teaching_moment="Check spelling"
        )
        assert len(response.common_causes) == 2

    def test_encouragement_endpoint_model(self):
        """Verify encouragement endpoint models exist."""
        # Using module-level imported models to avoid path conflicts

        # Test request model
        request = EncouragementRequest(skill_level="beginner")
        assert request.skill_level == "beginner"

        # Test response model structure
        response = EncouragementResponse(
            encouragement_phrases=["Great job!", "Keep learning!"],
            skill_level="beginner"
        )
        assert len(response.encouragement_phrases) == 2

    def test_prompts_status_endpoint_model(self):
        """Verify prompts status endpoint model exists."""
        # Using module-level imported PromptStatusResponse to avoid path conflicts

        response = PromptStatusResponse(
            prompts_available=True,
            message="Prompts are available"
        )
        assert response.prompts_available is True
