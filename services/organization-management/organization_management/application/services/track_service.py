"""
Track Service - Business Logic for Track Management and Auto-Enrollment
Single Responsibility: Track business operations and student enrollment automation
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on DAO abstractions (converted from repository pattern)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from organization_management.domain.entities.track import Track, TrackStatus, TrackType
from data_access.organization_dao import OrganizationManagementDAO


class TrackService:
    """
    Service class for track business operations including automatic enrollment
    """

    def __init__(self, organization_dao: OrganizationManagementDAO):
        self._organization_dao = organization_dao
        self._logger = logging.getLogger(__name__)

    async def create_track(self, project_id: UUID, name: str, slug: str,
                           description: str = None, track_type: TrackType = TrackType.SEQUENTIAL,
                           target_audience: List[str] = None, prerequisites: List[str] = None,
                           duration_weeks: int = None, max_enrolled: int = None,
                           learning_objectives: List[str] = None, skills_taught: List[str] = None,
                           difficulty_level: str = "beginner", auto_enroll_enabled: bool = True,
                           settings: Dict[str, Any] = None, created_by: UUID = None) -> Track:
        """Create a new track"""
        try:
            # Check if slug already exists within project
            if await self._organization_dao.exists_by_project_and_slug(project_id, slug):
                raise ValueError(f"Track with slug '{slug}' already exists in this project")

            # Determine sequence order
            existing_tracks = await self._organization_dao.get_by_project(project_id)
            sequence_order = len(existing_tracks) + 1

            # Create track entity
            track = Track(
                project_id=project_id,
                name=name,
                slug=slug,
                description=description,
                track_type=track_type,
                target_audience=target_audience or [],
                prerequisites=prerequisites or [],
                duration_weeks=duration_weeks,
                max_enrolled=max_enrolled,
                learning_objectives=learning_objectives or [],
                skills_taught=skills_taught or [],
                difficulty_level=difficulty_level,
                sequence_order=sequence_order,
                auto_enroll_enabled=auto_enroll_enabled,
                settings=settings or {},
                created_by=created_by
            )

            # Validate track
            if not track.is_valid():
                raise ValueError("Invalid track data")

            # Persist track
            created_track = await self._organization_dao.create(track)

            self._logger.info(f"Track created successfully: {created_track.slug} in project {project_id}")
            return created_track

        except Exception as e:
            self._logger.error(f"Error creating track: {str(e)}")
            raise

    async def get_track(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID"""
        try:
            return await self._organization_dao.get_by_id(track_id)
        except Exception as e:
            self._logger.error(f"Error getting track {track_id}: {str(e)}")
            raise

    async def get_track_by_project_and_slug(self, project_id: UUID, slug: str) -> Optional[Track]:
        """Get track by project and slug"""
        try:
            return await self._organization_dao.get_by_project_and_slug(project_id, slug)
        except Exception as e:
            self._logger.error(f"Error getting track by project {project_id} and slug {slug}: {str(e)}")
            raise

    async def update_track(self, track_id: UUID, name: str = None, description: str = None,
                           track_type: TrackType = None, target_audience: List[str] = None,
                           prerequisites: List[str] = None, duration_weeks: int = None,
                           max_enrolled: int = None, learning_objectives: List[str] = None,
                           skills_taught: List[str] = None, difficulty_level: str = None,
                           auto_enroll_enabled: bool = None, settings: Dict[str, Any] = None) -> Track:
        """Update track"""
        try:
            # Get existing track
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            # Update track information
            track.update_info(
                name=name,
                description=description,
                track_type=track_type,
                target_audience=target_audience,
                prerequisites=prerequisites,
                duration_weeks=duration_weeks,
                max_enrolled=max_enrolled,
                learning_objectives=learning_objectives,
                skills_taught=skills_taught,
                difficulty_level=difficulty_level,
                auto_enroll_enabled=auto_enroll_enabled,
                settings=settings
            )

            # Validate updated track
            if not track.is_valid():
                raise ValueError("Invalid track data")

            # Persist changes
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track updated successfully: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error updating track {track_id}: {str(e)}")
            raise

    async def activate_track(self, track_id: UUID) -> Track:
        """Activate track for student enrollment"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            if not track.can_activate():
                raise ValueError("Track cannot be activated - check status and validation")

            track.activate()
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track activated: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error activating track {track_id}: {str(e)}")
            raise

    async def archive_track(self, track_id: UUID) -> Track:
        """Archive track"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            track.archive()
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track archived: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error archiving track {track_id}: {str(e)}")
            raise

    async def delete_track(self, track_id: UUID) -> bool:
        """Delete track"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            result = await self._organization_dao.delete(track_id)

            if result:
                self._logger.info(f"Track deleted successfully: {track.slug}")

            return result

        except Exception as e:
            self._logger.error(f"Error deleting track {track_id}: {str(e)}")
            raise

    async def get_tracks_by_project(self, project_id: UUID, status: TrackStatus = None) -> List[Track]:
        """Get tracks by project, optionally filtered by status"""
        try:
            if status:
                return await self._organization_dao.get_by_project_and_status(project_id, status)
            else:
                return await self._organization_dao.get_by_project(project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for project {project_id}: {str(e)}")
            raise

    async def get_active_tracks_by_project(self, project_id: UUID) -> List[Track]:
        """Get active tracks by project"""
        try:
            return await self._organization_dao.get_by_project_and_status(project_id, TrackStatus.ACTIVE)
        except Exception as e:
            self._logger.error(f"Error getting active tracks for project {project_id}: {str(e)}")
            raise

    async def get_tracks_for_auto_enrollment(self, project_id: UUID) -> List[Track]:
        """Get tracks that have auto-enrollment enabled"""
        try:
            return await self._organization_dao.get_active_tracks_with_auto_enroll(project_id)
        except Exception as e:
            self._logger.error(f"Error getting auto-enrollment tracks for project {project_id}: {str(e)}")
            raise

    async def get_tracks_by_target_audience(self, target_audience: str, project_id: UUID = None) -> List[Track]:
        """Get tracks targeting specific audience"""
        try:
            return await self._organization_dao.get_by_target_audience(target_audience, project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for audience {target_audience}: {str(e)}")
            raise

    async def get_tracks_by_difficulty(self, difficulty_level: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by difficulty level"""
        try:
            return await self._organization_dao.get_by_difficulty_level(difficulty_level, project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for difficulty {difficulty_level}: {str(e)}")
            raise

    async def search_tracks(self, project_id: UUID, query: str) -> List[Track]:
        """Search tracks within project"""
        try:
            return await self._organization_dao.search_by_project(project_id, query)
        except Exception as e:
            self._logger.error(f"Error searching tracks in project {project_id}: {str(e)}")
            raise

    async def reorder_tracks(self, project_id: UUID, track_orders: List[Dict[str, int]]) -> List[Track]:
        """Reorder tracks within project"""
        try:
            updated_tracks = []

            for track_order in track_orders:
                track_id = track_order.get('track_id')
                new_order = track_order.get('sequence_order')

                track = await self._organization_dao.get_by_id(track_id)
                if track and track.project_id == project_id:
                    track.sequence_order = new_order
                    updated_track = await self._organization_dao.update(track)
                    updated_tracks.append(updated_track)

            self._logger.info(f"Reordered {len(updated_tracks)} tracks in project {project_id}")
            return updated_tracks

        except Exception as e:
            self._logger.error(f"Error reordering tracks in project {project_id}: {str(e)}")
            raise

    async def get_track_statistics(self, track_id: UUID) -> Dict[str, Any]:
        """Get track statistics"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            # Basic stats for now - could be extended with enrollment counts, completion rates, etc.
            return {
                "id": str(track.id),
                "name": track.name,
                "slug": track.slug,
                "status": track.status.value,
                "track_type": track.track_type.value,
                "difficulty_level": track.difficulty_level,
                "target_audience": track.get_target_audience_display(),
                "skills_taught": track.get_skills_display(),
                "estimated_completion": track.estimate_completion_time(),
                "auto_enroll_enabled": track.auto_enroll_enabled,
                "sequence_order": track.sequence_order,
                "created_at": track.created_at.isoformat() if track.created_at else None,
                "updated_at": track.updated_at.isoformat() if track.updated_at else None
            }

        except Exception as e:
            self._logger.error(f"Error getting track statistics {track_id}: {str(e)}")
            raise

    async def validate_track_prerequisites(self, track_id: UUID, student_background: List[str]) -> Dict[str, Any]:
        """Validate if student meets track prerequisites"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            missing_prerequisites = []
            for prerequisite in track.prerequisites:
                if prerequisite not in student_background:
                    missing_prerequisites.append(prerequisite)

            meets_requirements = len(missing_prerequisites) == 0

            return {
                "meets_requirements": meets_requirements,
                "required_prerequisites": track.prerequisites,
                "missing_prerequisites": missing_prerequisites,
                "student_background": student_background
            }

        except Exception as e:
            self._logger.error(f"Error validating prerequisites for track {track_id}: {str(e)}")
            raise
