"""
Unit Tests for Learning Analytics Dashboard Domain Entities

What: Comprehensive unit tests for all dashboard domain entities including
      enums, data classes, validation, and serialization.

Where: Tests the analytics/domain/entities/dashboard.py module.

Why: Ensures entity correctness, validation rules, serialization/deserialization,
     and business logic methods work as expected.
"""

import pytest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from uuid import uuid4

from analytics.domain.entities.dashboard import (
    # Enums
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
    # Data classes
    LayoutConfig,
    DashboardPreferences,
    DashboardTemplate,
    UserDashboard,
    DataSource,
    DashboardWidget,
    WidgetInstance,
    ReportConfig,
    ReportTemplate,
    DeliveryConfig,
    ScheduledReport,
    ReportExecution,
    MembershipRules,
    AnalyticsCohort,
    CohortMember,
    DistributionMetrics,
    CohortSnapshot,
    LearningPathProgress,
    LearningPathEvent,
    NotificationConfig,
    AnalyticsAlertThreshold,
    AlertHistory,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestUserRole:
    """Tests for UserRole enum."""

    def test_all_roles_exist(self):
        """Test all user roles are defined."""
        assert UserRole.SITE_ADMIN.value == "site_admin"
        assert UserRole.ORG_ADMIN.value == "org_admin"
        assert UserRole.INSTRUCTOR.value == "instructor"
        assert UserRole.STUDENT.value == "student"

    def test_role_count(self):
        """Test correct number of roles."""
        assert len(UserRole) == 4


class TestDashboardScope:
    """Tests for DashboardScope enum."""

    def test_all_scopes_exist(self):
        """Test all scopes are defined."""
        assert DashboardScope.PLATFORM.value == "platform"
        assert DashboardScope.ORGANIZATION.value == "organization"
        assert DashboardScope.PERSONAL.value == "personal"


class TestWidgetType:
    """Tests for WidgetType enum."""

    def test_all_widget_types_exist(self):
        """Test all widget types are defined."""
        expected_types = [
            "kpi_card", "line_chart", "bar_chart", "pie_chart", "heatmap",
            "table", "progress_ring", "leaderboard", "activity_feed",
            "risk_indicator", "cohort_comparison", "learning_path",
            "completion_funnel", "engagement_score", "custom"
        ]
        for widget_type in expected_types:
            assert WidgetType(widget_type) is not None

    def test_widget_type_count(self):
        """Test correct number of widget types."""
        assert len(WidgetType) == 15


class TestReportType:
    """Tests for ReportType enum."""

    def test_all_report_types_exist(self):
        """Test all report types are defined."""
        expected_types = [
            "student_progress", "course_analytics", "cohort_comparison",
            "engagement_summary", "completion_report", "assessment_analysis",
            "instructor_summary", "organization_overview", "custom"
        ]
        for report_type in expected_types:
            assert ReportType(report_type) is not None


class TestScheduleType:
    """Tests for ScheduleType enum."""

    def test_all_schedule_types_exist(self):
        """Test all schedule types are defined."""
        assert ScheduleType.ONCE.value == "once"
        assert ScheduleType.DAILY.value == "daily"
        assert ScheduleType.WEEKLY.value == "weekly"
        assert ScheduleType.BIWEEKLY.value == "biweekly"
        assert ScheduleType.MONTHLY.value == "monthly"
        assert ScheduleType.QUARTERLY.value == "quarterly"


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_all_output_formats_exist(self):
        """Test all output formats are defined."""
        assert OutputFormat.PDF.value == "pdf"
        assert OutputFormat.CSV.value == "csv"
        assert OutputFormat.XLSX.value == "xlsx"
        assert OutputFormat.JSON.value == "json"


class TestDeliveryMethod:
    """Tests for DeliveryMethod enum."""

    def test_all_delivery_methods_exist(self):
        """Test all delivery methods are defined."""
        assert DeliveryMethod.EMAIL.value == "email"
        assert DeliveryMethod.DOWNLOAD.value == "download"
        assert DeliveryMethod.WEBHOOK.value == "webhook"
        assert DeliveryMethod.STORAGE.value == "storage"


class TestReportExecutionStatus:
    """Tests for ReportExecutionStatus enum."""

    def test_all_statuses_exist(self):
        """Test all execution statuses are defined."""
        assert ReportExecutionStatus.PENDING.value == "pending"
        assert ReportExecutionStatus.GENERATING.value == "generating"
        assert ReportExecutionStatus.COMPLETED.value == "completed"
        assert ReportExecutionStatus.FAILED.value == "failed"
        assert ReportExecutionStatus.EXPIRED.value == "expired"


class TestCohortType:
    """Tests for CohortType enum."""

    def test_all_cohort_types_exist(self):
        """Test all cohort types are defined."""
        expected_types = [
            "enrollment_date", "course", "track", "manual", "performance", "dynamic"
        ]
        for cohort_type in expected_types:
            assert CohortType(cohort_type) is not None


class TestLearningPathStatus:
    """Tests for LearningPathStatus enum."""

    def test_all_statuses_exist(self):
        """Test all learning path statuses are defined."""
        expected_statuses = [
            "not_started", "in_progress", "on_track", "behind",
            "at_risk", "completed", "abandoned"
        ]
        for status in expected_statuses:
            assert LearningPathStatus(status) is not None


class TestLearningPathEventType:
    """Tests for LearningPathEventType enum."""

    def test_all_event_types_exist(self):
        """Test all event types are defined."""
        expected_types = [
            "path_started", "course_started", "course_completed",
            "module_completed", "quiz_completed", "milestone_reached",
            "certificate_earned", "status_changed", "pace_adjusted"
        ]
        for event_type in expected_types:
            assert LearningPathEventType(event_type) is not None


class TestMetricType:
    """Tests for MetricType enum."""

    def test_all_metric_types_exist(self):
        """Test all metric types are defined."""
        expected_types = [
            "engagement_score", "completion_rate", "quiz_score",
            "days_inactive", "at_risk_count", "drop_rate",
            "time_spent", "progress_rate"
        ]
        for metric_type in expected_types:
            assert MetricType(metric_type) is not None


class TestThresholdOperator:
    """Tests for ThresholdOperator enum."""

    def test_all_operators_exist(self):
        """Test all threshold operators are defined."""
        assert ThresholdOperator.LT.value == "lt"
        assert ThresholdOperator.LTE.value == "lte"
        assert ThresholdOperator.GT.value == "gt"
        assert ThresholdOperator.GTE.value == "gte"
        assert ThresholdOperator.EQ.value == "eq"
        assert ThresholdOperator.BETWEEN.value == "between"


class TestAlertScope:
    """Tests for AlertScope enum."""

    def test_all_scopes_exist(self):
        """Test all alert scopes are defined."""
        assert AlertScope.COURSE.value == "course"
        assert AlertScope.TRACK.value == "track"
        assert AlertScope.ORGANIZATION.value == "organization"
        assert AlertScope.PLATFORM.value == "platform"


class TestAlertSeverity:
    """Tests for AlertSeverity enum."""

    def test_all_severities_exist(self):
        """Test all alert severities are defined."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestAlertStatus:
    """Tests for AlertStatus enum."""

    def test_all_statuses_exist(self):
        """Test all alert statuses are defined."""
        assert AlertStatus.ACTIVE.value == "active"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.DISMISSED.value == "dismissed"


# ============================================================================
# DATA CLASS TESTS
# ============================================================================

class TestLayoutConfig:
    """Tests for LayoutConfig data class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LayoutConfig()
        assert config.columns == 12
        assert config.rows == []
        assert config.widgets == []

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LayoutConfig(
            columns=6,
            rows=[{"height": 100}],
            widgets=[{"id": "test"}]
        )
        assert config.columns == 6
        assert len(config.rows) == 1
        assert len(config.widgets) == 1

    def test_to_dict(self):
        """Test dictionary serialization."""
        config = LayoutConfig(columns=8, rows=[{"h": 50}], widgets=[])
        result = config.to_dict()
        assert result["columns"] == 8
        assert result["rows"] == [{"h": 50}]
        assert result["widgets"] == []

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"columns": 10, "rows": [], "widgets": [{"type": "kpi"}]}
        config = LayoutConfig.from_dict(data)
        assert config.columns == 10
        assert len(config.widgets) == 1

    def test_from_dict_with_missing_keys(self):
        """Test deserialization with missing keys uses defaults."""
        config = LayoutConfig.from_dict({})
        assert config.columns == 12


