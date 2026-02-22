import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useAuth, H as Heading, S as Spinner, C as Card, B as Button, a as SEO } from "./index-C0G9mbri.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { a as analyticsService } from "./analyticsService-DsWqh8bd.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "site-admin-dashboard": "_site-admin-dashboard_1ycxt_15",
  "welcome-section": "_welcome-section_1ycxt_25",
  "welcome-text": "_welcome-text_1ycxt_29",
  "stats-grid": "_stats-grid_1ycxt_40",
  "stat-card": "_stat-card_1ycxt_46",
  "stat-value": "_stat-value_1ycxt_51",
  "stat-label": "_stat-label_1ycxt_58",
  "content-grid": "_content-grid_1ycxt_70",
  "section-description": "_section-description_1ycxt_76",
  "action-buttons": "_action-buttons_1ycxt_83"
};
const SiteAdminDashboard = () => {
  const { user } = useAuth();
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "Site Admin Dashboard",
      description: "Platform-wide administration dashboard. Manage all organizations, monitor system health, view platform analytics, and configure global settings.",
      keywords: "site admin dashboard, platform administration, system management, platform analytics, global settings"
    }
  );
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["dashboardStats", "platform"],
    queryFn: () => analyticsService.getDashboardStats(),
    staleTime: 5 * 60 * 1e3,
    // Cache for 5 minutes
    retry: 2
  });
  const displayName = user?.firstName ? `${user.firstName} ${user.lastName || ""}` : user?.username || "Admin";
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["site-admin-dashboard"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["welcome-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Platform Administration" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) })
      ] }) })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      seoElement,
      /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["site-admin-dashboard"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Platform Administration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load dashboard data. Please try refreshing the page." }) })
      ] }) }) })
    ] });
  }
  const formatCurrency = (value) => {
    if (!value) return "$0";
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}k`;
    return `$${value}`;
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    seoElement,
    /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["site-admin-dashboard"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["welcome-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Platform Administration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["welcome-text"], children: [
          "Welcome, ",
          displayName,
          "! Manage the entire platform, organizations, users, and system configuration."
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stats-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: stats?.total_organizations || 0 }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Organizations" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: stats?.total_users?.toLocaleString() || "0" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Total Users" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-value"], children: formatCurrency(stats?.monthly_revenue) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "Monthly Revenue" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-card"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["stat-value"], children: [
            stats?.system_uptime ? Math.round(stats.system_uptime) : 0,
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["stat-label"], children: "System Uptime" })
        ] }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["content-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Organization Management" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "View, create, and manage all organizations on the platform" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["action-buttons"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/organizations", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Manage Organizations" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/organizations/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "Create Organization" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "User Management" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Manage all users across the platform and their permissions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/users", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Manage Users" }) }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Platform Analytics" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "View platform-wide metrics, usage statistics, and performance data" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/analytics", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "View Analytics" }) }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "System Configuration" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["section-description"], children: "Configure platform settings, features, and system-wide preferences" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/settings", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "System Settings" }) }) })
        ] })
      ] })
    ] }) })
  ] });
};
export {
  SiteAdminDashboard
};
//# sourceMappingURL=index-D93Maqfm.js.map
