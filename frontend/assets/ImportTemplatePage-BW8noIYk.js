import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, C as Card, B as Button, S as Spinner, c as apiClient } from "./index-C0G9mbri.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const ImportTemplatePage = () => {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.user.profile);
  const [templateFile, setTemplateFile] = reactExports.useState(null);
  const [isDragging, setIsDragging] = reactExports.useState(false);
  const [isImporting, setIsImporting] = reactExports.useState(false);
  const [importResult, setImportResult] = reactExports.useState(null);
  const [error, setError] = reactExports.useState(null);
  const handleDrop = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      const validTypes = ["application/json", "text/yaml", "application/x-yaml"];
      const validExtensions = [".json", ".yaml", ".yml"];
      const hasValidExtension = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
      if (validTypes.includes(file.type) || hasValidExtension) {
        setTemplateFile(file);
        setError(null);
      } else {
        setError("Please upload a JSON or YAML file.");
      }
    }
  }, []);
  const handleDragOver = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const handleDragLeave = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setTemplateFile(file);
      setError(null);
    }
  };
  const handleImport = async () => {
    if (!templateFile || !user?.organizationId) return;
    setIsImporting(true);
    setError(null);
    setImportResult(null);
    try {
      const formData = new FormData();
      formData.append("template", templateFile);
      formData.append("organization_id", user.organizationId);
      const response = await apiClient.post(
        "/api/v1/organizations/import-template",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        }
      );
      setImportResult(response.data);
      if (response.data.success) {
        setTimeout(() => navigate("/dashboard/org-admin"), 3e3);
      }
    } catch (err) {
      console.error("Failed to import template:", err);
      setError(err.response?.data?.message || "Failed to import template. Please check the file format and try again.");
    } finally {
      setIsImporting(false);
    }
  };
  const downloadSampleTemplate = () => {
    const sampleTemplate = {
      name: "Sample Organization Template",
      version: "1.0",
      description: "A sample template for creating training projects and tracks",
      projects: [
        {
          name: "AI Fundamentals Training",
          description: "Comprehensive AI training program for corporate teams",
          tracks: [
            {
              name: "Machine Learning Basics",
              description: "Introduction to ML concepts",
              courses: [
                {
                  title: "Introduction to Machine Learning",
                  description: "Learn ML fundamentals",
                  difficulty_level: "beginner",
                  duration_hours: 8
                }
              ]
            }
          ]
        }
      ]
    };
    const blob = new Blob([JSON.stringify(sampleTemplate, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "organization_template_sample.json";
    link.click();
    URL.revokeObjectURL(url);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1000px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Import Organization Template" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem", marginBottom: "1rem" }, children: "Import a template to automatically create projects, tracks, and courses for your organization" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { backgroundColor: "#eff6ff" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: 0, fontSize: "0.9rem", color: "#1e40af" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "💡 Tip:" }),
        " Templates can define complete training programs with multiple tracks and courses. AI will help populate course content based on the template structure."
      ] }) })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem", borderColor: "#ef4444", backgroundColor: "#fee2e2" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", margin: 0, fontWeight: 500 }, children: error }) }),
    importResult && /* @__PURE__ */ jsxRuntimeExports.jsxs(
      Card,
      {
        variant: "elevated",
        padding: "large",
        style: {
          marginBottom: "1.5rem",
          backgroundColor: importResult.success ? "#d1fae5" : "#fee2e2",
          borderColor: importResult.success ? "#10b981" : "#ef4444"
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "1rem" }, children: importResult.success ? "✅ Import Successful!" : "⚠️ Import Completed with Issues" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem", marginBottom: "1rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#666" }, children: "Projects Created" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.5rem", fontWeight: "bold" }, children: importResult.projectsCreated })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#666" }, children: "Tracks Created" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.5rem", fontWeight: "bold" }, children: importResult.tracksCreated })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#666" }, children: "Courses Created" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.5rem", fontWeight: "bold" }, children: importResult.coursesCreated })
            ] })
          ] }),
          importResult.errors.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginTop: "1rem", padding: "1rem", backgroundColor: "#fff", borderRadius: "0.5rem" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0 0 0.5rem", fontWeight: 500, color: "#dc2626" }, children: "Errors:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { style: { margin: 0, paddingLeft: "1.5rem" }, children: importResult.errors.map((err, idx) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { style: { color: "#dc2626", fontSize: "0.875rem" }, children: err }, idx)) })
          ] })
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", margin: 0 }, children: "Upload Template File" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "text",
            size: "small",
            onClick: downloadSampleTemplate,
            children: "📥 Download Sample Template"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          onDrop: handleDrop,
          onDragOver: handleDragOver,
          onDragLeave: handleDragLeave,
          style: {
            border: `2px dashed ${isDragging ? "#3b82f6" : "#d1d5db"}`,
            borderRadius: "0.5rem",
            padding: "3rem 2rem",
            textAlign: "center",
            backgroundColor: isDragging ? "#eff6ff" : "#f9fafb",
            cursor: "pointer",
            transition: "all 0.2s"
          },
          onClick: () => document.getElementById("templateFile")?.click(),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "templateFile",
                type: "file",
                accept: ".json,.yaml,.yml",
                onChange: handleFileChange,
                style: { display: "none" },
                disabled: isImporting
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "3rem", marginBottom: "1rem" }, children: "📁" }),
            templateFile ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "1.1rem", fontWeight: 500, color: "#10b981", marginBottom: "0.5rem" }, children: [
                "✅ ",
                templateFile.name
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "0.875rem", color: "#666" }, children: [
                (templateFile.size / 1024).toFixed(2),
                " KB • Click to replace"
              ] })
            ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "1.1rem", fontWeight: 500, marginBottom: "0.5rem" }, children: "Drag & drop your template file here" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666" }, children: "or click to browse • Supports JSON, YAML" })
            ] })
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginTop: "1.5rem", padding: "1rem", backgroundColor: "#f0f9ff", borderRadius: "0.375rem", border: "1px solid #bae6fd" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0 0 0.5rem", fontWeight: 500, fontSize: "0.875rem", color: "#0c4a6e" }, children: "Template Structure:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "projects[]" }),
            " - Array of training projects"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "tracks[]" }),
            " - Learning tracks within projects"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "courses[]" }),
            " - Courses within tracks"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "AI will generate content for courses based on titles and descriptions" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem", justifyContent: "flex-end" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/org-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", disabled: isImporting, children: "Cancel" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: handleImport,
          disabled: !templateFile || isImporting,
          children: isImporting ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
            " Importing..."
          ] }) : "🚀 Import Template"
        }
      )
    ] })
  ] }) });
};
export {
  ImportTemplatePage
};
//# sourceMappingURL=ImportTemplatePage-BW8noIYk.js.map
