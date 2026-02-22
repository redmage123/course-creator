import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
import { c as apiClient } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
class InstructorInsightsService {
  baseUrl = "/analytics/instructor";
  /**
   * Get instructor effectiveness metrics
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Teaching effectiveness metrics
   */
  async getEffectivenessMetrics(instructorId, timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/effectiveness`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get current instructor's effectiveness metrics
   */
  async getMyEffectivenessMetrics(timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/me/effectiveness`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get course performance for specific course
   *
   * @param courseId - Course UUID
   * @param timeRange - Time range for metrics
   * @returns Course performance analytics
   */
  async getCoursePerformance(courseId, timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/courses/${courseId}/performance`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get all course performances for instructor
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Array of course performance data
   */
  async getAllCoursePerformances(instructorId, timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/courses/performance`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get current instructor's course performances
   */
  async getMyCoursePerformances(timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/me/courses/performance`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get student engagement metrics
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Student engagement analytics
   */
  async getStudentEngagement(instructorId, timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/engagement`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get current instructor's student engagement
   */
  async getMyStudentEngagement(timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/me/engagement`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get teaching recommendations
   *
   * @param instructorId - Instructor UUID
   * @param category - Optional category filter
   * @param priority - Optional priority filter
   * @returns Array of recommendations
   */
  async getRecommendations(instructorId, category, priority) {
    const params = {};
    if (category) params.category = category;
    if (priority) params.priority = priority;
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/recommendations`,
      { params }
    );
  }
  /**
   * Get current instructor's recommendations
   */
  async getMyRecommendations(category, priority) {
    const params = {};
    if (category) params.category = category;
    if (priority) params.priority = priority;
    return await apiClient.get(
      `${this.baseUrl}/me/recommendations`,
      { params }
    );
  }
  /**
   * Acknowledge a recommendation
   *
   * @param recommendationId - Recommendation UUID
   */
  async acknowledgeRecommendation(recommendationId) {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/acknowledge`
    );
  }
  /**
   * Mark recommendation as in progress
   *
   * @param recommendationId - Recommendation UUID
   */
  async startRecommendation(recommendationId) {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/start`
    );
  }
  /**
   * Complete a recommendation
   *
   * @param recommendationId - Recommendation UUID
   * @param outcomeData - Optional outcome tracking data
   */
  async completeRecommendation(recommendationId, outcomeData) {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/complete`,
      outcomeData
    );
  }
  /**
   * Dismiss a recommendation
   *
   * @param recommendationId - Recommendation UUID
   * @param reason - Reason for dismissal
   */
  async dismissRecommendation(recommendationId, reason) {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/dismiss`,
      { reason }
    );
  }
  /**
   * Get peer comparisons
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for comparison
   * @returns Array of peer comparison data
   */
  async getPeerComparisons(instructorId, timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/peer-comparisons`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get current instructor's peer comparisons
   */
  async getMyPeerComparisons(timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/me/peer-comparisons`,
      { params: { range: timeRange2 } }
    );
  }
  /**
   * Get content effectiveness breakdown
   *
   * @param instructorId - Instructor UUID
   * @param courseId - Optional course filter
   * @param timeRange - Time range for analysis
   * @returns Array of content effectiveness data
   */
  async getContentEffectiveness(instructorId, courseId, timeRange2 = "30d") {
    const params = { range: timeRange2 };
    if (courseId) params.course_id = courseId;
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/content-effectiveness`,
      { params }
    );
  }
  /**
   * Get current instructor's content effectiveness
   */
  async getMyContentEffectiveness(courseId, timeRange2 = "30d") {
    const params = { range: timeRange2 };
    if (courseId) params.course_id = courseId;
    return await apiClient.get(
      `${this.baseUrl}/me/content-effectiveness`,
      { params }
    );
  }
  /**
   * Export insights report
   *
   * @param instructorId - Instructor UUID
   * @param format - Report format (pdf, csv, excel)
   * @param timeRange - Time range for report
   * @returns Report blob
   */
  async exportReport(instructorId, format = "pdf", timeRange2 = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/export`,
      {
        params: { format, range: timeRange2 },
        responseType: "blob"
      }
    );
  }
}
const instructorInsightsService = new InstructorInsightsService();
const useInstructorInsights = (instructorId, courseId, timeRange2 = "30d") => {
  const [effectiveness, setEffectiveness] = reactExports.useState(null);
  const [coursePerformances, setCoursePerformances] = reactExports.useState([]);
  const [engagement, setEngagement] = reactExports.useState(null);
  const [recommendations, setRecommendations] = reactExports.useState([]);
  const [peerComparisons, setPeerComparisons] = reactExports.useState([]);
  const [contentEffectiveness, setContentEffectiveness] = reactExports.useState([]);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const fetchInsights = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const useMe = !instructorId;
      const [
        effectivenessData,
        performanceData,
        engagementData,
        recommendationsData,
        peerComparisonsData,
        contentEffectivenessData
      ] = await Promise.all([
        // Effectiveness metrics
        useMe ? instructorInsightsService.getMyEffectivenessMetrics(timeRange2) : instructorInsightsService.getEffectivenessMetrics(instructorId, timeRange2),
        // Course performances
        useMe ? instructorInsightsService.getMyCoursePerformances(timeRange2) : instructorInsightsService.getAllCoursePerformances(instructorId, timeRange2),
        // Student engagement
        useMe ? instructorInsightsService.getMyStudentEngagement(timeRange2) : instructorInsightsService.getStudentEngagement(instructorId, timeRange2),
        // Recommendations
        useMe ? instructorInsightsService.getMyRecommendations() : instructorInsightsService.getRecommendations(instructorId),
        // Peer comparisons
        useMe ? instructorInsightsService.getMyPeerComparisons(timeRange2) : instructorInsightsService.getPeerComparisons(instructorId, timeRange2),
        // Content effectiveness
        useMe ? instructorInsightsService.getMyContentEffectiveness(courseId, timeRange2) : instructorInsightsService.getContentEffectiveness(instructorId, courseId, timeRange2)
      ]);
      setEffectiveness(effectivenessData);
      setCoursePerformances(performanceData);
      setEngagement(engagementData);
      setRecommendations(recommendationsData);
      setPeerComparisons(peerComparisonsData);
      setContentEffectiveness(contentEffectivenessData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load instructor insights";
      setError(message);
      console.error("Instructor insights fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };
  const acknowledgeRecommendation = async (id) => {
    try {
      await instructorInsightsService.acknowledgeRecommendation(id);
      setRecommendations(
        (prev) => prev.map(
          (rec) => rec.id === id ? { ...rec, status: "acknowledged", acknowledged_at: (/* @__PURE__ */ new Date()).toISOString() } : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to acknowledge recommendation";
      console.error("Error acknowledging recommendation:", err);
      throw new Error(message);
    }
  };
  const startRecommendation = async (id) => {
    try {
      await instructorInsightsService.startRecommendation(id);
      setRecommendations(
        (prev) => prev.map(
          (rec) => rec.id === id ? { ...rec, status: "in_progress" } : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start recommendation";
      console.error("Error starting recommendation:", err);
      throw new Error(message);
    }
  };
  const completeRecommendation = async (id, outcome) => {
    try {
      await instructorInsightsService.completeRecommendation(id, outcome);
      setRecommendations(
        (prev) => prev.map(
          (rec) => rec.id === id ? { ...rec, status: "completed", completed_at: (/* @__PURE__ */ new Date()).toISOString() } : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to complete recommendation";
      console.error("Error completing recommendation:", err);
      throw new Error(message);
    }
  };
  const dismissRecommendation = async (id, reason) => {
    try {
      await instructorInsightsService.dismissRecommendation(id, reason);
      setRecommendations((prev) => prev.filter((rec) => rec.id !== id));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to dismiss recommendation";
      console.error("Error dismissing recommendation:", err);
      throw new Error(message);
    }
  };
  reactExports.useEffect(() => {
    fetchInsights();
  }, [instructorId, courseId, timeRange2]);
  return {
    // Data
    effectiveness,
    coursePerformances,
    engagement,
    recommendations,
    peerComparisons,
    contentEffectiveness,
    // State
    isLoading,
    error,
    // Actions
    refetch: fetchInsights,
    acknowledgeRecommendation,
    startRecommendation,
    completeRecommendation,
    dismissRecommendation
  };
};
const widget$3 = "_widget_7cf70_5";
const header$2 = "_header_7cf70_12";
const title$4 = "_title_7cf70_21";
const timeRange = "_timeRange_7cf70_28";
const legend = "_legend_7cf70_34";
const legendItem = "_legendItem_7cf70_41";
const legendColor = "_legendColor_7cf70_49";
const chartContainer = "_chartContainer_7cf70_55";
const contentRow = "_contentRow_7cf70_61";
const contentType = "_contentType_7cf70_68";
const contentLabel = "_contentLabel_7cf70_74";
const contentCount = "_contentCount_7cf70_82";
const improvementBadge = "_improvementBadge_7cf70_87";
const metrics = "_metrics_7cf70_98";
const metricBar = "_metricBar_7cf70_104";
const metricLabel$2 = "_metricLabel_7cf70_110";
const metricValue$2 = "_metricValue_7cf70_118";
const barBackground = "_barBackground_7cf70_123";
const barFill = "_barFill_7cf70_131";
const summary = "_summary_7cf70_137";
const summaryItem = "_summaryItem_7cf70_145";
const summaryLabel = "_summaryLabel_7cf70_151";
const summaryValue = "_summaryValue_7cf70_156";
const emptyState$3 = "_emptyState_7cf70_162";
const styles$4 = {
  widget: widget$3,
  header: header$2,
  title: title$4,
  timeRange,
  legend,
  legendItem,
  legendColor,
  chartContainer,
  contentRow,
  contentType,
  contentLabel,
  contentCount,
  improvementBadge,
  metrics,
  metricBar,
  metricLabel: metricLabel$2,
  metricValue: metricValue$2,
  barBackground,
  barFill,
  summary,
  summaryItem,
  summaryLabel,
  summaryValue,
  emptyState: emptyState$3
};
const ContentEffectivenessChart = ({
  contentEffectiveness,
  timeRange: timeRange2
}) => {
  const getScoreColor = (score, needsImprovement) => {
    if (needsImprovement) return "#f44336";
    if (score >= 80) return "#4caf50";
    if (score >= 60) return "#ff9800";
    return "#f44336";
  };
  const formatTimeRange = (range) => {
    const ranges = {
      "7d": "Last 7 Days",
      "30d": "Last 30 Days",
      "90d": "Last 90 Days",
      "1y": "Last Year",
      all: "All Time"
    };
    return ranges[range];
  };
  if (!contentEffectiveness || contentEffectiveness.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.widget, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.header, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$4.title, children: "Content Effectiveness" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.timeRange, children: formatTimeRange(timeRange2) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No content data available for this time period." }) })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.widget, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$4.title, children: "Content Effectiveness" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.timeRange, children: formatTimeRange(timeRange2) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.legend, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.legendColor, style: { backgroundColor: "#2196f3" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Average Rating" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.legendColor, style: { backgroundColor: "#4caf50" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Completion Rate" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.legendColor, style: { backgroundColor: "#ff9800" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Engagement Score" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.chartContainer, children: contentEffectiveness.map((content, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.contentRow, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.contentType, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$4.contentLabel, children: content.content_type }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.contentCount, children: [
          content.total_items,
          " items"
        ] }),
        content.needs_improvement && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.improvementBadge, children: "Needs Improvement" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metrics, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricBar, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricLabel, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Rating" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.metricValue, children: [
              content.average_rating.toFixed(1),
              "/5.0"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.barBackground, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: styles$4.barFill,
              style: {
                width: `${content.average_rating / 5 * 100}%`,
                backgroundColor: getScoreColor(
                  content.average_rating / 5 * 100,
                  content.needs_improvement
                )
              }
            }
          ) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricBar, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricLabel, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Completion" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.metricValue, children: [
              content.completion_rate.toFixed(1),
              "%"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.barBackground, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: styles$4.barFill,
              style: {
                width: `${content.completion_rate}%`,
                backgroundColor: getScoreColor(
                  content.completion_rate,
                  content.needs_improvement
                )
              }
            }
          ) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricBar, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.metricLabel, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Engagement" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4.metricValue, children: [
              content.engagement_score.toFixed(0),
              "/100"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.barBackground, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: styles$4.barFill,
              style: {
                width: `${content.engagement_score}%`,
                backgroundColor: getScoreColor(
                  content.engagement_score,
                  content.needs_improvement
                )
              }
            }
          ) })
        ] })
      ] })
    ] }, index)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.summary, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryLabel, children: "Content Types:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryValue, children: contentEffectiveness.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryLabel, children: "Total Items:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryValue, children: contentEffectiveness.reduce((sum, c) => sum + c.total_items, 0) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.summaryItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryLabel, children: "Needs Improvement:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.summaryValue, children: contentEffectiveness.filter((c) => c.needs_improvement).length })
      ] })
    ] })
  ] });
};
const widget$2 = "_widget_pv6cq_5";
const title$3 = "_title_pv6cq_12";
const metricsGrid = "_metricsGrid_pv6cq_19";
const metric = "_metric_pv6cq_19";
const metricIcon = "_metricIcon_pv6cq_35";
const metricContent = "_metricContent_pv6cq_39";
const metricLabel$1 = "_metricLabel_pv6cq_43";
const metricValue$1 = "_metricValue_pv6cq_49";
const section = "_section_pv6cq_55";
const sectionTitle = "_sectionTitle_pv6cq_61";
const statsList = "_statsList_pv6cq_68";
const statRow = "_statRow_pv6cq_74";
const statLabel = "_statLabel_pv6cq_81";
const statValue = "_statValue_pv6cq_86";
const responseMetrics = "_responseMetrics_pv6cq_92";
const responseRate = "_responseRate_pv6cq_99";
const responseCircle = "_responseCircle_pv6cq_104";
const responseInner = "_responseInner_pv6cq_114";
const responseValue = "_responseValue_pv6cq_125";
const responsePercent = "_responsePercent_pv6cq_132";
const responseLabel = "_responseLabel_pv6cq_137";
const responseStats = "_responseStats_pv6cq_144";
const emptyState$2 = "_emptyState_pv6cq_150";
const styles$3 = {
  widget: widget$2,
  title: title$3,
  metricsGrid,
  metric,
  metricIcon,
  metricContent,
  metricLabel: metricLabel$1,
  metricValue: metricValue$1,
  section,
  sectionTitle,
  statsList,
  statRow,
  statLabel,
  statValue,
  responseMetrics,
  responseRate,
  responseCircle,
  responseInner,
  responseValue,
  responsePercent,
  responseLabel,
  responseStats,
  emptyState: emptyState$2
};
const StudentEngagementWidget = ({
  engagement
}) => {
  if (!engagement) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.widget, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$3.title, children: "Student Engagement" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No engagement data available." }) })
    ] });
  }
  const formatDuration = (minutes) => {
    if (!minutes) return "N/A";
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };
  const formatHour = (hour) => {
    if (hour === void 0 || hour === null) return "N/A";
    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;
    return `${displayHour}:00 ${period}`;
  };
  const getResponseRateColor = (rate) => {
    if (!rate) return "#999";
    if (rate >= 90) return "#4caf50";
    if (rate >= 70) return "#ff9800";
    return "#f44336";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.widget, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$3.title, children: "Student Engagement" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metricsGrid, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricIcon, children: "📊" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metricContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricLabel, children: "Total Sessions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricValue, children: engagement.total_sessions.toLocaleString() })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricIcon, children: "⏱️" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metricContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricLabel, children: "Avg Session" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricValue, children: formatDuration(engagement.average_session_duration) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricIcon, children: "🕐" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metricContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricLabel, children: "Peak Hour" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricValue, children: formatHour(engagement.peak_hour) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metric, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricIcon, children: "📅" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.metricContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricLabel, children: "Most Active" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.metricValue, children: engagement.most_active_day || "N/A" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$3.sectionTitle, children: "Student Interactions" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statsList, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Content Views" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.total_content_views.toLocaleString() })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Lab Sessions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.total_lab_sessions.toLocaleString() })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Quiz Attempts" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.total_quiz_attempts.toLocaleString() })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Forum Posts" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.total_forum_posts.toLocaleString() })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$3.sectionTitle, children: "Instructor Responsiveness" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.responseMetrics, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.responseRate, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: styles$3.responseCircle,
            style: {
              background: `conic-gradient(${getResponseRateColor(engagement.response_rate)} ${(engagement.response_rate || 0) * 3.6}deg, #f0f0f0 0deg)`
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.responseInner, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.responseValue, children: [
                engagement.response_rate?.toFixed(0) || "N/A",
                engagement.response_rate !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.responsePercent, children: "%" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.responseLabel, children: "Response Rate" })
            ] })
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.responseStats, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Questions Asked" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.total_questions_asked.toLocaleString() })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Questions Answered" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.questions_answered.toLocaleString() })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.statRow, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statLabel, children: "Avg Response Time" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.statValue, children: engagement.average_response_time ? `${engagement.average_response_time.toFixed(1)}h` : "N/A" })
          ] })
        ] })
      ] })
    ] })
  ] });
};
const widget$1 = "_widget_abo6w_5";
const title$2 = "_title_abo6w_12";
const courseList = "_courseList_abo6w_19";
const courseCard = "_courseCard_abo6w_27";
const selected = "_selected_abo6w_40";
const courseHeader = "_courseHeader_abo6w_45";
const courseName = "_courseName_abo6w_52";
const enrollmentBadge = "_enrollmentBadge_abo6w_59";
const courseMetrics = "_courseMetrics_abo6w_68";
const metricItem = "_metricItem_abo6w_75";
const metricLabel = "_metricLabel_abo6w_81";
const metricValue = "_metricValue_abo6w_88";
const performanceMetrics = "_performanceMetrics_abo6w_94";
const performanceItem = "_performanceItem_abo6w_101";
const performanceLabel = "_performanceLabel_abo6w_110";
const performanceValue = "_performanceValue_abo6w_115";
const ratings = "_ratings_abo6w_120";
const ratingItem = "_ratingItem_abo6w_127";
const ratingLabel = "_ratingLabel_abo6w_133";
const ratingStars = "_ratingStars_abo6w_138";
const peerSection = "_peerSection_abo6w_144";
const peerTitle = "_peerTitle_abo6w_150";
const peerDescription = "_peerDescription_abo6w_157";
const peerList = "_peerList_abo6w_163";
const peerItem = "_peerItem_abo6w_169";
const peerMetric = "_peerMetric_abo6w_175";
const peerMetricName = "_peerMetricName_abo6w_182";
const peerPosition = "_peerPosition_abo6w_188";
const peerStats = "_peerStats_abo6w_197";
const peerStat = "_peerStat_abo6w_197";
const peerStatLabel = "_peerStatLabel_abo6w_210";
const peerStatValue = "_peerStatValue_abo6w_217";
const emptyState$1 = "_emptyState_abo6w_223";
const styles$2 = {
  widget: widget$1,
  title: title$2,
  courseList,
  courseCard,
  selected,
  courseHeader,
  courseName,
  enrollmentBadge,
  courseMetrics,
  metricItem,
  metricLabel,
  metricValue,
  performanceMetrics,
  performanceItem,
  performanceLabel,
  performanceValue,
  ratings,
  ratingItem,
  ratingLabel,
  ratingStars,
  peerSection,
  peerTitle,
  peerDescription,
  peerList,
  peerItem,
  peerMetric,
  peerMetricName,
  peerPosition,
  peerStats,
  peerStat,
  peerStatLabel,
  peerStatValue,
  emptyState: emptyState$1
};
const CoursePerformanceWidget = ({
  coursePerformances,
  peerComparisons
}) => {
  const [selectedCourse, setSelectedCourse] = reactExports.useState(null);
  if (!coursePerformances || coursePerformances.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.widget, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$2.title, children: "Course Performance" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No course data available." }) })
    ] });
  }
  const getScoreColor = (score) => {
    if (!score) return "#999";
    if (score >= 80) return "#4caf50";
    if (score >= 60) return "#ff9800";
    return "#f44336";
  };
  const handleCourseClick = (courseId) => {
    setSelectedCourse(selectedCourse === courseId ? null : courseId);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.widget, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$2.title, children: "Course Performance" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.courseList, children: coursePerformances.map((course) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        className: `${styles$2.courseCard} ${selectedCourse === course.course_id ? styles$2.selected : ""}`,
        onClick: () => handleCourseClick(course.course_id),
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.courseHeader, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.courseName, children: course.course_title || `Course ${course.course_id.slice(0, 8)}` }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.enrollmentBadge, children: [
              course.total_enrolled,
              " students"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.courseMetrics, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricLabel, children: "Active" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricValue, children: course.active_students })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricLabel, children: "Completed" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricValue, children: course.completed_students })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.metricItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricLabel, children: "Dropped" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.metricValue, children: course.dropped_students })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.performanceMetrics, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.performanceItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.performanceLabel, children: "Average Score" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "span",
                {
                  className: styles$2.performanceValue,
                  style: { color: getScoreColor(course.average_score) },
                  children: [
                    course.average_score?.toFixed(1) || "N/A",
                    "%"
                  ]
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.performanceItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.performanceLabel, children: "Pass Rate" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "span",
                {
                  className: styles$2.performanceValue,
                  style: { color: getScoreColor(course.pass_rate) },
                  children: [
                    course.pass_rate?.toFixed(1) || "N/A",
                    "%"
                  ]
                }
              )
            ] })
          ] }),
          (course.content_rating || course.difficulty_rating || course.workload_rating) && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.ratings, children: [
            course.content_rating && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.ratingItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.ratingLabel, children: "Content" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.ratingStars, children: [
                "★".repeat(Math.round(course.content_rating)),
                "☆".repeat(5 - Math.round(course.content_rating))
              ] })
            ] }),
            course.difficulty_rating && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.ratingItem, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.ratingLabel, children: "Difficulty" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.ratingStars, children: [
                "★".repeat(Math.round(course.difficulty_rating)),
                "☆".repeat(5 - Math.round(course.difficulty_rating))
              ] })
            ] })
          ] })
        ]
      },
      course.id
    )) }),
    peerComparisons && peerComparisons.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.peerTitle, children: "Peer Benchmarking" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.peerDescription, children: "See how you compare to other instructors (anonymized)" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.peerList, children: peerComparisons.slice(0, 3).map((comparison) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerMetric, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerMetricName, children: comparison.metric_name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerPosition, children: comparison.position_description })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerStats, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerStat, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatLabel, children: "You" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatValue, children: comparison.instructor_score?.toFixed(1) || "N/A" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerStat, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatLabel, children: "Avg" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatValue, children: comparison.peer_average?.toFixed(1) || "N/A" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.peerStat, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatLabel, children: "Median" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.peerStatValue, children: comparison.peer_median?.toFixed(1) || "N/A" })
          ] })
        ] })
      ] }, comparison.id)) })
    ] })
  ] });
};
const widget = "_widget_12ngp_5";
const header$1 = "_header_12ngp_12";
const title$1 = "_title_12ngp_21";
const filters = "_filters_12ngp_28";
const filterButton = "_filterButton_12ngp_33";
const active = "_active_12ngp_49";
const recommendationsList = "_recommendationsList_12ngp_55";
const recommendationCard = "_recommendationCard_12ngp_61";
const expanded = "_expanded_12ngp_73";
const cardHeader = "_cardHeader_12ngp_77";
const headerLeft = "_headerLeft_12ngp_86";
const categoryIcon = "_categoryIcon_12ngp_93";
const headerContent$1 = "_headerContent_12ngp_97";
const recommendationTitle = "_recommendationTitle_12ngp_101";
const recommendationCategory = "_recommendationCategory_12ngp_108";
const headerRight = "_headerRight_12ngp_115";
const priorityBadge = "_priorityBadge_12ngp_121";
const statusBadge = "_statusBadge_12ngp_131";
const expandIcon = "_expandIcon_12ngp_141";
const cardBody = "_cardBody_12ngp_147";
const description = "_description_12ngp_153";
const actionItems = "_actionItems_12ngp_160";
const actionItemsTitle = "_actionItemsTitle_12ngp_164";
const actionItemsList = "_actionItemsList_12ngp_171";
const impact = "_impact_12ngp_183";
const effort = "_effort_12ngp_184";
const cardActions = "_cardActions_12ngp_195";
const actionButton = "_actionButton_12ngp_203";
const primaryButton = "_primaryButton_12ngp_224";
const dismissButton = "_dismissButton_12ngp_236";
const emptyState = "_emptyState_12ngp_247";
const emptySubtext = "_emptySubtext_12ngp_258";
const styles$1 = {
  widget,
  header: header$1,
  title: title$1,
  filters,
  filterButton,
  active,
  recommendationsList,
  recommendationCard,
  expanded,
  cardHeader,
  headerLeft,
  categoryIcon,
  headerContent: headerContent$1,
  recommendationTitle,
  recommendationCategory,
  headerRight,
  priorityBadge,
  statusBadge,
  expandIcon,
  cardBody,
  description,
  actionItems,
  actionItemsTitle,
  actionItemsList,
  impact,
  effort,
  cardActions,
  actionButton,
  primaryButton,
  dismissButton,
  emptyState,
  emptySubtext
};
const TeachingRecommendationsWidget = ({
  recommendations,
  onAcknowledge,
  onStart,
  onComplete,
  onDismiss
}) => {
  const [expandedId, setExpandedId] = reactExports.useState(null);
  const [filter, setFilter] = reactExports.useState("all");
  const [processing, setProcessing] = reactExports.useState(null);
  const getPriorityColor = (priority) => {
    const colors = {
      critical: "#d32f2f",
      high: "#f57c00",
      medium: "#fbc02d",
      low: "#689f38"
    };
    return colors[priority];
  };
  const getCategoryIcon = (category) => {
    const icons = {
      engagement: "🎯",
      content_quality: "📚",
      responsiveness: "⚡",
      assessment: "✅",
      communication: "💬",
      organization: "📋",
      accessibility: "♿",
      technical: "⚙️"
    };
    return icons[category] || "📌";
  };
  const handleAction = async (id, action, reason) => {
    try {
      setProcessing(id);
      switch (action) {
        case "acknowledge":
          await onAcknowledge(id);
          break;
        case "start":
          await onStart(id);
          break;
        case "complete":
          await onComplete(id);
          break;
        case "dismiss":
          if (reason) {
            await onDismiss(id, reason);
          }
          break;
      }
    } catch (error) {
      console.error("Error performing action:", error);
      alert("Failed to perform action. Please try again.");
    } finally {
      setProcessing(null);
    }
  };
  const toggleExpanded = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };
  const filteredRecommendations = filter === "all" ? recommendations : recommendations.filter((rec) => rec.priority === filter);
  const sortedRecommendations = [...filteredRecommendations].sort((a, b) => {
    const priorityOrder = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3
    };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });
  if (!recommendations || recommendations.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.widget, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$1.title, children: "Teaching Recommendations" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.emptyState, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "🎉 Great job! No recommendations at this time." }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.emptySubtext, children: "Keep up the excellent work with your teaching." })
      ] })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.widget, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$1.title, children: "Teaching Recommendations" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.filters, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            className: `${styles$1.filterButton} ${filter === "all" ? styles$1.active : ""}`,
            onClick: () => setFilter("all"),
            children: [
              "All (",
              recommendations.length,
              ")"
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            className: `${styles$1.filterButton} ${filter === "critical" ? styles$1.active : ""}`,
            onClick: () => setFilter("critical"),
            children: [
              "Critical (",
              recommendations.filter((r) => r.priority === "critical").length,
              ")"
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            className: `${styles$1.filterButton} ${filter === "high" ? styles$1.active : ""}`,
            onClick: () => setFilter("high"),
            children: [
              "High (",
              recommendations.filter((r) => r.priority === "high").length,
              ")"
            ]
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.recommendationsList, children: sortedRecommendations.map((rec) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        className: `${styles$1.recommendationCard} ${expandedId === rec.id ? styles$1.expanded : ""}`,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.cardHeader, onClick: () => toggleExpanded(rec.id), children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.headerLeft, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.categoryIcon, children: getCategoryIcon(rec.category) }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.headerContent, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1.recommendationTitle, children: rec.title }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.recommendationCategory, children: rec.category.replace("_", " ") })
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.headerRight, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  className: styles$1.priorityBadge,
                  style: { backgroundColor: getPriorityColor(rec.priority) },
                  children: rec.priority
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.statusBadge, children: rec.status.replace("_", " ") }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.expandIcon, children: expandedId === rec.id ? "▼" : "▶" })
            ] })
          ] }),
          expandedId === rec.id && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.cardBody, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.description, children: rec.description }),
            rec.action_items && rec.action_items.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.actionItems, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$1.actionItemsTitle, children: "Action Items:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: styles$1.actionItemsList, children: rec.action_items.map((item, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: item }, index)) })
            ] }),
            rec.expected_impact && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.impact, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Expected Impact:" }),
              " ",
              rec.expected_impact
            ] }),
            rec.estimated_effort && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.effort, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Estimated Effort:" }),
              " ",
              rec.estimated_effort
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.cardActions, children: [
              rec.status === "pending" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    className: styles$1.actionButton,
                    onClick: () => handleAction(rec.id, "acknowledge"),
                    disabled: processing === rec.id,
                    children: "Acknowledge"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    className: styles$1.actionButton,
                    onClick: () => handleAction(rec.id, "start"),
                    disabled: processing === rec.id,
                    children: "Start Working"
                  }
                )
              ] }),
              rec.status === "acknowledged" && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  className: styles$1.actionButton,
                  onClick: () => handleAction(rec.id, "start"),
                  disabled: processing === rec.id,
                  children: "Start Working"
                }
              ),
              rec.status === "in_progress" && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  className: `${styles$1.actionButton} ${styles$1.primaryButton}`,
                  onClick: () => handleAction(rec.id, "complete"),
                  disabled: processing === rec.id,
                  children: "Mark Complete"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  className: `${styles$1.actionButton} ${styles$1.dismissButton}`,
                  onClick: () => {
                    const reason = prompt("Why are you dismissing this recommendation?");
                    if (reason) {
                      handleAction(rec.id, "dismiss", reason);
                    }
                  },
                  disabled: processing === rec.id,
                  children: "Dismiss"
                }
              )
            ] })
          ] })
        ]
      },
      rec.id
    )) })
  ] });
};
const dashboard = "_dashboard_zfiex_13";
const header = "_header_zfiex_22";
const headerContent = "_headerContent_zfiex_31";
const title = "_title_zfiex_35";
const subtitle = "_subtitle_zfiex_42";
const controls = "_controls_zfiex_49";
const label = "_label_zfiex_55";
const select = "_select_zfiex_61";
const refreshButton = "_refreshButton_zfiex_81";
const summaryCards = "_summaryCards_zfiex_102";
const card = "_card_zfiex_109";
const cardIcon = "_cardIcon_zfiex_125";
const cardContent = "_cardContent_zfiex_130";
const cardTitle = "_cardTitle_zfiex_134";
const cardValue = "_cardValue_zfiex_143";
const cardSubvalue = "_cardSubvalue_zfiex_150";
const trend = "_trend_zfiex_157";
const improving = "_improving_zfiex_169";
const stable = "_stable_zfiex_174";
const declining = "_declining_zfiex_179";
const widgetsGrid = "_widgetsGrid_zfiex_185";
const widgetFull = "_widgetFull_zfiex_191";
const widgetHalf = "_widgetHalf_zfiex_195";
const loadingContainer = "_loadingContainer_zfiex_200";
const spinner = "_spinner_zfiex_209";
const spin = "_spin_zfiex_209";
const errorContainer = "_errorContainer_zfiex_229";
const retryButton = "_retryButton_zfiex_250";
const styles = {
  dashboard,
  header,
  headerContent,
  title,
  subtitle,
  controls,
  label,
  select,
  refreshButton,
  summaryCards,
  card,
  cardIcon,
  cardContent,
  cardTitle,
  cardValue,
  cardSubvalue,
  trend,
  improving,
  stable,
  declining,
  widgetsGrid,
  widgetFull,
  widgetHalf,
  loadingContainer,
  spinner,
  spin,
  errorContainer,
  retryButton
};
const InstructorInsightsDashboard = ({
  instructorId,
  courseId
}) => {
  const [timeRange2, setTimeRange] = reactExports.useState("30d");
  const {
    effectiveness,
    coursePerformances,
    engagement,
    recommendations,
    peerComparisons,
    contentEffectiveness,
    isLoading,
    error,
    refetch,
    acknowledgeRecommendation,
    startRecommendation,
    completeRecommendation,
    dismissRecommendation
  } = useInstructorInsights(instructorId, courseId, timeRange2);
  const handleTimeRangeChange = (event) => {
    setTimeRange(event.target.value);
  };
  const handleRefresh = () => {
    refetch();
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.dashboard, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loadingContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.spinner }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading instructor insights..." })
    ] }) });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.dashboard, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Error Loading Insights" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleRefresh, className: styles.retryButton, children: "Retry" })
    ] }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.dashboard, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.headerContent, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles.title, children: "Instructor Insights" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.subtitle, children: "Track your teaching effectiveness and receive personalized improvement recommendations" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "timeRange", className: styles.label, children: "Time Range:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "timeRange",
            value: timeRange2,
            onChange: handleTimeRangeChange,
            className: styles.select,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "7d", children: "Last 7 Days" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "30d", children: "Last 30 Days" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "90d", children: "Last 90 Days" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "1y", children: "Last Year" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Time" })
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: handleRefresh, className: styles.refreshButton, title: "Refresh data", children: "↻ Refresh" })
      ] })
    ] }),
    effectiveness && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.summaryCards, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.card, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.cardIcon, style: { color: "#4caf50" }, children: "⭐" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles.cardTitle, children: "Overall Rating" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardValue, children: [
            effectiveness.overall_rating?.toFixed(1) || "N/A",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.cardSubvalue, children: " / 5.0" })
          ] }),
          effectiveness.rating_trend && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles.trend} ${styles[effectiveness.rating_trend]}`, children: [
            effectiveness.rating_trend === "improving" && "↑",
            effectiveness.rating_trend === "declining" && "↓",
            effectiveness.rating_trend === "stable" && "→",
            " ",
            effectiveness.rating_trend
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.card, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.cardIcon, style: { color: "#2196f3" }, children: "👥" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles.cardTitle, children: "Students Taught" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.cardValue, children: effectiveness.total_students_taught })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.card, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.cardIcon, style: { color: "#ff9800" }, children: "📈" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles.cardTitle, children: "Completion Rate" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardValue, children: [
            effectiveness.course_completion_rate?.toFixed(1) || "N/A",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.cardSubvalue, children: "%" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.card, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.cardIcon, style: { color: "#9c27b0" }, children: "🎯" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles.cardTitle, children: "Engagement Score" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.cardValue, children: [
            effectiveness.engagement_score?.toFixed(0) || "N/A",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.cardSubvalue, children: " / 100" })
          ] }),
          effectiveness.engagement_trend && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles.trend} ${styles[effectiveness.engagement_trend]}`, children: [
            effectiveness.engagement_trend === "improving" && "↑",
            effectiveness.engagement_trend === "declining" && "↓",
            effectiveness.engagement_trend === "stable" && "→",
            " ",
            effectiveness.engagement_trend
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.widgetsGrid, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.widgetFull, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        TeachingRecommendationsWidget,
        {
          recommendations,
          onAcknowledge: acknowledgeRecommendation,
          onStart: startRecommendation,
          onComplete: completeRecommendation,
          onDismiss: dismissRecommendation
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.widgetHalf, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        CoursePerformanceWidget,
        {
          coursePerformances,
          peerComparisons
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.widgetHalf, children: /* @__PURE__ */ jsxRuntimeExports.jsx(StudentEngagementWidget, { engagement }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.widgetFull, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        ContentEffectivenessChart,
        {
          contentEffectiveness,
          timeRange: timeRange2
        }
      ) })
    ] })
  ] });
};
export {
  InstructorInsightsDashboard,
  InstructorInsightsDashboard as default
};
//# sourceMappingURL=InstructorInsightsDashboard-CJ7JRKmo.js.map
