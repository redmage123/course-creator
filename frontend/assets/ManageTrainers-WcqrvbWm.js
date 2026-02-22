import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, B as Button, C as Card, M as Modal } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const mockTrainers = [
  {
    id: "1",
    name: "John Smith",
    email: "john.smith@company.com",
    status: "active",
    coursesCount: 12,
    studentsCount: 145,
    joinedDate: "2024-01-15",
    lastActive: "2025-11-04"
  },
  {
    id: "2",
    name: "Sarah Johnson",
    email: "sarah.johnson@company.com",
    status: "active",
    coursesCount: 8,
    studentsCount: 98,
    joinedDate: "2024-03-22",
    lastActive: "2025-11-05"
  },
  {
    id: "3",
    name: "Michael Chen",
    email: "michael.chen@company.com",
    status: "inactive",
    coursesCount: 5,
    studentsCount: 34,
    joinedDate: "2024-06-10",
    lastActive: "2025-10-20"
  }
];
const ManageTrainers = () => {
  const user = useAppSelector((state) => state.user.profile);
  const [trainers] = reactExports.useState(mockTrainers);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const [isInviteModalOpen, setIsInviteModalOpen] = reactExports.useState(false);
  const [inviteEmail, setInviteEmail] = reactExports.useState("");
  const [inviteName, setInviteName] = reactExports.useState("");
  const filteredTrainers = trainers.filter((trainer) => {
    const matchesSearch = trainer.name.toLowerCase().includes(searchQuery.toLowerCase()) || trainer.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || trainer.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  const handleInvite = (e) => {
    e.preventDefault();
    console.log("Inviting trainer:", { inviteName, inviteEmail });
    alert(`Invitation sent to ${inviteEmail}!`);
    setInviteEmail("");
    setInviteName("");
    setIsInviteModalOpen(false);
  };
  const handleStatusChange = (trainerId, newStatus) => {
    console.log("Updating trainer status:", { trainerId, newStatus });
    alert(`Trainer status updated to ${newStatus}`);
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
      case "inactive":
        return "#6b7280";
      case "pending":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1400px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Manage Trainers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { color: "#666", fontSize: "0.95rem" }, children: [
          "Manage instructor accounts and permissions for ",
          user?.organizationId || "your organization"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => setIsInviteModalOpen(true), children: "+ Invite Trainer" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/org-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Trainers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }, children: trainers.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Active" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: trainers.filter((t) => t.status === "active").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Courses" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: trainers.reduce((sum, t) => sum + t.coursesCount, 0) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: trainers.reduce((sum, t) => sum + t.studentsCount, 0) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "search",
          name: "search",
          type: "text",
          placeholder: "Search by name or email...",
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
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "inactive", children: "Inactive" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "pending", children: "Pending" })
          ]
        }
      ) })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "none", children: filteredTrainers.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "3rem", textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", color: "#666", marginBottom: "1rem" }, children: searchQuery || statusFilter !== "all" ? "No trainers match your filters" : "No trainers yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => setIsInviteModalOpen(true), children: "Invite Your First Trainer" })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { overflowX: "auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { style: { width: "100%", borderCollapse: "collapse" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Trainer" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Courses" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Joined" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Last Active" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Actions" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: filteredTrainers.map((trainer) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "1px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 500, marginBottom: "0.25rem" }, children: trainer.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#6b7280" }, children: trainer.email })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          textTransform: "capitalize",
          backgroundColor: `${getStatusColor(trainer.status)}20`,
          color: getStatusColor(trainer.status)
        }, children: trainer.status }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem" }, children: trainer.coursesCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem" }, children: trainer.studentsCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: formatDate(trainer.joinedDate) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: trainer.lastActive ? formatDate(trainer.lastActive) : "Never" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/organization/trainers/${trainer.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "small", children: "View" }) }),
          trainer.status === "active" ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "secondary",
              size: "small",
              onClick: () => handleStatusChange(trainer.id, "inactive"),
              children: "Deactivate"
            }
          ) : /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              size: "small",
              onClick: () => handleStatusChange(trainer.id, "active"),
              children: "Activate"
            }
          )
        ] }) })
      ] }, trainer.id)) })
    ] }) }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginTop: "1.5rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "0.75rem", color: "#0c4a6e" }, children: "💡 Trainer Management Tips" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e", lineHeight: "1.6" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Trainers can create and manage training programs for your organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Each trainer has full control over their courses and enrolled students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Deactivating a trainer preserves their courses but prevents new content creation" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Invited trainers receive an email with instructions to set up their account" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      Modal,
      {
        isOpen: isInviteModalOpen,
        onClose: () => setIsInviteModalOpen(false),
        title: "Invite Trainer",
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleInvite, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "inviteName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Full Name *" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "inviteName",
                name: "inviteName",
                type: "text",
                placeholder: "John Smith",
                value: inviteName,
                onChange: (e) => setInviteName(e.target.value),
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "inviteEmail", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Email Address *" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "inviteEmail",
                name: "inviteEmail",
                type: "email",
                placeholder: "john.smith@company.com",
                value: inviteEmail,
                onChange: (e) => setInviteEmail(e.target.value),
                required: true
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "An invitation email will be sent with setup instructions." })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem", justifyContent: "flex-end", paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Button,
              {
                type: "button",
                variant: "secondary",
                onClick: () => setIsInviteModalOpen(false),
                children: "Cancel"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { type: "submit", variant: "primary", children: "Send Invitation" })
          ] })
        ] })
      }
    )
  ] }) });
};
export {
  ManageTrainers
};
//# sourceMappingURL=ManageTrainers-WcqrvbWm.js.map
