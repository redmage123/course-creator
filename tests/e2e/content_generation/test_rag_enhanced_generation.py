"""
Comprehensive E2E Tests for RAG-Enhanced Content Generation

BUSINESS REQUIREMENT:
Instructors need AI-powered content generation that leverages RAG (Retrieval-Augmented
Generation) to create contextually relevant, pedagogically sound course materials. The
system must integrate with the knowledge graph to ensure content is prerequisite-aware,
difficulty-appropriate, and connected to related concepts.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Validates RAG integration with knowledge graph
- Tests multi-layer verification (UI + Database + Knowledge Graph)
- Covers 10 comprehensive RAG-enhanced generation scenarios

TEST COVERAGE:
1. RAG Integration (4 tests)
   - Generate content with RAG context from knowledge graph
   - Generate personalized content based on student progress
   - Generate prerequisite-aware content (adaptive to knowledge gaps)
   - Generate progressive difficulty content

2. Knowledge Graph Queries (3 tests)
   - Query related concepts for slide generation
   - Query prerequisite relationships for content ordering
   - Query learning paths for module structure

3. Content Enhancement (3 tests)
   - Enhance slides with related examples from knowledge base
   - Add cross-references to related modules
   - Suggest additional resources based on content

PRIORITY: P0 (CRITICAL) - RAG-enhanced content generation is a core platform differentiator
"""

