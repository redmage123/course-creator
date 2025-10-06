"""
TDD Tests for Entity Extraction

BUSINESS CONTEXT:
Entity extraction enables targeted searches and reduces hallucination
by identifying specific courses, topics, skills, concepts from queries.

TECHNICAL APPROACH:
- Regex-based pattern matching for structured entities
- Integration with metadata service for entity validation
- Confidence scoring based on match quality
- Support for multiple entity types (COURSE, TOPIC, SKILL, CONCEPT, etc.)

PERFORMANCE TARGET:
- Extraction time: <10ms per query
- Accuracy: >80% on typical queries
"""

import pytest
from application.entity_extractor import EntityExtractor
from domain.entities import EntityType


class TestEntityExtractor:
    """
    TDD: Regex-based entity extraction

    PERFORMANCE TARGET: <10ms per extraction
    """

    @pytest.fixture
    def extractor(self):
        """Create extractor instance for tests"""
        return EntityExtractor()

    # COURSE entity extraction tests
    def test_extracts_course_name_with_quotes(self, extractor):
        """Course names in quotes should be extracted"""
        query = "Tell me about 'Python Basics' course"

        entities = extractor.extract(query)

        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        assert len(course_entities) > 0
        assert course_entities[0].text == "Python Basics"
        assert course_entities[0].confidence > 0.7

    def test_extracts_course_name_with_double_quotes(self, extractor):
        """Course names in double quotes should be extracted"""
        query = 'What are the prerequisites for "Machine Learning Advanced"?'

        entities = extractor.extract(query)

        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        assert len(course_entities) > 0
        assert course_entities[0].text == "Machine Learning Advanced"
        assert course_entities[0].confidence > 0.7

    def test_extracts_multiple_course_names(self, extractor):
        """Multiple course names should be extracted"""
        query = "Is 'Python Basics' easier than 'Python Advanced'?"

        entities = extractor.extract(query)

        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        assert len(course_entities) == 2
        course_texts = [e.text for e in course_entities]
        assert "Python Basics" in course_texts
        assert "Python Advanced" in course_texts

    def test_extracts_course_with_course_keyword(self, extractor):
        """'X course' pattern should extract course name"""
        query = "Show me the Python Basics course"

        entities = extractor.extract(query)

        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        assert len(course_entities) > 0
        assert "Python Basics" in course_entities[0].text

    # TOPIC entity extraction tests
    def test_extracts_topic_with_about_keyword(self, extractor):
        """'about X' pattern should extract topic"""
        query = "Find courses about machine learning"

        entities = extractor.extract(query)

        topic_entities = [e for e in entities if e.entity_type == EntityType.TOPIC]
        assert len(topic_entities) > 0
        assert topic_entities[0].text == "machine learning"
        assert topic_entities[0].confidence > 0.6

    def test_extracts_topic_with_on_keyword(self, extractor):
        """'on X' pattern should extract topic"""
        query = "Are there courses on data science?"

        entities = extractor.extract(query)

        topic_entities = [e for e in entities if e.entity_type == EntityType.TOPIC]
        assert len(topic_entities) > 0
        assert topic_entities[0].text == "data science"

    def test_extracts_topic_with_related_to_keyword(self, extractor):
        """'related to X' pattern should extract topic"""
        query = "Courses related to artificial intelligence"

        entities = extractor.extract(query)

        topic_entities = [e for e in entities if e.entity_type == EntityType.TOPIC]
        assert len(topic_entities) > 0
        assert "artificial intelligence" in topic_entities[0].text

    # SKILL entity extraction tests
    def test_extracts_skill_with_learn_keyword(self, extractor):
        """'learn X' pattern should extract skill"""
        query = "I want to learn Python programming"

        entities = extractor.extract(query)

        skill_entities = [e for e in entities if e.entity_type == EntityType.SKILL]
        assert len(skill_entities) > 0
        assert "Python" in skill_entities[0].text or "programming" in skill_entities[0].text

    def test_extracts_skill_with_skills_keyword(self, extractor):
        """'skills in X' pattern should extract skill"""
        query = "What skills in data analysis will I gain?"

        entities = extractor.extract(query)

        skill_entities = [e for e in entities if e.entity_type == EntityType.SKILL]
        assert len(skill_entities) > 0
        assert "data analysis" in skill_entities[0].text

    # CONCEPT entity extraction tests
    def test_extracts_concept_with_explain_keyword(self, extractor):
        """'explain X' pattern should extract concept"""
        query = "Can you explain gradient descent?"

        entities = extractor.extract(query)

        concept_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
        assert len(concept_entities) > 0
        assert concept_entities[0].text == "gradient descent"
        assert concept_entities[0].confidence > 0.6

    def test_extracts_concept_with_what_is_keyword(self, extractor):
        """'what is X' pattern should extract concept"""
        query = "What is a neural network?"

        entities = extractor.extract(query)

        concept_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
        assert len(concept_entities) > 0
        assert "neural network" in concept_entities[0].text

    # DIFFICULTY entity extraction tests
    def test_extracts_difficulty_beginner(self, extractor):
        """'beginner' keyword should be extracted as DIFFICULTY"""
        query = "Show me beginner level courses"

        entities = extractor.extract(query)

        difficulty_entities = [e for e in entities if e.entity_type == EntityType.DIFFICULTY]
        assert len(difficulty_entities) > 0
        assert difficulty_entities[0].text == "beginner"
        assert difficulty_entities[0].confidence > 0.8

    def test_extracts_difficulty_advanced(self, extractor):
        """'advanced' keyword should be extracted as DIFFICULTY"""
        query = "I need advanced Python courses"

        entities = extractor.extract(query)

        difficulty_entities = [e for e in entities if e.entity_type == EntityType.DIFFICULTY]
        assert len(difficulty_entities) > 0
        assert difficulty_entities[0].text == "advanced"

    def test_extracts_difficulty_intermediate(self, extractor):
        """'intermediate' keyword should be extracted as DIFFICULTY"""
        query = "Looking for intermediate data science"

        entities = extractor.extract(query)

        difficulty_entities = [e for e in entities if e.entity_type == EntityType.DIFFICULTY]
        assert len(difficulty_entities) > 0
        assert difficulty_entities[0].text == "intermediate"

    # DURATION entity extraction tests
    def test_extracts_duration_with_hours(self, extractor):
        """'X hours' pattern should extract duration"""
        query = "Find courses under 10 hours"

        entities = extractor.extract(query)

        duration_entities = [e for e in entities if e.entity_type == EntityType.DURATION]
        assert len(duration_entities) > 0
        assert "10 hours" in duration_entities[0].text

    def test_extracts_duration_with_weeks(self, extractor):
        """'X weeks' pattern should extract duration"""
        query = "Courses that take 4 weeks to complete"

        entities = extractor.extract(query)

        duration_entities = [e for e in entities if e.entity_type == EntityType.DURATION]
        assert len(duration_entities) > 0
        assert "4 weeks" in duration_entities[0].text

    # Confidence scoring tests
    def test_quoted_entities_have_higher_confidence(self, extractor):
        """Entities in quotes should have higher confidence than inferred ones"""
        query_quoted = "Tell me about 'Python Basics'"
        query_inferred = "Tell me about Python Basics course"

        entities_quoted = extractor.extract(query_quoted)
        entities_inferred = extractor.extract(query_inferred)

        course_quoted = [e for e in entities_quoted if e.entity_type == EntityType.COURSE][0]
        course_inferred = [e for e in entities_inferred if e.entity_type == EntityType.COURSE][0]

        assert course_quoted.confidence > course_inferred.confidence

    # Span tracking tests
    def test_entity_span_tracks_position(self, extractor):
        """Entity span should track character positions"""
        query = "What is gradient descent?"

        entities = extractor.extract(query)

        concept_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
        assert len(concept_entities) > 0

        entity = concept_entities[0]
        start, end = entity.span

        # Verify span matches actual text position
        extracted_text = query[start:end]
        assert entity.text in extracted_text or extracted_text in entity.text

    # Case insensitivity tests
    def test_case_insensitive_extraction(self, extractor):
        """Extraction should be case-insensitive"""
        query_upper = "EXPLAIN GRADIENT DESCENT"
        query_lower = "explain gradient descent"

        entities_upper = extractor.extract(query_upper)
        entities_lower = extractor.extract(query_lower)

        concepts_upper = [e for e in entities_upper if e.entity_type == EntityType.CONCEPT]
        concepts_lower = [e for e in entities_lower if e.entity_type == EntityType.CONCEPT]

        assert len(concepts_upper) > 0
        assert len(concepts_lower) > 0

    # Multiple entity types in one query
    def test_extracts_multiple_entity_types(self, extractor):
        """Should extract multiple entity types from same query"""
        query = "Find beginner courses about machine learning in 'Python Basics'"

        entities = extractor.extract(query)

        entity_types = {e.entity_type for e in entities}

        # Should find at least 2 different entity types
        assert len(entity_types) >= 2

    # Edge cases
    def test_empty_query_returns_empty_list(self, extractor):
        """Empty queries should return empty entity list"""
        query = ""

        entities = extractor.extract(query)

        assert entities == []

    def test_no_entities_in_query(self, extractor):
        """Queries without recognizable entities should return empty list"""
        query = "asdfghjkl qwerty"

        entities = extractor.extract(query)

        assert len(entities) == 0

    # Performance tests
    def test_extraction_performance(self, extractor, benchmark):
        """Benchmark: Should extract in <10ms"""
        query = "Find beginner courses about machine learning and data science in 'Python Basics' that take 10 hours"

        result = benchmark(extractor.extract, query)

        # Should extract multiple entities
        assert len(result) > 0


class TestEntityExtractorMetadata:
    """
    TDD: Entity metadata and context extraction
    """

    @pytest.fixture
    def extractor(self):
        return EntityExtractor()

    def test_metadata_includes_extraction_method(self, extractor):
        """Metadata should include how entity was extracted"""
        query = "Tell me about 'Python Basics'"

        entities = extractor.extract(query)

        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        assert len(course_entities) > 0

        entity = course_entities[0]
        assert "extraction_method" in entity.metadata
        assert entity.metadata["extraction_method"] in ["quoted", "pattern", "keyword"]

    def test_metadata_includes_pattern_matched(self, extractor):
        """Metadata should include which pattern matched"""
        query = "Find courses about machine learning"

        entities = extractor.extract(query)

        topic_entities = [e for e in entities if e.entity_type == EntityType.TOPIC]
        assert len(topic_entities) > 0

        entity = topic_entities[0]
        assert "pattern" in entity.metadata
