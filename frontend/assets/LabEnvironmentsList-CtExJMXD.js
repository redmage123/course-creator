import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { u as useAuth, H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const LAB_API_BASE = "https://176.9.99.103:8005/api/v1/labs";
class LabServiceError extends Error {
  constructor(message, statusCode, detail) {
    super(message);
    this.statusCode = statusCode;
    this.detail = detail;
    this.name = "LabServiceError";
  }
}
async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "An error occurred"
    }));
    throw new LabServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }
  return response.json();
}
const studentLabService = {
  /**
   * Get all labs for the authenticated student.
   *
   * Security Context:
   * Uses student_id from JWT token to ensure data isolation.
   * Prevents cross-user data leakage (OWASP A01:2021).
   *
   * Business Context:
   * Returns labs the student has actually interacted with,
   * fixing the "Retry Lab" button appearing for labs never attempted.
   */
  async getStudentLabs(studentId) {
    const response = await fetch(`${LAB_API_BASE}/student/${studentId}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" }
    });
    return handleResponse(response);
  }
};
const mockLabEnvironments = [
  {
    id: "1",
    title: "Python Basics - Variables and Data Types",
    courseName: "Introduction to Python Programming",
    courseId: "course-1",
    description: "Learn Python fundamentals by working with variables, strings, numbers, and basic operations in an interactive environment.",
    difficulty: "beginner",
    estimatedTime: 30,
    technology: "Python 3.11",
    ideType: "jupyter",
    status: "completed",
    progressPercentage: 100,
    lastAccessedAt: "2025-10-28",
    completedAt: "2025-10-28",
    objectives: [
      "Create and use variables",
      "Work with different data types",
      "Perform basic arithmetic operations",
      "Use string formatting"
    ]
  },
  {
    id: "2",
    title: "Python Functions and Modules",
    courseName: "Introduction to Python Programming",
    courseId: "course-1",
    description: "Master function definitions, parameters, return values, and importing modules in this hands-on lab.",
    difficulty: "beginner",
    estimatedTime: 45,
    technology: "Python 3.11",
    ideType: "jupyter",
    status: "in-progress",
    progressPercentage: 60,
    lastAccessedAt: "2025-11-02",
    containerUrl: "https://lab.example.com/containers/student123-lab2",
    objectives: [
      "Define and call functions",
      "Use function parameters and return values",
      "Import and use standard library modules",
      "Create custom modules"
    ]
  },
  {
    id: "3",
    title: "Data Structures - Lists and Dictionaries",
    courseName: "Introduction to Python Programming",
    courseId: "course-1",
    description: "Explore Python's powerful built-in data structures through practical exercises.",
    difficulty: "intermediate",
    estimatedTime: 60,
    technology: "Python 3.11",
    ideType: "vscode",
    status: "available",
    progressPercentage: 0,
    objectives: [
      "Create and manipulate lists",
      "Use list comprehensions",
      "Work with dictionaries",
      "Combine data structures"
    ]
  },
  {
    id: "4",
    title: "JavaScript ES6+ Features",
    courseName: "Modern JavaScript Development",
    courseId: "course-2",
    description: "Learn modern JavaScript syntax including arrow functions, destructuring, spread operators, and more.",
    difficulty: "intermediate",
    estimatedTime: 50,
    technology: "Node.js 18",
    ideType: "vscode",
    status: "available",
    progressPercentage: 0,
    objectives: [
      "Use arrow functions",
      "Apply destructuring syntax",
      "Work with spread and rest operators",
      "Understand template literals"
    ]
  },
  {
    id: "5",
    title: "React Components and State",
    courseName: "Modern JavaScript Development",
    courseId: "course-2",
    description: "Build interactive React components and manage state in this practical lab environment.",
    difficulty: "advanced",
    estimatedTime: 90,
    technology: "React 18 + TypeScript",
    ideType: "vscode",
    status: "available",
    progressPercentage: 0,
    objectives: [
      "Create functional components",
      "Use React hooks (useState, useEffect)",
      "Handle events",
      "Manage component state"
    ]
  },
  {
    id: "6",
    title: "Data Analysis with R",
    courseName: "Statistical Computing",
    courseId: "course-3",
    description: "Analyze datasets using R programming language and create visualizations.",
    difficulty: "intermediate",
    estimatedTime: 75,
    technology: "R 4.3",
    ideType: "rstudio",
    status: "available",
    progressPercentage: 0,
    objectives: [
      "Import and clean data",
      "Perform statistical analysis",
      "Create visualizations with ggplot2",
      "Generate reports with R Markdown"
    ]
  },
  {
    id: "7",
    title: "Linux Command Line Basics",
    courseName: "DevOps Fundamentals",
    courseId: "course-4",
    description: "Master essential Linux commands and shell scripting in a real terminal environment.",
    difficulty: "beginner",
    estimatedTime: 40,
    technology: "Ubuntu 22.04",
    ideType: "terminal",
    status: "completed",
    progressPercentage: 100,
    lastAccessedAt: "2025-10-25",
    completedAt: "2025-10-25",
    objectives: [
      "Navigate the file system",
      "Manage files and directories",
      "Use pipes and redirection",
      "Write basic shell scripts"
    ]
  },
  {
    id: "8",
    title: "Docker Containers and Images",
    courseName: "DevOps Fundamentals",
    courseId: "course-4",
    description: "Learn Docker fundamentals by building, running, and managing containers.",
    difficulty: "advanced",
    estimatedTime: 120,
    technology: "Docker 24",
    ideType: "terminal",
    status: "available",
    progressPercentage: 0,
    objectives: [
      "Build Docker images",
      "Run and manage containers",
      "Work with Docker Compose",
      "Understand container networking"
    ]
  }
];
const LabEnvironmentsList = () => {
  const { user } = useAuth();
  const [labs, setLabs] = reactExports.useState(mockLabEnvironments);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const [courseFilter, setCourseFilter] = reactExports.useState("all");
  const [difficultyFilter, setDifficultyFilter] = reactExports.useState("all");
  reactExports.useEffect(() => {
    const fetchStudentLabs = async () => {
      if (!user?.id) {
        setLabs(mockLabEnvironments.map((lab) => ({
          ...lab,
          status: "available",
          progressPercentage: 0,
          lastAccessedAt: void 0,
          completedAt: void 0,
          containerUrl: void 0
        })));
        setIsLoading(false);
        return;
      }
      try {
        setIsLoading(true);
        setError(null);
        const studentLabData = await studentLabService.getStudentLabs(user.id);
        const labStatusMap = /* @__PURE__ */ new Map();
        studentLabData.labs.forEach((lab) => {
          let frontendStatus = "available";
          if (lab.status === "completed" || lab.status === "stopped") {
            frontendStatus = "completed";
          } else if (lab.status === "running" || lab.status === "paused") {
            frontendStatus = "in-progress";
          }
          labStatusMap.set(lab.lab_id, {
            status: frontendStatus,
            lastAccessedAt: lab.last_accessed,
            containerUrl: lab.ide_urls?.vscode || lab.ide_urls?.jupyter || void 0
          });
        });
        const mergedLabs = mockLabEnvironments.map((lab) => {
          const studentLabStatus = labStatusMap.get(lab.id);
          if (studentLabStatus) {
            return {
              ...lab,
              status: studentLabStatus.status,
              progressPercentage: studentLabStatus.status === "completed" ? 100 : studentLabStatus.status === "in-progress" ? 50 : 0,
              lastAccessedAt: studentLabStatus.lastAccessedAt || void 0,
              completedAt: studentLabStatus.status === "completed" ? studentLabStatus.lastAccessedAt || void 0 : void 0,
              containerUrl: studentLabStatus.containerUrl
            };
          }
          return {
            ...lab,
            status: "available",
            progressPercentage: 0,
            lastAccessedAt: void 0,
            completedAt: void 0,
            containerUrl: void 0
          };
        });
        setLabs(mergedLabs);
      } catch (err) {
        console.error("Failed to fetch student labs:", err);
        setError("Failed to load lab status. Showing available labs.");
        setLabs(mockLabEnvironments.map((lab) => ({
          ...lab,
          status: "available",
          progressPercentage: 0,
          lastAccessedAt: void 0,
          completedAt: void 0,
          containerUrl: void 0
        })));
      } finally {
        setIsLoading(false);
      }
    };
    fetchStudentLabs();
  }, [user?.id]);
  const uniqueCourses = Array.from(new Set(labs.map((lab) => lab.courseName)));
  const filteredLabs = labs.filter((lab) => {
    const matchesSearch = lab.title.toLowerCase().includes(searchQuery.toLowerCase()) || lab.description.toLowerCase().includes(searchQuery.toLowerCase()) || lab.courseName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || lab.status === statusFilter;
    const matchesCourse = courseFilter === "all" || lab.courseName === courseFilter;
    const matchesDifficulty = difficultyFilter === "all" || lab.difficulty === difficultyFilter;
    return matchesSearch && matchesStatus && matchesCourse && matchesDifficulty;
  });
  const handleLaunchLab = (labId) => {
    console.log("Launching lab:", labId);
    alert("Lab environment is being prepared. This will open in a new window once ready.");
  };
  const handleResumeLab = (labId, containerUrl) => {
    console.log("Resuming lab:", labId, "at", containerUrl);
    window.open(containerUrl, "_blank");
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
      case "available":
        return "#3b82f6";
      case "in-progress":
        return "#f59e0b";
      case "completed":
        return "#10b981";
      default:
        return "#6b7280";
    }
  };
  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case "beginner":
        return "#10b981";
      case "intermediate":
        return "#f59e0b";
      case "advanced":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };
  const getIdeInfo = (ideType) => {
    switch (ideType) {
      case "vscode":
        return { color: "#007acc", icon: "💻", label: "VS Code" };
      case "jupyter":
        return { color: "#f37726", icon: "📊", label: "Jupyter" };
      case "rstudio":
        return { color: "#75aadb", icon: "📈", label: "RStudio" };
      case "terminal":
        return { color: "#2d2d2d", icon: "⌨️", label: "Terminal" };
      default:
        return { color: "#6b7280", icon: "💻", label: "IDE" };
    }
  };
  const stats = {
    total: labs.length,
    available: labs.filter((l) => l.status === "available").length,
    inProgress: labs.filter((l) => l.status === "in-progress").length,
    completed: labs.filter((l) => l.status === "completed").length
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1400px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Lab Environments" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Interactive coding environments for hands-on practice" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/student", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
    ] }),
    isLoading && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem", textAlign: "center" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, color: "#666" }, children: "Loading lab environments..." }) }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem", backgroundColor: "#fef3c7", borderColor: "#f59e0b" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: 0, color: "#92400e" }, children: [
      "⚠️ ",
      error
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Total Labs" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#1f2937" }, children: stats.total })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Available" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: stats.available })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "In Progress" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: stats.inProgress })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Completed" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: stats.completed })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "search",
          name: "search",
          type: "text",
          placeholder: "Search labs...",
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
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "available", children: "Available" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "in-progress", children: "In Progress" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "completed", children: "Completed" })
          ]
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "select",
        {
          value: courseFilter,
          onChange: (e) => setCourseFilter(e.target.value),
          style: {
            width: "100%",
            padding: "0.75rem",
            fontSize: "0.875rem",
            border: "1px solid #d1d5db",
            borderRadius: "0.375rem",
            backgroundColor: "white"
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Courses" }),
            uniqueCourses.map((course) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: course, children: course }, course))
          ]
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "select",
        {
          value: difficultyFilter,
          onChange: (e) => setDifficultyFilter(e.target.value),
          style: {
            width: "100%",
            padding: "0.75rem",
            fontSize: "0.875rem",
            border: "1px solid #d1d5db",
            borderRadius: "0.375rem",
            backgroundColor: "white"
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Difficulties" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "beginner", children: "Beginner" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "intermediate", children: "Intermediate" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "advanced", children: "Advanced" })
          ]
        }
      ) })
    ] }) }),
    filteredLabs.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", color: "#666", marginBottom: "1rem" }, children: searchQuery || statusFilter !== "all" || courseFilter !== "all" || difficultyFilter !== "all" ? "No labs match your filters" : "No lab environments available yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/student", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Go to Dashboard" }) })
    ] }) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "1.5rem" }, children: filteredLabs.map((lab) => {
      const ideInfo = getIdeInfo(lab.ideType);
      return /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", margin: 0 }, children: lab.title }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
              display: "inline-block",
              padding: "0.25rem 0.75rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              textTransform: "capitalize",
              backgroundColor: `${getStatusColor(lab.status)}20`,
              color: getStatusColor(lab.status),
              whiteSpace: "nowrap"
            }, children: lab.status === "in-progress" ? "In Progress" : lab.status })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0", fontSize: "0.875rem", color: "#6b7280" }, children: lab.courseName })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#374151", lineHeight: "1.5", marginBottom: "1rem" }, children: lab.description }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: {
            display: "inline-flex",
            alignItems: "center",
            gap: "0.25rem",
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 600,
            backgroundColor: `${ideInfo.color}20`,
            color: ideInfo.color
          }, children: [
            ideInfo.icon,
            " ",
            ideInfo.label
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
            display: "inline-block",
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 600,
            textTransform: "capitalize",
            backgroundColor: `${getDifficultyColor(lab.difficulty)}20`,
            color: getDifficultyColor(lab.difficulty)
          }, children: lab.difficulty }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: {
            display: "inline-block",
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 600,
            backgroundColor: "#e5e7eb",
            color: "#374151"
          }, children: [
            "⏱️ ",
            lab.estimatedTime,
            " min"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
            display: "inline-block",
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 600,
            backgroundColor: "#e5e7eb",
            color: "#374151"
          }, children: lab.technology })
        ] }),
        lab.status !== "available" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: "0.875rem", color: "#6b7280" }, children: "Progress" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { fontSize: "0.875rem", fontWeight: 600, color: "#1f2937" }, children: [
              lab.progressPercentage,
              "%"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
            width: "100%",
            height: "8px",
            backgroundColor: "#e5e7eb",
            borderRadius: "9999px",
            overflow: "hidden"
          }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
            width: `${lab.progressPercentage}%`,
            height: "100%",
            backgroundColor: getStatusColor(lab.status),
            borderRadius: "9999px",
            transition: "width 0.3s ease"
          } }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "0.5rem" }, children: "Learning Objectives:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#6b7280", lineHeight: "1.6" }, children: [
            lab.objectives.slice(0, 3).map((objective, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: objective }, index)),
            lab.objectives.length > 3 && /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { style: { color: "#3b82f6" }, children: [
              "+",
              lab.objectives.length - 3,
              " more..."
            ] })
          ] })
        ] }),
        (lab.lastAccessedAt || lab.completedAt) && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "0.75rem", color: "#9ca3af", marginBottom: "1rem" }, children: [
          lab.completedAt && `✅ Completed on ${formatDate(lab.completedAt)}`,
          !lab.completedAt && lab.lastAccessedAt && `Last accessed on ${formatDate(lab.lastAccessedAt)}`
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem" }, children: [
          lab.status === "available" && /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              fullWidth: true,
              onClick: () => handleLaunchLab(lab.id),
              children: "🚀 Start Lab"
            }
          ),
          lab.status === "in-progress" && lab.containerUrl && /* @__PURE__ */ jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              fullWidth: true,
              onClick: () => handleResumeLab(lab.id, lab.containerUrl),
              children: "▶️ Resume Lab"
            }
          ) }),
          lab.status === "completed" && /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "secondary",
              fullWidth: true,
              onClick: () => handleLaunchLab(lab.id),
              children: "🔄 Retry Lab"
            }
          )
        ] })
      ] }, lab.id);
    }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginTop: "2rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "0.75rem", color: "#0c4a6e" }, children: "💡 Lab Environment Tips" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e", lineHeight: "1.6" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Each lab runs in an isolated Docker container for security" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Your progress is automatically saved as you work" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Labs remain active for 2 hours of inactivity before auto-suspension" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "You can resume suspended labs to continue from where you left off" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Completed labs can be retried to practice and improve your skills" })
      ] })
    ] })
  ] }) });
};
export {
  LabEnvironmentsList
};
//# sourceMappingURL=LabEnvironmentsList-CtExJMXD.js.map
