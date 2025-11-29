"""
Learning Analytics Dashboard Domain Entities

What: Domain entities for customizable analytics dashboards, widgets,
      scheduled reports, cohort analytics, and learning path tracking.

Where: Part of the Analytics service domain layer, extending existing
       student analytics with dashboard-specific presentation features.

Why: The existing analytics service provides raw data calculations.
     These entities enable:
     1. User-customizable dashboard layouts with draggable widgets
     2. Scheduled report generation with email/export delivery
     3. Cohort-based analytics for comparing student groups
     4. Learning path progress visualization
     5. Configurable alert thresholds for at-risk detection
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """
    What: User role types for dashboard access control.
    Where: Used in template targeting and widget permissions.
    Why: Different roles need different analytics views.
    """
    SITE_ADMIN = "site_admin"
    ORG_ADMIN = "org_admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class DashboardScope(str, Enum):
    """
    What: Visibility scope for dashboard templates.
    Where: Controls template availability.
    Why: Allows platform-wide, org-specific, or personal templates.
    """
    PLATFORM = "platform"
    ORGANIZATION = "organization"
    PERSONAL = "personal"


class WidgetType(str, Enum):
    """
    What: Available widget visualization types.
    Where: Maps to frontend components.
    Why: Determines rendering logic and data requirements.
    """
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    HEATMAP = "heatmap"
    TABLE = "table"
    PROGRESS_RING = "progress_ring"
    LEADERBOARD = "leaderboard"
    ACTIVITY_FEED = "activity_feed"
    RISK_INDICATOR = "risk_indicator"
    COHORT_COMPARISON = "cohort_comparison"
    LEARNING_PATH = "learning_path"
    COMPLETION_FUNNEL = "completion_funnel"
    ENGAGEMENT_SCORE = "engagement_score"
    CUSTOM = "custom"


class ReportType(str, Enum):
    """
    What: Classification of report types.
    Where: Determines report generation logic.
    Why: Different reports need different data aggregation.
    """
    STUDENT_PROGRESS = "student_progress"
    COURSE_ANALYTICS = "course_analytics"
    COHORT_COMPARISON = "cohort_comparison"
    ENGAGEMENT_SUMMARY = "engagement_summary"
    COMPLETION_REPORT = "completion_report"
    ASSESSMENT_ANALYSIS = "assessment_analysis"
    INSTRUCTOR_SUMMARY = "instructor_summary"
    ORGANIZATION_OVERVIEW = "organization_overview"
    CUSTOM = "custom"


class ScheduleType(str, Enum):
    """
    What: Report scheduling frequency options.
    Where: Determines when reports run.
    Why: Enables automated periodic report generation.
    """
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class OutputFormat(str, Enum):
    """
    What: Report output file formats.
    Where: Determines file generation type.
    Why: Users may need PDF, Excel, or CSV formats.
    """
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class DeliveryMethod(str, Enum):
    """
    What: Report delivery mechanisms.
    Where: How/where to send generated reports.
    Why: Different delivery preferences per user.
    """
    EMAIL = "email"
    DOWNLOAD = "download"
    WEBHOOK = "webhook"
    STORAGE = "storage"


class ReportExecutionStatus(str, Enum):
    """
    What: Status of report generation process.
    Where: Tracks async report generation.
    Why: Enables progress tracking for long-running reports.
    """
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CohortType(str, Enum):
    """
    What: Classification of cohort membership rules.
    Where: Determines how cohort membership is calculated.
    Why: Different cohort types serve different analysis needs.
    """
    ENROLLMENT_DATE = "enrollment_date"
    COURSE = "course"
    TRACK = "track"
    MANUAL = "manual"
    PERFORMANCE = "performance"
    DYNAMIC = "dynamic"


class LearningPathStatus(str, Enum):
    """
    What: Status of student's learning path progress.
    Where: Quick status identification.
    Why: Enables filtering and alerts based on progress status.
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    BEHIND = "behind"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class LearningPathEventType(str, Enum):
    """
    What: Types of events in learning path progress.
    Where: Classification of progress events.
    Why: Different events need different handling and display.
    """
    PATH_STARTED = "path_started"
    COURSE_STARTED = "course_started"
    COURSE_COMPLETED = "course_completed"
    MODULE_COMPLETED = "module_completed"
    QUIZ_COMPLETED = "quiz_completed"
    MILESTONE_REACHED = "milestone_reached"
    CERTIFICATE_EARNED = "certificate_earned"
    STATUS_CHANGED = "status_changed"
    PACE_ADJUSTED = "pace_adjusted"