class TestDashboardPreferences:
    """Tests for DashboardPreferences data class."""

    def test_default_values(self):
        """Test default preference values."""
        prefs = DashboardPreferences()
        assert prefs.refresh_interval == 300
        assert prefs.date_range == "30d"
        assert prefs.theme == "auto"
        assert prefs.compact_mode is False
        assert prefs.show_tooltips is True

    def test_to_dict(self):
        """Test dictionary serialization."""
        prefs = DashboardPreferences(refresh_interval=60, theme="dark")
        result = prefs.to_dict()
        assert result["refreshInterval"] == 60
        assert result["theme"] == "dark"

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"refreshInterval": 120, "dateRange": "7d", "compactMode": True}
        prefs = DashboardPreferences.from_dict(data)
        assert prefs.refresh_interval == 120
        assert prefs.date_range == "7d"
        assert prefs.compact_mode is True


class TestDashboardTemplate:
    """Tests for DashboardTemplate entity."""

    def test_valid_template_creation(self):
        """Test creating a valid template."""
        template = DashboardTemplate(
            id=uuid4(),
            name="Test Template",
            target_role=UserRole.INSTRUCTOR,
            layout_config=LayoutConfig()
        )
        assert template.name == "Test Template"
        assert template.target_role == UserRole.INSTRUCTOR
        assert template.is_default is False

    def test_template_with_all_fields(self):
        """Test template with all optional fields."""
        org_id = uuid4()
        user_id = uuid4()
        template = DashboardTemplate(
            id=uuid4(),
            name="Full Template",
            description="A complete template",
            target_role=UserRole.STUDENT,
            layout_config=LayoutConfig(columns=6),
            is_default=True,
            scope=DashboardScope.ORGANIZATION,
            organization_id=org_id,
            created_by=user_id
        )
        assert template.description == "A complete template"
        assert template.is_default is True
        assert template.organization_id == org_id

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Template name cannot be empty"):
            DashboardTemplate(
                id=uuid4(),
                name="",
                target_role=UserRole.STUDENT,
                layout_config=LayoutConfig()
            )

    def test_whitespace_name_raises_error(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Template name cannot be empty"):
            DashboardTemplate(
                id=uuid4(),
                name="   ",
                target_role=UserRole.STUDENT,
                layout_config=LayoutConfig()
            )

    def test_long_name_raises_error(self):
        """Test that name over 100 chars raises ValueError."""
        with pytest.raises(ValueError, match="Template name cannot exceed 100 characters"):
            DashboardTemplate(
                id=uuid4(),
                name="x" * 101,
                target_role=UserRole.STUDENT,
                layout_config=LayoutConfig()
            )

    def test_org_scope_requires_org_id(self):
        """Test that organization scope requires organization_id."""
        with pytest.raises(ValueError, match="Organization ID required"):
            DashboardTemplate(
                id=uuid4(),
                name="Org Template",
                target_role=UserRole.STUDENT,
                layout_config=LayoutConfig(),
                scope=DashboardScope.ORGANIZATION
            )


class TestUserDashboard:
    """Tests for UserDashboard entity."""

    def test_valid_dashboard_creation(self):
        """Test creating a valid user dashboard."""
        dashboard = UserDashboard(
            id=uuid4(),
            user_id=uuid4(),
            name="My Dashboard",
            layout_config=LayoutConfig()
        )
        assert dashboard.name == "My Dashboard"
        assert dashboard.is_active is True
        assert dashboard.preferences is not None

    def test_default_preferences_created(self):
        """Test that default preferences are created if None."""
        dashboard = UserDashboard(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            layout_config=LayoutConfig(),
            preferences=None
        )
        assert dashboard.preferences is not None
        assert isinstance(dashboard.preferences, DashboardPreferences)

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Dashboard name cannot be empty"):
            UserDashboard(
                id=uuid4(),
                user_id=uuid4(),
                name="",
                layout_config=LayoutConfig()
            )


class TestDataSource:
    """Tests for DataSource data class."""

    def test_default_values(self):
        """Test default data source values."""
        source = DataSource(endpoint="/api/test")
        assert source.endpoint == "/api/test"
        assert source.refresh_interval == 300
        assert source.parameters == {}

    def test_to_dict(self):
        """Test dictionary serialization."""
        source = DataSource(
            endpoint="/api/data",
            refresh_interval=60,
            parameters={"filter": "active"}
        )
        result = source.to_dict()
        assert result["endpoint"] == "/api/data"
        assert result["refreshInterval"] == 60
        assert result["parameters"]["filter"] == "active"

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"endpoint": "/api/test", "refreshInterval": 120}
        source = DataSource.from_dict(data)
        assert source.endpoint == "/api/test"
        assert source.refresh_interval == 120


