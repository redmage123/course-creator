import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const mockOrganizations = [
  {
    id: "1",
    name: "Acme Corporation",
    contactEmail: "admin@acme.com",
    subscriptionPlan: "Enterprise",
    status: "active",
    trainersCount: 15,
    studentsCount: 450,
    coursesCount: 38,
    createdDate: "2024-01-15",
    subscriptionExpiresAt: "2025-01-14"
  },
  {
    id: "2",
    name: "TechStart Inc",
    contactEmail: "admin@techstart.io",
    subscriptionPlan: "Professional",
    status: "active",
    trainersCount: 8,
    studentsCount: 120,
    coursesCount: 15,
    createdDate: "2024-03-22",
    subscriptionExpiresAt: "2025-03-21"
  },
  {
    id: "3",
    name: "Global Training Solutions",
    contactEmail: "contact@globaltraining.com",
    subscriptionPlan: "Trial",
    status: "trial",
    trainersCount: 3,
    studentsCount: 25,
    coursesCount: 5,
    createdDate: "2025-10-01",
    subscriptionExpiresAt: "2025-11-01"
  },
  {
    id: "4",
    name: "Legacy Systems Ltd",
    contactEmail: "admin@legacysystems.com",
    subscriptionPlan: "Professional",
    status: "suspended",
    trainersCount: 5,
    studentsCount: 89,
    coursesCount: 12,
    createdDate: "2024-06-10",
    subscriptionExpiresAt: "2024-10-10"
  }
];
const ManageOrganizations = () => {
  const [organizations] = reactExports.useState(mockOrganizations);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const filteredOrganizations = organizations.filter((org) => {
    const matchesSearch = org.name.toLowerCase().includes(searchQuery.toLowerCase()) || org.contactEmail.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || org.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  const handleStatusChange = (orgId, newStatus) => {
    console.log("Updating organization status:", { orgId, newStatus });
    alert(`Organization status updated to ${newStatus}`);
  };
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };
  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "#10b981";
      case "suspended":
        return "#ef4444";
      case "trial":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  };
  const getPlanColor = (plan) => {
    switch (plan.toLowerCase()) {
      case "enterprise":
        return "#8b5cf6";
      case "professional":
        return "#3b82f6";
      case "trial":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1600px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Manage Organizations" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Platform-wide organization administration and oversight" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/organizations/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "+ Create Organization" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/site-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Organizations" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }, children: organizations.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Active" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: organizations.filter((o) => o.status === "active").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Trainers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: organizations.reduce((sum, o) => sum + o.trainersCount, 0) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: organizations.reduce((sum, o) => sum + o.studentsCount, 0) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Courses" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#8b5cf6" }, children: organizations.reduce((sum, o) => sum + o.coursesCount, 0) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "search",
          name: "search",
          type: "text",
          placeholder: "Search by organization name or email...",
          value: searchQuery,
          onChange: (e) => setSearchQuery(e.target.value)
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "select",
        {
          value: statusFilter,
          onChange: (e) => setStatusFilter(e.target.value),
          style: {
            width: "100%",
            padding: "0.75rem",
            fontSize: "0.875rem",
            border: "1px solid #d1d5db",
            borderRadius: "0.375rem",
            backgroundColor: "white"
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Statuses" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "active", children: "Active" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "trial", children: "Trial" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "suspended", children: "Suspended" })
          ]
        }
      ) })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "none", children: filteredOrganizations.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "3rem", textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", color: "#666", marginBottom: "1rem" }, children: searchQuery || statusFilter !== "all" ? "No organizations match your filters" : "No organizations yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/organizations/create", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Create First Organization" }) })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { overflowX: "auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { style: { width: "100%", borderCollapse: "collapse" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Plan" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Trainers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Courses" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Created" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Expires" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Actions" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: filteredOrganizations.map((org) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "1px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 500, marginBottom: "0.25rem" }, children: org.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#6b7280" }, children: org.contactEmail })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          backgroundColor: `${getPlanColor(org.subscriptionPlan)}20`,
          color: getPlanColor(org.subscriptionPlan)
        }, children: org.subscriptionPlan }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          textTransform: "capitalize",
          backgroundColor: `${getStatusColor(org.status)}20`,
          color: getStatusColor(org.status)
        }, children: org.status }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", textAlign: "center" }, children: org.trainersCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", textAlign: "center" }, children: org.studentsCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", textAlign: "center" }, children: org.coursesCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: formatDate(org.createdDate) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: org.subscriptionExpiresAt ? formatDate(org.subscriptionExpiresAt) : "N/A" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/admin/organizations/${org.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "small", children: "View" }) }),
          org.status === "active" ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "danger",
              size: "small",
              onClick: () => handleStatusChange(org.id, "suspended"),
              children: "Suspend"
            }
          ) : org.status === "suspended" ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              size: "small",
              onClick: () => handleStatusChange(org.id, "active"),
              children: "Activate"
            }
          ) : null
        ] }) })
      ] }, org.id)) })
    ] }) }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginTop: "1.5rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "0.75rem", color: "#0c4a6e" }, children: "💡 Platform Administration Tips" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e", lineHeight: "1.6" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Monitor organization usage to identify growth opportunities" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Suspend organizations for non-payment or policy violations" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Trial accounts automatically expire after 30 days unless upgraded" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Contact organizations proactively when approaching subscription renewal" })
      ] })
    ] })
  ] }) });
};
export {
  ManageOrganizations
};
//# sourceMappingURL=ManageOrganizations-BSQpvcFo.js.map