class MetricType(str, Enum):
    """
    What: Types of metrics for alert thresholds.
    Where: Defines what metric triggers an alert.
    Why: Different metrics have different threshold semantics.
    """
    ENGAGEMENT_SCORE = "engagement_score"
    COMPLETION_RATE = "completion_rate"
    QUIZ_SCORE = "quiz_score"
    DAYS_INACTIVE = "days_inactive"
    AT_RISK_COUNT = "at_risk_count"
    DROP_RATE = "drop_rate"
    TIME_SPENT = "time_spent"
    PROGRESS_RATE = "progress_rate"


class ThresholdOperator(str, Enum):
    """
    What: Comparison operators for threshold evaluation.
    Where: Used in alert threshold configuration.
    Why: Flexible threshold definition (>, <, =, between).
    """
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    EQ = "eq"
    BETWEEN = "between"


class AlertScope(str, Enum):
    """
    What: Scope of alert monitoring.
    Where: Determines what entities are monitored.
    Why: Course-specific vs org-wide vs platform alerts.
    """
    COURSE = "course"
    TRACK = "track"
    ORGANIZATION = "organization"
    PLATFORM = "platform"


class AlertSeverity(str, Enum):
    """
    What: Alert priority levels.
    Where: Determines notification urgency.
    Why: Different alerts need different response urgency.
    """
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """
    What: Status of triggered alerts.
    Where: Tracks alert lifecycle.
    Why: Enables workflow for responding to alerts.
    """
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ============================================================================
# DASHBOARD ENTITIES
# ============================================================================

@dataclass
class LayoutConfig:
    """
    What: Configuration for dashboard grid layout.
    Where: Stored in templates and user dashboards.
    Why: Defines the grid system for widget positioning.
    """
    columns: int = 12
    rows: list[dict[str, Any]] = field(default_factory=list)
    widgets: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "widgets": self.widgets
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LayoutConfig":
        """Create from dictionary."""
        return cls(
            columns=data.get("columns", 12),
            rows=data.get("rows", []),
            widgets=data.get("widgets", [])
        )


@dataclass
class DashboardPreferences:
    """
    What: User preferences for dashboard behavior.
    Where: Stored per user dashboard.
    Why: Personalizes dashboard experience.
    """
    refresh_interval: int = 300  # seconds
    date_range: str = "30d"
    theme: str = "auto"
    compact_mode: bool = False
    show_tooltips: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "refreshInterval": self.refresh_interval,
            "dateRange": self.date_range,
            "theme": self.theme,
            "compactMode": self.compact_mode,
            "showTooltips": self.show_tooltips
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DashboardPreferences":
        """Create from dictionary."""
        return cls(
            refresh_interval=data.get("refreshInterval", 300),
            date_range=data.get("dateRange", "30d"),
            theme=data.get("theme", "auto"),
            compact_mode=data.get("compactMode", False),
            show_tooltips=data.get("showTooltips", True)
        )


@dataclass
class DashboardTemplate:
    """
    What: Pre-defined dashboard layout template.
    Where: System-provided or organization-created templates.
    Why: Provides role-appropriate default dashboards.
    """
    id: UUID
    name: str
    target_role: UserRole
    layout_config: LayoutConfig
    description: Optional[str] = None
    is_default: bool = False
    scope: DashboardScope = DashboardScope.PLATFORM
    organization_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate template configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Template name cannot exceed 100 characters")
        if self.scope == DashboardScope.ORGANIZATION and not self.organization_id:
            raise ValueError("Organization ID required for organization-scoped templates")