class TestDashboardWidget:
    """Tests for DashboardWidget entity."""

    def test_valid_widget_creation(self):
        """Test creating a valid widget."""
        widget = DashboardWidget(
            id=uuid4(),
            widget_type=WidgetType.KPI_CARD,
            name="Active Students",
            data_source=DataSource(endpoint="/api/kpi/students")
        )
        assert widget.name == "Active Students"
        assert widget.widget_type == WidgetType.KPI_CARD

    def test_default_dimensions(self):
        """Test default widget dimensions."""
        widget = DashboardWidget(
            id=uuid4(),
            widget_type=WidgetType.LINE_CHART,
            name="Trend",
            data_source=DataSource(endpoint="/api/trend")
        )
        assert widget.default_width == 4
        assert widget.default_height == 2
        assert widget.min_width == 2
        assert widget.min_height == 1

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Widget name cannot be empty"):
            DashboardWidget(
                id=uuid4(),
                widget_type=WidgetType.TABLE,
                name="",
                data_source=DataSource(endpoint="/api/data")
            )

    def test_invalid_width_raises_error(self):
        """Test that invalid width raises ValueError."""
        with pytest.raises(ValueError, match="Widget width must be between 1 and 12"):
            DashboardWidget(
                id=uuid4(),
                widget_type=WidgetType.TABLE,
                name="Test",
                data_source=DataSource(endpoint="/api/data"),
                default_width=15
            )

    def test_invalid_height_raises_error(self):
        """Test that invalid height raises ValueError."""
        with pytest.raises(ValueError, match="Widget height must be between 1 and 8"):
            DashboardWidget(
                id=uuid4(),
                widget_type=WidgetType.TABLE,
                name="Test",
                data_source=DataSource(endpoint="/api/data"),
                default_height=10
            )

    def test_min_width_exceeds_default(self):
        """Test min_width cannot exceed default_width."""
        with pytest.raises(ValueError, match="Minimum width cannot exceed default width"):
            DashboardWidget(
                id=uuid4(),
                widget_type=WidgetType.TABLE,
                name="Test",
                data_source=DataSource(endpoint="/api/data"),
                default_width=4,
                min_width=6
            )

    def test_is_allowed_for_role(self):
        """Test role permission check."""
        widget = DashboardWidget(
            id=uuid4(),
            widget_type=WidgetType.RISK_INDICATOR,
            name="At-Risk",
            data_source=DataSource(endpoint="/api/risk"),
            allowed_roles=[UserRole.INSTRUCTOR, UserRole.ORG_ADMIN]
        )
        assert widget.is_allowed_for_role(UserRole.INSTRUCTOR) is True
        assert widget.is_allowed_for_role(UserRole.STUDENT) is False


