"""
Project Builder NLP Module

BUSINESS CONTEXT:
This module provides intent classification and entity extraction specifically
for the AI-powered project builder feature. It enables natural language
conversation for bulk project creation.

WHY THIS EXISTS:
The project builder needs specialized NLP capabilities to understand:
- Project creation requests and descriptions
- Roster file uploads and references
- Schedule configuration commands
- Location, track, and instructor specifications
- Confirmation and cancellation signals

WHAT THIS MODULE PROVIDES:
- ProjectBuilderIntentType: Enum of project builder specific intents
- ProjectBuilderEntityType: Enum of project builder specific entity types
- ProjectBuilderIntentClassifier: Keyword-based intent classification
- ProjectBuilderEntityExtractor: Regex-based entity extraction

HOW TO USE:
1. Create classifier and extractor instances
2. Pass user query to classifier.classify() for intent
3. Pass user query to extractor.extract() for entities
4. Use results to drive conversation flow in ProjectBuilderOrchestrator

PERFORMANCE TARGETS:
- Intent classification: <5ms
- Entity extraction: <10ms

@module project_builder_nlp
@author Course Creator Platform
@version 1.0.0
"""

import re
from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProjectBuilderIntentType(str, Enum):
    """
    Intent types specific to project builder conversations.

    WHY: Enables intelligent routing of user messages to appropriate
    handlers in the project builder workflow.

    WHAT: Categorizes all possible user intents during project building.

    HOW: Used by ProjectBuilderOrchestrator to determine next action.
    """

    # Project Creation Intents
    CREATE_PROJECT = "create_project"      # User wants to start a new project
    DESCRIBE_PROJECT = "describe_project"  # User is describing project details

    # Roster Management Intents
    UPLOAD_ROSTER = "upload_roster"        # User wants to upload instructor/student roster
    ADD_INSTRUCTORS = "add_instructors"    # User is adding instructors manually
    ADD_STUDENTS = "add_students"          # User is adding students manually

    # Structure Configuration Intents
    ADD_LOCATIONS = "add_locations"        # User is adding training locations
    ADD_TRACKS = "add_tracks"              # User is adding learning tracks
    ADD_COURSES = "add_courses"            # User is adding courses to tracks

    # Schedule Configuration Intents
    CONFIGURE_SCHEDULE = "configure_schedule"  # User is configuring schedule
    REVIEW_SCHEDULE = "review_schedule"        # User wants to see schedule

    # Content and Integration Intents
    CONFIGURE_CONTENT = "configure_content"    # User is configuring content generation
    CONFIGURE_ZOOM = "configure_zoom"          # User is configuring Zoom rooms

    # Workflow Control Intents
    CONFIRM = "confirm"                    # User confirms action
    CANCEL = "cancel"                      # User cancels action
    EDIT = "edit"                          # User wants to modify something
    HELP = "help"                          # User needs help/guidance
    STATUS = "status"                      # User asking about current status

    # General
    UNKNOWN = "unknown"                    # Cannot classify intent


class ProjectBuilderEntityType(str, Enum):
    """
    Entity types extracted from project builder conversations.

    WHY: Enables structured data extraction from natural language
    descriptions of training programs.

    WHAT: All entity types that can appear in project builder context.

    HOW: Used to populate ProjectBuilderSpec from conversation.
    """

    # Project Entities
    PROJECT_NAME = "project_name"
    PROJECT_DESCRIPTION = "project_description"

    # Location Entities
    LOCATION = "location"
    CITY = "city"
    COUNTRY = "country"
    TIMEZONE = "timezone"

    # Track Entities
    TRACK_NAME = "track_name"
    COURSE_NAME = "course_name"

    # People Entities
    INSTRUCTOR_NAME = "instructor_name"
    STUDENT_NAME = "student_name"
    EMAIL = "email"

    # Quantity Entities
    STUDENT_COUNT = "student_count"
    INSTRUCTOR_COUNT = "instructor_count"
    TRACK_COUNT = "track_count"

    # Time Entities
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    DAY_OF_WEEK = "day_of_week"

    # File Entities
    FILE_REFERENCE = "file_reference"
    FILE_TYPE = "file_type"

    # Configuration Entities
    BOOLEAN_VALUE = "boolean_value"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProjectBuilderIntent:
    """
    Result of project builder intent classification.

    WHAT: Contains the classified intent type, confidence score,
    matched keywords, and additional metadata.

    HOW: Returned by ProjectBuilderIntentClassifier.classify()
    """

    intent_type: ProjectBuilderIntentType
    confidence: float = 0.0
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectBuilderEntity:
    """
    Extracted entity from project builder conversation.

    WHAT: Contains the extracted text, entity type, confidence,
    position span, and additional metadata.

    HOW: Returned by ProjectBuilderEntityExtractor.extract()
    """

    text: str
    entity_type: ProjectBuilderEntityType
    confidence: float = 0.0
    span: Tuple[int, int] = (0, 0)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# INTENT CLASSIFIER
