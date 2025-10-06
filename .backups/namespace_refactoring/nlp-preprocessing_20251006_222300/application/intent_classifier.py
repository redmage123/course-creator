"""
Rule-based Intent Classifier

BUSINESS CONTEXT:
Enables intelligent routing to skip LLM for simple queries,
reducing cost by 30-40% and latency from ~1s to ~50ms for direct lookups.

TECHNICAL IMPLEMENTATION:
- Keyword-based pattern matching
- Confidence scoring based on keyword strength
- Decision logic for LLM vs. direct response
- Case-insensitive matching with regex

PERFORMANCE TARGET:
- Classification time: <5ms per query
- Accuracy: >85% on typical queries

DESIGN PHILOSOPHY:
- Simple is better than complex for this use case
- Rule-based is more predictable than ML for routing
- Fast keyword matching beats ML inference latency
- Easy to debug and extend with new patterns
"""

import re
from typing import Dict, List, Set
from domain.entities import Intent, IntentType
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Rule-based intent classifier using keyword patterns

    BUSINESS VALUE:
    - Reduces LLM costs by 30-40% for simple queries
    - Reduces latency from ~1s to ~50ms for direct lookups
    - Enables intelligent routing to specialized services

    TECHNICAL APPROACH:
    - Pattern matching with weighted keywords
    - Confidence scoring based on match strength
    - Fallback to UNKNOWN for ambiguous queries
    """

    def __init__(self):
        """
        Initialize classifier with keyword patterns

        DESIGN NOTE:
        Patterns are ordered by specificity - more specific patterns first
        to avoid misclassification by broader patterns
        """
        # Define keyword patterns with weights
        # Higher weight = stronger indicator of intent
        self.intent_patterns: Dict[IntentType, List[Dict[str, any]]] = {
            # PREREQUISITE_CHECK - Can use knowledge graph directly
            IntentType.PREREQUISITE_CHECK: [
                {"keywords": ["prerequisites", "prerequisite"], "weight": 1.0},
                {"keywords": ["requirements", "required", "require"], "weight": 0.8},
                {"keywords": ["need to know", "should know", "must know"], "weight": 0.9},
                {"keywords": ["before taking", "before starting"], "weight": 0.7},
                {"keywords": ["background", "foundation"], "weight": 0.6},
            ],

            # COURSE_LOOKUP - Can use metadata search directly
            IntentType.COURSE_LOOKUP: [
                {"keywords": ["find courses", "search courses"], "weight": 1.0},
                {"keywords": ["show me courses", "show courses", "list courses"], "weight": 0.9},
                {"keywords": ["courses about", "courses on"], "weight": 0.8},
                {"keywords": ["available courses", "all courses"], "weight": 0.7},
                {"keywords": ["browse", "explore courses"], "weight": 0.7},
            ],

            # SKILL_LOOKUP - Can use metadata search directly
            IntentType.SKILL_LOOKUP: [
                {"keywords": ["what skills", "which skills"], "weight": 1.0},
                {"keywords": ["skills will i learn", "skills taught"], "weight": 0.9},
                {"keywords": ["learn skills", "acquire skills"], "weight": 0.7},
                {"keywords": ["competencies", "abilities"], "weight": 0.6},
            ],

            # LEARNING_PATH - Can use knowledge graph directly
            IntentType.LEARNING_PATH: [
                {"keywords": ["learning path", "learning journey"], "weight": 1.0},
                {"keywords": ["path from", "journey from"], "weight": 0.9},
                {"keywords": ["progression", "advance from"], "weight": 0.8},
                {"keywords": ["roadmap", "curriculum path"], "weight": 0.7},
                {"keywords": ["how do i progress", "how to advance"], "weight": 0.8},
            ],

            # CONCEPT_EXPLANATION - Requires LLM
            IntentType.CONCEPT_EXPLANATION: [
                {"keywords": ["explain", "explanation"], "weight": 1.0},
                {"keywords": ["what is", "what are"], "weight": 0.8},
                {"keywords": ["define", "definition"], "weight": 0.9},
                {"keywords": ["how does", "how do"], "weight": 0.7},
                {"keywords": ["describe", "tell me about"], "weight": 0.7},
            ],

            # GREETING - Simple canned response
            IntentType.GREETING: [
                {"keywords": ["hello", "hi", "hey"], "weight": 1.0},
                {"keywords": ["good morning", "good afternoon", "good evening"], "weight": 0.9},
                {"keywords": ["greetings", "howdy"], "weight": 0.8},
            ],

            # COMMAND - May need LLM for validation
            IntentType.COMMAND: [
                {"keywords": ["create", "generate"], "weight": 1.0},
                {"keywords": ["update", "modify", "change"], "weight": 0.9},
                {"keywords": ["delete", "remove"], "weight": 0.9},
                {"keywords": ["add", "insert"], "weight": 0.7},
            ],

            # CLARIFICATION - Needs conversation context (LLM)
            IntentType.CLARIFICATION: [
                {"keywords": ["more details", "tell me more"], "weight": 1.0},
                {"keywords": ["and what about", "what about"], "weight": 0.8},
                {"keywords": ["also", "additionally"], "weight": 0.6},
                {"keywords": ["furthermore", "moreover"], "weight": 0.5},
            ],

            # QUESTION - General questions requiring LLM
            IntentType.QUESTION: [
                {"keywords": ["why", "how come"], "weight": 0.7},
                {"keywords": ["when", "where"], "weight": 0.6},
                {"keywords": ["who", "whose"], "weight": 0.6},
            ],
        }

        # Define which intents should call LLM
        self.llm_required_intents: Set[IntentType] = {
            IntentType.CONCEPT_EXPLANATION,
            IntentType.COMMAND,
            IntentType.CLARIFICATION,
            IntentType.QUESTION,
            IntentType.UNKNOWN,
        }

    def classify(self, query: str) -> Intent:
        """
        Classify user query into intent type

        ALGORITHM:
        1. Normalize query (lowercase, strip whitespace)
        2. Check for empty/invalid queries -> UNKNOWN
        3. Match keywords against patterns
        4. Calculate confidence scores
        5. Select intent with highest confidence
        6. Apply minimum confidence threshold
        7. Return Intent with metadata

        Args:
            query: User query text

        Returns:
            Intent object with classification results

        Performance:
            - Typical: <2ms
            - Worst case: <5ms
        """
        # Normalize query
        query_normalized = query.strip().lower()

        # Handle empty queries
        if not query_normalized:
            return Intent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                keywords=[],
                should_call_llm=True,
                metadata={"reason": "empty_query"}
            )

        # Extract metadata
        word_count = len(query_normalized.split())
        query_length = len(query)

        # Match patterns and calculate scores
        intent_scores: Dict[IntentType, float] = {}
        matched_keywords: Dict[IntentType, List[str]] = {}

        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            keywords = []

            for pattern in patterns:
                # Track if any keyword in this pattern matched
                pattern_matched = False

                for keyword in pattern["keywords"]:
                    # Use regex for word boundary matching
                    # This ensures "find" doesn't match "finding" as a full word
                    pattern_regex = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern_regex, query_normalized):
                        if not pattern_matched:
                            # Only count pattern weight once, even if multiple keywords match
                            score += pattern["weight"]
                            pattern_matched = True
                        keywords.append(keyword)

            if score > 0:
                # Simply cap score at 1.0
                # Multiple pattern matches increase confidence naturally
                final_score = min(score, 1.0)
                intent_scores[intent_type] = final_score
                matched_keywords[intent_type] = keywords

        # Select intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]

            # Apply minimum confidence threshold
            # If confidence too low, classify as UNKNOWN
            if confidence < 0.3:
                best_intent = IntentType.UNKNOWN
                confidence = 0.2
                keywords_matched = []
            else:
                keywords_matched = matched_keywords[best_intent]
        else:
            # No patterns matched
            best_intent = IntentType.UNKNOWN
            confidence = 0.1
            keywords_matched = []

        # Determine if LLM is required
        should_call_llm = best_intent in self.llm_required_intents

        # Build metadata
        metadata = {
            "query_length": query_length,
            "word_count": word_count,
            "all_scores": {intent.value: score for intent, score in intent_scores.items()},
        }

        logger.debug(
            f"Intent classification: query='{query[:50]}...', "
            f"intent={best_intent.value}, confidence={confidence:.2f}, "
            f"keywords={keywords_matched}"
        )

        return Intent(
            intent_type=best_intent,
            confidence=confidence,
            keywords=keywords_matched,
            should_call_llm=should_call_llm,
            metadata=metadata
        )

    def add_pattern(
        self,
        intent_type: IntentType,
        keywords: List[str],
        weight: float = 0.7
    ) -> None:
        """
        Add custom pattern for intent type

        BUSINESS VALUE:
        Allows runtime extension of classifier without code changes

        Args:
            intent_type: Intent to add pattern for
            keywords: List of keywords for pattern
            weight: Pattern weight (0.0-1.0)

        Example:
            >>> classifier.add_pattern(
            ...     IntentType.COURSE_LOOKUP,
            ...     ["recommend courses", "suggest courses"],
            ...     weight=0.8
            ... )
        """
        if intent_type not in self.intent_patterns:
            self.intent_patterns[intent_type] = []

        self.intent_patterns[intent_type].append({
            "keywords": keywords,
            "weight": weight
        })

        logger.info(
            f"Added custom pattern: intent={intent_type.value}, "
            f"keywords={keywords}, weight={weight}"
        )
