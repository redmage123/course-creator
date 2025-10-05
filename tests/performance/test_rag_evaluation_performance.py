"""
Performance Benchmark Tests for RAG Evaluation Module

BUSINESS REQUIREMENT:
Measure baseline performance before numba optimization to validate
expected 20-50x speedup after implementation.

TEST STRATEGY:
1. Benchmark current Python implementation
2. Run same tests after numba optimization
3. Validate speedup meets 10x minimum threshold
4. Ensure behavioral equivalence (same results)
"""

import pytest
import time
import numpy as np
from typing import List, Tuple
import sys
from pathlib import Path

# Add rag-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'rag-service'))

from rag_evaluation import RAGEvaluator, RAGTestCase, RAGEvaluationResult


@pytest.fixture
def evaluator():
    """Create RAG evaluator instance"""
    return RAGEvaluator()


@pytest.fixture
def sample_texts():
    """Generate sample texts for benchmarking"""
    return {
        'short': "This is a short test sentence for evaluation.",
        'medium': " ".join(["This is a medium length sentence."] * 20),
        'long': " ".join(["This is a long test sentence with many words."] * 100),
        'very_long': " ".join(["Performance testing requires longer text samples."] * 500)
    }


@pytest.fixture
def sample_text_pairs():
    """Generate pairs of texts for similarity testing"""
    return [
        ("Python is a programming language", "Python is used for programming"),
        ("Machine learning models", "Deep learning neural networks"),
        ("Database queries are fast", "SQL databases handle queries efficiently"),
        ("Web development with frameworks", "Building web applications using modern frameworks"),
        ("Cloud computing infrastructure", "Scalable cloud-based systems")
    ]


class TestTextSimilarityPerformance:
    """
    Test performance of text similarity calculation

    CRITICAL PATH: This function is called in:
    - Context precision calculation (N*M comparisons)
    - Context recall calculation (N*M comparisons)
    - Answer similarity calculation

    For 10 contexts vs 10 ground truth = 100 comparisons per test case
    """

    def test_similarity_single_pair_baseline(self, evaluator, sample_texts, benchmark):
        """Benchmark single text similarity calculation"""
        text1 = sample_texts['medium']
        text2 = sample_texts['medium']

        result = benchmark(evaluator._simple_text_similarity, text1, text2)

        assert 0.0 <= result <= 1.0
        print(f"\n  Baseline single similarity: {benchmark.stats['mean']:.6f}s")

    def test_similarity_many_pairs_baseline(self, evaluator, sample_text_pairs, benchmark):
        """Benchmark many similarity calculations (realistic workload)"""

        def calculate_all_similarities():
            results = []
            for text1, text2 in sample_text_pairs:
                results.append(evaluator._simple_text_similarity(text1, text2))
            return results

        results = benchmark(calculate_all_similarities)

        assert len(results) == len(sample_text_pairs)
        assert all(0.0 <= r <= 1.0 for r in results)
        print(f"\n  Baseline {len(sample_text_pairs)} similarities: {benchmark.stats['mean']:.6f}s")

    def test_similarity_large_batch_baseline(self, evaluator, benchmark):
        """Benchmark large batch of similarity calculations (stress test)"""
        # Simulate context precision calculation: 10 retrieved vs 10 ground truth = 100 comparisons
        num_contexts = 10
        contexts = [
            f"Context document number {i} with relevant information about the topic"
            for i in range(num_contexts)
        ]
        ground_truth = [
            f"Ground truth context {i} describing the expected relevant content"
            for i in range(num_contexts)
        ]

        def calculate_context_similarities():
            results = []
            for retrieved in contexts:
                for truth in ground_truth:
                    results.append(evaluator._simple_text_similarity(retrieved, truth))
            return results

        results = benchmark(calculate_context_similarities)

        assert len(results) == num_contexts * num_contexts
        print(f"\n  Baseline {len(results)} comparisons: {benchmark.stats['mean']:.6f}s")


class TestFaithfulnessPerformance:
    """
    Test performance of faithfulness calculation

    CRITICAL PATH: Called once per test case
    - Splits answer into sentences
    - For each sentence, calculates word overlap with all contexts
    - Many set operations on word lists
    """

    @pytest.mark.asyncio
    async def test_faithfulness_short_answer_baseline(self, evaluator, benchmark):
        """Benchmark faithfulness with short answer"""
        answer = "Python is great. It has many libraries. Perfect for data science."
        contexts = [
            "Python is a powerful programming language with extensive libraries.",
            "Data science applications benefit from Python's ecosystem.",
            "Many developers choose Python for its simplicity."
        ]

        result = await benchmark.pedantic(
            evaluator._calculate_faithfulness,
            args=(answer, contexts),
            rounds=10
        )

        assert 0.0 <= result <= 1.0
        print(f"\n  Baseline short faithfulness: {benchmark.stats['mean']:.6f}s")

    @pytest.mark.asyncio
    async def test_faithfulness_long_answer_baseline(self, evaluator, benchmark):
        """Benchmark faithfulness with long answer (realistic)"""
        # Realistic answer: 10 sentences
        sentences = [
            "Machine learning is a subset of artificial intelligence.",
            "It focuses on training algorithms to learn from data.",
            "Common applications include image recognition and natural language processing.",
            "Deep learning uses neural networks with multiple layers.",
            "Training requires large datasets and computational resources.",
            "Popular frameworks include TensorFlow and PyTorch.",
            "Model evaluation uses metrics like accuracy and F1 score.",
            "Overfitting occurs when models memorize training data.",
            "Regularization techniques help prevent overfitting.",
            "Cross-validation ensures models generalize well."
        ]
        answer = " ".join(sentences)

        contexts = [
            "Artificial intelligence encompasses machine learning and deep learning.",
            "Neural networks are the foundation of deep learning systems.",
            "TensorFlow and PyTorch are widely used frameworks for model development.",
            "Evaluation metrics assess model performance on test data.",
            "Overfitting and regularization are key concepts in model training."
        ]

        result = await benchmark.pedantic(
            evaluator._calculate_faithfulness,
            args=(answer, contexts),
            rounds=10
        )

        assert 0.0 <= result <= 1.0
        print(f"\n  Baseline long faithfulness: {benchmark.stats['mean']:.6f}s")