# =============================================================================

class ProjectBuilderIntentClassifier:
    """
    Rule-based intent classifier for project builder conversations.

    BUSINESS VALUE:
    - Enables intelligent conversation routing
    - Reduces need for LLM on simple intents
    - Provides predictable intent recognition

    TECHNICAL APPROACH:
    - Keyword-based pattern matching with weights
    - Phrase patterns for multi-word expressions
    - Confidence scoring based on match strength
    """

    def __init__(self):
        """
        Initialize classifier with intent patterns.

        DESIGN NOTE:
        Patterns are organized by intent type with weighted keywords.
        Higher weight = stronger indicator of intent.
        """
        self.intent_patterns: Dict[ProjectBuilderIntentType, List[Dict[str, Any]]] = {
            # Project Creation
            ProjectBuilderIntentType.CREATE_PROJECT: [
                {"keywords": ["create a project", "create project", "new project"], "weight": 1.0},
                {"keywords": ["set up a project", "setup project"], "weight": 0.95},
                {"keywords": ["build a project", "build project"], "weight": 0.9},
                {"keywords": ["start a project", "start project"], "weight": 0.9},
                {"keywords": ["create a training program", "new training program"], "weight": 0.95},
                {"keywords": ["set up training", "setup training"], "weight": 0.85},
                # Broader patterns that combine
                {"keywords": ["create"], "weight": 0.5},
                {"keywords": ["project"], "weight": 0.4},
                {"keywords": ["training"], "weight": 0.3},
            ],

            ProjectBuilderIntentType.DESCRIBE_PROJECT: [
                {"keywords": ["we need to train", "training for"], "weight": 0.8},
                {"keywords": ["the project will", "this project is"], "weight": 0.7},
                {"keywords": ["bootcamp", "program"], "weight": 0.5},
                {"keywords": ["developers", "engineers", "analysts"], "weight": 0.4},
                {"keywords": ["train"], "weight": 0.5},
                {"keywords": ["graduates", "new hires", "employees"], "weight": 0.5},
            ],

            # Roster Upload
            ProjectBuilderIntentType.UPLOAD_ROSTER: [
                {"keywords": ["upload roster", "upload the roster"], "weight": 1.0},
                {"keywords": ["import roster", "import the roster"], "weight": 0.95},
                {"keywords": ["upload instructor", "upload instructors"], "weight": 0.9},
                {"keywords": ["upload student", "upload students"], "weight": 0.9},
                {"keywords": ["attach file", "attaching file"], "weight": 0.8},
                {"keywords": [".csv", ".xlsx", ".xls", ".json"], "weight": 0.7},
                {"keywords": ["spreadsheet", "excel file", "csv file"], "weight": 0.75},
                {"keywords": ["roster file", "list of students", "list of instructors"], "weight": 0.9},
                {"keywords": ["upload"], "weight": 0.4},
                {"keywords": ["roster", "instructor list", "student list"], "weight": 0.5},
                {"keywords": ["file", "import"], "weight": 0.3},
            ],

            ProjectBuilderIntentType.ADD_INSTRUCTORS: [
                {"keywords": ["add instructor", "add instructors"], "weight": 1.0},
                {"keywords": ["assign instructor", "assign instructors"], "weight": 0.9},
                {"keywords": ["instructors are", "instructors will be"], "weight": 0.8},
            ],

            ProjectBuilderIntentType.ADD_STUDENTS: [
                {"keywords": ["add student", "add students"], "weight": 1.0},
                {"keywords": ["enroll student", "enroll students"], "weight": 0.9},
                {"keywords": ["students are", "students will be"], "weight": 0.8},
            ],

            # Locations
            ProjectBuilderIntentType.ADD_LOCATIONS: [
                {"keywords": ["add location", "add locations"], "weight": 1.0},
                {"keywords": ["training location", "training locations"], "weight": 0.9},
                {"keywords": ["sites in", "offices in"], "weight": 0.8},
                {"keywords": ["locations are", "locations will be"], "weight": 0.85},
                {"keywords": ["location", "site"], "weight": 0.4},
                {"keywords": ["training site"], "weight": 0.7},
            ],

            # Tracks
            ProjectBuilderIntentType.ADD_TRACKS: [
                {"keywords": ["add track", "add tracks"], "weight": 1.0},
                {"keywords": ["create track", "create tracks"], "weight": 0.95},
                {"keywords": ["learning track", "learning tracks"], "weight": 0.9},
                {"keywords": ["tracks are", "tracks will be"], "weight": 0.85},
                {"keywords": ["three tracks", "two tracks", "multiple tracks"], "weight": 0.8},
                {"keywords": ["track"], "weight": 0.5},
            ],

            # Schedule
            ProjectBuilderIntentType.CONFIGURE_SCHEDULE: [
                {"keywords": ["set up schedule", "setup schedule", "configure schedule"], "weight": 1.0},
                {"keywords": ["set up the schedule"], "weight": 1.0},
                {"keywords": ["schedule the", "scheduling"], "weight": 0.85},
                {"keywords": ["start date", "end date"], "weight": 0.8},
                {"keywords": ["class times", "session times"], "weight": 0.85},
                {"keywords": ["from 9", "to 5", "9am", "5pm"], "weight": 0.6},
                {"keywords": ["schedule"], "weight": 0.4},
                {"keywords": ["configure"], "weight": 0.3},
            ],

            ProjectBuilderIntentType.REVIEW_SCHEDULE: [
                {"keywords": ["show schedule", "show the schedule"], "weight": 1.0},
                {"keywords": ["show me the schedule", "show me schedule"], "weight": 1.0},
                {"keywords": ["review schedule", "review the schedule"], "weight": 0.95},
                {"keywords": ["preview schedule", "preview the schedule"], "weight": 0.9},
                {"keywords": ["what does the schedule look like"], "weight": 0.9},
                {"keywords": ["proposed schedule"], "weight": 0.8},
                {"keywords": ["generated schedule"], "weight": 0.8},
            ],

            # Content Generation
            ProjectBuilderIntentType.CONFIGURE_CONTENT: [
                {"keywords": ["generate content", "content generation"], "weight": 1.0},
                {"keywords": ["auto-generate", "automatically generate"], "weight": 0.95},
                {"keywords": ["create slides", "generate slides"], "weight": 0.85},
                {"keywords": ["create quizzes", "generate quizzes"], "weight": 0.85},
                {"keywords": ["create syllabus", "generate syllabus"], "weight": 0.85},
                {"keywords": ["content automatically"], "weight": 0.8},
            ],

            # Zoom
            ProjectBuilderIntentType.CONFIGURE_ZOOM: [
                {"keywords": ["zoom room", "zoom rooms"], "weight": 1.0},
                {"keywords": ["zoom meeting", "zoom meetings"], "weight": 0.95},
                {"keywords": ["video conferencing", "virtual classroom"], "weight": 0.85},
                {"keywords": ["zoom link", "zoom links"], "weight": 0.9},
            ],

            # Confirmation
            ProjectBuilderIntentType.CONFIRM: [
                {"keywords": ["yes", "yeah", "yep", "correct", "right"], "weight": 0.8},
                {"keywords": ["confirm", "proceed", "go ahead"], "weight": 1.0},
                {"keywords": ["looks good", "looks great"], "weight": 0.9},
                {"keywords": ["that's correct", "that is correct"], "weight": 0.95},
                {"keywords": ["create it", "do it"], "weight": 0.85},
            ],

            # Cancel
            ProjectBuilderIntentType.CANCEL: [
                {"keywords": ["no", "nope", "cancel"], "weight": 0.9},
                {"keywords": ["stop", "abort", "quit"], "weight": 0.95},
                {"keywords": ["don't create", "do not create"], "weight": 1.0},
                {"keywords": ["never mind", "nevermind"], "weight": 0.85},
            ],

            # Edit
            ProjectBuilderIntentType.EDIT: [
                {"keywords": ["change", "modify", "update"], "weight": 0.9},
                {"keywords": ["edit", "revise"], "weight": 1.0},
                {"keywords": ["actually", "let me change"], "weight": 0.8},
                {"keywords": ["fix", "correct"], "weight": 0.75},
            ],

            # Help
            ProjectBuilderIntentType.HELP: [
                {"keywords": ["help", "help me"], "weight": 1.0},
                {"keywords": ["how do i", "how can i"], "weight": 0.9},
                {"keywords": ["what can you do", "what can i do"], "weight": 0.85},
                {"keywords": ["guide", "guidance"], "weight": 0.8},
            ],

            # Status
            ProjectBuilderIntentType.STATUS: [
                {"keywords": ["status", "current status"], "weight": 1.0},
                {"keywords": ["where are we", "what's done"], "weight": 0.9},
                {"keywords": ["progress", "how far"], "weight": 0.8},
            ],
        }

    def classify(self, query: str) -> ProjectBuilderIntent:
        """
        Classify user query into project builder intent.

        ALGORITHM:
        1. Normalize query (lowercase, strip)
        2. Handle empty queries
        3. Match keywords against patterns
        4. Calculate confidence scores
        5. Select intent with highest confidence
        6. Apply minimum threshold

        Args:
            query: User query text

        Returns:
            ProjectBuilderIntent with classification results

        Performance:
            Typical: <3ms
        """
        # Normalize query
        query_normalized = query.strip().lower() if query else ""

        # Handle empty queries
        if not query_normalized:
            return ProjectBuilderIntent(
                intent_type=ProjectBuilderIntentType.UNKNOWN,
                confidence=0.0,
                keywords=[],
                metadata={"reason": "empty_query"}
            )

        # Match patterns and calculate scores
        intent_scores: Dict[ProjectBuilderIntentType, float] = {}
        matched_keywords: Dict[ProjectBuilderIntentType, List[str]] = {}

        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            keywords = []

            for pattern in patterns:
                pattern_matched = False

                for keyword in pattern["keywords"]:
                    if keyword.lower() in query_normalized:
                        if not pattern_matched:
                            score += pattern["weight"]
                            pattern_matched = True
                        keywords.append(keyword)

            if score > 0:
                intent_scores[intent_type] = min(score, 1.0)
                matched_keywords[intent_type] = keywords

        # Select best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]

            # Apply minimum confidence threshold
            if confidence < 0.3:
                best_intent = ProjectBuilderIntentType.UNKNOWN
                confidence = 0.2
                keywords_matched = []
            else:
                keywords_matched = matched_keywords[best_intent]
        else:
            best_intent = ProjectBuilderIntentType.UNKNOWN
            confidence = 0.1
            keywords_matched = []

        logger.debug(
            f"Project builder intent classification: "
            f"query='{query[:50]}...', intent={best_intent.value}, "
            f"confidence={confidence:.2f}, keywords={keywords_matched}"
        )

        return ProjectBuilderIntent(
            intent_type=best_intent,
            confidence=confidence,
            keywords=keywords_matched,
            metadata={
                "query_length": len(query),
                "word_count": len(query_normalized.split()),
                "all_scores": {i.value: s for i, s in intent_scores.items()}
            }
        )


