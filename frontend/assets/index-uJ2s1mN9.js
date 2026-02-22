import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useAuth, H as Heading, S as Spinner, C as Card, B as Button, a as SEO } from "./index-C0G9mbri.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { a as analyticsService } from "./analyticsService-DsWqh8bd.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "instructor-dashboard": "_instructor-dashboard_c8tyk_15",
  "welcome-section": "_welcome-section_c8tyk_25",
  "welcome-text": "_welcome-text_c8tyk_29",
  "stats-grid": "_stats-grid_c8tyk_40",
  "stat-card": "_stat-card_c8tyk_46",
  "stat-value": "_stat-value_c8tyk_51",
  "stat-label": "_stat-label_c8tyk_58",
  "content-grid": "_content-grid_c8tyk_70",
  "section-description": "_section-description_c8tyk_76",
  "action-buttons": "_action-buttons_c8tyk_83"
};
const InstructorDashboard = () => {
  const { user } = useAuth();
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "Instructor Dashboard",
      description: "Manage your courses, create AI-powered content, track student progress, and view teaching analytics on the Course Creator Platform.",
      keywords: "instructor dashboard, course management, student analytics, content creation, teaching tools"
    }
  );
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ["instructorAnalytics", "me"],
    queryFn: () => analyticsService.getMyInstructorAnalytics(),
    staleTime: 5 * 60 * 1e3,
    // Cache for 5 minutes
    retry: 2
  });
  const displayName = user?.firstName ? `${user.firstName} ${user.lastName || ""}` : user?.username || "Instructor";
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["instructor-dashboard"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["welcome-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Corporate Trainer Dashboard" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) })
      ] }) })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["instructor-dashboard"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Corporate Trainer Dashboard" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load dashboard data. Please try refreshing the page." }) })
    ] }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    seoElement,
    /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["instructor-dashboard"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Corporate Trainer Dashboard" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["welcome-text"], children: [
          "Welcome back, ",
          displayName,
          "! Manage your IT training programs, enroll students, and create AI-focused course content."
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stats-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.total_programs || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Training Programs" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.total_students || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Enrolled Students" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-value"], children: [
            analytics?.average_completion_rate ? Math.round(analytics.average_completion_rate) : 0,
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Avg Completion Rate" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.average_course_rating?.toFixed(1) || "0.0" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Course Rating" })
        ] }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["content-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "IT Training Programs" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Manage your AI/IT training programs, update content, and track student engagement" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/programs", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Manage Programs" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/programs/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Create New Program" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Student Enrollment" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Enroll students, track progress, and manage training cohorts" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/students", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Manage Students" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/students/enroll", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Enroll Students" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Training Analytics" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Track training effectiveness, completion rates, and certification metrics" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/analytics", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Reports" }) }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "AI Content Generator" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Generate quizzes, labs, slides, and training materials with AI assistance" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/content-generator", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "generate", children: "Generate Content" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/content-generator?type=quiz", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "create-quiz", children: "Create Quiz" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/content-generator?type=slides", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "create-slides", children: "Create Slides" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Course & Lab Creation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Create new courses with labs, quizzes, and interactive content" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/courses/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "create-course", children: "Create Course" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/labs/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "create-lab", children: "Create Lab" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/students/bulk-enroll", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "bulk-enroll", children: "Bulk Enroll" }) })
          ] })
        ] })
      ] })
    ] }) })
  ] });
};
export {
  InstructorDashboard
};
//# sourceMappingURL=index-uJ2s1mN9.js.map
