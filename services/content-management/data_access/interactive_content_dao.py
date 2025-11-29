"""
Interactive Content Data Access Object (DAO)

WHAT: Data access layer for interactive content types
WHERE: Used by content-management service for all interactive content database operations
WHY: Provides abstraction over database operations following the DAO pattern,
     ensuring separation of concerns and maintainable data access logic

This module provides CRUD operations for:
- Interactive Elements (base entities)
- Simulations
- Drag-Drop Activities
- Interactive Diagrams
- Code Playgrounds
- Branching Scenarios
- Interactive Timelines
- Flashcard Decks and Flashcards
- Interactive Videos
- Interaction Sessions
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from asyncpg import Pool, Record, Connection

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
)


class InteractiveContentDAOException(InteractiveContentException):
    """
    WHAT: Exception for DAO-specific errors
    WHERE: Raised during database operations
    WHY: Wraps database errors with context for debugging
    """
    pass


class InteractiveContentDAO:
    """
    WHAT: Data Access Object for interactive content operations
    WHERE: Used by InteractiveContentService for persistence
    WHY: Encapsulates all database interactions following repository pattern

    Attributes:
        pool: AsyncPG connection pool for database operations
    """

    def __init__(self, pool: Pool):
        """
        WHAT: Initializes the DAO with a connection pool
        WHERE: Called during service initialization
        WHY: Provides database connectivity for all operations

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool

    # =========================================================================
    # Interactive Elements (Base)
    # =========================================================================

    async def create_interactive_element(
        self,
        element: InteractiveElement,
        conn: Optional[Connection] = None
    ) -> InteractiveElement:
        """
        WHAT: Creates a new interactive element in the database
        WHERE: Called when creating any interactive content
        WHY: Persists the base element that all content types reference

        Args:
            element: InteractiveElement to create
            conn: Optional connection for transaction support

        Returns:
            Created InteractiveElement with database-assigned values

        Raises:
            InteractiveContentDAOException: If creation fails
        """
        query = """
            INSERT INTO interactive_elements (
                id, title, description, content_type, course_id, module_id, lesson_id,
                creator_id, organization_id, status, version, difficulty_level,
                estimated_duration_minutes, learning_objectives, prerequisites,
                max_attempts, hints_enabled, feedback_immediate, allow_skip, points_value,
                accessibility_description, screen_reader_text, keyboard_navigable,
                high_contrast_available, total_attempts, total_completions,
                avg_completion_time_seconds, avg_score, engagement_score,
                tags, custom_properties, created_at, updated_at, published_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29,
                $30, $31, $32, $33, $34
            )
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                element.id,
                element.title,
                element.description,
                element.content_type.value,
                element.course_id,
                element.module_id,
                element.lesson_id,
                element.creator_id,
                element.organization_id,
                element.status.value,
                element.version,
                element.difficulty_level.value,
                element.estimated_duration_minutes,
                element.learning_objectives,
                [str(p) for p in element.prerequisites],
                element.max_attempts,
                element.hints_enabled,
                element.feedback_immediate,
                element.allow_skip,
                element.points_value,
                element.accessibility_description,
                element.screen_reader_text,
                element.keyboard_navigable,
                element.high_contrast_available,
                element.total_attempts,
                element.total_completions,
                element.avg_completion_time_seconds,
                element.avg_score,
                element.engagement_score,
                element.tags,
                json.dumps(element.custom_properties),
                element.created_at,
                element.updated_at,
                element.published_at
            )
            return self._row_to_interactive_element(row)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create interactive element: {str(e)}",
                {"element_id": str(element.id), "error": str(e)}
            )

    async def get_interactive_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveElement]:
        """
        WHAT: Retrieves an interactive element by ID
        WHERE: Called when loading any interactive content
        WHY: Provides access to base element data

        Args:
            element_id: UUID of the element
            conn: Optional connection

        Returns:
            InteractiveElement or None if not found
        """
        query = "SELECT * FROM interactive_elements WHERE id = $1"
        connection = conn or self.pool
        row = await connection.fetchrow(query, element_id)
        return self._row_to_interactive_element(row) if row else None

    async def get_elements_by_course(
        self,
        course_id: UUID,
        content_type: Optional[InteractiveContentType] = None,
        status: Optional[InteractiveElementStatus] = None,
        limit: int = 100,
        offset: int = 0,
        conn: Optional[Connection] = None
    ) -> List[InteractiveElement]:
        """
        WHAT: Retrieves interactive elements for a course
        WHERE: Called when listing course content
        WHY: Provides filtered list of interactive content

        Args:
            course_id: UUID of the course
            content_type: Optional filter by content type
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset
            conn: Optional connection

        Returns:
            List of InteractiveElements
        """
        query = """
            SELECT * FROM interactive_elements
            WHERE course_id = $1
        """
        params: List[Any] = [course_id]
        param_idx = 2

        if content_type:
            query += f" AND content_type = ${param_idx}"
            params.append(content_type.value)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status.value)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        connection = conn or self.pool
        rows = await connection.fetch(query, *params)
        return [self._row_to_interactive_element(row) for row in rows]

    async def update_interactive_element(
        self,
        element: InteractiveElement,
        conn: Optional[Connection] = None
    ) -> InteractiveElement:
        """
        WHAT: Updates an interactive element
        WHERE: Called when modifying element properties
        WHY: Persists element changes to database

        Args:
            element: InteractiveElement with updated values
            conn: Optional connection

        Returns:
            Updated InteractiveElement
        """
        query = """
            UPDATE interactive_elements SET
                title = $2, description = $3, status = $4, version = $5,
                difficulty_level = $6, estimated_duration_minutes = $7,
                learning_objectives = $8, prerequisites = $9, max_attempts = $10,
                hints_enabled = $11, feedback_immediate = $12, allow_skip = $13,
                points_value = $14, accessibility_description = $15,
                screen_reader_text = $16, keyboard_navigable = $17,
                high_contrast_available = $18, total_attempts = $19,
                total_completions = $20, avg_completion_time_seconds = $21,
                avg_score = $22, engagement_score = $23, tags = $24,
                custom_properties = $25, updated_at = $26, published_at = $27
            WHERE id = $1
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                element.id,
                element.title,
                element.description,
                element.status.value,
                element.version,
                element.difficulty_level.value,
                element.estimated_duration_minutes,
                element.learning_objectives,
                [str(p) for p in element.prerequisites],
                element.max_attempts,
                element.hints_enabled,
                element.feedback_immediate,
                element.allow_skip,
                element.points_value,
                element.accessibility_description,
                element.screen_reader_text,
                element.keyboard_navigable,
                element.high_contrast_available,
                element.total_attempts,
                element.total_completions,
                element.avg_completion_time_seconds,
                element.avg_score,
                element.engagement_score,
                element.tags,
                json.dumps(element.custom_properties),
                element.updated_at,
                element.published_at
            )
            return self._row_to_interactive_element(row)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to update interactive element: {str(e)}",
                {"element_id": str(element.id)}
            )

    async def delete_interactive_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> bool:
        """
        WHAT: Deletes an interactive element
        WHERE: Called when removing content
        WHY: Removes element and cascades to related tables

        Args:
            element_id: UUID of element to delete
            conn: Optional connection

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM interactive_elements WHERE id = $1"
        connection = conn or self.pool
        result = await connection.execute(query, element_id)
        return result == "DELETE 1"

    # =========================================================================
    # Simulations
    # =========================================================================

    async def create_simulation(
        self,
        simulation: Simulation,
        conn: Optional[Connection] = None
    ) -> Simulation:
        """
        WHAT: Creates a new simulation
        WHERE: Called when adding simulation content
        WHY: Persists simulation-specific data

        Args:
            simulation: Simulation to create
            conn: Optional connection

        Returns:
            Created Simulation
        """
        query = """
            INSERT INTO simulations (
                id, element_id, name, scenario_description, initial_state, parameters,
                expected_outcomes, simulation_type, time_limit_seconds, max_steps,
                allow_reset, save_checkpoints, guided_steps, show_hints,
                hint_penalty_percent, scoring_rubric, passing_score, partial_credit,
                is_active, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21
            )
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                simulation.id,
                simulation.element_id,
                simulation.name,
                simulation.scenario_description,
                json.dumps(simulation.initial_state),
                json.dumps(simulation.parameters),
                json.dumps(simulation.expected_outcomes),
                simulation.simulation_type,
                simulation.time_limit_seconds,
                simulation.max_steps,
                simulation.allow_reset,
                simulation.save_checkpoints,
                json.dumps(simulation.guided_steps),
                simulation.show_hints,
                simulation.hint_penalty_percent,
                json.dumps(simulation.scoring_rubric),
                simulation.passing_score,
                simulation.partial_credit,
                simulation.is_active,
                simulation.created_at,
                simulation.updated_at
            )
            return self._row_to_simulation(row)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create simulation: {str(e)}",
                {"simulation_id": str(simulation.id)}
            )

    async def get_simulation(
        self,
        simulation_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[Simulation]:
        """
        WHAT: Retrieves a simulation by ID
        WHERE: Called when loading simulation content
        WHY: Provides simulation data for display/execution

        Args:
            simulation_id: UUID of simulation
            conn: Optional connection

        Returns:
            Simulation or None
        """
        query = "SELECT * FROM simulations WHERE id = $1"
        connection = conn or self.pool
        row = await connection.fetchrow(query, simulation_id)
        return self._row_to_simulation(row) if row else None

    async def get_simulation_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[Simulation]:
        """
        WHAT: Retrieves a simulation by element ID
        WHERE: Called when loading content by element reference
        WHY: Links element to specific simulation data

        Args:
            element_id: UUID of parent element
            conn: Optional connection

        Returns:
            Simulation or None
        """
        query = "SELECT * FROM simulations WHERE element_id = $1"
        connection = conn or self.pool
        row = await connection.fetchrow(query, element_id)
        return self._row_to_simulation(row) if row else None

    async def update_simulation(
        self,
        simulation: Simulation,
        conn: Optional[Connection] = None
    ) -> Simulation:
        """
        WHAT: Updates a simulation
        WHERE: Called when modifying simulation properties
        WHY: Persists simulation changes

        Args:
            simulation: Simulation with updated values
            conn: Optional connection

        Returns:
            Updated Simulation
        """
        query = """
            UPDATE simulations SET
                name = $2, scenario_description = $3, initial_state = $4,
                parameters = $5, expected_outcomes = $6, simulation_type = $7,
                time_limit_seconds = $8, max_steps = $9, allow_reset = $10,
                save_checkpoints = $11, guided_steps = $12, show_hints = $13,
                hint_penalty_percent = $14, scoring_rubric = $15, passing_score = $16,
                partial_credit = $17, is_active = $18, updated_at = $19
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            simulation.id,
            simulation.name,
            simulation.scenario_description,
            json.dumps(simulation.initial_state),
            json.dumps(simulation.parameters),
            json.dumps(simulation.expected_outcomes),
            simulation.simulation_type,
            simulation.time_limit_seconds,
            simulation.max_steps,
            simulation.allow_reset,
            simulation.save_checkpoints,
            json.dumps(simulation.guided_steps),
            simulation.show_hints,
            simulation.hint_penalty_percent,
            json.dumps(simulation.scoring_rubric),
            simulation.passing_score,
            simulation.partial_credit,
            simulation.is_active,
            simulation.updated_at
        )
        return self._row_to_simulation(row)

    # =========================================================================
    # Drag-Drop Activities
    # =========================================================================

    async def create_drag_drop_activity(
        self,
        activity: DragDropActivity,
        conn: Optional[Connection] = None
    ) -> DragDropActivity:
        """
        WHAT: Creates a drag-drop activity
        WHERE: Called when adding drag-drop content
        WHY: Persists activity and associated items/zones

        Args:
            activity: DragDropActivity to create
            conn: Optional connection

        Returns:
            Created DragDropActivity
        """
        query = """
            INSERT INTO drag_drop_activities (
                id, element_id, activity_type, instructions, shuffle_items,
                shuffle_zones, show_item_count_per_zone, allow_reorder,
                snap_to_zone, show_correct_placement, show_feedback_on_drop,
                show_feedback_on_submit, partial_credit, deduct_for_incorrect,
                deduction_percent, item_style, zone_style, is_active,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20
            )
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    # Create main activity
                    row = await connection.fetchrow(
                        query,
                        activity.id,
                        activity.element_id,
                        activity.activity_type,
                        activity.instructions,
                        activity.shuffle_items,
                        activity.shuffle_zones,
                        activity.show_item_count_per_zone,
                        activity.allow_reorder,
                        activity.snap_to_zone,
                        activity.show_correct_placement,
                        activity.show_feedback_on_drop,
                        activity.show_feedback_on_submit,
                        activity.partial_credit,
                        activity.deduct_for_incorrect,
                        activity.deduction_percent,
                        json.dumps(activity.item_style),
                        json.dumps(activity.zone_style),
                        activity.is_active,
                        activity.created_at,
                        activity.updated_at
                    )

                    # Create items
                    for item in activity.items:
                        await self._create_drag_drop_item(item, activity.id, connection)

                    # Create zones
                    for zone in activity.zones:
                        await self._create_drop_zone(zone, activity.id, connection)

                    return self._row_to_drag_drop_activity(row, activity.items, activity.zones)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create drag-drop activity: {str(e)}",
                {"activity_id": str(activity.id)}
            )

    async def _create_drag_drop_item(
        self,
        item: DragDropItem,
        activity_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a drag-drop item."""
        query = """
            INSERT INTO drag_drop_items (
                id, activity_id, content, content_type, image_url,
                correct_zone_ids, feedback_correct, feedback_incorrect,
                points, order_index
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        await conn.execute(
            query,
            item.id,
            activity_id,
            item.content,
            item.content_type,
            item.image_url,
            [str(z) for z in item.correct_zone_ids],
            item.feedback_correct,
            item.feedback_incorrect,
            item.points,
            item.order_index
        )

    async def _create_drop_zone(
        self,
        zone: DropZone,
        activity_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a drop zone."""
        query = """
            INSERT INTO drop_zones (
                id, activity_id, label, description, accepts_multiple,
                max_items, position, style
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        await conn.execute(
            query,
            zone.id,
            activity_id,
            zone.label,
            zone.description,
            zone.accepts_multiple,
            zone.max_items,
            json.dumps(zone.position),
            json.dumps(zone.style)
        )

    async def get_drag_drop_activity(
        self,
        activity_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[DragDropActivity]:
        """
        WHAT: Retrieves a drag-drop activity with items and zones
        WHERE: Called when loading drag-drop content
        WHY: Provides complete activity data for display

        Args:
            activity_id: UUID of activity
            conn: Optional connection

        Returns:
            DragDropActivity with items and zones, or None
        """
        connection = conn or self.pool

        # Get activity
        activity_row = await connection.fetchrow(
            "SELECT * FROM drag_drop_activities WHERE id = $1", activity_id
        )
        if not activity_row:
            return None

        # Get items
        items_rows = await connection.fetch(
            "SELECT * FROM drag_drop_items WHERE activity_id = $1 ORDER BY order_index", activity_id
        )
        items = [self._row_to_drag_drop_item(row) for row in items_rows]

        # Get zones
        zones_rows = await connection.fetch(
            "SELECT * FROM drop_zones WHERE activity_id = $1", activity_id
        )
        zones = [self._row_to_drop_zone(row) for row in zones_rows]

        return self._row_to_drag_drop_activity(activity_row, items, zones)

    async def get_drag_drop_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[DragDropActivity]:
        """Gets drag-drop activity by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM drag_drop_activities WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_drag_drop_activity(row['id'], conn)
        return None

    # =========================================================================
    # Interactive Diagrams
    # =========================================================================

    async def create_interactive_diagram(
        self,
        diagram: InteractiveDiagram,
        conn: Optional[Connection] = None
    ) -> InteractiveDiagram:
        """
        WHAT: Creates an interactive diagram with layers and hotspots
        WHERE: Called when adding diagram content
        WHY: Persists diagram and associated components

        Args:
            diagram: InteractiveDiagram to create
            conn: Optional connection

        Returns:
            Created InteractiveDiagram
        """
        query = """
            INSERT INTO interactive_diagrams (
                id, element_id, title, base_image_url, zoom_enabled, pan_enabled,
                min_zoom, max_zoom, guided_tour_enabled, tour_hotspot_order,
                tour_auto_advance_seconds, quiz_mode_enabled, quiz_passing_score,
                highlight_on_hover, show_labels, label_position, is_active,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19
            )
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        query,
                        diagram.id,
                        diagram.element_id,
                        diagram.title,
                        diagram.base_image_url,
                        diagram.zoom_enabled,
                        diagram.pan_enabled,
                        diagram.min_zoom,
                        diagram.max_zoom,
                        diagram.guided_tour_enabled,
                        [str(h) for h in diagram.tour_hotspot_order],
                        diagram.tour_auto_advance_seconds,
                        diagram.quiz_mode_enabled,
                        diagram.quiz_passing_score,
                        diagram.highlight_on_hover,
                        diagram.show_labels,
                        diagram.label_position,
                        diagram.is_active,
                        diagram.created_at,
                        diagram.updated_at
                    )

                    # Create layers
                    for layer in diagram.layers:
                        await self._create_diagram_layer(layer, diagram.id, connection)

                    # Create hotspots
                    for hotspot in diagram.hotspots:
                        await self._create_hotspot(hotspot, diagram.id, connection)

                    return self._row_to_interactive_diagram(row, diagram.layers, diagram.hotspots)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create interactive diagram: {str(e)}",
                {"diagram_id": str(diagram.id)}
            )

    async def _create_diagram_layer(
        self,
        layer: DiagramLayer,
        diagram_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a diagram layer."""
        query = """
            INSERT INTO diagram_layers (
                id, diagram_id, name, description, image_url, is_visible,
                is_base_layer, opacity, order_index
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        await conn.execute(
            query,
            layer.id,
            diagram_id,
            layer.name,
            layer.description,
            layer.image_url,
            layer.is_visible,
            layer.is_base_layer,
            layer.opacity,
            layer.order_index
        )

    async def _create_hotspot(
        self,
        hotspot: Hotspot,
        diagram_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a diagram hotspot."""
        query = """
            INSERT INTO hotspots (
                id, diagram_id, label, description, shape, coordinates,
                popup_content, popup_media_url, linked_content_id, is_quiz_point,
                quiz_question, quiz_answer, style, order_index
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """
        await conn.execute(
            query,
            hotspot.id,
            diagram_id,
            hotspot.label,
            hotspot.description,
            hotspot.shape,
            json.dumps(hotspot.coordinates),
            hotspot.popup_content,
            hotspot.popup_media_url,
            hotspot.linked_content_id,
            hotspot.is_quiz_point,
            hotspot.quiz_question,
            hotspot.quiz_answer,
            json.dumps(hotspot.style),
            hotspot.order_index
        )

    async def get_interactive_diagram(
        self,
        diagram_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveDiagram]:
        """
        WHAT: Retrieves an interactive diagram with all components
        WHERE: Called when loading diagram content
        WHY: Provides complete diagram data for display

        Args:
            diagram_id: UUID of diagram
            conn: Optional connection

        Returns:
            InteractiveDiagram with layers and hotspots, or None
        """
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM interactive_diagrams WHERE id = $1", diagram_id
        )
        if not row:
            return None

        layers_rows = await connection.fetch(
            "SELECT * FROM diagram_layers WHERE diagram_id = $1 ORDER BY order_index",
            diagram_id
        )
        layers = [self._row_to_diagram_layer(r) for r in layers_rows]

        hotspots_rows = await connection.fetch(
            "SELECT * FROM hotspots WHERE diagram_id = $1 ORDER BY order_index",
            diagram_id
        )
        hotspots = [self._row_to_hotspot(r) for r in hotspots_rows]

        return self._row_to_interactive_diagram(row, layers, hotspots)

    async def get_diagram_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveDiagram]:
        """Gets diagram by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM interactive_diagrams WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_interactive_diagram(row['id'], conn)
        return None

    # =========================================================================
    # Code Playgrounds
    # =========================================================================

    async def create_code_playground(
        self,
        playground: CodePlayground,
        conn: Optional[Connection] = None
    ) -> CodePlayground:
        """
        WHAT: Creates a code playground
        WHERE: Called when adding coding exercise content
        WHY: Persists playground configuration and test cases

        Args:
            playground: CodePlayground to create
            conn: Optional connection

        Returns:
            Created CodePlayground
        """
        query = """
            INSERT INTO code_playgrounds (
                id, element_id, title, instructions, language, language_version,
                starter_code, solution_code, test_code, hidden_test_code,
                timeout_seconds, memory_limit_mb, allowed_imports, blocked_imports,
                test_cases, show_expected_output, show_test_cases, allow_solution_view,
                auto_run_on_change, passing_score, partial_credit, is_active,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
            )
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                playground.id,
                playground.element_id,
                playground.title,
                playground.instructions,
                playground.language.value,
                playground.language_version,
                playground.starter_code,
                playground.solution_code,
                playground.test_code,
                playground.hidden_test_code,
                playground.timeout_seconds,
                playground.memory_limit_mb,
                playground.allowed_imports,
                playground.blocked_imports,
                json.dumps(playground.test_cases),
                playground.show_expected_output,
                playground.show_test_cases,
                playground.allow_solution_view,
                playground.auto_run_on_change,
                playground.passing_score,
                playground.partial_credit,
                playground.is_active,
                playground.created_at,
                playground.updated_at
            )
            return self._row_to_code_playground(row)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create code playground: {str(e)}",
                {"playground_id": str(playground.id)}
            )

    async def get_code_playground(
        self,
        playground_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[CodePlayground]:
        """Gets a code playground by ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM code_playgrounds WHERE id = $1", playground_id
        )
        return self._row_to_code_playground(row) if row else None

    async def get_playground_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[CodePlayground]:
        """Gets code playground by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM code_playgrounds WHERE element_id = $1", element_id
        )
        return self._row_to_code_playground(row) if row else None

    async def update_code_playground(
        self,
        playground: CodePlayground,
        conn: Optional[Connection] = None
    ) -> CodePlayground:
        """Updates a code playground."""
        query = """
            UPDATE code_playgrounds SET
                title = $2, instructions = $3, language = $4, language_version = $5,
                starter_code = $6, solution_code = $7, test_code = $8,
                hidden_test_code = $9, timeout_seconds = $10, memory_limit_mb = $11,
                allowed_imports = $12, blocked_imports = $13, test_cases = $14,
                show_expected_output = $15, show_test_cases = $16,
                allow_solution_view = $17, auto_run_on_change = $18,
                passing_score = $19, partial_credit = $20, is_active = $21,
                updated_at = $22
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            playground.id,
            playground.title,
            playground.instructions,
            playground.language.value,
            playground.language_version,
            playground.starter_code,
            playground.solution_code,
            playground.test_code,
            playground.hidden_test_code,
            playground.timeout_seconds,
            playground.memory_limit_mb,
            playground.allowed_imports,
            playground.blocked_imports,
            json.dumps(playground.test_cases),
            playground.show_expected_output,
            playground.show_test_cases,
            playground.allow_solution_view,
            playground.auto_run_on_change,
            playground.passing_score,
            playground.partial_credit,
            playground.is_active,
            playground.updated_at
        )
        return self._row_to_code_playground(row)

    # =========================================================================
    # Branching Scenarios
    # =========================================================================

    async def create_branching_scenario(
        self,
        scenario: BranchingScenario,
        conn: Optional[Connection] = None
    ) -> BranchingScenario:
        """
        WHAT: Creates a branching scenario with branches
        WHERE: Called when adding scenario content
        WHY: Persists scenario and decision tree structure

        Args:
            scenario: BranchingScenario to create
            conn: Optional connection

        Returns:
            Created BranchingScenario
        """
        query = """
            INSERT INTO branching_scenarios (
                id, element_id, title, introduction, start_branch_id, max_score,
                passing_score, track_path, allow_backtrack, show_path_on_complete,
                show_optimal_path, visual_style, show_progress, is_active,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        query,
                        scenario.id,
                        scenario.element_id,
                        scenario.title,
                        scenario.introduction,
                        scenario.start_branch_id,
                        scenario.max_score,
                        scenario.passing_score,
                        scenario.track_path,
                        scenario.allow_backtrack,
                        scenario.show_path_on_complete,
                        scenario.show_optimal_path,
                        scenario.visual_style,
                        scenario.show_progress,
                        scenario.is_active,
                        scenario.created_at,
                        scenario.updated_at
                    )

                    # Create branches
                    for branch in scenario.branches:
                        await self._create_scenario_branch(branch, scenario.id, connection)

                    return self._row_to_branching_scenario(row, scenario.branches)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create branching scenario: {str(e)}",
                {"scenario_id": str(scenario.id)}
            )

    async def _create_scenario_branch(
        self,
        branch: ScenarioBranch,
        scenario_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a scenario branch."""
        query = """
            INSERT INTO scenario_branches (
                id, scenario_id, content, content_type, media_url, options,
                is_start, is_end, is_success_end, is_failure_end, points_value,
                branch_feedback, style
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        await conn.execute(
            query,
            branch.id,
            scenario_id,
            branch.content,
            branch.content_type,
            branch.media_url,
            json.dumps(branch.options),
            branch.is_start,
            branch.is_end,
            branch.is_success_end,
            branch.is_failure_end,
            branch.points_value,
            branch.branch_feedback,
            json.dumps(branch.style)
        )

    async def get_branching_scenario(
        self,
        scenario_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[BranchingScenario]:
        """Gets a branching scenario with all branches."""
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM branching_scenarios WHERE id = $1", scenario_id
        )
        if not row:
            return None

        branches_rows = await connection.fetch(
            "SELECT * FROM scenario_branches WHERE scenario_id = $1", scenario_id
        )
        branches = [self._row_to_scenario_branch(r) for r in branches_rows]

        return self._row_to_branching_scenario(row, branches)

    async def get_scenario_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[BranchingScenario]:
        """Gets branching scenario by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM branching_scenarios WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_branching_scenario(row['id'], conn)
        return None

    # =========================================================================
    # Interactive Timelines
    # =========================================================================

    async def create_interactive_timeline(
        self,
        timeline: InteractiveTimeline,
        conn: Optional[Connection] = None
    ) -> InteractiveTimeline:
        """Creates an interactive timeline with events."""
        query = """
            INSERT INTO interactive_timelines (
                id, element_id, title, description, start_date, end_date,
                time_scale, categories, zoom_enabled, filter_by_category,
                show_milestones_only, comparison_mode, orientation, event_density,
                show_event_images, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        query,
                        timeline.id,
                        timeline.element_id,
                        timeline.title,
                        timeline.description,
                        timeline.start_date,
                        timeline.end_date,
                        timeline.time_scale,
                        json.dumps(timeline.categories),
                        timeline.zoom_enabled,
                        timeline.filter_by_category,
                        timeline.show_milestones_only,
                        timeline.comparison_mode,
                        timeline.orientation,
                        timeline.event_density,
                        timeline.show_event_images,
                        timeline.is_active,
                        timeline.created_at,
                        timeline.updated_at
                    )

                    for event in timeline.events:
                        await self._create_timeline_event(event, timeline.id, connection)

                    return self._row_to_interactive_timeline(row, timeline.events)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create timeline: {str(e)}",
                {"timeline_id": str(timeline.id)}
            )

    async def _create_timeline_event(
        self,
        event: TimelineEvent,
        timeline_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a timeline event."""
        query = """
            INSERT INTO timeline_events (
                id, timeline_id, title, description, event_date, date_display,
                content, content_type, media_url, category, importance,
                is_milestone, linked_content_ids, icon, color, style
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        """
        await conn.execute(
            query,
            event.id,
            timeline_id,
            event.title,
            event.description,
            event.date,
            event.date_display,
            event.content,
            event.content_type,
            event.media_url,
            event.category,
            event.importance,
            event.is_milestone,
            [str(c) for c in event.linked_content_ids],
            event.icon,
            event.color,
            json.dumps(event.style)
        )

    async def get_interactive_timeline(
        self,
        timeline_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveTimeline]:
        """Gets an interactive timeline with events."""
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM interactive_timelines WHERE id = $1", timeline_id
        )
        if not row:
            return None

        events_rows = await connection.fetch(
            "SELECT * FROM timeline_events WHERE timeline_id = $1 ORDER BY event_date",
            timeline_id
        )
        events = [self._row_to_timeline_event(r) for r in events_rows]

        return self._row_to_interactive_timeline(row, events)

    async def get_timeline_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveTimeline]:
        """Gets timeline by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM interactive_timelines WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_interactive_timeline(row['id'], conn)
        return None

    # =========================================================================
    # Flashcard Decks
    # =========================================================================

    async def create_flashcard_deck(
        self,
        deck: FlashcardDeck,
        conn: Optional[Connection] = None
    ) -> FlashcardDeck:
        """Creates a flashcard deck with cards."""
        query = """
            INSERT INTO flashcard_decks (
                id, element_id, name, description, new_cards_per_day,
                reviews_per_day, shuffle_new, shuffle_review, show_remaining,
                flip_animation, auto_flip_seconds, total_reviews, correct_reviews,
                streak_days, last_study_date, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        query,
                        deck.id,
                        deck.element_id,
                        deck.name,
                        deck.description,
                        deck.new_cards_per_day,
                        deck.reviews_per_day,
                        deck.shuffle_new,
                        deck.shuffle_review,
                        deck.show_remaining,
                        deck.flip_animation,
                        deck.auto_flip_seconds,
                        deck.total_reviews,
                        deck.correct_reviews,
                        deck.streak_days,
                        deck.last_study_date,
                        deck.is_active,
                        deck.created_at,
                        deck.updated_at
                    )

                    for card in deck.cards:
                        await self._create_flashcard(card, deck.id, connection)

                    return self._row_to_flashcard_deck(row, deck.cards)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create flashcard deck: {str(e)}",
                {"deck_id": str(deck.id)}
            )

    async def _create_flashcard(
        self,
        card: Flashcard,
        deck_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a flashcard."""
        query = """
            INSERT INTO flashcards (
                id, deck_id, front_content, back_content, front_content_type,
                back_content_type, front_media_url, back_media_url, difficulty,
                interval_days, repetitions, next_review, last_reviewed,
                times_correct, times_incorrect, tags
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        """
        await conn.execute(
            query,
            card.id,
            deck_id,
            card.front_content,
            card.back_content,
            card.front_content_type,
            card.back_content_type,
            card.front_media_url,
            card.back_media_url,
            card.difficulty,
            card.interval_days,
            card.repetitions,
            card.next_review,
            card.last_reviewed,
            card.times_correct,
            card.times_incorrect,
            card.tags
        )

    async def get_flashcard_deck(
        self,
        deck_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[FlashcardDeck]:
        """Gets a flashcard deck with cards."""
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM flashcard_decks WHERE id = $1", deck_id
        )
        if not row:
            return None

        cards_rows = await connection.fetch(
            "SELECT * FROM flashcards WHERE deck_id = $1", deck_id
        )
        cards = [self._row_to_flashcard(r) for r in cards_rows]

        return self._row_to_flashcard_deck(row, cards)

    async def get_deck_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[FlashcardDeck]:
        """Gets flashcard deck by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM flashcard_decks WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_flashcard_deck(row['id'], conn)
        return None

    async def update_flashcard(
        self,
        card: Flashcard,
        deck_id: UUID,
        conn: Optional[Connection] = None
    ) -> Flashcard:
        """Updates a flashcard (for spaced repetition)."""
        query = """
            UPDATE flashcards SET
                difficulty = $2, interval_days = $3, repetitions = $4,
                next_review = $5, last_reviewed = $6, times_correct = $7,
                times_incorrect = $8, updated_at = NOW()
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            card.id,
            card.difficulty,
            card.interval_days,
            card.repetitions,
            card.next_review,
            card.last_reviewed,
            card.times_correct,
            card.times_incorrect
        )
        return self._row_to_flashcard(row)

    # =========================================================================
    # Interactive Videos
    # =========================================================================

    async def create_interactive_video(
        self,
        video: InteractiveVideo,
        conn: Optional[Connection] = None
    ) -> InteractiveVideo:
        """Creates an interactive video with interactions."""
        query = """
            INSERT INTO interactive_videos (
                id, element_id, title, description, video_url, video_duration_seconds,
                thumbnail_url, chapters, transcript_url, captions_url, show_transcript,
                allow_skip_interactions, require_all_interactions, allow_playback_speed,
                allow_seek, watch_percentage_required, interactions_percentage_required,
                passing_score, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
            RETURNING *
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        query,
                        video.id,
                        video.element_id,
                        video.title,
                        video.description,
                        video.video_url,
                        video.video_duration_seconds,
                        video.thumbnail_url,
                        json.dumps(video.chapters),
                        video.transcript_url,
                        video.captions_url,
                        video.show_transcript,
                        video.allow_skip_interactions,
                        video.require_all_interactions,
                        video.allow_playback_speed,
                        video.allow_seek,
                        video.watch_percentage_required,
                        video.interactions_percentage_required,
                        video.passing_score,
                        video.is_active,
                        video.created_at,
                        video.updated_at
                    )

                    for interaction in video.interactions:
                        await self._create_video_interaction(interaction, video.id, connection)

                    return self._row_to_interactive_video(row, video.interactions)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create interactive video: {str(e)}",
                {"video_id": str(video.id)}
            )

    async def _create_video_interaction(
        self,
        interaction: VideoInteraction,
        video_id: UUID,
        conn: Connection
    ) -> None:
        """Creates a video interaction."""
        query = """
            INSERT INTO video_interactions (
                id, video_id, timestamp_seconds, interaction_type, title, content,
                media_url, question, options, correct_answer, explanation, points,
                pause_video, required, skip_allowed, duration_seconds, position, style
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        """
        await conn.execute(
            query,
            interaction.id,
            video_id,
            interaction.timestamp_seconds,
            interaction.interaction_type,
            interaction.title,
            interaction.content,
            interaction.media_url,
            interaction.question,
            json.dumps(interaction.options),
            interaction.correct_answer,
            interaction.explanation,
            interaction.points,
            interaction.pause_video,
            interaction.required,
            interaction.skip_allowed,
            interaction.duration_seconds,
            json.dumps(interaction.position),
            json.dumps(interaction.style)
        )

    async def get_interactive_video(
        self,
        video_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveVideo]:
        """Gets an interactive video with interactions."""
        connection = conn or self.pool

        row = await connection.fetchrow(
            "SELECT * FROM interactive_videos WHERE id = $1", video_id
        )
        if not row:
            return None

        interactions_rows = await connection.fetch(
            "SELECT * FROM video_interactions WHERE video_id = $1 ORDER BY timestamp_seconds",
            video_id
        )
        interactions = [self._row_to_video_interaction(r) for r in interactions_rows]

        return self._row_to_interactive_video(row, interactions)

    async def get_video_by_element(
        self,
        element_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractiveVideo]:
        """Gets interactive video by element ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT id FROM interactive_videos WHERE element_id = $1", element_id
        )
        if row:
            return await self.get_interactive_video(row['id'], conn)
        return None

    # =========================================================================
    # Interaction Sessions
    # =========================================================================

    async def create_interaction_session(
        self,
        session: InteractionSession,
        conn: Optional[Connection] = None
    ) -> InteractionSession:
        """Creates an interaction session for tracking."""
        query = """
            INSERT INTO interaction_sessions (
                id, element_id, user_id, started_at, ended_at, duration_seconds,
                status, completion_percentage, score, max_score, passed, attempts,
                hints_used, actions_count, state_data, actions, device_type, browser
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        try:
            connection = conn or self.pool
            row = await connection.fetchrow(
                query,
                session.id,
                session.element_id,
                session.user_id,
                session.started_at,
                session.ended_at,
                session.duration_seconds,
                session.status,
                session.completion_percentage,
                session.score,
                session.max_score,
                session.passed,
                session.attempts,
                session.hints_used,
                session.actions_count,
                json.dumps(session.state_data),
                json.dumps(session.actions),
                session.device_type,
                session.browser
            )
            return self._row_to_interaction_session(row)
        except Exception as e:
            raise InteractiveContentDAOException(
                f"Failed to create interaction session: {str(e)}",
                {"session_id": str(session.id)}
            )

    async def get_interaction_session(
        self,
        session_id: UUID,
        conn: Optional[Connection] = None
    ) -> Optional[InteractionSession]:
        """Gets an interaction session by ID."""
        connection = conn or self.pool
        row = await connection.fetchrow(
            "SELECT * FROM interaction_sessions WHERE id = $1", session_id
        )
        return self._row_to_interaction_session(row) if row else None

    async def get_user_sessions_for_element(
        self,
        user_id: UUID,
        element_id: UUID,
        limit: int = 10,
        conn: Optional[Connection] = None
    ) -> List[InteractionSession]:
        """Gets a user's sessions for a specific element."""
        query = """
            SELECT * FROM interaction_sessions
            WHERE user_id = $1 AND element_id = $2
            ORDER BY started_at DESC
            LIMIT $3
        """
        connection = conn or self.pool
        rows = await connection.fetch(query, user_id, element_id, limit)
        return [self._row_to_interaction_session(row) for row in rows]

    async def update_interaction_session(
        self,
        session: InteractionSession,
        conn: Optional[Connection] = None
    ) -> InteractionSession:
        """Updates an interaction session."""
        query = """
            UPDATE interaction_sessions SET
                ended_at = $2, duration_seconds = $3, status = $4,
                completion_percentage = $5, score = $6, passed = $7,
                hints_used = $8, actions_count = $9, state_data = $10, actions = $11
            WHERE id = $1
            RETURNING *
        """
        connection = conn or self.pool
        row = await connection.fetchrow(
            query,
            session.id,
            session.ended_at,
            session.duration_seconds,
            session.status,
            session.completion_percentage,
            session.score,
            session.passed,
            session.hints_used,
            session.actions_count,
            json.dumps(session.state_data),
            json.dumps(session.actions)
        )
        return self._row_to_interaction_session(row)

    # =========================================================================
    # Row Conversion Helpers
    # =========================================================================

    def _row_to_interactive_element(self, row: Record) -> InteractiveElement:
        """Converts database row to InteractiveElement entity."""
        return InteractiveElement(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            content_type=InteractiveContentType(row['content_type']),
            course_id=row['course_id'],
            module_id=row['module_id'],
            lesson_id=row['lesson_id'],
            creator_id=row['creator_id'],
            organization_id=row['organization_id'],
            status=InteractiveElementStatus(row['status']),
            version=row['version'],
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            estimated_duration_minutes=row['estimated_duration_minutes'],
            learning_objectives=row['learning_objectives'] or [],
            prerequisites=[UUID(p) for p in (row['prerequisites'] or [])],
            max_attempts=row['max_attempts'],
            hints_enabled=row['hints_enabled'],
            feedback_immediate=row['feedback_immediate'],
            allow_skip=row['allow_skip'],
            points_value=row['points_value'],
            accessibility_description=row['accessibility_description'] or '',
            screen_reader_text=row['screen_reader_text'] or '',
            keyboard_navigable=row['keyboard_navigable'],
            high_contrast_available=row['high_contrast_available'],
            total_attempts=row['total_attempts'],
            total_completions=row['total_completions'],
            avg_completion_time_seconds=row['avg_completion_time_seconds'],
            avg_score=row['avg_score'],
            engagement_score=row['engagement_score'],
            tags=row['tags'] or [],
            custom_properties=json.loads(row['custom_properties']) if row['custom_properties'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            published_at=row['published_at']
        )

    def _row_to_simulation(self, row: Record) -> Simulation:
        """Converts database row to Simulation entity."""
        return Simulation(
            id=row['id'],
            element_id=row['element_id'],
            name=row['name'],
            scenario_description=row['scenario_description'],
            initial_state=json.loads(row['initial_state']) if row['initial_state'] else {},
            parameters=json.loads(row['parameters']) if row['parameters'] else {},
            expected_outcomes=json.loads(row['expected_outcomes']) if row['expected_outcomes'] else [],
            simulation_type=row['simulation_type'],
            time_limit_seconds=row['time_limit_seconds'],
            max_steps=row['max_steps'],
            allow_reset=row['allow_reset'],
            save_checkpoints=row['save_checkpoints'],
            guided_steps=json.loads(row['guided_steps']) if row['guided_steps'] else [],
            show_hints=row['show_hints'],
            hint_penalty_percent=row['hint_penalty_percent'],
            scoring_rubric=json.loads(row['scoring_rubric']) if row['scoring_rubric'] else {},
            passing_score=row['passing_score'],
            partial_credit=row['partial_credit'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_drag_drop_activity(
        self,
        row: Record,
        items: List[DragDropItem],
        zones: List[DropZone]
    ) -> DragDropActivity:
        """Converts database row to DragDropActivity entity."""
        return DragDropActivity(
            id=row['id'],
            element_id=row['element_id'],
            activity_type=row['activity_type'],
            instructions=row['instructions'],
            items=items,
            zones=zones,
            shuffle_items=row['shuffle_items'],
            shuffle_zones=row['shuffle_zones'],
            show_item_count_per_zone=row['show_item_count_per_zone'],
            allow_reorder=row['allow_reorder'],
            snap_to_zone=row['snap_to_zone'],
            show_correct_placement=row['show_correct_placement'],
            show_feedback_on_drop=row['show_feedback_on_drop'],
            show_feedback_on_submit=row['show_feedback_on_submit'],
            partial_credit=row['partial_credit'],
            deduct_for_incorrect=row['deduct_for_incorrect'],
            deduction_percent=row['deduction_percent'],
            item_style=json.loads(row['item_style']) if row['item_style'] else {},
            zone_style=json.loads(row['zone_style']) if row['zone_style'] else {},
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_drag_drop_item(self, row: Record) -> DragDropItem:
        """Converts database row to DragDropItem entity."""
        return DragDropItem(
            id=row['id'],
            content=row['content'],
            content_type=row['content_type'],
            image_url=row['image_url'],
            correct_zone_ids=[UUID(z) for z in (row['correct_zone_ids'] or [])],
            feedback_correct=row['feedback_correct'] or '',
            feedback_incorrect=row['feedback_incorrect'] or '',
            points=row['points'],
            order_index=row['order_index']
        )

    def _row_to_drop_zone(self, row: Record) -> DropZone:
        """Converts database row to DropZone entity."""
        return DropZone(
            id=row['id'],
            label=row['label'],
            description=row['description'] or '',
            accepts_multiple=row['accepts_multiple'],
            max_items=row['max_items'],
            position=json.loads(row['position']) if row['position'] else {},
            style=json.loads(row['style']) if row['style'] else {}
        )

    def _row_to_interactive_diagram(
        self,
        row: Record,
        layers: List[DiagramLayer],
        hotspots: List[Hotspot]
    ) -> InteractiveDiagram:
        """Converts database row to InteractiveDiagram entity."""
        return InteractiveDiagram(
            id=row['id'],
            element_id=row['element_id'],
            title=row['title'],
            base_image_url=row['base_image_url'],
            layers=layers,
            hotspots=hotspots,
            zoom_enabled=row['zoom_enabled'],
            pan_enabled=row['pan_enabled'],
            min_zoom=row['min_zoom'],
            max_zoom=row['max_zoom'],
            guided_tour_enabled=row['guided_tour_enabled'],
            tour_hotspot_order=[UUID(h) for h in (row['tour_hotspot_order'] or [])],
            tour_auto_advance_seconds=row['tour_auto_advance_seconds'],
            quiz_mode_enabled=row['quiz_mode_enabled'],
            quiz_passing_score=row['quiz_passing_score'],
            highlight_on_hover=row['highlight_on_hover'],
            show_labels=row['show_labels'],
            label_position=row['label_position'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_diagram_layer(self, row: Record) -> DiagramLayer:
        """Converts database row to DiagramLayer entity."""
        return DiagramLayer(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            image_url=row['image_url'],
            is_visible=row['is_visible'],
            is_base_layer=row['is_base_layer'],
            opacity=row['opacity'],
            order_index=row['order_index']
        )

    def _row_to_hotspot(self, row: Record) -> Hotspot:
        """Converts database row to Hotspot entity."""
        return Hotspot(
            id=row['id'],
            label=row['label'],
            description=row['description'] or '',
            shape=row['shape'],
            coordinates=json.loads(row['coordinates']) if row['coordinates'] else {},
            popup_content=row['popup_content'] or '',
            popup_media_url=row['popup_media_url'],
            linked_content_id=row['linked_content_id'],
            is_quiz_point=row['is_quiz_point'],
            quiz_question=row['quiz_question'],
            quiz_answer=row['quiz_answer'],
            style=json.loads(row['style']) if row['style'] else {},
            order_index=row['order_index']
        )

    def _row_to_code_playground(self, row: Record) -> CodePlayground:
        """Converts database row to CodePlayground entity."""
        return CodePlayground(
            id=row['id'],
            element_id=row['element_id'],
            title=row['title'],
            instructions=row['instructions'],
            language=CodeLanguage(row['language']),
            language_version=row['language_version'],
            starter_code=row['starter_code'] or '',
            solution_code=row['solution_code'] or '',
            test_code=row['test_code'] or '',
            hidden_test_code=row['hidden_test_code'] or '',
            timeout_seconds=row['timeout_seconds'],
            memory_limit_mb=row['memory_limit_mb'],
            allowed_imports=row['allowed_imports'] or [],
            blocked_imports=row['blocked_imports'] or [],
            test_cases=json.loads(row['test_cases']) if row['test_cases'] else [],
            show_expected_output=row['show_expected_output'],
            show_test_cases=row['show_test_cases'],
            allow_solution_view=row['allow_solution_view'],
            auto_run_on_change=row['auto_run_on_change'],
            passing_score=row['passing_score'],
            partial_credit=row['partial_credit'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_branching_scenario(
        self,
        row: Record,
        branches: List[ScenarioBranch]
    ) -> BranchingScenario:
        """Converts database row to BranchingScenario entity."""
        return BranchingScenario(
            id=row['id'],
            element_id=row['element_id'],
            title=row['title'],
            introduction=row['introduction'],
            branches=branches,
            start_branch_id=row['start_branch_id'],
            max_score=row['max_score'],
            passing_score=row['passing_score'],
            track_path=row['track_path'],
            allow_backtrack=row['allow_backtrack'],
            show_path_on_complete=row['show_path_on_complete'],
            show_optimal_path=row['show_optimal_path'],
            visual_style=row['visual_style'],
            show_progress=row['show_progress'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_scenario_branch(self, row: Record) -> ScenarioBranch:
        """Converts database row to ScenarioBranch entity."""
        return ScenarioBranch(
            id=row['id'],
            content=row['content'],
            content_type=row['content_type'],
            media_url=row['media_url'],
            options=json.loads(row['options']) if row['options'] else [],
            is_start=row['is_start'],
            is_end=row['is_end'],
            is_success_end=row['is_success_end'],
            is_failure_end=row['is_failure_end'],
            points_value=row['points_value'],
            branch_feedback=row['branch_feedback'] or '',
            style=json.loads(row['style']) if row['style'] else {}
        )

    def _row_to_interactive_timeline(
        self,
        row: Record,
        events: List[TimelineEvent]
    ) -> InteractiveTimeline:
        """Converts database row to InteractiveTimeline entity."""
        return InteractiveTimeline(
            id=row['id'],
            element_id=row['element_id'],
            title=row['title'],
            description=row['description'] or '',
            events=events,
            start_date=row['start_date'],
            end_date=row['end_date'],
            time_scale=row['time_scale'],
            categories=json.loads(row['categories']) if row['categories'] else [],
            zoom_enabled=row['zoom_enabled'],
            filter_by_category=row['filter_by_category'],
            show_milestones_only=row['show_milestones_only'],
            comparison_mode=row['comparison_mode'],
            orientation=row['orientation'],
            event_density=row['event_density'],
            show_event_images=row['show_event_images'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_timeline_event(self, row: Record) -> TimelineEvent:
        """Converts database row to TimelineEvent entity."""
        return TimelineEvent(
            id=row['id'],
            title=row['title'],
            description=row['description'] or '',
            date=row['event_date'],
            date_display=row['date_display'] or '',
            content=row['content'] or '',
            content_type=row['content_type'],
            media_url=row['media_url'],
            category=row['category'] or '',
            importance=row['importance'],
            is_milestone=row['is_milestone'],
            linked_content_ids=[UUID(c) for c in (row['linked_content_ids'] or [])],
            icon=row['icon'] or '',
            color=row['color'] or '',
            style=json.loads(row['style']) if row['style'] else {}
        )

    def _row_to_flashcard_deck(
        self,
        row: Record,
        cards: List[Flashcard]
    ) -> FlashcardDeck:
        """Converts database row to FlashcardDeck entity."""
        return FlashcardDeck(
            id=row['id'],
            element_id=row['element_id'],
            name=row['name'],
            description=row['description'] or '',
            cards=cards,
            new_cards_per_day=row['new_cards_per_day'],
            reviews_per_day=row['reviews_per_day'],
            shuffle_new=row['shuffle_new'],
            shuffle_review=row['shuffle_review'],
            show_remaining=row['show_remaining'],
            flip_animation=row['flip_animation'],
            auto_flip_seconds=row['auto_flip_seconds'],
            total_reviews=row['total_reviews'],
            correct_reviews=row['correct_reviews'],
            streak_days=row['streak_days'],
            last_study_date=row['last_study_date'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_flashcard(self, row: Record) -> Flashcard:
        """Converts database row to Flashcard entity."""
        return Flashcard(
            id=row['id'],
            front_content=row['front_content'],
            back_content=row['back_content'],
            front_content_type=row['front_content_type'],
            back_content_type=row['back_content_type'],
            front_media_url=row['front_media_url'],
            back_media_url=row['back_media_url'],
            difficulty=row['difficulty'],
            interval_days=row['interval_days'],
            repetitions=row['repetitions'],
            next_review=row['next_review'],
            last_reviewed=row['last_reviewed'],
            times_correct=row['times_correct'],
            times_incorrect=row['times_incorrect'],
            tags=row['tags'] or []
        )

    def _row_to_interactive_video(
        self,
        row: Record,
        interactions: List[VideoInteraction]
    ) -> InteractiveVideo:
        """Converts database row to InteractiveVideo entity."""
        return InteractiveVideo(
            id=row['id'],
            element_id=row['element_id'],
            title=row['title'],
            description=row['description'] or '',
            video_url=row['video_url'],
            video_duration_seconds=row['video_duration_seconds'],
            thumbnail_url=row['thumbnail_url'],
            interactions=interactions,
            chapters=json.loads(row['chapters']) if row['chapters'] else [],
            transcript_url=row['transcript_url'],
            captions_url=row['captions_url'],
            show_transcript=row['show_transcript'],
            allow_skip_interactions=row['allow_skip_interactions'],
            require_all_interactions=row['require_all_interactions'],
            allow_playback_speed=row['allow_playback_speed'],
            allow_seek=row['allow_seek'],
            watch_percentage_required=row['watch_percentage_required'],
            interactions_percentage_required=row['interactions_percentage_required'],
            passing_score=row['passing_score'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_video_interaction(self, row: Record) -> VideoInteraction:
        """Converts database row to VideoInteraction entity."""
        return VideoInteraction(
            id=row['id'],
            timestamp_seconds=row['timestamp_seconds'],
            interaction_type=row['interaction_type'],
            title=row['title'] or '',
            content=row['content'] or '',
            media_url=row['media_url'],
            question=row['question'],
            options=json.loads(row['options']) if row['options'] else [],
            correct_answer=row['correct_answer'],
            explanation=row['explanation'] or '',
            points=row['points'],
            pause_video=row['pause_video'],
            required=row['required'],
            skip_allowed=row['skip_allowed'],
            duration_seconds=row['duration_seconds'],
            position=json.loads(row['position']) if row['position'] else {},
            style=json.loads(row['style']) if row['style'] else {}
        )

    def _row_to_interaction_session(self, row: Record) -> InteractionSession:
        """Converts database row to InteractionSession entity."""
        return InteractionSession(
            id=row['id'],
            element_id=row['element_id'],
            user_id=row['user_id'],
            started_at=row['started_at'],
            ended_at=row['ended_at'],
            duration_seconds=row['duration_seconds'],
            status=row['status'],
            completion_percentage=row['completion_percentage'],
            score=row['score'],
            max_score=row['max_score'],
            passed=row['passed'],
            attempts=row['attempts'],
            hints_used=row['hints_used'],
            actions_count=row['actions_count'],
            state_data=json.loads(row['state_data']) if row['state_data'] else {},
            actions=json.loads(row['actions']) if row['actions'] else [],
            device_type=row['device_type'] or '',
            browser=row['browser'] or ''
        )
