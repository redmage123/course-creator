import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link, i as useParams } from "./react-vendor-cEae-lCc.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { B as Button, S as Spinner } from "./index-C0G9mbri.js";
import { T as Textarea } from "./Textarea-sTT_CGBL.js";
import { S as Select } from "./Select-D3EGugkq.js";
import "./state-vendor-B_izx0oA.js";
class BugService {
  /**
   * Base URL for bug tracking service
   * Uses port 8017 for the dedicated bug-tracking microservice
   */
  baseUrl = "/api/v1/bugs";
  /**
   * Get the full service URL
   * In development, connects directly to bug-tracking service
   * In production, routes through nginx proxy
   */
  getServiceUrl() {
    return "/api/bug-tracking/v1";
  }
  /**
   * Submit a new bug report
   *
   * @param data - Bug submission data
   * @returns Created bug report with ID for tracking
   */
  async submitBug(data) {
    const url = `${this.getServiceUrl()}/bugs`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders()
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error2 = await response.json().catch(() => ({ detail: "Failed to submit bug" }));
      throw new Error(error2.detail || "Failed to submit bug");
    }
    return response.json();
  }
  /**
   * Get bug details by ID
   *
   * @param bugId - Bug report ID
   * @returns Complete bug details including analysis and fix attempt
   */
  async getBug(bugId) {
    const url = `${this.getServiceUrl()}/bugs/${bugId}`;
    const response = await fetch(url, {
      method: "GET",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Bug report not found");
      }
      throw new Error("Failed to fetch bug details");
    }
    return response.json();
  }
  /**
   * Get analysis results for a bug
   *
   * @param bugId - Bug report ID
   * @returns Analysis results from Claude
   */
  async getBugAnalysis(bugId) {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/analysis`;
    const response = await fetch(url, {
      method: "GET",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Analysis not found");
      }
      throw new Error("Failed to fetch analysis");
    }
    return response.json();
  }
  /**
   * Get fix attempt details for a bug
   *
   * @param bugId - Bug report ID
   * @returns Fix attempt details including PR info
   */
  async getBugFix(bugId) {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/fix`;
    const response = await fetch(url, {
      method: "GET",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Fix attempt not found");
      }
      throw new Error("Failed to fetch fix details");
    }
    return response.json();
  }
  /**
   * List all bugs (admin only)
   *
   * @param filters - Optional filters for status, severity, pagination
   * @returns Paginated list of bug reports
   */
  async listBugs(filters2) {
    const params = new URLSearchParams();
    if (filters2?.status) params.append("status", filters2.status);
    if (filters2?.severity) params.append("severity", filters2.severity);
    if (filters2?.page) params.append("page", filters2.page.toString());
    if (filters2?.limit) params.append("limit", filters2.limit.toString());
    const url = `${this.getServiceUrl()}/bugs?${params.toString()}`;
    const response = await fetch(url, {
      method: "GET",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      throw new Error("Failed to fetch bugs");
    }
    return response.json();
  }
  /**
   * List bugs submitted by current user
   *
   * @param filters - Optional filters for status, severity, pagination
   * @returns Paginated list of user's bug reports
   */
  async listMyBugs(filters2) {
    const params = new URLSearchParams();
    if (filters2?.status) params.append("status", filters2.status);
    if (filters2?.severity) params.append("severity", filters2.severity);
    if (filters2?.page) params.append("page", filters2.page.toString());
    if (filters2?.limit) params.append("limit", filters2.limit.toString());
    const url = `${this.getServiceUrl()}/bugs/my/reports?${params.toString()}`;
    const response = await fetch(url, {
      method: "GET",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      throw new Error("Failed to fetch your bugs");
    }
    return response.json();
  }
  /**
   * Request re-analysis of a bug
   *
   * @param bugId - Bug report ID to re-analyze
   * @returns Updated bug report
   */
  async requestReanalysis(bugId) {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/reanalyze`;
    const response = await fetch(url, {
      method: "POST",
      headers: this.getAuthHeaders()
    });
    if (!response.ok) {
      throw new Error("Failed to request re-analysis");
    }
    return response.json();
  }
  /**
   * Get authentication headers from stored token
   */
  getAuthHeaders() {
    const token = localStorage.getItem("access_token");
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return {};
  }
}
const bugService = new BugService();
const form = "_form_itixx_9";
const formGroup = "_formGroup_itixx_15";
const formRow = "_formRow_itixx_19";
const label = "_label_itixx_31";
const required = "_required_itixx_38";
const error = "_error_itixx_42";
const hint = "_hint_itixx_49";
const errorBanner = "_errorBanner_itixx_56";
const formActions = "_formActions_itixx_65";
const submitButton = "_submitButton_itixx_71";
const infoBox = "_infoBox_itixx_78";
const successContainer = "_successContainer_itixx_107";
const successIcon = "_successIcon_itixx_114";
const successTitle = "_successTitle_itixx_127";
const successMessage = "_successMessage_itixx_133";
const trackingInfo = "_trackingInfo_itixx_140";
const trackingLabel = "_trackingLabel_itixx_147";
const trackingId = "_trackingId_itixx_154";
const successActions = "_successActions_itixx_162";
const styles$3 = {
  form,
  formGroup,
  formRow,
  label,
  required,
  error,
  hint,
  errorBanner,
  formActions,
  submitButton,
  infoBox,
  successContainer,
  successIcon,
  successTitle,
  successMessage,
  trackingInfo,
  trackingLabel,
  trackingId,
  successActions
};
const BugSubmissionForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = reactExports.useState({
    title: "",
    description: "",
    steps_to_reproduce: "",
    expected_behavior: "",
    actual_behavior: "",
    severity: "medium",
    affected_component: "",
    submitter_email: ""
  });
  const [errors, setErrors] = reactExports.useState({});
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [submitSuccess, setSubmitSuccess] = reactExports.useState(false);
  const [submittedBugId, setSubmittedBugId] = reactExports.useState(null);
  const severityOptions = [
    { value: "low", label: "Low - Minor issue, workaround exists" },
    { value: "medium", label: "Medium - Moderate impact on functionality" },
    { value: "high", label: "High - Significant impact, no workaround" },
    { value: "critical", label: "Critical - System unusable, data loss risk" }
  ];
  const componentOptions = [
    { value: "", label: "Select affected component..." },
    { value: "authentication", label: "Authentication / Login" },
    { value: "dashboard", label: "Dashboard" },
    { value: "courses", label: "Courses / Training Programs" },
    { value: "labs", label: "Lab Environment" },
    { value: "quizzes", label: "Quizzes / Assessments" },
    { value: "analytics", label: "Analytics / Reports" },
    { value: "content-generation", label: "AI Content Generation" },
    { value: "ai-assistant", label: "AI Assistant" },
    { value: "organization", label: "Organization Management" },
    { value: "user-management", label: "User Management" },
    { value: "notifications", label: "Notifications / Email" },
    { value: "api", label: "API / Backend" },
    { value: "frontend", label: "Frontend / UI" },
    { value: "other", label: "Other" }
  ];
  const handleChange = reactExports.useCallback((e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: void 0 }));
    }
  }, [errors]);
  const validateForm = reactExports.useCallback(() => {
    const newErrors = {};
    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    } else if (formData.title.length < 10) {
      newErrors.title = "Title must be at least 10 characters";
    } else if (formData.title.length > 255) {
      newErrors.title = "Title must be less than 255 characters";
    }
    if (!formData.description.trim()) {
      newErrors.description = "Description is required";
    } else if (formData.description.length < 20) {
      newErrors.description = "Description must be at least 20 characters";
    }
    if (!formData.submitter_email.trim()) {
      newErrors.submitter_email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.submitter_email)) {
      newErrors.submitter_email = "Please enter a valid email address";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);
  const handleSubmit = reactExports.useCallback(async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    setIsSubmitting(true);
    setErrors({});
    try {
      const submissionData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        severity: formData.severity,
        submitter_email: formData.submitter_email.trim(),
        browser_info: navigator.userAgent
      };
      if (formData.steps_to_reproduce.trim()) {
        submissionData.steps_to_reproduce = formData.steps_to_reproduce.trim();
      }
      if (formData.expected_behavior.trim()) {
        submissionData.expected_behavior = formData.expected_behavior.trim();
      }
      if (formData.actual_behavior.trim()) {
        submissionData.actual_behavior = formData.actual_behavior.trim();
      }
      if (formData.affected_component) {
        submissionData.affected_component = formData.affected_component;
      }
      const result = await bugService.submitBug(submissionData);
      setSubmitSuccess(true);
      setSubmittedBugId(result.id);
    } catch (error2) {
      const errorMessage = error2 instanceof Error ? error2.message : "Failed to submit bug report";
      setErrors({ general: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm]);
  const handleViewStatus = reactExports.useCallback(() => {
    if (submittedBugId) {
      navigate(`/bugs/${submittedBugId}`);
    }
  }, [navigate, submittedBugId]);
  const handleSubmitAnother = reactExports.useCallback(() => {
    setFormData({
      title: "",
      description: "",
      steps_to_reproduce: "",
      expected_behavior: "",
      actual_behavior: "",
      severity: "medium",
      affected_component: "",
      submitter_email: formData.submitter_email
      // Keep email for convenience
    });
    setSubmitSuccess(false);
    setSubmittedBugId(null);
  }, [formData.submitter_email]);
  if (submitSuccess && submittedBugId) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.successContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.successIcon, children: "✔" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$3.successTitle, children: "Bug Report Submitted" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3.successMessage, children: "Your bug report has been received and is being analyzed by our AI system. You will receive an email with the analysis results and any automated fixes." }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.trackingInfo, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.trackingLabel, children: "Tracking ID:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: styles$3.trackingId, children: submittedBugId })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.successActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: handleViewStatus, variant: "primary", children: "View Bug Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: handleSubmitAnother, variant: "secondary", children: "Submit Another Bug" })
      ] })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles$3.form, noValidate: true, children: [
    errors.general && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.errorBanner, role: "alert", children: errors.general }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "title", className: styles$3.label, children: [
        "Bug Title ",
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.required, children: "*" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "title",
          name: "title",
          type: "text",
          value: formData.title,
          onChange: handleChange,
          placeholder: "Brief summary of the issue",
          "aria-invalid": !!errors.title,
          "aria-describedby": errors.title ? "title-error" : void 0
        }
      ),
      errors.title && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { id: "title-error", className: styles$3.error, role: "alert", children: errors.title })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "description", className: styles$3.label, children: [
        "Description ",
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.required, children: "*" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Textarea,
        {
          id: "description",
          name: "description",
          value: formData.description,
          onChange: handleChange,
          placeholder: "Detailed description of the bug. Include any error messages you see.",
          rows: 5,
          "aria-invalid": !!errors.description,
          "aria-describedby": errors.description ? "description-error" : void 0
        }
      ),
      errors.description && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { id: "description-error", className: styles$3.error, role: "alert", children: errors.description })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "steps_to_reproduce", className: styles$3.label, children: "Steps to Reproduce" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Textarea,
        {
          id: "steps_to_reproduce",
          name: "steps_to_reproduce",
          value: formData.steps_to_reproduce,
          onChange: handleChange,
          placeholder: "1. Go to ...\n2. Click on ...\n3. Observe ...",
          rows: 4
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.hint, children: "List the exact steps to reproduce this bug" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formRow, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "expected_behavior", className: styles$3.label, children: "Expected Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Textarea,
          {
            id: "expected_behavior",
            name: "expected_behavior",
            value: formData.expected_behavior,
            onChange: handleChange,
            placeholder: "What should happen?",
            rows: 3
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "actual_behavior", className: styles$3.label, children: "Actual Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Textarea,
          {
            id: "actual_behavior",
            name: "actual_behavior",
            value: formData.actual_behavior,
            onChange: handleChange,
            placeholder: "What actually happens?",
            rows: 3
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formRow, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "severity", className: styles$3.label, children: "Severity" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            id: "severity",
            name: "severity",
            value: formData.severity,
            onChange: handleChange,
            options: severityOptions
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "affected_component", className: styles$3.label, children: "Affected Component" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            id: "affected_component",
            name: "affected_component",
            value: formData.affected_component,
            onChange: handleChange,
            options: componentOptions
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.formGroup, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "submitter_email", className: styles$3.label, children: [
        "Your Email ",
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.required, children: "*" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          id: "submitter_email",
          name: "submitter_email",
          type: "email",
          value: formData.submitter_email,
          onChange: handleChange,
          placeholder: "you@example.com",
          "aria-invalid": !!errors.submitter_email,
          "aria-describedby": errors.submitter_email ? "email-error" : void 0
        }
      ),
      errors.submitter_email && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { id: "email-error", className: styles$3.error, role: "alert", children: errors.submitter_email }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.hint, children: "Analysis results will be sent to this email" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.formActions, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      Button,
      {
        type: "submit",
        variant: "primary",
        disabled: isSubmitting,
        className: styles$3.submitButton,
        children: isSubmitting ? "Submitting..." : "Submit Bug Report"
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.infoBox, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { children: "What happens next?" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ol", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Your bug report will be analyzed by our AI system" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "The AI will identify the root cause and affected files" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "If possible, an automated fix will be generated" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "A pull request will be created for review" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "You'll receive an email with the full analysis and fix details" })
      ] })
    ] })
  ] });
};
const page$2 = "_page_pyum1_5";
const header$2 = "_header_pyum1_11";
const breadcrumb$2 = "_breadcrumb_pyum1_16";
const separator$2 = "_separator_pyum1_31";
const titleRow$1 = "_titleRow_pyum1_36";
const title$2 = "_title_pyum1_36";
const viewBugsLink = "_viewBugsLink_pyum1_57";
const subtitle$1 = "_subtitle_pyum1_67";
const content = "_content_pyum1_74";
const styles$2 = {
  page: page$2,
  header: header$2,
  breadcrumb: breadcrumb$2,
  separator: separator$2,
  titleRow: titleRow$1,
  title: title$2,
  viewBugsLink,
  subtitle: subtitle$1,
  content
};
const BugSubmissionPage = () => {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.page, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.breadcrumb, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard", children: "Dashboard" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.separator, children: "/" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Report Bug" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.titleRow, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles$2.title, children: "Report a Bug" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/my", className: styles$2.viewBugsLink, children: "View My Bug Reports" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.subtitle, children: "Help us improve the platform by reporting bugs. Our AI system will analyze your report and attempt to automatically generate a fix." })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.content, children: /* @__PURE__ */ jsxRuntimeExports.jsx(BugSubmissionForm, {}) })
  ] });
};
const page$1 = "_page_3coc1_5";
const loadingContainer$1 = "_loadingContainer_3coc1_11";
const errorContainer$1 = "_errorContainer_3coc1_12";
const breadcrumb$1 = "_breadcrumb_3coc1_21";
const separator$1 = "_separator_3coc1_36";
const header$1 = "_header_3coc1_42";
const headerTop = "_headerTop_3coc1_48";
const statusBadge$1 = "_statusBadge_3coc1_54";
const severityBadge$1 = "_severityBadge_3coc1_55";
const statusSubmitted$1 = "_statusSubmitted_3coc1_64";
const statusAnalyzing$1 = "_statusAnalyzing_3coc1_65";
const statusAnalysisComplete$1 = "_statusAnalysisComplete_3coc1_66";
const statusFixing$1 = "_statusFixing_3coc1_67";
const statusPrOpened$1 = "_statusPrOpened_3coc1_68";
const statusResolved$1 = "_statusResolved_3coc1_69";
const statusClosed$1 = "_statusClosed_3coc1_70";
const severityCritical$1 = "_severityCritical_3coc1_72";
const severityHigh$1 = "_severityHigh_3coc1_73";
const severityMedium$1 = "_severityMedium_3coc1_74";
const severityLow$1 = "_severityLow_3coc1_75";
const title$1 = "_title_3coc1_77";
const meta = "_meta_3coc1_83";
const section = "_section_3coc1_99";
const description = "_description_3coc1_115";
const preformatted = "_preformatted_3coc1_120";
const twoColumn = "_twoColumn_3coc1_130";
const analysisSection = "_analysisSection_3coc1_143";
const sectionHeader = "_sectionHeader_3coc1_151";
const confidenceMeter = "_confidenceMeter_3coc1_164";
const confidenceLabel = "_confidenceLabel_3coc1_170";
const confidenceScore = "_confidenceScore_3coc1_175";
const confidenceBar = "_confidenceBar_3coc1_181";
const confidenceFill = "_confidenceFill_3coc1_189";
const analysisBlock = "_analysisBlock_3coc1_195";
const analysisContent = "_analysisContent_3coc1_203";
const codeBlock = "_codeBlock_3coc1_211";
const fileList = "_fileList_3coc1_223";
const fileItem = "_fileItem_3coc1_231";
const fileIcon = "_fileIcon_3coc1_243";
const analysisMeta = "_analysisMeta_3coc1_251";
const fixSection = "_fixSection_3coc1_263";
const prSuccess = "_prSuccess_3coc1_273";
const prHeader = "_prHeader_3coc1_280";
const prIcon = "_prIcon_3coc1_287";
const prLink = "_prLink_3coc1_296";
const prStats = "_prStats_3coc1_311";
const testsFailed = "_testsFailed_3coc1_319";
const fixError = "_fixError_3coc1_323";
const fixErrorHint = "_fixErrorHint_3coc1_335";
const fixInProgress = "_fixInProgress_3coc1_341";
const actions = "_actions_3coc1_351";
const styles$1 = {
  page: page$1,
  loadingContainer: loadingContainer$1,
  errorContainer: errorContainer$1,
  breadcrumb: breadcrumb$1,
  separator: separator$1,
  header: header$1,
  headerTop,
  statusBadge: statusBadge$1,
  severityBadge: severityBadge$1,
  statusSubmitted: statusSubmitted$1,
  statusAnalyzing: statusAnalyzing$1,
  statusAnalysisComplete: statusAnalysisComplete$1,
  statusFixing: statusFixing$1,
  statusPrOpened: statusPrOpened$1,
  statusResolved: statusResolved$1,
  statusClosed: statusClosed$1,
  severityCritical: severityCritical$1,
  severityHigh: severityHigh$1,
  severityMedium: severityMedium$1,
  severityLow: severityLow$1,
  title: title$1,
  meta,
  section,
  description,
  preformatted,
  twoColumn,
  analysisSection,
  sectionHeader,
  confidenceMeter,
  confidenceLabel,
  confidenceScore,
  confidenceBar,
  confidenceFill,
  analysisBlock,
  analysisContent,
  codeBlock,
  fileList,
  fileItem,
  fileIcon,
  analysisMeta,
  fixSection,
  prSuccess,
  prHeader,
  prIcon,
  prLink,
  prStats,
  testsFailed,
  fixError,
  fixErrorHint,
  fixInProgress,
  actions
};
const getStatusBadgeClass$1 = (status) => {
  switch (status) {
    case "submitted":
      return styles$1.statusSubmitted;
    case "analyzing":
      return styles$1.statusAnalyzing;
    case "analysis_complete":
      return styles$1.statusAnalysisComplete;
    case "fixing":
      return styles$1.statusFixing;
    case "fix_ready":
    case "pr_opened":
      return styles$1.statusPrOpened;
    case "resolved":
      return styles$1.statusResolved;
    case "closed":
    case "wont_fix":
      return styles$1.statusClosed;
    default:
      return "";
  }
};
const getSeverityBadgeClass$1 = (severity) => {
  switch (severity) {
    case "critical":
      return styles$1.severityCritical;
    case "high":
      return styles$1.severityHigh;
    case "medium":
      return styles$1.severityMedium;
    case "low":
      return styles$1.severityLow;
    default:
      return "";
  }
};
const formatStatus$1 = (status) => {
  return status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};
const formatDate$1 = (dateString) => {
  return new Date(dateString).toLocaleString();
};
const BugStatusPage = () => {
  const { bugId } = useParams();
  const [bugDetail, setBugDetail] = reactExports.useState(null);
  const [loading, setLoading] = reactExports.useState(true);
  const [error2, setError] = reactExports.useState(null);
  const [requestingReanalysis, setRequestingReanalysis] = reactExports.useState(false);
  const fetchBugDetails = reactExports.useCallback(async () => {
    if (!bugId) return;
    try {
      const details = await bugService.getBug(bugId);
      setBugDetail(details);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bug details");
    } finally {
      setLoading(false);
    }
  }, [bugId]);
  reactExports.useEffect(() => {
    fetchBugDetails();
    const pollInterval = setInterval(() => {
      if (bugDetail?.bug.status === "analyzing" || bugDetail?.bug.status === "fixing") {
        fetchBugDetails();
      }
    }, 5e3);
    return () => clearInterval(pollInterval);
  }, [fetchBugDetails, bugDetail?.bug.status]);
  const handleReanalysis = async () => {
    if (!bugId) return;
    setRequestingReanalysis(true);
    try {
      await bugService.requestReanalysis(bugId);
      fetchBugDetails();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request re-analysis");
    } finally {
      setRequestingReanalysis(false);
    }
  };
  if (loading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.loadingContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading bug details..." })
    ] });
  }
  if (error2 || !bugDetail) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Error" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error2 || "Bug not found" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/submit", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Submit New Bug" }) })
    ] });
  }
  const { bug, analysis, fix_attempt } = bugDetail;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.page, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.breadcrumb, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard", children: "Dashboard" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.separator, children: "/" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/my", children: "My Bugs" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.separator, children: "/" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        bug.id.slice(0, 8),
        "..."
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.headerTop, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles$1.statusBadge} ${getStatusBadgeClass$1(bug.status)}`, children: formatStatus$1(bug.status) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles$1.severityBadge} ${getSeverityBadgeClass$1(bug.severity)}`, children: bug.severity.toUpperCase() })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles$1.title, children: bug.title }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.meta, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "ID: ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: bug.id })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Submitted: ",
          formatDate$1(bug.created_at)
        ] }),
        bug.affected_component && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Component: ",
          bug.affected_component
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles$1.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Description" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.description, children: bug.description })
    ] }),
    bug.steps_to_reproduce && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles$1.section, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Steps to Reproduce" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { className: styles$1.preformatted, children: bug.steps_to_reproduce })
    ] }),
    (bug.expected_behavior || bug.actual_behavior) && /* @__PURE__ */ jsxRuntimeExports.jsx("section", { className: styles$1.section, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.twoColumn, children: [
      bug.expected_behavior && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Expected Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: bug.expected_behavior })
      ] }),
      bug.actual_behavior && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Actual Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: bug.actual_behavior })
      ] })
    ] }) }),
    analysis && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles$1.analysisSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.sectionHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "AI Analysis" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.confidenceMeter, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.confidenceLabel, children: "Confidence:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.confidenceScore, children: [
            Math.round(analysis.confidence_score),
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.confidenceBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: styles$1.confidenceFill,
              style: { width: `${analysis.confidence_score}%` }
            }
          ) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.analysisBlock, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Root Cause Analysis" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.analysisContent, children: analysis.root_cause_analysis })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.analysisBlock, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Suggested Fix" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.codeBlock, children: analysis.suggested_fix })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.analysisBlock, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Affected Files" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: styles$1.fileList, children: analysis.affected_files.map((file, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: styles$1.fileItem, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.fileIcon, children: "📄" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: file })
        ] }, index)) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.analysisMeta, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Complexity: ",
          analysis.complexity_estimate
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Model: ",
          analysis.claude_model_used
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Tokens: ",
          analysis.tokens_used.toLocaleString()
        ] }),
        analysis.analysis_completed_at && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Completed: ",
          formatDate$1(analysis.analysis_completed_at)
        ] })
      ] })
    ] }),
    fix_attempt && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles$1.fixSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Fix Attempt" }),
      fix_attempt.pr_url ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.prSuccess, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.prHeader, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.prIcon, children: "✅" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Pull Request Created" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "An automated fix has been generated and submitted for review." }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "a",
          {
            href: fix_attempt.pr_url,
            target: "_blank",
            rel: "noopener noreferrer",
            className: styles$1.prLink,
            children: [
              "View PR #",
              fix_attempt.pr_number,
              " on GitHub"
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.prStats, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            "📝 ",
            fix_attempt.files_changed.length,
            " files"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            "➕ ",
            fix_attempt.lines_added,
            " added"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            "➖ ",
            fix_attempt.lines_removed,
            " removed"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            "✅ ",
            fix_attempt.tests_passed,
            " tests passed"
          ] }),
          fix_attempt.tests_failed > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.testsFailed, children: [
            "❌ ",
            fix_attempt.tests_failed,
            " tests failed"
          ] })
        ] })
      ] }) : fix_attempt.error_message ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.fixError, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "⚠️ Fix Generation Failed" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: fix_attempt.error_message }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.fixErrorHint, children: "A manual fix may be required. The analysis above provides guidance for resolving this issue." })
      ] }) : fix_attempt.status === "in_progress" ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.fixInProgress, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Generating fix..." })
      ] }) : null
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles$1.actions, children: [
      bug.status === "analysis_complete" && !fix_attempt && /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: handleReanalysis,
          disabled: requestingReanalysis,
          children: requestingReanalysis ? "Requesting..." : "Request Re-Analysis"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/submit", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Submit Another Bug" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/my", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "outline", children: "View All My Bugs" }) })
    ] })
  ] });
};
const page = "_page_vdtfk_5";
const header = "_header_vdtfk_11";
const breadcrumb = "_breadcrumb_vdtfk_15";
const separator = "_separator_vdtfk_30";
const titleRow = "_titleRow_vdtfk_34";
const title = "_title_vdtfk_34";
const subtitle = "_subtitle_vdtfk_55";
const filters = "_filters_vdtfk_61";
const filterGroup = "_filterGroup_vdtfk_79";
const filterInfo = "_filterInfo_vdtfk_91";
const loadingContainer = "_loadingContainer_vdtfk_104";
const errorContainer = "_errorContainer_vdtfk_110";
const emptyState = "_emptyState_vdtfk_115";
const bugList = "_bugList_vdtfk_134";
const bugCard = "_bugCard_vdtfk_140";
const bugCardHeader = "_bugCardHeader_vdtfk_156";
const statusBadge = "_statusBadge_vdtfk_162";
const severityBadge = "_severityBadge_vdtfk_163";
const statusSubmitted = "_statusSubmitted_vdtfk_172";
const statusAnalyzing = "_statusAnalyzing_vdtfk_173";
const statusAnalysisComplete = "_statusAnalysisComplete_vdtfk_174";
const statusFixing = "_statusFixing_vdtfk_175";
const statusPrOpened = "_statusPrOpened_vdtfk_176";
const statusResolved = "_statusResolved_vdtfk_177";
const statusClosed = "_statusClosed_vdtfk_178";
const severityCritical = "_severityCritical_vdtfk_180";
const severityHigh = "_severityHigh_vdtfk_181";
const severityMedium = "_severityMedium_vdtfk_182";
const severityLow = "_severityLow_vdtfk_183";
const bugTitle = "_bugTitle_vdtfk_185";
const bugDescription = "_bugDescription_vdtfk_191";
const bugMeta = "_bugMeta_vdtfk_198";
const pagination = "_pagination_vdtfk_207";
const pageInfo = "_pageInfo_vdtfk_215";
const styles = {
  page,
  header,
  breadcrumb,
  separator,
  titleRow,
  title,
  subtitle,
  filters,
  filterGroup,
  filterInfo,
  loadingContainer,
  errorContainer,
  emptyState,
  bugList,
  bugCard,
  bugCardHeader,
  statusBadge,
  severityBadge,
  statusSubmitted,
  statusAnalyzing,
  statusAnalysisComplete,
  statusFixing,
  statusPrOpened,
  statusResolved,
  statusClosed,
  severityCritical,
  severityHigh,
  severityMedium,
  severityLow,
  bugTitle,
  bugDescription,
  bugMeta,
  pagination,
  pageInfo
};
const getStatusBadgeClass = (status) => {
  switch (status) {
    case "submitted":
      return styles.statusSubmitted;
    case "analyzing":
      return styles.statusAnalyzing;
    case "analysis_complete":
      return styles.statusAnalysisComplete;
    case "fixing":
      return styles.statusFixing;
    case "fix_ready":
    case "pr_opened":
      return styles.statusPrOpened;
    case "resolved":
      return styles.statusResolved;
    case "closed":
    case "wont_fix":
      return styles.statusClosed;
    default:
      return "";
  }
};
const getSeverityBadgeClass = (severity) => {
  switch (severity) {
    case "critical":
      return styles.severityCritical;
    case "high":
      return styles.severityHigh;
    case "medium":
      return styles.severityMedium;
    case "low":
      return styles.severityLow;
    default:
      return "";
  }
};
const formatStatus = (status) => {
  return status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString();
};
const BugListPage = () => {
  const [bugs, setBugs] = reactExports.useState([]);
  const [loading, setLoading] = reactExports.useState(true);
  const [error2, setError] = reactExports.useState(null);
  const [filters2, setFilters] = reactExports.useState({});
  const [page2, setPage] = reactExports.useState(1);
  const [hasMore, setHasMore] = reactExports.useState(false);
  const [total, setTotal] = reactExports.useState(0);
  const statusOptions = [
    { value: "", label: "All Statuses" },
    { value: "submitted", label: "Submitted" },
    { value: "analyzing", label: "Analyzing" },
    { value: "analysis_complete", label: "Analysis Complete" },
    { value: "fixing", label: "Fixing" },
    { value: "pr_opened", label: "PR Opened" },
    { value: "resolved", label: "Resolved" },
    { value: "closed", label: "Closed" }
  ];
  const severityOptions = [
    { value: "", label: "All Severities" },
    { value: "critical", label: "Critical" },
    { value: "high", label: "High" },
    { value: "medium", label: "Medium" },
    { value: "low", label: "Low" }
  ];
  const fetchBugs = reactExports.useCallback(async () => {
    setLoading(true);
    try {
      const response = await bugService.listMyBugs({
        ...filters2,
        page: page2,
        limit: 10
      });
      setBugs(response.bugs);
      setHasMore(response.has_more);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bugs");
    } finally {
      setLoading(false);
    }
  }, [filters2, page2]);
  reactExports.useEffect(() => {
    fetchBugs();
  }, [fetchBugs]);
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value || void 0
    }));
    setPage(1);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.page, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.breadcrumb, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard", children: "Dashboard" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.separator, children: "/" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "My Bug Reports" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.titleRow, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles.title, children: "My Bug Reports" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/submit", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Report New Bug" }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.subtitle, children: "Track the status of your submitted bug reports" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.filters, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.filterGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "status-filter", children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            id: "status-filter",
            name: "status",
            value: filters2.status || "",
            onChange: handleFilterChange,
            options: statusOptions
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.filterGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "severity-filter", children: "Severity" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            id: "severity-filter",
            name: "severity",
            value: filters2.severity || "",
            onChange: handleFilterChange,
            options: severityOptions
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.filterInfo, children: [
        "Showing ",
        bugs.length,
        " of ",
        total,
        " bugs"
      ] })
    ] }),
    loading ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.loadingContainer, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) : error2 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error2 }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: fetchBugs, children: "Retry" })
    ] }) : bugs.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "No Bug Reports" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "You haven't submitted any bug reports yet." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/bugs/submit", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Submit Your First Bug" }) })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.bugList, children: bugs.map((bug) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        Link,
        {
          to: `/bugs/${bug.id}`,
          className: styles.bugCard,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.bugCardHeader, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles.statusBadge} ${getStatusBadgeClass(bug.status)}`, children: formatStatus(bug.status) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles.severityBadge} ${getSeverityBadgeClass(bug.severity)}`, children: bug.severity.toUpperCase() })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles.bugTitle, children: bug.title }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.bugDescription, children: bug.description.length > 150 ? `${bug.description.slice(0, 150)}...` : bug.description }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.bugMeta, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "ID: ",
                bug.id.slice(0, 8),
                "..."
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: formatDate(bug.created_at) }),
              bug.affected_component && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: bug.affected_component })
            ] })
          ]
        },
        bug.id
      )) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.pagination, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "outline",
            disabled: page2 === 1,
            onClick: () => setPage((p) => p - 1),
            children: "Previous"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.pageInfo, children: [
          "Page ",
          page2
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "outline",
            disabled: !hasMore,
            onClick: () => setPage((p) => p + 1),
            children: "Next"
          }
        )
      ] })
    ] })
  ] });
};
export {
  BugListPage,
  BugStatusPage,
  BugSubmissionForm,
  BugSubmissionPage
};
//# sourceMappingURL=index-Chw5amK1.js.map
