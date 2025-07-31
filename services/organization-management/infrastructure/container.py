"""
Dependency Injection Container
Single Responsibility: Service instantiation and dependency wiring
Dependency Inversion: Provides concrete implementations for abstractions
"""
import asyncpg
import logging
from typing import Optional
from omegaconf import DictConfig

from domain.interfaces.organization_repository import IOrganizationRepository
from domain.interfaces.project_repository import IProjectRepository
from domain.interfaces.track_repository import ITrackRepository
from domain.interfaces.membership_repository import IMembershipRepository, ITrackAssignmentRepository
from domain.interfaces.meeting_room_repository import IMeetingRoomRepository
from domain.interfaces.user_repository import IUserRepository
from infrastructure.repositories.postgresql_organization_repository import PostgreSQLOrganizationRepository
from infrastructure.repositories.postgresql_project_repository import PostgreSQLProjectRepository
from infrastructure.repositories.postgresql_track_repository import PostgreSQLTrackRepository
from infrastructure.repositories.postgresql_membership_repository import PostgreSQLMembershipRepository, PostgreSQLTrackAssignmentRepository
from infrastructure.repositories.postgresql_meeting_room_repository import PostgreSQLMeetingRoomRepository
from infrastructure.repositories.postgresql_user_repository import PostgreSQLUserRepository
from application.services.organization_service import OrganizationService
from application.services.track_service import TrackService
from application.services.membership_service import MembershipService
from application.services.meeting_room_service import MeetingRoomService
from application.services.auth_service import AuthService
from infrastructure.integrations.teams_integration import TeamsCredentials
from infrastructure.integrations.zoom_integration import ZoomCredentials
from auth.jwt_auth import JWTAuthenticator


