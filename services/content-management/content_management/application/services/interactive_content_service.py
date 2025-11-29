"""
Interactive Content Application Service

WHAT: Application service orchestrating interactive content business logic
WHERE: Used by API endpoints to handle interactive content operations
WHY: Implements business rules, validation, and coordination between
     domain entities and data access layer

This service provides operations for:
- Creating and managing interactive elements
- Content type-specific operations (simulations, drag-drop, etc.)
- Session tracking and analytics
- Evaluation and scoring
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from asyncpg import Pool

from content_management.domain.entities.interactive_content import (
    InteractiveElement,
    InteractiveContentType,
    InteractiveElementStatus,
    DifficultyLevel,
    CodeLanguage,
    Simulation,
    DragDropActivity,
    DragDropItem,
    DropZone,
    InteractiveDiagram,
    Hotspot,
    DiagramLayer,
    CodePlayground,
    BranchingScenario,
    ScenarioBranch,
    InteractiveTimeline,
    TimelineEvent,
    FlashcardDeck,
    Flashcard,
    InteractiveVideo,
    VideoInteraction,
    InteractionSession,
    InteractiveContentException,
    InvalidInteractiveStateException,
    InteractiveContentValidationException,
)
from data_access.interactive_content_dao import InteractiveContentDAO


class InteractiveContentServiceException(InteractiveContentException):
    """
    WHAT: Exception for service-level errors
    WHERE: Raised during business logic processing
    WHY: Wraps domain and DAO exceptions with service context
    """
    pass


class InteractiveContentService:
    """
    WHAT: Application service for interactive content operations
    WHERE: Called by API endpoints for business logic
    WHY: Orchestrates operations between presentation and data layers

    Attributes:
        dao: Data access object for persistence
        pool: Database connection pool
    """

    def __init__(self, pool: Pool):
        """
        WHAT: Initializes the service with database pool
        WHERE: Called during application startup
        WHY: Sets up dependencies for database operations

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.dao = InteractiveContentDAO(pool)

    # =========================================================================
    # Interactive Element Operations
    # =========================================================================

    async def create_interactive_element(
        self,
        title: str,
        description: str,
        content_type: InteractiveContentType,
        course_id: UUID,
        creator_id: UUID,
        module_id: Optional[UUID] = None,
        lesson_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        estimated_duration_minutes: int = 10,
        learning_objectives: Optional[List[str]] = None,
        max_attempts: int = 0,
        points_value: int = 10,
        tags: Optional[List[str]] = None
    ) -> InteractiveElement:
        """
        WHAT: Creates a new interactive element
        WHERE: Called when creating any interactive content
        WHY: Validates and persists the base element

        Args:
            title: Element title
            description: Element description
            content_type: Type of interactive content
            course_id: Parent course ID
            creator_id: ID of creating user
            module_id: Optional module ID
            lesson_id: Optional lesson ID
            organization_id: Optional organization ID
            difficulty_level: Content difficulty
            estimated_duration_minutes: Expected completion time
            learning_objectives: List of learning objectives
            max_attempts: Maximum attempts allowed (0 = unlimited)
            points_value: Points awarded for completion
            tags: Content tags

        Returns:
            Created InteractiveElement

        Raises:
            InteractiveContentServiceException: If creation fails
        """
        try:
            # Validate inputs
            if not title or len(title.strip()) == 0:
                raise InteractiveContentValidationException(
                    "Title is required",
                    {"field": "title"}
                )

            element = InteractiveElement(
                id=uuid4(),
                title=title.strip(),
                description=description or "",
                content_type=content_type,
                course_id=course_id,
                module_id=module_id,
                lesson_id=lesson_id,
                creator_id=creator_id,
                organization_id=organization_id,
                status=InteractiveElementStatus.DRAFT,
                version=1,
                difficulty_level=difficulty_level,
                estimated_duration_minutes=max(1, estimated_duration_minutes),
                learning_objectives=learning_objectives or [],
                max_attempts=max(0, max_attempts),
                points_value=max(0, points_value),
                tags=tags or []
            )

            return await self.dao.create_interactive_element(element)
        except InteractiveContentException:
            raise
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create interactive element: {str(e)}",
                {"content_type": content_type.value, "course_id": str(course_id)}
            )

    async def get_interactive_element(
        self,
        element_id: UUID
    ) -> Optional[InteractiveElement]:
        """
        WHAT: Retrieves an interactive element by ID
        WHERE: Called when loading content
        WHY: Provides element data for display or editing

        Args:
            element_id: UUID of the element

        Returns:
            InteractiveElement or None if not found
        """
        return await self.dao.get_interactive_element(element_id)

    async def get_course_interactive_content(
        self,
        course_id: UUID,
        content_type: Optional[InteractiveContentType] = None,
        status: Optional[InteractiveElementStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[InteractiveElement]:
        """
        WHAT: Lists interactive content for a course
        WHERE: Called when viewing course content
        WHY: Provides filtered list of interactive elements

        Args:
            course_id: UUID of the course
            content_type: Optional type filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of InteractiveElements
        """
        return await self.dao.get_elements_by_course(
            course_id, content_type, status, limit, offset
        )

    async def submit_for_review(
        self,
        element_id: UUID,
        reviewer_notes: Optional[str] = None
    ) -> InteractiveElement:
        """
        WHAT: Submits an element for review
        WHERE: Called when author completes draft
        WHY: Initiates review workflow

        Args:
            element_id: UUID of element to submit
            reviewer_notes: Optional notes for reviewer

        Returns:
            Updated InteractiveElement

        Raises:
            InteractiveContentServiceException: If submission fails
        """
        element = await self.dao.get_interactive_element(element_id)
        if not element:
            raise InteractiveContentServiceException(
                "Element not found",
                {"element_id": str(element_id)}
            )

        try:
            element.submit_for_review()
            if reviewer_notes:
                element.custom_properties["reviewer_notes"] = reviewer_notes
            return await self.dao.update_interactive_element(element)
        except InvalidInteractiveStateException as e:
            raise InteractiveContentServiceException(
                str(e),
                e.details
            )

    async def approve_element(
        self,
        element_id: UUID,
        approver_id: UUID
    ) -> InteractiveElement:
        """
        WHAT: Approves an element after review
        WHERE: Called by reviewer after quality check
        WHY: Marks content as ready for publishing

        Args:
            element_id: UUID of element to approve
            approver_id: ID of approving user

        Returns:
            Updated InteractiveElement
        """
        element = await self.dao.get_interactive_element(element_id)
        if not element:
            raise InteractiveContentServiceException(
                "Element not found",
                {"element_id": str(element_id)}
            )

        try:
            element.approve()
            element.custom_properties["approved_by"] = str(approver_id)
            element.custom_properties["approved_at"] = datetime.utcnow().isoformat()
            return await self.dao.update_interactive_element(element)
        except InvalidInteractiveStateException as e:
            raise InteractiveContentServiceException(str(e), e.details)

    async def publish_element(
        self,
        element_id: UUID
    ) -> InteractiveElement:
        """
        WHAT: Publishes an approved element
        WHERE: Called when making content available
        WHY: Makes content accessible to students

        Args:
            element_id: UUID of element to publish

        Returns:
            Updated InteractiveElement
        """
        element = await self.dao.get_interactive_element(element_id)
        if not element:
            raise InteractiveContentServiceException(
                "Element not found",
                {"element_id": str(element_id)}
            )

        try:
            element.publish()
            return await self.dao.update_interactive_element(element)
        except InvalidInteractiveStateException as e:
            raise InteractiveContentServiceException(str(e), e.details)

    async def archive_element(
        self,
        element_id: UUID
    ) -> InteractiveElement:
        """
        WHAT: Archives an element
        WHERE: Called when retiring content
        WHY: Preserves history while hiding from active use

        Args:
            element_id: UUID of element to archive

        Returns:
            Updated InteractiveElement
        """
        element = await self.dao.get_interactive_element(element_id)
        if not element:
            raise InteractiveContentServiceException(
                "Element not found",
                {"element_id": str(element_id)}
            )

        element.archive()
        return await self.dao.update_interactive_element(element)

    async def delete_element(
        self,
        element_id: UUID
    ) -> bool:
        """
        WHAT: Deletes an interactive element
        WHERE: Called when removing content
        WHY: Permanently removes element and related data

        Args:
            element_id: UUID of element to delete

        Returns:
            True if deleted
        """
        return await self.dao.delete_interactive_element(element_id)

    # =========================================================================
    # Simulation Operations
    # =========================================================================

    async def create_simulation(
        self,
        element_id: UUID,
        name: str,
        scenario_description: str,
        initial_state: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        expected_outcomes: Optional[List[Dict[str, Any]]] = None,
        simulation_type: str = "guided",
        time_limit_seconds: int = 0,
        guided_steps: Optional[List[Dict[str, Any]]] = None,
        passing_score: int = 70
    ) -> Simulation:
        """
        WHAT: Creates a simulation for an element
        WHERE: Called when adding simulation content
        WHY: Configures simulation behavior and outcomes

        Args:
            element_id: Parent element ID
            name: Simulation name
            scenario_description: Description of scenario
            initial_state: Starting state values
            parameters: Configurable parameters
            expected_outcomes: List of expected outcomes
            simulation_type: Type (guided/sandbox/challenge)
            time_limit_seconds: Time limit (0 = unlimited)
            guided_steps: Steps for guided mode
            passing_score: Score required to pass

        Returns:
            Created Simulation
        """
        try:
            simulation = Simulation(
                id=uuid4(),
                element_id=element_id,
                name=name,
                scenario_description=scenario_description,
                initial_state=initial_state or {},
                parameters=parameters or {},
                expected_outcomes=expected_outcomes or [],
                simulation_type=simulation_type,
                time_limit_seconds=max(0, time_limit_seconds),
                guided_steps=guided_steps or [],
                passing_score=max(0, min(100, passing_score))
            )

            return await self.dao.create_simulation(simulation)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create simulation: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_simulation(
        self,
        simulation_id: UUID
    ) -> Optional[Simulation]:
        """Gets a simulation by ID."""
        return await self.dao.get_simulation(simulation_id)

    async def get_simulation_by_element(
        self,
        element_id: UUID
    ) -> Optional[Simulation]:
        """Gets a simulation by element ID."""
        return await self.dao.get_simulation_by_element(element_id)

    async def evaluate_simulation(
        self,
        simulation_id: UUID,
        user_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates user's simulation results
        WHERE: Called when user completes simulation
        WHY: Determines success and calculates score

        Args:
            simulation_id: UUID of simulation
            user_state: User's final state

        Returns:
            Evaluation result with score and feedback
        """
        simulation = await self.dao.get_simulation(simulation_id)
        if not simulation:
            raise InteractiveContentServiceException(
                "Simulation not found",
                {"simulation_id": str(simulation_id)}
            )

        return simulation.validate_outcome(user_state)

    # =========================================================================
    # Drag-Drop Activity Operations
    # =========================================================================

    async def create_drag_drop_activity(
        self,
        element_id: UUID,
        activity_type: str,
        instructions: str,
        items: List[Dict[str, Any]],
        zones: List[Dict[str, Any]],
        shuffle_items: bool = True,
        partial_credit: bool = True
    ) -> DragDropActivity:
        """
        WHAT: Creates a drag-drop activity
        WHERE: Called when adding drag-drop content
        WHY: Configures interactive matching/sorting activity

        Args:
            element_id: Parent element ID
            activity_type: Type (categorize/match/order/sort)
            instructions: Activity instructions
            items: List of draggable items
            zones: List of drop zones
            shuffle_items: Whether to shuffle items
            partial_credit: Whether to award partial credit

        Returns:
            Created DragDropActivity
        """
        try:
            # Convert items to DragDropItem entities
            item_entities = []
            for i, item in enumerate(items):
                item_entities.append(DragDropItem(
                    id=uuid4(),
                    content=item.get("content", ""),
                    content_type=item.get("content_type", "text"),
                    image_url=item.get("image_url"),
                    correct_zone_ids=[UUID(z) for z in item.get("correct_zone_ids", [])],
                    feedback_correct=item.get("feedback_correct", ""),
                    feedback_incorrect=item.get("feedback_incorrect", ""),
                    points=item.get("points", 10),
                    order_index=item.get("order_index", i)
                ))

            # Convert zones to DropZone entities
            zone_entities = []
            for zone in zones:
                zone_entities.append(DropZone(
                    id=zone.get("id") if "id" in zone else uuid4(),
                    label=zone.get("label", ""),
                    description=zone.get("description", ""),
                    accepts_multiple=zone.get("accepts_multiple", False),
                    max_items=zone.get("max_items", 1),
                    position=zone.get("position", {}),
                    style=zone.get("style", {})
                ))

            # Update item correct_zone_ids with actual zone UUIDs
            zone_id_map = {str(z.id): z.id for z in zone_entities}

            activity = DragDropActivity(
                id=uuid4(),
                element_id=element_id,
                activity_type=activity_type,
                instructions=instructions,
                items=item_entities,
                zones=zone_entities,
                shuffle_items=shuffle_items,
                partial_credit=partial_credit
            )

            return await self.dao.create_drag_drop_activity(activity)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create drag-drop activity: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_drag_drop_activity(
        self,
        activity_id: UUID
    ) -> Optional[DragDropActivity]:
        """Gets a drag-drop activity by ID."""
        return await self.dao.get_drag_drop_activity(activity_id)

    async def evaluate_drag_drop(
        self,
        activity_id: UUID,
        placements: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates drag-drop submission
        WHERE: Called when user submits placements
        WHY: Determines correctness and score

        Args:
            activity_id: UUID of activity
            placements: Dict mapping zone_id to item_ids

        Returns:
            Evaluation result
        """
        activity = await self.dao.get_drag_drop_activity(activity_id)
        if not activity:
            raise InteractiveContentServiceException(
                "Activity not found",
                {"activity_id": str(activity_id)}
            )

        return activity.evaluate_submission(placements)

    # =========================================================================
    # Interactive Diagram Operations
    # =========================================================================

    async def create_interactive_diagram(
        self,
        element_id: UUID,
        title: str,
        base_image_url: str,
        layers: Optional[List[Dict[str, Any]]] = None,
        hotspots: Optional[List[Dict[str, Any]]] = None,
        guided_tour_enabled: bool = True,
        quiz_mode_enabled: bool = False,
        quiz_passing_score: int = 70
    ) -> InteractiveDiagram:
        """
        WHAT: Creates an interactive diagram
        WHERE: Called when adding diagram content
        WHY: Configures diagram with layers and hotspots

        Args:
            element_id: Parent element ID
            title: Diagram title
            base_image_url: URL of base image
            layers: Optional additional layers
            hotspots: Clickable hotspot definitions
            guided_tour_enabled: Enable guided tour mode
            quiz_mode_enabled: Enable quiz mode
            quiz_passing_score: Quiz passing score

        Returns:
            Created InteractiveDiagram
        """
        try:
            # Convert layers
            layer_entities = []
            if layers:
                for i, layer in enumerate(layers):
                    layer_entities.append(DiagramLayer(
                        id=uuid4(),
                        name=layer.get("name", f"Layer {i+1}"),
                        description=layer.get("description", ""),
                        image_url=layer.get("image_url", ""),
                        is_visible=layer.get("is_visible", True),
                        is_base_layer=layer.get("is_base_layer", False),
                        opacity=layer.get("opacity", 1.0),
                        order_index=layer.get("order_index", i)
                    ))

            # Convert hotspots
            hotspot_entities = []
            if hotspots:
                for i, hotspot in enumerate(hotspots):
                    hotspot_entities.append(Hotspot(
                        id=uuid4(),
                        label=hotspot.get("label", ""),
                        description=hotspot.get("description", ""),
                        shape=hotspot.get("shape", "circle"),
                        coordinates=hotspot.get("coordinates", {}),
                        popup_content=hotspot.get("popup_content", ""),
                        popup_media_url=hotspot.get("popup_media_url"),
                        is_quiz_point=hotspot.get("is_quiz_point", False),
                        quiz_question=hotspot.get("quiz_question"),
                        quiz_answer=hotspot.get("quiz_answer"),
                        style=hotspot.get("style", {}),
                        order_index=hotspot.get("order_index", i)
                    ))

            diagram = InteractiveDiagram(
                id=uuid4(),
                element_id=element_id,
                title=title,
                base_image_url=base_image_url,
                layers=layer_entities,
                hotspots=hotspot_entities,
                guided_tour_enabled=guided_tour_enabled,
                tour_hotspot_order=[h.id for h in hotspot_entities],
                quiz_mode_enabled=quiz_mode_enabled,
                quiz_passing_score=quiz_passing_score
            )

            return await self.dao.create_interactive_diagram(diagram)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create interactive diagram: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_interactive_diagram(
        self,
        diagram_id: UUID
    ) -> Optional[InteractiveDiagram]:
        """Gets an interactive diagram by ID."""
        return await self.dao.get_interactive_diagram(diagram_id)

    async def evaluate_diagram_quiz(
        self,
        diagram_id: UUID,
        answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates diagram quiz answers
        WHERE: Called when user submits quiz
        WHY: Scores the hotspot quiz

        Args:
            diagram_id: UUID of diagram
            answers: Dict mapping hotspot_id to answer

        Returns:
            Quiz evaluation result
        """
        diagram = await self.dao.get_interactive_diagram(diagram_id)
        if not diagram:
            raise InteractiveContentServiceException(
                "Diagram not found",
                {"diagram_id": str(diagram_id)}
            )

        return diagram.evaluate_quiz(answers)

    # =========================================================================
    # Code Playground Operations
    # =========================================================================

    async def create_code_playground(
        self,
        element_id: UUID,
        title: str,
        instructions: str,
        language: CodeLanguage,
        starter_code: str = "",
        solution_code: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: int = 30,
        passing_score: int = 70
    ) -> CodePlayground:
        """
        WHAT: Creates a code playground
        WHERE: Called when adding coding exercise
        WHY: Configures code editing and execution environment

        Args:
            element_id: Parent element ID
            title: Playground title
            instructions: Exercise instructions
            language: Programming language
            starter_code: Initial code template
            solution_code: Reference solution
            test_cases: List of test cases
            timeout_seconds: Execution timeout
            passing_score: Score required to pass

        Returns:
            Created CodePlayground
        """
        try:
            playground = CodePlayground(
                id=uuid4(),
                element_id=element_id,
                title=title,
                instructions=instructions,
                language=language,
                starter_code=starter_code,
                solution_code=solution_code,
                test_cases=test_cases or [],
                timeout_seconds=max(1, timeout_seconds),
                passing_score=max(0, min(100, passing_score))
            )

            return await self.dao.create_code_playground(playground)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create code playground: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_code_playground(
        self,
        playground_id: UUID
    ) -> Optional[CodePlayground]:
        """Gets a code playground by ID."""
        return await self.dao.get_code_playground(playground_id)

    async def evaluate_code_output(
        self,
        playground_id: UUID,
        outputs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates code execution outputs
        WHERE: Called after code execution
        WHY: Scores the coding exercise

        Args:
            playground_id: UUID of playground
            outputs: List of test outputs

        Returns:
            Evaluation result
        """
        playground = await self.dao.get_code_playground(playground_id)
        if not playground:
            raise InteractiveContentServiceException(
                "Playground not found",
                {"playground_id": str(playground_id)}
            )

        return playground.evaluate_output(outputs)

    # =========================================================================
    # Branching Scenario Operations
    # =========================================================================

    async def create_branching_scenario(
        self,
        element_id: UUID,
        title: str,
        introduction: str,
        branches: List[Dict[str, Any]],
        max_score: int = 100,
        passing_score: int = 70,
        allow_backtrack: bool = False,
        visual_style: str = "cards"
    ) -> BranchingScenario:
        """
        WHAT: Creates a branching scenario
        WHERE: Called when adding decision-tree content
        WHY: Configures scenario with multiple paths

        Args:
            element_id: Parent element ID
            title: Scenario title
            introduction: Opening text
            branches: List of branch definitions
            max_score: Maximum possible score
            passing_score: Score required to pass
            allow_backtrack: Allow going back
            visual_style: Visual presentation style

        Returns:
            Created BranchingScenario
        """
        try:
            # Convert branches
            branch_entities = []
            start_branch_id = None

            for branch in branches:
                branch_entity = ScenarioBranch(
                    id=UUID(branch["id"]) if "id" in branch else uuid4(),
                    content=branch.get("content", ""),
                    content_type=branch.get("content_type", "text"),
                    media_url=branch.get("media_url"),
                    options=branch.get("options", []),
                    is_start=branch.get("is_start", False),
                    is_end=branch.get("is_end", False),
                    is_success_end=branch.get("is_success_end", False),
                    is_failure_end=branch.get("is_failure_end", False),
                    points_value=branch.get("points_value", 0),
                    branch_feedback=branch.get("branch_feedback", "")
                )
                branch_entities.append(branch_entity)

                if branch_entity.is_start:
                    start_branch_id = branch_entity.id

            scenario = BranchingScenario(
                id=uuid4(),
                element_id=element_id,
                title=title,
                introduction=introduction,
                branches=branch_entities,
                start_branch_id=start_branch_id,
                max_score=max_score,
                passing_score=passing_score,
                allow_backtrack=allow_backtrack,
                visual_style=visual_style
            )

            return await self.dao.create_branching_scenario(scenario)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create branching scenario: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_branching_scenario(
        self,
        scenario_id: UUID
    ) -> Optional[BranchingScenario]:
        """Gets a branching scenario by ID."""
        return await self.dao.get_branching_scenario(scenario_id)

    async def evaluate_scenario_path(
        self,
        scenario_id: UUID,
        path: List[UUID],
        choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates the path through a scenario
        WHERE: Called when user completes scenario
        WHY: Scores the scenario completion

        Args:
            scenario_id: UUID of scenario
            path: List of branch IDs visited
            choices: List of choices made

        Returns:
            Evaluation result
        """
        scenario = await self.dao.get_branching_scenario(scenario_id)
        if not scenario:
            raise InteractiveContentServiceException(
                "Scenario not found",
                {"scenario_id": str(scenario_id)}
            )

        return scenario.evaluate_path(path, choices)

    # =========================================================================
    # Timeline Operations
    # =========================================================================

    async def create_interactive_timeline(
        self,
        element_id: UUID,
        title: str,
        description: str,
        events: List[Dict[str, Any]],
        time_scale: str = "years",
        categories: Optional[List[Dict[str, str]]] = None
    ) -> InteractiveTimeline:
        """
        WHAT: Creates an interactive timeline
        WHERE: Called when adding timeline content
        WHY: Configures chronological exploration

        Args:
            element_id: Parent element ID
            title: Timeline title
            description: Timeline description
            events: List of event definitions
            time_scale: Time scale (years/months/days/hours)
            categories: Optional event categories

        Returns:
            Created InteractiveTimeline
        """
        try:
            # Convert events
            event_entities = []
            for event in events:
                event_entities.append(TimelineEvent(
                    id=uuid4(),
                    title=event.get("title", ""),
                    description=event.get("description", ""),
                    date=event.get("date"),
                    date_display=event.get("date_display", ""),
                    content=event.get("content", ""),
                    content_type=event.get("content_type", "text"),
                    media_url=event.get("media_url"),
                    category=event.get("category", ""),
                    importance=event.get("importance", 1),
                    is_milestone=event.get("is_milestone", False),
                    icon=event.get("icon", ""),
                    color=event.get("color", "")
                ))

            timeline = InteractiveTimeline(
                id=uuid4(),
                element_id=element_id,
                title=title,
                description=description,
                events=event_entities,
                time_scale=time_scale,
                categories=categories or []
            )

            # Set date range from events
            if event_entities:
                timeline.start_date = min(e.date for e in event_entities)
                timeline.end_date = max(e.date for e in event_entities)

            return await self.dao.create_interactive_timeline(timeline)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create timeline: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_interactive_timeline(
        self,
        timeline_id: UUID
    ) -> Optional[InteractiveTimeline]:
        """Gets an interactive timeline by ID."""
        return await self.dao.get_interactive_timeline(timeline_id)

    # =========================================================================
    # Flashcard Deck Operations
    # =========================================================================

    async def create_flashcard_deck(
        self,
        element_id: UUID,
        name: str,
        description: str,
        cards: List[Dict[str, Any]],
        new_cards_per_day: int = 20,
        reviews_per_day: int = 100
    ) -> FlashcardDeck:
        """
        WHAT: Creates a flashcard deck
        WHERE: Called when adding flashcard content
        WHY: Configures deck with spaced repetition settings

        Args:
            element_id: Parent element ID
            name: Deck name
            description: Deck description
            cards: List of card definitions
            new_cards_per_day: Daily new card limit
            reviews_per_day: Daily review limit

        Returns:
            Created FlashcardDeck
        """
        try:
            # Convert cards
            card_entities = []
            for card in cards:
                card_entities.append(Flashcard(
                    id=uuid4(),
                    front_content=card.get("front_content", ""),
                    back_content=card.get("back_content", ""),
                    front_content_type=card.get("front_content_type", "text"),
                    back_content_type=card.get("back_content_type", "text"),
                    front_media_url=card.get("front_media_url"),
                    back_media_url=card.get("back_media_url"),
                    tags=card.get("tags", [])
                ))

            deck = FlashcardDeck(
                id=uuid4(),
                element_id=element_id,
                name=name,
                description=description,
                cards=card_entities,
                new_cards_per_day=max(1, new_cards_per_day),
                reviews_per_day=max(1, reviews_per_day)
            )

            return await self.dao.create_flashcard_deck(deck)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create flashcard deck: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_flashcard_deck(
        self,
        deck_id: UUID
    ) -> Optional[FlashcardDeck]:
        """Gets a flashcard deck by ID."""
        return await self.dao.get_flashcard_deck(deck_id)

    async def record_flashcard_review(
        self,
        deck_id: UUID,
        card_id: UUID,
        quality: int
    ) -> Flashcard:
        """
        WHAT: Records a flashcard review
        WHERE: Called after user reviews a card
        WHY: Updates spaced repetition scheduling

        Args:
            deck_id: UUID of deck
            card_id: UUID of card
            quality: Response quality (0-5)

        Returns:
            Updated Flashcard
        """
        deck = await self.dao.get_flashcard_deck(deck_id)
        if not deck:
            raise InteractiveContentServiceException(
                "Deck not found",
                {"deck_id": str(deck_id)}
            )

        # Find and update the card
        card = None
        for c in deck.cards:
            if c.id == card_id:
                card = c
                break

        if not card:
            raise InteractiveContentServiceException(
                "Card not found",
                {"card_id": str(card_id)}
            )

        # Update using spaced repetition algorithm
        card.update_spaced_repetition(max(0, min(5, quality)))

        # Persist the update
        return await self.dao.update_flashcard(card, deck_id)

    # =========================================================================
    # Interactive Video Operations
    # =========================================================================

    async def create_interactive_video(
        self,
        element_id: UUID,
        title: str,
        description: str,
        video_url: str,
        video_duration_seconds: float,
        interactions: Optional[List[Dict[str, Any]]] = None,
        chapters: Optional[List[Dict[str, Any]]] = None,
        watch_percentage_required: int = 80,
        passing_score: int = 70
    ) -> InteractiveVideo:
        """
        WHAT: Creates an interactive video
        WHERE: Called when adding video content
        WHY: Configures video with embedded interactions

        Args:
            element_id: Parent element ID
            title: Video title
            description: Video description
            video_url: URL of video file
            video_duration_seconds: Video length
            interactions: List of interaction definitions
            chapters: Optional chapter markers
            watch_percentage_required: Required watch percentage
            passing_score: Score required to pass

        Returns:
            Created InteractiveVideo
        """
        try:
            # Convert interactions
            interaction_entities = []
            if interactions:
                for interaction in interactions:
                    interaction_entities.append(VideoInteraction(
                        id=uuid4(),
                        timestamp_seconds=interaction.get("timestamp_seconds", 0),
                        interaction_type=interaction.get("interaction_type", "question"),
                        title=interaction.get("title", ""),
                        content=interaction.get("content", ""),
                        media_url=interaction.get("media_url"),
                        question=interaction.get("question"),
                        options=interaction.get("options", []),
                        correct_answer=interaction.get("correct_answer"),
                        explanation=interaction.get("explanation", ""),
                        points=interaction.get("points", 10),
                        pause_video=interaction.get("pause_video", True),
                        required=interaction.get("required", False),
                        skip_allowed=interaction.get("skip_allowed", True),
                        duration_seconds=interaction.get("duration_seconds", 0),
                        position=interaction.get("position", {}),
                        style=interaction.get("style", {})
                    ))

            video = InteractiveVideo(
                id=uuid4(),
                element_id=element_id,
                title=title,
                description=description,
                video_url=video_url,
                video_duration_seconds=video_duration_seconds,
                interactions=interaction_entities,
                chapters=chapters or [],
                watch_percentage_required=max(0, min(100, watch_percentage_required)),
                passing_score=max(0, min(100, passing_score))
            )

            return await self.dao.create_interactive_video(video)
        except Exception as e:
            raise InteractiveContentServiceException(
                f"Failed to create interactive video: {str(e)}",
                {"element_id": str(element_id)}
            )

    async def get_interactive_video(
        self,
        video_id: UUID
    ) -> Optional[InteractiveVideo]:
        """Gets an interactive video by ID."""
        return await self.dao.get_interactive_video(video_id)

    async def evaluate_video_session(
        self,
        video_id: UUID,
        watch_time_seconds: float,
        interaction_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates a video viewing session
        WHERE: Called when user completes video
        WHY: Determines completion and score

        Args:
            video_id: UUID of video
            watch_time_seconds: Total watch time
            interaction_responses: Answers to interactions

        Returns:
            Session evaluation result
        """
        video = await self.dao.get_interactive_video(video_id)
        if not video:
            raise InteractiveContentServiceException(
                "Video not found",
                {"video_id": str(video_id)}
            )

        return video.evaluate_session(watch_time_seconds, interaction_responses)

    # =========================================================================
    # Session Tracking Operations
    # =========================================================================

    async def start_interaction_session(
        self,
        element_id: UUID,
        user_id: UUID,
        device_type: str = "",
        browser: str = ""
    ) -> InteractionSession:
        """
        WHAT: Starts a new interaction session
        WHERE: Called when user begins interactive content
        WHY: Tracks user engagement for analytics

        Args:
            element_id: UUID of element
            user_id: UUID of user
            device_type: Type of device
            browser: Browser information

        Returns:
            Created InteractionSession
        """
        session = InteractionSession(
            id=uuid4(),
            element_id=element_id,
            user_id=user_id,
            device_type=device_type,
            browser=browser
        )

        return await self.dao.create_interaction_session(session)

    async def record_session_action(
        self,
        session_id: UUID,
        action_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> InteractionSession:
        """
        WHAT: Records an action in a session
        WHERE: Called during user interaction
        WHY: Enables detailed interaction analytics

        Args:
            session_id: UUID of session
            action_type: Type of action
            data: Optional action data

        Returns:
            Updated InteractionSession
        """
        session = await self.dao.get_interaction_session(session_id)
        if not session:
            raise InteractiveContentServiceException(
                "Session not found",
                {"session_id": str(session_id)}
            )

        session.record_action(action_type, data)
        return await self.dao.update_interaction_session(session)

    async def complete_session(
        self,
        session_id: UUID,
        score: float,
        passed: bool
    ) -> InteractionSession:
        """
        WHAT: Completes an interaction session
        WHERE: Called when user finishes interaction
        WHY: Finalizes session data for analytics

        Args:
            session_id: UUID of session
            score: Final score
            passed: Whether user passed

        Returns:
            Updated InteractionSession
        """
        session = await self.dao.get_interaction_session(session_id)
        if not session:
            raise InteractiveContentServiceException(
                "Session not found",
                {"session_id": str(session_id)}
            )

        session.complete(score, passed)

        # Also update the element analytics
        element = await self.dao.get_interactive_element(session.element_id)
        if element:
            element.record_attempt(True, score, session.duration_seconds)
            await self.dao.update_interactive_element(element)

        return await self.dao.update_interaction_session(session)

    async def abandon_session(
        self,
        session_id: UUID
    ) -> InteractionSession:
        """
        WHAT: Marks a session as abandoned
        WHERE: Called when user leaves without completing
        WHY: Tracks incomplete interactions

        Args:
            session_id: UUID of session

        Returns:
            Updated InteractionSession
        """
        session = await self.dao.get_interaction_session(session_id)
        if not session:
            raise InteractiveContentServiceException(
                "Session not found",
                {"session_id": str(session_id)}
            )

        session.abandon()
        return await self.dao.update_interaction_session(session)

    async def get_user_sessions(
        self,
        user_id: UUID,
        element_id: UUID,
        limit: int = 10
    ) -> List[InteractionSession]:
        """
        WHAT: Gets a user's sessions for an element
        WHERE: Called when viewing user progress
        WHY: Provides interaction history

        Args:
            user_id: UUID of user
            element_id: UUID of element
            limit: Maximum results

        Returns:
            List of InteractionSessions
        """
        return await self.dao.get_user_sessions_for_element(user_id, element_id, limit)

    # =========================================================================
    # Unified Content Operations
    # =========================================================================

    async def get_content_by_element(
        self,
        element_id: UUID
    ) -> Optional[Any]:
        """
        WHAT: Gets content type-specific data by element ID
        WHERE: Called when loading complete content
        WHY: Provides unified access to all content types

        Args:
            element_id: UUID of parent element

        Returns:
            The specific content entity or None
        """
        element = await self.dao.get_interactive_element(element_id)
        if not element:
            return None

        content_type = element.content_type

        if content_type == InteractiveContentType.SIMULATION:
            return await self.dao.get_simulation_by_element(element_id)
        elif content_type == InteractiveContentType.DRAG_DROP:
            return await self.dao.get_drag_drop_by_element(element_id)
        elif content_type == InteractiveContentType.INTERACTIVE_DIAGRAM:
            return await self.dao.get_diagram_by_element(element_id)
        elif content_type == InteractiveContentType.CODE_PLAYGROUND:
            return await self.dao.get_playground_by_element(element_id)
        elif content_type == InteractiveContentType.BRANCHING_SCENARIO:
            return await self.dao.get_scenario_by_element(element_id)
        elif content_type == InteractiveContentType.INTERACTIVE_TIMELINE:
            return await self.dao.get_timeline_by_element(element_id)
        elif content_type in (InteractiveContentType.FLASHCARD, InteractiveContentType.FLASHCARD_DECK):
            return await self.dao.get_deck_by_element(element_id)
        elif content_type == InteractiveContentType.INTERACTIVE_VIDEO:
            return await self.dao.get_video_by_element(element_id)

        return None
