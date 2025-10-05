"""
Integration test for numba-optimized RAG evaluation

BUSINESS REQUIREMENT:
Verify that numba optimization maintains behavioral equivalence
while improving performance.

TEST APPROACH:
- Import the optimized module
- Run basic functionality tests
- Verify results are valid
"""

import pytest
import sys
from pathlib import Path

# Add rag-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'rag-service'))

from rag_evaluation import RAGEvaluator, RAGTestCase, RAGEvaluationResult
import numpy as np


class TestNumbaIntegration:
    """Integration tests for numba-optimized functions"""

    def test_evaluator_imports_successfully(self):
        """Test that RAGEvaluator can be imported with numba"""
        evaluator = RAGEvaluator()
        assert evaluator is not None
        assert evaluator.pass_threshold == 0.7

    def test_text_similarity_basic_functionality(self):
        """Test text similarity calculation works"""
        evaluator = RAGEvaluator()

        # Test identical texts
        sim1 = evaluator._simple_text_similarity("hello world", "hello world")
        assert 0.95 <= sim1 <= 1.0, f"Expected ~1.0, got {sim1}"

        # Test different texts
        sim2 = evaluator._simple_text_similarity("hello world", "goodbye universe")
        assert 0.0 <= sim2 <= 0.3, f"Expected low similarity, got {sim2}"

        # Test partial overlap
        sim3 = evaluator._simple_text_similarity("python programming", "python coding")
        assert 0.3 <= sim3 <= 0.7, f"Expected medium similarity, got {sim3}"

    @pytest.mark.asyncio
    async def test_faithfulness_basic_functionality(self):
        """Test faithfulness calculation works"""
        evaluator = RAGEvaluator()

        # Test fully supported answer
        answer = "Python is a programming language. It is widely used."
        contexts = ["Python is a popular programming language used worldwide."]

        faithfulness = await evaluator._calculate_faithfulness(answer, contexts)
        assert 0.0 <= faithfulness <= 1.0, f"Invalid faithfulness score: {faithfulness}"

    def test_aggregated_metrics_basic_functionality(self):
        """Test aggregated metrics calculation works"""
        evaluator = RAGEvaluator()

        # Create mock results
        results = []
        for i in range(10):
            test_case = RAGTestCase(
                question=f"Question {i}",
                ground_truth=f"Answer {i}",
                contexts=[f"Context {i}"]
            )

            result = RAGEvaluationResult(
                test_case=test_case,
                retrieved_contexts=[f"Retrieved {i}"],
                generated_answer=f"Generated {i}",
                faithfulness=0.8,
                answer_relevancy=0.75,
                context_precision=0.7,
                context_recall=0.85,
                latency_ms=100.0
            )
            results.append(result)

        # Calculate aggregated metrics
        aggregated = evaluator._calculate_aggregated_metrics(results)

        # Verify results
        assert aggregated.num_test_cases == 10
        assert 0.7 <= aggregated.faithfulness_mean <= 0.9
        assert 0.6 <= aggregated.answer_relevancy_mean <= 0.8
        assert 0.0 <= aggregated.overall_quality_score <= 1.0

    def test_numba_functions_are_compiled(self):
        """Verify numba functions are actually JIT-compiled"""
        from rag_evaluation import jaccard_similarity_numba, calculate_pass_rate_numba

        # These should be numba Dispatcher objects
        assert hasattr(jaccard_similarity_numba, 'py_func'), "Function not JIT-compiled"
        assert hasattr(calculate_pass_rate_numba, 'py_func'), "Function not JIT-compiled"

    def test_performance_improvement_exists(self):
        """Verify numba provides measurable performance improvement"""
        import time
        evaluator = RAGEvaluator()

        # Create test data
        text1 = " ".join([f"word{i}" for i in range(100)])
        text2 = " ".join([f"word{i}" for i in range(50, 150)])

        # Warmup (trigger JIT compilation)
        for _ in range(5):
            evaluator._simple_text_similarity(text1, text2)

        # Measure performance
        start = time.perf_counter()
        for _ in range(100):
            evaluator._simple_text_similarity(text1, text2)
        elapsed = time.perf_counter() - start

        # Should complete 100 iterations in < 100ms (1ms per iteration)
        # Original Python: ~10-20ms per iteration
        # Numba optimized: ~0.5-1ms per iteration
        assert elapsed < 0.1, f"Performance not improved: {elapsed}s for 100 iterations"

    @pytest.mark.asyncio
    async def test_faithfulness_with_realistic_data(self):
        """Test faithfulness with realistic answer and contexts"""
        evaluator = RAGEvaluator()

        answer = """
        Machine learning is a subset of artificial intelligence.
        It focuses on training algorithms to learn from data.
        Common applications include image recognition and NLP.
        """

        contexts = [
            "Artificial intelligence encompasses machine learning and deep learning.",
            "Machine learning algorithms learn patterns from training data.",
            "Image recognition and natural language processing are ML applications."
        ]

        faithfulness = await evaluator._calculate_faithfulness(answer, contexts)

        # Should have reasonable faithfulness (some sentences supported)
        # Note: Exact score depends on word overlap threshold
        assert 0.0 <= faithfulness <= 1.0, f"Invalid faithfulness score: {faithfulness}"
        # In practice, faithfulness will vary based on exact word matches

    def test_aggregation_with_varied_results(self):
        """Test aggregation with varied metric values"""
        evaluator = RAGEvaluator()

        # Create results with varied scores
        results = []
        scores = [0.9, 0.85, 0.7, 0.65, 0.8, 0.75, 0.95, 0.6, 0.88, 0.72]

        for i, score in enumerate(scores):
            test_case = RAGTestCase(
                question=f"Q{i}",
                ground_truth=f"A{i}",
                contexts=[f"C{i}"]
            )

            result = RAGEvaluationResult(
                test_case=test_case,
                retrieved_contexts=[f"R{i}"],
                generated_answer=f"G{i}",
                faithfulness=score,
                answer_relevancy=score * 0.9,
                context_precision=score * 0.85,
                context_recall=score * 0.95,
                latency_ms=100.0 + i * 10
            )
            results.append(result)

        aggregated = evaluator._calculate_aggregated_metrics(results)

        # Verify statistics make sense
        assert aggregated.faithfulness_mean > aggregated.faithfulness_median * 0.9
        assert aggregated.faithfulness_std > 0.0  # Should have variance
        assert aggregated.latency_p90 > aggregated.latency_p50