class Container:
    """
    Dependency injection container for organization management service
    """

    def __init__(self, config: DictConfig):
        self._config = config
        self._logger = logging.getLogger(__name__)

        # Connection pool (initialized lazily)
        self._connection_pool: Optional[asyncpg.Pool] = None

        # Repositories (initialized lazily)
        self._organization_repository: Optional[IOrganizationRepository] = None
        self._project_repository: Optional[IProjectRepository] = None
        self._track_repository: Optional[ITrackRepository] = None
        self._membership_repository: Optional[IMembershipRepository] = None
        self._track_assignment_repository: Optional[ITrackAssignmentRepository] = None
        self._meeting_room_repository: Optional[IMeetingRoomRepository] = None
        self._user_repository: Optional[IUserRepository] = None

        # Services (initialized lazily)
        self._organization_service: Optional[OrganizationService] = None
        self._track_service: Optional[TrackService] = None
        self._membership_service: Optional[MembershipService] = None
        self._meeting_room_service: Optional[MeetingRoomService] = None
        self._auth_service: Optional[AuthService] = None
        self._jwt_authenticator: Optional[JWTAuthenticator] = None

        # Integration credentials
        self._teams_credentials: Optional[TeamsCredentials] = None
        self._zoom_credentials: Optional[ZoomCredentials] = None

    async def get_connection_pool(self) -> asyncpg.Pool:
        """Get database connection pool"""
        if self._connection_pool is None:
            try:
                database_config = self._config.database

                self._connection_pool = await asyncpg.create_pool(
                    host=database_config.host,
                    port=database_config.port,
                    user=database_config.user,
                    password=database_config.password,
                    database=database_config.name,
                    min_size=database_config.get('min_connections', 5),
                    max_size=database_config.get('max_connections', 20),
                    command_timeout=database_config.get('command_timeout', 60)
                )

                self._logger.info("Database connection pool created successfully")

            except Exception as e:
                self._logger.error(f"Failed to create database connection pool: {str(e)}")
                raise

        return self._connection_pool

    async def get_organization_repository(self) -> IOrganizationRepository:
        """Get organization repository"""
        if self._organization_repository is None:
            connection_pool = await self.get_connection_pool()
            self._organization_repository = PostgreSQLOrganizationRepository(connection_pool)
            self._logger.debug("Organization repository initialized")

        return self._organization_repository

    async def get_project_repository(self) -> IProjectRepository:
        """Get project repository"""
        if self._project_repository is None:
            connection_pool = await self.get_connection_pool()
            self._project_repository = PostgreSQLProjectRepository(connection_pool)
            self._logger.debug("Project repository initialized")

        return self._project_repository

    async def get_track_repository(self) -> ITrackRepository:
        """Get track repository"""
        if self._track_repository is None:
            connection_pool = await self.get_connection_pool()
            self._track_repository = PostgreSQLTrackRepository(connection_pool)
            self._logger.debug("Track repository initialized")

        return self._track_repository

    async def get_membership_repository(self) -> IMembershipRepository:
        """Get membership repository"""
        if self._membership_repository is None:
            connection_pool = await self.get_connection_pool()
            self._membership_repository = PostgreSQLMembershipRepository(connection_pool)
            self._logger.debug("Membership repository initialized")

        return self._membership_repository

    async def get_track_assignment_repository(self) -> ITrackAssignmentRepository:
        """Get track assignment repository"""
        if self._track_assignment_repository is None:
            connection_pool = await self.get_connection_pool()
            self._track_assignment_repository = PostgreSQLTrackAssignmentRepository(connection_pool)
            self._logger.debug("Track assignment repository initialized")

        return self._track_assignment_repository

    async def get_meeting_room_repository(self) -> IMeetingRoomRepository:
        """Get meeting room repository"""
        if self._meeting_room_repository is None:
            connection_pool = await self.get_connection_pool()
            self._meeting_room_repository = PostgreSQLMeetingRoomRepository(connection_pool)
            self._logger.debug("Meeting room repository initialized")

        return self._meeting_room_repository

    async def get_user_repository(self) -> IUserRepository:
        """Get user repository"""
        if self._user_repository is None:
            connection_pool = await self.get_connection_pool()
            self._user_repository = PostgreSQLUserRepository(connection_pool)
            self._logger.debug("User repository initialized")

        return self._user_repository

    async def get_organization_service(self) -> OrganizationService:
        """Get organization service"""
        if self._organization_service is None:
            organization_repository = await self.get_organization_repository()
            self._organization_service = OrganizationService(organization_repository)
            self._logger.debug("Organization service initialized")

        return self._organization_service

    async def get_track_service(self) -> TrackService:
        """Get track service"""
        if self._track_service is None:
            track_repository = await self.get_track_repository()
            self._track_service = TrackService(track_repository)
            self._logger.debug("Track service initialized")

        return self._track_service

    async def get_membership_service(self) -> MembershipService:
        """Get membership service"""
        if self._membership_service is None:
            membership_repository = await self.get_membership_repository()
            track_assignment_repository = await self.get_track_assignment_repository()
            user_repository = await self.get_user_repository()
            self._membership_service = MembershipService(
                membership_repository,
                track_assignment_repository,
                user_repository
            )
            self._logger.debug("Membership service initialized")

        return self._membership_service

    async def get_meeting_room_service(self) -> MeetingRoomService:
        """Get meeting room service"""
        if self._meeting_room_service is None:
            meeting_room_repository = await self.get_meeting_room_repository()
            teams_credentials = self._get_teams_credentials()
            zoom_credentials = self._get_zoom_credentials()

            self._meeting_room_service = MeetingRoomService(
                meeting_room_repository,
                teams_credentials,
                zoom_credentials
            )
            self._logger.debug("Meeting room service initialized")

        return self._meeting_room_service

    def _get_teams_credentials(self) -> Optional[TeamsCredentials]:
        """Get Teams credentials from configuration"""
        if self._teams_credentials is None:
            try:
                teams_config = self._config.get('integrations', {}).get('teams', {})
                if teams_config.get('enabled', False):
                    self._teams_credentials = TeamsCredentials(
                        tenant_id=teams_config.get('tenant_id'),
                        client_id=teams_config.get('client_id'),
                        client_secret=teams_config.get('client_secret')
                    )
                    self._logger.debug("Teams credentials initialized")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Teams credentials: {e}")

        return self._teams_credentials

    def _get_zoom_credentials(self) -> Optional[ZoomCredentials]:
        """Get Zoom credentials from configuration"""
        if self._zoom_credentials is None:
            try:
                zoom_config = self._config.get('integrations', {}).get('zoom', {})
                if zoom_config.get('enabled', False):
                    self._zoom_credentials = ZoomCredentials(
                        api_key=zoom_config.get('api_key'),
                        api_secret=zoom_config.get('api_secret'),
                        account_id=zoom_config.get('account_id')
                    )
                    self._logger.debug("Zoom credentials initialized")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Zoom credentials: {e}")

        return self._zoom_credentials

    def get_jwt_authenticator(self) -> JWTAuthenticator:
        """Get JWT authenticator"""
        if self._jwt_authenticator is None:
            self._jwt_authenticator = JWTAuthenticator(self._config)
            self._logger.debug("JWT authenticator initialized")

        return self._jwt_authenticator

    def get_auth_service(self) -> AuthService:
        """Get authentication service"""
        if self._auth_service is None:
            jwt_authenticator = self.get_jwt_authenticator()
            self._auth_service = AuthService(jwt_authenticator)
            self._logger.debug("Authentication service initialized")

        return self._auth_service

    async def close(self):
        """Close container and cleanup resources"""
        if self._connection_pool:
            await self._connection_pool.close()
            self._logger.info("Database connection pool closed")

# Global container instance
_container: Optional[Container] = None


def initialize_container(config: DictConfig) -> Container:
    """Initialize the global container"""
    global _container
    _container = Container(config)
    return _container


def get_container() -> Container:
    """Get the global container instance"""
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container first.")
    return _container


async def cleanup_container():
    """Cleanup the global container"""
    global _container
    if _container:
        await _container.close()
        _container = None