@dataclass
class UserDashboard:
    """
    What: Individual user's customized dashboard.
    Where: Stores user-specific layout and preferences.
    Why: Enables personalized analytics views.
    """
    id: UUID
    user_id: UUID
    name: str
    layout_config: LayoutConfig
    template_id: Optional[UUID] = None
    preferences: Optional[DashboardPreferences] = None
    is_active: bool = True
    last_accessed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate dashboard configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Dashboard name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Dashboard name cannot exceed 100 characters")
        if self.preferences is None:
            self.preferences = DashboardPreferences()


@dataclass
class DataSource:
    """
    What: Configuration for widget data fetching.
    Where: Specifies API endpoint and parameters.
    Why: Widgets need to know where to fetch data.
    """
    endpoint: str
    refresh_interval: int = 300
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "endpoint": self.endpoint,
            "refreshInterval": self.refresh_interval,
            "parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataSource":
        """Create from dictionary."""
        return cls(
            endpoint=data.get("endpoint", ""),
            refresh_interval=data.get("refreshInterval", 300),
            parameters=data.get("parameters", {})
        )


@dataclass
class DashboardWidget:
    """
    What: Available widget type definition.
    Where: System-defined widget types.
    Why: Reusable visualization components.
    """
    id: UUID
    widget_type: WidgetType
    name: str
    data_source: DataSource
    description: Optional[str] = None
    default_width: int = 4
    default_height: int = 2
    min_width: int = 2
    min_height: int = 1
    config_schema: dict[str, Any] = field(default_factory=dict)
    default_config: dict[str, Any] = field(default_factory=dict)
    allowed_roles: list[UserRole] = field(default_factory=lambda: list(UserRole))
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate widget configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Widget name cannot be empty")
        if self.default_width < 1 or self.default_width > 12:
            raise ValueError("Widget width must be between 1 and 12")
        if self.default_height < 1 or self.default_height > 8:
            raise ValueError("Widget height must be between 1 and 8")
        if self.min_width > self.default_width:
            raise ValueError("Minimum width cannot exceed default width")
        if self.min_height > self.default_height:
            raise ValueError("Minimum height cannot exceed default height")

    def is_allowed_for_role(self, role: UserRole) -> bool:
        """Check if widget is available for a specific role."""
        return role in self.allowed_roles