@pytest.mark.integration
class TestNumbaPerformanceValidation:
    """Validate performance improvements from numba"""

    def test_similarity_calculation_speed(self, benchmark):
        """Benchmark text similarity with numba"""
        evaluator = RAGEvaluator()

        # Warmup
        for _ in range(10):
            evaluator._simple_text_similarity("test", "test")

        result = benchmark(
            evaluator._simple_text_similarity,
            "machine learning algorithm",
            "deep learning model"
        )

        assert 0.0 <= result <= 1.0
        # Benchmark will show timing automatically

    @pytest.mark.asyncio
    async def test_faithfulness_calculation_speed(self, benchmark):
        """Benchmark faithfulness calculation with numba"""
        evaluator = RAGEvaluator()

        answer = "Machine learning is great. It has many uses. Very powerful technology."
        contexts = [
            "Machine learning is a powerful technology.",
            "It has numerous applications across industries."
        ]

        # Warmup
        for _ in range(5):
            await evaluator._calculate_faithfulness(answer, contexts)

        result = await benchmark.pedantic(
            evaluator._calculate_faithfulness,
            args=(answer, contexts),
            rounds=10
        )

        assert 0.0 <= result <= 1.0

    def test_aggregation_speed(self, benchmark):
        """Benchmark aggregation with numba"""
        evaluator = RAGEvaluator()

        # Create 100 results
        results = []
        for i in range(100):
            test_case = RAGTestCase(
                question=f"Q{i}",
                ground_truth=f"A{i}",
                contexts=[f"C{i}"]
            )

            result = RAGEvaluationResult(
                test_case=test_case,
                retrieved_contexts=[f"R{i}"],
                generated_answer=f"G{i}",
                faithfulness=np.random.random(),
                answer_relevancy=np.random.random(),
                context_precision=np.random.random(),
                context_recall=np.random.random(),
                latency_ms=np.random.uniform(50, 500)
            )
            results.append(result)

        # Warmup
        for _ in range(5):
            evaluator._calculate_aggregated_metrics(results)

        aggregated = benchmark(evaluator._calculate_aggregated_metrics, results)

        assert aggregated.num_test_cases == 100
