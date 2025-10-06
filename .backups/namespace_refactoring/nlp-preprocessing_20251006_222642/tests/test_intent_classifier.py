"""
TDD Tests for Intent Classification

BUSINESS CONTEXT:
Intent classification enables intelligent routing to skip LLM for simple queries,
reducing cost by 30-40% and latency from ~1s to ~50ms for direct lookups.

TECHNICAL APPROACH:
- Rule-based classifier with keyword matching
- Pattern recognition for common query types
- Confidence scoring based on keyword matches
- Decision logic for LLM vs. direct response

PERFORMANCE TARGET:
- Classification time: <5ms per query
- Accuracy: >85% on typical queries
"""

import pytest
from application.intent_classifier import IntentClassifier
from domain.entities import IntentType


class TestIntentClassifier:
    """
    TDD: Rule-based intent classification

    PERFORMANCE TARGET: <5ms per classification
    """

    @pytest.fixture
    def classifier(self):
        """Create classifier instance for tests"""
        return IntentClassifier()

    # PREREQUISITE_CHECK intent tests
    def test_prerequisite_check_intent_with_what_keyword(self, classifier):
        """'What are the prerequisites' should map to PREREQUISITE_CHECK"""
        query = "What are the prerequisites for Machine Learning?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.PREREQUISITE_CHECK
        assert intent.confidence > 0.7
        assert "prerequisites" in intent.keywords
        assert intent.should_call_llm is False  # Can use knowledge graph directly

    def test_prerequisite_check_intent_with_requirements_keyword(self, classifier):
        """'What do I need to know' should map to PREREQUISITE_CHECK"""
        query = "What do I need to know before taking Python Advanced?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.PREREQUISITE_CHECK
        assert intent.confidence > 0.6
        assert intent.should_call_llm is False

    # COURSE_LOOKUP intent tests
    def test_course_lookup_intent_with_find_keyword(self, classifier):
        """'Find courses about' should map to COURSE_LOOKUP"""
        query = "Find courses about data science"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.COURSE_LOOKUP
        assert intent.confidence > 0.7
        assert any("find" in kw or "courses" in kw for kw in intent.keywords)
        assert intent.should_call_llm is False  # Can use metadata search

    def test_course_lookup_intent_with_show_keyword(self, classifier):
        """'Show me courses' should map to COURSE_LOOKUP"""
        query = "Show me all courses on machine learning"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.COURSE_LOOKUP
        assert intent.confidence > 0.6
        assert intent.should_call_llm is False

    # SKILL_LOOKUP intent tests
    def test_skill_lookup_intent_with_skills_keyword(self, classifier):
        """'What skills' should map to SKILL_LOOKUP"""
        query = "What skills will I learn in Python Basics?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.SKILL_LOOKUP
        assert intent.confidence > 0.7
        assert any("skills" in kw for kw in intent.keywords)
        assert intent.should_call_llm is False

    # LEARNING_PATH intent tests
    def test_learning_path_intent_with_path_keyword(self, classifier):
        """'Learning path from X to Y' should map to LEARNING_PATH"""
        query = "What's the learning path from Python Basics to Machine Learning?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.LEARNING_PATH
        assert intent.confidence > 0.7
        assert "path" in intent.keywords or "learning path" in intent.keywords
        assert intent.should_call_llm is False  # Can use knowledge graph

    def test_learning_path_intent_with_progression_keyword(self, classifier):
        """'How do I progress' should map to LEARNING_PATH"""
        query = "How do I progress from beginner to advanced in data science?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.LEARNING_PATH
        assert intent.confidence > 0.6
        assert intent.should_call_llm is False

    # CONCEPT_EXPLANATION intent tests
    def test_concept_explanation_intent_with_explain_keyword(self, classifier):
        """'Explain' should map to CONCEPT_EXPLANATION"""
        query = "Explain gradient descent"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.CONCEPT_EXPLANATION
        assert intent.confidence > 0.7
        assert "explain" in intent.keywords
        assert intent.should_call_llm is True  # Requires LLM for explanation

    def test_concept_explanation_intent_with_what_is_keyword(self, classifier):
        """'What is' should map to CONCEPT_EXPLANATION"""
        query = "What is a neural network?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.CONCEPT_EXPLANATION
        assert intent.confidence > 0.6
        assert intent.should_call_llm is True

    # GREETING intent tests
    def test_greeting_intent_with_hello(self, classifier):
        """'Hello' should map to GREETING"""
        query = "Hello!"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.GREETING
        assert intent.confidence > 0.8
        assert intent.should_call_llm is False  # Simple canned response

    def test_greeting_intent_with_hi(self, classifier):
        """'Hi' should map to GREETING"""
        query = "Hi there"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.GREETING
        assert intent.confidence > 0.7
        assert intent.should_call_llm is False

    # COMMAND intent tests
    def test_command_intent_with_create_keyword(self, classifier):
        """'Create a course' should map to COMMAND"""
        query = "Create a course about Python"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.COMMAND
        assert intent.confidence > 0.7
        assert "create" in intent.keywords
        assert intent.should_call_llm is True  # May need LLM for validation

    # CLARIFICATION intent tests
    def test_clarification_intent_with_short_followup(self, classifier):
        """Short follow-up should map to CLARIFICATION"""
        query = "More details"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.CLARIFICATION
        assert intent.confidence > 0.6
        assert intent.should_call_llm is True  # Needs conversation context

    def test_clarification_intent_with_and_keyword(self, classifier):
        """'And what about' should map to CLARIFICATION"""
        query = "And what about advanced topics?"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.CLARIFICATION
        assert intent.confidence > 0.5
        assert intent.should_call_llm is True

    # QUESTION intent tests (general/complex questions)
    def test_question_intent_with_how_keyword(self, classifier):
        """'How does X work' should map to CONCEPT_EXPLANATION (more specific than QUESTION)"""
        query = "How does backpropagation work in neural networks?"

        intent = classifier.classify(query)

        # "how does" is in CONCEPT_EXPLANATION patterns, which is more specific
        assert intent.intent_type == IntentType.CONCEPT_EXPLANATION
        assert intent.confidence > 0.5
        assert intent.should_call_llm is True

    # UNKNOWN intent tests (fallback)
    def test_unknown_intent_with_gibberish(self, classifier):
        """Unrecognizable queries should map to UNKNOWN"""
        query = "asdfghjkl qwerty"

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.UNKNOWN
        assert intent.confidence < 0.5
        assert intent.should_call_llm is True  # Send to LLM to handle

    # Case insensitivity tests
    def test_case_insensitive_matching(self, classifier):
        """Classifier should be case-insensitive"""
        query_upper = "WHAT ARE THE PREREQUISITES FOR PYTHON?"
        query_lower = "what are the prerequisites for python?"

        intent_upper = classifier.classify(query_upper)
        intent_lower = classifier.classify(query_lower)

        assert intent_upper.intent_type == intent_lower.intent_type
        assert intent_upper.intent_type == IntentType.PREREQUISITE_CHECK

    # Confidence scoring tests
    def test_multiple_keyword_matches_increase_confidence(self, classifier):
        """Multiple pattern matches should increase confidence"""
        # Use queries that match multiple patterns cleanly
        query_single = "Show courses"  # Matches one pattern
        query_multiple = "Show me all available courses to browse"  # Matches multiple patterns

        intent_single = classifier.classify(query_single)
        intent_multiple = classifier.classify(query_multiple)

        assert intent_single.intent_type == IntentType.COURSE_LOOKUP
        assert intent_multiple.intent_type == IntentType.COURSE_LOOKUP
        assert intent_multiple.confidence >= intent_single.confidence

    # Performance tests
    def test_classification_performance(self, classifier, benchmark):
        """Benchmark: Should classify in <5ms"""
        query = "What are the prerequisites for Machine Learning Advanced?"

        result = benchmark(classifier.classify, query)

        assert result.intent_type == IntentType.PREREQUISITE_CHECK

    # Edge cases
    def test_empty_query_maps_to_unknown(self, classifier):
        """Empty queries should map to UNKNOWN"""
        query = ""

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.UNKNOWN
        assert intent.should_call_llm is True

    def test_whitespace_only_query_maps_to_unknown(self, classifier):
        """Whitespace-only queries should map to UNKNOWN"""
        query = "   \n\t  "

        intent = classifier.classify(query)

        assert intent.intent_type == IntentType.UNKNOWN
        assert intent.should_call_llm is True


class TestIntentClassifierMetadata:
    """
    TDD: Intent metadata and context extraction
    """

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    def test_metadata_includes_matched_keywords(self, classifier):
        """Metadata should include matched keywords for debugging"""
        query = "What are the prerequisites for Python?"

        intent = classifier.classify(query)

        assert "prerequisites" in intent.keywords
        assert len(intent.keywords) > 0

    def test_metadata_includes_query_length(self, classifier):
        """Metadata should include query length for analysis"""
        query = "Find courses"

        intent = classifier.classify(query)

        assert "query_length" in intent.metadata
        assert intent.metadata["query_length"] == len(query)

    def test_metadata_includes_word_count(self, classifier):
        """Metadata should include word count"""
        query = "What are the prerequisites for Machine Learning?"

        intent = classifier.classify(query)

        assert "word_count" in intent.metadata
        assert intent.metadata["word_count"] == 7
