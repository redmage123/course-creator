import { j as jsxRuntimeExports, u as useQuery } from "./query-vendor-BigVEegc.js";
import { C as Card, u as useAuth, H as Heading, S as Spinner, B as Button, a as SEO } from "./index-C0G9mbri.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { a as analyticsService } from "./analyticsService-DsWqh8bd.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const styles$1 = {
  "stat-card": "_stat-card_kiab8_19",
  "stat-content": "_stat-content_kiab8_28",
  "stat-icon": "_stat-icon_kiab8_41",
  "stat-value": "_stat-value_kiab8_71",
  "stat-label": "_stat-label_kiab8_91",
  "trend-indicator": "_trend-indicator_kiab8_104",
  "trend-up": "_trend-up_kiab8_125",
  "trend-down": "_trend-down_kiab8_131",
  "trend-neutral": "_trend-neutral_kiab8_137",
  "trend-icon": "_trend-icon_kiab8_146",
  "trend-value": "_trend-value_kiab8_159",
  "trend-label": "_trend-label_kiab8_168"
};
const formatValue = (value, format, currencySymbol) => {
  if (typeof value === "string") return value;
  switch (format) {
    case "percentage":
      return `${value}%`;
    case "currency":
      return `${currencySymbol}${value.toLocaleString()}`;
    case "duration":
      const hours = Math.floor(value / 60);
      const minutes = value % 60;
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    case "number":
    default:
      return value.toLocaleString();
  }
};
const getTrendDirection = (trend) => {
  if (trend > 0) return "up";
  if (trend < 0) return "down";
  return "neutral";
};
const TrendUpIcon = () => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "svg",
  {
    width: "16",
    height: "16",
    viewBox: "0 0 16 16",
    fill: "none",
    "aria-hidden": "true",
    className: styles$1["trend-icon"],
    children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "path",
      {
        d: "M8 4L12 8L10.6 9.4L9 7.8V12H7V7.8L5.4 9.4L4 8L8 4Z",
        fill: "currentColor"
      }
    )
  }
);
const TrendDownIcon = () => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "svg",
  {
    width: "16",
    height: "16",
    viewBox: "0 0 16 16",
    fill: "none",
    "aria-hidden": "true",
    className: styles$1["trend-icon"],
    children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "path",
      {
        d: "M8 12L4 8L5.4 6.6L7 8.2V4H9V8.2L10.6 6.6L12 8L8 12Z",
        fill: "currentColor"
      }
    )
  }
);
const StatCard = ({
  value,
  label,
  trend,
  trendDirection,
  trendLabel = "vs last period",
  valueFormat = "number",
  currencySymbol = "$",
  icon,
  variant = "elevated",
  className,
  ariaDescription
}) => {
  const formattedValue = formatValue(value, valueFormat, currencySymbol);
  const direction = trendDirection ?? (trend !== void 0 ? getTrendDirection(trend) : "neutral");
  const hasTrend = trend !== void 0;
  const accessibleDescription = ariaDescription ?? (() => {
    let desc = `${label}: ${formattedValue}`;
    if (hasTrend) {
      const trendText = trend > 0 ? `up ${Math.abs(trend)}%` : trend < 0 ? `down ${Math.abs(trend)}%` : "unchanged";
      desc += `, ${trendText} ${trendLabel}`;
    }
    return desc;
  })();
  const classes = [styles$1["stat-card"], className].filter(Boolean).join(" ");
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Card,
    {
      variant,
      padding: "medium",
      className: classes,
      "data-testid": "stat-card",
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: styles$1["stat-content"],
          role: "group",
          "aria-label": accessibleDescription,
          children: [
            icon && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["stat-icon"], "aria-hidden": "true", children: icon }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["stat-value"], children: formattedValue }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["stat-label"], children: label }),
            hasTrend && /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                className: `${styles$1["trend-indicator"]} ${styles$1[`trend-${direction}`]}`,
                "aria-label": `Trend: ${Math.abs(trend)}% ${direction} ${trendLabel}`,
                children: [
                  direction === "up" && /* @__PURE__ */ jsxRuntimeExports.jsx(TrendUpIcon, {}),
                  direction === "down" && /* @__PURE__ */ jsxRuntimeExports.jsx(TrendDownIcon, {}),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1["trend-value"], children: [
                    direction !== "neutral" && (direction === "up" ? "+" : ""),
                    trend.toFixed(1),
                    "%"
                  ] }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["trend-label"], children: trendLabel })
                ]
              }
            )
          ]
        }
      )
    }
  );
};
StatCard.displayName = "StatCard";
const styles = {
  "student-dashboard": "_student-dashboard_12tpv_15",
  "welcome-section": "_welcome-section_12tpv_25",
  "welcome-text": "_welcome-text_12tpv_29",
  "stats-grid": "_stats-grid_12tpv_40",
  "content-grid": "_content-grid_12tpv_70",
  "section-description": "_section-description_12tpv_76",
  "action-buttons": "_action-buttons_12tpv_83"
};
const StudentDashboard = () => {
  const { user } = useAuth();
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "Student Dashboard",
      description: "Access your assigned courses, track learning progress, view analytics, and manage your course work on the Course Creator Platform.",
      keywords: "student dashboard, my courses, learning progress, course analytics, student portal"
    }
  );
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ["studentAnalytics", "me"],
    queryFn: () => analyticsService.getMyAnalytics(),
    staleTime: 5 * 60 * 1e3,
    // Cache for 5 minutes
    retry: 2
  });
  const getGreeting = () => {
    const hour = (/* @__PURE__ */ new Date()).getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };
  const displayName = user?.firstName ? `${user.firstName} ${user.lastName || ""}` : user?.username || "Student";
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["student-dashboard"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["welcome-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Heading, { level: "h1", gutterBottom: true, children: [
          getGreeting(),
          ", ",
          displayName,
          "!"
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) })
      ] }) })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["student-dashboard"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Heading, { level: "h1", gutterBottom: true, children: [
        getGreeting(),
        ", ",
        displayName,
        "!"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load dashboard data. Please try refreshing the page." }) })
    ] }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    seoElement,
    /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["student-dashboard"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Heading, { level: "h1", gutterBottom: true, children: [
          getGreeting(),
          ", ",
          displayName,
          "!"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["welcome-text"], children: "Welcome to your corporate training dashboard. View your assigned courses, track your progress, and access lab environments." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stats-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          StatCard,
          {
            value: analytics?.active_courses || 0,
            label: "Assigned Courses",
            trend: analytics?.courses_trend,
            trendLabel: "vs last month"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          StatCard,
          {
            value: analytics?.average_progress ? Math.round(analytics.average_progress) : 0,
            label: "Average Progress",
            valueFormat: "percentage",
            trend: analytics?.progress_trend,
            trendLabel: "vs last week"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          StatCard,
          {
            value: analytics?.total_labs_completed || 0,
            label: "Labs Completed",
            trend: analytics?.labs_trend,
            trendLabel: "vs last month"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          StatCard,
          {
            value: analytics?.certificates_earned || 0,
            label: "Certificates Earned",
            trend: analytics?.certificates_trend,
            trendLabel: "this quarter"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["content-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Assigned Training Courses" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Continue your corporate training from where you left off" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/courses/my-courses", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Assigned Courses" }) }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Active Labs" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Practice your skills in hands-on lab environments with Monaco, Jupyter, or VS Code" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/labs", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "launch-lab", children: "Launch Labs" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/labs?ide=vscode", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-ide": "vscode", children: "VS Code" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/labs?ide=jupyter", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-ide": "jupyter", children: "Jupyter" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Quizzes & Assessments" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Complete quizzes to test your knowledge and track progress" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/quizzes", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "take-quiz", children: "Take Quiz" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/quizzes/history", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "View History" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Progress & Achievements" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Track your learning journey and earned certificates" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/progress", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Progress" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/certificates", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "My Certificates" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Learning Resources" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Access course materials, videos, and documentation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/resources", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Browse Resources" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/resources/download", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "download", children: "Download Materials" }) })
          ] })
        ] })
      ] })
    ] }) })
  ] });
};
export {
  StudentDashboard
};
//# sourceMappingURL=index-D_7OAKuV.js.map
