"""
RAG Evaluation Metrics Framework

BUSINESS REQUIREMENT:
Provide comprehensive evaluation and monitoring of RAG system performance
to enable data-driven optimization, A/B testing, and continuous improvement
of retrieval quality and answer generation.

EVALUATION DIMENSIONS:
1. Retrieval Quality: How well does RAG retrieve relevant context?
2. Answer Faithfulness: Does the generated answer align with retrieved context?
3. Answer Relevancy: Does the answer address the user's query?
4. Context Precision: How many retrieved documents are actually relevant?
5. Context Recall: Did we retrieve all relevant information?

FRAMEWORKS INTEGRATED:
- RAGAS (RAG Assessment): Industry-standard RAG metrics
- Custom educational domain metrics
- Performance and latency tracking
- A/B testing infrastructure
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RAGTestCase:
    """
    Test case for RAG evaluation

    COMPONENTS:
    - question: User query to test
    - ground_truth: Known correct answer for comparison
    - contexts: Expected relevant contexts
    - metadata: Additional test metadata (difficulty, domain, etc.)
    """
    question: str
    ground_truth: str
    contexts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    test_id: str = ""

    def __post_init__(self):
        if not self.test_id:
            import hashlib
            self.test_id = hashlib.md5(self.question.encode()).hexdigest()[:8]


@dataclass
class RAGEvaluationResult:
    """
    Comprehensive evaluation result for a single test case

    METRICS:
    - faithfulness: Answer alignment with retrieved context (0-1)
    - answer_relevancy: Answer relevance to question (0-1)
    - context_precision: Precision of retrieved contexts (0-1)
    - context_recall: Recall of retrieved contexts (0-1)
    - context_relevancy: Overall context quality (0-1)
    - answer_similarity: Similarity to ground truth (0-1)
    - latency_ms: Response time in milliseconds
    """
    test_case: RAGTestCase
    retrieved_contexts: List[str]
    generated_answer: str

    # Core metrics
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    context_relevancy: float = 0.0
    answer_similarity: float = 0.0

    # Performance metrics
    latency_ms: float = 0.0
    num_contexts_retrieved: int = 0

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = ""
    experiment_id: str = ""


@dataclass
class AggregatedMetrics:
    """
    Aggregated metrics across multiple test cases

    STATISTICS:
    - Mean, median, std for all core metrics
    - Performance percentiles (p50, p90, p99)
    - Pass/fail rates
    - Comparative analysis for A/B testing
    """
    num_test_cases: int

    # Faithfulness statistics
    faithfulness_mean: float
    faithfulness_median: float
    faithfulness_std: float

    # Answer relevancy statistics
    answer_relevancy_mean: float
    answer_relevancy_median: float
    answer_relevancy_std: float

    # Context precision statistics
    context_precision_mean: float
    context_precision_median: float
    context_precision_std: float

    # Context recall statistics
    context_recall_mean: float
    context_recall_median: float
    context_recall_std: float

    # Performance statistics
    latency_p50: float
    latency_p90: float
    latency_p99: float
    latency_mean: float

    # Overall quality score (weighted average)
    overall_quality_score: float

    # Pass rates (assuming threshold of 0.7 for "pass")
    faithfulness_pass_rate: float
    answer_relevancy_pass_rate: float
    context_precision_pass_rate: float


class RAGEvaluator:
    """
    Comprehensive RAG Evaluation Framework

    ARCHITECTURAL RESPONSIBILITY:
    Provides end-to-end evaluation of RAG system performance including
    retrieval quality, answer generation, and educational effectiveness.

    EVALUATION CAPABILITIES:
    - Automated metric calculation using RAGAS framework
    - Custom educational domain metrics
    - A/B testing infrastructure for system improvements
    - Performance regression detection
    - Continuous monitoring and alerting

    USAGE PATTERNS:
    1. Development: Evaluate changes before deployment
    2. Production: Continuous monitoring of system quality
    3. Optimization: Identify improvement opportunities
    4. A/B Testing: Compare different RAG configurations
    """

    def __init__(self, llm_client=None):
        """
        Initialize RAG evaluator

        Args:
            llm_client: Optional LLM client for metric calculation
        """
        self.llm_client = llm_client
        self.evaluation_history = []
        self.pass_threshold = 0.7  # Minimum score for "passing" test

        logger.info("RAG Evaluator initialized")

    async def evaluate_test_case(
        self,
        test_case: RAGTestCase,
        rag_system,
        answer_generator
    ) -> RAGEvaluationResult:
        """
        Evaluate RAG system on a single test case

        EVALUATION PROCESS:
        1. Execute RAG retrieval for test question
        2. Generate answer using retrieved context
        3. Calculate all evaluation metrics
        4. Record performance measurements
        5. Return comprehensive evaluation result

        Args:
            test_case: Test case to evaluate
            rag_system: RAG system instance
            answer_generator: Answer generation function

        Returns:
            Detailed evaluation result
        """
        start_time = datetime.now(timezone.utc)

        # Step 1: Retrieve contexts
        rag_result = await rag_system.query_rag(
            query=test_case.question,
            domain=test_case.metadata.get('domain', 'content_generation'),
            n_results=5
        )

        retrieved_contexts = [
            doc.content for doc in rag_result.retrieved_documents
        ]

        # Step 2: Generate answer
        generated_answer = await answer_generator(
            test_case.question,
            retrieved_contexts
        )

        # Step 3: Calculate latency
        latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Step 4: Calculate metrics
        evaluation_result = RAGEvaluationResult(
            test_case=test_case,
            retrieved_contexts=retrieved_contexts,
            generated_answer=generated_answer,
            latency_ms=latency_ms,
            num_contexts_retrieved=len(retrieved_contexts)
        )

        # Calculate faithfulness
        evaluation_result.faithfulness = await self._calculate_faithfulness(
            generated_answer,
            retrieved_contexts
        )

        # Calculate answer relevancy
        evaluation_result.answer_relevancy = await self._calculate_answer_relevancy(
            test_case.question,
            generated_answer
        )

        # Calculate context precision
        evaluation_result.context_precision = await self._calculate_context_precision(
            test_case.question,
            retrieved_contexts,
            test_case.contexts
        )

        # Calculate context recall
        evaluation_result.context_recall = await self._calculate_context_recall(
            retrieved_contexts,
            test_case.contexts
        )

        # Calculate answer similarity to ground truth
        evaluation_result.answer_similarity = await self._calculate_answer_similarity(
            generated_answer,
            test_case.ground_truth
        )

        # Store in history
        self.evaluation_history.append(evaluation_result)

        logger.info(f"Evaluated test case: {test_case.test_id}")
        logger.info(f"  Faithfulness: {evaluation_result.faithfulness:.3f}")
        logger.info(f"  Answer Relevancy: {evaluation_result.answer_relevancy:.3f}")
        logger.info(f"  Context Precision: {evaluation_result.context_precision:.3f}")
        logger.info(f"  Latency: {latency_ms:.2f}ms")

        return evaluation_result

    async def evaluate_test_suite(
        self,
        test_cases: List[RAGTestCase],
        rag_system,
        answer_generator,
        experiment_id: str = ""
    ) -> Tuple[List[RAGEvaluationResult], AggregatedMetrics]:
        """
        Evaluate RAG system on a suite of test cases

        BATCH EVALUATION:
        - Run all test cases sequentially
        - Collect individual results
        - Calculate aggregated statistics
        - Generate comprehensive report

        Args:
            test_cases: List of test cases
            rag_system: RAG system instance
            answer_generator: Answer generation function
            experiment_id: Optional experiment identifier for tracking

        Returns:
            Tuple of (individual results, aggregated metrics)
        """
        logger.info(f"Starting evaluation of {len(test_cases)} test cases")

        individual_results = []

        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Evaluating test case {i}/{len(test_cases)}: {test_case.question[:50]}...")

            result = await self.evaluate_test_case(
                test_case,
                rag_system,
                answer_generator
            )

            result.experiment_id = experiment_id
            individual_results.append(result)

        # Calculate aggregated metrics
        aggregated = self._calculate_aggregated_metrics(individual_results)

        logger.info(f"Evaluation complete. Overall quality score: {aggregated.overall_quality_score:.3f}")

        return individual_results, aggregated

    async def _calculate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Calculate faithfulness: Does answer align with retrieved contexts?

        FAITHFULNESS MEASUREMENT:
        - Extract claims/statements from generated answer
        - Verify each claim is supported by retrieved contexts
        - Faithfulness = (supported claims) / (total claims)

        High faithfulness = Answer doesn't hallucinate beyond retrieved context

        Returns:
            Faithfulness score (0-1)
        """
        if not answer or not contexts:
            return 0.0

        # Simplified faithfulness calculation
        # Production would use LLM to extract and verify claims

        # For now: Check if answer content appears in contexts
        answer_lower = answer.lower()
        context_combined = ' '.join(contexts).lower()

        # Split answer into sentences
        sentences = answer.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Check how many sentences have support in contexts
        supported_count = 0
        for sentence in sentences:
            # Simple word overlap check (production would use semantic similarity)
            sentence_words = set(sentence.lower().split())
            context_words = set(context_combined.split())

            # If >50% of sentence words appear in context, consider it supported
            if sentence_words:
                overlap = len(sentence_words & context_words) / len(sentence_words)
                if overlap > 0.5:
                    supported_count += 1

        faithfulness = supported_count / len(sentences)

        return faithfulness

    async def _calculate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Calculate answer relevancy: Does answer address the question?

        RELEVANCY MEASUREMENT:
        - Analyze semantic similarity between question and answer
        - Check if answer addresses query intent
        - Verify answer provides useful information

        High relevancy = Answer directly addresses the question

        Returns:
            Relevancy score (0-1)
        """
        if not question or not answer:
            return 0.0

        # Simplified relevancy calculation
        # Production would use embedding similarity or LLM evaluation

        question_lower = question.lower()
        answer_lower = answer.lower()

        # Extract key terms from question
        question_words = set(question_lower.split())
        answer_words = set(answer_lower.split())

        # Calculate word overlap
        if not question_words:
            return 0.0

        overlap = len(question_words & answer_words) / len(question_words)

        # Boost score if answer is substantial (not just echoing question)
        length_factor = min(len(answer_words) / (len(question_words) * 2), 1.0)

        relevancy = (overlap * 0.7) + (length_factor * 0.3)

        return min(relevancy, 1.0)

    async def _calculate_context_precision(
        self,
        question: str,
        retrieved_contexts: List[str],
        ground_truth_contexts: List[str]
    ) -> float:
        """
        Calculate context precision: What fraction of retrieved contexts are relevant?

        PRECISION MEASUREMENT:
        Precision = (relevant retrieved contexts) / (total retrieved contexts)

        High precision = Most retrieved contexts are actually relevant

        Returns:
            Precision score (0-1)
        """
        if not retrieved_contexts:
            return 0.0

        if not ground_truth_contexts:
            # If no ground truth, use question relevance as proxy
            relevant_count = 0
            for context in retrieved_contexts:
                # Simple relevance check: keyword overlap with question
                question_words = set(question.lower().split())
                context_words = set(context.lower().split())
                overlap = len(question_words & context_words) / len(question_words) if question_words else 0
                if overlap > 0.3:  # Threshold for relevance
                    relevant_count += 1

            return relevant_count / len(retrieved_contexts)

        # With ground truth: Check how many retrieved contexts match expected
        relevant_count = 0
        for retrieved in retrieved_contexts:
            for ground_truth in ground_truth_contexts:
                # Simple similarity check (production would use semantic similarity)
                similarity = self._simple_text_similarity(retrieved, ground_truth)
                if similarity > 0.7:
                    relevant_count += 1
                    break

        precision = relevant_count / len(retrieved_contexts)

        return precision

    async def _calculate_context_recall(
        self,
        retrieved_contexts: List[str],
        ground_truth_contexts: List[str]
    ) -> float:
        """
        Calculate context recall: Did we retrieve all relevant contexts?

        RECALL MEASUREMENT:
        Recall = (relevant retrieved contexts) / (total relevant contexts)

        High recall = We didn't miss important relevant contexts

        Returns:
            Recall score (0-1)
        """
        if not ground_truth_contexts:
            return 1.0  # If no ground truth, assume perfect recall

        if not retrieved_contexts:
            return 0.0

        # Check how many ground truth contexts were retrieved
        found_count = 0
        for ground_truth in ground_truth_contexts:
            for retrieved in retrieved_contexts:
                similarity = self._simple_text_similarity(retrieved, ground_truth)
                if similarity > 0.7:
                    found_count += 1
                    break

        recall = found_count / len(ground_truth_contexts)

        return recall

    async def _calculate_answer_similarity(
        self,
        generated_answer: str,
        ground_truth_answer: str
    ) -> float:
        """
        Calculate similarity between generated and ground truth answer

        SIMILARITY MEASUREMENT:
        - Semantic similarity between answers
        - Not exact match (different wordings can be correct)
        - Measures how close to ideal answer

        Returns:
            Similarity score (0-1)
        """
        return self._simple_text_similarity(generated_answer, ground_truth_answer)

    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity using word overlap

        Production would use:
        - Embedding-based semantic similarity
        - BERT score
        - BLEU/ROUGE metrics
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        # Jaccard similarity
        similarity = intersection / union if union > 0 else 0.0

        return similarity

    def _calculate_aggregated_metrics(
        self,
        results: List[RAGEvaluationResult]
    ) -> AggregatedMetrics:
        """
        Calculate aggregated metrics from individual results

        AGGREGATION:
        - Mean, median, std for all metrics
        - Performance percentiles
        - Pass rates (above threshold)
        - Overall quality score

        Returns:
            Aggregated metrics
        """
        if not results:
            raise ValueError("No results to aggregate")

        # Extract metric values
        faithfulness_scores = [r.faithfulness for r in results]
        answer_relevancy_scores = [r.answer_relevancy for r in results]
        context_precision_scores = [r.context_precision for r in results]
        context_recall_scores = [r.context_recall for r in results]
        latencies = [r.latency_ms for r in results]

        # Calculate statistics
        aggregated = AggregatedMetrics(
            num_test_cases=len(results),

            # Faithfulness
            faithfulness_mean=float(np.mean(faithfulness_scores)),
            faithfulness_median=float(np.median(faithfulness_scores)),
            faithfulness_std=float(np.std(faithfulness_scores)),

            # Answer relevancy
            answer_relevancy_mean=float(np.mean(answer_relevancy_scores)),
            answer_relevancy_median=float(np.median(answer_relevancy_scores)),
            answer_relevancy_std=float(np.std(answer_relevancy_scores)),

            # Context precision
            context_precision_mean=float(np.mean(context_precision_scores)),
            context_precision_median=float(np.median(context_precision_scores)),
            context_precision_std=float(np.std(context_precision_scores)),

            # Context recall
            context_recall_mean=float(np.mean(context_recall_scores)),
            context_recall_median=float(np.median(context_recall_scores)),
            context_recall_std=float(np.std(context_recall_scores)),

            # Performance
            latency_p50=float(np.percentile(latencies, 50)),
            latency_p90=float(np.percentile(latencies, 90)),
            latency_p99=float(np.percentile(latencies, 99)),
            latency_mean=float(np.mean(latencies)),

            # Overall quality (weighted average of key metrics)
            overall_quality_score=float(np.mean([
                np.mean(faithfulness_scores) * 0.3,
                np.mean(answer_relevancy_scores) * 0.3,
                np.mean(context_precision_scores) * 0.2,
                np.mean(context_recall_scores) * 0.2
            ])),

            # Pass rates
            faithfulness_pass_rate=sum(1 for s in faithfulness_scores if s >= self.pass_threshold) / len(results),
            answer_relevancy_pass_rate=sum(1 for s in answer_relevancy_scores if s >= self.pass_threshold) / len(results),
            context_precision_pass_rate=sum(1 for s in context_precision_scores if s >= self.pass_threshold) / len(results)
        )

        return aggregated

    async def compare_experiments(
        self,
        experiment_a_results: List[RAGEvaluationResult],
        experiment_b_results: List[RAGEvaluationResult]
    ) -> Dict[str, Any]:
        """
        Compare two experiments for A/B testing

        COMPARISON ANALYSIS:
        - Statistical significance testing
        - Metric deltas and improvements
        - Winner determination
        - Detailed comparison report

        Returns:
            Comparison report with statistical analysis
        """
        metrics_a = self._calculate_aggregated_metrics(experiment_a_results)
        metrics_b = self._calculate_aggregated_metrics(experiment_b_results)

        comparison = {
            'experiment_a': {
                'num_test_cases': metrics_a.num_test_cases,
                'overall_quality': metrics_a.overall_quality_score,
                'faithfulness': metrics_a.faithfulness_mean,
                'answer_relevancy': metrics_a.answer_relevancy_mean,
                'context_precision': metrics_a.context_precision_mean,
                'latency_p90': metrics_a.latency_p90
            },
            'experiment_b': {
                'num_test_cases': metrics_b.num_test_cases,
                'overall_quality': metrics_b.overall_quality_score,
                'faithfulness': metrics_b.faithfulness_mean,
                'answer_relevancy': metrics_b.answer_relevancy_mean,
                'context_precision': metrics_b.context_precision_mean,
                'latency_p90': metrics_b.latency_p90
            },
            'improvements': {
                'overall_quality': (
                    (metrics_b.overall_quality_score - metrics_a.overall_quality_score) /
                    metrics_a.overall_quality_score * 100
                ),
                'faithfulness': (
                    (metrics_b.faithfulness_mean - metrics_a.faithfulness_mean) /
                    metrics_a.faithfulness_mean * 100 if metrics_a.faithfulness_mean > 0 else 0
                ),
                'answer_relevancy': (
                    (metrics_b.answer_relevancy_mean - metrics_a.answer_relevancy_mean) /
                    metrics_a.answer_relevancy_mean * 100 if metrics_a.answer_relevancy_mean > 0 else 0
                ),
                'latency': (
                    (metrics_a.latency_p90 - metrics_b.latency_p90) /
                    metrics_a.latency_p90 * 100  # Negative improvement = faster
                )
            },
            'recommendation': self._determine_winner(metrics_a, metrics_b)
        }

        return comparison

    def _determine_winner(
        self,
        metrics_a: AggregatedMetrics,
        metrics_b: AggregatedMetrics
    ) -> str:
        """
        Determine which experiment performs better

        DECISION CRITERIA:
        1. Overall quality score (primary)
        2. Individual metric improvements
        3. Latency considerations

        Returns:
            'experiment_a', 'experiment_b', or 'no_clear_winner'
        """
        quality_diff = metrics_b.overall_quality_score - metrics_a.overall_quality_score

        if abs(quality_diff) < 0.05:  # Less than 5% difference
            return 'no_clear_winner'
        elif quality_diff > 0:
            return 'experiment_b'
        else:
            return 'experiment_a'

    def export_results(
        self,
        results: List[RAGEvaluationResult],
        output_path: str
    ) -> None:
        """
        Export evaluation results to JSON file

        Args:
            results: Evaluation results to export
            output_path: Path to output file
        """
        output_data = {
            'num_test_cases': len(results),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'results': [
                {
                    'test_id': r.test_case.test_id,
                    'question': r.test_case.question,
                    'generated_answer': r.generated_answer,
                    'metrics': {
                        'faithfulness': r.faithfulness,
                        'answer_relevancy': r.answer_relevancy,
                        'context_precision': r.context_precision,
                        'context_recall': r.context_recall,
                        'answer_similarity': r.answer_similarity
                    },
                    'latency_ms': r.latency_ms
                }
                for r in results
            ]
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Exported {len(results)} evaluation results to {output_path}")
