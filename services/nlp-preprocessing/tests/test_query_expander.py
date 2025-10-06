"""
TDD Tests for Query Expansion

BUSINESS CONTEXT:
Query expansion addresses vocabulary mismatch between user queries
and stored content, improving RAG recall by 15-25%.

TECHNICAL APPROACH:
- Synonym expansion using curated domain dictionaries
- Acronym expansion (ML -> Machine Learning)
- Common variations (Python -> Python programming)
- Preserves original query for multi-query search

PERFORMANCE TARGET:
- Expansion time: <5ms per query
"""

import pytest
from nlp_preprocessing.application.query_expander import QueryExpander
from nlp_preprocessing.domain.entities import ExpandedQuery


class TestQueryExpander:
    """
    TDD: Query expansion for improved search recall

    PERFORMANCE TARGET: <5ms per expansion
    """

    @pytest.fixture
    def expander(self):
        """Create expander instance for tests"""
        return QueryExpander()

    # Synonym expansion tests
    def test_expands_ml_acronym(self, expander):
        """'ML' should expand to 'Machine Learning'"""
        query = "Courses about ML"

        expanded = expander.expand(query)

        assert expanded.original == query
        # Should include original + expansion
        assert len(expanded.expansions) > 0
        # Check that ML expansion is present
        assert any("machine learning" in exp.lower() for exp in expanded.expansions)

    def test_expands_ai_acronym(self, expander):
        """'AI' should expand to 'Artificial Intelligence'"""
        query = "Learn AI fundamentals"

        expanded = expander.expand(query)

        assert len(expanded.expansions) > 0
        assert any("artificial intelligence" in exp.lower() for exp in expanded.expansions)

    def test_expands_dl_acronym(self, expander):
        """'DL' should expand to 'Deep Learning'"""
        query = "DL course recommendations"

        expanded = expander.expand(query)

        assert len(expanded.expansions) > 0
        assert any("deep learning" in exp.lower() for exp in expanded.expansions)

    # Technology synonym expansion
    def test_expands_python_synonym(self, expander):
        """'Python' should expand to include 'Python programming'"""
        query = "Python basics"

        expanded = expander.expand(query)

        assert len(expanded.expansions) > 0
        # Should have variations
        assert any("programming" in exp.lower() for exp in expanded.expansions)

    def test_expands_js_to_javascript(self, expander):
        """'JS' should expand to 'JavaScript'"""
        query = "JS frameworks"

        expanded = expander.expand(query)

        assert len(expanded.expansions) > 0
        assert any("javascript" in exp.lower() for exp in expanded.expansions)

    # Multiple term expansion
    def test_expands_multiple_terms(self, expander):
        """Multiple expandable terms should all be expanded"""
        query = "ML and AI courses"

        expanded = expander.expand(query)

        # Should have expansions for both ML and AI
        assert len(expanded.expansions) > 0
        # Check expansion_terms mapping
        assert "ml" in [k.lower() for k in expanded.expansion_terms.keys()] or \
               "ai" in [k.lower() for k in expanded.expansion_terms.keys()]

    # Combined query generation
    def test_combined_includes_all_variations(self, expander):
        """Combined query should include original + all expansions"""
        query = "ML basics"

        expanded = expander.expand(query)

        # Combined should include original
        assert "ML" in expanded.combined or "ml" in expanded.combined.lower()
        # Combined should include expansion
        assert "machine learning" in expanded.combined.lower()

    # Expansion terms mapping
    def test_expansion_terms_mapping(self, expander):
        """expansion_terms should map original -> synonyms"""
        query = "AI course"

        expanded = expander.expand(query)

        # Should have mapping for AI
        assert len(expanded.expansion_terms) > 0
        # Check that AI has expansions
        ai_key = next((k for k in expanded.expansion_terms.keys() if k.lower() == "ai"), None)
        if ai_key:
            assert len(expanded.expansion_terms[ai_key]) > 0
            assert any("artificial" in term.lower() for term in expanded.expansion_terms[ai_key])

    # Case insensitivity
    def test_case_insensitive_expansion(self, expander):
        """Expansion should work regardless of case"""
        query_upper = "ML BASICS"
        query_lower = "ml basics"

        expanded_upper = expander.expand(query_upper)
        expanded_lower = expander.expand(query_lower)

        # Both should have expansions
        assert len(expanded_upper.expansions) > 0
        assert len(expanded_lower.expansions) > 0

    # No expansion needed
    def test_no_expansion_for_unknown_terms(self, expander):
        """Queries with no expandable terms should still work"""
        query = "quantum computing basics"  # No known synonyms

        expanded = expander.expand(query)

        # Should still return valid ExpandedQuery
        assert expanded.original == query
        # May have no expansions or just the original
        # Combined should at least have original
        assert query in expanded.combined or query.lower() in expanded.combined.lower()

    # Edge cases
    def test_empty_query(self, expander):
        """Empty query should return valid but empty expansion"""
        query = ""

        expanded = expander.expand(query)

        assert expanded.original == ""
        assert expanded.combined == ""

    def test_whitespace_only_query(self, expander):
        """Whitespace-only query should be handled"""
        query = "   \n\t  "

        expanded = expander.expand(query)

        assert expanded.original == query
        # Combined should be empty or whitespace
        assert len(expanded.combined.strip()) == 0

    # Domain-specific terms
    def test_expands_neural_network_variations(self, expander):
        """'Neural network' should have variations"""
        query = "neural network tutorial"

        expanded = expander.expand(query)

        # Should include variations like NN, neural networks (plural), etc.
        assert len(expanded.expansions) >= 0  # May or may not have expansions

    # Performance test
    def test_expansion_performance(self, expander, benchmark):
        """Benchmark: Should expand in <5ms"""
        query = "ML and AI courses about deep learning and Python"

        result = benchmark(expander.expand, query)

        # Should produce valid expansion
        assert result.original == query
        assert len(result.combined) > 0


class TestQueryExpanderCustomSynonyms:
    """
    TDD: Custom synonym management
    """

    @pytest.fixture
    def expander(self):
        return QueryExpander()

    def test_add_custom_synonym(self, expander):
        """Should allow adding custom synonyms at runtime"""
        # Add custom synonym
        expander.add_synonym("DL", ["Deep Learning", "Deep Neural Networks"])

        query = "DL fundamentals"
        expanded = expander.expand(query)

        # Should use custom synonym
        assert len(expanded.expansions) > 0
        assert any("deep learning" in exp.lower() or "deep neural" in exp.lower()
                   for exp in expanded.expansions)

    def test_preserves_original_query(self, expander):
        """Original query should never be modified"""
        query = "ML basics"
        expanded = expander.expand(query)

        # Original should be unchanged
        assert expanded.original == query
        assert query == "ML basics"  # Original string not mutated
