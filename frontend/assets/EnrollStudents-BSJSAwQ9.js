import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, h as useSearchParams, a as reactExports } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { S as Spinner, H as Heading, C as Card, B as Button } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { C as Checkbox } from "./Checkbox-CEUsiksA.js";
import { e as enrollmentService } from "./enrollmentService-CJs1-f8S.js";
import { t as trainingProgramService } from "./trainingProgramService-B-up7yl_.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const EnrollStudents = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = useAppSelector((state) => state.user.profile);
  const courseIdFromParams = searchParams.get("courseId");
  const [programs, setPrograms] = reactExports.useState([]);
  const [isLoadingPrograms, setIsLoadingPrograms] = reactExports.useState(true);
  const [selectedCourseId, setSelectedCourseId] = reactExports.useState(courseIdFromParams || "");
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [searchResults, setSearchResults] = reactExports.useState([]);
  const [isSearching, setIsSearching] = reactExports.useState(false);
  const [enrolledStudentIds, setEnrolledStudentIds] = reactExports.useState([]);
  const [selectedStudentIds, setSelectedStudentIds] = reactExports.useState([]);
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  const [success, setSuccess] = reactExports.useState(null);
  reactExports.useEffect(() => {
    const loadPrograms = async () => {
      if (!user?.id) return;
      try {
        setIsLoadingPrograms(true);
        const response = await trainingProgramService.getTrainingPrograms({
          instructor_id: user.id,
          published: true
        });
        setPrograms(response.data);
      } catch (err) {
        console.error("Failed to load training programs:", err);
        setError("Failed to load your training programs. Please refresh the page.");
      } finally {
        setIsLoadingPrograms(false);
      }
    };
    loadPrograms();
  }, [user?.id]);
  reactExports.useEffect(() => {
    const loadEnrolledStudents = async () => {
      if (!selectedCourseId) return;
      try {
        const enrolled = await enrollmentService.getEnrolledStudents(selectedCourseId);
        setEnrolledStudentIds(enrolled);
      } catch (err) {
        console.error("Failed to load enrolled students:", err);
      }
    };
    loadEnrolledStudents();
  }, [selectedCourseId]);
  reactExports.useEffect(() => {
    const searchStudents = async () => {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        return;
      }
      try {
        setIsSearching(true);
        const results = await enrollmentService.searchStudents(searchQuery);
        setSearchResults(results);
      } catch (err) {
        console.error("Failed to search students:", err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };
    const timeoutId = setTimeout(searchStudents, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);
  const handleStudentToggle = (studentId) => {
    setSelectedStudentIds(
      (prev) => prev.includes(studentId) ? prev.filter((id) => id !== studentId) : [...prev, studentId]
    );
  };
  const handleEnrollment = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!selectedCourseId) {
      setError("Please select a course.");
      return;
    }
    if (selectedStudentIds.length === 0) {
      setError("Please select at least one student to enroll.");
      return;
    }
    try {
      setIsSubmitting(true);
      const result = await enrollmentService.enrollStudents({
        courseId: selectedCourseId,
        studentIds: selectedStudentIds
      });
      const failedCount = result.failed?.length || 0;
      if (failedCount > 0) {
        setSuccess(`${result.enrolledCount} student(s) enrolled, ${failedCount} failed.`);
      } else {
        setSuccess(`Successfully enrolled ${result.enrolledCount} student(s)!`);
      }
      setSelectedStudentIds([]);
      setSearchQuery("");
      setSearchResults([]);
      const enrolled = await enrollmentService.getEnrolledStudents(selectedCourseId);
      setEnrolledStudentIds(enrolled);
      setTimeout(() => {
        navigate("/instructor/students");
      }, 2e3);
    } catch (err) {
      console.error("Failed to enroll students:", err);
      setError(err.response?.data?.message || err.message || "Failed to enroll students. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };
  if (isLoadingPrograms && !courseIdFromParams) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "400px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "900px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Enroll Students" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Search for students and enroll them in your training programs" })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx(
      Card,
      {
        variant: "outlined",
        padding: "medium",
        style: { marginBottom: "1.5rem", borderColor: "#ef4444", backgroundColor: "#fee2e2" },
        children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", margin: 0, fontWeight: 500 }, role: "alert", children: error })
      }
    ),
    success && /* @__PURE__ */ jsxRuntimeExports.jsx(
      Card,
      {
        variant: "outlined",
        padding: "medium",
        style: { marginBottom: "1.5rem", borderColor: "#10b981", backgroundColor: "#d1fae5" },
        children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#065f46", margin: 0, fontWeight: 500 }, role: "alert", children: success })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleEnrollment, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "course", style: { display: "block", fontWeight: 600, marginBottom: "0.5rem" }, children: "Select Course" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "course",
            value: selectedCourseId,
            onChange: (e) => setSelectedCourseId(e.target.value),
            style: {
              width: "100%",
              padding: "0.75rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              fontSize: "1rem"
            },
            required: true,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "Choose a course..." }),
              programs.map((program) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: program.id, children: program.title }, program.id))
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "search", style: { display: "block", fontWeight: 600, marginBottom: "0.5rem" }, children: "Search Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "search",
            type: "text",
            value: searchQuery,
            onChange: (e) => setSearchQuery(e.target.value),
            placeholder: "Search students by name, email, or ID",
            disabled: !selectedCourseId
          }
        ),
        !selectedCourseId && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "Please select a course first" })
      ] }),
      isSearching && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { textAlign: "center", padding: "2rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "medium" }) }),
      !isSearching && searchResults.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontWeight: 600, marginBottom: "0.75rem" }, children: [
          "Search Results (",
          searchResults.length,
          ")"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { maxHeight: "300px", overflowY: "auto", border: "1px solid #d1d5db", borderRadius: "0.375rem" }, children: searchResults.map((student) => {
          const isAlreadyEnrolled = enrolledStudentIds.includes(student.id);
          const isSelected = selectedStudentIds.includes(student.id);
          return /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                padding: "0.75rem 1rem",
                borderBottom: "1px solid #e5e7eb",
                backgroundColor: isSelected ? "#eff6ff" : "white",
                opacity: isAlreadyEnrolled ? 0.6 : 1
              },
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                Checkbox,
                {
                  label: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontWeight: 500 }, children: student.name }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: student.email }),
                    isAlreadyEnrolled && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.75rem", color: "#f59e0b", marginTop: "0.25rem" }, children: "Already enrolled" })
                  ] }),
                  checked: isSelected,
                  onChange: () => handleStudentToggle(student.id),
                  disabled: isAlreadyEnrolled
                }
              )
            },
            student.id
          );
        }) })
      ] }),
      !isSearching && searchQuery && searchResults.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { textAlign: "center", padding: "2rem", color: "#666" }, children: [
        'No students found matching "',
        searchQuery,
        '"'
      ] }),
      selectedStudentIds.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem", padding: "1rem", backgroundColor: "#f3f4f6", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontWeight: 600, marginBottom: "0.5rem" }, children: [
          "Selected Students: ",
          selectedStudentIds.length
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { fontSize: "0.875rem", color: "#666" }, children: selectedStudentIds.map((id) => {
          const student = searchResults.find((s) => s.id === id);
          return student ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "0.25rem" }, children: [
            "• ",
            student.name,
            " (",
            student.email,
            ")"
          ] }, id) : null;
        }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "1rem", justifyContent: "flex-end" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "button",
            variant: "secondary",
            onClick: () => navigate("/instructor/students"),
            disabled: isSubmitting,
            children: "Cancel"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "submit",
            variant: "primary",
            disabled: isSubmitting,
            children: isSubmitting ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
              "Enrolling..."
            ] }) : selectedStudentIds.length > 0 ? `Enroll ${selectedStudentIds.length} Student${selectedStudentIds.length !== 1 ? "s" : ""}` : "Enroll Students"
          }
        )
      ] })
    ] }) })
  ] }) });
};
export {
  EnrollStudents
};
//# sourceMappingURL=EnrollStudents-BSJSAwQ9.js.map
