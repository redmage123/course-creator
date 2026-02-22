import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, h as useSearchParams, a as reactExports } from "./react-vendor-cEae-lCc.js";
import { c as apiClient, u as useAuth } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
class CourseService {
  /**
   * Get all courses with optional filters
   *
   * @param filters - Optional filters for courses
   * @returns List of courses
   */
  async getCourses(filters) {
    const params = new URLSearchParams();
    if (filters) {
      if (filters.organization_id) params.append("organization_id", filters.organization_id);
      if (filters.track_id) params.append("track_id", filters.track_id);
      if (filters.instructor_id) params.append("instructor_id", filters.instructor_id);
      if (filters.difficulty_level) params.append("difficulty_level", filters.difficulty_level);
      if (filters.category) params.append("category", filters.category);
      if (filters.published_only !== void 0) params.append("published_only", String(filters.published_only));
    }
    const queryString = params.toString();
    const url = `/courses${queryString ? `?${queryString}` : ""}`;
    const response = await apiClient.get(url);
    return response;
  }
  /**
   * Get course by ID
   *
   * @param courseId - Course ID
   * @returns Course details
   */
  async getCourseById(courseId) {
    const response = await apiClient.get(`/courses/${courseId}`);
    return response;
  }
  /**
   * Create new course
   *
   * BUSINESS CONTEXT:
   * Creates a new course in the platform. Supports both standalone course creation
   * (for individual instructors) and organizational course creation (for corporate
   * training programs with organizational hierarchy).
   *
   * TECHNICAL IMPLEMENTATION:
   * - Calls POST /courses endpoint
   * - Instructor ID is automatically assigned from authentication token
   * - Course starts in unpublished/draft state
   * - Returns created course with generated ID
   *
   * @param courseData - Course creation data
   * @returns Created course
   */
  async createCourse(courseData) {
    const response = await apiClient.post("/courses", courseData);
    return response;
  }
  /**
   * Update course
   *
   * @param courseId - Course ID
   * @param updates - Course updates
   * @returns Updated course
   */
  async updateCourse(courseId, updates) {
    const response = await apiClient.put(`/courses/${courseId}`, updates);
    return response;
  }
  /**
   * Delete course
   *
   * @param courseId - Course ID
   */
  async deleteCourse(courseId) {
    await apiClient.delete(`/courses/${courseId}`);
  }
  /**
   * Publish course
   *
   * @param courseId - Course ID
   * @returns Published course
   */
  async publishCourse(courseId) {
    const response = await apiClient.post(`/courses/${courseId}/publish`, {});
    return response;
  }
  /**
   * Unpublish course
   *
   * @param courseId - Course ID
   * @returns Unpublished course
   */
  async unpublishCourse(courseId) {
    const response = await apiClient.post(`/courses/${courseId}/unpublish`, {});
    return response;
  }
  /**
   * Get courses by track
   *
   * @param trackId - Track ID
   * @returns List of courses in the track
   */
  async getCoursesByTrack(trackId) {
    return this.getCourses({ track_id: trackId });
  }
  /**
   * Get courses by organization
   *
   * @param organizationId - Organization ID
   * @param publishedOnly - Filter for published courses only
   * @returns List of courses in the organization
   */
  async getCoursesByOrganization(organizationId, publishedOnly = false) {
    return this.getCourses({ organization_id: organizationId, published_only: publishedOnly });
  }
}
const courseService = new CourseService();
class SyllabusService {
  baseUrl = "/api/v1/syllabus";
  /**
   * Generate syllabus from provided parameters
   *
   * SUPPORTS TWO GENERATION MODES:
   * 1. Standard: Uses title/description only
   * 2. URL-based: Fetches content from external URLs
   *
   * @param request - Generation request with optional URLs
   * @returns Generated syllabus with source attribution
   */
  async generateSyllabus(request) {
    try {
      const response = await apiClient.post(
        `${this.baseUrl}/generate`,
        request
      );
      return response;
    } catch (error2) {
      throw this.transformError(error2);
    }
  }
  /**
   * Get progress of a generation request
   *
   * BUSINESS CONTEXT:
   * URL-based generation can take time due to fetching multiple URLs.
   * This allows the UI to show real-time progress updates.
   *
   * @param requestId - UUID of the generation request
   * @returns Progress information
   */
  async getGenerationProgress(requestId) {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/generate/progress/${requestId}`
      );
      return response;
    } catch (error2) {
      throw this.transformError(error2);
    }
  }
  /**
   * Validate URL format
   *
   * @param url - URL to validate
   * @returns Whether URL is valid
   */
  validateUrl(url) {
    if (!url || !url.trim()) {
      return { valid: false, error: "URL cannot be empty" };
    }
    const trimmedUrl = url.trim();
    if (!trimmedUrl.startsWith("http://") && !trimmedUrl.startsWith("https://")) {
      return { valid: false, error: "URL must start with http:// or https://" };
    }
    if (trimmedUrl.length > 2048) {
      return { valid: false, error: "URL exceeds maximum length of 2048 characters" };
    }
    try {
      new URL(trimmedUrl);
    } catch {
      return { valid: false, error: "Invalid URL format" };
    }
    return { valid: true };
  }
  /**
   * Validate multiple URLs
   *
   * @param urls - Array of URLs to validate
   * @returns Validation results
   */
  validateUrls(urls) {
    const errors = [];
    if (urls.length > 10) {
      errors.push("Maximum 10 URLs allowed");
    }
    urls.forEach((url, index) => {
      const result = this.validateUrl(url);
      if (!result.valid) {
        errors.push(`URL ${index + 1}: ${result.error}`);
      }
    });
    return {
      valid: errors.length === 0,
      errors
    };
  }
  /**
   * Transform API errors for UI display
   *
   * @param error - Raw error from API
   * @returns Transformed error with user-friendly message
   */
  transformError(error2) {
    if (error2 instanceof Error) {
      const apiError = error2;
      if (apiError.response?.data?.detail) {
        const detail = apiError.response.data.detail;
        if (typeof detail === "string") {
          return new Error(detail);
        }
        if (Array.isArray(detail)) {
          const messages = detail.map(
            (d) => `${d.loc.join(".")}: ${d.msg}`
          );
          return new Error(`Validation failed: ${messages.join(", ")}`);
        }
        if (typeof detail === "object" && "message" in detail) {
          return new Error(detail.message);
        }
      }
      return error2;
    }
    return new Error("An unexpected error occurred");
  }
  /**
   * Check if generation request has external sources
   *
   * @param request - Generation request
   * @returns Whether request includes external URLs
   */
  hasExternalSources(request) {
    return Boolean(
      request.source_url || request.source_urls && request.source_urls.length > 0 || request.external_sources && request.external_sources.length > 0
    );
  }
  /**
   * Get all source URLs from request
   *
   * @param request - Generation request
   * @returns Array of all source URLs
   */
  getAllSourceUrls(request) {
    const urls = [];
    if (request.source_url) {
      urls.push(request.source_url);
    }
    if (request.source_urls) {
      urls.push(...request.source_urls);
    }
    if (request.external_sources) {
      request.external_sources.forEach((source) => {
        if (!urls.includes(source.url)) {
          urls.push(source.url);
        }
      });
    }
    return urls;
  }
}
const syllabusService = new SyllabusService();
const container = "_container_1e3zn_5";
const header = "_header_1e3zn_11";
const subtitle = "_subtitle_1e3zn_22";
const form = "_form_1e3zn_27";
const section = "_section_1e3zn_34";
const formGroup = "_formGroup_1e3zn_51";
const required = "_required_1e3zn_63";
const charCount = "_charCount_1e3zn_92";
const helpText = "_helpText_1e3zn_100";
const formRow = "_formRow_1e3zn_107";
const error = "_error_1e3zn_113";
const tagInputContainer = "_tagInputContainer_1e3zn_123";
const addTagBtn = "_addTagBtn_1e3zn_132";
const tagsList = "_tagsList_1e3zn_149";
const tag = "_tag_1e3zn_123";
const removeTagBtn = "_removeTagBtn_1e3zn_167";
const actions = "_actions_1e3zn_188";
const cancelBtn = "_cancelBtn_1e3zn_197";
const submitBtn = "_submitBtn_1e3zn_198";
const sectionHeader = "_sectionHeader_1e3zn_234";
const toggleLabel = "_toggleLabel_1e3zn_247";
const toggleCheckbox = "_toggleCheckbox_1e3zn_256";
const toggleSwitch = "_toggleSwitch_1e3zn_263";
const urlGenerationContent = "_urlGenerationContent_1e3zn_294";
const featureDescription = "_featureDescription_1e3zn_299";
const urlInputList = "_urlInputList_1e3zn_306";
const urlInputRow = "_urlInputRow_1e3zn_312";
const inputError = "_inputError_1e3zn_334";
const urlError = "_urlError_1e3zn_338";
const removeUrlBtn = "_removeUrlBtn_1e3zn_346";
const addUrlBtn = "_addUrlBtn_1e3zn_371";
const generationOptions = "_generationOptions_1e3zn_396";
const checkboxLabel = "_checkboxLabel_1e3zn_403";
const generateBtn = "_generateBtn_1e3zn_418";
const progressContainer = "_progressContainer_1e3zn_447";
const progressHeader = "_progressHeader_1e3zn_455";
const progressStep = "_progressStep_1e3zn_462";
const progressTime = "_progressTime_1e3zn_468";
const progressBar = "_progressBar_1e3zn_473";
const progressFill = "_progressFill_1e3zn_480";
const progressDetails = "_progressDetails_1e3zn_487";
const progressWarning = "_progressWarning_1e3zn_495";
const syllabusPreview = "_syllabusPreview_1e3zn_500";
const syllabusContent = "_syllabusContent_1e3zn_517";
const syllabusHeader = "_syllabusHeader_1e3zn_521";
const syllabusLevel = "_syllabusLevel_1e3zn_528";
const syllabusDescription = "_syllabusDescription_1e3zn_538";
const syllabusObjectives = "_syllabusObjectives_1e3zn_545";
const syllabusModules = "_syllabusModules_1e3zn_568";
const moduleDescription = "_moduleDescription_1e3zn_594";
const syllabusSources = "_syllabusSources_1e3zn_600";
const styles = {
  container,
  header,
  subtitle,
  form,
  section,
  formGroup,
  required,
  charCount,
  helpText,
  formRow,
  error,
  tagInputContainer,
  addTagBtn,
  tagsList,
  tag,
  removeTagBtn,
  actions,
  cancelBtn,
  submitBtn,
  sectionHeader,
  toggleLabel,
  toggleCheckbox,
  toggleSwitch,
  urlGenerationContent,
  featureDescription,
  urlInputList,
  urlInputRow,
  inputError,
  urlError,
  removeUrlBtn,
  addUrlBtn,
  generationOptions,
  checkboxLabel,
  generateBtn,
  progressContainer,
  progressHeader,
  progressStep,
  progressTime,
  progressBar,
  progressFill,
  progressDetails,
  progressWarning,
  syllabusPreview,
  syllabusContent,
  syllabusHeader,
  syllabusLevel,
  syllabusDescription,
  syllabusObjectives,
  syllabusModules,
  moduleDescription,
  syllabusSources
};
const CourseCreatePage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const trackIdFromUrl = searchParams.get("track_id");
  const organizationId = user?.organization_id;
  const [formData, setFormData] = reactExports.useState({
    title: "",
    description: "",
    category: "",
    difficulty_level: "beginner",
    estimated_duration: void 0,
    duration_unit: "weeks",
    price: 0,
    tags: [],
    organization_id: organizationId,
    track_id: trackIdFromUrl || void 0
  });
  const [tagInput, setTagInput] = reactExports.useState("");
  const [loading, setLoading] = reactExports.useState(false);
  const [error2, setError] = reactExports.useState(null);
  const [useUrlGeneration, setUseUrlGeneration] = reactExports.useState(false);
  const [sourceUrls, setSourceUrls] = reactExports.useState([""]);
  const [urlErrors, setUrlErrors] = reactExports.useState([]);
  const [isGenerating, setIsGenerating] = reactExports.useState(false);
  const [generationProgress, setGenerationProgress] = reactExports.useState(null);
  const [generatedSyllabus, setGeneratedSyllabus] = reactExports.useState(null);
  const [useRagEnhancement, setUseRagEnhancement] = reactExports.useState(true);
  const [includeCodeExamples, setIncludeCodeExamples] = reactExports.useState(true);
  const progressIntervalRef = reactExports.useRef(null);
  const difficultyOptions = ["beginner", "intermediate", "advanced"];
  const durationUnits = ["hours", "days", "weeks", "months"];
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "estimated_duration" || name === "price" ? value ? parseFloat(value) : void 0 : value
    }));
  };
  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags || [], tagInput.trim()]
      }));
      setTagInput("");
    }
  };
  const handleRemoveTag = (tagToRemove) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((tag2) => tag2 !== tagToRemove) || []
    }));
  };
  const handleUrlChange = (index, value) => {
    const newUrls = [...sourceUrls];
    newUrls[index] = value;
    setSourceUrls(newUrls);
    const newErrors = [...urlErrors];
    if (value.trim()) {
      const validation = syllabusService.validateUrl(value);
      newErrors[index] = validation.error || "";
    } else {
      newErrors[index] = "";
    }
    setUrlErrors(newErrors);
  };
  const handleAddUrl = () => {
    if (sourceUrls.length < 10) {
      setSourceUrls([...sourceUrls, ""]);
      setUrlErrors([...urlErrors, ""]);
    }
  };
  const handleRemoveUrl = (index) => {
    if (sourceUrls.length > 1) {
      const newUrls = sourceUrls.filter((_, i) => i !== index);
      const newErrors = urlErrors.filter((_, i) => i !== index);
      setSourceUrls(newUrls);
      setUrlErrors(newErrors);
    }
  };
  const getValidUrls = reactExports.useCallback(() => {
    return sourceUrls.filter((url) => {
      const trimmed = url.trim();
      return trimmed && syllabusService.validateUrl(trimmed).valid;
    });
  }, [sourceUrls]);
  reactExports.useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);
  const startProgressPolling = reactExports.useCallback((requestId) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }
    progressIntervalRef.current = setInterval(async () => {
      try {
        const response = await syllabusService.getGenerationProgress(requestId);
        if (response.success) {
          setGenerationProgress(response.progress);
          if (response.progress.generation_complete) {
            if (progressIntervalRef.current) {
              clearInterval(progressIntervalRef.current);
              progressIntervalRef.current = null;
            }
          }
        }
      } catch (err) {
        console.error("Progress polling error:", err);
      }
    }, 2e3);
  }, []);
  const handleGenerateSyllabus = async () => {
    const validUrls = getValidUrls();
    if (validUrls.length === 0) {
      setError("Please enter at least one valid URL");
      return;
    }
    if (!formData.title.trim()) {
      setError("Please enter a course title before generating");
      return;
    }
    setIsGenerating(true);
    setError(null);
    setGeneratedSyllabus(null);
    setGenerationProgress(null);
    try {
      const request = {
        title: formData.title,
        description: formData.description || `Training course generated from external documentation`,
        level: formData.difficulty_level,
        source_urls: validUrls,
        use_rag_enhancement: useRagEnhancement,
        include_code_examples: includeCodeExamples
      };
      const response = await syllabusService.generateSyllabus(request);
      if (response.request_id) {
        startProgressPolling(response.request_id);
      }
      if (response.success && response.syllabus) {
        setGeneratedSyllabus(response.syllabus);
        if (response.syllabus.description && !formData.description) {
          setFormData((prev) => ({
            ...prev,
            description: response.syllabus.description
          }));
        }
      } else {
        setError(response.message || "Failed to generate syllabus");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
      console.error("Syllabus generation error:", err);
    } finally {
      setIsGenerating(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!formData.title.trim()) {
        throw new Error("Course title is required");
      }
      if (!formData.description.trim()) {
        throw new Error("Course description is required");
      }
      await courseService.createCourse(formData);
      if (trackIdFromUrl) {
        navigate("/organization/tracks");
      } else {
        navigate("/dashboard/org-admin");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create course");
      console.error("Course creation error:", err);
    } finally {
      setLoading(false);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.container, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: "Create New Course" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.subtitle, children: trackIdFromUrl ? "Add a new course to your learning track" : "Create a standalone course" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { className: styles.form, onSubmit: handleSubmit, children: [
      error2 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.error, role: "alert", children: error2 }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Basic Information" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "title", children: [
            "Course Title ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.required, children: "*" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              id: "title",
              name: "title",
              value: formData.title,
              onChange: handleInputChange,
              placeholder: "e.g., Introduction to Python Programming",
              required: true,
              maxLength: 200
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "description", children: [
            "Description ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.required, children: "*" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "textarea",
            {
              id: "description",
              name: "description",
              value: formData.description,
              onChange: handleInputChange,
              placeholder: "Provide a detailed description of the course...",
              required: true,
              maxLength: 2e3,
              rows: 5
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.charCount, children: [
            formData.description.length,
            " / 2000"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "category", children: "Category" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              id: "category",
              name: "category",
              value: formData.category || "",
              onChange: handleInputChange,
              placeholder: "e.g., Programming, Data Science, Business"
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionHeader, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "AI-Powered Content Generation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.toggleLabel, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "checkbox",
                checked: useUrlGeneration,
                onChange: (e) => setUseUrlGeneration(e.target.checked),
                className: styles.toggleCheckbox
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.toggleSwitch }),
            "Generate from external documentation"
          ] })
        ] }),
        useUrlGeneration && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.urlGenerationContent, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.featureDescription, children: "Automatically generate course content by providing URLs to external documentation. Works with Salesforce docs, AWS documentation, internal wikis, and more." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Documentation URLs" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.urlInputList, children: sourceUrls.map((url, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.urlInputRow, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "url",
                  value: url,
                  onChange: (e) => handleUrlChange(index, e.target.value),
                  placeholder: "https://docs.example.com/guide",
                  className: urlErrors[index] ? styles.inputError : "",
                  disabled: isGenerating
                }
              ),
              sourceUrls.length > 1 && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  type: "button",
                  onClick: () => handleRemoveUrl(index),
                  className: styles.removeUrlBtn,
                  disabled: isGenerating,
                  "aria-label": "Remove URL",
                  children: "×"
                }
              ),
              urlErrors[index] && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.urlError, children: urlErrors[index] })
            ] }, index)) }),
            sourceUrls.length < 10 && /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                type: "button",
                onClick: handleAddUrl,
                className: styles.addUrlBtn,
                disabled: isGenerating,
                children: "+ Add another URL"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Add up to 10 URLs. Supports HTTP/HTTPS documentation pages." })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.generationOptions, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.checkboxLabel, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: useRagEnhancement,
                  onChange: (e) => setUseRagEnhancement(e.target.checked),
                  disabled: isGenerating
                }
              ),
              "Use RAG enhancement for better context"
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.checkboxLabel, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: includeCodeExamples,
                  onChange: (e) => setIncludeCodeExamples(e.target.checked),
                  disabled: isGenerating
                }
              ),
              "Include code examples from documentation"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: handleGenerateSyllabus,
              className: styles.generateBtn,
              disabled: isGenerating || getValidUrls().length === 0 || !formData.title.trim(),
              children: isGenerating ? "Generating..." : "Generate Syllabus from URLs"
            }
          ),
          isGenerating && generationProgress && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.progressContainer, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.progressHeader, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.progressStep, children: generationProgress.current_step }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.progressTime, children: [
                Math.round(generationProgress.elapsed_seconds),
                "s"
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.progressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                className: styles.progressFill,
                style: {
                  width: `${Math.min(
                    (generationProgress.urls_fetched + generationProgress.chunks_ingested) / (generationProgress.total_urls * 2 + 10) * 100,
                    95
                  )}%`
                }
              }
            ) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.progressDetails, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "URLs: ",
                generationProgress.urls_fetched,
                "/",
                generationProgress.total_urls
              ] }),
              generationProgress.urls_failed > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.progressWarning, children: [
                "(",
                generationProgress.urls_failed,
                " failed)"
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "Chunks: ",
                generationProgress.chunks_ingested
              ] })
            ] })
          ] }),
          generatedSyllabus && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusPreview, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Generated Syllabus Preview" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusContent, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusHeader, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: generatedSyllabus.title }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.syllabusLevel, children: generatedSyllabus.level })
              ] }),
              generatedSyllabus.description && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.syllabusDescription, children: generatedSyllabus.description }),
              generatedSyllabus.objectives && generatedSyllabus.objectives.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusObjectives, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Learning Objectives:" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { children: generatedSyllabus.objectives.map((obj, i) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: obj }, i)) })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusModules, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("strong", { children: [
                  "Modules (",
                  generatedSyllabus.modules.length,
                  "):"
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("ol", { children: generatedSyllabus.modules.map((module, i) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: module.title }),
                  module.description && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.moduleDescription, children: module.description })
                ] }, i)) })
              ] }),
              generatedSyllabus.external_sources && generatedSyllabus.external_sources.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.syllabusSources, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Sources:" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { children: generatedSyllabus.external_sources.map((source, i) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: /* @__PURE__ */ jsxRuntimeExports.jsx("a", { href: source.url, target: "_blank", rel: "noopener noreferrer", children: source.title || source.url }) }, i)) })
              ] })
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Course Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "difficulty_level", children: "Difficulty Level" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "select",
              {
                id: "difficulty_level",
                name: "difficulty_level",
                value: formData.difficulty_level,
                onChange: handleInputChange,
                children: difficultyOptions.map((level) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: level, children: level.charAt(0).toUpperCase() + level.slice(1) }, level))
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "estimated_duration", children: "Estimated Duration" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "number",
                id: "estimated_duration",
                name: "estimated_duration",
                value: formData.estimated_duration || "",
                onChange: handleInputChange,
                min: "1",
                placeholder: "e.g., 8"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "duration_unit", children: "Duration Unit" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "select",
              {
                id: "duration_unit",
                name: "duration_unit",
                value: formData.duration_unit,
                onChange: handleInputChange,
                children: durationUnits.map((unit) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: unit, children: unit.charAt(0).toUpperCase() + unit.slice(1) }, unit))
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "price", children: "Price (USD)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "number",
              id: "price",
              name: "price",
              value: formData.price,
              onChange: handleInputChange,
              min: "0",
              step: "0.01",
              placeholder: "0.00"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Set to 0 for free courses" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Tags" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "tag-input", children: "Add Tags" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.tagInputContainer, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "text",
                id: "tag-input",
                value: tagInput,
                onChange: (e) => setTagInput(e.target.value),
                onKeyPress: (e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag();
                  }
                },
                placeholder: "Type a tag and press Enter"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                type: "button",
                onClick: handleAddTag,
                className: styles.addTagBtn,
                children: "Add Tag"
              }
            )
          ] }),
          formData.tags && formData.tags.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.tagsList, children: formData.tags.map((tag2) => /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.tag, children: [
            tag2,
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                type: "button",
                onClick: () => handleRemoveTag(tag2),
                className: styles.removeTagBtn,
                "aria-label": `Remove ${tag2}`,
                children: "×"
              }
            )
          ] }, tag2)) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.actions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            onClick: () => navigate(-1),
            className: styles.cancelBtn,
            disabled: loading,
            children: "Cancel"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "submit",
            className: styles.submitBtn,
            disabled: loading,
            children: loading ? "Creating..." : "Create Course"
          }
        )
      ] })
    ] })
  ] });
};
export {
  CourseCreatePage
};
//# sourceMappingURL=CourseCreatePage-CvcWsUdq.js.map