@dataclass
class WidgetInstance:
    """
    What: Specific widget configuration on a dashboard.
    Where: Links widget to dashboard with position/config.
    Why: Same widget type can appear multiple times with different settings.
    """
    id: UUID
    dashboard_id: UUID
    widget_id: UUID
    grid_x: int = 0
    grid_y: int = 0
    grid_width: int = 4
    grid_height: int = 2
    config: dict[str, Any] = field(default_factory=dict)
    title_override: Optional[str] = None
    is_visible: bool = True
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate instance configuration."""
        if self.grid_x < 0:
            raise ValueError("Grid X position cannot be negative")
        if self.grid_y < 0:
            raise ValueError("Grid Y position cannot be negative")
        if self.grid_width < 1:
            raise ValueError("Grid width must be at least 1")
        if self.grid_height < 1:
            raise ValueError("Grid height must be at least 1")


# ============================================================================
# REPORT ENTITIES
# ============================================================================

@dataclass
class ReportConfig:
    """
    What: Configuration for report content.
    Where: Specifies metrics, filters, groupings.
    Why: Defines what data appears in report.
    """
    metrics: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    group_by: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "metrics": self.metrics,
            "filters": self.filters,
            "groupBy": self.group_by,
            "includeCharts": self.include_charts,
            "includeRecommendations": self.include_recommendations
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportConfig":
        """Create from dictionary."""
        return cls(
            metrics=data.get("metrics", []),
            filters=data.get("filters", {}),
            group_by=data.get("groupBy"),
            include_charts=data.get("includeCharts", True),
            include_recommendations=data.get("includeRecommendations", False)
        )


@dataclass
class ReportTemplate:
    """
    What: Reusable report configuration template.
    Where: System or user-defined templates.
    Why: Enables consistent report generation.
    """
    id: UUID
    name: str
    report_type: ReportType
    config: ReportConfig
    description: Optional[str] = None
    output_formats: list[OutputFormat] = field(default_factory=lambda: [OutputFormat.PDF, OutputFormat.CSV])
    scope: DashboardScope = DashboardScope.PLATFORM
    organization_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate template configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Report template name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Report template name cannot exceed 100 characters")
        if not self.output_formats:
            raise ValueError("At least one output format is required")


@dataclass
class DeliveryConfig:
    """
    What: Configuration for report delivery.
    Where: How/where to send generated reports.
    Why: Flexible delivery options per schedule.
    """
    email_addresses: list[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    storage_path: Optional[str] = None
    include_summary: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "emailAddresses": self.email_addresses,
            "webhookUrl": self.webhook_url,
            "storagePath": self.storage_path,
            "includeSummary": self.include_summary
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeliveryConfig":
        """Create from dictionary."""
        return cls(
            email_addresses=data.get("emailAddresses", []),
            webhook_url=data.get("webhookUrl"),
            storage_path=data.get("storagePath"),
            include_summary=data.get("includeSummary", True)
        )


@dataclass
class ScheduledReport:
    """
    What: User-configured report schedule.
    Where: Defines automated report generation.
    Why: Enables periodic report delivery.
    """
    id: UUID
    user_id: UUID
    template_id: UUID
    name: str
    schedule_type: ScheduleType
    output_format: OutputFormat = OutputFormat.PDF
    delivery_method: DeliveryMethod = DeliveryMethod.EMAIL
    delivery_config: Optional[DeliveryConfig] = None
    schedule_cron: Optional[str] = None
    schedule_day: Optional[int] = None
    schedule_time: time = field(default_factory=lambda: time(9, 0))
    schedule_timezone: str = "UTC"
    config_overrides: dict[str, Any] = field(default_factory=dict)
    recipients: list[dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate schedule configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Scheduled report name cannot be empty")
        if self.schedule_day is not None and (self.schedule_day < 0 or self.schedule_day > 31):
            raise ValueError("Schedule day must be between 0 and 31")
        if self.delivery_config is None:
            self.delivery_config = DeliveryConfig()


@dataclass
class ReportExecution:
    """
    What: Record of report generation execution.
    Where: History of generated reports.
    Why: Enables async generation with status tracking.
    """
    id: UUID
    user_id: UUID
    status: ReportExecutionStatus = ReportExecutionStatus.PENDING
    scheduled_report_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    output_format: Optional[OutputFormat] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_checksum: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    generation_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def is_downloadable(self) -> bool:
        """Check if report file can be downloaded."""
        if self.status != ReportExecutionStatus.COMPLETED:
            return False
        if not self.file_path:
            return False
        if self.expires_at and self.expires_at < datetime.now(self.expires_at.tzinfo):
            return False
        return True


# ============================================================================
# COHORT ENTITIES
# ============================================================================

@dataclass
class MembershipRules:
    """
    What: Rules for automatic cohort membership.
    Where: Dynamic cohorts use these rules.
    Why: Automatic membership updates based on criteria.
    """
    enrollment_date_start: Optional[date] = None
    enrollment_date_end: Optional[date] = None
    course_ids: list[UUID] = field(default_factory=list)
    track_ids: list[UUID] = field(default_factory=list)
    min_score: Optional[Decimal] = None
    max_score: Optional[Decimal] = None
    min_engagement: Optional[Decimal] = None
    custom_filters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "enrollmentDateStart": self.enrollment_date_start.isoformat() if self.enrollment_date_start else None,
            "enrollmentDateEnd": self.enrollment_date_end.isoformat() if self.enrollment_date_end else None,
            "courseIds": [str(cid) for cid in self.course_ids],
            "trackIds": [str(tid) for tid in self.track_ids],
            "minScore": float(self.min_score) if self.min_score else None,
            "maxScore": float(self.max_score) if self.max_score else None,
            "minEngagement": float(self.min_engagement) if self.min_engagement else None,
            "customFilters": self.custom_filters
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MembershipRules":
        """Create from dictionary."""
        return cls(
            enrollment_date_start=date.fromisoformat(data["enrollmentDateStart"]) if data.get("enrollmentDateStart") else None,
            enrollment_date_end=date.fromisoformat(data["enrollmentDateEnd"]) if data.get("enrollmentDateEnd") else None,
            course_ids=[UUID(cid) for cid in data.get("courseIds", [])],
            track_ids=[UUID(tid) for tid in data.get("trackIds", [])],
            min_score=Decimal(str(data["minScore"])) if data.get("minScore") is not None else None,
            max_score=Decimal(str(data["maxScore"])) if data.get("maxScore") is not None else None,
            min_engagement=Decimal(str(data["minEngagement"])) if data.get("minEngagement") is not None else None,
            custom_filters=data.get("customFilters", {})
        )


@dataclass
class AnalyticsCohort:
    """
    What: Group of students for comparison analytics.
    Where: Organization-level cohort definitions.
    Why: Enables cohort-based performance comparison.
    """
    id: UUID
    name: str
    cohort_type: CohortType
    organization_id: Optional[UUID] = None
    description: Optional[str] = None
    membership_rules: Optional[MembershipRules] = None
    linked_course_id: Optional[UUID] = None
    linked_track_id: Optional[UUID] = None
    tags: list[str] = field(default_factory=list)
    created_by: Optional[UUID] = None
    is_active: bool = True
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate cohort configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Cohort name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Cohort name cannot exceed 100 characters")
        if self.cohort_type == CohortType.DYNAMIC and not self.membership_rules:
            raise ValueError("Dynamic cohorts require membership rules")
        if self.membership_rules is None:
            self.membership_rules = MembershipRules()


@dataclass
class CohortMember:
    """
    What: Student membership in a cohort.
    Where: Links students to cohorts.
    Why: Track membership over time.
    """
    id: UUID
    cohort_id: UUID
    user_id: UUID
    joined_at: Optional[datetime] = None
    is_active: bool = True
    left_at: Optional[datetime] = None


@dataclass
class DistributionMetrics:
    """
    What: Distribution of values within a cohort.
    Where: Score/completion distribution.
    Why: Shows spread, not just averages.
    """
    buckets: list[dict[str, Any]] = field(default_factory=list)
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    median: Optional[Decimal] = None
    std_dev: Optional[Decimal] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "buckets": self.buckets,
            "minValue": float(self.min_value) if self.min_value else None,
            "maxValue": float(self.max_value) if self.max_value else None,
            "median": float(self.median) if self.median else None,
            "stdDev": float(self.std_dev) if self.std_dev else None
        }


@dataclass
class CohortSnapshot:
    """
    What: Point-in-time cohort metrics snapshot.
    Where: Historical cohort analytics.
    Why: Enables trend analysis over time.
    """
    id: UUID
    cohort_id: UUID
    snapshot_date: date
    member_count: int = 0
    avg_completion_rate: Optional[Decimal] = None
    avg_quiz_score: Optional[Decimal] = None
    avg_engagement_score: Optional[Decimal] = None
    avg_time_spent_minutes: Optional[int] = None
    completion_distribution: Optional[DistributionMetrics] = None
    score_distribution: Optional[DistributionMetrics] = None
    active_member_count: int = 0
    at_risk_count: int = 0
    completed_count: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


# ============================================================================
# LEARNING PATH ENTITIES
# ============================================================================

@dataclass
class LearningPathProgress:
    """
    What: Student's progress through a learning track.
    Where: Per-user, per-track progress tracking.
    Why: Visualize and monitor path completion.
    """
    id: UUID
    user_id: UUID
    track_id: UUID
    overall_progress: Decimal = Decimal("0.00")
    current_course_id: Optional[UUID] = None
    current_module_order: Optional[int] = None
    milestones_completed: list[dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    estimated_completion_at: Optional[datetime] = None
    actual_completion_at: Optional[datetime] = None
    total_time_spent_minutes: int = 0
    avg_quiz_score: Optional[Decimal] = None
    avg_assignment_score: Optional[Decimal] = None
    status: LearningPathStatus = LearningPathStatus.NOT_STARTED
    last_activity_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate progress values."""
        if self.overall_progress < Decimal("0") or self.overall_progress > Decimal("100"):
            raise ValueError("Overall progress must be between 0 and 100")

    def is_completed(self) -> bool:
        """Check if learning path is completed."""
        return self.status == LearningPathStatus.COMPLETED

    def is_at_risk(self) -> bool:
        """Check if student is at risk of not completing."""
        return self.status in [LearningPathStatus.BEHIND, LearningPathStatus.AT_RISK]