class TestWidgetInstance:
    """Tests for WidgetInstance entity."""

    def test_valid_instance_creation(self):
        """Test creating a valid widget instance."""
        instance = WidgetInstance(
            id=uuid4(),
            dashboard_id=uuid4(),
            widget_id=uuid4(),
            grid_x=0,
            grid_y=0,
            grid_width=4,
            grid_height=2
        )
        assert instance.is_visible is True
        assert instance.display_order == 0

    def test_negative_grid_x_raises_error(self):
        """Test that negative grid_x raises ValueError."""
        with pytest.raises(ValueError, match="Grid X position cannot be negative"):
            WidgetInstance(
                id=uuid4(),
                dashboard_id=uuid4(),
                widget_id=uuid4(),
                grid_x=-1,
                grid_y=0,
                grid_width=4,
                grid_height=2
            )

    def test_invalid_grid_width_raises_error(self):
        """Test that width < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Grid width must be at least 1"):
            WidgetInstance(
                id=uuid4(),
                dashboard_id=uuid4(),
                widget_id=uuid4(),
                grid_x=0,
                grid_y=0,
                grid_width=0,
                grid_height=2
            )


class TestReportConfig:
    """Tests for ReportConfig data class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ReportConfig()
        assert config.metrics == []
        assert config.filters == {}
        assert config.include_charts is True

    def test_to_dict(self):
        """Test dictionary serialization."""
        config = ReportConfig(
            metrics=["completion_rate", "avg_score"],
            group_by="course",
            include_recommendations=True
        )
        result = config.to_dict()
        assert len(result["metrics"]) == 2
        assert result["groupBy"] == "course"
        assert result["includeRecommendations"] is True

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"metrics": ["score"], "includeCharts": False}
        config = ReportConfig.from_dict(data)
        assert config.metrics == ["score"]
        assert config.include_charts is False


