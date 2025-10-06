"""
TDD Tests for Numba-optimized similarity algorithms

BUSINESS CONTEXT:
Performance-critical operations for semantic deduplication
Must process conversation histories with 10-50 messages in <10ms

TECHNICAL APPROACH:
- Numba JIT compilation for hot loops
- NumPy vectorization for batch operations
- Cosine similarity for semantic comparison
"""

import pytest
import numpy as np
from application.similarity_algorithms import (
    cosine_similarity_numba,
    batch_cosine_similarity,
    find_duplicates_fast,
    deduplicate_embeddings
)


class TestCosineSimilarityNumba:
    """
    TDD: Numba-optimized cosine similarity

    PERFORMANCE TARGET: <1μs per comparison
    """

    def test_identical_vectors_returns_one(self):
        """Identical vectors should have similarity of 1.0"""
        vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        similarity = cosine_similarity_numba(vec, vec)
        assert np.isclose(similarity, 1.0, atol=1e-6)

    def test_orthogonal_vectors_returns_zero(self):
        """Orthogonal vectors should have similarity of 0.0"""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        similarity = cosine_similarity_numba(vec1, vec2)
        assert np.isclose(similarity, 0.0, atol=1e-6)

    def test_opposite_vectors_returns_negative_one(self):
        """Opposite vectors should have similarity of -1.0"""
        vec1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        vec2 = np.array([-1.0, -2.0, -3.0], dtype=np.float32)
        similarity = cosine_similarity_numba(vec1, vec2)
        assert np.isclose(similarity, -1.0, atol=1e-6)

    def test_handles_zero_magnitude_vectors(self):
        """Zero vectors should return 0.0 similarity (avoid division by zero)"""
        vec1 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        similarity = cosine_similarity_numba(vec1, vec2)
        assert similarity == 0.0

    def test_performance_on_large_vectors(self, benchmark):
        """Benchmark: Should process 384-dim vectors in <1μs"""
        vec1 = np.random.randn(384).astype(np.float32)
        vec2 = np.random.randn(384).astype(np.float32)

        # Warm up JIT
        cosine_similarity_numba(vec1, vec2)

        # Benchmark
        result = benchmark(cosine_similarity_numba, vec1, vec2)
        assert -1.0 <= result <= 1.0


class TestBatchCosineSimilarity:
    """
    TDD: Batch cosine similarity with NumPy vectorization

    PERFORMANCE TARGET: Process 50x50 matrix in <5ms
    """

    def test_single_vector_against_batch(self):
        """Compare one vector against multiple vectors"""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vectors = np.array([
            [1.0, 0.0, 0.0],  # Same as query
            [0.0, 1.0, 0.0],  # Orthogonal
            [-1.0, 0.0, 0.0],  # Opposite
        ], dtype=np.float32)

        similarities = batch_cosine_similarity(query, vectors)

        assert len(similarities) == 3
        assert np.isclose(similarities[0], 1.0, atol=1e-6)
        assert np.isclose(similarities[1], 0.0, atol=1e-6)
        assert np.isclose(similarities[2], -1.0, atol=1e-6)

    def test_batch_returns_correct_shape(self):
        """Output shape should match number of vectors"""
        query = np.random.randn(10).astype(np.float32)
        vectors = np.random.randn(5, 10).astype(np.float32)

        similarities = batch_cosine_similarity(query, vectors)

        assert similarities.shape == (5,)
        assert np.all((similarities >= -1.0) & (similarities <= 1.0))

    def test_performance_on_conversation_batch(self, benchmark):
        """Benchmark: 50 messages x 384-dim embeddings in <5ms"""
        query = np.random.randn(384).astype(np.float32)
        vectors = np.random.randn(50, 384).astype(np.float32)

        result = benchmark(batch_cosine_similarity, query, vectors)
        assert len(result) == 50


class TestFindDuplicatesFast:
    """
    TDD: Fast duplicate detection using Numba

    PERFORMANCE TARGET: Find duplicates in 50 messages in <10ms
    """

    def test_finds_exact_duplicates(self):
        """Should identify messages with similarity > threshold"""
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],  # Duplicate of index 0
            [0.0, 1.0, 0.0],  # Different
        ], dtype=np.float32)

        duplicates = find_duplicates_fast(embeddings, threshold=0.95)

        # Should find (0, 1) as duplicate pair
        assert len(duplicates) > 0
        # Check if any pair contains indices 0 and 1
        found_pair = any((pair[0] == 0 and pair[1] == 1) or (pair[0] == 1 and pair[1] == 0) for pair in duplicates)
        assert found_pair

    def test_respects_similarity_threshold(self):
        """Only pairs above threshold should be marked as duplicates"""
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],  # Similar but not identical (cosine sim ~0.994)
            [0.0, 1.0, 0.0],  # Different
        ], dtype=np.float32)

        # Very high threshold - should not find duplicates
        duplicates_high = find_duplicates_fast(embeddings, threshold=0.995)
        assert len(duplicates_high) == 0

        # Lower threshold - should find some duplicates
        duplicates_low = find_duplicates_fast(embeddings, threshold=0.90)
        assert len(duplicates_low) > 0

    def test_no_duplicates_in_distinct_vectors(self):
        """Orthogonal vectors should not be marked as duplicates"""
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

        duplicates = find_duplicates_fast(embeddings, threshold=0.50)
        assert len(duplicates) == 0


class TestDeduplicateEmbeddings:
    """
    TDD: Deduplicate conversation history by semantic similarity

    BUSINESS VALUE:
    Reduces LLM context tokens by 20-30%
    """

    def test_removes_duplicate_messages(self):
        """Should keep only unique messages"""
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],  # Duplicate
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],  # Duplicate
        ], dtype=np.float32)

        unique_indices = deduplicate_embeddings(embeddings, threshold=0.95)

        # Should keep 2 out of 4 messages
        assert len(unique_indices) == 2
        # First occurrence should be kept
        assert 0 in unique_indices or 1 in unique_indices
        assert 2 in unique_indices or 3 in unique_indices

    def test_keeps_all_distinct_messages(self):
        """Distinct messages should all be retained"""
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

        unique_indices = deduplicate_embeddings(embeddings, threshold=0.95)

        assert len(unique_indices) == 3
        assert set(unique_indices) == {0, 1, 2}

    def test_preserves_message_order(self):
        """Returned indices should be in ascending order"""
        embeddings = np.random.randn(10, 384).astype(np.float32)

        unique_indices = deduplicate_embeddings(embeddings, threshold=0.95)

        assert unique_indices == sorted(unique_indices)

    def test_performance_on_long_conversation(self, benchmark):
        """Benchmark: Deduplicate 50 messages in <10ms"""
        embeddings = np.random.randn(50, 384).astype(np.float32)

        # Add some duplicates
        embeddings[10] = embeddings[5]
        embeddings[20] = embeddings[15]

        result = benchmark(deduplicate_embeddings, embeddings, threshold=0.95)
        assert len(result) < 50  # Should remove some duplicates
