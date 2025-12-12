"""
Unit Tests for Student AI Prompts

BUSINESS CONTEXT:
Tests the student AI prompts module to ensure correct prompt generation,
context handling, and pedagogical appropriateness.

WHY THESE TESTS:
- Verify prompts are correctly configured for all contexts
- Ensure skill level adaptation works properly
- Validate emotional support prompts are helpful
- Test error explanation generation
- Confirm helper functions work as expected
"""
import pytest
import sys
from pathlib import Path

# Add service to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "ai-assistant-service"))

from ai_assistant_service.application.services.student_ai_prompts import (
    # Enums
    StudentInteractionContext,
    StudentSkillLevel,
    AssistanceIntensity,

    # Constants
    STUDENT_SYSTEM_PROMPT,
    LEARNING_CONTEXT_PROMPTS,
    SKILL_LEVEL_PROMPTS,
    ASSISTANCE_INTENSITY_PROMPTS,
    EMOTIONAL_SUPPORT_PROMPTS,
    ERROR_EXPLANATION_PROMPTS,

    # Functions
    get_student_prompt,
    get_quiz_hint,
    get_emotional_support,
    get_error_explanation,
    get_encouragement_for_level,
    build_contextual_prompt
)


class TestStudentSystemPrompt:
    """
    Tests for the base student system prompt.

    BUSINESS CONTEXT:
    Verifies the system prompt contains essential pedagogical elements.
    """

    def test_system_prompt_exists(self):
        """System prompt should be defined and substantial."""
        assert STUDENT_SYSTEM_PROMPT is not None
        assert len(STUDENT_SYSTEM_PROMPT) > 500

    def test_system_prompt_has_core_identity(self):
        """System prompt should define AI identity."""
        assert "CORE IDENTITY" in STUDENT_SYSTEM_PROMPT

    def test_system_prompt_has_pedagogical_approach(self):
        """System prompt should include pedagogical principles."""
        assert "PEDAGOGICAL APPROACH" in STUDENT_SYSTEM_PROMPT
        assert "Socratic" in STUDENT_SYSTEM_PROMPT
        assert "Scaffolding" in STUDENT_SYSTEM_PROMPT

    def test_system_prompt_has_communication_style(self):
        """System prompt should define communication style."""
        assert "COMMUNICATION STYLE" in STUDENT_SYSTEM_PROMPT

    def test_system_prompt_has_response_guidelines(self):
        """System prompt should include response guidelines."""
        assert "RESPONSE GUIDELINES" in STUDENT_SYSTEM_PROMPT

    def test_system_prompt_has_boundaries(self):
        """System prompt should set appropriate boundaries."""
        assert "BOUNDARIES" in STUDENT_SYSTEM_PROMPT
        assert "Never do assignments for students" in STUDENT_SYSTEM_PROMPT

    def test_system_prompt_mentions_growth_mindset(self):
        """System prompt should encourage growth mindset."""
        assert "growth mindset" in STUDENT_SYSTEM_PROMPT.lower()