class TestReportTemplate:
    """Tests for ReportTemplate entity."""

    def test_valid_template_creation(self):
        """Test creating a valid report template."""
        template = ReportTemplate(
            id=uuid4(),
            name="Weekly Progress",
            report_type=ReportType.STUDENT_PROGRESS,
            config=ReportConfig(metrics=["completion"])
        )
        assert template.name == "Weekly Progress"
        assert template.is_active is True

    def test_default_output_formats(self):
        """Test default output formats."""
        template = ReportTemplate(
            id=uuid4(),
            name="Report",
            report_type=ReportType.COURSE_ANALYTICS,
            config=ReportConfig()
        )
        assert OutputFormat.PDF in template.output_formats
        assert OutputFormat.CSV in template.output_formats

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Report template name cannot be empty"):
            ReportTemplate(
                id=uuid4(),
                name="",
                report_type=ReportType.CUSTOM,
                config=ReportConfig()
            )

    def test_empty_output_formats_raises_error(self):
        """Test that empty output formats raises ValueError."""
        with pytest.raises(ValueError, match="At least one output format is required"):
            ReportTemplate(
                id=uuid4(),
                name="Test",
                report_type=ReportType.CUSTOM,
                config=ReportConfig(),
                output_formats=[]
            )


class TestDeliveryConfig:
    """Tests for DeliveryConfig data class."""

    def test_default_values(self):
        """Test default delivery values."""
        config = DeliveryConfig()
        assert config.email_addresses == []
        assert config.webhook_url is None
        assert config.include_summary is True

    def test_to_dict(self):
        """Test dictionary serialization."""
        config = DeliveryConfig(
            email_addresses=["test@example.com"],
            webhook_url="https://webhook.example.com"
        )
        result = config.to_dict()
        assert result["emailAddresses"] == ["test@example.com"]
        assert result["webhookUrl"] == "https://webhook.example.com"

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"emailAddresses": ["a@b.com"], "includeSummary": False}
        config = DeliveryConfig.from_dict(data)
        assert config.email_addresses == ["a@b.com"]
        assert config.include_summary is False


class TestScheduledReport:
    """Tests for ScheduledReport entity."""

    def test_valid_scheduled_report(self):
        """Test creating a valid scheduled report."""
        report = ScheduledReport(
            id=uuid4(),
            user_id=uuid4(),
            template_id=uuid4(),
            name="Daily Report",
            schedule_type=ScheduleType.DAILY
        )
        assert report.name == "Daily Report"
        assert report.is_active is True
        assert report.output_format == OutputFormat.PDF

    def test_default_delivery_config_created(self):
        """Test that default delivery config is created."""
        report = ScheduledReport(
            id=uuid4(),
            user_id=uuid4(),
            template_id=uuid4(),
            name="Report",
            schedule_type=ScheduleType.WEEKLY,
            delivery_config=None
        )
        assert report.delivery_config is not None

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Scheduled report name cannot be empty"):
            ScheduledReport(
                id=uuid4(),
                user_id=uuid4(),
                template_id=uuid4(),
                name="",
                schedule_type=ScheduleType.MONTHLY
            )

    def test_invalid_schedule_day_raises_error(self):
        """Test that invalid schedule_day raises ValueError."""
        with pytest.raises(ValueError, match="Schedule day must be between 0 and 31"):
            ScheduledReport(
                id=uuid4(),
                user_id=uuid4(),
                template_id=uuid4(),
                name="Report",
                schedule_type=ScheduleType.MONTHLY,
                schedule_day=35
            )


