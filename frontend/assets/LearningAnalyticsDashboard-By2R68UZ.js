import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, i as useParams } from "./react-vendor-cEae-lCc.js";
import { c as apiClient } from "./index-C0G9mbri.js";
import { L as Line, C as Chart, a as CategoryScale, b as LinearScale, P as PointElement, c as LineElement, p as plugin_title, d as plugin_tooltip, e as plugin_legend, i as index, R as Radar, g as RadialLinearScale, B as Bar, h as Pie, f as BarElement, A as ArcElement } from "./index-BM3tqO1q.js";
import "./state-vendor-B_izx0oA.js";
class LearningAnalyticsService {
  baseUrl = "/analytics/learning";
  /**
   * Get student's learning analytics summary
   *
   * WHAT: Retrieves comprehensive learning analytics overview
   * WHERE: Student dashboard main analytics widget
   * WHY: Provides quick snapshot of overall learning performance
   */
  async getStudentLearningAnalytics(studentId) {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/summary`
    );
  }
  /**
   * Get current user's learning analytics
   *
   * WHAT: Retrieves learning analytics for logged-in user
   * WHERE: Student dashboard (no ID required)
   * WHY: Convenience method for current user analytics
   */
  async getMyLearningAnalytics() {
    return await apiClient.get(`${this.baseUrl}/student/me/summary`);
  }
  /**
   * Get learning path progress for student
   *
   * WHAT: Retrieves detailed learning path progress data
   * WHERE: Learning path progress visualization components
   * WHY: Tracks student advancement through structured curriculum
   */
  async getLearningPathProgress(studentId, trackId) {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/path/${trackId}`
    );
  }
  /**
   * Get all learning paths for student
   *
   * WHAT: Retrieves all active and completed learning paths
   * WHERE: Learning paths overview page
   * WHY: Shows complete learning journey across multiple tracks
   */
  async getStudentLearningPaths(studentId) {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/paths`
    );
  }
  /**
   * Get skill mastery data for student
   *
   * WHAT: Retrieves mastery levels for all tracked skills
   * WHERE: Skill mastery dashboard widget
   * WHY: Identifies strengths, weaknesses, and review needs
   */
  async getSkillMastery(studentId, courseId) {
    const params = courseId ? { course_id: courseId } : {};
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/skills`,
      { params }
    );
  }
  /**
   * Get specific skill mastery data
   *
   * WHAT: Retrieves detailed mastery data for a single skill
   * WHERE: Skill detail page, spaced repetition scheduler
   * WHY: Supports targeted practice and review scheduling
   */
  async getSkillMasteryDetail(studentId, skillTopic) {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/skill/${encodeURIComponent(skillTopic)}`
    );
  }
  /**
   * Get skills needing review (spaced repetition)
   *
   * WHAT: Retrieves skills due for review based on SM-2 algorithm
   * WHERE: Review scheduler, practice recommendations
   * WHY: Optimizes retention through spaced repetition
   */
  async getSkillsNeedingReview(studentId) {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/skills/review-needed`
    );
  }
  /**
   * Get session activity data
   *
   * WHAT: Retrieves learning session activity history
   * WHERE: Session activity widget, engagement analytics
   * WHY: Tracks learning patterns and engagement trends
   */
  async getSessionActivity(studentId, timeRange = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/sessions`,
      { params: { range: timeRange } }
    );
  }
  /**
   * Get learning progress over time
   *
   * WHAT: Retrieves time-series progress data for charts
   * WHERE: Progress chart visualizations
   * WHY: Shows learning trajectory and velocity
   */
  async getLearningProgressTimeSeries(studentId, courseId, timeRange = "30d") {
    const params = { range: timeRange };
    if (courseId) {
      params.course_id = courseId;
    }
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/progress-timeline`,
      { params }
    );
  }
  /**
   * Get course-level learning analytics (instructor view)
   *
   * WHAT: Retrieves aggregated learning analytics for entire course
   * WHERE: Instructor dashboard, course analytics page
   * WHY: Enables instructors to monitor class progress and identify issues
   */
  async getCourseLearningAnalytics(courseId) {
    return await apiClient.get(
      `${this.baseUrl}/course/${courseId}/summary`
    );
  }
  /**
   * Get organization-level learning analytics (org admin view)
   *
   * WHAT: Retrieves aggregated learning analytics for organization
   * WHERE: Organization admin dashboard
   * WHY: Provides organizational insights for resource allocation
   */
  async getOrganizationLearningAnalytics(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/organization/${organizationId}/summary`
    );
  }
  /**
   * Export learning analytics report
   *
   * WHAT: Generates downloadable analytics report
   * WHERE: Export functionality in analytics dashboards
   * WHY: Enables offline analysis and record keeping
   */
  async exportLearningAnalytics(studentId, format = "pdf") {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/export`,
      {
        params: { format },
        responseType: "blob"
      }
    );
  }
}
const learningAnalyticsService = new LearningAnalyticsService();
const useLearningAnalytics = (studentId, courseId, timeRange = "30d") => {
  const [summary, setSummary] = reactExports.useState(null);
  const [learningPaths, setLearningPaths] = reactExports.useState(null);
  const [skillMastery, setSkillMastery] = reactExports.useState(null);
  const [sessionActivity, setSessionActivity] = reactExports.useState(null);
  const [progressTimeSeries, setProgressTimeSeries] = reactExports.useState(
    null
  );
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const fetchLearningAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const isValidResponse = (data) => data !== null && data !== void 0 && typeof data === "object" && !Array.isArray(data);
      const isValidArrayResponse = (data) => Array.isArray(data);
      let summaryData = null;
      try {
        const raw = studentId ? await learningAnalyticsService.getStudentLearningAnalytics(studentId) : await learningAnalyticsService.getMyLearningAnalytics();
        summaryData = isValidResponse(raw) ? raw : null;
      } catch {
        summaryData = null;
      }
      const effectiveId = studentId || summaryData?.student_id;
      let pathsData = [];
      let skillsData = [];
      let sessionsData = [];
      let progressData = [];
      if (effectiveId) {
        const [rawPaths, rawSkills, rawSessions, rawProgress] = await Promise.allSettled([
          learningAnalyticsService.getStudentLearningPaths(effectiveId),
          learningAnalyticsService.getSkillMastery(effectiveId, courseId),
          learningAnalyticsService.getSessionActivity(effectiveId, timeRange),
          learningAnalyticsService.getLearningProgressTimeSeries(effectiveId, courseId, timeRange)
        ]);
        pathsData = rawPaths.status === "fulfilled" && isValidArrayResponse(rawPaths.value) ? rawPaths.value : [];
        skillsData = rawSkills.status === "fulfilled" && isValidArrayResponse(rawSkills.value) ? rawSkills.value : [];
        sessionsData = rawSessions.status === "fulfilled" && isValidArrayResponse(rawSessions.value) ? rawSessions.value : [];
        progressData = rawProgress.status === "fulfilled" && isValidArrayResponse(rawProgress.value) ? rawProgress.value : [];
      }
      setSummary(summaryData);
      setLearningPaths(pathsData);
      setSkillMastery(skillsData);
      setSessionActivity(sessionsData);
      setProgressTimeSeries(progressData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load learning analytics";
      setError(message);
      console.error("Learning analytics fetch error:", err);
      setSummary(null);
      setLearningPaths(null);
      setSkillMastery(null);
      setSessionActivity(null);
      setProgressTimeSeries(null);
    } finally {
      setIsLoading(false);
    }
  };
  reactExports.useEffect(() => {
    fetchLearningAnalytics();
  }, [studentId, courseId, timeRange]);
  return {
    summary,
    learningPaths,
    skillMastery,
    sessionActivity,
    progressTimeSeries,
    isLoading,
    error,
    refetch: fetchLearningAnalytics
  };
};
const chartContainer$1 = "_chartContainer_y26c0_3";
const chartWrapper = "_chartWrapper_y26c0_7";
const statsRow = "_statsRow_y26c0_12";
const statItem = "_statItem_y26c0_20";
const statLabel$1 = "_statLabel_y26c0_27";
const statValue$1 = "_statValue_y26c0_34";
const emptyState$3 = "_emptyState_y26c0_40";
const emptyIcon$3 = "_emptyIcon_y26c0_49";
const styles$4 = {
  chartContainer: chartContainer$1,
  chartWrapper,
  statsRow,
  statItem,
  statLabel: statLabel$1,
  statValue: statValue$1,
  emptyState: emptyState$3,
  emptyIcon: emptyIcon$3
};
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  plugin_title,
  plugin_tooltip,
  plugin_legend,
  index
);
const LearningProgressChart = ({ data }) => {
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No progress data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.emptyIcon, children: "📊" })
    ] });
  }
  const labels = data.map((point) => {
    const date = new Date(point.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });
  const chartData = {
    labels,
    datasets: [
      {
        label: "Progress %",
        data: data.map((point) => point.progress_percentage),
        borderColor: "#2196f3",
        backgroundColor: "rgba(33, 150, 243, 0.1)",
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: "#2196f3",
        pointBorderColor: "#fff",
        pointBorderWidth: 2
      },
      {
        label: "Engagement Score",
        data: data.map((point) => point.engagement_score),
        borderColor: "#4caf50",
        backgroundColor: "rgba(76, 175, 80, 0.1)",
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: "#4caf50",
        pointBorderColor: "#fff",
        pointBorderWidth: 2
      }
    ]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false
    },
    plugins: {
      legend: {
        display: true,
        position: "top",
        labels: {
          usePointStyle: true,
          padding: 15
        }
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const index2 = context[0].dataIndex;
            const date = new Date(data[index2].date);
            return date.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric"
            });
          },
          afterBody: (context) => {
            const index2 = context[0].dataIndex;
            const dataPoint = data[index2];
            return [
              `
Items Completed: ${dataPoint.items_completed}`,
              `Time Spent: ${Math.round(dataPoint.time_spent_minutes / 60)}h ${dataPoint.time_spent_minutes % 60}m`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          callback: (value) => `${value}%`
        },
        grid: {
          color: "rgba(0, 0, 0, 0.05)"
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.chartContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.chartWrapper, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Line, { data: chartData, options }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statsRow, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Total Items" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statValue, children: data[data.length - 1]?.items_completed || 0 })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Total Time" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.statValue, children: [
          Math.round(
            data.reduce((sum, point) => sum + point.time_spent_minutes, 0) / 60
          ),
          "h"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Avg Engagement" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.statValue, children: [
          Math.round(
            data.reduce((sum, point) => sum + point.engagement_score, 0) / data.length
          ),
          "%"
        ] })
      ] })
    ] })
  ] });
};
const widgetContainer$1 = "_widgetContainer_h0vi7_3";
const controls = "_controls_h0vi7_7";
const viewToggle$1 = "_viewToggle_h0vi7_16";
const toggleBtn$1 = "_toggleBtn_h0vi7_21";
const active$2 = "_active_h0vi7_36";
const sortSelector = "_sortSelector_h0vi7_42";
const sortSelect = "_sortSelect_h0vi7_42";
const chartView$1 = "_chartView_h0vi7_63";
const radarChart = "_radarChart_h0vi7_69";
const chartNote = "_chartNote_h0vi7_76";
const listView$1 = "_listView_h0vi7_83";
const skillCard = "_skillCard_h0vi7_89";
const skillHeader = "_skillHeader_h0vi7_95";
const skillName = "_skillName_h0vi7_102";
const masteryBadge = "_masteryBadge_h0vi7_109";
const progressSection$1 = "_progressSection_h0vi7_117";
const progressBar$1 = "_progressBar_h0vi7_124";
const progressFill$1 = "_progressFill_h0vi7_132";
const progressValue$1 = "_progressValue_h0vi7_137";
const skillMetrics = "_skillMetrics_h0vi7_145";
const metric = "_metric_h0vi7_152";
const metricLabel$1 = "_metricLabel_h0vi7_158";
const metricValue$1 = "_metricValue_h0vi7_165";
const repetitionInfo = "_repetitionInfo_h0vi7_171";
const repetitionMetric = "_repetitionMetric_h0vi7_179";
const repetitionLabel = "_repetitionLabel_h0vi7_185";
const repetitionValue = "_repetitionValue_h0vi7_190";
const lastPractice = "_lastPractice_h0vi7_196";
const summaryStats$1 = "_summaryStats_h0vi7_202";
const summaryItem$1 = "_summaryItem_h0vi7_210";
const summaryLabel$1 = "_summaryLabel_h0vi7_217";
const summaryValue$1 = "_summaryValue_h0vi7_224";
const emptyState$2 = "_emptyState_h0vi7_230";
const emptyIcon$2 = "_emptyIcon_h0vi7_239";
const styles$3 = {
  widgetContainer: widgetContainer$1,
  controls,
  viewToggle: viewToggle$1,
  toggleBtn: toggleBtn$1,
  active: active$2,
  sortSelector,
  sortSelect,
  chartView: chartView$1,
  radarChart,
  chartNote,
  listView: listView$1,
  skillCard,
  skillHeader,
  skillName,
  masteryBadge,
  progressSection: progressSection$1,
  progressBar: progressBar$1,
  progressFill: progressFill$1,
  progressValue: progressValue$1,
  skillMetrics,
  metric,
  metricLabel: metricLabel$1,
  metricValue: metricValue$1,
  repetitionInfo,
  repetitionMetric,
  repetitionLabel,
  repetitionValue,
  lastPractice,
  summaryStats: summaryStats$1,
  summaryItem: summaryItem$1,
  summaryLabel: summaryLabel$1,
  summaryValue: summaryValue$1,
  emptyState: emptyState$2,
  emptyIcon: emptyIcon$2
};
Chart.register(RadialLinearScale, PointElement, LineElement, index, plugin_tooltip, plugin_legend);
const SkillMasteryWidget = ({ skills }) => {
  const [sortBy, setSortBy] = reactExports.useState("mastery");
  const [viewMode, setViewMode] = reactExports.useState("chart");
  if (!skills || skills.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No skills tracked yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.emptyIcon, children: "🎯" })
    ] });
  }
  const getMasteryColor = (level) => {
    const colorMap = {
      novice: "#f44336",
      beginner: "#ff9800",
      intermediate: "#ffeb3b",
      proficient: "#8bc34a",
      expert: "#4caf50",
      master: "#2196f3"
    };
    return colorMap[level] || "#9e9e9e";
  };
  const sortedSkills = [...skills].sort((a, b) => {
    switch (sortBy) {
      case "mastery":
        return b.mastery_score - a.mastery_score;
      case "recent":
        if (!a.last_practiced_at) return 1;
        if (!b.last_practiced_at) return -1;
        return new Date(b.last_practiced_at).getTime() - new Date(a.last_practiced_at).getTime();
      case "name":
        return a.skill_topic.localeCompare(b.skill_topic);
      case "review":
        return a.current_interval_days - b.current_interval_days;
      default:
        return 0;
    }
  });
  const topSkills = sortedSkills.slice(0, 8);
  const radarData = {
    labels: topSkills.map((skill) => skill.skill_topic),
    datasets: [
      {
        label: "Mastery Score",
        data: topSkills.map((skill) => skill.mastery_score),
        backgroundColor: "rgba(33, 150, 243, 0.2)",
        borderColor: "#2196f3",
        borderWidth: 2,
        pointBackgroundColor: "#2196f3",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ]
  };
  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20
        },
        grid: {
          color: "rgba(0, 0, 0, 0.1)"
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => `Mastery: ${context.parsed.r}%`
        }
      }
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.widgetContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.controls, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.viewToggle, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles$3.toggleBtn} ${viewMode === "chart" ? styles$3.active : ""}`,
            onClick: () => setViewMode("chart"),
            "aria-pressed": viewMode === "chart",
            children: "Chart View"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles$3.toggleBtn} ${viewMode === "list" ? styles$3.active : ""}`,
            onClick: () => setViewMode("list"),
            "aria-pressed": viewMode === "list",
            children: "List View"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.sortSelector, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "sort-skills", children: "Sort by:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "sort-skills",
            value: sortBy,
            onChange: (e) => setSortBy(e.target.value),
            className: styles$3.sortSelect,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "mastery", children: "Mastery Level" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "recent", children: "Recently Practiced" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "name", children: "Skill Name" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "review", children: "Review Due" })
            ]
          }
        )
      ] })
    ] }),
    viewMode === "chart" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.chartView, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.radarChart, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Radar, { data: radarData, options: radarOptions }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3.chartNote, children: "Showing top 8 skills by mastery score" })
    ] }),
    viewMode === "list" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.listView, children: sortedSkills.map((skill) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$3.skillName, children: skill.skill_topic }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "span",
          {
            className: styles$3.masteryBadge,
            style: { backgroundColor: getMasteryColor(skill.mastery_level) },
            children: skill.mastery_level.charAt(0).toUpperCase() + skill.mastery_level.slice(1)
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.progressSection, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.progressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: styles$3.progressFill,
            style: {
              width: `${skill.mastery_score}%`,
              backgroundColor: getMasteryColor(skill.mastery_level)
            }
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.progressValue, children: [
          skill.mastery_score,
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillMetrics, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.metricLabel, children: "Assessments" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.metricValue, children: [
            skill.assessments_passed,
            "/",
            skill.assessments_completed
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.metricLabel, children: "Practice Time" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.metricValue, children: [
            Math.round(skill.total_practice_time_minutes / 60),
            "h"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.metricLabel, children: "Streak" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.metricValue, children: [
            skill.practice_streak_days,
            " days"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.repetitionInfo, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.repetitionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.repetitionLabel, children: "Retention:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.repetitionValue, children: [
            Math.round(skill.retention_estimate * 100),
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.repetitionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.repetitionLabel, children: "Review Interval:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.repetitionValue, children: [
            skill.current_interval_days,
            " days"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.repetitionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.repetitionLabel, children: "Ease Factor:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.repetitionValue, children: skill.ease_factor.toFixed(2) })
        ] })
      ] }),
      skill.last_practiced_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles$3.lastPractice, children: [
        "Last practiced:",
        " ",
        new Date(skill.last_practiced_at).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric"
        })
      ] })
    ] }, skill.id)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.summaryStats, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.summaryLabel, children: "Total Skills" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.summaryValue, children: skills.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.summaryLabel, children: "Avg Mastery" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.summaryValue, children: [
          Math.round(
            skills.reduce((sum, skill) => sum + skill.mastery_score, 0) / skills.length
          ),
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.summaryLabel, children: "Total Practice" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.summaryValue, children: [
          Math.round(
            skills.reduce((sum, skill) => sum + skill.total_practice_time_minutes, 0) / 60
          ),
          "h"
        ] })
      ] })
    ] })
  ] });
};
const pathsContainer = "_pathsContainer_192ug_3";
const pathCard = "_pathCard_192ug_9";
const pathHeader = "_pathHeader_192ug_15";
const pathTitleSection = "_pathTitleSection_192ug_29";
const pathTitle = "_pathTitle_192ug_29";
const statusBadge = "_statusBadge_192ug_42";
const expandButton = "_expandButton_192ug_50";
const progressSection = "_progressSection_192ug_60";
const progressBar = "_progressBar_192ug_67";
const progressFill = "_progressFill_192ug_75";
const progressValue = "_progressValue_192ug_80";
const quickStats = "_quickStats_192ug_88";
const stat = "_stat_192ug_42";
const statIcon$1 = "_statIcon_192ug_100";
const statText = "_statText_192ug_104";
const timeDiff = "_timeDiff_192ug_110";
const timeDiffSuccess = "_timeDiffSuccess_192ug_117";
const timeDiffWarning = "_timeDiffWarning_192ug_121";
const expandedContent = "_expandedContent_192ug_125";
const currentPosition = "_currentPosition_192ug_131";
const datesSection = "_datesSection_192ug_150";
const datesList = "_datesList_192ug_163";
const dateItem = "_dateItem_192ug_169";
const dateLabel = "_dateLabel_192ug_175";
const dateValue = "_dateValue_192ug_179";
const milestonesSection$1 = "_milestonesSection_192ug_184";
const milestonesList$1 = "_milestonesList_192ug_197";
const milestoneItem$1 = "_milestoneItem_192ug_203";
const milestoneIcon$1 = "_milestoneIcon_192ug_212";
const milestoneContent$1 = "_milestoneContent_192ug_217";
const milestoneName = "_milestoneName_192ug_221";
const milestoneDate$1 = "_milestoneDate_192ug_228";
const milestoneScore$1 = "_milestoneScore_192ug_234";
const performanceMetrics = "_performanceMetrics_192ug_241";
const metricsGrid = "_metricsGrid_192ug_250";
const metricItem = "_metricItem_192ug_256";
const metricLabel = "_metricLabel_192ug_262";
const metricValue = "_metricValue_192ug_267";
const emptyState$1 = "_emptyState_192ug_273";
const emptyIcon$1 = "_emptyIcon_192ug_282";
const styles$2 = {
  pathsContainer,
  pathCard,
  pathHeader,
  pathTitleSection,
  pathTitle,
  statusBadge,
  expandButton,
  progressSection,
  progressBar,
  progressFill,
  progressValue,
  quickStats,
  stat,
  statIcon: statIcon$1,
  statText,
  timeDiff,
  timeDiffSuccess,
  timeDiffWarning,
  expandedContent,
  currentPosition,
  datesSection,
  datesList,
  dateItem,
  dateLabel,
  dateValue,
  milestonesSection: milestonesSection$1,
  milestonesList: milestonesList$1,
  milestoneItem: milestoneItem$1,
  milestoneIcon: milestoneIcon$1,
  milestoneContent: milestoneContent$1,
  milestoneName,
  milestoneDate: milestoneDate$1,
  milestoneScore: milestoneScore$1,
  performanceMetrics,
  metricsGrid,
  metricItem,
  metricLabel,
  metricValue,
  emptyState: emptyState$1,
  emptyIcon: emptyIcon$1
};
const LearningPathProgress = ({ paths }) => {
  const [expandedPath, setExpandedPath] = reactExports.useState(null);
  if (!paths || paths.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No active learning paths" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.emptyIcon, children: "🛤️" })
    ] });
  }
  const getStatusColor = (status) => {
    const colorMap = {
      not_started: "#9e9e9e",
      in_progress: "#2196f3",
      on_track: "#4caf50",
      behind: "#ff9800",
      at_risk: "#f44336",
      completed: "#8bc34a",
      abandoned: "#757575"
    };
    return colorMap[status] || "#9e9e9e";
  };
  const getStatusLabel = (status) => {
    return status.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
  };
  const togglePathExpansion = (pathId) => {
    setExpandedPath(expandedPath === pathId ? null : pathId);
  };
  const calculateTimeDifference = (path) => {
    if (!path.estimated_completion_at) return null;
    const now = /* @__PURE__ */ new Date();
    const estimated = new Date(path.estimated_completion_at);
    const diffDays = Math.ceil((estimated.getTime() - now.getTime()) / (1e3 * 60 * 60 * 24));
    if (path.actual_completion_at) {
      const actual = new Date(path.actual_completion_at);
      const completionDiff = Math.ceil(
        (actual.getTime() - estimated.getTime()) / (1e3 * 60 * 60 * 24)
      );
      return completionDiff > 0 ? `Completed ${completionDiff} days late` : `Completed ${Math.abs(completionDiff)} days early`;
    }
    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return "Due today";
    } else {
      return `${diffDays} days remaining`;
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.pathsContainer, children: paths.map((path) => {
    const isExpanded = expandedPath === path.id;
    const timeDiff2 = calculateTimeDifference(path);
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.pathCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: styles$2.pathHeader,
          onClick: () => togglePathExpansion(path.id),
          role: "button",
          tabIndex: 0,
          onKeyPress: (e) => {
            if (e.key === "Enter" || e.key === " ") {
              togglePathExpansion(path.id);
            }
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.pathTitleSection, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("h3", { className: styles$2.pathTitle, children: [
                "Learning Path ",
                path.track_id
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  className: styles$2.statusBadge,
                  style: { backgroundColor: getStatusColor(path.status) },
                  children: getStatusLabel(path.status)
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("button", { className: styles$2.expandButton, "aria-expanded": isExpanded, children: isExpanded ? "▼" : "▶" })
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.progressSection, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.progressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: styles$2.progressFill,
            style: {
              width: `${path.overall_progress}%`,
              backgroundColor: getStatusColor(path.status)
            }
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.progressValue, children: [
          path.overall_progress.toFixed(1),
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.quickStats, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.stat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.statIcon, children: "⏱️" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.statText, children: [
            Math.round(path.total_time_spent_minutes / 60),
            "h"
          ] })
        ] }),
        path.avg_quiz_score !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.stat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.statIcon, children: "📝" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.statText, children: [
            path.avg_quiz_score.toFixed(0),
            "%"
          ] })
        ] }),
        path.milestones_completed && path.milestones_completed.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.stat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.statIcon, children: "🏆" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.statText, children: [
            path.milestones_completed.length,
            " milestones"
          ] })
        ] })
      ] }),
      timeDiff2 && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "p",
        {
          className: `${styles$2.timeDiff} ${timeDiff2.includes("overdue") || timeDiff2.includes("late") ? styles$2.timeDiffWarning : styles$2.timeDiffSuccess}`,
          children: timeDiff2
        }
      ),
      isExpanded && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.expandedContent, children: [
        path.current_course_id && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.currentPosition, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { children: "Current Position" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
            "Course ID: ",
            path.current_course_id
          ] }),
          path.current_module_order && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
            "Module: ",
            path.current_module_order
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.datesSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { children: "Timeline" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.datesList, children: [
            path.started_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.dateItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateLabel, children: "Started:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateValue, children: new Date(path.started_at).toLocaleDateString() })
            ] }),
            path.estimated_completion_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.dateItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateLabel, children: "Est. Completion:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateValue, children: new Date(path.estimated_completion_at).toLocaleDateString() })
            ] }),
            path.actual_completion_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.dateItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateLabel, children: "Completed:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateValue, children: new Date(path.actual_completion_at).toLocaleDateString() })
            ] }),
            path.last_activity_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.dateItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateLabel, children: "Last Activity:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.dateValue, children: new Date(path.last_activity_at).toLocaleDateString() })
            ] })
          ] })
        ] }),
        path.milestones_completed && path.milestones_completed.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.milestonesSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { children: "Completed Milestones" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.milestonesList, children: path.milestones_completed.map((milestone, index2) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.milestoneItem, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.milestoneIcon, children: "✓" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.milestoneContent, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.milestoneName, children: milestone.name }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.milestoneDate, children: new Date(milestone.completed_at).toLocaleDateString() }),
              milestone.score !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles$2.milestoneScore, children: [
                "Score: ",
                milestone.score,
                "%"
              ] })
            ] })
          ] }, index2)) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.performanceMetrics, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { children: "Performance" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricsGrid, children: [
            path.avg_quiz_score !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricLabel, children: "Avg Quiz Score" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.metricValue, children: [
                path.avg_quiz_score.toFixed(1),
                "%"
              ] })
            ] }),
            path.avg_assignment_score !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricLabel, children: "Avg Assignment Score" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.metricValue, children: [
                path.avg_assignment_score.toFixed(1),
                "%"
              ] })
            ] })
          ] })
        ] })
      ] })
    ] }, path.id);
  }) });
};
const widgetContainer = "_widgetContainer_2mpqt_3";
const viewToggle = "_viewToggle_2mpqt_7";
const toggleBtn = "_toggleBtn_2mpqt_13";
const active$1 = "_active_2mpqt_28";
const chartView = "_chartView_2mpqt_34";
const chartContainer = "_chartContainer_2mpqt_39";
const chartLegend = "_chartLegend_2mpqt_45";
const legendItem = "_legendItem_2mpqt_54";
const legendDot = "_legendDot_2mpqt_62";
const pieChartContainer = "_pieChartContainer_2mpqt_69";
const breakdownStats = "_breakdownStats_2mpqt_75";
const breakdownItem = "_breakdownItem_2mpqt_84";
const breakdownLabel = "_breakdownLabel_2mpqt_91";
const breakdownValue = "_breakdownValue_2mpqt_98";
const listView = "_listView_2mpqt_104";
const sessionCard = "_sessionCard_2mpqt_112";
const sessionHeader = "_sessionHeader_2mpqt_118";
const sessionDate = "_sessionDate_2mpqt_125";
const engagementBadge = "_engagementBadge_2mpqt_131";
const sessionMetrics = "_sessionMetrics_2mpqt_139";
const sessionMetric = "_sessionMetric_2mpqt_139";
const metricIcon = "_metricIcon_2mpqt_154";
const sessionActivities = "_sessionActivities_2mpqt_158";
const summaryStats = "_summaryStats_2mpqt_164";
const summaryItem = "_summaryItem_2mpqt_174";
const summaryLabel = "_summaryLabel_2mpqt_181";
const summaryValue = "_summaryValue_2mpqt_189";
const emptyState = "_emptyState_2mpqt_195";
const emptyIcon = "_emptyIcon_2mpqt_204";
const styles$1 = {
  widgetContainer,
  viewToggle,
  toggleBtn,
  active: active$1,
  chartView,
  chartContainer,
  chartLegend,
  legendItem,
  legendDot,
  pieChartContainer,
  breakdownStats,
  breakdownItem,
  breakdownLabel,
  breakdownValue,
  listView,
  sessionCard,
  sessionHeader,
  sessionDate,
  engagementBadge,
  sessionMetrics,
  sessionMetric,
  metricIcon,
  sessionActivities,
  summaryStats,
  summaryItem,
  summaryLabel,
  summaryValue,
  emptyState,
  emptyIcon
};
Chart.register(CategoryScale, LinearScale, BarElement, ArcElement, plugin_title, plugin_tooltip, plugin_legend);
const SessionActivityWidget = ({ sessions }) => {
  const [viewMode, setViewMode] = reactExports.useState("timeline");
  if (!sessions || sessions.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No session activity recorded" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.emptyIcon, children: "📊" })
    ] });
  }
  const activityBreakdown = sessions.reduce(
    (acc, session) => {
      acc.contentViewed += session.content_items_viewed;
      acc.quizzesAttempted += session.quizzes_attempted;
      acc.labsWorked += session.labs_worked_on;
      return acc;
    },
    { contentViewed: 0, quizzesAttempted: 0, labsWorked: 0 }
  );
  const timelineData = {
    labels: sessions.map((session) => {
      const date = new Date(session.started_at);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }),
    datasets: [
      {
        label: "Session Duration (minutes)",
        data: sessions.map((session) => session.duration_minutes),
        backgroundColor: sessions.map((session) => {
          if (session.engagement_score >= 80) return "rgba(76, 175, 80, 0.7)";
          if (session.engagement_score >= 60) return "rgba(33, 150, 243, 0.7)";
          if (session.engagement_score >= 40) return "rgba(255, 152, 0, 0.7)";
          return "rgba(244, 67, 54, 0.7)";
        }),
        borderColor: sessions.map((session) => {
          if (session.engagement_score >= 80) return "#4caf50";
          if (session.engagement_score >= 60) return "#2196f3";
          if (session.engagement_score >= 40) return "#ff9800";
          return "#f44336";
        }),
        borderWidth: 2,
        borderRadius: 4
      }
    ]
  };
  const timelineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const session = sessions[context[0].dataIndex];
            const date = new Date(session.started_at);
            return date.toLocaleString("en-US", {
              month: "short",
              day: "numeric",
              hour: "numeric",
              minute: "2-digit"
            });
          },
          afterBody: (context) => {
            const session = sessions[context[0].dataIndex];
            return [
              `Engagement: ${session.engagement_score}%`,
              `Activities: ${session.activities_count}`,
              `Content Viewed: ${session.content_items_viewed}`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => `${value}m`
        }
      }
    }
  };
  const breakdownData = {
    labels: ["Content Viewed", "Quizzes Attempted", "Labs Worked On"],
    datasets: [
      {
        data: [
          activityBreakdown.contentViewed,
          activityBreakdown.quizzesAttempted,
          activityBreakdown.labsWorked
        ],
        backgroundColor: [
          "rgba(33, 150, 243, 0.7)",
          "rgba(255, 152, 0, 0.7)",
          "rgba(156, 39, 176, 0.7)"
        ],
        borderColor: ["#2196f3", "#ff9800", "#9c27b0"],
        borderWidth: 2
      }
    ]
  };
  const breakdownOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom"
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || "";
            const value = context.parsed || 0;
            const total = activityBreakdown.contentViewed + activityBreakdown.quizzesAttempted + activityBreakdown.labsWorked;
            const percentage = total > 0 ? (value / total * 100).toFixed(1) : "0";
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
  };
  const summaryStats2 = {
    totalSessions: sessions.length,
    totalDuration: sessions.reduce((sum, s) => sum + s.duration_minutes, 0),
    avgDuration: Math.round(
      sessions.reduce((sum, s) => sum + s.duration_minutes, 0) / sessions.length
    ),
    avgEngagement: Math.round(
      sessions.reduce((sum, s) => sum + s.engagement_score, 0) / sessions.length
    ),
    totalActivities: sessions.reduce((sum, s) => sum + s.activities_count, 0)
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.widgetContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.viewToggle, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles$1.toggleBtn} ${viewMode === "timeline" ? styles$1.active : ""}`,
          onClick: () => setViewMode("timeline"),
          "aria-pressed": viewMode === "timeline",
          children: "Timeline"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles$1.toggleBtn} ${viewMode === "breakdown" ? styles$1.active : ""}`,
          onClick: () => setViewMode("breakdown"),
          "aria-pressed": viewMode === "breakdown",
          children: "Breakdown"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles$1.toggleBtn} ${viewMode === "list" ? styles$1.active : ""}`,
          onClick: () => setViewMode("list"),
          "aria-pressed": viewMode === "list",
          children: "List"
        }
      )
    ] }),
    viewMode === "timeline" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.chartView, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.chartContainer, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Bar, { data: timelineData, options: timelineOptions }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.chartLegend, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.legendItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.legendDot, style: { backgroundColor: "#4caf50" } }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "High Engagement (80%+)" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.legendItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.legendDot, style: { backgroundColor: "#2196f3" } }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Good Engagement (60-79%)" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.legendItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.legendDot, style: { backgroundColor: "#ff9800" } }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Moderate Engagement (40-59%)" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.legendItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.legendDot, style: { backgroundColor: "#f44336" } }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Low Engagement (<40%)" })
        ] })
      ] })
    ] }),
    viewMode === "breakdown" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.chartView, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.pieChartContainer, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Pie, { data: breakdownData, options: breakdownOptions }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.breakdownStats, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.breakdownItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownLabel, children: "Content Items" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownValue, children: activityBreakdown.contentViewed })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.breakdownItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownLabel, children: "Quizzes" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownValue, children: activityBreakdown.quizzesAttempted })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.breakdownItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownLabel, children: "Labs" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.breakdownValue, children: activityBreakdown.labsWorked })
        ] })
      ] })
    ] }),
    viewMode === "list" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.listView, children: sessions.map((session) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.sessionDate, children: new Date(session.started_at).toLocaleString("en-US", {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit"
        }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "span",
          {
            className: styles$1.engagementBadge,
            style: {
              backgroundColor: session.engagement_score >= 80 ? "#4caf50" : session.engagement_score >= 60 ? "#2196f3" : session.engagement_score >= 40 ? "#ff9800" : "#f44336"
            },
            children: [
              session.engagement_score,
              "% engaged"
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionMetrics, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.metricIcon, children: "⏱️" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            session.duration_minutes,
            "m"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.metricIcon, children: "📄" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            session.content_items_viewed,
            " items"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.metricIcon, children: "📝" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            session.quizzes_attempted,
            " quizzes"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sessionMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.metricIcon, children: "💻" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            session.labs_worked_on,
            " labs"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles$1.sessionActivities, children: [
        session.activities_count,
        " total activities"
      ] })
    ] }, session.session_id)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryStats, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryLabel, children: "Total Sessions" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryValue, children: summaryStats2.totalSessions })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryLabel, children: "Total Time" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.summaryValue, children: [
          Math.round(summaryStats2.totalDuration / 60),
          "h"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryLabel, children: "Avg Duration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.summaryValue, children: [
          summaryStats2.avgDuration,
          "m"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryLabel, children: "Avg Engagement" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.summaryValue, children: [
          summaryStats2.avgEngagement,
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryLabel, children: "Total Activities" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.summaryValue, children: summaryStats2.totalActivities })
      ] })
    ] })
  ] });
};
const dashboardContainer = "_dashboardContainer_1sqys_9";
const dashboardHeader = "_dashboardHeader_1sqys_15";
const titleSection = "_titleSection_1sqys_23";
const subtitle = "_subtitle_1sqys_30";
const timeRangeSelector = "_timeRangeSelector_1sqys_36";
const timeRangeBtn = "_timeRangeBtn_1sqys_42";
const active = "_active_1sqys_58";
const summaryGrid = "_summaryGrid_1sqys_64";
const statCard = "_statCard_1sqys_71";
const statIcon = "_statIcon_1sqys_87";
const statContent = "_statContent_1sqys_91";
const statValue = "_statValue_1sqys_100";
const statLabel = "_statLabel_1sqys_107";
const widgetsGrid = "_widgetsGrid_1sqys_112";
const widgetCard = "_widgetCard_1sqys_119";
const reviewSection = "_reviewSection_1sqys_133";
const reviewSubtitle = "_reviewSubtitle_1sqys_148";
const reviewGrid = "_reviewGrid_1sqys_154";
const reviewCard = "_reviewCard_1sqys_160";
const reviewMeta = "_reviewMeta_1sqys_173";
const reviewBadge = "_reviewBadge_1sqys_180";
const reviewInterval = "_reviewInterval_1sqys_189";
const reviewProgress = "_reviewProgress_1sqys_194";
const reviewProgressBar = "_reviewProgressBar_1sqys_200";
const reviewProgressFill = "_reviewProgressFill_1sqys_208";
const reviewScore = "_reviewScore_1sqys_214";
const milestonesSection = "_milestonesSection_1sqys_220";
const milestonesList = "_milestonesList_1sqys_234";
const milestoneItem = "_milestoneItem_1sqys_240";
const milestoneIcon = "_milestoneIcon_1sqys_249";
const milestoneContent = "_milestoneContent_1sqys_254";
const milestoneDate = "_milestoneDate_1sqys_261";
const milestoneScore = "_milestoneScore_1sqys_267";
const loadingContainer = "_loadingContainer_1sqys_274";
const spinner = "_spinner_1sqys_283";
const errorContainer = "_errorContainer_1sqys_297";
const retryButton = "_retryButton_1sqys_312";
const styles = {
  dashboardContainer,
  dashboardHeader,
  titleSection,
  subtitle,
  timeRangeSelector,
  timeRangeBtn,
  active,
  summaryGrid,
  statCard,
  statIcon,
  statContent,
  statValue,
  statLabel,
  widgetsGrid,
  widgetCard,
  reviewSection,
  reviewSubtitle,
  reviewGrid,
  reviewCard,
  reviewMeta,
  reviewBadge,
  reviewInterval,
  reviewProgress,
  reviewProgressBar,
  reviewProgressFill,
  reviewScore,
  milestonesSection,
  milestonesList,
  milestoneItem,
  milestoneIcon,
  milestoneContent,
  milestoneDate,
  milestoneScore,
  loadingContainer,
  spinner,
  errorContainer,
  retryButton
};
const LearningAnalyticsDashboard = ({
  viewType,
  studentId,
  courseId,
  organizationId
}) => {
  const { studentId: paramStudentId, courseId: paramCourseId } = useParams();
  const effectiveStudentId = studentId || paramStudentId;
  const effectiveCourseId = courseId || paramCourseId;
  const [timeRange, setTimeRange] = reactExports.useState("30d");
  const {
    summary,
    learningPaths,
    skillMastery,
    sessionActivity,
    progressTimeSeries,
    isLoading,
    error,
    refetch
  } = useLearningAnalytics(effectiveStudentId, effectiveCourseId, timeRange);
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loadingContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.spinner, "aria-label": "Loading analytics" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading learning analytics..." })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Error Loading Learning Analytics" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: refetch, className: styles.retryButton, children: "Retry" })
    ] });
  }
  const timeRangeOptions = [
    { value: "7d", label: "Week" },
    { value: "30d", label: "Month" },
    { value: "90d", label: "Quarter" },
    { value: "6m", label: "6 Months" },
    { value: "1y", label: "Year" },
    { value: "all", label: "All Time" }
  ];
  const getDashboardTitle = () => {
    switch (viewType) {
      case "student":
        return "My Learning Analytics";
      case "instructor":
        return "Student Learning Analytics";
      case "org_admin":
        return "Organization Learning Analytics";
      default:
        return "Learning Analytics";
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.dashboardContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.dashboardHeader, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.titleSection, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: getDashboardTitle() }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.subtitle, children: [
          viewType === "student" && "Track your learning progress and skill development",
          viewType === "instructor" && "Monitor student learning outcomes and engagement",
          viewType === "org_admin" && "Organizational learning insights and trends"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.timeRangeSelector, children: timeRangeOptions.map((option) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles.timeRangeBtn} ${timeRange === option.value ? styles.active : ""}`,
          onClick: () => setTimeRange(option.value),
          "aria-pressed": timeRange === option.value,
          children: option.label
        },
        option.value
      )) })
    ] }),
    summary && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.summaryGrid, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.statIcon, children: "📈" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Engagement Score" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.statValue, children: [
            summary.overall_engagement_score,
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.statLabel, children: "Overall engagement" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.statIcon, children: "🎯" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Skills Mastered" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.statValue, children: [
            summary.skills_mastered,
            "/",
            summary.total_skills_tracked
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.statLabel, children: summary.total_skills_tracked > 0 ? `${Math.round(summary.skills_mastered / summary.total_skills_tracked * 100)}% mastery rate` : "No skills tracked" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.statIcon, children: "🔥" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Current Streak" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.statValue, children: [
            summary.current_streak_days,
            " days"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.statLabel, children: [
            "Longest: ",
            summary.longest_streak_days,
            " days"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.statIcon, children: "⏱️" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.statContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Learning Time" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.statValue, children: [
            Math.round(summary.total_learning_time_minutes / 60),
            "h"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.statLabel, children: "Total time invested" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetsGrid, children: [
      progressTimeSeries && progressTimeSeries.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Learning Progress Over Time" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(LearningProgressChart, { data: progressTimeSeries })
      ] }),
      skillMastery && skillMastery.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Skill Mastery" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(SkillMasteryWidget, { skills: skillMastery })
      ] }),
      learningPaths && learningPaths.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Learning Path Progress" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(LearningPathProgress, { paths: learningPaths })
      ] }),
      sessionActivity && sessionActivity.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Session Activity" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(SessionActivityWidget, { sessions: sessionActivity })
      ] })
    ] }),
    summary && summary.skills_needing_review && summary.skills_needing_review.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.reviewSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Skills Due for Review" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.reviewSubtitle, children: "Based on spaced repetition schedule (SM-2 algorithm)" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.reviewGrid, children: summary.skills_needing_review.map((skill) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.reviewCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: skill.skill_topic }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.reviewMeta, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.reviewBadge, children: skill.mastery_level.charAt(0).toUpperCase() + skill.mastery_level.slice(1) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.reviewInterval, children: [
            "Next review: ",
            skill.current_interval_days,
            " days"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.reviewProgress, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.reviewProgressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: styles.reviewProgressFill,
              style: { width: `${skill.mastery_score}%` }
            }
          ) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.reviewScore, children: [
            skill.mastery_score,
            "%"
          ] })
        ] })
      ] }, skill.id)) })
    ] }),
    summary && summary.recent_milestones && summary.recent_milestones.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.milestonesSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Recent Milestones" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.milestonesList, children: summary.recent_milestones.map((milestone, index2) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.milestoneItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.milestoneIcon, children: "🏆" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.milestoneContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: milestone.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.milestoneDate, children: [
            "Completed: ",
            new Date(milestone.completed_at).toLocaleDateString()
          ] }),
          milestone.score && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.milestoneScore, children: [
            "Score: ",
            milestone.score,
            "%"
          ] })
        ] })
      ] }, index2)) })
    ] })
  ] });
};
export {
  LearningAnalyticsDashboard,
  LearningAnalyticsDashboard as default
};
//# sourceMappingURL=LearningAnalyticsDashboard-By2R68UZ.js.map