# =============================================================================
# ENTITY EXTRACTOR
# =============================================================================

class ProjectBuilderEntityExtractor:
    """
    Regex-based entity extractor for project builder conversations.

    BUSINESS VALUE:
    - Extracts structured data from natural language
    - Enables auto-population of ProjectBuilderSpec
    - Reduces need for follow-up questions

    TECHNICAL APPROACH:
    - Multi-pass extraction with priority ordering
    - Pattern-based extraction for each entity type
    - Confidence scoring based on extraction method
    """

    def __init__(self):
        """
        Initialize extractor with regex patterns.

        DESIGN NOTE:
        Patterns are ordered by specificity and confidence.
        More specific patterns are matched first.
        """
        # Quoted strings pattern (highest confidence)
        self.quoted_pattern = re.compile(r"""
            ['""]          # Opening quote
            ([^'"\"]+)     # Capture group
            ['""]          # Closing quote
        """, re.VERBOSE)

        # Project name patterns
        self.project_name_patterns = [
            re.compile(r'(?:project|program)\s+(?:called|named)\s+["\']?([^"\'.,]+)["\']?', re.IGNORECASE),
            re.compile(r'(?:the|a)\s+project\s+is\s+["\']?([^"\'.,]+)["\']?', re.IGNORECASE),
            re.compile(r'create\s+["\']([^"\']+)["\']', re.IGNORECASE),
        ]

        # Location patterns - major cities
        self.major_cities = {
            "new york", "nyc", "los angeles", "la", "chicago", "san francisco", "sf",
            "seattle", "boston", "austin", "denver", "atlanta", "dallas", "houston",
            "miami", "london", "paris", "berlin", "tokyo", "singapore", "sydney",
            "melbourne", "toronto", "vancouver", "amsterdam", "dublin", "munich",
            "zürich", "zurich", "frankfurt", "hong kong", "shanghai", "beijing",
            "bangalore", "mumbai", "delhi", "hyderabad", "pune"
        }

        self.location_patterns = [
            re.compile(r'(?:locations?|sites?|offices?)\s+(?:in|are|at)\s+([^.]+?)(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        ]

        # Track name patterns
        self.track_patterns = [
            re.compile(r'(?:the\s+)?([A-Z][a-zA-Z\s]+?)\s+track', re.IGNORECASE),
            re.compile(r'track\s+(?:for\s+)?([A-Z][a-zA-Z\s]+?)(?:\.|,|$)', re.IGNORECASE),
            re.compile(r'tracks?:\s*([^.]+?)(?:\.|$)', re.IGNORECASE),
            re.compile(r'(?:create|add)\s+tracks?:\s*([^.]+)', re.IGNORECASE),
        ]

        # Track name keywords for filtering
        self.track_keywords = {
            "backend", "frontend", "fullstack", "full-stack", "full stack",
            "devops", "dev ops", "development", "developer",
            "business analyst", "ba", "operations", "ops",
            "data science", "data", "machine learning", "ml", "ai",
            "cloud", "infrastructure", "security", "qa", "testing",
            "mobile", "ios", "android", "react", "angular", "vue"
        }

        # Email pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # Name patterns (for instructors/students)
        self.name_patterns = [
            re.compile(r'(?:instructor|teacher|professor)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
            re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+will\s+teach', re.IGNORECASE),
        ]

        # Count patterns
        self.count_patterns = [
            re.compile(r'(\d+)\s+(?:students?|participants?|enrollees?|trainees?)', re.IGNORECASE),
            re.compile(r'(?:about|approximately|around)\s+(\d+)\s+(?:students?|participants?)', re.IGNORECASE),
        ]

        # Date patterns
        self.date_patterns = [
            re.compile(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?', re.IGNORECASE),
            re.compile(r'\d{4}-\d{2}-\d{2}'),
            re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}'),
        ]

        # Duration patterns
        self.duration_pattern = re.compile(r'(\d+)\s+(weeks?|months?|days?)', re.IGNORECASE)

        # Time patterns
        self.time_patterns = [
            re.compile(r'(\d{1,2})\s*(?::|)?(?:\d{2})?\s*(?:am|pm)', re.IGNORECASE),
            re.compile(r'from\s+(\d{1,2}(?::\d{2})?(?:\s*(?:am|pm))?)\s+to\s+(\d{1,2}(?::\d{2})?(?:\s*(?:am|pm))?)', re.IGNORECASE),
        ]

        # File reference patterns
        self.file_pattern = re.compile(r'(\S+\.(?:csv|xlsx?|json|txt))\b', re.IGNORECASE)

    def extract(self, query: str) -> List[ProjectBuilderEntity]:
        """
        Extract entities from user query.

        ALGORITHM:
        1. Extract quoted strings (highest confidence)
        2. Extract project names
        3. Extract locations
        4. Extract track names
        5. Extract emails
        6. Extract names
        7. Extract counts
        8. Extract dates and times
        9. Extract file references
        10. Remove duplicates and overlaps

        Args:
            query: User query text

        Returns:
            List of extracted entities sorted by confidence

        Performance:
            Typical: <8ms
        """
        if not query or not query.strip():
            return []

        entities: List[ProjectBuilderEntity] = []
        extracted_spans: List[Tuple[int, int]] = []

        # Step 1: Extract quoted strings as project names
        for match in self.quoted_pattern.finditer(query):
            text = match.group(1).strip()
            span = (match.start(1), match.end(1))

            if text and len(text) >= 3 and not self._overlaps(span, extracted_spans):
                entities.append(ProjectBuilderEntity(
                    text=text,
                    entity_type=ProjectBuilderEntityType.PROJECT_NAME,
                    confidence=0.95,
                    span=span,
                    metadata={"extraction_method": "quoted"}
                ))
                extracted_spans.append(span)

        # Step 2: Extract project names from patterns
        for pattern in self.project_name_patterns:
            for match in pattern.finditer(query):
                text = match.group(1).strip()
                span = (match.start(1), match.end(1))

                if text and len(text) >= 3 and not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=text,
                        entity_type=ProjectBuilderEntityType.PROJECT_NAME,
                        confidence=0.8,
                        span=span,
                        metadata={"extraction_method": "pattern"}
                    ))
                    extracted_spans.append(span)

        # Step 3: Extract locations
        entities.extend(self._extract_locations(query, extracted_spans))

        # Step 4: Extract track names
        entities.extend(self._extract_tracks(query, extracted_spans))

        # Step 5: Extract emails
        for match in self.email_pattern.finditer(query):
            text = match.group(0)
            span = (match.start(), match.end())

            if not self._overlaps(span, extracted_spans):
                entities.append(ProjectBuilderEntity(
                    text=text,
                    entity_type=ProjectBuilderEntityType.EMAIL,
                    confidence=0.95,
                    span=span,
                    metadata={"extraction_method": "email_pattern"}
                ))
                extracted_spans.append(span)

        # Step 6: Extract instructor/student names
        for pattern in self.name_patterns:
            for match in pattern.finditer(query):
                text = match.group(1).strip()
                span = (match.start(1), match.end(1))

                if text and len(text) >= 3 and not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=text,
                        entity_type=ProjectBuilderEntityType.INSTRUCTOR_NAME,
                        confidence=0.75,
                        span=span,
                        metadata={"extraction_method": "pattern"}
                    ))
                    extracted_spans.append(span)

        # Step 7: Extract counts
        for pattern in self.count_patterns:
            for match in pattern.finditer(query):
                count = int(match.group(1))
                span = (match.start(), match.end())

                if not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=match.group(0),
                        entity_type=ProjectBuilderEntityType.STUDENT_COUNT,
                        confidence=0.9,
                        span=span,
                        metadata={"extraction_method": "count_pattern", "value": count}
                    ))
                    extracted_spans.append(span)

        # Step 8: Extract dates
        for pattern in self.date_patterns:
            for match in pattern.finditer(query):
                text = match.group(0)
                span = (match.start(), match.end())

                if not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=text,
                        entity_type=ProjectBuilderEntityType.DATE,
                        confidence=0.85,
                        span=span,
                        metadata={"extraction_method": "date_pattern"}
                    ))
                    extracted_spans.append(span)

        # Step 9: Extract durations
        for match in self.duration_pattern.finditer(query):
            value = int(match.group(1))
            unit = match.group(2).lower()
            span = (match.start(), match.end())

            if not self._overlaps(span, extracted_spans):
                entities.append(ProjectBuilderEntity(
                    text=match.group(0),
                    entity_type=ProjectBuilderEntityType.DURATION,
                    confidence=0.85,
                    span=span,
                    metadata={"extraction_method": "duration_pattern", "value": value, "unit": unit}
                ))
                extracted_spans.append(span)

        # Step 10: Extract times
        for pattern in self.time_patterns:
            for match in pattern.finditer(query):
                text = match.group(0)
                span = (match.start(), match.end())

                if not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=text,
                        entity_type=ProjectBuilderEntityType.TIME,
                        confidence=0.8,
                        span=span,
                        metadata={"extraction_method": "time_pattern"}
                    ))
                    extracted_spans.append(span)

        # Step 11: Extract file references
        for match in self.file_pattern.finditer(query):
            text = match.group(1)
            span = (match.start(1), match.end(1))

            if not self._overlaps(span, extracted_spans):
                extension = text.split('.')[-1].lower()
                entities.append(ProjectBuilderEntity(
                    text=text,
                    entity_type=ProjectBuilderEntityType.FILE_REFERENCE,
                    confidence=0.9,
                    span=span,
                    metadata={"extraction_method": "file_pattern", "extension": extension}
                ))
                extracted_spans.append(span)

        # Sort by confidence
        entities.sort(key=lambda e: e.confidence, reverse=True)

        logger.debug(
            f"Extracted {len(entities)} project builder entities: "
            f"{[(e.entity_type.value, e.text[:20]) for e in entities]}"
        )

        return entities

    def _extract_locations(
        self,
        query: str,
        extracted_spans: List[Tuple[int, int]]
    ) -> List[ProjectBuilderEntity]:
        """
        Extract location entities from query.

        ALGORITHM:
        1. Look for pattern-based locations
        2. Match against known major cities
        3. Assign confidence based on method
        """
        entities = []
        query_lower = query.lower()

        # Check for major cities in query
        for city in self.major_cities:
            if city in query_lower:
                # Find the position in original query
                start = query_lower.find(city)
                end = start + len(city)
                span = (start, end)

                if not self._overlaps(span, extracted_spans):
                    # Get original case version
                    original_text = query[start:end]

                    entities.append(ProjectBuilderEntity(
                        text=original_text,
                        entity_type=ProjectBuilderEntityType.LOCATION,
                        confidence=0.85,
                        span=span,
                        metadata={"extraction_method": "city_lookup"}
                    ))
                    extracted_spans.append(span)

        # Also try pattern-based extraction
        for pattern in self.location_patterns:
            for match in pattern.finditer(query):
                text = match.group(1).strip()
                span = (match.start(1), match.end(1))

                # Parse comma-separated locations
                if ',' in text or ' and ' in text.lower():
                    parts = re.split(r',\s*|\s+and\s+', text, flags=re.IGNORECASE)
                    for part in parts:
                        part = part.strip()
                        if part and len(part) >= 2:
                            # Find approximate span
                            part_start = query.lower().find(part.lower())
                            if part_start >= 0:
                                part_span = (part_start, part_start + len(part))
                                if not self._overlaps(part_span, extracted_spans):
                                    entities.append(ProjectBuilderEntity(
                                        text=part,
                                        entity_type=ProjectBuilderEntityType.LOCATION,
                                        confidence=0.75,
                                        span=part_span,
                                        metadata={"extraction_method": "pattern_split"}
                                    ))
                                    extracted_spans.append(part_span)

        return entities

    def _extract_tracks(
        self,
        query: str,
        extracted_spans: List[Tuple[int, int]]
    ) -> List[ProjectBuilderEntity]:
        """
        Extract track name entities from query.

        ALGORITHM:
        1. Look for track patterns
        2. Parse comma-separated track names
        3. Match against track keywords
        """
        entities = []
        query_lower = query.lower()

        # First check for comma/and separated list patterns
        for pattern in self.track_patterns:
            for match in pattern.finditer(query):
                text = match.group(1).strip()
                span = (match.start(1), match.end(1))

                # Parse list of tracks
                if ',' in text or ' and ' in text.lower():
                    parts = re.split(r',\s*|\s+and\s+', text, flags=re.IGNORECASE)
                    for part in parts:
                        part = part.strip()
                        if part and len(part) >= 2:
                            part_start = query.lower().find(part.lower())
                            if part_start >= 0:
                                part_span = (part_start, part_start + len(part))
                                if not self._overlaps(part_span, extracted_spans):
                                    entities.append(ProjectBuilderEntity(
                                        text=part,
                                        entity_type=ProjectBuilderEntityType.TRACK_NAME,
                                        confidence=0.8,
                                        span=part_span,
                                        metadata={"extraction_method": "pattern_split"}
                                    ))
                                    extracted_spans.append(part_span)
                elif not self._overlaps(span, extracted_spans):
                    entities.append(ProjectBuilderEntity(
                        text=text,
                        entity_type=ProjectBuilderEntityType.TRACK_NAME,
                        confidence=0.75,
                        span=span,
                        metadata={"extraction_method": "pattern"}
                    ))
                    extracted_spans.append(span)

        # Also check for track keywords
        for keyword in self.track_keywords:
            if keyword in query_lower:
                start = query_lower.find(keyword)
                end = start + len(keyword)
                span = (start, end)

                if not self._overlaps(span, extracted_spans):
                    original_text = query[start:end]

                    entities.append(ProjectBuilderEntity(
                        text=original_text,
                        entity_type=ProjectBuilderEntityType.TRACK_NAME,
                        confidence=0.7,
                        span=span,
                        metadata={"extraction_method": "keyword"}
                    ))
                    extracted_spans.append(span)

        return entities

    def _overlaps(
        self,
        span: Tuple[int, int],
        existing_spans: List[Tuple[int, int]]
    ) -> bool:
        """
        Check if span overlaps with any existing spans.

        Args:
            span: (start, end) tuple
            existing_spans: List of existing spans

        Returns:
            True if overlap exists
        """
        start, end = span

        for existing_start, existing_end in existing_spans:
            if not (end <= existing_start or start >= existing_end):
                return True

        return False
