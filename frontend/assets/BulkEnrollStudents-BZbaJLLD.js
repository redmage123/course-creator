import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { S as Spinner, H as Heading, C as Card, B as Button } from "./index-C0G9mbri.js";
import { S as Select } from "./Select-D3EGugkq.js";
import { e as enrollmentService } from "./enrollmentService-CJs1-f8S.js";
import { t as trainingProgramService } from "./trainingProgramService-B-up7yl_.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const BulkEnrollStudents = () => {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.user.profile);
  const [target, setTarget] = reactExports.useState("course");
  const [programs, setPrograms] = reactExports.useState([]);
  const [isLoadingPrograms, setIsLoadingPrograms] = reactExports.useState(true);
  const [selectedId, setSelectedId] = reactExports.useState("");
  const [bulkStudentIds, setBulkStudentIds] = reactExports.useState("");
  const [csvFile, setCsvFile] = reactExports.useState(null);
  const [useCSV, setUseCSV] = reactExports.useState(false);
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  const [success, setSuccess] = reactExports.useState(null);
  const [bulkResult, setBulkResult] = reactExports.useState(null);
  reactExports.useEffect(() => {
    const loadPrograms = async () => {
      if (!user?.organizationId) return;
      try {
        setIsLoadingPrograms(true);
        const response = await trainingProgramService.getTrainingPrograms({
          organization_id: user.organizationId,
          published: true
        });
        setPrograms(response.data);
      } catch (err) {
        console.error("Failed to load training programs:", err);
        setError("Failed to load organization training programs. Please refresh the page.");
      } finally {
        setIsLoadingPrograms(false);
      }
    };
    loadPrograms();
  }, [user?.organizationId]);
  const tracks = Array.from(
    new Map(
      programs.filter((p) => p.track_id).map((p) => [p.track_id, { id: p.track_id, name: `Track ${p.track_id}` }])
    ).values()
  );
  const handleBulkEnrollment = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setBulkResult(null);
    if (!selectedId) {
      setError(`Please select a ${target === "course" ? "training program" : "track"}.`);
      return;
    }
    if (useCSV) {
      if (!csvFile) {
        setError("Please upload a CSV file.");
        return;
      }
      try {
        setIsSubmitting(true);
        const result = await enrollmentService.bulkEnrollFromCSV(selectedId, csvFile);
        setBulkResult(result);
        if (result.success_count > 0) {
          setSuccess(`Successfully enrolled ${result.success_count} student(s) from CSV!`);
        }
        if (result.failed_count > 0) {
          setError(`${result.failed_count} enrollment(s) failed. See details below.`);
        }
        if (result.failed_count === 0) {
          setCsvFile(null);
          setTimeout(() => navigate("/dashboard/org-admin"), 3e3);
        }
      } catch (err) {
        console.error("Failed to upload CSV:", err);
        setError(err.response?.data?.message || "Failed to process CSV file. Please check the format and try again.");
      } finally {
        setIsSubmitting(false);
      }
      return;
    }
    if (!bulkStudentIds.trim()) {
      setError("Please enter student IDs.");
      return;
    }
    const studentIdList = bulkStudentIds.split(/[,\n]/).map((id) => id.trim()).filter((id) => id.length > 0);
    if (studentIdList.length === 0) {
      setError("No valid student IDs found.");
      return;
    }
    try {
      setIsSubmitting(true);
      let result;
      if (target === "course") {
        result = await enrollmentService.bulkEnrollStudents({
          course_id: selectedId,
          student_ids: studentIdList
        });
      } else {
        result = await enrollmentService.bulkEnrollStudentsInTrack({
          track_id: selectedId,
          student_ids: studentIdList
        });
      }
      setBulkResult(result);
      if (result.success_count > 0) {
        setSuccess(`Successfully enrolled ${result.success_count} student(s) in ${target}!`);
      }
      if (result.failed_count > 0) {
        setError(`${result.failed_count} enrollment(s) failed. See details below.`);
      }
      if (result.failed_count === 0) {
        setBulkStudentIds("");
        setTimeout(() => navigate("/dashboard/org-admin"), 3e3);
      }
    } catch (err) {
      console.error("Failed to bulk enroll students:", err);
      setError(err.response?.data?.message || "Failed to enroll students. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };
  const downloadCSVTemplate = () => {
    const template = "student_id,student_name,student_email\nstudent123,John Doe,john@example.com\nstudent456,Jane Smith,jane@example.com\nstudent789,Bob Wilson,bob@example.com";
    const blob = new Blob([template], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "bulk_enrollment_template.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  if (isLoadingPrograms) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "400px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1000px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Bulk Enroll Students" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem", marginBottom: "1rem" }, children: "Enroll multiple students across your organization's training programs or tracks" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { backgroundColor: "#eff6ff" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: 0, fontSize: "0.9rem", color: "#1e40af" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "💡 Tip:" }),
        " Use track enrollment to enroll students in entire learning paths at once. CSV upload supports enrolling hundreds of students in seconds."
      ] }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1rem" }, children: "Enrollment Target" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Card,
          {
            variant: target === "course" ? "elevated" : "outlined",
            padding: "medium",
            style: {
              cursor: "pointer",
              border: target === "course" ? "2px solid #3b82f6" : void 0,
              transition: "all 0.2s"
            },
            onClick: () => setTarget("course"),
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2.5rem", marginBottom: "0.5rem" }, children: "📚" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 600, marginBottom: "0.25rem", fontSize: "1.1rem" }, children: "Single Training Program" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: "Enroll students in one specific course" })
            ] })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Card,
          {
            variant: target === "track" ? "elevated" : "outlined",
            padding: "medium",
            style: {
              cursor: "pointer",
              border: target === "track" ? "2px solid #3b82f6" : void 0,
              transition: "all 0.2s"
            },
            onClick: () => setTarget("track"),
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2.5rem", marginBottom: "0.5rem" }, children: "🎯" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 600, marginBottom: "0.25rem", fontSize: "1.1rem" }, children: "Complete Learning Track" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: "Enroll students in all courses in a track" })
            ] })
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1rem" }, children: "Input Method" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Card,
          {
            variant: !useCSV ? "elevated" : "outlined",
            padding: "medium",
            style: {
              cursor: "pointer",
              border: !useCSV ? "2px solid #10b981" : void 0,
              transition: "all 0.2s"
            },
            onClick: () => setUseCSV(false),
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2.5rem", marginBottom: "0.5rem" }, children: "✍️" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 600, marginBottom: "0.25rem", fontSize: "1.1rem" }, children: "Manual Entry" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: "Paste student IDs directly" })
            ] })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Card,
          {
            variant: useCSV ? "elevated" : "outlined",
            padding: "medium",
            style: {
              cursor: "pointer",
              border: useCSV ? "2px solid #10b981" : void 0,
              transition: "all 0.2s"
            },
            onClick: () => setUseCSV(true),
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center" }, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "2.5rem", marginBottom: "0.5rem" }, children: "📤" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 600, marginBottom: "0.25rem", fontSize: "1.1rem" }, children: "CSV Upload" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: "Upload file with student list" })
            ] })
          }
        )
      ] })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem", borderColor: "#ef4444", backgroundColor: "#fee2e2" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", margin: 0, fontWeight: 500 }, children: error }) }),
    success && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", style: { marginBottom: "1.5rem", borderColor: "#10b981", backgroundColor: "#d1fae5" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#065f46", margin: 0, fontWeight: 500 }, children: success }) }),
    bulkResult && bulkResult.failed_students && bulkResult.failed_students.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", style: { marginBottom: "1.5rem", borderColor: "#f59e0b" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "1rem" }, children: [
        "Failed Enrollments (",
        bulkResult.failed_count,
        ")"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { maxHeight: "300px", overflowY: "auto" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { style: { width: "100%", fontSize: "0.875rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "2px solid #e5e7eb" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "0.5rem", textAlign: "left", fontWeight: 600 }, children: "Student ID" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("th", { style: { padding: "0.5rem", textAlign: "left", fontWeight: 600 }, children: "Reason" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: bulkResult.failed_students.map((failure, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { style: { borderBottom: "1px solid #e5e7eb" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "0.5rem", fontFamily: "monospace" }, children: failure.student_id }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("td", { style: { padding: "0.5rem", color: "#dc2626" }, children: failure.reason })
        ] }, index)) })
      ] }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleBulkEnrollment, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "target", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: target === "course" ? "Select Training Program *" : "Select Learning Track *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            id: "target",
            name: "target",
            value: selectedId,
            onChange: (value) => setSelectedId(value),
            options: target === "course" ? [
              { value: "", label: "Choose a training program..." },
              ...programs.map((program) => ({
                value: program.id,
                label: `${program.title} (${program.difficulty_level})`
              }))
            ] : [
              { value: "", label: "Choose a learning track..." },
              ...tracks.map((track) => ({
                value: track.id,
                label: track.name
              }))
            ],
            disabled: isSubmitting
          }
        ),
        programs.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#dc2626", marginTop: "0.5rem" }, children: "No training programs found for your organization." }),
        target === "track" && tracks.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#dc2626", marginTop: "0.5rem" }, children: "No learning tracks configured yet." })
      ] }),
      !useCSV && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "bulkStudentIds", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Student IDs (one per line or comma-separated) *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "textarea",
          {
            id: "bulkStudentIds",
            name: "bulkStudentIds",
            rows: 10,
            placeholder: "Enter student IDs, one per line:\nstudent123\nstudent456\nstudent789\n...\n\nOr comma-separated: student123, student456, student789",
            value: bulkStudentIds,
            onChange: (e) => setBulkStudentIds(e.target.value),
            disabled: isSubmitting,
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              fontFamily: "monospace",
              resize: "vertical"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "💡 Tip: You can paste hundreds of IDs at once for bulk processing." })
      ] }),
      useCSV && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "csvFile", style: { fontWeight: 500 }, children: "CSV File *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              type: "button",
              variant: "text",
              size: "small",
              onClick: downloadCSVTemplate,
              children: "📥 Download Template"
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            id: "csvFile",
            name: "csvFile",
            type: "file",
            accept: ".csv",
            onChange: (e) => setCsvFile(e.target.files?.[0] || null),
            disabled: isSubmitting,
            style: {
              width: "100%",
              padding: "1rem",
              fontSize: "0.875rem",
              border: "2px dashed #d1d5db",
              borderRadius: "0.375rem",
              cursor: "pointer",
              backgroundColor: "#f9fafb"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginTop: "1rem", padding: "1rem", backgroundColor: "#f0f9ff", borderRadius: "0.375rem", border: "1px solid #bae6fd" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0 0 0.5rem", fontWeight: 500, fontSize: "0.875rem", color: "#0c4a6e" }, children: "CSV Format Requirements:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { style: { margin: 0, paddingLeft: "1.5rem", fontSize: "0.875rem", color: "#0c4a6e" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
              "Required column: ",
              /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "student_id" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
              "Optional columns: ",
              /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "student_name" }),
              ", ",
              /* @__PURE__ */ jsxRuntimeExports.jsx("code", { style: { backgroundColor: "#e0f2fe", padding: "0.125rem 0.25rem", borderRadius: "0.25rem" }, children: "student_email" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Maximum recommended: 1000 students per upload" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem", justifyContent: "flex-end", paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/org-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", disabled: isSubmitting, children: "Cancel" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "submit",
            variant: "primary",
            disabled: isSubmitting || !selectedId || (useCSV ? !csvFile : !bulkStudentIds.trim()),
            children: isSubmitting ? "Processing..." : useCSV ? "Upload & Enroll" : `Enroll Students in ${target === "course" ? "Course" : "Track"}`
          }
        )
      ] })
    ] }) }),
    bulkResult && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", style: { marginTop: "1.5rem", backgroundColor: "#f0fdf4", border: "1px solid #86efac" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "1rem", color: "#166534" }, children: "Enrollment Summary" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#166534" }, children: "Total Processed" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.75rem", fontWeight: "bold", color: "#166534" }, children: bulkResult.success_count + bulkResult.failed_count })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#166534" }, children: "Successful" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.75rem", fontWeight: "bold", color: "#16a34a" }, children: bulkResult.success_count })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#166534" }, children: "Failed" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.25rem 0 0", fontSize: "1.75rem", fontWeight: "bold", color: "#dc2626" }, children: bulkResult.failed_count })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.875rem", color: "#166534" }, children: "Success Rate" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: "0.25rem 0 0", fontSize: "1.75rem", fontWeight: "bold", color: "#16a34a" }, children: [
            Math.round(bulkResult.success_count / (bulkResult.success_count + bulkResult.failed_count) * 100),
            "%"
          ] })
        ] })
      ] })
    ] })
  ] }) });
};
export {
  BulkEnrollStudents
};
//# sourceMappingURL=BulkEnrollStudents-BZbaJLLD.js.map
