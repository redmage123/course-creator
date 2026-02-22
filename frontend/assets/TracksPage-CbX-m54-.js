import { j as jsxRuntimeExports, c as useQueryClient, d as useMutation, u as useQuery } from "./query-vendor-BigVEegc.js";
import { a as reactExports, R as React } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { c as apiClient, C as Card, B as Button, M as Modal, S as Spinner, u as useAuth, H as Heading, t as tokenManager } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { S as Select } from "./Select-D3EGugkq.js";
import { T as Textarea } from "./Textarea-sTT_CGBL.js";
import "./state-vendor-B_izx0oA.js";
class TrackService {
  baseUrl = "/tracks/";
  /**
   * Get all tracks for an organization
   *
   * BUSINESS LOGIC:
   * Organization admins view all tracks in their organization.
   * Supports filtering by project, status, and difficulty.
   *
   * @param organizationId - Organization ID
   * @param filters - Optional filters (project_id, status, difficulty_level)
   * @returns Array of tracks
   */
  async getOrganizationTracks(organizationId, filters) {
    const params = {
      organization_id: organizationId
    };
    if (filters?.project_id) params.project_id = filters.project_id;
    if (filters?.status) params.track_status = filters.status;
    if (filters?.difficulty_level) params.difficulty_level = filters.difficulty_level;
    return await apiClient.get(this.baseUrl, { params });
  }
  /**
   * Get tracks by project
   *
   * BUSINESS LOGIC:
   * View all tracks within a specific project.
   * Projects can have multiple tracks (e.g., "Web Dev Fundamentals", "Advanced Web Dev").
   *
   * @param projectId - Project ID
   * @param status - Optional status filter
   * @returns Array of tracks
   */
  async getProjectTracks(projectId, status) {
    const params = {
      project_id: projectId
    };
    if (status) params.track_status = status;
    return await apiClient.get(this.baseUrl, { params });
  }
  /**
   * Get track by ID
   *
   * @param trackId - Track ID
   * @returns Track details with enrollment and instructor counts
   */
  async getTrackById(trackId) {
    return await apiClient.get(`${this.baseUrl}/${trackId}`);
  }
  /**
   * Create new track
   *
   * BUSINESS LOGIC:
   * Organization admins create learning tracks to structure course content.
   * Each track belongs to a project and can contain multiple courses.
   *
   * @param data - Track creation data
   * @returns Created track
   */
  async createTrack(data) {
    return await apiClient.post(this.baseUrl, data);
  }
  /**
   * Update existing track
   *
   * BUSINESS LOGIC:
   * Organization admins can modify track details, learning objectives,
   * difficulty level, and capacity limits.
   *
   * @param trackId - Track ID
   * @param data - Updated track data
   * @returns Updated track
   */
  async updateTrack(trackId, data) {
    return await apiClient.put(`${this.baseUrl}/${trackId}`, data);
  }
  /**
   * Delete track
   *
   * BUSINESS LOGIC:
   * Soft delete for tracks with active enrollments.
   * Hard delete only allowed for tracks with no enrollments.
   *
   * @param trackId - Track ID
   */
  async deleteTrack(trackId) {
    await apiClient.delete(`${this.baseUrl}/${trackId}`);
  }
  /**
   * Publish track (make available for enrollment)
   *
   * BUSINESS LOGIC:
   * Publishing a track makes it visible to students for enrollment.
   * Requires track to have at least one course assigned.
   *
   * @param trackId - Track ID
   * @returns Published track with updated status
   */
  async publishTrack(trackId) {
    return await apiClient.post(`${this.baseUrl}/${trackId}/publish`);
  }
  /**
   * Unpublish track (make unavailable for enrollment)
   *
   * BUSINESS LOGIC:
   * Unpublishing a track hides it from new enrollments.
   * Existing enrollments remain active.
   *
   * @param trackId - Track ID
   * @returns Unpublished track with updated status
   */
  async unpublishTrack(trackId) {
    return await apiClient.post(`${this.baseUrl}/${trackId}/unpublish`);
  }
  /**
   * Bulk enroll students in track
   *
   * BUSINESS LOGIC:
   * Organization admins can enroll multiple students at once.
   * Students are enrolled in all courses within the track.
   *
   * @param trackId - Track ID
   * @param data - Enrollment request with student emails
   * @returns Enrollment results (successful and failed)
   */
  async bulkEnrollStudents(trackId, data) {
    return await apiClient.post(
      `${this.baseUrl}/${trackId}/enroll`,
      data
    );
  }
  /**
   * Get track enrollments
   *
   * BUSINESS LOGIC:
   * View all student enrollments for a track.
   * Supports filtering by enrollment status.
   *
   * @param trackId - Track ID
   * @param enrollmentStatus - Optional status filter
   * @returns Enrollment list with student details
   */
  async getTrackEnrollments(trackId, enrollmentStatus) {
    const params = {};
    if (enrollmentStatus) params.enrollment_status = enrollmentStatus;
    return await apiClient.get(`${this.baseUrl}/${trackId}/enrollments`, { params });
  }
  /**
   * Get track analytics
   *
   * BUSINESS LOGIC:
   * Comprehensive analytics for track performance:
   * - Enrollment trends
   * - Completion rates
   * - Student progress
   * - Engagement metrics
   *
   * @param trackId - Track ID
   * @returns Track analytics data
   */
  async getTrackAnalytics(trackId) {
    const response = await apiClient.get(`${this.baseUrl}/${trackId}/analytics`);
    return response.analytics;
  }
  /**
   * Duplicate track
   *
   * BUSINESS LOGIC:
   * Create a copy of an existing track with new name.
   * Useful for creating similar tracks or versioning.
   *
   * @param trackId - Track ID to duplicate
   * @param newName - Optional new name for duplicated track
   * @returns Duplicated track details
   */
  async duplicateTrack(trackId, newName) {
    const body = newName ? { new_name: newName } : {};
    return await apiClient.post(`${this.baseUrl}/${trackId}/duplicate`, body);
  }
  /**
   * Get track locations (for instructor assignment)
   *
   * BUSINESS LOGIC:
   * When a track belongs to a project with multiple geographic locations,
   * instructors can be assigned to specific locations.
   * This returns available locations for the track's parent project.
   *
   * @param trackId - Track ID
   * @returns Array of available locations
   */
  async getTrackLocations(trackId) {
    return await apiClient.get(`${this.baseUrl}/${trackId}/locations`);
  }
  /**
   * Search tracks by name
   *
   * BUSINESS LOGIC:
   * Search tracks within organization by name or description.
   * Client-side filtering is preferred for better UX.
   *
   * @param organizationId - Organization ID
   * @param query - Search query
   * @returns Matching tracks
   */
  async searchTracks(organizationId, query) {
    const allTracks = await this.getOrganizationTracks(organizationId);
    const lowerQuery = query.toLowerCase();
    return allTracks.filter(
      (track) => track.name.toLowerCase().includes(lowerQuery) || track.description?.toLowerCase().includes(lowerQuery)
    );
  }
}
const trackService = new TrackService();
const styles$3 = {
  "track-card": "_track-card_w97ll_6",
  "card-header": "_card-header_w97ll_20",
  "title-section": "_title-section_w97ll_29",
  "track-title": "_track-title_w97ll_33",
  "status-badges": "_status-badges_w97ll_41",
  "status-badge": "_status-badge_w97ll_41",
  "difficulty-badge": "_difficulty-badge_w97ll_48",
  "status-active": "_status-active_w97ll_59",
  "status-draft": "_status-draft_w97ll_64",
  "status-archived": "_status-archived_w97ll_69",
  "difficulty-beginner": "_difficulty-beginner_w97ll_75",
  "difficulty-intermediate": "_difficulty-intermediate_w97ll_80",
  "difficulty-advanced": "_difficulty-advanced_w97ll_85",
  "card-body": "_card-body_w97ll_91",
  "track-description": "_track-description_w97ll_98",
  "metadata-grid": "_metadata-grid_w97ll_110",
  "metadata-item": "_metadata-item_w97ll_116",
  "metadata-icon": "_metadata-icon_w97ll_122",
  "metadata-content": "_metadata-content_w97ll_127",
  "metadata-label": "_metadata-label_w97ll_134",
  "metadata-value": "_metadata-value_w97ll_140",
  "capacity-section": "_capacity-section_w97ll_147",
  "capacity-label": "_capacity-label_w97ll_151",
  "capacity-percentage": "_capacity-percentage_w97ll_161",
  "capacity-bar": "_capacity-bar_w97ll_166",
  "capacity-fill": "_capacity-fill_w97ll_173",
  "capacity-healthy": "_capacity-healthy_w97ll_179",
  "capacity-warning": "_capacity-warning_w97ll_183",
  "capacity-critical": "_capacity-critical_w97ll_187",
  "objectives-section": "_objectives-section_w97ll_192",
  "objectives-title": "_objectives-title_w97ll_199",
  "objectives-list": "_objectives-list_w97ll_206",
  "objective-item": "_objective-item_w97ll_215",
  "objective-item-more": "_objective-item-more_w97ll_231",
  "card-footer": "_card-footer_w97ll_239",
  "action-buttons": "_action-buttons_w97ll_248",
  "delete-button": "_delete-button_w97ll_254",
  "metadata-footer": "_metadata-footer_w97ll_263",
  "metadata-footer-item": "_metadata-footer-item_w97ll_269"
};
const TrackCard = ({
  track,
  onEdit,
  onDelete,
  onViewCourses
}) => {
  const formatDuration = () => {
    if (!track.duration_weeks) return "Duration not specified";
    const weeks = track.duration_weeks;
    if (weeks === 1) return "1 week";
    return `${weeks} weeks`;
  };
  const formatDifficulty = (level) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };
  const getStatusClass = () => {
    switch (track.status) {
      case "active":
        return styles$3["status-active"];
      case "draft":
        return styles$3["status-draft"];
      case "archived":
        return styles$3["status-archived"];
      default:
        return styles$3["status-draft"];
    }
  };
  const getDifficultyClass = () => {
    switch (track.difficulty_level) {
      case "beginner":
        return styles$3["difficulty-beginner"];
      case "intermediate":
        return styles$3["difficulty-intermediate"];
      case "advanced":
        return styles$3["difficulty-advanced"];
      default:
        return styles$3["difficulty-beginner"];
    }
  };
  const getCapacityPercentage = () => {
    if (!track.max_students) return 0;
    return Math.round(track.enrollment_count / track.max_students * 100);
  };
  const getCapacityStatus = () => {
    const percentage = getCapacityPercentage();
    if (percentage >= 90) return "critical";
    if (percentage >= 75) return "warning";
    return "healthy";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "medium", className: styles$3["track-card"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["card-header"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["title-section"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$3["track-title"], children: track.name }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["status-badges"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles$3["status-badge"]} ${getStatusClass()}`, children: track.status.charAt(0).toUpperCase() + track.status.slice(1) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles$3["difficulty-badge"]} ${getDifficultyClass()}`, children: formatDifficulty(track.difficulty_level) })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["card-body"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3["track-description"], children: track.description || "No description available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-icon"], children: "📅" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-content"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-label"], children: "Duration" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-value"], children: formatDuration() })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-icon"], children: "👥" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-content"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-label"], children: "Enrolled" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3["metadata-value"], children: [
              track.enrollment_count,
              track.max_students && ` / ${track.max_students}`
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-icon"], children: "👨‍🏫" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-content"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-label"], children: "Instructors" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-value"], children: track.instructor_count || 0 })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-icon"], children: "🎯" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["metadata-content"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-label"], children: "Objectives" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3["metadata-value"], children: track.learning_objectives.length || 0 })
          ] })
        ] })
      ] }),
      track.max_students && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["capacity-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["capacity-label"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Enrollment Capacity" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3["capacity-percentage"], children: [
            getCapacityPercentage(),
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["capacity-bar"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: `${styles$3["capacity-fill"]} ${styles$3[`capacity-${getCapacityStatus()}`]}`,
            style: { width: `${getCapacityPercentage()}%` }
          }
        ) })
      ] }),
      track.learning_objectives.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["objectives-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$3["objectives-title"], children: "Learning Objectives:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles$3["objectives-list"], children: [
          track.learning_objectives.slice(0, 3).map((objective, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { className: styles$3["objective-item"], children: objective }, index)),
          track.learning_objectives.length > 3 && /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: styles$3["objective-item-more"], children: [
            "+",
            track.learning_objectives.length - 3,
            " more..."
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["card-footer"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["action-buttons"], children: [
        onViewCourses && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "ghost",
            size: "small",
            onClick: () => onViewCourses(track.id),
            children: "View Courses"
          }
        ),
        onEdit && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "ghost",
            size: "small",
            onClick: () => onEdit(track.id),
            children: "Edit"
          }
        ),
        onDelete && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "ghost",
            size: "small",
            onClick: () => onDelete(track.id),
            className: styles$3["delete-button"],
            children: "Delete"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["metadata-footer"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3["metadata-footer-item"], children: [
        "Created ",
        new Date(track.created_at).toLocaleDateString()
      ] }) })
    ] })
  ] });
};
const form$1 = "_form_zdj8r_3";
const formGroup = "_formGroup_zdj8r_9";
const label = "_label_zdj8r_15";
const required = "_required_zdj8r_21";
const errorText = "_errorText_zdj8r_25";
const helpText = "_helpText_zdj8r_31";
const gridTwo = "_gridTwo_zdj8r_37";
const errorBox = "_errorBox_zdj8r_43";
const actions = "_actions_zdj8r_52";
const styles$2 = {
  form: form$1,
  formGroup,
  label,
  required,
  errorText,
  helpText,
  gridTwo,
  errorBox,
  actions
};
const initialFormData = {
  name: "",
  description: "",
  duration_weeks: "",
  difficulty_level: "beginner",
  max_students: "",
  target_audience: "",
  prerequisites: "",
  learning_objectives: ""
};
const CreateTrackModal = ({
  isOpen,
  onClose,
  projectId,
  onSuccess
}) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = reactExports.useState(initialFormData);
  const [validationErrors, setValidationErrors] = reactExports.useState({});
  const createMutation = useMutation({
    mutationFn: (data) => {
      console.log("[CreateTrackModal] mutationFn called with data:", data);
      return trackService.createTrack(data);
    },
    onSuccess: (createdTrack) => {
      console.log("[CreateTrackModal] Track created successfully:", createdTrack);
      queryClient.invalidateQueries({ queryKey: ["tracks"] });
      if (onSuccess) {
        onSuccess(createdTrack.id);
      }
      setFormData(initialFormData);
      setValidationErrors({});
      onClose();
    },
    onError: (error2) => {
      console.error("[CreateTrackModal] Failed to create track:", error2);
      console.error("[CreateTrackModal] Error details:", {
        message: error2.message,
        response: error2.response,
        stack: error2.stack
      });
      setValidationErrors({
        submit: error2.message || "Failed to create track. Please try again."
      });
    }
  });
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };
  const validateForm = () => {
    const errors = {};
    if (!formData.name.trim()) {
      errors.name = "Track name is required";
    } else if (formData.name.length < 3) {
      errors.name = "Track name must be at least 3 characters";
    } else if (formData.name.length > 200) {
      errors.name = "Track name must be less than 200 characters";
    }
    if (formData.duration_weeks && isNaN(Number(formData.duration_weeks))) {
      errors.duration_weeks = "Duration must be a number";
    } else if (formData.duration_weeks && Number(formData.duration_weeks) < 1) {
      errors.duration_weeks = "Duration must be at least 1 week";
    } else if (formData.duration_weeks && Number(formData.duration_weeks) > 52) {
      errors.duration_weeks = "Duration must be less than 52 weeks";
    }
    if (formData.max_students && isNaN(Number(formData.max_students))) {
      errors.max_students = "Max students must be a number";
    } else if (formData.max_students && Number(formData.max_students) < 1) {
      errors.max_students = "Max students must be at least 1";
    } else if (formData.max_students && Number(formData.max_students) > 1e3) {
      errors.max_students = "Max students must be less than 1000";
    }
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };
  const handleSubmit = async (e) => {
    console.log("[CreateTrackModal] handleSubmit called");
    console.log("[CreateTrackModal] Project ID:", projectId);
    console.log("[CreateTrackModal] Form data:", formData);
    e.preventDefault();
    const isValid = validateForm();
    console.log("[CreateTrackModal] Validation result:", isValid);
    console.log("[CreateTrackModal] Validation errors:", validationErrors);
    if (!isValid) {
      console.error("[CreateTrackModal] Validation failed, not submitting");
      return;
    }
    const parseArrayField = (value) => {
      return value.split("\n").map((item) => item.trim()).filter((item) => item.length > 0);
    };
    const requestData = {
      name: formData.name.trim(),
      description: formData.description.trim() || void 0,
      project_id: projectId,
      duration_weeks: formData.duration_weeks ? Number(formData.duration_weeks) : void 0,
      difficulty_level: formData.difficulty_level,
      max_students: formData.max_students ? Number(formData.max_students) : void 0,
      target_audience: parseArrayField(formData.target_audience),
      prerequisites: parseArrayField(formData.prerequisites),
      learning_objectives: parseArrayField(formData.learning_objectives)
    };
    console.log("[CreateTrackModal] Submitting request data:", requestData);
    createMutation.mutate(requestData);
    console.log("[CreateTrackModal] Mutation called");
  };
  const handleClose = () => {
    if (!createMutation.isPending) {
      setFormData(initialFormData);
      setValidationErrors({});
      onClose();
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Modal,
    {
      isOpen,
      onClose: handleClose,
      title: "Create New Track",
      size: "large",
      preventClose: createMutation.isPending,
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { className: styles$2.form, onSubmit: handleSubmit, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "name", className: styles$2.label, children: [
            "Track Name ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.required, children: "*" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "name",
              name: "name",
              type: "text",
              value: formData.name,
              onChange: handleChange,
              placeholder: "e.g., Web Development Bootcamp",
              disabled: createMutation.isPending,
              error: validationErrors.name
            }
          ),
          validationErrors.name && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.errorText, children: validationErrors.name })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "description", className: styles$2.label, children: "Description" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              id: "description",
              name: "description",
              value: formData.description,
              onChange: handleChange,
              placeholder: "Describe what students will learn in this track...",
              rows: 3,
              disabled: createMutation.isPending
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.gridTwo, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "difficulty_level", className: styles$2.label, children: "Difficulty Level" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Select,
              {
                id: "difficulty_level",
                name: "difficulty_level",
                value: formData.difficulty_level,
                onChange: (value) => {
                  const event = {
                    target: { name: "difficulty_level", value }
                  };
                  handleChange(event);
                },
                disabled: createMutation.isPending,
                options: [
                  { value: "beginner", label: "Beginner" },
                  { value: "intermediate", label: "Intermediate" },
                  { value: "advanced", label: "Advanced" }
                ]
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "duration_weeks", className: styles$2.label, children: "Duration (weeks)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "duration_weeks",
                name: "duration_weeks",
                type: "number",
                value: formData.duration_weeks,
                onChange: handleChange,
                placeholder: "e.g., 12",
                min: "1",
                max: "52",
                disabled: createMutation.isPending,
                error: validationErrors.duration_weeks
              }
            ),
            validationErrors.duration_weeks && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.errorText, children: validationErrors.duration_weeks })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "max_students", className: styles$2.label, children: "Maximum Students (Optional)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "max_students",
              name: "max_students",
              type: "number",
              value: formData.max_students,
              onChange: handleChange,
              placeholder: "Leave empty for unlimited",
              min: "1",
              max: "1000",
              disabled: createMutation.isPending,
              error: validationErrors.max_students
            }
          ),
          validationErrors.max_students && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.errorText, children: validationErrors.max_students })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "target_audience", className: styles$2.label, children: "Target Audience" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              id: "target_audience",
              name: "target_audience",
              value: formData.target_audience,
              onChange: handleChange,
              placeholder: "Enter each audience on a new line\ne.g., Junior developers\nCareer changers",
              rows: 3,
              disabled: createMutation.isPending
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.helpText, children: "One item per line" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "prerequisites", className: styles$2.label, children: "Prerequisites" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              id: "prerequisites",
              name: "prerequisites",
              value: formData.prerequisites,
              onChange: handleChange,
              placeholder: "Enter each prerequisite on a new line\ne.g., Basic HTML knowledge\nFamiliarity with command line",
              rows: 3,
              disabled: createMutation.isPending
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.helpText, children: "One item per line" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "learning_objectives", className: styles$2.label, children: "Learning Objectives" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              id: "learning_objectives",
              name: "learning_objectives",
              value: formData.learning_objectives,
              onChange: handleChange,
              placeholder: "Enter each objective on a new line\ne.g., Build responsive web applications\nDeploy to production",
              rows: 4,
              disabled: createMutation.isPending
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.helpText, children: "One objective per line" })
        ] }),
        validationErrors.submit && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.errorBox, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Error:" }),
          " ",
          validationErrors.submit
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.actions, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              type: "button",
              variant: "ghost",
              onClick: handleClose,
              disabled: createMutation.isPending,
              children: "Cancel"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              type: "submit",
              variant: "primary",
              disabled: createMutation.isPending,
              children: createMutation.isPending ? "Creating..." : "Create Track"
            }
          )
        ] })
      ] })
    }
  );
};
const form = "_form_ldrcq_3";
const error = "_error_ldrcq_30";
const styles$1 = {
  form,
  "form-section": "_form-section_ldrcq_9",
  "section-title": "_section-title_ldrcq_15",
  "form-row": "_form-row_ldrcq_24",
  error
};
const EditTrackModal = ({
  isOpen,
  track,
  onClose,
  onSuccess
}) => {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = reactExports.useState(null);
  const [formData, setFormData] = reactExports.useState({
    name: track.name,
    description: track.description || "",
    duration_weeks: track.duration_weeks?.toString() || "",
    difficulty_level: track.difficulty_level,
    max_students: track.max_students?.toString() || "",
    status: track.status,
    target_audience: track.target_audience?.join(", ") || "",
    prerequisites: track.prerequisites?.join(", ") || "",
    learning_objectives: track.learning_objectives?.join(", ") || ""
  });
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };
  const updateMutation = useMutation({
    mutationFn: (data) => trackService.updateTrack(track.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tracks"] });
      onSuccess();
      setSubmitError(null);
    },
    onError: (error2) => {
      setSubmitError(error2.message || "Failed to update track");
    }
  });
  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitError(null);
    if (!formData.name.trim()) {
      setSubmitError("Track name is required");
      return;
    }
    const updateData = {
      name: formData.name.trim(),
      description: formData.description.trim() || void 0,
      duration_weeks: formData.duration_weeks ? parseInt(formData.duration_weeks, 10) : void 0,
      difficulty_level: formData.difficulty_level,
      max_students: formData.max_students ? parseInt(formData.max_students, 10) : void 0,
      status: formData.status,
      target_audience: formData.target_audience ? formData.target_audience.split(",").map((s) => s.trim()).filter(Boolean) : void 0,
      prerequisites: formData.prerequisites ? formData.prerequisites.split(",").map((s) => s.trim()).filter(Boolean) : void 0,
      learning_objectives: formData.learning_objectives ? formData.learning_objectives.split(",").map((s) => s.trim()).filter(Boolean) : void 0
    };
    updateMutation.mutate(updateData);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Modal,
    {
      isOpen,
      onClose,
      title: "Edit Track",
      size: "large",
      footer: /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "ghost", onClick: onClose, disabled: updateMutation.isPending, children: "Cancel" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "primary",
            onClick: handleSubmit,
            disabled: updateMutation.isPending,
            children: updateMutation.isPending ? /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }) : "Save Changes"
          }
        )
      ] }),
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles$1.form, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1["section-title"], children: "Basic Information" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              name: "name",
              label: "Track Name",
              type: "text",
              placeholder: "Enter track name",
              value: formData.name,
              onChange: handleChange,
              required: true,
              fullWidth: true
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              name: "description",
              label: "Description",
              placeholder: "Describe this learning track",
              value: formData.description,
              onChange: handleChange,
              fullWidth: true,
              rows: 3
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1["section-title"], children: "Track Settings" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-row"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              Select,
              {
                name: "difficulty_level",
                label: "Difficulty Level",
                value: formData.difficulty_level,
                onChange: handleChange,
                fullWidth: true,
                required: true,
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "beginner", children: "Beginner" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "intermediate", children: "Intermediate" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "advanced", children: "Advanced" })
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              Select,
              {
                name: "status",
                label: "Status",
                value: formData.status,
                onChange: handleChange,
                fullWidth: true,
                required: true,
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "draft", children: "Draft" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "active", children: "Active" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "archived", children: "Archived" })
                ]
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-row"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                name: "duration_weeks",
                label: "Duration (weeks)",
                type: "number",
                placeholder: "e.g., 12",
                value: formData.duration_weeks,
                onChange: handleChange,
                fullWidth: true,
                min: "1"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                name: "max_students",
                label: "Max Students",
                type: "number",
                placeholder: "e.g., 30",
                value: formData.max_students,
                onChange: handleChange,
                fullWidth: true,
                min: "1"
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1["section-title"], children: "Additional Details" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              name: "target_audience",
              label: "Target Audience",
              placeholder: "e.g., Web developers, Data scientists (comma-separated)",
              value: formData.target_audience,
              onChange: handleChange,
              fullWidth: true,
              rows: 2,
              helperText: "Comma-separated list"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              name: "prerequisites",
              label: "Prerequisites",
              placeholder: "e.g., Basic programming, HTML/CSS (comma-separated)",
              value: formData.prerequisites,
              onChange: handleChange,
              fullWidth: true,
              rows: 2,
              helperText: "Comma-separated list"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Textarea,
            {
              name: "learning_objectives",
              label: "Learning Objectives",
              placeholder: "e.g., Build web apps, Understand React (comma-separated)",
              value: formData.learning_objectives,
              onChange: handleChange,
              fullWidth: true,
              rows: 3,
              helperText: "Comma-separated list"
            }
          )
        ] }),
        submitError && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.error, role: "alert", children: submitError })
      ] })
    }
  );
};
const styles = {
  "tracks-page": "_tracks-page_188wm_3",
  "page-header": "_page-header_188wm_12",
  "header-content": "_header-content_188wm_20",
  "header-description": "_header-description_188wm_25",
  "filters-card": "_filters-card_188wm_31",
  "filters-grid": "_filters-grid_188wm_37",
  "filter-group": "_filter-group_188wm_43",
  "results-count": "_results-count_188wm_48",
  "tracks-grid": "_tracks-grid_188wm_56",
  "empty-state": "_empty-state_188wm_62"
};
const TracksPage = () => {
  const { organizationId } = useAuth();
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = reactExports.useState(false);
  const [editingTrack, setEditingTrack] = reactExports.useState(null);
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [difficultyFilter, setDifficultyFilter] = reactExports.useState("all");
  const [statusFilter, setStatusFilter] = reactExports.useState("all");
  const [selectedProjectId, setSelectedProjectId] = reactExports.useState("");
  const { data: programsData } = useQuery({
    queryKey: ["trainingPrograms", "organization", organizationId],
    queryFn: async () => {
      const token = tokenManager.getToken();
      const response = await fetch(`/api/v1/courses?organization_id=${organizationId}&published_only=false`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error("Failed to fetch programs");
      return response.json();
    },
    enabled: !!organizationId,
    staleTime: 5 * 60 * 1e3
  });
  React.useEffect(() => {
    if (programsData && !selectedProjectId) {
      const programs = Array.isArray(programsData) ? programsData : programsData.data || [];
      if (programs.length > 0) {
        setSelectedProjectId(programs[0].id);
        console.log("[TracksPage] Auto-selected project:", programs[0].id, programs[0].title);
      }
    }
  }, [programsData, selectedProjectId]);
  const {
    data: tracks,
    isLoading,
    error: error2
  } = useQuery({
    queryKey: ["tracks", organizationId],
    queryFn: () => trackService.getOrganizationTracks(organizationId),
    enabled: !!organizationId,
    staleTime: 2 * 60 * 1e3
    // Cache for 2 minutes
  });
  const filteredTracks = reactExports.useMemo(() => {
    if (!tracks) return [];
    return tracks.filter((track) => {
      const matchesSearch = !searchQuery || track.name.toLowerCase().includes(searchQuery.toLowerCase()) || track.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesDifficulty = difficultyFilter === "all" || track.difficulty_level === difficultyFilter;
      const matchesStatus = statusFilter === "all" || track.status === statusFilter;
      return matchesSearch && matchesDifficulty && matchesStatus;
    });
  }, [tracks, searchQuery, difficultyFilter, statusFilter]);
  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ["tracks"] });
  };
  const handleEditTrack = (track) => {
    setEditingTrack(track);
  };
  const handleEditSuccess = () => {
    setEditingTrack(null);
    queryClient.invalidateQueries({ queryKey: ["tracks"] });
  };
  const handleDeleteTrack = async (trackId) => {
    if (window.confirm("Are you sure you want to delete this track? This action cannot be undone.")) {
      try {
        await trackService.deleteTrack(trackId);
        queryClient.invalidateQueries({ queryKey: ["tracks"] });
      } catch (error22) {
        console.error("Failed to delete track:", error22);
        alert("Failed to delete track. Please try again.");
      }
    }
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["tracks-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) }) });
  }
  if (error2) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["tracks-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load tracks. Please try refreshing the page." }) }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["tracks-page"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["page-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["header-content"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Learning Tracks" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["header-description"], children: "Manage learning tracks and structured educational paths" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => setIsCreateModalOpen(true), children: "Create Track" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "medium", className: styles["filters-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["filters-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["filter-group"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            type: "text",
            placeholder: "Search by name or description...",
            value: searchQuery,
            onChange: (e) => setSearchQuery(e.target.value),
            fullWidth: true,
            label: "Search"
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["filter-group"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            value: difficultyFilter,
            onChange: (value) => setDifficultyFilter(value),
            label: "Difficulty",
            fullWidth: true,
            options: [
              { value: "all", label: "All Levels" },
              { value: "beginner", label: "Beginner" },
              { value: "intermediate", label: "Intermediate" },
              { value: "advanced", label: "Advanced" }
            ]
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["filter-group"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          Select,
          {
            value: statusFilter,
            onChange: (value) => setStatusFilter(value),
            label: "Status",
            fullWidth: true,
            options: [
              { value: "all", label: "All Status" },
              { value: "draft", label: "Draft" },
              { value: "active", label: "Active" },
              { value: "archived", label: "Archived" }
            ]
          }
        ) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["results-count"], children: [
        "Showing ",
        filteredTracks.length,
        " of ",
        tracks?.length || 0,
        " tracks"
      ] })
    ] }),
    filteredTracks.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles["empty-state"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "No Tracks Found" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: searchQuery || difficultyFilter !== "all" || statusFilter !== "all" ? "Try adjusting your filters to see more results." : "Get started by creating your first learning track." }),
      !searchQuery && difficultyFilter === "all" && statusFilter === "all" && /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => setIsCreateModalOpen(true),
          style: { marginTop: "1rem" },
          children: "Create First Track"
        }
      )
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["tracks-grid"], children: filteredTracks.map((track) => /* @__PURE__ */ jsxRuntimeExports.jsx(
      TrackCard,
      {
        track,
        onEdit: handleEditTrack,
        onDelete: handleDeleteTrack
      },
      track.id
    )) }),
    isCreateModalOpen && (() => {
      const testProjectId = typeof window !== "undefined" && window.__TEST_PROJECT_ID__;
      const effectiveProjectId = testProjectId || selectedProjectId || "default-project-id";
      console.log("[TracksPage] Opening CreateTrackModal with projectId:", effectiveProjectId);
      console.log("[TracksPage] - Test injected ID:", testProjectId);
      console.log("[TracksPage] - Selected ID:", selectedProjectId);
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        CreateTrackModal,
        {
          isOpen: isCreateModalOpen,
          onClose: () => setIsCreateModalOpen(false),
          projectId: effectiveProjectId,
          onSuccess: handleCreateSuccess
        }
      );
    })(),
    editingTrack && /* @__PURE__ */ jsxRuntimeExports.jsx(
      EditTrackModal,
      {
        isOpen: true,
        onClose: () => setEditingTrack(null),
        onSuccess: handleEditSuccess,
        track: editingTrack
      }
    )
  ] }) });
};
export {
  TracksPage
};
//# sourceMappingURL=TracksPage-CbX-m54-.js.map