@dataclass
class LearningPathEvent:
    """
    What: Event in learning path progress.
    Where: Detailed progress history.
    Why: Full audit trail of progress changes.
    """
    id: UUID
    progress_id: UUID
    event_type: LearningPathEventType
    event_data: dict[str, Any] = field(default_factory=dict)
    related_course_id: Optional[UUID] = None
    related_module_id: Optional[UUID] = None
    progress_at_event: Optional[Decimal] = None
    created_at: Optional[datetime] = None


# ============================================================================
# ALERT ENTITIES
# ============================================================================

@dataclass
class NotificationConfig:
    """
    What: Configuration for alert notifications.
    Where: Determines how alerts are delivered.
    Why: Flexible notification channels.
    """
    channels: list[str] = field(default_factory=lambda: ["in_app"])
    email_addresses: list[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    include_details: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "channels": self.channels,
            "emailAddresses": self.email_addresses,
            "webhookUrl": self.webhook_url,
            "includeDetails": self.include_details
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationConfig":
        """Create from dictionary."""
        return cls(
            channels=data.get("channels", ["in_app"]),
            email_addresses=data.get("emailAddresses", []),
            webhook_url=data.get("webhookUrl"),
            include_details=data.get("includeDetails", True)
        )


@dataclass
class AnalyticsAlertThreshold:
    """
    What: Configurable alert rule for analytics.
    Where: User or org-level alert definitions.
    Why: Proactive notification of concerning metrics.
    """
    id: UUID
    name: str
    metric_type: MetricType
    threshold_operator: ThresholdOperator
    threshold_value: Decimal
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    description: Optional[str] = None
    threshold_value_upper: Optional[Decimal] = None
    scope: AlertScope = AlertScope.ORGANIZATION
    scope_entity_id: Optional[UUID] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    notification_channels: list[str] = field(default_factory=lambda: ["in_app"])
    notification_config: Optional[NotificationConfig] = None
    cooldown_minutes: int = 60
    last_triggered_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate threshold configuration."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Alert threshold name cannot be empty")
        if self.threshold_operator == ThresholdOperator.BETWEEN and not self.threshold_value_upper:
            raise ValueError("Upper threshold required for BETWEEN operator")
        if self.user_id is None and self.organization_id is None:
            raise ValueError("Either user_id or organization_id must be set")
        if self.user_id is not None and self.organization_id is not None:
            raise ValueError("Cannot set both user_id and organization_id")
        if self.cooldown_minutes < 0:
            raise ValueError("Cooldown minutes cannot be negative")
        if self.notification_config is None:
            self.notification_config = NotificationConfig()

    def evaluate(self, value: Decimal) -> bool:
        """
        Evaluate if the given value triggers this threshold.

        Args:
            value: The metric value to evaluate

        Returns:
            True if threshold is triggered, False otherwise
        """
        if self.threshold_operator == ThresholdOperator.LT:
            return value < self.threshold_value
        elif self.threshold_operator == ThresholdOperator.LTE:
            return value <= self.threshold_value
        elif self.threshold_operator == ThresholdOperator.GT:
            return value > self.threshold_value
        elif self.threshold_operator == ThresholdOperator.GTE:
            return value >= self.threshold_value
        elif self.threshold_operator == ThresholdOperator.EQ:
            return value == self.threshold_value
        elif self.threshold_operator == ThresholdOperator.BETWEEN:
            return self.threshold_value <= value <= self.threshold_value_upper
        return False


@dataclass
class AlertHistory:
    """
    What: Record of triggered alert.
    Where: Historical alert log.
    Why: Track alerts and responses.
    """
    id: UUID
    threshold_id: UUID
    triggered_value: Decimal
    triggered_at: Optional[datetime] = None
    affected_entities: list[dict[str, Any]] = field(default_factory=list)
    affected_count: int = 0
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    notifications_sent: list[dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None

    def acknowledge(self, user_id: UUID) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now()

    def resolve(self, notes: Optional[str] = None) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolution_notes = notes

    def dismiss(self) -> None:
        """Dismiss the alert without resolution."""
        self.status = AlertStatus.DISMISSED
