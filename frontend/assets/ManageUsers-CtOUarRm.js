import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const mockUsers = [
  {
    id: "1",
    name: "Alice Johnson",
    email: "alice@example.com",
    role: "site_admin",
    organizationName: "Platform",
    status: "active",
    lastActive: "2025-11-05",
    createdDate: "2024-01-01"
  },
  {
    id: "2",
    name: "Bob Smith",
    email: "bob@acme.com",
    role: "org_admin",
    organizationName: "Acme Corporation",
    status: "active",
    lastActive: "2025-11-04",
    createdDate: "2024-01-15"
  },
  {
    id: "3",
    name: "Carol Davis",
    email: "carol@acme.com",
    role: "instructor",
    organizationName: "Acme Corporation",
    status: "active",
    lastActive: "2025-11-05",
    createdDate: "2024-02-10"
  },
  {
    id: "4",
    name: "David Wilson",
    email: "david@techstart.io",
    role: "instructor",
    organizationName: "TechStart Inc",
    status: "active",
    lastActive: "2025-11-03",
    createdDate: "2024-03-22"
  },
  {
    id: "5",
    name: "Eve Martinez",
    email: "eve@acme.com",
    role: "student",
    organizationName: "Acme Corporation",
    status: "active",
    lastActive: "2025-11-05",
    createdDate: "2024-04-15"
  },
  {
    id: "6",
    name: "Frank Brown",
    email: "frank@legacysystems.com",
    role: "instructor",
    organizationName: "Legacy Systems Ltd",
    status: "suspended",
    lastActive: "2025-09-20",
    createdDate: "2024-06-10"
  }
];
const ManageUsers = () => {
  const [users] = reactExports.useState(mockUsers);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [roleFilter, setRoleFilter] = reactExports.useState("all");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const filteredUsers = users.filter((user) => {
    const matchesSearch = user.name.toLowerCase().includes(searchQuery.toLowerCase()) || user.email.toLowerCase().includes(searchQuery.toLowerCase()) || user.organizationName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "all" || user.role === roleFilter;
    const matchesStatus = statusFilter === "all" || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });
  const handleStatusChange = (userId, newStatus) => {
    console.log("Updating user status:", { userId, newStatus });
    alert(`User status updated to ${newStatus}`);
  };
  const handleRoleChange = (userId, newRole) => {
    console.log("Updating user role:", { userId, newRole });
    alert(`User role updated to ${newRole}`);
  };
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };
  const getRoleColor = (role) => {
    switch (role) {
      case "site_admin":
        return "#8b5cf6";
      case "org_admin":
        return "#3b82f6";
      case "instructor":
        return "#10b981";
      case "student":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  };
  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "#10b981";
      case "suspended":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };
  const formatRoleName = (role) => {
    return role.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1600px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Manage Platform Users" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Platform-wide user administration and role management" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/site-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Users" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }, children: users.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Site Admins" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#8b5cf6" }, children: users.filter((u) => u.role === "site_admin").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Org Admins" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: users.filter((u) => u.role === "org_admin").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Instructors" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: users.filter((u) => u.role === "instructor").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: users.filter((u) => u.role === "student").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Active" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: users.filter((u) => u.status === "active").length })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "search",
          name: "search",
          type: "text",
          placeholder: "Search by name, email, or organization...",
          value: searchQuery,
          onChange: (e) => setSearchQuery(e.target.value)
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "select",
        {
          value: roleFilter,
          onChange: (e) => setRoleFilter(e.target.value),
          style: {
            width: "100%",
            padding: "0.75rem",
            fontSize: "0.875rem",
            border: "1px solid #d1d5db",
            borderRadius: "0.375rem",
            backgroundColor: "white"
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Roles" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "site_admin", children: "Site Admin" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "org_admin", children: "Org Admin" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "instructor", children: "Instructor" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "student", children: "Student" })
          ]
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
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "suspended", children: "Suspended" })
          ]
        }
      ) })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "none", children: filteredUsers.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { padding: "3rem", textAlign: "center" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", color: "#666", marginBottom: "1rem" }, children: searchQuery || roleFilter !== "all" || statusFilter !== "all" ? "No users match your filters" : "No users found" }) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { overflowX: "auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { style: { width: "100%", borderCollapse: "collapse" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "User" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Role" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Last Active" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Created" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Actions" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: filteredUsers.map((user) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "1px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 500, marginBottom: "0.25rem" }, children: user.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#6b7280" }, children: user.email })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          backgroundColor: `${getRoleColor(user.role)}20`,
          color: getRoleColor(user.role)
        }, children: formatRoleName(user.role) }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem" }, children: user.organizationName }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          textTransform: "capitalize",
          backgroundColor: `${getStatusColor(user.status)}20`,
          color: getStatusColor(user.status)
        }, children: user.status }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: user.lastActive ? formatDate(user.lastActive) : "Never" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: formatDate(user.createdDate) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/admin/users/${user.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "small", children: "View" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              value: user.role,
              onChange: (e) => handleRoleChange(user.id, e.target.value),
              style: {
                padding: "0.375rem 0.5rem",
                fontSize: "0.875rem",
                borderRadius: "0.375rem",
                border: "1px solid #d1d5db",
                backgroundColor: "white",
                cursor: "pointer"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "site_admin", children: "Site Admin" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "org_admin", children: "Org Admin" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "instructor", children: "Instructor" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "student", children: "Student" })
              ]
            }
          ),
          user.status === "active" ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "danger",
              size: "small",
              onClick: () => handleStatusChange(user.id, "suspended"),
              children: "Suspend"
            }
          ) : /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              size: "small",
              onClick: () => handleStatusChange(user.id, "active"),
              children: "Activate"
            }
          )
        ] }) })
      ] }, user.id)) })
    ] }) }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginTop: "1.5rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "0.75rem", color: "#0c4a6e" }, children: "💡 User Management Tips" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e", lineHeight: "1.6" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Site admins have full platform access and should be limited to trusted personnel" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Org admins can only manage users within their own organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Suspending a user immediately revokes all access but preserves their data" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Changing roles may require the user to log out and back in" })
      ] })
    ] })
  ] }) });
};
export {
  ManageUsers
};
//# sourceMappingURL=ManageUsers-CtOUarRm.js.map
