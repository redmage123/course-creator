import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { h as useSearchParams, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { S as Spinner, C as Card, B as Button, H as Heading, c as apiClient } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const ResourcesPage = () => {
  const [searchParams] = useSearchParams();
  const downloadMode = searchParams.get("download") === "true";
  const [searchTerm, setSearchTerm] = reactExports.useState("");
  const [selectedType, setSelectedType] = reactExports.useState("all");
  const [downloadingIds, setDownloadingIds] = reactExports.useState(/* @__PURE__ */ new Set());
  const { data, isLoading, error } = useQuery({
    queryKey: ["studentResources"],
    queryFn: async () => {
      const response = await apiClient.get("/api/v1/resources/my-resources");
      return response.data;
    },
    staleTime: 5 * 60 * 1e3,
    retry: 2
  });
  const resources = data?.resources || [];
  const filteredResources = reactExports.useMemo(() => {
    return resources.filter((resource) => {
      const matchesSearch = searchTerm === "" || resource.title.toLowerCase().includes(searchTerm.toLowerCase()) || resource.description.toLowerCase().includes(searchTerm.toLowerCase()) || resource.course_title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = selectedType === "all" || resource.type === selectedType;
      return matchesSearch && matchesType;
    });
  }, [resources, searchTerm, selectedType]);
  const getTypeIcon = (type) => {
    const icons = {
      video: "🎥",
      document: "📄",
      code: "💻",
      slides: "📊",
      dataset: "📊",
      other: "📁"
    };
    return icons[type] || "📁";
  };
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };
  const handleDownload = async (resource) => {
    setDownloadingIds((prev) => /* @__PURE__ */ new Set([...prev, resource.id]));
    try {
      const response = await apiClient.get(`/api/v1/resources/${resource.id}/download`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${resource.title}.${resource.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      alert("Download failed. Please try again.");
    } finally {
      setDownloadingIds((prev) => {
        const next = new Set(prev);
        next.delete(resource.id);
        return next;
      });
    }
  };
  const resourceTypes = reactExports.useMemo(() => {
    const types = new Set(resources.map((r) => r.type));
    return Array.from(types);
  }, [resources]);
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "400px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", marginBottom: "1rem" }, children: "Unable to load resources. Please try refreshing the page." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => window.location.reload(), children: "Refresh Page" })
    ] }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: downloadMode ? "Download Materials" : "Learning Resources" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: downloadMode ? "Download course materials for offline access" : "Access course materials, videos, and documentation" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flex: 1, minWidth: "250px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          type: "search",
          placeholder: "Search resources...",
          value: searchTerm,
          onChange: (e) => setSearchTerm(e.target.value)
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: selectedType === "all" ? "primary" : "secondary",
            size: "small",
            onClick: () => setSelectedType("all"),
            children: "All"
          }
        ),
        resourceTypes.map((type) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          Button,
          {
            variant: selectedType === type ? "primary" : "secondary",
            size: "small",
            onClick: () => setSelectedType(type),
            children: [
              getTypeIcon(type),
              " ",
              type.charAt(0).toUpperCase() + type.slice(1)
            ]
          },
          type
        ))
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem", marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: resources.length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Total Resources" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: resources.filter((r) => r.type === "video").length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Videos" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#8b5cf6" }, children: resources.filter((r) => r.type === "document").length }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Documents" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "medium", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: formatFileSize(resources.reduce((sum, r) => sum + r.file_size_bytes, 0)) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { color: "#666", fontSize: "0.875rem" }, children: "Total Size" })
      ] }) })
    ] }),
    filteredResources.length > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gap: "1rem" }, children: filteredResources.map((resource) => /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1rem", flex: 1, minWidth: "200px" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2.5rem" }, children: getTypeIcon(resource.type) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "0.25rem" }, children: resource.title }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.875rem", marginBottom: "0.5rem" }, children: resource.description }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1.5rem", fontSize: "0.75rem", color: "#666" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "📚 ",
              resource.course_title
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "📁 ",
              resource.format.toUpperCase()
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "💾 ",
              formatFileSize(resource.file_size_bytes)
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "📅 ",
              new Date(resource.created_at).toLocaleDateString()
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem" }, children: [
        resource.type === "video" ? /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/courses/${resource.course_id}/videos/${resource.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "▶️ Watch" }) }) : null,
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "secondary",
            size: "medium",
            onClick: () => handleDownload(resource),
            disabled: downloadingIds.has(resource.id),
            "data-action": "download",
            children: downloadingIds.has(resource.id) ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
              " Downloading..."
            ] }) : "⬇️ Download"
          }
        )
      ] })
    ] }) }, resource.id)) }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { textAlign: "center" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "4rem", marginBottom: "1rem" }, children: "📚" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { marginBottom: "0.5rem" }, children: searchTerm || selectedType !== "all" ? "No Resources Found" : "No Resources Available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", marginBottom: "1.5rem" }, children: searchTerm || selectedType !== "all" ? "Try adjusting your search or filters." : "Resources will appear here once your trainer adds them to your enrolled courses." }),
      (searchTerm || selectedType !== "all") && /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => {
        setSearchTerm("");
        setSelectedType("all");
      }, children: "Clear Filters" })
    ] })
  ] }) });
};
export {
  ResourcesPage
};
//# sourceMappingURL=ResourcesPage-Dw2sKuVb.js.map