class TestReportExecution:
    """Tests for ReportExecution entity."""

    def test_valid_execution(self):
        """Test creating a valid report execution."""
        execution = ReportExecution(
            id=uuid4(),
            user_id=uuid4(),
            status=ReportExecutionStatus.PENDING
        )
        assert execution.status == ReportExecutionStatus.PENDING

    def test_is_downloadable_completed(self):
        """Test downloadable check for completed report."""
        execution = ReportExecution(
            id=uuid4(),
            user_id=uuid4(),
            status=ReportExecutionStatus.COMPLETED,
            file_path="/reports/test.pdf",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        assert execution.is_downloadable() is True

    def test_is_downloadable_pending(self):
        """Test downloadable check for pending report."""
        execution = ReportExecution(
            id=uuid4(),
            user_id=uuid4(),
            status=ReportExecutionStatus.PENDING
        )
        assert execution.is_downloadable() is False

    def test_is_downloadable_no_file(self):
        """Test downloadable check without file path."""
        execution = ReportExecution(
            id=uuid4(),
            user_id=uuid4(),
            status=ReportExecutionStatus.COMPLETED,
            file_path=None
        )
        assert execution.is_downloadable() is False


class TestMembershipRules:
    """Tests for MembershipRules data class."""

    def test_default_values(self):
        """Test default membership rules."""
        rules = MembershipRules()
        assert rules.enrollment_date_start is None
        assert rules.course_ids == []
        assert rules.custom_filters == {}

    def test_to_dict(self):
        """Test dictionary serialization."""
        course_id = uuid4()
        rules = MembershipRules(
            enrollment_date_start=date(2024, 1, 1),
            course_ids=[course_id],
            min_score=Decimal("70.0")
        )
        result = rules.to_dict()
        assert result["enrollmentDateStart"] == "2024-01-01"
        assert len(result["courseIds"]) == 1
        assert result["minScore"] == 70.0

    def test_from_dict(self):
        """Test dictionary deserialization."""
        course_id = str(uuid4())
        data = {
            "enrollmentDateStart": "2024-06-15",
            "courseIds": [course_id],
            "minScore": 80.0
        }
        rules = MembershipRules.from_dict(data)
        assert rules.enrollment_date_start == date(2024, 6, 15)
        assert len(rules.course_ids) == 1
        assert rules.min_score == Decimal("80.0")


class TestAnalyticsCohort:
    """Tests for AnalyticsCohort entity."""

    def test_valid_cohort_creation(self):
        """Test creating a valid cohort."""
        cohort = AnalyticsCohort(
            id=uuid4(),
            name="Q1 2024 Cohort",
            cohort_type=CohortType.ENROLLMENT_DATE
        )
        assert cohort.name == "Q1 2024 Cohort"
        assert cohort.is_active is True
        assert cohort.member_count == 0

    def test_default_membership_rules_created(self):
        """Test that default membership rules are created."""
        cohort = AnalyticsCohort(
            id=uuid4(),
            name="Test",
            cohort_type=CohortType.MANUAL,
            membership_rules=None
        )
        assert cohort.membership_rules is not None

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Cohort name cannot be empty"):
            AnalyticsCohort(
                id=uuid4(),
                name="",
                cohort_type=CohortType.COURSE
            )

    def test_dynamic_cohort_requires_rules(self):
        """Test that dynamic cohort requires membership rules."""
        with pytest.raises(ValueError, match="Dynamic cohorts require membership rules"):
            AnalyticsCohort(
                id=uuid4(),
                name="Dynamic",
                cohort_type=CohortType.DYNAMIC,
                membership_rules=None
            )


class TestCohortMember:
    """Tests for CohortMember entity."""

    def test_valid_member(self):
        """Test creating a valid cohort member."""
        member = CohortMember(
            id=uuid4(),
            cohort_id=uuid4(),
            user_id=uuid4()
        )
        assert member.is_active is True
        assert member.left_at is None


class TestCohortSnapshot:
    """Tests for CohortSnapshot entity."""

    def test_valid_snapshot(self):
        """Test creating a valid snapshot."""
        snapshot = CohortSnapshot(
            id=uuid4(),
            cohort_id=uuid4(),
            snapshot_date=date.today(),
            member_count=50,
            avg_completion_rate=Decimal("75.5"),
            avg_quiz_score=Decimal("82.3")
        )
        assert snapshot.member_count == 50
        assert snapshot.avg_completion_rate == Decimal("75.5")


class TestLearningPathProgress:
    """Tests for LearningPathProgress entity."""

    def test_valid_progress(self):
        """Test creating valid progress record."""
        progress = LearningPathProgress(
            id=uuid4(),
            user_id=uuid4(),
            track_id=uuid4(),
            overall_progress=Decimal("50.00"),
            status=LearningPathStatus.IN_PROGRESS
        )
        assert progress.overall_progress == Decimal("50.00")
        assert progress.total_time_spent_minutes == 0

    def test_invalid_progress_raises_error(self):
        """Test that progress > 100 raises ValueError."""
        with pytest.raises(ValueError, match="Overall progress must be between 0 and 100"):
            LearningPathProgress(
                id=uuid4(),
                user_id=uuid4(),
                track_id=uuid4(),
                overall_progress=Decimal("150.00")
            )

    def test_negative_progress_raises_error(self):
        """Test that negative progress raises ValueError."""
        with pytest.raises(ValueError, match="Overall progress must be between 0 and 100"):
            LearningPathProgress(
                id=uuid4(),
                user_id=uuid4(),
                track_id=uuid4(),
                overall_progress=Decimal("-10.00")
            )

    def test_is_completed(self):
        """Test completed check."""
        progress = LearningPathProgress(
            id=uuid4(),
            user_id=uuid4(),
            track_id=uuid4(),
            status=LearningPathStatus.COMPLETED
        )
        assert progress.is_completed() is True

    def test_is_at_risk(self):
        """Test at-risk check."""
        progress = LearningPathProgress(
            id=uuid4(),
            user_id=uuid4(),
            track_id=uuid4(),
            status=LearningPathStatus.AT_RISK
        )
        assert progress.is_at_risk() is True

        progress.status = LearningPathStatus.BEHIND
        assert progress.is_at_risk() is True

        progress.status = LearningPathStatus.ON_TRACK
        assert progress.is_at_risk() is False


class TestLearningPathEvent:
    """Tests for LearningPathEvent entity."""

    def test_valid_event(self):
        """Test creating valid event."""
        event = LearningPathEvent(
            id=uuid4(),
            progress_id=uuid4(),
            event_type=LearningPathEventType.COURSE_COMPLETED,
            event_data={"course_name": "Python Basics"},
            progress_at_event=Decimal("25.00")
        )
        assert event.event_type == LearningPathEventType.COURSE_COMPLETED


class TestNotificationConfig:
    """Tests for NotificationConfig data class."""

    def test_default_values(self):
        """Test default notification config."""
        config = NotificationConfig()
        assert config.channels == ["in_app"]
        assert config.email_addresses == []
        assert config.include_details is True

    def test_to_dict(self):
        """Test dictionary serialization."""
        config = NotificationConfig(
            channels=["in_app", "email"],
            email_addresses=["admin@example.com"]
        )
        result = config.to_dict()
        assert len(result["channels"]) == 2
        assert result["emailAddresses"] == ["admin@example.com"]

    def test_from_dict(self):
        """Test dictionary deserialization."""
        data = {"channels": ["email"], "includeDetails": False}
        config = NotificationConfig.from_dict(data)
        assert config.channels == ["email"]
        assert config.include_details is False


class TestAnalyticsAlertThreshold:
    """Tests for AnalyticsAlertThreshold entity."""

    def test_valid_threshold_user_level(self):
        """Test creating valid user-level threshold."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Low Engagement Alert",
            metric_type=MetricType.ENGAGEMENT_SCORE,
            threshold_operator=ThresholdOperator.LT,
            threshold_value=Decimal("50.0"),
            user_id=uuid4()
        )
        assert threshold.name == "Low Engagement Alert"
        assert threshold.is_active is True
        assert threshold.cooldown_minutes == 60

    def test_valid_threshold_org_level(self):
        """Test creating valid org-level threshold."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="High Drop Rate",
            metric_type=MetricType.DROP_RATE,
            threshold_operator=ThresholdOperator.GT,
            threshold_value=Decimal("20.0"),
            organization_id=uuid4()
        )
        assert threshold.organization_id is not None

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Alert threshold name cannot be empty"):
            AnalyticsAlertThreshold(
                id=uuid4(),
                name="",
                metric_type=MetricType.QUIZ_SCORE,
                threshold_operator=ThresholdOperator.LT,
                threshold_value=Decimal("60.0"),
                user_id=uuid4()
            )

    def test_between_requires_upper_value(self):
        """Test that BETWEEN operator requires upper value."""
        with pytest.raises(ValueError, match="Upper threshold required for BETWEEN operator"):
            AnalyticsAlertThreshold(
                id=uuid4(),
                name="Score Range",
                metric_type=MetricType.QUIZ_SCORE,
                threshold_operator=ThresholdOperator.BETWEEN,
                threshold_value=Decimal("60.0"),
                user_id=uuid4()
            )

    def test_requires_user_or_org_id(self):
        """Test that either user_id or organization_id is required."""
        with pytest.raises(ValueError, match="Either user_id or organization_id must be set"):
            AnalyticsAlertThreshold(
                id=uuid4(),
                name="Test",
                metric_type=MetricType.COMPLETION_RATE,
                threshold_operator=ThresholdOperator.LT,
                threshold_value=Decimal("50.0")
            )

    def test_cannot_set_both_user_and_org(self):
        """Test that both user_id and organization_id cannot be set."""
        with pytest.raises(ValueError, match="Cannot set both user_id and organization_id"):
            AnalyticsAlertThreshold(
                id=uuid4(),
                name="Test",
                metric_type=MetricType.COMPLETION_RATE,
                threshold_operator=ThresholdOperator.LT,
                threshold_value=Decimal("50.0"),
                user_id=uuid4(),
                organization_id=uuid4()
            )

    def test_negative_cooldown_raises_error(self):
        """Test that negative cooldown raises ValueError."""
        with pytest.raises(ValueError, match="Cooldown minutes cannot be negative"):
            AnalyticsAlertThreshold(
                id=uuid4(),
                name="Test",
                metric_type=MetricType.COMPLETION_RATE,
                threshold_operator=ThresholdOperator.LT,
                threshold_value=Decimal("50.0"),
                user_id=uuid4(),
                cooldown_minutes=-10
            )

    def test_evaluate_lt(self):
        """Test threshold evaluation with LT operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.ENGAGEMENT_SCORE,
            threshold_operator=ThresholdOperator.LT,
            threshold_value=Decimal("50.0"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("40.0")) is True
        assert threshold.evaluate(Decimal("50.0")) is False
        assert threshold.evaluate(Decimal("60.0")) is False

    def test_evaluate_lte(self):
        """Test threshold evaluation with LTE operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.ENGAGEMENT_SCORE,
            threshold_operator=ThresholdOperator.LTE,
            threshold_value=Decimal("50.0"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("40.0")) is True
        assert threshold.evaluate(Decimal("50.0")) is True
        assert threshold.evaluate(Decimal("60.0")) is False

    def test_evaluate_gt(self):
        """Test threshold evaluation with GT operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.DROP_RATE,
            threshold_operator=ThresholdOperator.GT,
            threshold_value=Decimal("20.0"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("10.0")) is False
        assert threshold.evaluate(Decimal("20.0")) is False
        assert threshold.evaluate(Decimal("30.0")) is True

    def test_evaluate_gte(self):
        """Test threshold evaluation with GTE operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.DROP_RATE,
            threshold_operator=ThresholdOperator.GTE,
            threshold_value=Decimal("20.0"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("10.0")) is False
        assert threshold.evaluate(Decimal("20.0")) is True
        assert threshold.evaluate(Decimal("30.0")) is True

    def test_evaluate_eq(self):
        """Test threshold evaluation with EQ operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.AT_RISK_COUNT,
            threshold_operator=ThresholdOperator.EQ,
            threshold_value=Decimal("10"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("9")) is False
        assert threshold.evaluate(Decimal("10")) is True
        assert threshold.evaluate(Decimal("11")) is False

    def test_evaluate_between(self):
        """Test threshold evaluation with BETWEEN operator."""
        threshold = AnalyticsAlertThreshold(
            id=uuid4(),
            name="Test",
            metric_type=MetricType.QUIZ_SCORE,
            threshold_operator=ThresholdOperator.BETWEEN,
            threshold_value=Decimal("60.0"),
            threshold_value_upper=Decimal("80.0"),
            user_id=uuid4()
        )
        assert threshold.evaluate(Decimal("50.0")) is False
        assert threshold.evaluate(Decimal("60.0")) is True
        assert threshold.evaluate(Decimal("70.0")) is True
        assert threshold.evaluate(Decimal("80.0")) is True
        assert threshold.evaluate(Decimal("90.0")) is False


class TestAlertHistory:
    """Tests for AlertHistory entity."""

    def test_valid_alert_history(self):
        """Test creating valid alert history."""
        alert = AlertHistory(
            id=uuid4(),
            threshold_id=uuid4(),
            triggered_value=Decimal("45.0"),
            affected_count=5
        )
        assert alert.status == AlertStatus.ACTIVE
        assert alert.affected_count == 5

    def test_acknowledge(self):
        """Test acknowledging an alert."""
        alert = AlertHistory(
            id=uuid4(),
            threshold_id=uuid4(),
            triggered_value=Decimal("45.0")
        )
        user_id = uuid4()
        alert.acknowledge(user_id)

        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == user_id
        assert alert.acknowledged_at is not None

    def test_resolve(self):
        """Test resolving an alert."""
        alert = AlertHistory(
            id=uuid4(),
            threshold_id=uuid4(),
            triggered_value=Decimal("45.0")
        )
        alert.resolve("Issue fixed by increasing resources")

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert alert.resolution_notes == "Issue fixed by increasing resources"

    def test_dismiss(self):
        """Test dismissing an alert."""
        alert = AlertHistory(
            id=uuid4(),
            threshold_id=uuid4(),
            triggered_value=Decimal("45.0")
        )
        alert.dismiss()

        assert alert.status == AlertStatus.DISMISSED


# ============================================================================
# DISTRIBUTION METRICS TESTS
# ============================================================================

class TestDistributionMetrics:
    """Tests for DistributionMetrics data class."""

    def test_default_values(self):
        """Test default distribution metrics."""
        metrics = DistributionMetrics()
        assert metrics.buckets == []
        assert metrics.min_value is None
        assert metrics.median is None

    def test_to_dict(self):
        """Test dictionary serialization."""
        metrics = DistributionMetrics(
            buckets=[{"range": "0-50", "count": 10}],
            min_value=Decimal("25.5"),
            max_value=Decimal("98.0"),
            median=Decimal("72.0"),
            std_dev=Decimal("15.5")
        )
        result = metrics.to_dict()
        assert len(result["buckets"]) == 1
        assert result["minValue"] == 25.5
        assert result["median"] == 72.0
