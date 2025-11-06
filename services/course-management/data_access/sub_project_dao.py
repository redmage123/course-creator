"""
Sub-Project Data Access Object (DAO)

BUSINESS CONTEXT:
Provides data access layer for sub-projects (locations) with support for
locations-based filtering, date range queries, and capacity management.
Handles all database operations for hierarchical project structures.

TECHNICAL IMPLEMENTATION:
- Uses PostgreSQL with psycopg2
- Supports complex filtering (locations, dates, status)
- Implements participant count tracking
- Handles status lifecycle transitions

@module sub_project_dao
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor

from course_management.domain.entities.sub_project import SubProject
from course_management.infrastructure.exceptions import (
    SubProjectNotFoundException,
    DuplicateSubProjectException,
    InvalidLocationException,
    InvalidDateRangeException,
    SubProjectCapacityException,
    DatabaseQueryException
)

logger = logging.getLogger(__name__)


class SubProjectDAO:
    """
    Data Access Object for Sub-Projects

    BUSINESS VALUE:
    - Enables multi-locations program management
    - Supports complex locations filtering
    - Tracks capacity across locations
    - Maintains referential integrity

    USAGE:
    ```python
    dao = SubProjectDAO(db_connection)
    sub_project = dao.create_sub_project(data)
    locations = dao.get_sub_projects_by_parent(project_id, filters={'location_country': 'USA'})
    ```
    """

    def __init__(self, db_connection):
        """
        Initialize DAO with database connection

        Args:
            db_connection: psycopg2 database connection
        """
        self.conn = db_connection

    def create_sub_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new sub-project

        BUSINESS LOGIC:
        - Validates locations data (country required)
        - Validates date range (start <= end)
        - Auto-generates UUID if not provided
        - Auto-calculates duration from dates (via trigger)
        - Enforces unique slug per organization and parent project

        Args:
            data: Sub-project data dictionary

        Returns:
            Created sub-project as dictionary

        Raises:
            InvalidLocationException: If locations data is invalid
            InvalidDateRangeException: If date range is invalid
            DuplicateSubProjectException: If slug already exists
        """
        # Validate locations
        if not data.get('location_country'):
            raise InvalidLocationException("location_country is required")

        # Validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise InvalidDateRangeException(start_date, end_date)

        query = """
            INSERT INTO sub_projects (
                parent_project_id, organization_id, name, slug, description,
                location_country, location_region, location_city,
                location_address, timezone,
                start_date, end_date, duration_weeks,
                max_participants, current_participants,
                status, created_by, metadata
            ) VALUES (
                %(parent_project_id)s, %(organization_id)s, %(name)s, %(slug)s, %(description)s,
                %(location_country)s, %(location_region)s, %(location_city)s,
                %(location_address)s, %(timezone)s,
                %(start_date)s, %(end_date)s, %(duration_weeks)s,
                %(max_participants)s, %(current_participants)s,
                %(status)s, %(created_by)s, %(metadata)s
            )
            RETURNING *
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, {
                    'parent_project_id': str(data['parent_project_id']),
                    'organization_id': str(data['organization_id']),
                    'name': data['name'],
                    'slug': data['slug'],
                    'description': data.get('description'),
                    'location_country': data['location_country'],
                    'location_region': data.get('location_region'),
                    'location_city': data.get('location_city'),
                    'location_address': data.get('location_address'),
                    'timezone': data.get('timezone', 'UTC'),
                    'start_date': data.get('start_date'),
                    'end_date': data.get('end_date'),
                    'duration_weeks': data.get('duration_weeks'),
                    'max_participants': data.get('max_participants'),
                    'current_participants': data.get('current_participants', 0),
                    'status': data.get('status', 'draft'),
                    'created_by': str(data['created_by']) if data.get('created_by') else None,
                    'metadata': psycopg2.extras.Json(data.get('metadata', {}))
                })
                result = cursor.fetchone()
                self.conn.commit()
                logger.info(f"Created sub-project: {result['id']}")
                return dict(result)

        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if 'sub_projects_unique' in str(e):
                raise DuplicateSubProjectException(data['slug'])
            raise DatabaseQueryException(query, str(e))

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating sub-project: {e}")
            raise DatabaseQueryException(query, str(e))

    def get_sub_project_by_id(self, sub_project_id: str) -> Dict[str, Any]:
        """
        Retrieve sub-project by ID

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            Sub-project as dictionary

        Raises:
            SubProjectNotFoundException: If not found
        """
        query = """
            SELECT *
            FROM sub_projects
            WHERE id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (str(sub_project_id),))
                result = cursor.fetchone()

                if not result:
                    raise SubProjectNotFoundException(sub_project_id)

                return dict(result)

        except SubProjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving sub-project: {e}")
            raise DatabaseQueryException(query, str(e))

    def get_sub_projects_by_parent(
        self,
        parent_project_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sub-projects for a parent project with optional filtering

        FILTERING OPTIONS:
        - location_country: Filter by country
        - location_region: Filter by region
        - location_city: Filter by city (partial match)
        - status: Filter by status
        - start_date_from: Locations starting on or after this date
        - start_date_to: Locations starting on or before this date

        Args:
            parent_project_id: UUID of parent project
            filters: Optional filtering criteria

        Returns:
            List of sub-projects as dictionaries
        """
        filters = filters or {}

        # Build dynamic query with filters
        query = "SELECT * FROM sub_projects WHERE parent_project_id = %s"
        params = [str(parent_project_id)]

        if filters.get('location_country'):
            query += " AND location_country = %s"
            params.append(filters['location_country'])

        if filters.get('location_region'):
            query += " AND location_region = %s"
            params.append(filters['location_region'])

        if filters.get('location_city'):
            query += " AND location_city ILIKE %s"
            params.append(f"%{filters['location_city']}%")

        if filters.get('status'):
            query += " AND status = %s"
            params.append(filters['status'])

        if filters.get('start_date_from'):
            query += " AND start_date >= %s"
            params.append(filters['start_date_from'])

        if filters.get('start_date_to'):
            query += " AND start_date <= %s"
            params.append(filters['start_date_to'])

        query += " ORDER BY start_date DESC, created_at DESC"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error retrieving sub-projects: {e}")
            raise DatabaseQueryException(query, str(e))

    def update_sub_project(self, sub_project_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing sub-project

        BUSINESS LOGIC:
        - Validates dates if provided
        - Updates updated_at timestamp (via trigger)
        - Maintains audit trail

        Args:
            sub_project_id: UUID of sub-project to update
            data: Dictionary of fields to update

        Returns:
            True if updated successfully

        Raises:
            SubProjectNotFoundException: If sub-project not found
            InvalidDateRangeException: If date range is invalid
        """
        # Validate dates if both provided
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] and data['end_date'] and data['start_date'] > data['end_date']:
                raise InvalidDateRangeException(data['start_date'], data['end_date'])

        # Build dynamic UPDATE query
        set_clauses = []
        params = []

        for key, value in data.items():
            if key not in ['id', 'parent_project_id', 'organization_id', 'created_at', 'created_by']:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return True  # Nothing to update

        query = f"""
            UPDATE sub_projects
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        params.append(str(sub_project_id))

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()

                if cursor.rowcount == 0:
                    raise SubProjectNotFoundException(sub_project_id)

                logger.info(f"Updated sub-project: {sub_project_id}")
                return True

        except SubProjectNotFoundException:
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating sub-project: {e}")
            raise DatabaseQueryException(query, str(e))

    def delete_sub_project(self, sub_project_id: str) -> bool:
        """
        Delete a sub-project

        BUSINESS LOGIC:
        - Cascades to sub_project_tracks (handled by DB constraint)
        - Removes all enrollment references (handled by application layer)

        Args:
            sub_project_id: UUID of sub-project to delete

        Returns:
            True if deleted successfully

        Raises:
            SubProjectNotFoundException: If not found
        """
        query = "DELETE FROM sub_projects WHERE id = %s"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(sub_project_id),))
                self.conn.commit()

                if cursor.rowcount == 0:
                    raise SubProjectNotFoundException(sub_project_id)

                logger.info(f"Deleted sub-project: {sub_project_id}")
                return True

        except SubProjectNotFoundException:
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error deleting sub-project: {e}")
            raise DatabaseQueryException(query, str(e))

    def increment_participant_count(self, sub_project_id: str) -> Dict[str, Any]:
        """
        Increment participant count for sub-project

        BUSINESS LOGIC:
        - Checks capacity before incrementing
        - Raises exception if at capacity
        - Returns updated counts

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            Dictionary with current_participants and max_participants

        Raises:
            SubProjectCapacityException: If at capacity
            SubProjectNotFoundException: If not found
        """
        # First check current capacity
        check_query = """
            SELECT current_participants, max_participants
            FROM sub_projects
            WHERE id = %s
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(check_query, (str(sub_project_id),))
                result = cursor.fetchone()

                if not result:
                    raise SubProjectNotFoundException(sub_project_id)

                current = result['current_participants']
                max_capacity = result['max_participants']

                # Check capacity
                if max_capacity is not None and current >= max_capacity:
                    raise SubProjectCapacityException(current, max_capacity)

                # Increment
                update_query = """
                    UPDATE sub_projects
                    SET current_participants = current_participants + 1
                    WHERE id = %s
                """
                cursor.execute(update_query, (str(sub_project_id),))
                self.conn.commit()

                return {'current_participants': current + 1, 'max_participants': max_capacity}

        except (SubProjectNotFoundException, SubProjectCapacityException):
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error incrementing participant count: {e}")
            raise DatabaseQueryException(check_query, str(e))

    def decrement_participant_count(self, sub_project_id: str) -> bool:
        """
        Decrement participant count for sub-project

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            True if decremented successfully

        Raises:
            SubProjectNotFoundException: If not found
        """
        query = """
            UPDATE sub_projects
            SET current_participants = GREATEST(0, current_participants - 1)
            WHERE id = %s
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(sub_project_id),))
                self.conn.commit()

                if cursor.rowcount == 0:
                    raise SubProjectNotFoundException(sub_project_id)

                logger.info(f"Decremented participant count for sub-project: {sub_project_id}")
                return True

        except SubProjectNotFoundException:
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error decrementing participant count: {e}")
            raise DatabaseQueryException(query, str(e))

    def update_status(self, sub_project_id: str, new_status: str) -> bool:
        """
        Update sub-project status

        BUSINESS LOGIC:
        - Validates status is in allowed values
        - Updates updated_at timestamp (via trigger)

        Args:
            sub_project_id: UUID of sub-project
            new_status: New status value

        Returns:
            True if updated successfully

        Raises:
            ValueError: If status is invalid
            SubProjectNotFoundException: If not found
        """
        valid_statuses = ['draft', 'active', 'completed', 'cancelled', 'archived']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        query = """
            UPDATE sub_projects
            SET status = %s
            WHERE id = %s
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (new_status, str(sub_project_id)))
                self.conn.commit()

                if cursor.rowcount == 0:
                    raise SubProjectNotFoundException(sub_project_id)

                logger.info(f"Updated status for sub-project {sub_project_id}: {new_status}")
                return True

        except SubProjectNotFoundException:
            raise
        except ValueError:
            raise
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating status: {e}")
            raise DatabaseQueryException(query, str(e))

    def assign_track_to_sub_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a track to a sub-project with optional date overrides

        NOTE: This method is a placeholder for future implementation.
        Track assignments will be stored in the sub_project metadata field
        or in a separate sub_project_tracks table (not yet implemented).

        Args:
            data: Assignment data (sub_project_id, track_id, dates, instructor)

        Returns:
            Assignment record as dictionary

        Raises:
            DuplicateSubProjectException: If track already assigned
        """
        # For now, store track assignment in metadata
        sub_project_id = data['sub_project_id']
        track_id = data['track_id']

        try:
            # Get current sub-project
            sub_project = self.get_sub_project_by_id(sub_project_id)

            # Get or initialize tracks array in metadata
            metadata = sub_project.get('metadata', {})
            tracks = metadata.get('tracks', [])

            # Check if track already assigned
            if any(t['track_id'] == str(track_id) for t in tracks):
                raise DuplicateSubProjectException(f"track_{track_id}")

            # Add new track assignment
            track_assignment = {
                'track_id': str(track_id),
                'start_date': data.get('start_date').isoformat() if data.get('start_date') else None,
                'end_date': data.get('end_date').isoformat() if data.get('end_date') else None,
                'primary_instructor_id': str(data['primary_instructor_id']) if data.get('primary_instructor_id') else None,
                'sequence_order': data.get('sequence_order', 0)
            }
            tracks.append(track_assignment)

            # Update metadata
            metadata['tracks'] = tracks
            self.update_sub_project(sub_project_id, {'metadata': psycopg2.extras.Json(metadata)})

            logger.info(f"Assigned track {track_id} to sub-project {sub_project_id}")
            return track_assignment

        except Exception as e:
            logger.error(f"Error assigning track: {e}")
            raise

    def get_tracks_for_sub_project(self, sub_project_id: str) -> List[Dict[str, Any]]:
        """
        Get all tracks assigned to a sub-project

        NOTE: This method returns tracks from metadata.
        In a future implementation, this would JOIN with a sub_project_tracks table.

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            List of track assignments
        """
        try:
            sub_project = self.get_sub_project_by_id(sub_project_id)
            metadata = sub_project.get('metadata', {})
            tracks = metadata.get('tracks', [])

            logger.info(f"Retrieved {len(tracks)} tracks for sub-project {sub_project_id}")
            return tracks

        except Exception as e:
            logger.error(f"Error retrieving tracks: {e}")
            raise
