import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { S as Spinner, C as Card, B as Button, H as Heading, c as apiClient } from "./index-C0G9mbri.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const QuizListPage = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["studentQuizzes"],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/quizzes/my-quizzes");
      return response.data;
    },
    staleTime: 5 * 60 * 1e3,
    // Cache for 5 minutes
    retry: 2
  });
  const quizzes = data?.quizzes || [];
  const pendingQuizzes = quizzes.filter((q) => q.status === "pending" || q.status === "in_progress");
  const completedQuizzes = quizzes.filter((q) => q.status === "completed");
  const getStatusBadge = (status, score, passingScore) => {
    const styles = {
      pending: { backgroundColor: "#fef3c7", color: "#92400e", padding: "0.25rem 0.75rem", borderRadius: "9999px", fontSize: "0.75rem", fontWeight: 600 },
      in_progress: { backgroundColor: "#dbeafe", color: "#1e40af", padding: "0.25rem 0.75rem", borderRadius: "9999px", fontSize: "0.75rem", fontWeight: 600 },
      completed: { backgroundColor: score && passingScore && score >= passingScore ? "#d1fae5" : "#fee2e2", color: score && passingScore && score >= passingScore ? "#065f46" : "#991b1b", padding: "0.25rem 0.75rem", borderRadius: "9999px", fontSize: "0.75rem", fontWeight: 600 }
    };
    const labels = {
      pending: "Not Started",
      in_progress: "In Progress",
      completed: score && passingScore && score >= passingScore ? "Passed" : "Needs Review"
    };
    return /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: styles[status], children: labels[status] });
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "400px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", marginBottom: "1rem" }, children: "Unable to load quizzes. Please try refreshing the page." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => window.location.reload(), children: "Refresh Page" })
    ] }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Quizzes & Assessments" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Complete quizzes to test your knowledge and track your progress" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: pendingQuizzes.length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Pending Quizzes" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: completedQuizzes.length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Completed" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#8b5cf6" }, children: [
          completedQuizzes.length > 0 ? Math.round(completedQuizzes.reduce((sum, q) => sum + (q.score || 0), 0) / completedQuizzes.length) : 0,
          "%"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Average Score" })
      ] }) })
    ] }),
    pendingQuizzes.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1rem" }, children: "📝 Ready to Take" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gap: "1rem" }, children: pendingQuizzes.map((quiz) => /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: "200px" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", margin: 0 }, children: quiz.title }),
            getStatusBadge(quiz.status)
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.875rem", marginBottom: "0.75rem" }, children: quiz.description }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1.5rem", fontSize: "0.875rem", color: "#666" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "📚 ",
              quiz.course_title
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "❓ ",
              quiz.num_questions,
              " questions"
            ] }),
            quiz.time_limit_minutes && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "⏱️ ",
              quiz.time_limit_minutes,
              " min"
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "✅ Pass: ",
              quiz.passing_score,
              "%"
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/quizzes/${quiz.id}/course/${quiz.course_id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", "data-action": "take-quiz", children: quiz.status === "in_progress" ? "Continue Quiz" : "Start Quiz" }) }) })
      ] }) }, quiz.id)) })
    ] }),
    completedQuizzes.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1rem" }, children: "✅ Completed Quizzes" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gap: "1rem" }, children: completedQuizzes.map((quiz) => /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { backgroundColor: "#f9fafb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: "200px" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", margin: 0 }, children: quiz.title }),
            getStatusBadge(quiz.status, quiz.score, quiz.passing_score)
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { color: "#666", fontSize: "0.875rem", marginBottom: "0.75rem" }, children: [
            "📚 ",
            quiz.course_title
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1.5rem", fontSize: "0.875rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { fontWeight: 600, color: quiz.score && quiz.score >= quiz.passing_score ? "#10b981" : "#dc2626" }, children: [
              "Score: ",
              quiz.score,
              "%"
            ] }),
            quiz.completed_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { color: "#666" }, children: [
              "Completed: ",
              new Date(quiz.completed_at).toLocaleDateString()
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/quizzes/${quiz.id}/course/${quiz.course_id}/results`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "medium", children: "View Results" }) }),
          quiz.score && quiz.score < quiz.passing_score && /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/quizzes/${quiz.id}/course/${quiz.course_id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Retake Quiz" }) })
        ] })
      ] }) }, quiz.id)) })
    ] }),
    quizzes.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "4rem", marginBottom: "1rem" }, children: "📝" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { marginBottom: "0.5rem" }, children: "No Quizzes Available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", marginBottom: "1.5rem" }, children: "Quizzes will appear here once your trainer assigns them to your enrolled courses." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/courses/my-courses", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "View My Courses" }) })
    ] })
  ] }) });
};
export {
  QuizListPage
};
//# sourceMappingURL=QuizListPage-OjkRQsRR.js.map
