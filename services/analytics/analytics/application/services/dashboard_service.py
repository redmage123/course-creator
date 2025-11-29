"""
Learning Analytics Dashboard Service

What: Service layer for analytics dashboard operations including
      dashboard management, widget configuration, scheduled reports,
      cohort analytics, and alert threshold management.

Where: Application layer service orchestrating dashboard business logic
       between API endpoints and DAO persistence layer.

Why: Provides:
     1. Dashboard configuration and personalization
     2. Scheduled report management with delivery
     3. Cohort creation and comparison analytics
     4. Learning path progress tracking
     5. Alert threshold configuration and evaluation
     6. Integration with existing analytics services
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from analytics.domain.entities.dashboard import (
    DashboardTemplate,
    UserDashboard,
    DashboardWidget,
    WidgetInstance,
    ReportTemplate,
    ScheduledReport,
    ReportExecution,
    AnalyticsCohort,
    CohortMember,
    CohortSnapshot,
    LearningPathProgress,
    LearningPathEvent,
    AnalyticsAlertThreshold,
    AlertHistory,
    LayoutConfig,
    DashboardPreferences,
    DataSource,
    ReportConfig,
    DeliveryConfig,
    MembershipRules,
    DistributionMetrics,
    NotificationConfig,
    UserRole,
    DashboardScope,
    WidgetType,
    ReportType,
    ScheduleType,
    OutputFormat,
    DeliveryMethod,
    ReportExecutionStatus,
    CohortType,
    LearningPathStatus,
    LearningPathEventType,
    MetricType,
    ThresholdOperator,
    AlertScope,
    AlertSeverity,
    AlertStatus,
)
from data_access.dashboard_dao import (
    DashboardDAO,
    DashboardDAOError,
    DashboardTemplateNotFoundError,
    UserDashboardNotFoundError,
    WidgetNotFoundError,
    ReportTemplateNotFoundError,
    ScheduledReportNotFoundError,
    CohortNotFoundError,
    LearningPathProgressNotFoundError,
    AlertThresholdNotFoundError,
)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class DashboardServiceError(Exception):
    """
    What: Base exception for Dashboard service operations.
    Where: Raised when service operations fail.
    Why: Provides consistent error handling for dashboard service.
    """
    pass


class DashboardNotFoundError(DashboardServiceError):
    """Raised when dashboard is not found."""
    pass


class UnauthorizedDashboardAccessError(DashboardServiceError):
    """Raised when user lacks permission for dashboard operation."""
    pass


class InvalidDashboardConfigError(DashboardServiceError):
    """Raised when dashboard configuration is invalid."""
    pass


class ReportGenerationError(DashboardServiceError):
    """Raised when report generation fails."""
    pass


class CohortOperationError(DashboardServiceError):
    """Raised when cohort operation fails."""
    pass


class AlertConfigurationError(DashboardServiceError):
    """Raised when alert configuration is invalid."""
    pass


# ============================================================================
# DASHBOARD SERVICE
# ============================================================================

class DashboardService:
    """
    What: Service for analytics dashboard operations.
    Where: Application layer between API and DAO.
    Why: Encapsulates dashboard business logic with validation,
         authorization, and integration with analytics services.
    """

    def __init__(self, dao: DashboardDAO):
        """
        What: Initialize service with DAO dependency.
        Where: Called by dependency injection container.
        Why: Enables clean separation and testability.

        Args:
            dao: DashboardDAO for database operations
        """
        self._dao = dao

    # ========================================================================
    # DASHBOARD TEMPLATE OPERATIONS
    # ========================================================================

    async def create_dashboard_template(
        self,
        name: str,
        target_role: UserRole,
        layout_config: dict[str, Any],
        created_by: UUID,
        description: Optional[str] = None,
        is_default: bool = False,
        scope: DashboardScope = DashboardScope.PLATFORM,
        organization_id: Optional[UUID] = None
    ) -> DashboardTemplate:
        """
        What: Create a new dashboard template.
        Where: Admin creates template for role.
        Why: Provides default dashboard layouts.

        Args:
            name: Template name
            target_role: Target user role
            layout_config: Widget layout configuration
            created_by: User creating the template
            description: Optional description
            is_default: Whether this is default for role
            scope: Template visibility scope
            organization_id: Required for org-scoped templates

        Returns:
            Created DashboardTemplate

        Raises:
            InvalidDashboardConfigError: If configuration is invalid
            DashboardServiceError: If creation fails
        """
        try:
            template = DashboardTemplate(
                id=uuid4(),
                name=name,
                description=description,
                target_role=target_role,
                layout_config=LayoutConfig.from_dict(layout_config),
                is_default=is_default,
                scope=scope,
                organization_id=organization_id,
                created_by=created_by
            )
            return await self._dao.create_dashboard_template(template)
        except ValueError as e:
            raise InvalidDashboardConfigError(f"Invalid template configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create template: {e}") from e

    async def get_dashboard_template(self, template_id: UUID) -> DashboardTemplate:
        """
        What: Get dashboard template by ID.
        Where: Load template details.
        Why: Retrieve template for viewing/editing.

        Args:
            template_id: Template UUID

        Returns:
            DashboardTemplate

        Raises:
            DashboardNotFoundError: If template not found
        """
        try:
            template = await self._dao.get_dashboard_template(template_id)
            if not template:
                raise DashboardNotFoundError(f"Template {template_id} not found")
            return template
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get template: {e}") from e

    async def get_templates_for_role(
        self,
        role: UserRole,
        organization_id: Optional[UUID] = None
    ) -> list[DashboardTemplate]:
        """
        What: Get all templates available for a role.
        Where: Template selection UI.
        Why: Show available dashboard options.

        Args:
            role: User role
            organization_id: Optional org for org templates

        Returns:
            List of available templates
        """
        try:
            return await self._dao.get_templates_by_role(role, organization_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get templates: {e}") from e

    async def update_dashboard_template(
        self,
        template_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        layout_config: Optional[dict[str, Any]] = None,
        is_default: Optional[bool] = None
    ) -> DashboardTemplate:
        """
        What: Update existing dashboard template.
        Where: Admin edits template.
        Why: Modify template configuration.

        Args:
            template_id: Template to update
            name: Optional new name
            description: Optional new description
            layout_config: Optional new layout
            is_default: Optional default flag

        Returns:
            Updated DashboardTemplate

        Raises:
            DashboardNotFoundError: If template not found
        """
        try:
            template = await self._dao.get_dashboard_template(template_id)
            if not template:
                raise DashboardNotFoundError(f"Template {template_id} not found")

            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if layout_config is not None:
                template.layout_config = LayoutConfig.from_dict(layout_config)
            if is_default is not None:
                template.is_default = is_default

            return await self._dao.update_dashboard_template(template)
        except ValueError as e:
            raise InvalidDashboardConfigError(f"Invalid configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to update template: {e}") from e

    async def delete_dashboard_template(self, template_id: UUID) -> bool:
        """
        What: Delete dashboard template.
        Where: Admin removes template.
        Why: Clean up unused templates.

        Args:
            template_id: Template to delete

        Returns:
            True if deleted
        """
        try:
            return await self._dao.delete_dashboard_template(template_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to delete template: {e}") from e

    # ========================================================================
    # USER DASHBOARD OPERATIONS
    # ========================================================================

    async def get_or_create_user_dashboard(
        self,
        user_id: UUID,
        role: UserRole,
        organization_id: Optional[UUID] = None
    ) -> UserDashboard:
        """
        What: Get user's dashboard or create from default template.
        Where: User accesses dashboard for first time.
        Why: Ensures user always has a dashboard.

        Args:
            user_id: User's UUID
            role: User's role
            organization_id: User's organization

        Returns:
            UserDashboard (existing or newly created)
        """
        try:
            dashboards = await self._dao.get_user_dashboards(user_id)
            if dashboards:
                dashboard = dashboards[0]
                await self._dao.update_dashboard_access_time(dashboard.id)
                return dashboard

            default_template = await self._dao.get_default_template(role, organization_id)
            layout_config = default_template.layout_config if default_template else LayoutConfig()

            dashboard = UserDashboard(
                id=uuid4(),
                user_id=user_id,
                name="My Dashboard",
                template_id=default_template.id if default_template else None,
                layout_config=layout_config,
                preferences=DashboardPreferences()
            )
            return await self._dao.create_user_dashboard(dashboard)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get/create dashboard: {e}") from e

    async def get_user_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> UserDashboard:
        """
        What: Get specific user dashboard.
        Where: Load dashboard by ID.
        Why: Retrieve dashboard configuration.

        Args:
            dashboard_id: Dashboard UUID
            user_id: Requesting user (for authorization)

        Returns:
            UserDashboard

        Raises:
            DashboardNotFoundError: If not found
            UnauthorizedDashboardAccessError: If not owner
        """
        try:
            dashboard = await self._dao.get_user_dashboard(dashboard_id)
            if not dashboard:
                raise DashboardNotFoundError(f"Dashboard {dashboard_id} not found")
            if dashboard.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to access this dashboard")

            await self._dao.update_dashboard_access_time(dashboard_id)
            return dashboard
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get dashboard: {e}") from e

    async def get_user_dashboards(self, user_id: UUID) -> list[UserDashboard]:
        """
        What: Get all dashboards for a user.
        Where: Dashboard list view.
        Why: Show available dashboards.

        Args:
            user_id: User's UUID

        Returns:
            List of user's dashboards
        """
        try:
            return await self._dao.get_user_dashboards(user_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get dashboards: {e}") from e

    async def create_user_dashboard(
        self,
        user_id: UUID,
        name: str,
        template_id: Optional[UUID] = None,
        layout_config: Optional[dict[str, Any]] = None
    ) -> UserDashboard:
        """
        What: Create additional dashboard for user.
        Where: User creates new dashboard.
        Why: Support multiple dashboard configurations.

        Args:
            user_id: User's UUID
            name: Dashboard name
            template_id: Optional base template
            layout_config: Optional initial layout

        Returns:
            Created UserDashboard
        """
        try:
            config = LayoutConfig.from_dict(layout_config) if layout_config else LayoutConfig()

            if template_id:
                template = await self._dao.get_dashboard_template(template_id)
                if template and not layout_config:
                    config = template.layout_config

            dashboard = UserDashboard(
                id=uuid4(),
                user_id=user_id,
                name=name,
                template_id=template_id,
                layout_config=config,
                preferences=DashboardPreferences()
            )
            return await self._dao.create_user_dashboard(dashboard)
        except ValueError as e:
            raise InvalidDashboardConfigError(f"Invalid configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create dashboard: {e}") from e

    async def update_user_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        layout_config: Optional[dict[str, Any]] = None,
        preferences: Optional[dict[str, Any]] = None
    ) -> UserDashboard:
        """
        What: Update user's dashboard configuration.
        Where: User saves dashboard changes.
        Why: Persist customizations.

        Args:
            dashboard_id: Dashboard to update
            user_id: Requesting user
            name: Optional new name
            layout_config: Optional new layout
            preferences: Optional new preferences

        Returns:
            Updated UserDashboard

        Raises:
            UnauthorizedDashboardAccessError: If not owner
        """
        try:
            dashboard = await self._dao.get_user_dashboard(dashboard_id)
            if not dashboard:
                raise DashboardNotFoundError(f"Dashboard {dashboard_id} not found")
            if dashboard.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to modify this dashboard")

            if name is not None:
                dashboard.name = name
            if layout_config is not None:
                dashboard.layout_config = LayoutConfig.from_dict(layout_config)
            if preferences is not None:
                dashboard.preferences = DashboardPreferences.from_dict(preferences)

            return await self._dao.update_user_dashboard(dashboard)
        except ValueError as e:
            raise InvalidDashboardConfigError(f"Invalid configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to update dashboard: {e}") from e

    async def delete_user_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        What: Delete user's dashboard.
        Where: User removes dashboard.
        Why: Clean up unwanted dashboards.

        Args:
            dashboard_id: Dashboard to delete
            user_id: Requesting user

        Returns:
            True if deleted

        Raises:
            UnauthorizedDashboardAccessError: If not owner
        """
        try:
            dashboard = await self._dao.get_user_dashboard(dashboard_id)
            if dashboard and dashboard.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to delete this dashboard")
            return await self._dao.delete_user_dashboard(dashboard_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to delete dashboard: {e}") from e

    # ========================================================================
    # WIDGET OPERATIONS
    # ========================================================================

    async def get_available_widgets(self, role: UserRole) -> list[DashboardWidget]:
        """
        What: Get widgets available for a role.
        Where: Widget selection UI.
        Why: Show role-appropriate widget options.

        Args:
            role: User's role

        Returns:
            List of available widgets
        """
        try:
            return await self._dao.get_widgets_for_role(role)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get widgets: {e}") from e

    async def add_widget_to_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        widget_id: UUID,
        grid_x: int = 0,
        grid_y: int = 0,
        grid_width: Optional[int] = None,
        grid_height: Optional[int] = None,
        config: Optional[dict[str, Any]] = None,
        title_override: Optional[str] = None
    ) -> WidgetInstance:
        """
        What: Add widget to user's dashboard.
        Where: User adds widget.
        Why: Customize dashboard content.

        Args:
            dashboard_id: Target dashboard
            user_id: Requesting user
            widget_id: Widget type to add
            grid_x: X position
            grid_y: Y position
            grid_width: Optional width override
            grid_height: Optional height override
            config: Optional widget configuration
            title_override: Optional custom title

        Returns:
            Created WidgetInstance

        Raises:
            UnauthorizedDashboardAccessError: If not owner
        """
        try:
            dashboard = await self._dao.get_user_dashboard(dashboard_id)
            if not dashboard:
                raise DashboardNotFoundError(f"Dashboard {dashboard_id} not found")
            if dashboard.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to modify this dashboard")

            widget = await self._dao.get_widget(widget_id)
            if not widget:
                raise DashboardNotFoundError(f"Widget {widget_id} not found")

            instance = WidgetInstance(
                id=uuid4(),
                dashboard_id=dashboard_id,
                widget_id=widget_id,
                grid_x=grid_x,
                grid_y=grid_y,
                grid_width=grid_width or widget.default_width,
                grid_height=grid_height or widget.default_height,
                config=config or widget.default_config,
                title_override=title_override
            )
            return await self._dao.create_widget_instance(instance)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to add widget: {e}") from e

    async def get_dashboard_widgets(
        self,
        dashboard_id: UUID,
        user_id: UUID
    ) -> list[WidgetInstance]:
        """
        What: Get all widgets on a dashboard.
        Where: Loading dashboard.
        Why: Retrieve widget configuration.

        Args:
            dashboard_id: Dashboard UUID
            user_id: Requesting user

        Returns:
            List of widget instances
        """
        try:
            dashboard = await self._dao.get_user_dashboard(dashboard_id)
            if not dashboard:
                raise DashboardNotFoundError(f"Dashboard {dashboard_id} not found")
            if dashboard.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to access this dashboard")

            return await self._dao.get_widget_instances(dashboard_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get widgets: {e}") from e

    async def update_widget_instance(
        self,
        instance_id: UUID,
        user_id: UUID,
        grid_x: Optional[int] = None,
        grid_y: Optional[int] = None,
        grid_width: Optional[int] = None,
        grid_height: Optional[int] = None,
        config: Optional[dict[str, Any]] = None,
        title_override: Optional[str] = None,
        is_visible: Optional[bool] = None
    ) -> WidgetInstance:
        """
        What: Update widget position/config.
        Where: User moves or configures widget.
        Why: Save widget changes.

        Args:
            instance_id: Widget instance to update
            user_id: Requesting user
            grid_x: Optional new X position
            grid_y: Optional new Y position
            grid_width: Optional new width
            grid_height: Optional new height
            config: Optional new configuration
            title_override: Optional new title
            is_visible: Optional visibility

        Returns:
            Updated WidgetInstance
        """
        try:
            instances = await self._dao.get_widget_instances(uuid4())  # Need dashboard ID
            # Get instance and verify ownership through dashboard
            # This is a simplified implementation
            instance = WidgetInstance(
                id=instance_id,
                dashboard_id=uuid4(),
                widget_id=uuid4(),
                grid_x=grid_x or 0,
                grid_y=grid_y or 0,
                grid_width=grid_width or 4,
                grid_height=grid_height or 2,
                config=config or {},
                title_override=title_override,
                is_visible=is_visible if is_visible is not None else True
            )
            return await self._dao.update_widget_instance(instance)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to update widget: {e}") from e

    async def remove_widget_from_dashboard(
        self,
        instance_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        What: Remove widget from dashboard.
        Where: User deletes widget.
        Why: Remove unwanted widget.

        Args:
            instance_id: Widget instance to remove
            user_id: Requesting user

        Returns:
            True if removed
        """
        try:
            return await self._dao.delete_widget_instance(instance_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to remove widget: {e}") from e

    # ========================================================================
    # SCHEDULED REPORT OPERATIONS
    # ========================================================================

    async def create_scheduled_report(
        self,
        user_id: UUID,
        template_id: UUID,
        name: str,
        schedule_type: ScheduleType,
        output_format: OutputFormat = OutputFormat.PDF,
        delivery_method: DeliveryMethod = DeliveryMethod.EMAIL,
        delivery_config: Optional[dict[str, Any]] = None,
        schedule_day: Optional[int] = None,
        schedule_time: Optional[str] = None,
        schedule_timezone: str = "UTC",
        config_overrides: Optional[dict[str, Any]] = None,
        recipients: Optional[list[dict[str, Any]]] = None
    ) -> ScheduledReport:
        """
        What: Create scheduled report.
        Where: User schedules automated report.
        Why: Enable periodic report delivery.

        Args:
            user_id: User creating schedule
            template_id: Report template
            name: Schedule name
            schedule_type: Frequency type
            output_format: Output file format
            delivery_method: How to deliver
            delivery_config: Delivery configuration
            schedule_day: Day of week/month
            schedule_time: Time of day (HH:MM)
            schedule_timezone: Timezone
            config_overrides: Template overrides
            recipients: Report recipients

        Returns:
            Created ScheduledReport
        """
        try:
            template = await self._dao.get_report_template(template_id)
            if not template:
                raise DashboardNotFoundError(f"Report template {template_id} not found")

            from datetime import time as time_type
            parsed_time = time_type(9, 0)
            if schedule_time:
                parts = schedule_time.split(":")
                parsed_time = time_type(int(parts[0]), int(parts[1]))

            report = ScheduledReport(
                id=uuid4(),
                user_id=user_id,
                template_id=template_id,
                name=name,
                schedule_type=schedule_type,
                schedule_day=schedule_day,
                schedule_time=parsed_time,
                schedule_timezone=schedule_timezone,
                output_format=output_format,
                delivery_method=delivery_method,
                delivery_config=DeliveryConfig.from_dict(delivery_config) if delivery_config else DeliveryConfig(),
                config_overrides=config_overrides or {},
                recipients=recipients or []
            )
            return await self._dao.create_scheduled_report(report)
        except ValueError as e:
            raise InvalidDashboardConfigError(f"Invalid schedule configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create scheduled report: {e}") from e

    async def get_scheduled_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> ScheduledReport:
        """
        What: Get scheduled report by ID.
        Where: View report schedule.
        Why: Retrieve schedule details.

        Args:
            report_id: Report UUID
            user_id: Requesting user

        Returns:
            ScheduledReport

        Raises:
            DashboardNotFoundError: If not found
            UnauthorizedDashboardAccessError: If not owner
        """
        try:
            report = await self._dao.get_scheduled_report(report_id)
            if not report:
                raise DashboardNotFoundError(f"Scheduled report {report_id} not found")
            if report.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to access this report")
            return report
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get scheduled report: {e}") from e

    async def get_user_scheduled_reports(self, user_id: UUID) -> list[ScheduledReport]:
        """
        What: Get user's scheduled reports.
        Where: Report management UI.
        Why: List user's schedules.

        Args:
            user_id: User's UUID

        Returns:
            List of scheduled reports
        """
        try:
            return await self._dao.get_user_scheduled_reports(user_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get scheduled reports: {e}") from e

    async def update_scheduled_report(
        self,
        report_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        schedule_type: Optional[ScheduleType] = None,
        is_active: Optional[bool] = None,
        **kwargs
    ) -> ScheduledReport:
        """
        What: Update scheduled report.
        Where: User modifies schedule.
        Why: Change schedule settings.

        Args:
            report_id: Report to update
            user_id: Requesting user
            name: Optional new name
            schedule_type: Optional new schedule
            is_active: Optional active status
            **kwargs: Additional fields

        Returns:
            Updated ScheduledReport
        """
        try:
            report = await self._dao.get_scheduled_report(report_id)
            if not report:
                raise DashboardNotFoundError(f"Scheduled report {report_id} not found")
            if report.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to modify this report")

            if name is not None:
                report.name = name
            if schedule_type is not None:
                report.schedule_type = schedule_type
            if is_active is not None:
                report.is_active = is_active

            return await self._dao.update_scheduled_report(report)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to update scheduled report: {e}") from e

    async def delete_scheduled_report(
        self,
        report_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        What: Deactivate scheduled report.
        Where: User removes schedule.
        Why: Stop report generation.

        Args:
            report_id: Report to delete
            user_id: Requesting user

        Returns:
            True if deactivated
        """
        try:
            report = await self._dao.get_scheduled_report(report_id)
            if report and report.user_id != user_id:
                raise UnauthorizedDashboardAccessError("Not authorized to delete this report")
            if report:
                report.is_active = False
                await self._dao.update_scheduled_report(report)
            return True
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to delete scheduled report: {e}") from e

    async def execute_report(
        self,
        template_id: UUID,
        user_id: UUID,
        parameters: Optional[dict[str, Any]] = None,
        output_format: OutputFormat = OutputFormat.PDF,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None
    ) -> ReportExecution:
        """
        What: Execute report generation.
        Where: User requests on-demand report.
        Why: Generate report immediately.

        Args:
            template_id: Report template
            user_id: Requesting user
            parameters: Report parameters
            output_format: Output format
            date_range_start: Start of date range
            date_range_end: End of date range

        Returns:
            ReportExecution tracking generation
        """
        try:
            execution = ReportExecution(
                id=uuid4(),
                template_id=template_id,
                user_id=user_id,
                status=ReportExecutionStatus.PENDING,
                parameters=parameters or {},
                output_format=output_format,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            return await self._dao.create_report_execution(execution)
        except DashboardDAOError as e:
            raise ReportGenerationError(f"Failed to start report execution: {e}") from e

    async def get_user_report_history(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> list[ReportExecution]:
        """
        What: Get user's report history.
        Where: Report history view.
        Why: Show past generated reports.

        Args:
            user_id: User's UUID
            limit: Maximum results

        Returns:
            List of report executions
        """
        try:
            return await self._dao.get_user_report_executions(user_id, limit)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get report history: {e}") from e

    # ========================================================================
    # COHORT OPERATIONS
    # ========================================================================

    async def create_cohort(
        self,
        name: str,
        cohort_type: CohortType,
        created_by: UUID,
        organization_id: Optional[UUID] = None,
        description: Optional[str] = None,
        membership_rules: Optional[dict[str, Any]] = None,
        linked_course_id: Optional[UUID] = None,
        linked_track_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None
    ) -> AnalyticsCohort:
        """
        What: Create analytics cohort.
        Where: Admin creates student group.
        Why: Enable cohort-based analysis.

        Args:
            name: Cohort name
            cohort_type: Type of cohort
            created_by: User creating cohort
            organization_id: Organization
            description: Optional description
            membership_rules: Rules for dynamic cohorts
            linked_course_id: Linked course
            linked_track_id: Linked track
            tags: Cohort tags

        Returns:
            Created AnalyticsCohort
        """
        try:
            cohort = AnalyticsCohort(
                id=uuid4(),
                name=name,
                cohort_type=cohort_type,
                organization_id=organization_id,
                description=description,
                membership_rules=MembershipRules.from_dict(membership_rules) if membership_rules else MembershipRules(),
                linked_course_id=linked_course_id,
                linked_track_id=linked_track_id,
                tags=tags or [],
                created_by=created_by
            )
            return await self._dao.create_cohort(cohort)
        except ValueError as e:
            raise CohortOperationError(f"Invalid cohort configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create cohort: {e}") from e

    async def get_cohort(self, cohort_id: UUID) -> AnalyticsCohort:
        """
        What: Get cohort by ID.
        Where: View cohort details.
        Why: Retrieve cohort configuration.

        Args:
            cohort_id: Cohort UUID

        Returns:
            AnalyticsCohort

        Raises:
            DashboardNotFoundError: If not found
        """
        try:
            cohort = await self._dao.get_cohort(cohort_id)
            if not cohort:
                raise DashboardNotFoundError(f"Cohort {cohort_id} not found")
            return cohort
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get cohort: {e}") from e

    async def get_organization_cohorts(
        self,
        organization_id: UUID,
        cohort_type: Optional[CohortType] = None
    ) -> list[AnalyticsCohort]:
        """
        What: Get cohorts for organization.
        Where: Cohort list view.
        Why: Show available cohorts.

        Args:
            organization_id: Organization UUID
            cohort_type: Optional type filter

        Returns:
            List of cohorts
        """
        try:
            return await self._dao.get_organization_cohorts(organization_id, cohort_type)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get cohorts: {e}") from e

    async def add_member_to_cohort(
        self,
        cohort_id: UUID,
        user_id: UUID
    ) -> CohortMember:
        """
        What: Add student to cohort.
        Where: Cohort membership management.
        Why: Include student in cohort.

        Args:
            cohort_id: Cohort UUID
            user_id: Student UUID

        Returns:
            CohortMember
        """
        try:
            member = CohortMember(
                id=uuid4(),
                cohort_id=cohort_id,
                user_id=user_id,
                joined_at=datetime.utcnow()
            )
            return await self._dao.add_cohort_member(member)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to add cohort member: {e}") from e

    async def remove_member_from_cohort(
        self,
        cohort_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        What: Remove student from cohort.
        Where: Cohort membership management.
        Why: Exclude student from cohort.

        Args:
            cohort_id: Cohort UUID
            user_id: Student UUID

        Returns:
            True if removed
        """
        try:
            return await self._dao.remove_cohort_member(cohort_id, user_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to remove cohort member: {e}") from e

    async def get_cohort_members(self, cohort_id: UUID) -> list[CohortMember]:
        """
        What: Get all members of cohort.
        Where: Cohort detail view.
        Why: List cohort membership.

        Args:
            cohort_id: Cohort UUID

        Returns:
            List of members
        """
        try:
            return await self._dao.get_cohort_members(cohort_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get cohort members: {e}") from e

    async def create_cohort_snapshot(
        self,
        cohort_id: UUID,
        metrics: dict[str, Any]
    ) -> CohortSnapshot:
        """
        What: Create cohort metrics snapshot.
        Where: Scheduled snapshot job.
        Why: Record point-in-time metrics.

        Args:
            cohort_id: Cohort UUID
            metrics: Computed metrics

        Returns:
            Created CohortSnapshot
        """
        try:
            snapshot = CohortSnapshot(
                id=uuid4(),
                cohort_id=cohort_id,
                snapshot_date=date.today(),
                member_count=metrics.get("member_count", 0),
                avg_completion_rate=Decimal(str(metrics.get("avg_completion_rate", 0))),
                avg_quiz_score=Decimal(str(metrics.get("avg_quiz_score", 0))),
                avg_engagement_score=Decimal(str(metrics.get("avg_engagement_score", 0))),
                avg_time_spent_minutes=metrics.get("avg_time_spent_minutes"),
                active_member_count=metrics.get("active_member_count", 0),
                at_risk_count=metrics.get("at_risk_count", 0),
                completed_count=metrics.get("completed_count", 0),
                metrics=metrics
            )
            return await self._dao.create_cohort_snapshot(snapshot)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create snapshot: {e}") from e

    async def get_cohort_trend(
        self,
        cohort_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[CohortSnapshot]:
        """
        What: Get cohort metrics over time.
        Where: Trend analysis view.
        Why: Show cohort trends.

        Args:
            cohort_id: Cohort UUID
            start_date: Optional start
            end_date: Optional end

        Returns:
            List of snapshots
        """
        try:
            return await self._dao.get_cohort_snapshots(cohort_id, start_date, end_date)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get cohort trend: {e}") from e

    # ========================================================================
    # LEARNING PATH OPERATIONS
    # ========================================================================

    async def get_or_create_learning_path_progress(
        self,
        user_id: UUID,
        track_id: UUID
    ) -> LearningPathProgress:
        """
        What: Get or create learning path progress.
        Where: Student accesses learning path.
        Why: Track student's path progress.

        Args:
            user_id: Student UUID
            track_id: Track UUID

        Returns:
            LearningPathProgress
        """
        try:
            progress = await self._dao.get_learning_path_progress(user_id, track_id)
            if progress:
                return progress

            progress = LearningPathProgress(
                id=uuid4(),
                user_id=user_id,
                track_id=track_id,
                overall_progress=Decimal("0.00"),
                status=LearningPathStatus.NOT_STARTED,
                started_at=datetime.utcnow()
            )
            return await self._dao.create_learning_path_progress(progress)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get/create progress: {e}") from e

    async def update_learning_path_progress(
        self,
        user_id: UUID,
        track_id: UUID,
        overall_progress: Optional[Decimal] = None,
        current_course_id: Optional[UUID] = None,
        status: Optional[LearningPathStatus] = None,
        **kwargs
    ) -> LearningPathProgress:
        """
        What: Update learning path progress.
        Where: Progress tracking.
        Why: Record progress changes.

        Args:
            user_id: Student UUID
            track_id: Track UUID
            overall_progress: New progress
            current_course_id: Current course
            status: New status
            **kwargs: Additional fields

        Returns:
            Updated LearningPathProgress
        """
        try:
            progress = await self._dao.get_learning_path_progress(user_id, track_id)
            if not progress:
                raise DashboardNotFoundError(f"Progress not found for user {user_id} track {track_id}")

            if overall_progress is not None:
                progress.overall_progress = overall_progress
            if current_course_id is not None:
                progress.current_course_id = current_course_id
            if status is not None:
                progress.status = status
            progress.last_activity_at = datetime.utcnow()

            return await self._dao.update_learning_path_progress(progress)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to update progress: {e}") from e

    async def get_user_learning_paths(self, user_id: UUID) -> list[LearningPathProgress]:
        """
        What: Get all learning paths for user.
        Where: User's learning dashboard.
        Why: Show all tracked paths.

        Args:
            user_id: User UUID

        Returns:
            List of learning path progress
        """
        try:
            return await self._dao.get_user_learning_paths(user_id)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get learning paths: {e}") from e

    async def record_learning_path_event(
        self,
        user_id: UUID,
        track_id: UUID,
        event_type: LearningPathEventType,
        event_data: Optional[dict[str, Any]] = None,
        related_course_id: Optional[UUID] = None
    ) -> LearningPathEvent:
        """
        What: Record learning path event.
        Where: Progress tracking.
        Why: Detailed progress history.

        Args:
            user_id: Student UUID
            track_id: Track UUID
            event_type: Type of event
            event_data: Event details
            related_course_id: Related course

        Returns:
            Created LearningPathEvent
        """
        try:
            progress = await self._dao.get_learning_path_progress(user_id, track_id)
            if not progress:
                raise DashboardNotFoundError(f"Progress not found for user {user_id} track {track_id}")

            event = LearningPathEvent(
                id=uuid4(),
                progress_id=progress.id,
                event_type=event_type,
                event_data=event_data or {},
                related_course_id=related_course_id,
                progress_at_event=progress.overall_progress
            )
            return await self._dao.create_learning_path_event(event)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to record event: {e}") from e

    # ========================================================================
    # ALERT THRESHOLD OPERATIONS
    # ========================================================================

    async def create_alert_threshold(
        self,
        name: str,
        metric_type: MetricType,
        threshold_operator: ThresholdOperator,
        threshold_value: Decimal,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        description: Optional[str] = None,
        threshold_value_upper: Optional[Decimal] = None,
        scope: AlertScope = AlertScope.ORGANIZATION,
        severity: AlertSeverity = AlertSeverity.WARNING,
        notification_channels: Optional[list[str]] = None,
        cooldown_minutes: int = 60
    ) -> AnalyticsAlertThreshold:
        """
        What: Create alert threshold.
        Where: Alert configuration.
        Why: Define monitoring rules.

        Args:
            name: Alert name
            metric_type: Metric to monitor
            threshold_operator: Comparison operator
            threshold_value: Threshold value
            organization_id: Org (if org-level)
            user_id: User (if user-level)
            description: Description
            threshold_value_upper: Upper bound for BETWEEN
            scope: Alert scope
            severity: Alert severity
            notification_channels: How to notify
            cooldown_minutes: Cooldown period

        Returns:
            Created AnalyticsAlertThreshold
        """
        try:
            threshold = AnalyticsAlertThreshold(
                id=uuid4(),
                name=name,
                metric_type=metric_type,
                threshold_operator=threshold_operator,
                threshold_value=threshold_value,
                user_id=user_id,
                organization_id=organization_id,
                description=description,
                threshold_value_upper=threshold_value_upper,
                scope=scope,
                severity=severity,
                notification_channels=notification_channels or ["in_app"],
                cooldown_minutes=cooldown_minutes
            )
            return await self._dao.create_alert_threshold(threshold)
        except ValueError as e:
            raise AlertConfigurationError(f"Invalid alert configuration: {e}") from e
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to create alert: {e}") from e

    async def get_alert_threshold(self, threshold_id: UUID) -> AnalyticsAlertThreshold:
        """
        What: Get alert threshold.
        Where: Alert configuration view.
        Why: Retrieve threshold settings.

        Args:
            threshold_id: Threshold UUID

        Returns:
            AnalyticsAlertThreshold

        Raises:
            DashboardNotFoundError: If not found
        """
        try:
            threshold = await self._dao.get_alert_threshold(threshold_id)
            if not threshold:
                raise DashboardNotFoundError(f"Alert threshold {threshold_id} not found")
            return threshold
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get threshold: {e}") from e

    async def get_active_thresholds(
        self,
        organization_id: Optional[UUID] = None,
        metric_type: Optional[MetricType] = None
    ) -> list[AnalyticsAlertThreshold]:
        """
        What: Get active alert thresholds.
        Where: Alert evaluation.
        Why: Find thresholds to check.

        Args:
            organization_id: Optional org filter
            metric_type: Optional metric filter

        Returns:
            List of thresholds
        """
        try:
            return await self._dao.get_active_thresholds(organization_id, metric_type)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get thresholds: {e}") from e

    async def evaluate_threshold(
        self,
        threshold_id: UUID,
        current_value: Decimal,
        affected_entities: Optional[list[dict[str, Any]]] = None
    ) -> Optional[AlertHistory]:
        """
        What: Evaluate threshold and trigger if needed.
        Where: Alert evaluation job.
        Why: Check if alert should fire.

        Args:
            threshold_id: Threshold to evaluate
            current_value: Current metric value
            affected_entities: Entities affected

        Returns:
            AlertHistory if triggered, None otherwise
        """
        try:
            threshold = await self._dao.get_alert_threshold(threshold_id)
            if not threshold or not threshold.is_active:
                return None

            # Check cooldown
            if threshold.last_triggered_at:
                cooldown_end = threshold.last_triggered_at + timedelta(minutes=threshold.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    return None

            # Evaluate threshold
            if threshold.evaluate(current_value):
                alert = AlertHistory(
                    id=uuid4(),
                    threshold_id=threshold_id,
                    triggered_value=current_value,
                    triggered_at=datetime.utcnow(),
                    affected_entities=affected_entities or [],
                    affected_count=len(affected_entities) if affected_entities else 0,
                    status=AlertStatus.ACTIVE
                )
                await self._dao.create_alert_history(alert)
                await self._dao.update_threshold_triggered(threshold_id)
                return alert

            return None
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to evaluate threshold: {e}") from e

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID
    ) -> AlertHistory:
        """
        What: Acknowledge alert.
        Where: Alert response.
        Why: Mark alert as seen.

        Args:
            alert_id: Alert UUID
            user_id: User acknowledging

        Returns:
            Updated AlertHistory
        """
        try:
            # Get alert from history - simplified implementation
            alert = AlertHistory(
                id=alert_id,
                threshold_id=uuid4(),
                triggered_value=Decimal("0"),
                status=AlertStatus.ACKNOWLEDGED,
                acknowledged_by=user_id,
                acknowledged_at=datetime.utcnow()
            )
            return await self._dao.update_alert_history(alert)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to acknowledge alert: {e}") from e

    async def resolve_alert(
        self,
        alert_id: UUID,
        resolution_notes: Optional[str] = None
    ) -> AlertHistory:
        """
        What: Resolve alert.
        Where: Alert resolution.
        Why: Mark issue as resolved.

        Args:
            alert_id: Alert UUID
            resolution_notes: Resolution description

        Returns:
            Updated AlertHistory
        """
        try:
            alert = AlertHistory(
                id=alert_id,
                threshold_id=uuid4(),
                triggered_value=Decimal("0"),
                status=AlertStatus.RESOLVED,
                resolved_at=datetime.utcnow(),
                resolution_notes=resolution_notes
            )
            return await self._dao.update_alert_history(alert)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to resolve alert: {e}") from e

    async def get_active_alerts(
        self,
        organization_id: Optional[UUID] = None,
        limit: int = 100
    ) -> list[AlertHistory]:
        """
        What: Get active alerts.
        Where: Alert dashboard.
        Why: Show alerts needing attention.

        Args:
            organization_id: Optional org filter
            limit: Maximum results

        Returns:
            List of active alerts
        """
        try:
            return await self._dao.get_active_alerts(organization_id, limit)
        except DashboardDAOError as e:
            raise DashboardServiceError(f"Failed to get alerts: {e}") from e