class TestAggregatedMetricsPerformance:
    """
    Test performance of aggregated metrics calculation

    CRITICAL PATH: Called once per test suite
    - Calculates mean, median, std for multiple metrics
    - Percentile calculations for latency
    - Pass rate calculations
    """

    def test_aggregate_small_batch_baseline(self, evaluator, benchmark):
        """Benchmark aggregation with small result set (10 results)"""
        results = self._create_mock_results(10)

        aggregated = benchmark(evaluator._calculate_aggregated_metrics, results)

        assert aggregated.num_test_cases == 10
        assert 0.0 <= aggregated.overall_quality_score <= 1.0
        print(f"\n  Baseline 10 results aggregation: {benchmark.stats['mean']:.6f}s")

    def test_aggregate_medium_batch_baseline(self, evaluator, benchmark):
        """Benchmark aggregation with medium result set (100 results)"""
        results = self._create_mock_results(100)

        aggregated = benchmark(evaluator._calculate_aggregated_metrics, results)

        assert aggregated.num_test_cases == 100
        print(f"\n  Baseline 100 results aggregation: {benchmark.stats['mean']:.6f}s")

    def test_aggregate_large_batch_baseline(self, evaluator, benchmark):
        """Benchmark aggregation with large result set (1000 results)"""
        results = self._create_mock_results(1000)

        aggregated = benchmark(evaluator._calculate_aggregated_metrics, results)

        assert aggregated.num_test_cases == 1000
        print(f"\n  Baseline 1000 results aggregation: {benchmark.stats['mean']:.6f}s")

    def _create_mock_results(self, count: int) -> List[RAGEvaluationResult]:
        """Create mock evaluation results for testing"""
        results = []
        for i in range(count):
            test_case = RAGTestCase(
                question=f"Test question {i}",
                ground_truth=f"Test answer {i}",
                contexts=[f"Context {i}"]
            )

            result = RAGEvaluationResult(
                test_case=test_case,
                retrieved_contexts=[f"Retrieved context {i}"],
                generated_answer=f"Generated answer {i}",
                faithfulness=np.random.random(),
                answer_relevancy=np.random.random(),
                context_precision=np.random.random(),
                context_recall=np.random.random(),
                latency_ms=np.random.uniform(50, 500)
            )
            results.append(result)

        return results


class TestEndToEndPerformance:
    """
    End-to-end performance tests

    BUSINESS VALUE: Measure total time for complete evaluation workflow
    """

    @pytest.mark.asyncio
    async def test_complete_evaluation_baseline(self, evaluator, benchmark):
        """Benchmark complete evaluation of single test case"""
        # This would require full RAG system - skipping for now
        # Will add once numba optimization is complete
        pass


@pytest.mark.performance
class TestPerformanceTargets:
    """
    Performance target validation

    ACCEPTANCE CRITERIA:
    - After numba optimization, should achieve 10x+ speedup minimum
    - Target: 20-50x speedup for critical paths
    """

    def test_similarity_performance_target(self, evaluator, benchmark):
        """
        Current baseline will be compared to numba version
        Target: < 1ms for 100 similarity calculations
        """
        contexts = [f"Context {i}" for i in range(10)]
        ground_truth = [f"Truth {i}" for i in range(10)]

        def calculate_all():
            results = []
            for c in contexts:
                for g in ground_truth:
                    results.append(evaluator._simple_text_similarity(c, g))
            return results

        results = benchmark(calculate_all)
        assert len(results) == 100

        # Document baseline for comparison
        baseline_time = benchmark.stats['mean']
        print(f"\n  Baseline time for 100 comparisons: {baseline_time*1000:.3f}ms")
        print(f"  Target after numba: < {baseline_time*1000/10:.3f}ms (10x speedup)")
        print(f"  Stretch target: < {baseline_time*1000/20:.3f}ms (20x speedup)")


# Performance test configuration
@pytest.fixture
def benchmark(benchmark):
    """Configure benchmark settings"""
    benchmark.pedantic(rounds=10, iterations=5, warmup_rounds=2)
    return benchmark