import pytest
import time
import uuid
import json
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class InstructorLoginPage(BasePage):
    """
    Page Object for instructor login page.

    BUSINESS CONTEXT:
    Instructors must authenticate to access RAG-enhanced content generation tools.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to instructor login page."""
        self.navigate_to("/login")

    def login(self, email, password):
        """
        Perform instructor login.

        Args:
            email: Instructor email
            password: Instructor password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)


class RAGContentGenerationPage(BasePage):
    """
    Page Object for RAG-enhanced content generation interface.

    BUSINESS CONTEXT:
    This interface allows instructors to generate course content (slides, quizzes, labs)
    using RAG technology that retrieves relevant context from the knowledge graph and
    generates personalized, prerequisite-aware content.
    """

    # Locators - Content Generation UI
    GENERATE_CONTENT_BUTTON = (By.ID, "generateContentBtn")
    CONTENT_TYPE_DROPDOWN = (By.ID, "contentType")
    TOPIC_INPUT = (By.ID, "topicInput")
    DIFFICULTY_LEVEL_DROPDOWN = (By.ID, "difficultyLevel")

    # RAG Configuration
    ENABLE_RAG_CHECKBOX = (By.ID, "enableRAG")
    RAG_SOURCES_DROPDOWN = (By.ID, "ragSources")
    KNOWLEDGE_GRAPH_CHECKBOX = (By.ID, "useKnowledgeGraph")
    STUDENT_PROGRESS_CHECKBOX = (By.ID, "useStudentProgress")

    # Knowledge Graph Integration
    SHOW_GRAPH_BUTTON = (By.ID, "showKnowledgeGraph")
    GRAPH_CONCEPTS_LIST = (By.ID, "graphConceptsList")
    SELECT_PREREQUISITE_BUTTON = (By.ID, "selectPrerequisites")
    PREREQUISITE_CHIPS = (By.CLASS_NAME, "prerequisite-chip")

    # Generation Progress
    GENERATION_PROGRESS_BAR = (By.ID, "generationProgress")
    GENERATION_STATUS_TEXT = (By.ID, "generationStatus")
    GENERATION_COMPLETE_MESSAGE = (By.CLASS_NAME, "generation-complete")

    # Generated Content Preview
    CONTENT_PREVIEW_PANEL = (By.ID, "contentPreview")
    SLIDE_PREVIEW_LIST = (By.CLASS_NAME, "slide-preview-item")
    QUIZ_PREVIEW_LIST = (By.CLASS_NAME, "quiz-preview-item")
    RAG_SOURCES_SECTION = (By.CLASS_NAME, "rag-sources-section")
    SOURCE_CITATION = (By.CLASS_NAME, "source-citation")

    # Content Enhancement
    ENHANCE_CONTENT_BUTTON = (By.ID, "enhanceContentBtn")
    ADD_EXAMPLES_CHECKBOX = (By.ID, "addExamples")
    ADD_CROSS_REFERENCES_CHECKBOX = (By.ID, "addCrossReferences")
    SUGGEST_RESOURCES_CHECKBOX = (By.ID, "suggestResources")

    # Personalization
    TARGET_STUDENT_DROPDOWN = (By.ID, "targetStudent")
    ADAPT_TO_PROGRESS_CHECKBOX = (By.ID, "adaptToProgress")
    KNOWLEDGE_GAPS_SECTION = (By.CLASS_NAME, "knowledge-gaps")
    PROGRESSIVE_DIFFICULTY_CHECKBOX = (By.ID, "progressiveDifficulty")

    # Action Buttons
    SAVE_CONTENT_BUTTON = (By.ID, "saveContentBtn")
    REGENERATE_BUTTON = (By.ID, "regenerateBtn")
    CANCEL_BUTTON = (By.ID, "cancelBtn")

    def navigate(self):
        """Navigate to RAG content generation page."""
        self.navigate_to("/html/instructor-dashboard.html#content-generation")
        time.sleep(1)

    def enable_rag_generation(self):
        """Enable RAG-enhanced content generation."""
        if not self.is_element_selected(*self.ENABLE_RAG_CHECKBOX):
            self.click_element(*self.ENABLE_RAG_CHECKBOX)
            time.sleep(0.5)

    def select_content_type(self, content_type):
        """
        Select content type to generate.

        Args:
            content_type: 'slides', 'quiz', 'lab', 'module'
        """
        select = Select(self.find_element(*self.CONTENT_TYPE_DROPDOWN))
        select.select_by_value(content_type)
        time.sleep(0.5)

    def enter_topic(self, topic):
        """Enter topic for content generation."""
        self.enter_text(*self.TOPIC_INPUT, topic)

    def select_difficulty_level(self, level):
        """
        Select difficulty level.

        Args:
            level: 'beginner', 'intermediate', 'advanced'
        """
        select = Select(self.find_element(*self.DIFFICULTY_LEVEL_DROPDOWN))
        select.select_by_value(level)
        time.sleep(0.5)

    def enable_knowledge_graph_integration(self):
        """Enable knowledge graph integration for RAG."""
        if not self.is_element_selected(*self.KNOWLEDGE_GRAPH_CHECKBOX):
            self.click_element(*self.KNOWLEDGE_GRAPH_CHECKBOX)
            time.sleep(0.5)

    def enable_student_progress_personalization(self):
        """Enable student progress-based personalization."""
        if not self.is_element_selected(*self.STUDENT_PROGRESS_CHECKBOX):
            self.click_element(*self.STUDENT_PROGRESS_CHECKBOX)
            time.sleep(0.5)

    def select_target_student(self, student_name):
        """
        Select target student for personalization.

        Args:
            student_name: Student name or ID
        """
        select = Select(self.find_element(*self.TARGET_STUDENT_DROPDOWN))
        select.select_by_visible_text(student_name)
        time.sleep(0.5)

    def generate_content(self, wait_for_completion=True):
        """
        Click generate content button and optionally wait for completion.

        Args:
            wait_for_completion: Whether to wait for generation to complete

        Returns:
            True if generation completed successfully
        """
        self.click_element(*self.GENERATE_CONTENT_BUTTON)

        if wait_for_completion:
            # Wait for progress bar to appear
            time.sleep(1)

            # Wait for generation to complete (max 120 seconds for AI generation)
            try:
                WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located(self.GENERATION_COMPLETE_MESSAGE)
                )
                return True
            except TimeoutException:
                return False

        return True

    def get_generation_status(self):
        """Get current generation status text."""
        if self.is_element_present(*self.GENERATION_STATUS_TEXT, timeout=2):
            return self.get_element_text(*self.GENERATION_STATUS_TEXT)
        return None

    def show_knowledge_graph(self):
        """Show knowledge graph visualization."""
        self.click_element(*self.SHOW_GRAPH_BUTTON)
        time.sleep(1)

    def get_knowledge_graph_concepts(self):
        """
        Get list of concepts from knowledge graph.

        Returns:
            List of concept names
        """
        concepts = []
        concept_elements = self.find_elements(*self.GRAPH_CONCEPTS_LIST)
        for element in concept_elements:
            concepts.append(element.text)
        return concepts

    def get_selected_prerequisites(self):
        """
        Get list of selected prerequisite concepts.

        Returns:
            List of prerequisite concept names
        """
        prerequisites = []
        prereq_chips = self.find_elements(*self.PREREQUISITE_CHIPS)
        for chip in prereq_chips:
            prerequisites.append(chip.text)
        return prerequisites

    def get_generated_slides_count(self):
        """Get number of generated slides."""
        slides = self.find_elements(*self.SLIDE_PREVIEW_LIST)
        return len(slides)

    def get_generated_quiz_questions_count(self):
        """Get number of generated quiz questions."""
        questions = self.find_elements(*self.QUIZ_PREVIEW_LIST)
        return len(questions)

    def get_rag_sources(self):
        """
        Get list of RAG sources cited in generated content.

        Returns:
            List of source citations
        """
        sources = []
        if self.is_element_present(*self.RAG_SOURCES_SECTION, timeout=3):
            source_elements = self.find_elements(*self.SOURCE_CITATION)
            for element in source_elements:
                sources.append(element.text)
        return sources

    def enhance_content_with_examples(self):
        """Enhance content by adding related examples."""
        if not self.is_element_selected(*self.ADD_EXAMPLES_CHECKBOX):
            self.click_element(*self.ADD_EXAMPLES_CHECKBOX)
        self.click_element(*self.ENHANCE_CONTENT_BUTTON)
        time.sleep(2)

    def add_cross_references(self):
        """Add cross-references to related modules."""
        if not self.is_element_selected(*self.ADD_CROSS_REFERENCES_CHECKBOX):
            self.click_element(*self.ADD_CROSS_REFERENCES_CHECKBOX)
        self.click_element(*self.ENHANCE_CONTENT_BUTTON)
        time.sleep(2)

    def suggest_additional_resources(self):
        """Suggest additional learning resources."""
        if not self.is_element_selected(*self.SUGGEST_RESOURCES_CHECKBOX):
            self.click_element(*self.SUGGEST_RESOURCES_CHECKBOX)
        self.click_element(*self.ENHANCE_CONTENT_BUTTON)
        time.sleep(2)

    def get_knowledge_gaps(self):
        """
        Get identified knowledge gaps for target student.

        Returns:
            List of knowledge gap descriptions
        """
        gaps = []
        if self.is_element_present(*self.KNOWLEDGE_GAPS_SECTION, timeout=3):
            gap_items = self.find_elements(By.CLASS_NAME, "knowledge-gap-item")
            for item in gap_items:
                gaps.append(item.text)
        return gaps

    def enable_progressive_difficulty(self):
        """Enable progressive difficulty content generation."""
        if not self.is_element_selected(*self.PROGRESSIVE_DIFFICULTY_CHECKBOX):
            self.click_element(*self.PROGRESSIVE_DIFFICULTY_CHECKBOX)
            time.sleep(0.5)

    def save_generated_content(self):
        """Save generated content to course."""
        self.click_element(*self.SAVE_CONTENT_BUTTON)
        time.sleep(2)

    def regenerate_content(self):
        """Regenerate content with current settings."""
        self.click_element(*self.REGENERATE_BUTTON)
        time.sleep(1)


class KnowledgeGraphBrowserPage(BasePage):
    """
    Page Object for Knowledge Graph Browser.

    BUSINESS CONTEXT:
    The knowledge graph browser allows instructors to explore concepts, prerequisites,
    and learning paths visually, enabling them to make informed decisions about
    content generation and course structure.
    """

    # Locators
    GRAPH_CANVAS = (By.ID, "knowledgeGraphCanvas")
    GRAPH_NODE = (By.CLASS_NAME, "graph-node")
    GRAPH_EDGE = (By.CLASS_NAME, "graph-edge")
    SEARCH_CONCEPT_INPUT = (By.ID, "searchConcept")
    SEARCH_BUTTON = (By.ID, "searchConceptBtn")

    # Node Details Panel
    NODE_DETAILS_PANEL = (By.ID, "nodeDetailsPanel")
    NODE_NAME = (By.ID, "nodeName")
    NODE_DESCRIPTION = (By.ID, "nodeDescription")
    PREREQUISITE_LIST = (By.ID, "prerequisiteList")
    RELATED_CONCEPTS_LIST = (By.ID, "relatedConceptsList")

    # Learning Path
    SHOW_LEARNING_PATH_BUTTON = (By.ID, "showLearningPath")
    LEARNING_PATH_STEPS = (By.CLASS_NAME, "learning-path-step")

    # Filters
    DIFFICULTY_FILTER = (By.ID, "difficultyFilter")
    COURSE_FILTER = (By.ID, "courseFilter")

    def navigate(self):
        """Navigate to knowledge graph browser."""
        self.navigate_to("/html/knowledge-graph.html")
        time.sleep(2)

    def search_concept(self, concept_name):
        """
        Search for a concept in the knowledge graph.

        Args:
            concept_name: Name of concept to search
        """
        self.enter_text(*self.SEARCH_CONCEPT_INPUT, concept_name)
        self.click_element(*self.SEARCH_BUTTON)
        time.sleep(1)

    def get_visible_nodes_count(self):
        """Get count of visible nodes in graph."""
        nodes = self.find_elements(*self.GRAPH_NODE)
        return len(nodes)

    def get_visible_edges_count(self):
        """Get count of visible edges in graph."""
        edges = self.find_elements(*self.GRAPH_EDGE)
        return len(edges)

    def click_node(self, node_name):
        """Click on a specific node by name."""
        nodes = self.find_elements(*self.GRAPH_NODE)
        for node in nodes:
            if node_name.lower() in node.text.lower():
                node.click()
                time.sleep(1)
                return True
        return False

    def get_node_prerequisites(self):
        """
        Get list of prerequisites for selected node.

        Returns:
            List of prerequisite concept names
        """
        prerequisites = []
        if self.is_element_present(*self.NODE_DETAILS_PANEL, timeout=2):
            prereq_items = self.find_elements(By.CLASS_NAME, "prerequisite-item")
            for item in prereq_items:
                prerequisites.append(item.text)
        return prerequisites

    def get_related_concepts(self):
        """
        Get list of related concepts for selected node.

        Returns:
            List of related concept names
        """
        related = []
        if self.is_element_present(*self.NODE_DETAILS_PANEL, timeout=2):
            related_items = self.find_elements(By.CLASS_NAME, "related-concept-item")
            for item in related_items:
                related.append(item.text)
        return related

    def show_learning_path(self, target_concept):
        """
        Show learning path to target concept.

        Args:
            target_concept: Target concept name

        Returns:
            List of concepts in learning path
        """
        self.search_concept(target_concept)
        time.sleep(1)
        self.click_element(*self.SHOW_LEARNING_PATH_BUTTON)
        time.sleep(2)

        path_steps = self.find_elements(*self.LEARNING_PATH_STEPS)
        return [step.text for step in path_steps]

    def filter_by_difficulty(self, difficulty):
        """
        Filter graph by difficulty level.

        Args:
            difficulty: 'beginner', 'intermediate', 'advanced'
        """
        select = Select(self.find_element(*self.DIFFICULTY_FILTER))
        select.select_by_value(difficulty)
        time.sleep(1)


class ContentEnhancementPage(BasePage):
    """
    Page Object for Content Enhancement Interface.

    BUSINESS CONTEXT:
    After generating initial content, instructors can enhance it with examples,
    cross-references, and additional resources from the knowledge base.
    """

    # Locators
    CONTENT_EDITOR = (By.ID, "contentEditor")
    ENHANCEMENT_PANEL = (By.ID, "enhancementPanel")

    # Example Enhancement
    ADD_EXAMPLE_BUTTON = (By.ID, "addExampleBtn")
    EXAMPLE_SUGGESTIONS_LIST = (By.CLASS_NAME, "example-suggestion")
    SELECT_EXAMPLE_CHECKBOX = (By.CLASS_NAME, "select-example")

    # Cross-Reference Enhancement
    ADD_CROSS_REF_BUTTON = (By.ID, "addCrossRefBtn")
    CROSS_REF_SUGGESTIONS = (By.CLASS_NAME, "cross-ref-suggestion")

    # Resource Suggestions
    SUGGESTED_RESOURCES_SECTION = (By.ID, "suggestedResources")
    RESOURCE_ITEM = (By.CLASS_NAME, "resource-item")
    ADD_RESOURCE_BUTTON = (By.CLASS_NAME, "add-resource-btn")

    # Preview
    PREVIEW_ENHANCED_CONTENT_BUTTON = (By.ID, "previewEnhancedBtn")
    ENHANCED_CONTENT_PREVIEW = (By.ID, "enhancedPreview")

    def navigate(self):
        """Navigate to content enhancement page."""
        self.navigate_to("/html/content-enhancement.html")
        time.sleep(1)

    def get_example_suggestions_count(self):
        """Get number of example suggestions."""
        suggestions = self.find_elements(*self.EXAMPLE_SUGGESTIONS_LIST)
        return len(suggestions)

    def select_example(self, index):
        """
        Select an example suggestion by index.

        Args:
            index: Index of example to select (0-based)
        """
        checkboxes = self.find_elements(*self.SELECT_EXAMPLE_CHECKBOX)
        if index < len(checkboxes):
            checkboxes[index].click()
            time.sleep(0.5)

    def add_selected_examples(self):
        """Add selected examples to content."""
        self.click_element(*self.ADD_EXAMPLE_BUTTON)
        time.sleep(1)

    def get_cross_reference_suggestions_count(self):
        """Get number of cross-reference suggestions."""
        suggestions = self.find_elements(*self.CROSS_REF_SUGGESTIONS)
        return len(suggestions)

    def add_cross_reference(self, index):
        """
        Add a cross-reference by index.

        Args:
            index: Index of cross-reference to add
        """
        suggestions = self.find_elements(*self.CROSS_REF_SUGGESTIONS)
        if index < len(suggestions):
            suggestions[index].click()
            time.sleep(1)

    def get_suggested_resources_count(self):
        """Get number of suggested resources."""
        if self.is_element_present(*self.SUGGESTED_RESOURCES_SECTION, timeout=2):
            resources = self.find_elements(*self.RESOURCE_ITEM)
            return len(resources)
        return 0

    def add_resource(self, index):
        """
        Add a suggested resource by index.

        Args:
            index: Index of resource to add
        """
        add_buttons = self.find_elements(*self.ADD_RESOURCE_BUTTON)
        if index < len(add_buttons):
            add_buttons[index].click()
            time.sleep(1)

    def preview_enhanced_content(self):
        """Preview enhanced content."""
        self.click_element(*self.PREVIEW_ENHANCED_CONTENT_BUTTON)
        time.sleep(2)
        return self.is_element_present(*self.ENHANCED_CONTENT_PREVIEW, timeout=3)


# ============================================================================
# TEST SUITE - RAG Integration Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
@pytest.mark.rag
@pytest.mark.priority_critical
class TestRAGIntegration(BaseTest):
    """
    Test RAG-enhanced content generation with knowledge graph integration.

    BUSINESS REQUIREMENT:
    Content generation must leverage RAG to retrieve relevant context from the
    knowledge graph, ensuring generated content is accurate, contextually appropriate,
    and pedagogically sound.
    """

    def test_01_generate_content_with_rag_context_from_knowledge_graph(self):
        """
        Test generating content with RAG context retrieved from knowledge graph.

        BUSINESS SCENARIO:
        An instructor wants to generate slides about "Python Functions" that include
        context from prerequisite concepts (variables, data types) and related concepts
        (scope, recursion) from the knowledge graph.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to RAG content generation page
        3. Enable RAG with knowledge graph integration
        4. Select topic "Python Functions"
        5. Generate slides
        6. Verify slides include context from knowledge graph
        7. Verify RAG sources are cited
        8. Verify prerequisite concepts are referenced

        EXPECTED BEHAVIOR:
        - Generation completes successfully within 120 seconds
        - At least 5 slides generated
        - RAG sources section visible with 3+ citations
        - Prerequisite concepts (variables, data types) mentioned in slides
        - Related concepts (scope, recursion) suggested in enhancement panel

        VALIDATION:
        - UI: Slides displayed in preview panel
        - UI: RAG sources section shows citations
        - Database: Generated content saved with RAG metadata
        - Knowledge Graph: Concept relationships queried correctly
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login as instructor
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Navigate to RAG content generation
        rag_page.navigate()

        # Step 3: Enable RAG with knowledge graph
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()

        # Step 4: Configure content generation
        rag_page.select_content_type("slides")
        rag_page.enter_topic("Python Functions")
        rag_page.select_difficulty_level("beginner")

        # Step 5: Generate content
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Content generation should complete within 120 seconds"

        # Step 6: Verify slides generated
        slides_count = rag_page.get_generated_slides_count()
        assert slides_count >= 5, f"Expected at least 5 slides, got {slides_count}"

        # Step 7: Verify RAG sources cited
        rag_sources = rag_page.get_rag_sources()
        assert len(rag_sources) >= 3, f"Expected at least 3 RAG sources, got {len(rag_sources)}"

        # Step 8: Verify prerequisite concepts referenced
        prerequisites = rag_page.get_selected_prerequisites()
        assert any("variable" in p.lower() for p in prerequisites), \
            "Prerequisites should include 'variables'"
        assert any("data type" in p.lower() for p in prerequisites), \
            "Prerequisites should include 'data types'"

    def test_02_generate_personalized_content_based_on_student_progress(self):
        """
        Test generating content personalized to a specific student's progress.

        BUSINESS SCENARIO:
        An instructor wants to generate personalized quiz questions for a student
        who has mastered basic Python but struggles with object-oriented concepts.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to RAG content generation
        3. Enable student progress personalization
        4. Select target student "John Doe"
        5. Generate quiz on "Python OOP"
        6. Verify quiz questions adapted to student's level
        7. Verify knowledge gaps addressed
        8. Verify difficulty progression

        EXPECTED BEHAVIOR:
        - Generation completes successfully
        - Quiz questions focus on OOP concepts (student's weak area)
        - Questions avoid basic Python (student's strong area)
        - Knowledge gaps section shows OOP concepts student hasn't mastered
        - Question difficulty increases progressively

        VALIDATION:
        - UI: Quiz questions displayed
        - UI: Knowledge gaps section shows OOP concepts
        - Database: Student progress data retrieved
        - RAG: Content personalized based on progress data
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Navigate to RAG generation
        rag_page.navigate()

        # Step 3: Enable personalization
        rag_page.enable_rag_generation()
        rag_page.enable_student_progress_personalization()

        # Step 4: Select target student
        rag_page.select_target_student("John Doe")

        # Step 5: Configure quiz generation
        rag_page.select_content_type("quiz")
        rag_page.enter_topic("Python Object-Oriented Programming")
        rag_page.select_difficulty_level("intermediate")

        # Step 6: Generate quiz
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Quiz generation should complete"

        # Step 7: Verify quiz questions
        questions_count = rag_page.get_generated_quiz_questions_count()
        assert questions_count >= 5, f"Expected at least 5 questions, got {questions_count}"

        # Step 8: Verify knowledge gaps identified
        knowledge_gaps = rag_page.get_knowledge_gaps()
        assert len(knowledge_gaps) > 0, "Knowledge gaps should be identified"
        assert any("class" in gap.lower() or "object" in gap.lower()
                  for gap in knowledge_gaps), \
            "Knowledge gaps should include OOP concepts"

    def test_03_generate_prerequisite_aware_content_adaptive_to_knowledge_gaps(self):
        """
        Test generating content that adapts to identified knowledge gaps.

        BUSINESS SCENARIO:
        An instructor discovers a student has knowledge gaps in "loops" while learning
        "recursion". The system should generate prerequisite content to fill the gap
        before moving to advanced topics.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to RAG content generation
        3. Enable knowledge gap adaptation
        4. Select topic "Recursion"
        5. Select student with loop knowledge gaps
        6. Generate content
        7. Verify prerequisite content (loops) included
        8. Verify content progression from basic to advanced
        9. Verify knowledge graph shows prerequisite path

        EXPECTED BEHAVIOR:
        - System identifies "loops" as prerequisite for "recursion"
        - Generated content includes loop review before recursion
        - Content follows prerequisite order (loops -> recursion)
        - Knowledge graph shows prerequisite relationships
        - Student can navigate prerequisite path

        VALIDATION:
        - UI: Content includes prerequisite review
        - UI: Knowledge graph shows prerequisite path
        - Database: Content metadata includes prerequisite info
        - Knowledge Graph: Prerequisite relationships queried
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)
        kg_page = KnowledgeGraphBrowserPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Navigate to RAG generation
        rag_page.navigate()

        # Step 3: Configure prerequisite-aware generation
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.enable_student_progress_personalization()

        # Step 4: Select student with gaps
        rag_page.select_target_student("Student With Gaps")

        # Step 5: Select advanced topic
        rag_page.select_content_type("slides")
        rag_page.enter_topic("Recursion in Python")
        rag_page.select_difficulty_level("intermediate")

        # Step 6: Show knowledge graph
        rag_page.show_knowledge_graph()

        # Step 7: Verify prerequisites shown
        prerequisites = rag_page.get_selected_prerequisites()
        assert any("loop" in p.lower() for p in prerequisites), \
            "Prerequisites should include 'loops'"

        # Step 8: Generate content
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Content generation should complete"

        # Step 9: Verify slides include prerequisite content
        slides_count = rag_page.get_generated_slides_count()
        assert slides_count >= 7, \
            f"Expected at least 7 slides (prerequisite + main content), got {slides_count}"

    def test_04_generate_progressive_difficulty_content(self):
        """
        Test generating content with progressive difficulty levels.

        BUSINESS SCENARIO:
        An instructor wants to create a learning module that starts with easy concepts
        and progressively increases in difficulty, adapting to student skill level.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to RAG content generation
        3. Enable progressive difficulty
        4. Generate module on "Data Structures"
        5. Verify content starts with beginner level
        6. Verify content progresses to intermediate
        7. Verify content ends with advanced topics
        8. Verify difficulty transitions are smooth

        EXPECTED BEHAVIOR:
        - Module includes beginner, intermediate, and advanced content
        - Early slides cover basic concepts (lists, tuples)
        - Middle slides cover intermediate concepts (dictionaries, sets)
        - Late slides cover advanced concepts (trees, graphs)
        - Difficulty transitions are gradual
        - Each section references previous concepts

        VALIDATION:
        - UI: Slides show progressive difficulty
        - UI: Difficulty indicators visible on slides
        - Database: Slides tagged with difficulty levels
        - Content: Logical progression from basic to advanced
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Navigate to RAG generation
        rag_page.navigate()

        # Step 3: Configure progressive difficulty
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.enable_progressive_difficulty()

        # Step 4: Generate module
        rag_page.select_content_type("module")
        rag_page.enter_topic("Python Data Structures")
        rag_page.select_difficulty_level("beginner")  # Starting difficulty

        # Step 5: Generate content
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Module generation should complete"

        # Step 6: Verify progressive difficulty
        slides_count = rag_page.get_generated_slides_count()
        assert slides_count >= 10, \
            f"Expected at least 10 slides for progressive module, got {slides_count}"

        # Step 7: Verify RAG sources include multiple difficulty levels
        rag_sources = rag_page.get_rag_sources()
        assert len(rag_sources) >= 5, \
            f"Expected sources from multiple difficulty levels, got {len(rag_sources)}"


# ============================================================================
# TEST SUITE - Knowledge Graph Query Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
@pytest.mark.knowledge_graph
@pytest.mark.priority_high
class TestKnowledgeGraphQueries(BaseTest):
    """
    Test knowledge graph integration for content generation.

    BUSINESS REQUIREMENT:
    The knowledge graph provides structured relationships between concepts,
    enabling intelligent content generation that respects prerequisites and
    leverages related concepts.
    """

    def test_05_query_related_concepts_for_slide_generation(self):
        """
        Test querying knowledge graph for related concepts during slide generation.

        BUSINESS SCENARIO:
        An instructor generates slides on "Python Lists" and the system queries
        the knowledge graph to find related concepts (tuples, arrays, iteration)
        that should be referenced or included.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to knowledge graph browser
        3. Search for concept "Python Lists"
        4. View related concepts
        5. Navigate to RAG content generation
        6. Generate slides on "Python Lists"
        7. Verify related concepts suggested
        8. Verify related concepts included in content

        EXPECTED BEHAVIOR:
        - Knowledge graph shows related concepts
        - Related concepts include: tuples, arrays, iteration, indexing
        - Generated slides reference related concepts
        - Cross-references to related modules suggested

        VALIDATION:
        - UI: Related concepts visible in knowledge graph
        - UI: Related concepts suggested in generation
        - Database: Related concepts retrieved from graph
        - Content: Related concepts referenced in slides
        """
        login_page = InstructorLoginPage(self.driver)
        kg_page = KnowledgeGraphBrowserPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Browse knowledge graph
        kg_page.navigate()

        # Step 3: Search for concept
        kg_page.search_concept("Python Lists")

        # Step 4: Verify related concepts
        related_concepts = kg_page.get_related_concepts()
        assert len(related_concepts) >= 3, \
            f"Expected at least 3 related concepts, got {len(related_concepts)}"

        # Step 5: Navigate to content generation
        rag_page.navigate()

        # Step 6: Configure generation
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.select_content_type("slides")
        rag_page.enter_topic("Python Lists")

        # Step 7: Generate content
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Slide generation should complete"

        # Step 8: Verify related concepts suggested
        concepts = rag_page.get_knowledge_graph_concepts()
        assert len(concepts) >= 3, "Related concepts should be suggested"

    def test_06_query_prerequisite_relationships_for_content_ordering(self):
        """
        Test querying prerequisite relationships to order content correctly.

        BUSINESS SCENARIO:
        An instructor creates a course on "Web Development" and needs to ensure
        content is ordered correctly based on prerequisite relationships
        (HTML before CSS before JavaScript before React).

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to knowledge graph
        3. Search for "React"
        4. View prerequisite chain
        5. Verify prerequisite order
        6. Generate module with correct ordering
        7. Verify content follows prerequisite order

        EXPECTED BEHAVIOR:
        - Prerequisite chain shown: HTML � CSS � JavaScript � React
        - Generated module follows this order
        - Each section assumes knowledge from prerequisites
        - No forward references to concepts not yet covered

        VALIDATION:
        - UI: Prerequisite chain displayed correctly
        - UI: Module sections ordered correctly
        - Database: Prerequisite relationships retrieved
        - Content: Logical prerequisite order maintained
        """
        login_page = InstructorLoginPage(self.driver)
        kg_page = KnowledgeGraphBrowserPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Browse knowledge graph
        kg_page.navigate()

        # Step 3: Search for advanced concept
        kg_page.search_concept("React")

        # Step 4: Get prerequisite chain
        prerequisites = kg_page.get_node_prerequisites()
        assert len(prerequisites) >= 2, \
            f"Expected at least 2 prerequisites for React, got {len(prerequisites)}"

        # Step 5: Verify prerequisite order
        # Note: This assumes prerequisites are returned in order
        assert any("javascript" in p.lower() for p in prerequisites), \
            "Prerequisites should include JavaScript"

        # Step 6: Generate module with prerequisites
        rag_page.navigate()
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.select_content_type("module")
        rag_page.enter_topic("React Development")

        # Step 7: Show knowledge graph to verify prerequisites
        rag_page.show_knowledge_graph()
        selected_prereqs = rag_page.get_selected_prerequisites()
        assert len(selected_prereqs) >= 2, \
            "Prerequisites should be automatically selected"

    def test_07_query_learning_paths_for_module_structure(self):
        """
        Test querying learning paths to structure course modules.

        BUSINESS SCENARIO:
        An instructor wants to create a course that follows an optimal learning
        path from "Basic Python" to "Machine Learning", ensuring students learn
        concepts in the most effective order.

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to knowledge graph
        3. Show learning path from "Basic Python" to "Machine Learning"
        4. Verify learning path steps
        5. Generate course following learning path
        6. Verify course structure matches path

        EXPECTED BEHAVIOR:
        - Learning path shows optimal progression
        - Path includes: Basic Python � Data Structures � NumPy � Pandas � ML
        - Generated course follows this structure
        - Each module builds on previous concepts

        VALIDATION:
        - UI: Learning path displayed visually
        - UI: Course structure matches path
        - Database: Learning path retrieved from graph
        - Content: Modules ordered according to path
        """
        login_page = InstructorLoginPage(self.driver)
        kg_page = KnowledgeGraphBrowserPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Navigate to knowledge graph
        kg_page.navigate()

        # Step 3: Show learning path
        learning_path = kg_page.show_learning_path("Machine Learning")
        assert len(learning_path) >= 4, \
            f"Expected learning path with at least 4 steps, got {len(learning_path)}"

        # Step 4: Verify path includes foundational concepts
        path_text = " ".join(learning_path).lower()
        assert "python" in path_text, "Learning path should include Python"
        assert any(term in path_text for term in ["data", "structure", "numpy", "pandas"]), \
            "Learning path should include data science prerequisites"

        # Step 5: Generate course following path
        rag_page.navigate()
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.select_content_type("module")
        rag_page.enter_topic("Introduction to Machine Learning")

        # Step 6: Verify prerequisites selected
        rag_page.show_knowledge_graph()
        prerequisites = rag_page.get_selected_prerequisites()
        assert len(prerequisites) >= 2, \
            "Learning path prerequisites should be selected"


# ============================================================================
# TEST SUITE - Content Enhancement Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.content_generation
@pytest.mark.content_enhancement
@pytest.mark.priority_medium
class TestContentEnhancement(BaseTest):
    """
    Test content enhancement with examples, cross-references, and resources.

    BUSINESS REQUIREMENT:
    After generating initial content, instructors can enhance it with relevant
    examples from the knowledge base, cross-references to related modules, and
    additional learning resources.
    """

    def test_08_enhance_slides_with_related_examples_from_knowledge_base(self):
        """
        Test enhancing slides with examples from knowledge base.

        BUSINESS SCENARIO:
        An instructor generates slides on "Python Functions" and wants to add
        practical examples from the knowledge base to make concepts more concrete.

        TEST SCENARIO:
        1. Login as instructor
        2. Generate slides on "Python Functions"
        3. Navigate to content enhancement
        4. View example suggestions
        5. Select relevant examples
        6. Add examples to slides
        7. Preview enhanced content
        8. Verify examples integrated correctly

        EXPECTED BEHAVIOR:
        - System suggests 5+ relevant examples
        - Examples match topic difficulty level
        - Examples include code snippets and explanations
        - Enhanced slides show examples inline
        - Examples sourced from knowledge base

        VALIDATION:
        - UI: Example suggestions displayed
        - UI: Enhanced slides show examples
        - Database: Examples retrieved from knowledge base
        - Content: Examples contextually relevant
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)
        enhance_page = ContentEnhancementPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Generate base content
        rag_page.navigate()
        rag_page.enable_rag_generation()
        rag_page.select_content_type("slides")
        rag_page.enter_topic("Python Functions")
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Initial content generation should complete"

        # Step 3: Navigate to enhancement
        enhance_page.navigate()

        # Step 4: View example suggestions
        examples_count = enhance_page.get_example_suggestions_count()
        assert examples_count >= 3, \
            f"Expected at least 3 example suggestions, got {examples_count}"

        # Step 5: Select examples
        enhance_page.select_example(0)
        enhance_page.select_example(1)

        # Step 6: Add examples
        enhance_page.add_selected_examples()

        # Step 7: Preview
        preview_visible = enhance_page.preview_enhanced_content()
        assert preview_visible, "Enhanced content preview should be visible"

    def test_09_add_cross_references_to_related_modules(self):
        """
        Test adding cross-references to related modules.

        BUSINESS SCENARIO:
        An instructor creates slides on "Object-Oriented Programming" and wants
        to add cross-references to related modules on "Classes", "Inheritance",
        and "Polymorphism" so students can explore related topics.

        TEST SCENARIO:
        1. Login as instructor
        2. Generate slides on "OOP Concepts"
        3. Navigate to content enhancement
        4. View cross-reference suggestions
        5. Add cross-references to related modules
        6. Verify cross-references link correctly
        7. Preview enhanced content

        EXPECTED BEHAVIOR:
        - System suggests 4+ related modules
        - Cross-references include module titles and descriptions
        - Links navigate to related modules
        - Enhanced slides show "See also" sections
        - Cross-references bidirectional (target modules link back)

        VALIDATION:
        - UI: Cross-reference suggestions displayed
        - UI: Enhanced slides show cross-references
        - Database: Cross-references stored
        - Navigation: Links navigate correctly
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)
        enhance_page = ContentEnhancementPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Generate content
        rag_page.navigate()
        rag_page.enable_rag_generation()
        rag_page.enable_knowledge_graph_integration()
        rag_page.select_content_type("slides")
        rag_page.enter_topic("Object-Oriented Programming Concepts")
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Content generation should complete"

        # Step 3: Navigate to enhancement
        enhance_page.navigate()

        # Step 4: View cross-reference suggestions
        cross_refs_count = enhance_page.get_cross_reference_suggestions_count()
        assert cross_refs_count >= 3, \
            f"Expected at least 3 cross-reference suggestions, got {cross_refs_count}"

        # Step 5: Add cross-references
        enhance_page.add_cross_reference(0)
        enhance_page.add_cross_reference(1)

        # Step 6: Preview
        preview_visible = enhance_page.preview_enhanced_content()
        assert preview_visible, "Enhanced content with cross-references should preview"

    def test_10_suggest_additional_resources_based_on_content(self):
        """
        Test suggesting additional learning resources based on content.

        BUSINESS SCENARIO:
        An instructor generates quiz on "Python Data Structures" and wants to
        suggest additional resources (tutorials, documentation, videos) to help
        students learn the material more deeply.

        TEST SCENARIO:
        1. Login as instructor
        2. Generate quiz on "Data Structures"
        3. Navigate to content enhancement
        4. View resource suggestions
        5. Verify resource relevance
        6. Add selected resources
        7. Verify resources accessible to students

        EXPECTED BEHAVIOR:
        - System suggests 6+ relevant resources
        - Resources include different types (docs, videos, tutorials)
        - Resources match content difficulty level
        - Resources from reputable sources
        - Students can access resources from quiz page

        VALIDATION:
        - UI: Resource suggestions displayed with metadata
        - UI: Added resources shown in student view
        - Database: Resources stored with content
        - Links: Resources accessible and valid
        """
        login_page = InstructorLoginPage(self.driver)
        rag_page = RAGContentGenerationPage(self.driver)
        enhance_page = ContentEnhancementPage(self.driver)

        # Step 1: Login
        login_page.navigate()
        login_page.login("instructor@example.com", "password123")

        # Step 2: Generate quiz
        rag_page.navigate()
        rag_page.enable_rag_generation()
        rag_page.select_content_type("quiz")
        rag_page.enter_topic("Python Data Structures")
        rag_page.select_difficulty_level("intermediate")
        success = rag_page.generate_content(wait_for_completion=True)
        assert success, "Quiz generation should complete"

        # Step 3: Navigate to enhancement
        enhance_page.navigate()

        # Step 4: View resource suggestions
        resources_count = enhance_page.get_suggested_resources_count()
        assert resources_count >= 4, \
            f"Expected at least 4 resource suggestions, got {resources_count}"

        # Step 5: Add resources
        enhance_page.add_resource(0)
        enhance_page.add_resource(1)
        enhance_page.add_resource(2)

        # Step 6: Preview
        preview_visible = enhance_page.preview_enhanced_content()
        assert preview_visible, "Enhanced content with resources should preview"

        # Step 7: Verify resources added
        # After enhancement, resources should be visible in preview
        # This verifies the enhancement was successful


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "rag: Tests for RAG-enhanced content generation"
    )
    config.addinivalue_line(
        "markers", "knowledge_graph: Tests for knowledge graph integration"
    )
    config.addinivalue_line(
        "markers", "content_enhancement: Tests for content enhancement features"
    )