class TestLearningContextPrompts:
    """
    Tests for learning context-specific prompts.

    BUSINESS CONTEXT:
    Verifies prompts exist for all learning contexts.
    """

    def test_all_contexts_have_prompts(self):
        """All StudentInteractionContext values should have prompts."""
        for context in StudentInteractionContext:
            assert context.value in LEARNING_CONTEXT_PROMPTS, \
                f"Missing prompts for context: {context.value}"

    def test_course_content_has_required_keys(self):
        """Course content prompts should have required structure."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("course_content", {})
        assert "system_context" in prompts
        assert "opening_prompts" in prompts
        assert "follow_up_prompts" in prompts

    def test_quiz_help_has_hint_levels(self):
        """Quiz help should have progressive hint levels."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("quiz_help", {})
        hint_levels = prompts.get("hint_levels", {})

        assert "level_1" in hint_levels
        assert "level_2" in hint_levels
        assert "level_3" in hint_levels
        assert "level_4" in hint_levels

    def test_quiz_help_discourages_direct_answers(self):
        """Quiz help should explicitly prevent giving direct answers."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("quiz_help", {})
        system_context = prompts.get("system_context", "")

        assert "NEVER provide direct answers" in system_context

    def test_lab_programming_has_debugging_prompts(self):
        """Lab programming context should have debugging prompts."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("lab_programming", {})
        assert "debugging_prompts" in prompts
        assert len(prompts["debugging_prompts"]) > 0

    def test_onboarding_has_welcome_prompts(self):
        """Onboarding context should have welcoming prompts."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("onboarding", {})
        assert "welcome_prompts" in prompts
        assert len(prompts["welcome_prompts"]) > 0

    def test_study_planning_has_techniques(self):
        """Study planning should include study techniques."""
        prompts = LEARNING_CONTEXT_PROMPTS.get("study_planning", {})
        techniques = prompts.get("study_techniques", {})

        assert "spaced_repetition" in techniques
        assert "active_recall" in techniques
        assert "pomodoro" in techniques


class TestSkillLevelPrompts:
    """
    Tests for skill level-specific prompts.

    BUSINESS CONTEXT:
    Verifies prompts adapt appropriately to different skill levels.
    """

    def test_all_skill_levels_have_prompts(self):
        """All skill levels should have prompts."""
        for level in StudentSkillLevel:
            assert level.value in SKILL_LEVEL_PROMPTS, \
                f"Missing prompts for skill level: {level.value}"

    def test_beginner_prompts_emphasize_simplicity(self):
        """Beginner prompts should emphasize simple language."""
        prompts = SKILL_LEVEL_PROMPTS.get("beginner", {})

        assert prompts.get("language_style") == "simple, clear, step-by-step"
        assert "jargon" in prompts.get("vocabulary", "").lower()  # "avoid jargon"

    def test_advanced_prompts_use_technical_language(self):
        """Advanced prompts should use technical language."""
        prompts = SKILL_LEVEL_PROMPTS.get("advanced", {})

        assert prompts.get("language_style") == "technical, industry-standard"
        assert "full technical vocabulary" in prompts.get("vocabulary", "")

    def test_all_levels_have_system_context(self):
        """All skill levels should have system context."""
        for level in StudentSkillLevel:
            prompts = SKILL_LEVEL_PROMPTS.get(level.value, {})
            assert "system_context" in prompts

    def test_all_levels_have_encouragement(self):
        """All skill levels should have encouragement phrases."""
        for level in StudentSkillLevel:
            prompts = SKILL_LEVEL_PROMPTS.get(level.value, {})
            assert "encouragement" in prompts
            assert len(prompts["encouragement"]) > 0


class TestEmotionalSupportPrompts:
    """
    Tests for emotional support prompts.

    BUSINESS CONTEXT:
    Verifies emotional support is available for common student emotions.
    """

    def test_common_emotions_covered(self):
        """Common student emotions should have support prompts."""
        expected_emotions = ["frustrated", "confused", "discouraged", "anxious", "excited", "accomplished"]

        for emotion in expected_emotions:
            assert emotion in EMOTIONAL_SUPPORT_PROMPTS, \
                f"Missing support for emotion: {emotion}"

    def test_emotional_support_has_required_keys(self):
        """Each emotion should have recognition, validation, and support."""
        for emotion, prompts in EMOTIONAL_SUPPORT_PROMPTS.items():
            assert "recognition" in prompts, f"{emotion} missing recognition"
            assert "validation" in prompts, f"{emotion} missing validation"
            assert "support" in prompts, f"{emotion} missing support"
            assert len(prompts["support"]) > 0, f"{emotion} has no support messages"

    def test_frustrated_support_is_empathetic(self):
        """Frustrated support should be empathetic."""
        prompts = EMOTIONAL_SUPPORT_PROMPTS.get("frustrated", {})

        assert "normal" in prompts.get("recognition", "").lower()
        assert len(prompts.get("support", [])) > 0


class TestErrorExplanationPrompts:
    """
    Tests for programming error explanations.

    BUSINESS CONTEXT:
    Verifies helpful explanations exist for common error types.
    """

    def test_common_errors_covered(self):
        """Common Python errors should have explanations."""
        expected_errors = [
            "syntax_error", "name_error", "type_error",
            "index_error", "key_error", "attribute_error", "value_error"
        ]

        for error in expected_errors:
            assert error in ERROR_EXPLANATION_PROMPTS, \
                f"Missing explanation for: {error}"

    def test_error_explanation_has_required_keys(self):
        """Each error should have explanation, causes, and teaching moment."""
        for error, prompts in ERROR_EXPLANATION_PROMPTS.items():
            assert "explanation" in prompts, f"{error} missing explanation"
            assert "common_causes" in prompts, f"{error} missing common_causes"
            assert "teaching_moment" in prompts, f"{error} missing teaching_moment"

    def test_syntax_error_explanation_is_helpful(self):
        """Syntax error explanation should be student-friendly."""
        prompts = ERROR_EXPLANATION_PROMPTS.get("syntax_error", {})

        assert "typo" in prompts.get("explanation", "").lower()
        assert len(prompts.get("common_causes", [])) >= 3


class TestGetStudentPromptFunction:
    """
    Tests for get_student_prompt() function.

    BUSINESS CONTEXT:
    Verifies the prompt generation function works correctly.
    """

    def test_returns_string(self):
        """Should return a string."""
        result = get_student_prompt(
            StudentInteractionContext.COURSE_CONTENT,
            StudentSkillLevel.BEGINNER
        )
        assert isinstance(result, str)

    def test_includes_base_prompt_by_default(self):
        """Should include base system prompt by default."""
        result = get_student_prompt(
            StudentInteractionContext.COURSE_CONTENT,
            StudentSkillLevel.BEGINNER
        )
        assert "CORE IDENTITY" in result

    def test_can_exclude_base_prompt(self):
        """Should be able to exclude base system prompt."""
        result = get_student_prompt(
            StudentInteractionContext.COURSE_CONTENT,
            StudentSkillLevel.BEGINNER,
            include_base=False
        )
        assert "CORE IDENTITY" not in result

    def test_includes_context_specific_prompt(self):
        """Should include context-specific prompt."""
        result = get_student_prompt(
            StudentInteractionContext.QUIZ_HELP,
            StudentSkillLevel.INTERMEDIATE
        )
        assert "CURRENT CONTEXT" in result

    def test_includes_skill_level_prompt(self):
        """Should include skill level prompt."""
        result = get_student_prompt(
            StudentInteractionContext.LAB_PROGRAMMING,
            StudentSkillLevel.ADVANCED
        )
        assert "STUDENT LEVEL" in result

    def test_different_contexts_produce_different_prompts(self):
        """Different contexts should produce different prompts."""
        quiz_prompt = get_student_prompt(
            StudentInteractionContext.QUIZ_HELP,
            StudentSkillLevel.INTERMEDIATE
        )
        lab_prompt = get_student_prompt(
            StudentInteractionContext.LAB_PROGRAMMING,
            StudentSkillLevel.INTERMEDIATE
        )
        assert quiz_prompt != lab_prompt


class TestGetQuizHintFunction:
    """
    Tests for get_quiz_hint() function.

    BUSINESS CONTEXT:
    Verifies quiz hints are generated appropriately.
    """

    def test_returns_string(self):
        """Should return a string."""
        result = get_quiz_hint("Python", "variables", hint_level=1)
        assert isinstance(result, str)

    def test_hint_level_is_bounded(self):
        """Should handle hint levels beyond 4."""
        # Should not crash with high hint level
        result = get_quiz_hint("Python", "loops", hint_level=10)
        assert isinstance(result, str)


class TestGetEmotionalSupportFunction:
    """
    Tests for get_emotional_support() function.

    BUSINESS CONTEXT:
    Verifies emotional support is retrieved correctly.
    """

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_emotional_support("frustrated")
        assert isinstance(result, dict)

    def test_returns_required_keys(self):
        """Should return recognition, validation, and support."""
        result = get_emotional_support("confused")

        assert "recognition" in result
        assert "validation" in result
        assert "support" in result

    def test_handles_unknown_emotion(self):
        """Should handle unknown emotions gracefully."""
        result = get_emotional_support("unknown_emotion")

        assert "recognition" in result
        assert "validation" in result
        assert "support" in result


class TestGetErrorExplanationFunction:
    """
    Tests for get_error_explanation() function.

    BUSINESS CONTEXT:
    Verifies error explanations are retrieved correctly.
    """

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_error_explanation("syntax_error")
        assert isinstance(result, dict)

    def test_returns_required_keys(self):
        """Should return explanation, common_causes, and teaching_moment."""
        result = get_error_explanation("name_error")

        assert "explanation" in result
        assert "common_causes" in result
        assert "teaching_moment" in result

    def test_handles_unknown_error(self):
        """Should handle unknown error types gracefully."""
        result = get_error_explanation("unknown_weird_error")

        assert "explanation" in result
        assert "common_causes" in result


class TestGetEncouragementForLevelFunction:
    """
    Tests for get_encouragement_for_level() function.

    BUSINESS CONTEXT:
    Verifies encouragement retrieval works correctly.
    """

    def test_returns_list(self):
        """Should return a list."""
        result = get_encouragement_for_level(StudentSkillLevel.BEGINNER)
        assert isinstance(result, list)

    def test_returns_non_empty_list(self):
        """Should return non-empty list for all levels."""
        for level in StudentSkillLevel:
            result = get_encouragement_for_level(level)
            assert len(result) > 0


class TestBuildContextualPromptFunction:
    """
    Tests for build_contextual_prompt() function.

    BUSINESS CONTEXT:
    Verifies comprehensive prompt building works correctly.
    """

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = build_contextual_prompt(
            StudentInteractionContext.COURSE_CONTENT,
            StudentSkillLevel.INTERMEDIATE
        )
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Should have all required keys."""
        result = build_contextual_prompt(
            StudentInteractionContext.LAB_PROGRAMMING,
            StudentSkillLevel.BEGINNER
        )

        assert "system_prompt" in result
        assert "context" in result
        assert "skill_level" in result
        assert "suggested_responses" in result
        assert "encouragement" in result
        assert "metadata" in result

    def test_includes_student_name_when_provided(self):
        """Should include student name in prompt."""
        result = build_contextual_prompt(
            StudentInteractionContext.COURSE_CONTENT,
            StudentSkillLevel.INTERMEDIATE,
            student_name="Alex"
        )

        assert "Alex" in result["system_prompt"]
        assert result["metadata"]["student_name"] == "Alex"

    def test_includes_topic_when_provided(self):
        """Should include topic in prompt."""
        result = build_contextual_prompt(
            StudentInteractionContext.CONCEPT_CLARIFICATION,
            StudentSkillLevel.ADVANCED,
            topic="Machine Learning"
        )

        assert "Machine Learning" in result["system_prompt"]

    def test_includes_progress_when_provided(self):
        """Should include progress information."""
        progress = {"modules_completed": 5, "total_modules": 10}
        result = build_contextual_prompt(
            StudentInteractionContext.PROGRESS_REVIEW,
            StudentSkillLevel.INTERMEDIATE,
            course_progress=progress
        )

        assert "50%" in result["system_prompt"]
        assert "5/10" in result["system_prompt"]

    def test_limits_suggested_responses(self):
        """Should limit suggested responses to 5."""
        result = build_contextual_prompt(
            StudentInteractionContext.STUDY_PLANNING,
            StudentSkillLevel.BEGINNER
        )

        assert len(result["suggested_responses"]) <= 5


class TestEnumerations:
    """
    Tests for enumeration values.

    BUSINESS CONTEXT:
    Verifies enums have expected values.
    """

    def test_student_interaction_context_values(self):
        """StudentInteractionContext should have expected values."""
        expected = [
            "course_content", "quiz_help", "lab_programming",
            "assignment_help", "concept_clarification", "study_planning",
            "progress_review", "general_learning", "onboarding"
        ]

        actual = [ctx.value for ctx in StudentInteractionContext]

        for expected_value in expected:
            assert expected_value in actual

    def test_student_skill_level_values(self):
        """StudentSkillLevel should have expected values."""
        assert StudentSkillLevel.BEGINNER.value == "beginner"
        assert StudentSkillLevel.INTERMEDIATE.value == "intermediate"
        assert StudentSkillLevel.ADVANCED.value == "advanced"

    def test_assistance_intensity_values(self):
        """AssistanceIntensity should have expected values."""
        expected = ["hint_only", "guided", "detailed", "full_explanation"]
        actual = [intensity.value for intensity in AssistanceIntensity]

        for expected_value in expected:
            assert expected_value in actual
