import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, i as useParams } from "./react-vendor-cEae-lCc.js";
import { L as Line, C as Chart, a as CategoryScale, b as LinearScale, P as PointElement, c as LineElement, p as plugin_title, d as plugin_tooltip, e as plugin_legend, i as index, B as Bar, f as BarElement, D as Doughnut, A as ArcElement, R as Radar, g as RadialLinearScale } from "./index-BM3tqO1q.js";
const ANALYTICS_API_BASE = "https://176.9.99.103:8000/api/v1";
class AnalyticsServiceError extends Error {
  constructor(message, statusCode, detail) {
    super(message);
    this.statusCode = statusCode;
    this.detail = detail;
    this.name = "AnalyticsServiceError";
  }
}
async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "An error occurred"
    }));
    throw new AnalyticsServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }
  return response.json();
}
const analyticsService = {
  /**
   * Get student engagement data
   */
  async getEngagement(studentId, courseId, timeRange) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/engagement?time_range=${timeRange}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get student progress data
   */
  async getProgress(studentId, courseId) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/progress-summary`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get quiz performance data
   */
  async getQuizPerformance(studentId, courseId) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/quiz-performance`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get lab proficiency data
   */
  async getLabProficiency(studentId, courseId) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/lab-proficiency`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get risk assessment for student (instructor view)
   */
  async getRiskAssessment(studentId, courseId) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/risk-assessment`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get course-level analytics
   */
  async getCourseAnalytics(courseId, timeRange) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/courses/${courseId}/analytics?time_range=${timeRange}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Record student activity
   */
  async recordActivity(studentId, courseId, activityType, metadata) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/activities`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          activity_type: activityType,
          timestamp: (/* @__PURE__ */ new Date()).toISOString(),
          metadata
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Record quiz performance
   */
  async recordQuizPerformance(studentId, courseId, quizId, score, passed) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/quiz-performance`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          quiz_id: quizId,
          score,
          passed,
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Record lab usage
   */
  async recordLabUsage(studentId, courseId, labId, duration, completed) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/lab-usage`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          lab_id: labId,
          duration_seconds: duration,
          completed,
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Update progress
   */
  async updateProgress(studentId, courseId, completedItems, totalItems) {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/progress`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          completed_items: completedItems,
          total_items: totalItems,
          completion_percentage: completedItems / totalItems * 100,
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        })
      }
    );
    return handleResponse(response);
  }
};
const useAnalytics = (viewType, studentId, courseId, timeRange) => {
  const [engagement, setEngagement] = reactExports.useState(null);
  const [progress, setProgress] = reactExports.useState(null);
  const [quizPerformance, setQuizPerformance] = reactExports.useState(null);
  const [labProficiency, setLabProficiency] = reactExports.useState(null);
  const [riskAssessment, setRiskAssessment] = reactExports.useState(null);
  const [courseAnalytics, setCourseAnalytics] = reactExports.useState(null);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);
      switch (viewType) {
        case "student":
          if (!studentId || !courseId) {
            throw new Error("Student ID and Course ID required for student view");
          }
          const [
            engagementData,
            progressData,
            quizData,
            labData
          ] = await Promise.all([
            analyticsService.getEngagement(studentId, courseId, timeRange),
            analyticsService.getProgress(studentId, courseId),
            analyticsService.getQuizPerformance(studentId, courseId),
            analyticsService.getLabProficiency(studentId, courseId)
          ]);
          setEngagement(engagementData);
          setProgress(progressData);
          setQuizPerformance(quizData);
          setLabProficiency(labData);
          break;
        case "instructor":
          if (!studentId || !courseId) {
            throw new Error("Student ID and Course ID required for instructor view");
          }
          const [
            instrEngagement,
            instrProgress,
            instrQuiz,
            instrLab,
            riskData
          ] = await Promise.all([
            analyticsService.getEngagement(studentId, courseId, timeRange),
            analyticsService.getProgress(studentId, courseId),
            analyticsService.getQuizPerformance(studentId, courseId),
            analyticsService.getLabProficiency(studentId, courseId),
            analyticsService.getRiskAssessment(studentId, courseId)
          ]);
          setEngagement(instrEngagement);
          setProgress(instrProgress);
          setQuizPerformance(instrQuiz);
          setLabProficiency(instrLab);
          setRiskAssessment(riskData);
          break;
        case "course":
          if (!courseId) {
            throw new Error("Course ID required for course view");
          }
          const courseData = await analyticsService.getCourseAnalytics(courseId, timeRange);
          setCourseAnalytics(courseData);
          break;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load analytics";
      setError(message);
      console.error("Analytics fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };
  reactExports.useEffect(() => {
    fetchAnalytics();
  }, [viewType, studentId, courseId, timeRange]);
  return {
    engagement,
    progress,
    quizPerformance,
    labProficiency,
    riskAssessment,
    courseAnalytics,
    isLoading,
    error,
    refetch: fetchAnalytics
  };
};
const chartContainer$3 = "_chartContainer_dv1bq_5";
const chartWrapper$3 = "_chartWrapper_dv1bq_12";
const emptyState$3 = "_emptyState_dv1bq_18";
const legend$2 = "_legend_dv1bq_27";
const legendItem$2 = "_legendItem_dv1bq_34";
const legendDot$2 = "_legendDot_dv1bq_42";
const styles$6 = {
  chartContainer: chartContainer$3,
  chartWrapper: chartWrapper$3,
  emptyState: emptyState$3,
  legend: legend$2,
  legendItem: legendItem$2,
  legendDot: legendDot$2
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
const EngagementChart = ({ data }) => {
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$6.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No engagement data available" }) });
  }
  const labels = data.map((point) => {
    const date = new Date(point.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });
  const chartData = {
    labels,
    datasets: [
      {
        label: "Engagement Score",
        data: data.map((point) => point.score),
        borderColor: "#2196f3",
        backgroundColor: "rgba(33, 150, 243, 0.1)",
        pointBackgroundColor: data.map((point) => {
          if (point.score >= 70) return "#4caf50";
          if (point.score >= 50) return "#ff9800";
          return "#f44336";
        }),
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        fill: true
      }
    ]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `Engagement: ${context.parsed.y}%`;
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          callback: (value2) => `${value2}%`
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
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.chartContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$6.chartWrapper, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Line, { data: chartData, options }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.legend, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.legendDot, style: { backgroundColor: "#4caf50" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "High (70+)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.legendDot, style: { backgroundColor: "#ff9800" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Medium (50-69)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.legendDot, style: { backgroundColor: "#f44336" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Low (<50)" })
      ] })
    ] })
  ] });
};
const chartContainer$2 = "_chartContainer_19jhm_5";
const chartWrapper$2 = "_chartWrapper_19jhm_12";
const emptyState$2 = "_emptyState_19jhm_18";
const legend$1 = "_legend_19jhm_27";
const legendItem$1 = "_legendItem_19jhm_34";
const legendDot$1 = "_legendDot_19jhm_42";
const styles$5 = {
  chartContainer: chartContainer$2,
  chartWrapper: chartWrapper$2,
  emptyState: emptyState$2,
  legend: legend$1,
  legendItem: legendItem$1,
  legendDot: legendDot$1
};
Chart.register(
  CategoryScale,
  LinearScale,
  BarElement,
  plugin_title,
  plugin_tooltip,
  plugin_legend
);
const ProgressChart = ({ data }) => {
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No progress data available" }) });
  }
  const labels = data.map((point) => {
    const date = new Date(point.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });
  const chartData = {
    labels,
    datasets: [
      {
        label: "Course Progress",
        data: data.map((point) => point.completion_percentage),
        backgroundColor: data.map((point) => {
          const percentage = point.completion_percentage;
          if (percentage === 100) return "#4caf50";
          if (percentage >= 75) return "#8bc34a";
          if (percentage >= 50) return "#ff9800";
          if (percentage >= 25) return "#ff5722";
          return "#f44336";
        }),
        borderColor: "#2196f3",
        borderWidth: 0,
        borderRadius: 4,
        barThickness: 40
      }
    ]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const dataPoint = data[context.dataIndex];
            return [
              `Progress: ${context.parsed.y}%`,
              `Items Completed: ${dataPoint.items_completed}`
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
          callback: (value2) => `${value2}%`
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
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.chartContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.chartWrapper, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Bar, { data: chartData, options }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.legend, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.legendDot, style: { backgroundColor: "#4caf50" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Complete (100%)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.legendDot, style: { backgroundColor: "#8bc34a" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "High (75-99%)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.legendDot, style: { backgroundColor: "#ff9800" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Medium (50-74%)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.legendDot, style: { backgroundColor: "#f44336" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Low (<50%)" })
      ] })
    ] })
  ] });
};
const chartContainer$1 = "_chartContainer_t3bu7_5";
const chartWrapper$1 = "_chartWrapper_t3bu7_13";
const centerText = "_centerText_t3bu7_20";
const centerValue = "_centerValue_t3bu7_29";
const centerLabel = "_centerLabel_t3bu7_36";
const emptyState$1 = "_emptyState_t3bu7_44";
const stats = "_stats_t3bu7_53";
const statItem = "_statItem_t3bu7_60";
const statValue = "_statValue_t3bu7_67";
const statLabel = "_statLabel_t3bu7_73";
const styles$4 = {
  chartContainer: chartContainer$1,
  chartWrapper: chartWrapper$1,
  centerText,
  centerValue,
  centerLabel,
  emptyState: emptyState$1,
  stats,
  statItem,
  statValue,
  statLabel
};
Chart.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  plugin_title,
  plugin_tooltip,
  plugin_legend
);
const QuizPerformanceChart = ({ data }) => {
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No quiz performance data available" }) });
  }
  const passedCount = data.filter((point) => point.passed).length;
  const failedCount = data.length - passedCount;
  const averageScore = Math.round(
    data.reduce((sum, point) => sum + point.score, 0) / data.length
  );
  const chartData = {
    labels: ["Passed", "Failed"],
    datasets: [
      {
        label: "Quiz Results",
        data: [passedCount, failedCount],
        backgroundColor: ["#4caf50", "#f44336"],
        borderColor: ["#fff", "#fff"],
        borderWidth: 3,
        hoverOffset: 10
      }
    ]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "70%",
    plugins: {
      legend: {
        display: true,
        position: "bottom",
        labels: {
          padding: 20,
          font: {
            size: 13
          }
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || "";
            const value2 = context.parsed || 0;
            const percentage = (value2 / data.length * 100).toFixed(1);
            return `${label}: ${value2} (${percentage}%)`;
          }
        }
      }
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.chartContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.chartWrapper, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Doughnut, { data: chartData, options }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.centerText, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.centerValue, children: [
          averageScore,
          "%"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.centerLabel, children: "Avg Score" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.stats, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statValue, children: passedCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Passed" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statValue, children: failedCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Failed" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.statItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statValue, children: data.length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.statLabel, children: "Total" })
      ] })
    ] })
  ] });
};
const chartContainer = "_chartContainer_1ap4r_5";
const chartWrapper = "_chartWrapper_1ap4r_12";
const emptyState = "_emptyState_1ap4r_20";
const legend = "_legend_1ap4r_29";
const legendItem = "_legendItem_1ap4r_36";
const legendDot = "_legendDot_1ap4r_44";
const skillsList = "_skillsList_1ap4r_51";
const skillItem = "_skillItem_1ap4r_58";
const skillHeader = "_skillHeader_1ap4r_64";
const skillName = "_skillName_1ap4r_71";
const skillValue = "_skillValue_1ap4r_77";
const progressBar = "_progressBar_1ap4r_83";
const progressFill = "_progressFill_1ap4r_92";
const skillMeta = "_skillMeta_1ap4r_98";
const styles$3 = {
  chartContainer,
  chartWrapper,
  emptyState,
  legend,
  legendItem,
  legendDot,
  skillsList,
  skillItem,
  skillHeader,
  skillName,
  skillValue,
  progressBar,
  progressFill,
  skillMeta
};
Chart.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  index,
  plugin_tooltip,
  plugin_legend
);
const LabProficiencyChart = ({ data }) => {
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No lab proficiency data available" }) });
  }
  const chartData = {
    labels: data.map((skill) => skill.skill_name),
    datasets: [
      {
        label: "Proficiency Level",
        data: data.map((skill) => skill.proficiency_level),
        backgroundColor: "rgba(156, 39, 176, 0.2)",
        borderColor: "#9c27b0",
        borderWidth: 2,
        pointBackgroundColor: data.map((skill) => {
          if (skill.proficiency_level >= 80) return "#4caf50";
          if (skill.proficiency_level >= 60) return "#ff9800";
          return "#f44336";
        }),
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8
      }
    ]
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
          callback: (value2) => `${value2}%`
        },
        grid: {
          color: "rgba(0, 0, 0, 0.1)"
        },
        pointLabels: {
          font: {
            size: 12
          }
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const skill = data[context.dataIndex];
            return [
              `Proficiency: ${context.parsed.r}%`,
              `Exercises: ${skill.exercises_completed}`
            ];
          }
        }
      }
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.chartContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.chartWrapper, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Radar, { data: chartData, options }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.legend, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.legendDot, style: { backgroundColor: "#4caf50" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Advanced (80+)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.legendDot, style: { backgroundColor: "#ff9800" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Intermediate (60-79)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.legendItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.legendDot, style: { backgroundColor: "#f44336" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Beginner (<60)" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.skillsList, children: data.map((skill, index2) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillItem, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.skillName, children: skill.skill_name }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.skillValue, children: [
          skill.proficiency_level,
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.progressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: styles$3.progressFill,
          style: {
            width: `${skill.proficiency_level}%`,
            backgroundColor: skill.proficiency_level >= 80 ? "#4caf50" : skill.proficiency_level >= 60 ? "#ff9800" : "#f44336"
          }
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.skillMeta, children: [
        skill.exercises_completed,
        " exercises completed"
      ] })
    ] }, index2)) })
  ] });
};
const riskCard = "_riskCard_1is32_7";
const header = "_header_1is32_15";
const headerLeft = "_headerLeft_1is32_24";
const title$1 = "_title_1is32_28";
const lastUpdated = "_lastUpdated_1is32_35";
const riskBadge = "_riskBadge_1is32_41";
const riskLevel = "_riskLevel_1is32_51";
const riskScore = "_riskScore_1is32_58";
const section = "_section_1is32_64";
const sectionTitle = "_sectionTitle_1is32_72";
const factorsList = "_factorsList_1is32_79";
const factorItem = "_factorItem_1is32_85";
const factorHeader = "_factorHeader_1is32_92";
const severityIcon = "_severityIcon_1is32_99";
const low = "_low_1is32_105";
const medium = "_medium_1is32_109";
const high = "_high_1is32_113";
const factorName = "_factorName_1is32_117";
const factorDescription = "_factorDescription_1is32_123";
const recommendationsList = "_recommendationsList_1is32_130";
const recommendationItem = "_recommendationItem_1is32_136";
const styles$2 = {
  riskCard,
  header,
  headerLeft,
  title: title$1,
  lastUpdated,
  riskBadge,
  riskLevel,
  riskScore,
  section,
  sectionTitle,
  factorsList,
  factorItem,
  factorHeader,
  severityIcon,
  low,
  medium,
  high,
  factorName,
  factorDescription,
  recommendationsList,
  recommendationItem
};
const RiskAssessmentCard = ({ riskData }) => {
  const getRiskLevelColor = () => {
    switch (riskData.risk_level) {
      case "low":
        return "#4caf50";
      case "medium":
        return "#ff9800";
      case "high":
        return "#f44336";
      case "critical":
        return "#d32f2f";
      default:
        return "#999";
    }
  };
  const getRiskLevelLabel = () => {
    return riskData.risk_level.charAt(0).toUpperCase() + riskData.risk_level.slice(1);
  };
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case "low":
        return "○";
      case "medium":
        return "◐";
      case "high":
        return "●";
      default:
        return "○";
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.riskCard, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.headerLeft, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$2.title, children: "Risk Assessment" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles$2.lastUpdated, children: [
          "Last updated: ",
          new Date(riskData.last_updated).toLocaleDateString()
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: styles$2.riskBadge,
          style: { backgroundColor: getRiskLevelColor() },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.riskLevel, children: getRiskLevelLabel() }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.riskScore, children: [
              riskData.risk_score,
              "/100"
            ] })
          ]
        }
      )
    ] }),
    riskData.factors && riskData.factors.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.sectionTitle, children: "Contributing Factors" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.factorsList, children: riskData.factors.map((factor, index2) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.factorItem, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.factorHeader, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "span",
            {
              className: `${styles$2.severityIcon} ${styles$2[factor.severity]}`,
              children: getSeverityIcon(factor.severity)
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.factorName, children: factor.factor })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.factorDescription, children: factor.description })
      ] }, index2)) })
    ] }),
    riskData.recommendations && riskData.recommendations.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.sectionTitle, children: "Recommended Actions" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: styles$2.recommendationsList, children: riskData.recommendations.map((recommendation, index2) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { className: styles$2.recommendationItem, children: recommendation }, index2)) })
    ] })
  ] });
};
const statCard = "_statCard_ykgui_7";
const iconContainer = "_iconContainer_ykgui_24";
const icon = "_icon_ykgui_24";
const content = "_content_ykgui_34";
const title = "_title_ykgui_39";
const value = "_value_ykgui_48";
const subtitle$1 = "_subtitle_ykgui_56";
const trend = "_trend_ykgui_62";
const up = "_up_ykgui_71";
const down = "_down_ykgui_75";
const trendIcon = "_trendIcon_ykgui_79";
const trendValue = "_trendValue_ykgui_84";
const trendLabel = "_trendLabel_ykgui_88";
const styles$1 = {
  statCard,
  iconContainer,
  icon,
  content,
  title,
  value,
  subtitle: subtitle$1,
  trend,
  up,
  down,
  trendIcon,
  trendValue,
  trendLabel
};
const StatCard = ({
  title: title2,
  value: value2,
  subtitle: subtitle2,
  trend: trend2,
  icon: icon2,
  color = "#4caf50"
}) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.statCard, style: { borderLeftColor: color }, children: [
    icon2 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.iconContainer, style: { color }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.icon, children: icon2 }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.content, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1.title, children: title2 }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.value, children: value2 }),
      subtitle2 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.subtitle, children: subtitle2 }),
      trend2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles$1.trend} ${styles$1[trend2.direction]}`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.trendIcon, children: trend2.direction === "up" ? "↑" : "↓" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.trendValue, children: [
          Math.abs(trend2.value),
          "%"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.trendLabel, children: "vs last period" })
      ] })
    ] })
  ] });
};
const dashboardContainer = "_dashboardContainer_1vx7p_7";
const dashboardHeader = "_dashboardHeader_1vx7p_15";
const subtitle = "_subtitle_1vx7p_31";
const timeRangeSelector = "_timeRangeSelector_1vx7p_38";
const timeRangeBtn = "_timeRangeBtn_1vx7p_46";
const active = "_active_1vx7p_63";
const metricsGrid = "_metricsGrid_1vx7p_69";
const chartsGrid = "_chartsGrid_1vx7p_77";
const chartCard = "_chartCard_1vx7p_84";
const courseAnalyticsSection = "_courseAnalyticsSection_1vx7p_99";
const courseStatsGrid = "_courseStatsGrid_1vx7p_114";
const courseStat = "_courseStat_1vx7p_114";
const courseStatLabel = "_courseStatLabel_1vx7p_130";
const courseStatValue = "_courseStatValue_1vx7p_138";
const loadingContainer = "_loadingContainer_1vx7p_145";
const spinner = "_spinner_1vx7p_154";
const errorContainer = "_errorContainer_1vx7p_179";
const styles = {
  dashboardContainer,
  dashboardHeader,
  subtitle,
  timeRangeSelector,
  timeRangeBtn,
  active,
  metricsGrid,
  chartsGrid,
  chartCard,
  courseAnalyticsSection,
  courseStatsGrid,
  courseStat,
  courseStatLabel,
  courseStatValue,
  loadingContainer,
  spinner,
  errorContainer
};
const AnalyticsDashboard = ({ viewType }) => {
  const { studentId, courseId } = useParams();
  const [timeRange, setTimeRange] = reactExports.useState("month");
  const {
    engagement,
    progress,
    quizPerformance,
    labProficiency,
    riskAssessment,
    courseAnalytics,
    isLoading,
    error
  } = useAnalytics(viewType, studentId, courseId, timeRange);
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loadingContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.spinner }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading analytics..." })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Error Loading Analytics" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.dashboardContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.dashboardHeader, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: "Analytics Dashboard" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.subtitle, children: [
          viewType === "student" && "Your Learning Progress",
          viewType === "course" && "Course Performance Overview",
          viewType === "instructor" && "Student Analytics"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.timeRangeSelector, children: ["week", "month", "quarter", "year"].map((range) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles.timeRangeBtn} ${timeRange === range ? styles.active : ""}`,
          onClick: () => setTimeRange(range),
          children: range.charAt(0).toUpperCase() + range.slice(1)
        },
        range
      )) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.metricsGrid, children: [
      engagement && /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Engagement Score",
          value: `${engagement.score}%`,
          trend: engagement.trend,
          icon: "📊",
          color: "#4caf50"
        }
      ),
      progress && /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Course Progress",
          value: `${progress.completion_percentage}%`,
          subtitle: `${progress.completed_items}/${progress.total_items} completed`,
          icon: "✅",
          color: "#2196f3"
        }
      ),
      quizPerformance && /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Quiz Average",
          value: `${quizPerformance.average_score}%`,
          subtitle: `${quizPerformance.quizzes_passed}/${quizPerformance.quizzes_taken} passed`,
          icon: "🎯",
          color: "#ff9800"
        }
      ),
      labProficiency && /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Lab Proficiency",
          value: `${labProficiency.proficiency_score}%`,
          subtitle: `${labProficiency.labs_completed} labs completed`,
          icon: "💻",
          color: "#9c27b0"
        }
      )
    ] }),
    viewType === "instructor" && riskAssessment && /* @__PURE__ */ jsxRuntimeExports.jsx(RiskAssessmentCard, { riskData: riskAssessment }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.chartsGrid, children: [
      engagement && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.chartCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Engagement Over Time" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(EngagementChart, { data: engagement.history })
      ] }),
      progress && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.chartCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Progress Timeline" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(ProgressChart, { data: progress.timeline })
      ] }),
      quizPerformance && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.chartCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Quiz Performance" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(QuizPerformanceChart, { data: quizPerformance.history })
      ] }),
      labProficiency && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.chartCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Lab Proficiency" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(LabProficiencyChart, { data: labProficiency.skills })
      ] })
    ] }),
    viewType === "course" && courseAnalytics && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseAnalyticsSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Course Analytics Summary" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseStatsGrid, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseStat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatLabel, children: "Total Students" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatValue, children: courseAnalytics.total_students })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseStat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatLabel, children: "Active Students" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatValue, children: courseAnalytics.active_students })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseStat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatLabel, children: "Completion Rate" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.courseStatValue, children: [
            courseAnalytics.completion_rate,
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.courseStat, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.courseStatLabel, children: "Average Grade" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.courseStatValue, children: [
            courseAnalytics.average_grade,
            "%"
          ] })
        ] })
      ] })
    ] })
  ] });
};
export {
  AnalyticsDashboard,
  AnalyticsDashboard as default
};
//# sourceMappingURL=AnalyticsDashboard-D8grcL1o.js.map
