import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { S as Spinner, H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { S as Select } from "./Select-D3EGugkq.js";
import { e as enrollmentService } from "./enrollmentService-CJs1-f8S.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const ManageStudents = () => {
  const user = useAppSelector((state) => state.user.profile);
  const [enrollments, setEnrollments] = reactExports.useState([]);
  const [filteredEnrollments, setFilteredEnrollments] = reactExports.useState([]);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const [sortBy, setSortBy] = reactExports.useState("name");
  reactExports.useEffect(() => {
    const loadEnrollments = async () => {
      if (!user?.id) return;
      try {
        setIsLoading(true);
        setError(null);
        const summary = await enrollmentService.getInstructorEnrollmentSummary(user.id);
        const enrollmentData = [];
        for (const studentSummary of summary) {
          const studentEnrollments = await enrollmentService.getStudentEnrollments(studentSummary.student_id);
          enrollmentData.push(...studentEnrollments);
        }
        setEnrollments(enrollmentData);
        setFilteredEnrollments(enrollmentData);
      } catch (err) {
        console.error("Failed to load enrollments:", err);
        setError("Failed to load student enrollments. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };
    loadEnrollments();
  }, [user?.id]);
  reactExports.useEffect(() => {
    let filtered = [...enrollments];
    if (statusFilter !== "all") {
      filtered = filtered.filter((e) => e.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (e) => e.student_name?.toLowerCase().includes(query) || e.student_email?.toLowerCase().includes(query) || e.course_title?.toLowerCase().includes(query)
      );
    }
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "name":
          return (a.student_name || "").localeCompare(b.student_name || "");
        case "progress":
          return b.progress_percentage - a.progress_percentage;
        case "date":
          return new Date(b.enrollment_date).getTime() - new Date(a.enrollment_date).getTime();
        default:
          return 0;
      }
    });
    setFilteredEnrollments(filtered);
  }, [enrollments, searchQuery, statusFilter, sortBy]);
  const handleStatusUpdate = async (enrollmentId, newStatus) => {
    try {
      await enrollmentService.updateEnrollmentStatus(enrollmentId, newStatus);
      setEnrollments(
        (prev) => prev.map((e) => e.id === enrollmentId ? { ...e, status: newStatus } : e)
      );
    } catch (err) {
      console.error("Failed to update enrollment status:", err);
      alert("Failed to update enrollment status. Please try again.");
    }
  };
  const handleUnenroll = async (enrollmentId, studentName) => {
    if (!confirm(`Are you sure you want to unenroll ${studentName}?`)) {
      return;
    }
    try {
      await enrollmentService.unenrollStudent(enrollmentId);
      setEnrollments((prev) => prev.filter((e) => e.id !== enrollmentId));
    } catch (err) {
      console.error("Failed to unenroll student:", err);
      alert("Failed to unenroll student. Please try again.");
    }
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
      case "completed":
        return "#3b82f6";
      case "dropped":
        return "#ef4444";
      case "pending":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "400px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1400px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Manage Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "View and manage student enrollments across all your training programs" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/students/enroll", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Enroll Students" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/instructor", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
      ] })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem", borderColor: "#ef4444", backgroundColor: "#fee2e2" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", margin: 0 }, children: error }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "search",
          name: "search",
          type: "text",
          placeholder: "Search by name, email, or course...",
          value: searchQuery,
          onChange: (e) => setSearchQuery(e.target.value)
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Select,
        {
          id: "status",
          name: "status",
          value: statusFilter,
          onChange: (value) => setStatusFilter(value),
          options: [
            { value: "all", label: "All Statuses" },
            { value: "active", label: "Active" },
            { value: "completed", label: "Completed" },
            { value: "pending", label: "Pending" },
            { value: "dropped", label: "Dropped" }
          ]
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Select,
        {
          id: "sort",
          name: "sort",
          value: sortBy,
          onChange: (value) => setSortBy(value),
          options: [
            { value: "name", label: "Sort by Name" },
            { value: "progress", label: "Sort by Progress" },
            { value: "date", label: "Sort by Date" }
          ]
        }
      ) })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Enrollments" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }, children: enrollments.length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Active Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: enrollments.filter((e) => e.status === "active").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Completed" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: enrollments.filter((e) => e.status === "completed").length })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Average Progress" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: [
          enrollments.length > 0 ? Math.round(enrollments.reduce((sum, e) => sum + e.progress_percentage, 0) / enrollments.length) : 0,
          "%"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "none", children: filteredEnrollments.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "3rem", textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", color: "#666", marginBottom: "1rem" }, children: searchQuery || statusFilter !== "all" ? "No enrollments match your filters" : "No student enrollments yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/instructor/students/enroll", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Enroll Your First Students" }) })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { overflowX: "auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { style: { width: "100%", borderCollapse: "collapse" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Student" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Course" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Progress" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Enrolled" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "1rem", textAlign: "left", fontWeight: 600, fontSize: "0.875rem" }, children: "Actions" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: filteredEnrollments.map((enrollment) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "1px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 500, marginBottom: "0.25rem" }, children: enrollment.student_name || "Unknown Student" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#6b7280" }, children: enrollment.student_email })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/courses/${enrollment.course_id}`, style: { color: "#3b82f6", textDecoration: "none" }, children: enrollment.course_title || "Unknown Course" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "0.5rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
            flex: 1,
            height: "8px",
            backgroundColor: "#e5e7eb",
            borderRadius: "4px",
            overflow: "hidden"
          }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
            height: "100%",
            width: `${enrollment.progress_percentage}%`,
            backgroundColor: "#3b82f6",
            transition: "width 0.3s ease"
          } }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { fontSize: "0.875rem", fontWeight: 500 }, children: [
            enrollment.progress_percentage,
            "%"
          ] })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
          display: "inline-block",
          padding: "0.25rem 0.75rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          textTransform: "capitalize",
          backgroundColor: `${getStatusColor(enrollment.status)}20`,
          color: getStatusColor(enrollment.status)
        }, children: enrollment.status }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem", fontSize: "0.875rem", color: "#6b7280" }, children: formatDate(enrollment.enrollment_date) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/instructor/students/${enrollment.student_id}/analytics`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "small", children: "View" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              value: enrollment.status,
              onChange: (e) => handleStatusUpdate(enrollment.id, e.target.value),
              style: {
                padding: "0.375rem 0.5rem",
                fontSize: "0.875rem",
                borderRadius: "0.375rem",
                border: "1px solid #d1d5db",
                backgroundColor: "white",
                cursor: "pointer"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "active", children: "Active" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "completed", children: "Completed" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "pending", children: "Pending" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "dropped", children: "Dropped" })
              ]
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "danger",
              size: "small",
              onClick: () => handleUnenroll(enrollment.id, enrollment.student_name || "this student"),
              children: "Unenroll"
            }
          )
        ] }) })
      ] }, enrollment.id)) })
    ] }) }) })
  ] }) });
};
export {
  ManageStudents
};
//# sourceMappingURL=ManageStudents-BsB9JE0B.js.map
