import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useAuth, H as Heading, S as Spinner, C as Card, B as Button, a as SEO } from "./index-C0G9mbri.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { a as analyticsService } from "./analyticsService-DsWqh8bd.js";
import { o as organizationService } from "./organizationService-DsJ0Nzue.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "org-admin-dashboard": "_org-admin-dashboard_14jyd_15",
  "org-header": "_org-header_14jyd_25",
  "org-title-row": "_org-title-row_14jyd_31",
  "org-title": "_org-title_14jyd_31",
  "org-subtitle": "_org-subtitle_14jyd_51",
  "welcome-section": "_welcome-section_14jyd_62",
  "welcome-text": "_welcome-text_14jyd_66",
  "stats-grid": "_stats-grid_14jyd_77",
  "stat-card": "_stat-card_14jyd_83",
  "stat-value": "_stat-value_14jyd_88",
  "stat-label": "_stat-label_14jyd_95",
  "content-grid": "_content-grid_14jyd_107",
  "section-description": "_section-description_14jyd_113",
  "action-buttons": "_action-buttons_14jyd_120"
};
const OrgAdminDashboard = () => {
  const { user } = useAuth();
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "Organization Admin Dashboard",
      description: "Manage your organization's training programs, instructors, students, and view organization-wide analytics on the Course Creator Platform.",
      keywords: "org admin dashboard, organization management, training programs, instructor management, corporate training"
    }
  );
  const { data: organization, isLoading: orgLoading, error: orgError } = useQuery({
    queryKey: ["organization", "me"],
    queryFn: () => organizationService.getMyOrganization(),
    staleTime: 10 * 60 * 1e3,
    // Cache for 10 minutes
    retry: 2
  });
  const { data: analytics, isLoading: analyticsLoading, error: analyticsError } = useQuery({
    queryKey: ["organizationAnalytics", organization?.id],
    queryFn: () => analyticsService.getOrganizationAnalytics(organization.id),
    enabled: !!organization?.id,
    // Only run if organization ID is available
    staleTime: 5 * 60 * 1e3,
    // Cache for 5 minutes
    retry: 2
  });
  const displayName = user?.firstName ? `${user.firstName} ${user.lastName || ""}` : user?.username || "Admin";
  const orgName = organization?.name || user?.organizationName || "Your Organization";
  const isLoading = orgLoading || analyticsLoading;
  const error = orgError || analyticsError;
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["org-admin-dashboard"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["welcome-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Organization Administration" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) })
      ] }) })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["org-admin-dashboard"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Organization Administration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load dashboard data. Please try refreshing the page." }) })
      ] }) }) })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    seoElement,
    /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["org-admin-dashboard"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["org-header"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["org-title-row"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-building", "aria-hidden": "true" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles["org-title"], children: orgName })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["org-subtitle"], children: "Organization Administration Dashboard" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["welcome-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["welcome-text"], children: [
        "Welcome, ",
        displayName,
        "! Manage your corporate trainers, enroll students in IT training programs, and track organizational learning metrics."
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stats-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.total_students || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Enrolled Students" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.total_training_programs || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Training Programs" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: analytics?.total_trainers || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Corporate Trainers" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-value"], children: [
            analytics?.engagement_rate ? Math.round(analytics.engagement_rate) : 0,
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Engagement Rate" })
        ] }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["content-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Trainer & Student Management" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Manage corporate trainers, organization members, enroll students in bulk, and organize learning tracks" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/members", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Manage Members" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/trainers", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Manage Trainers" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/students/enroll", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Bulk Enroll Students" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Training Programs" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Manage IT training courses, learning tracks, assign programs to students, and track completions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/programs", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Programs" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/tracks", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Manage Tracks" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/programs/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Create New Program" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Import & AI Automation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Import organization templates and let AI automatically create projects and tracks" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/import", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "import", children: "Import Template" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/ai-create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "ai-create-project", children: "AI Auto Create Project" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/templates/download", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", "data-action": "download-template", children: "Download Template" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Training Analytics & Compliance" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Track training completion rates, certifications, and compliance metrics" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/analytics", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Reports" }) }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Organization Settings" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Configure branding, billing, and organizational preferences" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/organization/settings", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Manage Settings" }) }) })
        ] })
      ] })
    ] }) })
  ] });
};
export {
  OrgAdminDashboard
};
//# sourceMappingURL=index-Di7RGUjS.js.map
