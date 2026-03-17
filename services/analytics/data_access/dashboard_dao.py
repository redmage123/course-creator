"""
Learning Analytics Dashboard Data Access Object

What: DAO for dashboard configuration, widgets, scheduled reports,
      cohort analytics, and learning path tracking database operations.

Where: Data access layer for the Analytics service, extending existing
       analytics DAO with dashboard-specific persistence.

Why: Provides clean separation between domain logic and database operations.
     Encapsulates all SQL queries for dashboard features with:
     1. Dashboard template and user dashboard CRUD
     2. Widget instance management
     3. Scheduled report configuration
     4. Cohort membership and snapshot tracking
     5. Learning path progress persistence
     6. Alert threshold configuration and history
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from asyncpg import Pool

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


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class DashboardDAOError(Exception):
    """
    What: Base exception for Dashboard DAO operations.
    Where: Raised when database operations fail.
    Why: Provides consistent error handling for dashboard data access.
    """
    pass


class DashboardTemplateNotFoundError(DashboardDAOError):
    """Raised when dashboard template is not found."""
    pass


class UserDashboardNotFoundError(DashboardDAOError):
    """Raised when user dashboard is not found."""
    pass


class WidgetNotFoundError(DashboardDAOError):
    """Raised when widget is not found."""
    pass


class ReportTemplateNotFoundError(DashboardDAOError):
    """Raised when report template is not found."""
    pass


class ScheduledReportNotFoundError(DashboardDAOError):
    """Raised when scheduled report is not found."""
    pass


class CohortNotFoundError(DashboardDAOError):
    """Raised when cohort is not found."""
    pass


class LearningPathProgressNotFoundError(DashboardDAOError):
    """Raised when learning path progress is not found."""
    pass


class AlertThresholdNotFoundError(DashboardDAOError):
    """Raised when alert threshold is not found."""
    pass


# ============================================================================
# DASHBOARD DAO
# ============================================================================

class DashboardDAO:
    """
    What: Data Access Object for Learning Analytics Dashboard.
    Where: Analytics service data layer.
    Why: Encapsulates all database operations for dashboard features
         with proper error handling and entity mapping.
    """

    def __init__(self, pool: Pool):
        """
        What: Initialize DAO with database connection pool.
        Where: Called by dependency injection container.
        Why: Pool management enables connection reuse and efficiency.

        Args:
            pool: AsyncPG connection pool
        """
        self._pool = pool

    # ========================================================================
    # DASHBOARD TEMPLATE OPERATIONS
    # ========================================================================

    async def create_dashboard_template(self, template: DashboardTemplate) -> DashboardTemplate:
        """
        What: Create a new dashboard template.
        Where: System/org admin creates template.
        Why: Provides default layouts for different roles.

        Args:
            template: DashboardTemplate entity to create

        Returns:
            Created DashboardTemplate with generated ID

        Raises:
            DashboardDAOError: If creation fails
        """
        query = """
            INSERT INTO dashboard_templates (
                id, name, description, target_role, layout_config,
                is_default, scope, organization_id, created_by,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    template.id,
                    template.name,
                    template.description,
                    template.target_role.value,
                    template.layout_config.to_dict(),
                    template.is_default,
                    template.scope.value,
                    template.organization_id,
                    template.created_by,
                    datetime.utcnow()
                )
                template.created_at = row["created_at"]
                template.updated_at = row["updated_at"]
                return template
        except Exception as e:
            raise DashboardDAOError(f"Failed to create dashboard template: {e}") from e

    async def get_dashboard_template(self, template_id: UUID) -> Optional[DashboardTemplate]:
        """
        What: Retrieve dashboard template by ID.
        Where: Used when loading template details.
        Why: Fetch template configuration for display/editing.

        Args:
            template_id: UUID of template to retrieve

        Returns:
            DashboardTemplate if found, None otherwise
        """
        query = """
            SELECT id, name, description, target_role, layout_config,
                   is_default, scope, organization_id, created_by,
                   created_at, updated_at
            FROM dashboard_templates
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, template_id)
                if not row:
                    return None
                return self._map_dashboard_template(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get dashboard template: {e}") from e

    async def get_templates_by_role(
        self,
        target_role: UserRole,
        organization_id: Optional[UUID] = None
    ) -> list[DashboardTemplate]:
        """
        What: Get templates available for a specific role.
        Where: Dashboard selection UI.
        Why: Show role-appropriate template options.

        Args:
            target_role: Role to filter templates for
            organization_id: Optional org filter for org-scoped templates

        Returns:
            List of available DashboardTemplates
        """
        query = """
            SELECT id, name, description, target_role, layout_config,
                   is_default, scope, organization_id, created_by,
                   created_at, updated_at
            FROM dashboard_templates
            WHERE target_role = $1
              AND (scope = 'platform'
                   OR (scope = 'organization' AND organization_id = $2))
            ORDER BY is_default DESC, name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, target_role.value, organization_id)
                return [self._map_dashboard_template(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get templates by role: {e}") from e

    async def get_default_template(
        self,
        target_role: UserRole,
        organization_id: Optional[UUID] = None
    ) -> Optional[DashboardTemplate]:
        """
        What: Get the default template for a role.
        Where: First-time dashboard access.
        Why: Provides sensible default when user has no dashboard.

        Args:
            target_role: Role to get default for
            organization_id: Optional org for org-specific defaults

        Returns:
            Default template if exists, None otherwise
        """
        query = """
            SELECT id, name, description, target_role, layout_config,
                   is_default, scope, organization_id, created_by,
                   created_at, updated_at
            FROM dashboard_templates
            WHERE target_role = $1
              AND is_default = true
              AND (scope = 'platform'
                   OR (scope = 'organization' AND organization_id = $2))
            ORDER BY scope DESC
            LIMIT 1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, target_role.value, organization_id)
                if not row:
                    return None
                return self._map_dashboard_template(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get default template: {e}") from e

    async def update_dashboard_template(self, template: DashboardTemplate) -> DashboardTemplate:
        """
        What: Update existing dashboard template.
        Where: Admin edits template configuration.
        Why: Modify template layout or settings.

        Args:
            template: DashboardTemplate with updated values

        Returns:
            Updated DashboardTemplate

        Raises:
            DashboardTemplateNotFoundError: If template doesn't exist
        """
        query = """
            UPDATE dashboard_templates
            SET name = $2, description = $3, layout_config = $4,
                is_default = $5, updated_at = $6
            WHERE id = $1
            RETURNING updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    template.id,
                    template.name,
                    template.description,
                    template.layout_config.to_dict(),
                    template.is_default,
                    datetime.utcnow()
                )
                if not row:
                    raise DashboardTemplateNotFoundError(f"Template {template.id} not found")
                template.updated_at = row["updated_at"]
                return template
        except DashboardTemplateNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update dashboard template: {e}") from e

    async def delete_dashboard_template(self, template_id: UUID) -> bool:
        """
        What: Delete a dashboard template.
        Where: Admin removes unused template.
        Why: Clean up obsolete templates.

        Args:
            template_id: UUID of template to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM dashboard_templates WHERE id = $1 RETURNING id"
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, template_id)
                return row is not None
        except Exception as e:
            raise DashboardDAOError(f"Failed to delete dashboard template: {e}") from e

    # ========================================================================
    # USER DASHBOARD OPERATIONS
    # ========================================================================

    async def create_user_dashboard(self, dashboard: UserDashboard) -> UserDashboard:
        """
        What: Create a user's personal dashboard.
        Where: User creates new dashboard or first access.
        Why: Store user's customized layout.

        Args:
            dashboard: UserDashboard entity to create

        Returns:
            Created UserDashboard with generated ID
        """
        query = """
            INSERT INTO user_dashboards (
                id, user_id, name, template_id, layout_config,
                preferences, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    dashboard.id,
                    dashboard.user_id,
                    dashboard.name,
                    dashboard.template_id,
                    dashboard.layout_config.to_dict(),
                    dashboard.preferences.to_dict() if dashboard.preferences else {},
                    dashboard.is_active,
                    datetime.utcnow()
                )
                dashboard.created_at = row["created_at"]
                dashboard.updated_at = row["updated_at"]
                return dashboard
        except Exception as e:
            raise DashboardDAOError(f"Failed to create user dashboard: {e}") from e

    async def get_user_dashboard(self, dashboard_id: UUID) -> Optional[UserDashboard]:
        """
        What: Get user dashboard by ID.
        Where: Load specific dashboard.
        Why: Retrieve dashboard configuration.

        Args:
            dashboard_id: UUID of dashboard

        Returns:
            UserDashboard if found, None otherwise
        """
        query = """
            SELECT id, user_id, name, template_id, layout_config,
                   preferences, is_active, last_accessed_at,
                   created_at, updated_at
            FROM user_dashboards
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, dashboard_id)
                if not row:
                    return None
                return self._map_user_dashboard(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get user dashboard: {e}") from e

    async def get_user_dashboards(self, user_id: UUID) -> list[UserDashboard]:
        """
        What: Get all dashboards for a user.
        Where: Dashboard list view.
        Why: Show user's available dashboards.

        Args:
            user_id: User's UUID

        Returns:
            List of user's dashboards
        """
        query = """
            SELECT id, user_id, name, template_id, layout_config,
                   preferences, is_active, last_accessed_at,
                   created_at, updated_at
            FROM user_dashboards
            WHERE user_id = $1 AND is_active = true
            ORDER BY last_accessed_at DESC NULLS LAST, name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._map_user_dashboard(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get user dashboards: {e}") from e

    async def update_user_dashboard(self, dashboard: UserDashboard) -> UserDashboard:
        """
        What: Update user dashboard configuration.
        Where: User saves dashboard changes.
        Why: Persist layout customizations.

        Args:
            dashboard: UserDashboard with updates

        Returns:
            Updated UserDashboard
        """
        query = """
            UPDATE user_dashboards
            SET name = $2, layout_config = $3, preferences = $4,
                updated_at = $5
            WHERE id = $1
            RETURNING updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    dashboard.id,
                    dashboard.name,
                    dashboard.layout_config.to_dict(),
                    dashboard.preferences.to_dict() if dashboard.preferences else {},
                    datetime.utcnow()
                )
                if not row:
                    raise UserDashboardNotFoundError(f"Dashboard {dashboard.id} not found")
                dashboard.updated_at = row["updated_at"]
                return dashboard
        except UserDashboardNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update user dashboard: {e}") from e

    async def update_dashboard_access_time(self, dashboard_id: UUID) -> None:
        """
        What: Update last accessed timestamp.
        Where: User opens dashboard.
        Why: Track usage for sorting and analytics.

        Args:
            dashboard_id: Dashboard to update
        """
        query = """
            UPDATE user_dashboards
            SET last_accessed_at = $2
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(query, dashboard_id, datetime.utcnow())
        except Exception as e:
            raise DashboardDAOError(f"Failed to update access time: {e}") from e

    async def delete_user_dashboard(self, dashboard_id: UUID) -> bool:
        """
        What: Soft delete user dashboard.
        Where: User removes dashboard.
        Why: Mark as inactive but preserve data.

        Args:
            dashboard_id: Dashboard to delete

        Returns:
            True if deleted, False if not found
        """
        query = """
            UPDATE user_dashboards
            SET is_active = false, updated_at = $2
            WHERE id = $1
            RETURNING id
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, dashboard_id, datetime.utcnow())
                return row is not None
        except Exception as e:
            raise DashboardDAOError(f"Failed to delete user dashboard: {e}") from e

    # ========================================================================
    # WIDGET OPERATIONS
    # ========================================================================

    async def get_widget(self, widget_id: UUID) -> Optional[DashboardWidget]:
        """
        What: Get widget definition by ID.
        Where: Load widget details.
        Why: Retrieve widget configuration.

        Args:
            widget_id: Widget UUID

        Returns:
            DashboardWidget if found
        """
        query = """
            SELECT id, widget_type, name, description, default_width,
                   default_height, min_width, min_height, data_source,
                   config_schema, default_config, allowed_roles,
                   is_active, created_at, updated_at
            FROM dashboard_widgets
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, widget_id)
                if not row:
                    return None
                return self._map_dashboard_widget(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get widget: {e}") from e

    async def get_widgets_for_role(self, role: UserRole) -> list[DashboardWidget]:
        """
        What: Get all widgets available for a role.
        Where: Widget selector UI.
        Why: Show role-appropriate widgets.

        Args:
            role: User role

        Returns:
            List of available widgets
        """
        query = """
            SELECT id, widget_type, name, description, default_width,
                   default_height, min_width, min_height, data_source,
                   config_schema, default_config, allowed_roles,
                   is_active, created_at, updated_at
            FROM dashboard_widgets
            WHERE is_active = true
              AND $1 = ANY(allowed_roles)
            ORDER BY name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, role.value)
                return [self._map_dashboard_widget(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get widgets for role: {e}") from e

    async def create_widget_instance(self, instance: WidgetInstance) -> WidgetInstance:
        """
        What: Add widget to dashboard.
        Where: User adds widget to layout.
        Why: Store widget placement and config.

        Args:
            instance: WidgetInstance to create

        Returns:
            Created WidgetInstance
        """
        query = """
            INSERT INTO widget_instances (
                id, dashboard_id, widget_id, grid_x, grid_y,
                grid_width, grid_height, config, title_override,
                is_visible, display_order, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $12)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    instance.id,
                    instance.dashboard_id,
                    instance.widget_id,
                    instance.grid_x,
                    instance.grid_y,
                    instance.grid_width,
                    instance.grid_height,
                    instance.config,
                    instance.title_override,
                    instance.is_visible,
                    instance.display_order,
                    datetime.utcnow()
                )
                instance.created_at = row["created_at"]
                instance.updated_at = row["updated_at"]
                return instance
        except Exception as e:
            raise DashboardDAOError(f"Failed to create widget instance: {e}") from e

    async def get_widget_instances(self, dashboard_id: UUID) -> list[WidgetInstance]:
        """
        What: Get all widgets on a dashboard.
        Where: Loading dashboard.
        Why: Retrieve widget layout.

        Args:
            dashboard_id: Dashboard UUID

        Returns:
            List of widget instances
        """
        query = """
            SELECT id, dashboard_id, widget_id, grid_x, grid_y,
                   grid_width, grid_height, config, title_override,
                   is_visible, display_order, created_at, updated_at
            FROM widget_instances
            WHERE dashboard_id = $1
            ORDER BY display_order ASC, grid_y ASC, grid_x ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, dashboard_id)
                return [self._map_widget_instance(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get widget instances: {e}") from e

    async def update_widget_instance(self, instance: WidgetInstance) -> WidgetInstance:
        """
        What: Update widget position/config.
        Where: User moves or configures widget.
        Why: Save widget changes.

        Args:
            instance: WidgetInstance with updates

        Returns:
            Updated WidgetInstance
        """
        query = """
            UPDATE widget_instances
            SET grid_x = $2, grid_y = $3, grid_width = $4, grid_height = $5,
                config = $6, title_override = $7, is_visible = $8,
                display_order = $9, updated_at = $10
            WHERE id = $1
            RETURNING updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    instance.id,
                    instance.grid_x,
                    instance.grid_y,
                    instance.grid_width,
                    instance.grid_height,
                    instance.config,
                    instance.title_override,
                    instance.is_visible,
                    instance.display_order,
                    datetime.utcnow()
                )
                if not row:
                    raise WidgetNotFoundError(f"Widget instance {instance.id} not found")
                instance.updated_at = row["updated_at"]
                return instance
        except WidgetNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update widget instance: {e}") from e

    async def delete_widget_instance(self, instance_id: UUID) -> bool:
        """
        What: Remove widget from dashboard.
        Where: User deletes widget.
        Why: Clean up unwanted widgets.

        Args:
            instance_id: Instance to delete

        Returns:
            True if deleted
        """
        query = "DELETE FROM widget_instances WHERE id = $1 RETURNING id"
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, instance_id)
                return row is not None
        except Exception as e:
            raise DashboardDAOError(f"Failed to delete widget instance: {e}") from e

    # ========================================================================
    # SCHEDULED REPORT OPERATIONS
    # ========================================================================

    async def create_report_template(self, template: ReportTemplate) -> ReportTemplate:
        """
        What: Create report template.
        Where: Admin defines reusable report.
        Why: Enable consistent report generation.

        Args:
            template: ReportTemplate to create

        Returns:
            Created ReportTemplate
        """
        query = """
            INSERT INTO report_templates (
                id, name, description, report_type, config,
                output_formats, scope, organization_id, created_by,
                is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    template.id,
                    template.name,
                    template.description,
                    template.report_type.value,
                    template.config.to_dict(),
                    [fmt.value for fmt in template.output_formats],
                    template.scope.value,
                    template.organization_id,
                    template.created_by,
                    template.is_active,
                    datetime.utcnow()
                )
                template.created_at = row["created_at"]
                template.updated_at = row["updated_at"]
                return template
        except Exception as e:
            raise DashboardDAOError(f"Failed to create report template: {e}") from e

    async def get_report_template(self, template_id: UUID) -> Optional[ReportTemplate]:
        """
        What: Get report template by ID.
        Where: Load template details.
        Why: Retrieve template configuration.

        Args:
            template_id: Template UUID

        Returns:
            ReportTemplate if found
        """
        query = """
            SELECT id, name, description, report_type, config,
                   output_formats, scope, organization_id, created_by,
                   is_active, created_at, updated_at
            FROM report_templates
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, template_id)
                if not row:
                    return None
                return self._map_report_template(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get report template: {e}") from e

    async def get_report_templates(
        self,
        organization_id: Optional[UUID] = None,
        report_type: Optional[ReportType] = None
    ) -> list[ReportTemplate]:
        """
        What: Get available report templates.
        Where: Report creation UI.
        Why: Show available report options.

        Args:
            organization_id: Optional org filter
            report_type: Optional type filter

        Returns:
            List of available templates
        """
        query = """
            SELECT id, name, description, report_type, config,
                   output_formats, scope, organization_id, created_by,
                   is_active, created_at, updated_at
            FROM report_templates
            WHERE is_active = true
              AND (scope = 'platform'
                   OR (scope = 'organization' AND organization_id = $1))
              AND ($2::text IS NULL OR report_type = $2)
            ORDER BY name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    query,
                    organization_id,
                    report_type.value if report_type else None
                )
                return [self._map_report_template(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get report templates: {e}") from e

    async def create_scheduled_report(self, report: ScheduledReport) -> ScheduledReport:
        """
        What: Create scheduled report.
        Where: User schedules automated report.
        Why: Enable periodic report delivery.

        Args:
            report: ScheduledReport to create

        Returns:
            Created ScheduledReport
        """
        query = """
            INSERT INTO scheduled_reports (
                id, user_id, template_id, name, schedule_type,
                schedule_cron, schedule_day, schedule_time, schedule_timezone,
                config_overrides, output_format, delivery_method, delivery_config,
                recipients, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $16)
            RETURNING id, next_run_at, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    report.id,
                    report.user_id,
                    report.template_id,
                    report.name,
                    report.schedule_type.value,
                    report.schedule_cron,
                    report.schedule_day,
                    report.schedule_time,
                    report.schedule_timezone,
                    report.config_overrides,
                    report.output_format.value,
                    report.delivery_method.value,
                    report.delivery_config.to_dict() if report.delivery_config else {},
                    report.recipients,
                    report.is_active,
                    datetime.utcnow()
                )
                report.next_run_at = row["next_run_at"]
                report.created_at = row["created_at"]
                report.updated_at = row["updated_at"]
                return report
        except Exception as e:
            raise DashboardDAOError(f"Failed to create scheduled report: {e}") from e

    async def get_scheduled_report(self, report_id: UUID) -> Optional[ScheduledReport]:
        """
        What: Get scheduled report by ID.
        Where: Load report details.
        Why: Retrieve schedule configuration.

        Args:
            report_id: Report UUID

        Returns:
            ScheduledReport if found
        """
        query = """
            SELECT id, user_id, template_id, name, schedule_type,
                   schedule_cron, schedule_day, schedule_time, schedule_timezone,
                   config_overrides, output_format, delivery_method, delivery_config,
                   recipients, is_active, next_run_at, last_run_at, last_run_status,
                   created_at, updated_at
            FROM scheduled_reports
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, report_id)
                if not row:
                    return None
                return self._map_scheduled_report(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get scheduled report: {e}") from e

    async def get_user_scheduled_reports(self, user_id: UUID) -> list[ScheduledReport]:
        """
        What: Get user's scheduled reports.
        Where: Report management UI.
        Why: List user's report schedules.

        Args:
            user_id: User's UUID

        Returns:
            List of user's scheduled reports
        """
        query = """
            SELECT id, user_id, template_id, name, schedule_type,
                   schedule_cron, schedule_day, schedule_time, schedule_timezone,
                   config_overrides, output_format, delivery_method, delivery_config,
                   recipients, is_active, next_run_at, last_run_at, last_run_status,
                   created_at, updated_at
            FROM scheduled_reports
            WHERE user_id = $1
            ORDER BY is_active DESC, name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._map_scheduled_report(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get user scheduled reports: {e}") from e

    async def get_due_scheduled_reports(self, limit: int = 100) -> list[ScheduledReport]:
        """
        What: Get reports due for execution.
        Where: Report scheduler service.
        Why: Find reports to generate.

        Args:
            limit: Maximum reports to return

        Returns:
            List of due reports
        """
        query = """
            SELECT id, user_id, template_id, name, schedule_type,
                   schedule_cron, schedule_day, schedule_time, schedule_timezone,
                   config_overrides, output_format, delivery_method, delivery_config,
                   recipients, is_active, next_run_at, last_run_at, last_run_status,
                   created_at, updated_at
            FROM scheduled_reports
            WHERE is_active = true
              AND next_run_at <= CURRENT_TIMESTAMP
            ORDER BY next_run_at ASC
            LIMIT $1
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, limit)
                return [self._map_scheduled_report(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get due scheduled reports: {e}") from e

    async def update_scheduled_report(self, report: ScheduledReport) -> ScheduledReport:
        """
        What: Update scheduled report.
        Where: User modifies schedule.
        Why: Save configuration changes.

        Args:
            report: ScheduledReport with updates

        Returns:
            Updated ScheduledReport
        """
        query = """
            UPDATE scheduled_reports
            SET name = $2, schedule_type = $3, schedule_cron = $4,
                schedule_day = $5, schedule_time = $6, schedule_timezone = $7,
                config_overrides = $8, output_format = $9, delivery_method = $10,
                delivery_config = $11, recipients = $12, is_active = $13,
                updated_at = $14
            WHERE id = $1
            RETURNING next_run_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    report.id,
                    report.name,
                    report.schedule_type.value,
                    report.schedule_cron,
                    report.schedule_day,
                    report.schedule_time,
                    report.schedule_timezone,
                    report.config_overrides,
                    report.output_format.value,
                    report.delivery_method.value,
                    report.delivery_config.to_dict() if report.delivery_config else {},
                    report.recipients,
                    report.is_active,
                    datetime.utcnow()
                )
                if not row:
                    raise ScheduledReportNotFoundError(f"Report {report.id} not found")
                report.next_run_at = row["next_run_at"]
                report.updated_at = row["updated_at"]
                return report
        except ScheduledReportNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update scheduled report: {e}") from e

    async def update_report_run_status(
        self,
        report_id: UUID,
        status: str,
        next_run_at: Optional[datetime] = None
    ) -> None:
        """
        What: Update report execution status.
        Where: After report generation.
        Why: Track execution history.

        Args:
            report_id: Report UUID
            status: Execution status
            next_run_at: Next scheduled run time
        """
        query = """
            UPDATE scheduled_reports
            SET last_run_at = CURRENT_TIMESTAMP,
                last_run_status = $2,
                next_run_at = COALESCE($3, next_run_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(query, report_id, status, next_run_at)
        except Exception as e:
            raise DashboardDAOError(f"Failed to update report run status: {e}") from e

    async def create_report_execution(self, execution: ReportExecution) -> ReportExecution:
        """
        What: Record report execution.
        Where: Report generation starts.
        Why: Track generation progress.

        Args:
            execution: ReportExecution to create

        Returns:
            Created ReportExecution
        """
        query = """
            INSERT INTO report_executions (
                id, scheduled_report_id, template_id, user_id, status,
                parameters, date_range_start, date_range_end, output_format,
                started_at, expires_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id, created_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    execution.id,
                    execution.scheduled_report_id,
                    execution.template_id,
                    execution.user_id,
                    execution.status.value,
                    execution.parameters,
                    execution.date_range_start,
                    execution.date_range_end,
                    execution.output_format.value if execution.output_format else None,
                    execution.started_at,
                    execution.expires_at,
                    datetime.utcnow()
                )
                execution.created_at = row["created_at"]
                return execution
        except Exception as e:
            raise DashboardDAOError(f"Failed to create report execution: {e}") from e

    async def update_report_execution(self, execution: ReportExecution) -> ReportExecution:
        """
        What: Update report execution status.
        Where: During/after generation.
        Why: Track progress and completion.

        Args:
            execution: ReportExecution with updates

        Returns:
            Updated ReportExecution
        """
        query = """
            UPDATE report_executions
            SET status = $2, file_path = $3, file_size_bytes = $4,
                file_checksum = $5, completed_at = $6, generation_time_ms = $7,
                error_message = $8, error_details = $9
            WHERE id = $1
            RETURNING id
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    execution.id,
                    execution.status.value,
                    execution.file_path,
                    execution.file_size_bytes,
                    execution.file_checksum,
                    execution.completed_at,
                    execution.generation_time_ms,
                    execution.error_message,
                    execution.error_details
                )
                if not row:
                    raise DashboardDAOError(f"Execution {execution.id} not found")
                return execution
        except Exception as e:
            raise DashboardDAOError(f"Failed to update report execution: {e}") from e

    async def get_user_report_executions(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> list[ReportExecution]:
        """
        What: Get user's report execution history.
        Where: Report history view.
        Why: Show past generated reports.

        Args:
            user_id: User's UUID
            limit: Maximum results

        Returns:
            List of report executions
        """
        query = """
            SELECT id, scheduled_report_id, template_id, user_id, status,
                   parameters, date_range_start, date_range_end, output_format,
                   file_path, file_size_bytes, file_checksum,
                   started_at, completed_at, generation_time_ms,
                   error_message, error_details, expires_at, created_at
            FROM report_executions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, limit)
                return [self._map_report_execution(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get user report executions: {e}") from e

    # ========================================================================
    # COHORT OPERATIONS
    # ========================================================================

    async def create_cohort(self, cohort: AnalyticsCohort) -> AnalyticsCohort:
        """
        What: Create analytics cohort.
        Where: Admin creates student group.
        Why: Enable cohort-based analysis.

        Args:
            cohort: AnalyticsCohort to create

        Returns:
            Created AnalyticsCohort
        """
        query = """
            INSERT INTO analytics_cohorts (
                id, organization_id, name, description, cohort_type,
                membership_rules, linked_course_id, linked_track_id,
                tags, created_by, is_active, member_count,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $13)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    cohort.id,
                    cohort.organization_id,
                    cohort.name,
                    cohort.description,
                    cohort.cohort_type.value,
                    cohort.membership_rules.to_dict() if cohort.membership_rules else {},
                    cohort.linked_course_id,
                    cohort.linked_track_id,
                    cohort.tags,
                    cohort.created_by,
                    cohort.is_active,
                    cohort.member_count,
                    datetime.utcnow()
                )
                cohort.created_at = row["created_at"]
                cohort.updated_at = row["updated_at"]
                return cohort
        except Exception as e:
            raise DashboardDAOError(f"Failed to create cohort: {e}") from e

    async def get_cohort(self, cohort_id: UUID) -> Optional[AnalyticsCohort]:
        """
        What: Get cohort by ID.
        Where: Load cohort details.
        Why: Retrieve cohort configuration.

        Args:
            cohort_id: Cohort UUID

        Returns:
            AnalyticsCohort if found
        """
        query = """
            SELECT id, organization_id, name, description, cohort_type,
                   membership_rules, linked_course_id, linked_track_id,
                   tags, created_by, is_active, member_count,
                   created_at, updated_at
            FROM analytics_cohorts
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, cohort_id)
                if not row:
                    return None
                return self._map_cohort(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get cohort: {e}") from e

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
        query = """
            SELECT id, organization_id, name, description, cohort_type,
                   membership_rules, linked_course_id, linked_track_id,
                   tags, created_by, is_active, member_count,
                   created_at, updated_at
            FROM analytics_cohorts
            WHERE organization_id = $1
              AND is_active = true
              AND ($2::text IS NULL OR cohort_type = $2)
            ORDER BY name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    query,
                    organization_id,
                    cohort_type.value if cohort_type else None
                )
                return [self._map_cohort(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get organization cohorts: {e}") from e

    async def add_cohort_member(self, member: CohortMember) -> CohortMember:
        """
        What: Add student to cohort.
        Where: Cohort membership management.
        Why: Track cohort membership.

        Args:
            member: CohortMember to add

        Returns:
            Created CohortMember
        """
        query = """
            INSERT INTO cohort_members (
                id, cohort_id, user_id, joined_at, is_active
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (cohort_id, user_id) DO UPDATE
            SET is_active = $5, left_at = NULL
            RETURNING id, joined_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    member.id,
                    member.cohort_id,
                    member.user_id,
                    member.joined_at or datetime.utcnow(),
                    member.is_active
                )
                member.joined_at = row["joined_at"]
                return member
        except Exception as e:
            raise DashboardDAOError(f"Failed to add cohort member: {e}") from e

    async def remove_cohort_member(self, cohort_id: UUID, user_id: UUID) -> bool:
        """
        What: Remove student from cohort.
        Where: Cohort membership management.
        Why: Track membership changes.

        Args:
            cohort_id: Cohort UUID
            user_id: User UUID

        Returns:
            True if removed
        """
        query = """
            UPDATE cohort_members
            SET is_active = false, left_at = CURRENT_TIMESTAMP
            WHERE cohort_id = $1 AND user_id = $2 AND is_active = true
            RETURNING id
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, cohort_id, user_id)
                return row is not None
        except Exception as e:
            raise DashboardDAOError(f"Failed to remove cohort member: {e}") from e

    async def get_cohort_members(self, cohort_id: UUID) -> list[CohortMember]:
        """
        What: Get all members of a cohort.
        Where: Cohort detail view.
        Why: List cohort membership.

        Args:
            cohort_id: Cohort UUID

        Returns:
            List of cohort members
        """
        query = """
            SELECT id, cohort_id, user_id, joined_at, is_active, left_at
            FROM cohort_members
            WHERE cohort_id = $1 AND is_active = true
            ORDER BY joined_at ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, cohort_id)
                return [self._map_cohort_member(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get cohort members: {e}") from e

    async def create_cohort_snapshot(self, snapshot: CohortSnapshot) -> CohortSnapshot:
        """
        What: Create cohort metrics snapshot.
        Where: Scheduled snapshot job.
        Why: Enable historical trend analysis.

        Args:
            snapshot: CohortSnapshot to create

        Returns:
            Created CohortSnapshot
        """
        query = """
            INSERT INTO cohort_snapshots (
                id, cohort_id, snapshot_date, member_count,
                avg_completion_rate, avg_quiz_score, avg_engagement_score,
                avg_time_spent_minutes, completion_distribution, score_distribution,
                active_member_count, at_risk_count, completed_count, metrics,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (cohort_id, snapshot_date) DO UPDATE
            SET member_count = $4, avg_completion_rate = $5, avg_quiz_score = $6,
                avg_engagement_score = $7, avg_time_spent_minutes = $8,
                completion_distribution = $9, score_distribution = $10,
                active_member_count = $11, at_risk_count = $12, completed_count = $13,
                metrics = $14
            RETURNING id, created_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    snapshot.id,
                    snapshot.cohort_id,
                    snapshot.snapshot_date,
                    snapshot.member_count,
                    snapshot.avg_completion_rate,
                    snapshot.avg_quiz_score,
                    snapshot.avg_engagement_score,
                    snapshot.avg_time_spent_minutes,
                    snapshot.completion_distribution.to_dict() if snapshot.completion_distribution else {},
                    snapshot.score_distribution.to_dict() if snapshot.score_distribution else {},
                    snapshot.active_member_count,
                    snapshot.at_risk_count,
                    snapshot.completed_count,
                    snapshot.metrics,
                    datetime.utcnow()
                )
                snapshot.created_at = row["created_at"]
                return snapshot
        except Exception as e:
            raise DashboardDAOError(f"Failed to create cohort snapshot: {e}") from e

    async def get_cohort_snapshots(
        self,
        cohort_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[CohortSnapshot]:
        """
        What: Get cohort snapshots in date range.
        Where: Trend analysis view.
        Why: Show cohort metrics over time.

        Args:
            cohort_id: Cohort UUID
            start_date: Optional start of range
            end_date: Optional end of range

        Returns:
            List of snapshots
        """
        query = """
            SELECT id, cohort_id, snapshot_date, member_count,
                   avg_completion_rate, avg_quiz_score, avg_engagement_score,
                   avg_time_spent_minutes, completion_distribution, score_distribution,
                   active_member_count, at_risk_count, completed_count, metrics,
                   created_at
            FROM cohort_snapshots
            WHERE cohort_id = $1
              AND ($2::date IS NULL OR snapshot_date >= $2)
              AND ($3::date IS NULL OR snapshot_date <= $3)
            ORDER BY snapshot_date DESC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, cohort_id, start_date, end_date)
                return [self._map_cohort_snapshot(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get cohort snapshots: {e}") from e

    # ========================================================================
    # LEARNING PATH OPERATIONS
    # ========================================================================

    async def create_learning_path_progress(
        self,
        progress: LearningPathProgress
    ) -> LearningPathProgress:
        """
        What: Create learning path progress record.
        Where: Student starts a track.
        Why: Track progress through learning path.

        Args:
            progress: LearningPathProgress to create

        Returns:
            Created LearningPathProgress
        """
        query = """
            INSERT INTO learning_path_progress (
                id, user_id, track_id, overall_progress, current_course_id,
                current_module_order, milestones_completed, started_at,
                estimated_completion_at, total_time_spent_minutes,
                avg_quiz_score, avg_assignment_score, status,
                last_activity_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $15)
            ON CONFLICT (user_id, track_id) DO UPDATE
            SET overall_progress = $4, current_course_id = $5,
                current_module_order = $6, status = $13,
                last_activity_at = $14, updated_at = $15
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    progress.id,
                    progress.user_id,
                    progress.track_id,
                    progress.overall_progress,
                    progress.current_course_id,
                    progress.current_module_order,
                    progress.milestones_completed,
                    progress.started_at,
                    progress.estimated_completion_at,
                    progress.total_time_spent_minutes,
                    progress.avg_quiz_score,
                    progress.avg_assignment_score,
                    progress.status.value,
                    progress.last_activity_at or datetime.utcnow(),
                    datetime.utcnow()
                )
                progress.created_at = row["created_at"]
                progress.updated_at = row["updated_at"]
                return progress
        except Exception as e:
            raise DashboardDAOError(f"Failed to create learning path progress: {e}") from e

    async def get_learning_path_progress(
        self,
        user_id: UUID,
        track_id: UUID
    ) -> Optional[LearningPathProgress]:
        """
        What: Get learning path progress.
        Where: Progress visualization.
        Why: Show student's position in path.

        Args:
            user_id: User UUID
            track_id: Track UUID

        Returns:
            LearningPathProgress if found
        """
        query = """
            SELECT id, user_id, track_id, overall_progress, current_course_id,
                   current_module_order, milestones_completed, started_at,
                   estimated_completion_at, actual_completion_at,
                   total_time_spent_minutes, avg_quiz_score, avg_assignment_score,
                   status, last_activity_at, created_at, updated_at
            FROM learning_path_progress
            WHERE user_id = $1 AND track_id = $2
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, track_id)
                if not row:
                    return None
                return self._map_learning_path_progress(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get learning path progress: {e}") from e

    async def get_user_learning_paths(self, user_id: UUID) -> list[LearningPathProgress]:
        """
        What: Get all learning paths for user.
        Where: User's learning dashboard.
        Why: Show all tracked learning paths.

        Args:
            user_id: User UUID

        Returns:
            List of learning path progress records
        """
        query = """
            SELECT id, user_id, track_id, overall_progress, current_course_id,
                   current_module_order, milestones_completed, started_at,
                   estimated_completion_at, actual_completion_at,
                   total_time_spent_minutes, avg_quiz_score, avg_assignment_score,
                   status, last_activity_at, created_at, updated_at
            FROM learning_path_progress
            WHERE user_id = $1
            ORDER BY last_activity_at DESC NULLS LAST
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._map_learning_path_progress(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get user learning paths: {e}") from e

    async def update_learning_path_progress(
        self,
        progress: LearningPathProgress
    ) -> LearningPathProgress:
        """
        What: Update learning path progress.
        Where: Progress tracking.
        Why: Record progress changes.

        Args:
            progress: LearningPathProgress with updates

        Returns:
            Updated LearningPathProgress
        """
        query = """
            UPDATE learning_path_progress
            SET overall_progress = $3, current_course_id = $4,
                current_module_order = $5, milestones_completed = $6,
                estimated_completion_at = $7, actual_completion_at = $8,
                total_time_spent_minutes = $9, avg_quiz_score = $10,
                avg_assignment_score = $11, status = $12,
                last_activity_at = $13, updated_at = $14
            WHERE user_id = $1 AND track_id = $2
            RETURNING updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    progress.user_id,
                    progress.track_id,
                    progress.overall_progress,
                    progress.current_course_id,
                    progress.current_module_order,
                    progress.milestones_completed,
                    progress.estimated_completion_at,
                    progress.actual_completion_at,
                    progress.total_time_spent_minutes,
                    progress.avg_quiz_score,
                    progress.avg_assignment_score,
                    progress.status.value,
                    progress.last_activity_at or datetime.utcnow(),
                    datetime.utcnow()
                )
                if not row:
                    raise LearningPathProgressNotFoundError(
                        f"Progress for user {progress.user_id} track {progress.track_id} not found"
                    )
                progress.updated_at = row["updated_at"]
                return progress
        except LearningPathProgressNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update learning path progress: {e}") from e

    async def create_learning_path_event(self, event: LearningPathEvent) -> LearningPathEvent:
        """
        What: Record learning path event.
        Where: Progress tracking.
        Why: Detailed progress history.

        Args:
            event: LearningPathEvent to create

        Returns:
            Created LearningPathEvent
        """
        query = """
            INSERT INTO learning_path_events (
                id, progress_id, event_type, event_data,
                related_course_id, related_module_id, progress_at_event,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, created_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    event.id,
                    event.progress_id,
                    event.event_type.value,
                    event.event_data,
                    event.related_course_id,
                    event.related_module_id,
                    event.progress_at_event,
                    datetime.utcnow()
                )
                event.created_at = row["created_at"]
                return event
        except Exception as e:
            raise DashboardDAOError(f"Failed to create learning path event: {e}") from e

    async def get_learning_path_events(
        self,
        progress_id: UUID,
        limit: int = 100
    ) -> list[LearningPathEvent]:
        """
        What: Get events for learning path.
        Where: Progress detail view.
        Why: Show progress history.

        Args:
            progress_id: Progress UUID
            limit: Maximum events

        Returns:
            List of events
        """
        query = """
            SELECT id, progress_id, event_type, event_data,
                   related_course_id, related_module_id, progress_at_event,
                   created_at
            FROM learning_path_events
            WHERE progress_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, progress_id, limit)
                return [self._map_learning_path_event(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get learning path events: {e}") from e

    # ========================================================================
    # ALERT THRESHOLD OPERATIONS
    # ========================================================================

    async def create_alert_threshold(
        self,
        threshold: AnalyticsAlertThreshold
    ) -> AnalyticsAlertThreshold:
        """
        What: Create alert threshold.
        Where: Alert configuration.
        Why: Define monitoring rules.

        Args:
            threshold: AnalyticsAlertThreshold to create

        Returns:
            Created AnalyticsAlertThreshold
        """
        query = """
            INSERT INTO analytics_alert_thresholds (
                id, user_id, organization_id, name, description,
                metric_type, threshold_operator, threshold_value,
                threshold_value_upper, scope, scope_entity_id,
                severity, notification_channels, notification_config,
                cooldown_minutes, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $17)
            RETURNING id, created_at, updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    threshold.id,
                    threshold.user_id,
                    threshold.organization_id,
                    threshold.name,
                    threshold.description,
                    threshold.metric_type.value,
                    threshold.threshold_operator.value,
                    threshold.threshold_value,
                    threshold.threshold_value_upper,
                    threshold.scope.value,
                    threshold.scope_entity_id,
                    threshold.severity.value,
                    threshold.notification_channels,
                    threshold.notification_config.to_dict() if threshold.notification_config else {},
                    threshold.cooldown_minutes,
                    threshold.is_active,
                    datetime.utcnow()
                )
                threshold.created_at = row["created_at"]
                threshold.updated_at = row["updated_at"]
                return threshold
        except Exception as e:
            raise DashboardDAOError(f"Failed to create alert threshold: {e}") from e

    async def get_alert_threshold(self, threshold_id: UUID) -> Optional[AnalyticsAlertThreshold]:
        """
        What: Get alert threshold by ID.
        Where: Alert configuration view.
        Why: Retrieve threshold settings.

        Args:
            threshold_id: Threshold UUID

        Returns:
            AnalyticsAlertThreshold if found
        """
        query = """
            SELECT id, user_id, organization_id, name, description,
                   metric_type, threshold_operator, threshold_value,
                   threshold_value_upper, scope, scope_entity_id,
                   severity, notification_channels, notification_config,
                   cooldown_minutes, last_triggered_at, is_active,
                   created_at, updated_at
            FROM analytics_alert_thresholds
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(query, threshold_id)
                if not row:
                    return None
                return self._map_alert_threshold(row)
        except Exception as e:
            raise DashboardDAOError(f"Failed to get alert threshold: {e}") from e

    async def get_active_thresholds(
        self,
        organization_id: Optional[UUID] = None,
        metric_type: Optional[MetricType] = None
    ) -> list[AnalyticsAlertThreshold]:
        """
        What: Get active alert thresholds.
        Where: Alert evaluation job.
        Why: Find thresholds to check.

        Args:
            organization_id: Optional org filter
            metric_type: Optional metric filter

        Returns:
            List of active thresholds
        """
        query = """
            SELECT id, user_id, organization_id, name, description,
                   metric_type, threshold_operator, threshold_value,
                   threshold_value_upper, scope, scope_entity_id,
                   severity, notification_channels, notification_config,
                   cooldown_minutes, last_triggered_at, is_active,
                   created_at, updated_at
            FROM analytics_alert_thresholds
            WHERE is_active = true
              AND ($1::uuid IS NULL OR organization_id = $1)
              AND ($2::text IS NULL OR metric_type = $2)
            ORDER BY severity DESC, name ASC
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    query,
                    organization_id,
                    metric_type.value if metric_type else None
                )
                return [self._map_alert_threshold(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get active thresholds: {e}") from e

    async def update_alert_threshold(
        self,
        threshold: AnalyticsAlertThreshold
    ) -> AnalyticsAlertThreshold:
        """
        What: Update alert threshold.
        Where: Alert configuration.
        Why: Modify threshold settings.

        Args:
            threshold: AnalyticsAlertThreshold with updates

        Returns:
            Updated AnalyticsAlertThreshold
        """
        query = """
            UPDATE analytics_alert_thresholds
            SET name = $2, description = $3, threshold_value = $4,
                threshold_value_upper = $5, severity = $6,
                notification_channels = $7, notification_config = $8,
                cooldown_minutes = $9, is_active = $10, updated_at = $11
            WHERE id = $1
            RETURNING updated_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    threshold.id,
                    threshold.name,
                    threshold.description,
                    threshold.threshold_value,
                    threshold.threshold_value_upper,
                    threshold.severity.value,
                    threshold.notification_channels,
                    threshold.notification_config.to_dict() if threshold.notification_config else {},
                    threshold.cooldown_minutes,
                    threshold.is_active,
                    datetime.utcnow()
                )
                if not row:
                    raise AlertThresholdNotFoundError(f"Threshold {threshold.id} not found")
                threshold.updated_at = row["updated_at"]
                return threshold
        except AlertThresholdNotFoundError:
            raise
        except Exception as e:
            raise DashboardDAOError(f"Failed to update alert threshold: {e}") from e

    async def update_threshold_triggered(self, threshold_id: UUID) -> None:
        """
        What: Update last triggered timestamp.
        Where: After alert fires.
        Why: Track for cooldown.

        Args:
            threshold_id: Threshold UUID
        """
        query = """
            UPDATE analytics_alert_thresholds
            SET last_triggered_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(query, threshold_id)
        except Exception as e:
            raise DashboardDAOError(f"Failed to update threshold triggered: {e}") from e

    async def create_alert_history(self, alert: AlertHistory) -> AlertHistory:
        """
        What: Record triggered alert.
        Where: Alert fires.
        Why: Maintain alert history.

        Args:
            alert: AlertHistory to create

        Returns:
            Created AlertHistory
        """
        query = """
            INSERT INTO analytics_alert_history (
                id, threshold_id, triggered_value, triggered_at,
                affected_entities, affected_count, status,
                notifications_sent, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, created_at
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    alert.id,
                    alert.threshold_id,
                    alert.triggered_value,
                    alert.triggered_at or datetime.utcnow(),
                    alert.affected_entities,
                    alert.affected_count,
                    alert.status.value,
                    alert.notifications_sent,
                    datetime.utcnow()
                )
                alert.created_at = row["created_at"]
                return alert
        except Exception as e:
            raise DashboardDAOError(f"Failed to create alert history: {e}") from e

    async def update_alert_history(self, alert: AlertHistory) -> AlertHistory:
        """
        What: Update alert status.
        Where: Alert acknowledgment/resolution.
        Why: Track alert response.

        Args:
            alert: AlertHistory with updates

        Returns:
            Updated AlertHistory
        """
        query = """
            UPDATE analytics_alert_history
            SET status = $2, acknowledged_by = $3, acknowledged_at = $4,
                resolved_at = $5, resolution_notes = $6
            WHERE id = $1
            RETURNING id
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    alert.id,
                    alert.status.value,
                    alert.acknowledged_by,
                    alert.acknowledged_at,
                    alert.resolved_at,
                    alert.resolution_notes
                )
                if not row:
                    raise DashboardDAOError(f"Alert {alert.id} not found")
                return alert
        except Exception as e:
            raise DashboardDAOError(f"Failed to update alert history: {e}") from e

    async def get_active_alerts(
        self,
        organization_id: Optional[UUID] = None,
        limit: int = 100
    ) -> list[AlertHistory]:
        """
        What: Get active (unresolved) alerts.
        Where: Alert dashboard.
        Why: Show alerts needing attention.

        Args:
            organization_id: Optional org filter
            limit: Maximum results

        Returns:
            List of active alerts
        """
        query = """
            SELECT ah.id, ah.threshold_id, ah.triggered_value, ah.triggered_at,
                   ah.affected_entities, ah.affected_count, ah.status,
                   ah.acknowledged_by, ah.acknowledged_at, ah.resolved_at,
                   ah.resolution_notes, ah.notifications_sent, ah.created_at
            FROM analytics_alert_history ah
            JOIN analytics_alert_thresholds at ON ah.threshold_id = at.id
            WHERE ah.status IN ('active', 'acknowledged')
              AND ($1::uuid IS NULL OR at.organization_id = $1)
            ORDER BY ah.triggered_at DESC
            LIMIT $2
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, organization_id, limit)
                return [self._map_alert_history(row) for row in rows]
        except Exception as e:
            raise DashboardDAOError(f"Failed to get active alerts: {e}") from e

    # ========================================================================
    # ENTITY MAPPING METHODS
    # ========================================================================

    def _map_dashboard_template(self, row: dict) -> DashboardTemplate:
        """Map database row to DashboardTemplate entity."""
        return DashboardTemplate(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            target_role=UserRole(row["target_role"]),
            layout_config=LayoutConfig.from_dict(row["layout_config"]),
            is_default=row["is_default"],
            scope=DashboardScope(row["scope"]),
            organization_id=row["organization_id"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_user_dashboard(self, row: dict) -> UserDashboard:
        """Map database row to UserDashboard entity."""
        return UserDashboard(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            template_id=row["template_id"],
            layout_config=LayoutConfig.from_dict(row["layout_config"]),
            preferences=DashboardPreferences.from_dict(row["preferences"]) if row["preferences"] else None,
            is_active=row["is_active"],
            last_accessed_at=row["last_accessed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_dashboard_widget(self, row: dict) -> DashboardWidget:
        """Map database row to DashboardWidget entity."""
        return DashboardWidget(
            id=row["id"],
            widget_type=WidgetType(row["widget_type"]),
            name=row["name"],
            description=row["description"],
            default_width=row["default_width"],
            default_height=row["default_height"],
            min_width=row["min_width"],
            min_height=row["min_height"],
            data_source=DataSource.from_dict(row["data_source"]),
            config_schema=row["config_schema"],
            default_config=row["default_config"],
            allowed_roles=[UserRole(r) for r in row["allowed_roles"]],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_widget_instance(self, row: dict) -> WidgetInstance:
        """Map database row to WidgetInstance entity."""
        return WidgetInstance(
            id=row["id"],
            dashboard_id=row["dashboard_id"],
            widget_id=row["widget_id"],
            grid_x=row["grid_x"],
            grid_y=row["grid_y"],
            grid_width=row["grid_width"],
            grid_height=row["grid_height"],
            config=row["config"],
            title_override=row["title_override"],
            is_visible=row["is_visible"],
            display_order=row["display_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_report_template(self, row: dict) -> ReportTemplate:
        """Map database row to ReportTemplate entity."""
        return ReportTemplate(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            report_type=ReportType(row["report_type"]),
            config=ReportConfig.from_dict(row["config"]),
            output_formats=[OutputFormat(f) for f in row["output_formats"]],
            scope=DashboardScope(row["scope"]),
            organization_id=row["organization_id"],
            created_by=row["created_by"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_scheduled_report(self, row: dict) -> ScheduledReport:
        """Map database row to ScheduledReport entity."""
        return ScheduledReport(
            id=row["id"],
            user_id=row["user_id"],
            template_id=row["template_id"],
            name=row["name"],
            schedule_type=ScheduleType(row["schedule_type"]),
            schedule_cron=row["schedule_cron"],
            schedule_day=row["schedule_day"],
            schedule_time=row["schedule_time"],
            schedule_timezone=row["schedule_timezone"],
            config_overrides=row["config_overrides"],
            output_format=OutputFormat(row["output_format"]),
            delivery_method=DeliveryMethod(row["delivery_method"]),
            delivery_config=DeliveryConfig.from_dict(row["delivery_config"]) if row["delivery_config"] else None,
            recipients=row["recipients"],
            is_active=row["is_active"],
            next_run_at=row["next_run_at"],
            last_run_at=row["last_run_at"],
            last_run_status=row["last_run_status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_report_execution(self, row: dict) -> ReportExecution:
        """Map database row to ReportExecution entity."""
        return ReportExecution(
            id=row["id"],
            scheduled_report_id=row["scheduled_report_id"],
            template_id=row["template_id"],
            user_id=row["user_id"],
            status=ReportExecutionStatus(row["status"]),
            parameters=row["parameters"],
            date_range_start=row["date_range_start"],
            date_range_end=row["date_range_end"],
            output_format=OutputFormat(row["output_format"]) if row["output_format"] else None,
            file_path=row["file_path"],
            file_size_bytes=row["file_size_bytes"],
            file_checksum=row["file_checksum"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            generation_time_ms=row["generation_time_ms"],
            error_message=row["error_message"],
            error_details=row["error_details"],
            expires_at=row["expires_at"],
            created_at=row["created_at"]
        )

    def _map_cohort(self, row: dict) -> AnalyticsCohort:
        """Map database row to AnalyticsCohort entity."""
        return AnalyticsCohort(
            id=row["id"],
            organization_id=row["organization_id"],
            name=row["name"],
            description=row["description"],
            cohort_type=CohortType(row["cohort_type"]),
            membership_rules=MembershipRules.from_dict(row["membership_rules"]) if row["membership_rules"] else None,
            linked_course_id=row["linked_course_id"],
            linked_track_id=row["linked_track_id"],
            tags=row["tags"],
            created_by=row["created_by"],
            is_active=row["is_active"],
            member_count=row["member_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_cohort_member(self, row: dict) -> CohortMember:
        """Map database row to CohortMember entity."""
        return CohortMember(
            id=row["id"],
            cohort_id=row["cohort_id"],
            user_id=row["user_id"],
            joined_at=row["joined_at"],
            is_active=row["is_active"],
            left_at=row["left_at"]
        )

    def _map_cohort_snapshot(self, row: dict) -> CohortSnapshot:
        """Map database row to CohortSnapshot entity."""
        return CohortSnapshot(
            id=row["id"],
            cohort_id=row["cohort_id"],
            snapshot_date=row["snapshot_date"],
            member_count=row["member_count"],
            avg_completion_rate=row["avg_completion_rate"],
            avg_quiz_score=row["avg_quiz_score"],
            avg_engagement_score=row["avg_engagement_score"],
            avg_time_spent_minutes=row["avg_time_spent_minutes"],
            completion_distribution=None,  # Parse from JSON if needed
            score_distribution=None,  # Parse from JSON if needed
            active_member_count=row["active_member_count"],
            at_risk_count=row["at_risk_count"],
            completed_count=row["completed_count"],
            metrics=row["metrics"],
            created_at=row["created_at"]
        )

    def _map_learning_path_progress(self, row: dict) -> LearningPathProgress:
        """Map database row to LearningPathProgress entity."""
        return LearningPathProgress(
            id=row["id"],
            user_id=row["user_id"],
            track_id=row["track_id"],
            overall_progress=row["overall_progress"],
            current_course_id=row["current_course_id"],
            current_module_order=row["current_module_order"],
            milestones_completed=row["milestones_completed"],
            started_at=row["started_at"],
            estimated_completion_at=row["estimated_completion_at"],
            actual_completion_at=row["actual_completion_at"],
            total_time_spent_minutes=row["total_time_spent_minutes"],
            avg_quiz_score=row["avg_quiz_score"],
            avg_assignment_score=row["avg_assignment_score"],
            status=LearningPathStatus(row["status"]),
            last_activity_at=row["last_activity_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_learning_path_event(self, row: dict) -> LearningPathEvent:
        """Map database row to LearningPathEvent entity."""
        return LearningPathEvent(
            id=row["id"],
            progress_id=row["progress_id"],
            event_type=LearningPathEventType(row["event_type"]),
            event_data=row["event_data"],
            related_course_id=row["related_course_id"],
            related_module_id=row["related_module_id"],
            progress_at_event=row["progress_at_event"],
            created_at=row["created_at"]
        )

    def _map_alert_threshold(self, row: dict) -> AnalyticsAlertThreshold:
        """Map database row to AnalyticsAlertThreshold entity."""
        return AnalyticsAlertThreshold(
            id=row["id"],
            user_id=row["user_id"],
            organization_id=row["organization_id"],
            name=row["name"],
            description=row["description"],
            metric_type=MetricType(row["metric_type"]),
            threshold_operator=ThresholdOperator(row["threshold_operator"]),
            threshold_value=row["threshold_value"],
            threshold_value_upper=row["threshold_value_upper"],
            scope=AlertScope(row["scope"]),
            scope_entity_id=row["scope_entity_id"],
            severity=AlertSeverity(row["severity"]),
            notification_channels=row["notification_channels"],
            notification_config=NotificationConfig.from_dict(row["notification_config"]) if row["notification_config"] else None,
            cooldown_minutes=row["cooldown_minutes"],
            last_triggered_at=row["last_triggered_at"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _map_alert_history(self, row: dict) -> AlertHistory:
        """Map database row to AlertHistory entity."""
        return AlertHistory(
            id=row["id"],
            threshold_id=row["threshold_id"],
            triggered_value=row["triggered_value"],
            triggered_at=row["triggered_at"],
            affected_entities=row["affected_entities"],
            affected_count=row["affected_count"],
            status=AlertStatus(row["status"]),
            acknowledged_by=row["acknowledged_by"],
            acknowledged_at=row["acknowledged_at"],
            resolved_at=row["resolved_at"],
            resolution_notes=row["resolution_notes"],
            notifications_sent=row["notifications_sent"],
            created_at=row["created_at"]
        )
