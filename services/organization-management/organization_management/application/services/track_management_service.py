"""
Track Management Service - Business Logic for Track Assignment System

BUSINESS PURPOSE:
Provides comprehensive track management including:
- Sub-project creation and hierarchy management
- Track creation with flexible parent references (project OR sub-project)
- Instructor assignment with minimum 1 enforcement
- Student assignment with instructor allocation
- Load balancing algorithm for fair workload distribution

ARCHITECTURE:
Application Service Layer - orchestrates domain entities and database operations
Following Clean Architecture principles with dependency inversion
"""

import psycopg2
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class TrackManagementService:
    """
    Service for managing tracks, instructors, and students

    RESPONSIBILITIES:
    - Project and sub-project CRUD operations
    - Track CRUD with XOR constraint enforcement
    - Instructor assignment with communication links
    - Student assignment with load balancing
    - Business rule validation
    """

    def __init__(self, db_connection_string: str):
        """
        Initialize service with database connection

        Args:
            db_connection_string: PostgreSQL connection string
                Example: "postgresql://user:pass@localhost:5433/course_creator"
        """
        self.db_connection_string = db_connection_string

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_connection_string)

    # ==========================================================================
    # Project and Sub-Project Operations
    # ==========================================================================

    def create_project(
        self,
        organization_id: UUID,
        name: str,
        slug: str,
        parent_project_id: Optional[UUID] = None,
        is_sub_project: bool = False
    ) -> Dict[str, Any]:
        """
        Create a project or sub-project

        BUSINESS RULES:
        - Main projects: is_sub_project=False, parent_project_id=None
        - Sub-projects: is_sub_project=True, parent_project_id must be set
        - XOR constraint enforced at database level

        Returns:
            Dict with project data including id, name, parent_project_id, etc.

        Raises:
            ValueError: If business rules violated
        """
        # Validate business rules
        if is_sub_project and parent_project_id is None:
            raise ValueError("Sub-project must have parent_project_id")

        if not is_sub_project and parent_project_id is not None:
            raise ValueError("Main project cannot have parent")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (
                        id, organization_id, name, slug,
                        parent_project_id, is_sub_project, auto_balance_students,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, organization_id, name, slug, parent_project_id,
                              is_sub_project, auto_balance_students, created_at
                """, (
                    str(uuid4()), str(organization_id), name, slug,
                    str(parent_project_id) if parent_project_id else None,
                    is_sub_project,
                    False,  # auto_balance_students defaults to FALSE
                    datetime.utcnow(),
                    datetime.utcnow()
                ))

                row = cur.fetchone()
                conn.commit()

                return {
                    'id': UUID(row[0]),
                    'organization_id': UUID(row[1]),
                    'name': row[2],
                    'slug': row[3],
                    'parent_project_id': UUID(row[4]) if row[4] else None,
                    'is_sub_project': row[5],
                    'auto_balance_students': row[6],
                    'created_at': row[7]
                }
        finally:
            conn.close()

    def create_sub_project(
        self,
        organization_id: UUID,
        parent_project_id: UUID,
        name: str,
        slug: str
    ) -> Dict[str, Any]:
        """
        Create a sub-project under a main project

        BUSINESS VALUE:
        Organizations can create quarterly/regional sub-projects
        (Q1, Q2, Q3, Q4 or EMEA, APAC, Americas)

        Returns:
            Dict with sub-project data
        """
        return self.create_project(
            organization_id=organization_id,
            name=name,
            slug=slug,
            parent_project_id=parent_project_id,
            is_sub_project=True
        )

    def list_sub_projects(
        self,
        organization_id: UUID,
        parent_project_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        List all sub-projects for a main project

        Returns:
            List of sub-project dicts
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, organization_id, name, slug, parent_project_id,
                           is_sub_project, auto_balance_students, created_at
                    FROM projects
                    WHERE organization_id = %s
                      AND parent_project_id = %s
                      AND is_sub_project = TRUE
                    ORDER BY created_at DESC
                """, (str(organization_id), str(parent_project_id)))

                rows = cur.fetchall()
                return [
                    {
                        'id': UUID(row[0]),
                        'organization_id': UUID(row[1]),
                        'name': row[2],
                        'slug': row[3],
                        'parent_project_id': UUID(row[4]) if row[4] else None,
                        'is_sub_project': row[5],
                        'auto_balance_students': row[6],
                        'created_at': row[7]
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def update_project(
        self,
        project_id: UUID,
        auto_balance_students: bool
    ) -> Dict[str, Any]:
        """
        Update project auto-balance setting

        BUSINESS VALUE:
        Org admins can enable/disable auto-balancing per project

        Returns:
            Updated project dict
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE projects
                    SET auto_balance_students = %s,
                        updated_at = %s
                    WHERE id = %s
                    RETURNING id, organization_id, name, slug, parent_project_id,
                              is_sub_project, auto_balance_students, created_at
                """, (auto_balance_students, datetime.utcnow(), str(project_id)))

                row = cur.fetchone()
                conn.commit()

                if not row:
                    raise ValueError(f"Project {project_id} not found")

                return {
                    'id': UUID(row[0]),
                    'organization_id': UUID(row[1]),
                    'name': row[2],
                    'slug': row[3],
                    'parent_project_id': UUID(row[4]) if row[4] else None,
                    'is_sub_project': row[5],
                    'auto_balance_students': row[6],
                    'created_at': row[7]
                }
        finally:
            conn.close()

    # ==========================================================================
    # Track Operations
    # ==========================================================================

    def create_track(
        self,
        organization_id: UUID,
        name: str,
        slug: str,
        project_id: Optional[UUID] = None,
        sub_project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a track under project OR sub-project

        BUSINESS RULES:
        - XOR constraint: Track must reference exactly one parent
        - Either project_id OR sub_project_id, not both, not neither

        Returns:
            Dict with track data

        Raises:
            ValueError: If XOR constraint violated
        """
        # Validate XOR constraint
        has_project = project_id is not None
        has_subproject = sub_project_id is not None

        if not has_project and not has_subproject:
            raise ValueError("Track must reference project OR sub-project")

        if has_project and has_subproject:
            raise ValueError("Track cannot reference both project AND sub-project")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                track_id = uuid4()
                cur.execute("""
                    INSERT INTO tracks (
                        id, organization_id, name, slug,
                        project_id, sub_project_id,
                        difficulty, status, display_order,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, organization_id, name, slug, project_id,
                              sub_project_id, difficulty, status, created_at
                """, (
                    str(track_id), str(organization_id), name, slug,
                    str(project_id) if project_id else None,
                    str(sub_project_id) if sub_project_id else None,
                    'beginner',  # default
                    'draft',     # default
                    0,           # default display_order
                    datetime.utcnow(),
                    datetime.utcnow()
                ))

                row = cur.fetchone()
                conn.commit()

                return {
                    'id': UUID(row[0]),
                    'organization_id': UUID(row[1]),
                    'name': row[2],
                    'slug': row[3],
                    'project_id': UUID(row[4]) if row[4] else None,
                    'sub_project_id': UUID(row[5]) if row[5] else None,
                    'difficulty': row[6],
                    'status': row[7],
                    'created_at': row[8]
                }
        finally:
            conn.close()

    # ==========================================================================
    # Instructor Assignment Operations
    # ==========================================================================

    def assign_instructor_to_track(
        self,
        track_id: UUID,
        instructor_id: UUID,
        zoom_link: Optional[str] = None,
        teams_link: Optional[str] = None,
        slack_links: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assign instructor to track with communication links

        BUSINESS VALUE:
        Instructors get unique communication links per track for student interaction

        Returns:
            Dict with assignment data including links
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                assignment_id = uuid4()
                slack_json = json.dumps(slack_links or [])

                cur.execute("""
                    INSERT INTO track_instructors (
                        id, track_id, user_id,
                        zoom_link, teams_link, slack_links,
                        assigned_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, track_id, user_id, zoom_link, teams_link,
                              slack_links, assigned_at
                """, (
                    str(assignment_id), str(track_id), str(instructor_id),
                    zoom_link, teams_link, slack_json,
                    datetime.utcnow()
                ))

                row = cur.fetchone()
                conn.commit()

                return {
                    'id': UUID(row[0]),
                    'track_id': UUID(row[1]),
                    'user_id': UUID(row[2]),
                    'zoom_link': row[3],
                    'teams_link': row[4],
                    'slack_links': row[5] if row[5] else [],  # psycopg2 auto-converts JSONB to list
                    'assigned_at': row[6]
                }
        finally:
            conn.close()

    def get_track_instructors(self, track_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all instructors assigned to a track

        Returns:
            List of instructor assignment dicts
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, track_id, user_id, zoom_link, teams_link,
                           slack_links, assigned_at
                    FROM track_instructors
                    WHERE track_id = %s
                    ORDER BY assigned_at ASC
                """, (str(track_id),))

                rows = cur.fetchall()
                return [
                    {
                        'id': UUID(row[0]),
                        'track_id': UUID(row[1]),
                        'user_id': UUID(row[2]),
                        'zoom_link': row[3],
                        'teams_link': row[4],
                        'slack_links': row[5] if row[5] else [],  # psycopg2 auto-converts JSONB to list
                        'assigned_at': row[6]
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def validate_track_has_instructors(self, track_id: UUID) -> None:
        """
        Validate track has at least 1 instructor

        BUSINESS RULE:
        Track must have minimum 1 instructor assigned

        Raises:
            ValueError: If track has no instructors
        """
        instructors = self.get_track_instructors(track_id)
        if len(instructors) == 0:
            raise ValueError("Track must have at least 1 instructor")

    def remove_instructor_from_track(
        self,
        track_id: UUID,
        instructor_id: UUID
    ) -> None:
        """
        Remove instructor from track

        BUSINESS RULE:
        Cannot remove last instructor (minimum 1 required)
        This is enforced by database trigger but we also check here

        Raises:
            ValueError: If attempting to remove last instructor
        """
        # Check current instructor count
        instructors = self.get_track_instructors(track_id)
        if len(instructors) <= 1:
            raise ValueError("Cannot remove last instructor")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM track_instructors
                    WHERE track_id = %s AND user_id = %s
                """, (str(track_id), str(instructor_id)))

                conn.commit()
        finally:
            conn.close()

    # ==========================================================================
    # Student Assignment Operations
    # ==========================================================================

    def assign_student_to_track(
        self,
        track_id: UUID,
        student_id: UUID,
        instructor_id: UUID
    ) -> Dict[str, Any]:
        """
        Assign student to track with instructor assignment

        BUSINESS RULES:
        - Student assigned to specific instructor for personalized guidance
        - Instructor must be assigned to this track (enforced via database trigger)

        Returns:
            Dict with student assignment data

        Raises:
            ValueError: If instructor not assigned to track
        """
        # Verify instructor is assigned to this track
        instructors = self.get_track_instructors(track_id)
        instructor_ids = [inst['user_id'] for inst in instructors]

        if instructor_id not in instructor_ids:
            raise ValueError("Instructor not assigned to this track")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                assignment_id = uuid4()
                cur.execute("""
                    INSERT INTO track_students (
                        id, track_id, student_id, assigned_instructor_id,
                        enrolled_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, track_id, student_id, assigned_instructor_id,
                              enrolled_at, last_reassigned_at
                """, (
                    str(assignment_id), str(track_id), str(student_id),
                    str(instructor_id), datetime.utcnow()
                ))

                row = cur.fetchone()
                conn.commit()

                return {
                    'id': UUID(row[0]),
                    'track_id': UUID(row[1]),
                    'student_id': UUID(row[2]),
                    'assigned_instructor_id': UUID(row[3]) if row[3] else None,
                    'enrolled_at': row[4],
                    'last_reassigned_at': row[5]
                }
        finally:
            conn.close()

    def reassign_student_to_instructor(
        self,
        track_id: UUID,
        student_id: UUID,
        new_instructor_id: UUID,
        reassigned_by: UUID
    ) -> Dict[str, Any]:
        """
        Reassign student to a different instructor

        BUSINESS VALUE:
        - Load balancing adjustments
        - Student preference accommodations
        - Instructor availability changes

        Returns:
            Updated student assignment dict
        """
        # Verify new instructor is assigned to this track
        instructors = self.get_track_instructors(track_id)
        instructor_ids = [inst['user_id'] for inst in instructors]

        if new_instructor_id not in instructor_ids:
            raise ValueError("Instructor not assigned to this track")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE track_students
                    SET assigned_instructor_id = %s,
                        assigned_by = %s,
                        last_reassigned_at = %s
                    WHERE track_id = %s AND student_id = %s
                    RETURNING id, track_id, student_id, assigned_instructor_id,
                              enrolled_at, last_reassigned_at
                """, (
                    str(new_instructor_id), str(reassigned_by),
                    datetime.utcnow(), str(track_id), str(student_id)
                ))

                row = cur.fetchone()
                conn.commit()

                if not row:
                    raise ValueError(f"Student {student_id} not found in track {track_id}")

                return {
                    'id': UUID(row[0]),
                    'track_id': UUID(row[1]),
                    'student_id': UUID(row[2]),
                    'assigned_instructor_id': UUID(row[3]) if row[3] else None,
                    'enrolled_at': row[4],
                    'last_reassigned_at': row[5]
                }
        finally:
            conn.close()

    # ==========================================================================
    # Load Balancing Operations
    # ==========================================================================

    def count_students_per_instructor(self, track_id: UUID) -> Dict[str, int]:
        """
        Count students assigned to each instructor for a track

        Returns:
            Dict mapping instructor_id (as string) → student_count
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT assigned_instructor_id, COUNT(*) as student_count
                    FROM track_students
                    WHERE track_id = %s
                      AND assigned_instructor_id IS NOT NULL
                    GROUP BY assigned_instructor_id
                """, (str(track_id),))

                rows = cur.fetchall()
                return {
                    row[0]: row[1]  # Return UUID as string for dict key
                    for row in rows
                }
        finally:
            conn.close()

    def auto_balance_students(
        self,
        track_id: UUID,
        student_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Auto-balance students across instructors

        ALGORITHM:
        1. Check if auto-balance is enabled for parent project
        2. Get all instructors for track
        3. Get current student loads
        4. Assign new students to instructor with lowest load
        5. Re-sort after each assignment
        6. Result: Even distribution (difference ≤ 1 student)

        BUSINESS VALUE:
        Fair workload distribution for instructors

        Returns:
            List of student assignments

        Raises:
            ValueError: If auto-balance not enabled for parent project
        """
        # First, check if auto-balance is enabled for the project
        # Get track info to find parent project
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.project_id, t.sub_project_id, p.auto_balance_students
                    FROM tracks t
                    LEFT JOIN projects p ON (
                        t.project_id = p.id OR t.sub_project_id = p.id
                    )
                    WHERE t.id = %s
                """, (str(track_id),))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Track {track_id} not found")

                # Check if auto-balance is enabled
                auto_balance_enabled = row[2]
                if not auto_balance_enabled:
                    raise ValueError("Auto-balance not enabled")
        finally:
            conn.close()

        # Get instructors for this track
        instructors = self.get_track_instructors(track_id)
        if not instructors:
            raise ValueError("Track must have at least 1 instructor")

        # Get current loads
        current_loads = self.count_students_per_instructor(track_id)

        # Initialize loads for instructors who don't have students yet
        instructor_loads = {
            str(inst['user_id']): current_loads.get(str(inst['user_id']), 0)
            for inst in instructors
        }

        # Assign students to instructors with lowest load
        assignments = []

        for student_id in student_ids:
            # Always get instructor with lowest current load
            sorted_instructors = sorted(
                instructor_loads.items(),
                key=lambda x: (x[1], x[0])  # Sort by load, then by ID for consistency
            )

            # Get instructor with lowest load (first in sorted list)
            instructor_id_str = sorted_instructors[0][0]
            instructor_id = UUID(instructor_id_str)

            # Assign student
            assignment = self.assign_student_to_track(
                track_id=track_id,
                student_id=student_id,
                instructor_id=instructor_id
            )
            assignments.append(assignment)

            # Update load for next iteration
            instructor_loads[instructor_id_str] += 1

        return assignments


# ==============================================================================
# Global Service Instance & Helper Functions
# ==============================================================================

# Default connection string (can be overridden via environment variable)
import os
DEFAULT_DB_STRING = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres_password@localhost:5433/course_creator'
)

# Global service instance
_service = TrackManagementService(DEFAULT_DB_STRING)


# Convenience functions that delegate to service instance
# These match the function signatures expected by the tests

def create_project(organization_id, name, slug, parent_project_id=None, is_sub_project=False):
    return _service.create_project(organization_id, name, slug, parent_project_id, is_sub_project)


def create_sub_project(organization_id, parent_project_id, name, slug):
    return _service.create_sub_project(organization_id, parent_project_id, name, slug)


def list_sub_projects(organization_id, parent_project_id):
    return _service.list_sub_projects(organization_id, parent_project_id)


def create_track(organization_id, name, slug, project_id=None, sub_project_id=None):
    return _service.create_track(organization_id, name, slug, project_id, sub_project_id)


def assign_instructor_to_track(track_id, instructor_id, zoom_link=None, teams_link=None, slack_links=None):
    return _service.assign_instructor_to_track(track_id, instructor_id, zoom_link, teams_link, slack_links)


def remove_instructor_from_track(track_id, instructor_id):
    return _service.remove_instructor_from_track(track_id, instructor_id)


def get_track_instructors(track_id):
    return _service.get_track_instructors(track_id)


def validate_track_has_instructors(track_id):
    return _service.validate_track_has_instructors(track_id)


def assign_student_to_track(track_id, student_id, instructor_id):
    return _service.assign_student_to_track(track_id, student_id, instructor_id)


def reassign_student_to_instructor(track_id, student_id, new_instructor_id, reassigned_by):
    return _service.reassign_student_to_instructor(track_id, student_id, new_instructor_id, reassigned_by)


def update_project(project_id, auto_balance_students):
    return _service.update_project(project_id, auto_balance_students)


def auto_balance_students(track_id, student_ids):
    return _service.auto_balance_students(track_id, student_ids)


def count_students_per_instructor(track_id):
    return _service.count_students_per_instructor(track_id)
